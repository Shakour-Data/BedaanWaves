"""Unit tests for Tier 2 HistoryService."""

import pytest

from app.services.data.history_service import HistoryService

pytestmark = pytest.mark.unit


class TestHistoryServiceInitialization:
    def test_default_service_name(self, brs_client):
        service = HistoryService(brs_client=brs_client)
        assert service.service_name == "HistoryService"

    async def test_initialize_logs(self, brs_client, caplog):
        service = HistoryService(brs_client=brs_client)
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "HistoryService initialized" in caplog.text

    async def test_shutdown_clears_cache(self, brs_client):
        service = HistoryService(brs_client=brs_client)
        service.set_cached("x", [])
        await service.shutdown()
        assert service.cache_get("x") is None


class TestGetStockHistory:
    async def test_cache_miss_calls_client(self, brs_client):
        service = HistoryService(
            cache_ttl_seconds=86400, brs_client=brs_client
        )
        result = await service.get_stock_history(
            "فملی", start_date="2025-01-01", end_date="2025-01-31", interval="daily"
        )
        assert result == {"ticker": "فملی", "history": []}

    async def test_cache_hit_returns_cached(self, brs_client):
        service = HistoryService(
            cache_ttl_seconds=86400, brs_client=brs_client
        )
        await service.get_stock_history("خودرو", start_date="2025-01-01", end_date="2025-01-31", interval="daily")
        second = await service.get_stock_history("خودرو", start_date="2025-01-01", end_date="2025-01-31", interval="daily")
        assert second == {"ticker": "خودرو", "history": []}

    async def test_missing_client_raises(self):
        service = HistoryService(brs_client=None)
        with pytest.raises(RuntimeError, match="BRS client not initialized"):
            await service.get_stock_history("فملی")


class TestGetPriceHistory:
    async def test_delegates_to_get_stock_history(self, brs_client):
        service = HistoryService(
            cache_ttl_seconds=86400, brs_client=brs_client
        )
        result = await service.get_price_history("فملی", days=7)
        assert result == {"ticker": "فملی", "history": []}


class TestGetVolumeHistory:
    async def test_transforms_price_history(self, brs_client):
        class _ClientWithHistory:
            async def get_stock_history(self, ticker, start_date, end_date, interval):
                return [
                    {"date": "2025-01-01", "volume": 1000},
                    {"date": "2025-01-02", "volume": 2000},
                ]

        service = HistoryService(brs_client=_ClientWithHistory())
        result = await service.get_volume_history("فملی", days=7)
        assert result == [
            {"date": "2025-01-01", "volume": 1000},
            {"date": "2025-01-02", "volume": 2000},
        ]


class TestStoreHistoricalData:
    async def test_warns_without_db_service(self, brs_client, caplog):
        service = HistoryService(db_service=None, brs_client=brs_client)
        with caplog.at_level("WARNING"):
            caplog.clear()
            await service.store_historical_data("فملی", "2025-01-01", {"open": 100})
        assert "Database service not available" in caplog.text
