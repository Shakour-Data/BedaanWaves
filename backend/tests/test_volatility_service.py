"""Unit tests for Tier 3 VolatilityService."""

import pytest

from app.services.analysis.volatility_service import VolatilityService

pytestmark = pytest.mark.unit


class TestVolatilityServiceInitialization:
    def test_default_service_name(self):
        service = VolatilityService()
        assert service.service_name == "VolatilityService"

    async def test_initialize_logs(self, caplog):
        service = VolatilityService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "VolatilityService initialized" in caplog.text

    async def test_shutdown_logs(self, caplog):
        service = VolatilityService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.shutdown()
        assert "VolatilityService shutdown" in caplog.text


class TestAnalyze:
    async def test_insufficient_data_returns_error(self):
        service = VolatilityService()
        result = await service.analyze({"prices": [1, 2, 3, 4, 5]})
        assert "error" in result
        assert result["error"] == "Insufficient price data"

    async def test_valid_data_returns_volatility(self):
        service = VolatilityService()
        prices = [100 + i + (i % 3) for i in range(30)]
        result = await service.analyze({
            "prices": prices,
            "ticker": "TEST",
        })
        assert result["ticker"] == "TEST"
        assert "volatility" in result
        assert "historical" in result["volatility"]
        assert "annualized" in result["volatility"]
        assert "short_term" in result["volatility"]
        assert "long_term" in result["volatility"]
        assert "regime" in result["volatility"]

    async def test_volatility_regime_values(self):
        service = VolatilityService()
        regimes = ["high_volatility", "elevated_volatility", "normal_volatility", "low_volatility"]
        result = await service.analyze({"prices": [100 + i for i in range(30)]})
        assert result["volatility"]["regime"] in regimes


class TestHistoricalVolatility:
    async def test_basic_calculation(self):
        service = VolatilityService()
        returns = [0.01, -0.02, 0.015, -0.005, 0.02] * 6
        vol = service._calculate_historical_volatility(returns)
        assert vol > 0

    async def test_single_return(self):
        service = VolatilityService()
        assert service._calculate_historical_volatility([0.01]) == 0.0

    async def test_constant_returns(self):
        service = VolatilityService()
        returns = [0.01] * 10
        assert service._calculate_historical_volatility(returns) == 0.0

    async def test_annualized_volatility(self):
        service = VolatilityService()
        returns = [0.01, -0.02, 0.015] * 10
        hist = service._calculate_historical_volatility(returns)
        annual = service._calculate_annualized_volatility(returns)
        assert annual == pytest.approx(hist * (252 ** 0.5))

    async def test_short_term_volatility(self):
        service = VolatilityService()
        returns = [0.01, -0.02, 0.015, -0.005, 0.02, 0.01, -0.01, 0.03, -0.02, 0.01]
        short = service._calculate_short_term_volatility(returns)
        assert short >= 0

    async def test_long_term_volatility(self):
        service = VolatilityService()
        returns = [0.01 + i * 0.001 for i in range(30)]
        long_vol = service._calculate_long_term_volatility(returns)
        assert long_vol >= 0


class TestVolatilityRegime:
    async def test_high_volatility(self):
        service = VolatilityService()
        calm = [0.01, -0.01, 0.01, -0.01, 0.01] * 20
        turbulent = [0.4, -0.45, 0.35, -0.4, 0.3] * 3
        returns = calm + turbulent
        regime = service._detect_volatility_regime(returns)
        assert regime in ("high_volatility", "elevated_volatility")

    async def test_normal_volatility(self):
        service = VolatilityService()
        returns = [0.01, -0.01, 0.01, -0.01, 0.01] * 6
        regime = service._detect_volatility_regime(returns)
        assert regime == "normal_volatility"


class TestForecastVolatility:
    async def test_mean_reversion_forecast(self):
        service = VolatilityService()
        current = 0.3
        mean = 0.2
        forecasts = await service.forecast_volatility(current, mean, periods=5)
        assert len(forecasts) == 5
        assert forecasts[0] == pytest.approx(current * 0.9 + mean * 0.1)
        assert forecasts[-1] == pytest.approx(mean, rel=0.5)

    async def test_zero_periods(self):
        service = VolatilityService()
        forecasts = await service.forecast_volatility(0.3, 0.2, periods=0)
        assert len(forecasts) == 0


class TestDetectVolatilityClusters:
    async def test_no_clusters(self):
        service = VolatilityService()
        returns = [0.01] * 20
        clusters = await service.detect_volatility_clusters(returns, threshold=2.0)
        assert len(clusters) == 0

    async def test_single_cluster(self):
        service = VolatilityService()
        normal = [0.01] * 10
        spike = [0.1, -0.09, 0.11, -0.08]
        rest = [0.01] * 6
        returns = normal + spike + rest
        clusters = await service.detect_volatility_clusters(returns, threshold=2.0)
        assert len(clusters) == 1
        assert clusters[0]["start"] == 10
        assert clusters[0]["end"] == 14

    async def test_empty_returns(self):
        service = VolatilityService()
        clusters = await service.detect_volatility_clusters([])
        assert len(clusters) == 0
