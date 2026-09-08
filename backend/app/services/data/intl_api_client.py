"""
International Market API Client - Tier 2 Data Service

Provides unified access to international market data APIs (NYSE, NASDAQ, LSE, TSX)
with automatic provider fallback, caching, and symbol normalisation.

When INTL_API_KEY is set in the environment, IntlApiClient makes real HTTP
requests to the configured provider.  When no key is available, the client
degrades gracefully and returns empty results (no fake data).  For testing
and development, MockIntlApiClient provides explicit stub responses.
"""

import logging
from typing import Any

import httpx

from app.core.utils import utc_now_iso
from app.services.core.base_service import DataService, ExternalAPIService


class IntlApiClient(ExternalAPIService):
    """
    International market data API client (real implementation).

    Makes HTTP requests to a real international market-data provider when
    an API key is configured.  Without a key the client returns empty
    results instead of mock data.
    """

    SUPPORTED_EXCHANGES = ["NASDAQ", "NYSE", "LSE", "TSX", "XETRA"]
    DEFAULT_BASE_URL = "https://api.twelvedata.com"

    def __init__(
        self,
        service_name: str = "IntlApiClient",
        logger: logging.Logger | None = None,
        timeout: int = 30,
        max_retries: int = 3,
        api_key: str | None = None,
    ):
        import os
        key = api_key or os.environ.get("INTL_API_KEY")
        super().__init__(
            service_name=service_name,
            base_url=self.DEFAULT_BASE_URL,
            logger=logger,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._api_key = key
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def initialize(self) -> None:
        if self._api_key:
            self.logger.info("IntlApiClient initialized with real API connection")
        else:
            self.logger.info("IntlApiClient initialized in offline mode (no INTL_API_KEY)")

    async def shutdown(self) -> None:
        self.cache_clear()
        await self._client.aclose()
        self.logger.info("IntlApiClient shutdown")

    def _is_online(self) -> bool:
        return self._api_key is not None

    async def fetch(self, endpoint: str, method: str = "GET", **kwargs) -> dict[str, Any]:
        raise NotImplementedError

    async def get_quote(self, symbol: str, exchange: str = "NASDAQ") -> dict[str, Any]:
        if not self._is_online():
            self.logger.warning("No API key configured; returning empty quote")
            return {
                "symbol": symbol,
                "exchange": exchange,
                "price": None,
                "change": None,
                "change_pct": None,
                "timestamp": utc_now_iso(),
                "source": "IntlApiClient",
            }
        try:
            params = {"symbol": symbol, "apikey": self._api_key}
            resp = await self._client.get(f"{self.base_url}/quote", params=params)
            resp.raise_for_status()
            data = resp.json()
            return {
                "symbol": symbol,
                "exchange": exchange,
                "price": float(data.get("price", 0)),
                "change": float(data.get("change", 0)),
                "change_pct": float(data.get("percent_change", 0)),
                "timestamp": utc_now_iso(),
                "source": "IntlApiClient",
            }
        except Exception as exc:
            self.logger.warning(f"IntlApiClient quote fetch failed for {symbol}: {exc}")
            return {
                "symbol": symbol,
                "exchange": exchange,
                "price": None,
                "change": None,
                "change_pct": None,
                "timestamp": utc_now_iso(),
                "source": "IntlApiClient",
            }

    async def get_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> list[dict[str, Any]]:
        if not self._is_online():
            self.logger.warning("No API key configured; returning empty history")
            return []
        try:
            params = {"symbol": symbol, "interval": interval, "apikey": self._api_key}
            resp = await self._client.get(f"{self.base_url}/time_series", params=params)
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "timestamp": k,
                    "open": float(v["open"]),
                    "high": float(v["high"]),
                    "low": float(v["low"]),
                    "close": float(v["close"]),
                    "volume": float(v.get("volume", 0)),
                }
                for k, v in data.get("values", {}).items()
            ]
        except Exception as exc:
            self.logger.warning(f"IntlApiClient history fetch failed for {symbol}: {exc}")
            return []

    async def get_market_status(self, exchange: str) -> dict[str, Any]:
        if not self._is_online():
            return {
                "exchange": exchange,
                "status": "unknown",
                "timestamp": utc_now_iso(),
                "source": "IntlApiClient",
            }
        try:
            params = {"apikey": self._api_key}
            resp = await self._client.get(f"{self.base_url}/market_status", params=params)
            resp.raise_for_status()
            data = resp.json()
            return {
                "exchange": exchange,
                "status": data.get("market_status", "unknown"),
                "timestamp": utc_now_iso(),
                "source": "IntlApiClient",
            }
        except Exception as exc:
            self.logger.warning(f"IntlApiClient market status fetch failed for {exchange}: {exc}")
            return {
                "exchange": exchange,
                "status": "unknown",
                "timestamp": utc_now_iso(),
                "source": "IntlApiClient",
            }

    async def search(self, query: str, exchange: str = "NASDAQ") -> list[dict[str, Any]]:
        if not self._is_online():
            self.logger.warning("No API key configured; returning empty search")
            return []
        try:
            params = {"query": query, "apikey": self._api_key}
            resp = await self._client.get(f"{self.base_url}/symbol_search", params=params)
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "symbol": item.get("symbol"),
                    "name": item.get("name"),
                    "exchange": exchange,
                    "type": item.get("type"),
                }
                for item in data.get("data", [])
            ]
        except Exception as exc:
            self.logger.warning(f"IntlApiClient search failed for {query}: {exc}")
            return []

    async def health_check(self) -> dict[str, Any]:
        base = await super().health_check()
        base.update({"status": "healthy" if self._is_online() else "offline", "source": "IntlApiClient"})
        return base


class MockIntlApiClient(DataService):
    """
    Mock implementation of the international market data client.

    Returns stub responses for development and testing.
    The real implementation is IntlApiClient above.
    """

    SUPPORTED_EXCHANGES = IntlApiClient.SUPPORTED_EXCHANGES

    def __init__(
        self,
        service_name: str = "MockIntlApiClient",
        logger: logging.Logger | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        super().__init__(service_name, logger=logger)
        self.timeout = timeout
        self.max_retries = max_retries

    async def initialize(self) -> None:
        self.logger.info("MockIntlApiClient initialized")

    async def shutdown(self) -> None:
        self.cache_clear()
        self.logger.info("MockIntlApiClient shutdown")

    async def get_quote(self, symbol: str, exchange: str = "NASDAQ") -> dict[str, Any]:
        return {
            "symbol": symbol,
            "exchange": exchange,
            "price": 0,
            "change": 0,
            "change_pct": 0,
            "timestamp": utc_now_iso(),
            "source": "MockIntlApiClient",
        }

    async def get_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> list[dict[str, Any]]:
        return []

    async def get_market_status(self, exchange: str) -> dict[str, Any]:
        return {
            "exchange": exchange,
            "status": "unknown",
            "timestamp": utc_now_iso(),
            "source": "MockIntlApiClient",
        }

    async def search(self, query: str, exchange: str = "NASDAQ") -> list[dict[str, Any]]:
        return []

    async def health_check(self) -> dict[str, Any]:
        base = await super().health_check()
        base.update({"status": "healthy", "source": "MockIntlApiClient"})
        return base
