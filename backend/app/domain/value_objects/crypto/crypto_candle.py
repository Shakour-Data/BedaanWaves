from dataclasses import dataclass
from datetime import datetime
from ..shared.exceptions import ValidationException

@dataclass(frozen=True)
class CryptoCandle:
    """Value Object for a cryptocurrency OHLC candle."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self):
        if self.low > self.high:
            raise ValidationException("Low price cannot be higher than high price")
        if self.open < 0 or self.high < 0 or self.low < 0 or self.close < 0:
            raise ValidationException("Prices cannot be negative")
