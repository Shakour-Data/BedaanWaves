"""Crypto Market API Client - Tier 2 Data Service

Minimal clients for public crypto market data (CoinGecko + Binance).
"""
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging

import aiohttp

from ..core import ExternalAPIService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class CryptoApiClient(ExternalAPIService):
    """Public crypto market data client."""

    def __init__(
        self,
        service_name: str = "CryptoApiClient",
        base_url: str = "https://api.coingecko.com/api/v3",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        super().__init__(
            service_name=service_name,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.session: Optional[aiohttp.ClientSession] = None
        self.binance_base = "https://api.binance.com/api/v3"

    async def initialize(self) -> None:
        self.session = aiohttp.ClientSession()
        self.logger.info("CryptoApiClient initialized")

    async def shutdown(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
        self.logger.info("CryptoApiClient shutdown")

    async def _request(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
    ) -> Any:
        if not self.session:
            raise RuntimeError("CryptoApiClient not initialized")
        if params is None:
            params = {}

        url = f"{base_url or self.base_url}{path}"
        headers = {"User-Agent": _BROWSER_USER_AGENT}

        for attempt in range(self.max_retries):
            try:
                async with self.session.get(
                    url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 429:
                        await asyncio.sleep(min(2 ** attempt, 60))
                        continue
                    if response.status >= 500 and attempt < self.max_retries - 1:
                        await asyncio.sleep(min(2 ** attempt, 30))
                        continue

                    data = await response.json()
                    if response.status == 200:
                        return data
                    raise RuntimeError(f"CryptoApi error {response.status}: {data}")
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning("Retry %s/%s: %s", attempt + 1, self.max_retries, e)
                    await asyncio.sleep(min(2 ** attempt, 30))
                else:
                    self.logger.error("CryptoApi request failed: %s", e)
                    raise
        raise RuntimeError("CryptoApi max retries exceeded")

    async def get_simple_price(self, symbol: str, vs_currency: str = "usd") -> Dict[str, Any]:
        """Get simple price from CoinGecko."""
        symbol = symbol.lower()
        return await self._request(
            "/simple/price",
            {"ids": symbol, "vs_currencies": vs_currency},
        )

    async def get_ohlc(self, symbol: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get OHLC candles from CoinGecko."""
        symbol = symbol.lower()
        return await self._request(
            f"/coins/{symbol}/ohlc",
            {"vs_currency": "usd", "days": str(days)},
        )

    async def get_binance_ticker(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Get 24h ticker from Binance."""
        return await self._request(
            "/ticker/24hr",
            {"symbol": symbol.upper()},
            base_url=self.binance_base,
        )

    async def get_binance_depth(self, symbol: str = "BTCUSDT", limit: int = 100) -> Dict[str, Any]:
        """Get order book depth from Binance."""
        return await self._request(
            "/depth",
            {"symbol": symbol.upper(), "limit": limit},
            base_url=self.binance_base,
        )

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search crypto assets on CoinGecko."""
        data = await self._request("/search", {"query": query})
        return data.get("coins", [])
