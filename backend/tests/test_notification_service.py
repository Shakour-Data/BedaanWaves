"""Unit tests for Tier 6 NotificationService."""

import pytest
from uuid import uuid4

from app.models.models import Notification
from app.services.user.notification_service import NotificationService

pytestmark = pytest.mark.unit


def _user_id():
    return uuid4()


class TestNotificationCrud:
    async def test_create(self, fake_session):
        uid = _user_id()
        service = NotificationService()
        n = await service.create_notification(
            uid, "price_change", "Title", "Body", session=fake_session
        )
        assert n.id is not None
        assert n.read is False

    async def test_list_with_total(self, fake_session):
        uid = _user_id()
        service = NotificationService()
        await service.create_notification(uid, "t", "T1", "B1", session=fake_session)
        await service.create_notification(uid, "t", "T2", "B2", session=fake_session)
        items, total = await service.list_notifications(uid, session=fake_session)
        assert total == 2
        assert len(items) == 2

    async def test_list_unread_only(self, fake_session):
        uid = _user_id()
        service = NotificationService()
        n1 = await service.create_notification(uid, "t", "T1", "B1", session=fake_session)
        n2 = await service.create_notification(uid, "t", "T2", "B2", session=fake_session)
        await service.mark_read(n1.id, uid, session=fake_session)
        items, total = await service.list_notifications(uid, unread_only=True, session=fake_session)
        assert total == 1
        assert items[0].id == n2.id


class TestReadState:
    async def test_mark_read(self, fake_session):
        uid = _user_id()
        service = NotificationService()
        n = await service.create_notification(uid, "t", "T", "B", session=fake_session)
        assert await service.mark_read(n.id, uid, session=fake_session) is True
        again = await service.get_notification(n.id, uid, session=fake_session)
        assert again.read is True
        assert again.read_at is not None

    async def test_mark_read_missing(self, fake_session):
        service = NotificationService()
        assert await service.mark_read(uuid4(), _user_id(), session=fake_session) is False

    async def test_mark_all_read(self, fake_session):
        uid = _user_id()
        service = NotificationService()
        await service.create_notification(uid, "t", "T1", "B1", session=fake_session)
        await service.create_notification(uid, "t", "T2", "B2", session=fake_session)
        count = await service.mark_all_read(uid, session=fake_session)
        assert count == 2


class TestDelete:
    async def test_delete_notification(self, fake_session):
        uid = _user_id()
        service = NotificationService()
        n = await service.create_notification(uid, "t", "T", "B", session=fake_session)
        assert await service.delete_notification(n.id, uid, session=fake_session) is True
        assert await service.get_notification(n.id, uid, session=fake_session) is None

    async def test_delete_missing(self, fake_session):
        service = NotificationService()
        assert await service.delete_notification(uuid4(), _user_id(), session=fake_session) is False
