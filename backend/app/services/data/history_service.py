"""
History Service - Tier 2 Data Service

Historical data management and retrieval.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from ..core import CachedService


class HistoryService(CachedService):
    """
    Historical data management service.
    
    Provides:
    - Historical data retrieval
    - Time-series data caching
    - Data aggregation
    """
    
    def __init__(
        self,
        service_name: str = "HistoryService",
        db_service=None,
        brs_client=None,
        cache_ttl_seconds: int = 86400,  # 24 hours
    ):
        """
        Initialize history service.
        
        Args:
            service_name: Service identifier
            db_service: Database service
            brs_client: BRS API client
            cache_ttl_seconds: Cache TTL
        """
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.db_service = db_service
        self.brs_client = brs_client
    
    async def initialize(self) -> None:
        """Initialize history service"""
        self.logger.info("HistoryService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown history service"""
        self.cache_clear()
        self.logger.info("HistoryService shutdown")
    
    async def get_stock_history(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "daily",
    ) -> List[Dict[str, Any]]:
        """
        Get stock historical data.
        
        Args:
            ticker: Stock ticker
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval
            
        Returns:
            Historical data
        """
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        
        cache_key = f"history:{ticker}:{start_date}:{end_date}:{interval}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        history = await self.brs_client.get_stock_history(
            ticker,
            start_date,
            end_date,
            interval
        )
        self.set_cached(cache_key, history)
        
        return history
    
    async def get_price_history(
        self,
        ticker: str,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get price history for last N days.
        
        Args:
            ticker: Stock ticker
            days: Number of days back
            
        Returns:
            Price data
        """
        end_date = datetime.utcnow().date().isoformat()
        start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        
        return await self.get_stock_history(ticker, start_date, end_date, "daily")
    
    async def get_volume_history(
        self,
        ticker: str,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get volume history"""
        history = await self.get_price_history(ticker, days)
        return [
            {
                "date": item.get("date"),
                "volume": item.get("volume"),
            }
            for item in history
        ]
    
    async def store_historical_data(
        self,
        ticker: str,
        date: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Store historical data in database.
        
        Args:
            ticker: Stock ticker
            date: Date of data
            data: Historical data point
        """
        if not self.db_service:
            self.logger.warning("Database service not available")
            return
        
        # TODO: Implement database insertion
        self.logger.debug(f"Stored historical data for {ticker} on {date}")
