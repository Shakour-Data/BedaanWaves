"""Unit tests for Tier 6 PreferenceService."""

import pytest
from uuid import uuid4

from app.models.models import UserPreference
from app.services.user.preference_service import PreferenceService

pytestmark = pytest.mark.unit


def _user_id():
    return uuid4()


class TestPreferences:
    async def test_set_and_get(self, fake_session):
        uid = _user_id()
        service = PreferenceService()
        await service.set_preference(uid, "theme", "dark", session=fake_session)
        pref = await service.get_preference(uid, "theme", session=fake_session)
        assert pref is not None
        assert pref.value == "dark"

    async def test_set_updates_existing(self, fake_session):
        uid = _user_id()
        service = PreferenceService()
        await service.set_preference(uid, "theme", "dark", session=fake_session)
        await service.set_preference(uid, "theme", "light", session=fake_session)
        listed = await service.list_preferences(uid, session=fake_session)
        assert len(listed) == 1
        assert listed[0].value == "light"

    async def test_list_preferences(self, fake_session):
        uid = _user_id()
        service = PreferenceService()
        await service.set_preference(uid, "a", 1, session=fake_session)
        await service.set_preference(uid, "b", 2, session=fake_session)
        assert len(await service.list_preferences(uid, session=fake_session)) == 2

    async def test_get_missing_returns_none(self, fake_session):
        service = PreferenceService()
        assert await service.get_preference(_user_id(), "nope", session=fake_session) is None

    async def test_delete_preference(self, fake_session):
        uid = _user_id()
        service = PreferenceService()
        await service.set_preference(uid, "a", 1, session=fake_session)
        assert await service.delete_preference(uid, "a", session=fake_session) is True
        assert await service.get_preference(uid, "a", session=fake_session) is None

    async def test_delete_missing(self, fake_session):
        service = PreferenceService()
        assert await service.delete_preference(_user_id(), "a", session=fake_session) is False
