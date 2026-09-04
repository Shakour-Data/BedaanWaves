# BedaanWaves Project Audit Report

Generated: 2026-09-04

---

## 1. Temporary / Ad-Hoc / Unused Files

### 1.1 Backend Root (`backend/`)

**High confidence — one-off diagnostic scripts:**
- `backend/test_minimal.py` — Standalone FastAPI test app
- `backend/test_minimal2.py` — Standalone FastAPI test app (variant)
- `backend/test_market.py` — Standalone FastAPI app importing market router
- `backend/test_market2.py` — Standalone FastAPI app (variant import)
- `backend/test_market3.py` — Standalone FastAPI app (variant import)
- `backend/test_market4.py` — Standalone FastAPI app (with lifespan)
- `backend/test_all.py` — Standalone FastAPI app importing all routers
- `backend/test_urls.py` — Requests-based URL smoke test
- `backend/test_urls2.py` — Requests-based URL smoke test (variant)
- `backend/test_endpoints.py` — Requests-based endpoint smoke test (126 lines)
- `backend/test_conn.py` — Async DB connection test
- `backend/test_config.py` — Config print script
- `backend/test_app.py` — Route enumeration script
- `backend/test_lifespan.py` — Lifespan event test
- `backend/test_ingestion.py` — NasdaqIngestionService smoke test
- `backend/check_asset_classes.py` — SQL asset class check
- `backend/check_db_data.py` — SQL data existence check
- `backend/check_macro.py` — SQL macro indicator check
- `backend/check_symbol_data.py` — SQL symbol_data schema check
- `backend/temp_check_db.py` — Temporary table-count script
- `backend/final_db_check.py` — One-time database validation
- `backend/final_validation.py` — One-time project status validation
- `backend/validate_data.py` — One-time data completeness validation
- `backend/verify_schema.py` — One-time schema verification
- `backend/verify_realtime_data.py` — Real-time data verification (194 lines)
- `backend/fix_all_imports.py` — One-time bulk import fixer (contains old hardcoded paths)
- `backend/populate_database.py` — Large synthetic data population script (620 lines)
- `backend/populate_indices.py` — One-time index insertion script
- `backend/backfill_sec_financials.py` — One-time SEC financial backfill
- `backend/ingest_candles.py` — One-time candle ingestion runner
- `backend/ingest_candles_db.py` — One-time candle ingestion from DB
- `backend/gen_histories.py` — Coefficient history generation
- `backend/gen_features.py` — Processed feature generation
- `backend/gen_signals.py` — ML signal generation
- `backend/gen_macro.py` — Macro indicator generation
- `backend/generate_score_history.py` — Score history backfill
- `backend/generate_processed_data.py` — Large synthetic data generator (304 lines)
- `backend/generate_market_score_trend.py` — Market score trend backfill
- `backend/complete_snapshots.py` — Market snapshot generation (150 lines)
- `backend/run_nasdaq_backfill.py` — One-time Nasdaq full backfill runner
- `backend/run_init_sql.py` — One-time init.sql executor
- `backend/create_admin.py` — One-time admin user creation
- `backend/sec_cik_lookup.py` — Ad-hoc SEC CIK lookup test
- `backend/fetch_news.py` — Ad-hoc dashboard news fetcher (202 lines)
- `backend/fetch_missing.py` — Ad-hoc missing symbol fetcher
- `backend/fetch_indices.py` — Ad-hoc index fetcher

**Artifact / log files:**
- `backend/debug_token.txt` — Contains a hardcoded JWT (security risk)
- `backend/test_out.txt` — Empty test output artifact
- `backend/ls_out.txt` — Directory listing artifact
- `backend/install_log.txt` — pip install log (289 lines)
- `backend/assets.txt` — Stale asset list from old environment
- `backend/daily_update.bat` — Windows scheduled task batch file
- `backend/daily_update.log` — Scheduled task log
- `backend/test_results/` — Old pytest result text files

**Other:**
- `backend/populate_database.py.backup` — Backup created by `fix_all_imports.py`

### 1.2 Frontend Root (`frontend/`)

- `frontend/find_rolldown_parse.js` — Ad-hoc debugging script for rolldown parser
- `frontend/test-parser.js` — Babel parser smoke test (5 lines)
- `frontend/temp_emnapi.json` — Corrupted/accidentally saved JSON dump from emnapi (1200+ lines of bundled JS)

### 1.3 Recommendation

Move all backend root one-off scripts to a `scripts/` or `tools/` directory (or delete if no longer needed). Delete artifact files (`debug_token.txt`, `test_out.txt`, `ls_out.txt`, `install_log.txt`, `assets.txt`). Remove `temp_emnapi.json` and the two JS debug scripts from the frontend root. The `daily_update.bat` / `.log` pair should be moved to `scripts/` if still in use.

---

## 2. Duplicate / Near-Duplicate Code Patterns

### 2.1 Frontend: Duplicated Constants & Helpers

| Pattern | File(s) | Lines |
|---------|---------|-------|
| `API_BASE_URL` constant | `frontend/src/lib/api.ts` (line 4) and `frontend/src/lib/sse.ts` (line 1) | Both define identical fallback `"http://localhost:3000/api/v1"` |
| `num()` helper | `frontend/src/lib/api/stocks.ts` (line 88), `frontend/src/lib/api/scoring.ts` (line 45), `frontend/src/lib/api/ranking.ts` (line 63), `frontend/src/app/stocks/[symbol]/scoring/page.tsx` (line 40), `frontend/src/app/stocks/[symbol]/charts/page.tsx` (line 32) | Same `null/undefined → 0` + `parseFloat` logic duplicated 5 times |
| `clamp()` helper | `frontend/src/lib/api/scoring.ts` (line 51) and likely re-defined in page components | Identical `Math.max/min` clamp |
| `formatTimeAgo()` | `frontend/src/lib/api/dashboard.ts` (line 233) | May be duplicated in other dashboard components |

### 2.2 Frontend: Duplicated UI Formatting

| Pattern | File(s) |
|---------|---------|
| `priceFormatter: (p) => p.toLocaleString("en-US", { maximumFractionDigits: 2 })` | `AreaChart.tsx`, `BarChart.tsx`, `ColumnChart.tsx`, `CandlestickChart.tsx`, `LineChart.tsx`, `ScoreTrendChart.tsx` |
| `toLocaleString("en-US")` for counts/prices | `AssetTable.tsx`, `StockDashboardWidget.tsx`, `dashboard/page.tsx`, `portfolio/page.tsx`, `analysis/page.tsx`, `dashboard.ts` API helper, etc. |

### 2.3 Backend: Repeated `datetime.now(timezone.utc).isoformat()` Pattern

This exact expression appears in dozens of API route handlers:
- `backend/app/api/routes/analysis.py` (lines 102, 119, 195, 278, 337, 400, 456, 507, 554, 603, 721, 753, 815, 870, 885, 898)
- `backend/app/api/routes/symbols.py` (lines 57, 72, 87, 102, 116, 143, 170, 191)
- `backend/app/api/routes/dashboard.py` (line 238)
- `backend/app/api/routes/health.py` (lines 34, 58, 112, 121)
- `backend/app/api/routes/data_health.py` (lines 35, 41, 50)
- `backend/app/api/routes/system.py` (line 90)
- `backend/app/api/routes/alerts.py` (line 501)
- `backend/app/api/routes/forecast.py` (lines 460, 509, 510, 519)
- `backend/app/api/routes/compare.py` (line 238)

**Recommendation:** Extract to a shared helper like `utc_now_iso()` in `app/core/utils.py` or `app/core/config.py`.

### 2.4 Backend: Repeated `import asyncio` Inside Functions

Multiple services import `asyncio` inside method bodies rather than at module top-level:
- `backend/app/services/data/stock_service.py` (line 48: `__import__("asyncio").get_event_loop()`)
- `backend/app/services/nlp/sentiment_analysis_service.py` (line 126)
- `backend/app/services/nlp/news_summarization_service.py` (line 159)
- `backend/app/services/nlp/multilingual_news_service.py` (line 10)
- `backend/app/services/nlp/document_extraction_service.py` (line 187)
- `backend/app/services/ml/prediction_service.py` (line 65)
- `backend/app/services/ml/anomaly_detection_service.py` (line 83)
- `backend/app/services/analysis/scoring_service.py` (line 436)
- `backend/app/services/analysis/ranking_service.py` (line 97)
- `backend/app/services/core/base_service.py` (lines 206, 273)

**Recommendation:** Move `import asyncio` to top-level in these files, or remove if truly unused.

---

## 3. Dead Code, Unused Imports, Commented-Out Blocks

### 3.1 Backend

**Large commented-out block in `backend/app/main.py` (lines 250–258):**
```python
# Step 2: Auto-create database if missing
# try:
#     _ensure_database()
# except Exception as e:
#     logger.warning(f"Database auto-creation failed: {e}")

# Step 3: Auto-run migrations
# Disabled for audit testing
pass
```
The `pass` statement is dead code left after disabling migrations.

**Commented-out code lines in `backend/app/main.py` (lines 251–254, 260–262):**
- Database auto-creation try/except block
- Step 4 auto-seed comment

**`# type: ignore` usage (likely unnecessary with modern type checkers):**
- `backend/app/domain/shared/result.py` (line 35)
- `backend/app/domain/shared/optional.py` (lines 40, 45)
- `backend/app/infrastructure/utils/circuit_breaker.py` (line 41)

**`# noqa: E712` for `== True` comparisons (style issue):**
- `backend/app/api/routes/dashboard.py` (line 288)
- `backend/app/api/routes/specialized.py` (lines 54, 85)
- `backend/app/services/analysis/market_score_trend_service.py` (line 288)
- `backend/app/services/analysis/dashboard_service.py` (line 391)

**`if __name__ == "__main__":` blocks in test files (in `backend/app/tests/`):**
- `test_ranking.py` (line 65)
- `test_score_trend_dashboard.py` (line 208)
- `test_market_score_trend_service.py` (line 210)
- `test_level_trend_dashboard.py` (line 238)
- `test_generate_market_score_trend_cli.py` (line 72)
- `test_fundamental_ratios.py` (line 194)

These are inside the `app/tests/` directory (which is proper test location) but contain executable main blocks that are atypical for pytest-based tests.

### 3.2 Frontend

**Minimal dead code detected.** The codebase is relatively clean. The main issues are the duplicate helpers listed in Section 2 and the `false ? "fa-IR" : "en-US"` ternary in `frontend/src/app/analysis/page.tsx` (lines 128, 147, 169, 181, 208) which always evaluates to `"en-US"` — the `"fa-IR"` branch is dead code.

---

## 4. i18n / Translation File Duplicates

### 4.1 Duplicate Keys Between `en.json` and `auth.ts`

`frontend/src/i18n/auth.ts` defines a separate `en` object with keys that largely overlap with `frontend/src/i18n/en.json` under `app.auth` and `app.signup` / `app.login` / `app.reset_password` / `app.forgot_password`.

**Duplicate / overlapping keys:**

| Key in `auth.ts` | Overlapping path in `en.json` |
|------------------|-------------------------------|
| `login_title` | `app.login.title` |
| `login_email` | `app.login.email` |
| `login_password` | `app.login.password` |
| `login_forgot_password` | `app.auth.forgot_password`, `app.login.forgot_password`, `app.forgot_password` (3 occurrences) |
| `login_submit` | `app.login.submit_button` |
| `login_no_account` | `app.login.no_account` |
| `signup_login_link` | `app.login.login_link` |
| `auth_loading` | `app.auth.loading`, `app.login.loading` |
| `auth_error_authentication` | `app.auth.error_authentication` |
| `login_back_to_login` | `app.reset_password.back_to_login`, `app.login.back_to_login` |
| `auth_remember_me` | `app.auth.remember_me` |
| `auth_language` | `app.auth.language` |
| `auth_show_password` | `app.auth.show_password` |
| `auth_hide_password` | `app.auth.hide_password` |
| `signup_title` | `app.signup.title` |
| `signup_name` | `app.signup.name` |
| `signup_email` | `app.signup.email` |
| `signup_password` | `app.signup.password` |
| `signup_confirm_password` | `app.signup.confirm_password` |
| `signup_submit` | `app.signup.submit_button` |
| `signup_already_have_account` | `app.signup.already_have_account` |
| `signup_error_password_length` | `app.signup.error_password_length` |
| `signup_error_password_match` | `app.signup.error_password_match` |

**Recommendation:** Consolidate into a single source of truth. Either:
- Remove `auth.ts` and source all strings from `en.json`, or
- Make `auth.ts` the source of truth for auth strings and remove duplicates from `en.json`.

The current split risks drift where one file is updated and the other is not.

---

## 5. Other Cleanup Recommendations

### 5.1 Security
- **Delete `backend/debug_token.txt` immediately.** It contains a hardcoded JWT (`eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`) that could be used to access the admin account if the secret key is compromised.

### 5.2 Hardcoded Paths
Multiple backend root scripts contain hardcoded Windows paths that will not work on other machines or even other user profiles:
- `backend/fix_all_imports.py` line 73: `r"E:\Shakour\BedaanProjects\OldFils\BedaanWaves\backend"`
- `backend/final_validation.py` line 9: `sys.path.insert(0, 'E:/Shakour/BedaanProjects/OldFils/BedaanWaves/backend')`
- `backend/run_init_sql.py` line 5: `sys.path.insert(0, r"C:\Users\Administrator\Documents\BedaanWaves\backend")`
- `backend/test_conn.py` line 3: `sys.path.insert(0, r"C:\Users\Administrator\Documents\BedaanWaves\backend")`
- `backend/verify_schema.py` line 5: `sys.path.insert(0, r"C:\Users\Administrator\Documents\BedaanWaves\backend")`

**Recommendation:** Use relative paths or environment variables.

### 5.3 Deprecated Async Pattern
`backend/app/services/data/stock_service.py` line 48 uses:
```python
loop = __import__("asyncio").get_event_loop()
```
This is deprecated in Python 3.10+ and will be removed in Python 3.12+. Replace with `asyncio.get_event_loop()` at top-level or refactor to `asyncio.run()`.

### 5.4 Duplicate Chart-Time Logic
`frontend/src/components/charts/chart-time.ts` and the inline `toTimestamp` logic in `frontend/src/lib/chart-time.ts` serve similar purposes. The component-local file should be removed if it duplicates the lib version.

### 5.5 Test Artifacts in Repo
- `backend/test_results/` — 7 old `.txt` result files from 2026-08-09
- `frontend/test-results/` — Playwright trace zip and error context markdown
- `frontend/.next/` — Build artifacts (already gitignored presumably)
- `backend/__pycache__/` — Python cache (already gitignored presumably)

### 5.6 `backend/app/tests/application/` Import Errors
`backend/test_out.txt` shows `tests/application/test_cache_service.py` fails with `ModuleNotFoundError: No module named 'backend'`. This suggests the `application/` test subdirectory is either misconfigured or abandoned.

---

## 6. Summary of Recommended Actions

| Priority | Action | Location |
|----------|--------|----------|
| **P0** | Delete `debug_token.txt` (security) | `backend/debug_token.txt` |
| **P0** | Consolidate `auth.ts` + `en.json` i18n duplicates | `frontend/src/i18n/` |
| **P1** | Extract `API_BASE_URL` to shared config | `frontend/src/lib/api.ts`, `frontend/src/lib/sse.ts` |
| **P1** | Extract shared `num()` / `clamp()` helpers | `frontend/src/lib/api/` |
| **P1** | Extract shared `utc_now_iso()` helper | `backend/app/api/routes/` |
| **P1** | Remove large commented-out block + dead `pass` | `backend/app/main.py` lines 250–258 |
| **P2** | Move ~40 ad-hoc scripts from `backend/` root to `scripts/` or delete | `backend/*.py` (root) |
| **P2** | Delete frontend root debug scripts & corrupted JSON | `frontend/find_rolldown_parse.js`, `frontend/test-parser.js`, `frontend/temp_emnapi.json` |
| **P2** | Remove artifact/log files | `backend/test_out.txt`, `backend/ls_out.txt`, `backend/install_log.txt`, `backend/assets.txt`, `backend/daily_update.bat`, `backend/daily_update.log`, `backend/test_results/`, `frontend/test-results/` |
| **P2** | Fix hardcoded paths in ad-hoc scripts | Various `backend/*.py` |
| **P2** | Fix deprecated `get_event_loop()` usage | `backend/app/services/data/stock_service.py` |
| **P3** | Remove dead `false ? "fa-IR" : "en-US"` branches | `frontend/src/app/analysis/page.tsx` |
| **P3** | Delete `populate_database.py.backup` | `backend/populate_database.py.backup` |

---

*This audit is read-only. No files were modified.*
