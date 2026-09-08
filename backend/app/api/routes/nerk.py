"""Nerk (Neark Index) API Routes

Provides endpoints for:
- Neark index constituents
- Neark index overview
- Price history for Neark constituents
- Neark market overview
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.utils import utc_now_iso
from app.db.base import async_session_maker
from app.models.models import Asset, IntlPriceCandle
from app.services.core.dependency_container import get_global_container
from app.services.data.nerk_ingestion_service import NerkIngestionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["nerk"])


def get_nerk_service() -> NerkIngestionService:
    """Get NerkIngestionService from the dependency container."""
    container = get_global_container()
    if container.has("nerk_service"):
        return container.get("nerk_service")
    return NerkIngestionService()


@router.get("/constituents")
async def get_nerk_constituents() -> dict[str, Any]:
    """Get all Neark (نزدک) index constituent symbols."""
    service = get_nerk_service()
    try:
        constituents = await service.get_constituents()
        return {
            "status": "success",
            "index": "Nerek (نزدک)",
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


@router.get("/overview")
async def get_nerk_overview() -> dict[str, Any]:
    """Get Neark index overview with top gainers and losers."""
    service = get_nerk_service()
    try:
        constituents = await service.get_constituents()

        gainers = []
        losers = []
        total_return = 0.0
        count = 0

        for item in constituents:
            change_pct = item.get("change_pct", 0)
            entry = {
                "symbol": item["symbol"],
                "name": item["name"],
                "price": item.get("price", 0),
                "change_pct": change_pct,
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


@router.get("/price-history/{symbol}")
async def get_nerk_price_history(
    symbol: str,
    period: str = Query("1y", description="Period: 1m, 3m, 6m, 1y, 2y, 5y"),
) -> dict[str, Any]:
    """Get price history for a Neark constituent symbol."""
    service = get_nerk_service()
    try:
        period_days = {
            "1m": 30, "3m": 90, "6m": 180,
            "1y": 365, "2y": 730, "5y": 1825
        }
        days = period_days.get(period, 365)
        cutoff = datetime.now(UTC) - timedelta(days=days)

        async with async_session_maker() as session:
            result = await session.execute(
                select(Asset).where(Asset.symbol == symbol).where(Asset.is_nerk_constituent == True)
            )
            asset = result.scalar_one_or_none()
            if not asset:
                raise HTTPException(status_code=404, detail=f"Neark symbol {symbol} not found")

            candles_result = await session.execute(
                select(IntlPriceCandle)
                .where(IntlPriceCandle.asset_id == asset.id)
                .where(IntlPriceCandle.timestamp >= cutoff)
                .where(IntlPriceCandle.timeframe == "1d")
                .order_by(IntlPriceCandle.timestamp.asc())
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
                "market": "NASDAQ",
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


@router.get("/market-overview")
async def get_nerk_market_overview() -> dict[str, Any]:
    """Get Neark index market overview."""
    service = get_nerk_service()
    try:
        overview = await service.get_market_overview()
        return {
            "status": "success",
            "data": overview,
            "timestamp": utc_now_iso(),
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching Neark market overview: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Error fetching Neark market overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
