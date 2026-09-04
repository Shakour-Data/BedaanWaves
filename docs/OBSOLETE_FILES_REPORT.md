# Obsolete Files Report

> **Phase 3 Output** — Archive and deletion recommendations for obsolete, stub, and superseded documentation files.

**Analysis Date:** 2026-09-04  
**Files Archived (moved to `11_legacy/`):** 6  
**Files Flagged for Deletion (stubs):** 6  
**Files Flagged for Review:** 3  
**Total Files Handled:** 15  

---

## 1. Summary Table

| # | Original File | Size | Category | Action Taken | Recommendation |
|---|---------------|------|----------|--------------|----------------|
| 1 | `planning/ANALYSIS_SUMMARY.md` | 154 B | Stub | Archived to `10_planning/PLAN_analysis-summary_v1.md` | **DELETE** — Empty 5-line placeholder |
| 2 | `planning/ANALYSIS_INDEX.md` | 154 B | Stub | Archived to `10_planning/PLAN_analysis-index_v1.md` | **DELETE** — Empty 5-line placeholder |
| 3 | `planning/Source_Within.md` | 154 B | Stub | Archived to `10_planning/PLAN_source-within_v1.md` | **DELETE** — Empty 5-line placeholder |
| 4 | `api/postgre.md` | 230 B | Stub | Archived to `05_api/API_postgre-config_ARCHIVED_v1.md` | **DELETE** — 6-line placeholder |
| 5 | `17_frontend.md` | 1.3 KB | Stub | Archived to `08_frontend/FE_frontend-overview_v1.md` | Consider **DELETE** — Superseded by `FE_display-documentation_v1.md` |
| 6 | `frontend/FrontEnd.md` | 622 B | Stub | Archived to `08_frontend/FE_legacy-frontend_v1.md` | Consider **DELETE** — 12-line stub, no unique content |

| 7 | `docs/architecture/ARCHITECTURE_ANALYSIS.md` | 19.5 KB | Historical | Archived to `11_legacy/LEGACY_architecture-analysis_v1.md` | **KEEP archived** — OldFils 5-project analysis (reference only) |
| 8 | `docs/architecture/ARCHITECTURE_DETAILS.md` | 32.8 KB | Historical | Archived to `11_legacy/LEGACY_architecture-details_v1.md` | **KEEP archived** — July 2026 planning document |
| 9 | `docs/architecture/BEDAANWAVES_REWRITE_STRATEGY.md` | 13.6 KB | Historical | Archived to `11_legacy/LEGACY_rewrite-strategy_v1.md` | **KEEP archived** — Rewrite strategy document |
| 10 | `docs/architecture/DATABASE_CRITICALITY_UPGRADE_PLAN.md` | 25.9 KB | Historical | Archived to `11_legacy/LEGACY_database-upgrade_v1.md` | **KEEP archived** — Database upgrade plan |
| 11 | `docs/integration/INTEGRATION_FRAMEWORK.md` | 49.6 KB | Historical | Archived to `11_legacy/LEGACY_integration-framework_v1.md` | **KEEP archived** — Labeled "HISTORICAL DOCUMENT" in source |
| 12 | `docs/project_documentation/index.html` | 50.5 KB | Legacy | Archived to `11_legacy/LEGACY_project-documentation.html` | **KEEP archived** — Standalone HTML documentation bundle |

| 13 | `04_service_catalog.md` | 20.3 KB | Redundant | Moved to `04_services/SERVICES_catalog_v1.md` | Review — Contains summary info overlapping with `018` and `02`, but adds service descriptions not found elsewhere |
| 14 | `REDIS_SETUP.md` (duplicate at root) | 6.4 KB | Duplicate | Moved to `02_architecture/ARCH_deployment-redis_v1.md` | **DELETE original** — Replaced by moved version |
| 15 | `12_core_services.md` | 2.1 KB | Stub/Partial | Moved to `02_architecture/ARCH_core-services-supplement_v1.md` | Review — Adds 2 services (RateLimiterService, ErrorHandlerService) not in `08_core_services.md` |

---

## 2. Detailed Recommendations

### 2.1 Stub Files Recommended for Deletion (6 files)

These files contain minimal content (under 2 KB) with no unique information. They serve as placeholders only.

1. **`PLAN_analysis-summary_v1.md`** (154 B) — "Planning Document" placeholder
2. **`PLAN_analysis-index_v1.md`** (154 B) — Identical placeholder
3. **`PLAN_source-within_v1.md`** (154 B) — Identical placeholder
4. **`API_postgre-config_ARCHIVED_v1.md`** (230 B) — 6-line stub
5. **`FE_frontend-overview_v1.md`** (1.3 KB) — Minimal overview, superseded
6. **`FE_legacy-frontend_v1.md`** (622 B) — 12-line listing, no unique content

> **Note:** Per the project rules, these files were archived (not deleted). Approval is required before removal.

### 2.2 Historical Documents to Keep Archived (6 files)

These files are explicitly labeled as historical or contain planning information from before the current implementation.

1. **`LEGACY_architecture-analysis_v1.md`** — OldFils 5-project analysis. Contains useful context for understanding the 4 projects that were consolidated.
2. **`LEGACY_architecture-details_v1.md`** — July 2026 technical specs. Contains an *older* database schema with international market support that contradicts current code (NASDAQ-only). **Flagged for code-alignment** in CODE_DOCS_MISMATCH_REPORT.md.
3. **`LEGACY_rewrite-strategy_v1.md`** — Rewrite strategy for 5 OldFils projects. Useful for understanding migration history.
4. **`LEGACY_database-upgrade_v1.md`** — Database criticality upgrade plan. Contains migration planning notes.
5. **`LEGACY_integration-framework_v1.md`** — Self-labeled "HISTORICAL DOCUMENT" (July 2026). Contains strategic planning with outdated assumptions.
6. **`LEGACY_project-documentation.html`** — Standalone HTML bundle. May contain useful reference but is not integrated into the markdown structure.

### 2.3 Files Flagged for Review (3 files)

| File | Review Notes |
|------|-------------|
| `SERVICES_catalog_v1.md` | Contains service descriptions that partially overlap with `OVERVIEW_implementation-status_v1.md` and `ARCH_architecture-design_v1.md`. Consider consolidating key service summaries into `SERVICES_catalog_v1.md` and removing redundant mentions from overview docs. |
| `ARCH_core-services-supplement_v1.md` | Adds RateLimiterService and ErrorHandlerService not documented in the primary `ARCH_core-services_v1.md`. These services **do exist** in the code (middleware: `RateLimitMiddleware`; handlers in `main.py`). **Recommendation:** Merge the supplemental content into the primary core services doc. |
| `SERVICES_ml-tier4-supplement_v1.md` | Contains an architecture diagram and service descriptions with no conflicts. **Recommendation:** Merge into `SERVICES_ml-tier4_v1.md` as an "Architecture" section. |

---

## 3. Superseded Content Mapping

| Original File | Superseded By | Notes |
|---------------|---------------|-------|
| `17_frontend.md` | `FE_display-documentation_v1.md` | Display documentation is more comprehensive |
| `frontend/FrontEnd.md` | `FE_display-documentation_v1.md` | Same content, more detail in display doc |
| `REDIS_SETUP.md` (duplicate) | `ARCH_deployment-redis_v1.md` | Same file, moved location |
| `system/architecture.md` | `ARCH_architecture-design_v1.md` | Brief summary, kept alongside comprehensive doc |

---

## 4. Files NOT Recommended for Deletion

| File | Reason to Keep |
|------|----------------|
| `FE_frontend-overview_v1.md` | Despite being a stub, provides a high-level entry point. Consider keeping or enhancing. |
| `SERVICES_ml-tier4-supplement_v1.md` | Architecture diagram is valuable. Merge recommendation only. |
| `DB_schema_supplemental_v1.md` | Historical MySQL schema provides useful comparison reference. |

---

*End of OBSOLETE_FILES_REPORT.md*
