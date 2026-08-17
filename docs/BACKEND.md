# BedaanWaves Backend Documentation

**Version**: 1.0.0  
**Status**: Development  
**Consolidation**: 5 OldFils Projects

---

## Overview
BedaanWaves Backend is a comprehensive financial analysis platform consolidating functionality from:
- **Bedaan4D-ML** - Backend APIs and ML services
- **Bedaan6D-project** - Data analysis and scoring
- **Bedaan_4D_AI** - AI/ML models
- **CryptoAndStocks** - Multi-asset support
- **.kilo** - Configuration management

### Core Capabilities
✅ **Data Integration**
- Tehran Stock Exchange (BrsApi.ir)
- Financial Disclosures (Codal API)
- News Aggregation
- Cryptocurrency Support (Binance, CoinGecko)

✅ **Analysis Engine**
- 6D Scoring System (305-node hierarchy)
- 50+ Technical Indicators
- Fundamental Analysis
- Risk Assessment

✅ **Machine Learning**
- Ensemble Models (RF, XGBoost, LightGBM, NN, SVM)
- Time-Series Forecasting
- Anomaly Detection
- Coefficient Learning

✅ **NLP & Sentiment**
- Persian Sentiment Analysis
- Named Entity Extraction
- Text Summarization
- Impact Scoring

✅ **User Features**
- Portfolio Management
- Real-time Alerts
- Performance Tracking
- Multi-channel Notifications

---

## Technology Stack

```
Framework:    FastAPI 0.104+ (Async ASGI)
Language:     Python 3.11+
Database:     PostgreSQL 14+ (Primary)
Cache:        Redis 7+ (Session/Cache)
ORM:          SQLAlchemy 2.0
Migrations:   Alembic
Validation:   Pydantic (v2)
Auth:         JWT (via AuthGuardMiddleware)

Data Science: Pandas, NumPy, SciPy
ML:           Scikit-learn, XGBoost, LightGBM, TensorFlow
NLP:          Hazm (Persian), NLTK, Scikit-learn
Testing:      Pytest, Coverage, Faker
```

---

## Directory Structure

```
backend/
├── app/
│   ├── core/                    # Core utilities
│   │   ├── config.py           # Consolidated configuration (100+ settings)
│   │   ├── security.py         # JWT, password hashing
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── constants.py        # Constants and enums
│   │
│   ├── services/               # 48+ Business Services (9 Tiers)
│   │   ├── core/               # Tier 1: Core (DI, Config, Logging, Cache, DB, Health)
│   │   ├── data/               # Tier 2: Data (APIs, Data Management)
│   │   ├── analysis/           # Tier 3: Analysis (Scoring, Technical, Fundamental, Risk, Momentum, Volatility)
│   │   ├── ml/                 # Tier 4: ML (Prediction, Pattern Recognition, Anomaly, Recommendation, Portfolio Optimization, Time Series, Coefficient Learning, Crypto ML, User Filtered Recommendation)
│   │   ├── nlp/                # Tier 5: NLP (Sentiment, News Summarization, Document Extraction, Chatbot, Search, Multi-Language News)
│   │   ├── user/               # Tier 6: User (Auth, Authorization, Profile, Watchlist, Notification, Preferences, Market Settings, Crypto Settings)
│   │   ├── specialized/        # Tier 7: Specialized (Sector Analysis, Screening, Comparison, Correlation, Calendar, International Market, Sector Filter)
│   │   ├── crypto/             # Tier 8: Crypto (Price, Portfolio, Ingestion, ML, Custom Selection, Market Cap, News, Arbitrage)
│   │   └── system/             # Tier 9: System (Scheduler, Metrics, Queue, Backup, Logging, Notification Dispatcher, Data Integrity, Settings Migration)
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   └── models.py           # All models in single file
│   │
│   ├── schemas/               # Pydantic request/response schemas
│   │   └── schemas.py         # All schemas in single file
│   │
│   ├── api/                   # 16 API routers
│   │   ├── routes/
│   │   │   ├── auth.py        # Authentication
│   │   │   ├── stocks.py      # Stock endpoints
│   │   │   ├── market.py      # Market data routes
│   │   │   ├── analysis.py    # Analysis routes
│   │   │   ├── portfolio.py   # Portfolio management
│   │   │   ├── history.py     # Historical data
│   │   │   ├── news.py        # News search
│   │   │   ├── ml.py          # Machine Learning
│   │   │   ├── users.py       # User management
│   │   │   ├── watchlists.py  # Watchlist management
│   │   │   ├── notifications.py # Notifications
│   │   │   ├── specialized.py # Specialized analysis
│   │   │   ├── system.py      # System routes
│   │   │   ├── crypto.py      # Cryptocurrency
│   │   │   ├── intl.py        # International markets
│   │   │   └── live.py        # Live data
│   │   └── middleware/        # Middleware stack
│   │       ├── cors.py
│   │       ├── auth.py
│   │       ├── rate_limit.py
│   │       ├── logging.py
│   │       └── error_handler.py
│   │
│   ├── db/                    # Database
│   │   ├── base.py            # DB initialization
│   │   ├── session.py         # Session management
│   │   └── alembic/           # Alembic migrations
│   │
│   └── main.py                # FastAPI app entry point
│
├── requirements.txt           # Dependencies (100+ packages)
├── .env.example              # Environment variables template
├── .env                      # Local configuration
├── pytest.ini               # Test configuration
├── pyproject.toml           # Project metadata
└── README.md                # This file
```

---

## Service Architecture (48+ Services)

### Tier 1: Core Services (Foundation)
```
├── DependencyContainer      - IoC/DI pattern implementation
├── ConfigService            - Centralized configuration via config.py
├── LoggerService            - Structured logging with JSON format
├── CacheService             - Redis/memory caching with TTL
├── DatabaseService          - Connection pooling & management
└── HealthChecker            - System health monitoring
```

### Tier 2: Data Services (API Integration)
```
├── BrsApiClient             - Tehran Stock Exchange integration
├── StockService             - Stock data management
├── MarketService            - Market-wide analysis
├── PortfolioService         - Portfolio operations
├── HistoryService           - Time-series data
├── NewsService              - News aggregation
├── IntlApiClient            - International market APIs
├── CryptoApiClient          - Crypto exchange APIs
├── IngestionService         - Data ingestion pipelines
├── MarketDataProcessing     - Data cleaning pipelines
├── FinancialDataIngestService - Multi-source financial statement ingestion
├── StockFundamentalDataIngestionService - Stock fundamental data pipeline
└── DataValidationService    - Data integrity validation
```

### Tier 3: Analysis Services (Intelligence)
```
├── ScoringService           - 6D scoring (305-node hierarchy)
├── TechnicalAnalysisService - 50+ technical indicators
├── FundamentalAnalysisService - Fundamental metrics & ratios
├── CryptoFundamentalAnalysisService - Crypto fundamental analysis
├── RiskAnalysisService      - Risk assessment
├── MomentumService          - Momentum indicators
├── VolatilityService        - Volatility metrics
├── UserFilteredScoringService - Custom scoring based on user selections
```

### Tier 4: ML Services (Prediction)
```
├── PredictionService        - Price prediction models
├── PatternRecognitionService - Chart pattern detection
├── AnomalyDetectionService   - Outlier detection
├── RecommendationService    - Stock recommendations
├── PortfolioOptimizationService - Efficient frontier optimization
├── TimeSeriesForecastingService - ARIMA, LSTM, Prophet models
├── CoefficientLearningService - Dynamic coefficient learning
├── CryptoMLService          - Crypto-specific ML models
└── UserFilteredRecommendationService - Recommendations filtered by user preferences
```

### Tier 5: NLP Services (Sentiment)
```
├── SentimentAnalysisService - Persian sentiment analysis
├── NewsSummarizationService - Text summarization
├── DocumentExtractionService - PDF/text extraction
├── ChatbotService           - Conversational AI
├── SearchService            - Semantic search
└── MultiLanguageNewsService - Country-specific news with language detection
```

### Tier 6: User Services (Personalization)
```
├── AuthService              - JWT authentication
├── AuthorizationService     - RBAC
├── UserProfileService       - User profiles and KYC
├── WatchlistService         - Watchlist management
├── PreferenceService        - User customization
├── NotificationService      - Multi-channel notifications
├── UserMarketSettingsService - Country/index/industry selection
└── UserCryptoSettingsService - Cryptocurrency selection preferences
```

### Tier 7: Specialized Services (Advanced)
```
├── SectorAnalysisService    - Sector performance & ranking
├── ScreeningService         - Stock screening filters
├── ComparisonService        - Peer benchmarking
├── CorrelationService       - Cross-asset correlation
├── CalendarService          - Market calendar integration
├── InternationalMarketService - Multi-country data integration
└── SectorFilterService      - Industry-based filtering
```

### Tier 8: Crypto Services (Multi-Asset)
```
├── PriceService             - Real-time crypto price feeds
├── PortfolioService         - Crypto portfolio management
├── CryptoIngestionService   - Exchange data ingestion
├── CryptoMLService          - Crypto-specific ML analysis (Analysis tier)
├── CustomCryptoSelectionService - User-defined selection from top 300
├── CryptoMarketCapService   - Market cap-based filtering
├── CryptoAnalysisService    - On-chain metrics analysis
├── NewsService (Crypto)     - Crypto-specific news integration
└── ArbitrageService         - Cross-exchange price monitoring
```

### Tier 9: System Services (Operations)
```
├── SchedulerService         - Task scheduling pipeline
├── MetricsService           - Performance monitoring
├── QueueService             - Message queuing system
├── BackupService            - Database/file backups
├── LoggingService           - Centralized logging aggregation
├── NotificationDispatcher   - Multi-channel notifications
├── DataIntegrityService     - Historical data validation
└── SettingsMigrationService - User preference migration
```

---

## 6D Scoring System

### Scoring Formula
```
fundamental_score   × 0.25   (Financial health)
+ technical_score     × 0.20   (Chart patterns)
+ sentiment_score     × 0.15   (News & sentiment)
+ risk_score          × 0.20   (Volatility & risk)
+ macro_score         × 0.10   (Economic factors)
+ ai_score            × 0.10   (ML prediction)
────────────────────────────────
= final_score (1-100)

Hierarchy (305 nodes):
  Level 1: 12 Dimensions
  Level 2: 40 Sub-Dimensions
  Level 3: 80 Aspects
  Level 4: 173 Sub-Aspects
```

---

## Technical Analysis (50+ Indicators)
```
Moving Averages:  SMA, EMA, WMA, TEMA
Momentum:         RSI, MACD, Stochastic, KDJ, CCI
Volatility:       Bollinger Bands, ATR, KAMA, Donchian
Trend:            ADX, Ichimoku, Parabolic SAR, TRIX
Volume:           OBV, CMF, VPTK, AD
Additional:       ROC, Williams %R, Ultimate Oscillator, ...
```

---

## ML Ensemble
```
Models:           Random Forest (100 trees)
                  XGBoost (gradient boosting)
                  LightGBM (fast GB)
                  Neural Network (LSTM)
                  SVM (support vectors)

Ensemble Voting:  Weighted average of predictions
Coefficient Learning: Daily performance-based adjustment
                  coef_t = 0.8 × coef_t-1 + 0.2 × performance
```

---

## NLP & Sentiment
```
Sentiment Pipeline:
  Raw Text → Tokenization → Lemmatization → Classification
  
Output: Sentiment score (-1 to 1) with impact weighting
```

---

## Multi-Asset Support
```
Stocks:           Tehran Stock Exchange (TSE)
Cryptocurrencies: BTC, ETH, BNB, SOL, ADA, XRP, ...
Futures:          Available via partner APIs
Forex:            Available via partner APIs
```

---

## API Routes (16 Routers)

### Authentication
```
POST   /api/v1/auth/register          # Register new user
POST   /api/v1/auth/login             # Login
POST   /api/v1/auth/refresh           # Refresh token
```

### Stocks
```
GET    /api/v1/stocks/list            # List all stocks
GET    /api/v1/stocks/{symbol}        # Stock details
GET    /api/v1/stocks/{symbol}/history    # Price history
GET    /api/v1/stocks/{symbol}/analysis   # Technical analysis
```

### Market
```
GET    /api/v1/market/overview        # Market overview
GET    /api/v1/market/indices         # Index data
GET    /api/v1/market/sectors         # Sector analysis
GET    /api/v1/market/tse-dashboard   # TSE dashboard
GET    /api/v1/market/latest-prices   # Latest prices
GET    /api/v1/market/price-history    # Historical price data
GET    /api/v1/market/industry-ranking  # Industry ranking
```

### Analysis / Signals
```
GET    /api/v1/analysis/signals/{symbol}   # ML signals
GET    /api/v1/analysis/signals-summary    # Signals summary
GET    /api/v1/analysis/top-performers    # Top performers
GET    /api/v1/analysis/risk-analysis/{symbol}  # Risk metrics
GET    /api/v1/analysis/technical/{symbol}     # Technical indicators
GET    /api/v1/analysis/risk/{symbol}          # Risk analysis
GET    /api/v1/analysis/fundamental/{symbol}   # Fundamental analysis
GET    /api/v1/analysis/momentum/{symbol}      # Momentum analysis
GET    /api/v1/analysis/volatility/{symbol}    # Volatility analysis
POST   /api/v1/analysis/scoring                # 6D scoring
POST   /api/v1/analysis/scoring/rank           # Score and rank
GET    /api/v1/analysis/fundamental/batch      # Batch fundamental analysis
GET    /api/v1/analysis/fundamental/crypto/{crypto_id} # Crypto fundamental
GET    /api/v1/analysis/fundamentals/health    # Fundamental services health
```

### Portfolio
```
GET    /api/v1/portfolio                 # List portfolios
POST   /api/v1/portfolio                 # Create portfolio
GET    /api/v1/portfolio/{id}            # Portfolio details
POST   /api/v1/portfolio/{id}/add        # Add holding
GET    /api/v1/portfolio/{id}/optimization # Optimization
```

### History
```
GET    /api/v1/history/symbol/{symbol}    # Historical data for symbol
```

### News
```
GET    /api/v1/news/market                # Market news
GET    /api/v1/news/{ticker}              # News for specific ticker
GET    /api/v1/news/search                # Search news
```

### Machine Learning
```
GET    /api/v1/ml/predict/{symbol}        # Price prediction
POST   /api/v1/ml/recommend/{symbol}      # Investment recommendation
POST   /api/v1/ml/patterns/{symbol}       # Pattern detection
POST   /api/v1/ml/anomaly/{symbol}        # Anomaly detection
GET    /api/v1/ml/portfolio/optimize      # Portfolio optimization
POST   /api/v1/ml/timeseries/forecast     # Time series forecasting
```

### Users
```
GET    /api/v1/users                     # List users
GET    /api/v1/users/{id}                # User details
PUT    /api/v1/users/{id}                # Update user
DELETE /api/v1/users/{id}                # Delete user
```

### Watchlists
```
GET    /api/v1/watchlists                # List watchlists
POST   /api/v1/watchlists                # Create watchlist
GET    /api/v1/watchlists/{id}           # Get watchlist
PUT    /api/v1/watchlists/{id}           # Update watchlist
DELETE /api/v1/watchlists/{id}           # Delete watchlist
```

### Notifications
```
GET    /api/v1/notifications             # List notifications
POST   /api/v1/notifications/preferences # Update preferences
```

### Specialized
```
GET    /api/v1/specialized/sector/{sector}  # Sector analysis
POST   /api/v1/specialized/screen            # Stock screening
GET    /api/v1/specialized/compare             # Compare stocks
GET    /api/v1/specialized/correlation         # Correlation analysis
GET    /api/v1/specialized/calendar            # Market calendar
GET    /api/v1/specialized/international       # International markets
GET    /api/v1/specialized/sector-filter       # Sector filtering
```

### System
```
GET    /api/v1/system/health                 # Health check
GET    /api/v1/system/metrics                # System metrics
GET    /api/v1/system/status                  # System status
POST   /api/v1/system/backup                  # Trigger backup
GET    /api/v1/system/backup/status           # Backup status
POST   /api/v1/system/settings/migrate        # Migrate settings
```

### Cryptocurrency
```
GET    /api/v1/crypto/list                    # List cryptocurrencies
GET    /api/v1/crypto/{symbol}                # Crypto details
GET    /api/v1/crypto/{symbol}/price          # Current price
GET    /api/v1/crypto/{symbol}/ohlc           # OHLC data
GET    /api/v1/crypto/{symbol}/ticker         # 24h ticker
GET    /api/v1/crypto/{symbol}/depth            # Order book depth
GET    /api/v1/crypto/search                   # Search cryptocurrencies
GET    /api/v1/crypto/fundamental/{symbol}     # Crypto fundamental analysis
```

### International
```
GET    /api/v1/intl/markets                 # List international markets
GET    /api/v1/intl/{market}/overview        # Market overview
GET    /api/v1/intl/{market}/indices         # Market indices
```

### Live Data
```
GET    /api/v1/live/price/{symbol}          # Real-time price
GET    /api/v1/live/prices                    # Multiple real-time prices
WS     /ws/market/stream                      # Market data WebSocket
```

---

## Security
✅ JWT Authentication & Authorization  
✅ Password Hashing (bcrypt)  
✅ CORS Protection  
✅ Rate Limiting (100 req/min default)  
✅ Input Validation & Sanitization  
✅ SQL Injection Prevention (SQLAlchemy ORM)  
✅ XSS Prevention (Pydantic validation)  
✅ HTTPS Ready  
✅ Audit Logging  
✅ Error Handling (no sensitive info exposed)

## Performance
```
API Response:     < 100ms (median)
                  < 300ms (P95)
                  < 1000ms (P99)

Database Query:   < 50ms (indexed)
                  < 200ms (complex)

Cache Hit Rate:   > 85%

Model Inference:  < 500ms (CPU)
                  < 100ms (GPU)

Throughput:       1000+ requests/second (on 4-core server)
```

## Testing
```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_auth.py

# Specific test
pytest tests/test_auth.py::test_login
```

### Test Structure
```
tests/
├── unit/
│   ├── services/
│   ├── schemas/
│   ├── utils/
│   └── models/
├── integration/
│   ├── api/
│   ├── database/
│   └── services/
├── e2e/
│   └── workflows/
└── conftest.py
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Generate new `SECRET_KEY`
- [ ] Configure PostgreSQL connection
- [ ] Setup Redis
- [ ] Enable monitoring/logging
- [ ] Configure backups
- [ ] Setup SSL/TLS
- [ ] Load testing (k6, Locust)
- [ ] Security audit
- [ ] Performance profiling

## Development Workflow
1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and commit: `git commit -m "feat: description"`
3. Run tests: `pytest --cov`
4. Run linting: `black . && flake8 . && mypy app`
5. Push and create PR

## Code Standards
- PEP 8 compliance
- Type hints for all functions
- Docstrings (Google style)
- Minimum 80% test coverage
- Black code formatting

---

**Last Updated**: July 29, 2026  
**Version**: 1.0.0  
**Status**: Phase 3 (~85% Complete) - Tiers 1-7 implemented, Tiers 8-9 in progress