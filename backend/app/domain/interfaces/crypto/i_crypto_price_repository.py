from abc import ABC, abstractmethod
from typing import List, Optional
from ...domain.shared.result import Result
from ..value_objects.crypto.crypto_price import CryptoPrice
from ..value_objects.crypto.crypto_candle import CryptoCandle

class ICryptoPriceRepository(ABC):
    """Domain interface for fetching cryptocurrency price data."""
    
    @abstractmethod
    async def get_price(self, symbol: str, vs_currency: str = "usd") -> Result[CryptoPrice]:
        """Fetch current price for a symbol."""
        pass
    
    @abstractmethod
    async def get_ohlc(self, symbol: str, days: int = 7) -> Result[List[CryptoCandle]]:
        """Fetch OHLC candles for a symbol."""
        pass
    
    @abstractmethod
    async def search_assets(self, query: str) -> Result[List[str]]:
        """Search for crypto assets matching the query."""
        pass
