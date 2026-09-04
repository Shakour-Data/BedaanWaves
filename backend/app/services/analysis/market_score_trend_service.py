"""MarketScoreTrendService

Aggregates the per-asset ``ScoreHistory`` rows into one ``MarketScoreTrend``
row per (date, market). The dashboard ``/dashboard/score-trend`` endpoint
reads from this precomputed table for O(1) chart rendering instead of doing
the same AVG/GROUP BY on every request.

Typical usage (called by the daily scheduler after ``DailyScoreRecalculation``):

    service = MarketScoreTrendService()
    await service.initialize()
    result = await service.compute_and_persist(market="NASDAQ")
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Numeric, and_, case as sa_case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.core import BaseService
from app.db.base import async_session_maker
from app.models.models import Asset, MarketScoreTrend, ScoreHistory


logger = logging.getLogger(__name__)


TREND_DIMENSIONS: tuple = (
    "fundamental",
    "technical",
    "sentiment",
    "risk",
    "macro",
    "ai",
)


class MarketScoreTrendService(BaseService):
    """Computes and persists daily market-wide score trend rows."""

    def __init__(self, service_name: str = "MarketScoreTrendService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        """No-op initializer kept for parity with other services."""
        self.logger.info("MarketScoreTrendService initialized")

    async def shutdown(self) -> None:
        """No-op shutdown kept for parity with other services."""
        self.logger.info("MarketScoreTrendService shutdown")

    async def compute_and_persist(
        self,
        target_date: Optional[date] = None,
        market: str = "NASDAQ",
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Aggregate ``ScoreHistory`` rows into ``market_score_trend``.

        Args:
            target_date: Last day in the window to populate (default: today UTC).
            market:      Market code to aggregate (default ``NASDAQ``).
            lookback_days: How many trailing days to populate, including
                           ``target_date`` (default 30).

        Returns:
            Summary dict with counts and the list of persisted rows.
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()

        start_date = target_date - timedelta(days=lookback_days - 1)
        self.logger.info(
            "MarketScoreTrendService: aggregating %s %s..%s (%d days)",
            market, start_date.isoformat(), target_date.isoformat(), lookback_days,
        )

        async with async_session_maker() as session:
            aggregated = await self._aggregate_window(
                session, market=market, start_date=start_date, end_date=target_date,
            )

            if not aggregated:
                self.logger.warning(
                    "MarketScoreTrendService: no ScoreHistory rows in window for %s",
                    market,
                )
                return {
                    "status": "completed",
                    "market": market,
                    "start_date": start_date.isoformat(),
                    "end_date": target_date.isoformat(),
                    "written": 0,
                    "days": 0,
                }

            await self._upsert_rows(session, market=market, rows=aggregated)
            await session.commit()

        self.logger.info(
            "MarketScoreTrendService: wrote %d rows for %s",
            len(aggregated), market,
        )
        return {
            "status": "completed",
            "market": market,
            "start_date": start_date.isoformat(),
            "end_date": target_date.isoformat(),
            "written": len(aggregated),
            "days": len(aggregated),
        }

    async def get_trend(
        self,
        days: int = 30,
        market: str = "NASDAQ",
        db: Optional[AsyncSession] = None,
        end_date: Optional[date] = None,
        latest: bool = False,
    ) -> List[Dict[str, Any]]:
        """Read the precomputed trend series for a market.

        Returns one dict per day ordered ascending by date. Each dict matches
        the shape produced by the on-the-fly aggregator (date, avg_score,
        avg_dimensions, symbol_count) so the endpoint can layer day-over-day
        deltas on top without further work.

        Args:
            days:     Lookback window length in days (default 30).
            market:   Market code (default ``NASDAQ``).
            db:       Optional injected session; otherwise a new one is opened.
            end_date: Explicit end date for the window. Takes precedence over
                      ``latest`` when supplied. When ``None`` the window
                      ends on ``today`` (server clock) unless ``latest`` is
                      ``True``.
            latest:   When ``True`` (and ``end_date`` is ``None``) the window
                      ends on the most recent date present in
                      ``market_score_trend`` (or ``score_history`` as a
                      fallback) rather than on ``today``. This ensures the
                      trend chart and the spider chart (which renders the
                      latest ``ScoreHistory`` date) display the same latest
                      data point.

        Returns:
            A list of daily aggregate dicts, ascending by date.
        """
        if days < 1:
            return []

        if end_date is not None:
            # An explicit ``end_date`` always wins, even when ``latest`` is
            # also requested. This guarantees that callers which already
            # resolved the "latest available date" (e.g. the spider chart
            # endpoint) can pin the trend window to that exact date and
            # never drift if the precomputed table lags.
            effective_end = end_date
        elif latest:
            effective_end = await self._latest_date(market, db)
        else:
            effective_end = datetime.now(timezone.utc).date()

        if effective_end is not None:
            cutoff = effective_end - timedelta(days=days - 1)
        else:
            cutoff = None

        async def _read(session: AsyncSession) -> List[Dict[str, Any]]:
            query = (
                MarketScoreTrend.__table__.select()
                .where(MarketScoreTrend.market == market)
            )
            if cutoff is not None:
                query = query.where(
                    and_(
                        MarketScoreTrend.date >= cutoff,
                        MarketScoreTrend.date <= effective_end,
                    )
                )
            query = query.order_by(MarketScoreTrend.date.asc())
            result = await session.execute(query)
            return list(result.mappings().all())

        if db is not None:
            rows = await _read(db)
        else:
            async with async_session_maker() as session:
                rows = await _read(session)

        series: List[Dict[str, Any]] = []
        for row in rows:
            series.append({
                "date": row["date"].isoformat(),
                "avg_score": float(row["avg_score"]),
                "avg_dimensions": dict(row["avg_dimensions"] or {}),
                "symbol_count": int(row["symbol_count"] or 0),
            })
        return series

    async def _latest_date(
        self,
        market: str = "NASDAQ",
        db: Optional[AsyncSession] = None,
    ) -> Optional[date]:
        """Return the most recent date with trend data.

        Tries ``market_score_trend`` first (the precomputed table) and falls
        back to ``ScoreHistory.date`` so callers always get a usable date even
        before the first scheduler backfill has run.
        """
        async def _query(session: AsyncSession) -> Optional[date]:
            result = await session.execute(
                select(func.max(MarketScoreTrend.date))
                .where(MarketScoreTrend.market == market)
            )
            val = result.scalar_one_or_none()
            if val is not None:
                return val
            result2 = await session.execute(
                select(func.max(ScoreHistory.date))
                .join(Asset, Asset.id == ScoreHistory.asset_id)
                .where(
                    and_(
                        Asset.active == True,
                        Asset.market == market,
                        Asset.asset_class.in_(["EQUITY", "ETF"]),
                    )
                )
            )
            return result2.scalar_one_or_none()

        if db is not None:
            result = await _query(db)
        else:
            async with async_session_maker() as session:
                result = await _query(session)

        if result is None:
            return None
        if isinstance(result, date):
            return result
        return date.fromisoformat(str(result))

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    async def _aggregate_window(
        self,
        session: AsyncSession,
        market: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        market_filter = and_(
            Asset.market == market,
            Asset.asset_class.in_(["EQUITY", "ETF"]),
        )

        dim_exprs = []
        for dim in TREND_DIMENSIONS:
            expr = func.coalesce(
                func.avg(
                    sa_case(
                        (
                            ScoreHistory.dimension_scores.has_key(dim),
                            func.cast(ScoreHistory.dimension_scores[dim], Numeric(10, 4)),
                        ),
                        else_=None,
                    )
                ),
                0.0,
            ).label(f"avg_{dim}")
            dim_exprs.append(expr)

        stmt = (
            select(
                ScoreHistory.date.label("date"),
                func.avg(ScoreHistory.overall_score).label("avg_score"),
                *dim_exprs,
                func.count(func.distinct(ScoreHistory.asset_id)).label("symbol_count"),
            )
            .join(Asset, Asset.id == ScoreHistory.asset_id)
            .where(
                and_(
                    Asset.active == True,  # noqa: E712
                    market_filter,
                    ScoreHistory.date >= start_date,
                    ScoreHistory.date <= end_date,
                )
            )
            .group_by(ScoreHistory.date)
            .order_by(ScoreHistory.date.asc())
        )

        result = await session.execute(stmt)
        rows = result.all()

        aggregated: List[Dict[str, Any]] = []
        for row in rows:
            aggregated.append({
                "date": row.date,
                "avg_score": round(float(row.avg_score or 0.0), 4),
                "avg_dimensions": {
                    dim: round(float(getattr(row, f"avg_{dim}") or 0.0), 4)
                    for dim in TREND_DIMENSIONS
                },
                "symbol_count": int(row.symbol_count or 0),
            })
        return aggregated

    async def _upsert_rows(
        self,
        session: AsyncSession,
        market: str,
        rows: List[Dict[str, Any]],
    ) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        payloads = [
            {
                "market": market,
                "date": row["date"],
                "avg_score": row["avg_score"],
                "avg_dimensions": row["avg_dimensions"],
                "symbol_count": row["symbol_count"],
                "computed_at": now,
            }
            for row in rows
        ]

        stmt = pg_insert(MarketScoreTrend).values(payloads)
        stmt = stmt.on_conflict_do_update(
            index_elements=["market", "date"],
            set_={
                "avg_score": stmt.excluded.avg_score,
                "avg_dimensions": stmt.excluded.avg_dimensions,
                "symbol_count": stmt.excluded.symbol_count,
                "computed_at": stmt.excluded.computed_at,
            },
        )
        await session.execute(stmt)