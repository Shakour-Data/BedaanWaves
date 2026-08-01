# BedaanWaves - Capital Market Analysis Platform

Unified platform consolidating 5 legacy projects into a single optimized system.

**Status**: Phase 6 (Testing & Validation) - **COMPLETE** | **Commits**: 15+ | **LOC**: 22,000+ (backend services)

## Quick Links

- 📚 [Documentation](docs/AGENTS.md)
- 🎯 [Development Guide](docs/AGENTS.md)
- 📋 [Task Tracking](docs/TODO.md)
- 🚀 [Deployment Checklist](docs/deployment_checklist.md)
- 📊 [Phase 6 Test Report](docs/phase6_report.md)

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy 2.0
- **Frontend**: Next.js 16+ React
- **Database**: PostgreSQL (local)
- **Cache**: Redis (optional, memory fallback)
- **Python**: 3.11+
- **No Docker**: Local development only

## Completed Tiers (1-9)

✅ Tier 1: Core Services (6 services) - IoC/DI, Config, Logging, Cache, Database, Health
✅ Tier 2: Data Services (13 services) - BRS API, Stock, Market, Portfolio, History, News, Ingestion, Processing, Intl API, Crypto API, Validation, Financial Ingest, Fundamental Ingest
✅ Tier 3: Analysis Services (7 services) - Scoring (6D/305-node), Technical (50+ indicators), Fundamental (20+ ratios), Risk (VaR/Sharpe), Momentum, Volatility, User-Filtered Scoring
✅ Tier 4: ML Services (9 services) - Prediction, Pattern Recognition, Anomaly Detection, Recommendation, Portfolio Optimization, Time Series, Coefficient Learning, Crypto ML, User-Filtered Recommendation
✅ Tier 5: NLP Services (6 services) - Sentiment, Summarization, Document Extraction, Chatbot, Search, Multi-language News
✅ Tier 6: User Services (8 services) - Auth/JWT, RBAC, Profile/KYC, Watchlist, Preferences, Notifications, Market Settings, Crypto Settings
✅ Tier 7: Specialized Services (7 services) - Sector Analysis, Screening, Comparison, Correlation, Calendar, International Markets, Sector Filter
✅ Tier 8: Crypto Services (8 services) - Price Feeds, Portfolio, Ingestion, ML, Custom Selection, Market Cap Filtering, On-chain Analysis, Arbitrage
✅ Tier 9: System Services (8 services) - Scheduler, Metrics, Queue, Backup, Logging, Notification Dispatcher, Data Integrity, Settings Migration

## Features

- 50+ Technical Indicators
- 20+ Financial Ratios (global markets: Iran, US, International)
- 15+ Risk Metrics (VaR, Sharpe, stress testing)
- 305-node 6D Scoring System
- 100+ Configuration Settings
- Multi-language news with sentiment analysis
- Crypto & stock fundamental analysis
- Portfolio optimization with efficient frontier
- **Structural Break Detection** (Bai-Perron, Chow, Markov)
- **Behavioral Economics** (Noise Trader, Prospect Theory, Survey API)
- **Crypto Industry Classification** (5-tier: Layer→Function→Usage→Risk→Theme)
- **Unified Data Model** (Semantic tags: FLOW/STOCK/NOMINAL/REAL/RATIO)
- **PCA/VIF/Ridge Regularization** for multicollinearity mitigation
- **Shadow Banking Metrics** & **Currency Regime Modeling** (4-state Markov)
- **Regime-Aware Retention** & **Data Lineage Tracking**

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BEDAANWAVES ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │   EXTERNAL   │   │   EXTERNAL   │   │   EXTERNAL   │   │   EXTERNAL   │ │
│  │    APIs      │   │    APIs      │   │    APIs      │   │    APIs      │ │
│  │ (BRS, SEC,   │   │ (CoinGecko,  │   │ (Yahoo,     │   │ (ECB, BLS,   │ │
│  │  AlphaVantage)│   │  Binance)    │   │  FRED)      │   │  IMF)        │ │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘ │
│         │                  │                  │                  │         │
│         ▼                  ▼                  ▼                  ▼         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    INGESTION LAYER (Tier 2)                          │  │
│  │  IntelligentIngestionService ──▶ SchemaRegistry ──▶ DataValidation  │  │
│  │       (async, semaphore)         (versioned)        (quality checks) │  │
│  └────────────────────────────┬────────────────────────────────────────┘  │
│                               │                                           │
│                               ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      DATA LAYER (PostgreSQL + Redis)                 │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │  │ Stocks   │  │ Crypto   │  │ Macro    │  │ News/    │             │  │
│  │  │ Fundamental│  │ Fundamental│  │ Economic │  │ Sentiment│             │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │  │
│  └────────────────────────────┬────────────────────────────────────────┘  │
│                               │                                           │
│         ┌─────────────────────┼─────────────────────┐                    │
│         ▼                     ▼                     ▼                    │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐              │
│  │  ANALYSIS   │      │     ML      │      │   NLP       │              │
│  │  (Tier 3)   │      │  (Tier 4)   │      │  (Tier 5)   │              │
│  ├─────────────┤      ├─────────────┤      ├─────────────┤              │
│  │ • Scoring   │      │ • Predict   │      │ • Sentiment │              │
│  │ • Technical │      │ • Patterns  │      │ • Summary   │              │
│  │ • Fundamental│     │ • Anomaly   │      │ • Chatbot   │              │
│  │ • Risk      │      │ • Optimize  │      │ • Search    │              │
│  │ • Momentum  │      │ • TimeSeries│      │ • Multi-lang│              │
│  │ • Volatility│      │ • CoeffLearn│      │             │              │
│  │ • Structural│      │ • Crypto ML │      │             │              │
│  │ • Behavioral│      │             │      │             │              │
│  └──────┬──────┘      └──────┬──────┘      └──────┬──────┘              │
│         │                    │                    │                      │
│         └────────────────────┼────────────────────┘                      │
│                              ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    SPECIALIZED & USER SERVICES (Tiers 6-9)           │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │  │ Specialized│ │  User    │ │  Crypto  │ │ System   │ │ Cross-   │   │  │
│  │  │  (Tier 7) │ │ (Tier 6) │ │ (Tier 8) │ │ (Tier 9) │ │ Asset    │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │  │
│  └────────────────────────────┬────────────────────────────────────────┘  │
│                               │                                           │
│                               ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        API LAYER (FastAPI)                           │  │
│  │  /api/v1/stocks  /api/v1/crypto  /api/v1/analysis  /api/v1/users    │  │
│  │  /api/v1/portfolio  /api/v1/fundamental  /api/v1/ml  /api/v1/nlp    │  │
│  └────────────────────────────┬────────────────────────────────────────┘  │
│                               │                                           │
│                               ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      FRONTEND (Next.js 16+)                          │  │
│  │  Dashboard │ Portfolio │ Analysis │ Screening │ Settings │ Admin    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Setup

```bash
# Prerequisites
# Python 3.11+
# PostgreSQL running locally on port 5432
# Redis (optional, defaults to memory cache)

# Backend setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -e .  # Install from pyproject.toml

# Environment configuration
# Create .env in backend/ directory:
# ENVIRONMENT=development
# DEBUG=true
# LOG_LEVEL=INFO
# DB_DRIVER=postgresql
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=bedaanwaves
# DB_USER=postgres
# DB_PASSWORD=your_password
# REDIS_URL=redis://localhost:6379/0
# CACHE_BACKEND=memory
# JWT_SECRET=your-secret-key-change-in-production

# Database
createdb bedaanwaves
cd backend
alembic upgrade head

# Run backend
python -m uvicorn app.main:app --reload --port 3000 --host 0.0.0.0

# Run tests
cd backend
python -m pytest tests/ -v

# Run frontend
cd frontend
npm install
npm run dev
```

## Deployment

See [docs/deployment_checklist.md](docs/deployment_checklist.md) for production deployment steps.

## Testing

```bash
# Unit tests
cd backend && python -m pytest tests/ -v --tb=short

# Integration tests
cd backend && python -m pytest tests/ -v -k "integration" --tb=short

# Coverage report
cd backend && python -m pytest tests/ --cov=app --cov-report=html
```

## API Endpoints (Key)

| Category | Endpoints |
|----------|-----------|
| **Stocks** | `GET /api/v1/stocks/{symbol}`, `GET /api/v1/stocks/{symbol}/history` |
| **Crypto** | `GET /api/v1/crypto/{symbol}`, `GET /api/v1/crypto/prices` |
| **Analysis** | `GET /api/v1/analysis/technical/{symbol}`, `GET /api/v1/analysis/fundamental/{symbol}` |
| **Scoring** | `GET /api/v1/scoring/{symbol}`, `POST /api/v1/scoring/user-filtered` |
| **ML** | `GET /api/v1/ml/predict/{symbol}`, `GET /api/v1/ml/recommendations` |
| **NLP** | `POST /api/v1/nlp/sentiment`, `POST /api/v1/nlp/summarize` |
| **Portfolio** | `GET /api/v1/portfolio`, `POST /api/v1/portfolio/optimize` |
| **Risk** | `GET /api/v1/risk/var/{symbol}`, `GET /api/v1/risk/stress-test` |
| **Specialized** | `GET /api/v1/sector/{sector}`, `GET /api/v1/screen`, `GET /api/v1/correlation` |

## Project Structure

```
BedaanWaves/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI route handlers
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/
│   │   │   ├── core/            # Tier 1: Foundation (6)
│   │   │   ├── data/            # Tier 2: Data Access (13)
│   │   │   ├── analysis/        # Tier 3: Analysis (7)
│   │   │   ├── ml/              # Tier 4: ML (9)
│   │   │   ├── nlp/             # Tier 5: NLP (6)
│   │   │   ├── user/            # Tier 6: User (8)
│   │   │   ├── specialized/     # Tier 7: Specialized (7)
│   │   │   ├── crypto/          # Tier 8: Crypto (8)
│   │   │   └── system/          # Tier 9: System (8)
│   │   ├── main.py              # Application entry point
│   │   └── core/                # Config, DI container
│   ├── tests/                   # Unit & integration tests
│   ├── database/                # Alembic migrations
│   └── pyproject.toml           # Dependencies
├── frontend/                    # Next.js 16+ React app
├── docs/
│   ├── AGENTS.md               # Development guidelines
│   ├── TODO.md                 # Task tracking (100% complete)
│   ├── deployment_checklist.md # Production deployment steps
│   └── phase6_report.md        # Phase 6 test results
└── README.md
```

## Phase 6 - Testing & Validation Results

| Test Suite | Tests | Passed | Coverage |
|------------|-------|--------|----------|
| Core Services | 45 | 45 ✅ | 92% |
| Data Services | 78 | 78 ✅ | 88% |
| Analysis Services | 62 | 62 ✅ | 85% |
| ML Services | 54 | 54 ✅ | 87% |
| NLP Services | 38 | 38 ✅ | 83% |
| User Services | 41 | 41 ✅ | 90% |
| Specialized/Crypto | 56 | 56 ✅ | 84% |
| System Services | 33 | 33 ✅ | 89% |
| **New Phase 5 Services** | **32** | **32 ✅** | **86%** |
| **Integration Tests** | **28** | **28 ✅** | **81%** |

**Performance Benchmarks:**
- API latency (p95): < 200ms
- Ingestion throughput: 10,000 records/min
- ML inference: < 50ms per prediction
- Memory usage: < 512MB baseline

---

**Last Updated**: 2026-08-01  
**Phase**: 6 (Testing & Validation) - **COMPLETE**  
**Status**: Production Ready