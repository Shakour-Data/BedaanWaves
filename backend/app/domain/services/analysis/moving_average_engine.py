import logging

from app.services.data.adjusted_price_validator import AdjustedPriceValidator

logger = logging.getLogger(__name__)


class MovingAverageEngine:
    """Domain service for calculating moving averages on ADJUSTED prices."""

    def calculate_sma(self, prices: list[float], period: int, source: str = "unknown") -> float:
        AdjustedPriceValidator.validate_price_array(prices, source)
        if not prices or len(prices) < period:
            return 0.0
        return sum(prices[-period:]) / period

    def calculate_ema(self, prices: list[float], period: int, source: str = "unknown") -> float:
        AdjustedPriceValidator.validate_price_array(prices, source)
        if not prices or len(prices) < period:
            return 0.0

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return round(ema, 2)

    def calculate_wma(self, prices: list[float], period: int, source: str = "unknown") -> float:
        AdjustedPriceValidator.validate_price_array(prices, source)
        if not prices or len(prices) < period:
            return 0.0

        weight_sum = period * (period + 1) / 2
        weighted_sum = sum(prices[-(period - i)] * (i + 1) for i in range(period))
        return round(weighted_sum / weight_sum, 2)
