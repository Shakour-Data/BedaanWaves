"""Dashboard API Routes"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, Numeric
from typing import Optional
import logging

from app.db.base import get_async_session
from app.models.models import Asset, ScoreHistory
from app.services.analysis.dashboard_service import DashboardService

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
    limit: int = Query(50, ge=10, le=200),
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
    limit: int = Query(50, ge=10, le=200),
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
    limit: int = Query(50, ge=10, le=200),
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
    limit: int = Query(50, ge=10, le=200),
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
    limit: int = Query(50, ge=10, le=200),
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

    Aggregates ``ScoreHistory`` rows for every active asset in the given
    ``market`` (defaults to NASDAQ) and returns one data point per
    trading day with:

    - ``avg_score``        - mean ``overall_score`` across all assets
    - ``avg_technical``    - mean of the ``technical`` value inside
                             ``dimension_scores`` JSONB (or 0 if missing)
    - ``score_change``     - ``avg_score[t] - avg_score[t-1]``
    - ``technical_change`` - ``avg_technical[t] - avg_technical[t-1]``
    - ``symbol_count``     - number of assets that contributed to the day

    Args:
        days:   Lookback window in days (default 30, max 365).
        market: Market filter (defaults to ``NASDAQ``). Pass ``null``
                (or the literal string ``"ALL"``) to span every market.

    Returns:
        Aggregated daily series for charting.
    """
    try:
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)

        # Build the market filter. We special-case ``ALL`` and ``None`` to mean
        # "every active asset" (used by tests and internal debugging).
        market_filter = Asset.market == market if market and market.upper() != "ALL" else Asset.market.isnot(None)

        # A single GROUP BY date query does the heavy lifting on the database
        # side. ``coalesce`` makes the technical aggregation NULL-safe because
        # some legacy rows may not have a ``technical`` key in dimension_scores.
        technical_expr = func.coalesce(
            func.avg(
                case(
                    (ScoreHistory.dimension_scores.has_key("technical"),
                     func.cast(ScoreHistory.dimension_scores["technical"], Numeric(10, 4))),
                    else_=0,
                )
            ),
            0.0,
        ).label("avg_technical")

        query = (
            select(
                ScoreHistory.date.label("date"),
                func.avg(ScoreHistory.overall_score).label("avg_score"),
                technical_expr,
                func.count(func.distinct(ScoreHistory.asset_id)).label("symbol_count"),
            )
            .join(Asset, Asset.id == ScoreHistory.asset_id)
            .where(
                and_(
                    Asset.active == True,
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
            series.append(
                {
                    "date": row.date.isoformat(),
                    "avg_score": round(float(row.avg_score or 0.0), 4),
                    "avg_technical": round(float(row.avg_technical or 0.0), 4),
                    "symbol_count": int(row.symbol_count or 0),
                }
            )

        # Compute day-over-day deltas on the server so the client can plot
        # them directly. The first day is reported with a delta of 0.
        for i, point in enumerate(series):
            if i == 0:
                point["score_change"] = 0.0
                point["technical_change"] = 0.0
            else:
                prev = series[i - 1]
                point["score_change"] = round(point["avg_score"] - prev["avg_score"], 4)
                point["technical_change"] = round(point["avg_technical"] - prev["avg_technical"], 4)

        return {
            "status": "success",
            "days": days,
            "market": market,
            "count": len(series),
            "series": series,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.error(f"Score trend error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
