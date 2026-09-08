"""TSE (Tehran Stock Exchange) API Routes

Provides endpoints for:
- Neark index constituents
- Neark index overview
- TSE market overview
- Price history for TSE symbols
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.utils import utc_now_iso
from app.db.base import async_session_maker
from app.models.models import Asset, TSEPriceCandle
from app.services.core.dependency_container import get_global_container
from app.services.data.tse_ingestion_service import TseIngestionService
from app.db.base import async_session_maker

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["tse"])


def get_tse_service() -> TseIngestionService:
    """Get TseIngestionService from the dependency container."""
    container = get_global_container()
    if container.has("tse_service"):
        return container.get("tse_service")
    return TseIngestionService()


@router.get("/nerk/constituents", response_model=None)
async def get_nerk_constituents() -> dict[str, Any]:
    """Get all Neark (نزدک) index constituent symbols."""
    service = get_tse_service()
    try:
        constituents = await service.get_nerk_constituents()
        return {
            "status": "success",
            "index": "Nerek (نزدک)",
            "exchange": "Tehran Stock Exchange (TSE)",
            "count": len(constituents),
            "data": constituents,
            "timestamp": utc_now_iso(),
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching Neark constituents: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Error fetching Neark constituents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nerk/overview", response_model=None)
async def get_nerk_overview() -> dict[str, Any]:
    """Get Neark index overview with top gainers and losers."""
    service = get_tse_service()
    try:
        constituents = await service.get_nerk_constituents()

        # Get latest price data for constituents
        gainers = []
        losers = []
        total_return = 0.0
        count = 0

        for item in constituents[:50]:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(TSEPriceCandle)
                    .where(TSEPriceCandle.asset_id == item.get("id"))
                    .order_by(TSEPriceCandle.timestamp.desc())
                    .limit(2)
                )
                candles = result.scalars().all()
                if len(candles) >= 2:
                    latest = candles[0]
                    prev = candles[1]
                    change_pct = ((float(latest.close) - float(prev.close)) / float(prev.close)) * 100 if float(prev.close) > 0 else 0
                    entry = {
                        "symbol": item["symbol"],
                        "name": item["name"],
                        "price": float(latest.close),
                        "change_pct": round(change_pct, 2),
                    }
                    total_return += change_pct
                    count += 1
                    if change_pct > 0:
                        gainers.append(entry)
                    else:
                        losers.append(entry)

        gainers.sort(key=lambda x: x["change_pct"], reverse=True)
        losers.sort(key=lambda x: x["change_pct"])

        market_overview = await service.get_market_overview()

        return {
            "status": "success",
            "index": "Nerek (نزدک)",
            "exchange": "Tehran Stock Exchange",
            "market_overview": market_overview,
            "constituents_count": len(constituents),
            "top_gainers": gainers[:10],
            "top_losers": losers[:10],
            "avg_change_pct": round(total_return / count, 2) if count > 0 else 0,
            "timestamp": utc_now_iso(),
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching Neark overview: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Error fetching Neark overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nerk/price-history/{symbol}", response_model=None)
async def get_nerk_price_history(
    symbol: str,
    period: str = Query("1y", description="Period: 1m, 3m, 6m, 1y, 2y, 5y"),
) -> dict[str, Any]:
    """Get price history for a TSE symbol."""
    service = get_tse_service()
    try:
        # Period to days mapping
        period_days = {
            "1m": 30, "3m": 90, "6m": 180,
            "1y": 365, "2y": 730, "5y": 1825
        }
        days = period_days.get(period, 365)
        cutoff = datetime.now(UTC) - timedelta(days=days)

        async with async_session_maker() as session:
            result = await session.execute(
                select(Asset).where(Asset.symbol == symbol).where(Asset.market == "TSE")
            )
            asset = result.scalar_one_or_none()
            if not asset:
                raise HTTPException(status_code=404, detail=f"TSE symbol {symbol} not found")

            candles_result = await session.execute(
                select(TSEPriceCandle)
                .where(TSEPriceCandle.asset_id == asset.id)
                .where(TSEPriceCandle.timestamp >= cutoff)
                .where(TSEPriceCandle.timeframe == "1d")
                .order_by(TSEPriceCandle.timestamp.asc())
            )
            candles = candles_result.scalars().all()

            candle_data = []
            for c in candles:
                candle_data.append({
                    "timestamp": c.timestamp.isoformat(),
                    "open": float(c.open),
                    "high": float(c.high),
                    "low": float(c.low),
                    "close": float(c.close),
                    "volume": int(c.volume),
                    "turnover": float(c.turnover) if c.turnover else None,
                    "adjusted_close": float(c.adjusted_close) if c.adjusted_close else None,
                })

            return {
                "status": "success",
                "symbol": symbol,
                "name": asset.name,
                "market": "TSE",
                "period": period,
                "count": len(candle_data),
                "data": candle_data,
                "timestamp": utc_now_iso(),
            }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching price history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Error fetching price history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols")
async def get_tse_symbols(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Get all TSE symbols with pagination."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Asset.symbol, Asset.name, Asset.sector, Asset.asset_class, Asset.active)
                .where(Asset.market == "TSE")
                .order_by(Asset.symbol)
                .limit(limit)
                .offset(offset)
            )
            rows = result.all()

            total_result = await session.execute(
                select(func.count(Asset.id)).where(Asset.market == "TSE")
            )
            total = total_result.scalar_one_or_none() or 0

            symbols = [
                {
                    "symbol": r[0],
                    "name": r[1],
                    "sector": r[2],
                    "asset_class": r[3],
                    "active": r[4],
                }
                for r in rows
            ]

            return {
                "status": "success",
                "market": "TSE",
                "total": total,
                "limit": limit,
                "offset": offset,
                "data": symbols,
                "timestamp": utc_now_iso(),
            }
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching TSE symbols: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Error fetching TSE symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-overview", response_model=None)
async def get_tse_market_overview() -> dict[str, Any]:
    """Get TSE market overview."""
    service = get_tse_service()
    try:
        overview = await service.get_market_overview()
        return {
            "status": "success",
            "data": overview,
            "timestamp": utc_now_iso(),
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching TSE market overview: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Error fetching TSE market overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
