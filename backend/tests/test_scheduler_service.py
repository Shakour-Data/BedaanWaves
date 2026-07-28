"""
Unit tests for Tier 9 SchedulerService.
"""

import asyncio

import pytest

from app.services.system.scheduler_service import SchedulerService

pytestmark = pytest.mark.unit


class _Scheduler(SchedulerService):
    async def initialize(self):  # pragma: no cover - trivial
        self._running = True

    async def shutdown(self):  # pragma: no cover - trivial
        self._running = False


class TestSchedulerService:
    async def test_initialize_and_shutdown(self):
        svc = _Scheduler("TestScheduler")
        await svc.initialize()
        assert svc._running is True
        await svc.shutdown()
        assert svc._running is False

    async def test_register_and_unregister_job(self):
        svc = _Scheduler("TestScheduler")
        await svc.initialize()
        async def job():
            return {"ok": True}
        j = svc.register_job("test_job", job, 60)
        assert j.name == "test_job"
        assert j.interval_seconds == 60
        assert svc.get_job_status("test_job") is not None
        ok = svc.unregister_job("test_job")
        assert ok is True
        assert svc.get_job_status("test_job") is None
        await svc.shutdown()

    async def test_run_job_now(self):
        svc = _Scheduler("TestScheduler")
        await svc.initialize()
        async def job():
            return {"ok": True}
        svc.register_job("test_job", job, 60)
        result = await svc.run_job_now("test_job")
        assert result["status"] == "success"
        assert result["job"] == "test_job"
        await svc.shutdown()

    async def test_run_job_now_missing(self):
        svc = _Scheduler("TestScheduler")
        await svc.initialize()
        with pytest.raises(ValueError):
            await svc.run_job_now("missing")
        await svc.shutdown()

    async def test_list_jobs(self):
        svc = _Scheduler("TestScheduler")
        await svc.initialize()
        async def job():
            return {}
        svc.register_job("j1", job, 60)
        svc.register_job("j2", job, 120)
        jobs = svc.list_jobs()
        assert len(jobs) == 2
        await svc.shutdown()

    async def test_health_check(self):
        svc = _Scheduler("TestScheduler")
        await svc.initialize()
        health = await svc.health_check()
        assert health["service"] == "TestScheduler"
        assert health["status"] == "healthy"
        await svc.shutdown()
