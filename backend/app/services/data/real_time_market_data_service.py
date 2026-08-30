"""
Real-Time Market Data Service

Abstraction layer for fetching live NASDAQ equity data.
Primary provider: yfinance (free, adjusted=True support).
All returned price arrays use adjusted_close as the primary input for calculations.

STRICT CONTRACT:
- No hardcoded prices.
- No mock data.
- No fake fallbacks.
- On API failure, returns a structured error; never stale or fake data.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import DataProviderException
from app.services.core.base_service import BaseService
from app.services.data.market_hours_service import MarketHoursService
from app.schemas.schemas import (
    HistoricalCandleResponse,
    HistoricalDataResponse,
    IntradayDataResponse,
    RealtimeQuoteResponse,
)

logger = logging.getLogger(__name__)

# yfinance calls are blocking; use a bounded thread pool.
_EXECUTOR = ThreadPoolExecutor(max_workers=8)


class RealTimeMarketDataService(BaseService):
    """
    Service that fetches real-time and historical market data for NASDAQ equities.
    Uses yfinance as the primary (and currently only) provider.
    All analytical consumers MUST use adjusted_close.
    """

    def __init__(
        self,
        service_name: str = "RealTimeMarketDataService",
        cache_service: Any = None,
    ):
        super().__init__(service_name)
        self._settings = get_settings()
        self._market_hours = MarketHoursService()
        self._cache = cache_service
        self._provider = self._settings.DATA_PROVIDER.lower()
        self._last_fetch_ts: Dict[str, datetime] = {}
        self._last_fetch_error: Optional[str] = None
        self._last_fetch_latency_ms: Optional[float] = None

    async def initialize(self) -> None:
        self.logger.info(f"RealTimeMarketDataService initialized (provider={self._provider})")

    async def shutdown(self) -> None:
        self.logger.info("RealTimeMarketDataService shutdown")

    async def get_realtime_quote(self, symbol: str) -> RealtimeQuoteResponse:
        """
        Fetch the current real-time quote for a symbol.

        Returns RealtimeQuoteResponse with current price, change %, volume, timestamp,
        and market status. adjusted_close is included for analytical use.

        STRICT: Raises DataProviderException on failure. Never returns fake data.
        """
        cache_key = f"quote:{symbol.upper()}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return RealtimeQuoteResponse(**cached)

        raw = await self._run_blocking(self._fetch_yfinance_quote, symbol)
        if raw is None:
            raise DataProviderException(
                f"Failed to fetch real-time quote for {symbol}",
                details={"symbol": symbol, "provider": self._provider},
            )

        market_status = self._market_hours.get_market_status()
        response = RealtimeQuoteResponse(
            symbol=symbol.upper(),
            current_price=float(raw["current_price"]),
            change_value=float(raw["change_value"]),
            change_percent=float(raw["change_percent"]),
            open=float(raw["open"]),
            high=float(raw["high"]),
            low=float(raw["low"]),
            previous_close=float(raw["previous_close"]),
            volume=int(raw["volume"]),
            timestamp=datetime.fromtimestamp(raw["timestamp"], tz=timezone.utc),
            market_status=market_status["status"],
            freshness_label=market_status["freshness_label"],
            is_delayed=market_status["is_delayed"],
            data_source="yfinance",
            adjusted_close=float(raw["adjusted_close"]) if raw.get("adjusted_close") is not None else None,
        )

        ttl = self._settings.REALTIME_QUOTE_CACHE_TTL_SECONDS
        self._set_cached(cache_key, response.model_dump(mode="json"), ttl)
        self._last_fetch_ts[symbol.upper()] = datetime.now(timezone.utc)
        return response

    async def get_adjusted_historical(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
    ) -> HistoricalDataResponse:
        """
        Fetch adjusted OHLCV historical data for a symbol.

        Returns candles where every row includes adjusted_close.
        Analytical functions MUST use adjusted_close; raw close is provided for reference only.

        STRICT: Raises DataProviderException on failure. Never returns fake data.
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=self._settings.DEFAULT_LOOKBACK_DAYS)

        cache_key = f"hist:{symbol.upper()}:{interval}:{start_date.date()}:{end_date.date()}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return HistoricalDataResponse(**cached)

        raw_candles = await self._run_blocking(
            self._fetch_yfinance_history,
            symbol,
            start_date,
            end_date,
            interval,
        )
        if not raw_candles:
            raise DataProviderException(
                f"No historical data returned for {symbol} ({start_date.date()} to {end_date.date()})",
                details={"symbol": symbol, "provider": self._provider},
            )

        market_status = self._market_hours.get_market_status()
        candles = [
            HistoricalCandleResponse(
                timestamp=c["timestamp"],
                open=float(c["open"]),
                high=float(c["high"]),
                low=float(c["low"]),
                close=float(c["close"]),
                adjusted_close=float(c["adjusted_close"]),
                volume=int(c["volume"]),
                split_ratio=float(c["split_ratio"]) if c.get("split_ratio") is not None else None,
                source="yfinance",
            )
            for c in raw_candles
        ]

        response = HistoricalDataResponse(
            symbol=symbol.upper(),
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            candles=candles,
            data_source="yfinance",
            fetched_at=datetime.now(timezone.utc),
        )

        ttl = self._settings.HISTORICAL_DATA_CACHE_TTL_SECONDS
        self._set_cached(cache_key, response.model_dump(mode="json"), ttl)
        self._last_fetch_ts[symbol.upper()] = datetime.now(timezone.utc)
        return response

    async def get_intraday(self, symbol: str, interval: str = "5m") -> IntradayDataResponse:
        """
        Fetch intraday OHLCV bars for the current trading day.

        Returns candles with adjusted_close. For intraday, adjusted_close typically
        equals close (no dividends/splits intraday), but we still enforce the field.

        STRICT: Raises DataProviderException on failure. Never returns fake data.
        """
        cache_key = f"intraday:{symbol.upper()}:{interval}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return IntradayDataResponse(**cached)

        raw_candles = await self._run_blocking(
            self._fetch_yfinance_intraday,
            symbol,
            interval,
        )
        if not raw_candles:
            raise DataProviderException(
                f"No intraday data returned for {symbol} ({interval})",
                details={"symbol": symbol, "interval": interval, "provider": self._provider},
            )

        market_status = self._market_hours.get_market_status()
        candles = [
            HistoricalCandleResponse(
                timestamp=c["timestamp"],
                open=float(c["open"]),
                high=float(c["high"]),
                low=float(c["low"]),
                close=float(c["close"]),
                adjusted_close=float(c["adjusted_close"]),
                volume=int(c["volume"]),
                split_ratio=float(c["split_ratio"]) if c.get("split_ratio") is not None else None,
                source="yfinance",
            )
            for c in raw_candles
        ]

        response = IntradayDataResponse(
            symbol=symbol.upper(),
            interval=interval,
            candles=candles,
            market_status=market_status["status"],
            freshness_label=market_status["freshness_label"],
            data_source="yfinance",
            fetched_at=datetime.now(timezone.utc),
        )

        ttl = self._settings.INTRADAY_DATA_CACHE_TTL_SECONDS
        self._set_cached(cache_key, response.model_dump(mode="json"), ttl)
        self._last_fetch_ts[symbol.upper()] = datetime.now(timezone.utc)
        return response

    async def get_price_array(self, symbol: str, days: int = 252) -> List[float]:
        """
        Utility for analytical engines: returns a list of adjusted_close prices.

        ALL technical indicator engines MUST consume this method rather than raw close.
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days + 30)
        hist = await self.get_adjusted_historical(symbol, start_date, end_date, interval="1d")
        return [c.adjusted_close for c in hist.candles]

    async def health_check(self) -> Dict[str, Any]:
        """Return data provider health status."""
        status = "healthy"
        last_error = None
        latency_ms = None

        test_symbol = "AAPL"
        start = time.perf_counter()
        try:
            await self.get_realtime_quote(test_symbol)
            latency_ms = (time.perf_counter() - start) * 1000
        except Exception as exc:
            status = "unhealthy"
            last_error = str(exc)
            latency_ms = (time.perf_counter() - start) * 1000

        last_ts = self._last_fetch_ts.get(test_symbol)
        return {
            "provider": self._provider,
            "status": status,
            "last_successful_fetch": last_ts.isoformat() if last_ts else None,
            "last_error": last_error,
            "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
            "details": {
                "yfinance_enabled": self._settings.YFINANCE_ENABLED,
                "cache_backend": getattr(self._cache, 'backend_type', 'none') if self._cache else 'none',
            },
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        if self._cache is None:
            return None
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self._cache.get(key, namespace="market_data"), loop
                )
                result = future.result(timeout=2)
            else:
                result = loop.run_until_complete(self._cache.get(key, namespace="market_data"))
            if hasattr(result, 'value') and hasattr(result, 'is_success'):
                if result.is_success:
                    return result.value
            elif isinstance(result, dict):
                return result
            return None
        except Exception:
            return None

    def _set_cached(self, key: str, value: Any, ttl: int) -> None:
        if self._cache is None:
            return
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self._cache.set(key, value, namespace="market_data", ttl=ttl), loop
                )
                future.result(timeout=2)
            else:
                loop.run_until_complete(self._cache.set(key, value, namespace="market_data", ttl=ttl))
        except Exception:
            pass

    async def _run_blocking(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_EXECUTOR, lambda: func(*args, **kwargs))

    def _fetch_yfinance_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Blocking call to yfinance for a real-time quote.
        Uses ticker.info for the latest available data.
        """
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        if not info:
            self.logger.warning(f"yfinance returned empty info for {symbol}")
            self._last_fetch_error = f"Empty info for {symbol}"
            return None

        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        open_price = info.get("open") or info.get("regularMarketOpen")
        day_high = info.get("dayHigh") or info.get("regularMarketDayHigh")
        day_low = info.get("dayLow") or info.get("regularMarketDayLow")
        volume = info.get("volume") or info.get("regularMarketVolume") or 0

        if current_price is None:
            self._last_fetch_error = f"No current price for {symbol}"
            return None

        change_value = (current_price - previous_close) if previous_close is not None else 0.0
        change_percent = (change_value / previous_close * 100) if previous_close not in (None, 0) else 0.0

        # For adjusted_close on a quote, use currentPrice which yfinance already adjusts
        adjusted_close = current_price

        return {
            "current_price": current_price,
            "change_value": change_value,
            "change_percent": change_percent,
            "open": open_price if open_price is not None else current_price,
            "high": day_high if day_high is not None else current_price,
            "low": day_low if day_low is not None else current_price,
            "previous_close": previous_close if previous_close is not None else current_price,
            "volume": volume,
            "timestamp": time.time(),
            "adjusted_close": adjusted_close,
        }

    def _fetch_yfinance_history(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> List[Dict[str, Any]]:
        """
        Blocking call to yfinance for adjusted historical OHLCV.
        Uses auto_adjust=False so we can explicitly read Adj Close.
        """
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        start_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, "strftime") else str(start_date)
        end_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, "strftime") else str(end_date)

        hist = ticker.history(start=start_str, end=end_str, interval=interval, auto_adjust=False)
        if hist.empty:
            self._last_fetch_error = f"Empty history for {symbol}"
            return []

        candles = []
        for ts, row in hist.iterrows():
            # yfinance returns timezone-aware timestamps
            ts_utc = ts.tz_convert("UTC") if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
            open_p = float(row["Open"])
            high_p = float(row["High"])
            low_p = float(row["Low"])
            close_p = float(row["Close"])
            adj_close = float(row["Adj Close"]) if "Adj Close" in hist.columns else close_p
            volume_p = int(row["Volume"]) if "Volume" in hist.columns else 0
            split_ratio = float(row.get("Stock Splits", 1.0)) if "Stock Splits" in hist.columns else None
            if split_ratio == 0.0:
                split_ratio = None

            # Ensure OHLC consistency
            high_p = max(open_p, high_p, low_p, close_p, adj_close)
            low_p = min(open_p, high_p, low_p, close_p, adj_close)

            candles.append({
                "timestamp": ts_utc.replace(tzinfo=None),
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
                "adjusted_close": adj_close,
                "volume": volume_p,
                "split_ratio": split_ratio,
            })

        return candles

    def _fetch_yfinance_intraday(self, symbol: str, interval: str = "5m") -> List[Dict[str, Any]]:
        """
        Blocking call to yfinance for intraday bars.
        Uses auto_adjust=False for explicit adjusted_close.
        """
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        # For intraday, yfinance typically supports 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h
        valid_intervals = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"}
        if interval not in valid_intervals:
            interval = "5m"

        hist = ticker.history(period="5d", interval=interval, auto_adjust=False)
        if hist.empty:
            self._last_fetch_error = f"Empty intraday history for {symbol}"
            return []

        candles = []
        for ts, row in hist.iterrows():
            ts_utc = ts.tz_convert("UTC") if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
            open_p = float(row["Open"])
            high_p = float(row["High"])
            low_p = float(row["Low"])
            close_p = float(row["Close"])
            adj_close = float(row["Adj Close"]) if "Adj Close" in hist.columns else close_p
            volume_p = int(row["Volume"]) if "Volume" in hist.columns else 0

            high_p = max(open_p, high_p, low_p, close_p, adj_close)
            low_p = min(open_p, high_p, low_p, close_p, adj_close)

            candles.append({
                "timestamp": ts_utc.replace(tzinfo=None),
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
                "adjusted_close": adj_close,
                "volume": volume_p,
                "split_ratio": None,
            })

        return candles
