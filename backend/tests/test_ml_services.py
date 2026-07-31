"""
Comprehensive unit tests for Tier 4 ML Services.

Tests cover: PredictionService, RecommendationService, AnomalyDetectionService,
PatternRecognitionService, and PortfolioOptimizationService.

Uses pytest-asyncio for async testing and pytest-mock for external dependency isolation.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ml.prediction_service import PredictionService
from app.services.ml.recommendation_service import RecommendationService
from app.services.ml.anomaly_detection_service import AnomalyDetectionService
from app.services.ml.pattern_recognition_service import PatternRecognitionService
from app.services.ml.portfolio_optimization_service import PortfolioOptimizationService


class TestPredictionService:
    """Unit tests for PredictionService."""

    @pytest.fixture
    def service(self):
        return PredictionService()

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        await service.initialize()
        assert service.service_name == "PredictionService"
        assert service.model is None

    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        await service.initialize()
        service.model = {"trained": True}
        await service.shutdown()
        assert service.model is None

    @pytest.mark.asyncio
    async def test_train_valid_data(self, service):
        await service.initialize()
        training_data = {
            "features": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            "labels": [10, 20, 30]
        }
        result = await service.train(training_data)
        assert result["status"] == "trained"
        assert result["samples"] == 3
        assert service.model["trained"] is True

    @pytest.mark.asyncio
    async def test_train_invalid_data_mismatched_features_labels(self, service):
        await service.initialize()
        training_data = {
            "features": [[1, 2], [3, 4]],
            "labels": [10, 20, 30]
        }
        with pytest.raises(ValueError, match="Invalid training data"):
            await service.train(training_data)

    @pytest.mark.asyncio
    async def test_train_invalid_data_empty_features(self, service):
        await service.initialize()
        training_data = {"features": [], "labels": []}
        with pytest.raises(ValueError, match="Invalid training data"):
            await service.train(training_data)

    @pytest.mark.asyncio
    async def test_predict_insufficient_data(self, service):
        await service.initialize()
        await service.train({"features": [[1] * 10], "labels": [1]})
        predict_data = {"prices": [100], "ticker": "TEST"}
        with pytest.raises(ValueError, match="Insufficient data"):
            await service.predict(predict_data)

    @pytest.mark.asyncio
    async def test_predict_model_not_trained(self, service):
        await service.initialize()
        predict_data = {"prices": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109], "ticker": "TEST"}
        with pytest.raises(ValueError, match="model not trained"):
            await service.predict(predict_data)

    @pytest.mark.asyncio
    async def test_predict_success_upward(self, service):
        await service.initialize()
        prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 120]
        await service.train({"features": [[p] for p in prices], "labels": [1] * len(prices)})
        result = await service.predict({"prices": prices, "ticker": "TEST", "horizon": 1})
        assert result["ticker"] == "TEST"
        assert result["direction"] == "up"
        assert result["confidence"] > 0
        assert result["horizon_days"] == 1
        assert "predicted_price" in result

    @pytest.mark.asyncio
    async def test_predict_success_downward(self, service):
        await service.initialize()
        prices = [120, 118, 116, 114, 112, 110, 108, 106, 104, 100]
        await service.train({"features": [[p] for p in prices], "labels": [1] * len(prices)})
        result = await service.predict({"prices": prices, "ticker": "TEST"})
        assert result["direction"] == "down"
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_predict_custom_horizon(self, service):
        await service.initialize()
        prices = [100] * 10
        await service.train({"features": [[100]], "labels": [1]})
        result = await service.predict({"prices": prices, "ticker": "TEST", "horizon": 7})
        assert result["horizon_days"] == 7

    @pytest.mark.asyncio
    async def test_batch_predict_success(self, service):
        await service.initialize()
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 110]
        await service.train({"features": [[p] for p in prices], "labels": [1] * len(prices)})
        data_list = [
            {"prices": prices, "ticker": "AAPL"},
            {"prices": prices, "ticker": "GOOG"}
        ]
        results = await service.batch_predict(data_list)
        assert len(results) == 2
        assert all(isinstance(r, dict) for r in results)
        assert results[0]["ticker"] == "AAPL"
        assert results[1]["ticker"] == "GOOG"

    @pytest.mark.asyncio
    async def test_batch_predict_with_exceptions(self, service):
        await service.initialize()
        await service.train({"features": [[100]], "labels": [1]})
        data_list = [
            {"prices": [100], "ticker": "AAPL"},
            {"prices": [100] * 10, "ticker": "GOOG"}
        ]
        results = await service.batch_predict(data_list)
        assert len(results) == 2
        assert "error" in results[0]

    @pytest.mark.asyncio
    async def test_health_check(self, service):
        await service.initialize()
        result = await service.health_check()
        assert result["service"] == "PredictionService"
        assert result["status"] == "healthy"
        assert "uptime_seconds" in result
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, service):
        await service.initialize()
        await service.train({"features": [[100]], "labels": [1]})
        result = await service.predict({"prices": [100] * 10, "ticker": "TEST"})
        metrics = service.get_metrics()
        assert metrics["calls"] >= 1
        assert metrics["errors"] == 0


class TestRecommendationService:
    """Unit tests for RecommendationService."""

    @pytest.fixture
    def service(self):
        return RecommendationService()

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        await service.initialize()
        assert service.service_name == "RecommendationService"

    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        await service.initialize()
        await service.shutdown()
        assert service.model is None

    @pytest.mark.asyncio
    async def test_predict_strong_buy(self, service):
        await service.initialize()
        data = {
            "ticker": "TEST",
            "fundamental": {"pe_ratio": 10},
            "technical": {"momentum": 0.8},
            "risk": {"sharpe_ratio": 1.5}
        }
        result = await service.predict(data)
        assert result["recommendation"] == "STRONG_BUY"
        assert result["score"] > 70
        assert "factors" in result

    @pytest.mark.asyncio
    async def test_predict_buy(self, service):
        await service.initialize()
        data = {
            "ticker": "TEST",
            "fundamental": {"pe_ratio": 15},
            "technical": {"momentum": 0.5},
            "risk": {"sharpe_ratio": 0.8}
        }
        result = await service.predict(data)
        assert result["recommendation"] == "BUY"
        assert 50 < result["score"] <= 70

    @pytest.mark.asyncio
    async def test_predict_hold(self, service):
        await service.initialize()
        data = {
            "ticker": "TEST",
            "fundamental": {"pe_ratio": 25},
            "technical": {"momentum": 0.2},
            "risk": {"sharpe_ratio": 0.3}
        }
        result = await service.predict(data)
        assert result["recommendation"] == "HOLD"
        assert 40 < result["score"] <= 50

    @pytest.mark.asyncio
    async def test_predict_sell(self, service):
        await service.initialize()
        data = {
            "ticker": "TEST",
            "fundamental": {"pe_ratio": 35},
            "technical": {"momentum": 0.0},
            "risk": {"sharpe_ratio": 0.0}
        }
        result = await service.predict(data)
        assert result["recommendation"] == "SELL"
        assert 25 < result["score"] <= 40

    @pytest.mark.asyncio
    async def test_predict_strong_sell(self, service):
        await service.initialize()
        data = {
            "ticker": "TEST",
            "fundamental": {"pe_ratio": 50},
            "technical": {"momentum": -0.5},
            "risk": {"sharpe_ratio": -0.5}
        }
        result = await service.predict(data)
        assert result["recommendation"] == "STRONG_SELL"
        assert result["score"] <= 25

    @pytest.mark.asyncio
    async def test_predict_default_values(self, service):
        await service.initialize()
        data = {"ticker": "TEST"}
        result = await service.predict(data)
        assert result["ticker"] == "TEST"
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_predict_score_calculation_accuracy(self, service):
        await service.initialize()
        data = {
            "ticker": "TEST",
            "fundamental": {"pe_ratio": 10},
            "technical": {"momentum": 0.5},
            "risk": {"sharpe_ratio": 1.0}
        }
        result = await service.predict(data)
        expected_fundamental = max(0, 100 - 10) * 0.3
        expected_risk = max(0, 1.0 * 20) * 0.3
        expected_momentum = max(0, 0.5 * 10) * 0.4
        expected_score = expected_fundamental + expected_risk + expected_momentum
        assert abs(result["score"] - expected_score) < 0.01

    @pytest.mark.asyncio
    async def test_confidence_capped_at_0_95(self, service):
        await service.initialize()
        data = {
            "ticker": "TEST",
            "fundamental": {"pe_ratio": 0},
            "technical": {"momentum": 10},
            "risk": {"sharpe_ratio": 10}
        }
        result = await service.predict(data)
        assert result["confidence"] <= 0.95

    @pytest.mark.asyncio
    async def test_train_integration(self, service):
        await service.initialize()
        training_data = {
            "labels": [1, 0, 1, 1, 0]
        }
        result = await service.train(training_data)
        assert result["status"] == "trained"
        assert result["labels"] == 5


class TestAnomalyDetectionService:
    """Unit tests for AnomalyDetectionService."""

    @pytest.fixture
    def service(self):
        return AnomalyDetectionService()

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        await service.initialize()
        assert service.service_name == "AnomalyDetectionService"

    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        await service.initialize()
        await service.shutdown()
        assert service.model is None

    @pytest.mark.asyncio
    async def test_train_calculates_statistics(self, service):
        await service.initialize()
        values = [100, 102, 98, 101, 99, 103, 97, 104, 96, 105]
        result = await service.train({"values": values})
        assert result["status"] == "trained"
        assert "mean" in result
        assert "std" in result

    @pytest.mark.asyncio
    async def test_train_empty_data_raises_error(self, service):
        await service.initialize()
        with pytest.raises(ValueError, match="No training data provided"):
            await service.train({"values": []})

    @pytest.mark.asyncio
    async def test_predict_anomaly_detected(self, service):
        await service.initialize()
        values = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        await service.train({"values": values})
        result = await service.predict({
            "ticker": "TEST",
            "prices": values,
            "returns": [50],
            "z_threshold": 2.0
        })
        assert result["is_anomaly"] is True
        assert result["severity"] in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_predict_no_anomaly(self, service):
        await service.initialize()
        values = [100, 101, 99, 100, 102, 98, 101, 100, 99, 100]
        await service.train({"values": values})
        result = await service.predict({
            "ticker": "TEST",
            "prices": values,
            "returns": [0.1]
        })
        assert result["is_anomaly"] is False

    @pytest.mark.asyncio
    async def test_predict_insufficient_data(self, service):
        await service.initialize()
        await service.train({"values": [100, 101, 102]})
        with pytest.raises(ValueError, match="Insufficient data"):
            await service.predict({"ticker": "TEST", "prices": [100], "returns": [1]})

    @pytest.mark.asyncio
    async def test_predict_model_not_trained(self, service):
        await service.initialize()
        with pytest.raises(ValueError, match="model not trained"):
            await service.predict({"ticker": "TEST", "prices": [1] * 10, "returns": [1]})

    @pytest.mark.asyncio
    async def test_predict_uses_returns_over_prices(self, service):
        await service.initialize()
        await service.train({"values": [100] * 10})
        result = await service.predict({
            "ticker": "TEST",
            "prices": [i for i in range(100, 110)],
            "returns": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        })
        assert result["ticker"] == "TEST"
        assert "z_score" in result

    @pytest.mark.asyncio
    async def test_batch_detect(self, service):
        await service.initialize()
        values = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
        await service.train({"values": values})
        data_list = [
            {"ticker": "AAPL", "prices": values, "returns": [0.1]},
            {"ticker": "GOOG", "prices": values, "returns": [0.2]}
        ]
        results = await service.batch_detect(data_list)
        assert len(results) == 2
        assert all(isinstance(r, dict) for r in results)


class TestPatternRecognitionService:
    """Unit tests for PatternRecognitionService."""

    @pytest.fixture
    def service(self):
        return PatternRecognitionService()

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        await service.initialize()
        assert service.service_name == "PatternRecognitionService"

    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        await service.initialize()
        await service.shutdown()
        assert service.model is None

    @pytest.mark.asyncio
    async def test_train(self, service):
        await service.initialize()
        training_data = {"patterns": ["double_top", "head_and_shoulders", "triangle"]}
        result = await service.train(training_data)
        assert result["status"] == "trained"
        assert result["patterns"] == 3

    @pytest.mark.asyncio
    async def test_predict_resistance_test(self, service):
        await service.initialize()
        prices = [95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 115]
        result = await service.predict({"ticker": "TEST", "prices": prices})
        assert result["pattern"] == "resistance_test"
        assert result["probability"] == 0.75
        assert result["current_price"] == prices[-1]

    @pytest.mark.asyncio
    async def test_predict_support_test(self, service):
        await service.initialize()
        prices = [110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 90]
        result = await service.predict({"ticker": "TEST", "prices": prices})
        assert result["pattern"] == "support_test"

    @pytest.mark.asyncio
    async def test_predict_continuation(self, service):
        await service.initialize()
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101]
        result = await service.predict({"ticker": "TEST", "prices": prices})
        assert result["pattern"] == "continuation"
        assert result["probability"] == 0.55

    @pytest.mark.asyncio
    async def test_predict_insufficient_data(self, service):
        await service.initialize()
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        with pytest.raises(ValueError, match="Insufficient data"):
            await service.predict({"ticker": "TEST", "prices": prices})

    @pytest.mark.asyncio
    async def test_detect_patterns_multiple(self, service):
        await service.initialize()
        prices = [100 + i for i in range(50)]
        patterns = await service.detect_patterns(prices)
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_predict_default_ticker(self, service):
        await service.initialize()
        prices = [100] * 20
        result = await service.predict({"prices": prices})
        assert result["ticker"] == "UNKNOWN"


class TestPortfolioOptimizationService:
    """Unit tests for PortfolioOptimizationService."""

    @pytest.fixture
    def service(self):
        return PortfolioOptimizationService()

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        await service.initialize()
        assert service.service_name == "PortfolioOptimizationService"

    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        await service.initialize()
        await service.shutdown()
        assert service.model is None

    @pytest.mark.asyncio
    async def test_predict_basic_allocation(self, service):
        await service.initialize()
        data = {
            "ticker": "PORT1",
            "assets": ["AAPL", "GOOG", "MSFT"],
            "expected_returns": {"AAPL": 0.1, "GOOG": 0.15, "MSFT": 0.12},
            "risks": {"AAPL": 0.2, "GOOG": 0.25, "MSFT": 0.18}
        }
        result = await service.predict(data)
        assert result["portfolio_id"] == "PORT1"
        assert "allocation" in result
        assert len(result["allocation"]) == 3
        total_weight = sum(result["allocation"].values())
        assert abs(total_weight - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_predict_empty_assets_raises_error(self, service):
        await service.initialize()
        with pytest.raises(ValueError, match="No assets provided"):
            await service.predict({"assets": []})

    @pytest.mark.asyncio
    async def test_predict_allocation_positive(self, service):
        await service.initialize()
        data = {
            "assets": ["AAPL", "GOOG"],
            "expected_returns": {"AAPL": 0.1, "GOOG": 0.1},
            "risks": {"AAPL": 0.2, "GOOG": 0.2}
        }
        result = await service.predict(data)
        assert all(w > 0 for w in result["allocation"].values())

    @pytest.mark.asyncio
    async def test_predict_expected_return_calculation(self, service):
        await service.initialize()
        data = {
            "assets": ["A", "B"],
            "expected_returns": {"A": 0.1, "B": 0.2},
            "risks": {"A": 0.15, "B": 0.25}
        }
        result = await service.predict(data)
        assert "expected_return" in result
        assert isinstance(result["expected_return"], float)

    @pytest.mark.asyncio
    async def test_predict_sharpe_ratio_calculation(self, service):
        await service.initialize()
        data = {
            "assets": ["A", "B"],
            "expected_returns": {"A": 0.15, "B": 0.2},
            "risks": {"A": 0.1, "B": 0.15}
        }
        result = await service.predict(data)
        assert "sharpe_ratio" in result
        assert isinstance(result["sharpe_ratio"], float)

    @pytest.mark.asyncio
    async def test_predict_missing_asset_defaults(self, service):
        await service.initialize()
        data = {
            "assets": ["A", "B"],
            "expected_returns": {"A": 0.1},
            "risks": {"A": 0.1}
        }
        result = await service.predict(data)
        assert result["expected_return"] is not None

    @pytest.mark.asyncio
    async def test_predict_default_portfolio_id(self, service):
        await service.initialize()
        data = {
            "assets": ["A"],
            "expected_returns": {"A": 0.1},
            "risks": {"A": 0.1}
        }
        result = await service.predict(data)
        assert result["portfolio_id"] is None

    @pytest.mark.asyncio
    async def test_train_integration(self, service):
        await service.initialize()
        result = await service.train({"dummy": "data"})
        assert result["status"] == "trained"


class TestMLServiceIntegration:
    """Integration tests for ML services lifecycle."""

    @pytest.mark.asyncio
    async def test_service_lifecycle_full_flow(self):
        services = [
            PredictionService(),
            RecommendationService(),
            AnomalyDetectionService(),
            PatternRecognitionService(),
            PortfolioOptimizationService()
        ]
        for service in services:
            await service.initialize()
            health = await service.health_check()
            assert health["status"] == "healthy"
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_multiple_prediction_calls(self):
        service = PredictionService()
        await service.initialize()
        await service.train({"features": [[100]], "labels": [1]})
        for i in range(5):
            result = await service.predict({"prices": [100] * 10, "ticker": f"TEST{i}"})
            assert result["ticker"] == f"TEST{i}"
        metrics = service.get_metrics()
        assert metrics["calls"] == 5