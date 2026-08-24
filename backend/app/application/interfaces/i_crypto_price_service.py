from abc import ABC, abstractmethod
from typing import List
from ...domain.shared.result import Result
from ...domain.value_objects.crypto.crypto_price import CryptoPrice
from ...domain.value_objects.crypto.crypto_candle import CryptoCandle

class ICryptoPriceService(ABC):
    """Application-level interface for crypto price operations."""
    
    @abstractmethod
    async def get_current_price(self, symbol: str, vs_currency: str = "usd") -> Result[CryptoPrice]:
        """Get the current price, potentially using cache."""
        pass
    
    @abstractmethod
    async def get_historical_candles(self, symbol: str, days: int = 7) -> Result[List[CryptoCandle]]:
        """Get historical candles, potentially using cache."""
        pass
    
    @abstractmethod
    async def search_symbols(self, query: str) -> Result[List[str]]:
        """Search for cryptocurrency symbols."""
        pass
