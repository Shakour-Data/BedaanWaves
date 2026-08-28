"""Ranking API Routes"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.base import get_async_session
from app.services.analysis.ranking_service import RankingService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ranking"])


@router.get("/nasdaq", response_model=dict)
async def get_nasdaq_rankings(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("overall_score"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get ranked list of Nasdaq stocks with their 6D scores.

    Query params:
        limit: Number of results to return (default 50, max 200)
        offset: Pagination offset (default 0)
        sort_by: Field to sort by (overall_score, fundamental, technical, sentiment, risk, macro, ai)
        order: Sort order (asc or desc)
    """
    service = RankingService()
    await service.initialize()
    try:
        result = await service.get_nasdaq_rankings(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            order=order,
            db=db,
        )
        return result
    finally:
        await service.shutdown()
