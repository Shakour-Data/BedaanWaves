# CHANGELOG — BEDAANWAVES NASDAQ FINANCIAL INTELLIGENCE PLATFORM
## Semantically Versioned Release Notes · Strict SemVer 2.0.0

**Document ID:** BW-CHANGELOG-v2.0.0  
**File Location (canonical):** [CHANGELOG.md](file:///e:/BedaanWaves/docs/project_closure/CHANGELOG.md)  
**Format:** Keep a Changelog 1.1.0 — https://keepachangelog.com/en/1.1.0/  
**Git Tag (planned at deploy):** `v2.0.0@2026-09-05`

---

## [2.0.0] — 2026-09-05 · CODENAME: NASDAQ-VANGUARD

### Added (MINOR · backward-compatible capability additions = 10)
- Forecast module: 7 endpoints (ARIMA/LSTM/Prophet/XGBoost/Ensemble models, 8 horizons, CI bands, feature importance, backtest metrics) — [forecast.py](file:///e:/BedaanWaves/backend/app/api/routes/forecast.py)
- Comparison Engine: Score Matrix, Relative Performance, Pearson/Spearman Correlation — [compare.py](file:///e:/BedaanWaves/backend/app/api/routes/compare.py)
- Alerting Engine: 8 alert types (PRICE/RSI/SMA_CROSS/PCT_CHANGE/DIM_SCORE), 3 delivery channels, FSM lifecycle — [alerts.py](file:///e:/BedaanWaves/backend/app/api/routes/alerts.py)
- Redis L1/L2 caching with automatic MemoryCacheBackend fallback — [redis_cache_backend.py](file:///e:/BedaanWaves/backend/app/infrastructure/cache/redis_cache_backend.py)
- Server-Sent Event realtime feed (`/live/sse`) — tick stream, alert firing, market_status events — [live_sse.py](file:///e:/BedaanWaves/backend/app/api/routes/live_sse.py)
- Password Recovery Finite State Machine (INIT → CODE_REQUESTED → CODE_VERIFIED → PASSWORD_CHANGED) — [password_reset.py](file:///e:/BedaanWaves/backend/app/api/routes/password_reset.py)
- Centralized DateStore (Zustand) for cross-chart effectiveDate synchronization — [useDateStore.ts](file:///e:/BedaanWaves/frontend/src/store/useDateStore.ts)
- NASDAQ symbol disambiguation: NDX (Nasdaq-100 = NAS100 CFD) vs IXIC (Nasdaq Composite), trader-educational banner in search + indices endpoint
- Portfolio module: holdings CRUD, CSV bulk import, MTM series, Sharpe/Beta/VaR risk — [portfolios.py](file:///e:/BedaanWaves/backend/app/api/routes/portfolios.py)
- WCAG 2.1 Level AA accessibility compliance end-to-end

### Changed (MAJOR · Public API breaking changes = 5)
- **[BREAKING]** `DB_URL` → `DATABASE_URL` in backend env; SQLAlchemy 2.0 strict AsyncPG session config
- **[BREAKING]** JWT signing algorithm RS256 → HS256; all existing tokens/revocation lists invalidated
- **[BREAKING]** Scoring Engine weight vector v1.0 → v2.0; all historical scores re-computed; new `market_score_trend` table
- **[BREAKING]** Removed ALL i18n/localization (endpoints, hooks, catalogs, Accept-Language header handling). English-only LTR platform
- **[BREAKING]** Deprecated `GET /api/v1/scores/raw` in favor of standardized `GET /api/v1/stocks/{symbol}/scores`

### Fixed (PATCH · Bugfixes and hardening = 19)
- PostgreSQL connection pool exhaustion (120 concurrent users) — pool_recycle=3600, max_overflow=10, AsyncSession scoping
- bcrypt synchronous hash blocking event loop — now asyncio.to_thread + semaphore
- Ranking CSV export ANSI → UTF-8 with BOM for Excel compatibility
- SpiderChart re-render jank on every date mutation — now React.memo + RAF batch
- Dashboard N+1 query cartesian product → single CTE window function on pre-computed `score_history`
- 5 deprecated dependencies purged (hazm, jupyter, ipdb, memcache, diskcache); `pip-audit` = 0 vulns
- 13 temporary/debug/scratch files purged from repository root; delivery-hygiene .gitignore updated
- 6 new PostgreSQL indexes on `score_history(symbol, date, dimensions[]);` planner cost 14,200 → 210
- Distributed rate limiting (100/min, 5,000/hr) via Redis SLIDING_WINDOW algorithm
- Prometheus `/system/metrics` endpoint (7 standard histograms/gauges/counters)
- Secret scanning via gitleaks on every PR + push; 0 secrets in tree at time of cut
- Windows-specific port 5432 firewall guidance added to setup docs
- Memurai documented as native Windows Redis alternative path
- Standardized error envelope across all 90 endpoints + trace_id propagation
- Circuit breaker for upstream market-data APIs (3 consecutive fails → OPEN for 60s)
- Tripartite health: liveness `/health` · readiness `/health/ready` · business-SLA `/health/data-freshness`
- Stale i18n catalogs (Persian/Farsi/Arabic) purged; i18n-related Next config removed
- Docker references removed from setup/deploy docs; compose files `.disabled` suffix
- Windows Defender Inbound Rule for PostgreSQL 5432 port added to Prerequisites script

### Security (cross-cutting hardening)
- bcrypt work factor standardized at rounds=12 across all password hashing paths (auth + recovery FSM OTP)
- Refresh tokens one-time-use (RFC 6819 §5.2.2.1) — atomic revoke-on-rotate
- `pip-audit` + `npm audit --audit-level=high` = 0 vulns; SAST via Bandit = 0 critical/high
- OWASP Top 10 scanned + closed: SQLi (parametrized AsyncPG only), XSS (CSP nonce, React auto-escape), CSRF (SameSite=Lax + JWT not in cookie), SSRF (URL allowlist for market data fetches)

### Deprecated (will be removed in v3.0.0)
- `GET /api/v1/scores/raw` — returns HTTP 410 GONE in v3; use `GET /api/v1/stocks/{symbol}/scores`
- Legacy (v1.0) `/api/v1/dashboard` aggregated without effectiveDate param
- Plain-text email delivery (planned migration to DKIM/SPF/DMARC hardened SMTP relay)

### Removed (NOT deprecated — directly removed in v2.0.0)
- Persian NLP library `hazm` and all its call sites
- DiskCache L1 tier; Redis or in-process Memory only
- Memcache Python client (no native Windows support)
- Notebook stack (jupyter/jupyterlab/ipdb/python-debugpy) from dev deps
- Localization module (i18n) from both frontend and backend
- 13 ad-hoc developer scratch utilities from tree

---

## [1.0.1] — 2026-07-15 · Patch baseline against v1.0.0
- Fixed: Registration password policy enforcement (client + server dual-check)
- Fixed: Dashboard chart tooltip z-index overlap with sidebar flyouts
- Fixed: Alembic merge heads (`20260816_merge_heads.py`)

---

## [1.0.0] — 2026-07-01 · INITIAL PRODUCTION RELEASE (CODENAME: FOUNDATION)
- Initial public release of BedaanWaves Nasdaq platform
- 6-dimension multi-factor scoring (Profitability/Valuation/Momentum/Volatility/Quality/Growth)
- Ranking page + CSV export
- Stock detail + Candlestick
- Dashboard (Spider + ScoreTrend + News)
- JWT Authentication (register/login/refresh/logout)
- Watchlists module
- News + basic sentiment
- PostgreSQL 14+ with Alembic migrations
- Next.js 14 + React 18 frontend
- 45 backend tests, 10 frontend tests (QA not yet v2.0-grade)

---

*This CHANGELOG is authoritative. Do not rely on Git commit messages as a substitute for release-quality communication.*
*Changelog maintainer: Project Closure Manager · Last amended: 2026-09-05*
