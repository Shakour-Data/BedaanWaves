"""Unit tests for Tier 2 StockService."""

import pytest

from app.services.data.stock_service import StockService

pytestmark = pytest.mark.unit


class TestStockServiceInitialization:
    def test_default_service_name(self, brs_client):
        service = StockService(brs_client=brs_client)
        assert service.service_name == "StockService"

    async def test_initialize_logs(self, brs_client, caplog):
        service = StockService(brs_client=brs_client)
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "StockService initialized" in caplog.text

    async def test_shutdown_clears_cache(self, brs_client):
        service = StockService(brs_client=brs_client)
        service.set_cached("x", {"ticker": "x"})
        await service.shutdown()
        assert service.cache_get("x") is None


class TestGetStock:
    async def test_cache_miss_calls_client(self, brs_client):
        service = StockService(cache_ttl_seconds=3600, brs_client=brs_client)
        result = await service.get_stock("FAMILY", use_cache=False)
        assert result == {"ticker": "FAMILY", "name": "Stock FAMILY"}

    async def test_cache_hit_returns_cached(self, brs_client):
        service = StockService(cache_ttl_seconds=3600, brs_client=brs_client)
        await service.get_stock("KHODRO", use_cache=False)
        cached = service.get_cached("stock:KHODRO")
        assert cached is not None
        second = await service.get_stock("KHODRO", use_cache=True)
        assert second == cached

    async def test_missing_client_raises(self):
        service = StockService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_stock("FAMILY")

    async def test_stores_result_in_cache(self, brs_client):
        service = StockService(cache_ttl_seconds=3600, brs_client=brs_client)
        await service.get_stock("SHPNA", use_cache=False)
        assert service.get_cached("stock:SHPNA") is not None


class TestGetPrice:
    async def test_delegates_to_client(self, brs_client):
        service = StockService(brs_client=brs_client)
        result = await service.get_price("FAMILY")
        assert result == {"ticker": "FAMILY", "price": 100.0}

    async def test_missing_client_raises(self):
        service = StockService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_price("FAMILY")


class TestGetHistory:
    async def test_cache_miss_calls_client(self, brs_client):
        service = StockService(cache_ttl_seconds=86400, brs_client=brs_client)
        result = await service.get_history("FAMILY", start_date="2025-01-01", end_date="2025-01-31", interval="daily")
        assert result == {"ticker": "FAMILY", "history": []}

    async def test_cache_hit_returns_cached(self, brs_client):
        service = StockService(cache_ttl_seconds=86400, brs_client=brs_client)
        await service.get_history("KHODRO", start_date="2025-01-01", end_date="2025-01-31", interval="daily")
        second = await service.get_history("KHODRO", start_date="2025-01-01", end_date="2025-01-31", interval="daily")
        assert second == {"ticker": "KHODRO", "history": []}

    async def test_missing_client_raises(self):
        service = StockService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_history("FAMILY")


class TestSearch:
    async def test_cache_miss_calls_client(self, brs_client):
        service = StockService(cache_ttl_seconds=3600, brs_client=brs_client)
        result = await service.search("PETR")
        assert result == [{"symbol": "PETR"}]

    async def test_cache_hit_returns_cached(self, brs_client):
        service = StockService(cache_ttl_seconds=86400, brs_client=brs_client)
        await service.search("KHODRO")
        second = await service.search("KHODRO")
        assert second == [{"symbol": "KHODRO"}]

    async def test_missing_client_raises(self):
        service = StockService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.search("PETR")


class TestGetMultiple:
    async def test_collects_all_results(self, brs_client):
        service = StockService(cache_ttl_seconds=3600, brs_client=brs_client)
        result = await service.get_multiple(["FAMILY", "KHODRO"])
        assert "FAMILY" in result
        assert "KHODRO" in result
        assert result["FAMILY"]["ticker"] == "FAMILY"

    async def test_handles_client_error_gracefully(self, brs_client):
        class _BadClient:
            async def get_stock_info(self, ticker):
                raise RuntimeError("boom")

        service = StockService(cache_ttl_seconds=3600, brs_client=_BadClient())
        result = await service.get_multiple(["X"])
        assert "error" in result["X"]
