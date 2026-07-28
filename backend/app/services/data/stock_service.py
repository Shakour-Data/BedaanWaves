"""
Stock Service - Tier 2 Data Service

Manages stock data and operations.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
from ..core import CachedService


class StockService(CachedService):
    """
    Stock data management service.
    
    Provides:
    - Stock information retrieval
    - Price data management
    - Stock search
    - Batch stock operations
    """
    
    def __init__(
        self,
        service_name: str = "StockService",
        brs_client=None,
        cache_ttl_seconds: int = 3600,
    ):
        """
        Initialize stock service.
        
        Args:
            service_name: Service identifier
            brs_client: BRS API client instance
            cache_ttl_seconds: Cache TTL
        """
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.brs_client = brs_client
    
    async def initialize(self) -> None:
        """Initialize stock service"""
        self.logger.info("StockService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown stock service"""
        self.cache_clear()
        self.logger.info("StockService shutdown")
    
    async def get_stock(self, ticker: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get stock information.
        
        Args:
            ticker: Stock ticker
            use_cache: Use cached data if available
            
        Returns:
            Stock information
        """
        cache_key = f"stock:{ticker}"
        
        if use_cache:
            cached = self.get_cached(cache_key)
            if cached:
                return cached
        
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        
        stock_data = await self.brs_client.get_stock_info(ticker)
        self.set_cached(cache_key, stock_data)
        
        return stock_data
    
    async def get_price(self, ticker: str) -> Dict[str, float]:
        """
        Get current stock price.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Price data {open, high, low, close, last}
        """
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        
        return await self.brs_client.get_stock_price(ticker)
    
    async def get_history(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "daily",
    ) -> List[Dict[str, Any]]:
        """
        Get historical stock data.
        
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
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search stocks.
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        
        cache_key = f"search:{query}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        results = await self.brs_client.search_stocks(query)
        self.set_cached(cache_key, results)
        
        return results
    
    async def get_multiple(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple stocks.
        
        Args:
            tickers: List of stock tickers
            
        Returns:
            Dictionary of {ticker: stock_data}
        """
        results = {}
        for ticker in tickers:
            try:
                results[ticker] = await self.get_stock(ticker)
            except Exception as e:
                self.logger.error(f"Error getting stock {ticker}: {e}")
                results[ticker] = {"error": str(e)}
        
        return results
