# BedaanWaves - Complete Rewrite Strategy

**Date**: July 9, 2026  
**Goal**: Consolidate 5 OldFils projects into unified BedaanWaves platform  
**Approach**: 100% Code Rewrite using learned patterns and business logic

---

## Executive Strategy

### Phase 1: Architecture & Foundation (Week 1)
- Unified directory structure
- Core backend setup (FastAPI, PostgreSQL, Redis)
- Database schema consolidation
- Configuration management

### Phase 2: Backend Services (Week 2-3)
- Data integration services
- 6D scoring engine
- Technical analysis (50+ indicators)
- ML pipeline (ensemble models)
- NLP sentiment analysis

### Phase 3: Frontend Implementation (Week 4)
- Magic design system (6D numerology)
- Dashboard and UI components
- Real-time data visualization
- Hierarchy explorer

### Phase 4: Integration & Testing (Week 5)
- API integration
- E2E testing
- Performance optimization
- Deployment

---

## What We're Consolidating

| Component | Source | Purpose |
|-----------|--------|---------|
| Configuration | .kilo | Agent & environment setup |
| Data Archive | Bedaan_4D_AI | Historical data reference |
| Backend Core | Bedaan4D-ML | APIs, services, ML, NLP |
| Stock Frontend | Bedaan6D-project | UI, design system |
| Crypto System | CryptoAndStocks | Multi-asset support |

---

## New Unified BedaanWaves Architecture

```
BedaanWaves/
├── backend/                    # Unified Python backend
│   ├── app/
│   │   ├── core/              # Core components
│   │   ├── services/          # 50+ business services
│   │   ├── api/               # API routes
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Data schemas
│   │   ├── ml/                # ML pipeline
│   │   ├── nlp/               # NLP services
│   │   ├── integrations/      # External APIs
│   │   ├── utils/             # Utilities
│   │   └── main.py            # Entry point
│   ├── tests/                 # Test suite
│   ├── requirements.txt        # Dependencies
│   └── .env                   # Configuration
│
├── frontend/                   # Unified Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js app router
│   │   ├── components/        # React components
│   │   │   ├── magic/         # Magic design system
│   │   │   ├── ui/            # shadcn/ui
│   │   │   ├── pages/         # Page components
│   │   │   └── charts/        # Data visualization
│   │   ├── services/          # API services
│   │   ├── stores/            # Zustand state
│   │   ├── hooks/             # Custom hooks
│   │   ├── lib/               # Utilities
│   │   ├── types/             # TypeScript types
│   │   └── styles/            # Global styles
│   ├── tests/                 # Test suite
│   ├── package.json
│   └── tsconfig.json
│
├── database/                   # Database schema & migrations
│   ├── schema.sql             # PostgreSQL schema
│   ├── migrations/            # Alembic migrations
│   └── seeds/                 # Test data
│
├── config/                     # Configuration
│   ├── .kilo/                 # Kilo agent configuration
│   ├── docker-compose.yml     # Local development
│   └── .env.example           # Environment template
│
├── docs/                       # Documentation
│   ├── API.md                 # API documentation
│   ├── ARCHITECTURE.md        # Technical architecture
│   ├── DEPLOYMENT.md          # Deployment guide
│   └── DEVELOPMENT.md         # Development guide
│
└── scripts/                    # Helper scripts
    ├── setup_db.py            # Database setup
    ├── migrate.py             # Database migrations
    └── seed_data.py           # Initial data loading
```

---

## Backend Services Architecture (50+ Services)

### Tier 1: Core Services (Foundation)
1. **DependencyContainer** - IoC / DI
2. **ConfigService** - Configuration management
3. **LoggerService** - Structured logging
4. **CacheService** - Redis caching
5. **DatabaseService** - Connection pooling
6. **HealthChecker** - System health

### Tier 2: Data Services (Access)
7. **BrsApiClient** - Tehran Stock Exchange API
8. **CodalApiClient** - Financial disclosures
9. **NewsApiClient** - News aggregation
10. **CryptoApiClient** - Cryptocurrency data
11. **StockService** - Stock data management
12. **MarketService** - Market-wide analysis
13. **PortfolioService** - Portfolio operations
14. **HistoryService** - Time-series data

### Tier 3: Analysis Services (Intelligence)
15. **ScoringService** - 6D scoring calculation
16. **TechnicalAnalysisService** - 50+ technical indicators
17. **FundamentalAnalysisService** - Fundamental metrics
18. **RiskAnalysisService** - Risk assessment
19. **MomentumService** - Momentum analysis
20. **VolatilityService** - Volatility calculation

### Tier 4: ML Services (Prediction)
21. **MLService** - Model training/inference
22. **PricePredictionService** - Time-series forecasting
23. **AnomalyDetectionService** - Outlier detection
24. **ClusteringService** - Pattern clustering
25. **ReinforcementLearnerService** - RL models
26. **EnsembleService** - Model ensemble voting

### Tier 5: NLP Services (Sentiment)
27. **SentimentAnalysisService** - Persian sentiment
28. **NewsAnalysisService** - News processing
29. **NLPService** - Natural language processing
30. **EntityExtractionService** - Named entity extraction
31. **SummarizationService** - Text summarization

### Tier 6: User Services (Personalization)
32. **UserService** - User management
33. **AuthService** - Authentication/JWT
34. **SubscriptionService** - Subscription management
35. **PreferenceService** - User preferences
36. **AlertService** - Alert management
37. **NotificationService** - Multi-channel notifications

### Tier 7: Specialized Services (Advanced)
38. **HierarchyService** - 305-node hierarchy management
39. **AssistantService** - AI recommendations
40. **BacktestService** - Strategy backtesting
41. **PortfolioOptimizationService** - Portfolio optimization
42. **RegressionAnalysisService** - Statistical regression
43. **CorrelationService** - Correlation analysis

### Tier 8: Crypto Services (Multi-Asset)
44. **CryptoAnalysisService** - Cryptocurrency analysis
45. **ChainAnalysisService** - Blockchain analysis
46. **DeFiService** - DeFi protocol analysis
47. **TransactionService** - On-chain transactions
48. **WalletService** - Wallet monitoring

### Tier 9: System Services (Operations)
49. **DataRecoveryService** - Data recovery
50. **BackupService** - Backup management
51. **AuditService** - Audit logging
52. **PerformanceMonitor** - Performance tracking
53. **ErrorHandler** - Exception handling
54. **RateLimiter** - Rate limiting

---

## Core Data Models

### Primary Tables (PostgreSQL)

#### Assets
- `assets` - Stock/crypto universe
- `symbols` - Symbol metadata
- `exchanges` - Exchange information

#### Market Data
- `market_data` - OHLCV candles
- `technical_signals` - Technical indicators
- `fundamental_data` - Fundamental metrics
- `sentiment_scores` - News sentiment

#### Analysis
- `scores` - 6D scoring results
- `predictions` - ML predictions
- `anomalies` - Detected anomalies
- `correlations` - Asset correlations

#### User Data
- `users` - User accounts
- `portfolios` - Portfolio definitions
- `holdings` - Portfolio holdings
- `transactions` - Transaction history
- `alerts` - User alerts
- `subscriptions` - Subscription info

#### System
- `audit_log` - Audit trail
- `error_log` - Error tracking
- `performance_metrics` - System metrics

---

## Technology Stack (Consolidated)

### Backend
- **Framework**: FastAPI 0.100+
- **Server**: Uvicorn (ASGI)
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 14+
- **Cache**: Redis 7+

### Data Science
- **Data**: Pandas, NumPy
- **ML**: Scikit-learn, XGBoost, LightGBM
- **DL**: TensorFlow/Keras
- **Time-Series**: Statsmodels, Prophet
- **NLP**: Hazm, NLTK, Scikit-learn
- **Science**: SciPy

### Frontend
- **Framework**: Next.js 16+
- **UI**: React 19+
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4
- **Components**: shadcn/ui
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **State**: Zustand, React Query
- **Forms**: React Hook Form, Zod
- **Charts**: Recharts, Chart.js

### Testing
- **Backend**: Pytest, Coverage
- **Frontend**: Vitest, React Testing Library, Playwright
- **Load**: Locust, K6

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, ELK
- **Logging**: Structured logging

---

## 6D Scoring System (Core Algorithm)

### Dimensions (Weight Distribution)
```python
dimensions = {
    'fundamental': 0.25,      # Financial health
    'technical': 0.20,        # Chart patterns
    'sentiment': 0.15,        # News & sentiment
    'risk': 0.20,             # Volatility & drawdown
    'macro': 0.10,            # Economic indicators
    'ai': 0.10                # ML prediction
}

# Normalized to 100-point scale
final_score = sum(weight * score for weight, score in dimensions.items())
```

### Scoring Hierarchy (305 Nodes)
```
Level 1 (12): Dimensions
├── Level 2 (40): Sub-Dimensions
│   ├── Level 3 (80): Aspects
│   │   ├── Level 4 (173): Sub-Aspects
```

---

## Technical Indicators (50+)

### Moving Averages (4)
- SMA, EMA, WMA, TEMA

### Momentum (5)
- RSI, MACD, Stochastic, KDJ, CCI

### Volatility (4)
- Bollinger Bands, ATR, KAMA, Donchian

### Trend (4)
- ADX, Ichimoku, Parabolic SAR, TRIX

### Volume (4)
- OBV, CMF, VPTK, AD

### Additional (20+)
- ROC, Williams %R, Ultimate Oscillator, etc.

---

## ML Pipeline

### Model Ensemble
1. **Random Forest** - 100 trees
2. **XGBoost** - Gradient boosting
3. **LightGBM** - Fast gradient boosting
4. **Neural Network** - LSTM for sequences
5. **SVM** - Support Vector Machine

### Training Pipeline
```
Raw Data → Preprocessing → Feature Engineering → Model Training → Validation → Deployment
```

### Coefficient Learning
```python
# Daily performance-based weight adjustment
coefficient_t = 0.8 * coefficient_t-1 + 0.2 * performance
performance = correlation(predictions, actual_returns)
```

---

## Frontend - Magic Design System

### Numerological Foundation
- **12**: Spatial perfection (grid system)
- **3**: Balance (animation speeds)
- **7**: Spiritual harmony
- **1.618**: Golden ratio (spacing)
- **Fibonacci**: [1, 1, 2, 3, 5, 8, 13, 21, 34]

### Color Kabbalah
- **FIRE (Red)**: Energy, action
- **WATER (Blue)**: Intuition, connection
- **EARTH (Gray)**: Stability, security
- **AIR (Gold)**: Creativity, inspiration

### Animation Framework (3-7-3)
- 300ms: Quick interactions
- 700ms: Transitions
- 3000ms: Ambient effects

---

## API Structure (16+ Routers)

### Authentication
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

### Stocks
- `GET /stocks/list`
- `GET /stocks/{symbol}`
- `GET /stocks/{symbol}/history`
- `GET /stocks/{symbol}/analysis`
- `GET /stocks/{symbol}/fundamental`

### Analysis
- `GET /analysis/scores`
- `GET /analysis/signals`
- `GET /analysis/predict`
- `GET /analysis/backtest`

### Portfolio
- `POST /portfolio/create`
- `GET /portfolio/{id}`
- `POST /portfolio/{id}/add`
- `GET /portfolio/{id}/optimization`

### Alerts
- `POST /alerts/create`
- `GET /alerts`
- `PUT /alerts/{id}`
- `DELETE /alerts/{id}`

### Ranking
- `GET /ranking/general`
- `GET /ranking/sector`
- `GET /ranking/by-score`

### Market
- `GET /market/overview`
- `GET /market/indices`
- `GET /market/sectors`

### News
- `GET /news/search`
- `GET /news/{symbol}`
- `GET /news/sentiment`

---

## Development Timeline

### Week 1: Foundation
- [ ] Directory structure
- [ ] PostgreSQL schema
- [ ] Redis setup
- [ ] FastAPI template
- [ ] Next.js template

### Week 2: Core Backend
- [ ] 15 core services
- [ ] Database layer
- [ ] Authentication
- [ ] API routes (stock/market)

### Week 3: Advanced Backend
- [ ] 6D scoring engine
- [ ] Technical analysis
- [ ] ML pipeline
- [ ] NLP services

### Week 4: Frontend
- [ ] Magic design system
- [ ] Dashboard
- [ ] Components library
- [ ] State management

### Week 5: Integration & Testing
- [ ] E2E tests
- [ ] Performance testing
- [ ] Load testing
- [ ] Deployment

---

## Success Criteria

✅ **Backend**
- [ ] 50+ services implemented
- [ ] 16+ API routers
- [ ] 16+ database tables
- [ ] <100ms API response time
- [ ] >99% uptime

✅ **Frontend**
- [ ] 50+ React components
- [ ] Magic design system
- [ ] Real-time data updates
- [ ] <3s page load
- [ ] 90+ Lighthouse score

✅ **ML**
- [ ] Ensemble predictions
- [ ] >85% accuracy
- [ ] Daily coefficient updates
- [ ] Anomaly detection

✅ **NLP**
- [ ] Persian sentiment analysis
- [ ] Named entity extraction
- [ ] Text summarization
- [ ] Impact scoring

---

## Notes

- **Code Origin**: 100% fresh rewrite using learned patterns
- **Business Logic**: Consolidated from 5 OldFils projects
- **Testing**: Comprehensive test coverage (unit, integration, e2e)
- **Documentation**: Complete API and architecture docs
- **Deployment**: Containerized with Docker
- **Monitoring**: Full observability stack

