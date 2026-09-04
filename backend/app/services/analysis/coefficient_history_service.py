"""CoefficientHistoryService

Reads :class:`CoefficientHistory` rows for a window and groups the
``coefficients`` JSONB by level. The existing dashboard endpoint only
exposes the six top-level dimension weights; this service additionally
exposes sub-dimension, aspect, and sub-aspect weights so the dashboard can
render the rest of the project's 20-chart suite (charts #14–#20).

The full ``coefficients`` dict already includes nested weight entries (the
``coefficient_learning_service`` writes the complete hierarchy), so we
filter by key-prefix at the right level.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from app.core.utils import utc_now_iso

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_maker
from app.models.models import CoefficientHistory
from app.services.core import BaseService


logger = logging.getLogger(__name__)


DIMENSION_KEYS = ("fundamental", "technical", "sentiment", "risk", "macro", "ai")


def _is_sub_dimension_key(key: str) -> bool:
    return any(key.startswith(f"{d}_") for d in DIMENSION_KEYS) and (
        key.count("_") == 2
    )


def _is_aspect_key(key: str) -> bool:
    return "aspect" in key and key.split("_")[-2] == "aspect"


def _is_sub_aspect_key(key: str) -> bool:
    if not any(key.startswith(f"{d}_") for d in DIMENSION_KEYS):
        return False
    if _is_sub_dimension_key(key) or _is_aspect_key(key):
        return False
    return True


class CoefficientHistoryService(BaseService):
    """Returns per-day coefficient history at a chosen hierarchy level."""

    def __init__(self, service_name: str = "CoefficientHistoryService") -> None:
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("CoefficientHistoryService initialized")

    async def shutdown(self) -> None:
        self.logger.info("CoefficientHistoryService shutdown")

    async def get_history(
        self,
        days: int = 30,
        market: str = "NASDAQ",
        level: str = "dimension",
        parent: Optional[str] = None,
        latest: bool = False,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Return per-day coefficient snapshots filtered by ``level``.

        Args:
            level:  One of ``dimension``, ``sub_dimension``, ``aspect``,
                    ``sub_aspect``.
            parent: Optional parent key to filter by (dimension for
                    sub-dimensions, sub-dim for aspects, aspect for
                    sub-aspects).

        Returns:
            ``{status, level, days, market, count, latest_date, series}``
            where each ``series[i]`` has ``date``, ``metrics`` (the per-key
            weight snapshot) and ``metric_changes`` (day-over-day deltas).
        """
        if level not in ("dimension", "sub_dimension", "aspect", "sub_aspect"):
            raise ValueError(f"Unsupported level: {level}")

        async with async_session_maker() as session:
            if latest:
                effective_end = await self._latest_date(market, session)
            else:
                effective_end = end_date or datetime.now(timezone.utc).date()

            if effective_end is None:
                return self._empty(level, days, market)

            start_date = effective_end - timedelta(days=days - 1)
            rows = await self._fetch_window(
                session, market=market, start_date=start_date, end_date=effective_end,
            )

        series = self._shape_series(rows, level=level, parent=parent)
        latest_date = series[-1]["date"] if series else None
        return {
            "status": "success",
            "level": level,
            "days": days,
            "market": market,
            "parent": parent,
            "count": len(series),
            "latest_date": latest_date,
            "series": series,
            "timestamp": utc_now_iso(),
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
            "timestamp": utc_now_iso(),
        }

    async def _latest_date(
        self,
        market: str,
        db: AsyncSession,
    ) -> Optional[date]:
        result = await db.execute(
            select(func.max(func.date(CoefficientHistory.effective_at)))
            .where(CoefficientHistory.market == market)
        )
        value = result.scalar_one_or_none()
        return value

    async def _fetch_window(
        self,
        db: AsyncSession,
        market: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        query = (
            select(
                func.date(CoefficientHistory.effective_at).label("effective_date"),
                CoefficientHistory.coefficients,
            )
            .where(
                and_(
                    CoefficientHistory.market == market,
                    CoefficientHistory.effective_at >= start_dt,
                    CoefficientHistory.effective_at < end_dt,
                )
            )
            .order_by(CoefficientHistory.effective_at.asc())
        )
        result = await db.execute(query)
        rows = result.all()
        out: List[Dict[str, Any]] = []
        for row in rows:
            eff = row.effective_date
            if isinstance(eff, datetime):
                eff = eff.date()
            out.append({
                "date": eff.isoformat(),
                "coefficients": dict(row.coefficients or {}),
            })
        return out

    def _shape_series(
        self,
        rows: List[Dict[str, Any]],
        level: str,
        parent: Optional[str],
    ) -> List[Dict[str, Any]]:
        if level == "dimension":
            keys = DIMENSION_KEYS
        elif level == "sub_dimension":
            keys = None  # derived
        elif level == "aspect":
            keys = None
        else:
            keys = None

        series: List[Dict[str, Any]] = []
        for row in rows:
            metrics = self._filter_metrics(
                row["coefficients"], level=level, parent=parent, known_keys=keys,
            )
            series.append({
                "date": row["date"],
                "metrics": metrics,
            })

        for i, point in enumerate(series):
            if i == 0:
                point["metric_changes"] = {k: 0.0 for k in point["metrics"]}
                continue
            prev = series[i - 1]["metrics"]
            point["metric_changes"] = {
                k: round(point["metrics"].get(k, 0.0) - prev.get(k, 0.0), 4)
                for k in point["metrics"]
            }
        return series

    @staticmethod
    def _filter_metrics(
        coeffs: Dict[str, Any],
        level: str,
        parent: Optional[str],
        known_keys: Optional[tuple],
    ) -> Dict[str, float]:
        if level == "dimension":
            return {k: float(coeffs.get(k, 0.0)) for k in (known_keys or DIMENSION_KEYS)}

        result: Dict[str, float] = {}
        for key, value in coeffs.items():
            if level == "sub_dimension" and not _is_sub_dimension_key(key):
                continue
            if level == "aspect" and not _is_aspect_key(key):
                continue
            if level == "sub_aspect" and not _is_sub_aspect_key(key):
                continue
            if parent is not None and not key.startswith(f"{parent}_") and key != parent:
                continue
            try:
                result[key] = float(value)
            except (TypeError, ValueError):
                continue
        return result
