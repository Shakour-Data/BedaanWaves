from abc import ABC, abstractmethod
from typing import Dict
from decimal import Decimal
from dataclasses import dataclass
from ...domain.shared.result import Result

@dataclass
class ExchangeTicker:
    symbol: str
    bid: Decimal
    ask: Decimal
    volume_24h: Decimal

class IExchangePriceProvider(ABC):
    """Interface for fetching ticker data from a specific exchange."""
    
    @property
    @abstractmethod
    def exchange_name(self) -> str:
        pass
        
    @abstractmethod
    async def get_tickers(self) -> Result[Dict[str, ExchangeTicker]]:
        """Fetch all available tickers from the exchange."""
        pass
