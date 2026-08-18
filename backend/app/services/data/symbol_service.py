"""Symbol Service - Tier 2 Data Service
Manages symbol data and operations with multi-market support and cache integration."""

import shelve
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy import select, func, or_

from app.core.config import Settings
from app.db.base import async_session_maker
from app.models.symbol import SymbolData
from app.core.services import DataService
from app.services.core.dependency_container import get_global_container

container = get_global_container()


class SymbolService(DataService):
    """Comprehensive symbol data management with multi-market support and cache integration."""

    def __init__(self):
        super().__init__(
            service_name="SymbolService",
            cache_backend=settings.CACHE_BACKEND,
            cache_timeout=settings.SYMBOL_CACHE_TTL
        )

    async def initialize(self) -> None:
        """Initialize service with database and cache connections."""
        await super().initialize()
        self._initialize_cache()
        await self._load_initial_symbols()

    async def _initialize_cache(self) -> None:
        """Set up cache configuration."""
        self._symbol_cache = shelve.open(f"symbol_cache_{settings.ENVIRONMENT}")
        if not self._symbol_cache.awake():
            self._symbol_cache.sync()

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

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Flexible symbol search with caching."""
        cache_key = f"search:{query}:{limit}"
        
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
        self._symbol_cache.sync()

    async def shutdown(self) -> None:
        """Clean up resources."""
        self._symbol_cache.close()
        await super().shutdown()


# Register SymbolService in dependency container
container.register(DataService, SymbolService)