"""Unit tests for Tier 6 WatchlistService."""

import pytest
from uuid import uuid4

from app.models.models import Watchlist, WatchlistItem
from app.services.user.watchlist_service import WatchlistService

pytestmark = pytest.mark.unit


def _user_id():
    return uuid4()


class TestWatchlistCrud:
    async def test_create_and_list(self, fake_session):
        uid = _user_id()
        service = WatchlistService()
        wl = await service.create_watchlist(uid, "My List", session=fake_session)
        assert wl.id is not None
        assert wl.user_id == uid
        listed = await service.list_watchlists(uid, session=fake_session)
        assert len(listed) == 1

    async def test_get_by_owner(self, fake_session):
        uid = _user_id()
        service = WatchlistService()
        wl = await service.create_watchlist(uid, "WL", session=fake_session)
        got = await service.get_watchlist(wl.id, uid, session=fake_session)
        assert got.id == wl.id

    async def test_get_wrong_owner_returns_none(self, fake_session):
        service = WatchlistService()
        wl = await service.create_watchlist(_user_id(), "WL", session=fake_session)
        assert await service.get_watchlist(wl.id, _user_id(), session=fake_session) is None

    async def test_delete(self, fake_session):
        uid = _user_id()
        service = WatchlistService()
        wl = await service.create_watchlist(uid, "WL", session=fake_session)
        assert await service.delete_watchlist(wl.id, uid, session=fake_session) is True
        assert await service.get_watchlist(wl.id, uid, session=fake_session) is None


class TestWatchlistItems:
    async def test_add_and_remove_item(self, fake_session):
        uid = _user_id()
        asset_id = uuid4()
        service = WatchlistService()
        wl = await service.create_watchlist(uid, "WL", session=fake_session)
        item = await service.add_item(wl.id, uid, asset_id, session=fake_session)
        assert item.asset_id == asset_id
        assert item.watchlist_id == wl.id
        assert await service.remove_item(wl.id, item.id, uid, session=fake_session) is True

    async def test_add_item_to_missing_watchlist(self, fake_session):
        service = WatchlistService()
        assert await service.add_item(uuid4(), _user_id(), uuid4(), session=fake_session) is None

    async def test_remove_item_from_other_user_fails(self, fake_session):
        uid = _user_id()
        other = _user_id()
        asset_id = uuid4()
        service = WatchlistService()
        wl = await service.create_watchlist(uid, "WL", session=fake_session)
        item = await service.add_item(wl.id, uid, asset_id, session=fake_session)
        assert await service.remove_item(wl.id, item.id, other, session=fake_session) is False
