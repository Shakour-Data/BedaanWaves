"""Symbol Service - Tier 2 Data Service
Manages symbol data and operations with multi-market support and cache integration."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy import select, func, or_

from app.core.config import get_settings
from app.db.base import async_session_maker
from app.models.models import SymbolData
from app.services.core.base_service import DataService
from app.services.core.dependency_container import get_global_container

settings = get_settings()
container = get_global_container()


class SymbolService(DataService):
    """Comprehensive symbol data management with multi-market support and cache integration."""

    def __init__(self):
        super().__init__(service_name="SymbolService")
        self._symbol_cache: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize service with database and cache connections."""
        await super().initialize()
        await self._load_initial_symbols()

    async def _load_initial_symbols(self) -> int:
        """Load initial symbols from database."""
        async with async_session_maker() as session:
            stmt = select(SymbolData).order_by(SymbolData.symbol)
            result = await session.execute(stmt)
            symbols = result.scalars().all()

        for symbol in symbols:
            cache_key = f"symbol:{symbol.symbol}"
            self._symbol_cache[cache_key] = {
                "symbol_id": symbol.symbol_id,
                "security_name": symbol.security_name,
                "exchange": symbol.exchange,
                "market_type": symbol.market_type,
                "active": symbol.active_status,
                "last_updated": symbol.updated_at
            }

        return len(symbols)

    async def get_symbol(self, symbol: str) -> Dict[str, Any]:
        """Cached symbol data retrieval with fallback to database."""
        cache_key = f"symbol:{symbol.upper()}"
        
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        async with async_session_maker() as session:
            stmt = select(SymbolData).where(SymbolData.symbol == symbol.upper())
            result = await session.execute(stmt)
            symbol_data = result.scalar_one_or_none()
            
        if symbol_data:
            data = {
                "symbol_id": symbol_data.symbol_id,
                "security_name": symbol_data.security_name,
                "exchange": symbol_data.exchange,
                "country_code": symbol_data.country_code,
                "market_type": symbol_data.market_type,
                "active": symbol_data.active_status,
                "last_updated": symbol_data.updated_at
            }
            self._symbol_cache[cache_key] = data
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
        """Flexible symbol search with caching and optional filters."""
        cache_key = f"search:{query}:{limit}:{exchange}:{market_type}:{active_only}"
        
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        async with async_session_maker() as session:
            stmt = select(SymbolData)
            search_pattern = f"%{query.upper()}%"
            stmt = stmt.where(
                or_(
                    func.upper(SymbolData.symbol).like(search_pattern),
                    func.upper(SymbolData.security_name).like(search_pattern),
                )
            )
            if exchange:
                stmt = stmt.where(SymbolData.exchange == exchange)
            if market_type:
                stmt = stmt.where(SymbolData.market_type == market_type)
            if active_only:
                stmt = stmt.where(SymbolData.active_status == True)
            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            symbols = result.scalars().all()
            
        data_list = [{
            "symbol": s.symbol,
            "name": s.security_name,
            "exchange": s.exchange,
            "market_type": s.market_type,
            "active": s.active_status
        } for s in symbols]
        
        self._symbol_cache[cache_key] = data_list
        return data_list

    async def get_exchanges(self) -> List[str]:
        """Get list of all available exchanges."""
        cache_key = "meta:exchanges"
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        async with async_session_maker() as session:
            stmt = select(SymbolData.exchange).distinct().order_by(SymbolData.exchange)
            result = await session.execute(stmt)
            exchanges = [r for r in result.scalars().all() if r]
        
        self._symbol_cache[cache_key] = exchanges
        return exchanges

    async def get_market_types(self) -> List[str]:
        """Get list of all available market types."""
        cache_key = "meta:market_types"
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        async with async_session_maker() as session:
            stmt = select(SymbolData.market_type).distinct().order_by(SymbolData.market_type)
            result = await session.execute(stmt)
            market_types = [r for r in result.scalars().all() if r]
        
        self._symbol_cache[cache_key] = market_types
        return market_types

    async def get_countries(self) -> List[str]:
        """Get list of all available country codes."""
        cache_key = "meta:countries"
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        async with async_session_maker() as session:
            stmt = select(SymbolData.country_code).distinct().order_by(SymbolData.country_code)
            result = await session.execute(stmt)
            countries = [r for r in result.scalars().all() if r]
        
        self._symbol_cache[cache_key] = countries
        return countries

    async def get_by_exchange(
        self,
        exchange: str,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get symbols by exchange with pagination."""
        cache_key = f"exchange_symbols:{exchange}:{limit}:{offset}:{active_only}"
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        async with async_session_maker() as session:
            stmt = select(SymbolData).where(SymbolData.exchange == exchange)
            if active_only:
                stmt = stmt.where(SymbolData.active_status == True)
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            symbols = result.scalars().all()
        
        data_list = [{
            "symbol": s.symbol,
            "name": s.security_name,
            "exchange": s.exchange,
            "market_type": s.market_type,
            "active": s.active_status
        } for s in symbols]
        
        self._symbol_cache[cache_key] = data_list
        return data_list

    async def get_by_market_type(
        self,
        market_type: str,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get symbols by market type with pagination."""
        cache_key = f"market_type_symbols:{market_type}:{limit}:{offset}:{active_only}"
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        async with async_session_maker() as session:
            stmt = select(SymbolData).where(SymbolData.market_type == market_type)
            if active_only:
                stmt = stmt.where(SymbolData.active_status == True)
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            symbols = result.scalars().all()
        
        data_list = [{
            "symbol": s.symbol,
            "name": s.security_name,
            "exchange": s.exchange,
            "market_type": s.market_type,
            "active": s.active_status
        } for s in symbols]
        
        self._symbol_cache[cache_key] = data_list
        return data_list

    async def get_stats(self) -> Dict[str, Any]:
        """Get symbol statistics."""
        async with async_session_maker() as session:
            total = await session.execute(select(func.count()).select_from(SymbolData))
            active = await session.execute(
                select(func.count()).where(SymbolData.active_status == True).select_from(SymbolData)
            )
            exchanges = await session.execute(
                select(func.count(SymbolData.exchange.distinct()))
            )
        
        return {
            "total_symbols": total.scalar(),
            "active_symbols": active.scalar(),
            "total_exchanges": exchanges.scalar() or 0,
        }

    async def get_exchange_symbols(self, exchange: str) -> List[Dict[str, Any]]:
        """Get all symbols for a specific exchange."""
        cache_key = f"exchange:{exchange}"
        
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]
        
        async with async_session_maker() as session:
            stmt = select(SymbolData).where(SymbolData.exchange == exchange)
            result = await session.execute(stmt)
            symbols = result.scalars().all()
            
        data_list = [{
            "symbol": s.symbol,
            "name": s.security_name,
            "market_type": s.market_type,
            "active": s.active_status
        } for s in symbols]
        
        self._symbol_cache[cache_key] = data_list
        return data_list

    async def clear_cache(self) -> None:
        """Clear symbol cache."""
        self._symbol_cache.clear()

    async def shutdown(self) -> None:
        """Clean up resources."""
        self._symbol_cache.clear()
        await super().shutdown()


# Register SymbolService in dependency container
container.register(DataService, SymbolService)