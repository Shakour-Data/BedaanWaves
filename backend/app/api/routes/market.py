"""Market Data Routes"""

from collections import defaultdict
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta
from typing import List, Dict
import logging

from app.db.base import get_async_session
from app.models.models import Asset, candle_model_for_market
from app.schemas.schemas import (
    AssetResponse, PriceCandleResponse, PaginationParams,
    MarketDataResponse, TimeframeEnum, AssetClassEnum, MarketEnum
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market", tags=["market"])


@router.get("/symbols", response_model=List[AssetResponse])
async def get_symbols(
    asset_class: AssetClassEnum = Query(None),
    market: MarketEnum = Query(None),
    sector: str = Query(None),
    industry: str = Query(None, description="TSE industry group filter (e.g. فلزات اساسی)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
) -> List[AssetResponse]:
    """
    Get available trading symbols with filters

    Args:
        asset_class: Filter by asset class (EQUITY, CRYPTO, ETF)
        market: Filter by market (TSE, BINANCE, etc.)
        sector: Filter by sector
        industry: Filter by TSE industry group
        skip: Pagination skip
        limit: Pagination limit

    Returns:
        List of assets matching criteria
    """
    query = select(Asset)

    if asset_class:
        query = query.where(Asset.asset_class == asset_class)
    if market:
        query = query.where(Asset.market == market)
    if sector:
        query = query.where(Asset.sector == sector)
    if industry:
        query = query.where(Asset.industry == industry)
    
    query = query.where(Asset.active == True)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    assets = result.scalars().all()
    
    logger.info(f"Retrieved {len(assets)} symbols")
    return assets


@router.get("/price-history", response_model=List[PriceCandleResponse])
async def get_price_history(
    symbol: str = Query(...),
    timeframe: TimeframeEnum = Query("1d"),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_async_session),
) -> List[PriceCandleResponse]:
    """
    Get historical OHLCV data for a symbol
    
    Args:
        symbol: Asset symbol (required)
        timeframe: Candle timeframe (1m, 5m, 1h, 1d, etc.)
        start_date: Start date (default: last 252 days)
        end_date: End date (default: now)
        limit: Maximum number of candles
        
    Returns:
        List of price candles
    """
    # Get asset
    asset_query = select(Asset).where(func.lower(Asset.symbol) == func.lower(symbol))
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    
    # Set default dates
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=252)
    
    # Get price data
    Candle = candle_model_for_market(asset.market)
    candle_query = select(Candle).where(
        and_(
            Candle.asset_id == asset.id,
            Candle.timeframe == timeframe,
            Candle.timestamp >= start_date,
            Candle.timestamp <= end_date,
        )
    ).order_by(Candle.timestamp.asc()).limit(limit)
    
    result = await db.execute(candle_query)
    candles = result.scalars().all()
    
    logger.info(f"Retrieved {len(candles)} price candles for {symbol}")
    return candles


@router.get("/latest-prices", response_model=dict)
async def get_latest_prices(
    symbols: List[str] = Query(...),
    include_change: bool = Query(True),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get latest prices for multiple symbols with single query optimization
    
    Args:
        symbols: List of symbols
        include_change: Include price change percentage
        
    Returns:
        Dictionary with latest prices
    """
    if not symbols:
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {}
        }

    # Create lowercase symbol map for case-insensitive lookup
    symbol_lower_map = {symbol.lower(): symbol for symbol in symbols}
    
    # Get all matching assets in a single query
    lower_symbols = list(symbol_lower_map.keys())
    asset_query = select(Asset).where(func.lower(Asset.symbol).in_(lower_symbols))
    asset_result = await db.execute(asset_query)
    assets_by_symbol = {a.symbol.lower(): a for a in asset_result.scalars()}
    
    if not assets_by_symbol:
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {}
        }
    
    # Get all latest candles in a single query by asset ID
    asset_ids = [asset.id for asset in assets_by_symbol.values()]
    
    # Use first symbol's market to determine candle model (all should be from same market for this endpoint)
    # In a real implementation, we might need to handle multiple markets, but for TSE focus:
    sample_symbol = symbols[0]
    # Extract market from symbol or use default - for now assuming TSE as this is TSE-focused endpoint
    Candle = candle_model_for_market("TSE")  # Default to TSE for this endpoint
    
    # Subquery to get the latest candle for each asset
    latest_candle_subquery = (
        select(
            Candle.asset_id,
            Candle,
            func.row_number()
            .over(
                partition_by=Candle.asset_id,
                order_by=Candle.timestamp.desc()
            )
            .label("rn")
        )
        .where(Candle.timeframe == "1d")
        .subquery()
    )
    
    # Get latest candle for each asset in single query
    latest_candles_query = (
        select(latest_candle_subquery.c.asset_id, latest_candle_subquery.c)
        .where(latest_candle_subquery.c.rn == 1)
        .where(latest_candle_subquery.c.asset_id.in_(asset_ids))
    )
    
    candle_result = await db.execute(latest_candles_query)
    latest_candles = {row.asset_id: row.c for row in candle_result}
    
    # Build response using fetched data
    result = {}
    for symbol_lower, asset in assets_by_symbol.items():
        original_symbol = symbol_lower_map[symbol_lower]
        candle = latest_candles.get(asset.id)
        
        if candle:
            change = float(candle.close) - float(candle.open)
            change_pct = (change / float(candle.open)) * 100 if float(candle.open) > 0 else 0.0
            
            result[original_symbol] = {
                "price": float(candle.close),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": getattr(candle, 'volume', 0),
                "timestamp": candle.timestamp.isoformat()
            }
    
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "data": result
    }


@router.get("/market-overview", response_model=dict)
async def get_market_overview(
    market: MarketEnum = Query("TSE"),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get market overview for a specific market
    
    Args:
        market: Market identifier
        
    Returns:
        Market overview data
    """
    query = select(Asset).where(
        and_(
            Asset.market == market,
            Asset.active == True,
        )
    )
    
    result = await db.execute(query)
    assets = result.scalars().all()
    
    total_assets = len(assets)
    sectors = {}
    
    for asset in assets:
        if asset.sector:
            sectors[asset.sector] = sectors.get(asset.sector, 0) + 1
    
    return {
        "status": "success",
        "market": market,
        "total_assets": total_assets,
        "sectors": sectors,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/tse-dashboard", response_model=dict)
async def tse_dashboard(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    TSE market dashboard summary (Tehran Stock Exchange only).

    Returns total symbols, average daily change, and top 5 gainers / losers
    from the latest stored daily candles using a single window-function query.
    Crypto / international markets are excluded by the market='TSE' filter.

    Returns:
        TSE market overview snapshot
    """
    assets = (
        await db.execute(
            select(Asset).where(Asset.market == "TSE", Asset.active == True)
        )
    ).scalars().all()

    if not assets:
        return {
            "status": "success",
            "market": "TSE",
            "total_symbols": 0,
            "average_change_pct": 0.0,
            "top_gainers": [],
            "top_losers": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

    asset_ids = [a.id for a in assets]
    Candle = candle_model_for_market("TSE")

    ranked = (
        select(
            Candle.asset_id,
            Candle.close,
            func.row_number()
            .over(
                partition_by=Candle.asset_id,
                order_by=Candle.timestamp.desc(),
            )
            .label("rn"),
        )
        .where(
            and_(
                Candle.asset_id.in_(asset_ids),
                Candle.timeframe == "1d",
            )
        )
        .subquery()
    )

    rows = (
        await db.execute(
            select(ranked)
            .where(ranked.c.rn <= 2)
            .order_by(ranked.c.asset_id, ranked.c.rn)
        )
    ).all()

    candles_by_asset: Dict[str, list] = defaultdict(list)
    for row in rows:
        candles_by_asset[str(row.asset_id)].append(row)

    result_rows = []
    for asset in assets:
        asset_candles = candles_by_asset.get(str(asset.id), [])
        asset_candles.sort(key=lambda r: r.rn)

        last_close = float(asset_candles[0].close) if len(asset_candles) >= 1 else None
        change_pct = None
        if len(asset_candles) >= 2:
            older, newer = asset_candles[1], asset_candles[0]
            base = float(older.close)
            change_pct = (float(newer.close) - base) / base * 100 if base else 0.0
        elif len(asset_candles) == 1:
            change_pct = 0.0

        result_rows.append(
            {
                "symbol": asset.symbol,
                "name": asset.name,
                "last_close": last_close,
                "change_pct": round(change_pct, 2) if change_pct is not None else None,
            }
        )

    ranked_change = [r for r in result_rows if r["change_pct"] is not None]
    ranked_change.sort(key=lambda x: x["change_pct"], reverse=True)
    avg_change = sum(r["change_pct"] for r in ranked_change) / len(ranked_change) if ranked_change else 0.0

    return {
        "status": "success",
        "market": "TSE",
        "total_symbols": len(result_rows),
        "average_change_pct": round(avg_change, 2),
        "top_gainers": ranked_change[:5],
        "top_losers": sorted(ranked_change, key=lambda x: x["change_pct"])[:5],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/industry-ranking", response_model=dict)
async def industry_ranking(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    TSE industry ranking (رتبه‌بندی صنایع).

    Ranks Tehran Stock Exchange industries by the average daily change of their
    constituent symbols using a single window-function query over daily candles.
    Only market='TSE' symbols are considered; crypto / international are excluded.

    Returns:
        Industries ranked by average change %, each with member count
    """
    assets = (
        await db.execute(
            select(Asset).where(
                Asset.market == "TSE", Asset.active == True, Asset.industry.isnot(None)
            )
        )
    ).scalars().all()

    if not assets:
        return {
            "status": "success",
            "market": "TSE",
            "ranked_industries": 0,
            "ranking": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

    asset_ids = [a.id for a in assets]
    Candle = candle_model_for_market("TSE")

    ranked = (
        select(
            Candle.asset_id,
            Candle.close,
            func.row_number()
            .over(
                partition_by=Candle.asset_id,
                order_by=Candle.timestamp.desc(),
            )
            .label("rn"),
        )
        .where(
            and_(
                Candle.asset_id.in_(asset_ids),
                Candle.timeframe == "1d",
            )
        )
        .subquery()
    )

    rows = (
        await db.execute(
            select(ranked)
            .where(ranked.c.rn <= 2)
            .order_by(ranked.c.asset_id, ranked.c.rn)
        )
    ).all()

    candles_by_asset: Dict[str, list] = defaultdict(list)
    for row in rows:
        candles_by_asset[str(row.asset_id)].append(row)

    industry_changes: Dict[str, List[float]] = {}
    for asset in assets:
        asset_candles = candles_by_asset.get(str(asset.id), [])
        asset_candles.sort(key=lambda r: r.rn)
        if len(asset_candles) >= 2:
            older, newer = asset_candles[1], asset_candles[0]
            base = float(older.close)
            change = (float(newer.close) - base) / base * 100 if base else 0.0
            industry_changes.setdefault(asset.industry, []).append(change)

    ranking = []
    for industry, changes in industry_changes.items():
        avg = sum(changes) / len(changes) if changes else 0.0
        ranking.append(
            {
                "industry": industry,
                "member_count": len(changes),
                "average_change_pct": round(avg, 2),
            }
        )

    ranking.sort(key=lambda x: x["average_change_pct"], reverse=True)

    return {
        "status": "success",
        "market": "TSE",
        "ranked_industries": len(ranking),
        "ranking": ranking,
        "timestamp": datetime.utcnow().isoformat(),
    }
