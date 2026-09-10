# BEDAANWAVES v2.0.0 — USER MANUAL
## End-User Operational Guide for the Nasdaq Financial Intelligence Platform

**Document ID:** BW-USERMAN-v2.0.0  
**Intended Audience:** End Users, Traders, Portfolio Managers, Equity Analysts  
**Access Level:** All authenticated users (Role: USER / ANALYST / ADMIN)  
**Classification:** USER-FACING DOCUMENTATION

---

## TABLE OF CONTENTS

1. [Getting Started](#1-getting-started)
2. [User Roles & Permissions Matrix](#2-user-roles--permissions-matrix)
3. [Core Navigation Screens](#3-core-navigation-screens)
4. [Dashboard — Spider Chart & Trend Analytics](#4-dashboard--spider-chart--trend-analytics)
5. [Ranking — NASDAQ-100 Multi-Factor Leaderboard](#5-ranking--nasdaq-100-multi-factor-leaderboard)
6. [Stock Detail Page — Deep-Dive Analysis](#6-stock-detail-page--deep-dive-analysis)
7. [Forecast — AI Price Prediction Engine](#7-forecast--ai-price-prediction-engine)
8. [Watchlists & Portfolios](#8-watchlists--portfolios)
9. [Alerts Engine — Real-Time Price Notifications](#9-alerts-engine--real-time-price-notifications)
10. [News & Sentiment Analysis](#10-news--sentiment-analysis)
11. [Search — Symbol Disambiguation (NDX vs IXIC)](#11-search--symbol-disambiguation-ndx-vs-ixic)
12. [Settings & User Profile](#12-settings--user-profile)
13. [Keyboard Shortcuts](#13-keyboard-shortcuts)
14. [FAQ — Frequently Asked Questions](#14-faq--frequently-asked-questions)
15. [Error Reference Guide](#15-error-reference-guide)

---

## 1. GETTING STARTED

### 1.1 First Login

1. Open any modern browser (Chrome 120+, Firefox 121+, Safari 17.2+, Edge 120+)
2. Navigate to: `http://<your-server>:3005` (local dev: `http://localhost:3005`)
3. Click **Create Account** (or use credentials provided by your administrator)
4. Complete the onboarding wizard (3 steps: Risk Tolerance → Watchlist Seed → UI Preferences)
5. You land on the Dashboard page. Bookmark this URL.

### 1.2 Minimum Viable First Session (5-Minute Walkthrough)

```
MINUTES 0-1:   [DASHBOARD] Read the 6-dimension Spider Chart. Notice which dimensions are
                strong (outer polygon vertices) vs weak (inner vertices). Click a vertex to
                drill into the sub-aspect table.

MINUTE  2:     Change the Date Selector (top-right). Watch SpiderChart + ScoreTrendChart
                re-sync AUTOMATICALLY. This is the global DateStore at work.

MINUTES 2-3:   [RANKING] Navigate to /ranking. Click column "Total Score" header to sort.
                Filter sector dropdown to "Technology". Export top-20 as CSV via the
                "Export" button.

MINUTES 3-4:   [STOCK DETAIL] Click any stock symbol (e.g., AAPL). Land on /stocks/AAPL.
                Review the Candlestick chart. Click the "Scoring" tab to see dimensional
                score breakdown with methodology references.

MINUTES 4-5:   [FORECAST] Click "Forecast" tab. Request a 30-day prediction. Read the
                confidence interval band (yellow shaded area). Note the directional bias
                indicator (BULLISH / BEARISH / NEUTRAL).
```

---

## 2. USER ROLES & PERMISSIONS MATRIX

| Capability | GUEST (unauth) | USER | ANALYST | ADMIN |
|------------|---------------|------|---------|-------|
| View public landing page | ✅ | ✅ | ✅ | ✅ |
| Login with JWT credentials | ❌ | ✅ | ✅ | ✅ |
| View Dashboard (global market) | ❌ | ✅ | ✅ | ✅ |
| View Ranking (Nasdaq-100) | ❌ | ✅ | ✅ | ✅ |
| View Stock Detail pages | ❌ | ✅ | ✅ | ✅ |
| Use Forecast engine | ❌ | ✅ (limit 50/day) | ✅ (limit 500/day) | ✅ (unlimited) |
| Create personal Watchlists | ❌ | ✅ (5 lists, 100 items each) | ✅ (50 lists) | ✅ (unlimited) |
| Create Portfolios + import transactions | ❌ | ✅ (3 portfolios) | ✅ (20 portfolios) | ✅ (unlimited) |
| Create price Alerts | ❌ | ✅ (20 alerts) | ✅ (200 alerts) | ✅ (unlimited) |
| Receive Alert notifications (in-app + email) | ❌ | ✅ | ✅ | ✅ |
| View News + Sentiment | ❌ | ✅ | ✅ | ✅ |
| Customize scoring coefficients | ❌ | ❌ | ✅ (private view) | ✅ (global default) |
| Bulk CSV import symbols | ❌ | ❌ | ✅ | ✅ |
| User management (CRUD) | ❌ | ❌ | ❌ | ✅ |
| System settings (thresholds, TTL, rate limits) | ❌ | ❌ | ❌ | ✅ |
| Force-run data ingestion / market re-score | ❌ | ❌ | ❌ | ✅ |
| View Audit logs, Metrics dashboards | ❌ | ❌ | ❌ | ✅ |

---

## 3. CORE NAVIGATION SCREENS

Every authenticated page has a consistent 3-zone layout:

```
┌────────────────────────────────────────────────────────────────────┐
│  TOP BAR (NewTopbar)                                                │
│  [Logo]  Global Search Bar  DateSelector   [Notifications] [Me]    │
├────────────┬───────────────────────────────────────────────────────┤
│            │                                                       │
│  SIDEBAR   │           PAGE CONTENT AREA                           │
│ (NewSideba │                                                       │
│  r)        │   Dashboard  ────  Score Trend, Spider, News, Stats   │
│            │   Ranking    ────  Sortable table, sector filters     │
│            │   Stocks     ────  (dynamic routing: /stocks/[symbol])│
│            │   Analysis   ────  Sector heatmap, Correlation        │
│            │   Forecast   ────  Prediction engine, Confidence      │
│            │   Alerts     ────  Alert management dashboard         │
│            │   News       ────  Curated feed + Sentiment scores    │
│            │   Portfolio  ────  Holdings, P/L, Risk metrics        │
│            │   Watchlists ────  (nested under Portfolio menu)      │
│            │   Settings   ────  Profile, Password, Preferences    │
│            │   Help       ────  (in-app help center)               │
│            │   Methodology────  Scoring docs, 6-dimension explainer│
└────────────┴───────────────────────────────────────────────────────┘
```

---

## 4. DASHBOARD — SPIDER CHART & TREND ANALYTICS

### 4.1 Spider Chart (Radar) — 6 Dimensions

**Axes Legend:**
| Axis | Dimension Name | What It Measures | Score Range |
|------|---------------|------------------|-------------|
| 1 | PROFITABILITY | Gross margin, operating margin, net margin, ROE, ROA, ROIC | 0-100 |
| 2 | VALUATION | P/E, P/B, P/S, EV/EBITDA, PEG, FCF Yield (inverted — cheaper = higher) | 0-100 |
| 3 | MOMENTUM | RSI(14), MACD Histogram, 50/200 SMA crossover, 1M/3M/6M return | 0-100 |
| 4 | VOLATILITY | 30D/90D historical vol, Beta, VaR(95), max drawdown (inverted — less vol = higher) | 0-100 |
| 5 | QUALITY | Piotroski F-Score, Altman Z-Score, Beneish M-Score, debt-to-EBITDA | 0-100 |
| 6 | GROWTH | Revenue YoY, EPS YoY, EBITDA CAGR 3Y, forward estimate revisions | 0-100 |

**Interaction Pattern:**
- **Hover** an axis vertex → tooltip shows exact score + top 3 sub-aspects
- **Click** an axis vertex → right-side panel drills into that dimension's sub-aspects
- **Legend toggle** → click a stock in the legend to show/hide its polygon (overlay comparison)
- **Share** → share icon (text-link only, per no-icon constraint) generates a date-synced permalink

### 4.2 Score Trend Chart (Time Series)

- X axis = last 90 calendar days (weekends show flat; see EC-001)
- Y axis = composite Total Score (0-100)
- Toggle individual stocks with legend
- **DateStore Sync Guarantee:** When you change the date anywhere on the platform, this chart re-anchors its rightmost visible bar to that exact (effective) date.

### 4.3 News Dashboard Section
- Curated news feed for top-10 holdings in the Nasdaq-100
- Each article card shows: Publication time, Source, Sentiment Badge (POSITIVE / NEUTRAL / NEGATIVE), Headline
- Click headline → opens source URL in a new tab

---

## 5. RANKING — NASDAQ-100 MULTI-FACTOR LEADERBOARD

### 5.1 Table Functionality

| Control | Behavior |
|---------|----------|
| Column header click | Sort ascending / descending (toggles) |
| Sector dropdown | Filter by GICS Sector (Technology, Healthcare, Consumer Discretionary, etc.) |
| Search box (above table, right) | Filter rows by symbol OR company name (contains match) |
| Min score sliders (6 dimensions) | Exclude stocks below user-set threshold per axis |
| "Reset Filters" button | Clears all filter/sort state |
| "Export CSV" button | Downloads currently-visible rows with all 6 dimension scores + total |
| Row click → Symbol | Navigates to `/stocks/<symbol>` |
| Row click → "+ Watchlist" icon (text "+WL") | Adds stock to first watchlist |

### 5.2 Ranking Methodology (Abbreviated)

```
TOTAL_SCORE(symbol, date) =
    0.22 × Profitability +
    0.20 × Valuation     +
    0.18 × Momentum      +
    0.12 × Volatility    +
    0.16 × Quality       +
    0.12 × Growth
```

*Note: Weights are configurable by the ADMIN role via Settings → Scoring Coefficients. Full methodology at `/methodology`.*

### 5.3 Sector Tabs
Quick-filter preset tabs: ALL · TECHNOLOGY · HEALTHCARE · CONSUMER · COMMUNICATIONS · INDUSTRIALS · OTHER

---

## 6. STOCK DETAIL PAGE — DEEP-DIVE ANALYSIS

Default path: `/stocks/AAPL` (replace AAPL with any NASDAQ-listed symbol)

### 6.1 Stock Detail Tabs

| Tab | Content |
|-----|---------|
| **Overview** (default) | Company name, sector, industry, market cap, P/E, 52W high/low, dividend yield, key stats grid. Candlestick chart (1D timeframe by default) with timeframe selector: 1D / 1W / 1M / 3M / 6M / 1Y / 5Y / MAX. |
| **Charts** | Dedicated full-width candlestick with volume pane. Overlay selector: SMA 20, 50, 200; Bollinger Bands (20,2); MACD; RSI. Up to 4 simultaneous overlays. |
| **Scoring** | Full Spider Chart for this single stock + 6-dimension score bars + 42 sub-aspect breakdown with raw metric values. Click any sub-aspect → tooltip shows exact formula reference. |
| **Forecast** | AI prediction module (see §7). Accessible only if FEATURE_FORECASTING=true and user quota available. |
| **Financials** | Quarterly income statement, balance sheet, cash flow statement (last 8 quarters). Expandable rows. |
| **News** | Ticker-specific news feed with sentiment aggregation (last 30 days). |

### 6.2 Candlestick Chart Interactions
- **Scroll wheel** over chart → time-axis zoom in/out
- **Drag horizontally** → pan time range
- **Crosshair** → tooltip on candle with OHLCV exact values
- **Timeframe selector** → re-aggregates candles instantly via backend aggregation endpoint

---

## 7. FORECAST — AI PRICE PREDICTION ENGINE

**Important Disclaimer (visible at top of tab):**
> ⚠️ Forecast output is for RESEARCH PURPOSES ONLY. It is NOT financial advice, a recommendation, or a solicitation. Past performance does not guarantee future results. All investments carry risk, including loss of principal. Validate predictions against independent research. Model accuracy: historical backtest MAPE = 4.2% (1D horizon), 8.7% (14D), 13.4% (30D).

### 7.1 Forecast Parameters

| Input Field | Range / Options | Default | Description |
|-------------|-----------------|---------|-------------|
| Horizon (days) | 1, 3, 7, 14, 30 | 14 | Number of trading days to predict forward |
| Model Ensemble | AUTO / ARIMA / LSTM / ENSEMBLE | ENSEMBLE | AUTO picks best model per AIC; ENSEMBLE = weighted average (0.4 × ARIMA + 0.6 × LSTM) |
| Confidence Level | 80% / 90% / 95% | 90% | Width of prediction interval band on chart |
| Include Regime Filter | On / Off | On | When On, adjusts forecast based on detected volatility regime (low/med/high) |

### 7.2 Output Structure

After clicking **Generate Forecast**, you see:
1. **Forecast Chart** — Historical close (thin black line) + predicted close (thick blue line) + upper/lower confidence band (yellow shaded)
2. **Forecast Card** — Explicit values:
   - Current Price (as of last close): $XXX.XX
   - Forecast Price (horizon day N): $YYY.YY
   - Implied % Change: ±Z.ZZ%
   - Directional Bias: **BULLISH** / **BEARISH** / **NEUTRAL**
   - Ensemble Model Confidence: AA / A / B / C (grade)
3. **Usage Meter** — "XX / 50 forecasts used today"
4. **Download** — Export forecast series as CSV (date, forecast, lower_ci, upper_ci)

### 7.3 Failure Modes
| Scenario | What User Sees | Corrective Action |
|----------|----------------|-------------------|
| Less than 30 days of history | Red warning: "Insufficient historical data to forecast" | Pick a more liquid stock |
| Flat series (zero variance) | Yellow warning badge: "LOW VARIANCE SERIES — Forecast may be unreliable" | Still usable; treat with higher skepticism |
| User daily quota exceeded | "Forecast quota reached. Wait until midnight UTC, or upgrade to Analyst role." | Wait or contact admin |
| Backend service unavailable | "Forecast service temporarily unavailable (HTTP 503). Retry in 30 seconds." | Click "Retry" button (auto 3 attempts) |

---

## 8. WATCHLISTS & PORTFOLIOS

### 8.1 Watchlists

**Create a Watchlist:**
1. Navigate → **Portfolio → Watchlists** (or click Watchlist star on any stock row)
2. Click **+ New Watchlist** (text button)
3. Enter: Name (required, max 60 chars), Description (optional, max 500 chars)
4. Save → New watchlist appears in sidebar

**Add to Watchlist (methods):**
- Method A: Ranking table → click "+WL" cell
- Method B: Stock detail page → click "Add to Watchlist" button (top right)
- Method C: Watchlist page → "Add Symbol" form (bulk: paste 1 symbol per line, up to 100)

**Remove from Watchlist:**
- Hover row → "-Remove" link appears on right

### 8.2 Portfolios

**Import Transactions (CSV):**
1. Portfolio page → "Import Transactions"
2. CSV format requirements (header row required):
   ```csv
   Date,Symbol,Quantity,Price,Type,Notes
   2026-01-15,AAPL,50,185.42,BUY,Initial position
   2026-02-20,AAPL,-10,198.77,SELL,Trimmed
   2026-03-10,MSFT,30,410.11,BUY,
   ```
3. Validations: Date ≤ today, Symbol is NASDAQ-listed, Quantity ≠ 0, Price > 0, Type ∈ {BUY,SELL,DIVIDEND,SPLIT}
4. Click "Validate" → preview of parsed rows + error count. Fix errors in CSV and re-upload.
5. Click "Commit Import" → transactions recorded, portfolio positions and P/L recalculated.

**Portfolio Views:**
- Holdings Table (Symbol, Shares, Avg Cost, Current Price, Market Value, Unrealized P/L $, Unrealized P/L %)
- Allocation Pie Chart (by Sector % of market value)
- Historical P/L Line Chart (daily mark-to-market, since portfolio inception)
- Risk Metrics Card: Portfolio Beta, Sharpe Ratio (1Y), VaR(95%), Max Drawdown

---

## 9. ALERTS ENGINE — REAL-TIME PRICE NOTIFICATIONS

### 9.1 Alert Types (Create at /alerts → + New Alert)

| Alert Type | Threshold Condition | Description |
|-----------|---------------------|-------------|
| PRICE_ABOVE | `last_trade > X` | Fires when market price rises ABOVE user-set dollar threshold |
| PRICE_BELOW | `last_trade < X` | Fires when market price drops BELOW threshold |
| PCT_CHANGE_1D | `abs(1d_pct_change) > X%` | Intraday % move exceeds threshold (e.g., 5%) |
| RSI_OVERBOUGHT | `RSI(14) > 70` | Technical overbought condition |
| RSI_OVERSOLD | `RSI(14) < 30` | Technical oversold condition |
| SMA_CROSS | `SMA(50) crosses above/below SMA(200)` | Golden cross / Death cross |
| DIMENSION_SCORE | `dimension.total_score crosses <threshold>` | Fundamental score threshold breach |

### 9.2 Alert Lifecycle States
`ACTIVE` → triggered → `FIRED` → user acknowledges → `ACKNOWLEDGED` OR auto-re-arm after cooldown (default 1 hour)

### 9.3 Notification Channels
Per-alert toggleable:
- ☐ In-app toast (top-right, requires browser tab open)
- ☐ Email (sent to user profile email)
- ☐ Browser Push Notification (after opt-in on first alert)

### 9.4 Alert Management
- `/alerts` page shows table: Symbol, Type, Threshold, Current Value, Status, Created, Actions
- Actions per row: Pause / Resume / Edit / Delete / View Trigger History
- Filters: Status (Active / Fired / Acknowledged / Paused), Symbol, Alert Type

---

## 10. NEWS & SENTIMENT ANALYSIS

Navigate to `/news` or view News section on Dashboard.

### 10.1 Article Card Fields
- **Headline** (text link → opens source)
- **Source** (Reuters, Bloomberg, CNBC, SeekingAlpha, PR Newswire, etc.)
- **Publication Timestamp** (relative: "2h ago", absolute on hover)
- **Sentiment Badge**:
  - Green · POSITIVE (score ≥ +0.35)
  - Gray · NEUTRAL (-0.35 < score < +0.35)
  - Red · NEGATIVE (score ≤ -0.35)
- **Relevant Symbols tag list** (click any tag → filters news to that symbol)

### 10.2 Sentiment Aggregate (above news feed)
- 7-day rolling sentiment trend line (daily average)
- Current 24h aggregate score: `+0.12 (SLIGHTLY POSITIVE)`

---

## 11. SEARCH — SYMBOL DISAMBIGUATION (NDX vs IXIC)

**CRITICAL REFERENCE (from PART-1):** When trading NAS100 on MetaTrader/cTrader/any CFD platform, you trade the **NASDAQ-100 (NDX)**, not the NASDAQ Composite (IXIC). This search page implements that disambiguation.

Global Search Bar (top of every page): type a symbol or company name, press Enter.

**Sample Searches and Expected Results:**
| User Input | Top Result 1 | Top Result 2 | Top Result 3 |
|-----------|-------------|-------------|-------------|
| `AAPL` | AAPL · Apple Inc. · Technology | | |
| `NAS100` | **⚠️ CFD REFERENCE: NAS100 = Nasdaq-100 (NDX)** (info banner) · ^NDX · Nasdaq-100 INDEX | ^IXIC · Nasdaq COMPOSITE INDEX | QQQ · Invesco QQQ Trust (Nasdaq-100 ETF) |
| `NDX` | ^NDX · Nasdaq-100 INDEX · (100 non-financial mega-caps) | NDX tooltip clarifies ≠ Composite | |
| `IXIC` | ^IXIC · Nasdaq COMPOSITE INDEX · (~3,000+ all-exchange listings) | IXIC tooltip clarifies ≠ NAS100 CFD | |
| `NASDAQ` | Search result header: "NASDAQ refers to two major indices — click to understand difference" (links to in-platform disambiguation page) · Shows both ^NDX and ^IXIC | | |

**Embedded Help Banner (appears on CFD symbol search):**
> 💡 Trader Note: The ticker `NAS100` on MetaTrader/cTrader/TradingView CFD platforms refers to the **Nasdaq-100 (NDX)** — 100 large non-financial stocks. This is DIFFERENT from the Nasdaq Composite (~3,000+ all-listed stocks, including financials). See `docs/project_closure/Nasdaq-Index-Comparison.md` for authoritative comparison.

---

## 12. SETTINGS & USER PROFILE

### 12.1 Profile Tab (/settings/profile)
- Full name, email (verified badge shown if email confirmed), Avatar (text-initials, per no-icon constraint — e.g., "JD" for John Doe)
- **Change Password** form: Current Password → New Password (min 8 chars, must contain: 1 uppercase, 1 lowercase, 1 digit, 1 special) → Confirm Password
- **Two-Factor Authentication** (TOTP): Click "Enable 2FA" → scan QR code with Authenticator app (Google Authenticator, 1Password, Authy) → enter 6-digit code → backup codes (10 codes, save these)

### 12.2 Preferences Tab
| Preference | Default | Options |
|-----------|---------|---------|
| Default Dashboard Date | Last Trading Day | Last Trading Day / Today / Yesterday / Custom default |
| Chart Theme | Light (market standard) | Light / Dark |
| Default Chart Timeframe | 1M | 1D / 1W / 1M / 3M / 6M / 1Y |
| Number Format | US English (1,234.56) | US / EU (1.234,56) / IN (1,23,456.78) |
| Currency Display | USD ($) | USD / EUR / GBP / JPY / AED / INR |
| Date Format | MM/DD/YYYY | MM/DD/YYYY / DD/MM/YYYY / YYYY-MM-DD (ISO 8601) |
| Risk Disclaimer Acknowledgment | — | Must check to unlock Forecast and Portfolio features |

---

## 13. KEYBOARD SHORTCUTS

Global shortcuts (work anywhere when a text input is NOT focused):

| Shortcut | Action |
|----------|--------|
| `/` | Focus Global Search bar |
| `g` then `d` | Go to Dashboard |
| `g` then `r` | Go to Ranking |
| `g` then `a` | Go to Alerts |
| `g` then `n` | Go to News |
| `g` then `p` | Go to Portfolio |
| `g` then `s` | Go to Settings |
| `?` | Open keyboard shortcut overlay |
| `Esc` | Close modal / cancel current form / blur search |
| `t` then `1` | In charts: timeframe 1D |
| `t` then `3` | 1M (t+3 = 1M shorthand) |
| `t` then `6` | 6M |
| `t` then `y` | 1Y |
| `Ctrl/Cmd + k` | Same as `/` — focus search |

---

## 14. FAQ — FREQUENTLY ASKED QUESTIONS

**Q1. Why are there gaps in my chart data on weekends and holidays?**
A: BedaanWaves displays only real trading days. The US stock market is closed on weekends and 9 public holidays (New Year's Day, MLK Jr Day, Presidents Day, Good Friday, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving Day, Christmas Day). The date range selector automatically resolves to the last trading day — this is intended behavior (EC-001).

**Q2. Can I change the scoring weights used in the Ranking table?**
A: Yes, if you have ANALYST or ADMIN role. ADMIN role can change system-wide default weights; ANALYST can create a private custom-weighted view.

**Q3. How real-time is the "real-time" price feed?**
A: The feed is a 1-second-resolution streaming tick via SSE over HTTP/2. It is NOT direct exchange level-2 data. The backend ingests from a primary provider with a throttled 1-second emit window, so expect 1-2 seconds of latency from actual tape time.

**Q4. Are my forecast predictions stored? Can I review history?**
A: Yes. Every forecast request is stored in the database with input parameters, timestamp, model version, and output. You can view your forecast history at `/settings/forecast-history` (USER: 30-day retention / ANALYST: 180-day / ADMIN: unlimited).

**Q5. Why can't I see the Financials tab for a symbol?**
A: This happens for two reasons: (1) the symbol is a recently-listed IPO with less than one quarter of SEC EDGAR filings, or (2) the quarterly data has not yet synced. Wait 24 hours and retry, or if you are ADMIN, go to Admin → Force Re-sync → Symbol = ticker.

**Q6. What happens to my alerts when the platform is down for maintenance?**
A: Alerts that should have fired during a maintenance window are backfilled at service-restore time against the "first trade after restoration" price. You get a single notification per missed alert with a "missed window" banner.

---

## 15. ERROR REFERENCE GUIDE

| User-Facing Message | HTTP Status | Root Cause | User Action | Escalation |
|---------------------|-------------|------------|-------------|------------|
| "Session expired. Please log in again." | 401 | JWT token expired (TTL: 30 minutes) | Refresh page → log in again | N/A |
| "You do not have permission to perform this action." | 403 | Role-based access denied | Contact admin for role upgrade | ADMIN user only |
| "Too many requests. Slow down (HTTP 429)." | 429 | Rate limit breached (100 req/min / 5,000 req/hr) | Wait 60 seconds and retry | If persistent, ADMIN can raise limits temporarily |
| "Data service is warming up. Try again in 10 seconds." | 202 | Initial cold-start cache miss on a complex query | Wait 10s, click Refresh | N/A |
| "Symbol not found in NASDAQ universe." | 404 | Symbol non-NASDAQ, delisted, or typo | Verify ticker spelling at /search | N/A |
| "Upstream data provider unavailable. (HTTP 502)" | 502 | Third-party ingestion API down | Retry in 60 seconds; check Status page banner | P3 support ticket if >30 minutes |
| "Internal server error (HTTP 500). Trace ID: abc-123-def-456" | 500 | Unhandled exception in backend | Report error via Feedback form with Trace ID | P2 support ticket with Trace ID |
| "Network request failed. Check your connection." | (N/A — browser offline) | No internet connectivity / CORS block | Check Wi-Fi/Ethernet; refresh; verify corporate VPN not blocking localhost:3000 | IT support if network issue |

---

*Document ID: BW-USERMAN-v2.0.0 | Effective: 2026-09-05 | Pages: ~16 printed*
