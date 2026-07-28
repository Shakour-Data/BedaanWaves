"""Unit tests for Tier 6 UserProfileService."""

import pytest
from uuid import uuid4

from app.models.models import User
from app.services.user.user_profile_service import UserProfileService

pytestmark = pytest.mark.unit


def _make_user() -> User:
    return User(
        id=uuid4(),
        username="tester",
        email="tester@example.com",
        hashed_password="x",
        full_name="Tester",
        preferred_language="fa",
        theme="dark",
        notifications_enabled=True,
    )


class TestGetProfile:
    async def test_returns_user(self, fake_session):
        user = _make_user()
        fake_session.add(user)
        service = UserProfileService()
        result = await service.get_profile(user.id, session=fake_session)
        assert result is not None
        assert result.id == user.id

    async def test_missing_user_returns_none(self, fake_session):
        service = UserProfileService()
        assert await service.get_profile(uuid4(), session=fake_session) is None


class TestUpdateProfile:
    async def test_updates_fields(self, fake_session):
        user = _make_user()
        fake_session.add(user)
        service = UserProfileService()
        updated = await service.update_profile(
            user.id, {"full_name": "New Name", "theme": "light"}, session=fake_session
        )
        assert updated.full_name == "New Name"
        assert updated.theme == "light"

    async def test_ignores_none_values(self, fake_session):
        user = _make_user()
        fake_session.add(user)
        service = UserProfileService()
        updated = await service.update_profile(
            user.id, {"theme": None}, session=fake_session
        )
        # Unchanged because None is skipped.
        assert updated.theme == "dark"

    async def test_missing_user_returns_none(self, fake_session):
        service = UserProfileService()
        assert await service.update_profile(uuid4(), {"theme": "light"}, session=fake_session) is None
