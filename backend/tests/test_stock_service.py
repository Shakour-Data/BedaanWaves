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
        result = await service.get_stock("فملی", use_cache=False)
        assert result == {"ticker": "فملی", "name": "Stock فملی"}

    async def test_cache_hit_returns_cached(self, brs_client):
        service = StockService(cache_ttl_seconds=3600, brs_client=brs_client)
        await service.get_stock("خودرو", use_cache=False)
        cached = service.get_cached("stock:خودرو")
        assert cached is not None
        second = await service.get_stock("خودرو", use_cache=True)
        assert second == cached

    async def test_missing_client_raises(self):
        service = StockService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_stock("فملی")

    async def test_stores_result_in_cache(self, brs_client):
        service = StockService(cache_ttl_seconds=3600, brs_client=brs_client)
        await service.get_stock("شپنا", use_cache=False)
        assert service.get_cached("stock:شپنا") is not None


class TestGetPrice:
    async def test_delegates_to_client(self, brs_client):
        service = StockService(brs_client=brs_client)
        result = await service.get_price("فملی")
        assert result == {"ticker": "فملی", "price": 100.0}

    async def test_missing_client_raises(self):
        service = StockService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_price("فملی")


class TestGetHistory:
    async def test_cache_miss_calls_client(self, brs_client):
        service = StockService(cache_ttl_seconds=86400, brs_client=brs_client)
        result = await service.get_history("فملی", start_date="2025-01-01", end_date="2025-01-31", interval="daily")
        assert result == {"ticker": "فملی", "history": []}

    async def test_cache_hit_returns_cached(self, brs_client):
        service = StockService(cache_ttl_seconds=86400, brs_client=brs_client)
        await service.get_history("خودرو", start_date="2025-01-01", end_date="2025-01-31", interval="daily")
        second = await service.get_history("خودرو", start_date="2025-01-01", end_date="2025-01-31", interval="daily")
        assert second == {"ticker": "خودرو", "history": []}

    async def test_missing_client_raises(self):
        service = StockService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_history("فملی")


class TestSearch:
    async def test_cache_miss_calls_client(self, brs_client):
        service = StockService(cache_ttl_seconds=3600, brs_client=brs_client)
        result = await service.search("پتر")
        assert result == [{"symbol": "پتر"}]

    async def test_cache_hit_returns_cached(self, brs_client):
        service = StockService(cache_ttl_seconds=86400, brs_client=brs_client)
        await service.search("خودرو")
        second = await service.search("خودرو")
        assert second == [{"symbol": "خودرو"}]

    async def test_missing_client_raises(self):
        service = StockService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.search("پتر")


class TestGetMultiple:
    async def test_collects_all_results(self, brs_client):
        service = StockService(cache_ttl_seconds=3600, brs_client=brs_client)
        result = await service.get_multiple(["فملی", "خودرو"])
        assert "فملی" in result
        assert "خودرو" in result
        assert result["فملی"]["ticker"] == "فملی"

    async def test_handles_client_error_gracefully(self, brs_client):
        class _BadClient:
            async def get_stock_info(self, ticker):
                raise RuntimeError("boom")

        service = StockService(cache_ttl_seconds=3600, brs_client=_BadClient())
        result = await service.get_multiple(["X"])
        assert "error" in result["X"]
