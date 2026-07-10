"""Specialized Routes - Tier 7 (sector analysis, screening, comparison, correlation, calendar)"""

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import logging

from app.db.base import get_async_session
from app.models.models import Asset, PriceCandle, MLSignal
from app.services.specialized.sector_analysis_service import SectorAnalysisService
from app.services.specialized.screening_service import ScreeningService
from app.services.specialized.comparison_service import ComparisonService
from app.services.specialized.correlation_service import CorrelationService
from app.services.specialized.calendar_service import CalendarService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/specialized", tags=["specialized"])


def _load(svc_cls):
    svc = svc_cls()
    return svc


async def _build_universe(
    db: AsyncSession, market: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Build a stock universe from stored assets, latest candle, and latest signal."""
    latest_ts = (
        select(
            PriceCandle.asset_id,
            func.max(PriceCandle.timestamp).label("ts"),
        )
        .where(PriceCandle.timeframe == "1d")
        .group_by(PriceCandle.asset_id)
        .subquery()
    )

    query = (
        select(Asset, PriceCandle)
        .where(Asset.active == True)  # noqa: E712
        .join(
            latest_ts,
            Asset.id == latest_ts.c.asset_id,
        )
        .join(
            PriceCandle,
            and_(
                PriceCandle.asset_id == latest_ts.c.asset_id,
                PriceCandle.timestamp == latest_ts.c.ts,
                PriceCandle.timeframe == "1d",
            ),
        )
    )
    if market:
        query = query.where(Asset.market == market)

    result = await db.execute(query)
    rows = result.all()

    assets = [a for a, _ in rows]
    asset_ids = [a.id for a in assets]
    signals: Dict[Any, MLSignal] = {}
    if asset_ids:
        sig_query = (
            select(MLSignal)
            .where(
                and_(
                    MLSignal.asset_id.in_(asset_ids),
                    MLSignal.is_active == True,  # noqa: E712
                    MLSignal.valid_until >= datetime.utcnow(),
                )
            )
            .order_by(MLSignal.generated_at.desc())
        )
        sig_rows = (await db.execute(sig_query)).scalars().all()
        for sig in sig_rows:
            signals.setdefault(sig.asset_id, sig)

    universe = []
    for asset, candle in rows:
        change_pct = (
            (float(candle.close) - float(candle.open)) / float(candle.open) * 100
            if float(candle.open) > 0 else 0.0
        )
        sig = signals.get(asset.id)
        universe.append({
            "symbol": asset.symbol,
            "name": asset.name,
            "sector": asset.sector,
            "asset_class": asset.asset_class,
            "price": float(candle.close),
            "volume": int(candle.volume),
            "change_pct": round(change_pct, 2),
            "score": float(sig.confidence) if sig else None,
            "signal": sig.signal_type if sig else None,
        })
    return universe


@router.get("/sectors/summary")
async def sectors_summary(
    market: str = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Aggregate the stock universe into sector-level intelligence."""
    universe = await _build_universe(db, market)
    svc = _load(SectorAnalysisService)
    await svc.initialize()
    result = await svc.analyze_all(universe)
    result["timestamp"] = datetime.utcnow().isoformat()
    return {"status": "success", **result}


@router.post("/screen")
async def screen(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Screen stocks against criteria.

    Body: {"criteria": {...}, "universe": [optional explicit records]}
    If `universe` is omitted, it is built from the stored stock database.
    """
    criteria = data.get("criteria", {})
    universe = data.get("universe")
    if universe is None:
        universe = await _build_universe(db, data.get("market"))

    svc = _load(ScreeningService)
    await svc.initialize()
    return await svc.screen(universe, criteria)


@router.post("/compare")
async def compare(data: dict = Body(...)) -> dict:
    """
    Compare symbols across metrics.

    Body: {"symbols": [ {symbol, score, change_pct, volatility, momentum, risk_score, expected_return}, ... ]}
    """
    symbols_data = data.get("symbols", [])
    svc = _load(ComparisonService)
    await svc.initialize()
    result = await svc.compare(symbols_data)
    result["timestamp"] = datetime.utcnow().isoformat()
    return result


@router.post("/correlation")
async def correlation(data: dict = Body(...)) -> dict:
    """
    Compute a correlation matrix from return series.

    Body: {
        "returns_map": {"SYM1": [r1, r2, ...], "SYM2": [...]},
        "high_threshold": 0.7,
        "low_threshold": -0.7
    }
    """
    returns_map = data.get("returns_map", {})
    if not isinstance(returns_map, dict) or not returns_map:
        raise HTTPException(status_code=400, detail="returns_map must be a non-empty object")

    svc = _load(CorrelationService)
    await svc.initialize()
    result = await svc.compute_correlation(
        returns_map,
        high_threshold=float(data.get("high_threshold", 0.7)),
        low_threshold=float(data.get("low_threshold", -0.7)),
    )
    result["timestamp"] = datetime.utcnow().isoformat()
    return result


@router.get("/calendar/month")
async def calendar_month(
    year: int = Query(..., ge=1300, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> dict:
    """Return trading days and weekend days for a month."""
    svc = _load(CalendarService)
    await svc.initialize()
    result = svc.get_month_calendar(year, month)
    return {"status": "success", **result}


@router.get("/calendar/events")
async def calendar_events(
    day: str = Query(None, description="ISO date (YYYY-MM-DD)"),
    symbol: str = Query(None),
) -> dict:
    """List corporate/calendar events, optionally filtered by day and symbol."""
    svc = _load(CalendarService)
    await svc.initialize()
    if day:
        parsed = datetime.strptime(day, "%Y-%m-%d").date()
        events = svc.get_events(day=parsed, symbol=symbol)
    else:
        events = svc.get_events(symbol=symbol)
    return {"status": "success", "count": len(events), "events": events}


@router.post("/calendar/events")
async def add_calendar_event(data: dict = Body(...)) -> dict:
    """Add a corporate/calendar event. Required: date, type, title."""
    svc = _load(CalendarService)
    await svc.initialize()
    record = svc.add_event(data)
    return {"status": "success", "event": record}
