"""
Constants shared across the live streaming pipeline.

Event names, stream health states, and other string literals.
No logic or imports here to avoid cycles.
"""

LIVE_EVENT_QUOTE = "quote"
LIVE_EVENT_INTRADAY = "intraday"
LIVE_EVENT_MARKET_PULSE = "market_pulse"
LIVE_EVENT_SCORE_DELTA = "score_delta"
LIVE_EVENT_NEWS_ITEM = "news_item"
LIVE_EVENT_HEALTH = "health"
LIVE_EVENT_PING = "ping"
LIVE_EVENT_ORDERBOOK = "orderbook"

STREAM_HEALTH_LIVE = "live"
STREAM_HEALTH_DEGRADED = "degraded"
STREAM_HEALTH_STALE = "stale"
STREAM_HEALTH_DISCONNECTED = "disconnected"

VALID_LIVE_EVENTS = frozenset({
    LIVE_EVENT_QUOTE,
    LIVE_EVENT_INTRADAY,
    LIVE_EVENT_MARKET_PULSE,
    LIVE_EVENT_SCORE_DELTA,
    LIVE_EVENT_NEWS_ITEM,
    LIVE_EVENT_HEALTH,
    LIVE_EVENT_PING,
    LIVE_EVENT_ORDERBOOK,
})

VALID_STREAM_HEALTH = frozenset({
    STREAM_HEALTH_LIVE,
    STREAM_HEALTH_DEGRADED,
    STREAM_HEALTH_STALE,
    STREAM_HEALTH_DISCONNECTED,
})

VALID_INTRADAY_INTERVALS = frozenset({"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"})

SYMBOL_MAX_LENGTH = 16
SYMBOL_ALLOWED_CHARSET = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.")
