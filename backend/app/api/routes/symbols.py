"""Symbol Data Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime
import logging

from app.services.data.symbol_service import SymbolService
from app.services.data.stock_service import StockService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["symbols"])


@router.get("/search", response_model=dict)
async def search_symbols(
    q: str = Query(..., min_length=1, description="Search query (symbol or company name)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    market_type: Optional[str] = Query(None, description="Filter by market type"),
    active_only: bool = Query(True, description="Only active symbols"),
    service: SymbolService = Depends(SymbolService),
) -> dict:
    """Search symbols by query string."""
    results = await service.search(
        query=q,
        limit=limit,
        exchange=exchange,
        market_type=market_type,
        active_only=active_only,
    )
    
    return {
        "status": "success",
        "query": q,
        "count": len(results),
        "data": results,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/exchanges", response_model=dict)
async def get_exchanges(
    service: SymbolService = Depends(SymbolService),
) -> dict:
    """Get list of all available exchanges."""
    exchanges = await service.get_exchanges()
    
    return {
        "status": "success",
        "exchanges": exchanges,
        "count": len(exchanges),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/market-types", response_model=dict)
async def get_market_types(
    service: SymbolService = Depends(SymbolService),
) -> dict:
    """Get list of all available market types."""
    market_types = await service.get_market_types()
    
    return {
        "status": "success",
        "market_types": market_types,
        "count": len(market_types),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/countries", response_model=dict)
async def get_countries(
    service: SymbolService = Depends(SymbolService),
) -> dict:
    """Get list of all available country codes."""
    countries = await service.get_countries()
    
    return {
        "status": "success",
        "countries": countries,
        "count": len(countries),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/stats", response_model=dict)
async def get_symbol_stats(
    service: SymbolService = Depends(SymbolService),
) -> dict:
    """Get symbol statistics."""
    stats = await service.get_stats()
    
    return {
        "status": "success",
        "stats": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/exchanges/{exchange}/count", response_model=dict)
async def get_symbols_by_exchange(
    exchange: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(True),
    service: SymbolService = Depends(SymbolService),
) -> dict:
    """Get symbols by exchange with pagination."""
    symbols = await service.get_by_exchange(
        exchange=exchange,
        limit=limit,
        offset=offset,
        active_only=active_only,
    )
    
    return {
        "status": "success",
        "exchange": exchange,
        "count": len(symbols),
        "limit": limit,
        "offset": offset,
        "data": symbols,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/market-types/{market_type}/count", response_model=dict)
async def get_symbols_by_market_type(
    market_type: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(True),
    service: SymbolService = Depends(SymbolService),
) -> dict:
    """Get symbols by market type with pagination."""
    symbols = await service.get_by_market_type(
        market_type=market_type,
        limit=limit,
        offset=offset,
        active_only=active_only,
    )
    
    return {
        "status": "success",
        "market_type": market_type,
        "count": len(symbols),
        "limit": limit,
        "offset": offset,
        "data": symbols,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/{symbol}", response_model=dict)
async def get_symbol(
    symbol: str,
    service: SymbolService = Depends(SymbolService),
) -> dict:
    """Get symbol data by ticker."""
    data = await service.get_symbol(symbol)
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Symbol '{symbol}' not found"
        )
    
    return {
        "status": "success",
        "symbol": symbol,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
