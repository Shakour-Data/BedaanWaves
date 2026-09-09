"""
Unit tests for the unified GET /analysis/dashboard/snapshot endpoint.

The endpoint composes a 3-tier (daily / hourly / current) scoring snapshot with
deltas, weights, weight trends/deltas and both daily + intraday trend series -
all bound to a single `snapshotId` so the analytical dashboard can render the
20 chart views with guaranteed parity.

Following the project's existing pattern (see test_score_trend_dashboard.py),
we invoke the route coroutine directly and patch the underlying service method
so no live database is required.
"""
import asyncio
from unittest.mock import patch

from app.api.routes import dashboard as dashboard_routes


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


FAKE_SNAPSHOT = {
    "snapshotId": "snap_abc123",
    "timestamp": "2026-09-09T12:00:00Z",
    "tier": "daily",
    "effectiveAt": "2026-09-09T00:00:00Z",
    "scores": {
        "daily": {
            "overall": 82.0,
            "dimension": {"fundamental": 72.0, "technical": 65.0, "sentiment": 55.0},
            "sub_dimension": {"fdmnt_risk": 10.0},
            "aspect": {"momentum": 7.0},
            "sub_aspect": {"price_reaction": 8.0},
        },
        "hourly": {"overall": 81.5, "dimension": {"fundamental": 71.5}},
        "current": {"overall": 82.3, "dimension": {"fundamental": 72.3}},
    },
    "deltas": {
        "hourly_vs_daily": {"overall_delta": 0.5, "overall_delta_pct": 0.6, "dimension_deltas": {}},
        "current_vs_hourly": {"overall_delta": 0.8, "overall_delta_pct": 0.98, "dimension_deltas": {}},
        "current_vs_daily": {"overall_delta": 0.3, "overall_delta_pct": 0.36, "dimension_deltas": {}},
    },
    "weights": {
        "dimension": {"fundamental": 0.4, "technical": 0.3, "sentiment": 0.3},
        "sub_dimension": {},
        "aspect": {},
        "sub_aspect": {},
    },
    "weight_trends": {
        "daily": [
            {"date": "2026-09-08", "effective_at": "2026-09-08T00:00:00Z", "weights": {"fundamental": 0.4}},
            {"date": "2026-09-09", "effective_at": "2026-09-09T00:00:00Z", "weights": {"fundamental": 0.42}},
        ]
    },
    "weight_deltas": {
        "daily": {
            "weights": {
                "dimension": {"fundamental": {"delta": 0.02, "delta_pct": 5.0}}
            }
        }
    },
    "trends": {
        "daily": [
            {"date": "2026-09-08", "effective_at": "2026-09-08T00:00:00Z", "overall": 80.0, "level_scores": {}},
            {"date": "2026-09-09", "effective_at": "2026-09-09T00:00:00Z", "overall": 82.0, "level_scores": {}},
        ],
        "intraday": [
            {"date": "2026-09-09T10:00:00Z", "effective_at": "2026-09-09T10:00:00Z", "overall": 81.0, "level_scores": {}},
            {"date": "2026-09-09T12:00:00Z", "effective_at": "2026-09-09T12:00:00Z", "overall": 82.3, "level_scores": {}},
        ],
    },
}


def _fake_session():
    """A session-like object; never consulted because get_market_snapshot is patched."""
    return object()


def _patch_snapshot_service():
    async def fake_get_market_snapshot(self, db, window_daily=30, window_intraday="24h", symbol=None, snapshot_id=None):
        return FAKE_SNAPSHOT

    return patch.object(
        dashboard_routes.TemporalSnapshotService,
        "get_market_snapshot",
        new=fake_get_market_snapshot,
    )


class TestTemporalSnapshotEndpoint:
    def test_snapshot_returns_unified_envelope(self):
        with _patch_snapshot_service():
            response = _run(
                dashboard_routes.get_dashboard_snapshot(
                    symbol=None,
                    snapshotId=None,
                    window_daily=30,
                    window_intraday="24h",
                    db=_fake_session(),
                )
            )

        assert response["status"] == "success"
        assert response["timestamp"] == "2026-09-09T12:00:00Z"
        assert response["snapshotId"] == "snap_abc123"

    def test_snapshot_includes_three_tiers(self):
        with _patch_snapshot_service():
            response = _run(
                dashboard_routes.get_dashboard_snapshot(
                    symbol=None,
                    snapshotId=None,
                    window_daily=30,
                    window_intraday="24h",
                    db=_fake_session(),
                )
            )

        scores = response["scores"]
        assert {"daily", "hourly", "current"}.issubset(scores.keys())

    def test_snapshot_carries_parity_ready_payload(self):
        """The unified snapshot must expose daily trend + weights + weight trends so the
        frontend can build spider/trend charts from a single snapshotId (FR1)."""
        with _patch_snapshot_service():
            response = _run(
                dashboard_routes.get_dashboard_snapshot(
                    symbol=None,
                    snapshotId=None,
                    window_daily=30,
                    window_intraday="24h",
                    db=_fake_session(),
                )
            )

        assert isinstance(response["trends"]["daily"], list)
        assert len(response["trends"]["daily"]) == 2
        assert isinstance(response["weights"]["dimension"], dict)
        assert isinstance(response["weight_trends"]["daily"], list)
        assert isinstance(response["weight_deltas"]["daily"]["weights"]["dimension"], dict)

    def test_snapshot_accepts_symbol_scope(self):
        captured = {}

        async def fake_get_market_snapshot(self, db, window_daily=30, window_intraday="24h", symbol=None, snapshot_id=None):
            captured["symbol"] = symbol
            return FAKE_SNAPSHOT

        with patch.object(
            dashboard_routes.TemporalSnapshotService,
            "get_market_snapshot",
            new=fake_get_market_snapshot,
        ):
            _run(
                dashboard_routes.get_dashboard_snapshot(
                    symbol="AAPL",
                    snapshotId=None,
                    window_daily=30,
                    window_intraday="24h",
                    db=_fake_session(),
                )
            )

        assert captured["symbol"] == "AAPL"
