"""Unit tests for Tier 2 PortfolioService."""

import pytest

from app.services.data.portfolio_service import PortfolioService

pytestmark = pytest.mark.unit


class TestPortfolioServiceInitialization:
    def test_default_service_name(self):
        service = PortfolioService()
        assert service.service_name == "PortfolioService"

    async def test_initialize_logs(self, caplog):
        service = PortfolioService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "PortfolioService initialized" in caplog.text

    async def test_shutdown_logs(self, caplog):
        service = PortfolioService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.shutdown()
        assert "PortfolioService shutdown" in caplog.text


class TestCRUD:
    async def test_get_by_id_returns_none(self):
        service = PortfolioService()
        assert await service.get_by_id(1) is None

    async def test_list_all_returns_empty(self):
        service = PortfolioService()
        assert await service.list_all() == []

    async def test_create_returns_data(self):
        service = PortfolioService()
        data = {"name": "My Portfolio", "type": "PERSONAL"}
        result = await service.create(data)
        assert result == data

    async def test_update_returns_data(self):
        service = PortfolioService()
        data = {"name": "Updated"}
        result = await service.update(1, data)
        assert result == data

    async def test_delete_returns_true(self):
        service = PortfolioService()
        assert await service.delete(1) is True

    async def test_add_holding_creates_holding_dict(self):
        service = PortfolioService()
        holding = await service.add_holding(
            portfolio_id=1,
            stock_ticker="فملی",
            quantity=100,
            purchase_price=1234.5,
        )
        assert holding["portfolio_id"] == 1
        assert holding["stock_ticker"] == "فملی"
        assert holding["quantity"] == 100
        assert holding["purchase_price"] == 1234.5
        assert "purchase_date" in holding

    async def test_remove_holding_returns_true(self):
        service = PortfolioService()
        assert await service.remove_holding(1, 1) is True

    async def test_get_holdings_returns_empty(self):
        service = PortfolioService()
        assert await service.get_holdings(1) == []


class TestCalculateValue:
    async def test_computes_total_value(self):
        service = PortfolioService()
        current_prices = {"فملی": 1500.0, "خودرو": 2000.0}
        result = await service.calculate_value(1, current_prices)
        assert "total_current_value" in result
        assert "total_purchase_value" in result
        assert "total_gain_loss" in result
        assert "gain_loss_percent" in result

    async def test_zero_holdings_returns_zero(self):
        service = PortfolioService()
        result = await service.calculate_value(1, {})
        assert result["total_current_value"] == 0.0
        assert result["total_purchase_value"] == 0.0
        assert result["gain_loss_percent"] == 0
