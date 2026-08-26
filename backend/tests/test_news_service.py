"""News Service Unit Tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.data.news_service import NewsService

pytestmark = pytest.mark.unit


class _FakeAsyncResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items


class _FakeAsyncSession:
    def __init__(self, items=None):
        self._items = items or []

    async def execute(self, stmt):
        return _FakeAsyncResult(self._items)

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class _FakeSessionMaker:
    def __init__(self, session):
        self._session = session

    def __call__(self):
        return self._session


class TestNewsServiceInitialization:
    def test_default_service_name(self, news_client):
        service = NewsService(news_client=news_client)
        assert service.service_name == "NewsService"

    async def test_initialize_logs(self, news_client, caplog):
        service = NewsService(news_client=news_client)
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "NewsService initialized" in caplog.text

    async def test_shutdown_clears_cache(self, news_client):
        service = NewsService(news_client=news_client)
        service.set_cached("x", [])
        await service.shutdown()
        assert service.cache_get("x") is None


class TestGetMarketNews:
    async def test_returns_empty_when_client_and_db_empty(self):
        fake_session = _FakeAsyncSession([])
        fake_maker = _FakeSessionMaker(fake_session)
        with patch("app.services.data.news_service.async_session_maker", fake_maker):
            service = NewsService(news_client=None)
            result = await service.get_market_news(limit=10)
        assert result == []

    async def test_caches_result(self, news_client):
        fake_session = _FakeAsyncSession([])
        fake_maker = _FakeSessionMaker(fake_session)
        with patch("app.services.data.news_service.async_session_maker", fake_maker):
            service = NewsService(cache_ttl_seconds=1800, news_client=news_client)
            result = await service.get_market_news(limit=10)
        assert service.get_cached("market_news_10") is not None
        assert result == []

    async def test_cache_hit_returns_cached(self, news_client):
        fake_session = _FakeAsyncSession([])
        fake_maker = _FakeSessionMaker(fake_session)
        with patch("app.services.data.news_service.async_session_maker", fake_maker):
            service = NewsService(cache_ttl_seconds=3600, news_client=news_client)
            await service.get_market_news(limit=5)
            second = await service.get_market_news(limit=5)
        assert second == []


class TestGetStockNews:
    async def test_returns_empty_when_client_and_db_empty(self):
        fake_session = _FakeAsyncSession([])
        fake_maker = _FakeSessionMaker(fake_session)
        with patch("app.services.data.news_service.async_session_maker", fake_maker):
            service = NewsService(news_client=None)
            result = await service.get_stock_news("TEST", limit=10)
        assert result == []

    async def test_caches_result(self, news_client):
        fake_session = _FakeAsyncSession([])
        fake_maker = _FakeSessionMaker(fake_session)
        with patch("app.services.data.news_service.async_session_maker", fake_maker):
            service = NewsService(cache_ttl_seconds=1800, news_client=news_client)
            await service.get_stock_news("TEST", limit=5)
        assert service.get_cached("stock_news:TEST:5") is not None


class TestSearchNews:
    async def test_returns_empty_when_client_and_db_empty(self):
        fake_session = _FakeAsyncSession([])
        fake_maker = _FakeSessionMaker(fake_session)
        with patch("app.services.data.news_service.async_session_maker", fake_maker):
            service = NewsService(news_client=None)
            result = await service.search_news("query", limit=10)
        assert result == []

    async def test_caches_result(self, news_client):
        fake_session = _FakeAsyncSession([])
        fake_maker = _FakeSessionMaker(fake_session)
        with patch("app.services.data.news_service.async_session_maker", fake_maker):
            service = NewsService(cache_ttl_seconds=1800, news_client=news_client)
            await service.search_news("query", limit=5)
        assert service.get_cached("news_search:query:5") is not None


class TestGetRelatedNews:
    async def test_aggregates_stock_news(self, news_client):
        fake_session = _FakeAsyncSession([])
        fake_maker = _FakeSessionMaker(fake_session)
        with patch("app.services.data.news_service.async_session_maker", fake_maker):
            service = NewsService(cache_ttl_seconds=1800, news_client=news_client)
            result = await service.get_related_news("some text", ["TEST"])
        assert result == []
