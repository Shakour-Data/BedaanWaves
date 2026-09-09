"""Unit tests for the settings (recent-searches) API layer.

Follows the same self-contained FastAPI TestClient pattern as the auth tests:
the router is mounted into a throwaway app and ``preference_service`` is mocked,
so no database or authenticated session is required.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.settings import RECENT_SEARCHES_KEY, router


@pytest.fixture
def app():
    _app = FastAPI()
    _app.include_router(router, prefix="/api/v1/settings", tags=["settings"])
    return _app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_prefs():
    with patch(
        "app.api.routes.settings.preference_service.get_preference",
        new_callable=AsyncMock,
    ) as mock_get, patch(
        "app.api.routes.settings.preference_service.set_preference",
        new_callable=AsyncMock,
    ) as mock_set:
        yield {"get": mock_get, "set": mock_set}


DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000000")


class TestRecentSearches:
    def test_get_returns_empty_when_no_preference(self, client, mock_prefs):
        mock_prefs["get"].return_value = None
        resp = client.get("/api/v1/settings/recent-searches")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["searches"] == []

    def test_get_returns_stored_searches(self, client, mock_prefs):
        mock_prefs["get"].return_value = SimpleNamespace(value=["AAPL", "TSLA", "NVDA"])
        resp = client.get("/api/v1/settings/recent-searches")
        assert resp.status_code == 200
        assert resp.json()["searches"] == ["AAPL", "TSLA", "NVDA"]

    def test_get_ignores_non_string_values(self, client, mock_prefs):
        mock_prefs["get"].return_value = SimpleNamespace(value=["AAPL", 123, None, "MSFT"])
        resp = client.get("/api/v1/settings/recent-searches")
        assert resp.json()["searches"] == ["AAPL", "MSFT"]

    def test_post_adds_new_search(self, client, mock_prefs):
        mock_prefs["get"].return_value = None
        resp = client.post("/api/v1/settings/recent-searches", json={"query": "AAPL"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["recent_searches"] == ["AAPL"]
        mock_prefs["set"].assert_awaited_once()
        args = mock_prefs["set"].await_args.args
        assert args[0] == DEV_USER_ID
        assert args[1] == RECENT_SEARCHES_KEY
        assert args[2] == ["AAPL"]

    def test_post_prepends_and_dedupes_case_insensitive(self, client, mock_prefs):
        mock_prefs["get"].return_value = SimpleNamespace(value=["AAPL", "TSLA", "aapl"])
        resp = client.post("/api/v1/settings/recent-searches", json={"query": "MsFt"})
        assert resp.status_code == 200
        body = resp.json()
        # "MsFt" normalized -> "MSFT", prepended; existing case-dupe "aapl" collapsed.
        assert body["recent_searches"] == ["MSFT", "AAPL", "TSLA"]

    def test_post_caps_to_limit(self, client, mock_prefs):
        mock_prefs["get"].return_value = SimpleNamespace(
            value=["ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT"]
        )
        resp = client.post(
            "/api/v1/settings/recent-searches", json={"query": "NEW", "limit": 3}
        )
        assert resp.status_code == 200
        assert resp.json()["recent_searches"] == ["NEW", "ONE", "TWO"]

    def test_post_rejects_empty_query(self, client, mock_prefs):
        mock_prefs["get"].return_value = None
        resp = client.post("/api/v1/settings/recent-searches", json={"query": "   "})
        assert resp.status_code == 400
        mock_prefs["set"].assert_not_awaited()

    def test_post_rejects_short_query(self, client, mock_prefs):
        mock_prefs["get"].return_value = None
        resp = client.post("/api/v1/settings/recent-searches", json={"query": ""})
        assert resp.status_code == 422
