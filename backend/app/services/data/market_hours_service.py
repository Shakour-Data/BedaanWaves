"""
Market Hours Service

Determines NASDAQ market status: pre-market, regular, after-hours, or closed.
Provides freshness labels for UI display.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MarketHoursService:
    """
    Service for checking NASDAQ market hours and providing freshness labels.
    """

    def __init__(self):
        self._settings = get_settings()
        self._tz = ZoneInfo(self._settings.MARKET_TIMEZONE)
        self._cache = {}
        self._cache_expiry = None
        self._cache_ttl = timedelta(seconds=self._settings.MARKET_STATUS_CACHE_TTL_SECONDS)

    def get_market_status(self) -> dict:
        """
        Returns current market status and metadata.
        Cached for MARKET_STATUS_CACHE_TTL_SECONDS to avoid repeated calculations.
        """
        now_utc = datetime.now(timezone.utc)
        if self._cache_expiry and now_utc < self._cache_expiry:
            return self._cache

        now_ny = now_utc.astimezone(self._tz)
        current_time = now_ny.time()
        weekday = now_ny.weekday()  # 0=Monday, 6=Sunday

        market_open = datetime(
            now_ny.year, now_ny.month, now_ny.day,
            self._settings.MARKET_OPEN_HOUR, self._settings.MARKET_OPEN_MINUTE,
            tzinfo=self._tz
        )
        market_close = datetime(
            now_ny.year, now_ny.month, now_ny.day,
            self._settings.MARKET_CLOSE_HOUR, self._settings.MARKET_CLOSE_MINUTE,
            tzinfo=self._tz
        )
        pre_market_start = datetime(
            now_ny.year, now_ny.month, now_ny.day,
            self._settings.PRE_MARKET_START_HOUR, self._settings.PRE_MARKET_START_MINUTE,
            tzinfo=self._tz
        )
        after_hours_end = datetime(
            now_ny.year, now_ny.month, now_ny.day,
            self._settings.AFTER_HOURS_END_HOUR, self._settings.AFTER_HOURS_END_MINUTE,
            tzinfo=self._tz
        )

        is_weekend = self._settings.WEEKEND_CLOSED and weekday >= 5

        if is_weekend:
            status = "closed"
            freshness_label = "Market Closed"
            is_trading = False
            is_delayed = False
        elif pre_market_start <= now_ny < market_open:
            status = "pre_market"
            freshness_label = "Pre-Market"
            is_trading = True
            is_delayed = True
        elif market_open <= now_ny < market_close:
            status = "regular"
            freshness_label = "Live"
            is_trading = True
            is_delayed = False
        elif market_close <= now_ny < after_hours_end:
            status = "after_hours"
            freshness_label = "After-Hours"
            is_trading = True
            is_delayed = True
        else:
            status = "closed"
            freshness_label = "Market Closed"
            is_trading = False
            is_delayed = False

        result = {
            "status": status,
            "freshness_label": freshness_label,
            "is_trading": is_trading,
            "is_delayed": is_delayed,
            "timestamp": now_utc.isoformat(),
            "local_time": now_ny.isoformat(),
            "timezone": self._settings.MARKET_TIMEZONE,
            "market_open": market_open.isoformat(),
            "market_close": market_close.isoformat(),
        }

        self._cache = result
        self._cache_expiry = now_utc + self._cache_ttl
        return result

    def is_market_open(self) -> bool:
        """Quick check if market is currently in regular trading hours."""
        return self.get_market_status()["status"] == "regular"

    def should_refresh_intraday(self) -> bool:
        """Whether intraday data should be actively refreshed."""
        status = self.get_market_status()
        return status["is_trading"]

    def get_last_trading_day(self, dt: Optional[datetime] = None) -> datetime:
        """Get the most recent trading day (skip weekends)."""
        if dt is None:
            dt = datetime.now(timezone.utc)
        day = dt.astimezone(self._tz)
        while day.weekday() >= 5:
            day -= timedelta(days=1)
        return day.replace(
            hour=self._settings.MARKET_CLOSE_HOUR,
            minute=self._settings.MARKET_CLOSE_MINUTE,
            second=0,
            microsecond=0,
            tzinfo=self._tz,
        )
