from typing import List, Dict
import logging

from app.services.data.adjusted_price_validator import AdjustedPriceValidator

logger = logging.getLogger(__name__)

class MovingAverageEngine:
    """Domain service for calculating moving averages on ADJUSTED prices."""

    def calculate_sma(self, prices: List[float], period: int, source: str = "unknown") -> float:
        AdjustedPriceValidator.validate_price_array(prices, source)
        if not prices or len(prices) < period:
            return 0.0
        return sum(prices[-period:]) / period

    def calculate_ema(self, prices: List[float], period: int, source: str = "unknown") -> float:
        AdjustedPriceValidator.validate_price_array(prices, source)
        if not prices or len(prices) < period:
            return 0.0

        alpha = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price * alpha) + (ema * (1 - alpha))
        return round(ema, 2)

    def calculate_wma(self, prices: List[float], period: int, source: str = "unknown") -> float:
        AdjustedPriceValidator.validate_price_array(prices, source)
        if not prices or len(prices) < period:
            return 0.0

        weight_sum = period * (period + 1) / 2
        weighted_sum = sum(prices[-(period-i)] * (i+1) for i in range(period))
        return round(weighted_sum / weight_sum, 2)
