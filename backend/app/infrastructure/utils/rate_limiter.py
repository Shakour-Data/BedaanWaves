import asyncio
import time
from typing import List
from ...application.interfaces.i_logger import ILogger

class RateLimiter:
    """
    Infrastructure implementation of a simple sliding window rate limiter.
    """
    
    def __init__(self, logger: ILogger, max_requests: int = 100, time_window: int = 60):
        self._logger = logger
        self._max_requests = max_requests
        self._time_window = time_window
        self._request_times: List[float] = []

    async def acquire(self) -> None:
        """Wait if rate limit is reached, then record new request."""
        now = time.time()
        self._clean_window(now)
        
        if len(self._request_times) >= self._max_requests:
            sleep_time = self._time_window - (now - self._request_times[0])
            if sleep_time > 0:
                self._logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                now = time.time()
                self._clean_window(now)
        
        self._request_times.append(now)

    def _clean_window(self, current_time: float):
        self._request_times = [t for t in self._request_times if current_time - t < self._time_window]
