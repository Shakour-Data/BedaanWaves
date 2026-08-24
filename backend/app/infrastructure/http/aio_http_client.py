import aiohttp
import asyncio
from typing import Any, Dict, Optional
from ...application.interfaces.i_http_client import IHttpClient
from ...application.interfaces.i_logger import ILogger
from ...domain.shared.result import Result

class AioHttpClient(IHttpClient):
    """
    Infrastructure implementation of IHttpClient using aiohttp.
    Handles retries, timeouts, and structured logging.
    """
    
    def __init__(self, logger: ILogger, timeout: int = 30, max_retries: int = 3):
        self._logger = logger
        self._timeout = timeout
        self._max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None) -> Result[Any]:
        return await self._request("GET", url, params=params, headers=headers)

    async def post(self, url: str, data: Any = None, json: Any = None, headers: Optional[Dict[str, Any]] = None) -> Result[Any]:
        return await self._request("POST", url, data=data, json=json, headers=headers)

    async def _request(self, method: str, url: str, **kwargs) -> Result[Any]:
        session = await self._get_session()
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        
        for attempt in range(self._max_retries):
            try:
                async with session.request(method, url, timeout=timeout, **kwargs) as response:
                    if response.status == 429:
                        await self._handle_rate_limit(attempt)
                        continue
                        
                    data = await response.json()
                    if 200 <= response.status < 300:
                        return Result.success(data)
                        
                    return Result.failure(f"HTTP {response.status}: {data}", "HTTP_ERROR")
            except Exception as e:
                if attempt == self._max_retries - 1:
                    self._logger.error(f"HTTP request failed: {url}", error=e)
                    return Result.failure(str(e), "NETWORK_ERROR")
                await asyncio.sleep(2 ** attempt)
        
        return Result.failure("Max retries exceeded", "MAX_RETRIES_EXCEEDED")

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _handle_rate_limit(self, attempt: int):
        wait_time = min(2 ** attempt, 60)
        self._logger.warning(f"Rate limited. Waiting {wait_time}s...")
        await asyncio.sleep(wait_time)

    async def shutdown(self):
        if self._session and not self._session.closed:
            await self._session.close()
