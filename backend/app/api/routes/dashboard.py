"""Dashboard API Routes - Leaderboard & Biggest Movers"""

from datetime import datetime, timezone, timedelta, date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, and_, case, Numeric
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from app.core.utils import utc_now_iso

from app.db.base import get_async_session
from app.models.models import Asset, ScoreHistory
from app.services.analysis.dashboard_service import DashboardService
from app.services.analysis.hierarchical_score_trend_service import SUB_DIMENSION_TO_PARENT
from app.services.analysis.market_score_trend_service import MarketScoreTrendService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dashboard"])

SUB_DIMENSION_TREND_KEYS = tuple(SUB_DIMENSION_TO_PARENT.keys())
ASPECT_TREND_KEYS = tuple(
    f"{k.rsplit('_', 1)[0]}_aspect_{i}"
    for k in SUB_DIMENSION_TREND_KEYS
    for i in (1, 2)
)
SUB_ASPECT_TREND_KEYS = tuple(
    f"{k}_detail_{i}"
    for k in ASPECT_TREND_KEYS
    for i in range(1, 5)
)

VALID_LEVELS = ("overall", "dimension", "sub_dimension", "aspect", "sub_aspect")
CANONICAL_DIMENSIONS = ("fundamental", "technical", "sentiment", "risk", "macro", "ai")


@router.get("/dashboard/top-performers", response_model=dict)
async def get_top_performers(
    level: str = Query("overall", pattern="^(overall|dimension|sub_dimension|aspect|sub_aspect)$"),
    dimension: Optional[str] = Query(None, pattern="^(fundamental|technical|sentiment|risk|macro|ai)$"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get top performers at the specified scoring level.

    - level=overall: rank by overall score
    - level=dimension: rank by dimension score (requires dimension param)
    - level=sub_dimension: rank by sub-dimension score (requires dimension param)
    - level=aspect: rank by aspect score (requires dimension param)
    - level=sub_aspect: rank by sub-aspect score (requires dimension param)
    """
    service = DashboardService()
    try:
        result = await service.get_top_performers(db, level=level, dimension=dimension, limit=limit)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Top performers error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/biggest-movers", response_model=dict)
async def get_biggest_movers(
    level: str = Query("overall", pattern="^(overall|dimension|sub_dimension|aspect|sub_aspect)$"),
    dimension: Optional[str] = Query(None, pattern="^(fundamental|technical|sentiment|risk|macro|ai)$"),
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(1, ge=1, le=30),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Get biggest movers by score change over the last N trading days.

    - level=overall: compute change in overall score
    - level=dimension: compute change in dimension score (requires dimension param)
    - level=sub_dimension: compute change in sub-dimension score (requires dimension param)
    - level=aspect: compute change in aspect score (requires dimension param)
    - level=sub_aspect: compute change in sub-aspect score (requires dimension param)
    """
    service = DashboardService()
    try:
        result = await service.get_biggest_movers(db, level=level, dimension=dimension, limit=limit, days=days)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Biggest movers error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/score-trend", response_model=dict)
async def get_score_trend(
    days: int = Query(30, ge=1, le=365),
    market: Optional[str] = Query("NASDAQ"),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Portfolio-level score trend endpoint (preserved for compatibility)."""
    from app.services.analysis.market_score_trend_service import MarketScoreTrendService

    DIMENSIONS = ("fundamental", "technical", "sentiment", "risk", "macro", "ai")
    if market is None or market.upper() != "NASDAQ":
        raise HTTPException(
            status_code=400,
            detail="Only the NASDAQ market is supported by /dashboard/score-trend.",
        )
    try:
        trend_service = MarketScoreTrendService()
        series = await trend_service.get_trend(days=days, market=market, db=db)
        source = "precomputed"

        if not series:
            from app.services.analysis.dashboard_service import _aggregate_score_trend_on_the_fly
            series = await _aggregate_score_trend_on_the_fly(db, days=days)
            source = "on_the_fly_fallback"

        median_count = (
            sorted([p.get("symbol_count", 0) for p in series])[len(series) // 2]
            if series
            else 0
        )
        min_acceptable_count = max(median_count * 0.1, 100)
        series = [p for p in series if (p.get("symbol_count", 0) or 0) >= min_acceptable_count]

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


@router.get("/dashboard/coefficient-history", response_model=dict)
async def get_coefficient_history(
    days: int = Query(30, ge=1, le=365),
    market: Optional[str] = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Coefficient history endpoint (preserved for compatibility)."""
    from app.services.analysis.coefficient_history_service import (
        CoefficientHistoryService,
        DIMENSION_KEYS,
    )

    service = CoefficientHistoryService()
    try:
        end_dt = datetime.fromisoformat(end_date).date() if end_date else None
        result = await service.get_history(
            days=days, market=market, level="dimension", latest=latest, end_date=end_dt,
        )
        series = [
            {
                "date": pt["date"],
                "dimensions": pt["metrics"],
                "dimension_changes": pt["metric_changes"],
            }
            for pt in result.get("series", [])
        ]
        return {
            "status": "success",
            "days": result["days"],
            "market": result["market"],
            "count": result["count"],
            "dimensions": list(DIMENSION_KEYS),
            "series": series,
            "latest_date": result.get("latest_date"),
            "timestamp": utc_now_iso(),
        }
    except Exception as exc:
        logger.error(f"Coefficient history error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/hierarchical-trend", response_model=dict)
async def get_hierarchical_trend(
    level: str = Query("sub_dimension"),
    days: int = Query(30, ge=1, le=365),
    market: Optional[str] = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: Optional[str] = Query(None),
    parent: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Hierarchical trend endpoint (preserved for compatibility)."""
    from app.services.analysis.hierarchical_score_trend_service import (
        HierarchicalScoreTrendService,
        SUB_DIMENSION_TO_PARENT,
    )

    if level not in ("sub_dimension", "aspect", "sub_aspect"):
        raise HTTPException(status_code=400, detail="level must be sub_dimension, aspect, or sub_aspect")
    service = HierarchicalScoreTrendService()
    try:
        end_dt = datetime.fromisoformat(end_date).date() if end_date else None
        result = await service.get_trend(
            level=level, days=days, market=market, latest=latest, end_date=end_dt, db=db,
        )
        return {
            "status": "success",
            "level": level,
            "days": result["days"],
            "market": result["market"],
            "parent": result.get("parent"),
            "count": result["count"],
            "latest_date": result.get("latest_date"),
            "series": result.get("series", []),
            "timestamp": utc_now_iso(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Hierarchical trend error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/sub-dimension-trend", response_model=dict)
async def get_sub_dimension_trend(
    days: int = Query(30, ge=1, le=365),
    market: Optional[str] = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Sub-dimension trend endpoint (preserved for compatibility)."""
    from app.services.analysis.hierarchical_score_trend_service import (
        HierarchicalScoreTrendService,
        SUB_DIMENSION_TO_PARENT,
    )

    if market is None or market.upper() != "NASDAQ":
        raise HTTPException(
            status_code=400,
            detail="Only the NASDAQ market is supported by /dashboard/sub-dimension-trend.",
        )
    if not isinstance(latest, bool):
        latest = False
    if not isinstance(end_date, str):
        end_date = None
    service = HierarchicalScoreTrendService()
    try:
        end_dt = datetime.fromisoformat(end_date).date() if end_date else None
        result = await service.get_trend(
            level="sub_dimension", days=days, market=market, latest=latest, end_date=end_dt, db=db,
        )
        series = [
            {
                "date": pt["date"],
                "avg_scores": pt["metrics"],
                "score_changes": pt["metric_changes"],
                "symbol_count": pt.get("symbol_count", 0),
            }
            for pt in result.get("series", [])
        ]
        return {
            "status": "success",
            "level": "sub_dimension",
            "days": result["days"],
            "market": result["market"],
            "count": result["count"],
            "keys": list(SUB_DIMENSION_TREND_KEYS),
            "series": series,
            "latest_date": result.get("latest_date"),
            "timestamp": utc_now_iso(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Sub-dimension trend error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/aspect-trend", response_model=dict)
async def get_aspect_trend(
    days: int = Query(30, ge=1, le=365),
    market: Optional[str] = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: Optional[str] = Query(None),
    parent: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Aspect trend endpoint (preserved for compatibility)."""
    from app.services.analysis.hierarchical_score_trend_service import HierarchicalScoreTrendService

    if market is None or market.upper() != "NASDAQ":
        raise HTTPException(
            status_code=400,
            detail="Only the NASDAQ market is supported by /dashboard/aspect-trend.",
        )
    if not isinstance(latest, bool):
        latest = False
    if not isinstance(end_date, str):
        end_date = None
    if not isinstance(parent, str):
        parent = None
    service = HierarchicalScoreTrendService()
    try:
        end_dt = datetime.fromisoformat(end_date).date() if end_date else None
        result = await service.get_trend(
            level="aspect", days=days, market=market, latest=latest, end_date=end_dt, db=db,
        )
        series = [
            {
                "date": pt["date"],
                "avg_scores": pt["metrics"],
                "score_changes": pt["metric_changes"],
                "symbol_count": pt.get("symbol_count", 0),
            }
            for pt in result.get("series", [])
        ]
        return {
            "status": "success",
            "level": "aspect",
            "days": result["days"],
            "market": result["market"],
            "count": result["count"],
            "keys": list(ASPECT_TREND_KEYS),
            "series": series,
            "latest_date": result.get("latest_date"),
            "timestamp": utc_now_iso(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Aspect trend error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/sub-aspect-trend", response_model=dict)
async def get_sub_aspect_trend(
    days: int = Query(30, ge=1, le=365),
    market: Optional[str] = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: Optional[str] = Query(None),
    parent: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Sub-aspect trend endpoint (preserved for compatibility)."""
    from app.services.analysis.hierarchical_score_trend_service import HierarchicalScoreTrendService

    if market is None or market.upper() != "NASDAQ":
        raise HTTPException(
            status_code=400,
            detail="Only the NASDAQ market is supported by /dashboard/sub-aspect-trend.",
        )
    if not isinstance(latest, bool):
        latest = False
    if not isinstance(end_date, str):
        end_date = None
    if not isinstance(parent, str):
        parent = None
    service = HierarchicalScoreTrendService()
    try:
        end_dt = datetime.fromisoformat(end_date).date() if end_date else None
        result = await service.get_trend(
            level="sub_aspect", days=days, market=market, latest=latest, end_date=end_dt, db=db,
        )
        series = [
            {
                "date": pt["date"],
                "avg_scores": pt["metrics"],
                "score_changes": pt["metric_changes"],
                "symbol_count": pt.get("symbol_count", 0),
            }
            for pt in result.get("series", [])
        ]
        return {
            "status": "success",
            "level": "sub_aspect",
            "days": result["days"],
            "market": result["market"],
            "count": result["count"],
            "keys": list(SUB_ASPECT_TREND_KEYS),
            "series": series,
            "latest_date": result.get("latest_date"),
            "timestamp": utc_now_iso(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Sub-aspect trend error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/coefficient-history-by-level", response_model=dict)
async def get_coefficient_history_by_level(
    level: str = Query("dimension"),
    days: int = Query(30, ge=1, le=365),
    market: Optional[str] = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: Optional[str] = Query(None),
    parent: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Coefficient history by level endpoint (preserved for compatibility)."""
    from app.services.analysis.coefficient_history_service import CoefficientHistoryService

    if level not in ("dimension", "sub_dimension", "aspect", "sub_aspect"):
        raise HTTPException(status_code=400, detail="level must be dimension, sub_dimension, aspect, or sub_aspect")
    service = CoefficientHistoryService()
    try:
        end_dt = datetime.fromisoformat(end_date).date() if end_date else None
        result = await service.get_history(
            days=days, market=market, level=level, parent=parent, latest=latest, end_date=end_dt,
        )
        return {
            "status": "success",
            "level": level,
            "days": result["days"],
            "market": result["market"],
            "parent": result.get("parent"),
            "count": result["count"],
            "latest_date": result.get("latest_date"),
            "series": result.get("series", []),
            "timestamp": utc_now_iso(),
        }
    except Exception as exc:
        logger.error(f"Coefficient history by level error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
