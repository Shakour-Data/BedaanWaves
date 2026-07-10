"""
Technical Analysis Service - Tier 3 Analysis Service

50+ technical indicators and analysis. Pure Python implementations for TSE/OTC,
foreign exchanges, and crypto.
"""

from typing import Any, Dict, List, Optional

from datetime import datetime, timezone
import math

from ..core import AnalysisService


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

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prices = data.get("prices", [])
        highs = data.get("highs", prices)
        lows = data.get("lows", prices)
        volumes = data.get("volumes", [])
        current_price = data.get("current_price", prices[-1] if prices else 0)

        if not prices or len(prices) < 30:
            return {"error": "Insufficient price data", "min_required": 30}

        indicators = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticker": data.get("ticker", "UNKNOWN"),
            "market": data.get("market", "TSE"),
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
    # Category orchestrators
    # ------------------------------------------------------------------ #

    async def _moving_averages(self, prices: List[float]) -> Dict[str, Any]:
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

    async def _momentum(self, prices: List[float]) -> Dict[str, Any]:
        return {
            "rsi_14": self._rsi(prices, 14),
            "macd": self._macd(prices),
            "stochastic": self._stochastic(prices, 14),
            "kdj": self._kdj(prices, 9),
            "cci": self._cci(prices, 20),
            "williams_r": self._williams_r(prices, 14),
            "roc_12": self._roc(prices, 12),
            "momentum_10": self._momentum_indicator(prices, 10),
            "trix": self._trix(prices, 15),
            "stoch_rsi": self._stoch_rsi(prices, 14),
        }

    async def _volatility(
        self, prices: List[float], highs: List[float], lows: List[float]
    ) -> Dict[str, Any]:
        return {
            "bollinger_bands": self._bollinger_bands(prices, 20),
            "atr_14": self._atr(highs, lows, prices, 14),
            "kama_10": self._kama(prices, 10),
            "donchian_20": self._donchian(highs, lows, 20),
            "std_dev_20": self._std_dev(prices, 20),
            "variance_20": self._variance(prices, 20),
        }

    async def _trend(
        self, prices: List[float], highs: List[float], lows: List[float]
    ) -> Dict[str, Any]:
        return {
            "adx_14": self._adx(highs, lows, prices, 14),
            "ichimoku": self._ichimoku(highs, lows, prices),
            "parabolic_sar": self._parabolic_sar(highs, lows, prices),
            "aroon": self._aroon(highs, lows, 25),
            "supertrend": self._supertrend(highs, lows, prices, 10, 3.0),
        }

    async def _volume(
        self,
        prices: List[float],
        highs: List[float],
        lows: List[float],
        volumes: List[float],
    ) -> Dict[str, Any]:
        return {
            "obv": self._obv(prices, volumes),
            "cmf_20": self._cmf(highs, lows, prices, volumes, 20),
            "ad_line": self._ad_line(highs, lows, prices, volumes),
            "vpt": self._vpt(prices, volumes),
            "mfi_14": self._mfi(highs, lows, prices, volumes, 14),
            "ease_of_movement": self._ease_of_movement(highs, lows, volumes, 14),
        }

    async def _support_resistance(
        self, prices: List[float], highs: List[float], lows: List[float]
    ) -> Dict[str, Any]:
        return {
            "pivot_points": self._pivot_points(highs, lows, prices),
            "fibonacci": self._fibonacci(highs, lows, prices),
        }

    async def _oscillators(
        self,
        prices: List[float],
        highs: List[float],
        lows: List[float],
        volumes: List[float],
    ) -> Dict[str, Any]:
        return {
            "awesome_oscillator": self._awesome_oscillator(highs, lows),
            "commodity_channel_index": self._cci(prices, 20),
            "ultimate_oscillator": self._ultimate_oscillator(highs, lows, prices, volumes),
            "price_oscillator": self._price_oscillator(prices, 12, 26),
        }

    # ------------------------------------------------------------------ #
    # Generic helpers
    # ------------------------------------------------------------------ #

    def _sma(self, values: List[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        return sum(values[-period:]) / period

    def _sma_series(self, values: List[float], period: int) -> List[float]:
        if len(values) < period:
            return []
        out: List[float] = []
        for i in range(period - 1, len(values)):
            out.append(sum(values[i - period + 1 : i + 1]) / period)
        return out

    def _ema(self, prices: List[float], period: int) -> float:
        series = self._ema_series(prices, period)
        return series[-1] if series else 0.0

    def _ema_series(self, prices: List[float], period: int) -> List[float]:
        if len(prices) < period:
            return []
        multiplier = 2.0 / (period + 1)
        seed = sum(prices[:period]) / period
        out: List[float] = [seed]
        for p in prices[period:]:
            seed = p * multiplier + seed * (1 - multiplier)
            out.append(seed)
        return out

    def _wma(self, prices: List[float], period: int) -> float:
        series = self._wma_series(prices, period)
        return series[-1] if series else 0.0

    def _wma_series(self, prices: List[float], period: int) -> List[float]:
        if len(prices) < period:
            return []
        weights = list(range(1, period + 1))
        weight_sum = sum(weights)
        out: List[float] = []
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1 : i + 1]
            out.append(sum(p * w for p, w in zip(window, weights)) / weight_sum)
        return out

    def _std_dev(self, values: List[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        window = values[-period:]
        mean = sum(window) / period
        variance = sum((v - mean) ** 2 for v in window) / period
        return math.sqrt(variance)

    def _variance(self, values: List[float], period: int) -> float:
        if len(values) < period:
            return 0.0
        window = values[-period:]
        mean = sum(window) / period
        return sum((v - mean) ** 2 for v in window) / period

    # ------------------------------------------------------------------ #
    # Moving Averages (extended)
    # ------------------------------------------------------------------ #

    def _dema(self, prices: List[float], period: int) -> float:
        ema1 = self._ema_series(prices, period)
        if not ema1:
            return 0.0
        ema2 = self._ema_series(ema1, period)
        return 2 * ema1[-1] - ema2[-1]

    def _tema(self, prices: List[float], period: int) -> float:
        ema1 = self._ema_series(prices, period)
        if not ema1:
            return 0.0
        ema2 = self._ema_series(ema1, period)
        ema3 = self._ema_series(ema2, period)
        return 3 * ema1[-1] - 3 * ema2[-1] + ema3[-1]

    def _t3(self, prices: List[float], period: int, vfactor: float = 0.7) -> float:
        e1 = self._ema_series(prices, period)
        if not e1:
            return 0.0
        e2 = self._ema_series(e1, period)
        if not e2:
            return 0.0
        e3 = self._ema_series(e2, period)
        if not e3:
            return 0.0
        e4 = self._ema_series(e3, period)
        if not e4:
            return 0.0
        e5 = self._ema_series(e4, period)
        if not e5:
            return 0.0
        e6 = self._ema_series(e5, period)
        if not e6:
            return 0.0
        a = vfactor
        c1 = -a ** 3
        c2 = 3 * a ** 2 + 3 * a ** 3
        c3 = -6 * a ** 2 - 3 * a - 3 * a ** 3
        c4 = 1 + 3 * a + a ** 3 + 3 * a ** 2
        return (
            c1 * e6[-1]
            + c2 * e5[-1]
            + c3 * e4[-1]
            + c4 * e3[-1]
        )

    def _hull_ma(self, prices: List[float], period: int) -> float:
        half = max(1, period // 2)
        wma_half = self._wma_series(prices, half)
        wma_full = self._wma_series(prices, period)
        if not wma_half or not wma_full:
            return 0.0
        n = len(wma_full)
        raw = [
            2 * wma_half[-n + i] - wma_full[i]
            for i in range(n)
        ]
        return self._wma(raw, max(1, int(math.sqrt(period))))

    # ------------------------------------------------------------------ #
    # Momentum / Oscillators
    # ------------------------------------------------------------------ #

    def _rsi(self, prices: List[float], period: int) -> float:
        if len(prices) < period + 1:
            return 50.0
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0.0 for d in deltas]
        losses = [-d if d < 0 else 0.0 for d in deltas]
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        ema_fast = self._ema_series(prices, fast)
        ema_slow = self._ema_series(prices, slow)
        if not ema_fast or not ema_slow:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
        n = min(len(ema_fast), len(ema_slow))
        macd_line = [ema_fast[-n + i] - ema_slow[-n + i] for i in range(n)]
        signal_line = self._ema_series(macd_line, signal)
        macd_val = macd_line[-1]
        sig_val = signal_line[-1] if signal_line else macd_val
        return {
            "macd": macd_val,
            "signal": sig_val,
            "histogram": macd_val - sig_val,
        }

    def _stochastic(self, prices: List[float], period: int) -> Dict[str, float]:
        if len(prices) < period:
            return {"k": 50.0, "d": 50.0}
        window = prices[-period:]
        high = max(window)
        low = min(window)
        close = prices[-1]
        k = 100 * (close - low) / (high - low) if high != low else 50.0
        return {"k": k, "d": k}

    def _kdj(self, prices: List[float], period: int = 9) -> Dict[str, float]:
        if len(prices) < period:
            return {"k": 50.0, "d": 50.0, "j": 50.0}
        window = prices[-period:]
        high = max(window)
        low = min(window)
        rsv = 100 * (prices[-1] - low) / (high - low) if high != low else 50.0
        k = 2 / 3 * 50 + 1 / 3 * rsv
        d = 2 / 3 * 50 + 1 / 3 * k
        j = 3 * k - 2 * d
        return {"k": k, "d": d, "j": j}

    def _cci(self, prices: List[float], period: int) -> float:
        if len(prices) < period:
            return 0.0
        typical = prices  # when only closes are available, treat close as typical price
        sma = sum(typical[-period:]) / period
        mean_dev = sum(abs(t - sma) for t in typical[-period:]) / period
        if mean_dev == 0:
            return 0.0
        return (typical[-1] - sma) / (0.015 * mean_dev)

    def _williams_r(self, prices: List[float], period: int) -> float:
        if len(prices) < period:
            return -50.0
        window = prices[-period:]
        high = max(window)
        low = min(window)
        if high == low:
            return -50.0
        return -100 * (high - prices[-1]) / (high - low)

    def _roc(self, prices: List[float], period: int) -> float:
        if len(prices) < period + 1 or prices[-period - 1] == 0:
            return 0.0
        return ((prices[-1] - prices[-period - 1]) / prices[-period - 1]) * 100

    def _momentum_indicator(self, prices: List[float], period: int) -> float:
        if len(prices) < period + 1:
            return 0.0
        return prices[-1] - prices[-period - 1]

    def _trix(self, prices: List[float], period: int) -> float:
        ema1 = self._ema_series(prices, period)
        if not ema1:
            return 0.0
        ema2 = self._ema_series(ema1, period)
        ema3 = self._ema_series(ema2, period)
        if len(ema3) < 2:
            return 0.0
        return ((ema3[-1] - ema3[-2]) / ema3[-2]) * 100 if ema3[-2] != 0 else 0.0

    def _stoch_rsi(self, prices: List[float], period: int) -> Dict[str, float]:
        if len(prices) < period + 1:
            return {"k": 50.0, "d": 50.0}
        rsis = []
        for i in range(period, len(prices)):
            rsi_val = self._rsi(prices[: i + 1], period)
            rsis.append(rsi_val)
        if len(rsis) < period:
            return {"k": 50.0, "d": 50.0}
        window = rsis[-period:]
        high = max(window)
        low = min(window)
        k = 100 * (rsis[-1] - low) / (high - low) if high != low else 50.0
        return {"k": k, "d": k}

    def _price_oscillator(self, prices: List[float], fast: int, slow: int) -> float:
        fast_ma = self._ema(prices, fast)
        slow_ma = self._ema(prices, slow)
        if slow_ma == 0:
            return 0.0
        return ((fast_ma - slow_ma) / slow_ma) * 100

    # ------------------------------------------------------------------ #
    # Volatility
    # ------------------------------------------------------------------ #

    def _bollinger_bands(self, prices: List[float], period: int, num_std: float = 2.0) -> Dict[str, float]:
        sma = self._sma(prices, period)
        std = self._std_dev(prices, period)
        return {
            "upper": sma + num_std * std,
            "middle": sma,
            "lower": sma - num_std * std,
        }

    def _true_range(self, highs: List[float], lows: List[float], closes: List[float]) -> List[float]:
        tr: List[float] = []
        for i in range(1, len(closes)):
            high = highs[i] if i < len(highs) else closes[i]
            low = lows[i] if i < len(lows) else closes[i]
            prev_close = closes[i - 1]
            tr.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
        return tr

    def _atr(self, highs: List[float], lows: List[float], closes: List[float], period: int) -> float:
        tr = self._true_range(highs, lows, closes)
        if len(tr) < period:
            return sum(tr) / len(tr) if tr else 0.0
        atr = sum(tr[:period]) / period
        for v in tr[period:]:
            atr = (atr * (period - 1) + v) / period
        return atr

    def _kama(self, prices: List[float], period: int, fast: int = 2, slow: int = 30) -> float:
        if len(prices) < period + 1:
            return 0.0
        change = abs(prices[-1] - prices[-period - 1])
        volatility = sum(abs(prices[i] - prices[i - 1]) for i in range(len(prices) - period, len(prices)))
        if volatility == 0:
            return prices[-1]
        er = change / volatility
        sc = (er * (2.0 / (fast + 1) - 2.0 / (slow + 1)) + 2.0 / (slow + 1)) ** 2
        kama = prices[-period - 1]
        for i in range(len(prices) - period, len(prices)):
            kama = kama + sc * (prices[i] - kama)
        return kama

    def _donchian(self, highs: List[float], lows: List[float], period: int) -> Dict[str, float]:
        if len(highs) < period or len(lows) < period:
            return {"upper": 0.0, "lower": 0.0, "middle": 0.0}
        upper = max(highs[-period:])
        lower = min(lows[-period:])
        return {"upper": upper, "lower": lower, "middle": (upper + lower) / 2}

    # ------------------------------------------------------------------ #
    # Trend
    # ------------------------------------------------------------------ #

    def _adx(self, highs: List[float], lows: List[float], closes: List[float], period: int) -> Dict[str, float]:
        if len(closes) < period + 1:
            return {"adx": 0.0, "plus_di": 0.0, "minus_di": 0.0}
        plus_dm: List[float] = []
        minus_dm: List[float] = []
        tr: List[float] = []
        for i in range(1, len(closes)):
            up = highs[i] - highs[i - 1] if i < len(highs) else closes[i] - closes[i - 1]
            down = lows[i - 1] - lows[i] if i < len(lows) else closes[i - 1] - closes[i]
            pdm = up if (up > down and up > 0) else 0.0
            mdm = down if (down > up and down > 0) else 0.0
            plus_dm.append(pdm)
            minus_dm.append(mdm)
            h = highs[i] if i < len(highs) else closes[i]
            l = lows[i] if i < len(lows) else closes[i]
            tr.append(max(h - l, abs(h - closes[i - 1]), abs(l - closes[i - 1])))

        def wilder_smooth(values: List[float]) -> List[float]:
            if len(values) < period:
                return []
            first = sum(values[:period]) / period
            out = [first]
            prev = first
            for v in values[period:]:
                prev = (prev * (period - 1) + v) / period
                out.append(prev)
            return out

        atr_s = wilder_smooth(tr)
        pdm_s = wilder_smooth(plus_dm)
        mdm_s = wilder_smooth(minus_dm)
        if not atr_s:
            return {"adx": 0.0, "plus_di": 0.0, "minus_di": 0.0}
        n = min(len(atr_s), len(pdm_s), len(mdm_s))
        plus_di: List[float] = []
        minus_di: List[float] = []
        dx: List[float] = []
        for i in range(n):
            pdi = 100 * pdm_s[i] / atr_s[i] if atr_s[i] else 0.0
            mdi = 100 * mdm_s[i] / atr_s[i] if atr_s[i] else 0.0
            di_sum = pdi + mdi
            dxv = 100 * abs(pdi - mdi) / di_sum if di_sum else 0.0
            plus_di.append(pdi)
            minus_di.append(mdi)
            dx.append(dxv)
        adx_val = sum(dx) / len(dx) if dx else 0.0
        return {
            "adx": adx_val,
            "plus_di": plus_di[-1] if plus_di else 0.0,
            "minus_di": minus_di[-1] if minus_di else 0.0,
        }

    def _ichimoku(
        self, highs: List[float], lows: List[float], closes: List[float]
    ) -> Dict[str, float]:
        def hh_ll(period: int, hi: bool) -> float:
            h = highs[-period:] if len(highs) >= period else closes[-period:]
            l = lows[-period:] if len(lows) >= period else closes[-period:]
            if hi:
                return max(h)
            return min(l)

        tenkan = (hh_ll(9, True) + hh_ll(9, False)) / 2
        kijun = (hh_ll(26, True) + hh_ll(26, False)) / 2
        senkou_a = (tenkan + kijun) / 2
        senkou_b = (hh_ll(52, True) + hh_ll(52, False)) / 2
        return {
            "tenkan_sen": tenkan,
            "kijun_sen": kijun,
            "senkou_a": senkou_a,
            "senkou_b": senkou_b,
            "chikou_span": closes[-1],
        }

    def _parabolic_sar(
        self, highs: List[float], lows: List[float], closes: List[float],
        acceleration: float = 0.02, maximum: float = 0.2,
    ) -> Dict[str, Any]:
        n = len(closes)
        if n < 2:
            return {"sar": 0.0, "trend": "neutral"}
        high = highs if len(highs) == n else closes
        low = lows if len(lows) == n else closes
        trend_up = high[1] > high[0]
        sar = low[0] if trend_up else high[0]
        ep = high[1] if trend_up else low[1]
        af = acceleration
        for i in range(2, n):
            sar = sar + af * (ep - sar)
            if trend_up:
                sar = min(sar, low[i - 1], low[i - 2] if i >= 2 else low[i - 1])
                if low[i] < sar:
                    trend_up = False
                    sar = ep
                    ep = low[i]
                    af = acceleration
                else:
                    if high[i] > ep:
                        ep = high[i]
                        af = min(af + acceleration, maximum)
            else:
                sar = max(sar, high[i - 1], high[i - 2] if i >= 2 else high[i - 1])
                if high[i] > sar:
                    trend_up = True
                    sar = ep
                    ep = high[i]
                    af = acceleration
                else:
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + acceleration, maximum)
        return {"sar": sar, "trend": "up" if trend_up else "down"}

    def _aroon(self, highs: List[float], lows: List[float], period: int) -> Dict[str, float]:
        if len(highs) < period or len(lows) < period:
            return {"up": 0.0, "down": 0.0, "oscillator": 0.0}
        window_high = highs[-period:]
        window_low = lows[-period:]
        days_since_high = period - 1 - window_high.index(max(window_high))
        days_since_low = period - 1 - window_low.index(min(window_low))
        up = ((period - days_since_high) / period) * 100
        down = ((period - days_since_low) / period) * 100
        return {"up": up, "down": down, "oscillator": up - down}

    def _supertrend(
        self, highs: List[float], lows: List[float], closes: List[float],
        period: int, multiplier: float,
    ) -> Dict[str, Any]:
        if len(closes) < period + 1:
            return {"supertrend": 0.0, "trend": "neutral"}
        atr = self._atr(highs, lows, closes, period)
        if atr == 0:
            return {"supertrend": closes[-1], "trend": "neutral"}
        upper_band = lower_band = final_upper = final_lower = 0.0
        prev_final_upper = prev_final_lower = 0.0
        trend_up = True
        supertrend = closes[-1]
        for i in range(period, len(closes)):
            basic_upper = (highs[i] + lows[i]) / 2 + multiplier * atr if i < len(highs) else (closes[i] + closes[i]) / 2 + multiplier * atr
            basic_lower = (highs[i] + lows[i]) / 2 - multiplier * atr if i < len(highs) else (closes[i] + closes[i]) / 2 - multiplier * atr
            if i == period:
                upper_band = basic_upper
                lower_band = basic_lower
            else:
                upper_band = min(basic_upper, prev_final_upper) if basic_upper < prev_final_upper else basic_upper
                lower_band = max(basic_lower, prev_final_lower) if basic_lower > prev_final_lower else basic_lower
            if closes[i - 1] <= prev_final_upper:
                final_upper = upper_band
            else:
                final_upper = max(upper_band, prev_final_upper)
            if closes[i - 1] >= prev_final_lower:
                final_lower = lower_band
            else:
                final_lower = min(lower_band, prev_final_lower)
            if closes[i] <= final_upper:
                trend_up = False
                supertrend = final_upper
            else:
                trend_up = True
                supertrend = final_lower
            prev_final_upper = final_upper
            prev_final_lower = final_lower
        return {"supertrend": supertrend, "trend": "up" if trend_up else "down"}

    # ------------------------------------------------------------------ #
    # Volume
    # ------------------------------------------------------------------ #

    def _obv(self, prices: List[float], volumes: List[float]) -> float:
        obv = 0.0
        for i in range(len(prices)):
            if i == 0:
                continue
            if prices[i] > prices[i - 1]:
                obv += volumes[i]
            elif prices[i] < prices[i - 1]:
                obv -= volumes[i]
        return obv

    def _cmf(
        self, highs: List[float], lows: List[float], closes: List[float],
        volumes: List[float], period: int,
    ) -> float:
        if len(closes) < period or len(volumes) < period:
            return 0.0
        mfv: List[float] = []
        vol: List[float] = []
        for i in range(len(closes) - period + 1, len(closes)):
            h = highs[i] if i < len(highs) else closes[i]
            l = lows[i] if i < len(lows) else closes[i]
            c = closes[i]
            if h == l:
                mfm = 0.0
            else:
                mfm = ((c - l) - (h - c)) / (h - l)
            mfv.append(mfm * volumes[i])
            vol.append(volumes[i])
        sum_mfv = sum(mfv)
        sum_vol = sum(vol)
        return sum_mfv / sum_vol if sum_vol else 0.0

    def _ad_line(
        self, highs: List[float], lows: List[float], closes: List[float], volumes: List[float]
    ) -> float:
        ad = 0.0
        for i in range(len(closes)):
            h = highs[i] if i < len(highs) else closes[i]
            l = lows[i] if i < len(lows) else closes[i]
            c = closes[i]
            clv = (c - l) / (h - l) if h != l else 0.0
            ad += clv * volumes[i]
        return ad

    def _vpt(self, prices: List[float], volumes: List[float]) -> float:
        vpt = 0.0
        for i in range(1, len(prices)):
            if prices[i - 1] != 0:
                vpt += volumes[i] * ((prices[i] - prices[i - 1]) / prices[i - 1])
        return vpt

    def _mfi(
        self, highs: List[float], lows: List[float], closes: List[float],
        volumes: List[float], period: int,
    ) -> float:
        if len(closes) < period + 1:
            return 50.0
        positive: List[float] = []
        negative: List[float] = []
        for i in range(1, len(closes)):
            h = highs[i] if i < len(highs) else closes[i]
            l = lows[i] if i < len(lows) else closes[i]
            tp = (h + l + closes[i]) / 3
            prev_tp = (h + l + closes[i - 1]) / 3
            raw_mf = tp * volumes[i]
            if tp > prev_tp:
                positive.append(raw_mf)
                negative.append(0.0)
            else:
                negative.append(raw_mf)
                positive.append(0.0)
        pos = sum(positive[-period:])
        neg = sum(negative[-period:])
        if neg == 0:
            return 100.0
        mr = pos / neg
        return 100 - (100 / (1 + mr))

    def _ease_of_movement(
        self, highs: List[float], lows: List[float], volumes: List[float], period: int
    ) -> float:
        if len(highs) < 2 or len(volumes) < 2:
            return 0.0
        emv: List[float] = []
        for i in range(1, len(highs)):
            box_ratio = volumes[i] / 1000000 if volumes[i] != 0 else 0.0
            distance = ((highs[i] + lows[i]) / 2) - ((highs[i - 1] + lows[i - 1]) / 2)
            if box_ratio == 0:
                emv.append(0.0)
            else:
                emv.append(distance / box_ratio)
        window = emv[-period:]
        return sum(window) / len(window) if window else 0.0

    # ------------------------------------------------------------------ #
    # Support / Resistance
    # ------------------------------------------------------------------ #

    def _pivot_points(
        self, highs: List[float], lows: List[float], closes: List[float]
    ) -> Dict[str, Any]:
        if not closes:
            return {}
        h = highs[-1] if highs else closes[-1]
        l = lows[-1] if lows else closes[-1]
        c = closes[-1]
        pivot = (h + l + c) / 3
        r1 = 2 * pivot - l
        r2 = pivot + (h - l)
        r3 = h + 2 * (pivot - l)
        s1 = 2 * pivot - h
        s2 = pivot - (h - l)
        s3 = l - 2 * (h - pivot)
        return {
            "pivot": pivot,
            "r1": r1, "r2": r2, "r3": r3,
            "s1": s1, "s2": s2, "s3": s3,
        }

    def _fibonacci(
        self, highs: List[float], lows: List[float], closes: List[float]
    ) -> Dict[str, float]:
        if not closes:
            return {}
        h = max(highs[-20:]) if len(highs) >= 20 else max(closes[-20:])
        l = min(lows[-20:]) if len(lows) >= 20 else min(closes[-20:])
        diff = h - l
        return {
            "level_0": h,
            "level_236": h - 0.236 * diff,
            "level_382": h - 0.382 * diff,
            "level_50": h - 0.5 * diff,
            "level_618": h - 0.618 * diff,
            "level_100": l,
        }

    # ------------------------------------------------------------------ #
    # Extra oscillators
    # ------------------------------------------------------------------ #

    def _awesome_oscillator(self, highs: List[float], lows: List[float]) -> Dict[str, float]:
        if len(highs) < 34:
            return {"ao": 0.0}
        midpoints = [(highs[i] + lows[i]) / 2 for i in range(len(highs))]
        fast = self._sma_series(midpoints, 5)
        slow = self._sma_series(midpoints, 34)
        if not fast or not slow:
            return {"ao": 0.0}
        n = min(len(fast), len(slow))
        ao = fast[-1] - slow[-1]
        return {"ao": ao}

    def _ultimate_oscillator(
        self, highs: List[float], lows: List[float], closes: List[float],
        volumes: List[float], periods: tuple = (7, 14, 28),
    ) -> float:
        if len(closes) < periods[2]:
            return 50.0
        bp: List[float] = []
        tr: List[float] = []
        for i in range(1, len(closes)):
            h = highs[i] if i < len(highs) else closes[i]
            l = lows[i] if i < len(lows) else closes[i]
            bp.append(closes[i] - min(l, closes[i - 1]))
            tr.append(max(h, closes[i - 1]) - min(l, closes[i - 1]))
        av: List[float] = []
        for p in periods:
            avg_bp = sum(bp[-p:]) / p
            avg_tr = sum(tr[-p:]) / p
            av.append(avg_bp / avg_tr if avg_tr else 0.0)
        w = (4, 2, 1)
        total_w = sum(w)
        uo = 100 * (w[0] * av[0] + w[1] * av[1] + w[2] * av[2]) / total_w
        return uo
