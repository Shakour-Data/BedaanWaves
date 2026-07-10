"""System Routes - Tier 9 (Scheduler, Metrics, Queue)"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional
import logging

from app.services.system.scheduler_service import SchedulerService
from app.services.system.metrics_service import MetricsService
from app.services.system.queue_service import QueueService, JobStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["system"])


def _load(svc_cls):
    svc = svc_cls()
    return svc


# ---- Scheduler Endpoints ----

@router.get("/scheduler/jobs")
async def list_scheduler_jobs() -> dict:
    """List all registered scheduler jobs."""
    svc = _load(SchedulerService)
    await svc.initialize()
    jobs = svc.list_jobs()
    return {"status": "success", "jobs": jobs, "count": len(jobs)}


@router.post("/scheduler/jobs")
async def register_scheduler_job(data: dict) -> dict:
    """
    Register a new scheduled job.
    
    Body: {"name": "job_name", "interval_seconds": 3600}
    """
    name = data.get("name")
    interval_seconds = int(data.get("interval_seconds", 3600))
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    
    async def _noop():
        return {"status": "ok"}
    
    svc = _load(SchedulerService)
    await svc.initialize()
    job = svc.register_job(name, _noop, interval_seconds)
    return {"status": "success", "job": svc.get_job_status(name)}


@router.delete("/scheduler/jobs/{name}")
async def unregister_scheduler_job(name: str) -> dict:
    """Unregister a scheduled job."""
    svc = _load(SchedulerService)
    await svc.initialize()
    ok = svc.unregister_job(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Job not found: {name}")
    return {"status": "success", "message": f"Job '{name}' unregistered"}


@router.post("/scheduler/jobs/{name}/run")
async def run_scheduler_job_now(name: str) -> dict:
    """Trigger a scheduled job immediately."""
    svc = _load(SchedulerService)
    await svc.initialize()
    result = await svc.run_job_now(name)
    return result


# ---- Metrics Endpoints ----

@router.get("/metrics")
async def get_platform_metrics() -> dict:
    """Get platform-wide metrics summary."""
    svc = _load(MetricsService)
    await svc.initialize()
    metrics = svc.get_all_metrics()
    return {"status": "success", "timestamp": datetime.utcnow().isoformat(), **metrics}


@router.get("/metrics/health")
async def get_health_summary() -> dict:
    """Get health summary for all services."""
    svc = _load(MetricsService)
    await svc.initialize()
    health = svc.get_health_summary()
    return {"status": "success", **health}


# ---- Queue Endpoints ----

@router.post("/queue/jobs")
async def enqueue_job(data: dict) -> dict:
    """
    Enqueue a new job.
    
    Body: {"name": "task_name", "payload": {...}, "priority": 0, "max_retries": 3}
    """
    name = data.get("name")
    payload = data.get("payload", {})
    priority = int(data.get("priority", 0))
    max_retries = int(data.get("max_retries", 3))
    
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    
    async def default_processor(job):
        return {"processed": job.name, "payload": job.payload}
    
    svc = _load(QueueService)
    await svc.initialize()
    svc.set_processor(default_processor)
    job = await svc.enqueue(name, payload, priority=priority, max_retries=max_retries)
    return {"status": "success", "job_id": job.id, "name": job.name}


@router.get("/queue/jobs/{job_id}")
async def get_queue_job(job_id: str) -> dict:
    """Get job details by ID."""
    svc = _load(QueueService)
    await svc.initialize()
    job = svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return {"status": "success", **job}


@router.get("/queue/stats")
async def get_queue_stats() -> dict:
    """Get queue statistics."""
    svc = _load(QueueService)
    await svc.initialize()
    stats = svc.get_queue_stats()
    return {"status": "success", **stats}


@router.get("/queue/dead-letter")
async def get_dead_letter_jobs() -> dict:
    """Get dead-letter jobs."""
    svc = _load(QueueService)
    await svc.initialize()
    jobs = svc.get_dead_letter_jobs()
    return {"status": "success", "jobs": jobs, "count": len(jobs)}
