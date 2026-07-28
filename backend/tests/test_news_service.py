"""Unit tests for Tier 2 NewsService."""

import pytest

from app.services.data.news_service import NewsService

pytestmark = pytest.mark.unit


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
    async def test_returns_empty_when_client_missing(self):
        service = NewsService(news_client=None)
        result = await service.get_market_news(limit=10)
        assert result == []

    async def test_caches_result(self, news_client):
        service = NewsService(cache_ttl_seconds=1800, news_client=news_client)
        result = await service.get_market_news(limit=10)
        assert service.get_cached("market_news_10") is not None
        assert result == []

    async def test_cache_hit_returns_cached(self, news_client):
        service = NewsService(cache_ttl_seconds=3600, news_client=news_client)
        await service.get_market_news(limit=5)
        second = await service.get_market_news(limit=5)
        assert second == []


class TestGetStockNews:
    async def test_returns_empty_when_client_missing(self):
        service = NewsService(news_client=None)
        result = await service.get_stock_news("فملی", limit=10)
        assert result == []

    async def test_caches_result(self, news_client):
        service = NewsService(cache_ttl_seconds=1800, news_client=news_client)
        await service.get_stock_news("فملی", limit=5)
        assert service.get_cached("stock_news:فملی:5") is not None


class TestSearchNews:
    async def test_returns_empty_when_client_missing(self):
        service = NewsService(news_client=None)
        result = await service.search_news("پتر", limit=10)
        assert result == []

    async def test_caches_result(self, news_client):
        service = NewsService(cache_ttl_seconds=1800, news_client=news_client)
        await service.search_news("پتر", limit=5)
        assert service.get_cached("news_search:پتر:5") is not None


class TestGetRelatedNews:
    async def test_aggregates_stock_news(self, news_client):
        service = NewsService(cache_ttl_seconds=1800, news_client=news_client)
        result = await service.get_related_news("some text", ["فملی", "خودرو"])
        assert result == []
