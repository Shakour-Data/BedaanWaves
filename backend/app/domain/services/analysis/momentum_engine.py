import logging

from app.services.data.adjusted_price_validator import AdjustedPriceValidator

logger = logging.getLogger(__name__)


class MomentumEngine:
    """Domain service for calculating momentum indicators on ADJUSTED prices."""

    def calculate_rsi(self, prices: list[float], period: int = 14, source: str = "unknown") -> float:
        AdjustedPriceValidator.validate_price_array(prices, source)
        if len(prices) < period + 1:
            return 50.0

        deltas = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
        gains = [max(d, 0.0) for d in deltas]
        losses = [max(-d, 0.0) for d in deltas]

        if len(gains) < period:
            return 50.0

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    def calculate_macd(self, prices: list[float], source: str = "unknown") -> tuple:
        AdjustedPriceValidator.validate_price_array(prices, source)
        ema_12 = self._calculate_ema(prices, 12, source)
        ema_26 = self._calculate_ema(prices, 26, source)
        macd_line = ema_12 - ema_26

        macd_values = []
        for i in range(26, len(prices) + 1):
            subset = prices[:i]
            f = self._calculate_ema(subset, 12, source)
            s = self._calculate_ema(subset, 26, source)
            if f is not None and s is not None:
                macd_values.append(f - s)

        signal_line = 0.0
        histogram = macd_line
        if len(macd_values) >= 9:
            signal_line = self._calculate_ema(macd_values, 9, source)
            histogram = macd_line - signal_line

        return round(macd_line, 2), round(signal_line, 2), round(histogram, 2), round(ema_12, 2), round(ema_26, 2)

    def _calculate_ema(self, prices: list[float], period: int, source: str = "unknown") -> float:
        AdjustedPriceValidator.validate_price_array(prices, source)
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
