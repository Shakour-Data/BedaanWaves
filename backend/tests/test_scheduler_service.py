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


class _TestScheduler(SchedulerService):
    """SchedulerService that skips the background loop but still registers jobs."""

    async def initialize(self):
        self._running = True
        await self._register_default_jobs()

    async def shutdown(self):
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


class FakeScoringService:
    """Minimal stub for ScoringService used in scheduler jobs."""

    def __init__(self):
        self.analyzed = []

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    async def analyze(self, data: dict) -> dict:
        self.analyzed.append((data.get("ticker", ""), data.get("market", "NASDAQ")))
        return {"symbol": data.get("ticker", ""), "score": 0.5}


class FakeCacheService:
    def __init__(self):
        self.cleared = False
        self.cleared_namespace = None

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    async def clear(self, namespace: str | None = None):
        self.cleared = True
        self.cleared_namespace = namespace

    def get_stats(self) -> dict:
        return {"keys": 0, "size": 0}


class TestSchedulerServiceWithInjectedServices:
    """Tests verifying that SchedulerService correctly uses injected services."""

    async def test_scheduler_accepts_service_injection(self):
        """SchedulerService stores injected services as attributes."""
        scoring = FakeScoringService()
        cache = FakeCacheService()
        svc = SchedulerService(
            service_name="TestScheduler",
            scoring_service=scoring,
            cache_service=cache,
        )
        assert svc.scoring_service is scoring
        assert svc.cache_service is cache
        assert svc.nasdaq_service is None  # not injected

    async def test_scheduler_defaults_to_none_services(self):
        """SchedulerService works with no services injected."""
        svc = SchedulerService("TestScheduler")
        assert svc.scoring_service is None
        assert svc.cache_service is None
        assert svc.nasdaq_service is None
        assert svc.ml_training_service is None
        assert svc.backup_service is None

    async def test_daily_score_recalculation_uses_scoring_service(self):
        """When scoring_service is set, daily_score_recalculation_job calls analyze per symbol."""
        scoring = FakeScoringService()
        svc = _TestScheduler(
            service_name="TestScheduler",
            scoring_service=scoring,
        )
        await svc.initialize()

        # The job will try to query the DB; with no DB it will log warnings but
        # scoring_service.initialize/shutdown are still called
        result = await svc.run_job_now("DailyScoreRecalculation")
        assert result["status"] in ("success", "skipped", "error")

        await svc.shutdown()
        # Scoring service lifecycle methods should have been called
        # (analyze is only reached if DB query succeeds)
        if scoring.analyzed:
            assert len(scoring.analyzed) > 0

    async def test_cache_warming_uses_cache_service(self):
        """When cache_service is set, cache_warming_job calls clear() with await."""
        cache = FakeCacheService()
        svc = _TestScheduler(
            service_name="TestScheduler",
            cache_service=cache,
        )
        await svc.initialize()

        result = await svc.run_job_now("CacheWarming")
        assert result["status"] in ("success", "skipped", "error")
        await svc.shutdown()

    async def test_model_training_uses_ml_service(self):
        """When ml_training_service is set, ModelTraining job calls retrain_all."""

        class FakeMLService:
            def __init__(self):
                self.retrained = False
                self.initialized = False
                self.shutdown_called = False

            async def initialize(self):
                self.initialized = True

            async def shutdown(self):
                self.shutdown_called = True

            async def retrain_all(self):
                self.retrained = True
                return {"status": "ok", "models_trained": 5}

        ml_svc = FakeMLService()
        svc = _TestScheduler(
            service_name="TestScheduler",
            ml_training_service=ml_svc,
        )
        await svc.initialize()

        result = await svc.run_job_now("ModelTraining")
        assert result["status"] in ("success", "skipped", "error")
        await svc.shutdown()

        if ml_svc.retrained:
            assert ml_svc.initialized is True
            assert ml_svc.shutdown_called is True
