"""
Market Service - Tier 2 Data Service

Market data aggregation and analysis.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from ..core import CachedService


class MarketService(CachedService):
    """
    Market data management service.
    
    Provides:
    - Market indices
    - Market statistics
    - Top performers
    - Market trends
    """
    
    def __init__(
        self,
        service_name: str = "MarketService",
        brs_client=None,
        cache_ttl_seconds: int = 300,  # 5 minute cache
    ):
        """
        Initialize market service.
        
        Args:
            service_name: Service identifier
            brs_client: BRS API client
            cache_ttl_seconds: Cache TTL
        """
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.brs_client = brs_client
    
    async def initialize(self) -> None:
        """Initialize market service"""
        self.logger.info("MarketService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown market service"""
        self.cache_clear()
        self.logger.info("MarketService shutdown")
    
    async def get_indices(self) -> List[Dict[str, Any]]:
        """
        Get market indices.
        
        Returns:
            List of indices data
        """
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        
        cached = self.get_cached("market_indices")
        if cached:
            return cached
        
        indices = await self.brs_client.get_market_indices()
        self.set_cached("market_indices", indices)
        
        return indices
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get market statistics.
        
        Returns:
            Market statistics
        """
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        
        cached = self.get_cached("market_stats")
        if cached:
            return cached
        
        stats = await self.brs_client.get_market_stats()
        self.set_cached("market_stats", stats)
        
        return stats
    
    async def get_gainers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top gainers"""
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        
        cache_key = f"gainers_{limit}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        gainers = await self.brs_client.get_top_gainers(limit)
        self.set_cached(cache_key, gainers)
        
        return gainers
    
    async def get_losers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top losers"""
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        
        cache_key = f"losers_{limit}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        losers = await self.brs_client.get_top_losers(limit)
        self.set_cached(cache_key, losers)
        
        return losers
    
    async def get_most_active(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most active stocks"""
        if not self.brs_client:
            raise RuntimeError("BRS client not initialized")
        
        cache_key = f"most_active_{limit}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached
        
        active = await self.brs_client.get_most_active(limit)
        self.set_cached(cache_key, active)
        
        return active
