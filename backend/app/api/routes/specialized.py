"""Specialized Routes - Tier 7 (sector analysis, screening, comparison, correlation, calendar)"""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schemas import (
    CalendarEventResponse,
    CalendarEventsResponse,
    CalendarMonthResponse,
    CompareStocksResponse,
    CorrelationResponse,
    ScreenResponse,
    SectorSummaryResponse,
)
from app.core.utils import utc_now_iso
from app.db.base import get_async_session
from app.models.models import Asset, MLSignal, candle_model_for_market
from app.services.specialized.calendar_service import CalendarService
from app.services.specialized.comparison_service import ComparisonService
from app.services.specialized.correlation_service import CorrelationService
from app.services.specialized.screening_service import ScreeningService
from app.services.specialized.sector_analysis_service import SectorAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["specialized"])


def _load(svc_cls):
    svc = svc_cls()
    return svc


async def _build_universe(
    db: AsyncSession, market: str | None = None
) -> list[dict[str, Any]]:
    """Build a stock universe from stored assets, latest candle, and latest signal.

    The universe is hard-locked to Nasdaq-listed equities and ETFs. The
    ``market`` argument is accepted for backward compatibility but any
    value other than ``"NASDAQ"`` is treated as ``"NASDAQ"``.
    """
    market = (market or "NASDAQ").upper()
    if market != "NASDAQ":
        market = "NASDAQ"
    Candle = candle_model_for_market("NASDAQ")
    latest_ts = (
        select(
            Candle.asset_id,
            func.max(Candle.timestamp).label("ts"),
        )
        .where(Candle.timeframe == "1d")
        .group_by(Candle.asset_id)
        .subquery()
    )

    query = (
        select(Asset, Candle)
        .where(
            and_(
                Asset.active,
                Asset.market == "NASDAQ",
                Asset.asset_class.in_(["EQUITY", "ETF"]),
            )
        )
        .join(
            latest_ts,
            Asset.id == latest_ts.c.asset_id,
        )
        .join(
            Candle,
            and_(
                Candle.asset_id == latest_ts.c.asset_id,
                Candle.timestamp == latest_ts.c.ts,
                Candle.timeframe == "1d",
            ),
        )
    )

    result = await db.execute(query)
    rows = result.all()

    assets = [a for a, _ in rows]
    asset_ids = [a.id for a in assets]
    signals: dict[Any, MLSignal] = {}
    if asset_ids:
        sig_query = (
            select(MLSignal)
            .where(
                and_(
                    MLSignal.asset_id.in_(asset_ids),
                    MLSignal.is_active,
                    MLSignal.valid_until >= datetime.now(UTC).replace(tzinfo=None),
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


@router.get("/sectors/summary", response_model=SectorSummaryResponse)
async def sectors_summary(
    market: str = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> SectorSummaryResponse:
    """Aggregate the stock universe into sector-level intelligence."""
    universe = await _build_universe(db, market)
    svc = _load(SectorAnalysisService)
    await svc.initialize()
    result = await svc.analyze_all(universe)
    return {
        "status": "success",
        "data": result.get("sectors", []),
        "timestamp": utc_now_iso(),
    }


@router.post("/screen", response_model=ScreenResponse)
async def screen(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_async_session),
) -> ScreenResponse:
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
    result = await svc.screen(universe, criteria)
    return {
        "status": "success",
        "results": result.get("results", []),
        "count": result.get("matched", 0),
        "timestamp": utc_now_iso(),
    }


@router.post("/compare", response_model=CompareStocksResponse)
async def compare(data: dict = Body(...)) -> CompareStocksResponse:
    """
    Compare symbols across metrics.

    Body: {"symbols": [ {symbol, score, change_pct, volatility, momentum, risk_score, expected_return}, ... ]}
    """
    symbols_data = data.get("symbols", [])
    svc = _load(ComparisonService)
    await svc.initialize()
    result = await svc.compare(symbols_data)
    return {
        "status": "success",
        "data": result,
        "timestamp": utc_now_iso(),
    }


@router.post("/correlation", response_model=CorrelationResponse)
async def correlation(data: dict = Body(...)) -> CorrelationResponse:
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
    return {
        "status": "success",
        "correlation_matrix": result,
        "timestamp": utc_now_iso(),
    }


@router.get("/calendar/month", response_model=CalendarMonthResponse)
async def calendar_month(
    year: int = Query(..., ge=1300, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> CalendarMonthResponse:
    """Return trading days and weekend days for a month."""
    svc = _load(CalendarService)
    await svc.initialize()
    result = svc.get_month_calendar(year, month)
    return {
        "status": "success",
        "year": result["year"],
        "month": result["month"],
        "events": result["trading_days"],
        "count": result["trading_day_count"],
    }


@router.get("/calendar/events", response_model=CalendarEventsResponse)
async def calendar_events(
    day: str = Query(None, description="ISO date (YYYY-MM-DD)"),
    symbol: str = Query(None),
) -> CalendarEventsResponse:
    """List corporate/calendar events, optionally filtered by day and symbol."""
    svc = _load(CalendarService)
    await svc.initialize()
    if day:
        parsed = datetime.strptime(day, "%Y-%m-%d").date()
        events = svc.get_events(day=parsed, symbol=symbol)
    else:
        events = svc.get_events(symbol=symbol)
    return {
        "status": "success",
        "events": events,
        "count": len(events),
        "timestamp": utc_now_iso(),
    }


@router.post("/calendar/events", response_model=CalendarEventResponse, status_code=201)
async def add_calendar_event(data: dict = Body(...)) -> CalendarEventResponse:
    """Add a corporate/calendar event. Required: date, type, title."""
    svc = _load(CalendarService)
    await svc.initialize()
    record = svc.add_event(data)
    return {
        "status": "success",
        "event": record,
        "timestamp": utc_now_iso(),
    }
