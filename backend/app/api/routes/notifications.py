"""Notification Routes (Tier 6)"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID

from app.api.dependencies import get_route_user_id
from app.schemas.schemas import NotificationResponse
from app.services.user.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(get_route_user_id),
):
    notifications, _ = await notification_service.list_notifications(
        user_id=user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return notifications


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: UUID,
    user_id: UUID = Depends(get_route_user_id),
):
    marked = await notification_service.mark_read(notification_id, user_id)
    if not marked:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification = await notification_service.get_notification(notification_id, user_id)
    return notification


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(user_id: UUID = Depends(get_route_user_id)):
    count = await notification_service.mark_all_read(user_id)
    return {"status": "success", "marked": count}


@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    notification_id: UUID,
    user_id: UUID = Depends(get_route_user_id),
):
    deleted = await notification_service.delete_notification(notification_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success", "id": str(notification_id)}
