"""Notification Service (Tier 6: User Services)

Creates, lists, marks-read and deletes user notifications.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select

from app.db.base import async_session_maker
from app.models.models import Notification


class NotificationService:
    """CRUD + read-state management for notifications."""

    def __init__(self, session_factory=async_session_maker):
        self.session_factory = session_factory

    async def create_notification(
        self,
        user_id: UUID,
        type: str,
        title: str,
        message: str,
        channel: str = "IN_APP",
        priority: str = "NORMAL",
        metadata: Optional[Dict] = None,
        session=None,
    ) -> Notification:
        session = session or self.session_factory()
        owns = session is None
        try:
            notification = Notification(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                channel=channel,
                priority=priority,
                extra=metadata or {},
            )
            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            return notification
        finally:
            if owns:
                await session.close()

    async def get_notification(
        self, notification_id: UUID, user_id: UUID, session=None
    ) -> Optional[Notification]:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(
                select(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            return result.scalars().first()
        finally:
            if owns:
                await session.close()

    async def list_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
        session=None,
    ) -> Tuple[List[Notification], int]:
        session = session or self.session_factory()
        owns = session is None
        try:
            conditions = [Notification.user_id == user_id]
            if unread_only:
                conditions.append(Notification.read.is_(False))
            result = await session.execute(
                select(Notification).where(*conditions)
            )
            rows = list(result.scalars().all())
            rows.sort(key=lambda n: n.created_at or datetime.min, reverse=True)
            total = len(rows)
            page = rows[offset : offset + limit]
            return page, total
        finally:
            if owns:
                await session.close()

    async def mark_read(
        self, notification_id: UUID, user_id: UUID, session=None
    ) -> bool:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(
                select(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            notification = result.scalars().first()
            if notification is None:
                return False
            if not notification.read:
                notification.read = True
                from datetime import datetime
                notification.read_at = datetime.utcnow()
                await session.commit()
            return True
        finally:
            if owns:
                await session.close()

    async def mark_all_read(self, user_id: UUID, session=None) -> int:
        session = session or self.session_factory()
        owns = session is None
        try:
            from datetime import datetime

            result = await session.execute(
                select(Notification).where(
                    Notification.user_id == user_id,
                    Notification.read.is_(False),
                )
            )
            now = datetime.utcnow()
            count = 0
            for notification in result.scalars().all():
                notification.read = True
                notification.read_at = now
                count += 1
            await session.commit()
            return count
        finally:
            if owns:
                await session.close()

    async def delete_notification(
        self, notification_id: UUID, user_id: UUID, session=None
    ) -> bool:
        session = session or self.session_factory()
        owns = session is None
        try:
            result = await session.execute(
                select(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            notification = result.scalars().first()
            if notification is None:
                return False
            await session.delete(notification)
            await session.commit()
            return True
        finally:
            if owns:
                await session.close()


notification_service = NotificationService()
