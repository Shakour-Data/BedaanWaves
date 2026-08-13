"""
Technical Analysis Service - Tier 3 Analysis Service

50+ technical indicators and analysis. Pure Python implementations for TSE/OTC,
foreign exchanges, and crypto. Optimized with caching for production use.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import math
import asyncio
from functools import lru_cache

from ..core import AnalysisService


# Cache LRU for frequently-used indicator series calculations
@lru_cache(maxsize=128)
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
            "sma_20": _cached_sma(tuple(prices), 20),
            "sma_50": _cached_sma(tuple(prices), 50),
            "sma_200": _cached_sma(tuple(prices), 200),
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

    # ... (rest of the file remains the same, keeping original implementations)
    # The _sma method can now use _cached_sma for repeated calculations
    # but the class methods maintain their original implementations for consistency