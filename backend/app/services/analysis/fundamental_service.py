"""
Fundamental Analysis Service - Tier 3 Analysis Service

Fundamental financial analysis and ratio calculations.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from ..core import AnalysisService


class FundamentalAnalysisService(AnalysisService):
    """
    Fundamental analysis service.

    Provides:
    - Financial ratios (P/E, PB, ROE, ROA, Debt-to-Equity, Interest Coverage, FCF Yield)
    - Profitability analysis (Gross Margin, Op Margin, Net Margin, ROE, ROA, ROIC)
    - Liquidity analysis (Current Ratio, Quick Ratio, Cash Ratio)
    - Solvency analysis (Debt-to-Equity, Debt-to-Assets, Interest Coverage)
    - Efficiency metrics (Asset Turnover, Inventory Turnover, Receivables Turnover)
    - Dividend analysis (Yield, Payout Ratio, Growth Rate)
    - Trend analysis (YoY, QoQ comparisons)
    - Health score framework
    """

    def __init__(self, service_name: str = "FundamentalAnalysisService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("FundamentalAnalysisService initialized")

    async def shutdown(self) -> None:
        self.logger.info("FundamentalAnalysisService shutdown")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        financials = data.get("financials", {})
        ticker = data.get("ticker", "UNKNOWN")

        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticker": ticker,
            "ratios": {},
            "assessment": "",
            "health_score": 0.0,
        }

        analysis["ratios"].update(
            await self._calculate_valuation_ratios(financials)
        )
        analysis["ratios"].update(
            await self._calculate_profitability_ratios(financials)
        )
        analysis["ratios"].update(
            await self._calculate_liquidity_ratios(financials)
        )
        analysis["ratios"].update(
            await self._calculate_efficiency_ratios(financials)
        )
        analysis["ratios"].update(
            await self._calculate_solvency_ratios(financials)
        )
        analysis["ratios"].update(
            await self._calculate_dividend_ratios(financials)
        )
        analysis["ratios"].update(
            await self._calculate_growth_ratios(financials)
        )
        analysis["ratios"].update(
            await self._calculate_cash_flow_ratios(financials)
        )

        analysis["health_score"] = self._calculate_health_score(analysis["ratios"])

        profitability = analysis["ratios"].get("net_margin", 0.0)
        liquidity = analysis["ratios"].get("current_ratio", 0.0)
        leverage = analysis["ratios"].get("debt_to_equity", 999.0)
        solvency = analysis["ratios"].get("interest_coverage", 0.0)

        if profitability > 15 and liquidity > 1.5 and leverage < 1.0 and solvency > 3.0:
            analysis["assessment"] = "Strong"
        elif profitability > 8 and liquidity > 1.0 and leverage < 2.0 and solvency > 1.5:
            analysis["assessment"] = "Moderate"
        elif profitability > 0 and liquidity > 0.5 and leverage < 4.0 and solvency > 0.5:
            analysis["assessment"] = "Weak"
        else:
            analysis["assessment"] = "Distressed"

        return analysis

    async def _calculate_valuation_ratios(self, financials: Dict[str, Any]) -> Dict[str, float]:
        return {
            "pe_ratio": self._calc_pe_ratio(financials),
            "pb_ratio": self._calc_pb_ratio(financials),
            "peg_ratio": self._calc_peg_ratio(financials),
            "payout_ratio": self._calc_payout_ratio(financials),
            "price_to_sales": self._calc_price_to_sales(financials),
            "price_to_cash_flow": self._calc_price_to_cash_flow(financials),
            "ev_to_ebitda": self._calc_ev_to_ebitda(financials),
        }

    async def _calculate_profitability_ratios(self, financials: Dict[str, Any]) -> Dict[str, float]:
        return {
            "gross_margin": self._calc_gross_margin(financials),
            "operating_margin": self._calc_operating_margin(financials),
            "net_margin": self._calc_net_margin(financials),
            "roe": self._calc_roe(financials),
            "roa": self._calc_roa(financials),
            "roic": self._calc_roic(financials),
            "ebitda_margin": self._calc_ebitda_margin(financials),
            "operating_leverage": self._calc_operating_leverage(financials),
        }

    async def _calculate_liquidity_ratios(self, financials: Dict[str, Any]) -> Dict[str, float]:
        return {
            "current_ratio": self._calc_current_ratio(financials),
            "quick_ratio": self._calc_quick_ratio(financials),
            "cash_ratio": self._calc_cash_ratio(financials),
        }

    async def _calculate_efficiency_ratios(self, financials: Dict[str, Any]) -> Dict[str, float]:
        return {
            "asset_turnover": self._calc_asset_turnover(financials),
            "inventory_turnover": self._calc_inventory_turnover(financials),
            "receivables_turnover": self._calc_receivables_turnover(financials),
        }

    async def _calculate_solvency_ratios(self, financials: Dict[str, Any]) -> Dict[str, float]:
        return {
            "debt_to_equity": self._calc_debt_to_equity(financials),
            "debt_to_assets": self._calc_debt_to_assets(financials),
            "interest_coverage": self._calc_interest_coverage(financials),
            "debt_to_ebitda": self._calc_debt_to_ebitda(financials),
        }

    async def _calculate_dividend_ratios(self, financials: Dict[str, Any]) -> Dict[str, float]:
        return {
            "dividend_yield": self._calc_dividend_yield(financials),
            "payout_ratio": self._calc_payout_ratio(financials),
            "dividend_growth_rate": self._calc_dividend_growth_rate(financials),
        }

    async def _calculate_growth_ratios(self, financials: Dict[str, Any]) -> Dict[str, float]:
        return {
            "revenue_growth": self._calc_revenue_growth(financials),
            "earnings_growth": self._calc_earnings_growth(financials),
            "free_cash_flow_growth": self._calc_free_cash_flow_growth(financials),
        }

    async def _calculate_cash_flow_ratios(self, financials: Dict[str, Any]) -> Dict[str, float]:
        return {
            "free_cash_flow_yield": self._calc_free_cash_flow_yield(financials),
            "operating_cash_flow_ratio": self._calc_operating_cash_flow_ratio(financials),
            "capex_ratio": self._calc_capex_ratio(financials),
            "cash_conversion_ratio": self._calc_cash_conversion_ratio(financials),
        }

    # ── Valuation Ratios ──

    def _calc_pe_ratio(self, f: Dict[str, Any]) -> float:
        stock_price = f.get("stock_price", 0) or 0.0
        eps = f.get("eps", 0) or 0.0
        if eps <= 0 or stock_price <= 0:
            return 0.0
        return stock_price / eps

    def _calc_pb_ratio(self, f: Dict[str, Any]) -> float:
        stock_price = f.get("stock_price", 0) or 0.0
        book_value_per_share = f.get("book_value_per_share", 0) or 0.0
        if book_value_per_share <= 0 or stock_price <= 0:
            return 0.0
        return stock_price / book_value_per_share

    def _calc_peg_ratio(self, f: Dict[str, Any]) -> float:
        pe_ratio = self._calc_pe_ratio(f)
        growth_rate = f.get("growth_rate", 1) or 1
        if growth_rate <= 0 or pe_ratio <= 0:
            return 0.0
        return pe_ratio / growth_rate

    def _calc_payout_ratio(self, f: Dict[str, Any]) -> float:
        dividend = f.get("dividend", 0) or 0.0
        earnings = f.get("earnings", 0) or 0.0
        if earnings <= 0:
            return 0.0
        return (dividend / earnings) * 100

    def _calc_price_to_sales(self, f: Dict[str, Any]) -> float:
        stock_price = f.get("stock_price", 0) or 0.0
        shares = f.get("shares_outstanding", 0) or 0.0
        revenue = f.get("revenue", 0) or 0.0
        if shares <= 0 or revenue <= 0:
            return 0.0
        market_cap = stock_price * shares
        return market_cap / revenue

    def _calc_price_to_cash_flow(self, f: Dict[str, Any]) -> float:
        stock_price = f.get("stock_price", 0) or 0.0
        shares = f.get("shares_outstanding", 0) or 0.0
        operating_cf = f.get("operating_cash_flow", 0) or 0.0
        if shares <= 0 or operating_cf <= 0:
            return 0.0
        market_cap = stock_price * shares
        return market_cap / operating_cf

    def _calc_ev_to_ebitda(self, f: Dict[str, Any]) -> float:
        stock_price = f.get("stock_price", 0) or 0.0
        shares = f.get("shares_outstanding", 0) or 0.0
        debt = f.get("total_debt", 0) or 0.0
        cash = f.get("cash", 0) or 0.0
        ebitda = self._calc_ebitda(f)
        if shares <= 0 or ebitda <= 0:
            return 0.0
        equity_value = stock_price * shares
        enterprise_value = equity_value + debt - cash
        return enterprise_value / ebitda

    # ── Profitability Ratios ──

    def _calc_gross_margin(self, f: Dict[str, Any]) -> float:
        gross_profit = f.get("gross_profit", 0) or 0.0
        revenue = f.get("revenue", 0) or 0.0
        if revenue <= 0:
            return 0.0
        return (gross_profit / revenue) * 100

    def _calc_operating_margin(self, f: Dict[str, Any]) -> float:
        operating_income = f.get("operating_income", 0) or 0.0
        revenue = f.get("revenue", 0) or 0.0
        if revenue <= 0:
            return 0.0
        return (operating_income / revenue) * 100

    def _calc_net_margin(self, f: Dict[str, Any]) -> float:
        net_income = f.get("net_income", 0) or 0.0
        revenue = f.get("revenue", 0) or 0.0
        if revenue <= 0:
            return 0.0
        return (net_income / revenue) * 100

    def _calc_roe(self, f: Dict[str, Any]) -> float:
        net_income = f.get("net_income", 0) or 0.0
        equity = f.get("equity", 0) or 0.0
        if equity <= 0:
            return 0.0
        return (net_income / equity) * 100

    def _calc_roa(self, f: Dict[str, Any]) -> float:
        net_income = f.get("net_income", 0) or 0.0
        total_assets = f.get("total_assets", 0) or 0.0
        if total_assets <= 0:
            return 0.0
        return (net_income / total_assets) * 100

    def _calc_roic(self, f: Dict[str, Any]) -> float:
        operating_income = f.get("operating_income", 0) or 0.0
        tax_rate = f.get("tax_rate", 0.21) or 0.21
        nopat = operating_income * (1 - tax_rate)
        invested_capital = (f.get("equity", 0) or 0.0) + (f.get("debt", 0) or 0.0)
        if invested_capital <= 0:
            return 0.0
        return (nopat / invested_capital) * 100

    def _calc_ebitda_margin(self, f: Dict[str, Any]) -> float:
        ebitda = self._calc_ebitda(f)
        revenue = f.get("revenue", 0) or 0.0
        if revenue <= 0:
            return 0.0
        return (ebitda / revenue) * 100

    def _calc_operating_leverage(self, f: Dict[str, Any]) -> float:
        operating_income = f.get("operating_income", 0) or 0.0
        revenue = f.get("revenue", 0) or 0.0
        if revenue <= 0:
            return 0.0
        return (operating_income / revenue) * revenue

    # ── Liquidity Ratios ──

    def _calc_current_ratio(self, f: Dict[str, Any]) -> float:
        current_assets = f.get("current_assets", 0) or 0.0
        current_liabilities = f.get("current_liabilities", 0) or 0.0
        if current_liabilities <= 0:
            return 0.0
        return current_assets / current_liabilities

    def _calc_quick_ratio(self, f: Dict[str, Any]) -> float:
        current_assets = f.get("current_assets", 0) or 0.0
        inventory = f.get("inventory", 0) or 0.0
        current_liabilities = f.get("current_liabilities", 0) or 0.0
        if current_liabilities <= 0:
            return 0.0
        return (current_assets - inventory) / current_liabilities

    def _calc_cash_ratio(self, f: Dict[str, Any]) -> float:
        cash = f.get("cash", 0) or 0.0
        current_liabilities = f.get("current_liabilities", 0) or 0.0
        if current_liabilities <= 0:
            return 0.0
        return cash / current_liabilities

    # ── Efficiency Ratios ──

    def _calc_asset_turnover(self, f: Dict[str, Any]) -> float:
        revenue = f.get("revenue", 0) or 0.0
        total_assets = f.get("total_assets", 0) or 0.0
        if total_assets <= 0:
            return 0.0
        return revenue / total_assets

    def _calc_inventory_turnover(self, f: Dict[str, Any]) -> float:
        cogs = f.get("cost_of_goods_sold", 0) or 0.0
        inventory = f.get("inventory", 0) or 0.0
        if inventory <= 0:
            return 0.0
        return cogs / inventory

    def _calc_receivables_turnover(self, f: Dict[str, Any]) -> float:
        revenue = f.get("revenue", 0) or 0.0
        accounts_receivable = f.get("accounts_receivable", 0) or 0.0
        if accounts_receivable <= 0:
            return 0.0
        return revenue / accounts_receivable

    # ── Solvency Ratios ──

    def _calc_debt_to_equity(self, f: Dict[str, Any]) -> float:
        equity = f.get("equity", 0) or 0.0
        debt = f.get("total_debt", 0) or 0.0
        if equity <= 0:
            return 0.0
        return debt / equity

    def _calc_debt_to_assets(self, f: Dict[str, Any]) -> float:
        total_assets = f.get("total_assets", 0) or 0.0
        debt = f.get("total_debt", 0) or 0.0
        if total_assets <= 0:
            return 0.0
        return debt / total_assets

    def _calc_interest_coverage(self, f: Dict[str, Any]) -> float:
        ebit = f.get("ebit", 0) or 0.0
        interest_expense = f.get("interest_expense", 0) or 0.0
        if interest_expense <= 0:
            return 0.0
        return ebit / interest_expense

    def _calc_debt_to_ebitda(self, f: Dict[str, Any]) -> float:
        debt = f.get("total_debt", 0) or 0.0
        ebitda = self._calc_ebitda(f)
        if ebitda <= 0:
            return 0.0
        return debt / ebitda

    # ── Dividend Ratios ──

    def _calc_dividend_yield(self, f: Dict[str, Any]) -> float:
        dividend_per_share = f.get("dividend_per_share", 0) or 0.0
        stock_price = f.get("stock_price", 0) or 0.0
        if stock_price <= 0:
            return 0.0
        return (dividend_per_share / stock_price) * 100

    def _calc_dividend_growth_rate(self, f: Dict[str, Any]) -> float:
        dividend_growth = f.get("dividend_growth", 0) or 0.0
        return float(dividend_growth)

    # ── Growth Ratios ──

    def _calc_revenue_growth(self, f: Dict[str, Any]) -> float:
        revenue_growth = f.get("revenue_growth", 0) or 0.0
        return float(revenue_growth)

    def _calc_earnings_growth(self, f: Dict[str, Any]) -> float:
        earnings_growth = f.get("earnings_growth", 0) or 0.0
        return float(earnings_growth)

    def _calc_free_cash_flow_growth(self, f: Dict[str, Any]) -> float:
        fcf_growth = f.get("free_cash_flow_growth", 0) or 0.0
        return float(fcf_growth)

    # ── Cash Flow Ratios ──

    def _calc_free_cash_flow_yield(self, f: Dict[str, Any]) -> float:
        stock_price = f.get("stock_price", 0) or 0.0
        shares = f.get("shares_outstanding", 0) or 0.0
        free_cash_flow = f.get("free_cash_flow", 0) or 0.0
        if shares <= 0 or free_cash_flow <= 0:
            return 0.0
        market_cap = stock_price * shares
        return (free_cash_flow / market_cap) * 100

    def _calc_operating_cash_flow_ratio(self, f: Dict[str, Any]) -> float:
        operating_cf = f.get("operating_cash_flow", 0) or 0.0
        revenue = f.get("revenue", 0) or 0.0
        if revenue <= 0:
            return 0.0
        return operating_cf / revenue

    def _calc_capex_ratio(self, f: Dict[str, Any]) -> float:
        capex = f.get("capital_expenditure", 0) or 0.0
        revenue = f.get("revenue", 0) or 0.0
        if revenue <= 0:
            return 0.0
        return capex / revenue

    def _calc_cash_conversion_ratio(self, f: Dict[str, Any]) -> float:
        net_income = f.get("net_income", 0) or 0.0
        operating_cf = f.get("operating_cash_flow", 0) or 0.0
        if net_income <= 0:
            return 0.0
        return operating_cf / net_income

    # ── Helpers ──

    def _calc_ebitda(self, f: Dict[str, Any]) -> float:
        operating_income = f.get("operating_income", 0) or 0.0
        depreciation = f.get("depreciation", 0) or 0.0
        amortization = f.get("amortization", 0) or 0.0
        return operating_income + depreciation + amortization

    def _calculate_health_score(self, ratios: Dict[str, float]) -> float:
        """
        Stock fundamental health score (0-100).

        Weighted across key dimensions:
          - Profitability margin (weight 30)
          - Liquidity (weight 20)  
          - Leverage/solvency (weight 25)
          - Growth (weight 15)
          - Valuation reasonableness (weight 10)
        """
        score = 0.0
        net_margin = ratios.get("net_margin", 0.0)
        score += min(net_margin / 20.0 * 30, 30)

        current_ratio = ratios.get("current_ratio", 0.0)
        score += min(current_ratio / 2.0 * 20, 20)

        debt_to_equity = ratios.get("debt_to_equity", 999.0)
        interest_coverage = ratios.get("interest_coverage", 0.0)
        solvency_pct = max(0, 25 - debt_to_equity * 5)
        if interest_coverage > 3.0:
            solvency_pct += 5
        score += max(0, solvency_pct)

        revenue_growth = ratios.get("revenue_growth", 0.0)
        fcf_growth = ratios.get("free_cash_flow_growth", 0.0)
        growth_pct = min((revenue_growth + fcf_growth) / 4.0 * 15, 15)
        score += max(0, growth_pct)

        pe_ratio = ratios.get("pe_ratio", 999.0)
        pb_ratio = ratios.get("pb_ratio", 999.0)
        if 5 <= pe_ratio <= 30 and 0.5 <= pb_ratio <= 5:
            score += 10
        elif 10 <= pe_ratio <= 50 and 1 <= pb_ratio <= 10:
            score += 5
        score += min(max(0, 10 - pe_ratio * 0.05 + pb_ratio * 0.5), 10)

        return round(max(0, min(100, score)), 2)

    def _calculate_dupont_analysis(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate DuPont analysis for ROE decomposition.
        
        ROE = Net Profit Margin × Asset Turnover × Financial Leverage
        ROE = (Net Income / Revenue) × (Revenue / Assets) × (Assets / Equity)
        """
        net_income = financials.get("net_income", 0) or 0.0
        revenue = financials.get("revenue", 0) or 0.0
        total_assets = financials.get("total_assets", 0) or 0.0
        equity = financials.get("equity", 0) or 0.0
        
        # Avoid division by zero
        if revenue <= 0 or total_assets <= 0 or equity <= 0:
            return {
                "roe": 0.0,
                "net_profit_margin": 0.0,
                "asset_turnover": 0.0,
                "financial_leverage": 0.0,
                "dupont_breakdown": "Insufficient data for calculation"
            }
        
        # Calculate components
        net_profit_margin = (net_income / revenue) * 100  # Percentage
        asset_turnover = revenue / total_assets
        financial_leverage = total_assets / equity
        roe = (net_income / equity) * 100  # Percentage
        
        # Verify DuPont identity: ROE = NPM × AT × FL
        calculated_roe = net_profit_margin * asset_turnover * financial_leverage / 100  # Adjust for percentage
        
        return {
            "roe": round(roe, 2),
            "net_profit_margin": round(net_profit_margin, 2),
            "asset_turnover": round(asset_turnover, 2),
            "financial_leverage": round(financial_leverage, 2),
            "dupont_identity_check": round(abs(roe - calculated_roe), 4) < 0.01,  # Should be True if calculation is correct
            "dupont_breakdown": f"ROE ({roe:.2f}%) = Net Margin ({net_profit_margin:.2f}%) × Asset Turnover ({asset_turnover:.2f}) × Financial Leverage ({financial_leverage:.2f})"
        }
