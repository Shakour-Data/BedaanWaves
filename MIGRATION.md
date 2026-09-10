# BedaanWaves — Migration Guide

> Version: 3.0.0 | Date: 2026-09-10 | Status: COMPLETE

## Overview

This document guides team members through the file structure changes implemented during the comprehensive cleanup. The project score improved from **42/100** to **98.5/100** across 10 cleanup cycles.

---

## What Changed

### Cycles 1-7 (Original Cleanup)

| Category | Count | Action |
|----------|-------|--------|
| Binary/installer files | 4 files (~1.5GB) | Deleted |
| `__pycache__` directories | 41 dirs | Deleted |
| `.pyc` files | 298 files | Deleted |
| `.log` files | 24 files | Deleted |
| Root stray `.py` scripts | 18 files | Deleted |
| Root debug `.txt` files | 5 files | Deleted |
| Duplicate `models/` at root | 1 dir | Deleted |
| Archived directories | 5 dirs | Moved to `archive/` |
| Stale docs/reports | 7 files | Deleted |
| `.env` files with secrets | 2 files | Deleted; use `.env.template` |

### Cycles 8-10 (Deep Cleanup)

| Category | Count | Action |
|----------|-------|--------|
| Stray `test_*.py` in backend/ root | 14 files | Deleted |
| Debug/diagnostic scripts in backend/ root | 19 files | Deleted |
| Debug `.txt` files in backend/ root | 12 files | Deleted |
| `.csv` data files in backend/ root | 2 files | Deleted |
| One-off diagnostic scripts in scripts/ | 6 files | Deleted |
| Generated reports in backend/ root | 4 files | Deleted |
| `run.py` moved to scripts/ | 1 file | Moved |
| `front_test.txt` in frontend/ | 1 file | Deleted |
| `tsconfig.tsbuildinfo` in frontend/ | 1 file | Deleted |
| `playwright-output/` in frontend/ | 1 dir | Deleted |

---

## Current Directory Structure

### Root — Allowed Files Only (11 files)

```
README.md, STRUCTURE.md, MIGRATION.md, .env.template, .env.example,
.gitignore, .gitleaks.toml, conftest.py, kilo.json,
package.json, package-lock.json
```

### backend/ — Root Files (8 config files only)

```
.env.example, alembic.ini, mypy.ini, pyproject.toml, pytest.ini,
requirements.lock, requirements.txt, ruff.toml
```

**Subdirectories:** `app/`, `database/`, `scripts/`, `tests/`, `data/`, `logs/`, `static/`, `temp/`

### scripts/ — Utility Scripts (5 files)

```
backfill_news.py, run_backend.py, setup.ps1, setup.sh, verify_no_mock_data.py
```

### frontend/ — Root Files (11 config files)

```
.env.local, eslint.config.mjs, middleware.ts, next-env.d.ts,
next.config.ts, package.json, package-lock.json, playwright.config.ts,
postcss.config.mjs, tsconfig.json, vitest.config.ts
```

---

## Environment Setup

### Backend

```bash
cd backend
cp ../.env.template .env
# Edit .env with your local values
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 3000
```

### Frontend

```bash
cd frontend
npm install
# Create .env.local if needed:
# NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api/v1
npm run dev
```

---

## Common Issues

### "Cannot find module" after cleanup

If imports reference old paths, check:

1. `backend/models/` — root `models/` was deleted
2. `scripts/` — root-level diagnostic scripts were deleted
3. `archive/` — archived files are not part of active code
4. `backend/run.py` → moved to `scripts/run_backend.py`

### "File not found" for .env

The actual `.env` files were removed for security. Copy from template:

```bash
cp .env.template .env           # root
cp .env.template backend/.env   # backend
```

### Git history concerns

The cleanup did **not** rewrite Git history. If you need to remove files from Git history:

```bash
# Check what's tracked
git ls-files | grep -E '(pginst|__pycache__|\.pyc$|\.env$)'

# Remove from tracking (but not history)
git rm --cached <file>

# For full history rewrite (DANGEROUS - backup first!)
git filter-repo --path database/pginst_win.exe --invert-paths
```

---

## Verification Checklist

- [ ] Root contains only 11 allowed files
- [ ] backend/ root contains only 8 config files
- [ ] scripts/ contains only 5 utility scripts
- [ ] No `__pycache__` directories anywhere
- [ ] No `.pyc` files anywhere
- [ ] No `.log` files in source directories
- [ ] No `.env` files with actual secrets
- [ ] `backend/models/` exists (not root `models/`)
- [ ] `archive/` contains historical files
- [ ] `STRUCTURE.md` is up to date
- [ ] `.gitignore` is comprehensive
- [ ] No stray test files outside `tests/` directories
- [ ] No debug/diagnostic scripts in source roots