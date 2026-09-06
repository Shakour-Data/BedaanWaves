"""
Temporal Snapshot Service - Composes 3-tier scoring snapshots (daily / hourly / current)
into a single unified payload with deltas, weights, and trends.

Consumed by:
  - GET /analysis/dashboard/snapshot (new unified endpoint)
  - Legacy dashboard endpoints (delegation to guarantee numeric parity)

Uses AsyncSession + pooled connections only. Never opens sync DB sessions.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import utc_now_iso
from app.models.models import Asset, ScoreHistory
from app.models.scoring_snapshot import ScoringSnapshot, SnapshotTier
from app.services.analysis.coefficient_history_service import (
    CoefficientHistoryService,
    DIMENSION_KEYS,
)
from app.services.analysis.market_score_trend_service import MarketScoreTrendService
from app.services.analysis.hierarchical_score_trend_service import (
    HierarchicalScoreTrendService,
    SUB_DIMENSION_TO_PARENT,
)

try:
    from app.services.core.cache_service import CacheService
except Exception:  # pragma: no cover - optional
    CacheService = None  # type: ignore

logger = logging.getLogger(__name__)

CANONICAL_DIMS = ("fundamental", "technical", "sentiment", "risk", "macro", "ai")


@dataclass
class TierRoot:
    tier: str  # "daily" | "hourly" | "current"
    effective_at: datetime
    scores: Dict[str, Any]  # nested dict of overall, dimensions, sub_dimensions, ...


def _floor_to_hour(dt: datetime) -> datetime:
    """Return dt floored to the previous top-of-hour, UTC timezone-aware."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.replace(minute=0, second=0, microsecond=0)


def _floor_to_day(dt: datetime) -> datetime:
    """Return dt floored to 00:00 UTC of the same calendar day."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _iso(ts: Optional[datetime]) -> str:
    if ts is None:
        return ""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _compute_delta(a: Optional[float], b: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    """Return (delta_abs, delta_pct) where delta = a - b (a is 'newer')."""
    if a is None or b is None:
        return None, None
    delta = round(a - b, 4)
    if abs(b) < 1e-9:
        pct = 0.0 if abs(delta) < 1e-9 else None
    else:
        pct = round(delta / b * 100.0, 4)
    return delta, pct


def _dict_delta(new_map: Optional[dict], old_map: Optional[dict]) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    out: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    if not new_map or not old_map:
        return out
    for key in set(new_map.keys()) | set(old_map.keys()):
        a = float(new_map[key]) if new_map.get(key) is not None else None
        b = float(old_map[key]) if old_map.get(key) is not None else None
        out[key] = _compute_delta(a, b)
    return out


class TemporalSnapshotService:
    """Service that composes 3-tier snapshots into a unified response."""

    def __init__(self):
        self.cache: Optional[Any] = None
        if CacheService is not None:
            try:
                self.cache = CacheService()
                # init is optional; service methods fall through on any error
            except Exception as exc:  # pragma: no cover
                logger.warning(f"TemporalSnapshotService cache init skipped: {exc}")

    async def initialize(self) -> None:
        if self.cache and hasattr(self.cache, "initialize"):
            try:
                await self.cache.initialize()  # type: ignore[union-attr]
            except Exception as exc:  # pragma: no cover
                logger.warning(f"cache init failed: {exc}")

    async def shutdown(self) -> None:
        if self.cache and hasattr(self.cache, "shutdown"):
            try:
                await self.cache.shutdown()  # type: ignore[union-attr]
            except Exception as exc:  # pragma: no cover
                logger.warning(f"cache shutdown failed: {exc}")

    # ------------------------------------------------------------------ cache
    async def _cache_get(self, key: str) -> Optional[Any]:
        if not self.cache or not hasattr(self.cache, "get"):
            return None
        try:
            return await self.cache.get(key)  # type: ignore[union-attr]
        except Exception:
            return None

    async def _cache_set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        if not self.cache or not hasattr(self.cache, "set"):
            return
        try:
            await self.cache.set(key, value, ttl_seconds)  # type: ignore[union-attr]
        except Exception:
            pass

    # --------------------------------------------------------------- tiers
    async def _active_assets_count(self, db: AsyncSession) -> int:
        query = (
            select(func.count(Asset.id))
            .where(
                and_(
                    Asset.active == True,  # noqa: E712
                    Asset.market == "NASDAQ",
                    Asset.asset_class.in_(["EQUITY", "ETF"]),
                )
            )
        )
        result = await db.execute(query)
        val = result.scalar_one_or_none()
        return int(val) if val is not None else 0

    async def _resolve_tier_root(
        self,
        db: AsyncSession,
        tier: SnapshotTier,
        symbol: Optional[str] = None,
    ) -> Optional[TierRoot]:
        """Return the latest ScoringSnapshot-derived row for a tier.

        Falls back to ScoreHistory when the desired ScoringSnapshot row
        does not exist yet (e.g. hourly job has never run in a dev env).
        """
        asset_id = None
        if symbol:
            asset_q = select(Asset.id).where(
                func.lower(Asset.symbol) == func.lower(symbol)
            )
            res = await db.execute(asset_q)
            row = res.scalar_one_or_none()
            if not row:
                return None
            asset_id = row

        # Query 1: Latest ScoringSnapshot row for the tier
        filters: list = [ScoringSnapshot.snapshot_tier == tier.value]
        if asset_id is not None:
            filters.append(ScoringSnapshot.asset_id == asset_id)

        base_q = (
            select(ScoringSnapshot)
            .where(and_(*filters))
            .order_by(desc(ScoringSnapshot.effective_at))
            .limit(1)
        )
        res = await db.execute(base_q)
        snap_row = res.scalar_one_or_none()

        # Construct effective_at + build aggregated scores from ScoreHistory
        effective_at: Optional[datetime] = None
        if snap_row and snap_row.effective_at:
            effective_at = snap_row.effective_at

        # Aggregate from ScoreHistory (last matching date)
        sh_effective_date = None
        sh_q = (
            select(ScoreHistory, Asset)
            .join(Asset, Asset.id == ScoreHistory.asset_id)
            .where(
                and_(
                    Asset.active == True,  # noqa: E712
                    Asset.market == "NASDAQ",
                    Asset.asset_class.in_(["EQUITY", "ETF"]),
                )
            )
            .order_by(desc(ScoreHistory.date))
        )
        if symbol:
            sh_q = sh_q.where(func.lower(Asset.symbol) == func.lower(symbol)).limit(1)
        else:
            # take top 500 most recent to compute market median/mean
            sh_q = sh_q.limit(500)

        sh_res = await db.execute(sh_q)
        sh_rows = sh_res.all()

        scores: Dict[str, Any] = {"dimensions": {}}
        overall_list: List[float] = []
        dim_map: Dict[str, List[float]] = {d: [] for d in CANONICAL_DIMS}

        sub_dimensions: Dict[str, float] = {}
        aspects: Dict[str, float] = {}
        sub_aspects: Dict[str, float] = {}

        for sh, asset in sh_rows:
            if not sh_effective_date:
                sh_effective_date = sh.date
            if isinstance(sh.overall_score, (int, float)):
                overall_list.append(float(sh.overall_score))
            if sh.dimension_scores and isinstance(sh.dimension_scores, dict):
                for d, v in sh.dimension_scores.items():
                    if d in dim_map and isinstance(v, (int, float)):
                        dim_map[d].append(float(v))

        if snap_row and not effective_at and sh_effective_date:
            # derive effective_at from ScoreHistory.date if missing
            effective_at = datetime(
                year=sh_effective_date.year,
                month=sh_effective_date.month,
                day=sh_effective_date.day,
                hour=0 if tier == SnapshotTier.DAILY else 0,
                tzinfo=timezone.utc,
            )

        # Market-level aggregation: use mean
        if overall_list:
            scores["overall"] = round(sum(overall_list) / len(overall_list), 4)
        for d, vs in dim_map.items():
            if vs:
                scores["dimensions"][d] = round(sum(vs) / len(vs), 4)

        # (Optional) Pull sub-dim / aspect / sub-aspect from snap_row.extra_fields
        # if present; otherwise keep empty dict so UI renders — never None.
        scores.setdefault("sub_dimensions", sub_dimensions)
        scores.setdefault("aspects", aspects)
        scores.setdefault("sub_aspects", sub_aspects)

        if not scores.get("overall") and snap_row:
            scores["overall"] = float(snap_row.score) if snap_row.score else None

        if not effective_at:
            return None

        return TierRoot(tier=tier.value, effective_at=effective_at, scores=scores)

    async def _resolve_current(
        self,
        db: AsyncSession,
        symbol: Optional[str] = None,
    ) -> TierRoot:
        """Current = freshest available (hourly if <5 min old, else latest daily)."""
        now = datetime.now(timezone.utc)
        hourly = await self._resolve_tier_root(db, SnapshotTier.HOURLY, symbol=symbol)
        if hourly and (now - hourly.effective_at).total_seconds() < 300:
            return TierRoot(
                tier="current",
                effective_at=hourly.effective_at,
                scores=hourly.scores,
            )
        # else fallback to hourly if present, else daily
        if hourly:
            return TierRoot(tier="current", effective_at=hourly.effective_at, scores=hourly.scores)
        daily = await self._resolve_tier_root(db, SnapshotTier.DAILY, symbol=symbol)
        if daily:
            return TierRoot(tier="current", effective_at=daily.effective_at, scores=daily.scores)
        # ultimate fallback: synthetic empty
        return TierRoot(
            tier="current",
            effective_at=now,
            scores={"overall": 0.0, "dimensions": {}, "sub_dimensions": {}, "aspects": {}, "sub_aspects": {}},
        )

    def _build_deltas(self, daily: TierRoot, hourly: TierRoot, current: TierRoot) -> Dict[str, Any]:
        def _frame(newer: TierRoot, older: TierRoot) -> Dict[str, Any]:
            overall_abs, overall_pct = _compute_delta(
                float(newer.scores.get("overall")) if newer.scores.get("overall") is not None else None,
                float(older.scores.get("overall")) if older.scores.get("overall") is not None else None,
            )
            dim_deltas = _dict_delta(newer.scores.get("dimensions"), older.scores.get("dimensions"))
            dim_frame: Dict[str, Any] = {}
            for k, (vabs, vpct) in dim_deltas.items():
                dim_frame[k] = {"delta": vabs, "delta_pct": vpct}

            sub_dim_deltas = _dict_delta(newer.scores.get("sub_dimensions"), older.scores.get("sub_dimensions"))
            sub_dim_frame: Dict[str, Any] = {
                k: {"delta": vabs, "delta_pct": vpct} for k, (vabs, vpct) in sub_dim_deltas.items()
            }

            aspect_deltas = _dict_delta(newer.scores.get("aspects"), older.scores.get("aspects"))
            aspect_frame: Dict[str, Any] = {
                k: {"delta": vabs, "delta_pct": vpct} for k, (vabs, vpct) in aspect_deltas.items()
            }

            sub_aspect_deltas = _dict_delta(newer.scores.get("sub_aspects"), older.scores.get("sub_aspects"))
            sub_aspect_frame: Dict[str, Any] = {
                k: {"delta": vabs, "delta_pct": vpct} for k, (vabs, vpct) in sub_aspect_deltas.items()
            }

            return {
                "overall": overall_abs,
                "overall_pct": overall_pct,
                "dimensions": dim_frame,
                "sub_dimensions": sub_dim_frame,
                "aspects": aspect_frame,
                "sub_aspects": sub_aspect_frame,
            }

        return {
            "hourly_vs_daily": _frame(hourly, daily),
            "current_vs_hourly": _frame(current, hourly),
            "current_vs_daily": _frame(current, daily),
        }

    async def _build_weights(self, db: AsyncSession, days: int = 30) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        try:
            svc = CoefficientHistoryService()
            result = await svc.get_history(days=days, market="NASDAQ", level="dimension", latest=True)
            series: List[dict] = result.get("series", []) or []

            weight_snapshot: Dict[str, Any] = {}
            weight_trends: List[Dict[str, Any]] = []
            weight_deltas: List[Dict[str, Any]] = []

            current_weights: Dict[str, float] = {}
            if series:
                last = series[-1]
                metrics = last.get("metrics") or {}
                for k in DIMENSION_KEYS:
                    v = metrics.get(k)
                    if isinstance(v, (int, float)):
                        current_weights[k] = float(v)

            weight_snapshot["dimension"] = current_weights
            # sub_dimension / aspect / sub_aspect: stubs that mirror coefficient
            weight_snapshot["sub_dimension"] = {k: 1.0 / max(1, len(SUB_DIMENSION_TO_PARENT)) for k in list(SUB_DIMENSION_TO_PARENT.keys())[:6]}
            weight_snapshot["aspect"] = {}
            weight_snapshot["sub_aspect"] = {}

            for pt in series:
                weight_trends.append({
                    "date": str(pt.get("date")),
                    "weights": pt.get("metrics") or {},
                })

            if len(series) >= 2:
                prev = series[-2].get("metrics") or {}
                for k in DIMENSION_KEYS:
                    cur_v = current_weights.get(k)
                    prev_v = prev.get(k) if isinstance(prev.get(k), (int, float)) else None
                    if cur_v is not None and prev_v is not None:
                        weight_deltas.append({
                            "key": k,
                            "value": round(cur_v - prev_v, 6),
                        })

            return weight_snapshot, weight_trends, weight_deltas
        except Exception as exc:
            logger.warning(f"Coefficient snapshot fallback: {exc}")
            return (
                {"dimension": {}, "sub_dimension": {}, "aspect": {}, "sub_aspect": {}},
                [],
                [],
            )

    async def _build_trends(
        self,
        db: AsyncSession,
        window_daily: int = 30,
        window_intraday: str = "24h",
        symbol: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        daily_points: List[Dict[str, Any]] = []
        intraday_points: List[Dict[str, Any]] = []

        # Daily
        try:
            svc = MarketScoreTrendService()
            data = await svc.get_trend(days=window_daily, market="NASDAQ", db=db)
            for pt in data or []:
                daily_points.append({
                    "timestamp": str(pt.get("date")),
                    "avg_score": float(pt.get("avg_score")) if isinstance(pt.get("avg_score"), (int, float)) else None,
                    "dimensions": pt.get("avg_dimensions") or {},
                    "symbol_count": int(pt.get("symbol_count")) if pt.get("symbol_count") is not None else None,
                })
        except Exception as exc:
            logger.warning(f"market daily trend fallback: {exc}")

        # Intraday: reuse ScoringSnapshot hourly last 24 entries
        try:
            hours: Dict[str, Any] = {
                "6h": 6,
                "24h": 24,
                "7d": 24 * 7,
            }
            n = hours.get(window_intraday, 24)
            now = datetime.now(timezone.utc)
            start = now - timedelta(hours=n)
            query = (
                select(ScoringSnapshot)
                .where(
                    and_(
                        ScoringSnapshot.snapshot_tier == SnapshotTier.HOURLY.value,
                        ScoringSnapshot.effective_at >= start,
                    )
                )
                .order_by(ScoringSnapshot.effective_at.asc())
                .limit(500)
            )
            if symbol:
                asset_q = select(Asset.id).where(func.lower(Asset.symbol) == func.lower(symbol))
                res = await db.execute(asset_q)
                aid = res.scalar_one_or_none()
                if aid:
                    query = query.where(ScoringSnapshot.asset_id == aid)
            res = await db.execute(query)
            bucket: Dict[str, Dict[str, Any]] = {}
            for row in res.scalars().all():
                ts = _iso(row.effective_at)
                if ts not in bucket:
                    bucket[ts] = {"count": 0, "sum_score": 0.0, "dims": {d: [] for d in CANONICAL_DIMS}}
                if isinstance(row.score, (int, float)):
                    bucket[ts]["count"] += 1
                    bucket[ts]["sum_score"] += float(row.score)
            for ts in sorted(bucket.keys()):
                b = bucket[ts]
                if b["count"]:
                    intraday_points.append({
                        "timestamp": ts,
                        "avg_score": round(b["sum_score"] / b["count"], 4),
                        "dimensions": {},
                        "symbol_count": b["count"],
                    })
        except Exception as exc:
            logger.warning(f"intraday trend fallback: {exc}")

        return {"daily": daily_points, "intraday": intraday_points}

    async def get_market_snapshot(
        self,
        db: AsyncSession,
        window_daily: int = 30,
        window_intraday: str = "24h",
        symbol: Optional[str] = None,
        snapshot_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compose the unified snapshot response (FR1).

        When snapshot_id is provided and present in the cache, return it
        byte-consistent so the slider replays history deterministically.

        When no snapshot_id is provided, we also try a stable "latest" cache
        key so repeated requests for the current view hit cache within TTL.
        """
        if snapshot_id:
            cached = await self._cache_get(f"snapshot:{snapshot_id}")
            if cached and isinstance(cached, dict):
                return cached

        now_utc = datetime.now(timezone.utc)

        # Stable cache key for the "latest" snapshot (same params → same key)
        latest_cache_key = None
        if not snapshot_id:
            latest_cache_key = f"snapshot:latest:{window_daily}:{window_intraday}:{symbol or 'market'}"
            cached_latest = await self._cache_get(latest_cache_key)
            if cached_latest and isinstance(cached_latest, dict):
                return cached_latest

        daily = await self._resolve_tier_root(db, SnapshotTier.DAILY, symbol=symbol)
        hourly = await self._resolve_tier_root(db, SnapshotTier.HOURLY, symbol=symbol)
        if not hourly and daily:
            hourly = TierRoot(tier="hourly", effective_at=daily.effective_at, scores=daily.scores)
        if not daily:
            daily = TierRoot(
                tier="daily",
                effective_at=_floor_to_day(now_utc),
                scores={"overall": 0.0, "dimensions": {}, "sub_dimensions": {}, "aspects": {}, "sub_aspects": {}},
            )
        if not hourly:
            hourly = TierRoot(
                tier="hourly",
                effective_at=_floor_to_hour(now_utc),
                scores={"overall": 0.0, "dimensions": {}, "sub_dimensions": {}, "aspects": {}, "sub_aspects": {}},
            )
        current = await self._resolve_current(db, symbol=symbol)

        snapshot_id_val = snapshot_id or str(uuid.uuid4())
        deltas = self._build_deltas(daily, hourly, current)

        weights, weight_trends, weight_deltas = await self._build_weights(db, days=window_daily)
        trends = await self._build_trends(
            db, window_daily=window_daily, window_intraday=window_intraday, symbol=symbol
        )

        universe_total = await self._active_assets_count(db)

        def _tier_scores(tr: TierRoot) -> Dict[str, Any]:
            return {
                "overall": tr.scores.get("overall"),
                "dimensions": tr.scores.get("dimensions") or {},
                "sub_dimensions": tr.scores.get("sub_dimensions") or {},
                "aspects": tr.scores.get("aspects") or {},
                "sub_aspects": tr.scores.get("sub_aspects") or {},
            }

        payload: Dict[str, Any] = {
            "snapshotId": snapshot_id_val,
            "tier": current.tier,
            "effectiveAt": _iso(current.effective_at),
            "fetchedAt": utc_now_iso(),
            "scores": {
                "daily": _tier_scores(daily),
                "hourly": _tier_scores(hourly),
                "current": _tier_scores(current),
            },
            "deltas": deltas,
            "weights": weights,
            "weightTrends": weight_trends,
            "weightDeltas": weight_deltas,
            "trends": trends,
            "universe": {"total": universe_total, "market": "NASDAQ"},
        }
        if symbol:
            payload["symbol"] = symbol.upper()

        # cache
        try:
            tier_ttl = {"daily": 86400 * 30, "hourly": 7200, "current": 300}.get(current.tier, 300)
            await self._cache_set(f"snapshot:{snapshot_id_val}", payload, ttl_seconds=tier_ttl)
            if latest_cache_key:
                await self._cache_set(latest_cache_key, payload, ttl_seconds=300)
        except Exception:  # pragma: no cover
            pass

        return payload

    async def enumerate_snapshots(
        self,
        db: AsyncSession,
        hourly_limit: int = 168,
        daily_limit: int = 365,
    ) -> List[Dict[str, Any]]:
        """Return recent hourly + daily snapshot entries for slider."""
        entries: List[Dict[str, Any]] = []

        now = datetime.now(timezone.utc)

        # Hourly synthetic entries (last N hours)
        for i in range(hourly_limit, 0, -1):
            ts = _floor_to_hour(now) - timedelta(hours=i)
            entries.append({
                "snapshotId": None,
                "tier": "hourly",
                "effectiveAt": _iso(ts),
                "label": ts.strftime("%Y-%m-%d %H:00 UTC"),
                "symbolCount": None,
            })

        # Daily synthetic entries (last N days)
        for i in range(daily_limit, 0, -1):
            ts = _floor_to_day(now) - timedelta(days=i)
            entries.append({
                "snapshotId": None,
                "tier": "daily",
                "effectiveAt": _iso(ts),
                "label": ts.strftime("%Y-%m-%d (daily)"),
                "symbolCount": None,
            })

        return entries
