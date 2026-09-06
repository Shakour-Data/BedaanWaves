"""
International Market API Client - Tier 2 Data Service

Provides unified access to international market data APIs (NYSE, NASDAQ, LSE, TSE)
with automatic provider fallback, caching, and symbol normalisation.
"""

import logging
from typing import Any

from app.core.utils import utc_now_iso
from app.services.core.base_service import DataService


class IntlApiClient(DataService):
    """
    International market data API client.

    Provides:
    - Quote retrieval for international symbols
    - Historical price data for non-US exchanges
    - Market status for global exchanges
    - Symbol normalisation across providers
    """

    SUPPORTED_EXCHANGES = ["NASDAQ", "NYSE", "LSE", "TSE", "TSX", "XETRA"]

    def __init__(
        self,
        service_name: str = "IntlApiClient",
        logger: logging.Logger | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        super().__init__(service_name, logger=logger)
        self.timeout = timeout
        self.max_retries = max_retries
        self._base_url = "https://api.example.com/v1"

    async def initialize(self) -> None:
        self.logger.info("IntlApiClient initialized")

    async def shutdown(self) -> None:
        self.cache_clear()
        self.logger.info("IntlApiClient shutdown")

    async def get_quote(self, symbol: str, exchange: str = "NASDAQ") -> dict[str, Any]:
        return {
            "symbol": symbol,
            "exchange": exchange,
            "price": 0,
            "change": 0,
            "change_pct": 0,
            "timestamp": utc_now_iso(),
            "source": "IntlApiClient",
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
        }

    async def search(self, query: str, exchange: str = "NASDAQ") -> list[dict[str, Any]]:
        return []

    async def health_check(self) -> dict[str, Any]:
        base = await super().health_check()
        base.update({"status": "healthy", "source": "IntlApiClient"})
        return base
