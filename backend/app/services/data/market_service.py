"""
Market Service - Tier 2 Data Service

Market data aggregation and analysis with real database integration.
Provides market status, aggregated market data, and market-level analytics.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select

from app.core.utils import utc_now_iso
from app.db.base import async_session_maker
from app.models.models import Asset, MarketDataSnapshot

from ..core import CachedService


class MarketService(CachedService):
    """
    Market data management service.

    Provides:
    - Market status (open/closed/pre-market/after-hours)
    - Aggregated market data (total market cap, active symbols, etc.)
    - Market-wide analytics from database
    - Caching of market data
    """

    def __init__(
        self,
        service_name: str = "MarketService",
        cache_ttl_seconds: int = 300,
        market_hours_service: Any | None = None,
    ):
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.market_hours_service = market_hours_service

    async def initialize(self) -> None:
        self.logger.info("MarketService initialized")

    async def shutdown(self) -> None:
        self.cache_clear()
        self.logger.info("MarketService shutdown")

    async def get_market_status(self) -> dict[str, Any]:
        cache_key = "market_status"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        if self.market_hours_service:
            try:
                status = self.market_hours_service.get_market_status()
                self.set_cached(cache_key, status)
                return status
            except Exception as exc:
                self.logger.debug(f"MarketHoursService lookup failed: {exc}")

        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(func.count(Asset.id)).where(
                        Asset.asset_class.in_(["EQUITY", "ETF"]), Asset.active.is_(True)
                    )
                )
                active_count = result.scalar() or 0

                now = datetime.now(UTC)
                return {
                    "status": "regular",
                    "is_trading": True,
                    "is_delayed": False,
                    "active_symbols": active_count,
                    "timestamp": now.isoformat(),
                    "source": "db",
                }
        except Exception as exc:
            self.logger.debug(f"Market DB lookup failed: {exc}")

        status = {
            "status": "unknown",
            "is_trading": False,
            "is_delayed": True,
            "timestamp": utc_now_iso(),
            "source": "fallback",
        }
        self.set_cached(cache_key, status)
        return status

    async def get_market_data(
        self,
        symbol: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        cache_key = f"market_data:{symbol or 'all'}:{limit}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        try:
            async with async_session_maker() as session:
                if symbol:
                    stmt = (
                        select(Asset, MarketDataSnapshot.close, MarketDataSnapshot.volume)
                        .join(MarketDataSnapshot, MarketDataSnapshot.asset_id == Asset.id)
                        .where(Asset.symbol == symbol.upper())
                        .order_by(desc(MarketDataSnapshot.snapshot_time))
                        .limit(limit)
                    )
                else:
                    stmt = (
                        select(Asset, MarketDataSnapshot.close, MarketDataSnapshot.open, MarketDataSnapshot.volume)
                        .join(MarketDataSnapshot, MarketDataSnapshot.asset_id == Asset.id)
                        .order_by(desc(MarketDataSnapshot.snapshot_time))
                        .limit(limit)
                    )

                result = await session.execute(stmt)
                rows = result.all()

                top_gainers = []
                top_losers = []
                total_volume = 0

                for row in rows:
                    asset = row[0]
                    close = float(row[1]) if row[1] else 0
                    open_price = float(row[2]) if len(row) > 2 and row[2] else close
                    volume = int(row[3]) if len(row) > 3 and row[3] else 0

                    if open_price > 0:
                        change_pct = (close - open_price) / open_price * 100
                        if change_pct > 0:
                            top_gainers.append({
                                "symbol": asset.symbol,
                                "price": round(close, 2),
                                "change_pct": round(change_pct, 2),
                            })
                        elif change_pct < 0:
                            top_losers.append({
                                "symbol": asset.symbol,
                                "price": round(close, 2),
                                "change_pct": round(change_pct, 2),
                            })
                    total_volume += volume

                top_gainers.sort(key=lambda x: x["change_pct"], reverse=True)
                top_losers.sort(key=lambda x: x["change_pct"])

                data = {
                    "symbol": symbol,
                    "total_assets": len(rows),
                    "top_gainers": top_gainers[:10],
                    "top_losers": top_losers[:10],
                    "total_volume": total_volume,
                    "timestamp": utc_now_iso(),
                    "source": "db",
                }
                self.set_cached(cache_key, data)
                return data
        except Exception as exc:
            self.logger.debug(f"Market data DB lookup failed: {exc}")

        data = {
            "symbol": symbol,
            "total_assets": 0,
            "top_gainers": [],
            "top_losers": [],
            "total_volume": 0,
            "timestamp": utc_now_iso(),
            "source": "fallback",
        }
        return data

    async def get_market_overview(self) -> dict[str, Any]:
        cache_key = "market_overview"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        try:
            async with async_session_maker() as session:
                asset_result = await session.execute(
                    select(func.count(Asset.id)).where(
                        Asset.asset_class.in_(["EQUITY", "ETF"])
                    )
                )
                snapshot_result = await session.execute(
                    select(
                        func.count(MarketDataSnapshot.id).label("snapshot_count"),
                        func.sum(MarketDataSnapshot.volume).label("total_volume"),
                    )
                )
                snap_row = snapshot_result.fetchone()
                overview = {
                    "total_assets": asset_result.scalar() or 0,
                    "total_snapshots": snap_row.snapshot_count or 0 if snap_row else 0,
                    "total_volume": float(snap_row.total_volume) if snap_row and snap_row.total_volume else 0,
                    "timestamp": utc_now_iso(),
                    "source": "db",
                }
                self.set_cached(cache_key, overview)
                return overview
        except Exception as exc:
            self.logger.debug(f"Market overview DB lookup failed: {exc}")

        overview = {
            "total_assets": 0,
            "total_snapshots": 0,
            "total_volume": 0,
            "timestamp": utc_now_iso(),
            "source": "fallback",
        }
        return overview

    async def health_check(self) -> dict[str, Any]:
        base = await super().health_check()
        base.update({"source": "MarketService"})
        return base
