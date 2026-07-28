"""Unit tests for Tier 1 CacheService and MemoryCacheBackend."""

import asyncio
from datetime import datetime, timedelta

import pytest

from app.services.core.cache_service import (
    CacheService,
    MemoryCacheBackend,
)

pytestmark = pytest.mark.unit


class TestMemoryCacheBackend:
    async def test_set_and_get(self, memory_backend):
        await memory_backend.set("k", "v")
        assert await memory_backend.get("k") == "v"

    async def test_get_missing_returns_none(self, memory_backend):
        assert await memory_backend.get("missing") is None

    async def test_delete(self, memory_backend):
        await memory_backend.set("k", "v")
        await memory_backend.delete("k")
        assert await memory_backend.get("k") is None

    async def test_delete_missing_is_noop(self, memory_backend):
        await memory_backend.delete("missing")  # should not raise

    async def test_clear(self, memory_backend):
        await memory_backend.set("a", 1)
        await memory_backend.set("b", 2)
        await memory_backend.clear()
        assert memory_backend.size() == 0

    async def test_exists(self, memory_backend):
        await memory_backend.set("k", "v")
        assert await memory_backend.exists("k") is True
        assert await memory_backend.exists("nope") is False

    async def test_ttl_expiry_on_get(self, memory_backend):
        await memory_backend.set("k", "v", ttl=1)
        # back-date the expiry to force expiration
        memory_backend._cache["k"]["expiry"] = datetime.utcnow() - timedelta(seconds=1)
        assert await memory_backend.get("k") is None

    async def test_ttl_expiry_on_exists(self, memory_backend):
        await memory_backend.set("k", "v", ttl=1)
        memory_backend._cache["k"]["expiry"] = datetime.utcnow() - timedelta(seconds=1)
        assert await memory_backend.exists("k") is False

    async def test_size(self, memory_backend):
        await memory_backend.set("a", 1)
        await memory_backend.set("b", 2)
        assert memory_backend.size() == 2


class TestCacheServiceBackendSelection:
    def test_memory_backend_created(self):
        svc = CacheService(backend="memory")
        assert isinstance(svc.backend, MemoryCacheBackend)

    def test_redis_falls_back_to_memory(self):
        svc = CacheService(backend="redis")
        assert isinstance(svc.backend, MemoryCacheBackend)

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError):
            CacheService(backend="cassandra")


class TestCacheServiceOperations:
    async def test_set_and_get(self, cache_service):
        await cache_service.set("k", "v")
        assert await cache_service.get("k") == "v"

    async def test_namespacing(self, cache_service):
        await cache_service.set("k", "one", namespace="ns1")
        await cache_service.set("k", "two", namespace="ns2")
        assert await cache_service.get("k", namespace="ns1") == "one"
        assert await cache_service.get("k", namespace="ns2") == "two"

    async def test_metrics_hits_and_misses(self, cache_service):
        await cache_service.get("missing")  # miss
        await cache_service.set("k", "v")
        await cache_service.get("k")  # hit
        assert cache_service._metrics["cache_hits"] == 1
        assert cache_service._metrics["cache_misses"] == 1

    async def test_delete(self, cache_service):
        await cache_service.set("k", "v")
        await cache_service.delete("k")
        assert await cache_service.get("k") is None

    async def test_exists(self, cache_service):
        await cache_service.set("k", "v")
        assert await cache_service.exists("k") is True
        assert await cache_service.exists("nope") is False

    async def test_clear_all(self, cache_service):
        await cache_service.set("k", "v")
        await cache_service.clear()
        assert await cache_service.get("k") is None

    async def test_get_or_set_computes_and_caches(self, cache_service):
        calls = {"n": 0}

        def factory():
            calls["n"] += 1
            return "computed"

        first = await cache_service.get_or_set("k", factory)
        second = await cache_service.get_or_set("k", factory)
        assert first == "computed"
        assert second == "computed"
        assert calls["n"] == 1  # factory only invoked once

    async def test_get_or_set_with_non_callable(self, cache_service):
        value = await cache_service.get_or_set("k", "static")
        assert value == "static"

    async def test_set_many_and_get_many(self, cache_service):
        await cache_service.set_many({"a": 1, "b": 2})
        results = await cache_service.get_many(["a", "b", "missing"])
        assert results == {"a": 1, "b": 2}

    async def test_register_namespace(self, cache_service):
        cache_service.register_namespace("ns", "prefix")
        assert cache_service._key_prefixes["ns"] == "prefix"


class TestCacheServiceKeys:
    def test_get_key_format(self, cache_service):
        assert cache_service._get_key("ns", "id") == "ns:id"

    def test_hash_key_stable(self, cache_service):
        h1 = cache_service._get_hash_key({"a": 1, "b": 2})
        h2 = cache_service._get_hash_key({"b": 2, "a": 1})
        assert h1 == h2  # sort_keys makes it order-independent


class TestCacheServiceLifecycleAndStats:
    async def test_initialize_and_shutdown(self, cache_service):
        await cache_service.initialize()
        await cache_service.set("k", "v")
        await cache_service.shutdown()
        assert await cache_service.get("k") is None  # shutdown clears cache

    async def test_get_stats_includes_size(self, cache_service):
        await cache_service.set("a", 1)
        stats = cache_service.get_stats()
        assert stats["cache_size"] == 1
