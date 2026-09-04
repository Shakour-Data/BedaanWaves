# BEDAANWAVES v2.0.0 — COMPREHENSIVE README
## Nasdaq Financial Intelligence & Multi-Factor Stock Ranking Platform

**Version:** v2.0.0 | **Codename:** NASDAQ-VANGUARD | **Release Date:** 2026-09-05  
**Lifecycle Status:** ✅ PRODUCTION-READY (Pre-Deployment Qualified)  
**License:** PROPRIETARY — Internal Use Only  
**Document ID:** BW-README-v2.0.0

---

## TABLE OF CONTENTS

1. [Platform Overview](#1-platform-overview)
2. [Technology Stack](#2-technology-stack)
3. [Prerequisites — Native (No Docker)](#3-prerequisites--native-no-docker)
4. [Installation — Step-by-Step](#4-installation--step-by-step)
5. [Local Execution (Development Mode)](#5-local-execution-development-mode)
6. [Build for Production](#6-build-for-production)
7. [Native Services Management (Windows)](#7-native-services-management-windows)
8. [Troubleshooting — All Known Failure Modes](#8-troubleshooting--all-known-failure-modes)
9. [Testing — Full QA Suite Execution](#9-testing--full-qa-suite-execution)
10. [Project Structure (Canonical)](#10-project-structure-canonical)
11. [Support & Escalation](#11-support--escalation)

---

## 1. PLATFORM OVERVIEW

BedaanWaves v2.0.0 is an enterprise-grade, NASDAQ-exclusive financial intelligence platform that delivers multi-factor stock ranking, AI-driven price forecasting, real-time market data streaming, spider-chart dimensional analysis, price-alert management, and institutional-grade portfolio risk analytics.

**Core Capabilities:**
- Multi-Factor Scoring Engine (Profitability, Valuation, Momentum, Volatility, Quality, Growth) — 6 dimensions, 42 sub-aspects
- ARIMA + LSTM Time-Series Forecasting with 30-day forward prediction
- Real-Time Server-Sent Event (SSE) Market Feed (Redis pub/sub)
- Nasdaq Composite vs Nasdaq-100 Symbol Disambiguation (§PART-1 reference)
- Spider-Chart Dimensional Visualization with Centralized DateStore Sync
- WCAG 2.1 Level AA Compliant UI / English-only LTR interface
- JWT HS256 Authentication + FSM-driven Password Recovery
- Redis L1/L2 Caching with Automatic Memory Fallback

---

## 2. TECHNOLOGY STACK (NATIVE, ZERO DOCKER)

| Tier | Technology | Version | Installation Method |
|------|-----------|---------|---------------------|
| Web Server (API) | Uvicorn (ASGI, standard workers) | 0.24.0 | pip (Python) |
| Web Server (Frontend) | Next.js Production Standalone | 16.2.9 | npm (Node) |
| Database | PostgreSQL | 14+ (16.x recommended) | Native installer (postgresql.org) |
| In-Memory Cache | Redis | 7.2+ (7.4 recommended) | Native Windows: Memurai or WSL2 |
| Runtime (Backend) | Python | 3.11.x | python.org installer |
| Runtime (Frontend) | Node.js | 18.x+ (20.x LTS recommended) | nodejs.org installer |
| Package Manager (BE) | pip + requirements.txt | latest | Bundled |
| Package Manager (FE) | npm | latest | Bundled with Node |
| ORM | SQLAlchemy Async + AsyncPG | 2.0.23 / 0.29.0 | pip |
| Migrations | Alembic | 1.13.0 | pip |
| ML Engine | scikit-learn 1.3.2 + XGBoost 2.0.2 + statsmodels 0.14.0 | — | pip |
| UI Framework | React 19 + Next.js 16 (App Router) | 19.2.7 / 16.2.9 | npm |
| State Management | Zustand (DateStore central) | 5.0.6 | npm |
| Charts | TradingView Lightweight Charts 5.2.0 + Recharts-compatible custom SVG | 5.2.0 | npm |
| Styling | Tailwind CSS 4.0.0 (zero-config) + Inter font | 4.0.0 | npm |

---

## 3. PREREQUISITES — NATIVE (NO DOCKER)

Execute these steps BEFORE attempting installation. Check each box as complete.

```
☐ Install Python 3.11.x (NOT 3.12+ — some C-extension wheels for scipy/xgboost unavailable)
    • Verify: python --version  → Python 3.11.x
    • Install from: https://www.python.org/downloads/release/python-3119/
    • CHECK "Add Python to PATH" during installation.

☐ Install Node.js 20.x LTS
    • Verify: node --version  → v20.x.x  |  npm --version  → 10.x.x
    • Install from: https://nodejs.org/en/download/  (Windows x64 .msi)

☐ Install PostgreSQL 16.x
    • Download: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
    • During install: set password for postgres superuser, port = 5432, install Stack Builder if needed.
    • Verify Windows Service: services.msc → "postgresql-x64-16" → Status = Running
    • Verify: psql -U postgres -c "SELECT version();"

☐ Install Redis (or Memurai for native Windows)
    • OPTION A (Native Windows): Download Memurai Developer: https://www.memurai.com/get-memurai
    • OPTION B (WSL2): wsl --install Ubuntu → sudo apt install redis-server
    • Verify: redis-cli ping  →  PONG
    • Service: services.msc → "Memurai" or WSL redis-server running

☐ Verify port availability:
    • Port 5432 (PostgreSQL): netstat -ano | findstr :5432 → LISTENING
    • Port 6379 (Redis):      netstat -ano | findstr :6379 → LISTENING
    • Port 3000 (API):        netstat -ano | findstr :3000 → free
    • Port 3005 (Frontend):   netstat -ano | findstr :3005 → free

☐ Inbound Rule for PostgreSQL (Windows Defender Firewall):
    Control Panel → Windows Defender Firewall → Advanced Settings → Inbound Rules → New Rule
    → Port → TCP → Specific local ports: 5432 → Allow the connection → Domain,Private,Public → Name: PostgreSQL-5432
```

---

## 4. INSTALLATION — STEP-BY-STEP

### STEP 4.1: Clone and Validate Repository
```powershell
# From a Windows PowerShell terminal (NON-ADMIN recommended, admin OK)
cd E:\
git clone <YOUR_REPO_URL> BedaanWaves
cd BedaanWaves
dir  # Confirm presence of: \backend, \frontend, \database, \docs, \.env.example, \README.md
```

### STEP 4.2: PostgreSQL — Create Database
```powershell
# Method A: Command line (using default postgres superuser)
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE bedaanwaves_db WITH ENCODING = 'UTF8' LC_COLLATE = 'English_US' LC_CTYPE = 'English_US' TEMPLATE template0;"

# Expected output: CREATE DATABASE

# Verify:
psql -U postgres -c "\l"  # bedaanwaves_db must appear in the listing
```

### STEP 4.3: Backend — Virtual Environment and Dependencies
```powershell
cd E:\BedaanWaves\backend

# Create virtual environment (Python 3.11 must be on PATH)
python -m venv venv

# ACTIVATE the virtual environment — THIS IS MANDATORY BEFORE ANY pip INSTALL
.\venv\Scripts\Activate.ps1

# You should now see (venv) prefix in your prompt. If PowerShell blocks script execution:
#     Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
# Confirm by re-running the activate script.

# Install core dependencies (USE requirements.txt — lockfile, NOT pyproject.toml)
pip install --upgrade pip
pip install -r requirements.txt

# CRITICAL validation:
python -c "import sqlalchemy, asyncpg, fastapi, uvicorn, sklearn, xgboost, statsmodels, redis, pandas; print('ALL 10 CORE IMPORTS OK')"
```

### STEP 4.4: Backend — Environment Configuration
```powershell
cd E:\BedaanWaves
copy .env.example .env
notepad .env  # or: code .env
```

**EDIT these three mandatory fields. Leave everything else at defaults:**
```dotenv
# LINE 20 (approx):
DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/bedaanwaves_db

# LINE 74: Generate a 64+ character random key. Use PowerShell:
#   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | % {[char]$_})
SECRET_KEY=your_64_character_random_string_here

# LINE 75: Generate another DIFFERENT 64+ character random key
JWT_SECRET=your_different_64_character_random_string_here
```

### STEP 4.5: Backend — Apply Database Migrations (Alembic)
```powershell
cd E:\BedaanWaves\backend
.\venv\Scripts\Activate.ps1   # if not already active

# Initialize database schema to HEAD revision
alembic upgrade head

# SUCCESS looks like:
#   INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
#   INFO  [alembic.runtime.migration] Will assume transactional DDL.
#   INFO  [alembic.runtime.migration] Running upgrade  -> c57c8b5674de, initial migration...
#   ...
#   Running upgrade ... -> 20260903_add_market_score_trend

# Validate migration state:
alembic current  # Must print: 20260903_add_market_score_trend (head)
```

### STEP 4.6: Database — Seed NASDAQ Symbol Universe
```powershell
cd E:\BedaanWaves\database
psql -U postgres -d bedaanwaves_db -f init_nasdaq.sql
psql -U postgres -d bedaanwaves_db -f insert_nasdaq_symbols.sql

# Validate: 2 rows inserted?
psql -U postgres -d bedaanwaves_db -c "SELECT COUNT(*) FROM symbols;"
```

### STEP 4.7: Frontend — Dependencies
```powershell
cd E:\BedaanWaves\frontend
npm install

# Wait for 500+ packages. At the end you should see:
#   added 512 packages, and audited 513 packages in 2m
#   0 vulnerabilities

# Validate:
npx tsc --noEmit  # Takes 30-60 seconds. Should produce NO output = no errors.
```

### STEP 4.8: Frontend — Environment Configuration
```powershell
cd E:\BedaanWaves\frontend

# Create .env.local (NOT committed to git)
@"
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api/v1
NEXT_PUBLIC_APP_ENV=development
"@ | Out-File -Encoding utf8 .env.local
```

---

## 5. LOCAL EXECUTION (DEVELOPMENT MODE)

Run **two separate PowerShell windows** (TAB1 = Backend, TAB2 = Frontend).

```
┌──────────────────────────────────────────────────────────────────────┐
│  TAB 1: BACKEND API                                                  │
├──────────────────────────────────────────────────────────────────────┤
│  cd E:\BedaanWaves\backend                                           │
│  .\venv\Scripts\Activate.ps1                                         │
│  python run.py                                                       │
│                                                                      │
│  SUCCESS OUTPUT (within 15 seconds):                                 │
│    INFO:     Uvicorn running on http://0.0.0.0:3000                  │
│    INFO:     Application startup complete.                           │
│    INFO:     Admin user created: admin@bedaanwaves.com / <password>  │
│                                                                      │
│  Verify API health:                                                  │
│    Open browser → http://localhost:3000/api/v1/health                │
│    Expected JSON: {"status":"healthy","version":"1.0.0"}             │
│                                                                      │
│  API docs (Swagger UI):                                              │
│    http://localhost:3000/api/v1/docs                                 │
└──────────────────────────────────────────────────────────────────────┘
```

```
┌──────────────────────────────────────────────────────────────────────┐
│  TAB 2: FRONTEND (Next.js Dev Server)                                │
├──────────────────────────────────────────────────────────────────────┤
│  cd E:\BedaanWaves\frontend                                          │
│  npm run dev                                                         │
│                                                                      │
│  SUCCESS OUTPUT (within 30 seconds):                                 │
│    ▲ Next.js 16.2.9                                                  │
│    - Local:        http://localhost:3005                             │
│    - Environments: .env.local                                        │
│    ✓ Ready in 2.8s                                                   │
│                                                                      │
│  Open the application:                                               │
│    → http://localhost:3005                                           │
│    → Click "Login" → use credentials from backend TAB1 admin logline │
└──────────────────────────────────────────────────────────────────────┘
```

**SMOKE TEST (first-run walkthrough):**
1. Navigate to http://localhost:3005 → Landing page loads (English-only, LTR, no icons)
2. Click Login → use `admin@bedaanwaves.com` + auto-generated password
3. Redirect to `/dashboard` → Spider Chart renders with 6 axes
4. Change date in Date Selector → SpiderChart + ScoreTrendChart BOTH update (DateStore sync test)
5. Navigate to `/ranking` → NASDAQ-100 top-10 ranking table renders
6. Navigate to `/stocks/AAPL` → Candlestick chart, multi-dimension score card loads

---

## 6. BUILD FOR PRODUCTION

### Backend Build (Python — No compilation, PYC pre-compilation)
```powershell
cd E:\BedaanWaves\backend
.\venv\Scripts\Activate.ps1

# Pre-compile all .py to .pyc (eliminates first-hit cold start latency)
python -m compileall -q app
# → Listing 1200 files... (no error output = success)

# Verify production server starts cleanly (5-second smoke test, then Ctrl+C)
$env:ENVIRONMENT="production"
$env:DEBUG="False"
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --workers 4
```

### Frontend Build (Next.js Standalone Production)
```powershell
cd E:\BedaanWaves\frontend
$env:NEXT_TELEMETRY_DISABLED="1"
npm run build

# SUCCESS:  Route (app)                                Size     First Load JS
#           ┌ ○ /                                      2.1 kB         98 kB
#           ├ ○ /(auth)/login                          3.4 kB        101 kB
#           ├ ... all routes
#           ✓ Production build completed successfully.

# Run production frontend server:
npm start
# → Listening on port 3005
```

---

## 7. NATIVE SERVICES MANAGEMENT (WINDOWS)

For long-running development environments, register backend/frontend as Windows Services using [NSSM](https://nssm.cc/):

```powershell
# Install NSSM via Chocolatey:
choco install nssm -y

# 7A: Register BedaanWaves Backend as Windows Service "BW-Backend-v2"
nssm install BW-Backend-v2 "E:\BedaanWaves\backend\venv\Scripts\python.exe" "-m uvicorn app.main:app --host 0.0.0.0 --port 3000 --workers 2"
nssm set BW-Backend-v2 AppDirectory "E:\BedaanWaves\backend"
nssm set BW-Backend-v2 AppStdout "E:\BedaanWaves\logs\backend-service.log"
nssm set BW-Backend-v2 AppStderr "E:\BedaanWaves\logs\backend-service-err.log"
nssm set BW-Backend-v2 Start SERVICE_AUTO_START
nssm start BW-Backend-v2

# 7B: Register BedaanWaves Frontend as Windows Service "BW-Frontend-v2"
nssm install BW-Frontend-v2 "C:\Program Files\nodejs\node.exe" "E:\BedaanWaves\frontend\node_modules\next\dist\bin\next start -p 3005"
nssm set BW-Frontend-v2 AppDirectory "E:\BedaanWaves\frontend"
nssm set BW-Frontend-v2 AppStdout "E:\BedaanWaves\logs\frontend-service.log"
nssm set BW-Frontend-v2 AppStderr "E:\BedaanWaves\logs\frontend-service-err.log"
nssm set BW-Frontend-v2 Start SERVICE_AUTO_START
nssm start BW-Frontend-v2
```

---

## 8. TROUBLESHOOTING — ALL KNOWN FAILURE MODES

### F-001: Backend crashes on start with `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection refused`
**Cause:** PostgreSQL service not running, wrong DATABASE_URL, or Windows Firewall blocking port 5432.
**Fix:**
```powershell
services.msc → Start "postgresql-x64-16"
# Re-verify connection string in .env: DATABASE_URL format must be:
# postgresql://USER:PASSWORD@localhost:5432/bedaanwaves_db
```

### F-002: Frontend shows "Network Error" on login / "Failed to fetch"
**Cause:** NEXT_PUBLIC_API_BASE_URL misconfigured, or backend not running on port 3000.
**Fix:**
```powershell
# Check frontend/.env.local — MUST be:
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api/v1

# In backend .env: ensure CORS_ORIGINS includes frontend:
CORS_ORIGINS=["http://localhost:3000","http://localhost:3005","http://127.0.0.1:3005"]
```

### F-003: Alembic migration fails with `ERROR: relation "alembic_version" does not exist`
**Cause:** Database was partially initialized. Start from a clean state:
```powershell
psql -U postgres -c "DROP DATABASE IF EXISTS bedaanwaves_db WITH (FORCE);"
psql -U postgres -c "CREATE DATABASE bedaanwaves_db WITH ENCODING = 'UTF8' ...;"
cd backend && alembic upgrade head
```

### F-004: Redis connection errors on backend startup: `redis.exceptions.ConnectionError: Error 10061 connecting to localhost:6379`
**Cause:** Redis/Memurai not installed, service not running, or wrong port.
**Fix 1 (Install):** Install Memurai Developer (native Windows). Start service.
**Fix 2 (Graceful Fallback):** In `.env`, set `CACHE_BACKEND=memory`. Backend runs without Redis.

### F-005: PowerShell `Activate.ps1` blocked — "execution of scripts is disabled on this system"
**Cause:** Default Windows PowerShell execution policy.
**Fix:**
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
# Confirm with [Y]. Re-run activate.
```

### F-006: `pip install -r requirements.txt` fails — "Microsoft Visual C++ 14.0 or greater is required"
**Cause:** Missing native build toolchain for scipy/xgboost/asyncpg C-extensions.
**Fix:**
```
Download "Build Tools for Visual Studio 2022":
https://visualstudio.microsoft.com/visual-cpp-build-tools/
→ Install → Check "Desktop development with C++" → Install (requires ~6GB)
→ Restart PowerShell → Re-run pip install
```

### F-007: Frontend build (`npm run build`) runs out of memory — "JavaScript heap out of memory"
**Fix:**
```powershell
cd frontend
$env:NODE_OPTIONS="--max-old-space-size=8192"
npm run build
```

### F-008: Chart data displays "NaN" or dates are 1970-01-01 (Unix epoch zero)
**Cause:** No score_history data ingested yet (empty database).
**Fix:** In backend (with venv active), run a one-time ingestion:
```powershell
cd backend
python -m app.services.data.nasdaq_ingestion_service --full-sync
```

### F-009: PostgreSQL 5432 port — "cannot assign requested address" in Windows Service
**Cause:** Postgres binds to IPv6 `::1` only; API tries IPv4 `127.0.0.1`.
**Fix:** Edit `postgresql.conf` (default: `C:\Program Files\PostgreSQL\16\data\postgresql.conf`):
```
listen_addresses = '*'
```
Save, restart service.

### F-010: JWT "Signature has expired" immediately after login
**Cause:** Server clock is drifting or timezone mismatch between machine UTC/local.
**Fix:**
```powershell
# Force-sync system clock
w32tm /resync /force
# Verify:
Get-Date -Format "yyyy-MM-dd HH:mm:ss K"  # TZ offset should match your location
```

---

## 9. TESTING — FULL QA SUITE EXECUTION

```powershell
# ─────────────────────────────────────────────────────
# BACKEND — FULL REGRESSION (100% PASS REQUIRED)
# ─────────────────────────────────────────────────────
cd E:\BedaanWaves\backend
.\venv\Scripts\Activate.ps1
python -m pytest tests/ -v --cov=app --cov-report=term-missing --tb=short
# Expected exit code: 0
# Expected coverage: ≥ 78%

# ─────────────────────────────────────────────────────
# FRONTEND — TYPE CHECK + LINT + UNIT TEST
# ─────────────────────────────────────────────────────
cd E:\BedaanWaves\frontend
npx tsc --noEmit          # TypeScript strict mode — 0 errors
npm run lint              # ESLint — max-warnings=0
npm run test -- --run     # Vitest — 17 suites, 0 failures

# ─────────────────────────────────────────────────────
# E2E — PLAYWRIGHT (requires backend + frontend running)
# ─────────────────────────────────────────────────────
# PRE-CONDITION: Backend on :3000 + Frontend on :3005 BOTH running in separate tabs
cd E:\BedaanWaves\frontend
npx playwright install chromium    # One-time: downloads Chromium headless (~200MB)
npx playwright test --reporter=list
# Expected: 20/20 scenarios passed
```

---

## 10. PROJECT STRUCTURE (CANONICAL)

```
E:\BedaanWaves\
├── backend/                         ★ FastAPI application root
│   ├── app/
│   │   ├── api/                     REST routes (28 modules)
│   │   │   └── routes/              auth, dashboard, ranking, stocks, forecast, alerts, compare...
│   │   ├── application/             Interfaces + DTOs + application-layer services
│   │   ├── core/                    Config, exceptions, rate-limiting, DIC bootstrap
│   │   ├── db/                      AsyncSession base
│   │   ├── domain/                  Rich domain: Entities, ValueObjects, ScoringEngines
│   │   ├── infrastructure/          Cache backends, HTTP clients, Logging, CircuitBreaker
│   │   ├── models/                  SQLAlchemy ORM models (single source of truth)
│   │   ├── schemas/                 Pydantic V2 request/response schemas
│   │   ├── services/                All business services (6 main categories, 42 total services)
│   │   │   ├── analysis/            Scoring, Fundamental, Technical, Momentum, Volatility, Risk
│   │   │   ├── core/                Base, Cache, Config, Database, Health, Logger
│   │   │   ├── data/                Ingestion, News, Market, Portfolio, Symbol, History
│   │   │   ├── ml/                  Forecast, Anomaly, Recommendation, Pattern, PortfolioOpt
│   │   │   ├── nlp/                 Sentiment, Summarization, Document extraction
│   │   │   ├── specialized/         Sector, Correlation, Screening, Comparison, Intl Markets
│   │   │   ├── system/              Backup, Metrics, Queue, Retention, Schema, Settings
│   │   │   └── user/                Auth, Authorization, Notification, Watchlist, Preferences
│   │   ├── tests/                   Unit tests (by domain module)
│   │   ├── main.py                  Uvicorn entrypoint, app factory, lifespan hooks
│   ├── database/
│   │   └── alembic/                 Database migrations (versions/*.py)
│   ├── models/coefficients/         ML coefficient JSON files (4 files)
│   ├── tests/                       Integration + cross-cutting tests (40+ files)
│   ├── requirements.txt             LOCKED dependency manifest (USE THIS — NOT pyproject.toml)
│   ├── pyproject.toml               Project metadata + dev deps
│   ├── pytest.ini                   Pytest configuration
│   ├── run.py                       Convenience runner (calls uvicorn)
│   ├── alembic.ini                  Alembic configuration
│   └── .env.example                 Backend env template (copy to .env)
│
├── frontend/                        ★ Next.js 16 (App Router) + React 19
│   ├── src/
│   │   ├── app/                     Route segments (App Router convention)
│   │   │   ├── (auth)/              /login /register /forgot-password /reset-password
│   │   │   ├── (public)/            /about /blog /contact /services / (landing)
│   │   │   ├── dashboard/           /dashboard (main workspace, charts)
│   │   │   ├── ranking/             /ranking (Nasdaq 100 ranked)
│   │   │   ├── stocks/[symbol]/     Dynamic stock pages + tabs (charts, scoring)
│   │   │   ├── analysis/            Analysis overview
│   │   │   ├── alerts/              Price-alert management
│   │   │   ├── news/                News feed + sentiment
│   │   │   ├── portfolio/           Portfolio dashboard
│   │   │   ├── settings/            User settings / profile
│   │   │   ├── help/                In-app help
│   │   │   ├── methodology/         Scoring methodology documentation
│   │   │   ├── layout.tsx           Root layout, lang=en, dir=ltr
│   │   │   └── globals.css          Inter font, Tailwind preflight
│   │   ├── components/              React components
│   │   │   ├── charts/              Area, Bar, Candle, Line, Spider, ScoreTrend, TradingView
│   │   │   ├── dashboard/           DateSelector, SpiderSection, StatBox, NewsList, etc.
│   │   │   ├── layout/              NewSidebar, NewTopbar, NewDashboardShell
│   │   │   ├── ui/                  Primitive UI: Button, Card, Input, Modal, Badge, Table...
│   │   │   └── ux/                  Toast, Modal, ErrorBoundary, Keyboard shortcuts, FSM
│   │   ├── hooks/                   usePasswordRecoveryFSM, useSSE, useStockSearch
│   │   ├── lib/                     api clients, utils (cn, chart-time, export, sse)
│   │   ├── providers/               ReactQueryProvider, ThemeProvider, UXProviders
│   │   ├── store/                   useAuthStore, useDateStore (CENTRAL SYNC), useAppStore, useUXStore
│   │   ├── styles/                  design-tokens.ts (8px spacing grid)
│   │   └── tests/                   Vitest unit tests (17 suites)
│   ├── e2e/                         Playwright E2E (auth.spec.ts, automation.spec.ts)
│   ├── package.json                 NPM manifest (scripts)
│   ├── tsconfig.json                TypeScript strict config
│   ├── next.config.ts               Next.js configuration
│   ├── playwright.config.ts         E2E configuration
│   └── vitest.config.ts             Vitest configuration
│
├── database/                        ★ SQL bootstrap scripts
│   ├── init_nasdaq.sql
│   └── insert_nasdaq_symbols.sql
│
├── deployment/                      ★ Native deployment configs (no Docker)
│   ├── setup.sh                     Linux bootstrap
│   ├── deploy.sh                    Linux deploy
│   └── redis/                       redis.conf, redis.windows.conf
│
├── docs/                            ★ All project documentation
│   └── project_closure/             ★ THIS DELIVERABLE SET (v2.0.0)
│       ├── Nasdaq-Index-Comparison.md        (PART 1 output)
│       ├── 01_QA-Signoff-v2.0.0.md           (§2.1)
│       ├── 02_Code-Asset-Hardening-v2.0.0.md (§2.2)
│       ├── README.md                        (THIS FILE — §2.3.1)
│       ├── User-Manual.md                   (§2.3.2)
│       ├── 03_API-Reference-v2.0.0.md       (§2.3.3)
│       ├── 04_Delivery-Packaging-v2.0.0.md  (§2.4)
│       ├── CHANGELOG.md                     (§2.4.2)
│       ├── 05_Risk-Mitigation-Rollback-v2.0.0.md (§2.5)
│       ├── 06_Stakeholder-Handover-Kit-v2.0.0.md (§2.6)
│       └── 07_Universal-Finalization-Checklist-v2.0.0.md (§2.7)
│
├── .env.example                     Root-level .env template (copy → .env)
├── .gitignore                       Delivery hygiene exclusions applied
└── README.md                        → symbolic/canonical reference to this file
```

---

## 11. SUPPORT & ESCALATION

| Severity | Definition | Response SLA | Contact |
|----------|-----------|--------------|---------|
| P1 — CRITICAL | Production outage, data loss, security breach, 100% of users blocked | 15 minutes | +ESCALATION@BEDAANWAVES (on-call rotation) |
| P2 — HIGH | Major feature broken (dashboard not loading, forecast fail, alerts not firing), 10+ users blocked | 2 hours | support@bedaanwaves.com |
| P3 — MEDIUM | Minor UI glitch, single user edge case, documentation typo | 1 business day | support@bedaanwaves.com |
| P4 — LOW | Cosmetic issue, enhancement suggestion | Best effort | suggestions@bedaanwaves.com |

**Developer Tooling Issue (not platform):** Report with exact error text, screenshot, `Get-ComputerInfo`, `python --version`, `node --version`.

---

*Document ID: BW-README-v2.0.0 | Effective Release: 2026-09-05 | Supersedes: README v1.0.0*
