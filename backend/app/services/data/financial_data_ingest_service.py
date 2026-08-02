"""
Financial Data Ingestion Service - Tier 2 Data Service

Fetches and processes financial statements from multiple sources:
- Iranian market (CODAL via BRS API)
- US markets (Yahoo Finance, Alpha Vantage)
- International markets (various APIs)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from ..core import DataService
from .brs_api_client import BrsApiClient
from app.core.config import get_settings


class FinancialStatementType(str, Enum):
    """Types of financial statements"""
    INCOME = "INCOME"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASH_FLOW = "CASH_FLOW"
    COMPREHENSIVE_INCOME = "COMPREHENSIVE_INCOME"


class MarketType(str, Enum):
    """Supported market types"""
    IRAN = "IRAN"
    US = "US"
    INTERNATIONAL = "INTERNATIONAL"
    CRYPTO = "CRYPTO"


@dataclass
class FinancialStatement:
    """Standardized financial statement structure"""
    asset_id: str
    symbol: str
    market: MarketType
    statement_type: FinancialStatementType
    period: str  # e.g., "2024-Q1", "1403-Q1"
    fiscal_year: int
    fiscal_quarter: Optional[int]
    data: Dict[str, Any]
    source: str
    fetched_at: datetime
    as_of: Optional[datetime] = None


class FinancialDataProvider(ABC):
    """Abstract base class for financial data providers"""
    
    @abstractmethod
    async def fetch_financial_statements(
        self,
        symbol: str,
        statement_types: List[FinancialStatementType],
        periods: Optional[List[str]] = None
    ) -> List[FinancialStatement]:
        pass
    
    @abstractmethod
    async def get_supported_markets(self) -> List[MarketType]:
        pass


class BrsFinancialDataProvider(FinancialDataProvider):
    """Financial data provider for Iranian market via BRS API / CODAL"""
    
    def __init__(self, brs_client: BrsApiClient):
        self.brs_client = brs_client
    
    async def fetch_financial_statements(
        self,
        symbol: str,
        statement_types: List[FinancialStatementType],
        periods: Optional[List[str]] = None
    ) -> List[FinancialStatement]:
        statements = []
        
        # CODAL categories: 1=Annual financial, 3=Monthly performance
        category_map = {
            FinancialStatementType.INCOME: 1,
            FinancialStatementType.BALANCE_SHEET: 1,
            FinancialStatementType.CASH_FLOW: 1,
        }
        
        for stmt_type in statement_types:
            category = category_map.get(stmt_type, 1)
            try:
                codal_data = await self.brs_client.get_codal(l18=symbol, category=category)
                
                for announcement in codal_data.get("announcements", []):
                    # Parse the financial data from announcement
                    parsed = self._parse_codal_announcement(announcement, stmt_type)
                    if parsed:
                        statements.append(parsed)
                        
            except Exception as e:
                # Log error but continue
                pass
        
        return statements
    
    def _parse_codal_announcement(
        self,
        announcement: Dict[str, Any],
        stmt_type: FinancialStatementType
    ) -> Optional[FinancialStatement]:
        """Parse CODAL announcement into standardized financial statement"""
        try:
            # This would parse the actual CODAL response structure
            # Simplified for now
            return FinancialStatement(
                asset_id=announcement.get("symbol", ""),
                symbol=announcement.get("symbol", ""),
                market=MarketType.IRAN,
                statement_type=stmt_type,
                period=announcement.get("period", ""),
                fiscal_year=int(announcement.get("fiscal_year", 0)),
                fiscal_quarter=announcement.get("fiscal_quarter"),
                data=announcement.get("financial_data", {}),
                source="CODAL",
                fetched_at=datetime.now(timezone.utc),
                as_of=datetime.fromisoformat(announcement.get("publish_date", "")) if announcement.get("publish_date") else None
            )
        except Exception:
            return None
    
    async def get_supported_markets(self) -> List[MarketType]:
        return [MarketType.IRAN]


class YahooFinanceProvider(FinancialDataProvider):
    """Financial data provider for US and international markets via Yahoo Finance"""
    
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v10/finance"
        self.settings = get_settings()
    
    async def fetch_financial_statements(
        self,
        symbol: str,
        statement_types: List[FinancialStatementType],
        periods: Optional[List[str]] = None
    ) -> List[FinancialStatement]:
        # This would integrate with Yahoo Finance API
        # For now, return empty list - implementation would use yfinance or similar
        return []
    
    async def get_supported_markets(self) -> List[MarketType]:
        return [MarketType.US, MarketType.INTERNATIONAL]


class AlphaVantageProvider(FinancialDataProvider):
    """Financial data provider via Alpha Vantage API"""
    
    def __init__(self):
        self.base_url = "https://www.alphavantage.co/query"
        self.settings = get_settings()
        # Use getattr with default None for optional API key
        self.api_key = getattr(self.settings, 'ALPHA_VANTAGE_API_KEY', None)
    
    async def fetch_financial_statements(
        self,
        symbol: str,
        statement_types: List[FinancialStatementType],
        periods: Optional[List[str]] = None
    ) -> List[FinancialStatement]:
        if not self.api_key:
            return []
        
        # This would integrate with Alpha Vantage API
        # For now, return empty list
        return []
    
    async def get_supported_markets(self) -> List[MarketType]:
        return [MarketType.US, MarketType.INTERNATIONAL]


class FinancialDataIngestService(DataService):
    """
    Financial Data Ingestion Service
    
    Coordinates fetching financial statements from multiple providers
    and storing them in the database.
    """
    
    def __init__(
        self,
        service_name: str = "FinancialDataIngestService",
        brs_client: Optional[BrsApiClient] = None,
    ):
        super().__init__(service_name)
        self.brs_client = brs_client
        self.providers: Dict[MarketType, FinancialDataProvider] = {}
        self._register_providers()
    
    def _register_providers(self) -> None:
        """Register default data providers"""
        if self.brs_client:
            self.providers[MarketType.IRAN] = BrsFinancialDataProvider(self.brs_client)
        
        self.providers[MarketType.US] = YahooFinanceProvider()
        self.providers[MarketType.INTERNATIONAL] = AlphaVantageProvider()
    
    def register_provider(self, market: MarketType, provider: FinancialDataProvider) -> None:
        """Register a custom data provider"""
        self.providers[market] = provider
    
    async def initialize(self) -> None:
        if self.brs_client:
            await self.brs_client.initialize()
        self.logger.info("FinancialDataIngestService initialized")
    
    async def shutdown(self) -> None:
        if self.brs_client:
            await self.brs_client.shutdown()
        self.logger.info("FinancialDataIngestService shutdown")
    
    async def ingest_financial_statements(
        self,
        symbol: str,
        market: MarketType,
        statement_types: Optional[List[FinancialStatementType]] = None,
        periods: Optional[List[str]] = None
    ) -> List[FinancialStatement]:
        """
        Fetch and store financial statements for a symbol.
        
        Args:
            symbol: Stock symbol/ticker
            market: Market type (IRAN, US, INTERNATIONAL)
            statement_types: Types of statements to fetch (default: all)
            periods: Specific periods to fetch (default: latest)
            
        Returns:
            List of ingested financial statements
        """
        if statement_types is None:
            statement_types = [
                FinancialStatementType.INCOME,
                FinancialStatementType.BALANCE_SHEET,
                FinancialStatementType.CASH_FLOW,
            ]
        
        provider = self.providers.get(market)
        if not provider:
            raise ValueError(f"No provider registered for market: {market}")
        
        statements = await provider.fetch_financial_statements(
            symbol=symbol,
            statement_types=statement_types,
            periods=periods
        )
        
        # Store in database (implementation would use repository pattern)
        stored = await self._store_statements(statements)
        
        self.logger.info(f"Ingested {len(stored)} financial statements for {symbol} ({market})")
        return stored
    
    async def _store_statements(self, statements: List[FinancialStatement]) -> List[FinancialStatement]:
        """Store statements in database"""
        # Implementation would use database service to store
        # For now, return as-is
        return statements
    
    async def get_financial_statements(
        self,
        asset_id: str,
        statement_type: Optional[FinancialStatementType] = None,
        limit: int = 10
    ) -> List[FinancialStatement]:
        """Retrieve stored financial statements for an asset"""
        # Implementation would query database
        return []
    
    async def get_latest_fundamentals(
        self,
        asset_id: str,
        market: MarketType
    ) -> Dict[str, Any]:
        """
        Get the latest fundamental data formatted for analysis.
        
        Returns standardized financial data ready for FundamentalAnalysisService.
        """
        statements = await self.get_financial_statements(asset_id)
        
        # Combine statements into a single financials dict
        financials = {}
        for stmt in statements:
            financials.update(stmt.data)
        
        return {
            "asset_id": asset_id,
            "market": market.value,
            "financials": financials,
            "statements_count": len(statements),
            "latest_period": statements[0].period if statements else None
        }
    
    async def batch_ingest(
        self,
        symbols: List[str],
        market: MarketType,
        statement_types: Optional[List[FinancialStatementType]] = None
    ) -> Dict[str, List[FinancialStatement]]:
        """Ingest financial statements for multiple symbols"""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = await self.ingest_financial_statements(
                    symbol=symbol,
                    market=market,
                    statement_types=statement_types
                )
            except Exception as e:
                self.logger.error(f"Failed to ingest {symbol}: {e}")
                results[symbol] = []
        return results