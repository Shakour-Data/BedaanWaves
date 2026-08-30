"""
Data Health Endpoint

Provides /api/data-health as a top-level route (not versioned).
Verifies connectivity to the data provider and returns status.
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import logging

from app.services.data.real_time_market_data_service import RealTimeMarketDataService
from app.services.core.dependency_container import get_global_container

logger = logging.getLogger(__name__)
router = APIRouter(tags=["data-health"])


@router.get("/data-health")
async def data_health_check() -> dict:
    """
    Health check for the live data pipeline.

    Verifies connectivity to the data provider, confirms last successful fetch,
    and returns current data source status.
    """
    try:
        container = get_global_container()
        service = container.get("real_time_market_data_service")
        if service is None:
            return {
                "status": "error",
                "error_code": "SERVICE_UNAVAILABLE",
                "message": "Real-time market data service is not registered",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        health = await service.health_check()
        return {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": health,
        }
    except Exception as exc:
        logger.error(f"Data health check failed: {exc}")
        return {
            "status": "error",
            "error_code": "HEALTH_CHECK_FAILED",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
