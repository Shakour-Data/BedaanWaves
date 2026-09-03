"""Unit tests for MarketScoreTrendService.

Exercises the service against mocked AsyncSessions so the tests stay
self-contained (no live DB required). Both the precomputed ``get_trend``
read path and the fallback on-the-fly aggregator are covered.
"""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.services.analysis import market_score_trend_service as svc_module
from app.services.analysis.market_score_trend_service import MarketScoreTrendService


DIM_KEYS = ("fundamental", "technical", "sentiment", "risk", "macro", "ai")


class _FakeRow:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def _trend_row(date_iso: str, avg_score: float, dims: dict, symbol_count: int = 10):
    return {
        "date": SimpleNamespace(isoformat=lambda d=date_iso: d),
        "avg_score": avg_score,
        "avg_dimensions": dims,
        "symbol_count": symbol_count,
    }


def _make_session(execute_return):
    """Build a session whose ``execute`` resolves to the given object.

    The returned object must expose ``.mappings().all()`` for the read path.
    """
    session = MagicMock()
    result = MagicMock()
    mappings = MagicMock()
    mappings.all = MagicMock(return_value=execute_return)
    result.mappings = MagicMock(return_value=mappings)
    session.execute = AsyncMock(return_value=result)
    return session


def _make_session_for_aggregation(rows):
    """Build a session whose ``execute`` returns rows via ``.all()``."""
    session = MagicMock()
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    session.execute = AsyncMock(return_value=result)
    return session


def _row(date, avg_score, dims, symbol_count=42):
    return _FakeRow(
        date=date,
        avg_score=avg_score,
        symbol_count=symbol_count,
        **dims,
    )


def _dims(f, t, s, r, m, a):
    return {
        "avg_fundamental": f,
        "avg_technical": t,
        "avg_sentiment": s,
        "avg_risk": r,
        "avg_macro": m,
        "avg_ai": a,
    }


class TestMarketScoreTrendService(unittest.TestCase):
    def _run(self, coro):
        return asyncio.new_event_loop().run_until_complete(coro)

    def test_get_trend_returns_rows_in_order(self):
        rows = [
            _trend_row("2026-08-30", 60.0, {k: 55.0 + i for i, k in enumerate(DIM_KEYS)}),
            _trend_row("2026-08-31", 62.0, {k: 56.0 + i for i, k in enumerate(DIM_KEYS)}),
        ]
        service = MarketScoreTrendService()
        result = self._run(
            service.get_trend(days=30, market="NASDAQ", db=_make_session(rows))
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["date"], "2026-08-30")
        self.assertEqual(result[0]["avg_score"], 60.0)
        self.assertEqual(result[0]["symbol_count"], 10)
        self.assertEqual(set(result[0]["avg_dimensions"].keys()), set(DIM_KEYS))
        self.assertEqual(result[1]["avg_score"], 62.0)

    def test_get_trend_handles_empty(self):
        service = MarketScoreTrendService()
        result = self._run(
            service.get_trend(days=30, market="NASDAQ", db=_make_session([]))
        )
        self.assertEqual(result, [])

    def test_compute_and_persist_aggregates_then_upserts(self):
        """Verify the SQL aggregation and upsert flow without hitting a DB."""
        rows = [
            _row("2026-09-01", 60.0, _dims(55.0, 58.0, 62.0, 70.0, 50.0, 65.0)),
            _row("2026-09-02", 62.5, _dims(57.0, 60.0, 63.0, 71.0, 51.0, 66.0)),
        ]

        upsert_calls = []

        # First execute() runs the aggregation SELECT -> return ``rows``;
        # the second execute() runs the upsert -> capture and return empty.
        execute_returns = iter([rows, []])

        class _FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def execute(self, stmt):
                payload = next(execute_returns, [])
                upsert_calls.append(stmt)
                if payload is rows:
                    return _make_result_with_all(payload)
                return MagicMock()

            async def commit(self):
                return None

        fake_session = _FakeSession()

        original_maker = svc_module.async_session_maker
        svc_module.async_session_maker = lambda: _FakeCtx(fake_session)
        try:
            service = MarketScoreTrendService()
            summary = self._run(
                service.compute_and_persist(target_date=None, market="NASDAQ")
            )
        finally:
            svc_module.async_session_maker = original_maker

        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["market"], "NASDAQ")
        self.assertEqual(summary["written"], 2)
        # Two executes: aggregation SELECT and the upsert.
        self.assertEqual(len(upsert_calls), 2)


def _make_result_with_all(rows):
    """Build a result-like object whose ``.all()`` returns ``rows``."""
    result = MagicMock()
    result.all = MagicMock(return_value=rows)
    return result


class _FakeCtx:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


if __name__ == "__main__":
    unittest.main()