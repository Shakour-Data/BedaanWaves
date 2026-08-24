from dataclasses import dataclass
from datetime import datetime, timezone
from ..shared.exceptions import ValidationException

@dataclass(frozen=True)
class CryptoPrice:
    """Value Object for a cryptocurrency price."""
    symbol: str
    vs_currency: str
    price: float
    timestamp: datetime = datetime.now(timezone.utc)

    def __post_init__(self):
        if not self.symbol:
            raise ValidationException("Symbol cannot be empty")
        if self.price < 0:
            raise ValidationException("Price cannot be negative")
