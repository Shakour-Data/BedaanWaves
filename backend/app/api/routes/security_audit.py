"""Security Audit Log Routes - Admin only

Provides endpoints for security audit trail review and monitoring.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.dependencies import get_current_admin_user
from app.db.base import async_session_maker
from app.models.models import AuditLog

logger = logging.getLogger(__name__)
router = APIRouter(tags=["security-audit"])


@router.get("/audit-log")
async def get_audit_log(
    current_user=Depends(get_current_admin_user),
    user_id: UUID | None = Query(None, description="Filter by user ID"),
    action: str | None = Query(None, description="Filter by action type"),
    entity: str | None = Query(None, description="Filter by entity type"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get security audit log entries with optional filters."""
    async with async_session_maker() as session:
        query = select(AuditLog).order_by(AuditLog.created_at.desc())

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if entity:
            query = query.where(AuditLog.entity == entity)

        query = query.limit(limit).offset(offset)
        result = await session.execute(query)
        logs = result.scalars().all()

        return {
            "status": "success",
            "data": [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "entity": log.entity,
                    "entity_id": log.entity_id,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            "count": len(logs),
        }


@router.get("/audit-log/suspicious")
async def get_suspicious_activity(
    current_user=Depends(get_current_admin_user),
    hours: int = Query(24, ge=1, le=720),
):
    """Get suspicious activity from the last N hours."""
    since = datetime.now(UTC) - timedelta(hours=hours)
    async with async_session_maker() as session:
        result = await session.execute(
            select(AuditLog)
            .where(AuditLog.created_at > since)
            .order_by(AuditLog.created_at.desc())
            .limit(200)
        )
        logs = result.scalars().all()

        suspicious_actions = {"login_failed", "password_reset", "account_locked", "admin_access"}
        suspicious = [log for log in logs if log.action in suspicious_actions]

        return {
            "status": "success",
            "period_hours": hours,
            "suspicious_count": len(suspicious),
            "data": [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "entity": log.entity,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in suspicious
            ],
        }
