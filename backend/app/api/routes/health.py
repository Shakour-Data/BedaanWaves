from fastapi import APIRouter, HTTPException
import logging
from datetime import timezone, datetime
from typing import Optional
from app.core.utils import utc_now_iso

from app.api.dependencies import get_current_admin_user
from app.services.core.dependency_container import get_global_container
from app.services.core.health_checker import HealthChecker, check_database, check_cache, check_memory, check_disk

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

@router.get("/")
async def health_check():
    """Root health check endpoint."""
    health_checker = HealthChecker()
    
    # Register common health checks
    container = get_global_container()
    db_service = container.get("database_service")
    cache_service = container.get("cache_service")
    
    health_checker.register_check("database", lambda: check_database(db_service))
    health_checker.register_check("cache", lambda: check_cache(cache_service))
    health_checker.register_check("memory", check_memory)
    health_checker.register_check("disk", check_disk)
    
    result = await health_checker.run_all_checks()
    
    return {
        "status": "success",
        "service": "health_check",
        "timestamp": utc_now_iso(),
        "overall_status": result.get('overall_status', 'unknown'),
        "checks": result.get('checks', {})
    }

@router.get("/services")
async def list_service_health():
    """Get health status for all services."""
    health_checker = HealthChecker()
    
    # Register common health checks
    container = get_global_container()
    db_service = container.get("database_service")
    cache_service = container.get("cache_service")
    
    health_checker.register_check("database", lambda: check_database(db_service))
    health_checker.register_check("cache", lambda: check_cache(cache_service))
    health_checker.register_check("memory", check_memory)
    health_checker.register_check("disk", check_disk)
    
    result = await health_checker.run_all_checks()
    
    return {
        "status": "success",
        "timestamp": utc_now_iso(),
        "services": result.get('checks', {})
    }

@router.get("/services/{service}")
async def get_service_health(service: str):
    """Get health status for specific service."""
    health_checker = HealthChecker()
    
    # Register common health checks
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
    if result.get('status') == 'unhealthy':
        result['error'] = result.get('error', 'Service is unhealthy')
    return {
        "status": "success",
        "service": service,
        "health": result
    }

@router.get("/ready")
async def readiness_check():
    """Readiness probe for load balancers and monitoring systems."""
    health_checker = HealthChecker()
    
    # Check critical services only for readiness
    container = get_global_container()
    db_service = container.get("database_service")
    cache_service = container.get("cache_service")
    
    # Register only critical checks
    health_checker.register_check("database", lambda: check_database(db_service))
    health_checker.register_check("cache", lambda: check_cache(cache_service))
    
    result = await health_checker.run_all_checks()
    
    # Readiness requires database and cache to be healthy
    db_status = result.get('checks', {}).get('database', {}).get('status', 'unknown')
    cache_status = result.get('checks', {}).get('cache', {}).get('status', 'unknown')
    
    is_ready = db_status == 'healthy' and cache_status == 'healthy'
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": utc_now_iso(),
        "checks": result.get('checks', {})
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