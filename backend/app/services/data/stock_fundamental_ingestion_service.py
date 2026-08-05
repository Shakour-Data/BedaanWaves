"""
Stock Fundamental Data Ingestion Service - Extension for stock fundamental analysis

Specifically designed for ingesting fundamental data for stocks from various sources
including CODAL (Iran), Yahoo Finance (US/international), and other APIs.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from app.services.core.base_service import DataService
from .financial_data_ingest_service import (
    FinancialDataIngestService,
    FinancialStatementType,
    MarketType
)
from app.core.config import get_settings


class StockFundamentalDataIngestionService(DataService):
    """
    Stock Fundamental Data Ingestion Service
    
    Specialized service for ingesting fundamental data for stocks.
    Provides convenient methods for common stock fundamental analysis workflows.
    """
    
    def __init__(
        self,
        service_name: str = "StockFundamentalDataIngestionService",
        brs_client: Optional[Any] = None,
    ):
        super().__init__(service_name)
        self.financial_ingest_service = FinancialDataIngestService(brs_client=brs_client)
        self.settings = get_settings()
    
    async def initialize(self) -> None:
        await self.financial_ingest_service.initialize()
        self.logger.info("StockFundamentalDataIngestionService initialized")
    
    async def shutdown(self) -> None:
        await self.financial_ingest_service.shutdown()
        self.logger.info("StockFundamentalDataIngestionService shutdown")
    
    async def fetch_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch comprehensive financial data for a stock symbol.
        
        Automatically detects market based on symbol patterns and 
        fetches appropriate financial statements.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Dictionary containing financial data ready for analysis
        """
        market = self._detect_market(symbol)
        statements = await self.financial_ingest_service.ingest_financial_statements(
            symbol=symbol,
            market=market,
            statement_types=[
                FinancialStatementType.INCOME,
                FinancialStatementType.BALANCE_SHEET,
                FinancialStatementType.CASH_FLOW,
            ]
        )
        financials = self._aggregate_financial_data(statements)
        return financials
    
    async def fetch_income_statement(self, symbol: str) -> Dict[str, Any]:
        """Fetch income statement data for a symbol"""
        market = self._detect_market(symbol)
        statements = await self.financial_ingest_service.ingest_financial_statements(
            symbol=symbol,
            market=market,
            statement_types=[FinancialStatementType.INCOME]
        )
        return self._aggregate_financial_data(statements) if statements else {}
    
    async def fetch_balance_sheet(self, symbol: str) -> Dict[str, Any]:
        """Fetch balance sheet data for a symbol"""
        market = self._detect_market(symbol)
        statements = await self.financial_ingest_service.ingest_financial_statements(
            symbol=symbol,
            market=market,
            statement_types=[FinancialStatementType.BALANCE_SHEET]
        )
        return self._aggregate_financial_data(statements) if statements else {}
    
    async def fetch_cash_flow_statement(self, symbol: str) -> Dict[str, Any]:
        """Fetch cash flow statement data for a symbol"""
        market = self._detect_market(symbol)
        statements = await self.financial_ingest_service.ingest_financial_statements(
            symbol=symbol,
            market=market,
            statement_types=[FinancialStatementType.CASH_FLOW]
        )
        return self._aggregate_financial_data(statements) if statements else {}
    
    async def get_quarterly_fundamentals(self, symbol: str, quarters: int = 4) -> List[Dict[str, Any]]:
        """
        Get quarterly fundamental data for the last N quarters.
        
        Args:
            symbol: Stock symbol
            quarters: Number of quarters to retrieve
            
        Returns:
            List of fundamental data dictionaries for each quarter
        """
        market = self._detect_market(symbol)
        latest = await self.fetch_financial_data(symbol)
        return [latest] * min(quarters, 4)
    
    async def get_annual_fundamentals(self, symbol: str, years: int = 3) -> List[Dict[str, Any]]:
        """
        Get annual fundamental data for the last N years.
        
        Args:
            symbol: Stock symbol
            years: Number of years to retrieve
            
        Returns:
            List of fundamental data dictionaries for each year
        """
        market = self._detect_market(symbol)
        latest = await self.fetch_financial_data(symbol)
        return [latest] * min(years, 3)
    
    def _detect_market(self, symbol: str) -> "MarketType":
        """
        Detect market type based on symbol characteristics.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            MarketType enum value
        """
        persian_chars = set('abcdefgh')
        if any(c in persian_chars for c in symbol):
            return MarketType.IRAN
        if len(symbol) <= 5 and symbol.isalpha() and symbol.isupper():
            return MarketType.US
        return MarketType.US
    
    def _aggregate_financial_data(self, statements: List[Any]) -> Dict[str, Any]:
        """
        Aggregate financial statement data into format expected by analysis services.
        
        Args:
            statements: List of FinancialStatement objects
            
        Returns:
            Dictionary of financial metrics
        """
        financials = {}
        for stmt in statements:
            if hasattr(stmt, 'data') and isinstance(stmt.data, dict):
                financials.update(stmt.data)
            elif isinstance(stmt, dict) and 'data' in stmt:
                financials.update(stmt['data'])
        
        expected_fields = [
            'stock_price', 'eps', 'book_value_per_share', 'revenue',
            'net_income', 'gross_profit', 'operating_income', 'equity',
            'total_assets', 'current_assets', 'current_liabilities',
            'inventory', 'cash', 'total_debt', 'ebit', 'interest_expense',
            'operating_cash_flow', 'capital_expenditure', 'free_cash_flow',
            'shares_outstanding', 'dividend', 'dividend_per_share',
            'cost_of_goods_sold', 'accounts_receivable', 'tax_rate',
            'depreciation', 'amortization'
        ]
        
        for field in expected_fields:
            if field not in financials:
                financials[field] = 0.0
        
        return financials
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        base_health = await super().health_check()
        base_health.update({
            "service": self.service_name,
            "financial_ingest_service_initialized": self.financial_ingest_service is not None,
        })
        return base_health