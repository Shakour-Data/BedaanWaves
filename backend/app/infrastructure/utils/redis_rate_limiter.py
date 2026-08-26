import time
import logging

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Redis-backed distributed rate limiter using sorted sets."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._client = None
        self._connected = False

    async def _get_client(self):
        if self._client is None:
            try:
                import redis.asyncio as aioredis
                self._client = aioredis.from_url(self.redis_url, socket_connect_timeout=5)
                await self._client.ping()
                self._connected = True
            except Exception as exc:
                logger.warning(f"Redis rate limiter connection failed: {exc}")
                self._connected = False
                self._client = None
        return self._client

    async def is_allowed(self, key: str, per_minute: int, per_hour: int) -> tuple[bool, dict]:
        now = time.time()
        client = await self._get_client()
        if client is None:
            return True, {"redis_available": False}

        minute_key = f"rate_limit:{key}:minute"
        hour_key = f"rate_limit:{key}:hour"
        pipeline = client.pipeline()

        minute_ts = int(now)
        hour_ts = int(now / 3600)

        pipeline.zadd(minute_key, {str(minute_ts): minute_ts})
        pipeline.zremrangebyscore(minute_key, 0, now - 60)
        pipeline.zcard(minute_key)

        pipeline.zadd(hour_key, {str(hour_ts): hour_ts})
        pipeline.zremrangebyscore(hour_key, 0, now - 3600)
        pipeline.zcard(hour_key)

        results = await pipeline.execute()
        minute_count = results[2]
        hour_count = results[5]

        minute_allowed = minute_count < per_minute
        hour_allowed = hour_count < per_hour

        if minute_allowed:
            await client.expire(minute_key, 120)
        if hour_allowed:
            await client.expire(hour_key, 7200)

        return minute_allowed and hour_allowed, {
            "redis_available": True,
            "minute_count": minute_count,
            "hour_count": hour_count,
            "minute_limit": per_minute,
            "hour_limit": per_hour,
        }

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
            self._connected = False
