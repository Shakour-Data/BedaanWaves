"""Market Data Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import List
import logging

from app.db.base import get_async_session
from app.models.models import Asset, PriceCandle
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
    asset_query = select(Asset).where(Asset.symbol == symbol.upper())
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
    candle_query = select(PriceCandle).where(
        and_(
            PriceCandle.asset_id == asset.id,
            PriceCandle.timeframe == timeframe,
            PriceCandle.timestamp >= start_date,
            PriceCandle.timestamp <= end_date,
        )
    ).order_by(PriceCandle.timestamp.asc()).limit(limit)
    
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
    Get latest prices for multiple symbols
    
    Args:
        symbols: List of symbols
        include_change: Include price change percentage
        
    Returns:
        Dictionary with latest prices
    """
    latest_prices = {}
    
    for symbol in symbols:
        asset_query = select(Asset).where(Asset.symbol == symbol.upper())
        asset_result = await db.execute(asset_query)
        asset = asset_result.scalars().first()
        
        if not asset:
            continue
        
        # Get latest candle
        candle_query = (
            select(PriceCandle)
            .where(
                and_(
                    PriceCandle.asset_id == asset.id,
                    PriceCandle.timeframe == "1d",
                )
            )
            .order_by(PriceCandle.timestamp.desc())
            .limit(1)
        )
        
        result = await db.execute(candle_query)
        latest_candle = result.scalars().first()
        
        if latest_candle:
            change = float(latest_candle.close) - float(latest_candle.open)
            change_pct = (change / float(latest_candle.open)) * 100 if latest_candle.open > 0 else 0
            
            latest_prices[symbol] = {
                "price": float(latest_candle.close),
                "change": change,
                "change_pct": round(change_pct, 2),
                "volume": latest_candle.volume,
                "timestamp": latest_candle.timestamp.isoformat(),
            }
    
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "data": latest_prices,
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
    computed from the latest stored daily candles. Crypto / international
    markets are excluded by the market='TSE' filter.

    Returns:
        TSE market overview snapshot
    """
    assets = (
        await db.execute(
            select(Asset).where(Asset.market == "TSE", Asset.active == True)
        )
    ).scalars().all()

    rows = []
    for asset in assets:
        candles = (
            await db.execute(
                select(PriceCandle)
                .where(PriceCandle.asset_id == asset.id, PriceCandle.timeframe == "1d")
                .order_by(PriceCandle.timestamp.desc())
                .limit(2)
            )
        ).scalars().all()

        change_pct = None
        last_close = float(candles[0].close) if candles else None
        if len(candles) >= 2:
            older, newer = candles[1], candles[0]
            base = float(older.close)
            change_pct = (float(newer.close) - base) / base * 100 if base else 0.0
        elif len(candles) == 1:
            change_pct = 0.0

        rows.append(
            {
                "symbol": asset.symbol,
                "name": asset.name,
                "last_close": last_close,
                "change_pct": round(change_pct, 2) if change_pct is not None else None,
            }
        )

    ranked = [r for r in rows if r["change_pct"] is not None]
    ranked.sort(key=lambda x: x["change_pct"], reverse=True)
    avg_change = sum(r["change_pct"] for r in ranked) / len(ranked) if ranked else 0.0

    return {
        "status": "success",
        "market": "TSE",
        "total_symbols": len(rows),
        "average_change_pct": round(avg_change, 2),
        "top_gainers": ranked[:5],
        "top_losers": ranked[::-1][:5],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/industry-ranking", response_model=dict)
async def industry_ranking(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    TSE industry ranking (رتبه‌بندی صنایع).

    Ranks Tehran Stock Exchange industries by the average daily change of their
    constituent symbols (computed from the latest stored daily candles). Only
    market='TSE' symbols are considered; crypto / international are excluded.

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

    industry_changes: Dict[str, List[float]] = {}
    for asset in assets:
        candles = (
            await db.execute(
                select(PriceCandle)
                .where(PriceCandle.asset_id == asset.id, PriceCandle.timeframe == "1d")
                .order_by(PriceCandle.timestamp.desc())
                .limit(2)
            )
        ).scalars().all()

        if len(candles) >= 2:
            older, newer = candles[1], candles[0]
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
