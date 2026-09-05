# BedaanWaves API Reference

## Overview

BedaanWaves exposes a comprehensive RESTful API across **24 routers** (27 route
files exist; 3 — `alerts`, `compare`, `forecast` — are present in
`app/api/routes/` but **not imported in `__init__.py`** and are therefore
dead code not registered in `main.py`).

All endpoints are also available interactively via **Swagger UI** at
`http://localhost:3000/api/v1/docs` and **ReDoc** at
`http://localhost:3000/api/v1/redoc`.

## Base URL

| Environment | URL |
|-------------|-----|
| Development | `http://localhost:3000` |
| API prefix  | `/api/v1` (configurable via `API_V1_STR`) |

Full base URL for all endpoints below: `http://localhost:3000/api/v1`

## Authentication

Two auth mechanisms are supported:

### JWT Bearer Token (primary)

1. `POST /api/v1/auth/register` — create an account
2. `POST /api/v1/auth/login` — obtain access + refresh tokens
3. Include the access token in subsequent requests:
   `Authorization: Bearer <access_token>`
4. `POST /api/v1/auth/refresh?token=<refresh_token>` — mint a new access token

**Token lifetime:**
- Access token: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh token: 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)

### Cookie-based (optional)

A `refresh_token` cookie can also be used for session renewal.

### Public vs. Protected Routes

Routes under the following prefixes are **public** (no auth required):

- `/api/v1/auth` — authentication & password reset
- `/api/v1/market` — market data
- `/api/v1/analysis` — analysis & scoring
- `/api/v1/news` — news endpoints
- `/api/v1/docs`, `/api/v1/redoc`, `/api/v1/openapi.json` — API docs
- `/health` — root health check
- `/` — root welcome

All other routes require a valid Bearer token. Auth is controlled by the
`AuthGuardMiddleware` (enabled when `REQUIRE_AUTH=True`, which is the default).

### Language Parameter (`lang`)

Endpoints in the **auth** and **password-reset** routers accept an optional
`lang` query parameter:

| Value | Language | Description |
|-------|----------|-------------|
| `en` | English (default) | Standard English error/success messages |
| `fa` | Persian (Farsi) | Persian-language messages (WCAG 2.1 AA plain language) |

Any value not matching `^en|fa$` returns **422**.

## Response Format

### Success

```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2026-09-05T10:30:00Z"
}
```

### Error

```json
{
  "status": "error",
  "error_code": "NOT_FOUND",
  "message": "Human-readable description"
}
```

| HTTP Status | Meaning |
|-------------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request / validation failure |
| 401 | Authentication required |
| 403 | Access denied (insufficient permissions) |
| 404 | Resource not found |
| 422 | Request validation error (Pydantic) |
| 429 | Rate limit exceeded |
| 503 | Service unavailable (e.g. database down) |

---

## Router Index

| # | Router | Prefix | Tag | Auth | Endpoints |
|---|--------|--------|-----|------|-----------|
| 1 | auth | `/api/v1/auth` | `auth` | Public | 3 |
| 2 | password-reset | `/api/v1/auth` | `password-reset` | Public | 3 |
| 3 | stocks | `/api/v1/stocks` | `stocks` | Required | 6 |
| 4 | market | `/api/v1/market` | `market` | Public | 6 |
| 5 | analysis | `/api/v1/analysis` | `analysis` | Public | 20 |
| 6 | dashboard | `/api/v1/analysis` | `dashboard` | Public | 13 |
| 7 | portfolio | `/api/v1/portfolio` | `portfolio` | Required | 7 |
| 8 | history | `/api/v1/history` | `history` | Required | 2 |
| 9 | news | `/api/v1/news` | `news` | Public | 3 |
| 10 | ml | `/api/v1/ml` | `ml` | Required | 5 |
| 11 | users | `/api/v1/users` | `users` | Required | 6 |
| 12 | watchlists | `/api/v1/watchlists` | `watchlists` | Required | 5 |
| 13 | notifications | `/api/v1/notifications` | `notifications` | Required | 4 |
| 14 | specialized | `/api/v1/specialized` | `specialized` | Mixed | 7 |
| 15 | system | `/api/v1/system` | `system` | Required | 11 |
| 16 | intl | `/api/v1/intl` | `intl` | Public | 3 |
| 17 | live | `/api/v1/live` | `live` | Public (stub) | 6 |
| 18 | live-sse | `/api/v1/live` | `live-sse` | Public (stub) | 4 |
| 19 | health | `/api/v1/health` | `health` | Public | 5 |
| 20 | market-data | `/api/v1/market-data` | `market-data` | Public | 4 |
| 21 | data-health | `/` (root) | `data-health` | Public | 1 |
| 22 | symbols | `/api/v1/symbols` | `symbols` | Public | 8 |
| 23 | settings | `/api/v1/settings` | `settings` | Mixed | 3 |
| 24 | ranking | `/api/v1/ranking` | `ranking` | Public | 1 |

**Dead code (not registered):**
| File | Intended Route | Status |
|------|---------------|--------|
| `alerts.py` | `/api/v1/alerts` | Not imported, 8 endpoints unreachable |
| `compare.py` | `/api/v1/compare` | Not imported, 4 endpoints unreachable |
| `forecast.py` | `/api/v1/forecast` | Not imported, 6 endpoints unreachable |

---

## 1. Auth Router — `/api/v1/auth`

Authentication and authorization management.

### `POST /register`

Register a new user account.

**Query parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `lang` | string (`^(en\|fa)$`) | `en` | Response language |

**Request body:**
```json
{
  "username": "trader_pro",
  "email": "trader@example.com",
  "password": "securePass123",
  "full_name": "Pro Trader"
}
```

**Response 200:**
```json
{
  "access_token": "<jwt-access-token>",
  "refresh_token": "<jwt-refresh-token>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `400` — Username already registered
- `400` — Email already registered
- `422` — Validation error (username < 3 chars, invalid email, password < 3 chars)

### `POST /login`

Authenticate and receive JWT tokens.

**Query parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `lang` | string | `en` | Response language |

**Request body:**
```json
{
  "username": "trader_pro",
  "password": "securePass123"
}
```

**Response 200:** Same as `POST /register`.

**Errors:**
- `401` — Incorrect username or password
- `422` — Missing required fields

### `POST /refresh`

Exchange a refresh token for new access + refresh tokens.

> **Note:** `token` is passed as a **query parameter**, not a JSON body.

**Query parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `token` | string | Yes | — | The refresh token JWT |
| `lang` | string | No | `en` | Response language |

**Response 200:** Same token format as `POST /register`.

**Errors:**
- `401` — Invalid or expired refresh token (details in `detail`)
- `401` — Token is an access token, not a refresh token
- `401` — User not found

---

## 2. Password-Reset Endpoints — `POST /api/v1/auth/password-reset/*`

Password recovery flow. Mounted at `/api/v1/auth` via `password_reset_router`.

All endpoints return generic success messages regardless of whether the email
exists, to prevent account enumeration.

### `POST /password-reset/request`

Request a password recovery link.

**Query parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `lang` | string (`^(en\|fa)$`) | `en` | Response language |

**Request body:**
```json
{ "email": "user@example.com" }
```

**Response 200:**
```json
{
  "status": "success",
  "message": "If an account exists for that email, a recovery link has been sent."
}
```

### `POST /password-reset/verify`

Check whether a recovery token is still valid.

**Query parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `lang` | string | `en` | Response language |

**Request body:**
```json
{ "token": "<recovery-token-from-email>" }
```

**Response 200:**
```json
{
  "valid": true,
  "email_hint": null
}
```

### `POST /password-reset/confirm`

Consume a reset token and set a new password.

**Query parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `lang` | string | `en` | Response language |

**Request body:**
```json
{
  "token": "<recovery-token-from-email>",
  "new_password": "newSecurePass456"
}
```

**Response 200:**
```json
{
  "status": "success",
  "message": "Your password has been updated. You can now sign in."
}
```

**Errors:**
- `400` — Token missing, expired, or invalid
- `422` — `new_password` shorter than 8 characters (schema-level validation)

---

## 3. Stocks Router — `/api/v1/stocks`

### `GET /search`

Search stock tickers by company name or symbol.

**Query parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `q` | string | `""` | Search query |

**Auth:** Public

### `GET /{ticker}`

Get detailed information for a single stock.

**Path parameters:**
| Name | Type | Description |
|------|------|-------------|
| `ticker` | string | Stock ticker symbol (e.g. `AAPL`) |

**Auth:** Required

### `POST /batch`

Fetch details for multiple stocks.

**Request body:**
```json
["AAPL", "GOOGL", "MSFT"]
```

**Auth:** Required

### `POST /v2/batch`

Fetch multiple stocks (v2 with richer response).

**Request body:** Same as `POST /batch`.

**Auth:** Required

### `POST /export`

Export stock/portfolio data (CSV or JSON).

**Query parameters:**
| Name | Type | Description |
|------|------|-------------|
| `tickers` | List[string] | Optional list of tickers to export |

**Auth:** Required

### `POST /import`

Import stock/portfolio data via file upload.

**Request:** `multipart/form-data` with a `file` field (CSV).

**Auth:** Required

---

## 4. Market Router — `/api/v1/market`

Market-wide data, indices, and sector performance.

**Auth:** Public (all endpoints)

| Method | Path | Description | Key Parameters |
|--------|------|-------------|----------------|
| GET | `/symbols` | List all traded symbols | `asset_class` (enum, optional) |
| GET | `/price-history` | Historical OHLCV candles | `symbol`, `period`, `interval` |
| GET | `/latest-prices` | Batch latest prices | `symbols` (list) |
| GET | `/market-overview` | Overview by market | `market` (default: NASDAQ) |
| GET | `/nasdaq-dashboard` | NASDAQ dashboard | (DB query) |
| GET | `/indices` | Market indices summary | — |
| GET | `/industry-ranking` | Industry ranking | — |

---

## 5. Analysis Router — `/api/v1/analysis`

Technical, fundamental, sentiment, and scoring analysis.

**Auth:** Public (all endpoints)

| Method | Path | Description | Key Parameters |
|--------|------|-------------|----------------|
| GET | `/signals/{symbol}` | ML buy/sell signal for a symbol | `symbol` |
| GET | `/signals-summary` | Aggregated signal summary | `market` (optional) |
| GET | `/signals` | Paginated list of all signals | `market`, `limit`, `page` |
| GET | `/top-performers` | Top-performing stocks | `limit` (default 10) |
| GET | `/risk-analysis/{symbol}` | Full risk analysis | `symbol` |
| GET | `/technical/{symbol}` | Technical indicators | `symbol` |
| GET | `/risk/{symbol}` | Risk metrics | `symbol` |
| GET | `/fundamental/{symbol}` | Fundamental ratios | `symbol` — *rate-limited: 10/min* |
| GET | `/momentum/{symbol}` | Momentum analysis | `symbol` |
| GET | `/volatility/{symbol}` | Volatility profile | `symbol` |
| POST | `/scoring` | Run scoring on input data | `data` (body) |
| GET | `/scoring/{symbol}` | 6D scoring for a symbol | `symbol` |
| GET | `/sentiment/{symbol}` | News sentiment analysis | `symbol` |
| POST | `/scoring/rank` | Score & rank multiple stocks | `data` (body) |
| GET | `/fundamental/batch` | Batch fundamental analysis | — *rate-limited: 5/min* |
| GET | `/fundamentals/health` | Fundamental service health | — |
| GET | `/scoring/history/{symbol}` | Historical scores | `symbol` |
| GET | `/scoring/hierarchy/{symbol}` | 6D hierarchy breakdown | `symbol` |
| GET | `/scoring/coefficients/{symbol}` | Model coefficients | `symbol` |

---

## 6. Dashboard Router — `/api/v1/analysis/dashboard/*`

Dashboard data endpoints (registered with prefix `/api/v1/analysis`).

**Auth:** Public (all endpoints)

| Method | Path | Description | Key Parameters |
|--------|------|-------------|----------------|
| GET | `/dashboard/general` | General dashboard overview | — |
| GET | `/dashboard/technical` | Technical dashboard | `limit` (default 50) |
| GET | `/dashboard/fundamental` | Fundamental dashboard | `limit` |
| GET | `/dashboard/news` | News dashboard | `limit` |
| GET | `/dashboard/risk` | Risk dashboard | `limit` |
| GET | `/dashboard/board` | Board/scorecard view | `limit` |
| GET | `/dashboard/ai` | AI/ML dashboard | `limit` |
| GET | `/dashboard/score-trend` | Score trend over N days | `days` (1–365) |
| GET | `/dashboard/coefficient-history` | Coefficient history | `days` |
| GET | `/dashboard/hierarchical-trend` | 6D hierarchy trends | `level` |
| GET | `/dashboard/sub-dimension-trend` | Sub-dimension trends | `days` |
| GET | `/dashboard/aspect-trend` | Aspect-level trends | `days` |
| GET | `/dashboard/sub-aspect-trend` | Sub-aspect trends | `days` |
| GET | `/dashboard/coefficient-history-by-level` | Coeffs by hierarchy level | `level` |

---

## 7. Portfolio Router — `/api/v1/portfolio`

CRUD portfolio and position management.

**Auth:** Required (all endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create a new portfolio |
| GET | `/` | List all user portfolios |
| GET | `/{portfolio_id}` | Get a single portfolio |
| PUT | `/{portfolio_id}` | Update portfolio metadata |
| DELETE | `/{portfolio_id}` | Delete a portfolio |
| POST | `/{portfolio_id}/holdings` | Add a holding/position |
| GET | `/{portfolio_id}/holdings` | List all holdings |
| DELETE | `/{portfolio_id}/holdings/{holding_id}` | Remove a holding |

---

## 8. History Router — `/api/v1/history`

Historical price and volume data.

**Auth:** Required (all endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{ticker}` | Price history for a ticker |
| GET | `/volume/{ticker}` | Volume history for a ticker |

---

## 9. News Router — `/api/v1/news`

Market and stock-specific news with sentiment analysis.

**Auth:** Public (all endpoints)

| Method | Path | Description | Key Parameters |
|--------|------|-------------|----------------|
| GET | `/market` | Latest market news | `limit` (default 20) |
| GET | `/{ticker}` | News for a specific stock | `ticker` |
| GET | `/search` | Search news articles | `q` (required) |

---

## 10. ML Router — `/api/v1/ml`

Machine learning predictions and pattern detection.

**Auth:** Required (all endpoints)

| Method | Path | Description | Key Parameters |
|--------|------|-------------|----------------|
| GET | `/predict/{symbol}` | Price direction prediction | `symbol`, `horizon` (1–30 days) |
| GET | `/patterns/{symbol}` | Technical chart patterns | `symbol` |
| GET | `/anomaly/{symbol}` | Anomaly detection | `symbol` |
| POST | `/optimize` | Portfolio optimization | `data` (body: weights, constraints) |
| POST | `/forecast` | Price forecast | `data` (body: ticker, horizon) |

---

## 11. Users Router — `/api/v1/users`

User profile and preferences management.

**Auth:** Required (all endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/me` | Get current user profile |
| PATCH | `/me` | Update profile (email, name, theme, etc.) |
| GET | `/me/preferences` | List all user preferences |
| GET | `/me/preferences/{key}` | Get a single preference |
| PUT | `/me/preferences/{key}` | Set a single preference |
| DELETE | `/me/preferences/{key}` | Delete a preference |

---

## 12. Watchlists Router — `/api/v1/watchlists`

User watchlist management (create, list, add/remove symbols).

**Auth:** Required (all endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create a new watchlist |
| GET | `/` | List all user watchlists |
| GET | `/{watchlist_id}` | Get a watchlist |
| DELETE | `/{watchlist_id}` | Delete a watchlist |
| POST | `/{watchlist_id}/items` | Add an item to a watchlist |
| DELETE | `/{watchlist_id}/items/{item_id}` | Remove an item |

---

## 13. Notifications Router — `/api/v1/notifications`

In-app notification management.

**Auth:** Required (all endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List notifications (`unread_only` query param) |
| POST | `/{notification_id}/read` | Mark a notification as read |
| POST | `/read-all` | Mark all notifications as read |
| DELETE | `/{notification_id}` | Delete a notification |

---

## 14. Specialized Router — `/api/v1/specialized`

Specialized financial endpoints: stock screening, comparison, correlation,
and corporate calendar.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/sectors/summary` | Public | Sector performance summary |
| POST | `/screen` | Required | Stock screener (query by criteria) |
| POST | `/compare` | Required | Compare stocks/assets |
| POST | `/correlation` | Required | Correlation matrix between symbols |
| GET | `/calendar/month` | Public | Calendar data for a month (`year`) |
| GET | `/calendar/events` | Public | Corporate events on a date (`day`) |
| POST | `/calendar/events` | Required | Add a calendar event |

---

## 15. System Router — `/api/v1/system`

System administration, monitoring, and operational tooling.

**Auth:** Required (all endpoints)

### Scheduler jobs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/scheduler/jobs` | List all registered scheduler jobs |
| POST | `/scheduler/jobs` | Register a new scheduler job |
| DELETE | `/scheduler/jobs/{name}` | Unregister a job |
| POST | `/scheduler/jobs/{name}/run` | Trigger a job immediately |

### Metrics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | Platform-wide metrics summary |
| GET | `/metrics/health` | Overall health summary for all services |

### Queue operations

| Method | Path | Description |
|--------|------|-------------|
| POST | `/queue/jobs` | Enqueue a background job |
| GET | `/queue/jobs/{job_id}` | Get job details by ID |
| GET | `/queue/stats` | Queue statistics |
| GET | `/queue/dead-letter` | Dead-letter (failed) jobs |

---

## 16. International Stocks Router — `/api/v1/intl`

Real-time and historical data for non-NASDAQ international stocks.

**Auth:** Public (all endpoints)

| Method | Path | Description | Key Parameters |
|--------|------|-------------|----------------|
| GET | `/quote/{symbol}` | Real-time quote | `symbol` |
| GET | `/history/{symbol}` | Historical prices | `interval` (default `1d`), `days` (1–3650) |
| GET | `/search` | Search international symbols | `query` (required) |

---

## 17. Live Data Router — `/api/v1/live`

**Auth:** Public (all endpoints are stubs — return 501 Not Implemented)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/symbols` | All real-time symbols |
| GET | `/symbol/{l18}` | Comprehensive real-time data for one symbol |
| GET | `/candlestick/{l18}` | Candlestick data |
| GET | `/history/{l18}` | Daily price & trade history |
| GET | `/option/{l18}` | Option data |
| GET | `/realtime/{l18}` | Real-time price |

---

## 18. Live SSE Router — `/api/v1/live` (same prefix)

Server-Sent Events streaming endpoints. All are stubs.

**Auth:** Public

| Method | Path | Description |
|--------|------|-------------|
| GET | `/symbols/stream` | SSE stream of all real-time symbols |
| GET | `/symbol/{l18}/stream` | SSE stream for one symbol |
| GET | `/candlestick/{l18}/stream` | SSE candlestick stream |
| GET | `/history/{l18}/stream` | SSE daily history stream |

---

## 19. Health Router — `/api/v1/health`

Health checks and readiness/liveness probes for load balancers.

**Auth:** Public (all endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root health check (DB, cache, memory, disk) |
| GET | `/services` | Health status for all services |
| GET | `/services/{service}` | Health for a specific service |
| GET | `/ready` | Readiness probe (requires DB + cache healthy) |
| GET | `/live` | Liveness probe (always returns 200) |

---

## 20. Market Data Router — `/api/v1/market-data`

Real-time and historical market data via Yahoo Finance.

**Auth:** Public (all endpoints)

| Method | Path | Description | Key Parameters |
|--------|------|-------------|----------------|
| GET | `/quote/{symbol}` | Real-time quote | `symbol` |
| GET | `/history/{symbol}` | Adjusted historical data | `symbol`, `period`, `interval` |
| GET | `/intraday/{symbol}` | Intraday price data | `symbol`, `interval`, `range` |
| GET | `/market-status` | Current market open/closed status | — |

---

## 21. Data Health Router — `/` (root-level, no prefix)

**Auth:** Public

| Method | Path | Description |
|--------|------|-------------|
| GET | `/data-health` | Verify data provider connectivity & last fetch status |

---

## 22. Symbols Router — `/api/v1/symbols`

Symbol lookup and metadata.

**Auth:** Public (all endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/search` | Search symbols by name or ticker | `q` (required) |
| GET | `/exchanges` | List all exchanges |
| GET | `/market-types` | List all market types |
| GET | `/countries` | List all countries |
| GET | `/stats` | Symbol statistics summary |
| GET | `/exchanges/{exchange}/count` | Symbol count by exchange |
| GET | `/market-types/{market_type}/count` | Symbol count by market type |
| GET | `/{symbol}` | Full symbol details |

---

## 23. Settings Router — `/api/v1/settings`

User market preferences and supported countries.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/market-preferences` | Required | Get user's saved market preferences |
| POST | `/market-preferences` | Required | Save market preferences |
| GET | `/countries` | Public | List supported countries/regions |

---

## 24. Ranking Router — `/api/v1/ranking`

**Auth:** Public

| Method | Path | Description | Key Parameters |
|--------|------|-------------|----------------|
| GET | `/nasdaq` | NASDAQ stock rankings | `limit` (1–200, default 50) |

---

## Request & Response Models (Key Schemas)

### `Token`
```typescript
interface Token {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;   // seconds until access token expires
}
```

### `RegisterRequest`
```typescript
interface RegisterRequest {
  username: string;     // 3–100 chars
  email: string;        // valid email
  password: string;     // ≥ 3 chars
  full_name?: string;   // optional
}
```

### `LoginRequest`
```typescript
interface LoginRequest {
  username: string;
  password: string;
}
```

### `PasswordResetRequest`
```typescript
interface PasswordResetRequest {
  email: string;
}
```

### `PasswordResetConfirm`
```typescript
interface PasswordResetConfirm {
  token: string;
  new_password: string;  // ≥ 8 chars (enforced by schema)
}
```

### `PortfolioCreate`
```typescript
interface PortfolioCreate {
  name: string;
  description?: string;
}
```

### `WatchlistCreate`
```typescript
interface WatchlistCreate {
  name: string;
  symbol: string;  // initial symbol to add
}
```

---

## Rate Limiting

Default rate limits are applied per-client IP:

| Tier | Limit |
|------|-------|
| Default | 100 requests/minute, 5000/hour |
| Fundamental analysis (batched) | 5 requests/minute |
| Fundamental analysis (single) | 10 requests/minute |

When exceeded, the API returns `429 Too Many Requests`.

---

## Error Codes Reference

| Code | HTTP | Description |
|------|------|-------------|
| `VALIDATION_ERROR` | 422 | Pydantic request validation failed |
| `INVALID_CREDENTIALS` | 401 | Wrong username or password |
| `INVALID_TOKEN` | 401 | Malformed or expired JWT |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required permission |
| `NOT_FOUND` | 404 | Resource not found |
| `SERVICE_UNAVAILABLE` | 503 | Backend service (DB, cache) unavailable |
| `INTERNAL_ERROR` | 500 | Unhandled server error |
