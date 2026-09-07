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
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import utc_now_iso
from app.db.base import async_session_maker
from app.models.models import Asset, RawPerformanceScore
from app.services.analysis.hierarchy import (
    ASPECT_TO_PARENT,
    SUB_ASPECT_TO_PARENT,
    SUB_DIMENSION_TO_PARENT,
    is_aspect_key,
    is_sub_aspect_key,
    is_sub_dimension_key,
)
from app.services.core import BaseService

logger = logging.getLogger(__name__)


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
    ) -> date | None:
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
        parent: str | None = None,
        latest: bool = False,
        end_date: date | None = None,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
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
            db:       Optional pre-existing session (used by tests / route
                      handlers to share the request-scoped session).

        Returns:
            ``{status, level, days, market, count, latest_date, series}`` where
            ``series`` is a list of ``{date, metrics: {key: avg_score},
            metric_changes: {key: delta}}``.
        """
        if level not in ("sub_dimension", "aspect", "sub_aspect"):
            raise ValueError(f"Unsupported level: {level}")

        if db is None:
            async with async_session_maker() as session:
                return await self._get_trend_impl(
                    level=level, days=days, market=market, parent=parent,
                    latest=latest, end_date=end_date, db=session,
                )
        return await self._get_trend_impl(
            level=level, days=days, market=market, parent=parent,
            latest=latest, end_date=end_date, db=db,
        )

    async def _get_trend_impl(
        self,
        level: str,
        days: int,
        market: str,
        parent: str | None,
        latest: bool,
        end_date: date | None,
        db: AsyncSession,
    ) -> dict[str, Any]:
        if latest:
            effective_end = await self._latest_capture_date(market, db)
        else:
            effective_end = end_date or datetime.now(UTC).date()

        if effective_end is None:
            return self._empty(level, days, market)

        start_date = effective_end - timedelta(days=days - 1)
        rows = await self._aggregate_window(
            db, level=level, market=market,
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
            "timestamp": utc_now_iso(),
        }

    @staticmethod
    def _empty(level: str, days: int, market: str) -> dict[str, Any]:
        return {
            "status": "success",
            "level": level,
            "days": days,
            "market": market,
            "parent": None,
            "count": 0,
            "latest_date": None,
            "series": [],
            "timestamp": utc_now_iso(),
        }

    async def _aggregate_window(
        self,
        db: AsyncSession,
        level: str,
        market: str,
        start_date: date,
        end_date: date,
        parent: str | None,
    ) -> list[dict[str, Any]]:
        """Read ``RawPerformanceScore`` rows in the window and aggregate.

        We pull the raw JSONB columns and average in Python because the keys
        inside are dynamic. PostgreSQL ``jsonb_each_text`` would also work
        but adds coupling; the dataset for one window is bounded (≤ 30 days)
        so a Python pass is fine.
        """
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC)

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
        by_date: dict[str, dict[str, list[float]]] = {}

        column_name = {
            "sub_dimension": "sub_dimension_scores",
            "aspect": "aspect_scores",
            "sub_aspect": "sub_aspect_scores",
        }[level]

        parent_map = {
            "aspect": ASPECT_TO_PARENT,
            "sub_aspect": SUB_ASPECT_TO_PARENT,
        }.get(level)

        def _parent_filter(key: str) -> bool:
            if parent is None:
                return True
            if parent_map is None:
                return SUB_DIMENSION_TO_PARENT.get(key) == parent
            return parent_map.get(key) == parent

        level_filter = {
            "sub_dimension": is_sub_dimension_key,
            "aspect": is_aspect_key,
            "sub_aspect": is_sub_aspect_key,
        }[level]

        symbol_counts: dict[str, int] = {}

        for row in rows:
            capture_date = getattr(row, "capture_date", None)
            if capture_date is None:
                capture_date = getattr(row, "day", None)
            if capture_date is None:
                continue
            if isinstance(capture_date, datetime):
                capture_date = capture_date.date()
            if hasattr(capture_date, "isoformat"):
                capture_date = capture_date.isoformat()

            if hasattr(row, "_mapping"):
                scores = row._mapping[column_name] or {}
            elif hasattr(row, "raw_scores"):
                scores = row.raw_scores
            else:
                scores = {}
            bucket = by_date.setdefault(capture_date, {})
            has_contributing_score = False

            for raw_key, raw_value in scores.items():
                if not level_filter(raw_key):
                    continue
                if not _parent_filter(raw_key):
                    continue
                try:
                    value = float(raw_value)
                except (TypeError, ValueError):
                    continue
                bucket.setdefault(raw_key, []).append(value)
                has_contributing_score = True

            if has_contributing_score:
                symbol_counts[capture_date] = symbol_counts.get(capture_date, 0) + 1

        series: list[dict[str, Any]] = []
        for capture_date in sorted(by_date.keys()):
            metrics = {
                key: round(sum(values) / len(values), 2)
                for key, values in by_date[capture_date].items()
                if values
            }
            date_str = capture_date if isinstance(capture_date, str) else capture_date.isoformat()
            series.append({
                "date": date_str,
                "metrics": metrics,
                "symbol_count": symbol_counts.get(capture_date, 0),
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
