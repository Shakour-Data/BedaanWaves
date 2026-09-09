# BedaanWaves Backend — Test Coverage Gap Analysis

## 1. Critical Finding: pytest.ini Misconfiguration

**`pytest.ini` sets `testpaths = tests`, which completely excludes `backend/app/tests/` from collection.**

| Directory | Tests Collected | Status |
|-----------|----------------|--------|
| `backend/tests/` | 732 | Collected |
| `backend/app/tests/` | 0 | **EXCLUDED** |

The `app/tests/` directory contains actual FastAPI `TestClient` integration tests for auth, password reset, filter, settings, and dashboard endpoints. These tests are **dead code** — they are never executed by `pytest` and provide zero regression protection.

---

## 2. Endpoints With NO HTTP-Level Test Coverage

The following mounted endpoints have **zero** end-to-end or HTTP-layer test coverage (neither in `backend/tests/` nor in the excluded `backend/app/tests/`):

| Router | Prefix | Endpoints | HTTP Test Coverage |
|--------|--------|-----------|-------------------|
| `stocks` | `/api/v1/stocks` | `GET /search`, `GET /{ticker}`, `POST /batch`, `POST /v2/batch`, `POST /export`, `POST /import` | **None** |
| `market` | `/api/v1/market` | `GET /symbols`, `GET /price-history`, `GET /latest-prices`, `GET /market-overview`, `GET /nasdaq-dashboard`, `GET /indices`, `GET /industry-ranking`, `GET /{symbol}/orderbook`, `GET /{symbol}/orderbook/history` | **None** |
| `analysis` | `/api/v1/analysis` | `GET /signals/{symbol}`, `GET /signals-summary`, `GET /signals`, `GET /top-performers`, `GET /risk-analysis/{symbol}`, `GET /technical/{symbol}`, `GET /risk/{symbol}`, `GET /fundamental/{symbol}`, `GET /momentum/{symbol}`, `GET /volatility/{symbol}`, `POST /scoring`, `GET /scoring/{symbol}`, `GET /sentiment/{symbol}`, `POST /scoring/rank`, `GET /fundamental/batch`, `GET /fundamentals/health`, `GET /scoring/history/{symbol}`, `GET /scoring/hierarchy/{symbol}`, `GET /scoring/coefficients/{symbol}`, `GET /macro/indicators`, `GET /macro/forecast` | **None** |
| `portfolio` | `/api/v1/portfolio` | `POST /`, `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `POST /{id}/holdings`, `GET /{id}/holdings`, `DELETE /{id}/holdings/{hid}` | **None** |
| `history` | `/api/v1/history` | `GET /{ticker}`, `GET /volume/{ticker}` | **None** |
| `news` | `/api/v1/news` | `GET /market`, `GET /{ticker}`, `GET /search`, `GET /category/{category}`, `GET /categories`, `GET /regions`, `GET /market-moving` | **None** |
| `ml` | `/api/v1/ml` | `GET /predict/{symbol}`, `GET /patterns/{symbol}`, `GET /anomaly/{symbol}`, `POST /optimize`, `POST /forecast` | **None** |
| `users` | `/api/v1/users` | `GET /me`, `PATCH /me`, `GET /me/preferences`, `GET /me/preferences/{key}`, `PUT /me/preferences/{key}`, `DELETE /me/preferences/{key}` | **None** |
| `watchlists` | `/api/v1/watchlists` | `POST /`, `GET /`, `GET /{id}`, `DELETE /{id}`, `PUT /{id}`, `POST /{id}/items`, `DELETE /{id}/items/{iid}`, `PUT /{id}/items/{iid}` | **None** |
| `notifications` | `/api/v1/notifications` | `GET /`, `POST /{id}/read`, `POST /read-all`, `DELETE /{id}` | **None** |
| `specialized` | `/api/v1/specialized` | `GET /sectors/summary`, `POST /screen`, `POST /compare`, `POST /correlation`, `GET /calendar/month`, `GET /calendar/events`, `POST /calendar/events` | **None** |
| `system` | `/api/v1/system` | `GET /scheduler/jobs`, `POST /scheduler/jobs`, `DELETE /scheduler/jobs/{name}`, `POST /scheduler/jobs/{name}/run`, `GET /metrics`, `GET /metrics/prometheus`, `GET /metrics/health`, `POST /queue/jobs`, `GET /queue/jobs/{id}`, `GET /queue/stats`, `GET /queue/dead-letter`, `GET /news-sources`, `POST /news-sources/{id}/toggle` | **None** |
| `live` | `/api/v1/live` | `GET /quote/{symbol}`, `GET /intraday/{symbol}`, `GET /market`, `GET /scores`, `GET /news`, `GET /orderbook/{symbol}`, `GET /streams` | **None** |
| `live_sse` | `/api/v1/live` | `GET /quote/{symbol}/stream`, `GET /intraday/{symbol}/stream`, `GET /market/stream`, `GET /scores/stream`, `GET /news/stream`, `GET /orderbook/{symbol}/stream` | **Partial** (SSE route registration & headers tested in `backend/tests/`) |
| `dashboard` | `/api/v1/analysis/dashboard` | `GET /dashboard/general`, `GET /dashboard/{dimension}`, `GET /dashboard/snapshot`, `GET /dashboard/snapshots`, `GET /dashboard/top-performers`, `GET /dashboard/biggest-movers`, `GET /dashboard/score-trend`, `GET /dashboard/coefficient-history`, `GET /dashboard/hierarchical-trend`, `GET /dashboard/sub-dimension-trend`, `GET /dashboard/aspect-trend`, `GET /dashboard/sub-aspect-trend`, `GET /dashboard/coefficient-history-by-level` | **None** (unit tests exist in `app/tests/` but are excluded) |
| `filter` | `/api/v1/filter` | `POST /advanced`, `GET /fields` | **None** (integration test exists in `app/tests/` but is excluded) |
| `symbols` | `/api/v1/symbols` | `GET /search`, `GET /exchanges`, `GET /market-types`, `GET /countries`, `GET /stats`, `GET /exchanges/{exchange}/count`, `GET /market-types/{market_type}/count`, `GET /{symbol}` | **None** |
| `settings` | `/api/v1/settings` | `GET /market-preferences`, `POST /market-preferences`, `GET /countries`, `GET /recent-searches`, `POST /recent-searches` | **None** (integration test exists in `app/tests/` but is excluded) |
| `ranking` | `/api/v1/ranking` | `GET /nasdaq` | **None** (unit test exists in `app/tests/` but is excluded) |
| `health` | `/api/v1/health` | `GET /`, `GET /services`, `GET /services/{service}`, `GET /ready`, `GET /live` | **Partial** (`test_new_features.py` covers root health) |
| `data_health` | `/data-health` | `GET /data-health` | **Partial** (`test_data_health_enhanced.py` covers response shape) |
| `auth` | `/api/v1/auth` | `POST /register`, `POST /login`, `POST /refresh` | **None** (integration tests exist in `app/tests/` but are excluded) |
| `password_reset` | `/api/v1/auth` | `POST /password-reset/request`, `POST /password-reset/verify`, `POST /password-reset/confirm` | **None** (integration tests exist in `app/tests/` but are excluded) |

---

## 3. Unmounted / Dead Route Files

These route modules exist in the codebase but are **not registered** in `app/main.py`, meaning their endpoints are unreachable:

| File | Router Variable | Status |
|------|----------------|--------|
| `app/api/routes/compare.py` | `compare_router` | Not imported, not mounted |
| `app/api/routes/forecast.py` | `forecast_router` | Not imported, not mounted |
| `app/api/routes/alerts.py` | `alerts_router` | Not imported, not mounted |
| `app/api/routes/tse.py` | `tse_router` | Not imported, not mounted |
| `app/api/routes/nerk.py` | `nerk_router` | Not imported, not mounted |
| `app/api/routes/market_data.py` | `market_data_router` | Imported in `main.py` but **missing `app.include_router()` call** |

---

## 4. Test Files That Exist But Are Incomplete or Have Gaps

### 4.1 `backend/app/tests/` — Completely Excluded From Test Runs

All files in this directory are **invisible** to the current pytest configuration:

| File | Type | What It Covers | Gap |
|------|------|---------------|-----|
| `auth/test_auth_api.py` | Integration (TestClient) | `/auth/register`, `/auth/login`, `/auth/refresh` | Not collected |
| `auth/test_password_reset_api.py` | Integration (TestClient) | `/auth/password-reset/*` | Not collected |
| `auth/test_password_reset_service.py` | Unit | Token creation, verification, consumption | Not collected |
| `filter/test_filter_api.py` | Integration (TestClient) | `/filter/advanced`, `/filter/fields` | Not collected |
| `filter/test_filter_parser.py` | Unit | Parser, query builder, field registry | Not collected |
| `analysis/test_fundamental_ratios.py` | Unit + Isolated Async | Ratio calculations, `analyze()` | Not collected |
| `ranking/test_ranking.py` | Unit | `_assign_grade`, `_technical_score`, `_risk_score` | Not collected |
| `api/test_settings_api.py` | Integration (TestClient) | `/settings/recent-searches` | Not collected |
| `api/test_market_score_trend_service.py` | Unit | `MarketScoreTrendService.get_trend`, `compute_and_persist` | Not collected |
| `api/test_level_trend_dashboard.py` | Unit (handler-level) | Dashboard trend endpoints | Not collected |
| `api/test_score_trend_dashboard.py` | Unit (handler-level) | `/dashboard/score-trend` | Not collected |
| `api/test_generate_market_score_trend_cli.py` | Unit | CLI argument parsing | Not collected |
| `infrastructure/*` | Unit/Integration | Event bus, DB manager, circuit breaker, bulkhead | Not collected |

### 4.2 `backend/tests/` — Collected but Sparse on HTTP Coverage

| File | Type | Gap |
|------|------|-----|
| `test_api_security.py` | Integration | Only covers `AuthGuardMiddleware` and portfolio IDOR; no endpoint body validation or error-path coverage for most routes |
| `test_live_sse_endpoints.py` | Integration | Covers SSE headers, auth, and route registration; no payload/content validation |
| `test_data_health_enhanced.py` | Integration | Only verifies top-level response keys; no deep validation |
| `test_new_features.py` | Mixed | Covers `/health` and export/import, but export/import is synthetic (no real file I/O) |
| `test_snapshot_api.py` | Unit/Contract | Validates snapshot schema shape; no live HTTP test |

---

## 5. Overall Test-to-Endpoint Mapping

### 5.1 Coverage Matrix (Mounted Endpoints Only)

| Endpoint Group | Service Unit Tests | HTTP Integration Tests | Gap Severity |
|---------------|-------------------|------------------------|--------------|
| `/api/v1/auth` (register, login, refresh) | Partial | **YES** (in `app/tests/`, excluded) | High |
| `/api/v1/auth/password-reset/*` | Yes | **YES** (in `app/tests/`, excluded) | High |
| `/api/v1/stocks/*` | Partial | **None** | Critical |
| `/api/v1/market/*` | Partial | **None** | Critical |
| `/api/v1/analysis/*` | Extensive | **None** | Critical |
| `/api/v1/portfolio/*` | Yes | **None** | Critical |
| `/api/v1/history/*` | No | **None** | Critical |
| `/api/v1/news/*` | Yes | **None** | Critical |
| `/api/v1/ml/*` | Yes | **None** | Critical |
| `/api/v1/users/*` | Yes | **None** | High |
| `/api/v1/watchlists/*` | Yes | **None** | Critical |
| `/api/v1/notifications/*` | Yes | **None** | Critical |
| `/api/v1/specialized/*` | Yes | **None** | Critical |
| `/api/v1/system/*` | Yes | **None** | Critical |
| `/api/v1/live (REST)*` | Partial | **None** | High |
| `/api/v1/live (SSE)*` | Partial | **Partial** | Medium |
| `/api/v1/health/*` | Yes | **Partial** | Medium |
| `/data-health` | Yes | **Partial** | Medium |
| `/api/v1/analysis/dashboard/*` | Partial | **None** | Critical |
| `/api/v1/filter/*` | Yes | **YES** (in `app/tests/`, excluded) | High |
| `/api/v1/symbols/*` | No | **None** | Critical |
| `/api/v1/settings/*` | Yes | **YES** (in `app/tests/`, excluded) | High |
| `/api/v1/ranking/*` | Yes | **None** | High |
| `/` (root) | No | **None** | Low |

### 5.2 Unmounted Routes (Zero Coverage by Definition)

| File | Endpoints | Notes |
|------|-----------|-------|
| `compare.py` | `/compare/stocks`, `/compare/dimensions/{s1}/{s2}`, `/compare/metrics/{s1}/{s2}`, `/compare/historical` | Not mounted in `main.py` |
| `forecast.py` | `/forecast/price`, `/forecast/trend`, `/forecast/batch`, `/forecast/models`, `/forecast/models/{id}`, `/forecast/performance/{id}`, `/forecast/backtest` | Not mounted in `main.py` |
| `alerts.py` | `/alerts` (CRUD + history + bulk + types + stats) | Not mounted in `main.py` |
| `tse.py` | `/tse/nerk/*`, `/tse/symbols`, `/tse/market-overview` | Not mounted in `main.py` |
| `nerk.py` | `/nerk/constituents`, `/nerk/overview`, `/nerk/price-history/{symbol}`, `/nerk/market-overview` | Not mounted in `main.py` |
| `market_data.py` | `/market-data/quote/{symbol}`, `/market-data/history/{symbol}`, `/market-data/intraday/{symbol}`, `/market-data/market-status` | Imported but **not included** via `app.include_router()` |

---

## 6. Root Cause & Recommendations

### Root Cause
1. **`pytest.ini` misconfiguration**: `testpaths = tests` silently discards the entire `backend/app/tests/` suite.
2. **Missing `app.include_router()` calls**: `market_data_router` is imported but never mounted; `compare`, `forecast`, `alerts`, `tse`, and `nerk` routers are not imported at all.
3. **Test distribution imbalance**: 732 tests exist, but >95% are service-level unit tests. True HTTP integration tests are rare.

### Immediate Fixes
1. **Fix pytest.ini**: Add `app/tests` to `testpaths` or remove the directive to let pytest discover both directories.
2. **Mount missing routers** or remove dead route files to avoid confusion.
3. **Prioritize HTTP integration tests** for critical paths:
   - Auth flow (register → login → refresh)
   - Stock search & retrieval
   - Analysis endpoints (technical, fundamental, scoring)
   - Portfolio CRUD
   - Live data snapshots & SSE streams
4. **Add negative-path tests** (401, 403, 404, 422, 500) for all mounted endpoints.
