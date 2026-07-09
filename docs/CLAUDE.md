# Claude Agent Instructions for BedaanWaves

## Project Scope

**BedaanWaves** is a unified capital market analysis platform consolidating 5 legacy projects into a single optimized system.

- **Stack**: FastAPI, SQLAlchemy, PostgreSQL, React/Next.js
- **Database**: PostgreSQL (local, port 5432)
- **Python**: 3.11+
- **No Docker**: All services run directly
- **Active Directory**: `E:\Shakour\BedaanProjects\BedaanWaves` only

## Access Policy

### ✅ You CAN Access
- `backend/` - All Python services, API routes, models
- `frontend/` - Next.js React components
- `database/` - Alembic migrations
- `docs/` - Documentation
- `.kilo/` - Kilo configuration
- Root config files (`kilo.json`, `.env`, etc.)

### ❌ You CANNOT Access
- `E:\Shakour\BedaanProjects\OldFils\` (any subdirectory)
- External directories outside BedaanWaves
- Docker files (for reference only, no modifications)

## Implementation Strategy

### Current Status
- **Phase**: 3 (Services Implementation) - 35% complete
- **Services**: 18 implemented (Tiers 1-3)
- **Lines of Code**: 3,680+ lines
- **Commits**: 8 total

### Completed Tiers

**Tier 1: Core Services** ✅
- DependencyContainer: IoC/DI management (160 LOC)
- ConfigService: Configuration management (240 LOC)
- LoggerService: Structured logging (200 LOC)
- CacheService: Multi-backend caching (230 LOC)
- DatabaseService: Connection pooling (200 LOC)
- HealthChecker: System monitoring (240 LOC)

**Tier 2: Data Services** ✅
- BrsApiClient: TSE API integration (240 LOC)
- StockService: Stock management (150 LOC)
- MarketService: Market aggregation (120 LOC)
- PortfolioService: Portfolio operations (160 LOC)
- HistoryService: Historical data (130 LOC)
- NewsService: News integration (130 LOC)

**Tier 3: Analysis Services** ✅
- ScoringService: 6D scoring, 305-node hierarchy (220 LOC)
- TechnicalAnalysisService: 50+ indicators (380 LOC)
- FundamentalAnalysisService: 20+ ratios (280 LOC)
- RiskAnalysisService: VaR, Sharpe, stress tests (290 LOC)
- MomentumService: Momentum analysis (110 LOC)
- VolatilityService: Volatility forecasting (200 LOC)

### Pending Tiers

**Tier 4: ML Services** (6 services)
- MLService, PricePredictionService
- AnomalyDetectionService, ClusteringService
- EnsembleService, FeatureEngineeringService

**Tier 5: NLP Services** (5 services)
- SentimentAnalysisService, NewsAnalysisService
- NLPService, EntityExtractionService, SummarizationService

**Tier 6: User Services** (6 services)
- UserService, AuthService, SubscriptionService
- PreferenceService, AlertService, NotificationService

**Tier 7: Specialized Services** (5 services)
- HierarchyService, AssistantService, BacktestService
- PortfolioOptimizationService, RegressionService

**Tier 8: Crypto Services** (5 services)
- CryptoAnalysisService, ChainAnalysisService
- DeFiService, TransactionService, WalletService

**Tier 9: System Services** (6 services)
- DataRecoveryService, BackupService, AuditService
- PerformanceMonitor, ErrorHandler, RateLimiter

## Development Guidelines

### Code Quality Standards
- **Type Hints**: All functions must have type hints
- **Docstrings**: NumPy-style docstrings for all functions
- **Error Handling**: Try-catch with proper logging
- **Metrics**: Track calls, errors, latency
- **Logging**: Use service.logger for all logging

### Service Development Pattern

```python
from app.services.core import BaseService

class MyService(BaseService):
    """Service description"""
    
    def __init__(self, service_name: str = "MyService"):
        super().__init__(service_name)
        self._data = {}
    
    async def initialize(self) -> None:
        """Initialize service"""
        self.logger.info(f"{self.service_name} initialized")
    
    async def shutdown(self) -> None:
        """Shutdown service"""
        self._data.clear()
        self.logger.info(f"{self.service_name} shutdown")
    
    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data"""
        try:
            result = {}
            self._metrics["calls"] += 1
            return result
        except Exception as e:
            self._metrics["errors"] += 1
            self.logger.error(f"Error: {e}")
            raise
```

### Database Models

```python
from sqlalchemy import Column, Integer, String, DateTime
from app.db.base import Base

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, index=True)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
```

### API Routes

```python
from fastapi import APIRouter, Depends
from app.services.data import StockService

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])

@router.get("/{ticker}")
async def get_stock(ticker: str, stock_service: StockService = Depends()):
    """Get stock information"""
    return await stock_service.get_stock(ticker)
```

### Git Commit Messages

Format: `type: Description`

Types:
- `feat:` New feature/service
- `fix:` Bug fix
- `docs:` Documentation
- `config:` Configuration
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

Example:
```
feat: Implement Tier 4 ML Services

- MLService: Ensemble model training (150 LOC)
- PricePredictionService: LSTM predictions (200 LOC)
- AnomalyDetectionService: Isolation Forest (180 LOC)

Features:
- Cross-validation support
- Model persistence
- Confidence scores
```

## Project Structure

```
BedaanWaves/
├── .kilo/                      # Kilo configuration
│   └── agent/backend.md        # Backend agent config
├── backend/
│   ├── app/
│   │   ├── services/           # Service tiers 1-9
│   │   │   ├── core/           # Tier 1 ✅
│   │   │   ├── data/           # Tier 2 ✅
│   │   │   ├── analysis/       # Tier 3 ✅
│   │   │   ├── ml/             # Tier 4 🔄
│   │   │   ├── nlp/            # Tier 5 🔄
│   │   │   ├── user/           # Tier 6 🔄
│   │   │   ├── specialized/    # Tier 7 🔄
│   │   │   ├── crypto/         # Tier 8 🔄
│   │   │   └── system/         # Tier 9 🔄
│   │   ├── api/
│   │   │   └── routes/         # FastAPI routers
│   │   ├── models/             # SQLAlchemy ORM
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── core/
│   │   │   └── config.py       # Configuration
│   │   ├── db/                 # Database setup
│   │   └── main.py             # Entry point
│   ├── requirements.txt        # Dependencies
│   ├── .env.example            # Environment template
│   └── README.md               # Backend docs
├── frontend/                   # Next.js React
├── database/                   # Alembic migrations
├── docs/                       # Project documentation
│   ├── AGENTS.md               # Agent guidelines
│   ├── CLAUDE.md               # This file
│   └── REWRITE_PROGRESS.md     # Progress tracking
└── kilo.json                   # Kilo config
```

## Environment Setup

### Database Setup
```bash
# Create database
createdb bedaanwaves

# Create .env in backend/
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bedaanwaves
DB_USER=postgres
DB_PASSWORD=your_password
```

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Running Services
```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload

# Will be available at http://localhost:8000
```

## Testing

Create tests in `backend/tests/`:

```python
import pytest
from app.services.analysis import ScoringService

@pytest.mark.asyncio
async def test_scoring_service():
    service = ScoringService()
    await service.initialize()
    
    result = await service.analyze({
        "ticker": "TEST",
        "technical": {"rsi": 65, "macd": 0.5},
    })
    
    assert result["overall_score"] > 0
    await service.shutdown()
```

Run tests:
```bash
pytest backend/tests/ -v --cov=app
```

## Update Progress File

When completing a tier or feature, update `REWRITE_PROGRESS.md`:

```markdown
### Phase 3: Backend Services ✅ (70%)

#### 3.4: Tier 4 - ML Services ✅ COMPLETE
- [x] MLService (160 lines)
- [x] PricePredictionService (200 lines)
- [x] AnomalyDetectionService (180 lines)
- [x] ClusteringService (150 lines)
- [x] EnsembleService (140 lines)
- [x] FeatureEngineeringService (170 lines)

**Statistics**: 6 services, 1,000 lines
```

## No Docker Policy

⚠️ **Important**: This project runs WITHOUT Docker.

- Backend runs with Uvicorn directly
- PostgreSQL is local installation
- No containerization needed
- Simpler debugging and development
- Direct access to services

## Reference Documentation

- **Config**: See `kilo.json` and `docs/AGENTS.md`
- **Architecture**: See `backend/README.md`
- **Progress**: See `docs/REWRITE_PROGRESS.md`
- **Services**: See `backend/app/services/`

## Key Principles

1. **Single Codebase**: All 5 legacy projects consolidated
2. **Type Safety**: Full type hints everywhere
3. **Logging**: Comprehensive structured logging
4. **Metrics**: All services track metrics
5. **Clean Architecture**: Service tiers with clear dependencies
6. **Local Development**: No Docker, all local
7. **PostgreSQL**: Required, running locally

---

**Last Updated**: 2026-07-09  
**Phase**: 3 (35% complete)  
**Next**: Tier 4 - ML Services implementation
