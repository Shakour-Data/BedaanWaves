# BedaanWaves - Capital Market Analysis Platform

Unified platform consolidating 5 legacy projects into a single optimized system.

**Status**: Phase 3 (35% Complete) | **Commits**: 10 | **LOC**: 3,680+

## Quick Links

- 📚 [Documentation](docs/README.md)
- 🎯 [Development Guide](docs/AGENTS.md)
- 🤖 [Claude Instructions](docs/CLAUDE.md)
- 📊 [Progress](docs/REWRITE_PROGRESS.md)

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy
- **Frontend**: Next.js 16+ React
- **Database**: PostgreSQL (local)
- **Python**: 3.11+
- **No Docker**: Local development only

## Completed

✅ Tier 1: Core Services (6 services, 1,270 LOC)
✅ Tier 2: Data Services (6 services, 930 LOC)
✅ Tier 3: Analysis Services (6 services, 1,480 LOC)

## Features

- 50+ Technical Indicators
- 20+ Financial Ratios
- 15+ Risk Metrics
- 305-node 6D Scoring System
- 100+ Configuration Settings

## Setup

```bash
# Backend setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Database
createdb bedaanwaves

# Run backend
python -m uvicorn app.main:app --reload
```

See [docs/README.md](docs/README.md) for full documentation.

---

**Last Updated**: 2026-07-09  
**Phase**: 3 (Services Implementation)  
**Next**: Tier 4-9 implementation
