"""
Symbol Service - Tier 2 Data Service

Provides comprehensive symbol data management with multi-market support.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.core.base_service import DataService
from app.db.base import async_session_maker
from app.models.models import SymbolData

logger = logging.getLogger(__name__)


class SymbolService(DataService):
    """
    Symbol Data Service with multi-market support.

    Features:
    - Symbol search and retrieval
    - Market-based filtering
    - Batch operations
    - Cache integration
    """

    def __init__(
        self,
        service_name: str = "SymbolService",
    ):
        super().__init__(service_name)
        self._cache = {}
        self._cache_size_limit = 500

    async def initialize(self) -> None:
        """Initialize the symbol service."""
        self.logger.info("SymbolService initialized")

    async def shutdown(self) -> None:
        """Shutdown the symbol service."""
        self._cache.clear()
        self.logger.info("SymbolService shutdown")

    async def get_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol data by ticker.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            Symbol data dictionary or None if not found
        """
        cache_key = f"symbol:{symbol}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        async with async_session_maker() as session:
            stmt = select(SymbolData).where(SymbolData.symbol == symbol.upper())
            result = await session.execute(stmt)
            symbol_data = result.scalar_one_or_none()

            if symbol_data:
                data = {
                    "symbol_id": symbol_data.symbol_id,
                    "symbol": symbol_data.symbol,
                    "security_name": symbol_data.security_name,
                    "exchange": symbol_data.exchange,
                    "country_code": symbol_data.country_code,
                    "index_code": symbol_data.index_code,
                    "industry_code": symbol_data.industry_code,
                    "market_type": symbol_data.market_type,
                    "active_status": symbol_data.active_status,
                    "status_reason": symbol_data.status_reason,
                    "listing_date": symbol_data.listing_date.isoformat() if symbol_data.listing_date else None,
                    "delisting_date": symbol_data.delisting_date.isoformat() if symbol_data.delisting_date else None,
                    "round_lot_size": symbol_data.round_lot_size,
                    "market_category": symbol_data.market_category,
                    "financial_status": symbol_data.financial_status,
                    "etf_flag": symbol_data.etf_flag,
                    "next_shares": symbol_data.next_shares,
                    "is_test_issue": symbol_data.is_test_issue,
                    "security_type": symbol_data.security_type,
                    "created_at": symbol_data.created_at.isoformat() if symbol_data.created_at else None,
                    "updated_at": symbol_data.updated_at.isoformat() if symbol_data.updated_at else None,
                }

                # Cache result
                if len(self._cache) >= self._cache_size_limit:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                self._cache[cache_key] = data

                return data

        return None

    async def search(
        self,
        query: str,
        limit: int = 20,
        exchange: Optional[str] = None,
        market_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search symbols by query string.

        Args:
            query: Search query (symbol or company name)
            limit: Maximum number of results
            exchange: Filter by exchange
            market_type: Filter by market type
            active_only: Only return active symbols

        Returns:
            List of matching symbol data
        """
        cache_key = f"search:{query}:{limit}:{exchange}:{market_type}:{active_only}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        async with async_session_maker() as session:
            stmt = select(SymbolData)

            # Search by symbol or security name
            search_pattern = f"%{query.upper()}%"
            stmt = stmt.where(
                or_(
                    func.upper(SymbolData.symbol).like(search_pattern),
                    func.upper(SymbolData.security_name).like(search_pattern),
                )
            )

            # Apply filters
            if exchange:
                stmt = stmt.where(SymbolData.exchange == exchange)
            if market_type:
                stmt = stmt.where(SymbolData.market_type == market_type)
            if active_only:
                stmt = stmt.where(SymbolData.active_status == True)

            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            symbols = result.scalars().all()

            data_list = []
            for symbol_data in symbols:
                data_list.append({
                    "symbol_id": symbol_data.symbol_id,
                    "symbol": symbol_data.symbol,
                    "security_name": symbol_data.security_name,
                    "exchange": symbol_data.exchange,
                    "country_code": symbol_data.country_code,
                    "market_type": symbol_data.market_type,
                    "active_status": symbol_data.active_status,
                })

            # Cache results
            if len(self._cache) >= self._cache_size_limit:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            self._cache[cache_key] = data_list

            return data_list

    async def get_by_exchange(
        self,
        exchange: str,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get symbols by exchange.

        Args:
            exchange: Exchange name (e.g., 'NASDAQ')
            limit: Maximum number of results
            offset: Pagination offset
            active_only: Only return active symbols

        Returns:
            List of symbol data
        """
        async with async_session_maker() as session:
            stmt = select(SymbolData).where(SymbolData.exchange == exchange)

            if active_only:
                stmt = stmt.where(SymbolData.active_status == True)

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            symbols = result.scalars().all()

            return [
                {
                    "symbol_id": s.symbol_id,
                    "symbol": s.symbol,
                    "security_name": s.security_name,
                    "exchange": s.exchange,
                    "country_code": s.country_code,
                    "market_type": s.market_type,
                    "active_status": s.active_status,
                }
                for s in symbols
            ]

    async def get_by_market_type(
        self,
        market_type: str,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get symbols by market type.

        Args:
            market_type: Market type (e.g., 'NASDAQ', 'NYSE')
            limit: Maximum number of results
            offset: Pagination offset
            active_only: Only return active symbols

        Returns:
            List of symbol data
        """
        async with async_session_maker() as session:
            stmt = select(SymbolData).where(SymbolData.market_type == market_type)

            if active_only:
                stmt = stmt.where(SymbolData.active_status == True)

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            symbols = result.scalars().all()

            return [
                {
                    "symbol_id": s.symbol_id,
                    "symbol": s.symbol,
                    "security_name": s.security_name,
                    "exchange": s.exchange,
                    "country_code": s.country_code,
                    "market_type": s.market_type,
                    "active_status": s.active_status,
                }
                for s in symbols
            ]

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get symbol statistics.

        Returns:
            Statistics dictionary
        """
        async with async_session_maker() as session:
            # Total count
            total_stmt = select(func.count()).select_from(SymbolData)
            total_result = await session.execute(total_stmt)
            total = total_result.scalar()

            # By exchange
            exchange_stmt = (
                select(SymbolData.exchange, func.count())
                .group_by(SymbolData.exchange)
                .order_by(func.count().desc())
            )
            exchange_result = await session.execute(exchange_stmt)
            by_exchange = {row[0]: row[1] for row in exchange_result}

            # By market type
            market_stmt = (
                select(SymbolData.market_type, func.count())
                .group_by(SymbolData.market_type)
                .order_by(func.count().desc())
            )
            market_result = await session.execute(market_stmt)
            by_market_type = {row[0]: row[1] for row in market_result}

            # By country
            country_stmt = (
                select(SymbolData.country_code, func.count())
                .group_by(SymbolData.country_code)
                .order_by(func.count().desc())
            )
            country_result = await session.execute(country_stmt)
            by_country = {row[0]: row[1] for row in country_result}

            # Active count
            active_stmt = (
                select(func.count())
                .select_from(SymbolData)
                .where(SymbolData.active_status == True)
            )
            active_result = await session.execute(active_stmt)
            active_count = active_result.scalar()

            return {
                "total_symbols": total,
                "active_symbols": active_count,
                "inactive_symbols": total - active_count,
                "by_exchange": by_exchange,
                "by_market_type": by_market_type,
                "by_country": by_country,
                "last_updated": datetime.utcnow().isoformat(),
            }

    async def get_exchanges(self) -> List[str]:
        """Get list of all available exchanges."""
        async with async_session_maker() as session:
            stmt = select(SymbolData.exchange).distinct().order_by(SymbolData.exchange)
            result = await session.execute(stmt)
            return [row[0] for row in result]

    async def get_market_types(self) -> List[str]:
        """Get list of all available market types."""
        async with async_session_maker() as session:
            stmt = select(SymbolData.market_type).distinct().order_by(SymbolData.market_type)
            result = await session.execute(stmt)
            return [row[0] for row in result]

    async def get_countries(self) -> List[str]:
        """Get list of all available country codes."""
        async with async_session_maker() as session:
            stmt = select(SymbolData.country_code).distinct().order_by(SymbolData.country_code)
            result = await session.execute(stmt)
            return [row[0] for row in result]