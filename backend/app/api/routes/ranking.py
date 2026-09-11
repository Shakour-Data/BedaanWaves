"""Ranking API Routes"""

import logging
import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_async_session
from app.schemas.schemas import RankingResponse
from app.services.analysis.ranking_service import RankingService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ranking"])


def _assign_grade(score: float) -> str:
    """Assign a grade based on overall score."""
    if score >= 85:
        return "STRONG_BULLISH"
    elif score >= 70:
        return "BULLISH"
    elif score >= 55:
        return "NEUTRAL"
    elif score >= 40:
        return "BEARISH"
    else:
        return "STRONG_BEARISH"


def _technical_score(closes: list[float]) -> float:
    """Calculate technical score from closing prices (0-100)."""
    if len(closes) < 20:
        return 0.0
    recent = closes[-20:]
    first = recent[0]
    last = recent[-1]
    if first <= 0:
        return 50.0
    change_pct = (last - first) / first * 100
    if change_pct >= 50:
        return 100.0
    elif change_pct <= -50:
        return 0.0
    else:
        return max(0.0, min(100.0, 50.0 + change_pct))


def _risk_score(closes: list[float]) -> float:
    """Calculate risk score from closing prices (0-100, lower risk = higher score)."""
    if len(closes) < 2:
        return 50.0
    returns = []
    for i in range(1, len(closes)):
        if closes[i - 1] > 0:
            r = (closes[i] - closes[i - 1]) / closes[i - 1]
            returns.append(r)
    if not returns:
        return 50.0
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    volatility = math.sqrt(variance) * math.sqrt(252)
    if volatility >= 1.0:
        return 0.0
    elif volatility <= 0.05:
        return 100.0
    else:
        return max(0.0, 100.0 - (volatility * 100))


@router.get("/nasdaq", response_model=RankingResponse)
async def get_nasdaq_rankings(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("overall_score"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_async_session),
) -> RankingResponse:
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
        return RankingResponse(**result)
    finally:
        await service.shutdown()
