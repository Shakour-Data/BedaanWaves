"""
Unit tests for Tier 1 base_service module.

Covers BaseService and its specialized subclasses:
CachedService, DataService, AnalysisService, MLService, ExternalAPIService.
"""

import asyncio

import pytest

from app.services.core.base_service import (
    BaseService,
    CachedService,
    DataService,
    AnalysisService,
    MLService,
    ExternalAPIService,
)

pytestmark = pytest.mark.unit


class _ConcreteService(BaseService):
    """Minimal concrete implementation for testing the abstract base."""

    async def initialize(self) -> None:  # pragma: no cover - trivial
        pass

    async def shutdown(self) -> None:  # pragma: no cover - trivial
        pass


class TestBaseService:
    def test_cannot_instantiate_abstract_base(self):
        with pytest.raises(TypeError):
            BaseService("abstract")  # type: ignore[abstract]

    def test_initial_state(self):
        svc = _ConcreteService("svc")
        assert svc.service_name == "svc"
        assert svc._metrics["calls"] == 0
        assert svc._metrics["errors"] == 0
        assert svc.created_at is not None

    def test_repr(self):
        svc = _ConcreteService("svc")
        assert "_ConcreteService" in repr(svc)
        assert "svc" in repr(svc)

    def test_cache_set_and_get(self):
        svc = _ConcreteService("svc")
        svc.cache_set("k", "v")
        entry = svc.cache_get("k")
        assert entry["value"] == "v"
        assert svc._metrics["cache_hits"] == 1

    def test_cache_get_miss(self):
        svc = _ConcreteService("svc")
        assert svc.cache_get("missing") is None
        assert svc._metrics["cache_misses"] == 1

    def test_cache_clear_single_key(self):
        svc = _ConcreteService("svc")
        svc.cache_set("a", 1)
        svc.cache_set("b", 2)
        svc.cache_clear("a")
        assert svc.cache_get("a") is None
        assert svc.cache_get("b") is not None

    def test_cache_clear_all(self):
        svc = _ConcreteService("svc")
        svc.cache_set("a", 1)
        svc.cache_set("b", 2)
        svc.cache_clear()
        assert svc.cache_get("a") is None
        assert svc.cache_get("b") is None

    def test_track_metric_success(self):
        svc = _ConcreteService("svc")
        svc._track_metric(success=True, duration_ms=10.0)
        assert svc._metrics["calls"] == 1
        assert svc._metrics["errors"] == 0
        assert svc._metrics["total_time_ms"] == 10.0

    def test_track_metric_failure(self):
        svc = _ConcreteService("svc")
        svc._track_metric(success=False, duration_ms=5.0)
        assert svc._metrics["errors"] == 1

    def test_get_metrics_computed_rates(self):
        svc = _ConcreteService("svc")
        svc._track_metric(True, 100.0)
        svc._track_metric(False, 100.0)
        metrics = svc.get_metrics()
        assert metrics["calls"] == 2
        assert metrics["errors"] == 1
        assert metrics["error_rate"] == 0.5
        assert metrics["avg_response_time_ms"] == 100.0

    def test_get_metrics_zero_calls_no_division_error(self):
        svc = _ConcreteService("svc")
        metrics = svc.get_metrics()
        assert metrics["error_rate"] == 0
        assert metrics["cache_hit_rate"] == 0
        assert metrics["avg_response_time_ms"] == 0

    async def test_health_check(self):
        svc = _ConcreteService("svc")
        health = await svc.health_check()
        assert health["service"] == "svc"
        assert health["status"] == "healthy"
        assert "uptime_seconds" in health


class TestCachedService:
    class _Cached(CachedService):
        async def initialize(self):  # pragma: no cover
            pass

        async def shutdown(self):  # pragma: no cover
            pass

    def test_set_and_get_cached(self):
        svc = self._Cached("cached", cache_ttl_seconds=100)
        svc.set_cached("k", "v")
        assert svc.get_cached("k") == "v"
        assert svc._metrics["cache_hits"] == 1

    def test_get_cached_missing(self):
        svc = self._Cached("cached")
        assert svc.get_cached("nope") is None
        assert svc._metrics["cache_misses"] == 1

    def test_cache_none_ttl_always_valid(self):
        svc = self._Cached("cached")
        svc.cache_set("k", "v", ttl_seconds=None)
        assert svc.get_cached("k") == "v"

    def test_expired_cache_returns_none(self):
        svc = self._Cached("cached")
        svc.set_cached("k", "v", ttl_seconds=0)
        # ttl of 0 -> falls back to default cache_ttl (3600) because `ttl or default`
        # so force expiry by writing directly with a 1s ttl and back-dating timestamp
        from datetime import datetime, timezone, timedelta

        svc.cache_set("k2", "v2", ttl_seconds=1)
        svc._cache["k2"]["timestamp"] = datetime.now(timezone.utc) - timedelta(seconds=5)
        assert svc.get_cached("k2") is None


class TestDataService:
    class _Data(DataService):
        async def initialize(self):  # pragma: no cover
            pass

        async def shutdown(self):  # pragma: no cover
            pass

    async def test_unimplemented_methods_raise(self):
        svc = self._Data("data")
        with pytest.raises(NotImplementedError):
            await svc.get_by_id(1)
        with pytest.raises(NotImplementedError):
            await svc.list_all()
        with pytest.raises(NotImplementedError):
            await svc.create({})
        with pytest.raises(NotImplementedError):
            await svc.update(1, {})
        with pytest.raises(NotImplementedError):
            await svc.delete(1)


class TestAnalysisService:
    class _Analysis(AnalysisService):
        async def initialize(self):  # pragma: no cover
            pass

        async def shutdown(self):  # pragma: no cover
            pass

        async def analyze(self, data):
            if data.get("boom"):
                raise ValueError("boom")
            return {"result": data["value"] * 2}

    async def test_analyze(self):
        svc = self._Analysis("analysis")
        result = await svc.analyze({"value": 5})
        assert result["result"] == 10

    async def test_batch_analyze_handles_errors(self):
        svc = self._Analysis("analysis")
        results = await svc.batch_analyze([{"value": 1}, {"boom": True, "value": 0}])
        assert results[0]["result"] == 2
        assert "error" in results[1]

    async def test_default_analyze_raises(self):
        class Bare(AnalysisService):
            async def initialize(self):  # pragma: no cover
                pass

            async def shutdown(self):  # pragma: no cover
                pass

        svc = Bare("bare")
        with pytest.raises(NotImplementedError):
            await svc.analyze({})


class TestMLService:
    class _ML(MLService):
        async def initialize(self):  # pragma: no cover
            pass

        async def shutdown(self):  # pragma: no cover
            pass

    def test_initial_model_state(self):
        svc = self._ML("ml")
        assert svc.model is None
        assert svc.features is None

    async def test_unimplemented_methods_raise(self):
        svc = self._ML("ml")
        with pytest.raises(NotImplementedError):
            await svc.train({})
        with pytest.raises(NotImplementedError):
            await svc.predict({})
        with pytest.raises(NotImplementedError):
            await svc.evaluate({})


class TestExternalAPIService:
    class _Api(ExternalAPIService):
        async def initialize(self):  # pragma: no cover
            pass

        async def shutdown(self):  # pragma: no cover
            pass

    def test_configuration(self):
        svc = self._Api("api", base_url="https://example.com", timeout=15, max_retries=5)
        assert svc.base_url == "https://example.com"
        assert svc.timeout == 15
        assert svc.max_retries == 5

    async def test_fetch_not_implemented(self):
        svc = self._Api("api", base_url="https://example.com")
        with pytest.raises(NotImplementedError):
            await svc.fetch("/endpoint")

    async def test_handle_rate_limit_backoff(self, monkeypatch):
        svc = self._Api("api", base_url="https://example.com")
        sleeps = []

        async def fake_sleep(seconds):
            sleeps.append(seconds)

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        await svc._handle_rate_limit(2)
        assert sleeps == [4]  # 2 ** 2

    async def test_handle_rate_limit_caps_at_60(self, monkeypatch):
        svc = self._Api("api", base_url="https://example.com")
        sleeps = []

        async def fake_sleep(seconds):
            sleeps.append(seconds)

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        await svc._handle_rate_limit(10)  # 2 ** 10 = 1024, capped to 60
        assert sleeps == [60]
