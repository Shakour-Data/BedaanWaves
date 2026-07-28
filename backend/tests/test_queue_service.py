"""
Unit tests for Tier 9 QueueService.
"""

import asyncio

import pytest

from app.services.system.queue_service import QueueService, JobStatus, QueuedJob

pytestmark = pytest.mark.unit


class _Queue(QueueService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, max_workers=2, **kwargs)

    async def initialize(self):
        self._running = True
        self._queue = asyncio.PriorityQueue()

    async def shutdown(self):
        self._running = False
        self._workers.clear()
        self._jobs.clear()


class TestQueueService:
    async def test_initialize_and_shutdown(self):
        svc = _Queue("TestQueue")
        await svc.initialize()
        assert svc._running is True
        assert svc._queue is not None
        await svc.shutdown()
        assert svc._running is False

    async def test_set_processor(self):
        svc = _Queue("TestQueue")
        await svc.initialize()
        async def proc(job):
            return {"ok": True}
        svc.set_processor(proc)
        assert svc._job_processor is proc
        await svc.shutdown()

    async def test_enqueue_and_get_job(self):
        svc = _Queue("TestQueue")
        await svc.initialize()
        job = await svc.enqueue("task_a", {"key": "value"}, priority=5)
        assert job.name == "task_a"
        assert job.payload == {"key": "value"}
        assert job.priority == 5
        detail = svc.get_job(job.id)
        assert detail is not None
        assert detail["name"] == "task_a"
        await svc.shutdown()

    async def test_enqueue_no_processor_fails(self):
        svc = _Queue("TestQueue")
        await svc.initialize()
        job = await svc.enqueue("task_x", {})
        assert job.status == JobStatus.PENDING
        await svc._process_job(job)
        assert job.status == JobStatus.FAILED
        await svc.shutdown()

    async def test_get_queue_stats(self):
        svc = _Queue("TestQueue")
        await svc.initialize()
        await svc.enqueue("t1", {})
        await svc.enqueue("t2", {}, priority=10)
        stats = svc.get_queue_stats()
        assert stats["total_jobs"] == 2
        assert stats["pending"] == 2
        await svc.shutdown()

    async def test_get_dead_letter_jobs(self):
        svc = _Queue("TestQueue")
        await svc.initialize()

        async def failing_processor(job):
            raise RuntimeError("always fails")

        svc.set_processor(failing_processor)
        job = await svc.enqueue("fail_task", {}, max_retries=0)
        assert job.status == JobStatus.PENDING
        await svc._process_job(job)
        assert job.status == JobStatus.DEAD_LETTER
        dead = svc.get_dead_letter_jobs()
        assert len(dead) == 1
        assert dead[0]["id"] == job.id
        await svc.shutdown()

    async def test_health_check(self):
        svc = _Queue("TestQueue")
        await svc.initialize()
        health = await svc.health_check()
        assert health["service"] == "TestQueue"
        assert health["status"] == "healthy"
        assert health["workers"] == 0
        await svc.shutdown()
