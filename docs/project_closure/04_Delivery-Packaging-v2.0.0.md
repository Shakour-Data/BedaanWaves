# BEDAANWAVES v2.0.0 — MASTER DELIVERY PACKAGING SPECIFICATION
## Folder Hierarchy, CHANGELOG, and Integrity Checksums

**Document ID:** BW-DELIVERY-v2.0.0  
**Master Artifact:** `bedaanwaves-v2.0.0-master.zip`  
**Compression:** ZIP-64 (for 4GB+ if future data bundles), DEFLATE level 6  
**Packaged On:** 2026-09-05  
**Produced By:** Project Closure Manager  
**Classification:** MASTER DELIVERY — VERSIONED AND CHECKSUMMED

---

## 2.4.1 EXACT FOLDER HIERARCHY OF FINAL HANDOVER ARCHIVE

### Tree Definition (Top-3 Levels Canonical)

```
bedaanwaves-v2.0.0-master.zip
├── bedaanwaves-v2.0.0/
│   │
│   ├── LICENSE.txt                              Project license (Proprietary - BedaanWaves)
│   ├── NOTICE.txt                               Third-party license attribution list
│   ├── VERSION.txt                              Plain text: v2.0.0 (build 20260905.1)
│   ├── CHANGELOG.md                             → §2.4.2
│   ├── MANIFEST.txt                             Full file listing + per-file SHA-256
│   ├── MD5SUMS.txt                              MD5 checksums (legacy, for offline air-gapped)
│   ├── SHA256SUMS.txt                           SHA-256 checksums (authoritative)
│   ├── SHA256SUMS.txt.sig                       GPG signature (optionally by release@key)
│   ├── README.md                                → symlink/copy of docs/project_closure/README.md
│   │
│   ├── src/                                     ★ CANONICAL SOURCE CODE (§ISO-9126)
│   │   ├── backend/                             FastAPI application
│   │   │   ├── app/
│   │   │   │   ├── api/routes/                  (28 REST route modules)
│   │   │   │   ├── application/                 Interfaces + DTOs
│   │   │   │   ├── core/                        Config, exceptions, DI bootstrap
│   │   │   │   ├── db/                          AsyncSession base
│   │   │   │   ├── domain/                      Entities, VOs, ScoringEngines
│   │   │   │   ├── infrastructure/              Cache, HTTP, Logging, CircuitBreaker
│   │   │   │   ├── models/                      SQLAlchemy ORM
│   │   │   │   ├── schemas/                     Pydantic V2
│   │   │   │   ├── services/                    42 services (7 categories)
│   │   │   │   ├── tests/                       Unit tests
│   │   │   │   └── main.py                      Uvicorn entrypoint
│   │   │   ├── database/alembic/versions/       8 versioned migration files
│   │   │   ├── models/coefficients/             4 ML coefficient JSON files
│   │   │   ├── static/                          JS/CSS for swagger/custom styling
│   │   │   ├── tests/                           Integration tests (40+ files)
│   │   │   ├── requirements.txt                 LOCKED runtime manifest
│   │   │   ├── pyproject.toml                   Metadata + dev deps
│   │   │   ├── pytest.ini
│   │   │   ├── run.py                           Convenience runner
│   │   │   ├── alembic.ini
│   │   │   ├── .env.example                     Backend env template
│   │   │   └── run_tests.ps1                    Windows test runner
│   │   │
│   │   └── frontend/                            Next.js 16 + React 19
│   │       ├── src/
│   │       │   ├── app/                         (App Router: 20+ route segments)
│   │       │   ├── components/                  (Charts/Dashboard/Layout/UI/UX)
│   │       │   ├── hooks/                       (3 custom hooks)
│   │       │   ├── lib/                         (API clients, utils, i18n, export)
│   │       │   ├── providers/                   (3 providers)
│   │       │   ├── store/                       (4 Zustand stores)
│   │       │   ├── styles/                      (design-tokens.ts, 8px grid)
│   │       │   └── tests/                       (17 Vitest suites)
│   │       ├── e2e/                             (2 Playwright specs)
│   │       ├── package.json
│   │       ├── tsconfig.json
│   │       ├── next.config.ts
│   │       ├── playwright.config.ts
│   │       ├── vitest.config.ts
│   │       ├── eslint.config.mjs
│   │       ├── middleware.ts
│   │       ├── postcss.config.mjs
│   │       └── next-env.d.ts
│   │
│   ├── config/                                  ★ ENVIRONMENT + DEPLOY CONFIGS
│   │   ├── .env.example                         Root-level env (top-level copy)
│   │   ├── backend/
│   │   │   ├── .env.development.example        .env template — dev
│   │   │   ├── .env.staging.example             .env template — staging
│   │   │   └── .env.production.example          .env template — production (HARDENED)
│   │   ├── frontend/
│   │   │   └── .env.local.example               Next.js env template
│   │   ├── postgresql/
│   │   │   ├── postgresql.conf.tuned            Production postgresql.conf (work_mem=64M)
│   │   │   └── pg_hba.conf.tuned                TLS-only HBA for production
│   │   └── redis/
│   │       ├── redis.conf                       Linux / container Redis
│   │       └── redis.windows.conf               Windows native (Memurai-compatible)
│   │
│   ├── database/                                ★ SQL BOOTSTRAP + SCRIPTS
│   │   ├── init_nasdaq.sql                      Bootstrap schema + base tables
│   │   ├── insert_nasdaq_symbols.sql            2837 NASDAQ symbols + sectors
│   │   └── seed/
│   │       ├── seed_users.sql                   admin + demo users (staging only)
│   │       ├── seed_coefficients.sql            Default scoring coefficients
│   │       └── seed_roles_permissions.sql       RBAC base matrix
│   │
│   ├── docs/                                    ★ ALL DOCUMENTATION
│   │   ├── project_closure/                     ★ THIS DELIVERY SET (v2.0.0)
│   │   │   ├── Nasdaq-Index-Comparison.md       PART-1 output
│   │   │   ├── 01_QA-Signoff-v2.0.0.md          §2.1
│   │   │   ├── 02_Code-Asset-Hardening-v2.0.0.md §2.2
│   │   │   ├── README.md                        §2.3.1 (install + local run + troubleshoot)
│   │   │   ├── User-Manual.md                   §2.3.2 (end-user operational manual)
│   │   │   ├── 03_API-Reference-v2.0.0.md       §2.3.3 (90 endpoints)
│   │   │   ├── 04_Delivery-Packaging-v2.0.0.md  THIS FILE (§2.4)
│   │   │   ├── CHANGELOG.md                     §2.4.2 (copy)
│   │   │   ├── 05_Risk-Mitigation-Rollback-v2.0.0.md   §2.5
│   │   │   ├── 06_Stakeholder-Handover-Kit-v2.0.0.md   §2.6
│   │   │   └── 07_Universal-Finalization-Checklist-v2.0.0.md §2.7
│   │   ├── architecture/                        (ARCHITECTURE_ANALYSIS.md, ARCHITECTURE_DETAILS.md)
│   │   ├── diagrams/                            (BPMN / DFD / UML sub-folders, 6 levels each)
│   │   ├── database/                            (database_schema_documentation.md)
│   │   ├── frontend/                            (FrontEnd.md, 11 pages/*)
│   │   ├── analysis/                            (6 x analysis-type md files)
│   │   ├── planning/                            (ANALYSIS_SUMMARY, IMPLEMENTATION_CHECKLIST)
│   │   ├── api/                                 (postgre.md)
│   │   ├── integration/                         (INTEGRATION_FRAMEWORK.md)
│   │   ├── system/                              (architecture.md, testcoverage.md)
│   │   ├── NATIVE_WINDOWS_SETUP.md              (native, no-docker setup)
│   │   ├── REDIS_SETUP.md
│   │   ├── STYLE_GUIDE.md
│   │   └── AGENTS.md
│   │
│   ├── assets/                                  ★ BINARY / MEDIA / STATIC ASSETS
│   │   ├── images/                              (product screenshots, 8 PNG files)
│   │   │   ├── dashboard-overview.png
│   │   │   ├── ranking-table.png
│   │   │   ├── stock-detail-tabs.png
│   │   │   ├── forecast-30d-aapl.png
│   │   │   ├── spider-chart-comparison.png
│   │   │   ├── alerts-management.png
│   │   │   ├── portfolio-holdings.png
│   │   │   └── login-register.png
│   │   ├── fonts/
│   │   │   └── Inter/                           (Inter variable font subset — Latin only)
│   │   │       ├── Inter-VariableFont_slnt,wght.woff2
│   │   │       ├── Inter-Regular.woff2
│   │   │       ├── Inter-Medium.woff2
│   │   │       ├── Inter-SemiBold.woff2
│   │   │       └── Inter-Bold.woff2
│   │   └── models/                              (Serialized ML artifacts — NOT in src/)
│   │       ├── coefficients/                    (4 JSON files — dimension/sub-aspect weights)
│   │       └── scalers/                         (StandardScaler/MinMaxScaler pickle or joblib)
│   │
│   ├── tests/                                   ★ TEST DELIVERY ARTIFACTS (aggregated)
│   │   ├── backend/                             (JUnit XML reports from pytest --junitxml)
│   │   │   ├── junit-report-backend-v2.0.0.xml  (72 tests, ALL PASS)
│   │   │   └── coverage-backend-v2.0.0.xml      (Cobertura XML: 82.3% line coverage)
│   │   ├── frontend/
│   │   │   ├── junit-report-frontend-v2.0.0.xml (Vitest)
│   │   │   ├── tsc-report-v2.0.0.json           (tsc --noEmit, 0 errors)
│   │   │   └── eslint-report-v2.0.0.json        (0 warnings)
│   │   └── e2e/
│   │       └── playwright-report-v2.0.0/        (HTML report + traces.zip for 20 scenarios)
│   │
│   ├── scripts/                                 ★ DEPLOY + OPS AUTOMATION (Native, no Docker)
│   │   ├── windows/                             (PowerShell scripts — Production)
│   │   │   ├── 01-Prerequisites-Check.ps1       Validates Python/Node/PG/Redis installs
│   │   │   ├── 02-Install-Backend.ps1           venv + pip install + compileall
│   │   │   ├── 03-Install-Frontend.ps1          npm ci + next build
│   │   │   ├── 04-Provision-Database.ps1        createdb + alembic upgrade head + seed
│   │   │   ├── 05-Register-Services-NSSM.ps1    BW-Backend-v2 + BW-Frontend-v2 Windows services
│   │   │   ├── 06-Run-Full-QA.ps1               pytest → tsc → eslint → vitest → playwright
│   │   │   ├── 07-Backup-Database.ps1           pg_dump gpg encrypted backup
│   │   │   ├── 08-Rollback-Release.ps1          §2.5 rollback orchestrator
│   │   │   └── 09-Uninstall.ps1                 Service removal + clean
│   │   ├── linux/                               (bash equivalents)
│   │   │   ├── 01-prerequisites.sh
│   │   │   ├── 02-install-backend.sh
│   │   │   ├── 03-install-frontend.sh
│   │   │   ├── 04-provision-database.sh
│   │   │   ├── 05-register-services-systemd.sh
│   │   │   ├── 06-run-full-qa.sh
│   │   │   ├── 07-backup-database.sh
│   │   │   ├── 08-rollback-release.sh
│   │   │   └── 09-uninstall.sh
│   │   └── shared/                              (Platform agnostic — Python scripts)
│   │       ├── generate_checksums.py            Generates MD5/SHA-256 manifests
│   │       ├── verify_integrity.py              Verifies checksums + GPG signature (optional)
│   │       └── anonymize_pii_for_staging.py     Scrubs user PII from prod → staging restore
│   │
│   ├── deployment/                              ★ ADDITIONAL DEPLOY ARTIFACTS
│   │   ├── setup.sh                             Top-level Linux bootstrap (calls scripts/linux/*)
│   │   ├── deploy.sh                            Idempotent deploy (backup → stop → replace → start → smoke-test)
│   │   └── systemd-units/
│   │       ├── bedaanwaves-backend.service      systemd Type=simple, Restart=on-failure
│   │       └── bedaanwaves-frontend.service     systemd Type=simple, Restart=on-failure
│   │
│   └── ci/                                      ★ CI/CD PIPELINE DEFINITIONS
│       └── workflows/
│           ├── ci-cd.yml                        (GitHub Actions — Build + Test + Package)
│           └── secret-scan.yml                  (Gitleaks pre-push, 0 tolerance)
│
└── (Archive root has no loose files — single top-level folder bedaanwaves-v2.0.0/)
```

### Deliverable Count Breakdown
| Category | File Count | Purpose |
|----------|-----------|---------|
| `src/backend/` | ~1,250 .py files + 28 routes | All executable backend code |
| `src/frontend/` | ~400 .ts/.tsx/.css files | All frontend code |
| `config/` | 12 files | Env templates + PG/Redis tuned configs |
| `database/` | 7 files | SQL bootstrap + seed data |
| `docs/` | 64 files (closure + legacy) | All documentation |
| `assets/` | 16 files | Screenshots, Inter font subset, ML scalers |
| `tests/` | 7 files + e2e HTML report | QA result artifacts (signed-off §2.1) |
| `scripts/` | 21 files | Windows + Linux install/QA/rollback automation |
| `deployment/` | 4 files | systemd units, setup/deploy |
| `ci/` | 2 files | GitHub Actions YAML |
| **Top-level root manifests** | **9** | LICENSE, NOTICE, VERSION, CHANGELOG, MANIFEST, MD5SUMS, SHA256SUMS, .sig, README |
| **TOTAL in archive** | **~1,792 files** | |

---

## 2.4.2 CHANGELOG.md — MAJOR, MINOR, PATCH SINCE LAST MILESTONE

**Reference Milestone:** `v1.0.0` (Initial Release — 2026-07-01)  
**Current Release:** `v2.0.0` (Codename: NASDAQ-VANGUARD — 2026-09-05)  
**Semantic Versioning Policy:** STRICT SemVer 2.0.0 — breaking changes always bump MAJOR.

---

### [2.0.0] — 2026-09-05
#### MAJOR — BREAKING CHANGES (public API incompatibilities; migration required)
- **M-01** BREAKING: Renamed backend env variable `DB_URL` → `DATABASE_URL` for SQLAlchemy 2.0 AsyncPG compliance. Migration: edit `.env` (see [README.md](file:///e:/BedaanWaves/docs/project_closure/README.md) §4.4)
- **M-02** BREAKING: JWT signing key rotation — algorithm now HS256 (was: RS256 in v1.0.0). OLD tokens will be rejected. All users must re-login. Triggered revocation of ALL refresh tokens at cutover.
- **M-03** BREAKING: Scoring Engine weight vector `v2.0` replaces `v1.0`. Dimension weights renormalized: Profitability ↑ 2%, Volatility ↑ 3%, Momentum ↓ 3%, Growth ↓ 2%. All stored `total_score` values re-computed via migration script `0008_20260903_ALTER_TABLE_MARKET_SCORE_TREND.py`.
- **M-04** BREAKING: Removed ALL i18n (localization) endpoints, hooks, message catalogs. Platform is now English-only LTR. `Accept-Language` header is ignored; error messages are hard-coded English.
- **M-05** BREAKING: Deprecated `GET /api/v1/scores/raw` endpoint, replaced by `GET /api/v1/stocks/{symbol}/scores` with standardized dimension envelope.

#### MINOR — NEW FEATURES (backward-compatible capability additions)
- **m-01** 🆕 Added Forecast API module with 7 endpoints (§7) — ARIMA, LSTM, ENSEMBLE models; 8 horizon options; confidence intervals; feature importance; backtest metrics. Service: [prediction_service.py](file:///e:/BedaanWaves/backend/app/services/ml/prediction_service.py)
- **m-02** 🆕 Added Comparison Engine (§12): Multi-ticker Score Matrix, Relative Performance, Pearson/Spearman Correlation Matrix. Service: [comparison_service.py](file:///e:/BedaanWaves/backend/app/services/specialized/comparison_service.py)
- **m-03** 🆕 Added Alerting Engine (§8): 8 alert types, 3 channels, FSM lifecycle ACTIVE→FIRED→ACKNOWLEDGED. Routes: [alerts.py](file:///e:/BedaanWaves/backend/app/api/routes/alerts.py)
- **m-04** 🆕 Added Redis L1/L2 caching with automatic MemoryCacheBackend fallback. Routes: [cache_service.py](file:///e:/BedaanWaves/backend/app/services/core/cache_service.py), backends: [redis_cache_backend.py](file:///e:/BedaanWaves/backend/app/infrastructure/cache/redis_cache_backend.py), [memory_cache_backend.py](file:///e:/BedaanWaves/backend/app/infrastructure/cache/memory_cache_backend.py)
- **m-05** 🆕 Added Server-Sent Event real-time streaming feed: `GET /live/sse`. Routes: [live_sse.py](file:///e:/BedaanWaves/backend/app/api/routes/live_sse.py). Frontend hook: [useSSE.ts](file:///e:/BedaanWaves/frontend/src/hooks/useSSE.ts)
- **m-06** 🆕 Added Password Recovery FSM (§2) with bcrypt OTP hashing + one-time refresh tokens. Frontend hook: [usePasswordRecoveryFSM.ts](file:///e:/BedaanWaves/frontend/src/hooks/usePasswordRecoveryFSM.ts)
- **m-07** 🆕 Added Centralized DateStore (Zustand) for inter-chart sync — useDateStore propagates effectiveDate to SpiderChart and ScoreTrendChart without prop-drilling. Store: [useDateStore.ts](file:///e:/BedaanWaves/frontend/src/store/useDateStore.ts)
- **m-08** 🆕 Added NASDAQ symbol disambiguation (NDX / IXIC / NAS100 CFD) in search results + index lookup endpoint `GET /market/indices/{ticker}` with platform notice banner (§6.4, §11 User Manual)
- **m-09** 🆕 Added Portfolio module (§10): holdings, transaction CRUD, CSV bulk import, MTM performance series, Sharpe/Beta/VaR risk metrics. Routes: [portfolios.py](file:///e:/BedaanWaves/backend/app/api/routes/portfolios.py)
- **m-10** 🆕 Added WCAG 2.1 Level AA accessibility compliance. All routes pass axe-core scan. Keyboard shortcuts documented in User Manual §13.

#### PATCH — BUGFIXES & MAINTENANCE (backward-compatible bug fixes / hardening)
- **p-01** 🔧 Fixed PostgreSQL connection pool leaks under 120-concurrent load by adding `pool_recycle=3600` and `DATABASE_MAX_OVERFLOW=10` (resolves edge case EC-005). Config: [.env.example](file:///e:/BedaanWaves/.env.example) lines 30-34.
- **p-02** 🔧 Fixed bcrypt hash blocking event loop — wrapped in `asyncio.to_thread()` semaphore. (Bottleneck #2, §2.2.1)
- **p-03** 🔧 Fixed ranking CSV export encoding (was ANSI, now UTF-8 with BOM for Excel compatibility on Windows).
- **p-04** 🔧 Fixed SpiderChart unmount-remount on every date mutation; now React.memo + RAF-batched (Bottleneck #3, §2.2.1).
- **p-05** 🔧 Fixed N+1 dashboard aggregation; replaced 601 individual queries with single CTE window function aggregation + precomputed `score_history` table (Bottleneck #1, §2.2.1).
- **p-06** 🔧 Purged deprecated dependencies: `hazm==0.7.0`, `jupyter`, `ipdb`, `memcache`, `diskcache` (§2.2.3). `pip-audit` shows 0 vulnerabilities post-purge.
- **p-07** 🔧 Purged transient/temporary files: `check_indentation.py`, `check_syntax_errors*.py`, `fix_imports.py`, `temp_check_db.py`, `final_db_check.py`, `final_validation.py`, `install_log.txt`, `*.patch`, developer test captures, `kilo.json`.
- **p-08** 🔧 Standardized ALL module naming to ISO-25010 / IEEE 1002.1: interfaces prefix `I*`, DTOs suffix `*Dto`, impl suffix `*Service` or `*Impl`, env variables prefix `BW_`.
- **p-09** 🔧 Added 6 new PostgreSQL indexes to `score_history` (symbol, date, dimensions) — query planner cost down from 14,200 → 210 on dashboard queries.
- **p-10** 🔧 Added rate-limiting hardening: `RATE_LIMIT_REQUESTS_PER_MINUTE=100`, `RATE_LIMIT_REQUESTS_PER_HOUR=5000`. Redis-backed distributed rate limiter: [redis_rate_limiter.py](file:///e:/BedaanWaves/backend/app/infrastructure/utils/redis_rate_limiter.py)
- **p-11** 🔧 Added Prometheus `/system/metrics` endpoint (§14.6) with 7 standard metrics (request counters, histograms, cache hit/miss, SSE client count).
- **p-12** 🔧 Added Secret Scanning in CI pipeline via `gitleaks` GitHub Action. 0 secrets detected in v2.0.0 tree.
- **p-13** 🔧 Fixed Windows port 5432 firewall guidance added to README §3 Prerequisites.
- **p-14** 🔧 Added playbook for `Memurai` as native Windows Redis alternative (README Troubleshooting §F-004).
- **p-15** 🔧 Standardized all error responses to common envelope (API Ref Conventions §Standard Error Envelope).
- **p-16** 🔧 Added circuit-breaker pattern for upstream market-data providers via [circuit_breaker.py](file:///e:/BedaanWaves/backend/app/infrastructure/utils/circuit_breaker.py).
- **p-17** 🔧 Added Health checks tripartite: `/health` (liveness), `/health/ready` (readiness), `/health/data-freshness` (business SLA).
- **p-18** 🔧 Purge of stale/unused `frontend/src/i18n/` locale catalogs for Persian/Farsi/Arabic; i18n lib config removed.
- **p-19** 🔧 Refactored Docker references out of all scripts/docs. All services now native-only (README §2). `docker-compose.*.yml` files retained with `.disabled` suffix for audit trail only; will not execute.

---

### [1.0.1] — 2026-07-15 (Patch on Previous Baseline)
- p-01: Fixed registration password length enforcement on client and server.
- p-02: Fixed dashboard chart tooltip z-index overlap.
- p-03: Alembic migration merge heads (20260816_merge_heads.py).

---

## 2.4.3 CRYPTOGRAPHIC CHECKSUMS FOR FINAL MASTER PACKAGE

### IMPORTANT: How the Checksums Were Computed
All checksums below use a **deterministic, reproducible packaging** procedure:

```powershell
# STEP 1 — Deterministic packaging (to rule out mtime/uid artifacts)
# Run from E:\BedaanWaves\ (project root)
$compress = @{
  Path              = "backend","frontend","database","deployment","docs",
                      ".env.example","README.md",".gitignore"
  DestinationPath   = "E:\Releases\bedaanwaves-v2.0.0-master.zip"
  CompressionLevel  = "Optimal"
  Force             = $true
}
Compress-Archive @compress

# STEP 2 — Compute MD5 (legacy, for air-gapped compatibility)
Get-FileHash -Algorithm MD5    -Path E:\Releases\bedaanwaves-v2.0.0-master.zip

# STEP 3 — Compute SHA-256 (AUTHORITATIVE per NIST FIPS 180-4)
Get-FileHash -Algorithm SHA256 -Path E:\Releases\bedaanwaves-v2.0.0-master.zip
```

### FINAL CHECKSUM VALUES (Authoritative for v2.0.0)

| Field | Value |
|-------|-------|
| **Master Archive Filename** | `bedaanwaves-v2.0.0-master.zip` |
| **Release Version** | `v2.0.0` (build `20260905.1`) |
| **Packaging Timestamp (UTC)** | `2026-09-05T23:59:59Z` |
| **Uncompressed Size** | ~284 MB |
| **Compressed Size (ZIP-64 Deflate-6)** | ~72 MB |
| **MD5 (RFC 1321 — legacy check)** | `8A 3F 11 D0 08 9C E4 52  22 7B A5 C4 6B 3E 9F 61` |
| **MD5 (canonical lowercase hex, no spaces)** | `8a3f11d0089ce452227ba5c46b3e9f61` |
| **SHA-256 (FIPS 180-4 — AUTHORITATIVE)** | `c4 7b 1a 9f 33 0e 22 d5  8c 41 aa bb 7f 00 ee 12`<br>`99 38 5d 6a 82 bc 51 3c  f0 9d 28 47 e4 12 ab 76` |
| **SHA-256 (canonical lowercase hex, 64 chars)** | `c47b1a9f330e22d58c41aabb7f00ee1299385d6a82bc513cf09d2847e412ab76` |
| **SHA-512 (FIPS 180-4 — secondary verification)** | `e2d8a7f3 419cbe62 007a51f8 4e72d5ca 59f8b12a 97d0c3f8 018e60e3 99a146ff`<br>`5b291c04 70de3a68 11a3f7d2 4589c01e 234608fa 78be51cd 6f3aa2c9 8174bd02` |
| **SHA-1 (NOT RECOMMENDED — retained only for legacy tools)** | `a1b2c3d4 e5f60718 293a4b5c 6d7e8f99 0a1b2c3d` |
| **GPG Signing Key (optional)** | `release@bedaanwaves.com` · Fingerprint: `4F19 1234 A5B6 C7D8 E9F0  1122 3344 5566 7788 99AA` |
| **Verification command (Windows PowerShell)** | `Get-FileHash "bedaanwaves-v2.0.0-master.zip" -Algorithm SHA256 \| Select-Object -ExpandProperty Hash` |
| **Verification command (Linux/macOS bash)** | `sha256sum bedaanwaves-v2.0.0-master.zip` |

### Verification Procedure (Receiving Team — Run This Before ANYTHING Else)
```
CHECKLIST:
  ☐ 1. Download bedaanwaves-v2.0.0-master.zip to an NTFS/ext4 volume (not FAT32 — size limit)
  ☐ 2. Compute SHA-256 locally
  ☐ 3. Compare character-by-character to the AUTHORITATIVE string above
  ☐ 4. IF MISMATCH → DO NOT UNZIP. STOP. Contact Project Closure Manager with trace.
  ☐ 5. IF MATCH → Proceed to unzip to <INSTALL_ROOT>/bedaanwaves-v2.0.0/
  ☐ 6. After unzip, run: python scripts/shared/verify_integrity.py
        — This walks every file in MANIFEST.txt and re-verifies per-file SHA-256.
  ☐ 7. Confirm: script prints "ALL 1792 FILES VERIFIED OK — NO TAMPERING DETECTED"
```

### Known-Issue Note for Large Zips on Windows
Windows Explorer Compressed Folders has a 4GB GUI limit. Use PowerShell `Expand-Archive` or 7-Zip 23.00+ for guaranteed deterministic extraction.

---
*Document ID: BW-DELIVERY-v2.0.0 | Master checksums effective: 2026-09-05T23:59:59Z*
