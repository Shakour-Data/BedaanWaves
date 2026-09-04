"""HierarchicalScoreTrendService

Aggregates the per-asset ``RawPerformanceScore`` rows into a daily series of
per-sub-dimension, per-aspect, and per-sub-aspect market-wide averages. This
powers the secondary line/column charts on the dashboard (charts #6, #7, #8,
#10, #11, #12 in the project specification).

The aggregator walks a window of ``captured_at`` timestamps, groups by date,
and averages each metric key found in the ``sub_dimension_scores``,
``aspect_scores``, and ``sub_aspect_scores`` JSONB columns. The result mirrors
the structure produced by ``MarketScoreTrendService`` for the top-level
dimension series so the frontend can use the same chart components.

No schema changes are required: ``raw_performance_scores`` is already populated
by the daily scoring pipeline. Windows that contain no captured rows simply
return an empty series (the chart falls back to "No trend data available").
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker
from app.models.models import Asset, RawPerformanceScore
from app.services.core import BaseService


logger = logging.getLogger(__name__)


# Map score-json keys -> (level, parent)
# The "parent" is the key at the level above (None for sub-dimensions). This is
# used both for filtering and for the response metadata so the frontend can
# build chart legends without re-deriving the hierarchy.
SUB_DIMENSION_TO_PARENT: Dict[str, str] = {
    "fundamental_price_history": "fundamental",
    "fundamental_ohlcv": "fundamental",
    "fundamental_corporate_actions": "fundamental",
    "technical_moving_averages": "technical",
    "technical_momentum": "technical",
    "technical_volatility": "technical",
    "technical_volume": "technical",
    "technical_trend": "technical",
    "sentiment_news_sentiment": "sentiment",
    "sentiment_social_sentiment": "sentiment",
    "sentiment_analyst_sentiment": "sentiment",
    "risk_beta": "risk",
    "risk_var": "risk",
    "risk_volatility": "risk",
    "risk_drawdown": "risk",
    "macro_interest_rates": "macro",
    "macro_inflation": "macro",
    "macro_gdp": "macro",
    "ai_signal_quality": "ai",
    "ai_model_confidence": "ai",
}


def _is_sub_dimension_key(key: str) -> bool:
    """Heuristic: a sub-dimension key is ``<parent>_<sub>``.

    The existing ``RawPerformanceScore`` rows use a flat naming convention
    (e.g. ``fundamental_price_history``) so we can identify level-2 keys by
    counting underscores. This avoids accidentally treating aspect names like
    ``fundamental_aspect_1`` as sub-dimensions even though they also have
    two underscores.
    """
    if key not in SUB_DIMENSION_TO_PARENT:
        return False
    parts = key.split("_")
    # sub-dim keys: ``fundamental_price_history`` (3 parts)
    return len(parts) == 3


def _is_aspect_key(key: str) -> bool:
    """Aspect keys follow the ``<dimension>_<subdim>_aspect_<n>`` pattern."""
    parts = key.split("_")
    if len(parts) < 4 or "aspect" not in parts:
        return False
    return key.endswith("_aspect_1") or key.endswith("_aspect_2")


def _aspect_parent(key: str) -> Optional[str]:
    """Return the parent sub-dimension key for an aspect key, or None."""
    parts = key.split("_")
    if len(parts) < 4 or "aspect" not in parts:
        return None
    idx = parts.index("aspect")
    if idx < 1:
        return None
    return "_".join(parts[:idx])


def _is_sub_aspect_key(key: str) -> bool:
    """Sub-aspect keys are anything that isn't a dimension / sub-dim / aspect."""
    if _is_sub_dimension_key(key) or _is_aspect_key(key):
        return False
    # The known top-level dimension names. Anything else under a known prefix
    # is treated as a sub-aspect.
    if not any(key.startswith(f"{d}_") for d in (
        "fundamental", "technical", "sentiment", "risk", "macro", "ai"
    )):
        return False
    return True


def _sub_aspect_parent(key: str) -> Optional[str]:
    """Return parent aspect key for a sub-aspect, or None.

    We don't have a ground-truth parent map for sub-aspects, so we use the
    ``<dim>_<subdim>`` prefix as a best-effort parent. The frontend just
    uses this for filtering by parent aspect, so a slightly loose mapping
    is acceptable.
    """
    parts = key.split("_")
    if len(parts) < 4:
        return None
    return "_".join(parts[:3])


class HierarchicalScoreTrendService(BaseService):
    """Aggregates sub-dim / aspect / sub-aspect score trends.

    All public methods follow the same ``days / market / latest / end_date``
    contract as :class:`MarketScoreTrendService` so the dashboard endpoints
    stay consistent.
    """

    def __init__(self, service_name: str = "HierarchicalScoreTrendService") -> None:
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("HierarchicalScoreTrendService initialized")

    async def shutdown(self) -> None:
        self.logger.info("HierarchicalScoreTrendService shutdown")

    async def _latest_capture_date(
        self,
        market: str,
        db: AsyncSession,
    ) -> Optional[date]:
        """Return the most recent date with a ``RawPerformanceScore`` row."""
        result = await db.execute(
            select(func.max(func.date(RawPerformanceScore.captured_at)))
            .join(Asset, Asset.id == RawPerformanceScore.asset_id, isouter=True)
            .where(
                and_(
                    RawPerformanceScore.data_quality.in_(("VALIDATED", "CLEANED")),
                    (Asset.market == market) | (Asset.market.is_(None)),
                )
            )
        )
        value = result.scalar_one_or_none()
        return value

    async def get_trend(
        self,
        level: str,
        days: int = 30,
        market: str = "NASDAQ",
        parent: Optional[str] = None,
        latest: bool = False,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Aggregate sub-dim / aspect / sub-aspect scores for a window.

        Args:
            level:    One of ``sub_dimension``, ``aspect``, ``sub_aspect``.
            days:     Lookback window length (default 30).
            market:   Market code (default ``NASDAQ``).
            parent:   Optional parent key to filter to (dimension for
                      sub_dimensions, sub_dim key for aspects, aspect key
                      for sub_aspects).
            latest:   When ``True`` the window ends on the most recent
                      capture date instead of today.
            end_date: Explicit end date (overrides ``latest``).

        Returns:
            ``{status, level, days, market, count, latest_date, series}`` where
            ``series`` is a list of ``{date, metrics: {key: avg_score},
            metric_changes: {key: delta}}``.
        """
        if level not in ("sub_dimension", "aspect", "sub_aspect"):
            raise ValueError(f"Unsupported level: {level}")

        async with async_session_maker() as session:
            if latest:
                effective_end = await self._latest_capture_date(market, session)
            else:
                effective_end = end_date or datetime.now(timezone.utc).date()

            if effective_end is None:
                return self._empty(level, days, market)

            start_date = effective_end - timedelta(days=days - 1)
            rows = await self._aggregate_window(
                session, level=level, market=market,
                start_date=start_date, end_date=effective_end, parent=parent,
            )

        latest_date = rows[-1]["date"] if rows else None
        return {
            "status": "success",
            "level": level,
            "days": days,
            "market": market,
            "parent": parent,
            "count": len(rows),
            "latest_date": latest_date,
            "series": rows,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _empty(level: str, days: int, market: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "level": level,
            "days": days,
            "market": market,
            "parent": None,
            "count": 0,
            "latest_date": None,
            "series": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _aggregate_window(
        self,
        db: AsyncSession,
        level: str,
        market: str,
        start_date: date,
        end_date: date,
        parent: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Read ``RawPerformanceScore`` rows in the window and aggregate.

        We pull the raw JSONB columns and average in Python because the keys
        inside are dynamic. PostgreSQL ``jsonb_each_text`` would also work
        but adds coupling; the dataset for one window is bounded (≤ 30 days)
        so a Python pass is fine.
        """
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

        query = (
            select(
                func.date(RawPerformanceScore.captured_at).label("capture_date"),
                RawPerformanceScore.sub_dimension_scores,
                RawPerformanceScore.aspect_scores,
                RawPerformanceScore.sub_aspect_scores,
            )
            .where(
                and_(
                    RawPerformanceScore.captured_at >= start_dt,
                    RawPerformanceScore.captured_at < end_dt,
                    RawPerformanceScore.data_quality.in_(("VALIDATED", "CLEANED")),
                )
            )
            .join(Asset, Asset.id == RawPerformanceScore.asset_id, isouter=True)
            .where((Asset.market == market) | (Asset.market.is_(None)))
            .order_by(func.date(RawPerformanceScore.captured_at).asc())
        )

        result = await db.execute(query)
        rows = result.all()

        # Per-date accumulators
        by_date: Dict[date, Dict[str, List[float]]] = {}

        column_name = {
            "sub_dimension": "sub_dimension_scores",
            "aspect": "aspect_scores",
            "sub_aspect": "sub_aspect_scores",
        }[level]

        parent_filter = {
            "sub_dimension": lambda k: parent is None or SUB_DIMENSION_TO_PARENT.get(k) == parent,
            "aspect": lambda k: parent is None or _aspect_parent(k) == parent,
            "sub_aspect": lambda k: parent is None or _sub_aspect_parent(k) == parent,
        }[level]

        level_filter = {
            "sub_dimension": _is_sub_dimension_key,
            "aspect": _is_aspect_key,
            "sub_aspect": _is_sub_aspect_key,
        }[level]

        for row in rows:
            capture_date = row.capture_date
            if isinstance(capture_date, datetime):
                capture_date = capture_date.date()

            scores = row._mapping[column_name] or {}
            bucket = by_date.setdefault(capture_date, {})

            for raw_key, raw_value in scores.items():
                if not level_filter(raw_key):
                    continue
                if not parent_filter(raw_key):
                    continue
                try:
                    value = float(raw_value)
                except (TypeError, ValueError):
                    continue
                bucket.setdefault(raw_key, []).append(value)

        series: List[Dict[str, Any]] = []
        for capture_date in sorted(by_date.keys()):
            metrics = {
                key: round(sum(values) / len(values), 2)
                for key, values in by_date[capture_date].items()
                if values
            }
            series.append({
                "date": capture_date.isoformat(),
                "metrics": metrics,
            })

        # Day-over-day deltas
        for i, point in enumerate(series):
            if i == 0:
                point["metric_changes"] = {k: 0.0 for k in point["metrics"]}
                continue
            prev = series[i - 1]["metrics"]
            point["metric_changes"] = {
                k: round(point["metrics"].get(k, 0.0) - prev.get(k, 0.0), 2)
                for k in point["metrics"]
            }

        return series
