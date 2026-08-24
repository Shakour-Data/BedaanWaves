from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from ...domain.shared.result import Result

class ICryptoMarketDataRepository(ABC):
    """Domain interface for persisting raw crypto market data."""
    
    @abstractmethod
    async def save_raw_data(
        self, 
        asset_id: str, 
        symbol: str, 
        data_type: str, 
        payload: Dict[str, Any],
        exchange: str = "BINANCE"
    ) -> Result[bool]:
        """Save or update raw market data record."""
        pass
    
    @abstractmethod
    async def get_latest_ingestion_time(self, symbol: str, data_type: str) -> Result[Optional[datetime]]:
        """Get the timestamp of the last ingestion for a specific symbol and data type."""
        pass
