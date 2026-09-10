# BedaanWaves — Structure Map

> Last updated: 2026-09-10 | Version: 3.0.0 (Post-Cleanup v2)

## Overview

BedaanWaves is a unified capital market platform with a FastAPI backend (Python 3.11) and Next.js frontend (TypeScript). This document describes the final file and directory structure after comprehensive cleanup and reorganization.

---

## Top-Level Structure

```
BedaanWaves/
├── README.md                  # Setup instructions and project overview
├── STRUCTURE.md               # This structure map
├── MIGRATION.md               # Migration guide for team
├── .env.template              # Environment variable template
├── .env.example               # Legacy example
├── .gitignore                 # Comprehensive ignore rules
├── .gitleaks.toml             # Secret scanning configuration
├── conftest.py                # Pytest configuration for root
├── kilo.json                  # Kilo configuration
├── package.json               # Root npm config (for npm run dev)
├── package-lock.json          # Lock file
│
├── backend/                   # FastAPI backend
│   ├── app/                   # Application code
│   │   ├── api/               # API routes
│   │   ├── core/              # Core configuration
│   │   ├── db/                # Database models & sessions
│   │   ├── domain/            # Domain layer (DDD)
│   │   ├── gateway/           # API gateway
│   │   ├── infrastructure/    # Infrastructure implementations
│   │   ├── models/            # Data models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic services
│   │   └── tests/             # Backend tests
│   ├── database/              # Alembic migrations
│   ├── scripts/               # Backend utility scripts
│   ├── tests/                 # Integration tests
│   ├── alembic.ini            # Alembic configuration
│   ├── mypy.ini               # MyPy configuration
│   ├── pyproject.toml         # Project configuration
│   ├── pytest.ini             # Pytest configuration
│   ├── requirements.lock      # Lock file
│   ├── requirements.txt       # Python dependencies
│   ├── ruff.toml              # Ruff configuration
│   ├── .env.example           # Backend environment template
│   ├── data/                  # Data directory (.gitkeep)
│   ├── logs/                  # Application logs (.gitkeep)
│   ├── static/                # Static files
│   └── temp/                  # Temp directory (.gitkeep)
│
├── frontend/                  # Next.js frontend
│   ├── src/
│   │   ├── app/               # App Router pages
│   │   ├── components/        # React components
│   │   └── lib/               # Utilities and helpers
│   ├── public/                # Static assets
│   ├── .env.local             # Frontend environment
│   ├── eslint.config.mjs      # ESLint config
│   ├── middleware.ts          # Next.js middleware
│   ├── next.config.ts         # Next.js config
│   ├── next-env.d.ts          # Next.js env types
│   ├── package.json           # Node.js dependencies
│   ├── package-lock.json      # Lock file
│   ├── playwright.config.ts   # Playwright config
│   ├── postcss.config.mjs     # PostCSS config
│   ├── tsconfig.json          # TypeScript config
│   └── vitest.config.ts       # Vitest config
│
├── docs/                      # Documentation
│   ├── USER_GUIDE.md          # End-user guide
│   ├── 01_overview/           # Overview documents
│   ├── 02_architecture/       # Architecture deep-dives
│   ├── 03_technology/         # Technology docs
│   ├── 04_services/           # Service documentation
│   ├── 05_api/                # API reference
│   ├── 06_database/           # Database documentation
│   ├── 07_configuration/      # Configuration guides
│   ├── 08_frontend/           # Frontend documentation
│   ├── 09_observability/      # Monitoring docs
│   ├── adr/                   # Architecture Decision Records
│   └── runbooks/              # Operational runbooks
│
├── deployment/                # Deployment configurations
│   ├── ansible/               # Ansible playbooks
│   ├── kafka/                 # Kafka configuration
│   ├── kong/                  # Kong configuration
│   └── k8s/                   # Kubernetes manifests
│
├── scripts/                   # Utility scripts
│   ├── backfill_news.py       # Data backfill utility
│   ├── run_backend.py         # Backend runner
│   ├── setup.ps1              # Windows setup
│   ├── setup.sh               # Linux/macOS setup
│   └── verify_no_mock_data.py # Quality gate verification
│
├── database/                  # Database scripts
│   └── init_nasdaq.sql        # NASDAQ initialization
│
├── monitoring/                # Monitoring configurations
│   ├── alertmanager/          # Alertmanager config
│   ├── elk/                   # ELK stack config
│   ├── grafana/               # Grafana dashboards
│   ├── jaeger/                # Jaeger config
│   ├── opentelemetry/         # OpenTelemetry config
│   └── prometheus/            # Prometheus config
│
├── backups/                   # Current backup configs
│   ├── postgresql_conf_recommendations.conf
│   ├── postgresql_conf_tuning.sql
│   └── MIGRATION_SUMMARY.txt
│
├── archive/                   # Archived historical files
│   ├── backups_old/           # Historical backup SQL files
│   ├── purification_migration/ # Data purification tooling
│   ├── project_closure_docs/  # Project closure deliverables
│   ├── legacy_docs/           # Legacy documentation
│   └── planning_docs/         # Planning documents
│
└── .github/                   # GitHub workflows
    └── workflows/              # CI/CD workflows
```

---

## Key Conventions

- **Naming**: kebab-case for directories, snake_case for Python files, camelCase for TypeScript
- **Depth**: Maximum 5 levels from root to any file
- **Layering**: Presentation → Business → Data → Infrastructure
- **Co-location**: Related files stored together (tests next to source, configs near usage)
- **Gitignore**: All generated/cache/secret files excluded from version control

---

## Migration Notes

During cleanup (2026-09-10), the following changes were made:

| Change | From | To |
|--------|------|----|
| Removed binary installers | `database/pginst*.exe`, `pginst_extracted/` | Deleted |
| Removed duplicate models | `models/` (root) | Deleted (duplicate of `backend/models/`) |
| Archived old backups | `backups/*.sql` | `archive/backups_old/` |
| Archived purification | `purification/` | `archive/purification_migration/` |
| Archived closure docs | `docs/project_closure/` | `archive/project_closure_docs/` |
| Archived legacy docs | `docs/11_legacy/` | `archive/legacy_docs/` |
| Archived planning docs | `docs/10_planning/` | `archive/planning_docs/` |
| Removed root temp scripts | 18 `.py` files in root | Deleted |
| Removed backend/ test files | 14 `test_*.py` in backend/ root | Deleted |
| Removed backend/ debug scripts | 19 `debug_*.py` in backend/ root | Deleted |
| Removed backend/ debug txt | 12 `.txt` files in backend/ root | Deleted |
| Removed backend/ csv data | 2 `.csv` files in backend/ root | Deleted |
| Removed scripts/ diagnostics | 6 one-off scripts | Deleted |
| Removed cache artifacts | `__pycache__/`, `*.pyc`, `*.log` | Deleted |
| Consolidated env files | `.env` (with secrets) | Deleted; use `.env.template` |
| Moved runner | `backend/run.py` | `scripts/run_backend.py` |