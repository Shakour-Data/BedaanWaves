"""Unit tests for Tier 2 MarketService."""

import pytest

from app.services.data.market_service import MarketService

pytestmark = pytest.mark.unit


class TestMarketServiceInitialization:
    def test_default_service_name(self, brs_client):
        service = MarketService(brs_client=brs_client)
        assert service.service_name == "MarketService"

    async def test_initialize_logs(self, brs_client, caplog):
        service = MarketService(brs_client=brs_client)
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "MarketService initialized" in caplog.text

    async def test_shutdown_clears_cache(self, brs_client):
        service = MarketService(brs_client=brs_client)
        service.set_cached("x", {"name": "x"})
        await service.shutdown()
        assert service.cache_get("x") is None


class TestGetIndices:
    async def test_cache_miss_calls_client(self, brs_client):
        service = MarketService(cache_ttl_seconds=300, brs_client=brs_client)
        result = await service.get_indices()
        assert result == [{"name": "TSE", "value": 1000}]

    async def test_cache_hit_returns_cached(self, brs_client):
        service = MarketService(cache_ttl_seconds=3600, brs_client=brs_client)
        await service.get_indices()
        second = await service.get_indices()
        assert second == [{"name": "TSE", "value": 1000}]

    async def test_missing_client_raises(self):
        service = MarketService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_indices()


class TestGetStats:
    async def test_cache_miss_calls_client(self, brs_client):
        service = MarketService(cache_ttl_seconds=300, brs_client=brs_client)
        result = await service.get_stats()
        assert result == {"volume": 1000}

    async def test_cache_hit_returns_cached(self, brs_client):
        service = MarketService(cache_ttl_seconds=3600, brs_client=brs_client)
        await service.get_stats()
        second = await service.get_stats()
        assert second == {"volume": 1000}

    async def test_missing_client_raises(self):
        service = MarketService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_stats()


class TestGetGainers:
    async def test_cache_miss_calls_client(self, brs_client):
        service = MarketService(cache_ttl_seconds=300, brs_client=brs_client)
        result = await service.get_gainers(limit=5)
        assert result == []

        second = await service.get_gainers(limit=5)
        assert second == []

    async def test_missing_client_raises(self):
        service = MarketService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_gainers()


class TestGetLosers:
    async def test_cache_miss_calls_client(self, brs_client):
        service = MarketService(cache_ttl_seconds=300, brs_client=brs_client)
        result = await service.get_losers(limit=5)
        assert result == []

    async def test_missing_client_raises(self):
        service = MarketService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_losers()


class TestGetMostActive:
    async def test_cache_miss_calls_client(self, brs_client):
        service = MarketService(cache_ttl_seconds=300, brs_client=brs_client)
        result = await service.get_most_active(limit=5)
        assert result == []

    async def test_missing_client_raises(self):
        service = MarketService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_most_active()
