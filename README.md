# BedaanWaves - Capital Market Analysis Platform

Unified platform consolidating 5 legacy projects into a single optimized system.

**Status**: Phase 4 (Fundamental Analysis Completion) | **Commits**: 10+ | **LOC**: 17,000+ (backend services)

## Quick Links

- 📚 [Documentation](docs/AGENTS.md)
- 🎯 [Development Guide](docs/AGENTS.md)
- 📋 [Task Tracking](docs/TODO.md)

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy 2.0
- **Frontend**: Next.js 16+ React
- **Database**: PostgreSQL (local)
- **Python**: 3.11+
- **No Docker**: Local development only

## Completed Tiers (1-9)

✅ Tier 1: Core Services (6 services)
✅ Tier 2: Data Services (13 services)
✅ Tier 3: Analysis Services (7 services)
✅ Tier 4: ML Services (9 services)
✅ Tier 5: NLP Services (6 services)
✅ Tier 6: User Services (8 services)
✅ Tier 7: Specialized Services (7 services)
✅ Tier 8: Crypto Services (8 services)
✅ Tier 9: System Services (8 services)

## Features

- 50+ Technical Indicators
- 20+ Financial Ratios (global markets: Iran, US, International)
- 15+ Risk Metrics (VaR, Sharpe, stress testing)
- 305-node 6D Scoring System
- 100+ Configuration Settings
- Multi-language news with sentiment analysis
- Crypto & stock fundamental analysis
- Portfolio optimization with efficient frontier

## Setup

```bash
# Backend setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt  # or: pip install -e .

# Database
createdb bedaanwaves

# Run backend
python -m uvicorn app.main:app --reload --port 3000 --host 0.0.0.0

# Run frontend
cd frontend
npm install
npm run dev
```

See [docs/AGENTS.md](docs/AGENTS.md) for full documentation and development guidelines.

---

**Last Updated**: 2026-07-31  
**Phase**: 4 (Fundamental Analysis Completion)  
**Estimated Completion**: 2 weeks