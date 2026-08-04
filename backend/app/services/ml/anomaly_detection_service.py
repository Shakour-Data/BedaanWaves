"""Anomaly Detection Service - Tier 4 ML Service

Market anomaly detection and unusual activity spotting.
"""
import math
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from ..core import MLService


class AnomalyDetectionService(MLService):
    """Anomaly detection service."""

    def __init__(self, service_name: str = "AnomalyDetectionService"):
        super().__init__(service_name)
        self._min_training_samples = 5

    async def initialize(self) -> None:
        self.logger.info("AnomalyDetectionService initialized")

    async def shutdown(self) -> None:
        self.model = None
        self.logger.info("AnomalyDetectionService shutdown")

    async def train(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        values = training_data.get("values", [])
        if not values:
            raise ValueError("No training data provided")
        if len(values) < self._min_training_samples:
            raise ValueError(
                f"Insufficient data for training: {len(values)} samples, "
                f"minimum required: {self._min_training_samples}"
            )
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = math.sqrt(variance) if variance > 0 else 1.0
        self.model = {"trained": True, "mean": mean, "std": std}
        return {"status": "trained", "mean": mean, "std": std}

    async def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prices = data.get("prices", [])
        returns = data.get("returns", [])
        values = returns or [prices[i] - prices[i-1] for i in range(1, len(prices))]
        if not self.model or not self.model.get("trained"):
            raise ValueError("Model not trained or method called before training")
        mean = self.model["mean"]
        std = self.model["std"]
        current = values[-1] if values else 0.0
        z_threshold = data.get("z_threshold", 3.0)
        z_score = (current - mean) / std if std > 0 else 0
        is_anomaly = abs(z_score) > z_threshold
        return {
            "ticker": data.get("ticker", "UNKNOWN"),
            "is_anomaly": is_anomaly,
            "z_score": round(z_score, 4),
            "value": round(current, 4),
            "threshold": z_threshold,
            "severity": "high" if abs(z_score) > 4 else "medium" if abs(z_score) > 3 else "low",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def batch_detect(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        import asyncio
        tasks = [self.predict(d) for d in data_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        processed = []
        for item, result in zip(data_list, results):
            processed.append({"error": str(result)} if isinstance(result, Exception) else result)
        return processed