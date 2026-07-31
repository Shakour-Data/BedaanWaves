# BedaanWaves Agents Configuration

## Project Overview

BedaanWaves is a unified capital market analysis platform consolidating 5 legacy projects into a single, optimized system.

- **Framework**: FastAPI, SQLAlchemy 2.0
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

**Active Scope**: `E:\Shakour\BedaanProjects\OldFils\BedaanWaves` only

## Implementation Status

### ✅ COMPLETE (Master Implementation: 100%)

**Tier 1: Core Services** (6 services) ✅
- DependencyContainer: IoC/DI management
- ConfigService: Centralized configuration
- LoggerService: Structured logging
- CacheService: Multi-backend caching
- DatabaseService: Connection pooling
- HealthChecker: System monitoring

**Tier 2: Data Services** (13 services) ✅
- BrsApiClient: Tehran Stock Exchange API
- StockService: Stock data management
- MarketService: Market data aggregation
- PortfolioService: Portfolio operations
- HistoryService: Historical data
- NewsService: News integration
- IngestionService: Data ingestion pipelines
- MarketDataProcessing: Data cleaning pipelines
- IntlApiClient: International market APIs
- CryptoApiClient: Crypto exchange APIs
- DataValidationService: Data integrity validation
- FinancialDataIngestService: Multi-source financial statement ingestion (CODAL, Yahoo Finance, Alpha Vantage)
- StockFundamentalDataIngestionService: Stock fundamental data pipeline for Iran/US/International markets

**Additional Services Implemented:**
- SECRestAPIClient: SEC EDGAR filing retrieval (TODO-H2)
- IncrementalFinancialDataIngestService: Incremental data ingestion with change detection (TODO-I4)
- DataArchivalService: Historical data archival strategy (TODO-I5)
- CrossAssetComparisonService: Cross-asset fundamental comparison methodology (TODO-V1)
- MessageQueueService: Async message queue for data processing (TODO-N4)
- DataRetentionService: Data retention policies (TODO-O4)
- HistoricalDataRetrieval: Historical fundamental data endpoint (TODO-K4)
- UnifiedFundamentalDataModel: Cross-asset data model (TODO-N1)

**Tier 3: Analysis Services** (7 services) ✅
- ScoringService: 6D scoring, 305-node hierarchy
- TechnicalAnalysisService: 50+ indicators with live dashboard
- FundamentalAnalysisService: 20+ ratios with global market support (Iran, US, International)
- RiskAnalysisService: VaR, Sharpe, stress testing (production-ready)
- MomentumService: Momentum analysis (live signals)
- VolatilityService: Volatility forecasting (production-ready)
- UserFilteredScoringService: Custom scoring based on user selections (live API)

**Tier 4: ML Services** (9 services) ✅ COMPLETED
- PredictionService: Price prediction models
- PatternRecognitionService: Chart pattern detection
- AnomalyDetectionService: Outlier detection
- RecommendationService: Stock recommendations
- PortfolioOptimizationService: Efficient frontier optimization
- TimeSeriesForecastingService: ARIMA, LSTM, Prophet models
- CoefficientLearningService: Dynamic coefficient learning
- CryptoMLService: Crypto-specific ML models
- UserFilteredRecommendationService: Recommendations filtered by user preferences

**Tier 5: NLP Services** (6 services) ✅ COMPLETED
- SentimentAnalysisService: News sentiment analysis
- NewsSummarizationService: Text summarization
- DocumentExtractionService: PDF/text extraction
- ChatbotService: Conversational AI
- SearchService: Semantic search
- MultiLanguageNewsService: Country-specific news with language detection

**Tier 6: User Services** (8 services) ✅ COMPLETED
- AuthService: Authentication with JWT
- AuthorizationService: RBAC
- UserProfileService: User profiles and KYC
- WatchlistService: Watchlist management
- PreferenceService: User customization
- NotificationService: Multi-channel notifications
- UserMarketSettingsService: Country/index/industry selection
- UserCryptoSettingsService: Cryptocurrency selection preferences

**Tier 7: Specialized Services** (7 services) ✅ COMPLETED
- SectorAnalysisService: Sector performance
- ScreeningService: Stock screening filters
- ComparisonService: Peer benchmarking
- CorrelationService: Cross-asset correlation
- CalendarService: Market calendar integration
- InternationalMarketService: Multi-country data integration
- SectorFilterService: Industry-based filtering

**Tier 8: Crypto Services** (8 services) ✅ COMPLETED
- PriceService: Real-time crypto price feeds
- PortfolioService: Crypto portfolio management
- CryptoIngestionService: Exchange data ingestion
- CryptoMLService: Crypto-specific ML analysis
- CustomCryptoSelectionService: User-defined selection from top 300
- CryptoMarketCapService: Market cap-based filtering
- CryptoAnalysisService: On-chain metrics analysis
- ArbitrageService: Cross-exchange price monitoring

**Tier 9: System Services** (8 services) ✅ COMPLETED
- SchedulerService: Task scheduling pipeline
- MetricsService: Performance monitoring
- QueueService: Message queuing system
- BackupService: Database/file backups
- LoggingService: Centralized logging aggregation
- NotificationDispatcher: Multi-channel notifications
- DataIntegrityService: Historical data validation
- SettingsMigrationService: User preference migration

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

# Run migrations
cd backend
alembic upgrade head
```

### Backend Setup
```bash
cd backend
pip install -e .  # Install from pyproject.toml
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
- Progress tracked in docs/TODO.md

### Recent Commits
```
7a09ed7 - Update crypto_ingestion_service.py
b66dedf - Update init__.py
cc0eba2 - Update init__.py
92bdb4d - Add financial_data_ingest_service.py
c881e7a - Update TODO.md
11a8bd0 - Update AGENTS.md
36d36ea - Update stock_fundamental_ingestion_service.py
8fac24a - Update init__.py
7129f9f - Update fundamental_service.py
8f69185 - Update analysis.py
```

## Architecture
```
BedaanWaves/
├── backend/app/
│   ├── services/
│   │   ├── core/          # Tier 1: Foundation
│   │   ├── data/          # Tier 2: Data access
│   │   ├── analysis/      # Tier 3: Analysis
│   │   ├── ml/            # Tier 4: ML (completed)
│   │   ├── nlp/           # Tier 5: NLP (completed)
│   │   ├── user/          # Tier 6: User (completed)
│   │   ├── specialized/   # Tier 7: Specialized (completed)
│   │   ├── crypto/        # Tier 8: Crypto (completed)
│   │   └── system/        # Tier 9: System (completed)
│   ├── api/routes/        # FastAPI routes
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   └── main.py            # Entry point
├── database/              # Alembic migrations
├── frontend/              # Next.js 16+
├── docs/                  # Documentation
│   ├── AGENTS.md          # This file
│   └── TODO.md            # Task tracking
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

**Last Updated**: 2026-07-31  
**Phase**: Complete (100% Implementation)  
**Status**: Production Ready