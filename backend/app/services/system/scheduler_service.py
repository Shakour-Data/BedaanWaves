"""
Scheduler Service - Tier 9 System Service

Background task scheduler for periodic platform jobs:
- Daily 6D score recalculation
- Metrics aggregation
- Health checks
- Cache warming
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Coroutine
from dataclasses import dataclass, field

from ..core import BaseService


@dataclass
class ScheduledJob:
    """Definition of a scheduled job."""
    name: str
    coroutine_func: Callable[[], Coroutine[Any, Any, Any]]
    interval_seconds: int
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    _task: Optional[asyncio.Task] = field(default=None, repr=False)


class SchedulerService(BaseService):
    """
    Background scheduler for periodic platform jobs.
    
    Integrates with 6D scoring system for daily recalculation.
    """
    
    def __init__(self, service_name: str = "SchedulerService"):
        super().__init__(service_name)
        self._jobs: Dict[str, ScheduledJob] = {}
        self._running: bool = False
        self._main_task: Optional[asyncio.Task] = None
        self._score_recalc_interval_hours: int = 24
    
    async def initialize(self) -> None:
        self._running = True
        self._main_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("SchedulerService initialized")
    
    async def shutdown(self) -> None:
        self._running = False
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
        for job in self._jobs.values():
            if job._task:
                job._task.cancel()
                try:
                    await job._task
                except asyncio.CancelledError:
                    pass
        self._jobs.clear()
        self.logger.info("SchedulerService shutdown")
    
    def register_job(
        self,
        name: str,
        coroutine_func: Callable[[], Coroutine[Any, Any, Any]],
        interval_seconds: int,
    ) -> ScheduledJob:
        """
        Register a periodic job.
        
        Args:
            name: Unique job identifier
            coroutine_func: Async callable to execute
            interval_seconds: Interval between runs in seconds
            
        Returns:
            ScheduledJob instance
        """
        job = ScheduledJob(
            name=name,
            coroutine_func=coroutine_func,
            interval_seconds=interval_seconds,
            next_run=datetime.now(timezone.utc),
        )
        self._jobs[name] = job
        self.logger.info(f"Registered job: {name} (interval={interval_seconds}s)")
        return job
    
    def unregister_job(self, name: str) -> bool:
        """Remove a registered job."""
        if name in self._jobs:
            job = self._jobs.pop(name)
            if job._task:
                job._task.cancel()
            self.logger.info(f"Unregistered job: {name}")
            return True
        return False
    
    async def run_job_now(self, name: str) -> Dict[str, Any]:
        """
        Execute a job immediately, bypassing the schedule.
        
        Args:
            name: Job identifier
            
        Returns:
            Job execution result
        """
        if name not in self._jobs:
            raise ValueError(f"Job not found: {name}")
        job = self._jobs[name]
        return await self._execute_job(job)
    
    async def _execute_job(self, job: ScheduledJob) -> Dict[str, Any]:
        """Execute a single job and track metrics."""
        start = datetime.now(timezone.utc)
        try:
            result = await job.coroutine_func()
            duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            job.last_run = datetime.now(timezone.utc)
            job.run_count += 1
            job.next_run = datetime.now(timezone.utc)
            self._track_metric(success=True, duration_ms=duration_ms)
            self.logger.info(f"Job '{job.name}' completed in {duration_ms:.1f}ms")
            return {"status": "success", "job": job.name, "duration_ms": duration_ms, "result": result}
        except Exception as exc:
            duration_ms = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            job.last_run = datetime.now(timezone.utc)
            job.run_count += 1
            job.error_count += 1
            job.next_run = datetime.now(timezone.utc)
            self._track_metric(success=False, duration_ms=duration_ms)
            self.logger.error(f"Job '{job.name}' failed: {exc}", exc_info=True)
            return {"status": "error", "job": job.name, "error": str(exc), "duration_ms": duration_ms}
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop - checks jobs and runs them when due."""
        self.logger.info("Scheduler loop started")
        while self._running:
            now = datetime.now(timezone.utc)
            for job in list(self._jobs.values()):
                if not job.enabled:
                    continue
                if job.next_run and now >= job.next_run:
                    job._task = asyncio.create_task(self._execute_job(job))
                    job.next_run = datetime.now(timezone.utc)
            await asyncio.sleep(1)
    
    def get_job_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get status of a registered job."""
        if name not in self._jobs:
            return None
        job = self._jobs[name]
        return {
            "name": job.name,
            "enabled": job.enabled,
            "interval_seconds": job.interval_seconds,
            "last_run": job.last_run.isoformat() if job.last_run else None,
            "next_run": job.next_run.isoformat() if job.next_run else None,
            "run_count": job.run_count,
            "error_count": job.error_count,
        }
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all registered jobs and their status."""
        return [self.get_job_status(name) for name in self._jobs]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check scheduler health."""
        return {
            "service": self.service_name,
            "status": "healthy" if self._running else "stopped",
            "jobs_registered": len(self._jobs),
            "jobs_running": sum(1 for j in self._jobs.values() if j.enabled),
            "uptime_seconds": (datetime.now(timezone.utc) - self.created_at).total_seconds(),
        }
