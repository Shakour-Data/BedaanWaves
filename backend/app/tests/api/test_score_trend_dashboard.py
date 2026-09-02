"""
Unit tests for the /analysis/dashboard/score-trend endpoint.

Verifies that the response aggregates all six dimensions per trading day and
computes day-over-day deltas for both the overall score and each individual
dimension. The endpoint is exercised against a mocked AsyncSession so the
tests stay self-contained (no live DB required).
"""
import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.api.routes import dashboard as dashboard_routes


class _FakeRow:
    """Row-like object exposing dynamic attribute access."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def _make_session(rows):
    session = MagicMock()
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    session.execute = AsyncMock(return_value=result)
    return session


def _row(date, avg_score, dims, symbol_count=42):
    return _FakeRow(
        date=SimpleNamespace(isoformat=lambda d=date: d),
        avg_score=avg_score,
        symbol_count=symbol_count,
        **dims,
    )


DIM_KEYS = ("fundamental", "technical", "sentiment", "risk", "macro", "ai")


def _dims(f, t, s, r, m, a):
    return {
        "avg_fundamental": f,
        "avg_technical": t,
        "avg_sentiment": s,
        "avg_risk": r,
        "avg_macro": m,
        "avg_ai": a,
    }


class TestScoreTrendDashboard(unittest.TestCase):
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_score_trend_includes_all_six_dimensions(self):
        rows = [
            _row("2026-08-31", 60.0, _dims(55.0, 58.0, 62.0, 70.0, 50.0, 65.0)),
            _row("2026-09-01", 62.5, _dims(57.0, 60.0, 63.0, 71.0, 51.0, 66.0)),
        ]

        response = self._run(
            dashboard_routes.get_score_trend(
                days=30, market="NASDAQ", db=_make_session(rows)
            )
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["market"], "NASDAQ")
        self.assertEqual(response["count"], 2)
        self.assertEqual(set(response["dimensions"]), set(DIM_KEYS))

        first, second = response["series"]

        self.assertEqual(first["avg_score"], 60.0)
        self.assertEqual(set(first["avg_dimensions"].keys()), set(DIM_KEYS))
        self.assertEqual(first["score_change"], 0.0)
        self.assertTrue(all(v == 0.0 for v in first["dimension_changes"].values()))

        # Day-over-day: 62.5 - 60.0 = 2.5 overall.
        self.assertAlmostEqual(second["score_change"], 2.5)
        self.assertAlmostEqual(second["dimension_changes"]["fundamental"], 2.0)
        self.assertAlmostEqual(second["dimension_changes"]["technical"], 2.0)
        self.assertAlmostEqual(second["dimension_changes"]["sentiment"], 1.0)
        self.assertAlmostEqual(second["dimension_changes"]["risk"], 1.0)
        self.assertAlmostEqual(second["dimension_changes"]["macro"], 1.0)
        self.assertAlmostEqual(second["dimension_changes"]["ai"], 1.0)

        # ``technical_change`` mirrors the dimension_changes value for back-compat.
        self.assertEqual(
            second["technical_change"], second["dimension_changes"]["technical"]
        )

    def test_score_trend_handles_empty_series(self):
        response = self._run(
            dashboard_routes.get_score_trend(
                days=30, market="NASDAQ", db=_make_session([])
            )
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["count"], 0)
        self.assertEqual(response["series"], [])
        self.assertEqual(
            response["dimensions"],
            ["fundamental", "technical", "sentiment", "risk", "macro", "ai"],
        )

    def test_score_trend_all_market_accepted(self):
        rows = [
            _row("2026-09-01", 60.0, _dims(55.0, 58.0, 62.0, 70.0, 50.0, 65.0), symbol_count=10)
        ]
        response = self._run(
            dashboard_routes.get_score_trend(
                days=30, market="ALL", db=_make_session(rows)
            )
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["market"], "ALL")
        self.assertEqual(response["count"], 1)


if __name__ == "__main__":
    unittest.main()