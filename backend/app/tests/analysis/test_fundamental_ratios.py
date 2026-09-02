"""
Unit tests for fundamental ratio calculations.
Tests stock fundamental analysis services.
"""
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from app.services.analysis.fundamental_service import FundamentalAnalysisService


class TestStockFundamentalRatios(unittest.TestCase):
    """Test cases for stock fundamental ratio calculations."""

    def setUp(self):
        self.service = FundamentalAnalysisService(service_name="TestStockService")

    def test_pe_ratio_calculation(self):
        """Test Price-to-Earnings ratio calculation."""
        financials = {
            "stock_price": 50.0,
            "eps": 2.5
        }
        pe_ratio = self.service._calc_pe_ratio(financials)
        self.assertEqual(pe_ratio, 20.0)

    def test_pe_ratio_zero_eps(self):
        """Test P/E ratio when EPS is zero."""
        financials = {
            "stock_price": 50.0,
            "eps": 0
        }
        pe_ratio = self.service._calc_pe_ratio(financials)
        self.assertEqual(pe_ratio, 0.0)

    def test_pb_ratio_calculation(self):
        """Test Price-to-Book ratio calculation."""
        financials = {
            "stock_price": 50.0,
            "book_value_per_share": 10.0
        }
        pb_ratio = self.service._calc_pb_ratio(financials)
        self.assertEqual(pb_ratio, 5.0)

    def test_pb_ratio_zero_book_value(self):
        """Test P/B ratio when book value is zero."""
        financials = {
            "stock_price": 50.0,
            "book_value_per_share": 0
        }
        pb_ratio = self.service._calc_pb_ratio(financials)
        self.assertEqual(pb_ratio, 0.0)

    def test_roe_calculation(self):
        """Test Return on Equity calculation."""
        financials = {
            "net_income": 10000000.0,
            "equity": 200000000.0
        }
        roe = self.service._calc_roe(financials)
        self.assertAlmostEqual(roe, 5.0, places=2)

    def test_roa_calculation(self):
        """Test Return on Assets calculation."""
        financials = {
            "net_income": 10000000.0,
            "total_assets": 500000000.0
        }
        roa = self.service._calc_roa(financials)
        self.assertAlmostEqual(roa, 2.0, places=2)

    def test_gross_margin_calculation(self):
        """Test Gross Profit Margin calculation."""
        financials = {
            "gross_profit": 300000000.0,
            "revenue": 1000000000.0
        }
        gross_margin = self.service._calc_gross_margin(financials)
        self.assertAlmostEqual(gross_margin, 30.0, places=2)

    def test_net_margin_calculation(self):
        """Test Net Profit Margin calculation."""
        financials = {
            "net_income": 100000000.0,
            "revenue": 1000000000.0
        }
        net_margin = self.service._calc_net_margin(financials)
        self.assertAlmostEqual(net_margin, 10.0, places=2)

    def test_current_ratio_calculation(self):
        """Test Current Ratio calculation."""
        financials = {
            "current_assets": 500000000.0,
            "current_liabilities": 250000000.0
        }
        current_ratio = self.service._calc_current_ratio(financials)
        self.assertEqual(current_ratio, 2.0)

    def test_quick_ratio_calculation(self):
        """Test Quick Ratio calculation."""
        financials = {
            "current_assets": 500000000.0,
            "inventory": 100000000.0,
            "current_liabilities": 250000000.0
        }
        quick_ratio = self.service._calc_quick_ratio(financials)
        self.assertEqual(quick_ratio, 1.6)

    def test_roic_calculation(self):
        """Test Return on Invested Capital calculation."""
        financials = {
            "operating_income": 200000000.0,
            "tax_rate": 0.21,
            "equity": 300000000.0,
            "debt": 100000000.0
        }
        roic = self.service._calc_roic(financials)
        expected_nopat = 200000000.0 * (1 - 0.21)
        expected_invested_capital = 300000000.0 + 100000000.0
        expected_roic = (expected_nopat / expected_invested_capital) * 100
        self.assertAlmostEqual(roic, expected_roic, places=2)

    def test_edge_case_zero_revenue(self):
        """Test margin calculations with zero revenue."""
        financials = {
            "gross_profit": 100000.0,
            "revenue": 0
        }
        gross_margin = self.service._calc_gross_margin(financials)
        self.assertEqual(gross_margin, 0.0)

    def test_dividend_payout_ratio(self):
        """Test dividend payout ratio calculation."""
        financials = {
            "dividend": 2.0,
            "earnings": 5.0
        }
        payout_ratio = self.service._calc_payout_ratio(financials)
        self.assertEqual(payout_ratio, 40.0)

    def test_asset_turnover_calculation(self):
        """Test asset turnover calculation."""
        financials = {
            "revenue": 1000000000.0,
            "total_assets": 500000000.0
        }
        asset_turnover = self.service._calc_asset_turnover(financials)
        self.assertEqual(asset_turnover, 2.0)


class TestStockFundamentalAnalysis(unittest.IsolatedAsyncioTestCase):
    """Integration tests for stock fundamental analysis."""

    async def test_analyze_with_financial_data(self):
        """Test analysis with financial data."""
        service = FundamentalAnalysisService(service_name="TestService")
        
        financial_data = {
            "stock_price": 150.0,
            "eps": 5.0,
            "book_value_per_share": 75.0,
            "revenue": 1000000000.0,
            "net_income": 200000000.0,
            "gross_profit": 500000000.0,
            "operating_income": 300000000.0,
            "equity": 800000000.0,
            "total_assets": 2000000000.0,
            "current_assets": 1000000000.0,
            "current_liabilities": 500000000.0,
            "inventory": 200000000.0,
            "cash": 100000000.0,
            "growth_rate": 0.15,
            "dividend": 2.0,
            "earnings": 5.0,
            "cost_of_goods_sold": 500000000.0,
            "accounts_receivable": 150000000.0,
            "tax_rate": 0.21,
            "debt": 200000000.0,
        }
        
        result = await service.analyze({
            "ticker": "AAPL",
            "financials": financial_data
        })
        
        self.assertEqual(result["ticker"], "AAPL")
        self.assertIn("ratios", result)
        self.assertAlmostEqual(result["ratios"]["pe_ratio"], 30.0, places=2)
        self.assertAlmostEqual(result["ratios"]["pb_ratio"], 2.0, places=2)
        self.assertAlmostEqual(result["ratios"]["roe"], 25.0, places=2)


if __name__ == "__main__":
    unittest.main()
