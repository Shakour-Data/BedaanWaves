# Duplicates Removal Report

> **Phase 2 Output** — Decisions on every duplicate file set identified during inventory.

**Analysis Date:** 2026-09-04  
**Duplicate Sets Found:** 8  
**Files Merged/Reorganized:** 15  
**Files Retained As-Is:** 1  

---

## 1. Summary Table

| # | Duplicate Set | Original Files | Decision | Output File(s) |
|---|---------------|----------------|----------|----------------|
| 1 | Executive overview status | `01_executive_overview.md` vs `018_implementation_status_report.md` | **Merged into status report** (code is source of truth) | `01_overview/OVERVIEW_implementation-status_v1.md` + `01_overview/OVERVIEW_executive-summary_v1.md` |
| 2 | API documentation | `05_api_documentation.md` vs `API_DOCUMENTATION.md` | **Both retained** (different languages: English vs bilingual Persian) | `05_api/API_reference_v1.md`, `05_api/API_reference-persian_v1.md` |
| 3 | Core services | `08_core_services.md` vs `12_core_services.md` | **Both retained** (08 is detailed English; 12 adds 2 extra services) | `02_architecture/ARCH_core-services_v1.md`, `02_architecture/ARCH_core-services-supplement_v1.md` |
| 4 | ML services | `11_ml_services.md` vs `13_ml_services.md` | **Both retained** (11 is brief overview; 13 has architecture diagram) | `04_services/SERVICES_ml-tier4_v1.md`, `04_services/SERVICES_ml-tier4-supplement_v1.md` |
| 5 | Architecture design | `02_architecture_design.md` vs `system/architecture.md` | **Both retained** (02 is comprehensive; system/architecture is a brief summary) | `02_architecture/ARCH_architecture-design_v1.md`, `02_architecture/ARCH_system-architecture_v1.md` |
| 6 | Database schema | `06_database_schema.md` vs `database/database_schema_documentation.md` | **Both retained** (PostgreSQL vs MySQL-style schemas) | `06_database/DB_schema_v1.md`, `06_database/DB_schema_supplemental_v1.md` |
| 7 | Frontend documentation | `17_frontend.md` vs `frontend/FrontEnd.md` vs `frontend/FrontEnd_display_documentation.md` | **FrontEnd_display_documentation.md retained (most detailed); 17 and FrontEnd.md archived as stubs** | `08_frontend/FE_display-documentation_v1.md`, `08_frontend/FE_frontend-overview_v1.md`, `08_frontend/FE_legacy-frontend_v1.md` |
| 8 | Planning stubs | `planning/ANALYSIS_SUMMARY.md` vs `planning/ANALYSIS_INDEX.md` vs `planning/Source_Within.md` | **All 3 archived** (identical 5-line stubs) | `10_planning/PLAN_{analysis-summary,analysis-index,source-within}_v1.md` |

---

## 2. Detailed Decisions

### 2.1 Set 1: Executive Overview Status Conflict

**Files:**
- `01_executive_overview.md` (3.9 KB) — Bilingual project summary, claims "Production Ready 100%"
- `018_implementation_status_report.md` (14.0 KB) — Detailed status report, claims 79% complete with 14 P0/P1 services missing

**Content overlap:**
Both describe the same 9-tier architecture overview and project status. The key difference is implementation status: 01 claims 100%, 018 claims 79%.

**Decision:** **Merge** — Both files are retained but clearly differentiated:
- `OVERVIEW_executive-summary_v1.md` preserves the bilingual overview and project introduction from 01.
- `OVERVIEW_implementation-status_v1.md` preserves the detailed verified status from 018, which is the authoritative source.

**Rationale:** The implementation status report is verified against source code and is the authoritative source of truth. The executive overview contains useful introductory content but misleading status claims. Both are kept for different purposes (intro vs. status).

---

### 2.2 Set 2: API Documentation (English vs Persian)

**Files:**
- `05_api_documentation.md` (14.8 KB) — English-only, 16 routers, comprehensive endpoint listing
- `API_DOCUMENTATION.md` (5.7 KB) — Bilingual (English + Persian), different endpoint structure

**Content overlap:**
- Both document API endpoints, schemas, and rate limiting.
- 05 lists 16 routers and REST endpoints with detailed schemas.
- API_DOCUMENTATION.md lists auth endpoints (`/auth/login`, `/auth/register`) with different structure, mentions `/api/data-health` (different from `/api/v1/data-health`).

**Decision:** **Both retained** — Different audiences (English vs Persian) and slightly different content.

**Rationale:** Bilingual documentation serves different user segments. No content conflicts that require merging.

---

### 2.3 Set 3: Core Services

**Files:**
- `08_core_services.md` (16.1 KB) — Detailed English documentation of 7 core services: DependencyContainer, ConfigService, LoggerService, CacheService, DatabaseService, HealthChecker, plus SchedulerService
- `12_core_services.md` (2.1 KB) — Brief stub listing 9 core services, including RateLimiterService and ErrorHandlerService (not in 08)

**Content overlap:**
Both describe Tier 1 core services. 08 is detailed and authoritative. 12 adds RateLimiterService and ErrorHandlerService which are not documented in 08 but exist in the codebase (middleware: RateLimitMiddleware, global exception handlers in main.py).

**Decision:** **Both retained** — 08 is the primary document; 12 supplements with 2 additional services.

**Rationale:** 12 provides coverage of RateLimiterService and ErrorHandlerService that 08 misses. Both contain useful, non-overlapping information.

---

### 2.4 Set 4: ML Services

**Files:**
- `11_ml_services.md` (2.6 KB) — Brief ML overview, lists 8 services, notes duplicate 8th entry (TimeSeriesForecastingService appears twice)
- `13_ml_services.md` (2.5 KB) — More detailed ML documentation with mermaid architecture diagram, lists 8 services

**Content overlap:**
Both list the same 8 ML services: CoefficientLearningService, SignalGenerationService, SignalVerificationService, ModelTrainingService, ModelPredictionService, BacktestingService, TimeSeriesForecastingService, EnsembleService. 13 includes an architecture diagram and notes the service dependencies.

**Decision:** **Both retained** — 11 is a brief overview; 13 has the architecture diagram.

**Rationale:** 13 is more comprehensive with the architecture diagram. Both are small enough to keep separately.

---

### 2.5 Set 5: Architecture Design

**Files:**
- `02_architecture_design.md` (20.5 KB) — Comprehensive architecture: 9-tier design, principles, communication patterns, data flow, security
- `system/architecture.md` (5.5 KB) — Brief system architecture overview with component descriptions

**Content overlap:**
Both describe the system architecture. 02 covers design principles, 9-tier service architecture, communication patterns. system/architecture covers system components and data flow more briefly.

**Decision:** **Both retained** — 02 for design principles; system/architecture for component-level overview.

**Rationale:** Different levels of detail and different focus areas. No exact duplication of unique content.

---

### 2.6 Set 6: Database Schema

**Files:**
- `06_database_schema.md` (16.3 KB) — PostgreSQL schema: `assets`, `price_candles`, `order_books`, `users`, `portfolios`, etc. Migration structure with Alembic.
- `database/database_schema_documentation.md` (19.8 KB) — MySQL-style schema: `STOCKS`, `MARKET_DATA`, `USERS`, `PORTFOLIO`, etc. Different table names and structure.

**Content overlap:**
None — these describe fundamentally different schema designs. 06 is the current active PostgreSQL schema. database_schema_documentation appears to be from an older design using MySQL conventions.

**Decision:** **Both retained** — 06 is the primary active schema; database_schema_documentation is kept as a historical reference, archived as `DB_schema_supplemental_v1.md`.

**Rationale:** 06 matches the actual current `models.py` SQLAlchemy definitions (PostgreSQL, UUID primary keys, NASDAQ-only). database_schema_documentation is a divergent historical schema.

---

### 2.7 Set 7: Frontend Documentation

**Files:**
- `17_frontend.md` (1.3 KB) — 48-line stub with minimal frontend overview
- `frontend/FrontEnd.md` (622 B) — 12-line stub listing frontend pages
- `frontend/FrontEnd_display_documentation.md` (2.9 KB) — Comprehensive frontend page documentation (12 pages)

**Content overlap:**
17 and FrontEnd.md are both minimal stubs. FrontEnd_display_documentation.md is the most comprehensive, covering all 12 pages with descriptions, routing, UI/UX considerations.

**Decision:** **FrontEnd_display_documentation.md is the primary**; 17 and FrontEnd.md are archived as stubs.

**Rationale:** FrontEnd_display_documentation.md subsumes both stubs. The stubs contained no unique information but are preserved (archived) for historical reference.

---

### 2.8 Set 8: Planning Stubs

**Files:**
- `planning/ANALYSIS_SUMMARY.md` (154 B) — 5-line placeholder
- `planning/ANALYSIS_INDEX.md` (154 B) — 5-line placeholder (identical content)
- `planning/Source_Within.md` (154 B) — 5-line placeholder (identical content)

**Content overlap:**
All three files contain identical 5-line placeholder text: "Planning Document" with no substantive content.

**Decision:** **All 3 archived** — Consolidated as separate archived stubs in `10_planning/`.

**Rationale:** No content to merge. All are empty placeholders with no original content.

---

## 3. Files Requiring Post-Merge Cleanup

| File | Recommendation | Rationale |
|------|----------------|-----------|
| `ARCH_core-services-supplement_v1.md` | Consider merging into `ARCH_core-services_v1.md` | Supplement adds only 2 services |
| `SERVICES_ml-tier4-supplement_v1.md` | Consider merging into `SERVICES_ml-tier4_v1.md` | Supplement has architecture diagram, no conflicting content |
| All `PLAN_analysis-*.md` stubs | Recommend deletion | 5-line empty placeholders with no content |

---

*End of DUPLICATES_REMOVAL_REPORT.md*
