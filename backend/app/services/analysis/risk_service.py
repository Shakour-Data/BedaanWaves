"""
Risk Analysis Service - Tier 3 Analysis Service

Risk assessment and portfolio risk analysis.
"""

import math
from typing import Any

from app.core.utils import utc_now_iso

from ..core import AnalysisService


class RiskAnalysisService(AnalysisService):
    """
    Risk analysis service.

    Provides:
    - Value at Risk (VaR)
    - Beta calculation
    - Volatility analysis
    - Sharpe ratio
    - Correlation analysis
    - Stress testing
    """

    def __init__(self, service_name: str = "RiskAnalysisService"):
        """Initialize risk analysis service"""
        super().__init__(service_name)

    async def initialize(self) -> None:
        """Initialize service"""
        self.logger.info("RiskAnalysisService initialized")

    async def shutdown(self) -> None:
        """Shutdown service"""
        self.logger.info("RiskAnalysisService shutdown")

    async def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Perform risk analysis.

        Args:
            data: Price and returns data

        Returns:
            Risk metrics
        """
        returns = data.get("returns", [])
        data.get("prices", [])

        if not returns or len(returns) < 20:
            return {"error": "Insufficient return data"}

        analysis = {
            "timestamp": utc_now_iso(),
            "ticker": data.get("ticker", "UNKNOWN"),
            "metrics": {},
        }

        # Calculate risk metrics
        analysis["metrics"].update(
            await self._calculate_volatility_metrics(returns, data)
        )
        analysis["metrics"].update(
            await self._calculate_value_at_risk(returns)
        )
        analysis["metrics"].update(
            await self._calculate_performance_metrics(returns)
        )

        return analysis

    async def _calculate_volatility_metrics(self, returns: list[float], data: dict[str, Any] | None = None) -> dict[str, float]:
        """Calculate volatility metrics"""
        volatility = self._calculate_std_dev(returns)
        beta = self._calculate_beta(returns)

        return {
            "volatility": volatility,
            "annual_volatility": volatility * math.sqrt(252),  # 252 trading days
            "beta": beta,
        }

    async def _calculate_value_at_risk(self, returns: list[float]) -> dict[str, float]:
        """Calculate Value at Risk"""
        if not returns:
            return {"var_95": 0.0, "var_99": 0.0, "cvar_95": 0.0}

        sorted_returns = sorted(returns)
        n = len(sorted_returns)

        idx_95 = max(0, int(n * 0.05) - 1)
        idx_99 = max(0, int(n * 0.01) - 1)

        var_95 = sorted_returns[idx_95]
        var_99 = sorted_returns[idx_99]

        cvar_count = max(1, int(n * 0.05))
        cvar_95 = sum(sorted_returns[:cvar_count]) / cvar_count

        return {
            "var_95": var_95 * 100,
            "var_99": var_99 * 100,
            "cvar_95": cvar_95 * 100,
        }

    async def _calculate_performance_metrics(self, returns: list[float], risk_free_rate: float = 0.0) -> dict[str, float]:
        """Calculate performance metrics"""
        mean_return = sum(returns) / len(returns)
        volatility = self._calculate_std_dev(returns)
        excess_return = mean_return - risk_free_rate

        return {
            "mean_return": mean_return * 100,
            "sharpe_ratio": (excess_return / volatility) if volatility > 0 else 0,
            "max_drawdown": self._calculate_max_drawdown(returns),
            "sortino_ratio": self._calculate_sortino_ratio(returns, risk_free_rate),
        }

    def _calculate_std_dev(self, values: list[float]) -> float:
        """Standard deviation"""
        if not values or len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    def _calculate_max_drawdown(self, returns: list[float]) -> float:
        """Maximum drawdown"""
        if not returns:
            return 0.0

        cumulative = 1.0
        peak = 1.0
        max_dd = 0.0

        for ret in returns:
            cumulative *= (1 + ret)
            peak = max(peak, cumulative)
            drawdown = (peak - cumulative) / peak
            max_dd = max(max_dd, drawdown)

        return max_dd * 100

    def _calculate_sortino_ratio(self, returns: list[float], risk_free_rate: float = 0.0) -> float:
        """Sortino ratio (downside volatility focused)"""
        mean_return = sum(returns) / len(returns)
        excess_return = mean_return - risk_free_rate

        mar = 0.0
        downside_returns = [r - mar for r in returns if r < mar]
        if not downside_returns:
            return 0.0

        downside_variance = sum(r ** 2 for r in downside_returns) / len(returns)
        downside_volatility = math.sqrt(downside_variance)

        return (excess_return / downside_volatility) if downside_volatility > 0 else 0

    def _calculate_beta(self, returns: list[float], market_returns: list[float] | None = None) -> float:
        """Calculate beta relative to market returns."""
        if not returns or not market_returns or len(returns) != len(market_returns):
            return 1.0

        n = len(returns)
        mean_asset = sum(returns) / n
        mean_market = sum(market_returns) / n

        covariance = sum((returns[i] - mean_asset) * (market_returns[i] - mean_market) for i in range(n)) / (n - 1)
        market_variance = sum((r - mean_market) ** 2 for r in market_returns) / (n - 1)

        return covariance / market_variance if market_variance != 0 else 1.0

    async def calculate_portfolio_risk(
        self,
        weights: dict[str, float],
        correlations: dict[str, float],
        volatilities: dict[str, float],
    ) -> dict[str, Any]:
        """
        Calculate portfolio risk.

        Args:
            weights: Portfolio weights {ticker: weight}
            correlations: Asset correlations
            volatilities: Asset volatilities

        Returns:
            Portfolio risk metrics
        """
        # Calculate portfolio variance with correlations
        portfolio_var = 0.0
        tickers = list(weights.keys())

        for i, ticker_i in enumerate(tickers):
            w_i = weights[ticker_i]
            vol_i = volatilities.get(ticker_i, 0.0)

            for j, ticker_j in enumerate(tickers):
                w_j = weights[ticker_j]
                vol_j = volatilities.get(ticker_j, 0.0)
                corr = correlations.get(f"{ticker_i}_{ticker_j}", 1.0 if i == j else 0.0)

                portfolio_var += w_i * w_j * vol_i * vol_j * corr

        return {
            "portfolio_volatility": math.sqrt(portfolio_var) if portfolio_var > 0 else 0.0,
            "portfolio_var_95": math.sqrt(portfolio_var) * 1.645 if portfolio_var > 0 else 0.0,
            "portfolio_var_99": math.sqrt(portfolio_var) * 2.326 if portfolio_var > 0 else 0.0,
        }

    async def stress_test(
        self,
        portfolio: dict[str, float],
        scenarios: list[dict[str, float]],
    ) -> list[dict[str, Any]]:
        """
        Stress test portfolio under scenarios.

        Args:
            portfolio: Portfolio {ticker: position_value}
            scenarios: Stress scenarios {ticker: price_change}

        Returns:
            Stress test results
        """
        results = []

        for scenario in scenarios:
            portfolio_value = 0.0

            for ticker, position in portfolio.items():
                change = scenario.get(ticker, 0.0)
                new_value = position * (1 + change)
                portfolio_value += new_value

            results.append({
                "scenario": scenario,
                "portfolio_value": portfolio_value,
                "loss": sum(portfolio.values()) - portfolio_value,
            })

        return results
