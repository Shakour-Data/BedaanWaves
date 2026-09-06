"""
Pydantic v2 schemas for live streaming envelopes and payloads.

Every event emitted by the server is wrapped in a LiveEventEnvelope that
carries a monotonically increasing sequence per stream key, a correlation
id for tracing, and the typed payload.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.live.constants import (
    LIVE_EVENT_HEALTH,
    LIVE_EVENT_INTRADAY,
    LIVE_EVENT_MARKET_PULSE,
    LIVE_EVENT_NEWS_ITEM,
    LIVE_EVENT_PING,
    LIVE_EVENT_QUOTE,
    LIVE_EVENT_SCORE_DELTA,
    VALID_LIVE_EVENTS,
    VALID_STREAM_HEALTH,
)


EventType = Literal[
    "quote",
    "intraday",
    "market_pulse",
    "score_delta",
    "news_item",
    "health",
    "ping",
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class _BasePayload(BaseModel):
    """Shared fields for every data payload pushed over the live stream."""

    freshness_ts: datetime = Field(
        ...,
        description="UTC timestamp captured at the moment the provider returned the raw data.",
    )
    received_ts: datetime = Field(
        default_factory=_utc_now,
        description="UTC timestamp captured the moment the server enqueued the event.",
    )
    data_age_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Age of the payload in milliseconds at time of emission (received - freshness).",
    )
    stale: bool = Field(
        default=False,
        description="True when the payload is flagged as older than the SLO threshold.",
    )

    @field_validator("freshness_ts", "received_ts", mode="before")
    @classmethod
    def _coerce_tz(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            return _ensure_utc(value)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"Invalid datetime string: {value}") from exc
            return _ensure_utc(parsed)
        raise ValueError(f"Unsupported datetime value type: {type(value).__name__}")

    @model_validator(mode="after")
    def _populate_age(self) -> "_BasePayload":
        if self.data_age_ms is None:
            self.data_age_ms = max(
                0.0,
                (self.received_ts - self.freshness_ts).total_seconds() * 1000.0,
            )
        return self


class LiveQuotePayload(_BasePayload):
    symbol: str = Field(..., min_length=1, max_length=16)
    current_price: float = Field(..., gt=0)
    change_value: float
    change_percent: float
    open: float
    high: float
    low: float
    previous_close: float
    volume: int = Field(..., ge=0)
    adjusted_close: Optional[float] = None
    market_status: str = "open"
    freshness_label: str = "LIVE"
    is_delayed: bool = False
    data_source: str = "yfinance"

    @field_validator("symbol")
    @classmethod
    def _uppercase(cls, value: str) -> str:
        return value.upper()


class LiveIntradayCandle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int = Field(..., ge=0)
    split_ratio: Optional[float] = None
    source: str = "yfinance"

    @field_validator("timestamp", mode="before")
    @classmethod
    def _ts(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            return _ensure_utc(value)
        if isinstance(value, str):
            return _ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        raise ValueError(f"Unsupported timestamp type: {type(value).__name__}")


class LiveIntradayPayload(_BasePayload):
    symbol: str
    interval: str = "5m"
    candles: List[LiveIntradayCandle]
    market_status: str = "open"
    freshness_label: str = "LIVE"
    data_source: str = "yfinance"

    @field_validator("symbol")
    @classmethod
    def _uppercase(cls, value: str) -> str:
        return value.upper()


class _DimensionScores(BaseModel):
    model_config = {"extra": "allow"}


class LiveMarketPulsePayload(_BasePayload):
    market: str = "NASDAQ"
    composite_price: Optional[float] = None
    composite_change_pct: Optional[float] = None
    active_symbols: int = Field(..., ge=0)
    top_gainer_symbol: Optional[str] = None
    top_gainer_change_pct: Optional[float] = None
    top_loser_symbol: Optional[str] = None
    top_loser_change_pct: Optional[float] = None
    latest_date: Optional[str] = None
    dimension_avg_scores: Dict[str, float] = Field(default_factory=dict)
    symbol_count: int = Field(..., ge=0)


class LiveScoreDeltaPayload(_BasePayload):
    symbol: str
    overall_score: Optional[float] = None
    overall_score_delta: Optional[float] = None
    dimension_scores: Dict[str, float] = Field(default_factory=dict)
    dimension_score_changes: Dict[str, float] = Field(default_factory=dict)
    market: str = "NASDAQ"

    @field_validator("symbol")
    @classmethod
    def _uppercase(cls, value: str) -> str:
        return value.upper()


class LiveNewsPayload(_BasePayload):
    news_id: str
    title: str
    summary: Optional[str] = None
    source: str
    url: Optional[str] = None
    symbols_affected: List[str] = Field(default_factory=list)
    sentiment: Optional[str] = None
    published_at: Optional[datetime] = None

    @field_validator("symbols_affected")
    @classmethod
    def _symbols_upper(cls, values: List[str]) -> List[str]:
        return [v.upper() for v in values]

    @field_validator("published_at", mode="before")
    @classmethod
    def _pub_ts(cls, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return _ensure_utc(value)
        if isinstance(value, str):
            return _ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        raise ValueError(f"Unsupported published_at type: {type(value).__name__}")


class LiveHealthPayload(_BasePayload):
    stream_key: str
    state: str
    retry_after_s: Optional[float] = None
    last_good_freshness_ts: Optional[datetime] = None
    consecutive_failures: int = Field(..., ge=0)
    reason_code: Optional[str] = None
    reason_message: Optional[str] = None

    @field_validator("state")
    @classmethod
    def _valid_state(cls, value: str) -> str:
        if value not in VALID_STREAM_HEALTH:
            raise ValueError(f"Invalid stream state: {value}")
        return value

    @field_validator("last_good_freshness_ts", mode="before")
    @classmethod
    def _last_ts(cls, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return _ensure_utc(value)
        if isinstance(value, str):
            return _ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        raise ValueError(f"Unsupported last_good_freshness_ts type: {type(value).__name__}")


class LivePingPayload(_BasePayload):
    interval_s: float = Field(10.0, gt=0)
    subscription_count: int = Field(0, ge=0)


LivePayload = Union[
    LiveQuotePayload,
    LiveIntradayPayload,
    LiveMarketPulsePayload,
    LiveScoreDeltaPayload,
    LiveNewsPayload,
    LiveHealthPayload,
    LivePingPayload,
]


class LiveEventEnvelope(BaseModel):
    """Wire envelope for every SSE event."""

    event: EventType
    data: Dict[str, Any]
    sequence: int = Field(..., ge=0)
    correlation_id: Optional[str] = None
    stream_key: str

    @field_validator("event")
    @classmethod
    def _event_name(cls, value: str) -> str:
        if value not in VALID_LIVE_EVENTS:
            raise ValueError(f"Invalid event: {value}")
        return value
