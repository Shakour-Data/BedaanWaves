from typing import List
import logging

from app.services.data.adjusted_price_validator import AdjustedPriceValidator

logger = logging.getLogger(__name__)

class MomentumEngine:
    """Domain service for calculating momentum indicators on ADJUSTED prices."""

    def calculate_rsi(self, prices: List[float], period: int = 14, source: str = "unknown") -> float:
        AdjustedPriceValidator.validate_price_array(prices, source)
        if len(prices) < period + 1:
            return 50.0

        deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]

        avg_gain = sum(gains[-period:]) / period if gains else 0
        avg_loss = sum(losses[-period:]) / period if losses else 0

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    def calculate_macd(self, prices: List[float], source: str = "unknown") -> tuple:
        AdjustedPriceValidator.validate_price_array(prices, source)
        ema_12 = self._calculate_ema(prices, 12, source)
        ema_26 = self._calculate_ema(prices, 26, source)
        macd_line = ema_12 - ema_26
        return round(macd_line, 2), round(ema_12, 2), round(ema_26, 2)

    def _calculate_ema(self, prices: List[float], period: int, source: str = "unknown") -> float:
        AdjustedPriceValidator.validate_price_array(prices, source)
        alpha = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price * alpha) + (ema * (1 - alpha))
        return ema
