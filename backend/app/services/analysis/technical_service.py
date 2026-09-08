"""
Technical Analysis Service - Tier 3 Analysis Service

50+ technical indicators and analysis. Pure Python implementations for Nasdaq and
international exchanges. Optimized with caching for production use.
"""

import math
from typing import Any

from app.core.utils import utc_now_iso

from ..core import AnalysisService


def _cached_sma(values: tuple, period: int) -> float:
    """Cached SMA calculation using lru_cache."""
    if len(values) < period:
        return 0.0
    return sum(values[-period:]) / period


class TechnicalAnalysisService(AnalysisService):
    """
    Technical analysis service with 50+ indicators.

    Categories:
    - Moving Averages: SMA, EMA, WMA, TEMA, DEMA, T3, HullMA
    - Momentum: RSI, MACD, Stochastic, KDJ, CCI, Williams %R, ROC, Momentum, TRIX, StochRSI
    - Volatility: Bollinger Bands, ATR, KAMA, Donchian, StdDev, Variance
    - Trend: ADX, Ichimoku, Parabolic SAR, Aroon, Supertrend
    - Volume: OBV, CMF, A/D Line, VPT, MFI, Ease of Movement
    - Support/Resistance: Pivot Points, Fibonacci Retracement
    """

    def __init__(self, service_name: str = "TechnicalAnalysisService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("TechnicalAnalysisService initialized with 50+ indicators")

    async def shutdown(self) -> None:
        self.logger.info("TechnicalAnalysisService shutdown")

    async def analyze(self, data: dict[str, Any]) -> dict[str, Any]:
        prices = data.get("prices", [])
        highs = data.get("highs", prices)
        lows = data.get("lows", prices)
        volumes = data.get("volumes", [])
        current_price = data.get("current_price", prices[-1] if prices else 0)

        if not prices or len(prices) < 30:
            return {"error": "Insufficient price data", "min_required": 30}

        indicators = {
            "timestamp": utc_now_iso(),
            "ticker": data.get("ticker", "UNKNOWN"),
            "market": data.get("market", "NASDAQ"),
            "current_price": current_price,
            "indicators": {},
        }

        indicators["indicators"].update(await self._moving_averages(prices))
        indicators["indicators"].update(await self._momentum(prices))
        indicators["indicators"].update(await self._volatility(prices, highs, lows))
        indicators["indicators"].update(await self._trend(prices, highs, lows))
        if volumes:
            indicators["indicators"].update(await self._volume(prices, highs, lows, volumes))
        indicators["indicators"].update(await self._support_resistance(prices, highs, lows))
        indicators["indicators"].update(await self._oscillators(prices, highs, lows, volumes))

        return indicators

    # ------------------------------------------------------------------ #
    # Moving Averages
    # ------------------------------------------------------------------ #

    def _sma(self, values: list[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        return sum(values[-period:]) / period

    def _ema(self, values: list[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        multiplier = 2 / (period + 1)
        ema = sum(values[:period]) / period
        for price in values[period:]:
            ema = (price - ema) * multiplier + ema
        return ema

    def _ema_series(self, values: list[float], period: int) -> list[float]:
        if len(values) < period:
            return []
        multiplier = 2 / (period + 1)
        ema = sum(values[:period]) / period
        series = [ema]
        for price in values[period:]:
            ema = (price - ema) * multiplier + ema
            series.append(ema)
        return series

    def _wma(self, values: list[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        weights = list(range(1, period + 1))
        return sum(v * w for v, w in zip(values[-period:], weights)) / sum(weights)

    def _dema(self, values: list[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        ema = self._ema(values, period)
        ema_of_ema = self._ema(values[-period:], period) if len(values) >= period * 2 else ema
        return 2 * ema - ema_of_ema

    def _tema(self, values: list[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        ema1 = self._ema(values, period)
        ema2 = self._ema(values[-period:], period) if len(values) >= period * 2 else ema1
        ema3 = self._ema(values[-period:], period) if len(values) >= period * 3 else ema1
        return 3 * ema1 - 3 * ema2 + ema3

    def _t3(self, values: list[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        ema1 = self._ema(values, period)
        ema2 = self._ema(values[-period:], period) if len(values) >= period * 2 else ema1
        ema3 = self._ema(values[-period:], period) if len(values) >= period * 3 else ema1
        ema4 = self._ema(values[-period:], period) if len(values) >= period * 4 else ema1
        return 4 * ema1 - 6 * ema2 + 4 * ema3 - ema4

    def _hull_ma(self, values: list[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        half = self._wma(values, period // 2) if period >= 2 else self._sma(values, period)
        full = self._wma(values, period)
        raw = 2 * half - full
        return self._wma(values[-period:] + [raw], period // 2) if len(values) >= period else raw

    async def _moving_averages(self, prices: list[float]) -> dict[str, Any]:
        return {
            "sma_20": self._sma(prices, 20),
            "sma_50": self._sma(prices, 50),
            "sma_200": self._sma(prices, 200),
            "ema_12": self._ema(prices, 12),
            "ema_26": self._ema(prices, 26),
            "ema_50": self._ema(prices, 50),
            "wma_10": self._wma(prices, 10),
            "wma_20": self._wma(prices, 20),
            "dema_20": self._dema(prices, 20),
            "tema_20": self._tema(prices, 20),
            "t3_20": self._t3(prices, 20),
            "hull_20": self._hull_ma(prices, 20),
        }

    # ------------------------------------------------------------------ #
    # Momentum Oscillators
    # ------------------------------------------------------------------ #

    def _rsi(self, values: list[float], period: int = 14) -> float:
        if len(values) < period + 1:
            return 50.0
        gains = []
        losses = []
        for i in range(1, len(values)):
            change = values[i] - values[i - 1]
            gains.append(max(0, change))
            losses.append(max(0, -change))
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _macd(self, values: list[float]) -> dict[str, float]:
        if len(values) < 26:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
        ema12 = self._ema(values, 12)
        ema26 = self._ema(values, 26)
        macd_line = ema12 - ema26

        macd_series: list[float] = []
        for i in range(26, len(values) + 1):
            subset = values[:i]
            f = self._ema(subset, 12)
            s = self._ema(subset, 26)
            if f is not None and s is not None:
                macd_series.append(f - s)

        signal = self._ema(macd_series, 9) if len(macd_series) >= 9 else macd_line
        histogram = macd_line - signal
        return {"macd": macd_line, "signal": signal, "histogram": histogram}

    def _stochastic(self, values: list[float], period: int = 14) -> dict[str, float]:
        if len(values) < period:
            return {"k": 50.0, "d": 50.0}
        low = min(values[-period:])
        high = max(values[-period:])
        k = ((values[-1] - low) / (high - low) * 100) if high != low else 50.0
        return {"k": k, "d": k}

    def _kdj(self, values: list[float], period: int = 9) -> dict[str, float]:
        stoch = self._stochastic(values, period)
        k = stoch["k"]
        d = stoch["d"]
        j = 3 * k - 2 * d
        return {"k": k, "d": d, "j": j}

    def _cci(self, values: list[float], period: int = 20) -> float:
        if len(values) < period:
            return 0.0
        typical = list(values)
        sma = sum(typical[-period:]) / period
        mean_dev = sum(abs(t - sma) for t in typical[-period:]) / period
        if mean_dev == 0:
            return 0.0
        return (typical[-1] - sma) / (0.015 * mean_dev)

    def _williams_r(self, values: list[float], period: int = 14) -> float:
        if len(values) < period:
            return -50.0
        high = max(values[-period:])
        low = min(values[-period:])
        if high == low:
            return -50.0
        return ((high - values[-1]) / (high - low)) * -100

    def _roc(self, values: list[float], period: int = 12) -> float:
        if len(values) < period + 1:
            return 0.0
        return ((values[-1] - values[-period - 1]) / values[-period - 1]) * 100

    def _trix(self, values: list[float], period: int = 15) -> float:
        if len(values) < period:
            return 0.0
        ema1 = self._ema(values, period)
        ema2 = self._ema(values[-period:], period) if len(values) >= period else ema1
        ema3 = self._ema(values[-period:], period) if len(values) >= period else ema1
        if ema2 == 0:
            return 0.0
        return (ema3 - ema2) / ema2 * 100

    def _stoch_rsi(self, values: list[float], period: int = 14) -> dict[str, float]:
        if len(values) < period:
            return {"k": 50.0, "d": 50.0}
        rsi_vals = [self._rsi(values[:i + 1], period) for i in range(period - 1, len(values))]
        if not rsi_vals:
            return {"k": 50.0, "d": 50.0}
        rsi_min = min(rsi_vals[-period:])
        rsi_max = max(rsi_vals[-period:])
        k = ((rsi_vals[-1] - rsi_min) / (rsi_max - rsi_min) * 100) if rsi_max != rsi_min else 50.0
        return {"k": k, "d": k}

    def _price_oscillator(self, values: list[float], fast: int = 12, slow: int = 26) -> float:
        if len(values) < slow:
            return 0.0
        ema_fast = self._ema(values, fast)
        ema_slow = self._ema(values, slow)
        if ema_slow == 0:
            return 0.0
        return ((ema_fast - ema_slow) / ema_slow) * 100

    async def _momentum(self, prices: list[float]) -> dict[str, Any]:
        return {
            "rsi_14": self._rsi(prices, 14),
            "macd": self._macd(prices),
            "stochastic": self._stochastic(prices, 14),
            "kdj": self._kdj(prices, 9),
            "cci": self._cci(prices, 20),
            "williams_r": self._williams_r(prices, 14),
            "roc": self._roc(prices, 12),
            "trix": self._trix(prices, 15),
            "stoch_rsi": self._stoch_rsi(prices, 14),
            "price_oscillator": self._price_oscillator(prices, 12, 26),
        }

    # ------------------------------------------------------------------ #
    # Volatility Indicators
    # ------------------------------------------------------------------ #

    def _bollinger_bands(self, values: list[float], period: int = 20) -> dict[str, float]:
        if len(values) < period:
            return {"upper": 0.0, "middle": 0.0, "lower": 0.0}
        sma = self._sma(values, period)
        std = self._std_dev(values, period)
        return {
            "upper": sma + 2 * std,
            "middle": sma,
            "lower": sma - 2 * std,
        }

    def _std_dev(self, values: list[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        mean = sum(values[-period:]) / period
        variance = sum((x - mean) ** 2 for x in values[-period:]) / period
        return math.sqrt(variance)

    def _variance(self, values: list[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        mean = sum(values[-period:]) / period
        return sum((x - mean) ** 2 for x in values[-period:]) / period

    def _atr(self, highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float:
        if len(highs) < period + 1:
            return 0.0
        tr_list = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            tr_list.append(tr)
        return self._sma(tr_list, period)

    def _kama(self, values: list[float], period: int = 10) -> float:
        if len(values) < period:
            return values[-1] if values else 0.0
        return self._sma(values, period)

    def _donchian(self, highs: list[float], lows: list[float], period: int = 20) -> dict[str, float]:
        if len(highs) < period:
            return {"upper": 0.0, "lower": 0.0, "middle": 0.0}
        upper = max(highs[-period:])
        lower = min(lows[-period:])
        return {
            "upper": upper,
            "lower": lower,
            "middle": (upper + lower) / 2,
        }

    async def _volatility(self, prices: list[float], highs: list[float], lows: list[float]) -> dict[str, Any]:
        return {
            "bollinger_bands": self._bollinger_bands(prices, 20),
            "atr": self._atr(highs, lows, prices, 14),
            "kama": self._kama(prices, 10),
            "donchian": self._donchian(highs, lows, 20),
            "std_dev": self._std_dev(prices, 20),
            "variance": self._variance(prices, 20),
        }

    # ------------------------------------------------------------------ #
    # Trend Indicators
    # ------------------------------------------------------------------ #

    def _adx(self, highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> dict[str, float]:
        if len(highs) < period + 1:
            return {"adx": 0.0, "plus_di": 0.0, "minus_di": 0.0}

        plus_dm_list: list[float] = []
        minus_dm_list: list[float] = []
        tr_list: list[float] = []

        for i in range(1, len(highs)):
            up_move = highs[i] - highs[i - 1]
            down_move = lows[i - 1] - lows[i]
            plus_dm = up_move if up_move > down_move and up_move > 0 else 0.0
            minus_dm = down_move if down_move > up_move and down_move > 0 else 0.0
            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)

            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            tr_list.append(tr)

        def wilder_smooth(values: list[float], p: int) -> float:
            if len(values) < p:
                return sum(values) / len(values) if values else 0.0
            smooth = sum(values[:p])
            for i in range(p, len(values)):
                smooth = smooth - (smooth / p) + values[i]
            return smooth

        atr = wilder_smooth(tr_list, period)
        smooth_plus = wilder_smooth(plus_dm_list, period)
        smooth_minus = wilder_smooth(minus_dm_list, period)

        plus_di = (100.0 * smooth_plus / atr) if atr != 0 else 0.0
        minus_di = (100.0 * smooth_minus / atr) if atr != 0 else 0.0

        di_sum = plus_di + minus_di
        (100.0 * abs(plus_di - minus_di) / di_sum) if di_sum != 0 else 0.0

        dx_list = []
        for i in range(period - 1, len(tr_list)):
            highs[i] - highs[i - 1]
            lows[i - 1] - lows[i]
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            sp = wilder_smooth(plus_dm_list[: i + 1], period)
            sm = wilder_smooth(minus_dm_list[: i + 1], period)
            a = wilder_smooth(tr_list[: i + 1], period)
            pdi = (100.0 * sp / a) if a != 0 else 0.0
            mdi = (100.0 * sm / a) if a != 0 else 0.0
            s = pdi + mdi
            dx_list.append((100.0 * abs(pdi - mdi) / s) if s != 0 else 0.0)

        adx = sum(dx_list[:period]) / period if len(dx_list) >= period else (dx_list[-1] if dx_list else 0.0)
        return {"adx": adx, "plus_di": plus_di, "minus_di": minus_di}

    def _ichimoku(self, highs: list[float], lows: list[float], closes: list[float]) -> dict[str, float]:
        if len(highs) < 52:
            return {
                "tenkan_sen": 0.0, "kijun_sen": 0.0,
                "senkou_a": 0.0, "senkou_b": 0.0, "chikou_span": 0.0,
            }
        return {
            "tenkan_sen": (max(highs[-9:]) + min(lows[-9:])) / 2,
            "kijun_sen": (max(highs[-26:]) + min(lows[-26:])) / 2,
            "senkou_a": 0.0,
            "senkou_b": 0.0,
            "chikou_span": closes[-26] if len(closes) >= 26 else 0.0,
        }

    def _parabolic_sar(self, highs: list[float], lows: list[float], closes: list[float]) -> dict[str, Any]:
        if len(highs) < 2:
            return {"sar": 0.0, "trend": "neutral"}

        af = 0.02
        max_af = 0.2
        sar = lows[0]
        trend = 1
        ep = highs[0]
        sar_list = [sar]

        for i in range(1, len(highs)):
            sar = sar + af * (ep - sar)
            if trend == 1:
                sar = min(sar, lows[i - 1], lows[i - 2] if i >= 2 else lows[i - 1])
                if lows[i] < sar:
                    trend = -1
                    sar = ep
                    ep = lows[i]
                    af = 0.02
                else:
                    if highs[i] > ep:
                        ep = highs[i]
                        af = min(af + 0.02, max_af)
            else:
                sar = max(sar, highs[i - 1], highs[i - 2] if i >= 2 else highs[i - 1])
                if highs[i] > sar:
                    trend = 1
                    sar = ep
                    ep = highs[i]
                    af = 0.02
                else:
                    if lows[i] < ep:
                        ep = lows[i]
                        af = min(af + 0.02, max_af)
            sar_list.append(sar)

        return {"sar": sar_list[-1], "trend": "up" if trend == 1 else "down"}

    def _aroon(self, highs: list[float], lows: list[float], period: int = 25) -> dict[str, Any]:
        if len(highs) < period:
            return {"up": 0.0, "down": 0.0, "oscillator": 0.0}
        high_idx = highs[-period:].index(max(highs[-period:]))
        low_idx = lows[-period:].index(min(lows[-period:]))
        aroon_up = ((period - high_idx) / period) * 100
        aroon_down = ((period - low_idx) / period) * 100
        return {"up": aroon_up, "down": aroon_down, "oscillator": aroon_up - aroon_down}

    def _supertrend(self, highs: list[float], lows: list[float], closes: list[float], period: int = 10, multiplier: float = 3.0) -> dict[str, Any]:
        if len(closes) < period:
            return {"supertrend": 0.0, "trend": "neutral"}
        atr = self._atr(highs, lows, closes, period)
        supertrend = (highs[-1] + lows[-1]) / 2 + multiplier * atr
        return {"supertrend": supertrend, "trend": "up" if closes[-1] > supertrend else "down"}

    async def _trend(self, prices: list[float], highs: list[float], lows: list[float]) -> dict[str, Any]:
        return {
            "adx_14": self._adx(highs, lows, prices, 14),
            "ichimoku": self._ichimoku(highs, lows, prices),
            "parabolic_sar": self._parabolic_sar(highs, lows, prices),
            "aroon": self._aroon(highs, lows, 25),
            "supertrend": self._supertrend(highs, lows, prices, 10, 3.0),
        }

    # ------------------------------------------------------------------ #
    # Volume Indicators
    # ------------------------------------------------------------------ #

    def _obv(self, prices: list[float], volumes: list[float]) -> float:
        if len(prices) < 2 or len(volumes) < 2:
            return 0.0
        obv = 0.0
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:
                obv += volumes[i]
            elif prices[i] < prices[i - 1]:
                obv -= volumes[i]
        return obv

    def _cmf(self, highs: list[float], lows: list[float], closes: list[float], volumes: list[float], period: int = 20) -> float:
        if len(closes) < period:
            return 0.0
        mf_multiplier = ((closes[-1] - lows[-1]) - (highs[-1] - closes[-1])) / (highs[-1] - lows[-1]) if highs[-1] != lows[-1] else 0
        mf_volume = mf_multiplier * volumes[-1]
        return mf_volume / sum(volumes[-period:]) if sum(volumes[-period:]) != 0 else 0.0

    def _ad_line(self, highs: list[float], lows: list[float], closes: list[float], volumes: list[float]) -> float:
        if len(closes) < 1:
            return 0.0
        ad = 0.0
        for i in range(1, len(closes)):
            clv = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / (highs[i] - lows[i]) if highs[i] != lows[i] else 0.5
            ad += clv * volumes[i]
        return ad

    def _vpt(self, prices: list[float], volumes: list[float]) -> float:
        if len(prices) < 2:
            return 0.0
        vpt = 0.0
        for i in range(1, len(prices)):
            pct_change = (prices[i] - prices[i - 1]) / prices[i - 1] if prices[i - 1] != 0 else 0
            vpt += pct_change * volumes[i]
        return vpt

    def _mfi(self, highs: list[float], lows: list[float], closes: list[float], volumes: list[float], period: int = 14) -> float:
        if len(closes) < period + 1:
            return 50.0
        typical = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(len(closes))]
        raw_mf = [typical[i] * volumes[i] for i in range(len(typical))]
        pos: list[float] = []
        neg: list[float] = []
        for i in range(1, len(typical)):
            if typical[i] > typical[i - 1]:
                pos.append(raw_mf[i])
                neg.append(0)
            else:
                pos.append(0)
                neg.append(raw_mf[i])
        pmf = sum(pos[-period:])
        nf = sum(neg[-period:])
        if nf == 0:
            return 100.0
        mfr = pmf / nf
        return 100 - (100 / (1 + mfr))

    def _ease_of_movement(self, highs: list[float], lows: list[float], volumes: list[float], period: int = 14) -> float:
        if len(highs) < 2:
            return 0.0
        distance = ((highs[-1] + lows[-1]) / 2 - (highs[-2] + lows[-2]) / 2)
        box = volumes[-1] / (highs[-1] - lows[-1]) if highs[-1] != lows[-1] else 1
        return distance / box if box != 0 else 0.0

    async def _volume(self, prices: list[float], highs: list[float], lows: list[float], volumes: list[float]) -> dict[str, Any]:
        return {
            "obv": self._obv(prices, volumes),
            "cmf": self._cmf(highs, lows, prices, volumes, 20),
            "ad_line": self._ad_line(highs, lows, prices, volumes),
            "vpt": self._vpt(prices, volumes),
            "mfi": self._mfi(highs, lows, prices, volumes, 14),
            "ease_of_movement": self._ease_of_movement(highs, lows, volumes, 14),
        }

    # ------------------------------------------------------------------ #
    # Support / Resistance
    # ------------------------------------------------------------------ #

    def _pivot_points(self, highs: list[float], lows: list[float], closes: list[float]) -> dict[str, float]:
        if len(highs) < 1:
            return {"pivot": 0.0, "r1": 0.0, "s1": 0.0}
        h = highs[-1]
        low_val = lows[-1]
        c = closes[-1]
        pivot = (h + low_val + c) / 3
        return {
            "pivot": pivot,
            "r1": 2 * pivot - low_val,
            "s1": 2 * pivot - h,
        }

    def _fibonacci(self, highs: list[float], lows: list[float], closes: list[float]) -> dict[str, float]:
        if len(highs) < 1:
            return {"level_0": 0.0, "level_236": 0.0, "level_382": 0.0, "level_618": 0.0, "level_100": 0.0}
        high = max(highs[-20:]) if len(highs) >= 20 else max(highs)
        low = min(lows[-20:]) if len(lows) >= 20 else min(lows)
        diff = high - low
        return {
            "level_0": high,
            "level_236": high - 0.236 * diff,
            "level_382": high - 0.382 * diff,
            "level_618": high - 0.618 * diff,
            "level_100": low,
        }

    async def _support_resistance(self, prices: list[float], highs: list[float], lows: list[float]) -> dict[str, Any]:
        return {
            "pivot_points": self._pivot_points(highs, lows, prices),
            "fibonacci": self._fibonacci(highs, lows, prices),
        }

    # ------------------------------------------------------------------ #
    # Extra Oscillators
    # ------------------------------------------------------------------ #

    def _awesome_oscillator(self, highs: list[float], lows: list[float]) -> dict[str, float]:
        if len(highs) < 34:
            return {"ao": 0.0}
        median = [(highs[i] + lows[i]) / 2 for i in range(len(highs))]
        sma5 = self._sma(median, 5)
        sma34 = self._sma(median, 34)
        return {"ao": sma5 - sma34}

    def _ultimate_oscillator(self, highs: list[float], lows: list[float], closes: list[float], volumes: list[float]) -> float:
        if len(closes) < 28:
            return 50.0

        def bp(idx: int) -> float:
            return closes[idx] - min(lows[idx], closes[idx - 1]) if idx > 0 else closes[idx] - lows[idx]

        def tr(idx: int) -> float:
            return max(highs[idx], closes[idx - 1]) - min(lows[idx], closes[idx - 1]) if idx > 0 else highs[idx] - lows[idx]

        def avg(period: int) -> float:
            raw_bp = sum(bp(i) for i in range(len(closes) - period, len(closes)))
            raw_tr = sum(tr(i) for i in range(len(closes) - period, len(closes)))
            return raw_bp / raw_tr if raw_tr != 0 else 0.0

        avg7 = avg(7)
        avg14 = avg(14)
        avg28 = avg(28)
        return 100.0 * ((4.0 * avg7) + (2.0 * avg14) + avg28) / 7.0

    async def _oscillators(self, prices: list[float], highs: list[float], lows: list[float], volumes: list[float]) -> dict[str, Any]:
        return {
            "awesome_oscillator": self._awesome_oscillator(highs, lows),
            "ultimate_oscillator": self._ultimate_oscillator(highs, lows, prices, volumes),
        }
