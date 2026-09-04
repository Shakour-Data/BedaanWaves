"""
Unit tests for the three level-trend endpoints:

    GET /analysis/dashboard/sub-dimension-trend
    GET /analysis/dashboard/aspect-trend
    GET /analysis/dashboard/sub-aspect-trend

These endpoints aggregate ``raw_performance_scores`` per day for one
hierarchy level and return:
- ``avg_scores``: mean per key for that day
- ``score_changes``: day-over-day deltas (first day = zeros)
- ``latest_date``: the last date in the series

The tests exercise the endpoints against a mocked AsyncSession so no live
DB is needed, and verify:
  * market gating (NASDAQ-only)
  * end_date / latest propagation to the SQL filter
  * deltas for the second day
  * latest_date == last row's date
"""
import asyncio
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.api.routes import dashboard as dashboard_routes


class _FakeRow:
    """Row-like object exposing dynamic attribute access."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def _make_session(rows):
    """Build a session that yields the supplied rows for the level-trend SQL."""
    session = MagicMock()
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    session.execute = AsyncMock(return_value=result)
    return session


def _capture_row(day: str, raw_scores: dict, asset_id="AAPL"):
    return _FakeRow(
        day=SimpleNamespace(isoformat=lambda d=day: d),
        raw_scores=raw_scores,
        asset_id=asset_id,
    )


SUB_DIMENSION_KEYS = dashboard_routes.SUB_DIMENSION_TREND_KEYS
ASPECT_KEYS = dashboard_routes.ASPECT_TREND_KEYS
SUB_ASPECT_KEYS = dashboard_routes.SUB_ASPECT_TREND_KEYS


def _full_subdim_scores(prefix: str, value: float) -> dict:
    return {k: value for k in SUB_DIMENSION_KEYS}


def _full_aspect_scores(value: float) -> dict:
    return {k: value for k in ASPECT_KEYS}


def _full_sub_aspect_scores(value: float) -> dict:
    return {k: value for k in SUB_ASPECT_KEYS}


class TestLevelTrendEndpoints(unittest.TestCase):
    def _run(self, coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    # -------------------------------------------------------------- #
    # Sub-dimension trend
    # -------------------------------------------------------------- #
    def test_sub_dimension_trend_returns_one_point_per_day_with_deltas(self):
        rows = [
            _capture_row("2026-08-31", _full_subdim_scores("a", 50.0)),
            _capture_row("2026-09-01", _full_subdim_scores("a", 55.0)),
        ]
        response = self._run(
            dashboard_routes.get_sub_dimension_trend(
                days=30, market="NASDAQ", db=_make_session(rows)
            )
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["market"], "NASDAQ")
        self.assertEqual(response["level"], "sub_dimension")
        self.assertEqual(response["count"], 2)
        self.assertEqual(set(response["keys"]), set(SUB_DIMENSION_KEYS))
        self.assertEqual(response["latest_date"], "2026-09-01")

        first, second = response["series"]

        # First day: every change is 0
        self.assertTrue(all(v == 0.0 for v in first["score_changes"].values()))
        # Second day: every key advanced by 5.0
        self.assertTrue(
            all(abs(v - 5.0) < 1e-9 for v in second["score_changes"].values())
        )
        # avg_scores surface includes every canonical key
        self.assertEqual(set(first["avg_scores"].keys()), set(SUB_DIMENSION_KEYS))
        self.assertEqual(first["avg_scores"]["valuation"], 50.0)
        self.assertEqual(second["avg_scores"]["valuation"], 55.0)

    def test_sub_dimension_trend_rejects_non_nasdaq(self):
        with self.assertRaises(Exception) as ctx:
            self._run(
                dashboard_routes.get_sub_dimension_trend(
                    days=30, market="NYSE", db=_make_session([])
                )
            )
        self.assertEqual(ctx.exception.status_code, 400)

    def test_sub_dimension_trend_respects_end_date(self):
        rows = [
            _capture_row("2026-08-31", _full_subdim_scores("a", 50.0)),
            _capture_row("2026-09-01", _full_subdim_scores("a", 60.0)),
        ]
        response = self._run(
            dashboard_routes.get_sub_dimension_trend(
                days=30,
                market="NASDAQ",
                end_date="2026-08-31",
                db=_make_session(rows),
            )
        )
        self.assertEqual(response["count"], 2)
        self.assertEqual(response["latest_date"], "2026-09-01")
        self.assertEqual(response["series"][1]["avg_scores"]["valuation"], 60.0)

    # -------------------------------------------------------------- #
    # Aspect trend
    # -------------------------------------------------------------- #
    def test_aspect_trend_returns_one_point_per_day_with_deltas(self):
        rows = [
            _capture_row("2026-08-31", _full_aspect_scores(40.0)),
            _capture_row("2026-09-01", _full_aspect_scores(44.0)),
        ]
        response = self._run(
            dashboard_routes.get_aspect_trend(
                days=30, market="NASDAQ", db=_make_session(rows)
            )
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["level"], "aspect")
        self.assertEqual(response["count"], 2)
        self.assertEqual(response["latest_date"], "2026-09-01")

        first, second = response["series"]
        self.assertTrue(all(v == 0.0 for v in first["score_changes"].values()))
        self.assertTrue(
            all(abs(v - 4.0) < 1e-9 for v in second["score_changes"].values())
        )

    # -------------------------------------------------------------- #
    # Sub-aspect trend
    # -------------------------------------------------------------- #
    def test_sub_aspect_trend_returns_one_point_per_day_with_deltas(self):
        rows = [
            _capture_row("2026-08-31", _full_sub_aspect_scores(10.0)),
            _capture_row("2026-09-01", _full_sub_aspect_scores(15.0)),
        ]
        response = self._run(
            dashboard_routes.get_sub_aspect_trend(
                days=30, market="NASDAQ", db=_make_session(rows)
            )
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["level"], "sub_aspect")
        self.assertEqual(response["count"], 2)
        self.assertEqual(response["latest_date"], "2026-09-01")

        first, second = response["series"]
        self.assertEqual(first["avg_scores"]["sub_aspect_1"], 10.0)
        self.assertEqual(second["avg_scores"]["sub_aspect_1"], 15.0)
        self.assertTrue(
            all(abs(v - 5.0) < 1e-9 for v in second["score_changes"].values())
        )

    def test_sub_aspect_trend_rejects_non_nasdaq(self):
        with self.assertRaises(Exception) as ctx:
            self._run(
                dashboard_routes.get_sub_aspect_trend(
                    days=30, market="BTC", db=_make_session([])
                )
            )
        self.assertEqual(ctx.exception.status_code, 400)

    def test_level_trend_handles_empty_series(self):
        response = self._run(
            dashboard_routes.get_aspect_trend(
                days=30, market="NASDAQ", db=_make_session([])
            )
        )
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["count"], 0)
        self.assertEqual(response["latest_date"], None)
        self.assertEqual(response["series"], [])

    def test_level_trend_ignores_unknown_keys(self):
        """Keys outside the canonical allowlist must not bleed into avg_scores."""
        rows = [
            _capture_row(
                "2026-08-31",
                {"valuation": 60.0, "unknown_key": 999.0},
            ),
        ]
        response = self._run(
            dashboard_routes.get_sub_dimension_trend(
                days=30, market="NASDAQ", db=_make_session(rows)
            )
        )
        self.assertEqual(response["count"], 1)
        first = response["series"][0]
        self.assertNotIn("unknown_key", first["avg_scores"])
        self.assertEqual(first["avg_scores"]["valuation"], 60.0)

    def test_level_trend_invalid_end_date_returns_400(self):
        with self.assertRaises(Exception) as ctx:
            self._run(
                dashboard_routes.get_sub_dimension_trend(
                    days=30,
                    market="NASDAQ",
                    end_date="not-a-date",
                    db=_make_session([]),
                )
            )
        self.assertEqual(ctx.exception.status_code, 400)