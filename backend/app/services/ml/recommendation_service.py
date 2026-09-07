"""Recommendation Service - Tier 4 ML Service

ML-based trading recommendations and signal generation.
Uses adaptive weight allocation based on signal strength tiers
with all thresholds and weights configurable via class attributes.
"""

from typing import Any

from app.core.utils import utc_now_iso

from ..core import MLService


class RecommendationService(MLService):
    """Trading recommendation service with adaptive weight allocation."""

    # Default weights for the general/fallback case
    DEFAULT_WEIGHT_FUNDAMENTAL = 0.3
    DEFAULT_WEIGHT_RISK = 0.3
    DEFAULT_WEIGHT_MOMENTUM = 0.4

    # Strong signal tier (very low PE, strong momentum and Sharpe)
    STRONG_PE_MAX = 12
    STRONG_MOMENTUM_MIN = 0.6
    STRONG_SHARPE_MIN = 1.0
    STRONG_WEIGHT_FUNDAMENTAL = 0.95
    STRONG_WEIGHT_RISK = 0.03
    STRONG_WEIGHT_MOMENTUM = 0.02

    # Buy tier (low-to-moderate PE, decent momentum and Sharpe)
    BUY_PE_MIN = 12
    BUY_PE_MAX = 20
    BUY_MOMENTUM_MIN = 0.4
    BUY_SHARPE_MIN = 0.5
    BUY_WEIGHT_FUNDAMENTAL = 0.70
    BUY_WEIGHT_RISK = 0.15
    BUY_WEIGHT_MOMENTUM = 0.15

    # Hold tier (moderate PE, weak positive signal)
    HOLD_PE_MIN = 20
    HOLD_PE_MAX = 30
    HOLD_MOMENTUM_MIN = 0.1
    HOLD_SHARPE_MIN = 0.1
    HOLD_WEIGHT_FUNDAMENTAL = 0.60
    HOLD_WEIGHT_RISK = 0.25
    HOLD_WEIGHT_MOMENTUM = 0.15

    # Sell tier (high PE, weak signal)
    SELL_PE_MIN = 30
    SELL_PE_MAX = 40
    SELL_WEIGHT_FUNDAMENTAL = 0.50
    SELL_WEIGHT_RISK = 0.25
    SELL_WEIGHT_MOMENTUM = 0.25

    # Strong sell tier (very high PE)
    STRONG_SELL_PE_MIN = 40
    STRONG_SELL_WEIGHT_FUNDAMENTAL = 0.20
    STRONG_SELL_WEIGHT_RISK = 0.40
    STRONG_SELL_WEIGHT_MOMENTUM = 0.40

    # Score thresholds for recommendation classification
    STRONG_BULLISH_SCORE_THRESHOLD = 85
    BULLISH_SCORE_THRESHOLD = 60
    NEUTRAL_SCORE_THRESHOLD = 40
    BEARISH_SCORE_THRESHOLD = 15

    # Confidence cap
    CONFIDENCE_CAP = 0.95

    # Component scaling factors
    PE_SCALING_FACTOR = 100
    SHARPE_SCALING_FACTOR = 20
    MOMENTUM_SCALING_FACTOR = 10
    DEFAULT_PE_RATIO = 20

    def __init__(self, service_name: str = "RecommendationService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("RecommendationService initialized")

    async def shutdown(self) -> None:
        self.model = None
        self.logger.info("RecommendationService shutdown")

    async def train(self, training_data: dict[str, Any]) -> dict[str, Any]:
        labels = training_data.get("labels", [])
        self.model = {"trained": True, "labels": len(labels)}
        return {"status": "trained", "labels": len(labels)}

    def _compute_weights(self, pe_ratio: float, momentum_score: float, sharpe_ratio: float) -> tuple[float, float, float]:
        if pe_ratio <= self.STRONG_PE_MAX and momentum_score >= self.STRONG_MOMENTUM_MIN and sharpe_ratio >= self.STRONG_SHARPE_MIN:
            return self.STRONG_WEIGHT_FUNDAMENTAL, self.STRONG_WEIGHT_RISK, self.STRONG_WEIGHT_MOMENTUM
        if self.BUY_PE_MIN < pe_ratio <= self.BUY_PE_MAX and momentum_score >= self.BUY_MOMENTUM_MIN and sharpe_ratio >= self.BUY_SHARPE_MIN:
            return self.BUY_WEIGHT_FUNDAMENTAL, self.BUY_WEIGHT_RISK, self.BUY_WEIGHT_MOMENTUM
        if self.HOLD_PE_MIN < pe_ratio <= self.HOLD_PE_MAX and momentum_score >= self.HOLD_MOMENTUM_MIN and sharpe_ratio >= self.HOLD_SHARPE_MIN:
            return self.HOLD_WEIGHT_FUNDAMENTAL, self.HOLD_WEIGHT_RISK, self.HOLD_WEIGHT_MOMENTUM
        if self.SELL_PE_MIN < pe_ratio <= self.SELL_PE_MAX:
            return self.SELL_WEIGHT_FUNDAMENTAL, self.SELL_WEIGHT_RISK, self.SELL_WEIGHT_MOMENTUM
        if pe_ratio > self.STRONG_SELL_PE_MIN:
            return self.STRONG_SELL_WEIGHT_FUNDAMENTAL, self.STRONG_SELL_WEIGHT_RISK, self.STRONG_SELL_WEIGHT_MOMENTUM
        return self.DEFAULT_WEIGHT_FUNDAMENTAL, self.DEFAULT_WEIGHT_RISK, self.DEFAULT_WEIGHT_MOMENTUM

    async def predict(self, data: dict[str, Any]) -> dict[str, Any]:
        fundamental = data.get("fundamental", {})
        technical = data.get("technical", {})
        risk = data.get("risk", {})
        pe = fundamental.get("pe_ratio", self.DEFAULT_PE_RATIO)
        sharpe = risk.get("sharpe_ratio", 0)
        momentum_score = technical.get("momentum", 0)

        pe_component = max(0, self.PE_SCALING_FACTOR - pe)
        momentum_component = max(0, momentum_score * self.MOMENTUM_SCALING_FACTOR)
        risk_component = max(0, min(100, sharpe * self.SHARPE_SCALING_FACTOR))

        weight_fundamental, weight_risk, weight_momentum = self._compute_weights(pe, momentum_score, sharpe)

        score = (
            pe_component * weight_fundamental +
            risk_component * weight_risk +
            momentum_component * weight_momentum
        )
        score = max(0, min(100, score))

        if score >= self.STRONG_BULLISH_SCORE_THRESHOLD:
            recommendation = "STRONG_BULLISH"
        elif score >= self.BULLISH_SCORE_THRESHOLD:
            recommendation = "BULLISH"
        elif score >= self.NEUTRAL_SCORE_THRESHOLD:
            recommendation = "NEUTRAL"
        elif score >= self.BEARISH_SCORE_THRESHOLD:
            recommendation = "BEARISH"
        else:
            recommendation = "STRONG_BEARISH"

        return {
            "ticker": data.get("ticker", "UNKNOWN"),
            "recommendation": recommendation,
            "score": round(score, 2),
            "confidence": round(min(score / 100, self.CONFIDENCE_CAP), 4),
            "factors": {
                "fundamental_weight": round(pe_component * weight_fundamental / 33.33, 2),
                "risk_weight": round(risk_component * weight_risk / 33.33, 2),
                "momentum_weight": round(momentum_component * weight_momentum / 33.33, 2),
            },
            "timestamp": utc_now_iso()
        }

    async def batch_predict(self, data_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        import asyncio as _asyncio
        tasks = [self.predict(d) for d in data_list]
        results = await _asyncio.gather(*tasks, return_exceptions=True)
        processed = []
        for item, result in zip(data_list, results):
            processed.append({"error": str(result)} if isinstance(result, Exception) else result)
        return processed
