from fastapi import APIRouter
import logging
from datetime import datetime
from typing import Optional

from app.api.dependencies import get_current_admin_user
from app.services.core.dependency_container import get_global_container
from app.services.health_checker import HealthChecker
from app.services.health_checker import get_health_checker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Root health check endpoint."""
    check = HealthChecker()
    result = (await check.health_check()).copy()
    result['timestamp'] = datetime.utcnow().isoformat()
    return {
        "status": "success",
        "service": "health_check",
        "result": result
    }

@router.get("/services")
async def list_service_health():
    """Get health status for all services."""
    health_checker = get_health_checker()
    result = await health_checker.run_all_checks()
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "services": result.get('checks', {})
    }

@router.get("/services/{service}")
async def get_service_health(service: str):
    """Get health status for specific service."""
    health_checker = get_health_checker()
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