"""History Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import List
from collections import defaultdict
import logging

from app.db.base import get_async_session
from app.models.models import Asset
from app.services.data.stock_service import StockService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["history"])


@router.get("/{ticker}", response_model=List[dict])
async def get_price_history(
    ticker: str,
    days: int = Query(30, ge=1, le=3650),
    db: AsyncSession = Depends(get_async_session),
) -> List[dict]:
    """Get price history for a ticker."""
    asset_query = select(Asset).where(func.lower(Asset.symbol) == func.lower(ticker))
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")

    service = StockService()
    await service.initialize()
    end = datetime.utcnow().date().isoformat()
    start = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
    history = await service.get_history(asset.symbol, start_date=start, end_date=end, interval="daily")
    await service.shutdown()

    return [
        {"date": h["timestamp"], "open": h["open"], "high": h["high"],
         "low": h["low"], "close": h["close"]}
        for h in history
    ]


@router.get("/volume/{ticker}", response_model=List[dict])
async def get_volume_history(
    ticker: str,
    days: int = Query(30, ge=1, le=3650),
    db: AsyncSession = Depends(get_async_session),
) -> List[dict]:
    """Get volume history for a ticker."""
    asset_query = select(Asset).where(func.lower(Asset.symbol) == func.lower(ticker))
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")

    service = StockService()
    await service.initialize()
    end = datetime.utcnow().date().isoformat()
    start = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
    history = await service.get_history(asset.symbol, start_date=start, end_date=end, interval="daily")
    await service.shutdown()

    return [{"date": h["timestamp"], "volume": h["volume"]} for h in history]