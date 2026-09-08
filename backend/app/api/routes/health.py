import logging

from fastapi import APIRouter, HTTPException

from app.core.utils import utc_now_iso
from app.services.core.dependency_container import get_global_container
from app.services.core.health_checker import (
    HealthChecker,
    check_cache,
    check_database,
    check_disk,
    check_memory,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/")
async def health_check():
    """Root health check endpoint."""
    checks = {}
    try:
        health_checker = HealthChecker()
        container = get_global_container()
        db_service = container.get("database_service")
        cache_service = container.get("cache_service")
        health_checker.register_check("database", lambda: check_database(db_service))
        health_checker.register_check("cache", lambda: check_cache(cache_service))
        health_checker.register_check("memory", check_memory)
        health_checker.register_check("disk", check_disk)
        result = await health_checker.run_all_checks()
        checks = result.get('checks', {})
    except Exception as exc:
        logger.warning(f"Health check degraded: {exc}")
        checks = {"error": str(exc)}

    status = "healthy" if all(v.get("status") == "healthy" for v in checks.values() if isinstance(v, dict)) else "degraded"
    return {
        "status": status,
        "service": "health_check",
        "timestamp": utc_now_iso(),
        "overall_status": status,
        "checks": checks,
    }


@router.get("/services")
async def list_service_health():
    """Get health status for all services."""
    checks = {}
    try:
        health_checker = HealthChecker()
        container = get_global_container()
        db_service = container.get("database_service")
        cache_service = container.get("cache_service")
        health_checker.register_check("database", lambda: check_database(db_service))
        health_checker.register_check("cache", lambda: check_cache(cache_service))
        health_checker.register_check("memory", check_memory)
        health_checker.register_check("disk", check_disk)
        result = await health_checker.run_all_checks()
        checks = result.get('checks', {})
    except Exception as exc:
        logger.warning(f"Service health degraded: {exc}")
        checks = {"error": str(exc)}

    return {
        "status": "success",
        "timestamp": utc_now_iso(),
        "services": checks,
    }


@router.get("/services/{service}")
async def get_service_health(service: str):
    """Get health status for specific service."""
    checks = {}
    try:
        health_checker = HealthChecker()
        container = get_global_container()
        db_service = container.get("database_service")
        cache_service = container.get("cache_service")
        health_checker.register_check("database", lambda: check_database(db_service))
        health_checker.register_check("cache", lambda: check_cache(cache_service))
        health_checker.register_check("memory", check_memory)
        health_checker.register_check("disk", check_disk)
        result = await health_checker.run_check(service)
        if not result:
            raise HTTPException(status_code=404, detail=f"Health check not registered for {service}")
        checks = result
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Service health degraded for {service}: {exc}")
        checks = {"status": "error", "error": str(exc)}

    if checks.get("status") == "unhealthy":
        checks["error"] = checks.get("error", "Service is unhealthy")
    return {
        "status": "success",
        "service": service,
        "health": checks,
    }


@router.get("/ready")
async def readiness_check():
    """Readiness probe for load balancers and monitoring systems."""
    checks = {}
    try:
        health_checker = HealthChecker()
        container = get_global_container()
        db_service = container.get("database_service")
        cache_service = container.get("cache_service")
        health_checker.register_check("database", lambda: check_database(db_service))
        health_checker.register_check("cache", lambda: check_cache(cache_service))
        result = await health_checker.run_all_checks()
        checks = result.get('checks', {})
    except Exception as exc:
        logger.warning(f"Readiness check degraded: {exc}")
        checks = {"error": str(exc)}

    db_status = checks.get("database", {}).get("status", "unknown") if isinstance(checks.get("database"), dict) else "unknown"
    cache_status = checks.get("cache", {}).get("status", "unknown") if isinstance(checks.get("cache"), dict) else "unknown"
    is_ready = db_status == "healthy" and cache_status == "healthy"

    return {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": utc_now_iso(),
        "checks": checks,
    }


@router.get("/live")
async def liveness_check():
    """Liveness probe for load balancers."""
    return {
        "status": "alive",
        "timestamp": utc_now_iso(),
        "service": "bedaanwaves",
        "version": "1.0.0"
    }
