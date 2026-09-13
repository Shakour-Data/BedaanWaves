# BedaanWaves Documentation — Navigation Map

> **Quick Start:** Jump to [Section 01 — Overview](#01-overview) for executive summaries, or [Section 02 — Architecture](#02-architecture) for system design.

---

## New Folder Structure

```
docs/
├── README.md                              ← This file (navigation map)
│
├── 01_overview/                          → Project summaries, status, planning
│   ├── OVERVIEW_executive-summary_v1.md    # Merged: 01_executive_overview.md
│   ├── OVERVIEW_implementation-status_v1.md # Merged: 018_implementation_status_report.md
│   ├── OVERVIEW_project-plan_v1.md         # Merged: MASTER_PLAN.md
│   └── OVERVIEW_agent-reference_v1.md      # From AGENTS.md
│
├── 02_architecture/                      → System architecture & diagrams
│   ├── ARCH_architecture-design_v1.md      # From 02_architecture_design.md
│   ├── ARCH_system-architecture_v1.md      # From system/architecture.md
│   ├── ARCH_core-services_v1.md            # Merged: 08_core_services.md
│   ├── ARCH_core-services-supplement_v1.md # From 12_core_services.md
│   ├── ARCH_deployment-windows_v1.md       # From NATIVE_WINDOWS_SETUP.md
│   ├── ARCH_deployment-redis_v1.md         # From REDIS_SETUP.md
│   ├── ARCH_ecosystem-diagram_v1.png       # Architecture diagram
│   ├── ARCH_uml-level{1-6}_v1.md           # UML diagrams (consolidated from diagrams/uml/)
│   ├── ARCH_dfd-level{1-6}_v1.md           # DFD diagrams (consolidated from diagrams/dfd/)
│   ├── ARCH_bpmn-level{1-6}_v1.md          # BPMN diagrams (consolidated from diagrams/bpmn/)
│   └── ARCH_{uml,dfd,bpmn}-readme_v1.md    # Diagram section READMEs
│
├── 03_technology/                        → Technology stack & design system
│   ├── TECH_stack_v1.md                    # From 03_technology_stack.md
│   └── TECH_style-guide_v1.md              # From STYLE_GUIDE.md
│
├── 04_services/                          → Service catalog by tier
│   ├── SERVICES_catalog_v1.md              # From 04_service_catalog.md
│   ├── SERVICES_data-tier2_v1.md           # From 09_data_services.md
│   ├── SERVICES_analysis-tier3_v1.md       # From 10_analysis_services.md
│   ├── SERVICES_analysis_{ai,fundamental,macro risk,technical}_v1.md # From analysis/
│   ├── SERVICES_ml-tier4_v1.md             # From 11_ml_services.md
│   ├── SERVICES_ml-tier4-supplement_v1.md  # From 13_ml_services.md
│   ├── SERVICES_nlp-tier5_v1.md            # From 14_nlp_services.md
│   ├── SERVICES_nlp_sentiment_v1.md        # From analysis/sentiment_analysis.md
│   ├── SERVICES_specialized-tier7_v1.md    # From 16_specialized_services.md
│   └── SERVICES_catalog_v1.md              # Service inventory
│
├── 05_api/                               → API documentation
│   ├── API_reference_v1.md                 # From 05_api_documentation.md
│   ├── API_reference-persian_v1.md         # From API_DOCUMENTATION.md
│   ├── API_dashboard-charts_v1.md          # From dashboard-charts-spec.md
│   └── API_postgre-config_ARCHIVED_v1.md   # Archived stub from api/postgre.md
│
├── 06_database/                          → Database documentation
│   ├── DB_schema_v1.md                     # From 06_database_schema.md (PostgreSQL)
│   ├── DB_schema_supplemental_v1.md        # From database/database_schema_documentation.md
│   └── DB_design-system-checklist_v1.md    # From design-system-audit-checklist.md
│
├── 07_configuration/                     → Configuration guides
│   └── CONFIG_guide_v1.md                  # From 07_configuration_guide.md
│
├── 08_frontend/                          → Frontend documentation
│   ├── FE_frontend-overview_v1.md          # From 17_frontend.md
│   ├── FE_legacy-frontend_v1.md            # From frontend/FrontEnd.md
│   ├── FE_display-documentation_v1.md      # From frontend/FrontEnd_display_documentation.md
│   ├── FE_page-{alerts,analysis,dashboard,help,login,methodology,news,portfolio,register,stock,watchlist}_v1.md
│   ├── FE_password-recovery-architecture_v1.md  # From 18_password_recovery_architecture.md
│   └── FE_password-recovery-audit_v1.md    # From 19_password_recovery_audit.md
│
├── 09_observability/                     → Testing & monitoring
│   ├── OBS_integration-readme_v1.md        # From integration/README_INTEGRATION.md
│   └── OBS_test-coverage_v1.md             # From system/testcoverage.md
│
├── 10_planning/                          → Planning & tracking (some archived)
│   ├── PLAN_implementation-checklist_v1.md # From planning/IMPLEMENTATION_CHECKLIST.md
│   ├── PLAN_rewrite-progress_v1.md         # From planning/REWRITE_PROGRESS.md
│   ├── PLAN_todo_v1.md                     # From planning/TODO.md
│   └── PLAN_{analysis-summary,analysis-index,source-within}_v1.md # Archived stubs from planning/
│
├── 11_legacy/                            → Archived historical documents
│   ├── LEGACY_integration-framework_v1.md  # From integration/INTEGRATION_FRAMEWORK.md
│   ├── LEGACY_architecture-analysis_v1.md  # From architecture/ARCHITECTURE_ANALYSIS.md
│   ├── LEGACY_architecture-details_v1.md   # From architecture/ARCHITECTURE_DETAILS.md
│   ├── LEGACY_rewrite-strategy_v1.md       # From architecture/BEDAANWAVES_REWRITE_STRATEGY.md
│   ├── LEGACY_database-upgrade_v1.md       # From architecture/DATABASE_CRITICALITY_UPGRADE_PLAN.md
│   └── LEGACY_project-documentation.html   # From project_documentation/index.html
│
├── — Root-level reports (Phase 1-5 deliverables)
│   ├── INVENTORY.md                        # Phase 1: Full file inventory
│   ├── DUPLICATES_REMOVAL_REPORT.md        # Phase 2: Merge decisions
│   ├── OBSOLETE_FILES_REPORT.md          # Phase 3: Archive/delete recommendations
│   ├── CODE_DOCS_MISMATCH_REPORT.md        # Phase 5: Code-doc alignment
│   └── PROJECT_DOCS_STATUS.md             # Final summary & health score
│
└── AGENTS.md                              # Kept at docs root for Kilo tooling
```

---

## Quick Reference by Topic

| You Need To Know... | Go To |
|---------------------|-------|
| Is the project production-ready? | `01_overview/OVERVIEW_implementation-status_v1.md` |
| What services exist by tier? | `02_architecture/ARCH_architecture-design_v1.md` and `04_services/SERVICES_catalog_v1.md` |
| How does the 9-tier service architecture work? | `01_overview/OVERVIEW_executive-summary_v1.md` |
| What are the API endpoints? | `05_api/API_reference_v1.md` (English) / `05_api/API_reference-persian_v1.md` (Persian) |
| Database schema & tables? | `06_database/DB_schema_v1.md` |
| Environment variables? | `07_configuration/CONFIG_guide_v1.md` |
| Password recovery (FSM/audit)? | `08_frontend/FE_password-recovery-{architecture,audit}_v1.md` |
| Technology stack? | `03_technology/TECH_stack_v1.md` |
| Style guide & design tokens? | `03_technology/TECH_style-guide_v1.md` |
| Run on Windows? | `02_architecture/ARCH_deployment-windows_v1.md` |
| Set up Redis? | `02_architecture/ARCH_deployment-redis_v1.md` |
| Test coverage targets? | `09_observability/OBS_test-coverage_v1.md` |
| Diagram reference (UML/DFD/BPMN)? | `02_architecture/ARCH_{uml,dfd,bpmn}-readme_v1.md` |

---

## Naming Convention

All files follow the pattern: **`[SECTION]_[TOPIC]_[VERSION].md`**

| Component | Examples |
|-----------|----------|
| SECTION | `OVERVIEW`, `ARCH`, `TECH`, `SERVICES`, `API`, `DB`, `CONFIG`, `FE`, `OBS`, `PLAN`, `LEGACY` |
| TOPIC | Descriptive topic (`architecture-design`, `core-services`, `stack`, `data-tier2`, `reference`, `schema`, `guide`, `frontend-overview`) |
| VERSION | `v1`, `v2`, etc. |

**Archived/obsolete files** carry `ARCHIVED` in the topic and are stored in `11_legacy/` or flagged in `OBSOLETE_FILES_REPORT.md`.
