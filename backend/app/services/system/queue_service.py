"""
Queue Service - Tier 9 System Service

Async in-memory job queue for deferred task execution.
Supports priority, retries, and dead-letter handling.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..core import BaseService


class JobStatus(str, Enum):
    """Job lifecycle states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass
class QueuedJob:
    """Job payload for the queue."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    max_retries: int = 3
    retry_count: int = 0
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class QueueService(BaseService):
    """
    Async job queue for deferred task execution.
    
    Supports priority ordering, automatic retries, and dead-letter queue.
    """
    
    def __init__(self, service_name: str = "QueueService", max_workers: int = 4):
        super().__init__(service_name)
        self._max_workers = max_workers
        self._queue: Optional[asyncio.PriorityQueue] = None
        self._jobs: Dict[str, QueuedJob] = {}
        self._dead_letter: List[QueuedJob] = []
        self._workers: List[asyncio.Task] = []
        self._running: bool = False
        self._job_processor: Optional[Callable[[QueuedJob], Coroutine[Any, Any, Any]]] = None
    
    async def initialize(self) -> None:
        self._running = True
        self._queue = asyncio.PriorityQueue()
        for _ in range(self._max_workers):
            task = asyncio.create_task(self._worker_loop())
            self._workers.append(task)
        self.logger.info(f"QueueService initialized with {self._max_workers} workers")
    
    async def shutdown(self) -> None:
        self._running = False
        for task in self._workers:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._workers.clear()
        self._jobs.clear()
        self.logger.info("QueueService shutdown")
    
    def set_processor(self, processor: Callable[[QueuedJob], Coroutine[Any, Any, Any]]) -> None:
        """
        Set the job processor function.
        
        Args:
            processor: Async callable that receives a QueuedJob and returns a result dict
        """
        self._job_processor = processor
    
    async def enqueue(
        self,
        name: str,
        payload: Dict[str, Any],
        priority: int = 0,
        max_retries: int = 3,
    ) -> QueuedJob:
        """
        Add a job to the queue.
        
        Args:
            name: Job type identifier
            payload: Job data
            priority: Higher priority runs first
            max_retries: Max retry attempts on failure
            
        Returns:
            QueuedJob instance
        """
        job = QueuedJob(
            name=name,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
        )
        self._jobs[job.id] = job
        await self._queue.put((-priority, job.id))
        self.logger.debug(f"Enqueued job {job.id} ({name}) priority={priority}")
        return job
    
    async def dequeue(self) -> Optional[QueuedJob]:
        """Get next job from queue (blocks until available)."""
        _, job_id = await self._queue.get()
        return self._jobs.get(job_id)
    
    async def _worker_loop(self) -> None:
        """Worker loop - processes jobs from queue."""
        while self._running:
            try:
                job = await self.dequeue()
                if job is None:
                    continue
                await self._process_job(job)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error(f"Worker error: {exc}", exc_info=True)
    
    async def _process_job(self, job: QueuedJob) -> None:
        """Process a single job with retry logic."""
        if self._job_processor is None:
            job.status = JobStatus.FAILED
            job.error = "No processor configured"
            self.logger.error(f"Job {job.id} failed: no processor configured")
            return
        
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        
        try:
            result = await self._job_processor(job)
            job.status = JobStatus.COMPLETED
            job.result = result
            job.finished_at = datetime.now(timezone.utc)
            self._track_metric(success=True, duration_ms=0)
            self.logger.info(f"Job {job.id} ({job.name}) completed")
        except Exception as exc:
            job.retry_count += 1
            self._track_metric(success=False, duration_ms=0)
            self.logger.warning(f"Job {job.id} ({job.name}) attempt {job.retry_count} failed: {exc}")
            
            if job.retry_count >= job.max_retries:
                job.status = JobStatus.DEAD_LETTER
                job.error = str(exc)
                job.finished_at = datetime.now(timezone.utc)
                self._dead_letter.append(job)
                self.logger.error(f"Job {job.id} ({job.name}) moved to dead-letter queue")
            else:
                job.status = JobStatus.PENDING
                job.error = str(exc)
                await self._queue.put((-job.priority, job.id))
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID."""
        if job_id not in self._jobs:
            return None
        job = self._jobs[job_id]
        return {
            "id": job.id,
            "name": job.name,
            "status": job.status.value,
            "priority": job.priority,
            "retry_count": job.retry_count,
            "max_retries": job.max_retries,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "result": job.result,
            "error": job.error,
        }
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        pending = sum(1 for j in self._jobs.values() if j.status == JobStatus.PENDING)
        processing = sum(1 for j in self._jobs.values() if j.status == JobStatus.PROCESSING)
        completed = sum(1 for j in self._jobs.values() if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in self._jobs.values() if j.status == JobStatus.FAILED)
        dead_letter = len(self._dead_letter)
        return {
            "total_jobs": len(self._jobs),
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "dead_letter": dead_letter,
            "queue_size": self._queue.qsize(),
        }
    
    def get_dead_letter_jobs(self) -> List[Dict[str, Any]]:
        """Get all dead-letter jobs."""
        return [
            {
                "id": j.id,
                "name": j.name,
                "error": j.error,
                "retry_count": j.retry_count,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            }
            for j in self._dead_letter
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check queue service health."""
        return {
            "service": self.service_name,
            "status": "healthy" if self._running else "stopped",
            "workers": len(self._workers),
            "queue_size": self._queue.qsize(),
            "uptime_seconds": (datetime.now(timezone.utc) - self.created_at).total_seconds(),
        }
