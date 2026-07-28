"""Unit tests for Tier 1 HealthChecker service and common checks."""

import asyncio

import pytest

from app.services.core.health_checker import (
    HealthChecker,
    check_cache,
    check_memory,
    check_disk,
)

pytestmark = pytest.mark.unit


class TestHealthCheckRegistration:
    def test_register_check(self, health_checker):
        health_checker.register_check("dummy", lambda: {"status": "healthy"})
        assert "dummy" in health_checker._checks

    async def test_run_unregistered_check(self, health_checker):
        result = await health_checker.run_check("missing")
        assert result["status"] == "unknown"
        assert "error" in result


class TestRunChecks:
    async def test_run_sync_check(self, health_checker):
        health_checker.register_check("sync", lambda: {"name": "sync", "status": "healthy"})
        result = await health_checker.run_check("sync")
        assert result["status"] == "healthy"
        assert "timestamp" in result

    async def test_run_async_check(self, health_checker):
        async def async_check():
            return {"name": "async", "status": "healthy"}

        health_checker.register_check("async", async_check)
        result = await health_checker.run_check("async")
        assert result["status"] == "healthy"

    async def test_run_check_captures_exception(self, health_checker):
        def broken():
            raise RuntimeError("boom")

        health_checker.register_check("broken", broken)
        result = await health_checker.run_check("broken")
        assert result["status"] == "error"
        assert "boom" in result["error"]

    async def test_run_all_checks(self, health_checker):
        health_checker.register_check("a", lambda: {"status": "healthy"})
        health_checker.register_check("b", lambda: {"status": "healthy"})
        result = await health_checker.run_all_checks()
        assert result["overall_status"] == "healthy"
        assert set(result["checks"].keys()) == {"a", "b"}


class TestStatusAggregation:
    def test_aggregate_unhealthy(self, health_checker):
        results = {"a": {"status": "healthy"}, "b": {"status": "unhealthy"}}
        assert health_checker._aggregate_status(results) == "unhealthy"

    def test_aggregate_error_is_unhealthy(self, health_checker):
        results = {"a": {"status": "error"}}
        assert health_checker._aggregate_status(results) == "unhealthy"

    def test_aggregate_degraded(self, health_checker):
        results = {"a": {"status": "healthy"}, "b": {"status": "degraded"}}
        assert health_checker._aggregate_status(results) == "degraded"

    def test_aggregate_warning_is_degraded(self, health_checker):
        results = {"a": {"status": "warning"}}
        assert health_checker._aggregate_status(results) == "degraded"

    def test_aggregate_all_healthy(self, health_checker):
        results = {"a": {"status": "healthy"}, "b": {"status": "healthy"}}
        assert health_checker._aggregate_status(results) == "healthy"

    def test_aggregate_unknown(self, health_checker):
        results = {"a": {"status": "unknown"}}
        assert health_checker._aggregate_status(results) == "unknown"


class TestMonitoring:
    async def test_start_and_stop_monitoring(self, health_checker):
        await health_checker.start_monitoring()
        assert health_checker._is_monitoring is True
        await health_checker.stop_monitoring()
        assert health_checker._is_monitoring is False

    async def test_start_monitoring_idempotent(self, health_checker):
        await health_checker.start_monitoring()
        task = health_checker._monitor_task
        await health_checker.start_monitoring()  # should not create a new task
        assert health_checker._monitor_task is task
        await health_checker.stop_monitoring()

    async def test_initialize_starts_and_shutdown_stops(self, health_checker):
        await health_checker.initialize()
        assert health_checker._is_monitoring is True
        await health_checker.shutdown()
        assert health_checker._is_monitoring is False


class TestResultsAndStats:
    async def test_get_last_results(self, health_checker):
        health_checker.register_check("a", lambda: {"status": "healthy"})
        await health_checker.run_check("a")
        assert "a" in health_checker.get_last_results()

    async def test_get_check_status(self, health_checker):
        health_checker.register_check("a", lambda: {"status": "healthy"})
        await health_checker.run_check("a")
        assert health_checker.get_check_status("a")["status"] == "healthy"

    def test_get_check_status_missing(self, health_checker):
        assert health_checker.get_check_status("nope") is None

    def test_get_stats(self, health_checker):
        health_checker.register_check("a", lambda: {"status": "healthy"})
        stats = health_checker.get_stats()
        assert stats["registered_checks"] == 1
        assert stats["monitoring_active"] is False


class TestCommonChecks:
    async def test_check_cache_healthy(self, cache_service):
        result = await check_cache(cache_service)
        assert result["status"] == "healthy"

    async def test_check_cache_handles_failure(self):
        class BrokenCache:
            async def set(self, *a, **k):
                raise RuntimeError("cache down")

            async def get(self, *a, **k):  # pragma: no cover
                return None

        result = await check_cache(BrokenCache())
        assert result["status"] == "unhealthy"
        assert "cache down" in result["error"]

    async def test_check_memory(self):
        result = await check_memory()
        assert result["name"] == "memory"
        assert result["status"] in {"healthy", "degraded", "unhealthy", "unknown"}

    async def test_check_disk(self):
        result = await check_disk()
        assert result["name"] == "disk"
        assert result["status"] in {"healthy", "degraded", "unhealthy", "unknown"}
