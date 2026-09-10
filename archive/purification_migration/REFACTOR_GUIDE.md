# BedaänWaves — Purification Audit (FULL Nasdaq exchange scope)

> **Authoritative scope:** The BedaänWaves platform is exclusively for
> instruments that trade on the **Nasdaq Stock Market**. That includes
> the ~3,500+ equities, ETFs, ADRs, rights, warrants, and units that
> list on Nasdaq (any row with `assets.market = 'NASDAQ'`), the
> **Invesco QQQ** ETF, and the **Nasdaq Composite Index (^IXIC)** as a
> reference benchmark.
>
> Nothing else is allowed: no NYSE/AMEX/OTC equities, no non-Nasdaq
> indices (S&P 500, Dow, Russell, VIX, FTSE, DAX, N225, HSI), no
> NYSE-Arca-listed sector ETFs (XLK/XLV/XLF/XLE/...), no futures
> (GC=F, CL=F, ...), no crypto, no forex.

## Deliverables in this folder

| File | Purpose |
|---|---|
| `purify_to_nasdaq.sql` | One-shot SQL purge. Deletes any row with `market <> 'NASDAQ'` plus a hard-deny list. No DROP TABLE. |
| `verify_purification.py` | Post-purge audit script. Exits 0 on clean DB, 1 on violations. |
| `REFACTOR_GUIDE.md` | **(this file)** Phase 2/3/4/5 instructions. |

## Run order

```bash
# 1. Purge the database
psql -U postgres -d bedaanwaves_db -v ON_ERROR_STOP=1 -f purification/purify_to_nasdaq.sql

# 2. Verify
python purification/verify_purification.py
```

---

## Phase 1 — Database Purification (✅ automated)

Implemented in `purify_to_nasdaq.sql`. Key properties:

- **No DROP TABLE.** Only DELETE statements + CHECK constraints.
- All FKs from child tables to `assets.id` temporarily altered to
  `ON DELETE CASCADE` so the asset purge can't be blocked by orphan
  rows.
- **Two deletion criteria**, either one is sufficient:
  1. `assets.market <> 'NASDAQ'` (catches NYSE, AMEX, OTC, BINANCE,
     FOREX, CRYPTO, ...).
  2. `assets.symbol` in the hard-deny list (catches `^GSPC`, `^DJI`,
     `^RUT`, `^VIX`, `XLK`, `SPY`, `TLT`, `GC=F`, `EURUSD`, etc., which
     some yfinance feeds tag as 'NASDAQ' incorrectly).
- ^IXIC and QQQ upserted as reference rows if missing.
- User-linked favourites/alerts/watchlists cleared for offenders
  (users preserved).
- New CHECK constraints:
  - `market = 'NASDAQ'`
  - `asset_class IN ('EQUITY','ETF','INDEX','ADR','RIGHT','WARRANT','UNIT')`
- Post-purge RAISE EXCEPTION rolls back on any residual violation.
- VACUUM ANALYZE + REINDEX at the end.

**No new symbol whitelist file is needed** — the 5,569 symbols in
`database/insert_nasdaq_symbols.sql` are all legitimate Nasdaq listings
and will pass through the script untouched. The only rows that get
deleted are the ones tagged with the wrong `market` or hard-deny list.

---

## Phase 2 — Backend Code Purification

The backend code is much closer to compliant than I initially thought.
Almost all of the "non-Nasdaq" references in the audit are either
guard-rail docstrings (intentional) or stale enum values. The real
edits are small.

### 2.1 Hard-coded tickers

| File:Line | Current | Change |
|---|---|---|
| `backend/app/api/routes/stocks.py:38` | `DEFAULT_POPULAR_TICKERS = ["AAPL","MSFT","GOOGL","AMZN","META","TSLA","NVDA","BRK-B"]` | `BRK-B` is **NYSE** — drop it. List becomes `["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA"]` |
| `frontend/src/app/stocks/page.tsx:12` | mirrors the above | Same change |

### 2.2 Non-Nasdaq index endpoints

**File:** `backend/app/api/routes/market.py:377-379`

```python
{"symbol": "INX", "yf_symbol": "^GSPC", "name": "S&P 500"},
{"symbol": "DJI", "yf_symbol": "^DJI",  "name": "Dow Jones Industrial Average"},
{"symbol": "RUT", "yf_symbol": "^RUT",  "name": "Russell 2000"},
```

→ **Delete all three rows.** Keep only `^IXIC` (Nasdaq Composite) on L376.
Update the docstring on L390 to: *"Live prices for the Nasdaq Composite Index (^IXIC)."*

### 2.3 User market preferences

**File:** `backend/app/api/routes/settings.py:26`

- Drop the `{"id":"spx", "name":"S&P 500", ...}` entry. Keep only the Nasdaq entry (already present as `ixic`).

**File:** `backend/app/services/user/user_market_settings_service.py:59`

- `["SPX", "DJI", "IXIC", "RUT"]` → `["IXIC"]`
- L165 (markets list) — `NASDAQ, NYSE, LSE, XETRA, Euronext, ...` → `["NASDAQ"]`
- L168 (currencies) — trim to `["USD"]` (no FX)

### 2.4 API client / symbol registry

**File:** `backend/app/services/data/api_client.py:22-25, 221-275`

Replace the multi-exchange enum and the index map:

```python
# L22-25 — REMOVE NYSE, FOREX enums and the SUPPORTED list
class Market(str, Enum):
    NASDAQ = "nasdaq"
SUPPORTED = [Market.NASDAQ]

# L221-275 — replace multi-index dict with ^IXIC only
INDEX_SYMBOL_MAP = {"^IXIC": "Nasdaq Composite"}
SUPPORTED_INDICES = ("^IXIC",)
```

### 2.5 Macro / fundamental analysis

**File:** `backend/app/services/analysis/fundamental_service.py:221,225`

```python
# CURRENT
MacroIndicator.indicator_code.in_(["^VIX", "^GSPC"])
# → REPLACE WITH
MacroIndicator.indicator_code.in_(["^IXIC"])
```
Update the L221 docstring accordingly.

**File:** `backend/app/services/data/nasdaq_ingestion_service.py:9,56`

- L9 docstring lists `^GSPC, ^VIX, ^TNX, DX-Y.NYB, GC=F, CL=F` → rewrite to "Ingestion targets Nasdaq-listed assets, QQQ, and ^IXIC."
- L56 `"^GSPC": ("S&P 500","Index")` row → delete.

### 2.6 Sector ETF mapping (illegal)

**File:** `backend/app/services/specialized/sector_filter_service.py:87-95`

The State Street Select SPDRs (`XLK/XLV/XLF/XLE/XLB/XLI/XLY/XLP/XLU`) are listed on **NYSE Arca**, not Nasdaq. Replace the whole ETF proxy map with GICS sector names only (no ticker references):

```python
SECTOR_KEYWORDS = {
    "Technology":      ["Information Technology", "Software", "Semiconductors"],
    "Healthcare":      ["Health Care", "Biotechnology", "Pharmaceutical"],
    "Financial":       ["Banks", "Capital Markets", "Insurance"],
    "Energy":          ["Energy", "Oil", "Gas"],
    "Materials":       ["Materials"],
    "Industrials":     ["Industrials", "Aerospace & Defense"],
    "Consumer Disc.":  ["Consumer Discretionary", "Retail"],
    "Consumer Stap.":  ["Consumer Staples", "Beverages", "Food"],
    "Utilities":       ["Utilities"],
    "Telecom":         ["Telecommunication"],
}
```

### 2.7 International market stub

**File:** `backend/app/services/specialized/international_market_service.py:52-53`

- L52 `"primary_exchange": "NYSE"` → `"primary_exchange": "NASDAQ"`
- L53 `"major_indices": ["SPX","DJI","IXIC","RUT"]` → `["IXIC"]`

### 2.8 Currency / forex removal

**File:** `backend/app/services/analysis/currency_conversion_service.py`

- L24–26, L36–39, L250–255, L277–279 — delete every FX pair definition (`EUR`, `GBP`, `JPY`, `CNY`). Replace with a single USD pass-through:
  ```python
  SUPPORTED_CURRENCIES = ("USD",)
  ```

**File:** `backend/app/services/analysis/currency_regime_service.py:49,77` — limit currencies to `["USD"]`.

**File:** `backend/app/services/system/scheduler_service.py:874-876` — delete the three FX rate jobs (`USD→EUR/GBP/JPY`).

### 2.9 Validation middleware (rejects illegal symbols)

`backend/app/api/middleware/nasdaq_symbol_guard.py` (new file):

```python
"""Reject any API request whose symbol is outside the Nasdaq exchange."""
import re
from pathlib import Path
import sys
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS.parent))
from verify_purification import FORBIDDEN_SYMBOLS  # noqa: E402

FORBIDDEN = {s.upper() for s in FORBIDDEN_SYMBOLS}
SYMBOL_PARAMS = ("symbol", "symbols", "ticker", "tickers", "yf_symbol")
ALLOWED_MARKETS = {"NASDAQ"}


def _bad_symbol(sym: str) -> bool:
    if not sym:
        return False
    return sym.upper() in FORBIDDEN


class NasdaqSymbolGuard(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        params = dict(request.query_params)
        try:
            body = await request.json()
            if isinstance(body, dict):
                params.update({k: v for k, v in body.items()
                               if k in SYMBOL_PARAMS})
        except Exception:
            pass

        for key in SYMBOL_PARAMS:
            value = params.get(key)
            if not value:
                continue
            candidates = value if isinstance(value, (list, tuple)) else [value]
            for sym in candidates:
                if _bad_symbol(str(sym)):
                    return JSONResponse(
                        {"detail": f"symbol {sym!r} is not Nasdaq-listed"},
                        status_code=422,
                    )
        return await call_next(request)
```

Wire it into `backend/app/main.py` after the existing middleware.

### 2.10 Tests

- Keep all existing `test_asset_model_guards.py` cases — they assert
  `CRYPTO`, `NYSE`, `BINANCE` rejection and are now positive coverage.
- **Add new test** in `backend/app/tests/api/test_nasdaq_only_purge.py`
  that runs `purify_to_nasdaq.sql` against a transactional fixture and
  asserts that only `market = 'NASDAQ'` rows remain and the hard-deny
  list is gone.

---

## Phase 3 — Frontend Purification

### 3.1 Crypto-pattern detection (intentional — keep)

`frontend/src/lib/dashboard-data.ts:48-75` — this is the **reject** logic
for non-Nasdaq patterns (`BTC-USD`, `ETHUSDT`, etc.). Keep it; update the
L66 comment to clarify intent.

### 3.2 `POPULAR_TICKERS`

`frontend/src/app/stocks/page.tsx:12` — drop `"BRK-B"` (matches backend
change in 2.1).

### 3.3 Dropdowns / routes

No `/sp500`, `/dow`, `/spy`, `/crypto`, `/forex` routes exist in the
frontend source (verified by grep). The market-options selector is
served by `backend/app/api/routes/settings.py` — fixing that endpoint
(Phase 2.3) automatically cleans the dropdown.

### 3.4 Default chart / widget

Driven by the API response. Once `^GSPC/^DJI/^RUT` rows are removed in
Phase 2.2, the widget will show `^IXIC` only. No frontend changes
required.

---

## Phase 4 — Documentation Purification

### 4.1 Project introduction

Edit these files to use the new scope statement:

> **BedaänWaves is a platform exclusively for instruments that trade on
> the Nasdaq Stock Market. This includes Nasdaq-listed equities, ETFs,
> ADRs, rights, warrants, and units, plus the Invesco QQQ ETF and the
> Nasdaq Composite Index (^IXIC) as a reference benchmark. No other
> exchanges, indices, cryptocurrencies, or forex instruments are in
> scope.**

Files:

- `README.md` (root)
- `docs/README.md`
- `docs/AGENTS.md`
- `docs/01_overview/OVERVIEW_executive-summary_v1.md`
- `docs/01_overview/OVERVIEW_project-plan_v1.md`
- `docs/01_overview/OVERVIEW_agent-reference_v1.md`

### 4.2 Replace example tickers

**File:** `docs/04_services/SERVICES_analysis-tier3_v1.md`

| Line | Current | Replace with |
|---|---|---|
| L549 | `"symbols": ["SPY","TLT","GSG"]` | `"symbols": ["AAPL","MSFT","QQQ"]` |
| L556 | `"assets": ["AAPL","BTC-USD","GC=F","TLT"]` | `"assets": ["AAPL","MSFT","NVDA"]` |
| L842 | `{"symbol":"BRK.B", ...}` | `{"symbol":"AAPL", ...}` |
| L843 | `{"symbol":"JNJ", ...}` | `{"symbol":"MSFT", ...}` |

### 4.3 Database docs

**File:** `docs/06_database/DB_schema_v1.md`

- L51 column comment: `-- NASDAQ, NYSE, LSE, AMEX, OTC` → `-- NASDAQ only (CHECK constraint)`.

**File:** `docs/06_database/DB_schema_supplemental_v1.md:157-161`

- Delete the "indices / benchmarks" section that references `SPX`, `VIX`. Replace with: "The only index row kept is `^IXIC` (Nasdaq Composite)."

### 4.4 Architecture / service docs

Files (search-replace each):

- `docs/02_architecture/ARCH_architecture-design_v1.md` L39
- `docs/03_technology/TECH_stack_v1.md` L354, L481
- `docs/04_services/SERVICES_data-tier2_v1.md` L810–869
- `docs/04_services/SERVICES_specialized-tier7_v1.md` L62–63
- `docs/04_services/SERVICES_analysis_macro_v1.md` L20, L47
- `docs/04_services/SERVICES_analysis_risk_v1.md` L44
- `docs/08_frontend/FE_page-stock-v1.md` L21
- `docs/08_frontend/FE_page-dashboard_v1.md` L18
- `docs/08_frontend/FE_page-portfolio_v1.md` L9
- `docs/08_frontend/FE_page-analysis_v1.md` L10

Search-replace rules:

- `NYSE, NASDAQ, LSE, ...` → `NASDAQ`
- `S&P 500` / `SPX` / `^GSPC` → **delete reference** (or replace with `Nasdaq-100 / QQQ / ^IXIC` if contextually meaningful)
- `Dow Jones` / `DJI` / `^DJI` → **delete**
- `Russell 2000` / `RUT` / `^RUT` → **delete**
- `Forex`, `crypto`, `Bitcoin`, `BTC`, `ETH` → **delete paragraph**

### 4.5 Legacy docs

`docs/11_legacy/` is explicitly archived. Add a banner:

```markdown
> **ARCHIVED 2026-09-04.** These documents describe a previous
> multi-market scope (NYSE, LSE, FWB, HKEX, crypto, forex). They do
> **not** reflect the current Nasdaq-only product scope.
```

---

## Phase 5 — Final Verification & Audit Report

### 5.1 Database verification queries

```sql
-- (a) Total Nasdaq-listed assets
SELECT COUNT(*) AS total_nasdaq_assets FROM assets WHERE market = 'NASDAQ';

-- (b) Breakdown by asset class
SELECT asset_class, COUNT(*)
  FROM assets
 GROUP BY asset_class
 ORDER BY asset_class;

-- (c) No non-NASDAQ rows
SELECT COUNT(*) AS bad_market
  FROM assets
 WHERE market IS DISTINCT FROM 'NASDAQ';

-- (d) Reference rows present
SELECT symbol, asset_class
  FROM assets
 WHERE symbol IN ('^IXIC','QQQ');

-- (e) Hard-deny list fully gone
SELECT symbol FROM assets
 WHERE UPPER(symbol) IN (
   '^GSPC','^DJI','^RUT','^VIX','^TNX','^SPX',
   'XLK','XLV','XLF','XLE','XLB','XLI','XLY','XLP','XLU',
   'SPY','VOO','IVV','TLT','HYG','GLD','SLV','EEM','VWO','IWM',
   'GC=F','CL=F','SI=F','NG=F',
   'EURUSD','USDJPY','GBPUSD','USDEUR','USDGBP'
 );

-- (f) Orphan child rows
SELECT 'price_candles' AS tbl, COUNT(*) FROM price_candles c
  LEFT JOIN assets a ON a.id = c.asset_id
 WHERE c.asset_id IS NOT NULL AND a.id IS NULL
UNION ALL SELECT 'ml_signals',  COUNT(*) FROM ml_signals  c
  LEFT JOIN assets a ON a.id = c.asset_id
 WHERE c.asset_id IS NOT NULL AND a.id IS NULL
UNION ALL SELECT 'news',        COUNT(*) FROM news        c
  LEFT JOIN assets a ON a.id = c.asset_id
 WHERE c.asset_id IS NOT NULL AND a.id IS NULL
UNION ALL SELECT 'alerts',      COUNT(*) FROM alerts      c
  LEFT JOIN assets a ON a.id = c.asset_id
 WHERE c.asset_id IS NOT NULL AND a.id IS NULL;
```

### 5.2 Code grep audit

Run from repo root:

```bash
# Hard-deny tickers — must NOT appear (except in guard rails / tests)
rg -nP '\b(SPY|VOO|IVV|IWM|DIA|BRK-?B|TLT|HYG|GLD|SLV|EEM|VWO|XLK|XLV|XLF|XLE|XLB|XLI|XLY|XLP|XLU|GC=F|CL=F|EURUSD|USDJPY|GBPUSD)\b' backend/ frontend/ docs/

# Non-Nasdaq index symbols
rg -nP '\^GSPC|\^DJI|\^RUT|\^VIX|\^TNX|\^FTSE|\^GDAXI|\^N225|\^HSI' backend/ frontend/ docs/

# Crypto
rg -niw 'bitcoin|crypto|ethereum|forex|btc|eth|xbt|usdt|binance|coinbase|kraken' backend/ frontend/ docs/

# S&P / Dow text
rg -in 'S&P|S&P ?500|sp500|dow jones|dow 30|wall ?street|spx|djia' backend/ frontend/ docs/
```

Every match must be:
1. In a docstring that **describes** the rejection (e.g. `dashboard.py:181`), or
2. In a test that asserts the rejection, or
3. Removed/edited per the Phase 2/3/4 tables above.

### 5.3 Programmatic check (no DB needed)

```bash
python - <<'PY'
import pathlib, re, sys
FORBIDDEN = {
    '^GSPC','^DJI','^RUT','^VIX','^TNX','^SPX',
    'SPY','VOO','IVV','IWM','DIA','BRK-B','TLT','HYG','GLD','SLV',
    'EEM','VWO','XLK','XLV','XLF','XLE','XLB','XLI','XLY','XLP','XLU',
    'GC=F','CL=F','SI=F','NG=F','EURUSD','USDJPY','GBPUSD',
}
TICKER_RE = re.compile(r'["\']([A-Z][A-Z0-9.\-^=]{0,7})["\']')
skip = {".git","node_modules",".next","purification","__pycache__",
         "pginst_extracted",".pytest_cache","database"}
bad = []
for p in pathlib.Path(".").rglob("*"):
    if not p.is_file(): continue
    if any(part in p.parts for part in skip): continue
    if p.suffix not in (".py",".ts",".tsx",".js",".jsx",".md",".sql"): continue
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception: continue
    found = {m.group(1) for m in TICKER_RE.finditer(text)}
    hits = {s for s in found if s.upper() in FORBIDDEN}
    if hits: bad.append((p, hits))
if not bad:
    print("CLEAN: no non-Nasdaq tickers found in source.")
else:
    for p,h in bad: print(p, "->", h)
    sys.exit(1)
PY
```

### 5.4 Sign-off

| Layer | Owner | Status |
|---|---|---|
| DB schema CHECK constraints | `purify_to_nasdaq.sql` | ✅ added |
| DB rows (data) | `purify_to_nasdaq.sql` + `verify_purification.py` | ✅ |
| Backend Python | Phase 2 diff above | ⏳ TODO |
| Backend middleware | `nasdaq_symbol_guard.py` | ⏳ TODO |
| Frontend TS/TSX | Phase 3 diff above | ⏳ TODO |
| Docs | Phase 4 diff above | ⏳ TODO |
| Tests | new `test_nasdaq_only_purge.py` | ⏳ TODO |

When all rows are ✅, re-run:

```bash
python purification/verify_purification.py    # must print PASS
```

and the Phase 5 grep audit — both must report 0 violations.