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
    """Build a session that supports both code paths:

    - the precomputed ``MarketScoreTrendService.get_trend`` path
      (calls ``result.mappings().all()``) — returns ``[]`` by default so the
      endpoint falls back to the on-the-fly aggregator (matching the legacy
      behaviour asserted by these tests).
    - the on-the-fly ``_aggregate_score_trend_on_the_fly`` path
      (calls ``result.all()``) — returns the provided ``rows``.

    Tests that want to exercise the precomputed path patch
    ``MarketScoreTrendService.get_trend`` directly.
    """
    session = MagicMock()
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    mappings = MagicMock()
    mappings.all = MagicMock(return_value=[])
    result.mappings = MagicMock(return_value=mappings)
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
        return asyncio.new_event_loop().run_until_complete(coro)

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

    def test_score_trend_uses_precomputed_when_available(self):
        """The endpoint must report ``source: precomputed`` when the
        ``MarketScoreTrendService.get_trend`` path returns rows.
        """
        from unittest.mock import patch

        precomputed = [
            {
                "date": "2026-09-01",
                "avg_score": 60.0,
                "avg_dimensions": {dim: 60.0 for dim in DIM_KEYS},
                "symbol_count": 100,
            },
        ]

        async def fake_get_trend(self, days, market, db):
            return precomputed

        with patch.object(
            dashboard_routes.MarketScoreTrendService,
            "get_trend",
            new=fake_get_trend,
        ):
            response = self._run(
                dashboard_routes.get_score_trend(
                    days=30, market="NASDAQ", db=_make_session([])
                )
            )

        self.assertEqual(response["source"], "precomputed")
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["series"][0]["date"], "2026-09-01")
        self.assertEqual(response["series"][0]["score_change"], 0.0)

    def test_score_trend_falls_back_when_precomputed_empty(self):
        """If the precomputed table has no rows, the endpoint must compute
        on-the-fly and report ``source: on_the_fly_fallback``.
        """
        from unittest.mock import patch

        async def fake_get_trend(self, days, market, db):
            return []

        rows = [
            _row("2026-09-01", 60.0, _dims(55.0, 58.0, 62.0, 70.0, 50.0, 65.0)),
        ]
        with patch.object(
            dashboard_routes.MarketScoreTrendService,
            "get_trend",
            new=fake_get_trend,
        ):
            response = self._run(
                dashboard_routes.get_score_trend(
                    days=30, market="NASDAQ", db=_make_session(rows)
                )
            )

        self.assertEqual(response["source"], "on_the_fly_fallback")
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["series"][0]["avg_score"], 60.0)

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

    def test_score_trend_rejects_non_nasdaq_market(self):
        """Crypto, forex, and other non-Nasdaq markets are never aggregated.

        The endpoint used to accept the literal ``"ALL"`` value as an
        escape hatch that returned every active asset (including crypto).
        That behavior is gone — only ``"NASDAQ"`` (the default) is
        accepted, and any other value must raise a 400.
        """
        from fastapi import HTTPException
        for bad_market in ("ALL", "BINANCE", "NYSE", "CRYPTO", ""):
            with self.assertRaises(HTTPException) as ctx:
                self._run(
                    dashboard_routes.get_score_trend(
                        days=30, market=bad_market, db=_make_session([])
                    )
                )
            self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()