"""Calendar Service - Tier 7 Specialized Service

Provides Tehran Stock Exchange (TSE) trading-day awareness and a simple
corporate-events calendar.

TSE trading calendar: Saturday-Thursday, Friday is the weekend. This is a
lightweight, dependency-free implementation (no external holiday feed).
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from ..core import BaseService


class CalendarService(BaseService):
    """Trading-day awareness and corporate-event calendar."""

    def __init__(self, service_name: str = "CalendarService", weekend_days: Optional[List[int]] = None):
        super().__init__(service_name)
        # 4 = Friday (TSE weekend); allow override for other markets.
        self.weekend_days = set(weekend_days if weekend_days is not None else [4])
        self._events: Dict[str, List[Dict[str, Any]]] = {}

    async def initialize(self) -> None:
        self.logger.info("CalendarService initialized")

    async def shutdown(self) -> None:
        self.logger.info("CalendarService shutdown")

    def is_trading_day(self, day: date) -> bool:
        """Return True if the given date is a trading day (not a weekend)."""
        return day.weekday() not in self.weekend_days

    def next_trading_day(self, day: date) -> date:
        """Return the next trading day strictly after `day`."""
        candidate = day + timedelta(days=1)
        while not self.is_trading_day(candidate):
            candidate += timedelta(days=1)
        return candidate

    def previous_trading_day(self, day: date) -> date:
        """Return the previous trading day strictly before `day`."""
        candidate = day - timedelta(days=1)
        while not self.is_trading_day(candidate):
            candidate -= timedelta(days=1)
        return candidate

    def trading_days_in_range(self, start: date, end: date) -> List[str]:
        """List ISO trading days between start and end (inclusive)."""
        days: List[str] = []
        cursor = start
        while cursor <= end:
            if self.is_trading_day(cursor):
                days.append(cursor.isoformat())
            cursor += timedelta(days=1)
        return days

    def get_month_calendar(self, year: int, month: int) -> Dict[str, Any]:
        """Return trading days and weekend days for a given month."""
        first = date(year, month, 1)
        if month == 12:
            nxt = date(year + 1, 1, 1)
        else:
            nxt = date(year, month + 1, 1)
        last = nxt - timedelta(days=1)

        trading: List[str] = []
        weekends: List[str] = []
        cursor = first
        while cursor <= last:
            if self.is_trading_day(cursor):
                trading.append(cursor.isoformat())
            else:
                weekends.append(cursor.isoformat())
            cursor += timedelta(days=1)

        return {
            "year": year,
            "month": month,
            "trading_days": trading,
            "weekend_days": weekends,
            "trading_day_count": len(trading),
        }

    def add_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a corporate/calendar event.

        Required event fields: date (ISO str or date), type, title.
        Optional: symbol, description.
        """
        event_date = event.get("date")
        if isinstance(event_date, date):
            key = event_date.isoformat()
        elif isinstance(event_date, datetime):
            key = event_date.date().isoformat()
        elif isinstance(event_date, str):
            key = event_date
        else:
            raise ValueError("Event must include a 'date' field")

        record = {
            "date": key,
            "type": event.get("type", "GENERIC"),
            "title": event.get("title", "Untitled event"),
            "symbol": event.get("symbol"),
            "description": event.get("description"),
        }
        self._events.setdefault(key, []).append(record)
        return record

    def get_events(self, day: Optional[date] = None, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return events, optionally filtered by day and/or symbol."""
        if day is not None:
            key = day.isoformat() if isinstance(day, date) else str(day)
            events = self._events.get(key, [])
        else:
            events = [e for lst in self._events.values() for e in lst]

        if symbol is not None:
            sym = str(symbol).upper()
            events = [e for e in events if str(e.get("symbol", "")).upper() == sym]
        return events

    def events_in_range(self, start: date, end: date) -> List[Dict[str, Any]]:
        """Return all events within an inclusive date range."""
        result: List[Dict[str, Any]] = []
        cursor = start
        while cursor <= end:
            result.extend(self._events.get(cursor.isoformat(), []))
            cursor += timedelta(days=1)
        return result
