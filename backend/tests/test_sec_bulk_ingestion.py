"""
Unit tests for the bulk SEC EDGAR financial-statement ingestion methods
added to ``NasdaqIngestionService``.
"""

import pytest

from app.services.data.nasdaq_ingestion_service import (
    SEC_EDGAR_MIN_QUARTERS,
    SEC_EDGAR_CHUNK_SIZE,
    NasdaqIngestionService,
)

pytestmark = pytest.mark.unit


class FakeSecService:
    """Stub that records calls and returns configurable results."""

    def __init__(self):
        self.initialized = False
        self.shutdown_called = False
        self.calls: list[tuple[str, str]] = []
        self.quarter_counts: dict[str, int] = {}
        self.ingest_results: dict[str, dict] = {}

    async def initialize(self):
        self.initialized = True

    async def shutdown(self):
        self.shutdown_called = True

    async def count_quarters_in_db(self, asset_id: str) -> int:
        return self.quarter_counts.get(asset_id, 0)

    async def ingest_sec_financials(self, symbol, asset_id,
                                     min_quarters=0, skip_if_sufficient=False):
        self.calls.append((symbol, asset_id))
        return self.ingest_results.get(
            symbol,
            {"statements": 8, "ratios": 1, "errors": 0,
             "quarterly_periods_fetched": 8,
             "min_quarters_requested": min_quarters},
        )


class FakeAsset:
    def __init__(self, id_val, symbol, asset_class="EQUITY"):
        self.id = id_val
        self.symbol = symbol
        self.asset_class = asset_class


class TestBulkIngestSecFinancials:
    async def test_basic_run(self, monkeypatch):
        svc = NasdaqIngestionService()
        svc._symbols = ["AAPL", "MSFT"]
        fake_sec = FakeSecService()

        async def _ensure_asset(symbol, name, asset_class="EQUITY", **kwargs):
            return FakeAsset(id_val=f"id-{symbol}", symbol=symbol)

        monkeypatch.setattr(svc, "_ensure_asset", _ensure_asset)
        monkeypatch.setattr(svc, "_sec_service", fake_sec)

        result = await svc.bulk_ingest_sec_financials(
            symbols=["AAPL", "MSFT"],
            min_quarters=20,
            chunk_size=50,
        )

        assert result["symbols_processed"] == 2
        assert result["statements_stored"] == 16
        assert result["ratios_stored"] == 2
        assert result["errors"] == 0
        assert fake_sec.initialized is True
        assert fake_sec.shutdown_called is True
        assert len(fake_sec.calls) == 2

    async def test_skip_sufficient(self, monkeypatch):
        svc = NasdaqIngestionService()
        svc._symbols = ["AAPL"]
        fake_sec = FakeSecService()
        fake_sec.ingest_results = {
            "AAPL": {"statements": 0, "ratios": 0, "errors": 0, "skipped": True}
        }

        async def _ensure_asset(symbol, name, asset_class="EQUITY", **kwargs):
            return FakeAsset(id_val=f"id-{symbol}", symbol=symbol)

        monkeypatch.setattr(svc, "_ensure_asset", _ensure_asset)
        monkeypatch.setattr(svc, "_sec_service", fake_sec)

        result = await svc.bulk_ingest_sec_financials(
            symbols=["AAPL"],
            chunk_size=50,
        )

        assert result["symbols_processed"] == 1
        assert result["skipped"] == 1
        assert result["statements_stored"] == 0

    async def test_error_handling(self, monkeypatch):
        svc = NasdaqIngestionService()
        svc._symbols = ["AAPL"]
        fake_sec = FakeSecService()

        async def _ensure_asset(symbol, name, asset_class="EQUITY", **kwargs):
            return FakeAsset(id_val=f"id-{symbol}", symbol=symbol)

        async def _failing_ingest(symbol, asset_id, **kwargs):
            raise RuntimeError("SEC API unavailable")

        fake_sec.ingest_sec_financials = _failing_ingest
        monkeypatch.setattr(svc, "_ensure_asset", _ensure_asset)
        monkeypatch.setattr(svc, "_sec_service", fake_sec)

        result = await svc.bulk_ingest_sec_financials(
            symbols=["AAPL"],
            chunk_size=50,
        )

        assert result["errors"] == 1
        assert result["symbols_processed"] == 1


class TestConstants:
    def test_min_quarters_is_20(self):
        assert SEC_EDGAR_MIN_QUARTERS == 20

    def test_chunk_size_is_reasonable(self):
        assert SEC_EDGAR_CHUNK_SIZE == 50
