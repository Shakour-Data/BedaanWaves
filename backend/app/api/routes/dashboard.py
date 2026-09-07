"""Dashboard API Routes - Leaderboard & Biggest Movers"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import utc_now_iso
from app.db.base import get_async_session
from app.services.analysis.dashboard_service import DashboardService
from app.services.analysis.coefficient_history_service import DIMENSION_KEYS
from app.services.analysis.hierarchical_score_trend_service import (
    HierarchicalScoreTrendService,
)
from app.services.analysis.hierarchy import ALL_TREND_KEYS
from app.services.analysis.market_score_trend_service import MarketScoreTrendService
from app.services.analysis.temporal_snapshot_service import TemporalSnapshotService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dashboard"])

SUB_DIMENSION_TREND_KEYS = ALL_TREND_KEYS["sub_dimension"]
ASPECT_TREND_KEYS = ALL_TREND_KEYS["aspect"]
SUB_ASPECT_TREND_KEYS = ALL_TREND_KEYS["sub_aspect"]

VALID_LEVELS = ("overall", "dimension", "sub_dimension", "aspect", "sub_aspect")
CANONICAL_DIMENSIONS = ("fundamental", "technical", "sentiment", "risk", "macro", "ai")


@router.get("/dashboard/snapshot", response_model=dict)
async def get_dashboard_snapshot(
    symbol: str | None = Query(None, min_length=1, max_length=16),
    snapshotId: str | None = Query(None),
    window_daily: int = Query(30, ge=1, le=365),
    window_intraday: str = Query("24h", pattern="^(6h|24h|7d)$"),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Unified 3-tier snapshot endpoint (FR1).

    Returns daily / hourly / current scores, deltas, weights, weight trends/deltas,
    and both daily + intraday trend series, all tied to a single `snapshotId`.
    """
    service = TemporalSnapshotService()
    try:
        await service.initialize()
        try:
            result = await service.get_market_snapshot(
                db=db,
                window_daily=window_daily,
                window_intraday=window_intraday,
                symbol=symbol,
                snapshot_id=snapshotId,
            )
        finally:
            await service.shutdown()
        # ensure we return status + timestamp envelope for legacy parity of consumer
        result.setdefault("status", "success")
        result.setdefault("timestamp", utc_now_iso())
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Dashboard snapshot error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/snapshots", response_model=dict)
async def get_dashboard_snapshots_index(
    hourly_limit: int = Query(168, ge=24, le=720),
    daily_limit: int = Query(365, ge=30, le=1095),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Enumerate recent hourly + daily snapshots for time-slider (FR1, FR8).

    Frontend TypeScript contract expects shape:
      { hourly: SnapshotIndexEntry[], daily: SnapshotIndexEntry[] }
    (no outer status/count envelope — arrays carry their own length).
    """
    service = TemporalSnapshotService()
    try:
        await service.initialize()
        try:
            entries = await service.enumerate_snapshots(
                db=db,
                hourly_limit=hourly_limit,
                daily_limit=daily_limit,
            )
        finally:
            await service.shutdown()
        hourly_entries = [e for e in entries if e.get("tier") == "hourly"]
        daily_entries = [e for e in entries if e.get("tier") == "daily"]
        return {
            "hourly": hourly_entries,
            "daily": daily_entries,
        }
    except Exception as exc:
        logger.error(f"Snapshot index error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/top-performers", response_model=dict)
async def get_top_performers(
    level: str = Query("overall", pattern="^(overall|dimension|sub_dimension|aspect|sub_aspect)$"),
    dimension: str | None = Query(None, pattern="^(fundamental|technical|sentiment|risk|macro|ai)$"),
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
    dimension: str | None = Query(None, pattern="^(fundamental|technical|sentiment|risk|macro|ai)$"),
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
    market: str | None = Query("NASDAQ"),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Portfolio-level score trend endpoint (preserved for compatibility).

    Internally sources from TemporalSnapshotService first (parity rule: values
    must match new snapshot widgets within 0.05 abs tolerance). Falls back to
    the legacy MarketScoreTrendService path only when temporal snapshot rows
    are insufficient.
    """

    DIMENSIONS = ("fundamental", "technical", "sentiment", "risk", "macro", "ai")
    if market is None or market.upper() != "NASDAQ":
        raise HTTPException(
            status_code=400,
            detail="Only the NASDAQ market is supported by /dashboard/score-trend.",
        )
    try:
        series: list[dict] = []
        source: str = ""

        # ---- TemporalSnapshotService parity-first path ----
        snap_service = TemporalSnapshotService()
        try:
            await snap_service.initialize()
            try:
                snap = await snap_service.get_market_snapshot(
                    db=db,
                    window_daily=days,
                    window_intraday="24h",
                )
            finally:
                await snap_service.shutdown()
            daily_points = (snap.get("trends") or {}).get("daily") or []
            # min 80% coverage of requested days before trusting snapshot path
            if len(daily_points) >= max(1, int(days * 0.8)):
                for pt in daily_points:
                    dims_raw = pt.get("dimensions") or {}
                    dims = {
                        d: float(dims_raw.get(d)) if isinstance(dims_raw.get(d), (int, float)) else 0.0
                        for d in DIMENSIONS
                    }
                    series.append({
                        "date": pt.get("timestamp") or pt.get("date") or "",
                        "avg_score": float(pt.get("avg_score")) if isinstance(pt.get("avg_score"), (int, float)) else 0.0,
                        "avg_dimensions": dims,
                        "symbol_count": int(pt.get("symbol_count")) if pt.get("symbol_count") is not None else 0,
                    })
                source = "temporal_snapshot"
        except Exception as exc:  # pragma: no cover - safety net
            logger.warning(f"score-trend snapshot fallback: {exc}")
            series = []
            source = ""

        # ---- Legacy fallback path (when snapshot produced insufficient rows) ----
        if not source:
            trend_service = MarketScoreTrendService()
            series = await trend_service.get_trend(days=days, market=market, db=db)
            source = "precomputed"
            if not series:
                from app.services.analysis.dashboard_service import (
                    _aggregate_score_trend_on_the_fly,
                )
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
                prev_tech = prev["avg_dimensions"]["technical"] if "technical" in prev["avg_dimensions"] else 0.0
                curr_tech = point["avg_dimensions"]["technical"] if "technical" in point["avg_dimensions"] else 0.0
                point["technical_change"] = round(curr_tech - prev_tech, 4)
                point["dimension_changes"] = {
                    dim: round(
                        (point["avg_dimensions"].get(dim) or 0.0) - (prev["avg_dimensions"].get(dim) or 0.0), 4
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
    market: str | None = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Coefficient history endpoint (preserved for compatibility).

    Internally sources from TemporalSnapshotService.weightTrends when
    sufficient coverage exists (80% of requested days). Falls back to legacy
    CoefficientHistoryService otherwise.
    """
    from app.services.analysis.coefficient_history_service import (
        DIMENSION_KEYS,
        CoefficientHistoryService,
    )

    try:
        series: list[dict] = []
        source_count: int = 0
        latest_date: str | None = None

        # ---- TemporalSnapshotService parity-first path ----
        snap_service = TemporalSnapshotService()
        try:
            await snap_service.initialize()
            try:
                snap = await snap_service.get_market_snapshot(
                    db=db,
                    window_daily=days,
                    window_intraday="24h",
                )
            finally:
                await snap_service.shutdown()
            weight_trends = snap.get("weightTrends") or []
            if len(weight_trends) >= max(1, int(days * 0.8)):
                for i, pt in enumerate(weight_trends):
                    weights_raw = pt.get("weights") or {}
                    metrics = {
                        k: float(weights_raw.get(k)) if isinstance(weights_raw.get(k), (int, float)) else 0.0
                        for k in DIMENSION_KEYS
                    }
                    if i == 0:
                        metric_changes = {k: 0.0 for k in DIMENSION_KEYS}
                    else:
                        prev_raw = (weight_trends[i - 1].get("weights") or {})
                        metric_changes = {
                            k: round(
                                metrics.get(k, 0.0) - (
                                    float(prev_raw.get(k))
                                    if isinstance(prev_raw.get(k), (int, float))
                                    else 0.0
                                ),
                                6,
                            )
                            for k in DIMENSION_KEYS
                        }
                    d = str(pt.get("date") or "")
                    series.append({
                        "date": d,
                        "dimensions": metrics,
                        "dimension_changes": metric_changes,
                    })
                    latest_date = d
                source_count = len(series)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"coefficient-history snapshot fallback: {exc}")
            series = []

        # ---- Legacy fallback path ----
        if not series:
            service = CoefficientHistoryService()
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
            source_count = result.get("count", len(series))
            latest_date = result.get("latest_date")

        return {
            "status": "success",
            "days": days,
            "market": market or "NASDAQ",
            "count": source_count if source_count else len(series),
            "dimensions": list(DIMENSION_KEYS),
            "series": series,
            "latest_date": latest_date,
            "timestamp": utc_now_iso(),
        }
    except Exception as exc:
        logger.error(f"Coefficient history error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/hierarchical-trend", response_model=dict)
async def get_hierarchical_trend(
    level: str = Query("sub_dimension"),
    days: int = Query(30, ge=1, le=365),
    market: str | None = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: str | None = Query(None),
    parent: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Hierarchical trend endpoint (preserved for compatibility).

    Calls TemporalSnapshotService first to warm the latest snapshots and to
    attempt parity-first series derivation from snapshot trends.daily for
    the `dimension` level. For deeper levels (sub_dimension / aspect /
    sub_aspect) the snapshot currently exposes single-frame hierarchy scores
    but not multi-day series; in those cases we transparently fall back to
    HierarchicalScoreTrendService which reads the same up-to-date DB tables.
    """
    if level not in ("sub_dimension", "aspect", "sub_aspect", "dimension"):
        raise HTTPException(status_code=400, detail="level must be dimension, sub_dimension, aspect, or sub_aspect")
    try:
        derived_series: list[dict] = []
        derived_count: int = 0
        derived_latest: str | None = None

        # ---- TemporalSnapshotService parity-first path ----
        snap_service = TemporalSnapshotService()
        try:
            await snap_service.initialize()
            try:
                snap = await snap_service.get_market_snapshot(
                    db=db,
                    window_daily=days,
                    window_intraday="24h",
                )
            finally:
                await snap_service.shutdown()
            # only level=`dimension` can currently be derived from trends.daily
            if level == "dimension":
                daily_points = (snap.get("trends") or {}).get("daily") or []
                if len(daily_points) >= max(1, int(days * 0.8)):
                    for i, pt in enumerate(daily_points):
                        metrics = pt.get("dimensions") or {}
                        if parent and parent not in metrics:
                            continue
                        if i == 0:
                            metric_changes = {k: 0.0 for k in metrics.keys()}
                        else:
                            prev_metrics = daily_points[i - 1].get("dimensions") or {}
                            metric_changes = {
                                k: round(
                                    (float(metrics.get(k)) if isinstance(metrics.get(k), (int, float)) else 0.0) -
                                    (float(prev_metrics.get(k)) if isinstance(prev_metrics.get(k), (int, float)) else 0.0),
                                    4,
                                )
                                for k in set(list(metrics.keys()) + list(prev_metrics.keys()))
                            }
                        d = str(pt.get("timestamp") or pt.get("date") or "")
                        derived_series.append({
                            "date": d,
                            "metrics": metrics,
                            "metric_changes": metric_changes,
                            "symbol_count": int(pt.get("symbol_count")) if pt.get("symbol_count") is not None else 0,
                        })
                        derived_latest = d
                    derived_count = len(derived_series)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"hierarchical-trend snapshot derive skipped: {exc}")
            derived_series = []

        # ---- Legacy HierarchicalScoreTrendService fallback ----
        if not derived_series:
            service = HierarchicalScoreTrendService()
            end_dt = datetime.fromisoformat(end_date).date() if end_date else None
            result = await service.get_trend(
                level=level, days=days, market=market, latest=latest, end_date=end_dt, db=db,
            )
            derived_series = result.get("series", [])
            derived_count = result.get("count", len(derived_series))
            derived_latest = result.get("latest_date")

        return {
            "status": "success",
            "level": level,
            "days": days,
            "market": market or "NASDAQ",
            "parent": parent,
            "count": derived_count if derived_count else len(derived_series),
            "latest_date": derived_latest,
            "series": derived_series,
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
    market: str | None = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Sub-dimension trend endpoint (preserved for compatibility).

    Calls TemporalSnapshotService first to warm/validate latest tier snapshots,
    then derives from HierarchicalScoreTrendService (same underlying DB tables
    the snapshot composer materializes tier roots from). L2 series are not yet materialized inside
    snapshot.trends.daily; fallback path is always authoritative until trends
    builder is extended.
    """
    if market is None or market.upper() != "NASDAQ":
        raise HTTPException(
            status_code=400,
            detail="Only the NASDAQ market is supported by /dashboard/sub-dimension-trend.",
        )
    if not isinstance(latest, bool):
        latest = False
    if not isinstance(end_date, str):
        end_date = None
    try:
        # ---- TemporalSnapshotService warm-up / parity alignment hook ----
        try:
            snap_service = TemporalSnapshotService()
            await snap_service.initialize()
            try:
                _ = await snap_service.get_market_snapshot(
                    db=db, window_daily=days, window_intraday="24h",
                )
            finally:
                await snap_service.shutdown()
        except Exception as exc:  # pragma: no cover
            logger.warning(f"sub-dimension-trend snap warm skipped: {exc}")

        service = HierarchicalScoreTrendService()
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
    market: str | None = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: str | None = Query(None),
    parent: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Aspect trend endpoint (preserved for compatibility).

    Calls TemporalSnapshotService as parity warm-up hook, then delegates to
    HierarchicalScoreTrendService for the authoritative L3 series (same DB
    tables the snapshot composer materializes tier roots from).
    """
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
    try:
        # ---- TemporalSnapshotService warm-up / parity alignment hook ----
        try:
            snap_service = TemporalSnapshotService()
            await snap_service.initialize()
            try:
                _ = await snap_service.get_market_snapshot(
                    db=db, window_daily=days, window_intraday="24h",
                )
            finally:
                await snap_service.shutdown()
        except Exception as exc:  # pragma: no cover
            logger.warning(f"aspect-trend snap warm skipped: {exc}")

        service = HierarchicalScoreTrendService()
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
    market: str | None = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: str | None = Query(None),
    parent: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Sub-aspect trend endpoint (preserved for compatibility).

    Calls TemporalSnapshotService as parity warm-up hook, then delegates to
    HierarchicalScoreTrendService for the authoritative L4 series.
    """
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
    try:
        # ---- TemporalSnapshotService warm-up / parity alignment hook ----
        try:
            snap_service = TemporalSnapshotService()
            await snap_service.initialize()
            try:
                _ = await snap_service.get_market_snapshot(
                    db=db, window_daily=days, window_intraday="24h",
                )
            finally:
                await snap_service.shutdown()
        except Exception as exc:  # pragma: no cover
            logger.warning(f"sub-aspect-trend snap warm skipped: {exc}")

        service = HierarchicalScoreTrendService()
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
    market: str | None = Query("NASDAQ"),
    latest: bool = Query(False),
    end_date: str | None = Query(None),
    parent: str | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Coefficient history by level endpoint (preserved for compatibility).

    Calls TemporalSnapshotService for parity-first dimension weight-trend
    derivation when level=dimension (sourced from snapshot.weightTrends /
    weightDeltas). For deeper levels (sub_dimension / aspect / sub_aspect)
    transparently delegates to CoefficientHistoryService which reads the
    same underlying tables the snapshot composer materializes tier roots from.
    """
    from app.services.analysis.coefficient_history_service import (
        CoefficientHistoryService,
        DIMENSION_KEYS,
    )

    if level not in VALID_LEVELS or level == "overall":
        raise HTTPException(
            status_code=400,
            detail="level must be dimension, sub_dimension, aspect, or sub_aspect",
        )
    try:
        series: List[dict] = []
        source_count: int = 0
        latest_date: Optional[str] = None

        # ---- TemporalSnapshotService parity-first path (only dimension) ----
        if level == "dimension":
            try:
                snap_service = TemporalSnapshotService()
                await snap_service.initialize()
                try:
                    snap = await snap_service.get_market_snapshot(
                        db=db, window_daily=days, window_intraday="24h",
                    )
                finally:
                    await snap_service.shutdown()
                weight_trends = snap.get("weightTrends") or []
                if len(weight_trends) >= max(1, int(days * 0.8)):
                    for i, pt in enumerate(weight_trends):
                        weights_raw = pt.get("weights") or {}
                        metrics = {
                            k: float(weights_raw.get(k)) if isinstance(weights_raw.get(k), (int, float)) else 0.0
                            for k in DIMENSION_KEYS
                            if (parent is None or k == parent)
                        }
                        if i == 0:
                            metric_changes = {k: 0.0 for k in metrics.keys()}
                        else:
                            prev_raw = (weight_trends[i - 1].get("weights") or {})
                            metric_changes = {
                                k: round(
                                    metrics.get(k, 0.0) - (
                                        float(prev_raw.get(k))
                                        if isinstance(prev_raw.get(k), (int, float))
                                        else 0.0
                                    ),
                                    6,
                                )
                                for k in metrics.keys()
                            }
                        d = str(pt.get("date") or "")
                        series.append({
                            "date": d,
                            "metrics": metrics,
                            "metric_changes": metric_changes,
                        })
                        latest_date = d
                    source_count = len(series)
            except Exception as exc:  # pragma: no cover
                logger.warning(f"coefficient-by-level snapshot derive skipped: {exc}")
                series = []

        # ---- Legacy CoefficientHistoryService fallback ----
        if not series:
            service = CoefficientHistoryService()
            end_dt = datetime.fromisoformat(end_date).date() if end_date else None
            result = await service.get_history(
                days=days, market=market, level=level, parent=parent, latest=latest, end_date=end_dt,
            )
            series = result.get("series", [])
            source_count = result.get("count", len(series))
            latest_date = result.get("latest_date")

        return {
            "status": "success",
            "level": level,
            "days": days,
            "market": market or "NASDAQ",
            "parent": parent,
            "count": source_count if source_count else len(series),
            "latest_date": latest_date,
            "series": series,
            "timestamp": utc_now_iso(),
        }
    except Exception as exc:
        logger.error(f"Coefficient history by level error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
