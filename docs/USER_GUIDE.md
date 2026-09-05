# BedaanWaves End-User Guide

This guide walks through the features available to end users of the BedaanWaves
capital-market analysis platform — from account setup to portfolio management,
stock research, and real-time alerts.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Account & Authentication](#2-account--authentication)
3. [Dashboard Overview](#3-dashboard-overview)
4. [Stock Research](#4-stock-research)
5. [Market Data & Analysis](#5-market-data--analysis)
6. [Portfolios](#6-portfolios)
7. [Watchlists](#7-watchlists)
8. [Notifications](#8-notifications)
9. [Password Recovery](#9-password-recovery)
10. [Language Settings](#10-language-settings)

---

## 1. Quick Start

| Service | URL |
|---------|-----|
| Frontend | `http://localhost:3005` |
| API Docs (Swagger) | `http://localhost:3000/api/v1/docs` |
| API Docs (ReDoc) | `http://localhost:3000/api/v1/redoc` |

On first launch, the backend automatically creates a default admin account.
Check the backend logs for the generated admin password.

---

## 2. Account & Authentication

### Registering

1. Navigate to the registration page in the frontend.
2. Enter a **username** (3–100 characters), **email**, and **password**.
3. Click **Register**.
4. You are immediately logged in and receive an access token (valid 30 min)
   and a refresh token (valid 7 days).

### Logging In

1. Enter your username and password.
2. On success, the app stores both tokens in local storage.
3. The access token is sent as `Authorization: Bearer <token>` on every
   subsequent API request.

### Token Refresh

When the access token expires, the frontend automatically calls:

```
POST /api/v1/auth/refresh?token=<refresh_token>
```

If the refresh token is also expired, you are redirected to the login page.

### Logout

Click **Logout** in the user menu. This clears the stored tokens from the
browser.

---

## 3. Dashboard Overview

The dashboard (`http://localhost:3005/dashboard`) provides a unified view
of market health, AI signals, and portfolio performance.

| Panel | Description |
|-------|-------------|
| **General** | High-level summary: total symbols, recent signals, market status |
| **Technical** | Recently detected technical chart patterns |
| **Fundamental** | Top fundamentally-scored stocks |
| **News** | Latest market-moving news with sentiment |
| **Risk** | Portfolio-level risk metrics |
| **Board** | 6D scorecard view (Fundamental, Technical, Sentiment, Risk, Macro, AI) |
| **AI** | Machine-learning model predictions |
| **Score Trend** | Historical 6D score trends (last 30 days by default) |
| **Coefficient History** | ML model coefficient changes over time |

Each dashboard endpoint accepts a `limit` or `days` query parameter to control
the amount of data returned.

---

## 4. Stock Research

### Searching for Stocks

Use the stock search bar or call:

```
GET /api/v1/stocks/search?q=AAPL
```

Returns matching tickers with company name, exchange, and sector.

### Viewing Stock Details

Navigate to `/stocks/{ticker}` or call:

```
GET /api/v1/stocks/{ticker}
```

Displays:
- Real-time price and change
- Key ratios (P/E, P/B, market cap, dividend yield)
- Technical indicators (RSI, MACD, Bollinger Bands)
- Recent news sentiment
- ML prediction (bullish/bearish)

### Batch Stock Lookup

To fetch multiple stocks at once:

```
POST /api/v1/stocks/batch
Content-Type: application/json

["AAPL", "MSFT", "GOOGL"]
```

### Exporting Data

```
POST /api/v1/stocks/export?tickers=AAPL,MSFT
```

Returns CSV or JSON data for download.

### Importing Portfolio Data

Upload a CSV file:

```
POST /api/v1/stocks/import
Content-Type: multipart/form-data
file: <CSV file>
```

---

## 5. Market Data & Analysis

### Market Overview

```
GET /api/v1/market/market-overview?market=NASDAQ
```

Shows top gainers, losers, and most-active stocks.

### Real-Time Quotes

```
GET /api/v1/market-data/quote/{symbol}
```

### Historical Price History

```
GET /api/v1/market-data/history/{symbol}?period=1mo&interval=1d
```

The `interval` parameter supports `1m`, `5m`, `15m`, `1h`, `1d`, `1wk`, `1mo`.

### Technical Analysis

```
GET /api/v1/analysis/technical/{symbol}
```

Returns SMA, EMA, RSI, MACD, Bollinger Bands, and ATR values.

### Fundamental Analysis

```
GET /api/v1/analysis/fundamental/{symbol}
```

> Rate-limited to 10 requests/minute to protect the data provider.

### Risk Analysis

```
GET /api/v1/analysis/risk-analysis/{symbol}
```

Returns volatility metrics, Sharpe ratio, max drawdown, and Value-at-Risk.

### ML Prediction

```
GET /api/v1/ml/predict/{symbol}?horizon=5
```

Returns a bullish/bearish probability (0.0–1.0) for the next N days.

### Scoring & Ranking

```
GET /api/v1/analysis/scoring/{symbol}
```

Returns the 6D score breakdown:
- **Fundamental** (25% weight)
- **Technical** (20% weight)
- **Sentiment** (15% weight)
- **Risk** (20% weight)
- **Macro** (10% weight)
- **AI** (10% weight)

### Stock Screening

```
POST /api/v1/specialized/screen
Content-Type: application/json

{
  "min_market_cap": 1000000000,
  "min_price": 10,
  "sectors": ["Technology", "Healthcare"],
  "has_dividend": true
}
```

### Performance Rankings

```
GET /api/v1/ranking/nasdaq?limit=50
```

Ranks NASDAQ stocks by composite 6D score.

---

## 6. Portfolios

### Creating a Portfolio

```
POST /api/v1/portfolio
Content-Type: application/json

{
  "name": "Retirement 2030",
  "description": "Long-term growth portfolio"
}
```

### Listing Portfolios

```
GET /api/v1/portfolio
```

### Adding Holdings

```
POST /api/v1/portfolio/{portfolio_id}/holdings
Content-Type: application/json

{
  "symbol": "AAPL",
  "quantity": 10,
  "purchase_price": 175.50,
  "purchase_date": "2024-01-15"
}
```

### Viewing Holdings

```
GET /api/v1/portfolio/{portfolio_id}/holdings
```

### Deleting a Holding

```
DELETE /api/v1/portfolio/{portfolio_id}/holdings/{holding_id}
```

### Deleting a Portfolio

```
DELETE /api/v1/portfolio/{portfolio_id}
```

---

## 7. Watchlists

Watchlists are personalized lists of symbols you want to track.

### Creating a Watchlist

```
POST /api/v1/watchlists
Content-Type: application/json

{
  "name": "Tech Giants",
  "symbol": "AAPL"
}
```

### Listing Watchlists

```
GET /api/v1/watchlists
```

### Adding Symbols

```
POST /api/v1/watchlists/{watchlist_id}/items
Content-Type: application/json

{ "symbol": "MSFT" }
```

### Removing Symbols

```
DELETE /api/v1/watchlists/{watchlist_id}/items/{item_id}
```

### Deleting a Watchlist

```
DELETE /api/v1/watchlists/{watchlist_id}
```

---

## 8. Notifications

The platform sends in-app notifications for:
- Price threshold alerts
- Technical analysis signals (RSI oversold/overbought)
- Earnings announcements
- News sentiment shifts
- Portfolio rebalancing recommendations

### Listing Notifications

```
GET /api/v1/notifications?unread_only=true
```

### Marking as Read

```
POST /api/v1/notifications/{notification_id}/read
```

### Mark All as Read

```
POST /api/v1/notifications/read-all
```

### Deleting a Notification

```
DELETE /api/v1/notifications/{notification_id}
```

---

## 9. Password Recovery

### Step 1 — Request a Reset Link

```
POST /api/v1/auth/password-reset/request?lang=en
Content-Type: application/json

{ "email": "you@example.com" }
```

> The API always returns a success message — even if the email doesn't exist —
> to prevent account enumeration. Check your spam folder if you don't receive
> the email within a few minutes.

### Step 2 — Verify the Token

```
POST /api/v1/auth/password-reset/verify
Content-Type: application/json

{ "token": "<token-from-email>" }
```

### Step 3 — Set New Password

```
POST /api/v1/auth/password-reset/confirm?lang=en
Content-Type: application/json

{
  "token": "<token-from-email>",
  "new_password": "yourNewSecurePassword123"
}
```

Password must be at least **8 characters** long.

---

## 10. Language Settings

BedaanWaves supports English (`en`) and Persian (`fa`) for all authentication
and password-recovery messages.

- Pass `?lang=fa` to any auth or password-reset endpoint for Persian responses.
  Example: `POST /api/v1/auth/login?lang=fa`
- Pass `?lang=en` for English (default).
- Any other value returns a `422` validation error.

---

## Health & Monitoring

The platform exposes several health-check endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Basic liveness + readiness (root level) |
| `GET /api/v1/health/` | Detailed health (DB, cache, memory, disk) |
| `GET /api/v1/health/ready` | Readiness probe for load balancers |
| `GET /api/v1/health/live` | Liveness probe (always 200) |
| `GET /data-health` | Data provider connectivity status |
