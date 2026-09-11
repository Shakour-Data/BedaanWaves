"""Observability Routes - Lightweight endpoints for frontend and external integrations."""

import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(tags=["observability"])


@router.post("/frontend-metrics")
async def receive_frontend_metrics(request: Request):
    """Receive frontend web vitals and error reports from the browser."""
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}

    if not isinstance(payload, dict):
        return {"status": "error", "message": "Invalid payload"}

    logger.info(
        "frontend_metric type=%s name=%s value=%s",
        payload.get("type"),
        payload.get("name"),
        payload.get("value"),
        extra={"frontend_metric": payload},
    )
    return {"status": "accepted"}


@router.get("/health/lightweight")
async def lightweight_health():
    """Lightweight health check that does not require database."""
    return {"status": "healthy", "service": "bedaanwaves-observability"}
