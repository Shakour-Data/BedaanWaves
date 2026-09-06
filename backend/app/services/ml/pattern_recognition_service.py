"""Pattern Recognition Service - Tier 4 ML Service

Chart pattern recognition and analysis.
"""

from typing import Any

from app.core.utils import utc_now_iso

from ..core import MLService


class PatternRecognitionService(MLService):
    """Chart pattern recognition service."""

    def __init__(self, service_name: str = "PatternRecognitionService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("PatternRecognitionService initialized")

    async def shutdown(self) -> None:
        self.model = None
        self.logger.info("PatternRecognitionService shutdown")

    async def train(self, training_data: dict[str, Any]) -> dict[str, Any]:
        patterns = training_data.get("patterns", [])
        self.model = {"trained": True, "patterns_learned": len(patterns)}
        return {"status": "trained", "patterns": len(patterns)}

    async def predict(self, data: dict[str, Any]) -> dict[str, Any]:
        prices = data.get("prices", [])
        if len(prices) < 20:
            raise ValueError("Insufficient data for pattern recognition")

        # Use previous 10 items for range to compare against current
        historical_window = prices[-11:-1]
        local_max = max(historical_window)
        local_min = min(historical_window)
        current = prices[-1]

        if current > local_max:
            pattern = "resistance_test"
            probability = 0.75
        elif current < local_min:
            pattern = "support_test"
            probability = 0.75
        else:
            pattern = "continuation"
            probability = 0.55
        return {
            "ticker": data.get("ticker", "UNKNOWN"),
            "pattern": pattern,
            "probability": probability,
            "current_price": current,
            "local_max": local_max,
            "local_min": local_min,
            "timestamp": utc_now_iso(),
        }

    async def detect_patterns(self, prices: list[float], volume: list[float] | None = None) -> list[dict[str, Any]]:
        patterns = []
        n = len(prices)
        for i in range(20, n):
            window = prices[i-20:i]
            local_max = max(window)
            local_min = min(window)
            current = window[-1]
            if current >= local_max:
                patterns.append({"index": i, "pattern": "resistance_test", "price": current})
            elif current <= local_min:
                patterns.append({"index": i, "pattern": "support_test", "price": current})
        return patterns
