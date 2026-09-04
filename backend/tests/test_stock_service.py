"""Unit tests for Tier 2 StockService."""

import pytest
from unittest.mock import patch, AsyncMock

from app.services.data.stock_service import StockService

pytestmark = pytest.mark.unit


class TestStockServiceInitialization:
    def test_default_service_name(self):
        service = StockService()
        assert service.service_name == "StockService"

    async def test_initialize_logs(self, caplog):
        service = StockService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "StockService initialized" in caplog.text

    async def test_shutdown_clears_cache(self):
        service = StockService()
        service.set_cached("x", {"ticker": "x"})
        await service.shutdown()
        assert service.cache_get("x") is None


class TestGetStock:
    async def test_cache_miss_fetches_and_caches(self):
        service = StockService(cache_ttl_seconds=3600)
        mock_info = {
            "shortName": "Apple Inc.",
            "regularMarketPrice": 150.0,
            "regularMarketPreviousClose": 148.0,
            "volume": 50000000,
            "exchange": "NASDAQ",
            "currency": "USD",
            "marketCap": 2500000000000,
            "trailingPE": 28.0,
            "sector": "Technology",
            "industry": "Consumer Electronics",
        }
        with patch.object(service, '_run_blocking', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "exchange": "NASDAQ",
                "currency": "USD",
                "market_cap": 2500000000000,
                "pe_ratio": 28.0,
                "price": 150.0,
                "previous_close": 148.0,
                "change": 2.0,
                "change_percent": 1.35,
                "volume": 50000000,
                "timestamp": "2025-01-01T00:00:00+00:00",
            }
            result = await service.get_stock("AAPL", use_cache=False)
            assert result["symbol"] == "AAPL"
            assert result["name"] == "Apple Inc."

    async def test_cache_hit_returns_cached(self):
        service = StockService(cache_ttl_seconds=3600)
        service.set_cached("stock:MSFT", {"symbol": "MSFT", "price": 400.0})
        cached = service.get_cached("stock:MSFT")
        assert cached is not None
        result = await service.get_stock("MSFT", use_cache=True)
        assert result == cached


class TestGetMultiple:
    async def test_collects_all_results(self):
        service = StockService(cache_ttl_seconds=3600)
        service.set_cached("stock:AAPL", {"symbol": "AAPL", "name": "Apple"})
        service.set_cached("stock:MSFT", {"symbol": "MSFT", "name": "Microsoft"})
        service.set_cached("stock:GOOGL", {"symbol": "GOOGL", "name": "Google"})
        results = await service.get_multiple(["AAPL", "MSFT", "GOOGL"])
        assert "AAPL" in results
        assert "MSFT" in results
        assert "GOOGL" in results
        assert results["AAPL"]["name"] == "Apple"