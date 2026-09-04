"""Dashboard API Routes"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, Numeric
from typing import Optional
import logging
from app.core.utils import utc_now_iso

from app.db.base import get_async_session
from app.models.models import Asset, ScoreHistory
from app.services.analysis.dashboard_service import DashboardService
from app.services.analysis.market_score_trend_service import MarketScoreTrendService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/general", response_model=dict)
async def get_general_dashboard(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get general/overall dashboard data for all symbols.
    
    Returns:
        Overall scores, dimension summaries, top/bottom performers
    """
    service = DashboardService()
    try:
        result = await service.get_general_dashboard(db)
        return result
    except Exception as exc:
        logger.error(f"General dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/technical", response_model=dict)
async def get_technical_dashboard(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get technical dashboard data for all symbols.
    
    Returns:
        Technical scores, sub-dimensions, aspects, sub-aspects, distribution
    """
    service = DashboardService()
    try:
        result = await service.get_dimension_dashboard(db, dimension="technical", limit=limit)
        return result
    except Exception as exc:
        logger.error(f"Technical dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/fundamental", response_model=dict)
async def get_fundamental_dashboard(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get fundamental dashboard data for all symbols.
    
    Returns:
        Fundamental scores, sub-dimensions, aspects, sub-aspects, distribution
    """
    service = DashboardService()
    try:
        result = await service.get_dimension_dashboard(db, dimension="fundamental", limit=limit)
        return result
    except Exception as exc:
        logger.error(f"Fundamental dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/news", response_model=dict)
async def get_news_dashboard(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get news/sentiment dashboard data for all symbols.
    
    Returns:
        News sentiment scores, news counts, positive/negative/neutral breakdown
    """
    service = DashboardService()
    try:
        result = await service.get_news_dashboard(db, limit=limit)
        return result
    except Exception as exc:
        logger.error(f"News dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/risk", response_model=dict)
async def get_risk_dashboard(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get risk dashboard data for all symbols.
    
    Returns:
        Risk scores, sub-dimensions, aspects, sub-aspects, distribution
    """
    service = DashboardService()
    try:
        result = await service.get_dimension_dashboard(db, dimension="risk", limit=limit)
        return result
    except Exception as exc:
        logger.error(f"Risk dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/board", response_model=dict)
async def get_board_dashboard(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get board/governance dashboard data for all symbols.
    
    Returns:
        Board scores, board member counts, officer counts, governance metrics
    """
    service = DashboardService()
    try:
        result = await service.get_board_dashboard(db, limit=limit)
        return result
    except Exception as exc:
        logger.error(f"Board dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/ai", response_model=dict)
async def get_ai_dashboard(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get AI/ML dashboard data for all symbols.

    Returns:
        AI scores, ML signals, confidence, expected returns, risk scores
    """
    service = DashboardService()
    try:
        result = await service.get_ai_dashboard(db, limit=limit)
        return result
    except Exception as exc:
        logger.error(f"AI dashboard error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/score-trend", response_model=dict)
async def get_score_trend(
    days: int = Query(30, ge=1, le=365),
    market: Optional[str] = Query("NASDAQ"),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Portfolio-level 30-day trend of the average overall score and the
    average technical-analysis weight, plus their day-over-day deltas.

    Aggregates ``ScoreHistory`` rows for every active Nasdaq-listed
    equity or ETF and returns one data point per trading day with:

    - ``avg_score``        - mean ``overall_score`` across all assets
    - ``avg_dimensions``   - dict of mean per-dimension scores for all 6
                             dimensions (``fundamental``, ``technical``,
                             ``sentiment``, ``risk``, ``macro``, ``ai``)
    - ``score_change``     - ``avg_score[t] - avg_score[t-1]``
    - ``dimension_changes``- dict of per-dimension day-over-day deltas
    - ``symbol_count``     - number of assets that contributed to the day

    The universe is hard-locked to Nasdaq equities + ETFs. Crypto,
    forex, commodities, bonds, indexes, and any non-Nasdaq equity are
    always excluded, regardless of the ``market`` argument.

    Args:
        days:   Lookback window in days (default 30, max 365).
        market: Market filter (defaults to ``NASDAQ``). Anything other
                than ``"NASDAQ"`` is rejected to keep the chart honest.

    Returns:
        Aggregated daily series for charting.
    """
    DIMENSIONS = ("fundamental", "technical", "sentiment", "risk", "macro", "ai")
    if market is None or market.upper() != "NASDAQ":
        raise HTTPException(
            status_code=400,
            detail="Only the NASDAQ market is supported by /dashboard/score-trend.",
        )
    try:
        # Prefer the precomputed ``market_score_trend`` table populated by
        # the daily ``MarketScoreTrendRecompute`` scheduler job. Fall back to
        # the on-the-fly aggregation if rows are missing (e.g. before the
        # first scheduler run after the migration).
        trend_service = MarketScoreTrendService()
        series = await trend_service.get_trend(days=days, market=market, db=db)
        source = "precomputed"

        if not series:
            series = await _aggregate_score_trend_on_the_fly(db, days=days)
            source = "on_the_fly_fallback"

        # Compute day-over-day deltas on the server so the client can plot
        # them directly. The first day is reported with a delta of 0.
        for i, point in enumerate(series):
            if i == 0:
                point["score_change"] = 0.0
                point["technical_change"] = 0.0
                point["dimension_changes"] = {dim: 0.0 for dim in DIMENSIONS}
            else:
                prev = series[i - 1]
                point["score_change"] = round(point["avg_score"] - prev["avg_score"], 4)
                prev_tech = prev["avg_dimensions"]["technical"]
                curr_tech = point["avg_dimensions"]["technical"]
                point["technical_change"] = round(curr_tech - prev_tech, 4)
                point["dimension_changes"] = {
                    dim: round(
                        point["avg_dimensions"][dim] - prev["avg_dimensions"][dim], 4
                    )
                    for dim in DIMENSIONS
                }

        return {
            "status": "success",
            "days": days,
            "market": market,
            "count": len(series),
            "dimensions": list(DIMENSIONS),
            "series": series,
            "source": source,
            "timestamp": utc_now_iso(),
        }
    except Exception as exc:
        logger.error(f"Score trend error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


async def _aggregate_score_trend_on_the_fly(
    db: AsyncSession, days: int
) -> list:
    """Fallback aggregator: same SQL as the original endpoint.

    Used only when the precomputed ``market_score_trend`` table has no rows
    for the requested window. Kept as a private helper so the response shape
    stays identical to the precomputed path.
    """
    DIMENSIONS = ("fundamental", "technical", "sentiment", "risk", "macro", "ai")
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)

    market_filter = and_(
        Asset.market == "NASDAQ",
        Asset.asset_class.in_(["EQUITY", "ETF"]),
    )

    dim_exprs = []
    for dim in DIMENSIONS:
        expr = func.coalesce(
            func.avg(
                case(
                    (
                        ScoreHistory.dimension_scores.has_key(dim),
                        func.cast(ScoreHistory.dimension_scores[dim], Numeric(10, 4)),
                    ),
                    else_=None,
                )
            ),
            0.0,
        ).label(f"avg_{dim}")
        dim_exprs.append(expr)

    query = (
        select(
            ScoreHistory.date.label("date"),
            func.avg(ScoreHistory.overall_score).label("avg_score"),
            *dim_exprs,
            func.count(func.distinct(ScoreHistory.asset_id)).label("symbol_count"),
        )
        .join(Asset, Asset.id == ScoreHistory.asset_id)
        .where(
            and_(
                Asset.active,
                market_filter,
                ScoreHistory.date >= cutoff,
            )
        )
        .group_by(ScoreHistory.date)
        .order_by(ScoreHistory.date.asc())
    )

    result = await db.execute(query)
    rows = result.all()

    series = []
    for row in rows:
        avg_dims = {
            dim: round(float(getattr(row, f"avg_{dim}") or 0.0), 4)
            for dim in DIMENSIONS
        }
        series.append({
            "date": row.date.isoformat(),
            "avg_score": round(float(row.avg_score or 0.0), 4),
            "avg_dimensions": avg_dims,
            "symbol_count": int(row.symbol_count or 0),
        })
    return series
