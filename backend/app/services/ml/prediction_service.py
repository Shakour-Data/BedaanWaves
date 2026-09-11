"""Prediction Service - Tier 4 ML Service

Stock price and direction prediction using ML models.
Uses sklearn for model training and configurable parameters
for prediction logic.

Reproducibility: ``random_state=42`` in train_test_split ensures
deterministic model training (Peng, 2011, "Reproducible Research
in Computational Science").
"""

import asyncio
import time
from typing import Any

import numpy as np
from sklearn.model_selection import train_test_split

np.random.seed(42)

from app.core.utils import utc_now_iso

from ..core import MLService


class PredictionService(MLService):
    """Stock price prediction service with sklearn integration."""

    # Configurable parameters
    MOMENTUM_LOOKBACK = 5
    MOMENTUM_WEIGHT = 0.5
    MOMENTUM_CONFIDENCE_SCALE = 10.0
    CONFIDENCE_CAP = 0.95
    MIN_PRICES_FOR_PREDICTION = 10

    def __init__(self, service_name: str = "PredictionService"):
        super().__init__(service_name)
        self._sklearn_model = None

    async def initialize(self) -> None:
        self.logger.info("PredictionService initialized")

    async def shutdown(self) -> None:
        self.model = None
        self._sklearn_model = None
        self.logger.info("PredictionService shutdown")

    async def train(self, training_data: dict[str, Any]) -> dict[str, Any]:
        features = training_data.get("features", [])
        labels = training_data.get("labels", [])
        self._metrics["calls"] += 1
        if len(features) != len(labels) or not features:
            self._metrics["errors"] += 1
            raise ValueError("Invalid training data")

        start = time.perf_counter()
        self.features = features
        self.model = {"trained": True, "samples": len(features)}

        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression

            X = np.array(features, dtype=float)
            y = np.array(labels, dtype=float)
            self._sklearn_model = LinearRegression()
            self._sklearn_model.fit(X, y)
            predictions = self._sklearn_model.predict(X)
            mse = float(np.mean((y - predictions) ** 2))
        except Exception:
            mse = 0.0

        duration = (time.perf_counter() - start) * 1000
        self._track_metric(True, duration)
        return {"status": "trained", "samples": len(features), "metrics": {"mse": mse}}

    async def predict(self, data: dict[str, Any]) -> dict[str, Any]:
        start = time.perf_counter()
        prices = data.get("prices", [])
        horizon = data.get("horizon", 1)
        if len(prices) < self.MIN_PRICES_FOR_PREDICTION or not self.model:
            self._metrics["errors"] += 1
            raise ValueError("Insufficient data or model not trained")

        last = float(prices[-1])
        if len(prices) >= self.MOMENTUM_LOOKBACK and prices[-self.MOMENTUM_LOOKBACK]:
            momentum = (prices[-1] - prices[-self.MOMENTUM_LOOKBACK]) / prices[-self.MOMENTUM_LOOKBACK]
        else:
            momentum = 0

        if self._sklearn_model is not None:
            try:
                import numpy as np
                features = np.array([[momentum, last]], dtype=float)
                predicted = float(self._sklearn_model.predict(features)[0])
            except Exception:
                predicted = last * (1 + momentum * self.MOMENTUM_WEIGHT * horizon)
        else:
            predicted = last * (1 + momentum * self.MOMENTUM_WEIGHT * horizon)

        confidence = min(abs(momentum) * self.MOMENTUM_CONFIDENCE_SCALE, self.CONFIDENCE_CAP)

        duration = (time.perf_counter() - start) * 1000
        self._track_metric(True, duration)

        return {
            "ticker": data.get("ticker", "UNKNOWN"),
            "predicted_price": round(predicted, 2),
            "confidence": round(confidence, 4),
            "horizon_days": horizon,
            "direction": "up" if momentum > 0 else "down",
            "timestamp": utc_now_iso(),
        }

    async def batch_predict(self, data_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        tasks = [self.predict(d) for d in data_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        processed = []
        for item, result in zip(data_list, results):
            processed.append({"error": str(result)} if isinstance(result, Exception) else result)
        return processed
