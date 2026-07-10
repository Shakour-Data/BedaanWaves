"""
Unit tests for Tier 9 MetricsService.
"""

import pytest

from app.services.system.metrics_service import MetricsService

pytestmark = pytest.mark.unit


class _Metrics(MetricsService):
    async def initialize(self):  # pragma: no cover
        pass

    async def shutdown(self):  # pragma: no cover
        pass


class _FakeService:
    def __init__(self, metrics):
        self._metrics = metrics

    def get_metrics(self):
        return self._metrics


class TestMetricsService:
    async def test_initialize_and_shutdown(self):
        svc = _Metrics("TestMetrics")
        await svc.initialize()
        await svc.shutdown()

    async def test_register_and_unregister_service(self):
        svc = _Metrics("TestMetrics")
        await svc.initialize()
        fake = _FakeService({"calls": 10, "errors": 1})
        svc.register_service("fake", fake)
        assert svc.get_service_metrics("fake") is not None
        ok = svc.unregister_service("fake")
        assert ok is True
        assert svc.get_service_metrics("fake") is None
        await svc.shutdown()

    async def test_get_service_metrics_missing(self):
        svc = _Metrics("TestMetrics")
        await svc.initialize()
        assert svc.get_service_metrics("missing") is None
        await svc.shutdown()

    async def test_get_all_metrics_aggregation(self):
        svc = _Metrics("TestMetrics")
        await svc.initialize()
        fake1 = _FakeService({"calls": 10, "errors": 1, "cache_hits": 5, "cache_misses": 2})
        fake2 = _FakeService({"calls": 20, "errors": 2, "cache_hits": 8, "cache_misses": 3})
        svc.register_service("s1", fake1)
        svc.register_service("s2", fake2)
        all_metrics = svc.get_all_metrics()
        assert all_metrics["platform"]["total_calls"] == 30
        assert all_metrics["platform"]["total_errors"] == 3
        assert all_metrics["platform"]["services_count"] == 2
        assert "services" in all_metrics
        await svc.shutdown()

    async def test_get_health_summary(self):
        svc = _Metrics("TestMetrics")
        await svc.initialize()
        fake = _FakeService({"calls": 0, "errors": 0})
        svc.register_service("s1", fake)
        health = svc.get_health_summary()
        assert health["platform"] == "healthy"
        assert "s1" in health["services"]
        await svc.shutdown()

    async def test_health_check(self):
        svc = _Metrics("TestMetrics")
        await svc.initialize()
        health = await svc.health_check()
        assert health["service"] == "TestMetrics"
        assert health["status"] == "healthy"
        await svc.shutdown()
