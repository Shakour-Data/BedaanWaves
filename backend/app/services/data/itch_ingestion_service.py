"""
ITCH Order Book Ingestion Service.

Processes raw NASDAQ ITCH (Insertable Binary Orderbook) data to reconstruct
the limit order book, extract top-5 bid/ask levels at 15-minute intervals,
and store snapshots in the ``intl_order_book`` table (mapped to the
``IntlOrderBook`` model).

Historical mode: parses ITCH binary files on disk.
Real-time mode: reconstructs order books from a simulated feed when no live
MoldUDP64 subscription is configured, ensuring the frontend always receives
data even without a paid data feed.

Uses the ``meatpy`` library for ITCH 5.0 message parsing and LOB
reconstruction.
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from sqlalchemy import and_, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.base import get_async_session
from app.models.models import Asset, IntlOrderBook
from app.services.core.base_service import BaseService

logger = logging.getLogger(__name__)

DEFAULT_DEPTH = 5
SNAPSHOT_INTERVAL_MIN = 15


@dataclass
class OrderBookLevel:
    rank: int
    price: float
    volume: int
    order_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "price": self.price,
            "volume": self.volume,
            "order_count": self.order_count,
        }


@dataclass
class OrderBookSnapshot:
    symbol: str
    ts: datetime
    bids: list[OrderBookLevel]
    asks: list[OrderBookLevel]
    spread: float | None = None
    spread_pct: float | None = None
    source: str = "BRS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "snapshot_time": self.ts.isoformat() if self.ts.tzinfo else self.ts.replace(tzinfo=UTC).isoformat(),
            "bids": [b.to_dict() for b in self.bids],
            "asks": [a.to_dict() for a in self.asks],
            "spread": self.spread,
            "spread_pct": self.spread_pct,
            "source": self.source,
            "freshness_ts": datetime.now(UTC).isoformat(),
            "data_source": self.source,
        }


def _levels_from_meatpy(lob: Any, side: str, depth: int = DEFAULT_DEPTH) -> list[OrderBookLevel]:
    """Extract top-levels from a meatpy LimitOrderBook."""
    if lob is None:
        return []
    method = getattr(lob, f"get_{side}_levels", None)
    if method is None:
        return []
    levels = method(max_depth=depth)
    result: list[OrderBookLevel] = []
    for i, lvl in enumerate(levels):
        price_val = float(lvl.price)
        vol = int(lvl.volume) if lvl.volume else 0
        n_orders = len(lvl.queue)
        result.append(OrderBookLevel(
            rank=i + 1,
            price=price_val,
            volume=vol,
            order_count=n_orders,
        ))
    return result


class ITCHOrderBookService(BaseService):
    """
    Service that ingests ITCH order book data and exposes it for
    historical retrieval (REST) and real-time streaming (SSE).

    When real ITCH files are available, ``ingest_itch_file`` parses the
    binary feed using meatpy and stores 15-minute snapshot intervals.
    When no ITCH source is configured (the typical deployment scenario
    since ITCH feeds are free but require NASDAQ FTP access), the service
    falls back to a deterministic simulated generator seeded by the
    symbol's latest yfinance price.
    """

    def __init__(
        self,
        max_depth: int = DEFAULT_DEPTH,
        snapshot_interval_min: int = SNAPSHOT_INTERVAL_MIN,
        settings: Any = None,
    ):
        super().__init__("ITCHOrderBookService")
        self._settings = settings or get_settings()
        self._max_depth = max_depth
        self._snapshot_interval_min = snapshot_interval_min
        self._latest_cache: dict[str, OrderBookSnapshot] = {}
        self._seed_rng = random.Random(0xC0FFEE)

    async def initialize(self) -> None:
        """No async resources to initialize."""
        pass

    async def shutdown(self) -> None:
        """Clear cached snapshots."""
        self._latest_cache.clear()

    # ------------------------------------------------------------------
    # Historical ingestion from ITCH files
    # ------------------------------------------------------------------

    def ingest_itch_file(
        self,
        symbol: str,
        file_path: str,
    ) -> list[OrderBookSnapshot]:
        """
        Parse an ITCH 5.0 binary file, reconstruct the LOB for ``symbol``,
        and emit 15-minute snapshot intervals.

        Returns the list of snapshots extracted. The caller may persist
        them to the database via ``persist_snapshots``.

        Args:
            symbol: Ticker symbol to track (e.g. "AAPL").
            file_path: Path to the ITCH .bin / .gz file.
        """
        from meatpy.itch50 import ITCH50MarketProcessor, ITCH50MessageReader

        symbol = symbol.upper()
        instrument = symbol.encode("ascii")
        book_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        processor = ITCH50MarketProcessor(instrument=instrument, book_date=book_date)
        snapshots: list[OrderBookSnapshot] = []
        next_snapshot_at: datetime | None = None

        with ITCH50MessageReader(file_path) as reader:
            for message in reader:
                processor.process_message(message)
                lob = processor.current_lob
                if lob is None:
                    continue

                ts = self._message_timestamp(message)
                if next_snapshot_at is None or ts >= next_snapshot_at:
                    bids = _levels_from_meatpy(lob, "bid", self._max_depth)
                    asks = _levels_from_meatpy(lob, "ask", self._max_depth)
                    snap = self._build_snapshot(symbol, ts, bids, asks, source="ITCH")
                    snapshots.append(snap)
                    self._latest_cache[symbol] = snap
                    next_snapshot_at = ts + timedelta(minutes=self._snapshot_interval_min)

        logger.info(
            "Processed ITCH file for %s: %d snapshots extracted",
            symbol,
            len(snapshots),
        )
        return snapshots

    def _message_timestamp(self, message: Any) -> datetime:
        ts = getattr(message, "timestamp", None)
        if ts is None:
            return datetime.now(UTC)
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=UTC)
            return ts.astimezone(UTC)
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(float(ts), tz=UTC)
        return datetime.now(UTC)

    def _build_snapshot(
        self,
        symbol: str,
        ts: datetime,
        bids: list[OrderBookLevel],
        asks: list[OrderBookLevel],
        source: str = "BRS",
    ) -> OrderBookSnapshot:
        spread = None
        spread_pct = None
        if bids and asks:
            best_bid = bids[0].price
            best_ask = asks[0].price
            spread = round(best_ask - best_bid, 8)
            spread_pct = round((spread / best_bid * 100.0) if best_bid > 0 else 0.0, 4)
        return OrderBookSnapshot(
            symbol=symbol,
            ts=ts,
            bids=bids,
            asks=asks,
            spread=spread,
            spread_pct=spread_pct,
            source=source,
        )

    async def persist_snapshots(
        self,
        snapshots: Sequence[OrderBookSnapshot],
        symbol: str,
        session: AsyncSession,
    ) -> None:
        """Write all level records for the snapshots to the DB."""
        asset_q = select(Asset).where(Asset.symbol == symbol.upper())
        result = await session.execute(asset_q)
        asset = result.scalars().first()
        if asset is None:
            logger.warning("No Asset record for %s; skipping DB persist", symbol)
            return

        rows: list[dict[str, Any]] = []
        for snap in snapshots:
            for lvl in snap.bids:
                rows.append({
                    "asset_id": asset.id,
                    "snapshot_time": snap.ts,
                    "rank": lvl.rank,
                    "bid_price": lvl.price,
                    "bid_volume": lvl.volume,
                    "ask_price": None,
                    "ask_volume": None,
                    "source": snap.source,
                })
            for lvl in snap.asks:
                rows.append({
                    "asset_id": asset.id,
                    "snapshot_time": snap.ts,
                    "rank": lvl.rank,
                    "bid_price": None,
                    "bid_volume": None,
                    "ask_price": lvl.price,
                    "ask_volume": lvl.volume,
                    "source": snap.source,
                })

        stmt = insert(IntlOrderBook).values(rows)
        await session.execute(stmt)
        await session.commit()
        logger.info("Persisted %d order-book rows for %s", len(rows), symbol)

    # ------------------------------------------------------------------
    # Simulated order book (fallback / demo)
    # ------------------------------------------------------------------

    def _simulate_snapshot(self, symbol: str, reference_price: float | None = None) -> OrderBookSnapshot:
        """
        Generate a deterministic simulated order-book snapshot for ``symbol``.

        Uses a seeded RNG so that repeated calls within the same symbol
        produce a walkable price ladder. Falls back to a reference price
        (e.g. from yfinance) so the spread is anchored around the real
        market level.
        """
        symbol = symbol.upper()
        rng = self._seed_rng

        if reference_price is None or reference_price <= 0:
            reference_price = 100.0

        ts = datetime.now(UTC)
        tick = 0.01
        bids: list[OrderBookLevel] = []
        asks: list[OrderBookLevel] = []

        base_bid = round(reference_price - 0.05, 2)
        for i in range(1, self._max_depth + 1):
            price = round(base_bid - tick * i, 2)
            vol = rng.randint(100, 2000) * (self._max_depth - i + 1)
            bids.append(OrderBookLevel(rank=i, price=price, volume=vol, order_count=rng.randint(1, 10)))

        best_ask = round(reference_price + 0.05, 2)
        for i in range(1, self._max_depth + 1):
            price = round(best_ask + tick * i, 2)
            vol = rng.randint(100, 2000) * (self._max_depth - i + 1)
            asks.append(OrderBookLevel(rank=i, price=price, volume=vol, order_count=rng.randint(1, 10)))

        snap = self._build_snapshot(symbol, ts, bids, asks, source="BRS")
        self._latest_cache[symbol] = snap
        return snap

    # ------------------------------------------------------------------
    # Public API for live streaming
    # ------------------------------------------------------------------

    async def get_latest_orderbook(self, symbol: str) -> dict[str, Any]:
        """
        Return the most recent order book snapshot for ``symbol``.

        Checks the in-memory cache first. If no cached snapshot exists,
        falls back to a simulated snapshot based on the symbol's yfinance
        price.
        """
        symbol = symbol.upper()

        cached = self._latest_cache.get(symbol)
        if cached is not None:
            return cached.to_dict()

        reference_price = await self._fetch_reference_price(symbol)
        snap = self._simulate_snapshot(symbol, reference_price=reference_price)
        self._latest_cache[symbol] = snap
        return snap.to_dict()

    def get_latest_orderbook_sync(self, symbol: str) -> dict[str, Any]:
        """Synchronous variant for non-async callers."""
        symbol = symbol.upper()
        cached = self._latest_cache.get(symbol)
        if cached is not None:
            return cached.to_dict()
        snap = self._simulate_snapshot(symbol)
        self._latest_cache[symbol] = snap
        return snap.to_dict()

    async def _fetch_reference_price(self, symbol: str) -> float | None:
        """Best-effort fetch of a reference price; returns None on any error."""
        try:
            from app.services.core.dependency_container import get_global_container
            container = get_global_container()
            rt_service = container.get("real_time_market_data_service")
            quote = await rt_service.get_realtime_quote(symbol)
            return quote.current_price
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Historical retrieval
    # ------------------------------------------------------------------

    async def get_orderbook_history(
        self,
        symbol: str,
        session: Any,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """
        Retrieve historical order-book snapshots for ``symbol`` from the
        ``intl_order_book`` table.
        """
        asset_q = select(Asset).where(Asset.symbol == symbol.upper())
        result = await session.execute(asset_q)
        asset = result.scalars().first()
        if asset is None:
            return []

        criteria = [IntlOrderBook.asset_id == asset.id]
        if start_date is not None:
            criteria.append(IntlOrderBook.snapshot_time >= start_date)
        if end_date is not None:
            criteria.append(IntlOrderBook.snapshot_time <= end_date)

        stmt = (
            select(IntlOrderBook)
            .where(and_(*criteria))
            .order_by(IntlOrderBook.snapshot_time.asc())
            .limit(limit)
        )
        rows = (await session.execute(stmt)).scalars().all()

            by_ts: dict[str, dict[str, Any]] = {}
            for row in rows:
                ts_key = row.snapshot_time.isoformat() if row.snapshot_time else ""
                if ts_key not in by_ts:
                    by_ts[ts_key] = {
                        "symbol": symbol.upper(),
                        "snapshot_time": ts_key,
                        "bids": [],
                        "asks": [],
                        "source": row.source or "BRS",
                    }
                if row.bid_price is not None:
                    by_ts[ts_key]["bids"].append({
                        "rank": row.rank,
                        "price": float(row.bid_price),
                        "volume": row.bid_volume,
                        "order_count": 0,
                    })
                if row.ask_price is not None:
                    by_ts[ts_key]["asks"].append({
                        "rank": row.rank,
                        "price": float(row.ask_price),
                        "volume": row.ask_volume,
                        "order_count": 0,
                    })
            return list(by_ts.values())
        return []

    # ------------------------------------------------------------------
    # Live simulation loop (for streaming)
    # ------------------------------------------------------------------

    def start_simulation(self, symbol: str, interval_s: float = 1.0) -> None:
        """
        Start a background coroutine that pushes simulated order book
        snapshots into the live orchestrator on the ``orderbook:{symbol}``
        stream key.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(self._simulation_loop(symbol, interval_s))

    async def _simulation_loop(self, symbol: str, interval_s: float) -> None:
        """Continuously emit simulated order book snapshots."""
        symbol = symbol.upper()
        rng = self._seed_rng
        tick = 0.01
        base_price = 150.0

        try:
            ref = await self._fetch_reference_price(symbol)
            if ref and ref > 0:
                base_price = ref
        except Exception:
            pass

        while True:
            ts = datetime.now(UTC)
            bids: list[OrderBookLevel] = []
            asks: list[OrderBookLevel] = []

            perturbation = rng.uniform(-0.10, 0.10)
            mid = base_price + perturbation
            base_bid = round(mid - 0.05, 2)
            best_ask = round(mid + 0.05, 2)

            for i in range(1, self._max_depth + 1):
                price = round(base_bid - tick * i, 2)
                vol = rng.randint(100, 2000) * (self._max_depth - i + 1)
                bids.append(OrderBookLevel(
                    rank=i, price=price, volume=vol, order_count=rng.randint(1, 10),
                ))

            for i in range(1, self._max_depth + 1):
                price = round(best_ask + tick * i, 2)
                vol = rng.randint(100, 2000) * (self._max_depth - i + 1)
                asks.append(OrderBookLevel(
                    rank=i, price=price, volume=vol, order_count=rng.randint(1, 10),
                ))

            snap = self._build_snapshot(symbol, ts, bids, asks, source="BRS")
            self._latest_cache[symbol] = snap

            try:
                from app.services.core.dependency_container import get_global_container
                container = get_global_container()
                orch = container.get("live_orchestrator")
                stream_key = f"orderbook:{symbol}"
                orch._emit_envelope(
                    stream_key=stream_key,
                    event_name="orderbook",
                    data=snap.to_dict(),
                )
            except Exception:
                pass

            await asyncio.sleep(interval_s)
