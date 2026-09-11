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
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import utc_now_iso
from app.models.models import Asset, RawPerformanceScore, ScoreHistory
from app.models.scoring_snapshot import ScoringSnapshot, SnapshotTier
from app.services.analysis.coefficient_history_service import (
    DIMENSION_KEYS,
    CoefficientHistoryService,
)
from app.services.analysis.hierarchy import (
    tier_scores_with_aliases,
)
from app.services.analysis.hierarchical_score_trend_service import HierarchicalScoreTrendService
from app.services.analysis.market_score_trend_service import MarketScoreTrendService

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
    scores: dict[str, Any]  # nested dict of overall, dimensions, sub_dimensions, ...


def _floor_to_hour(dt: datetime) -> datetime:
    """Return dt floored to the previous top-of-hour, UTC timezone-aware."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.replace(minute=0, second=0, microsecond=0)


def _floor_to_day(dt: datetime) -> datetime:
    """Return dt floored to 00:00 UTC of the same calendar day."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _iso(ts: datetime | None) -> str:
    if ts is None:
        return ""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    else:
        ts = ts.astimezone(UTC)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _compute_delta(a: float | None, b: float | None) -> tuple[float | None, float | None]:
    """Return (delta_abs, delta_pct) where delta = a - b (a is 'newer')."""
    if a is None or b is None:
        return None, None
    delta = round(a - b, 4)
    if abs(b) < 1e-9:
        pct = 0.0 if abs(delta) < 1e-9 else None
    else:
        pct = round(delta / b * 100.0, 4)
    return delta, pct


def _to_float(value: Any) -> float | None:
    """Normalize database numerics without rejecting Decimal values."""
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def _dict_delta(new_map: dict | None, old_map: dict | None) -> dict[str, tuple[float | None, float | None]]:
    out: dict[str, tuple[float | None, float | None]] = {}
    if not new_map or not old_map:
        return out
    for key in set(new_map.keys()) | set(old_map.keys()):
        a = float(new_map[key]) if new_map.get(key) is not None else None
        b = float(old_map[key]) if old_map.get(key) is not None else None
        out[key] = _compute_delta(a, b)
    return out


def _plural_to_singular(plural: str) -> str:
    """Map a plural tier key to its singular form."""
    return {
        "dimensions": "dimension",
        "sub_dimensions": "sub_dimension",
        "aspects": "aspect",
        "sub_aspects": "sub_aspect",
    }.get(plural, plural.rstrip("s"))


class TemporalSnapshotService:
    """Service that composes 3-tier snapshots into a unified response."""

    def __init__(self):
        self.cache: Any | None = None
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
    async def _cache_get(self, key: str) -> Any | None:
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
                    Asset.active,
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
        symbol: str | None = None,
    ) -> TierRoot | None:
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
        effective_at: datetime | None = None
        if snap_row and snap_row.effective_at:
            effective_at = snap_row.effective_at

        # Aggregate from ScoreHistory (last matching date)
        sh_effective_date = None
        sh_q = (
            select(ScoreHistory, Asset)
            .join(Asset, Asset.id == ScoreHistory.asset_id)
            .where(
                and_(
                    Asset.active,
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

        # Aggregate from RawPerformanceScore for sub-dimension / aspect / sub-aspect
        # First get the latest captured_at per asset, then get the JSON columns
        rps_effective_date = None
        rps_subq = (
            select(
                RawPerformanceScore.asset_id,
                func.max(func.date(RawPerformanceScore.captured_at)).label("max_date"),
            )
            .join(Asset, Asset.id == RawPerformanceScore.asset_id, isouter=True)
            .where(
                and_(
                    Asset.active,
                    Asset.market == "NASDAQ",
                    Asset.asset_class.in_(["EQUITY", "ETF"]),
                    RawPerformanceScore.data_quality.in_(("VALIDATED", "CLEANED")),
                )
            )
            .group_by(RawPerformanceScore.asset_id)
            .subquery()
        )
        
        rps_q = (
            select(
                rps_subq.c.max_date,
                RawPerformanceScore.sub_dimension_scores,
                RawPerformanceScore.aspect_scores,
                RawPerformanceScore.sub_aspect_scores,
            )
            .join(
                rps_subq,
                and_(
                    RawPerformanceScore.asset_id == rps_subq.c.asset_id,
                    func.date(RawPerformanceScore.captured_at) == rps_subq.c.max_date,
                )
            )
            .where(RawPerformanceScore.data_quality.in_(("VALIDATED", "CLEANED")))
        )
        if symbol:
            asset_q = select(Asset.id).where(func.lower(Asset.symbol) == func.lower(symbol))
            asset_res = await db.execute(asset_q)
            asset_id = asset_res.scalar_one_or_none()
            if asset_id:
                rps_q = rps_q.where(RawPerformanceScore.asset_id == asset_id).limit(1)
        else:
            rps_q = rps_q.limit(500)

        rps_res = await db.execute(rps_q)
        rps_rows = rps_res.all()

        # Aggregate RawPerformanceScore JSON columns into market means
        def _avg_jsonb(rows: list, col_name: str) -> dict[str, float]:
            sums: dict[str, list[float]] = {}
            for row in rows:
                col_val = getattr(row, col_name, None) or {}
                if not isinstance(col_val, dict):
                    col_val = getattr(row, "_mapping", {}).get(col_name, {}) or {}
                for k, v in col_val.items():
                    try:
                        sums.setdefault(k, []).append(float(v))
                    except (TypeError, ValueError):
                        continue
            return {k: round(sum(vs) / len(vs), 4) for k, vs in sums.items() if vs}

        sub_dimension_scores = _avg_jsonb(rps_rows, "sub_dimension_scores")
        aspect_scores = _avg_jsonb(rps_rows, "aspect_scores")
        sub_aspect_scores = _avg_jsonb(rps_rows, "sub_aspect_scores")

        if rps_rows and rps_rows[0].max_date:
            rps_effective_date = rps_rows[0].max_date

        scores: dict[str, Any] = {"dimension": {}, "dimensions": {}}
        overall_list: list[float] = []
        dim_map: dict[str, list[float]] = {d: [] for d in CANONICAL_DIMS}

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
                tzinfo=UTC,
            )

        # Market-level aggregation: use mean
        if overall_list:
            scores["overall"] = round(sum(overall_list) / len(overall_list), 4)
        for d, vs in dim_map.items():
            if vs:
                dim_val = round(sum(vs) / len(vs), 4)
                scores["dimension"][d] = dim_val
                scores["dimensions"][d] = dim_val

        # (Optional) Pull sub-dim / aspect / sub-aspect from snap_row.extra_fields
        # if present; otherwise keep empty dict so UI renders — never None.
        # Use RawPerformanceScore aggregation as the authoritative source.
        if snap_row and snap_row.extra_fields:
            ef = snap_row.extra_fields if isinstance(snap_row.extra_fields, dict) else {}
            for level in ("sub_dimensions", "aspects", "sub_aspects",
                          "sub_dimension", "aspect", "sub_aspect"):
                val = ef.get(level)
                if isinstance(val, dict) and val:
                    scores.setdefault(level, {}).update({k: round(float(v), 4) for k, v in val.items()})

        scores.setdefault("sub_dimension", sub_dimension_scores)
        scores.setdefault("sub_dimensions", sub_dimension_scores)
        scores.setdefault("aspect", aspect_scores)
        scores.setdefault("aspects", aspect_scores)
        scores.setdefault("sub_aspect", sub_aspect_scores)
        scores.setdefault("sub_aspects", sub_aspect_scores)

        if not scores.get("overall") and snap_row:
            scores["overall"] = float(snap_row.score) if snap_row.score else None

        if not effective_at:
            return None

        return TierRoot(tier=tier.value, effective_at=effective_at, scores=scores)

    async def _resolve_current(
        self,
        db: AsyncSession,
        symbol: str | None = None,
    ) -> TierRoot:
        """Current = freshest available (hourly if <5 min old, else latest daily)."""
        now = datetime.now(UTC)
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
            scores={"overall": 0.0, "dimension": {}, "dimensions": {}, "sub_dimension": {}, "sub_dimensions": {}, "aspect": {}, "aspects": {}, "sub_aspect": {}, "sub_aspects": {}},
        )

    def _build_deltas(self, daily: TierRoot, hourly: TierRoot, current: TierRoot) -> dict[str, Any]:
        def _frame(newer: TierRoot, older: TierRoot) -> dict[str, Any]:
            overall_abs, overall_pct = _compute_delta(
                float(newer.scores.get("overall")) if newer.scores.get("overall") is not None else None,
                float(older.scores.get("overall")) if older.scores.get("overall") is not None else None,
            )

            def _deltas_for(plat: str) -> dict[str, Any]:
                singular = _plural_to_singular(plat)
                newer_map = newer.scores.get(plat) or newer.scores.get(singular) or {}
                older_map = older.scores.get(plat) or older.scores.get(singular) or {}
                d = _dict_delta(newer_map, older_map)
                return {k: {"delta": vabs, "delta_pct": vpct} for k, (vabs, vpct) in d.items()}

            dim_frame = _deltas_for("dimensions")
            sub_dim_frame = _deltas_for("sub_dimensions")
            aspect_frame = _deltas_for("aspects")
            sub_aspect_frame = _deltas_for("sub_aspects")

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

    async def _build_weights(self, db: AsyncSession, days: int = 30) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        try:
            svc = CoefficientHistoryService()
            result = await svc.get_history(days=days, market="NASDAQ", level="dimension", latest=True)
            series: list[dict] = result.get("series", []) or []

            weight_snapshot: dict[str, Any] = {}
            weight_trends: list[dict[str, Any]] = []
            weight_deltas: list[dict[str, Any]] = []

            current_weights: dict[str, float] = {}
            if series:
                last = series[-1]
                metrics = last.get("metrics") or {}
                for k in DIMENSION_KEYS:
                    v = metrics.get(k)
                    if isinstance(v, (int, float)):
                        current_weights[k] = float(v)

            weight_snapshot["dimension"] = current_weights
            # sub_dimension / aspect / sub_aspect weights from canonical hierarchy
            from app.services.analysis.hierarchy import (
                V2_SUB_DIMENSIONS,
            )
            weight_snapshot["dimensions"] = current_weights
            weight_snapshot["sub_dimension"] = {k: 1.0 / max(1, len(V2_SUB_DIMENSIONS)) for k in V2_SUB_DIMENSIONS}
            weight_snapshot["sub_dimensions"] = weight_snapshot["sub_dimension"]
            weight_snapshot["aspect"] = {}
            weight_snapshot["sub_aspect"] = {}
            weight_snapshot["aspects"] = {}
            weight_snapshot["sub_aspects"] = {}

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
                {"dimension": {}, "dimensions": {}, "sub_dimension": {}, "sub_dimensions": {}, "aspect": {}, "aspects": {}, "sub_aspect": {}, "sub_aspects": {}},
                [],
                [],
            )

    async def _build_trends(
        self,
        db: AsyncSession,
        window_daily: int = 30,
        window_intraday: str = "24h",
        symbol: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        daily_points: list[dict[str, Any]] = []
        intraday_points: list[dict[str, Any]] = []

        # Fetch all hierarchical trends in parallel
        hierarchical_trends: dict[str, list[dict[str, Any]]] = {}
        for level in ("sub_dimension", "aspect", "sub_aspect"):
            try:
                svc = HierarchicalScoreTrendService()
                result = await svc.get_trend(
                    level=level, days=window_daily, market="NASDAQ", latest=True, db=db
                )
                hierarchical_trends[level] = result.get("series", [])
            except Exception as exc:
                logger.warning(f"hierarchical trend {level} fallback: {exc}")
                hierarchical_trends[level] = []

        # Build a map: date -> {level: metrics}
        hierarchical_by_date: dict[str, dict[str, dict[str, float]]] = {}
        for level, series in hierarchical_trends.items():
            for pt in series:
                date_str = str(pt.get("date"))
                if date_str not in hierarchical_by_date:
                    hierarchical_by_date[date_str] = {}
                hierarchical_by_date[date_str][level] = pt.get("metrics", {})

        # Daily - from MarketScoreTrendService (dimension level) + hierarchical trends
        try:
            svc = MarketScoreTrendService()
            data = await svc.get_trend(days=window_daily, market="NASDAQ", db=db)
            for pt in data or []:
                date_str = str(pt.get("date"))
                level_scores: dict[str, float] = dict(pt.get("avg_dimensions") or {})
                # Merge hierarchical scores for this date
                if date_str in hierarchical_by_date:
                    for level_metrics in hierarchical_by_date[date_str].values():
                        level_scores.update(level_metrics)
                daily_points.append({
                    "date": date_str,
                    "effective_at": date_str,
                    "overall": float(pt.get("avg_score")) if isinstance(pt.get("avg_score"), (int, float)) else None,
                    "level_scores": level_scores,
                    "count": int(pt.get("symbol_count")) if pt.get("symbol_count") is not None else None,
                })
        except Exception as exc:
            logger.warning(f"market daily trend fallback: {exc}")

        # Intraday: reuse ScoringSnapshot hourly last 24 entries
        try:
            hours: dict[str, Any] = {
                "6h": 6,
                "24h": 24,
                "7d": 24 * 7,
            }
            n = hours.get(window_intraday, 24)
            now = datetime.now(UTC)
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
            bucket: dict[str, dict[str, Any]] = {}
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
                        "date": ts,
                        "effective_at": ts,
                        "overall": round(b["sum_score"] / b["count"], 4),
                        "level_scores": {},
                        "count": b["count"],
                    })
        except Exception as exc:
            logger.warning(f"intraday trend fallback: {exc}")

        return {"daily": daily_points, "intraday": intraday_points}

    async def get_market_snapshot(
        self,
        db: AsyncSession,
        window_daily: int = 30,
        window_intraday: str = "24h",
        symbol: str | None = None,
        snapshot_id: str | None = None,
    ) -> dict[str, Any]:
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

        now_utc = datetime.now(UTC)

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
                scores={"overall": 0.0, "dimension": {}, "dimensions": {}, "sub_dimension": {}, "sub_dimensions": {}, "aspect": {}, "aspects": {}, "sub_aspect": {}, "sub_aspects": {}},
            )
        if not hourly:
            hourly = TierRoot(
                tier="hourly",
                effective_at=_floor_to_hour(now_utc),
                scores={"overall": 0.0, "dimension": {}, "dimensions": {}, "sub_dimension": {}, "sub_dimensions": {}, "aspect": {}, "aspects": {}, "sub_aspect": {}, "sub_aspects": {}},
            )
        current = await self._resolve_current(db, symbol=symbol)

        snapshot_id_val = snapshot_id or str(uuid.uuid4())
        deltas = self._build_deltas(daily, hourly, current)

        weights, weight_trends, weight_deltas = await self._build_weights(db, days=window_daily)
        trends = await self._build_trends(
            db, window_daily=window_daily, window_intraday=window_intraday, symbol=symbol
        )

        universe_total = await self._active_assets_count(db)

        def _tier_scores(tr: TierRoot) -> dict[str, Any]:
            result = tier_scores_with_aliases(
                dimension_scores=tr.scores.get("dimensions") or tr.scores.get("dimension") or {},
                sub_dimension_scores=tr.scores.get("sub_dimensions") or tr.scores.get("sub_dimension") or {},
                aspect_scores=tr.scores.get("aspects") or tr.scores.get("aspect") or {},
                sub_aspect_scores=tr.scores.get("sub_aspects") or tr.scores.get("sub_aspect") or {},
            )
            result["overall"] = tr.scores.get("overall")
            return result

        payload: dict[str, Any] = {
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
    ) -> list[dict[str, Any]]:
        """Return recent hourly + daily snapshot entries for slider."""
        entries: list[dict[str, Any]] = []

        now = datetime.now(UTC)

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
