"""
History Service - Tier 2 Data Service

Historical data management and retrieval with real database persistence.
Supports storing OHLCV candle data, retrieving historical time series,
and managing data quality for historical records.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import desc, select

from app.core.utils import utc_now_iso
from app.db.base import async_session_maker
from app.models.models import Asset, IntlPriceCandle

from ..core import CachedService


class HistoryService(CachedService):
    """
    Historical data management service.

    Provides:
    - Time-series data storage in database (candles table)
    - Data aggregation and retrieval
    - Historical data caching
    - Data quality management
    """

    DEFAULT_TIMEFRAME = "1d"
    DEFAULT_LIMIT = 1000
    SOURCE_LABEL = "history"

    def __init__(
        self,
        service_name: str = "HistoryService",
        db_service=None,
        cache_ttl_seconds: int = 86400,
    ):
        super().__init__(service_name, cache_ttl_seconds=cache_ttl_seconds)
        self.db_service = db_service

    async def initialize(self) -> None:
        self.logger.info("HistoryService initialized")

    async def shutdown(self) -> None:
        self.cache_clear()
        self.logger.info("HistoryService shutdown")

    async def store_historical_data(
        self,
        ticker: str,
        candles: list[dict[str, Any]],
        timeframe: str = DEFAULT_TIMEFRAME,
    ) -> int:
        """
        Store historical candle data in the database.

        Each candle dict should contain: timestamp, open, high, low, close,
        volume, and optionally adjusted_close, turnover, split_ratio.

        Args:
            ticker: Stock ticker symbol
            candles: List of candle data dicts
            timeframe: Timeframe (1d, 1h, 5m, etc.)

        Returns:
            Number of candles stored
        """
        if not candles:
            return 0

        try:
            asset_id = await self._resolve_or_create_asset(ticker)
            if asset_id is None:
                self.logger.warning(f"Cannot resolve asset for {ticker}")
                return 0

            stored = 0
            async with async_session_maker() as session:
                for candle in candles:
                    ts = candle.get("timestamp")
                    if isinstance(ts, str):
                        parsed_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    elif isinstance(ts, datetime):
                        parsed_ts = ts
                    else:
                        parsed_ts = datetime.now(timezone.utc)

                    existing = await session.execute(
                        select(IntlPriceCandle).where(
                            IntlPriceCandle.asset_id == asset_id,
                            IntlPriceCandle.timestamp == parsed_ts,
                            IntlPriceCandle.timeframe == timeframe,
                        )
                    )
                    if existing.scalars().first():
                        continue

                    price_candle = IntlPriceCandle(
                        asset_id=asset_id,
                        timestamp=parsed_ts,
                        timeframe=timeframe,
                        open=Decimal(str(candle.get("open", 0))),
                        high=Decimal(str(candle.get("high", 0))),
                        low=Decimal(str(candle.get("low", 0))),
                        close=Decimal(str(candle.get("close", 0))),
                        volume=int(candle.get("volume", 0)),
                        turnover=Decimal(str(candle.get("turnover", 0))) if candle.get("turnover") else None,
                        transactions=candle.get("transactions"),
                        adjusted_close=Decimal(str(candle.get("adjusted_close", candle.get("close", 0)))) if candle.get("adjusted_close") else None,
                        split_ratio=Decimal(str(candle.get("split_ratio", 1.0))),
                        source=candle.get("source", self.SOURCE_LABEL),
                        data_quality=candle.get("data_quality", "CONFIRMED"),
                    )
                    session.add(price_candle)
                    stored += 1

                await session.commit()
                self.logger.info(f"Stored {stored} candles for {ticker} ({timeframe})")
                return stored
        except Exception as exc:
            self.logger.warning(f"Failed to store historical data for {ticker}: {exc}")
            return 0

    async def _resolve_or_create_asset(self, ticker: str) -> Any:
        try:
            async with async_session_maker() as session:
                result = await session.execute(select(Asset).where(Asset.symbol == ticker.upper()))
                asset = result.scalars().first()
                if asset:
                    return asset.id

                asset = Asset(
                    symbol=ticker.upper(),
                    name=ticker.upper(),
                    asset_class="EQUITY",
                    market="NASDAQ",
                    currency="USD",
                    exchange="NASDAQ",
                    is_active=True,
                )
                session.add(asset)
                await session.commit()
                await session.refresh(asset)
                return asset.id
        except Exception as exc:
            self.logger.debug(f"Asset resolution failed for {ticker}: {exc}")
            return None

    async def get_historical_data(
        self,
        ticker: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        timeframe: str = DEFAULT_TIMEFRAME,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict[str, Any]]:
        cache_key = f"history:{ticker}:{timeframe}:{start_date}:{end_date}:{limit}"
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        try:
            async with async_session_maker() as session:
                asset_result = await session.execute(select(Asset).where(Asset.symbol == ticker.upper()))
                asset = asset_result.scalars().first()
                if not asset:
                    return []

                stmt = (
                    select(IntlPriceCandle)
                    .where(IntlPriceCandle.asset_id == asset.id)
                    .where(IntlPriceCandle.timeframe == timeframe)
                    .order_by(desc(IntlPriceCandle.timestamp))
                    .limit(limit)
                )
                if start_date:
                    stmt = stmt.where(IntlPriceCandle.timestamp >= start_date)
                if end_date:
                    stmt = stmt.where(IntlPriceCandle.timestamp <= end_date)

                result = await session.execute(stmt)
                candles = result.scalars().all()

                data = [
                    {
                        "timestamp": c.timestamp.isoformat(),
                        "open": float(c.open) if c.open else 0,
                        "high": float(c.high) if c.high else 0,
                        "low": float(c.low) if c.low else 0,
                        "close": float(c.close) if c.close else 0,
                        "volume": c.volume,
                        "adjusted_close": float(c.adjusted_close) if c.adjusted_close else None,
                    }
                    for c in candles
                ]
                self.set_cached(cache_key, data)
                return data
        except Exception as exc:
            self.logger.debug(f"Historical data lookup failed for {ticker}: {exc}")
            return []

    async def get_historical_prices(
        self,
        ticker: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        timeframe: str = DEFAULT_TIMEFRAME,
        limit: int = DEFAULT_LIMIT,
    ) -> list[float]:
        data = await self.get_historical_data(ticker, start_date, end_date, timeframe, limit)
        return [d["close"] for d in data]

    async def health_check(self) -> dict[str, Any]:
        base = await super().health_check()
        base.update({"source": "HistoryService"})
        return base
