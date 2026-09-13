"""Market Data Routes"""

from collections import defaultdict
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import timezone, datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import math
import time
import asyncio
from app.core.utils import utc_now_iso

from app.db.base import get_async_session
from app.models.models import Asset, candle_model_for_market
from app.schemas.schemas import (
    AssetResponse, PriceCandleResponse, PaginationParams,
    MarketDataResponse, TimeframeEnum, AssetClassEnum, MarketEnum
)
from app.services.core.dependency_container import get_global_container
from app.services.data.real_time_market_data_service import RealTimeMarketDataService
from app.services.data.market_hours_service import MarketHoursService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["market"])


@router.get("/symbols", response_model=List[AssetResponse])
async def get_symbols(
    asset_class: AssetClassEnum = Query(None),
    market: MarketEnum = Query(None),
    sector: str = Query(None),
    industry: str = Query(None, description="NASDAQ industry group filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
) -> List[AssetResponse]:
    """
    Get available trading symbols with filters.

    Only instruments that participate in the formation of the Nasdaq index
    are returned (asset_class in {EQUITY, ETF} and market == "NASDAQ").
    The ``asset_class`` and ``market`` parameters, if supplied, are
    validated against this restricted set.

    Args:
        asset_class: Filter by asset class (EQUITY, ETF)
        market: Filter by market (NASDAQ only)
        sector: Filter by sector
        industry: Filter by industry group
        skip: Pagination skip
        limit: Pagination limit

    Returns:
        List of assets matching criteria
    """
    # Hard-cap the universe: only Nasdaq-listed equities and ETFs are
    # ever returned from this endpoint, regardless of caller filters.
    query = select(Asset).where(
        and_(
            Asset.active == True,
            Asset.market == "NASDAQ",
            Asset.asset_class.in_(["EQUITY", "ETF"]),
        )
    )

    if asset_class:
        query = query.where(Asset.asset_class == asset_class)
    if market:
        query = query.where(Asset.market == market)
    if sector:
        query = query.where(Asset.sector == sector)
    if industry:
        query = query.where(Asset.industry == industry)

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
        end_date = datetime.now(timezone.utc).replace(tzinfo=None)
    if not start_date:
        start_date = end_date - timedelta(days=252)
    
    if getattr(end_date, 'tzinfo', None) is not None:
        end_date = end_date.replace(tzinfo=None)
    if getattr(start_date, 'tzinfo', None) is not None:
        start_date = start_date.replace(tzinfo=None)
    
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
            "timestamp": utc_now_iso(),
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
            "timestamp": utc_now_iso(),
            "data": {}
        }
    
    # Get all latest candles in a single query by asset ID
    asset_ids = [asset.id for asset in assets_by_symbol.values()]
    
    # Use first symbol's market to determine candle model (all should be from same market for this endpoint)
    # In a real implementation, we might need to handle multiple markets, but for NASDAQ focus:
    sample_symbol = symbols[0]
    # Extract market from symbol or use default - for now assuming NASDAQ as this is NASDAQ-focused endpoint
    Candle = candle_model_for_market("NASDAQ")  # Default to NASDAQ for this endpoint
    
    latest_candles_query = (
        select(Candle)
        .where(Candle.timeframe == "1d")
        .where(Candle.asset_id.in_(asset_ids))
        .order_by(Candle.asset_id, Candle.timestamp.desc())
    )
    
    candle_result = await db.execute(latest_candles_query)
    candles = candle_result.scalars().all()
    
    latest_candles = {}
    for candle in candles:
        if candle.asset_id not in latest_candles:
            latest_candles[candle.asset_id] = candle
    
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
        "timestamp": utc_now_iso(),
        "data": result
    }


@router.get("/market-overview", response_model=dict)
async def get_market_overview(
    market: MarketEnum = Query("NASDAQ"),
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
            Asset.market == "NASDAQ",
            Asset.active == True,
            Asset.asset_class.in_(["EQUITY", "ETF"]),
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
        "timestamp": utc_now_iso(),
    }


@router.get("/nasdaq-dashboard", response_model=dict)
async def nasdaq_dashboard(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    NASDAQ market dashboard summary.

    Returns total symbols, average daily change, and top 5 gainers / losers
    from the latest stored daily candles using a single window-function query.
    Other markets are excluded by the market='NASDAQ' filter.

    Returns:
        NASDAQ market overview snapshot
    """
    Candle = candle_model_for_market("NASDAQ")

    latest_two_cte = (
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
        .where(Candle.timeframe == "1d")
        .cte("latest_two")
    )

    query = (
        select(
            Asset.id,
            Asset.symbol,
            Asset.name,
            func.max(latest_two_cte.c.close).filter(latest_two_cte.c.rn == 1).label("latest_close"),
            func.max(latest_two_cte.c.close).filter(latest_two_cte.c.rn == 2).label("previous_close"),
        )
        .join(latest_two_cte, Asset.id == latest_two_cte.c.asset_id)
        .where(
            and_(
                Asset.market == "NASDAQ",
                Asset.active == True,
                Asset.asset_class.in_(["EQUITY", "ETF"]),
            )
        )
        .group_by(
            Asset.id,
            Asset.symbol,
            Asset.name,
        )
        .order_by(Asset.symbol)
    )

    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return {
            "status": "success",
            "market": "NASDAQ",
            "total_symbols": 0,
            "average_change_pct": 0.0,
            "top_gainers": [],
            "top_losers": [],
            "timestamp": utc_now_iso(),
        }

    result_rows = []
    for row in rows:
        latest_close = float(row.latest_close)
        previous_close = float(row.previous_close) if row.previous_close is not None else latest_close
        change_pct = ((latest_close - previous_close) / previous_close * 100) if previous_close else 0.0
        if isinstance(change_pct, float) and math.isnan(change_pct):
            change_pct = 0.0

        result_rows.append({
            "symbol": row.symbol,
            "name": row.name,
            "last_close": latest_close,
            "change_pct": round(change_pct, 2),
        })

    ranked_change = sorted(result_rows, key=lambda x: x["change_pct"], reverse=True)
    change_values = [r["change_pct"] for r in ranked_change if isinstance(r["change_pct"], (int, float)) and not math.isnan(r["change_pct"])]
    avg_change = round(sum(change_values) / len(change_values), 2) if change_values else 0.0

    return {
        "status": "success",
        "market": "NASDAQ",
        "total_symbols": len(result_rows),
        "average_change_pct": round(avg_change, 2),
        "top_gainers": ranked_change[:5],
        "top_losers": sorted(ranked_change, key=lambda x: x["change_pct"])[:5],
        "timestamp": utc_now_iso(),
    }


# Major market indices tracked by the dashboard. `yf_symbol` is the yfinance
# ticker used to fetch live quotes.
MAJOR_INDICES = [
    {"symbol": "IXIC", "yf_symbol": "^IXIC", "name": "NASDAQ Composite"},
    {"symbol": "INX", "yf_symbol": "^GSPC", "name": "S&P 500"},
    {"symbol": "DJI", "yf_symbol": "^DJI", "name": "Dow Jones Industrial Average"},
    {"symbol": "RUT", "yf_symbol": "^RUT", "name": "Russell 2000"},
]

_indices_cache: Dict[str, Any] = {}
_indices_cache_expiry: float = 0.0
_INDICES_CACHE_TTL = 60.0


@router.get("/indices", response_model=dict)
async def get_market_indices(response: Response = None) -> dict:
    """
    Live prices for major market indices (NASDAQ Composite, S&P 500, Dow, Russell 2000).

    Uses the real-time market data service (yfinance) so the dashboard can show
    real index levels instead of a placeholder. Results are cached for a short
    window to avoid hammering the downstream provider on every dashboard load.
    """
    if response:
        response.headers["X-API-Version"] = "v1"

    global _indices_cache, _indices_cache_expiry
    now = time.time()
    if _indices_cache and now < _indices_cache_expiry:
        return _indices_cache

    container = get_global_container()
    if container.has("real_time_market_data_service"):
        rt_service = container.get("real_time_market_data_service")
    else:
        rt_service = RealTimeMarketDataService()

    market_hours = MarketHoursService()
    is_open = market_hours.is_market_open()

    async def _fetch_one(idx: Dict[str, str]) -> Optional[Dict[str, Any]]:
        try:
            quote = await rt_service.get_realtime_quote(idx["yf_symbol"])
        except Exception as exc:
            logger.warning(f"Failed to fetch index quote for {idx['yf_symbol']}: {exc}")
            return None
        return {
            "symbol": idx["symbol"],
            "yf_symbol": idx["yf_symbol"],
            "name": idx["name"],
            "price": quote.current_price,
            "change": quote.change_value,
            "change_percent": quote.change_percent,
            "is_open": is_open,
        }

    results = await asyncio.gather(*[_fetch_one(idx) for idx in MAJOR_INDICES])
    data = [item for item in results if item is not None]

    result = {
        "status": "success",
        "timestamp": utc_now_iso(),
        "data": data,
    }
    _indices_cache = result
    _indices_cache_expiry = now + _INDICES_CACHE_TTL
    return result


@router.get("/industry-ranking", response_model=dict)
async def industry_ranking(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    NASDAQ industry ranking.

    Ranks NASDAQ industries by the average daily change of their
    constituent symbols using a single window-function query over daily candles.
    Only market='NASDAQ' symbols are considered; other markets are excluded.

    Returns:
        Industries ranked by average change %, each with member count
    """
    Candle = candle_model_for_market("NASDAQ")

    # Single optimized query: join assets with candles, compute latest and previous close
    query = (
        select(
            Asset.industry,
            Asset.id,
            Asset.symbol,
            Candle.close,
            func.row_number()
            .over(
                partition_by=Candle.asset_id,
                order_by=Candle.timestamp.desc(),
            )
            .label("rn"),
        )
        .join(Candle, Asset.id == Candle.asset_id)
        .where(
            and_(
                Asset.market == "NASDAQ",
                Asset.active == True,
                Asset.asset_class.in_(["EQUITY", "ETF"]),
                Asset.industry.isnot(None),
                Candle.timeframe == "1d",
            )
        )
    )

    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return {
            "status": "success",
            "market": "NASDAQ",
            "ranked_industries": 0,
            "ranking": [],
            "timestamp": utc_now_iso(),
        }

    # Separate latest and previous close per asset
    asset_rows: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if row.rn == 1:
            latest = row.close
        elif row.rn == 2:
            previous = row.close
        else:
            continue
        if row.industry not in asset_rows:
            asset_rows[row.industry] = {}
        if row.rn == 1:
            asset_rows[row.industry][str(row.id)] = {
                "symbol": row.symbol,
                "latest": latest,
                "previous": None,
            }
        elif row.rn == 2:
            entry = asset_rows[row.industry].get(str(row.id))
            if entry:
                entry["previous"] = previous

    # Remove assets without a latest close
    for ind, assets in asset_rows.items():
        asset_rows[ind] = {k: v for k, v in assets.items() if v["latest"] is not None}

    industry_changes: Dict[str, List[float]] = {}
    for industry, assets in asset_rows.items():
        for data in assets.values():
            latest = float(data["latest"])
            previous = float(data["previous"]) if data["previous"] is not None else latest
            change = ((latest - previous) / previous * 100) if previous else 0.0
            industry_changes.setdefault(industry, []).append(change)

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
        "market": "NASDAQ",
        "ranked_industries": len(ranking),
        "ranking": ranking,
        "timestamp": utc_now_iso(),
    }
