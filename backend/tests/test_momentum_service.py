"""Unit tests for Tier 3 MomentumService."""

import pytest

from app.services.analysis.momentum_service import MomentumService

pytestmark = pytest.mark.unit


class TestMomentumServiceInitialization:
    def test_default_service_name(self):
        service = MomentumService()
        assert service.service_name == "MomentumService"

    async def test_initialize_logs(self, caplog):
        service = MomentumService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "MomentumService initialized" in caplog.text

    async def test_shutdown_logs(self, caplog):
        service = MomentumService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.shutdown()
        assert "MomentumService shutdown" in caplog.text


class TestAnalyze:
    async def test_insufficient_data_returns_error(self):
        service = MomentumService()
        result = await service.analyze({"prices": [1, 2, 3]})
        assert "error" in result
        assert result["error"] == "Insufficient price data"

    async def test_valid_data_returns_momentum(self):
        service = MomentumService()
        prices = [100 + i for i in range(40)]
        result = await service.analyze({
            "prices": prices,
            "ticker": "TEST",
        })
        assert result["ticker"] == "TEST"
        assert "momentum" in result
        assert "strength" in result["momentum"]
        assert "direction" in result["momentum"]
        assert "acceleration" in result["momentum"]
        assert "reversal_probability" in result["momentum"]


class TestMomentumStrength:
    async def test_bullish_strength(self):
        service = MomentumService()
        prices = [100.0] * 20 + [110.0, 112.0, 115.0, 118.0, 120.0]
        strength = service._calculate_momentum_strength(prices)
        assert strength > 0

    async def test_bearish_strength(self):
        service = MomentumService()
        prices = [100.0 + i for i in range(30)] + [70.0 + i for i in range(10)]
        prices.reverse()
        strength = service._calculate_momentum_strength(prices)
        assert strength < 0

    async def test_neutral_strength(self):
        service = MomentumService()
        prices = [100.0 + (i % 2) for i in range(40)]
        strength = service._calculate_momentum_strength(prices)
        assert isinstance(strength, float)

    async def test_insufficient_prices(self):
        service = MomentumService()
        assert service._calculate_momentum_strength([1.0, 2.0, 3.0]) == 0.0


class TestMomentumDirection:
    async def test_strong_bullish(self):
        service = MomentumService()
        prices = [100.0] * 20 + [120.0, 122.0, 125.0, 128.0, 130.0]
        assert service._determine_momentum_direction(prices) == "strong_bullish"

    async def test_bullish(self):
        service = MomentumService()
        prices = [100.0] * 20 + [100.0, 100.3, 100.6, 100.9, 101.2, 101.5]
        assert service._determine_momentum_direction(prices) == "bullish"

    async def test_neutral(self):
        service = MomentumService()
        prices = [100.0 + (i % 3 - 1) for i in range(40)]
        assert service._determine_momentum_direction(prices) == "neutral"

    async def test_strong_bearish(self):
        service = MomentumService()
        prices = [100.0 + i for i in range(30)] + [80.0, 78.0, 75.0, 72.0, 70.0]
        assert service._determine_momentum_direction(prices) == "strong_bearish"

    async def test_bearish(self):
        service = MomentumService()
        prices = [100.0] * 26 + [100.0, 99.8, 99.6, 99.4, 99.2, 99.0, 98.8, 98.6, 98.4, 98.2]
        assert service._determine_momentum_direction(prices) == "bearish"


class TestAcceleration:
    async def test_positive_acceleration(self):
        service = MomentumService()
        prices = [100.0, 101.0, 103.0, 106.0, 110.0, 116.0, 120.0, 125.0, 130.0, 136.0, 143.0]
        acc = service._calculate_acceleration(prices)
        assert acc > 0

    async def test_negative_acceleration(self):
        service = MomentumService()
        prices = [110.0, 105.0, 100.0, 95.0, 90.0, 85.0, 80.0, 75.0, 70.0, 65.0, 50.0]
        acc = service._calculate_acceleration(prices)
        assert acc < 0

    async def test_insufficient_prices(self):
        service = MomentumService()
        assert service._calculate_acceleration([1.0, 2.0]) == 0.0


class TestReversalProbability:
    async def test_at_high_extreme(self):
        service = MomentumService()
        prices = [100.0] * 15 + [120.0] * 5
        prob = service._estimate_reversal_probability(prices)
        assert prob == 60.0

    async def test_at_low_extreme(self):
        service = MomentumService()
        prices = [80.0] * 5 + [100.0] * 15
        prob = service._estimate_reversal_probability(prices)
        assert prob == 60.0

    async def test_not_at_extreme(self):
        service = MomentumService()
        prices = [100.0 + (i % 5) for i in range(30)]
        prices[-1] = 102.0
        prob = service._estimate_reversal_probability(prices)
        assert prob == 40.0

    async def test_insufficient_prices(self):
        service = MomentumService()
        assert service._estimate_reversal_probability([1.0, 2.0]) == 50.0
