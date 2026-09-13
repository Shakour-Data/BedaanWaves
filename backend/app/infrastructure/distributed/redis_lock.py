"""Distributed Lock Service - Redis-backed distributed locking.

Provides atomic lock acquisition and release using the Redis SET NX EX pattern,
suitable for coordinating work across multiple application instances.
"""

from __future__ import annotations

import logging
import secrets
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class RedisLockError(Exception):
    """Raised when a distributed lock operation fails."""


class RedisLock:
    """Atomic distributed lock backed by Redis.

    Uses ``SET key value NX EX ttl`` to acquire locks safely across multiple
    processes or hosts.  Tokens are random UUIDs so only the holder can release
    the lock.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self.redis_url = redis_url or settings.REDIS_URL
        self._client: aioredis.Redis | None = None

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            try:
                self._client = aioredis.from_url(
                    self.redis_url, socket_connect_timeout=5
                )
                await self._client.ping()
            except Exception as exc:
                logger.error("RedisLock connection failed: %s", exc)
                raise RedisLockError(f"Redis connection failed: {exc}") from exc
        return self._client

    async def acquire(self, lock_name: str, ttl_seconds: int) -> str:
        """Acquire a distributed lock.

        Args:
            lock_name: Unique identifier for the lock.
            ttl_seconds: Time-to-live in seconds before the lock auto-releases.

        Returns:
            A unique token that must be presented to release the lock.

        Raises:
            RedisLockError: If the lock cannot be acquired (already held).
        """
        token = secrets.token_urlsafe(32)
        client = await self._get_client()
        key = f"distributed_lock:{lock_name}"
        acquired = await client.set(key, token, nx=True, ex=ttl_seconds)
        if not acquired:
            raise RedisLockError(f"Failed to acquire lock: {lock_name}")
        logger.debug("Acquired lock %s (ttl=%ds)", lock_name, ttl_seconds)
        return token

    async def release(self, lock_name: str, token: str) -> bool:
        """Release a lock only if the caller holds the matching token.

        Uses a Lua script to make the check-and-delete operation atomic.

        Args:
            lock_name: The lock to release.
            token: The token returned by :meth:`acquire`.

        Returns:
            ``True`` if the lock was released, ``False`` if it was already
            released or held by another caller.
        """
        client = await self._get_client()
        key = f"distributed_lock:{lock_name}"
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        result = await client.eval(lua_script, 1, key, token)
        released = result == 1
        if released:
            logger.debug("Released lock %s", lock_name)
        return released

    async def close(self) -> None:
        """Release the underlying Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


class LockManager:
    """Manage multiple named distributed locks.

    Tracks active locks locally so they can be released or bulk-released
    without needing to remember individual tokens.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._lock = RedisLock(redis_url)
        self._active: dict[str, str] = {}

    async def acquire(self, lock_name: str, ttl_seconds: int) -> str:
        """Acquire a lock and track it internally.

        Args:
            lock_name: Unique identifier for the lock.
            ttl_seconds: Time-to-live in seconds.

        Returns:
            The lock token.

        Raises:
            RedisLockError: If the lock cannot be acquired.
        """
        token = await self._lock.acquire(lock_name, ttl_seconds)
        self._active[lock_name] = token
        return token

    async def release(self, lock_name: str) -> bool:
        """Release a tracked lock by name.

        Args:
            lock_name: The lock to release.

        Returns:
            ``True`` if released successfully.
        """
        token = self._active.pop(lock_name, None)
        if token is None:
            return False
        return await self._lock.release(lock_name, token)

    async def release_all(self) -> None:
        """Release all currently held locks."""
        for lock_name in list(self._active.keys()):
            await self.release(lock_name)

    async def close(self) -> None:
        """Release all locks and close the Redis connection."""
        await self.release_all()
        await self._lock.close()
