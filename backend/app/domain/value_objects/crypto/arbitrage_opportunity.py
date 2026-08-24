from dataclasses import dataclass
from decimal import Decimal
from ..shared.exceptions import ValidationException

@dataclass(frozen=True)
class ArbitrageOpportunity:
    """Value Object representing a potential arbitrage opportunity."""
    buy_exchange: str
    sell_exchange: str
    asset: str
    buy_price: Decimal
    sell_price: Decimal
    profit_percentage: Decimal
    estimated_fee_bps: int

    def __post_init__(self):
        if self.buy_exchange == self.sell_exchange:
            raise ValidationException("Buy and sell exchanges must be different")
        if self.buy_price <= 0 or self.sell_price <= 0:
            raise ValidationException("Prices must be positive")
        if self.profit_percentage < 0:
            # We allow negative profit for analysis, but usually it's positive
            pass
