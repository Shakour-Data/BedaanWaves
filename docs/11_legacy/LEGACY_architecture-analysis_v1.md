# OldFils Projects - Complete Architectural Analysis

**Analysis Date:** July 29, 2026 (Updated)  
**Analyst:** Kilo Software Engineer  
**Scope:** 5 Projects ? Unified BedaanWaves Platform  
**Status:** Phase 1-3 Implementation Complete (~85%)

---

## Executive Summary

The OldFils collection contains 5 sophisticated financial intelligence projects:

1. **.kilo** - Configuration and agent management layer
2. **Bedaan_4D_AI** - Data archive (SQLite databases)
3. **Bedaan4D-ML** - Python backend with FastAPI and 50+ services
4. **Bedaan6D-project** - React/Next.js frontend with magic design system

**Key Statistics:**
- 500+ Python files (Backend)
- 100+ TypeScript/React files (Frontend)
- 305 hierarchy nodes (Scoring system)
- 50+ services and APIs
- 16+ database tables
- 12+ frontend pages/sections

---

## Project Inventory

| Project | Purpose | Type | Primary Language | Status |
|---------|---------|------|------------------|--------|
| .kilo | Kilo configuration | Config | YAML/Markdown | Active |
| Bedaan_4D_AI | Data archive | Database | SQLite | Archive |
| Bedaan4D-ML | Backend API | Backend | Python 3.10+ | Production |
| Bedaan6D-project | Stock UI | Frontend | TypeScript/React | Production |


# PART 1: PROJECT ANALYSIS

## Project 1: .kilo - Kilo Configuration & Agent Management

### Location
\E:\Shakour\BedaanProjects\OldFils\.kilo\

### Structure
- agents/data.md - Notebook-first data analysis agent configuration
- skills/ - Skill definitions
- package.json - Kilo framework dependency (@kilocode/plugin v7.4.1)
- node_modules/ - Dependencies

### Purpose
Central configuration point for Kilo development environment integration.

### Agent Definition (agents/data.md)
- **Mode:** Primary (notebook-first)
- **ID:** data
- **Display Name:** Data
- **Color:** Blue (#2563EB)
- **Requirements:**
  - Skills: data-investigation
  - VS Code Extensions: Jupyter (ms-toolsai.jupyter)

### Features
- Notebook-first workflow (Jupyter)
- Cell execution and history preservation
- Kernel management
- Data analysis support

---

## Project 2: Bedaan_4D_AI - Data Archive

### Location
\E:\Shakour\BedaanProjects\OldFils\Bedaan_4D_AI\

### Structure
\\\
data/
  +-- TechAnalysis.db      (Technical analysis data)
  +-- market_data.db      (Market data storage)
database/
  +-- init_aras.sql        (Initial schema)
\\\

### Database Inventory
- **TechAnalysis.db**: Technical indicators and calculations
- **market_data.db**: Market data and quotes
- **Aras Schema**: Initialized database structure

### Purpose
Archive of historical financial data for backup and reference.

### Technology
- SQLite 3 (file-based database)
- SQL schema definition

### Characteristics
- Read-only archive
- Historical backup source
- Fallback data availability

---

## Project 3: Bedaan4D-ML - Backend System

### Location
\E:\Shakour\BedaanProjects\OldFils\Bedaan4D-ML\

### Core Statistics
- **Python Files:** 500+
- **Services:** 50+
- **API Routes:** 16+
- **Database Tables:** 16+
- **Code Lines:** 50,000+

### Architecture Layers

#### Layer 1: Application Entry Points
- \pp_factory.py\ - FastAPI application factory (391 lines)
- \main.py\ - Application startup
- \server.py\ - Server configuration
- \
un.py\ - Runner script

#### Layer 2: Middleware Stack
1. CORS Middleware - Cross-origin requests
2. GZip Compression - Response compression
3. Rate Limiting - DDoS protection (100 req/min)
4. Security Headers - HSTS, CSP, X-Frame-Options
5. Authentication - JWT token validation
6. Request Logging - Audit trail
7. Performance Monitoring - Metrics collection
8. Error Handling - Exception processing

#### Layer 3: API Routes (16 Routers)

\\\python
POST   /auth/register              # User registration
POST   /auth/login                 # Authentication
POST   /auth/refresh               # Token refresh

GET    /stocks/list                # Stock list
GET    /stocks/{symbol}            # Stock details
GET    /stocks/{symbol}/history    # Price history
GET    /stocks/{symbol}/analysis   # Technical analysis
GET    /stocks/{symbol}/fundamental # Fundamental data

POST   /portfolio/create           # Create portfolio
GET    /portfolio/{id}             # Portfolio details
POST   /portfolio/{id}/add         # Add holdings

GET    /ranking/general            # Overall ranking
GET    /ranking/sector             # Sector ranking

POST   /alerts/create              # Create alert
GET    /alerts                     # Get alerts

GET    /analysis/predict           # Price prediction
GET    /analysis/backtest          # Backtest results

POST   /news/search                # News search
GET    /news/{symbol}              # Stock news

GET    /system/health              # System status
\\\

#### Layer 4: Services (50+ Services)

**Data Services:**
1. \YahooFinanceClient\ - Yahoo Finance API integration
2. \StockService\ (1379 lines) - Stock data management
3. \MarketService\ - Market-wide analysis
4. \PortfolioService\ - Portfolio operations
5. \NewsService\ - News aggregation

**Analysis Services:**
6. \ScoringService\ - 6D scoring calculations
7. \TechnicalAnalysisService\ - Technical indicators (50+ indicators)
8. \FundamentalAnalysisService\ - Fundamental metrics
9. \RiskAnalysisService\ - Risk assessment

**ML Services:**
10. \MLService\ - Model training/inference
11. \PricePredictionService\ - Time-series forecasting
12. \AnomalyDetectionService\ - Outlier detection
13. \ReinforcementLearnerService\ - RL models

**NLP Services:**
14. \SentimentAnalysisService\ - Persian sentiment
15. \NewsAnalysisService\ - News processing
16. \NLPService\ - Natural language processing

**User Services:**
17. \UserService\ - User management
18. \AuthService\ - Authentication
19. \SubscriptionService\ - Subscription management
20. \AlertService\ - Alert management

**Specialized Services:**
21. \AssistantService\ - AI recommendations
22. \BacktestService\ - Strategy backtesting
23. \DataRecoveryService\ - Data recovery
24. \CacheManagementService\ - Redis caching
25. \HealthMonitor\ - System health
26. \PerformanceMonitor\ - Performance tracking
... (25+ more services)

#### Layer 5: Core Components (20+ Components)

1. \DependencyContainer\ - Dependency injection
2. \ErrorHandler\ - Error management
3. \HooksSystem\ - Event hooks
4. \CachingManager\ - Cache management
5. \ResponseFormatter\ - API responses
6. \HealthChecker\ - Health checks
7. \RateLimiter\ - Rate limiting
8. \JWTService\ - JWT handling
9. \DatabasePool\ - Connection pooling
10. \Logger\ - Structured logging
... (10+ more)

#### Layer 6: Data Access Layer

**Database (PostgreSQL)**
- stocks - Stock metadata (1000+ rows)
- market_data - OHLCV data (1M+ rows)
- scores - Scoring results (time-series)
- predictions - ML predictions
- kpi_history - KPI tracking
- users - User accounts
- portfolios - Portfolio data
- alerts - Alert definitions
- subscriptions - User subscriptions
- technical_signals - Technical indicators
- fundamental_data - Fundamental metrics
- sentiment_scores - News sentiment
- anomalies - Detected anomalies
- audit_log - Audit trail
- error_log - Error tracking

**Cache Layer (Redis)**
- Session data
- User preferences
- Score cache (TTL: 24 hours)
- API responses (TTL: 5 mins)
- Rate limit counters

#### Layer 7: External Integrations

 1. **Yahoo Finance API** (finance.yahoo.com)
    - Stock data
    - Market data
    - Real-time quotes

 2. **News APIs**
   - News articles
   - News search
   - News archives

 3. **Email Service**
   - Alert notifications
   - Report delivery

 4. **SMS Provider**
   - High-priority alerts

### Technology Stack

#### Core Framework
- FastAPI 0.100+ (Async web framework)
- Uvicorn (ASGI server)
- Python 3.10+
- Starlette (Web library)

#### Database
- PostgreSQL (Primary)
- Redis (Cache)
- SQLAlchemy (ORM)
- Alembic (Migrations)

#### Data Science
- Pandas (Data manipulation)
- NumPy (Numerical)
- Scikit-learn (ML)
- TensorFlow/Keras (Deep learning)
- XGBoost (Gradient boosting)
- Scipy (Scientific computing)

#### API & Integration
- Requests (HTTP)
- BeautifulSoup4 (Web scraping)
- Celery (Task queue)
- APScheduler (Job scheduling)

#### NLP
- Hazm (Persian text processing)
- NLTK (NLP toolkit)
- Scikit-learn (Text classification)

#### Testing
- Pytest
- Coverage
- Hypothesis (Property testing)

#### Monitoring
- Prometheus (Metrics)
- ELK Stack (Logging)
- Custom health checks

### Key Algorithms

#### 6D Scoring System
\\\
fundamental_score (25%)
technical_score (20%)
sentiment_score (15%)
risk_score (20%)
macro_score (10%)
ai_score (10%)

final_score = S(weight × score)
normalized to 1-100
\\\

#### ML Coefficient Learning
\\\
coefficient_t = 0.8 × coefficient_t-1 + 0.2 × performance
performance = correlation with actual returns
ensemble: Random Forest, XGBoost, LightGBM, NN, SVM
\\\

#### Technical Indicators (50+)
- Moving Averages: SMA, EMA, WMA, TEMA
- Momentum: RSI, MACD, Stochastic, KDJ, CCI
- Volatility: Bollinger Bands, ATR, KAMA
- Trend: ADX, Ichimoku, Parabolic SAR
- Volume: OBV, CMF, VPTK

---

## Project 4: Bedaan6D-project - Frontend UI

### Location
\E:\Shakour\BedaanProjects\OldFils\Bedaan6D-project\

### Core Statistics
- **React Components:** 50+
- **Pages:** 5+
- **Services:** 7 (API, Symbol, Scoring, Hierarchy, History, Todo, Magic)
- **UI Components:** 40+ (shadcn/ui)
- **Test Files:** 20+

### Architecture - The 6D Magic System

The frontend implements a sophisticated design system based on:

#### Numerology Principles
- **12**: Spatial perfection (12-column grid)
- **3**: Balance and harmony (3 animation speeds)
- **7**: Spiritual harmony
- **1.618**: Golden ratio (Fibonacci)
- **Fibonacci**: [1, 1, 2, 3, 5, 8, 13, 21, 34]

#### Color Kabbalah
- **FIRE (Red #C62828)**: Energy, action, passion
- **WATER (Blue #1565C0)**: Calm, intuition, connection
- **EARTH (Gray #F5F5F5)**: Stability, security, reality
- **AIR (Gold #FFD54F)**: Light, creativity, inspiration

#### Animation Framework - 3-7-3 Rule
- 300ms - Quick interactions
- 700ms - Transitions
- 3000ms - Ambient effects

### Directory Structure

\\\
src/
+-- app/                          # Next.js App Router
¦   +-- api/
¦   ¦   +-- hierarchy/
¦   ¦   +-- symbols/
¦   ¦   +-- scores/
¦   +-- layout.tsx               # Root layout
¦   +-- page.tsx                 # Home page
¦   +-- error.tsx                # Error boundary
¦   +-- globals.css              # Global styles

+-- components/                  # React components
¦   +-- magic/                  # Magic system
¦   ¦   +-- MagicButton.tsx
¦   ¦   +-- MagicCard.tsx
¦   ¦   +-- MagicForm.tsx
¦   ¦   +-- MagicGrid.tsx
¦   ¦   +-- MagicTypography.tsx
¦   +-- ui/                     # shadcn/ui (40+ components)
¦   ¦   +-- accordion.tsx
¦   ¦   +-- alert.tsx
¦   ¦   +-- button.tsx
¦   ¦   +-- card.tsx
¦   ¦   +-- dialog.tsx
¦   ¦   +-- dropdown-menu.tsx
¦   ¦   +-- form.tsx
¦   ¦   +-- input.tsx
¦   ¦   +-- tabs.tsx
¦   ¦   +-- ... (30+ more)
¦   +-- pages/                  # Page components
¦       +-- DashboardTab.tsx
¦       +-- CompaniesTab.tsx
¦       +-- HierarchyExplorer.tsx
¦       +-- ...

+-- contexts/                    # React Context
¦   +-- MagicContext.tsx        # Magic system state

+-- hooks/                       # Custom hooks
¦   +-- use-mobile.ts           # Mobile detection
¦   +-- use-magic-api.ts        # API management

+-- lib/                         # Utilities
¦   +-- design-tokens.ts        # Design tokens
¦   +-- utils.ts                # Helpers
¦   +-- hierarchy.ts            # Hierarchy logic
¦   +-- scoring.ts              # Scoring calculations
¦   +-- persian.ts              # Persian utilities
¦   +-- references.ts           # References
¦   +-- prisma.ts               # Prisma setup

+-- services/                    # API services
¦   +-- magic-api.ts            # API client
¦   +-- symbol-service.ts       # Symbol management
¦   +-- scoring-service.ts      # Scoring logic
¦   +-- hierarchy-service.ts    # Hierarchy logic
¦   +-- history-service.ts      # History management
¦   +-- todo-service.ts         # Todo management

+-- stores/                      # State (Zustand)
¦   +-- magicStore.ts           # Magic system state
¦   +-- __tests__/

+-- test/                        # Tests
¦   +-- api-routes.test.ts
¦   +-- components/
¦   +-- services/
¦   +-- ...

+-- prisma/
¦   +-- schema.prisma           # Database schema
¦   +-- seed.ts                 # Seed data

+-- package.json                 # Dependencies
+-- tsconfig.json                # TypeScript config
+-- next.config.js               # Next.js config
+-- tailwind.config.ts           # Tailwind config
+-- vitest.config.ts             # Vitest config
+-- playwright.config.ts         # Playwright config
+-- eslint.config.js             # ESLint config
\\\

### Technology Stack

#### Frontend Framework
- **Next.js 16.2.9** - React meta-framework
- **React 19.2.7** - UI library
- **TypeScript 5** - Type safety
- **Turbopack** - Next-gen bundler

#### UI & Styling
- **Tailwind CSS 4** - Utility-first CSS
- **shadcn/ui** - Component library (40+ components)
- **class-variance-authority (0.7.1)** - Component variants
- **Lucide React 0.525.0** - Icon library (350+ icons)
- **Framer Motion 12.23.2** - Animations

#### State Management
- **Zustand 5.0.6** - State management
- **React Context** - Local state
- **TanStack React Query 5.82.0** - Server state
- **TanStack React Table 8.21.3** - Advanced tables

#### Forms & Validation
- **React Hook Form 7.60.0** - Form handling
- **Zod 4.0.2** - Schema validation

#### Data & Database
- **Prisma Client 6.11.1** - ORM
- **PostgreSQL (pg 8.22.0)** - Database

#### Testing
- **Vitest 4.1.9** - Unit tests
- **React Testing Library 16.3.2** - Component tests
- **Playwright 1.61.1** - E2E tests
- **@testing-library/jest-dom 6.9.1** - Matchers

#### Additional Libraries
- **date-fns 4.1.0** - Date manipulation
- **uuid 14.0.0** - ID generation
- **jszip 3.10.1** - ZIP handling
- **sharp 0.34.3** - Image processing
- **recharts 3.8.1** - Charts
- **react-markdown 10.1.0** - Markdown
- **react-syntax-highlighter 16.1.1** - Code highlighting
- **embla-carousel-react 8.6.0** - Carousels
- **react-resizable-panels 3.0.3** - Resizable panels
- **sonner 2.0.6** - Toast notifications
- **vaul 1.1.2** - Dialog management

### Key Components

#### Magic System Components
1. **MagicButton** - Interactive button with glow effects
2. **MagicCard** - Container with shadow layering
3. **MagicForm** - Form with validation
4. **MagicGrid** - 12-column layout
5. **MagicTypography** - Fibonacci-scaled text

#### Dashboard Components
1. **DashboardTab** - Main dashboard
2. **CompaniesTab** - Company comparison
3. **DimensionCard** - 6D score display
4. **DimensionSpiderChart** - Radar chart
5. **HierarchyExplorer** - Tree navigation
6. **ScoreTickerBar** - Live ticker

### Services

#### MagicAPI Service
- Centralized HTTP client
- Retry logic with exponential backoff
- Error handling
- Response formatting
- Caching strategy

#### SymbolService
- Symbol data management
- Market data retrieval
- Symbol search
- Historical data fetching

#### ScoringService
- Score calculations
- Weight aggregation
- Trend analysis
- Change calculations

#### HierarchyService
- Tree navigation
- Node relationships
- Search functionality
- Breadcrumb generation

### State Management (Zustand Store)

\\\	ypescript
magicStore = {
  // UI State
  activeElement: 'fire' | 'water' | 'earth' | 'air',
  colorMode: 'light' | 'dark' | 'auto',
  energyLevel: 1-7,
  animationEnabled: boolean,
  
  // Data State
  selectedSymbol: string,
  selectedNode: HierarchyNode,
  dateRange: DateRange,
  
  // Loading State
  isLoading: boolean,
  error: Error | null,
  
  // Actions
  setActiveElement(),
  setColorMode(),
  setEnergyLevel(),
  selectSymbol(),
  selectNode(),
}
\\\

### Database Schema (Prisma)

Tables defined in \prisma/schema.prisma\:
- MainDimension
- SubDimension
- Aspect
- SubCategory
- Symbol
- MarketData
- Score
- News
- Shareholder
- BrokerTop5
- MarketDataSnapshot
- HistoryRecord

---

### Data Flow Between Projects

External APIs
  +- Yahoo Finance API (US stocks)
  +- News APIs (Multiple)
  ?
Bedaan4D-ML (Backend)
  +- Data Collection
  +- Validation
  +- Transformation
  +- ML Processing
  +- Score Calculation
  ?
PostgreSQL/Redis
  +- Primary data store
  +- Cache layer
  +- Historical backup
  ?
Bedaan6D-project (Frontend)
  +- Display scores
  +- Show charts
  +- Manage portfolio
  +- Receive alerts

---

## PERFORMANCE METRICS

### API Performance (SLOs)
- Median response: <100ms
- 95th percentile: <300ms
- 99th percentile: <1s
- Error rate: <0.1%
- Availability: >99.9%

### Database Performance
- Query (indexed): <50ms
- Query (aggregation): <500ms
- Insert throughput: >1000 rows/sec
- Cache hit rate: >85%

### Frontend Performance
- Time to Interactive: <2s
- Largest Contentful Paint: <1.5s
- Cumulative Layout Shift: <0.1
- First Input Delay: <100ms

---

## SUMMARY

The OldFils project suite has been consolidated into BedaanWaves, a unified financial intelligence platform with:

 Advanced Architecture: 6D hierarchy with 305 nodes (ScoringService)
 ML Integration: 5-model ensemble learning (PredictionService, PatternRecognitionService, AnomalyDetectionService, RecommendationService, TimeSeriesForecastingService)
 Full Stack: Data to dashboard pipeline (backend implemented, frontend pending)
 Scalability: Async processing, Redis caching, connection pooling
 Rich Analysis: 50+ technical indicators, sentiment NLP, macro metrics
  Multi-Market: US Stocks (NASDAQ/NYSE) + International Exchanges
 User Experience: Planned modern React UI, real-time updates, responsive design
 Enterprise Ready: Error handling, monitoring, audit logging, backups

**Current Implementation Status:**
- **Backend**: 42+ services implemented across 9 tiers (Tiers 1-7 complete, Tier 9 3/6)
- **API**: 16 routers with 50+ endpoints, OpenAPI documentation
- **Database**: PostgreSQL with Alembic migrations, unified schema
- **Frontend**: Pending (Next.js 16+ planned)
- **Total Lines of Code**: ~15,000+ lines (backend)
- **Technology**: FastAPI, SQLAlchemy, PostgreSQL, Pydantic v2, Uvicorn

**Note**: This analysis was conducted during the planning phase (July 9, 2026). The actual implementation in BedaanWaves has progressed significantly. Refer to AGENTS.md and REWRITE_PROGRESS.md for current status.

---

## CONTACT & DOCUMENTATION

For detailed implementation information, refer to:
- docs/AGENTS.md - Current agent configuration and tier status
- docs/planning/REWRITE_PROGRESS.md - Detailed progress tracking
- docs/planning/IMPLEMENTATION_CHECKLIST.md - Execution checklist
- docs/integration/README_INTEGRATION.md - Current integration status
- backend/app/ - Actual implementation code

Generated: July 9, 2026  
Updated: July 29, 2026

