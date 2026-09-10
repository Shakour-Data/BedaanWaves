# BedaanWaves — Migration Guide for Team

> Version: 1.0.0 | Date: 2026-09-11

This guide explains the file structure changes from the previous state to the current organized structure.

---

## What Changed

### 1. Root Directory Cleanup

**Removed:**
- `.env` (contained hardcoded secrets — now replaced with `.env.template`)
- `.env.example` (duplicate of `.env.template`)
- `.trae/` (AI tool artifacts — not needed in repo)
- `.snyk/` (Snyk config — not needed in repo)
- Root-level `.py` scripts (audit_analyze.py, audit_deep.py, conftest.py — moved or deleted)
- `kilo.json` (tool config — kept, not deleted)

**Kept:**
- `README.md`, `STRUCTURE.md`, `MIGRATION.md`
- `.env.template`, `.gitignore`, `.gitleaks.toml`
- `package.json`, `package-lock.json`
- `conftest.py` (root pytest config)

### 2. Backend Cleanup

**Removed:**
- All `__pycache__/` directories and `*.pyc` files (47 directories, 102 files)
- `backend/logs/*.log` (active log files — moved to `archive/backups_old/` if locked)
- `backend/.env` (contained secrets — now gitignored, use `backend/.env.example`)
- `backend/.env.example` (duplicate)
- Duplicate ML artifacts: `aspects_features.joblib`, `sub_aspects_features.joblib`, `sub_dimensions_features.joblib` (3 files, identical content)
- Duplicate ML artifacts: `aspects_scaler.joblib`, `sub_aspects_scaler.joblib`, `sub_dimensions_scaler.joblib` (3 files, identical content)
- Duplicate config: `aspects_coefficients.json`, `sub_aspects_coefficients.json` (2 files, identical content)

**Kept:**
- `backend/app/` (application code)
- `backend/database/` (Alembic migrations)
- `backend/scripts/` (utility scripts)
- `backend/tests/` (integration tests)
- `backend/data/`, `backend/logs/`, `backend/static/`, `backend/temp/` (with `.gitkeep` files)

### 3. Frontend Cleanup

**Removed:**
- `frontend/node_modules/` (dependencies — should be in `.gitignore`, not in repo)
- `frontend/.next/` (build output — should be in `.gitignore`, not in repo)
- `frontend/playwright-browsers/` (test browsers — should be in `.gitignore`, not in repo)
- `frontend/playwright-report/` (test reports — should be in `.gitignore`, not in repo)

**Kept:**
- `frontend/src/` (application source)
- `frontend/public/` (static assets)
- `frontend/*.config.*` (configuration files)
- `frontend/package.json`, `frontend/package-lock.json`

### 4. Documentation Cleanup

**Removed:**
- `docs/architecture_improvement_report.md` (superseded)
- `docs/architecture_improvement_report_v2.md` (superseded)
- `docs/CODE_DOCS_MISMATCH_REPORT.md` (superseded)
- `docs/data-flow-analysis-report.md` (superseded)
- `docs/VALIDATION_REPORT_FINAL.md` (superseded)
- `docs/INTEGRATION_AUDIT_REPORT.md` (superseded)
- `docs/AUDIT_REPORT.md` (superseded)
- `docs/security-privacy-report.md` (superseded)
- `docs/UX-AUDIT-analytical.md` (superseded)
- `docs/spec.yaml` (superseded)

**Kept:**
- `docs/USER_GUIDE.md`
- `docs/01_overview/` through `docs/09_observability/`
- `docs/adr/` (Architecture Decision Records)
- `docs/runbooks/`

### 5. Archive Cleanup

**Removed:**
- `archive/planning_docs/PLAN_analysis-index_v1.md` (empty file)
- `archive/planning_docs/PLAN_analysis-summary_v1.md` (empty file)
- `archive/planning_docs/PLAN_source-within_v1.md` (empty file)
- `archive/legacy_docs/LEGACY_project-documentation.html` (legacy HTML)

**Kept:**
- `archive/backups_old/` (historical SQL files)
- `archive/purification_migration/` (data purification tooling)
- `archive/project_closure_docs/` (project closure deliverables)
- `archive/legacy_docs/` (legacy documentation)
- `archive/planning_docs/` (planning documents)

---

## How to Update Your Code

### If you had imports like:
```python
from models.coefficients.aspects_features import load_features
```

**Update to:**
```python
from backend.models.coefficients.dimensions_features import load_features
```

### If you had references to:
```
backend/logs/bedaanwaves_20260909.log
```

**Update to:**
```
backend/logs/.gitkeep  # Log files are gitignored, use .gitkeep for directory
```

### If you had environment variables in:
```
backend/.env
```

**Update to:**
```
backend/.env.example  # Copy this to backend/.env and fill in real values
```

---

## Verification Checklist

After applying these changes, verify:

- [ ] No `__pycache__` directories exist
- [ ] No `.pyc` files exist
- [ ] No `.env` files contain real secrets
- [ ] `.gitignore` is updated
- [ ] `STRUCTURE.md` reflects current state
- [ ] `README.md` is updated
- [ ] `MIGRATION.md` is updated
- [ ] All duplicate files are removed
- [ ] All empty directories are removed
- [ ] All temporary files are removed

---

## Support

For questions about these changes, contact the DevOps team or check the `docs/` directory for detailed documentation.