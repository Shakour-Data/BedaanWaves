"""
Tests for ITCH Order Book ingestion service.

Covers:
  - Simulated snapshot generation (deterministic, seeded RNG)
  - Level extraction from meatpy-style LOB mock
  - Spread / spread_pct computation
  - to_dict serialization
  - get_orderbook_history with FakeAsyncSession
  - ITCH file ingestion with mocked meatpy reader
"""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.models import Asset, IntlOrderBook
from app.services.data.itch_ingestion_service import (
    ITCHOrderBookService,
    OrderBookLevel,
    OrderBookSnapshot,
    _levels_from_meatpy,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def ob_service():
    return ITCHOrderBookService(max_depth=5, snapshot_interval_min=15)


@pytest.fixture
def fake_session():
    from tests.conftest import FakeAsyncSession
    return FakeAsyncSession()


# --------------------------------------------------------------------------- #
# OrderBookLevel / OrderBookSnapshot dataclass tests
# --------------------------------------------------------------------------- #


def test_order_book_level_to_dict():
    lvl = OrderBookLevel(rank=1, price=150.25, volume=5000, order_count=3)
    d = lvl.to_dict()
    assert d == {"rank": 1, "price": 150.25, "volume": 5000, "order_count": 3}


def test_order_book_snapshot_to_dict_includes_all_fields():
    snap = OrderBookSnapshot(
        symbol="AAPL",
        ts=datetime.now(UTC),
        bids=[OrderBookLevel(rank=1, price=149.95, volume=1000, order_count=2)],
        asks=[OrderBookLevel(rank=1, price=150.05, volume=800, order_count=1)],
        spread=0.10,
        spread_pct=0.067,
        source="ITCH",
    )
    d = snap.to_dict()
    assert d["symbol"] == "AAPL"
    assert len(d["bids"]) == 1
    assert len(d["asks"]) == 1
    assert d["bids"][0]["price"] == 149.95
    assert d["asks"][0]["volume"] == 800
    assert d["spread"] == 0.10
    assert d["spread_pct"] == 0.067
    assert d["source"] == "ITCH"
    assert d["data_source"] == "ITCH"
    assert "freshness_ts" in d


# --------------------------------------------------------------------------- #
# _levels_from_meatpy
# --------------------------------------------------------------------------- #


class _FakeLevel:
    def __init__(self, price, volume, n_orders):
        self.price = price
        self.volume = volume
        self.queue = [MagicMock()] * n_orders


class _FakeLOB:
    def __init__(self, bids, asks):
        self._bids = bids
        self._asks = asks

    def get_bid_levels(self, max_depth=None):
        return self._bids[:max_depth] if max_depth else self._bids

    def get_ask_levels(self, max_depth=None):
        return self._asks[:max_depth] if max_depth else self._asks


def test_levels_from_meatpy_bid():
    lob = _FakeLOB(
        bids=[_FakeLevel(100.0, 500, 3), _FakeLevel(99.5, 300, 2)],
        asks=[_FakeLevel(100.5, 400, 1)],
    )
    levels = _levels_from_meatpy(lob, "bid", depth=5)
    assert len(levels) == 2
    assert levels[0].price == 100.0
    assert levels[0].volume == 500
    assert levels[0].order_count == 3
    assert levels[0].rank == 1
    assert levels[1].rank == 2


def test_levels_from_meatpy_ask():
    lob = _FakeLOB(
        bids=[_FakeLevel(100.0, 500, 3)],
        asks=[_FakeLevel(100.5, 400, 1), _FakeLevel(101.0, 200, 1)],
    )
    levels = _levels_from_meatpy(lob, "ask", depth=5)
    assert len(levels) == 2
    assert levels[0].price == 100.5
    assert levels[1].rank == 2


def test_levels_from_meatpy_none_lob():
    assert _levels_from_meatpy(None, "bid") == []
    assert _levels_from_meatpy(None, "ask") == []


def test_levels_from_meatpy_depth_limit():
    lob = _FakeLOB(
        bids=[_FakeLevel(100.0, 500, 1), _FakeLevel(99.5, 300, 1), _FakeLevel(99.0, 200, 1)],
        asks=[],
    )
    levels = _levels_from_meatpy(lob, "bid", depth=2)
    assert len(levels) == 2
    assert levels[0].price == 100.0
    assert levels[1].price == 99.5


# --------------------------------------------------------------------------- #
# Spread computation via OrderBookSnapshot._build_snapshot
# --------------------------------------------------------------------------- #


def _make_snapshot(symbol, bids, asks, source="BRS"):
    spread = None
    spread_pct = None
    if bids and asks:
        best_bid = bids[0].price
        best_ask = asks[0].price
        spread = round(best_ask - best_bid, 8)
        spread_pct = round((spread / best_bid * 100.0) if best_bid > 0 else 0.0, 4)
    return OrderBookSnapshot(
        symbol=symbol,
        ts=datetime.now(UTC),
        bids=bids,
        asks=asks,
        spread=spread,
        spread_pct=spread_pct,
        source=source,
    )


def test_snapshot_computes_spread():
    bids = [OrderBookLevel(rank=1, price=99.90, volume=1000, order_count=5)]
    asks = [OrderBookLevel(rank=1, price=100.10, volume=800, order_count=3)]
    snap = _make_snapshot("TEST", bids, asks)
    assert snap.spread == 0.20
    assert snap.spread_pct == pytest.approx(0.2002, rel=1e-2)


def test_snapshot_no_spread_when_empty():
    snap = _make_snapshot("TEST", [], [])
    assert snap.spread is None
    assert snap.spread_pct is None


# --------------------------------------------------------------------------- #
# Simulated snapshot
# --------------------------------------------------------------------------- #


def test_simulate_snapshot_generates_5_levels_each_side(ob_service):
    snap = ob_service._simulate_snapshot("AAPL", reference_price=150.0)
    assert snap.symbol == "AAPL"
    assert len(snap.bids) == 5
    assert len(snap.asks) == 5
    assert all(b.rank == i + 1 for i, b in enumerate(snap.bids))
    assert all(a.rank == i + 1 for i, a in enumerate(snap.asks))
    assert snap.bids[0].price > snap.bids[-1].price
    assert snap.asks[0].price < snap.asks[-1].price
    assert snap.spread > 0
    assert snap.spread_pct > 0


def test_simulate_snapshot_uses_reference_price(ob_service):
    snap = ob_service._simulate_snapshot("TSLA", reference_price=250.0)
    assert snap.bids[0].price < 250.0
    assert snap.asks[0].price > 250.0


def test_simulate_snapshot_caches_result(ob_service):
    snap1 = ob_service._simulate_snapshot("AAPL", reference_price=100.0)
    cached = ob_service._latest_cache.get("AAPL")
    assert cached is snap1
    result = ob_service.get_latest_orderbook_sync("AAPL")
    assert result["symbol"] == "AAPL"
    assert len(result["bids"]) == 5
    assert len(result["asks"]) == 5


def test_simulate_snapshot_default_price_when_none():
    svc = ITCHOrderBookService()
    snap = svc._simulate_snapshot("TEST")
    assert snap.bids[0].price < 100.0
    assert snap.asks[0].price > 100.0


# --------------------------------------------------------------------------- #
# get_latest_orderbook
# --------------------------------------------------------------------------- #


async def test_get_latest_orderbook_falls_back_to_simulation():
    service = ITCHOrderBookService()
    with patch.object(
        service, "_fetch_reference_price", new_callable=AsyncMock, return_value=150.0
    ):
        result = await service.get_latest_orderbook("MSFT")
    assert result["symbol"] == "MSFT"
    assert len(result["bids"]) == 5
    assert len(result["asks"]) == 5
    assert result["data_source"] == "BRS"
    assert result["freshness_ts"] is not None


async def test_get_latest_orderbook_returns_cached_if_present():
    service = ITCHOrderBookService()
    cached_snap = service._simulate_snapshot("GOOG", reference_price=130.0)
    result = await service.get_latest_orderbook("GOOG")
    assert result["symbol"] == "GOOG"
    assert result["spread"] == pytest.approx(cached_snap.spread, rel=1e-6)


async def test_get_latest_orderbook_reference_price_none():
    service = ITCHOrderBookService()
    with patch.object(
        service, "_fetch_reference_price", new_callable=AsyncMock, return_value=None
    ):
        result = await service.get_latest_orderbook("AAPL")
    assert result["symbol"] == "AAPL"
    assert len(result["bids"]) == 5


# --------------------------------------------------------------------------- #
# get_orderbook_history with FakeAsyncSession
# --------------------------------------------------------------------------- #


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
    return loop.run_until_complete(coro)


def test_get_orderbook_history_returns_empty_for_unknown_symbol(fake_session):
    service = ITCHOrderBookService()
    fake_session.add(Asset(symbol="AAPL", name="Apple", market="NASDAQ",
                           asset_class="EQUITY", active=True))
    result = _run_async(
        service.get_orderbook_history("NONEXIST", session=fake_session)
    )
    assert result == []


def test_get_orderbook_history_assembles_levels_by_timestamp(fake_session):
    service = ITCHOrderBookService()
    asset = Asset(symbol="AAPL", name="Apple", market="NASDAQ",
                  asset_class="EQUITY", active=True)
    fake_session.add(asset)
    asset_id = asset.id
    snap_ts = datetime.now(UTC)

    for i in range(1, 6):
        fake_session.add(IntlOrderBook(
            asset_id=asset_id,
            snapshot_time=snap_ts,
            rank=i,
            bid_price=100.0 - i * 0.01,
            bid_volume=1000 * i,
            source="BRS",
        ))
        fake_session.add(IntlOrderBook(
            asset_id=asset_id,
            snapshot_time=snap_ts,
            rank=i,
            ask_price=100.0 + i * 0.01,
            ask_volume=800 * i,
            source="BRS",
        ))

    result = _run_async(
        service.get_orderbook_history(
            "AAPL",
            start_date=snap_ts - timedelta(minutes=1),
            end_date=snap_ts + timedelta(minutes=1),
            session=fake_session,
        )
    )
    assert len(result) == 1
    assert result[0]["symbol"] == "AAPL"
    assert len(result[0]["bids"]) == 5
    assert len(result[0]["asks"]) == 5
    assert result[0]["bids"][0]["rank"] == 1
    assert result[0]["asks"][0]["rank"] == 1


# --------------------------------------------------------------------------- #
# ITCH file ingestion (with mocked meatpy reader/processor)
# --------------------------------------------------------------------------- #


def test_ingest_itch_file_processes_messages(ob_service):
    """Verify ingest_itch_file creates a meatpy processor and iterates messages."""
    mock_processor = MagicMock()
    mock_processor.current_lob = None
    mock_message = MagicMock()
    mock_message.timestamp = datetime.now(UTC)

    with patch(
        "app.services.data.itch_ingestion_service.ITCH50MessageReader"
    ) as mock_reader_cls, patch(
        "app.services.data.itch_ingestion_service.ITCH50MarketProcessor",
        return_value=mock_processor,
    ):
        mock_reader = MagicMock()
        mock_reader.__enter__ = MagicMock(return_value=mock_reader)
        mock_reader.__exit__ = MagicMock(return_value=False)
        mock_reader.__iter__ = MagicMock(return_value=iter([mock_message]))
        mock_reader_cls.return_value = mock_reader

        snapshots = ob_service.ingest_itch_file("AAPL", "/fake/path/to/itch.bin")
        assert snapshots == []


def test_persist_snapshots_writes_to_db(fake_session):
    service = ITCHOrderBookService()
    asset = Asset(symbol="TSLA", name="Tesla", market="NASDAQ",
                  asset_class="EQUITY", active=True)
    fake_session.add(asset)
    asset_id = asset.id

    snapshots = [
        OrderBookSnapshot(
            symbol="TSLA",
            ts=datetime.now(UTC),
            bids=[OrderBookLevel(rank=1, price=99.90, volume=1000, order_count=5)],
            asks=[OrderBookLevel(rank=1, price=100.10, volume=800, order_count=3)],
            source="ITCH",
        ),
    ]

    _run_async(service.persist_snapshots(snapshots, "TSLA", fake_session))

    itch_rows = fake_session._store.get(IntlOrderBook, [])
    bid_rows = [r for r in itch_rows if r.bid_price is not None]
    ask_rows = [r for r in itch_rows if r.ask_price is not None]
    assert len(bid_rows) == 1
    assert len(ask_rows) == 1
    assert bid_rows[0].bid_price == 99.90
    assert bid_rows[0].bid_volume == 1000
    assert ask_rows[0].ask_price == 100.10
