"""History Routes"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
import logging

from app.db.base import get_async_session
from app.models.models import Asset, PriceCandle
from app.services.data.history_service import HistoryService
from app.services.data.brs_api_client import BrsApiClient
from app.api.routes.live import get_brs_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{ticker}", response_model=List[dict])
async def get_price_history(
    ticker: str,
    days: int = Query(30, ge=1, le=3650),
    db: AsyncSession = Depends(get_async_session),
) -> List[dict]:
    """Get price history for a ticker."""
    asset_query = select(Asset).where(Asset.symbol == ticker.upper())
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")

    client = await get_brs_client()
    service = HistoryService(db_service=None, brs_client=client)
    await service.initialize()

    return await service.get_price_history(ticker, days)


@router.get("/volume/{ticker}", response_model=List[dict])
async def get_volume_history(
    ticker: str,
    days: int = Query(30, ge=1, le=3650),
    db: AsyncSession = Depends(get_async_session),
) -> List[dict]:
    """Get volume history for a ticker."""
    asset_query = select(Asset).where(Asset.symbol == ticker.upper())
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")

    client = await get_brs_client()
    service = HistoryService(db_service=None, brs_client=client)
    await service.initialize()

    return await service.get_volume_history(ticker, days)
