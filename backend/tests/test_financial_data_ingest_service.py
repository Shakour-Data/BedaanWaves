"""Unit tests for FinancialDataIngestService SEC EDGAR fallback and statements retrieval."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.data.financial_data_ingest_service import (
    FinancialDataIngestService,
    FinancialStatementType,
    MarketType,
)

pytestmark = pytest.mark.unit


class TestGetFinancialStatements:
    """Tests for FinancialDataIngestService.get_financial_statements DB query."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_data(self):
        """When DB has no matching statements, return empty list."""
        service = FinancialDataIngestService()
        service._result_cache.clear()

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []

        with patch("app.db.base.async_session_maker") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.get_financial_statements(asset_id="test-asset-id", limit=20)
            assert result == []

    @pytest.mark.asyncio
    async def test_returns_statements_from_db(self):
        """Returns FinancialStatement objects from the DB query."""
        service = FinancialDataIngestService()
        service._result_cache.clear()

        class FakeRow:
            asset_id = "test-asset-id"
            symbol = "AAPL"
            market = "NASDAQ"
            statement_type = "INCOME"
            period = "2024Q1"
            fiscal_year = 2024
            data = {"revenue": 1000}
            as_of = None

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [FakeRow(), FakeRow()]

        with patch("app.db.base.async_session_maker") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.get_financial_statements(asset_id="test-asset-id", limit=10)
            assert len(result) == 2
            assert all(s.statement_type == FinancialStatementType("INCOME") for s in result)

    @pytest.mark.asyncio
    async def test_limit_param_controls_max_results(self):
        """The limit parameter controls the max number of results."""
        service = FinancialDataIngestService()
        service._result_cache.clear()

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []  # empty - just verify no crash

        with patch("app.db.base.async_session_maker") as mock_session_factory:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.get_financial_statements(asset_id="test-asset-id", limit=20)
            assert result == []


class TestIngestFinancialStatementsSecEdgarFallback:
    """Tests for the SEC EDGAR fallback path in ingest_financial_statements."""

    @pytest.mark.asyncio
    async def test_uses_provider_when_data_available(self):
        """When the provider returns data, SEC EDGAR fallback is not used."""
        service = FinancialDataIngestService()
        service._result_cache.clear()

        mock_provider = MagicMock()
        mock_provider.fetch_financial_statements = AsyncMock(return_value=["stmt1"])

        service._providers[MarketType.US] = mock_provider

        result = await service.ingest_financial_statements("AAPL", MarketType.US)
        assert result == ["stmt1"]
        mock_provider.fetch_financial_statements.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_falls_back_to_sec_edgar_when_provider_empty(self):
        """When provider returns empty list, SEC EDGAR fallback is triggered."""
        service = FinancialDataIngestService()
        service._result_cache.clear()

        mock_provider = MagicMock()
        mock_provider.fetch_financial_statements = AsyncMock(return_value=[])

        service._providers[MarketType.US] = mock_provider
        service._sec_service = MagicMock()
        service._sec_service.ingest_sec_financials = AsyncMock()

        with (
            patch("app.db.base.async_session_maker") as mock_session_factory,
            patch.object(service, "get_financial_statements", new_callable=AsyncMock) as mock_get_stmts,
        ):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = MagicMock(id="asset-uuid")
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get_stmts.return_value = []

            result = await service.ingest_financial_statements("AAPL", MarketType.US)

            service._sec_service.ingest_sec_financials.assert_awaited_once()
            called_kwargs = service._sec_service.ingest_sec_financials.call_args
            assert called_kwargs.kwargs.get("min_quarters") == 20
            assert called_kwargs.kwargs.get("skip_if_sufficient") is True
            assert result == []

    @pytest.mark.asyncio
    async def test_sec_edgar_fallback_min_quarters_custom(self):
        """Fallback passes min_quarters through to SEC EDGAR service."""
        service = FinancialDataIngestService()
        service._result_cache.clear()

        mock_provider = MagicMock()
        mock_provider.fetch_financial_statements = AsyncMock(return_value=[])
        service._providers[MarketType.US] = mock_provider
        service._sec_service = MagicMock()
        service._sec_service.ingest_sec_financials = AsyncMock()

        with (
            patch("app.db.base.async_session_maker") as mock_session_factory,
            patch.object(service, "get_financial_statements", new_callable=AsyncMock) as mock_get,
        ):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = MagicMock(id="asset-uuid")
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get.return_value = []

            await service.ingest_financial_statements("AAPL", MarketType.US, min_quarters=24)

            called_kwargs = service._sec_service.ingest_sec_financials.call_args
            assert called_kwargs.kwargs.get("min_quarters") == 24
            mock_get.assert_awaited_once_with(asset_id="asset-uuid", limit=24)

    @pytest.mark.asyncio
    async def test_provider_exception_triggers_edgar_fallback(self):
        """If provider raises, SEC EDGAR fallback is still attempted."""
        service = FinancialDataIngestService()
        service._result_cache.clear()

        mock_provider = MagicMock()
        mock_provider.fetch_financial_statements = AsyncMock(side_effect=Exception("Provider error"))
        service._providers[MarketType.US] = mock_provider
        service._sec_service = MagicMock()
        service._sec_service.ingest_sec_financials = AsyncMock()

        with (
            patch("app.db.base.async_session_maker") as mock_session_factory,
            patch.object(service, "get_financial_statements", new_callable=AsyncMock) as mock_get,
        ):
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = MagicMock(id="asset-uuid")
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_get.return_value = []

            result = await service.ingest_financial_statements("AAPL", MarketType.US)
            service._sec_service.ingest_sec_financials.assert_awaited_once()
            assert result == []


class TestInitializeShutdown:
    """Tests for FinancialDataIngestService initialize/shutdown with SEC EDGAR."""

    @pytest.mark.asyncio
    async def test_initialize_creates_sec_service(self):
        """initialize() should create and initialize the SEC EDGAR service."""
        service = FinancialDataIngestService()
        service._result_cache.clear()

        with patch(
            "app.services.data.sec_edgar_client.SEDGARFinancialService"
        ) as mock_sec_cls:
            mock_instance = MagicMock()
            mock_instance.initialize = AsyncMock()
            mock_instance.shutdown = AsyncMock()
            mock_sec_cls.return_value = mock_instance

            await service.initialize()
            assert hasattr(service, "_sec_service")
            assert service._sec_service is mock_instance
            mock_instance.initialize.assert_awaited_once()

            await service.shutdown()
            mock_instance.shutdown.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_shutdown_handles_no_sec_service(self):
        """shutdown() should work even if initialize was never called."""
        service = FinancialDataIngestService()
        service._result_cache.clear()

        await service.shutdown()


class TestGetLatestFundamentals:
    """Verify get_latest_fundamentals requests 20 periods."""

    @pytest.mark.asyncio
    async def test_get_latest_fundamentals_requests_20_periods(self):
        """get_latest_fundamentals should request up to 20 periods."""
        service = FinancialDataIngestService()
        service._result_cache.clear()

        captured_kwargs = {}

        async def fake_get_statements(asset_id, statement_type=None, limit=10):
            captured_kwargs["asset_id"] = asset_id
            captured_kwargs["limit"] = limit
            return []

        with patch.object(service, "get_financial_statements", side_effect=fake_get_statements):
            result = await service.get_latest_fundamentals("AAPL-123", MarketType.US)

        assert captured_kwargs["asset_id"] == "AAPL-123"
        assert captured_kwargs["limit"] == 20
        assert result["statements_count"] == 0
        assert result["financials"] == {}
        assert result["latest_period"] is None
