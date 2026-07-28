"""Unit tests for Tier 3 FundamentalAnalysisService."""

import pytest

from app.services.analysis.fundamental_service import FundamentalAnalysisService

pytestmark = pytest.mark.unit


class TestFundamentalAnalysisServiceInitialization:
    def test_default_service_name(self):
        service = FundamentalAnalysisService()
        assert service.service_name == "FundamentalAnalysisService"

    async def test_initialize_logs(self, caplog):
        service = FundamentalAnalysisService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.initialize()
        assert "FundamentalAnalysisService initialized" in caplog.text

    async def test_shutdown_logs(self, caplog):
        service = FundamentalAnalysisService()
        with caplog.at_level("INFO"):
            caplog.clear()
            await service.shutdown()
        assert "FundamentalAnalysisService shutdown" in caplog.text


class TestAnalyze:
    async def test_empty_financials_returns_structure(self):
        service = FundamentalAnalysisService()
        result = await service.analyze({"ticker": "TEST"})
        assert result["ticker"] == "TEST"
        assert "ratios" in result
        assert "assessment" in result

    async def test_full_financials_returns_ratios(self):
        service = FundamentalAnalysisService()
        financials = {
            "stock_price": 100.0,
            "eps": 5.0,
            "book_value_per_share": 40.0,
            "growth_rate": 0.15,
            "dividend": 2.0,
            "earnings": 10.0,
            "gross_profit": 50.0,
            "revenue": 200.0,
            "operating_income": 25.0,
            "net_income": 20.0,
            "equity": 100.0,
            "total_assets": 200.0,
            "debt": 50.0,
            "current_assets": 80.0,
            "current_liabilities": 40.0,
            "inventory": 20.0,
            "cash": 30.0,
            "cost_of_goods_sold": 120.0,
            "accounts_receivable": 25.0,
        }
        result = await service.analyze({"ticker": "TEST", "financials": financials})
        ratios = result["ratios"]
        assert "pe_ratio" in ratios
        assert "pb_ratio" in ratios
        assert "gross_margin" in ratios
        assert "roe" in ratios
        assert "current_ratio" in ratios


class TestValuationRatios:
    async def test_pe_ratio_basic(self):
        service = FundamentalAnalysisService()
        financials = {"stock_price": 100.0, "eps": 10.0}
        assert service._calc_pe_ratio(financials) == 10.0

    async def test_pe_ratio_zero_eps(self):
        service = FundamentalAnalysisService()
        financials = {"stock_price": 100.0, "eps": 0.0}
        assert service._calc_pe_ratio(financials) == 0.0

    async def test_pe_ratio_negative_eps(self):
        service = FundamentalAnalysisService()
        financials = {"stock_price": 100.0, "eps": -5.0}
        assert service._calc_pe_ratio(financials) == 0.0

    async def test_pb_ratio_basic(self):
        service = FundamentalAnalysisService()
        financials = {"stock_price": 80.0, "book_value_per_share": 40.0}
        assert service._calc_pb_ratio(financials) == 2.0

    async def test_pb_ratio_zero_book_value(self):
        service = FundamentalAnalysisService()
        financials = {"stock_price": 80.0, "book_value_per_share": 0.0}
        assert service._calc_pb_ratio(financials) == 0.0

    async def test_peg_ratio_basic(self):
        service = FundamentalAnalysisService()
        financials = {"stock_price": 100.0, "eps": 10.0, "growth_rate": 0.20}
        assert service._calc_peg_ratio(financials) == 50.0

    async def test_peg_ratio_zero_growth(self):
        service = FundamentalAnalysisService()
        financials = {"stock_price": 100.0, "eps": 10.0, "growth_rate": 0.0}
        assert service._calc_peg_ratio(financials) == 0.0

    async def test_payout_ratio_basic(self):
        service = FundamentalAnalysisService()
        financials = {"dividend": 2.0, "earnings": 10.0}
        assert service._calc_payout_ratio(financials) == 20.0

    async def test_payout_ratio_zero_earnings(self):
        service = FundamentalAnalysisService()
        financials = {"dividend": 2.0, "earnings": 0.0}
        assert service._calc_payout_ratio(financials) == 0.0


class TestProfitabilityRatios:
    async def test_gross_margin(self):
        service = FundamentalAnalysisService()
        financials = {"gross_profit": 50.0, "revenue": 200.0}
        assert service._calc_gross_margin(financials) == 25.0

    async def test_gross_margin_zero_revenue(self):
        service = FundamentalAnalysisService()
        financials = {"gross_profit": 50.0, "revenue": 0.0}
        assert service._calc_gross_margin(financials) == 0.0

    async def test_operating_margin(self):
        service = FundamentalAnalysisService()
        financials = {"operating_income": 30.0, "revenue": 200.0}
        assert service._calc_operating_margin(financials) == 15.0

    async def test_net_margin(self):
        service = FundamentalAnalysisService()
        financials = {"net_income": 20.0, "revenue": 200.0}
        assert service._calc_net_margin(financials) == 10.0

    async def test_roe(self):
        service = FundamentalAnalysisService()
        financials = {"net_income": 20.0, "equity": 100.0}
        assert service._calc_roe(financials) == 20.0

    async def test_roe_zero_equity(self):
        service = FundamentalAnalysisService()
        financials = {"net_income": 20.0, "equity": 0.0}
        assert service._calc_roe(financials) == 0.0

    async def test_roa(self):
        service = FundamentalAnalysisService()
        financials = {"net_income": 20.0, "total_assets": 200.0}
        assert service._calc_roa(financials) == 10.0

    async def test_roa_zero_assets(self):
        service = FundamentalAnalysisService()
        financials = {"net_income": 20.0, "total_assets": 0.0}
        assert service._calc_roa(financials) == 0.0

    async def test_roic(self):
        service = FundamentalAnalysisService()
        financials = {
            "operating_income": 25.0,
            "tax_rate": 0.21,
            "equity": 100.0,
            "debt": 50.0,
        }
        nopat = 25.0 * (1 - 0.21)
        invested = 150.0
        expected = (nopat / invested) * 100
        assert service._calc_roic(financials) == pytest.approx(expected)

    async def test_roic_zero_invested_capital(self):
        service = FundamentalAnalysisService()
        financials = {"operating_income": 25.0, "equity": 0.0, "debt": 0.0}
        assert service._calc_roic(financials) == 0.0


class TestLiquidityRatios:
    async def test_current_ratio(self):
        service = FundamentalAnalysisService()
        financials = {"current_assets": 80.0, "current_liabilities": 40.0}
        assert service._calc_current_ratio(financials) == 2.0

    async def test_current_ratio_zero_liabilities(self):
        service = FundamentalAnalysisService()
        financials = {"current_assets": 80.0, "current_liabilities": 0.0}
        assert service._calc_current_ratio(financials) == 0.0

    async def test_quick_ratio(self):
        service = FundamentalAnalysisService()
        financials = {"current_assets": 80.0, "inventory": 20.0, "current_liabilities": 40.0}
        assert service._calc_quick_ratio(financials) == 1.5

    async def test_quick_ratio_zero_liabilities(self):
        service = FundamentalAnalysisService()
        financials = {"current_assets": 80.0, "inventory": 20.0, "current_liabilities": 0.0}
        assert service._calc_quick_ratio(financials) == 0.0

    async def test_cash_ratio(self):
        service = FundamentalAnalysisService()
        financials = {"cash": 30.0, "current_liabilities": 40.0}
        assert service._calc_cash_ratio(financials) == 0.75

    async def test_cash_ratio_zero_liabilities(self):
        service = FundamentalAnalysisService()
        financials = {"cash": 30.0, "current_liabilities": 0.0}
        assert service._calc_cash_ratio(financials) == 0.0


class TestEfficiencyRatios:
    async def test_asset_turnover(self):
        service = FundamentalAnalysisService()
        financials = {"revenue": 500.0, "total_assets": 200.0}
        assert service._calc_asset_turnover(financials) == 2.5

    async def test_asset_turnover_zero_assets(self):
        service = FundamentalAnalysisService()
        financials = {"revenue": 500.0, "total_assets": 0.0}
        assert service._calc_asset_turnover(financials) == 0.0

    async def test_inventory_turnover(self):
        service = FundamentalAnalysisService()
        financials = {"cost_of_goods_sold": 300.0, "inventory": 50.0}
        assert service._calc_inventory_turnover(financials) == 6.0

    async def test_inventory_turnover_zero_inventory(self):
        service = FundamentalAnalysisService()
        financials = {"cost_of_goods_sold": 300.0, "inventory": 0.0}
        assert service._calc_inventory_turnover(financials) == 0.0

    async def test_receivables_turnover(self):
        service = FundamentalAnalysisService()
        financials = {"revenue": 400.0, "accounts_receivable": 50.0}
        assert service._calc_receivables_turnover(financials) == 8.0

    async def test_receivables_turnover_zero_ar(self):
        service = FundamentalAnalysisService()
        financials = {"revenue": 400.0, "accounts_receivable": 0.0}
        assert service._calc_receivables_turnover(financials) == 0.0
