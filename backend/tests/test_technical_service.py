"""Unit tests for Tier 3 TechnicalAnalysisService."""

import math

import pytest

from app.services.analysis.technical_service import TechnicalAnalysisService

pytestmark = pytest.mark.unit


class TestTechnicalAnalysisServiceInitialization:
    def test_default_service_name(self):
        service = TechnicalAnalysisService()
        assert service.service_name == "TechnicalAnalysisService"

    async def test_initialize_logs(self, caplog):
        service = TechnicalAnalysisService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "TechnicalAnalysisService initialized" in caplog.text

    async def test_shutdown_logs(self, caplog):
        service = TechnicalAnalysisService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.shutdown()
        assert "TechnicalAnalysisService shutdown" in caplog.text


class TestAnalyze:
    async def test_insufficient_data_returns_error(self):
        service = TechnicalAnalysisService()
        result = await service.analyze({"prices": [1, 2, 3]})
        assert "error" in result
        assert result["error"] == "Insufficient price data"

    async def test_valid_data_returns_indicators(self):
        service = TechnicalAnalysisService()
        prices = [100 + i for i in range(100)]
        highs = [p + 1 for p in prices]
        lows = [p - 1 for p in prices]
        volumes = [1000 + i * 10 for i in range(100)]

        result = await service.analyze({
            "prices": prices,
            "highs": highs,
            "lows": lows,
            "volumes": volumes,
            "ticker": "TEST",
            "market": "TSE",
            "current_price": prices[-1],
        })

        assert result["ticker"] == "TEST"
        assert result["market"] == "TSE"
        assert "indicators" in result
        assert "sma_20" in result["indicators"]
        assert "rsi_14" in result["indicators"]
        assert "bollinger_bands" in result["indicators"]
        assert "adx_14" in result["indicators"]
        assert "obv" in result["indicators"]
        assert "pivot_points" in result["indicators"]
        assert "awesome_oscillator" in result["indicators"]

    async def test_missing_volumes_skips_volume_indicators(self):
        service = TechnicalAnalysisService()
        prices = [100 + i for i in range(100)]
        highs = [p + 1 for p in prices]
        lows = [p - 1 for p in prices]

        result = await service.analyze({
            "prices": prices,
            "highs": highs,
            "lows": lows,
            "ticker": "TEST",
        })

        assert "obv" not in result["indicators"]
        assert "sma_20" in result["indicators"]
        assert "awesome_oscillator" in result["indicators"]


class TestMovingAverages:
    async def test_sma_basic(self):
        service = TechnicalAnalysisService()
        prices = [10, 20, 30, 40, 50]
        assert service._sma(prices, 3) == 40.0
        assert service._sma(prices, 5) == 30.0

    async def test_sma_insufficient_data(self):
        service = TechnicalAnalysisService()
        assert service._sma([1, 2], 5) == 0.0

    async def test_ema_basic(self):
        service = TechnicalAnalysisService()
        prices = [10.0] * 20
        assert service._ema(prices, 10) == 10.0

    async def test_ema_series(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(20)]
        series = service._ema_series(prices, 5)
        assert len(series) == 16

    async def test_wma_basic(self):
        service = TechnicalAnalysisService()
        prices = [10.0, 20.0, 30.0]
        expected = (10 * 1 + 20 * 2 + 30 * 3) / 6
        assert service._wma(prices, 3) == expected

    async def test_dema(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(30)]
        result = service._dema(prices, 10)
        assert isinstance(result, float)

    async def test_tema(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(30)]
        result = service._tema(prices, 10)
        assert isinstance(result, float)

    async def test_t3(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(60)]
        result = service._t3(prices, 10)
        assert isinstance(result, float)

    async def test_hull_ma(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(30)]
        result = service._hull_ma(prices, 10)
        assert isinstance(result, float)


class TestMomentumOscillators:
    async def test_rsi_basic(self):
        service = TechnicalAnalysisService()
        prices = [44, 44.5, 43.5, 44.8, 46.0, 45.5, 44.5, 45.0, 46.5, 47.0,
                  46.5, 46.0, 45.5, 46.0, 47.5, 48.0, 47.5, 47.0, 46.5, 47.0]
        rsi = service._rsi(prices, 14)
        assert 0 <= rsi <= 100

    async def test_rsi_insufficient_data(self):
        service = TechnicalAnalysisService()
        assert service._rsi([1, 2, 3], 14) == 50.0

    async def test_macd_basic(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(50)]
        result = service._macd(prices)
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    async def test_stochastic(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(20)]
        result = service._stochastic(prices, 14)
        assert "k" in result
        assert "d" in result

    async def test_kdj(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(20)]
        result = service._kdj(prices, 9)
        assert "k" in result
        assert "d" in result
        assert "j" in result

    async def test_cci(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(20)]
        result = service._cci(prices, 20)
        assert isinstance(result, float)

    async def test_williams_r(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(20)]
        result = service._williams_r(prices, 14)
        assert -100 <= result <= 0

    async def test_roc(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(20)]
        result = service._roc(prices, 12)
        assert isinstance(result, float)

    async def test_trix(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(30)]
        result = service._trix(prices, 15)
        assert isinstance(result, float)

    async def test_stoch_rsi(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(30)]
        result = service._stoch_rsi(prices, 14)
        assert "k" in result
        assert "d" in result

    async def test_price_oscillator(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(30)]
        result = service._price_oscillator(prices, 12, 26)
        assert isinstance(result, float)


class TestVolatilityIndicators:
    async def test_bollinger_bands(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(30)]
        result = service._bollinger_bands(prices, 20)
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        assert result["upper"] >= result["middle"] >= result["lower"]

    async def test_std_dev(self):
        service = TechnicalAnalysisService()
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        std = service._std_dev(values, 8)
        assert std > 0

    async def test_variance(self):
        service = TechnicalAnalysisService()
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        var = service._variance(values, 8)
        assert var > 0

    async def test_atr(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(20)]
        lows = [float(i - 1) for i in range(20)]
        closes = [float(i) for i in range(20)]
        result = service._atr(highs, lows, closes, 14)
        assert result >= 0

    async def test_kama(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(30)]
        result = service._kama(prices, 10)
        assert isinstance(result, float)

    async def test_donchian(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 2) for i in range(20)]
        lows = [float(i - 2) for i in range(20)]
        result = service._donchian(highs, lows, 20)
        assert "upper" in result
        assert "lower" in result
        assert "middle" in result


class TestTrendIndicators:
    async def test_adx(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(30)]
        lows = [float(i - 1) for i in range(30)]
        closes = [float(i) for i in range(30)]
        result = service._adx(highs, lows, closes, 14)
        assert "adx" in result
        assert "plus_di" in result
        assert "minus_di" in result

    async def test_ichimoku(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(60)]
        lows = [float(i - 1) for i in range(60)]
        closes = [float(i) for i in range(60)]
        result = service._ichimoku(highs, lows, closes)
        assert "tenkan_sen" in result
        assert "kijun_sen" in result
        assert "senkou_a" in result
        assert "senkou_b" in result
        assert "chikou_span" in result

    async def test_parabolic_sar(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(20)]
        lows = [float(i - 1) for i in range(20)]
        closes = [float(i) for i in range(20)]
        result = service._parabolic_sar(highs, lows, closes)
        assert "sar" in result
        assert "trend" in result
        assert result["trend"] in ("up", "down", "neutral")

    async def test_aroon(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(30)]
        lows = [float(i - 1) for i in range(30)]
        result = service._aroon(highs, lows, 25)
        assert "up" in result
        assert "down" in result
        assert "oscillator" in result

    async def test_supertrend(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(20)]
        lows = [float(i - 1) for i in range(20)]
        closes = [float(i) for i in range(20)]
        result = service._supertrend(highs, lows, closes, 10, 3.0)
        assert "supertrend" in result
        assert "trend" in result


class TestVolumeIndicators:
    async def test_obv(self):
        service = TechnicalAnalysisService()
        prices = [10.0, 11.0, 10.5, 12.0, 11.5, 13.0]
        volumes = [1000.0, 1500.0, 800.0, 2000.0, 1200.0, 2500.0]
        result = service._obv(prices, volumes)
        assert isinstance(result, float)

    async def test_cmf(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(20)]
        lows = [float(i - 1) for i in range(20)]
        closes = [float(i) for i in range(20)]
        volumes = [1000.0] * 20
        result = service._cmf(highs, lows, closes, volumes, 20)
        assert isinstance(result, float)

    async def test_ad_line(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(20)]
        lows = [float(i - 1) for i in range(20)]
        closes = [float(i) for i in range(20)]
        volumes = [1000.0] * 20
        result = service._ad_line(highs, lows, closes, volumes)
        assert isinstance(result, float)

    async def test_vpt(self):
        service = TechnicalAnalysisService()
        prices = [float(i) for i in range(20)]
        volumes = [1000.0] * 20
        result = service._vpt(prices, volumes)
        assert isinstance(result, float)

    async def test_mfi(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(20)]
        lows = [float(i - 1) for i in range(20)]
        closes = [float(i) for i in range(20)]
        volumes = [1000.0] * 20
        result = service._mfi(highs, lows, closes, volumes, 14)
        assert 0 <= result <= 100

    async def test_ease_of_movement(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(20)]
        lows = [float(i - 1) for i in range(20)]
        volumes = [1000000.0] * 20
        result = service._ease_of_movement(highs, lows, volumes, 14)
        assert isinstance(result, float)


class TestSupportResistance:
    async def test_pivot_points(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(20)]
        lows = [float(i - 1) for i in range(20)]
        closes = [float(i) for i in range(20)]
        result = service._pivot_points(highs, lows, closes)
        assert "pivot" in result
        assert "r1" in result
        assert "s1" in result

    async def test_fibonacci(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 5) for i in range(20)]
        lows = [float(i - 5) for i in range(20)]
        closes = [float(i) for i in range(20)]
        result = service._fibonacci(highs, lows, closes)
        assert "level_0" in result
        assert "level_236" in result
        assert "level_382" in result
        assert "level_618" in result
        assert "level_100" in result


class TestExtraOscillators:
    async def test_awesome_oscillator(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(40)]
        lows = [float(i - 1) for i in range(40)]
        result = service._awesome_oscillator(highs, lows)
        assert "ao" in result

    async def test_ultimate_oscillator(self):
        service = TechnicalAnalysisService()
        highs = [float(i + 1) for i in range(30)]
        lows = [float(i - 1) for i in range(30)]
        closes = [float(i) for i in range(30)]
        volumes = [1000.0] * 30
        result = service._ultimate_oscillator(highs, lows, closes, volumes)
        assert 0 <= result <= 100
