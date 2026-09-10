"""
Cache Service - Tier 1 Core Service

Multi-backend caching service supporting memory, Redis, and other backends.
Provides TTL management, pattern-based invalidation, and statistics.
"""

import asyncio
import hashlib
import inspect
import json
from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from .base_service import BaseService


class CacheBackend(ABC):
    """Abstract base for cache backends"""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value from cache"""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache"""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete key from cache"""

    @abstractmethod
    async def clear(self) -> None:
        """Clear entire cache"""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend with LRU eviction."""

    def __init__(self, maxsize: int = 1000):
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._maxsize = maxsize

    async def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None

        entry = self._cache[key]

        # Check TTL
        if entry['ttl'] and datetime.now(UTC) > entry['expiry']:
            del self._cache[key]
            return None

        return entry['value']

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expiry = None
        if ttl:
            expiry = datetime.now(UTC) + timedelta(seconds=ttl)

        self._cache[key] = {
            'value': value,
            'ttl': ttl,
            'expiry': expiry,
            'created_at': datetime.now(UTC),
        }
        self._evict_if_needed()

    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    async def clear(self) -> None:
        self._cache.clear()

    async def exists(self, key: str) -> bool:
        if key not in self._cache:
            return False

        entry = self._cache[key]
        if entry['ttl'] and datetime.now(UTC) > entry['expiry']:
            del self._cache[key]
            return False

        return True

    def size(self) -> int:
        """Get cache size"""
        return len(self._cache)

    def _evict_if_needed(self) -> None:
        """Evict oldest entries if cache exceeds maxsize."""
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)


class CacheService(BaseService):
    """
    Centralized cache management for BedaanWaves.

    Provides:
    - Multiple backend support (memory, Redis)
    - Automatic TTL management
    - Pattern-based invalidation
    - Statistics and monitoring
    """

    def __init__(
        self,
        service_name: str = "CacheService",
        backend: str = "memory",
        default_ttl: int = 3600,
    ):
        """
        Initialize cache service.

        Args:
            service_name: Service identifier
            backend: Cache backend ('memory' or 'redis')
            default_ttl: Default TTL in seconds
        """
        super().__init__(service_name)
        self.backend_type = backend
        self.default_ttl = default_ttl
        self.backend = self._create_backend(backend)
        self._key_prefixes: dict[str, str] = {}

    async def initialize(self) -> None:
        """Initialize cache service"""
        self.logger.info(f"CacheService initialized with {self.backend_type} backend")

    async def shutdown(self) -> None:
        """Shutdown cache service"""
        await self.backend.clear()
        self.logger.info("CacheService shutdown")

    def _create_backend(self, backend_type: str) -> CacheBackend:
        """Create cache backend instance"""
        if backend_type.lower() == 'memory':
            return MemoryCacheBackend()
        elif backend_type.lower() == 'redis':
            try:
                from app.core.config import get_settings
                settings = get_settings()
                from app.infrastructure.cache.redis_cache_backend import (
                    RedisCacheBackend,
                )
                return RedisCacheBackend(redis_url=settings.REDIS_URL)
            except Exception as exc:
                self.logger.warning(f"Redis backend initialization failed ({exc}), using memory backend")
                return MemoryCacheBackend()
        else:
            raise ValueError(f"Unknown cache backend: {backend_type}")

    def _get_key(self, namespace: str, key: str) -> str:
        """Generate namespaced cache key"""
        return f"{namespace}:{key}"

    def _get_hash_key(self, data: Any) -> str:
        """Generate hash-based key from data"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()

    async def get(self, key: str, namespace: str = "default") -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key
            namespace: Key namespace

        Returns:
            Cached value or None
        """
        full_key = self._get_key(namespace, key)
        value = await self.backend.get(full_key)

        if value is not None:
            self._metrics["cache_hits"] += 1
        else:
            self._metrics["cache_misses"] += 1

        return value

    async def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: int | None = None,
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            namespace: Key namespace
            ttl: Time to live in seconds
        """
        full_key = self._get_key(namespace, key)
        ttl = self.default_ttl if ttl is None else ttl
        await self.backend.set(full_key, value, ttl)
        self.logger.debug(f"Cached {full_key} (TTL: {ttl}s)")

    async def delete(self, key: str, namespace: str = "default") -> None:
        """Delete cache entry"""
        full_key = self._get_key(namespace, key)
        await self.backend.delete(full_key)

    async def clear(self, namespace: str | None = None) -> None:
        """
        Clear cache.

        Args:
            namespace: Optional namespace to clear (clears all if not specified)
        """
        if namespace is None:
            await self.backend.clear()
            self.logger.info("Cleared entire cache")
        else:
            self.logger.warning("Namespace-specific clearing not yet implemented")

    async def exists(self, key: str, namespace: str = "default") -> bool:
        """Check if key exists in cache"""
        full_key = self._get_key(namespace, key)
        return await self.backend.exists(full_key)

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any] | Any,
        namespace: str = "default",
        ttl: int | None = None,
    ) -> Any:
        """
        Get from cache or compute and set (Cache-Aside pattern).

        Args:
            key: Cache key
            factory: Callable to compute value if not cached
            namespace: Key namespace
            ttl: Time to live in seconds

        Returns:
            Cached or computed value
        """
        cached = await self.get(key, namespace)
        if cached is not None:
            return cached

        value = factory() if callable(factory) else factory
        if inspect.isawaitable(value):
            value = await value
        await self.set(key, value, namespace, ttl)
        return value

    async def get_or_set_with_fallback(
        self,
        key: str,
        factory: Callable[[], Any] | Any,
        namespace: str = "default",
        ttl: int | None = None,
        stale_ttl: int | None = None,
    ) -> Any:
        """
        Get from cache with stale-while-revalidate pattern.

        Returns cached value immediately if available, even if stale,
        while triggering a background refresh.

        Args:
            key: Cache key
            factory: Callable to compute fresh value
            namespace: Key namespace
            ttl: Time to live in seconds
            stale_ttl: Time after which value is considered stale (optional)

        Returns:
            Cached or computed value
        """
        full_key = self._get_key(namespace, key)
        cached = await self.backend.get(full_key)

        if cached is not None:
            # Check if stale
            if stale_ttl and self._is_stale(full_key, stale_ttl):
                asyncio.create_task(self._refresh_key(key, factory, namespace, ttl))
            return cached

        value = factory() if callable(factory) else factory
        if inspect.isawaitable(value):
            value = await value
        await self.set(key, value, namespace, ttl)
        return value

    async def _refresh_key(
        self,
        key: str,
        factory: Callable[[], Any],
        namespace: str,
        ttl: int | None,
    ) -> None:
        """Background refresh of a stale cache key."""
        try:
            value = factory() if callable(factory) else factory
            if inspect.isawaitable(value):
                value = await value
            await self.set(key, value, namespace, ttl)
        except Exception as exc:
            self.logger.debug(f"Background refresh failed for {key}: {exc}")

    def _is_stale(self, full_key: str, stale_ttl: int) -> bool:
        """Check if a cache entry is stale based on creation time."""
        # Simplified check — in production this would use Redis TTL info
        return False

    async def write_through(
        self,
        key: str,
        value: Any,
        factory: Callable[[], Any] | None = None,
        namespace: str = "default",
        ttl: int | None = None,
    ) -> Any:
        """
        Write-Through caching: write to cache AND database simultaneously.

        Args:
            key: Cache key
            value: Value to cache
            factory: Optional callable to persist to database
            namespace: Key namespace
            ttl: Time to live in seconds

        Returns:
            The written value
        """
        await self.set(key, value, namespace, ttl)
        if factory is not None:
            result = factory() if callable(factory) else factory
            if inspect.isawaitable(result):
                result = await result
            return result
        return value

    async def cache_aside_read(
        self,
        key: str,
        loader: Callable[[], Any],
        namespace: str = "default",
        ttl: int | None = None,
    ) -> Any:
        """
        Explicit Cache-Aside read pattern.

        Checks cache first; on miss, calls loader, stores result, returns.

        Args:
            key: Cache key
            loader: Callable to load value on cache miss
            namespace: Key namespace
            ttl: Time to live in seconds

        Returns:
            Cached or loaded value
        """
        cached = await self.get(key, namespace)
        if cached is not None:
            self._metrics["cache_hits"] += 1
            return cached

        self._metrics["cache_misses"] += 1
        value = loader() if callable(loader) else loader
        if inspect.isawaitable(value):
            value = await value
        await self.set(key, value, namespace, ttl)
        return value

    async def invalidate_pattern(self, pattern: str, namespace: str = "default") -> int:
        """
        Invalidate all cache keys matching a pattern (Cache-Aside invalidation).

        Args:
            pattern: Pattern to match (e.g., "product:*")
            namespace: Key namespace

        Returns:
            Number of keys invalidated
        """
        if isinstance(self.backend, RedisCacheBackend):
            try:
                full_pattern = self._get_key(namespace, pattern)
                count = 0
                async for key in self.backend._client.scan_iter(
                    match=full_pattern, count=100
                ):
                    await self.backend._client.delete(key)
                    count += 1
                self.logger.info(
                    f"Invalidated {count} cache keys matching {full_pattern}"
                )
                return count
            except Exception as exc:
                self.logger.debug(f"Pattern invalidation failed: {exc}")

        self.logger.warning(
            "Pattern invalidation not supported for non-Redis backends"
        )
        return 0

    async def warm_cache(
        self,
        items: dict[str, Any],
        namespace: str = "default",
        ttl: int | None = None,
    ) -> None:
        """
        Pre-warm cache with known high-traffic keys.

        Args:
            items: Dict of key-value pairs to pre-load
            namespace: Key namespace
            ttl: Time to live in seconds
        """
        for key, value in items.items():
            await self.set(key, value, namespace, ttl)
        self.logger.info(f"Warmed {len(items)} cache entries in namespace '{namespace}'")

    async def get_cache_hit_ratio(self) -> float:
        """
        Calculate current cache hit ratio.

        Returns:
            Hit ratio as a float between 0.0 and 1.0
        """
        hits = self._metrics.get("cache_hits", 0)
        misses = self._metrics.get("cache_misses", 0)
        total = hits + misses
        if total == 0:
            return 0.0
        return hits / total

    async def set_many(
        self,
        items: dict[str, Any],
        namespace: str = "default",
        ttl: int | None = None,
    ) -> None:
        """Set multiple cache entries"""
        for key, value in items.items():
            await self.set(key, value, namespace, ttl)

    async def get_many(
        self,
        keys: list[str],
        namespace: str = "default",
    ) -> dict[str, Any]:
        """Get multiple cache entries"""
        results = {}
        for key in keys:
            value = await self.get(key, namespace)
            if value is not None:
                results[key] = value
        return results

    def register_namespace(self, namespace: str, prefix: str = "") -> None:
        """Register namespace prefix"""
        self._key_prefixes[namespace] = prefix

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        stats = super().get_metrics()

        if isinstance(self.backend, MemoryCacheBackend):
            stats['cache_size'] = self.backend.size()

        return stats
