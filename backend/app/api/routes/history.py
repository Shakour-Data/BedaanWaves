"""History Routes"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_async_session
from app.models.models import Asset
from app.schemas.schemas import PriceHistoryResponse
from app.services.data.stock_service import StockService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["history"])


@router.get("/{ticker}", response_model=PriceHistoryResponse)
async def get_price_history(
    ticker: str,
    days: int = Query(30, ge=1, le=3650),
    db: AsyncSession = Depends(get_async_session),
) -> PriceHistoryResponse:
    """Get price history for a ticker."""
    from app.core.utils import utc_now_iso
    asset_query = select(Asset).where(func.lower(Asset.symbol) == func.lower(ticker))
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")

    service = StockService()
    await service.initialize()
    end = datetime.now(UTC).date().isoformat()
    start = (datetime.now(UTC) - timedelta(days=days)).date().isoformat()
    history = await service.get_history(str(asset.symbol), start_date=start, end_date=end, interval="daily")
    await service.shutdown()

    data = [
        {"date": h["timestamp"], "open": h["open"], "high": h["high"],
         "low": h["low"], "close": h["close"]}
        for h in history
    ]
    return PriceHistoryResponse(
        status="success",
        symbol=asset.symbol,
        data=data,
        count=len(data),
        timestamp=utc_now_iso(),
    )


@router.get("/volume/{ticker}", response_model=PriceHistoryResponse)
async def get_volume_history(
    ticker: str,
    days: int = Query(30, ge=1, le=3650),
    db: AsyncSession = Depends(get_async_session),
) -> PriceHistoryResponse:
    """Get volume history for a ticker."""
    from app.core.utils import utc_now_iso
    asset_query = select(Asset).where(func.lower(Asset.symbol) == func.lower(ticker))
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")

    service = StockService()
    await service.initialize()
    end = datetime.now(UTC).date().isoformat()
    start = (datetime.now(UTC) - timedelta(days=days)).date().isoformat()
    history = await service.get_history(str(asset.symbol), start_date=start, end_date=end, interval="daily")
    await service.shutdown()

    data = [{"date": h["timestamp"], "volume": h["volume"]} for h in history]
    return PriceHistoryResponse(
        status="success",
        symbol=asset.symbol,
        data=data,
        count=len(data),
        timestamp=utc_now_iso(),
    )
