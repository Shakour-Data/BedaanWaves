# BEDAANWAVES v2.0.0 — COMPLETE API REFERENCE & FUNCTIONAL SPECIFICATION
## REST API v1 — OpenAPI 3.1 Compatible Functional Spec

**Document ID:** BW-API-REF-v2.0.0  
**Base Path:** `/api/v1`  
**Default Host:** `http://localhost:3000`  
**Auth Scheme:** `Authorization: Bearer <jwt_access_token>` (JWT HS256)  
**Rate Limit:** 100 req/min / 5,000 req/hr (per IP / per token)  
**Content Type:** All request bodies = `application/json`; All responses = `application/json`  
**Character Encoding:** UTF-8 (charset=utf-8)  
**Cache Response Header:** `X-Cache-Status: HIT|MISS|BYPASS|PASS`  
**Trace Response Header:** `X-BW-Trace-ID: <UUIDv4>` (include in every support ticket)

---

## TABLE OF CONTENTS

| Section | Module | # Endpoints |
|---------|--------|-------------|
| §1 | Authentication & Authorization (Auth) | 5 |
| §2 | Password Recovery FSM | 6 |
| §3 | Dashboard Services | 8 |
| §4 | Ranking Services | 4 |
| §5 | Stocks / Symbols | 7 |
| §6 | Market Data & Live Feeds | 6 |
| §7 | Forecast (ML Prediction Engine) | 7 |
| §8 | Alerting Engine | 8 |
| §9 | Watchlists | 6 |
| §10 | Portfolios | 7 |
| §11 | News & Sentiment (NLP) | 5 |
| §12 | Comparison Engine | 3 |
| §13 | Users & Preferences | 8 |
| §14 | System, Health, & Admin | 10 |
| **Total** | | **90 Endpoints** |

All 28 route files live at: [backend/app/api/routes/](file:///e:/BedaanWaves/backend/app/api/routes/)

---

## CONVENTIONS

### Standard Error Envelope
Every 4xx/5xx response uses this envelope:
```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Incorrect username or password",
    "trace_id": "abc-123-def-456",
    "timestamp": "2026-09-05T14:30:00Z",
    "details": []
  }
}
```
HTTP status codes follow RFC 7231 semantics precisely:
| Code | Semantic | When to use |
|------|----------|-------------|
| 200 OK | Success (GET/PUT/PATCH synchronous) | Entity returned in body |
| 201 CREATED | New entity persisted (POST) | POST /alerts, POST /watchlists |
| 202 ACCEPTED | Async job queued (not yet done) | Forecast long-running, batch ingestion |
| 204 NO CONTENT | Delete successful, no body | DELETE endpoints |
| 400 BAD REQUEST | Validation failure / bad inputs | Schema, enum, format errors |
| 401 UNAUTHORIZED | Missing or invalid JWT | Login required |
| 403 FORBIDDEN | Valid token but insufficient role | RBAC check failure |
| 404 NOT FOUND | Entity does not exist | Symbol/ticker not found |
| 409 CONFLICT | State conflict (duplicate) | Username/email exists on register |
| 422 UNPROCESSABLE | Semantic business rule violation | Quota exceeded, invalid horizon |
| 429 TOO MANY REQUESTS | Rate limit breached | See Retry-After header (seconds) |
| 500 INTERNAL ERROR | Unhandled exception | Report with trace_id |
| 502 BAD GATEWAY | Upstream provider down | Market data API down |
| 503 SERVICE UNAVAIL | Temporarily unavailable (Redis failover) | See Retry-After |

### Pagination Standard
Query params: `?limit=50&offset=0&sort_by=<field>&order=desc`
Response envelope:
```json
{
  "data": [ ... ],
  "pagination": { "limit": 50, "offset": 0, "total": 100, "has_next": true }
}
```

---

## §1 AUTHENTICATION & AUTHORIZATION (Auth)
**Source:** [auth.py](file:///e:/BedaanWaves/backend/app/api/routes/auth.py)

### 1.1 POST /auth/register — Register New User
**Auth Required:** No  
**Rate Limit:** 5 req/min (anti-bot)

Input:
```json
{
  "username": "jane_trader",
  "email": "jane@bedaanwaves.com",
  "password": "Str0ng!Pass#2026",
  "full_name": "Jane Trader"
}
```
Validation: username 3-50 chars (alphanumeric + _.-), email RFC 5322, password min 8 chars with 1× uppercase+lowercase+digit+special, full_name 1-100 chars.

Output 201 Created:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...<180 chars>",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...<200 chars>",
  "token_type": "bearer",
  "expires_in": 1800,
  "scope": "USER"
}
```

### 1.2 POST /auth/login — Obtain Token Pair
**Auth Required:** No

Input:
```json
{
  "username": "jane_trader",
  "password": "Str0ng!Pass#2026"
}
```
Output 200 OK: Same envelope as §1.1 (access_token + refresh_token)

### 1.3 POST /auth/refresh — Rotate Refresh Token
**Auth Required:** Refresh token (in body, NOT Bearer header)

Input: `{ "token": "<refresh_token>" }`

Output 200 OK: New `{ access_token, refresh_token, expires_in, token_type }`
- Old refresh_token is revoked atomically (one-time-use, per RFC 6819 §5.2.2.1 replay protection).

### 1.4 POST /auth/logout — Revoke Current Token
**Auth Required:** Bearer (access token)  
Output: 204 No Content
- Side effect: Refresh tokens for this user with `expires_at > now` are marked `revoked=true`.

### 1.5 GET /auth/me — Current User Profile
**Auth Required:** Bearer

Output 200 OK:
```json
{
  "id": "uuid-uuid-uuid-uuid",
  "username": "jane_trader",
  "email": "jane@bedaanwaves.com",
  "full_name": "Jane Trader",
  "role": "USER",
  "email_verified": true,
  "created_at": "2026-08-01T09:00:00Z",
  "last_login_at": "2026-09-05T14:29:00Z",
  "preferences": {
    "default_dashboard_date": "last_trading_day",
    "theme": "light",
    "chart_timeframe": "1M",
    "number_format": "us",
    "currency": "USD",
    "date_format": "mm/dd/yyyy"
  }
}
```

---

## §2 PASSWORD RECOVERY FSM (Finite State Machine)
**Source:** [password_reset.py](file:///e:/BedaanWaves/backend/app/api/routes/password_reset.py)
**Related Frontend FSM Hook:** [usePasswordRecoveryFSM.ts](file:///e:/BedaanWaves/frontend/src/hooks/usePasswordRecoveryFSM.ts)

State Machine: `INIT → CODE_REQUESTED → CODE_VERIFIED → PASSWORD_CHANGED` (one-way transitions only)

### 2.1 POST /password-reset/request — Initiate Recovery (State: INIT → CODE_REQUESTED)
Input: `{ "email": "jane@bedaanwaves.com" }`
Output: 202 Accepted (ALWAYS returns 202 regardless of whether email exists in DB — prevents user enumeration attack)
- Side effect: 6-digit numeric OTP code generated, stored hashed with bcrypt(rounds=10), TTL = 15 minutes. Email dispatched via SMTP (staging/dev → logged to console).

### 2.2 POST /password-reset/verify-code — Submit OTP (State: CODE_REQUESTED → CODE_VERIFIED)
Input:
```json
{
  "email": "jane@bedaanwaves.com",
  "code": "739104",
  "request_id": "req-uuid-from-step-2.1"
}
```
Output 200: `{ "reset_token": "<short-lived-JWT-5min>", "state": "CODE_VERIFIED" }`
Output 422: `{ "error": "PW_RESET_INVALID_CODE" }` (max 3 attempts per request_id — then reset_token invalidated)

### 2.3 POST /password-reset/confirm — Set New Password (State: CODE_VERIFIED → PASSWORD_CHANGED)
Input:
```json
{
  "reset_token": "<from step-2.2>",
  "new_password": "NewStr0ng!Pass#2026",
  "confirm_password": "NewStr0ng!Pass#2026"
}
```
Output 204 No Content (success) / 401 (reset_token expired/invalid) / 422 (mismatch or same-as-previous)
- Side effects: All existing refresh tokens for this user are revoked. User forced to log in again on all sessions.

### 2.4 GET /password-reset/{request_id}/state — Poll FSM State (frontend UX helper)
Output 200: `{ "state": "CODE_REQUESTED", "attempts_remaining": 2, "expires_at_iso": "2026-09-05T14:45:00Z" }`

---

## §3 DASHBOARD SERVICES
**Source:** [dashboard.py](file:///e:/BedaanWaves/backend/app/api/routes/dashboard.py)

### 3.1 GET /dashboard/general — Overall Market Summary
**Auth Required:** USER

Query Params: (none)

Output 200 OK:
```json
{
  "market_date": "2026-09-04",
  "next_trading_day": "2026-09-05",
  "aggregates": {
    "n_symbols_scored": 2837,
    "avg_total_score": 58.4,
    "pct_buy_or_better": 31.2,
    "pct_sell_or_worse": 19.8,
    "top_sector": "Technology",
    "bottom_sector": "Energy"
  },
  "top_performers": [
    { "symbol": "NVDA", "total_score": 92.1, "grade": "A_STRONG_BUY", "sector": "Technology" }
  ],
  "bottom_performers": [
    { "symbol": "XOM", "total_score": 18.3, "grade": "E_STRONG_SELL", "sector": "Energy" }
  ]
}
```

### 3.2 GET /dashboard/technical — Technical Dimension Dashboard
Query: `?limit=50` (1 ≤ limit ≤ 200)  
Output: Dimension dashboard structure (identical envelope for 3.3, 3.4, 3.5):
```json
{
  "dimension": "technical",
  "average": 56.7,
  "distribution_buckets": [
    { "range": "0-20", "count": 112 },
    { "range": "21-40", "count": 498 },
    { "range": "41-60", "count": 1204 },
    { "range": "61-80", "count": 782 },
    { "range": "81-100", "count": 241 }
  ],
  "top_symbols": [ { "symbol": "AAPL", "score": 94.2, "sub_scores": { "momentum": 96, "rsi": 88, ... } } ]
}
```

### 3.3 GET /dashboard/fundamental — Fundamental Dimension
Query: `?limit=50`

### 3.4 GET /dashboard/risk — Risk Dimension Dashboard
Query: `?limit=50`

### 3.5 GET /dashboard/board — Board View (Full Symbol Cards Grid)
Query: `?limit=50`

### 3.6 GET /dashboard/news — Sentiment + News Headlines
Query: `?limit=50` (1 ≤ limit ≤ 200)

Output 200:
```json
{
  "sentiment_24h": { "positive_pct": 38.2, "neutral_pct": 49.7, "negative_pct": 12.1, "composite": 0.14 },
  "top_articles": [
    {
      "id": "news-uuid",
      "headline": "Fed signals pause, tech rallies",
      "source": "Reuters",
      "published_at": "2026-09-05T13:00:00Z",
      "sentiment": "POSITIVE",
      "sentiment_score": 0.62,
      "relevant_symbols": ["AAPL", "MSFT", "NVDA"],
      "url": "https://reuters.com/.../"
    }
  ]
}
```

### 3.7 GET /dashboard/market-score-trend — Market Aggregate Score History
**SOURCE:** [market_score_trend_service.py](file:///e:/BedaanWaves/backend/app/services/analysis/market_score_trend_service.py)

Query: `?window_days=90&aggregate=market_mean` (1 ≤ window_days ≤ 365)

Output 200:
```json
{
  "window_days": 90,
  "data_points": 63,
  "series": [
    { "date": "2026-06-04", "market_mean_score": 54.1, "symbol_count": 2798, "cache_status": "HIT" },
    { "date": "2026-06-05", "market_mean_score": 54.8, "symbol_count": 2801, "cache_status": "HIT" }
  ]
}
```

### 3.8 GET /dashboard/spider/{symbol} — Single Symbol Spider Axes
Query: `?effective_date=2026-09-04` (defaults to last trading day)

Output 200:
```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "market_cap_usd": 3450000000000,
  "effective_date": "2026-09-04",
  "total_score": 87.3,
  "grade": "A_STRONG_BUY",
  "dimensions": {
    "profitability": { "score": 92.1, "sub_aspects": { "gross_margin": 43.2, "roe": 1.47, "roic": 0.62 } },
    "valuation":     { "score": 78.5, "sub_aspects": { "pe_fwd": 28.1, "ev_ebitda": 22.4 } },
    "momentum":      { "score": 84.2, "sub_aspects": { "rsi_14": 68, "macd_hist": 1.2 } },
    "volatility":    { "score": 81.0, "sub_aspects": { "beta": 1.28, "var_95": -0.028 } },
    "quality":       { "score": 90.3, "sub_aspects": { "piotroski_f": 8, "altman_z": 4.1 } },
    "growth":        { "score": 78.9, "sub_aspects": { "rev_yoy": 0.082, "eps_yoy": 0.11 } }
  }
}
```

---

## §4 RANKING SERVICES
**Source:** [ranking.py](file:///e:/BedaanWaves/backend/app/api/routes/ranking.py)

### 4.1 GET /ranking/nasdaq — NASDAQ Multi-Factor Leaderboard
**Auth Required:** USER

Query Params:
| Param | Type | Range | Default | Description |
|-------|------|-------|---------|-------------|
| limit | int | 1-200 | 50 | Rows per page |
| offset | int | 0+ | 0 | Pagination offset |
| sort_by | enum | `overall_score, profitability, valuation, momentum, volatility, quality, growth, symbol, market_cap` | overall_score | Column to sort by |
| order | enum | `asc, desc` | desc | Sort order |
| sector | string | GICS Sector OR `ALL` | ALL | Filter by sector |
| min_profitability | float | 0-100 | 0 | Dimension threshold |
| min_valuation | float | 0-100 | 0 | Dimension threshold |
| min_momentum | float | 0-100 | 0 | Dimension threshold |
| min_volatility | float | 0-100 | 0 | Dimension threshold |
| min_quality | float | 0-100 | 0 | Dimension threshold |
| min_growth | float | 0-100 | 0 | Dimension threshold |
| universe | enum | `nasdaq_all, nasdaq100, composite` | nasdaq_all | Stock universe |

Output 200 (rows array — every row = 1 ranked stock):
```json
{
  "data": [
    {
      "rank": 1,
      "symbol": "NVDA",
      "company_name": "NVIDIA Corporation",
      "sector": "Technology",
      "market_cap_usd": 3200000000000,
      "price_usd": 128.5,
      "price_change_1d_pct": 2.43,
      "total_score": 92.1,
      "grade": "A_STRONG_BUY",
      "profitability": 94.2,
      "valuation": 81.8,
      "momentum": 96.4,
      "volatility": 78.3,
      "quality": 89.7,
      "growth": 93.5
    }
  ],
  "pagination": { "limit": 50, "offset": 0, "total": 2837, "has_next": true },
  "filters_applied": { "sector": "ALL", "min_total_score": 0.0, "universe": "nasdaq_all" }
}
```

### 4.2 GET /ranking/sector/{sector} — Ranking Within Single Sector
Path: `{sector}` = Technology / Healthcare / Consumer-Discretionary / Financials / Industrials / Energy / Utilities / Real-Estate / Materials / Communication-Services / Consumer-Staples

Query: `?limit=50&sort_by=overall_score&order=desc`

### 4.3 GET /ranking/export — CSV Export of Current Filters
**Auth Required:** USER (rate limit: 10 exports/day)
Query params: Same as §4.1 (no pagination; dumps entire filtered result set)

Response: Content-Type `text/csv`, Content-Disposition `attachment; filename="nasdaq-ranking-2026-09-05.csv"`
CSV columns: `rank,symbol,company_name,sector,market_cap_usd,price_usd,price_change_1d_pct,total_score,grade,profitability,valuation,momentum,volatility,quality,growth`

### 4.4 GET /ranking/movers — Top 10 Gainers + Top 10 Losers (1D % Change)
Output 200:
```json
{
  "as_of": "2026-09-04T20:00:00Z",
  "top_gainers": [ { "symbol": "SMCI", "change_1d_pct": 18.2, "reason": "Earnings beat" }, ... ],
  "top_losers":  [ { "symbol": "FRC",  "change_1d_pct": -12.7, "reason": "Sector selloff" }, ... ]
}
```

---

## §5 STOCKS / SYMBOLS
**Source:** [stocks.py](file:///e:/BedaanWaves/backend/app/api/routes/stocks.py), [symbols.py](file:///e:/BedaanWaves/backend/app/api/routes/symbols.py)

### 5.1 GET /stocks/{symbol} — Symbol Overview (Full Payload)
Path: `{symbol}` = NASDAQ-listed ticker e.g. `AAPL`, `MSFT`, `NVDA`

Output 200:
```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc.",
  "gics_sector": "Technology",
  "gics_sub_industry": "Technology Hardware, Storage & Peripherals",
  "country": "United States",
  "exchange": "NASDAQ",
  "market_cap_usd": 3450000000000,
  "shares_outstanding": 15204000000,
  "last_close_price_usd": 226.89,
  "prev_close_price_usd": 223.12,
  "change_1d_usd": 3.77,
  "change_1d_pct": 1.69,
  "week_52_high_usd": 237.23,
  "week_52_low_usd": 164.08,
  "avg_volume_30d": 52380000,
  "dividend_yield_pct": 0.52,
  "pe_ratio_ttm": 29.4,
  "eps_ttm_usd": 7.72,
  "listing_date": "1980-12-12",
  "is_nasdaq100_constituent": true,
  "note_nasdaq_disambiguation": "AAPL is a constituent of BOTH Nasdaq Composite (IXIC) and Nasdaq-100 (NDX). Trading NAS100 CFD = NDX index, AAPL weight ~13%."
}
```
Output 404: `{ "error": { "code": "SYMBOL_NOT_FOUND_IN_NASDAQ_UNIVERSE", ... } }`

### 5.2 GET /stocks/{symbol}/prices — OHLCV Candles (Historical)
Query Params:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| timeframe | enum: 1D,1W,1M,3M,6M,1Y,5Y,MAX | 3M | Aggregation window |
| from | ISO date | 3 months ago | Inclusive start (YYYY-MM-DD) |
| to | ISO date | today | Inclusive end |

Output 200:
```json
{
  "symbol": "AAPL",
  "timeframe": "3M",
  "count": 63,
  "candles": [
    { "time": "2026-06-04T00:00:00Z", "open": 210.1, "high": 212.8, "low": 208.3, "close": 211.4, "volume": 58200000 }
  ],
  "next_fetch_at": "2026-09-05T20:00:00Z"
}
```

### 5.3 GET /stocks/{symbol}/scores — Dimensional + Sub-Aspect Scores
Query: `?effective_date=2026-09-04` (defaults to last trading day)
Output: Identical shape to §3.8 spider axes

### 5.4 GET /stocks/{symbol}/score-history — Historical Score Series
Query: `?window_days=90` (1-730)
Output 200:
```json
{
  "symbol": "AAPL",
  "window_days": 90,
  "series": [ { "date": "...", "total_score": 82.4, "dimensions": {...} } ],
  "trend_1m_pct_change": 3.7
}
```

### 5.5 GET /stocks/{symbol}/financials — Quarterly Financial Statements
Query: `?periods=8` (last N quarters, max 24)

Output 200:
```json
{
  "symbol": "AAPL",
  "fiscal_currency": "USD",
  "income_statement": [
    { "period_end": "2026-06-30", "fiscal_quarter": "FY2026-Q3", "revenue": 85780000000, "gross_profit": 38300000000, "operating_income": 26800000000, "net_income": 22400000000, "eps_diluted_usd": 1.47 }
  ],
  "balance_sheet": [ { "period_end": "...", "total_assets": 354000000000, ... } ],
  "cash_flow": [ { "period_end": "...", "operating_cf": 28900000000, ... } ]
}
```

### 5.6 GET /stocks/{symbol}/news — Ticker-Specific News Feed
Query: `?limit=20` (1-100)
Output: Same news-article array as §3.6 but filtered to relevant_symbols includes symbol.

### 5.7 GET /symbols/search — Fuzzy Symbol/Company Name Search
Query: `?q=AAPL&limit=10` (q = 1-20 chars)
Output 200:
```json
{
  "query": "AAPL",
  "results": [
    { "symbol": "AAPL", "company_name": "Apple Inc.", "sector": "Technology", "match_type": "EXACT_SYMBOL" },
    { "symbol": "AAPL.PR", "company_name": "Apple Preferred", "sector": "Technology", "match_type": "PREFIX_SYMBOL" }
  ],
  "disambiguation_banner": "If you searched NAS100/NDX/IXIC — open docs for Nasdaq Composite vs Nasdaq-100 distinction."
}
```

---

## §6 MARKET DATA & LIVE FEEDS
**Source:** [live.py](file:///e:/BedaanWaves/backend/app/api/routes/live.py), [live_sse.py](file:///e:/BedaanWaves/backend/app/api/routes/live_sse.py), [market.py](file:///e:/BedaanWaves/backend/app/api/routes/market.py), [market_data.py](file:///e:/BedaanWaves/backend/app/api/routes/market_data.py)

### 6.1 GET /market/hours — Current Market Status + Holiday Calendar
Output 200:
```json
{
  "now_utc": "2026-09-05T14:30:00Z",
  "status": "CLOSED",       // OPEN / PRE_MARKET / AFTER_HOURS / CLOSED
  "current_session": { "opens_at": "2026-09-05T13:30:00Z", "closes_at": "2026-09-05T20:00:00Z" },
  "next_holiday": { "date": "2026-11-26", "name": "Thanksgiving Day", "days_until": 82 },
  "is_weekend": true
}
```

### 6.2 GET /market/quote/{symbol} — Delayed Spot Quote (15-min)
Output 200: `{ "symbol": "AAPL", "price_usd": 226.89, "bid": 226.88, "ask": 226.90, "volume": 48100000, "delay_seconds": 900, "source": "Nasdaq TotalView-ITCH delayed feed" }`

### 6.3 GET /live/sse — REAL-TIME STREAMING TICKER (Server-Sent Events)
**Auth Required:** Bearer token (query param: `?token=<access_token>`)

Client opens EventSource on `http://localhost:3000/api/v1/live/sse?token=<jwt>&symbols=AAPL,MSFT,NVDA`.

Server events (one per second per subscribed symbol):
```
event: tick
id: tick-1725546600-0001
data: {"symbol":"AAPL","price_usd":226.89,"change_pct":1.69,"volume":48100000,"timestamp":"2026-09-05T14:30:00Z","source":"SSE-REALTIME"}

event: market_status
id: status-2026-09-05
data: {"status":"OPEN"}

event: alert
id: alert-abc
data: {"alert_id":"uuid","symbol":"AAPL","type":"PRICE_ABOVE","threshold":226.00,"actual":226.89,"fired_at":"..."}
```
- Throttle: 1 tick/sec per symbol (aggregate last within window).
- Keep-alive: If no tick, send `: sse-keepalive` comment every 15 seconds (prevents idle proxy close).

### 6.4 GET /market/indices/{index_ticker} — Index Spot Value
Path: `{index_ticker}` ∈ { `NDX` (Nasdaq-100), `IXIC` (Nasdaq Composite), `QQQ` (ETF proxy) }

Output 200:
```json
{
  "ticker": "NDX",
  "full_name": "Nasdaq-100 Index (NDX)",
  "cfd_disambiguation": "This index (NDX) is what CFD brokers quote as 'NAS100' on MetaTrader/cTrader/TradingView. It is NOT the same as IXIC (Composite).",
  "value": 19842.71,
  "change_1d_points": 412.34,
  "change_1d_pct": 2.12,
  "close_prev": 19430.37,
  "constituent_count": 100,
  "top_weightings": [ { "symbol": "AAPL", "weight_pct": 13.4 }, { "symbol": "MSFT", "weight_pct": 12.1 }, { "symbol": "NVDA", "weight_pct": 9.2 } ]
}
```

### 6.5 GET /market/movers — Quick Index-level Gainers/Losers (§4.4 alias, cached 10s TTL)
### 6.6 GET /market/sectors — All 11 GICS Sectors Aggregated Performance
Output 200:
```json
[ { "sector": "Technology", "constituent_count": 714, "avg_score_1d_change_pct": 2.8, "heat_value": 91.3 }, ... ]
```

---

## §7 FORECAST (ML PREDICTION ENGINE)
**Source:** [forecast.py](file:///e:/BedaanWaves/backend/app/api/routes/forecast.py#L1-L625)  
**Related Services:** [prediction_service.py](file:///e:/BedaanWaves/backend/app/services/ml/prediction_service.py), [time_series_forecasting_service.py](file:///e:/BedaanWaves/backend/app/services/ml/time_series_forecasting_service.py)

### 7.1 POST /forecast/price — Price Prediction (Core Endpoint)
**Auth Required:** USER  
**Rate Limit:** USER = 50/day, ANALYST = 500/day, ADMIN = unlimited  
**Quota Header on response:** `X-RateLimit-Forecast-Remaining: 43/50`

Input:
```json
{
  "symbol": "AAPL",
  "model": "ensemble",
  "horizon": "14d",
  "confidence_level": 0.95,
  "include_history": true,
  "regime_filter": true,
  "features": {
    "technical_indicators": true,
    "fundamental_data": true,
    "sentiment_scores": true,
    "market_context": true,
    "sector_performance": false
  }
}
```

Input field enums:
| Field | Allowed values |
|-------|---------------|
| model | `arima`, `lstm`, `prophet`, `xgboost`, `ensemble` (default) |
| horizon | `1d`, `3d`, `7d`, `14d` (default), `30d`, `90d`, `180d`, `365d` |
| confidence_level | 0.80, 0.90, 0.95 (default), 0.99 |

Output 200 (HTTP 200 synchronous for horizons ≤ 30d; 202 Accepted with job_id for horizons ≥ 90d):
```json
{
  "request_id": "forecast-uuid",
  "symbol": "AAPL",
  "model_used": "ENSEMBLE_WEIGHTED_04ARIMA_06LSTM",
  "horizon_days": 14,
  "as_of_price_usd": 226.89,
  "as_of_date": "2026-09-04",
  "forecast_value_usd": 241.72,
  "implied_change_pct": 6.54,
  "directional_bias": "BULLISH",
  "confidence_grade": "A",
  "model_confidence_interval": { "level": 0.95, "lower_usd": 233.11, "upper_usd": 250.33 },
  "warning_flags": [],
  "series": [
    { "t_plus": 1,  "date": "2026-09-05", "forecast_usd": 228.12, "lower_usd": 226.10, "upper_usd": 230.14 },
    { "t_plus": 2,  "date": "2026-09-08", "forecast_usd": 229.44, "lower_usd": 226.51, "upper_usd": 232.37 },
    { "t_plus": 14, "date": "2026-09-25", "forecast_usd": 241.72, "lower_usd": 233.11, "upper_usd": 250.33 }
  ],
  "historical_series": [ { "date": "...", "close_usd": 226.89 } ],
  "feature_importance_top5": [
    { "feature": "close_price_lag_1", "importance_gini": 0.314 },
    { "feature": "rsi_14",           "importance_gini": 0.182 },
    { "feature": "macd_signal",      "importance_gini": 0.098 },
    { "feature": "earnings_surprise","importance_gini": 0.077 },
    { "feature": "sentiment_comp",   "importance_gini": 0.052 }
  ],
  "backtest_metrics": {
    "train_window": "2025-01-01 → 2026-07-31",
    "holdout_window": "2026-08-01 → 2026-09-04",
    "holdout_mape_pct": 4.2,
    "holdout_rmse_usd": 7.88,
    "directional_accuracy_pct": 72.4,
    "volatility_regime_detected": "MEDIUM"
  },
  "disclaimer": "FORECAST IS RESEARCH DATA, NOT FINANCIAL ADVICE. SEE §7 OF USER MANUAL."
}
```

Warning flags (array of strings; empty if no issues):
- `"LOW_VARIANCE_INPUT_SERIES"` — flat historical series, treat output as unreliable
- `"HETEROSCEDASTIC_DETECTED"` — variance non-stationary; CI widens
- `"INSUFFICIENT_HISTORY"` — < 120 data points; switch to simpler ARIMA fallback
- `"REGIME_SHIFT_DETECTED_LAST_10D"` — structural break detected in window

### 7.2 POST /forecast/trend — Direction-Only Classifier
Input: `{ "symbol", "horizon":"14d", "features": {...} }`
Output 200: `{ "direction": "UP", "prob_up": 0.64, "prob_down": 0.22, "prob_sideways": 0.14, "entropy": 0.93 }`

### 7.3 POST /forecast/batch — Multi-Symbol Batch Forecast
**Auth Required:** ANALYST  
Input: `{ "symbols": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AVGO","PEP","COST"], "model":"ensemble","horizon":"14d" }` (max 100 symbols)
Output 202 Accepted with job_id + progress endpoint ref:
```json
{ "job_id": "batch-uuid", "status": "QUEUED", "eta_seconds": 78, "progress_url": "/api/v1/ml/jobs/batch-uuid" }
```

### 7.4 GET /forecast/models — Model Registry (Inventory)
Output 200:
```json
[
  { "model_id": "arima-v2.1.0", "family": "ARIMA", "params": { "order": [2,1,2], "seasonal_order": [1,1,1,5] }, "status": "ACTIVE", "mape_holdout_30d_pct": 5.8 },
  { "model_id": "lstm-v3.0.0", "family": "LSTM", "params": { "layers": 2, "units": 128, "dropout": 0.2, "seq_len": 60 }, "status": "ACTIVE", "mape_holdout_30d_pct": 4.3 },
  { "model_id": "ensemble-v1.5.0", "family": "STACKED", "weights": { "arima": 0.4, "lstm": 0.6 }, "status": "DEFAULT", "mape_holdout_30d_pct": 3.9 }
]
```

### 7.5 GET /forecast/models/{model_id} — Single Model Details
Path: model_id from §7.4 list

### 7.6 GET /forecast/performance/{model_id} — Historical Backtest KPIs
Output: Timeseries of monthly MAPE, MAE, RMSE, Directional Accuracy since model went live.

### 7.7 POST /forecast/backtest — Custom Holdout Backtest
**Auth Required:** ANALYST  
Input: `{ "symbol", "model", "horizon":"30d", "train_start":"2025-01-01", "holdout_start":"2026-06-01", "holdout_end":"2026-09-01" }`
Output 202 Accepted (async — long-running for LSTM retrain). Retrievable via job progress endpoint.

---

## §8 ALERTING ENGINE
**Source:** [alerts.py](file:///e:/BedaanWaves/backend/app/api/routes/alerts.py), [notifications.py](file:///e:/BedaanWaves/backend/app/api/routes/notifications.py)

### 8.1 POST /alerts — Create New Alert
**Auth Required:** USER  
Quota: USER = 20 concurrent, ANALYST = 200, ADMIN = unlimited

Input:
```json
{
  "symbol": "AAPL",
  "alert_type": "PRICE_ABOVE",
  "threshold": 250.0,
  "timeframe": "1d",
  "message": "AAPL broke 250 resistance",
  "channels": { "in_app": true, "email": true, "browser_push": true },
  "cooldown_seconds": 3600,
  "expires_at": "2026-12-31T23:59:59Z"
}
```
alert_type enum: `PRICE_ABOVE`, `PRICE_BELOW`, `PCT_CHANGE_1D_ABS`, `RSI_OVERBOUGHT`, `RSI_OVERSOLD`, `SMA_50_CROSS_ABOVE_200`, `SMA_50_CROSS_BELOW_200`, `DIMENSION_SCORE_ABOVE`, `DIMENSION_SCORE_BELOW`

Output 201 Created:
```json
{
  "alert_id": "alert-uuid",
  "status": "ACTIVE",
  "symbol": "AAPL",
  "alert_type": "PRICE_ABOVE",
  "threshold": 250.0,
  "current_value": 226.89,
  "created_at": "2026-09-05T14:30:00Z",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

### 8.2 GET /alerts — List All Alerts (Paginated, Filterable)
Query: `?status=ACTIVE&symbol=AAPL&limit=50&offset=0`
status enum filter: `ACTIVE | FIRED | ACKNOWLEDGED | PAUSED | EXPIRED`

### 8.3 GET /alerts/{alert_id} — Single Alert
Output 404 if wrong user (RBAC per user_id).

### 8.4 PATCH /alerts/{alert_id} — Modify Alert
Partial update: Any field from §8.1 except `alert_id`, `created_at`, `symbol`.

### 8.5 POST /alerts/{alert_id}/pause — Pause Alert (Skip Triggers)
Output: 200 → `{ "alert_id", "status": "PAUSED", "resumed_at": null }`

### 8.6 POST /alerts/{alert_id}/resume — Resume Alert from Pause
Output: 200 → `{ "alert_id", "status": "ACTIVE", "resumed_at": "..." }`

### 8.7 DELETE /alerts/{alert_id} — Permanently Remove Alert
Output: 204 No Content

### 8.8 GET /alerts/{alert_id}/history — Trigger Event History
Output 200:
```json
[ { "fired_at": "2026-09-02T19:45:12Z", "actual_value": 251.2, "threshold": 250.0, "channels_delivered": ["in_app", "email"], "acknowledged": true, "acknowledged_at": "2026-09-02T20:02:10Z" } ]
```

---

## §9 WATCHLISTS
**Source:** [watchlists.py](file:///e:/BedaanWaves/backend/app/api/routes/watchlists.py)

### 9.1 POST /watchlists — Create
Input: `{ "name": "FANG+ Tech", "description": "Top 10 mega-cap tech" }`
Output: 201 → `{ "watchlist_id": "wl-uuid", "name": "...", "item_count": 0, "created_at": "..." }`

### 9.2 GET /watchlists — List User's Watchlists
Output 200: `[{ "watchlist_id", "name", "item_count", "avg_total_score": 81.2 }, ...]`

### 9.3 GET /watchlists/{watchlist_id} — Single Watchlist Items
Output: Item array with full scores (same as §5.3 per symbol)

### 9.4 POST /watchlists/{watchlist_id}/items — Add One or Many Symbols
Input: `{ "symbols": ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","PEP","COST"] }`
Output 201: `{ "added": 10, "skipped": [ { "symbol": "NFLX", "reason": "ALREADY_PRESENT" } ] }`

### 9.5 DELETE /watchlists/{watchlist_id}/items/{symbol} — Remove Single Item
Output: 204 No Content

### 9.6 DELETE /watchlists/{watchlist_id} — Delete Entire Watchlist
Output: 204 No Content

---

## §10 PORTFOLIOS
**Source:** [portfolios.py](file:///e:/BedaanWaves/backend/app/api/routes/portfolios.py)

### 10.1 POST /portfolios — Create Portfolio
Input: `{ "name": "Core Long-Term", "base_currency": "USD", "description": "Buy-and-hold" }`

### 10.2 GET /portfolios — List User's Portfolios (Summary Cards)
Output: `[{ "portfolio_id", "name", "holding_count": 8, "total_market_value_usd": 128400, "total_unrealized_pl_usd": 12400, "total_unrealized_pl_pct": 10.68, "beta": 1.14, "sharpe_ratio_1y": 1.32 }]`

### 10.3 GET /portfolios/{portfolio_id} — Full Holdings View
Output:
```json
{
  "overview": { ... same shape as list-item in 10.2 ... },
  "holdings": [ { "symbol": "AAPL", "quantity": 50, "avg_cost_usd": 190.5, "current_price_usd": 226.89, "market_value_usd": 11344.5, "unrealized_pl_usd": 1819.5, "unrealized_pl_pct": 19.1, "weight_pct": 8.84 } ],
  "allocation_by_sector": [ { "sector": "Technology", "value_usd": 82300, "pct": 64.1 }, ... ],
  "risk_metrics": { "beta": 1.14, "sharpe_ratio_1y": 1.32, "var_95_daily_pct": -1.8, "max_drawdown_1y_pct": -12.4, "num holdings": 8 }
}
```

### 10.4 POST /portfolios/{portfolio_id}/transactions — Add Single Transaction
Input: `{ "date": "2026-01-15", "symbol": "AAPL", "quantity": 50, "price_usd": 190.50, "type": "BUY", "fees_usd": 4.95, "notes": "..." }`
type enum: `BUY`, `SELL`, `DIVIDEND`, `STOCK_SPLIT`
Output 201 → transaction_id + recalculated portfolio aggregates.

### 10.5 POST /portfolios/{portfolio_id}/transactions/import — Bulk CSV Import
Content-Type: `multipart/form-data`, field = `file` (UTF-8 CSV). CSV header: `Date,Symbol,Quantity,Price,Type,Fees,Notes`
Output 200:
```json
{ "parsed_rows": 120, "imported_rows": 117, "skipped_rows": 3, "skip_reasons": [ { "row": 48, "reason": "SYMBOL_NOT_IN_UNIVERSE", "raw_csv_row": "2026-03-01,XOM,100,110.00,BUY,0.00" } ] }
```

### 10.6 GET /portfolios/{portfolio_id}/performance — Historical MTM Series
Query: `?window_days=180&benchmark_symbol=^NDX`
Output: Time series (date, portfolio_value_usd, benchmark_value_relative=100, daily_pl_usd, daily_pl_pct)

### 10.7 DELETE /portfolios/{portfolio_id} — Delete Portfolio
Output: 204 No Content. (Soft-delete: rows retained with `deleted_at` timestamp for 90-day recovery by ADMIN.)

---

## §11 NEWS & SENTIMENT (NLP)
**Source:** [news.py](file:///e:/BedaanWaves/backend/app/api/routes/news.py)
**NLP Services:** [sentiment_analysis_service.py](file:///e:/BedaanWaves/backend/app/services/nlp/sentiment_analysis_service.py), [news_summarization_service.py](file:///e:/BedaanWaves/backend/app/services/nlp/news_summarization_service.py)

### 11.1 GET /news — Global News Feed (Paginated)
Query: `?limit=50&offset=0&min_sentiment_score=0&sector=ALL`
Output: Same article card array as §3.6 with pagination envelope.

### 11.2 GET /news/{article_id} — Single Article + NLP Enrichments
Output 200:
```json
{
  "id": "news-uuid",
  "headline": "...",
  "body_text": "... (1000 chars, fair-use clip)",
  "summary_extractive_3_sentences": "...",
  "sentence_sentiment_sentence_scores": [ { "i": 0, "text": "...", "score": 0.42 } ],
  "sentiment_document": { "label": "POSITIVE", "score": 0.62, "confidence": 0.91 },
  "entities_extracted": [ { "type": "SYMBOL", "text": "AAPL", "confidence": 0.99 }, { "type": "PERSON", "text": "Tim Cook", "confidence": 0.95 } ],
  "topics_latent_dirichlet_allocation": [ { "topic_id": 3, "label": "Earnings", "weight": 0.71 } ]
}
```

### 11.3 GET /news/sentiment/aggregate/{symbol} — Rolling Sentiment Series
Query: `?window_days=30&bucket=1d`
Output: 30-day per-day sentiment mean + volume count.

### 11.4 GET /news/sources — Supported News Provider Inventory
Output: List of sources with coverage stats: Reuters, Bloomberg, CNBC, WSJ, PR Newswire, BusinessWire, SeekingAlpha, MotleyFool, Barrons, MarketWatch.

### 11.5 POST /news/search — Full-Text Query Over Last 90 Days
Input: `{ "query": "artificial intelligence datacenter capex", "sector": "Technology", "limit": 20 }`
Output: Paginated matching articles ranked by BM25 + recency decay.

---

## §12 COMPARISON ENGINE
**Source:** [compare.py](file:///e:/BedaanWaves/backend/app/api/routes/compare.py), [comparison_service.py](file:///e:/BedaanWaves/backend/app/services/specialized/comparison_service.py)

### 12.1 POST /compare/scores — Multi-Ticker Score Matrix (2-10 Symbols)
Input: `{ "symbols": ["AAPL","MSFT","GOOGL"], "effective_date": "2026-09-04" }`
Output 200:
```json
{
  "symbols_compared": 3,
  "effective_date": "2026-09-04",
  "winners_by_dimension": { "profitability": "AAPL", "valuation": "GOOGL", "momentum": "AAPL", "volatility": "MSFT", "quality": "AAPL", "growth": "GOOGL" },
  "overall_winner": { "symbol": "AAPL", "total_score": 87.3, "wins": 4, "losses": 2 },
  "matrix_rows": [
    { "symbol": "AAPL",  "total_score": 87.3, "profitability": 92, "valuation": 78, "momentum": 84, "volatility": 81, "quality": 90, "growth": 78 },
    { "symbol": "MSFT",  "total_score": 85.1, ... }
  ]
}
```

### 12.2 POST /compare/performance — Historical Relative Performance
Input: `{ "symbols": [...], "window_days": 180, "rebase_to_100": true }`
Output: Rebased (start = 100) price series for all symbols, suitable for overlay line chart.

### 12.3 POST /compare/correlation — Cross-Symbol Correlation Matrix
Input: `{ "symbols": ["AAPL","MSFT","GOOGL","AMZN","META"], "window_days": 180, "method": "pearson" }`
method ∈ `pearson`, `spearman`
Output: N×N symmetric correlation matrix + heatmap-friendly scale values.

---

## §13 USERS & PREFERENCES
**Source:** [users.py](file:///e:/BedaanWaves/backend/app/api/routes/users.py), [settings.py](file:///e:/BedaanWaves/backend/app/api/routes/settings.py)

### 13.1 GET /users/me — Same as §1.5 /auth/me
### 13.2 PATCH /users/me — Update Own Profile
Partial update: fields = `full_name`, `email` (email change triggers re-verification email)

### 13.3 POST /users/me/change-password
Input: `{ "current_password": "...", "new_password": "...", "confirm_password": "..." }`
Output: 204 No Content → all refresh tokens revoked (same as §2.3).

### 13.4 POST /users/me/enable-2fa-totp
Output 200: `{ "qr_code_data_uri": "otpauth://totp/BedaanWaves:jane?secret=BASE32...&issuer=BedaanWaves", "backup_codes_10": ["ABCD-1234", ..., "WXYZ-9876"] }`
User must confirm with one valid TOTP code within 60 seconds.

### 13.5 GET /users/me/preferences — Fetch User Preferences Dict
Output 200: Preferences shape as §1.5.

### 13.6 PUT /users/me/preferences — Overwrite Preferences
Input: Same shape as preferences output; full server-side validation.

### 13.7 GET /users/me/activity — Login + Action Audit Log (Last 30 Days)
Query: `?limit=50`
Output: `[{ "timestamp", "action": "LOGIN_SUCCESS / FORECAST_REQUEST / ALERT_FIRED", "ip_address": "203.0.113.42", "user_agent": "Chrome 128 / Win 11", "success": true }]`

### 13.8 GET /users/me/forecast-history — Past Forecast Request Log
Query: `?limit=20`
Output: Summary list of forecast calls (symbol, horizon, model_used, generated_at, request_id, directional_bias_outcome_vs_actual if resolved).

---

## §14 SYSTEM, HEALTH, & ADMIN
**Source:** [health.py](file:///e:/BedaanWaves/backend/app/api/routes/health.py), [system.py](file:///e:/BedaanWaves/backend/app/api/routes/system.py), [data_health.py](file:///e:/BedaanWaves/backend/app/api/routes/data_health.py)

### 14.1 GET /health — Public Liveness Probe (No Auth)
Output 200:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 83812,
  "timestamp": "2026-09-05T14:30:00Z",
  "components": {
    "postgresql": "healthy",
    "redis": "healthy",
    "market_data_upstream": "degraded",
    "ml_engine": "healthy",
    "smtp_email": "healthy"
  }
}
```
- If any component = unhealthy, HTTP status still = 200 (readiness uses separate endpoint §14.2).

### 14.2 GET /health/ready — Readiness Probe
Output: 200 if ALL healthy, else 503 with `Retry-After: 10` header.

### 14.3 GET /health/db — Deep Database Sanity Checks
Health of: connections, migrations, symbol count, score_history recency, index bloat.

### 14.4 GET /health/cache — Redis Cache Stats
Output: `hit_rate_pct: 87.3`, `keys_count: 12483`, `used_memory_rss_mb: 412`, `evictions_1h: 0`

### 14.5 GET /health/data-freshness — Last Successful Market Ingestion Timestamps
Output: `{ "prices_last_ingested_at": "...", "score_history_last_completed_at": "...", "gap_days_since_last_score": 0 }`

### 14.6 GET /system/metrics — Prometheus Scrape (No Auth, restricted to localhost by default)
Content-Type: `text/plain; version=0.0.4; charset=utf-8`
Exposed counters/gauges/histograms:
- `bw_api_requests_total{method,path,status}`
- `bw_api_request_duration_seconds_bucket{path}`
- `bw_db_query_duration_seconds_bucket{query_class}`
- `bw_forecast_requests_total{model,horizon}`
- `bw_alert_firings_total{alert_type,channel}`
- `bw_cache_ops_total{hit_miss}`
- `bw_sse_client_count`

### 14.7 POST /admin/ingestion/run — Force Full Market Re-Ingestion
**Auth Required:** ADMIN  
Input: `{ "start_date": "2026-08-01", "end_date": "2026-09-05", "symbols_scope": "NASDAQ_100" }`
Output 202 Accepted → job_id.

### 14.8 POST /admin/scoring/recompute — Force Score Recalculation
**Auth Required:** ADMIN  
Input: `{ "date": "2026-09-04", "dimension": "ALL" }`

### 14.9 GET /admin/users — User Directory (ADMIN Only)
Paginated: id, username, email, role, last_login_at, status (ACTIVE / LOCKED / PENDING_VERIFY)

### 14.10 POST /admin/users/{user_id}/role — Change Role (ADMIN)
Body: `{ "role": "ANALYST" }`  enum: USER / ANALYST / ADMIN

---

## INDEX

| Topic | Locate at |
|-------|-----------|
| Auth / register / login / refresh / logout / me | §1 |
| Password reset FSM (4 endpoints) | §2 |
| Dashboard (general/technical/fundamental/risk/board/news/trend/spider) | §3 |
| Ranking (NASDAG leaderboard/sector/export/movers) | §4 |
| Stocks overview / prices / scores / history / financials / news / search | §5 |
| Market hours, delayed quotes, SSE live feed, indices (NDX/IXIC/QQQ) | §6 |
| Forecast price/trend/batch/models/performance/backtest (ARIMA/LSTM/Ensemble) | §7 |
| Alerts CRUD, pause/resume, trigger history (8 types, 3 channels) | §8 |
| Watchlists CRUD + items | §9 |
| Portfolios CRUD + transactions + CSV import + performance series | §10 |
| News feed + NLP enrichments + sentiment aggregates + search | §11 |
| Comparison: score matrix / relative performance / correlation matrix | §12 |
| User self-service: profile, password, 2FA TOTP, preferences, audit | §13 |
| Health probes, Prometheus metrics, data freshness, ADMIN ops | §14 |
| Standard error envelope, status codes, pagination | Conventions section above |

---
*Document ID: BW-API-REF-v2.0.0 | Effective: v2.0.0, 2026-09-05 | Endpoints documented: 90 (all route modules)*
