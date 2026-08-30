import logging
import asyncio
from typing import Any, Optional
from datetime import datetime, timedelta, timezone

from ...application.interfaces.i_cache_backend import ICacheBackend

logger = logging.getLogger(__name__)


class RedisCacheBackend(ICacheBackend):
    """
    Redis-backed cache backend.
    Uses redis.asyncio for non-blocking operations.
    Gracefully falls back if Redis is unavailable.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._redis_url = redis_url
        self._client = None
        self._connected = False
        self._lock = asyncio.Lock()

    async def _ensure_connection(self) -> bool:
        if self._connected and self._client is not None:
            return True
        async with self._lock:
            if self._connected and self._client is not None:
                return True
            try:
                import redis.asyncio as aioredis
                self._client = aioredis.from_url(
                    self._redis_url,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    decode_responses=False,
                    health_check_interval=30,
                )
                await self._client.ping()
                self._connected = True
                logger.info("RedisCacheBackend connected to Redis")
                return True
            except Exception as exc:
                logger.warning(f"Redis connection failed: {exc}")
                self._client = None
                self._connected = False
                return False

    async def get(self, key: str) -> Optional[Any]:
        if not await self._ensure_connection():
            return None
        try:
            value = await self._client.get(key)
            if value is None:
                return None
            return self._deserialize(value)
        except Exception as exc:
            logger.debug(f"Redis get failed for {key}: {exc}")
            self._connected = False
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not await self._ensure_connection():
            return
        try:
            serialized = self._serialize(value)
            if ttl is not None:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
        except Exception as exc:
            logger.debug(f"Redis set failed for {key}: {exc}")
            self._connected = False

    async def delete(self, key: str) -> None:
        if not await self._ensure_connection():
            return
        try:
            await self._client.delete(key)
        except Exception as exc:
            logger.debug(f"Redis delete failed for {key}: {exc}")
            self._connected = False

    async def clear(self) -> None:
        if not await self._ensure_connection():
            return
        try:
            await self._client.flushdb()
        except Exception as exc:
            logger.debug(f"Redis clear failed: {exc}")
            self._connected = False

    async def exists(self, key: str) -> bool:
        if not await self._ensure_connection():
            return False
        try:
            result = await self._client.exists(key)
            return result == 1
        except Exception as exc:
            logger.debug(f"Redis exists failed for {key}: {exc}")
            self._connected = False
            return False

    async def shutdown(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None
            self._connected = False

    def _serialize(self, value: Any) -> bytes:
        import json
        return json.dumps(value, default=str).encode("utf-8")

    def _deserialize(self, raw: bytes) -> Any:
        import json
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return raw
