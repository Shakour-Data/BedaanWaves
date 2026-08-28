"""Ranking Routes - Nasdaq stock ranking by 6D scores"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import timezone, datetime
from typing import List, Optional, Dict, Any
import logging
import time

from app.db.base import get_async_session
from app.models.models import Asset, MLSignal, candle_model_for_market

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ranking"])

MARKET = "NASDAQ"
CACHE_TTL = 300.0
_cache: Dict[str, Any] = {"ts": 0.0, "data": None}

DIMENSIONS = ["fundamental", "technical", "sentiment", "risk", "macro", "ai"]
DIMENSION_WEIGHTS = {
    "fundamental": 0.25,
    "technical": 0.20,
    "sentiment": 0.15,
    "risk": 0.20,
    "macro": 0.10,
    "ai": 0.10,
}

GRADE_THRESHOLDS = [
    (85, "A_STRONG_BUY"),
    (70, "B_BUY"),
    (55, "C_HOLD"),
    (40, "D_SELL"),
    (0, "E_STRONG_SELL"),
]

SIGNAL_SENTIMENT = {
    "STRONG_BUY": 100.0,
    "BUY": 75.0,
    "HOLD": 50.0,
    "SELL": 25.0,
    "STRONG_SELL": 0.0,
}


def _assign_grade(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "E_STRONG_SELL"


def _technical_score(closes: List[float]) -> float:
    if len(closes) < 2:
        return 0.0
    recent = closes[-1]
    lookback = closes[max(0, len(closes) - 20)]
    if lookback <= 0:
        return 50.0
    ret = (recent - lookback) / lookback * 100.0
    score = 50.0 + (ret / 25.0) * 50.0
    return max(0.0, min(100.0, score))


def _risk_score(closes: List[float]) -> float:
    if len(closes) < 3:
        return 50.0
    rets = [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1] > 0
    ]
    if not rets:
        return 50.0
    mean = sum(rets) / len(rets)
    variance = sum((r - mean) ** 2 for r in rets) / len(rets)
    std = variance ** 0.5
    vol_pct = std * 100.0
    score = 100.0 - vol_pct * 5.0
    return max(0.0, min(100.0, score))


async def _get_scored_list(db: AsyncSession) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)

    assets_q = select(Asset).where(
        Asset.market == MARKET,
        Asset.active == True,  # noqa: E712
    )
    assets = (await db.execute(assets_q)).scalars().all()
    if not assets:
        return []

    asset_ids = [a.id for a in assets]
    asset_by_id = {a.id: a for a in assets}

    Candle = candle_model_for_market(MARKET)
    candles_q = (
        select(Candle.asset_id, Candle.timestamp, Candle.open, Candle.close)
        .where(Candle.timeframe == "1d", Candle.asset_id.in_(asset_ids))
        .order_by(Candle.asset_id, Candle.timestamp.desc())
    )
    candle_rows = (await db.execute(candles_q)).all()

    closes_by_asset: Dict[Any, List[float]] = {}
    for asset_id, _ts, _open, close in candle_rows:
        closes_by_asset.setdefault(asset_id, []).append(float(close))
    for aid in closes_by_asset:
        closes_by_asset[aid].reverse()

    signals_q = (
        select(MLSignal)
        .where(
            MLSignal.asset_id.in_(asset_ids),
            MLSignal.is_active == True,  # noqa: E712
            MLSignal.valid_until >= now,
        )
        .order_by(MLSignal.generated_at.desc())
    )
    signal_rows = (await db.execute(signals_q)).scalars().all()
    signal_by_asset: Dict[Any, MLSignal] = {}
    for sig in signal_rows:
        signal_by_asset.setdefault(sig.asset_id, sig)

    scored: List[Dict[str, Any]] = []
    for aid, asset in asset_by_id.items():
        closes = closes_by_asset.get(aid, [])
        signal = signal_by_asset.get(aid)

        technical = _technical_score(closes)
        risk = _risk_score(closes)
        sentiment = SIGNAL_SENTIMENT.get(signal.signal_type, 50.0) if signal else 50.0
        ai = float(signal.confidence) if signal else 0.0
        fundamental = 0.0
        macro = 0.0

        overall = sum(
            DIMENSION_WEIGHTS[dim] * v
            for dim, v in {
                "fundamental": fundamental,
                "technical": technical,
                "sentiment": sentiment,
                "risk": risk,
                "macro": macro,
                "ai": ai,
            }.items()
        )

        scored.append({
            "symbol": asset.symbol,
            "name": asset.name,
            "rank": 0,
            "overall_score": round(overall, 2),
            "grade": _assign_grade(overall),
            "fundamental": round(fundamental, 2),
            "technical": round(technical, 2),
            "sentiment": round(sentiment, 2),
            "risk": round(risk, 2),
            "macro": round(macro, 2),
            "ai": round(ai, 2),
        })

    return scored


@router.get("/nasdaq")
async def rank_nasdaq(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("overall_score", pattern="^(overall_score|fundamental|technical|sentiment|risk|macro|ai)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Rank Nasdaq stocks by 6D scores (overall or any single dimension)."""
    global _cache
    if _cache.get("data") is None or (time.time() - _cache["ts"]) > CACHE_TTL:
        scored = await _get_scored_list(db)
        _cache = {"ts": time.time(), "data": scored}
    else:
        scored = _cache["data"]

    reverse = order == "desc"
    scored_sorted = sorted(scored, key=lambda r: r.get(sort_by, 0), reverse=reverse)

    for idx, row in enumerate(scored_sorted, start=1):
        row["rank"] = idx

    page = scored_sorted[offset: offset + limit]

    return {
        "status": "success",
        "market": MARKET,
        "total": len(scored_sorted),
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "order": order,
        "data": page,
    }
