# BedaanWaves Agents Configuration

## Project Overview

BedaanWaves is a unified capital market analysis platform consolidating 5 legacy projects into a single, optimized system.

- **Framework**: FastAPI, SQLAlchemy
- **Database**: PostgreSQL (local, required)
- **Python**: 3.11+
- **No Docker**: All services run directly on local machine
- **Scope**: Backend (`backend/`), Frontend (`frontend/`), Database (`database/`), Documentation (`docs/`)

## Access Restrictions

**Blocked Directories** (read/write):
- `E:\Shakour\BedaanProjects\OldFils\.kilo`
- `E:\Shakour\BedaanProjects\OldFils\Bedaan_4D_AI`
- `E:\Shakour\BedaanProjects\OldFils\Bedaan4D-ML`
- `E:\Shakour\BedaanProjects\OldFils\Bedaan6D-project`
- `E:\Shakour\BedaanProjects\OldFils\CryptoAndStocks`

**Active Scope**: `E:\Shakour\BedaanProjects\BedaanWaves` only

## Implementation Status

### ✅ Completed (Phase 3: 35%)

**Tier 1 Core Services** (6 services, 1,270 LOC)
- DependencyContainer: IoC/DI management
- ConfigService: Centralized configuration
- LoggerService: Structured logging
- CacheService: Multi-backend caching
- DatabaseService: Connection pooling
- HealthChecker: System monitoring

**Tier 2 Data Services** (6 services, 930 LOC)
- BrsApiClient: Tehran Stock Exchange API
- StockService: Stock data management
- MarketService: Market data aggregation
- PortfolioService: Portfolio operations
- HistoryService: Historical data
- NewsService: News integration

**Tier 3 Analysis Services** (6 services, 1,480 LOC)
- ScoringService: 6D scoring (305-node hierarchy)
- TechnicalAnalysisService: 50+ indicators
- FundamentalAnalysisService: 20+ ratios
- RiskAnalysisService: VaR, Sharpe, stress testing
- MomentumService: Momentum analysis
- VolatilityService: Volatility forecasting

### 🔄 Pending (Tiers 4-9)

**Tier 4 - ML Services**: 6 services
**Tier 5 - NLP Services**: 5 services
**Tier 6 - User Services**: 6 services
**Tier 7 - Specialized Services**: 5 services
**Tier 8 - Crypto Services**: 5 services
**Tier 9 - System Services**: 6 services

## Setup & Development

### Prerequisites
```bash
# Python 3.11+
# PostgreSQL running locally on port 5432
# Virtual environment activated
```

### Database Setup
```bash
# Create PostgreSQL database
createdb bedaanwaves

# Run migrations (when ready)
# alembic upgrade head
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### Environment
Create `.env` in backend directory:
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

DB_DRIVER=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bedaanwaves
DB_USER=postgres
DB_PASSWORD=your_password

REDIS_URL=redis://localhost:6379/0
CACHE_BACKEND=memory

JWT_SECRET=your-secret-key-change-in-production
```

## Git Workflow

### Commits
All work is committed to master branch:
- Tier implementations are committed separately
- Each commit includes comprehensive feature description
- Progress tracked in REWRITE_PROGRESS.md

### Recent Commits
```
af69d84 - docs: Update progress (Tiers 1-3)
2baa44f - feat: Implement Tier 3 Analysis Services
33badf6 - feat: Implement Tier 1 & 2 Services
```

## Architecture

```
BedaanWaves/
├── backend/app/
│   ├── services/
│   │   ├── core/          # Tier 1: Foundation
│   │   ├── data/          # Tier 2: Data access
│   │   ├── analysis/      # Tier 3: Analysis
│   │   ├── ml/            # Tier 4: ML (pending)
│   │   ├── nlp/           # Tier 5: NLP (pending)
│   │   ├── user/          # Tier 6: User (pending)
│   │   ├── specialized/   # Tier 7: Specialized (pending)
│   │   ├── crypto/        # Tier 8: Crypto (pending)
│   │   └── system/        # Tier 9: System (pending)
│   ├── api/routes/        # FastAPI routes
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   └── main.py            # Entry point
├── database/              # Alembic migrations
├── frontend/              # Next.js 16+
├── docs/                  # Documentation
│   ├── AGENTS.md          # This file
│   ├── CLAUDE.md          # Claude instructions
│   └── REWRITE_PROGRESS.md # Progress tracking
└── kilo.json              # Kilo config
```

## Development Guidelines

### Code Style
- Type hints on all functions
- Comprehensive docstrings
- Error handling with proper logging
- Metrics tracking for monitoring

### Service Development
1. Extend appropriate base class (BaseService, CachedService, DataService, etc.)
2. Implement `initialize()` and `shutdown()` lifecycle methods
3. Use DependencyContainer for service registration
4. Add comprehensive logging
5. Include metrics collection

### Testing
- Unit tests in `backend/tests/`
- Use pytest with coverage
- Mock external services
- Test service initialization/shutdown

## Configuration

All configuration via environment variables or `config.py`:
- 100+ settings organized by category
- Centralized ConfigService for access
- Type conversion helpers (get_int, get_bool, etc.)
- Validation on startup

## Monitoring & Health

HealthChecker service monitors:
- Database connectivity
- Cache functionality
- System memory/disk
- Service health status

Access health endpoint for system status.

## No Docker Policy

All services run directly:
- Backend: FastAPI with Uvicorn
- Database: PostgreSQL (local install)
- Cache: Redis (optional, memory fallback)
- No containerization required

---

**Last Updated**: 2026-07-09  
**Phase**: 3 (Services Implementation)  
**Estimated Completion**: 1.5 weeks
