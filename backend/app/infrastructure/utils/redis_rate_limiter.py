from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    _SCRIPT = """
local minute_count = tonumber(redis.call('GET', KEYS[1]) or '0')
local hour_count = tonumber(redis.call('GET', KEYS[2]) or '0')
local minute_limit = tonumber(ARGV[1])
local hour_limit = tonumber(ARGV[2])
local minute_ttl = tonumber(ARGV[3])
local hour_ttl = tonumber(ARGV[4])
if minute_count >= minute_limit or hour_count >= hour_limit then
    local minute_reset = redis.call('TTL', KEYS[1])
    local hour_reset = redis.call('TTL', KEYS[2])
    if minute_reset < 0 then minute_reset = 60 end
    if hour_reset < 0 then hour_reset = 3600 end
    return {0, minute_count, hour_count, minute_reset, hour_reset}
end
minute_count = redis.call('INCR', KEYS[1])
hour_count = redis.call('INCR', KEYS[2])
redis.call('EXPIRE', KEYS[1], minute_ttl)
redis.call('EXPIRE', KEYS[2], hour_ttl)
local minute_reset = redis.call('TTL', KEYS[1])
local hour_reset = redis.call('TTL', KEYS[2])
if minute_reset < 0 then minute_reset = 60 end
if hour_reset < 0 then hour_reset = 3600 end
return {1, minute_count, hour_count, minute_reset, hour_reset}
"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        *,
        connect_timeout: float = 1.5,
        socket_timeout: float = 1.5,
        circuit_breaker_seconds: float = 30.0,
        fail_closed: bool = True,
    ) -> None:
        self.redis_url = redis_url
        self.connect_timeout = max(0.1, float(connect_timeout))
        self.socket_timeout = max(0.1, float(socket_timeout))
        self.circuit_breaker_seconds = max(0.0, float(circuit_breaker_seconds))
        self.fail_closed = fail_closed
        self._client: Any | None = None
        self._connected = False
        self._client_lock = asyncio.Lock()
        self._unavailable_until = 0.0

    async def _get_client(self) -> Any | None:
        if self._client is not None:
            return self._client
        if time.monotonic() < self._unavailable_until:
            return None

        with self._client_lock:
            if self._client is not None:
                return self._client
            if time.monotonic() < self._unavailable_until:
                return None
            try:
                import redis.asyncio as aioredis

                client = aioredis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=self.connect_timeout,
                    socket_timeout=self.socket_timeout,
                    health_check_interval=30,
                )
                await asyncio.wait_for(client.ping(), timeout=self.connect_timeout)
                self._client = client
                self._connected = True
            except Exception as exc:
                logger.warning("Redis rate limiter connection failed: %s", exc)
                self._connected = False
                self._client = None
                self._unavailable_until = time.monotonic() + self.circuit_breaker_seconds
        return self._client

    async def is_allowed(self, key: str, per_minute: int, per_hour: int) -> tuple[bool, dict[str, Any]]:
        per_minute = max(1, int(per_minute))
        per_hour = max(1, int(per_hour))
        client = await self._get_client()
        if client is None:
            info = self._unavailable_info(per_minute, per_hour)
            if self.fail_closed:
                return False, info
            return True, info

        now = int(time.time())
        minute_window = now - (now % 60)
        hour_window = now - (now % 3600)
        minute_key = f"rate_limit:{key}:minute:{minute_window}"
        hour_key = f"rate_limit:{key}:hour:{hour_window}"

        try:
            result = await asyncio.wait_for(
                client.eval(
                    self._SCRIPT,
                    2,
                    minute_key,
                    hour_key,
                    per_minute,
                    per_hour,
                    120,
                    7200,
                ),
                timeout=self.socket_timeout,
            )
            allowed = bool(int(result[0]))
            minute_count = max(0, int(result[1]))
            hour_count = max(0, int(result[2]))
            minute_reset = max(1, int(result[3]))
            hour_reset = max(1, int(result[4]))
            self._unavailable_until = 0.0
            return allowed, {
                "redis_available": True,
                "minute_count": minute_count,
                "hour_count": hour_count,
                "minute_limit": per_minute,
                "hour_limit": per_hour,
                "minute_reset": minute_reset,
                "hour_reset": hour_reset,
                "retry_after": hour_reset if not allowed and hour_count >= per_hour else minute_reset,
            }
        except Exception as exc:
            logger.warning("Redis rate limiter operation failed: %s", exc)
            await self._close_client()
            self._unavailable_until = time.monotonic() + self.circuit_breaker_seconds
            info = self._unavailable_info(per_minute, per_hour)
            if self.fail_closed:
                return False, info
            return True, info

    @staticmethod
    def _unavailable_info(per_minute: int, per_hour: int) -> dict[str, Any]:
        return {
            "redis_available": False,
            "minute_count": 0,
            "hour_count": 0,
            "minute_limit": per_minute,
            "hour_limit": per_hour,
            "minute_reset": 60,
            "hour_reset": 3600,
            "retry_after": 60,
        }

    async def _close_client(self) -> None:
        client, self._client = self._client, None
        self._connected = False
        if client is None:
            return
        close_method = getattr(client, "aclose", None) or getattr(client, "close", None)
        if close_method is None:
            return
        result = close_method()
        if result is not None:
            await result

    async def close(self) -> None:
        await self._close_client()


class InMemoryRateLimiter:
    def __init__(self, *, max_keys: int = 4096) -> None:
        self.max_keys = max(1, int(max_keys))
        self._windows: dict[str, tuple[int, int, int, int, float]] = {}
        self._lock = threading.Lock()

    async def is_allowed(self, key: str, per_minute: int, per_hour: int) -> tuple[bool, dict[str, Any]]:
        per_minute = max(1, int(per_minute))
        per_hour = max(1, int(per_hour))
        now = int(time.time())
        minute_window = now - (now % 60)
        hour_window = now - (now % 3600)
        monotonic_now = time.monotonic()

        with self._lock:
            current = self._windows.get(key)
            if current is None or current[0] != minute_window or current[1] != hour_window:
                minute_count = 0
                hour_count = 0
            else:
                minute_count = current[2]
                hour_count = current[3]

            allowed = minute_count < per_minute and hour_count < per_hour
            if allowed:
                minute_count += 1
                hour_count += 1

            self._windows[key] = (
                minute_window,
                hour_window,
                minute_count,
                hour_count,
                monotonic_now,
            )
            if len(self._windows) > self.max_keys:
                self._evict(monotonic_now)

            minute_reset = max(1, 60 - (now % 60))
            hour_reset = max(1, 3600 - (now % 3600))
            return allowed, {
                "redis_available": False,
                "minute_count": minute_count,
                "hour_count": hour_count,
                "minute_limit": per_minute,
                "hour_limit": per_hour,
                "minute_reset": minute_reset,
                "hour_reset": hour_reset,
                "retry_after": hour_reset if not allowed and hour_count >= per_hour else minute_reset,
            }

    def _evict(self, now: float) -> None:
        if len(self._windows) <= self.max_keys:
            return
        active = sorted(self._windows.items(), key=lambda item: item[1][4])
        remove_count = len(active) - self.max_keys
        for key, _ in active[:remove_count]:
            self._windows.pop(key, None)

    async def close(self) -> None:
        with self._lock:
            self._windows.clear()
