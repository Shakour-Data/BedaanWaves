"""Portfolio Optimization Service - Tier 4 ML Service

Portfolio optimization and allocation suggestions.
Uses configurable parameters for risk-adjusted return weighting.
"""

from typing import Any

from app.core.utils import utc_now_iso

from ..core import MLService


class PortfolioOptimizationService(MLService):
    """Portfolio optimization service with configurable weight allocation."""

    # Configurable default parameters (replaces magic numbers)
    DEFAULT_EXPECTED_RETURN = 0.1
    DEFAULT_RISK = 0.2
    RISK_EPSILON = 1e-6

    def __init__(self, service_name: str = "PortfolioOptimizationService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("PortfolioOptimizationService initialized")

    async def shutdown(self) -> None:
        self.model = None
        self.logger.info("PortfolioOptimizationService shutdown")

    async def train(self, training_data: dict[str, Any]) -> dict[str, Any]:
        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression

            returns_data = training_data.get("returns", [])
            risks_data = training_data.get("risks", [])
            if returns_data and risks_data and len(returns_data) == len(risks_data):
                X = np.array([[r] for r in risks_data])
                y = np.array(returns_data)
                self._sklearn_model = LinearRegression()
                self._sklearn_model.fit(X, y)
        except Exception:
            pass

        self.model = {"trained": True}
        return {"status": "trained"}

    async def predict(self, data: dict[str, Any]) -> dict[str, Any]:
        assets = data.get("assets", [])
        returns = data.get("expected_returns", {})
        risks = data.get("risks", {})
        if not assets:
            raise ValueError("No assets provided")
        total = len(assets)
        if total == 0:
            raise ValueError("Empty portfolio")
        allocation = {}
        for asset in assets:
            er = returns.get(asset, self.DEFAULT_EXPECTED_RETURN)
            rk = risks.get(asset, self.DEFAULT_RISK)
            weight = er / (rk + self.RISK_EPSILON) if total > 0 else 0
            allocation[asset] = weight
        total_weight = sum(allocation.values())
        if total_weight > 0:
            allocation = {k: round(v / total_weight, 4) for k, v in allocation.items()}
        return {
            "portfolio_id": data.get("portfolio_id") or data.get("ticker"),
            "allocation": allocation,
            "expected_return": round(sum(allocation.get(a, 0) * returns.get(a, self.DEFAULT_EXPECTED_RETURN) for a in assets), 4),
            "expected_volatility": round(sum(allocation.get(a, 0) * risks.get(a, self.DEFAULT_RISK) for a in assets), 4),
            "sharpe_ratio": round(sum(allocation.get(a, 0) * returns.get(a, self.DEFAULT_EXPECTED_RETURN) for a in assets) / max(sum(allocation.get(a, 0) * risks.get(a, self.DEFAULT_RISK) for a in assets), self.RISK_EPSILON), 4),
            "timestamp": utc_now_iso(),
        }
