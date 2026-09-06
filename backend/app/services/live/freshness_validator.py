"""
Freshness Validator for live data payloads.

Pure validator class that checks payloads against freshness SLO thresholds,
numeric sanity rules (non-null prices, OHLC consistency), and intraday
monotonic-timestamp guarantees. Returns a Validated dict tagged with
data_age_ms / stale flag or a structured error list with rule_violated codes.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from app.core.config import Settings, get_settings
from app.services.data.market_hours_service import MarketHoursService

logger = logging.getLogger(__name__)

VALIDATED = "validated"
ERRORS = "errors"

RULE_NON_NULL_PRICE = "non_null_price"
RULE_OHLC_CONSISTENCY = "ohlc_consistency"
RULE_INTRADAY_MONOTONIC = "intraday_monotonic"
RULE_FRESHNESS = "freshness_threshold"
RULE_TIMESTAMP = "timestamp_present"


def _utc_now() -> datetime:
    return datetime.now(UTC)


class FreshnessValidator:
    """
    Validates raw payloads returned by the market-data provider.

    Pure validator with no side effects (no logging from inside validation
    paths; callers log the returned error list as appropriate).
    """

    def __init__(
        self,
        market_hours: MarketHoursService,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._market_hours = market_hours
        self._last_intraday_ts: dict[str, datetime] = {}

    # ------------------------------------------------------------------
    # Public validate methods
    # ------------------------------------------------------------------

    def validate_quote(
        self,
        symbol: str,
        raw_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate a raw quote payload.

        Returns dict with either:
            {VALIDATED: True, "data": {...payload tagged with data_age_ms+stale}}
            {VALIDATED: False, ERRORS: [{rule_violated, message, ...}]}
        """
        errors: list[dict[str, Any]] = []
        sym = symbol.upper()

        current_price = raw_payload.get("current_price")
        if current_price is None:
            errors.append({
                "rule_violated": RULE_NON_NULL_PRICE,
                "message": "current_price is null",
                "symbol": sym,
            })
            return _result(errors=errors)

        open_p = raw_payload.get("open")
        high_p = raw_payload.get("high")
        low_p = raw_payload.get("low")
        prev_close = raw_payload.get("previous_close")

        for label, value in (
            ("open", open_p),
            ("high", high_p),
            ("low", low_p),
            ("previous_close", prev_close),
        ):
            if value is None:
                errors.append({
                    "rule_violated": RULE_NON_NULL_PRICE,
                    "message": f"{label} is null",
                    "symbol": sym,
                })
                return _result(errors=errors)

        try:
            c = float(current_price)
            o = float(open_p)
            h = float(high_p)
            low_v = float(low_p)
            adj = raw_payload.get("adjusted_close")
            reference = adj if adj is not None else c
            ref_f = float(reference)
        except (TypeError, ValueError) as exc:
            errors.append({
                "rule_violated": RULE_NON_NULL_PRICE,
                "message": f"price fields not numeric: {exc}",
                "symbol": sym,
            })
            return _result(errors=errors)

        if h < max(o, low_v, c, ref_f) - 1e-9:
            errors.append({
                "rule_violated": RULE_OHLC_CONSISTENCY,
                "message": "high < max(open,low,close,adjusted_close)",
                "symbol": sym,
                "high": h,
            })
            return _result(errors=errors)
        if low_v > min(o, h, c, ref_f) + 1e-9:
            errors.append({
                "rule_violated": RULE_OHLC_CONSISTENCY,
                "message": "low > min(open,high,close,adjusted_close)",
                "symbol": sym,
                "low": low_v,
            })
            return _result(errors=errors)

        freshness_ts = _extract_freshness(raw_payload)
        if freshness_ts is None:
            errors.append({
                "rule_violated": RULE_TIMESTAMP,
                "message": "freshness_ts missing",
                "symbol": sym,
            })
            return _result(errors=errors)

        data_age_ms, stale, threshold_s = self._age_and_stale(freshness_ts)

        validated_data: dict[str, Any] = dict(raw_payload)
        validated_data["symbol"] = sym
        validated_data.setdefault("freshness_ts", freshness_ts)
        validated_data["data_age_ms"] = data_age_ms
        validated_data["stale"] = stale
        validated_data["_threshold_s"] = threshold_s
        return _result(data=validated_data)

    def validate_intraday(
        self,
        symbol: str,
        interval: str,
        raw_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate a raw intraday payload including candle monotonicity.
        """
        errors: list[dict[str, Any]] = []
        sym = symbol.upper()
        candles = raw_payload.get("candles") or []

        if not isinstance(candles, list):
            errors.append({
                "rule_violated": RULE_NON_NULL_PRICE,
                "message": "candles field not a list",
                "symbol": sym,
                "interval": interval,
            })
            return _result(errors=errors)

        last_ts: datetime | None = None
        for idx, candle in enumerate(candles):
            ts = candle.get("timestamp")
            if ts is None:
                errors.append({
                    "rule_violated": RULE_TIMESTAMP,
                    "message": f"candle[{idx}] missing timestamp",
                    "symbol": sym,
                    "interval": interval,
                })
                return _result(errors=errors)
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    errors.append({
                        "rule_violated": RULE_TIMESTAMP,
                        "message": f"candle[{idx}] invalid timestamp",
                        "symbol": sym,
                        "interval": interval,
                    })
                    return _result(errors=errors)
            if not isinstance(ts, datetime):
                errors.append({
                    "rule_violated": RULE_TIMESTAMP,
                    "message": f"candle[{idx}] bad timestamp type",
                    "symbol": sym,
                    "interval": interval,
                })
                return _result(errors=errors)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=UTC)
            else:
                ts = ts.astimezone(UTC)

            o = candle.get("open")
            h = candle.get("high")
            low_v = candle.get("low")
            c = candle.get("close")
            adj = candle.get("adjusted_close", c)
            try:
                of, hf, lf, cf, af = (
                    float(o), float(h), float(low_v), float(c), float(adj),
                )
            except (TypeError, ValueError):
                errors.append({
                    "rule_violated": RULE_NON_NULL_PRICE,
                    "message": f"candle[{idx}] non-numeric price",
                    "symbol": sym,
                    "interval": interval,
                })
                return _result(errors=errors)
            if hf < max(of, lf, cf, af) - 1e-9:
                errors.append({
                    "rule_violated": RULE_OHLC_CONSISTENCY,
                    "message": f"candle[{idx}] high violation",
                    "symbol": sym,
                    "interval": interval,
                })
                return _result(errors=errors)
            if lf > min(of, hf, cf, af) + 1e-9:
                errors.append({
                    "rule_violated": RULE_OHLC_CONSISTENCY,
                    "message": f"candle[{idx}] low violation",
                    "symbol": sym,
                    "interval": interval,
                })
                return _result(errors=errors)

            if last_ts is not None and ts <= last_ts:
                errors.append({
                    "rule_violated": RULE_INTRADAY_MONOTONIC,
                    "message": f"candle[{idx}] ts <= previous candle ts",
                    "symbol": sym,
                    "interval": interval,
                    "ts": ts.isoformat(),
                    "previous_ts": last_ts.isoformat(),
                })
                return _result(errors=errors)
            last_ts = ts

        key = f"{sym}:{interval}"
        store_last = self._last_intraday_ts.get(key)
        if last_ts is not None and store_last is not None and last_ts <= store_last:
            errors.append({
                "rule_violated": RULE_INTRADAY_MONOTONIC,
                "message": "candle set not newer than stored last-good ts",
                "symbol": sym,
                "interval": interval,
                "ts": last_ts.isoformat(),
                "previous_ts": store_last.isoformat(),
            })
            return _result(errors=errors)
        if last_ts is not None:
            self._last_intraday_ts[key] = last_ts

        freshness_ts = _extract_freshness(raw_payload)
        if freshness_ts is None:
            freshness_ts = last_ts or _utc_now()
        data_age_ms, stale, threshold_s = self._age_and_stale(freshness_ts)

        validated_data: dict[str, Any] = dict(raw_payload)
        validated_data["symbol"] = sym
        validated_data["interval"] = interval
        validated_data.setdefault("freshness_ts", freshness_ts)
        validated_data["data_age_ms"] = data_age_ms
        validated_data["stale"] = stale
        validated_data["_threshold_s"] = threshold_s
        return _result(data=validated_data)

    def validate_market_pulse(
        self,
        market: str,
        raw_payload: dict[str, Any],
    ) -> dict[str, Any]:
        errors: list[dict[str, Any]] = []
        freshness_ts = _extract_freshness(raw_payload)
        if freshness_ts is None:
            freshness_ts = _utc_now()
        data_age_ms, stale, threshold_s = self._age_and_stale(freshness_ts)

        validated_data: dict[str, Any] = dict(raw_payload)
        validated_data.setdefault("market", market or "NASDAQ")
        validated_data.setdefault("freshness_ts", freshness_ts)
        validated_data["data_age_ms"] = data_age_ms
        validated_data["stale"] = stale
        validated_data["_threshold_s"] = threshold_s
        if errors:
            return _result(errors=errors)
        return _result(data=validated_data)

    def validate_news_item(
        self,
        raw_payload: dict[str, Any],
    ) -> dict[str, Any]:
        errors: list[dict[str, Any]] = []
        news_id = raw_payload.get("news_id")
        if not news_id:
            errors.append({
                "rule_violated": RULE_NON_NULL_PRICE,
                "message": "news_id missing",
            })
            return _result(errors=errors)

        published_at = raw_payload.get("published_at") or raw_payload.get("freshness_ts")
        freshness_ts: datetime
        if isinstance(published_at, str):
            try:
                freshness_ts = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except ValueError:
                freshness_ts = _utc_now()
        elif isinstance(published_at, datetime):
            freshness_ts = published_at
        else:
            freshness_ts = _utc_now()
        if freshness_ts.tzinfo is None:
            freshness_ts = freshness_ts.replace(tzinfo=UTC)
        else:
            freshness_ts = freshness_ts.astimezone(UTC)

        data_age_ms, stale, threshold_s = self._age_and_stale(freshness_ts)

        validated_data: dict[str, Any] = dict(raw_payload)
        validated_data.setdefault("freshness_ts", freshness_ts)
        validated_data["data_age_ms"] = data_age_ms
        validated_data["stale"] = stale
        validated_data["_threshold_s"] = threshold_s
        return _result(data=validated_data)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _age_and_stale(
        self,
        freshness_ts: datetime,
    ) -> tuple[float, bool, float]:
        """Return (data_age_ms, stale_flag, threshold_seconds)."""
        if freshness_ts.tzinfo is None:
            freshness_ts = freshness_ts.replace(tzinfo=UTC)
        else:
            freshness_ts = freshness_ts.astimezone(UTC)
        now = _utc_now()
        age_s = max(0.0, (now - freshness_ts).total_seconds())
        age_ms = age_s * 1000.0

        market_status = self._market_hours.get_market_status()
        is_trading = market_status.get("is_trading", False)
        if is_trading:
            threshold_s = float(self._settings.LIVE_MAX_QUOTE_AGE_OPEN_S)
        else:
            threshold_s = float(self._settings.LIVE_MAX_QUOTE_AGE_CLOSED_S)

        stale = age_s > threshold_s
        return age_ms, stale, threshold_s


# ----------------------------------------------------------------------
# Module helpers
# ----------------------------------------------------------------------

def _result(
    data: dict[str, Any] | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if errors:
        return {VALIDATED: False, ERRORS: errors}
    assert data is not None
    return {VALIDATED: True, "data": data}


def _extract_freshness(raw_payload: dict[str, Any]) -> datetime | None:
    for key in ("freshness_ts", "timestamp", "fetched_at", "published_at"):
        value = raw_payload.get(key)
        if value is None:
            continue
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(float(value), tz=UTC)
            except (ValueError, OSError):
                continue
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                continue
    return None
