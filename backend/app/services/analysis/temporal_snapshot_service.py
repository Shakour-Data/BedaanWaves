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
from app.models.models import Asset, ScoreHistory
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

        snap_row = None
        snap_q = (
            select(ScoringSnapshot)
            .where(ScoringSnapshot.snapshot_tier == tier.value)
            .order_by(desc(ScoringSnapshot.effective_at))
        )
        if asset_id is not None:
            snap_q = snap_q.where(ScoringSnapshot.asset_id == asset_id)
        snap_row = (await db.execute(snap_q.limit(1))).scalar_one_or_none()

        # Resolve the latest ScoreHistory date for the requested universe. This
        # is the authoritative fallback when partitioned ScoringSnapshot rows
        # have not been materialized yet.
        sh_date_q = (
            select(func.max(ScoreHistory.date))
            .join(Asset, Asset.id == ScoreHistory.asset_id)
            .where(
                and_(
                    Asset.active,
                    Asset.market == "NASDAQ",
                    Asset.asset_class.in_(["EQUITY", "ETF"]),
                )
            )
        )
        if asset_id is not None:
            sh_date_q = sh_date_q.where(ScoreHistory.asset_id == asset_id)
        sh_date_res = await db.execute(sh_date_q)
        sh_effective_date = sh_date_res.scalar_one_or_none()

        if sh_effective_date is None:
            if not snap_row or not snap_row.effective_at:
                return None
            effective_at = snap_row.effective_at
            scores: dict[str, Any] = {
                "overall": _to_float(snap_row.score),
                "dimension": {},
                "dimensions": {},
                "sub_dimension": {},
                "sub_dimensions": {},
                "aspect": {},
                "aspects": {},
                "sub_aspect": {},
                "sub_aspects": {},
            }
            return TierRoot(tier=tier.value, effective_at=effective_at, scores=scores)

        sh_q = (
            select(ScoreHistory, Asset)
            .join(Asset, Asset.id == ScoreHistory.asset_id)
            .where(
                and_(
                    Asset.active,
                    Asset.market == "NASDAQ",
                    Asset.asset_class.in_(["EQUITY", "ETF"]),
                    ScoreHistory.date == sh_effective_date,
                )
            )
        )
        if asset_id is not None:
            sh_q = sh_q.where(ScoreHistory.asset_id == asset_id)
        sh_res = await db.execute(sh_q)
        sh_rows = sh_res.all()

        effective_at = datetime.combine(sh_effective_date, datetime.min.time(), tzinfo=UTC)
        if snap_row and snap_row.effective_at:
            effective_at = snap_row.effective_at

        scores: dict[str, Any] = {
            "overall": None,
            "dimension": {},
            "dimensions": {},
            "sub_dimension": {},
            "sub_dimensions": {},
            "aspect": {},
            "aspects": {},
            "sub_aspect": {},
            "sub_aspects": {},
        }
        overall_values: list[float] = []
        level_values: dict[str, dict[str, list[float]]] = {
            "dimension": {},
            "sub_dimension": {},
            "aspect": {},
            "sub_aspect": {},
        }
        level_columns = {
            "dimension": "dimension_scores",
            "sub_dimension": "sub_dimension_scores",
            "aspect": "aspect_scores",
            "sub_aspect": "sub_aspect_scores",
        }

        symbol_map: dict[str, dict[str, Any]] = {}
        for sh, asset in sh_rows:
            overall = _to_float(sh.overall_score)
            if overall is not None:
                overall_values.append(overall)
            for level, column in level_columns.items():
                values = getattr(sh, column, None) or {}
                if not isinstance(values, dict):
                    continue
                target = level_values[level]
                for key, value in values.items():
                    numeric = _to_float(value)
                    if numeric is None:
                        continue
                    target.setdefault(str(key), []).append(numeric)

            symbol_map[asset.symbol] = {
                "overall": overall,
                "grade": sh.grade,
                "dimension": dict(sh.dimension_scores) if sh.dimension_scores else {},
            }

        if overall_values:
            scores["overall"] = round(sum(overall_values) / len(overall_values), 4)
        for level, values_by_key in level_values.items():
            averages = {
                key: round(sum(values) / len(values), 4)
                for key, values in values_by_key.items()
                if values
            }
            scores[level] = averages
            scores[f"{level}s"] = averages

        scores["symbol_map"] = symbol_map
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
            result["symbol_map"] = tr.scores.get("symbol_map", {})
            return result

        # Compute best/worst symbols from daily tier's symbol_map
        daily_symbol_map = daily.scores.get("symbol_map", {})
        best_symbol = None
        worst_symbol = None
        if daily_symbol_map:
            sorted_symbols = sorted(
                [(sym, data.get("overall")) for sym, data in daily_symbol_map.items() if data.get("overall") is not None],
                key=lambda x: x[1],
                reverse=True
            )
            if sorted_symbols:
                best_symbol = sorted_symbols[0][0]
                worst_symbol = sorted_symbols[-1][0]

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
            "best_symbol": best_symbol,
            "worst_symbol": worst_symbol,
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
