"""Crypto Price Service - Tier 8 Crypto Service

Provides price data for cryptocurrency assets.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from ..core import CachedService
from ..data.crypto_api_client import CryptoApiClient


class CryptoPriceService(CachedService):
    """Cryptocurrency price data service."""

    def __init__(
        self,
        service_name: str = "CryptoPriceService",
        crypto_client: Optional[CryptoApiClient] = None,
        cache_ttl_seconds: int = 60,
    ):
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.crypto_client = crypto_client

    async def initialize(self) -> None:
        self.logger.info("CryptoPriceService initialized")

    async def shutdown(self) -> None:
        self.cache_clear()
        self.logger.info("CryptoPriceService shutdown")

    async def get_price(self, symbol: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get current price for a crypto asset."""
        cache_key = f"crypto:price:{symbol}:{vs_currency}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        if not self.crypto_client:
            raise RuntimeError("Crypto API client not initialized")

        data = await self.crypto_client.get_simple_price(symbol, vs_currency)
        self.set_cached(cache_key, data)
        return data

    async def get_ohlc(self, symbol: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get OHLC candles for a crypto asset."""
        cache_key = f"crypto:ohlc:{symbol}:{days}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        if not self.crypto_client:
            raise RuntimeError("Crypto API client not initialized")

        data = await self.crypto_client.get_ohlc(symbol, days)
        self.set_cached(cache_key, data)
        return data

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search crypto assets."""
        if not self.crypto_client:
            raise RuntimeError("Crypto API client not initialized")
        return await self.crypto_client.search(query)
