"""
Acceptance Tests for Temporal Snapshot API (Task 10).

Covers:
  AC1 — /dashboard/snapshot response schema: snapshotId, scores (daily/hourly/current),
        deltas (3 canonical frames), weights, weightTrends, weightDeltas, trends(daily/intraday).
  AC2 — Identical snapshotId replay -> byte-parity via in-memory cache; cache hit <100ms.
  Snapshot Index — /dashboard/snapshots returns {hourly: [...], daily: [...]} shape (TS contract).
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

from app.services.analysis.temporal_snapshot_service import (
    TemporalSnapshotService,
    _floor_to_hour,
    _floor_to_day,
)
from app.models.scoring_snapshot import ScoringSnapshot, SnapshotTier

pytestmark = pytest.mark.unit

REQUIRED_TOP_LEVEL_KEYS: tuple = (
    "snapshotId",
    "effectiveAt",
    "fetchedAt",
    "tier",
    "scores",
    "deltas",
    "weights",
    "weightTrends",
    "weightDeltas",
    "trends",
    "universe",
)

REQUIRED_SCORE_TIERS: tuple = ("daily", "hourly", "current")
REQUIRED_DELTA_FRAMES: tuple = ("hourly_vs_daily", "current_vs_hourly", "current_vs_daily")
REQUIRED_WEIGHT_LEVELS: tuple = ("dimension", "sub_dimension", "aspect", "sub_aspect")


def _empty_service() -> TemporalSnapshotService:
    """Return an isolated TemporalSnapshotService instance (no Redis)."""
    svc = TemporalSnapshotService()
    svc.cache = None  # force bypass external cache per-test; we use test-internal only
    return svc


class TestSnapshotContractAC1:
    """AC1: /dashboard/snapshot response shape matches Pydantic/TS contract."""

    async def test_get_market_snapshot_top_level_keys(self, fake_session):
        """All required top-level keys exist in the snapshot payload."""
        svc = _empty_service()
        await svc.initialize()
        try:
            snap = await svc.get_market_snapshot(
                db=fake_session, window_daily=30, window_intraday="24h",
            )
        finally:
            await svc.shutdown()

        for key in REQUIRED_TOP_LEVEL_KEYS:
            assert key in snap, f"missing top-level key: {key}"
        assert isinstance(snap["snapshotId"], str) and len(snap["snapshotId"]) > 0
        assert snap["tier"] in {"daily", "hourly", "current"}

    async def test_scores_three_tier_root_keys(self, fake_session):
        """scores dict exposes daily, hourly, current sub-dicts."""
        svc = _empty_service()
        await svc.initialize()
        try:
            snap = await svc.get_market_snapshot(db=fake_session)
        finally:
            await svc.shutdown()

        scores = snap["scores"]
        for tier in REQUIRED_SCORE_TIERS:
            assert tier in scores, f"scores.{tier} missing"
            frame = scores[tier]
            # each frame must expose 5 hierarchy levels (overall + 4 nested dicts)
            assert "overall" in frame
            for nested in ("dimensions", "sub_dimensions", "aspects", "sub_aspects"):
                assert nested in frame and isinstance(frame[nested], dict)

    async def test_deltas_three_canonical_frames(self, fake_session):
        """deltas contains hourly_vs_daily, current_vs_hourly, current_vs_daily."""
        svc = _empty_service()
        await svc.initialize()
        try:
            snap = await svc.get_market_snapshot(db=fake_session)
        finally:
            await svc.shutdown()

        deltas = snap["deltas"]
        for frame in REQUIRED_DELTA_FRAMES:
            assert frame in deltas, f"deltas.{frame} missing"
            entry = deltas[frame]
            # each delta frame should carry overall + level dicts
            assert "overall" in entry
            for nested in ("dimensions", "sub_dimensions", "aspects", "sub_aspects"):
                assert nested in entry and isinstance(entry[nested], dict)

    async def test_weights_four_levels(self, fake_session):
        """weights dict returns all four coefficient levels."""
        svc = _empty_service()
        await svc.initialize()
        try:
            snap = await svc.get_market_snapshot(db=fake_session)
        finally:
            await svc.shutdown()

        weights = snap["weights"]
        for lvl in REQUIRED_WEIGHT_LEVELS:
            assert lvl in weights, f"weights.{lvl} missing"
            assert isinstance(weights[lvl], dict)

    async def test_weight_trends_and_deltas_lists(self, fake_session):
        """weightTrends and weightDeltas are lists of well-shaped points."""
        svc = _empty_service()
        await svc.initialize()
        try:
            snap = await svc.get_market_snapshot(db=fake_session, window_daily=14)
        finally:
            await svc.shutdown()

        assert isinstance(snap["weightTrends"], list)
        assert isinstance(snap["weightDeltas"], list)
        for pt in snap["weightTrends"]:
            assert "date" in pt
            assert "weights" in pt and isinstance(pt["weights"], dict)
        for d in snap["weightDeltas"]:
            # delta items are {key, value} pairs
            assert "key" in d and isinstance(d["key"], str)
            assert "value" in d and isinstance(d["value"], (int, float))

    async def test_trends_daily_intraday_split(self, fake_session):
        """trends dict exposes daily + intraday series."""
        svc = _empty_service()
        await svc.initialize()
        try:
            snap = await svc.get_market_snapshot(db=fake_session)
        finally:
            await svc.shutdown()

        trends = snap["trends"]
        assert "daily" in trends and isinstance(trends["daily"], list)
        assert "intraday" in trends and isinstance(trends["intraday"], list)
        for pt in trends["daily"]:
            # daily points: timestamp/date, avg_score, dimensions, symbol_count
            has_ts = "timestamp" in pt or "date" in pt
            assert has_ts, f"daily point missing timestamp/date: {pt}"
        for pt in trends["intraday"]:
            has_ts = "timestamp" in pt or "date" in pt
            assert has_ts, f"intraday point missing timestamp/date: {pt}"

    async def test_symbol_snapshot_carries_symbol_key(self, fake_session):
        """When symbol param is passed, payload includes symbol key in uppercase."""
        svc = _empty_service()
        await svc.initialize()
        try:
            snap = await svc.get_market_snapshot(db=fake_session, symbol="aapl")
        finally:
            await svc.shutdown()
        assert snap.get("symbol") == "AAPL"


class TestSnapshotCacheParityAC2:
    """AC2: same snapshotId replays byte-parity, cache hit < 100 ms."""

    async def test_repeated_snapshotid_deterministic_response(self, fake_session, monkeypatch):
        """Force an in-memory cache; two calls with same snapshotId return identical dicts."""

        class InMemoryKV:
            def __init__(self):
                self._kv: Dict[str, Any] = {}
                self.gets = 0
                self.sets = 0

            async def get(self, key: str) -> Any:
                self.gets += 1
                return self._kv.get(key)

            async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
                self.sets += 1
                self._kv[key] = value

            async def initialize(self):
                pass

            async def shutdown(self):
                pass

        kv = InMemoryKV()
        svc = TemporalSnapshotService()
        # install cache_service compatible wrapper
        svc.cache = kv

        await svc.initialize()
        try:
            first = await svc.get_market_snapshot(
                db=fake_session, window_daily=7, window_intraday="6h",
            )
            # Second call passes the same snapshotId: must return the cached copy
            fixed_id = first["snapshotId"]
            start = time.perf_counter()
            second = await svc.get_market_snapshot(
                db=fake_session, snapshot_id=fixed_id,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000.0
        finally:
            await svc.shutdown()

        # Parity via json-sorted deep equality (no float rounding trickery; synthetic all-zero)
        a = json.dumps(first, sort_keys=True, default=str)
        b = json.dumps(second, sort_keys=True, default=str)
        assert a == b, "snapshotId replay must produce byte-parity payload"
        # AC2 perf: cache hit path < 100 ms
        assert elapsed_ms < 100.0, f"cache hit too slow: {elapsed_ms:.2f} ms"
        # cache behavior: 2 sets (snapshotId + latest key), 2 total gets (1 miss first pass, 1 hit second pass)
        assert kv.sets == 2
        assert kv.gets >= 1


class TestSnapshotIndexShape:
    """/dashboard/snapshots returns {hourly, daily} arrays; types match SnapshotIndexEntry."""

    async def test_enumerate_shape_returns_hourly_daily_split(self, fake_session):
        """Split entries by tier: array lengths match requested limits approximately."""
        svc = _empty_service()
        await svc.initialize()
        try:
            entries = await svc.enumerate_snapshots(
                db=fake_session, hourly_limit=48, daily_limit=60,
            )
        finally:
            await svc.shutdown()

        hourly_entries = [e for e in entries if e.get("tier") == "hourly"]
        daily_entries = [e for e in entries if e.get("tier") == "daily"]
        # synthetic generator should produce exact counts requested
        assert len(hourly_entries) == 48
        assert len(daily_entries) == 60

        for entry in hourly_entries + daily_entries:
            assert "tier" in entry and entry["tier"] in {"hourly", "daily"}
            assert "effectiveAt" in entry and isinstance(entry["effectiveAt"], str)
            assert "label" in entry and isinstance(entry["label"], str)
            # snapshotId can be None when synthetic (no DB rows yet), or str
            sid = entry.get("snapshotId")
            assert sid is None or isinstance(sid, str)


class TestTierFloorHelpers:
    """Unit guards for tier flooring functions (deterministic timestamp logic)."""

    def test_floor_to_hour_strips_minutes(self):
        dt = datetime(2026, 9, 6, 14, 37, 22, 123_456, tzinfo=timezone.utc)
        floored = _floor_to_hour(dt)
        assert floored.hour == 14
        assert floored.minute == 0
        assert floored.second == 0
        assert floored.microsecond == 0
        assert floored.tzinfo is not None

    def test_floor_to_day_strips_hours(self):
        dt = datetime(2026, 9, 6, 14, 37, 22, tzinfo=timezone.utc)
        floored = _floor_to_day(dt)
        assert floored.hour == 0
        assert floored.day == 6
        assert floored.month == 9
        assert floored.year == 2026
        assert floored.minute == 0
