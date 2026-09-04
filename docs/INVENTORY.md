# BedaanWaves Documentation — Master Inventory

> **Phase 1 Output** — Complete analysis of all original documentation files before reorganization.

**Analysis Date:** 2026-09-04  
**Total Original Files:** 87 (86 Markdown + 1 PNG + 1 HTML)  
**Total After Reorganization:** 64 active files + 6 archived stubs + 1 PNG  

---

## 1. Original File Tree (Pre-Refactor)

### Root-level docs (21 files)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 1 | `01_executive_overview.md` | 3.9 KB | Executive summary claiming "Production Ready 100%". Bilingual sections. 9-tier architecture overview. Getting started guide. |
| 2 | `018_implementation_status_report.md` | 14.0 KB | Verified status report. Contradicts 01 — claims 79% complete, 14 P0/P1 services missing across Tier 2 and Tier 9. |
| 3 | `02_architecture_design.md` | 20.5 KB | 9-tier architecture, design principles, communication patterns, data flow, security, code organization. |
| 4 | `03_technology_stack.md` | 27.1 KB | Full tech stack: Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis, NumPy, Pandas, spaCy, Transformers. |
| 5 | `04_service_catalog.md` | 20.3 KB | Service inventory across 9 tiers. Contains duplicate info with 02 and 08. |
| 6 | `05_api_documentation.md` | 14.8 KB | API docs — 16 routers, endpoints, schemas, rate limiting, WebSocket API. English. |
| 7 | `06_database_schema.md` | 16.3 KB | PostgreSQL schema design, table specs, migration structure, backup strategy. |
| 8 | `07_configuration_guide.md` | 10.3 KB | Environment variables, 15 config categories, validation, security best practices. |
| 9 | `08_core_services.md` | 16.1 KB | Detailed Tier 1 service docs: DependencyContainer, ConfigService, LoggerService, CacheService, DatabaseService, HealthChecker. |
| 10 | `09_data_services.md` | 38.2 KB | Detailed Tier 2 service docs: YahooFinanceClient, StockService, MarketService, PortfolioService, HistoryService, NewsService, IngestionService, MarketDataProcessing, IntlApiClient, DataValidationService, FinancialDataIngestService, StockFundamentalDataIngestionService. |
| 11 | `10_analysis_services.md` | 31.5 KB | Detailed Tier 3: ScoringService (6D/305 nodes), TechnicalAnalysisService (50+ indicators), FundamentalAnalysisService, RiskAnalysisService, MomentumService, VolatilityService, UserFilteredScoringService. Plus behavioral economics, currency, monetary policy services. |
| 12 | `11_ml_services.md` | 2.6 KB | Brief ML service overview. 8 services listed (note: duplicates 8th as TimeSeriesForecastingService). |
| 13 | `12_core_services.md` | 2.1 KB | Stub — lists 9 core services including RateLimiterService and ErrorHandlerService (not in 08). |
| 14 | `13_ml_services.md` | 2.5 KB | More detailed ML docs. 8 services with mermaid architecture diagram. |
| 15 | `14_nlp_services.md` | 2.6 KB | NLP services: Sentiment, Summarization, DocumentExtraction, Chatbot, Search, MultiLanguageNews. Persian support mentioned. |
| 16 | `16_specialized_services.md` | 2.1 KB | Specialized services: SectorAnalysis, Screening, Comparison, Correlation, Calendar, InternationalMarket, SectorFilter. |
| 17 | `17_frontend.md` | 1.3 KB | Stub — minimal frontend overview. |
| 18 | `18_password_recovery_architecture.md` | 9.5 KB | Password recovery FSM, component architecture, API endpoints, security, WCAG compliance. References `spec.yaml`. |
| 19 | `19_password_recovery_audit.md` | 5.7 KB | Audit checklist for password recovery — 34 items across 8 categories. |
| 20 | `AGENTS.md` | 2.1 KB | Agent reference: project layout, commands, test instructions. (KEPT at root for tooling) |
| 21 | `API_DOCUMENTATION.md` | 5.7 KB | Bilingual (English/Persian) API docs. Different endpoints from 05. |

### Standalone docs (6 files)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 22 | `dashboard-charts-spec.md` | 4.7 KB | Dashboard chart specification — 20 charts across spider/line/column/weight categories. Data sync contract. |
| 23 | `design-system-audit-checklist.md` | 6.3 KB | UI audit checklist — colors, typography, spacing, components, accessibility, dark mode. |
| 24 | `MASTER_PLAN.md` | 11.7 KB | Bilingual (Persian) master plan with roadmap, phases, risk management. |
| 25 | `NATIVE_WINDOWS_SETUP.md` | 16.7 KB | Bilingual (Persian) Windows native setup guide (no Docker). |
| 26 | `REDIS_SETUP.md` | 6.4 KB | Bilingual (Persian) Redis setup guide. |
| 27 | `STYLE_GUIDE.md` | 13.0 KB | Design system: tokens, components, layout, UX rules, migration notes. |

### docs/analysis/ (6 files)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 28 | `ai_analysis.md` | 19.4 KB | AI analysis services documentation. |
| 29 | `fundamental_analysis.md` | 14.2 KB | Fundamental analysis service. |
| 30 | `macro_analysis.md` | 7.5 KB | Macroeconomic analysis. |
| 31 | `risk_analysis.md` | 8.9 KB | Risk analysis services. |
| 32 | `sentiment_analysis.md` | 11.2 KB | Sentiment analysis (NLP). |
| 33 | `technical_analysis.md` | 11.9 KB | Technical analysis (50+ indicators). |

### docs/api/ (1 file — STUB)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 34 | `postgre.md` | 230 B | 6-line stub — "PostgreSQL Configuration Documentation". |

### docs/architecture/ (3 files — HISTORICAL)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 35 | `ARCHITECTURE_ANALYSIS.md` | 19.5 KB | OldFils 5-project architectural analysis (July 2026). |
| 36 | `ARCHITECTURE_DETAILS.md` | 32.8 KB | Historical technical specs from planning phase. DB schema for international markets. |
| 37 | `BEDAANWAVES_REWRITE_STRATEGY.md` | 13.6 KB | Rewrite strategy for consolidating 5 OldFils projects. |
| 38 | `DATABASE_CRITICALITY_UPGRADE_PLAN.md` | 25.9 KB | Database criticality upgrade plan. |

### docs/database/ (1 file)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 39 | `database_schema_documentation.md` | 19.8 KB | Database schema with different table names (USERS, MARKET_DATA, STOCK, etc.) than 06. MySQL-style, not PostgreSQL. |

### docs/diagrams/ (19 files)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 40 | `README.md` | 635 B | Diagrams package overview. |
| 41 | `uml/README.md` | 225 B | UML levels description. |
| 42 | `uml/level_1_overview.md` | 1.7 KB | UML Level 1: System overview. |
| 43 | `uml/level_2_components.md` | 2.4 KB | UML Level 2: Component diagram. |
| 44 | `uml/level_3_services.md` | 2.1 KB | UML Level 3: Service breakdown. |
| 45 | `uml/level_4_sequences.md` | 2.9 KB | UML Level 4: Sequence diagrams. |
| 46 | `uml/level_5_classes.md` | 2.1 KB | UML Level 5: Class diagrams. |
| 47 | `uml/level_6_end_to_end_paths.md` | 3.5 KB | UML Level 6: End-to-end paths. |
| 48 | `dfd/README.md` | 291 B | DFD levels description. |
| 49 | `dfd/level_1_context.md` | 760 B | DFD Level 1: System context. |
| 50 | `dfd/level_2_auth_and_access.md` | 1.1 KB | DFD Level 2: Authentication flow. |
| 51 | `dfd/level_3_market_data_flow.md` | 1.2 KB | DFD Level 3: Market data flow. |
| 52 | `dfd/level_4_analysis_ml_flow.md` | 1.1 KB | DFD Level 4: Analysis & ML flow. |
| 53 | `dfd/level_5_portfolio_and_user_flow.md` | 1.3 KB | DFD Level 5: Portfolio/user flow. |
| 54 | `dfd/level_6_system_jobs_metrics_queue_flow.md` | 1.3 KB | DFD Level 6: System jobs/metrics/queue. |
| 55 | `bpmn/README.md` | 321 B | BPMN levels description. |
| 56 | `bpmn/level_1_processes_overview.md` | 1.4 KB | BPMN Level 1: Process overview. |
| 57 | `bpmn/level_2_auth_process.md` | 1.2 KB | BPMN Level 2: Auth process. |
| 58 | `bpmn/level_3_market_ingest_process.md` | 1.4 KB | BPMN Level 3: Market ingestion. |
| 59 | `bpmn/level_4_signal_generation_process.md` | 1.5 KB | BPMN Level 4: Signal generation. |
| 60 | `bpmn/level_5_portfolio_management_process.md` | 1.5 KB | BPMN Level 5: Portfolio management. |
| 61 | `bpmn/level_6_notifications_process.md` | 1.3 KB | BPMN Level 6: Notifications. |

### docs/frontend/ (12 files)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 62 | `FrontEnd.md` | 622 B | Stub — minimal frontend display documentation. |
| 63 | `FrontEnd_display_documentation.md` | 2.9 KB | Frontend page documentation — lists 12 pages with descriptions. |
| 64 | `pages/alerts.md` | 2.0 KB | Alerts page specification. |
| 65 | `pages/analysis.md` | 1.8 KB | Analysis page specification. |
| 66 | `pages/dashboard.md` | 1.4 KB | Dashboard page specification. |
| 67 | `pages/help.md` | 1.4 KB | Help page specification. |
| 68 | `pages/login.md` | 1.5 KB | Login page specification. |
| 69 | `pages/methodology.md` | 1.7 KB | Methodology page specification. |
| 70 | `pages/news.md` | 1.4 KB | News page specification. |
| 71 | `pages/portfolio.md` | 1.2 KB | Portfolio page specification. |
| 72 | `pages/register.md` | 1.6 KB | Registration page specification. |
| 73 | `pages/stock.md` | 1.4 KB | Stock detail page specification. |
| 74 | `pages/watchlist.md` | 2.7 KB | Watchlist page specification. |

### docs/integration/ (2 files)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 75 | `INTEGRATION_FRAMEWORK.md` | 49.6 KB | Historical strategic planning document (July 2026). Labeled "HISTORICAL". |
| 76 | `README_INTEGRATION.md` | 8.3 KB | Current integration status — Phase 1 & 2 complete, Phase 3 ~85%. |

### docs/planning/ (5 files — 3 are 5-line stubs)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 77 | `ANALYSIS_SUMMARY.md` | 154 B | 5-line stub — "Planning Document" placeholder. |
| 78 | `ANALYSIS_INDEX.md` | 154 B | 5-line stub — "Planning Document" placeholder. |
| 79 | `IMPLEMENTATION_CHECKLIST.md` | 10.4 KB | Implementation checklist with pre-integration assessment. |
| 80 | `REWRITE_PROGRESS.md` | 12.6 KB | Rew progress tracking with phase completion status. |
| 81 | `TODO.md` | 7.9 KB | TODO list with service inventory by tier. |
| 82 | `Source_Within.md` | 154 B | 5-line stub — "Planning Document" placeholder. |

### docs/project_documentation/ (1 file)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 83 | `index.html` | 50.5 KB | Standalone HTML documentation bundle. |

### docs/system/ (2 files)
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 84 | `architecture.md` | 5.5 KB | System architecture overview (alternative to 02). |
| 85 | `testcoverage.md` | 2.3 KB | Test coverage plan — 671 tests, 95%+ target. |

### Other
| # | File | Size | Content Summary |
|---|------|------|-----------------|
| 86 | `Financial_Intelligence_Ecosystem_Architecture.png` | 6.1 MB | Visual architecture diagram. |
| 87 | `kilo.json` | (config) | Kilo agent configuration. |

---

## 2. Key Observations

### Content Discrepancies (Pre-Refactor)

| Discrepancy | Details |
|------------|---------|
| **Implementation Status** | `01_executive_overview.md` claims "Production Ready (100%)". `018_implementation_status_report.md` shows 79% — 14 P0/P1 services missing. |
| **API Router Count** | `05_api_documentation.md` and `03_technology_stack.md` claim "16 routers". Actual `main.py` imports 27 routers. |
| **Database Schema** | `06_database_schema.md` uses PostgreSQL with `assets`, `price_candles` tables. `database/database_schema_documentation.md` uses MySQL-style `STOCKS`, `MARKET_DATA` tables. |
| **Market Support** | Docs (02, 09, 09) describe NYSE, LSE, international markets. Source code (`models.py`) restricts to NASDAQ only. |
| **Frontend Tech** | `03_technology_stack.md` describes "Next.js 14+" and "Zustand 4.5.0+". Actual code uses Next.js 16 and already has Zustand. |
| **NLP Language** | Docs describe Persian + English NLP. `config.py` uses `bert-base-uncased` (English only). |

### Duplicate Detection Summary

| Duplicate Pair | Files | Resolution |
|---------------|-------|------------|
| A | `01_executive_overview.md` vs `018_implementation_status_report.md` | **Merged**: Overview claims 100%, status report shows 79%. Status report wins for accuracy. |
| B | `05_api_documentation.md` vs `API_DOCUMENTATION.md` | **Both kept**: English vs Bilingual/Persian — serve different audiences. |
| C | `08_core_services.md` vs `12_core_services.md` | **Merged**: 08 is detailed, 12 is a stub adding 2 extra services (RateLimiterService, ErrorHandlerService). |
| D | `11_ml_services.md` vs `13_ml_services.md` | **Both kept**: 11 is brief, 13 is detailed with architecture diagram. |
| E | `02_architecture_design.md` vs `system/architecture.md` | **Both kept**: 02 is detailed principles, system/architecture is a brief overview. |
| F | `06_database_schema.md` vs `database/database_schema_documentation.md` | **Both kept**: PostgreSQL vs MySQL-style, different audiences. |
| G | `17_frontend.md` vs `frontend/FrontEnd.md` vs `frontend/FrontEnd_display_documentation.md` | **Merged**: 17 is a stub, FrontEnd.md is a stub, FrontEnd_display_documentation.md is the most detailed. |
| H | `planning/ANALYSIS_SUMMARY.md`, `planning/ANALYSIS_INDEX.md`, `planning/Source_Within.md` | **All 3 are 5-line stubs** — identical content. Merged into one. |

### Obsolete / Stub Files

| File | Reason |
|------|--------|
| `planning/ANALYSIS_SUMMARY.md` | 5-line stub |
| `planning/ANALYSIS_INDEX.md` | 5-line stub (identical to above) |
| `planning/Source_Within.md` | 5-line stub (identical to above) |
| `api/postgre.md` | 6-line stub |
| `17_frontend.md` | 48-line minimal stub |
| `12_core_services.md` | 62-line stub with different service list |
| `11_ml_services.md` | 61-line brief, superseded by 13 |
| `17_frontend.md` + `frontend/FrontEnd.md` | Minimal stubs, superseded by frontend/FrontEnd_display_documentation.md |
| `docs/architecture/*` (4 files) | Explicitly labeled "Historical" in source |
| `docs/integration/INTEGRATION_FRAMEWORK.md` | Explicitly labeled "HISTORICAL DOCUMENT" |
| `project_documentation/index.html` | Standalone legacy HTML bundle |

---

## 3. Original Source Code Structure (Backend)

### Directory Layout
```
backend/
├── app/
│   ├── api/
│   │   ├── routes/          # 27 router modules
│   │   ├── middleware.py    # RateLimit, CorrelationId, AuthGuard, RequestLogging
│   │   └── dependencies.py
│   ├── core/                # config.py, exceptions.py, rate_limiting.py, services.py
│   ├── db/                  # base.py (async_session_maker)
│   ├── domain/              # entities, interfaces, services, shared, value_objects
│   ├── infrastructure/      # cache, core, http, logging, utils
│   ├── models/              # models.py (1573 lines, SQLAlchemy ORM)
│   ├── schemas/             # schemas.py (537 lines, Pydantic v2)
│   ├── services/
│   │   ├── core/            # 6 services (DependencyContainer, ConfigService, etc.)
│   │   ├── core/ (alt)      # base_service.py, cache_service.py, config_service.py
│   │   ├── data/            # 19 service files
│   │   ├── analysis/        # 27 service files
│   │   ├── ml/              # 8 service files
│   │   ├── nlp/             # 4 service files
│   │   ├── user/            # 8 service files (auth, password_reset, etc.)
│   │   ├── specialized/     # 7 service files
│   │   └── system/          # 9 service files
│   └── main.py              # Application entry point (556 lines)
├── database/alembic/        # Migrations
└── scripts/seed_real_data.py
```

### API Router Inventory (from `app/api/routes/__init__.py`)

**27 routers** exported (docs claim 16):

| Router | Prefix (in main.py) | Purpose |
|--------|---------------------|---------|
| auth | `/api/v1/auth` | Authentication (login, register, verify) |
| password_reset | `/api/v1/auth` | Password recovery (request, verify, confirm) |
| stocks | `/api/v1/stocks` | Stock data, details, history |
| market | `/api/v1/market` | Market overview, indices, gainers/losers |
| analysis | `/api/v1/analysis` | 6D scores, signals, predictions, backtest |
| portfolio | `/api/v1/portfolio` | Portfolio CRUD, holdings, performance |
| history | `/api/v1/history` | Historical price/score/signal/prediction data |
| news | `/api/v1/news` | News search, sentiment, summarization |
| ml | `/api/v1/ml` | ML models, predictions, recommendations |
| users | `/api/v1/users` | User profile, KYC, settings |
| watchlists | `/api/v1/watchlists` | Watchlist CRUD |
| notifications | `/api/v1/notifications` | Notification management |
| specialized | `/api/v1/specialized` | Macro, exchange rates, cross-asset |
| system | `/api/v1/system` | Status, health, metrics, logs, maintenance |
| intl | `/api/v1/intl` | International markets |
| live | `/api/v1/live` | Real-time data streaming (SSE) |
| live_sse | `/api/v1/live` | SSE-specific routes |
| health | `/api/v1/health` | Health check endpoints |
| market_data | `/api/v1/market-data` | Market data operations |
| data_health | (no prefix) | Data health checks |
| dashboard | `/api/v1/analysis` | Dashboard data |
| symbols | `/api/v1/symbols` | Symbol management |
| settings | `/api/v1/settings` | System settings |
| ranking | `/api/v1/ranking` | Ranking services |

**Note:** `password_reset` router is mounted under `/api/v1/auth` — docs (05) do not list it as a separate router, and API_DOCUMENTATION.md lists only `/auth/password-reset/request` etc. without mapping to the actual router structure.

---

## 4. Original Source Code Structure (Frontend)

### Directory Layout
```
frontend/
├── src/
│   ├── app/                    # Next.js 16 App Router
│   │   ├── (auth)/             # Auth group: login, register, forgot-password, reset-password
│   │   ├── (public)/           # Public: about, blog, contact, services, page
│   │   ├── alerts/             # Alert management
│   │   ├── analysis/           # Analysis pages
│   │   ├── dashboard/          # Main dashboard
│   │   ├── stocks/[symbol]/    # Stock detail pages
│   │   ├── portfolio/          # Portfolio pages
│   │   ├── ranking/            # Ranking display
│   │   ├── news/               # News feed
│   │   ├── settings/           # User settings
│   │   ├── scoring/            # Score visualization
│   │   ├── search-demo/        # Search component demo
│   │   └── design-system/      # Design system showcase
│   ├── components/               # React components (charts, dashboard, ui, layout, search, ux)
│   ├── hooks/                  # Custom hooks (usePasswordRecoveryFSM, useSSE, useStockSearch)
│   ├── i18n/                   # Internationalization
│   ├── lib/                    # Utilities (api.ts, auth.ts, i18n, stores, api modules)
│   ├── store/                  # Zustand stores (useAppStore, useAuthStore, useDateStore, useUXStore)
│   ├── styles/                 # Design tokens
│   └── tests/                  # Test files (13 test files)
```

---

*End of INVENTORY.md — Phase 1 deliverable*
