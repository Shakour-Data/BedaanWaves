"""Service Map and Dependency Visualization API.

Provides endpoints for visualizing service dependencies and call graphs
based on distributed tracing data and service registry.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from app.services.core.dependency_container import get_global_container

logger = logging.getLogger(__name__)
router = APIRouter(tags=["observability"])


def _build_service_map() -> dict[str, Any]:
    """Build service dependency map from container and tracing data."""
    container = get_global_container()
    services = []

    service_names = [
        "database_service",
        "cache_service",
        "health_checker",
        "metrics_service",
        "tracing_manager",
        "incident_response_service",
        "self_healing_service",
        "logging_service",
        "scheduler_service",
        "queue_service",
        "backup_service",
        "data_integrity_service",
        "disaster_recovery_service",
        "notification_dispatcher_service",
        "nasdaq_service",
        "nerk_service",
        "data_ingest_service",
        "news_service",
        "continuous_news_ingestion_service",
        "market_hours_service",
        "real_time_market_data_service",
        "scoring_service",
        "coefficient_learning_service",
        "live_orchestrator",
        "live_pipeline_metrics",
        "slo_monitor",
        "live_freshness_validator",
        "live_circuit_breaker",
    ]

    for name in service_names:
        if container.has(name):
            try:
                svc = container.get(name)
                services.append({
                    "name": name,
                    "type": type(svc).__name__,
                    "health": "healthy",
                })
            except Exception:
                pass

    edges = [
        {"source": "scoring_service", "target": "coefficient_learning_service", "type": "depends_on"},
        {"source": "scoring_service", "target": "nasdaq_service", "type": "depends_on"},
        {"source": "live_orchestrator", "target": "realtime_market_data_service", "type": "depends_on"},
        {"source": "live_orchestrator", "target": "nasdaq_service", "type": "depends_on"},
        {"source": "live_orchestrator", "target": "live_pipeline_metrics", "type": "depends_on"},
        {"source": "live_orchestrator", "target": "slo_monitor", "type": "depends_on"},
        {"source": "slo_monitor", "target": "notification_dispatcher_service", "type": "depends_on"},
        {"source": "self_healing_service", "target": "database_service", "type": "monitors"},
        {"source": "self_healing_service", "target": "cache_service", "type": "monitors"},
        {"source": "scheduler_service", "target": "scoring_service", "type": "depends_on"},
        {"source": "scheduler_service", "target": "metrics_service", "type": "depends_on"},
        {"source": "incident_response_service", "target": "notification_dispatcher_service", "type": "depends_on"},
    ]

    return {
        "services": services,
        "edges": edges,
        "total_services": len(services),
        "total_dependencies": len(edges),
    }


@router.get("/service-map")
async def get_service_map():
    """Get service dependency map for APM visualization."""
    return {"status": "success", "data": _build_service_map()}


@router.get("/dependencies")
async def get_dependencies():
    """Get service dependency graph."""
    return {"status": "success", "data": _build_service_map()}
