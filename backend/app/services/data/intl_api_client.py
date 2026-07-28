"""International Stock Exchange API Client - Tier 2 Data Service

Minimal client scaffold for NYSE/NASDAQ/LSE/XETRA market data.
Real implementations require specific vendor APIs (polygon.io, twelvedata, etc.).
"""
from typing import Any, Dict, List, Optional
import logging

import aiohttp

from ..core import ExternalAPIService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class IntlApiClient(ExternalAPIService):
    """International stock market data client."""

    def __init__(
        self,
        service_name: str = "IntlApiClient",
        base_url: str = "https://api.twelvedata.com",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        super().__init__(
            service_name=service_name,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.api_key = api_key or getattr(settings, "INTL_API_KEY", None)
        self.session = None

    async def initialize(self) -> None:
        self.session = aiohttp.ClientSession()
        self.logger.info("IntlApiClient initialized")

    async def shutdown(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
        self.logger.info("IntlApiClient shutdown")

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("Intl quote requires vendor API configuration")

    async def get_history(self, symbol: str, interval: str = "1d", outputsize: int = 100) -> List[Dict[str, Any]]:
        raise NotImplementedError("Intl history requires vendor API configuration")

    async def search(self, query: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("Intl search requires vendor API configuration")
