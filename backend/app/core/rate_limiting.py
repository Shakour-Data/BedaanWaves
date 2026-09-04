"""Rate Limiting Module for API Endpoints

Provides rate limiting decorators and utilities for API endpoints.
"""

import time
from functools import wraps
from threading import Lock
from collections import defaultdict
from typing import Callable, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket style rate limiter for API endpoints."""

    def __init__(
        self,
        requests_per_minute: int = 100,
        requests_per_hour: int = 5000,
        key_prefix: str = "rate_limit"
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.key_prefix = key_prefix
        self._buckets: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "minute_count": 0,
                "minute_reset": time.time() + 60,
                "hour_count": 0,
                "hour_reset": time.time() + 3600,
            }
        )
        self._lock = Lock()

    def _cleanup(self, key: str) -> None:
        """Periodically clean up old bucket data."""
        now = time.time()
        bucket = self._buckets.get(key)
        if bucket and now > bucket["hour_reset"] + 3600:
            del self._buckets[key]

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed based on rate limits."""
        now = time.time()

        with self._lock:
            bucket = self._buckets[key]

            # Reset minute counter if expired
            if now >= bucket["minute_reset"]:
                bucket["minute_count"] = 0
                bucket["minute_reset"] = now + 60

            # Reset hour counter if expired
            if now >= bucket["hour_reset"]:
                bucket["hour_count"] = 0
                bucket["hour_reset"] = now + 3600

            # Clean up expired buckets
            self._cleanup(key)

            # Check limits
            if bucket["minute_count"] >= self.requests_per_minute:
                return False
            if bucket["hour_count"] >= self.requests_per_hour:
                return False

            # Increment counters
            bucket["minute_count"] += 1
            bucket["hour_count"] += 1

            return True


def rate_limit(
    requests_per_minute: int = 100,
    requests_per_hour: int = 5000,
    key_prefix: str = "rate_limit",
    # Aliases for backward compatibility
    limit: Optional[int] = None,
    window: Optional[int] = None
) -> Callable:
    """
    Rate limiting decorator for FastAPI endpoints.

    Args:
        requests_per_minute: Maximum requests per minute
        requests_per_hour: Maximum requests per hour
        key_prefix: Prefix for rate limit keys
        limit: Alias for requests_per_minute (backward compat)
        window: Alias for requests_per_hour time window in seconds (backward compat)

    Usage:
        @router.get("/endpoint")
        @rate_limit(requests_per_minute=60, requests_per_hour=1000)
        async def endpoint():
            return {"data": "value"}
    """
    # Support backward compatible parameter names
    if limit is not None:
        requests_per_minute = limit
    if window is not None:
        requests_per_hour = max(1, int(3600 * requests_per_minute / window))
    limiter = RateLimiter(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        key_prefix=key_prefix
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            key = f"{key_prefix}:{func.__name__}"
            if args and hasattr(args[0], "client") and hasattr(args[0].client, "host"):
                key = f"{key_prefix}:{args[0].client.host}:{func.__name__}"

            if not limiter.is_allowed(key):
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator