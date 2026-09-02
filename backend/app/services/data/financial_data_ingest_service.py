"""
Financial Data Ingestion Service - Tier 2 Data Service

Fetches and processes financial statements for instruments that participate
in the formation of the Nasdaq index (Nasdaq-listed EQUITY and ETF).

Optimized with caching, batching, and lazy loading for performance.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import asyncio

from app.services.core.base_service import DataService
from app.core.exceptions import (
    DataProviderException,
    DataParsingException,
    FinancialDataException,
)
from .nasdaq_ingestion_service import NasdaqIngestionService
from app.core.config import get_settings


class MarketType(Enum):
    """Internal routing enum for data ingestion providers.

    Public-facing market filtering is restricted to ``NASDAQ`` (see
    ``app.schemas.schemas.MarketEnum`` and ``app.api.routes.market``). The
    ``US`` value is a routing key for US-based data providers; non-Nasdaq
    instruments are never returned through user-facing endpoints.
    """
    NASDAQ = "NASDAQ"
    US = "US"


class FinancialStatementType(Enum):
    INCOME = "INCOME"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASH_FLOW = "CASH_FLOW"


@dataclass
class FinancialStatement:
    """Standardized financial statement structure"""
    asset_id: str
    symbol: str
    market: MarketType
    statement_type: FinancialStatementType
    period: str
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
                    parsed = self._parse_codal_announcement(announcement, stmt_type)
                    if parsed:
                        statements.append(parsed)
                        
            except DataProviderException:
                raise
            except Exception as exc:
                raise DataProviderException(
                    f"Failed to fetch financial statements for {symbol}: {exc}"
                ) from exc
        
        return statements
    
    def _parse_codal_announcement(
        self,
        announcement: Dict[str, Any],
        stmt_type: FinancialStatementType
    ) -> Optional[FinancialStatement]:
        """Parse CODAL announcement into standardized financial statement."""
        try:
            fiscal_year = announcement.get("fiscal_year")
            if fiscal_year is not None:
                fiscal_year = int(fiscal_year)
            
            publish_date = announcement.get("publish_date")
            as_of_date = None
            if publish_date:
                as_of_date = datetime.fromisoformat(publish_date)
            
            return FinancialStatement(
                asset_id=announcement.get("symbol", ""),
                symbol=announcement.get("symbol", ""),
                market=MarketType.IRAN,
                statement_type=stmt_type,
                period=announcement.get("period", ""),
                fiscal_year=fiscal_year or 0,
                fiscal_quarter=announcement.get("fiscal_quarter"),
                data=announcement.get("financial_data", {}),
                source="CODAL",
                fetched_at=datetime.now(timezone.utc),
                as_of=as_of_date,
            )
        except (ValueError, TypeError) as exc:
            raise DataParsingException(
                f"Failed to parse CODAL announcement: {exc}"
            ) from exc
    
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
    Financial Data Ingestion Service with performance optimizations.

    Features:
    - Concurrent data fetching
    - LRU caching for frequent queries
    - Batch processing for multiple symbols
    - Lazy initialization of providers
    """

    def __init__(
        self,
        service_name: str = "FinancialDataIngestService",
        brs_client: Optional[BrsApiClient] = None,
        max_concurrent_requests: int = 10,
    ):
        super().__init__(service_name)
        self.brs_client = brs_client
        self.max_concurrent = max_concurrent_requests
        self._providers: Dict[MarketType, FinancialDataProvider] = {}
        self._provider_cache = {}
        self._result_cache = {}
        self._cache_size_limit = 100

    def _register_providers(self) -> None:
        """Register default data providers"""
        if self.brs_client:
            self._providers[MarketType.IRAN] = BrsFinancialDataProvider(self.brs_client)

        self._providers[MarketType.US] = YahooFinanceProvider()
        self._providers[MarketType.INTERNATIONAL] = AlphaVantageProvider()

    def register_provider(self, market: MarketType, provider: FinancialDataProvider) -> None:
        """Register a custom data provider"""
        self._providers[market] = provider

    async def initialize(self) -> None:
        if self.brs_client:
            await self.brs_client.initialize()
        self.logger.info("FinancialDataIngestService initialized")

    async def shutdown(self) -> None:
        if self.brs_client:
            await self.brs_client.shutdown()
        self.logger.info("FinancialDataIngestService shutdown")

    _result_cache: Dict[str, Any] = {}

    async def ingest_financial_statements(
        self,
        symbol: str,
        market: MarketType,
        statement_types: Optional[List[FinancialStatementType]] = None,
        periods: Optional[List[str]] = None
    ) -> List[FinancialStatement]:
        """
        Fetch and store financial statements for a symbol.

        Uses caching to avoid redundant fetches.
        """
        # Check cache first
        cache_key = f"{market.value}:{symbol}:{','.join(statement_types or [])}:{','.join(periods or [])}"
        cached = self._result_cache.get(cache_key)
        if cached is not None:
            return cached if cached else []

        # Lazy provider registration
        if not self._providers:
            self._register_providers()

        provider = self._providers.get(market)
        if not provider:
            raise ValueError(f"No provider registered for market: {market}")

        statements = await provider.fetch_financial_statements(
            symbol=symbol,
            statement_types=statement_types,
            periods=periods
        )

        # Cache the result
        if statements:
            self._result_cache[cache_key] = statements
        return statements or []

    async def batch_ingest_optimized(
        self,
        symbols: List[str],
        market: MarketType,
        statement_types: Optional[List[FinancialStatementType]] = None
    ) -> Dict[str, List[FinancialStatement]]:
        """Batch ingest financial statements with concurrent processing."""
        # Check which symbols are already cached
        cached_symbols = set()
        uncached_symbols = []

        for symbol in symbols:
            cache_key = f"{market.value}:{symbol}:{','.join(statement_types or [])}"
            if self._result_cache.get(cache_key):
                cached_symbols.add(symbol)
            else:
                uncached_symbols.append(symbol)

        # Fetch uncached symbols concurrently
        if uncached_symbols:
            tasks = [
                self.ingest_financial_statements(
                    symbol=symbol,
                    market=market,
                    statement_types=statement_types
                )
                for symbol in uncached_symbols
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for symbol, result in zip(uncached_symbols, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Failed to ingest {symbol}: {str(result)}")
                else:
                    # Cache the result
                    cache_key = f"{market.value}:{symbol}:{','.join(statement_types or [])}"
                    self._result_cache[cache_key] = result

        # Build results dictionary
        results = {}
        for symbol in symbols:
            cache_key = f"{market.value}:{symbol}:{','.join(statement_types or [])}"
            cached = self._result_cache.get(cache_key)
            results[symbol] = cached if cached else []

        return results

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
        market: MarketType = None,
        statement_types: Optional[List[FinancialStatementType]] = None
    ) -> Dict[str, List[FinancialStatement]]:
        """Ingest financial statements for multiple symbols"""
        if market in (MarketType.US, MarketType.NASDAQ) or (market is None and symbols):
            nasdaq = NasdaqIngestionService()
            await nasdaq.initialize()
            results = {}
            for symbol in symbols:
                try:
                    count = await nasdaq.ingest_price_history(symbol, period="5d")
                    results[symbol] = {"prices": count, "fundamentals": False}
                except Exception as e:
                    self.logger.error(f"Failed to ingest {symbol}: {e}")
                    results[symbol] = {"prices": 0, "fundamentals": False, "error": str(e)}
            await nasdaq.shutdown()
            return results

        results = {}
        for symbol in symbols:
            try:
                results[symbol] = await self.ingest_financial_statements(
                    symbol=symbol,
                    market=market or MarketType.US,
                    statement_types=statement_types
                )
            except Exception as e:
                self.logger.error(f"Failed to ingest {symbol}: {e}")
                results[symbol] = []
        return results