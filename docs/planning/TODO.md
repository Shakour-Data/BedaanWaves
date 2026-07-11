# TODO List - BedaanWaves

## Phase 1: Project Setup & Foundation
- [x] Project structure initialization
- [x] Database schema design
- [x] Environment configuration
- [x] Dependency management

## Backend Services

### Tier 1: Core Services (Completed - 6 services, 1,270 LOC)
- [x] DependencyContainer (IoC/DI management)
- [x] ConfigService (Centralized configuration)
- [x] LoggerService (Structured logging)
- [x] CacheService (Multi-backend caching)
- [x] DatabaseService (Connection pooling)
- [x] HealthChecker (System monitoring)

### Tier 2: Data Services (Completed - 6 services, 930 LOC)
- [x] BrsApiClient (Tehran Stock Exchange API)
- [x] StockService (Stock data management)
- [x] MarketService (Market data aggregation)
- [x] PortfolioService (Portfolio operations)
- [x] HistoryService (Historical data)
- [x] NewsService (News integration)

### Tier 3: Analysis Services (Completed - 6 services, 1,480 LOC)
- [x] ScoringService (6D scoring - 305-node hierarchy)
- [x] TechnicalAnalysisService (50+ indicators)
- [x] FundamentalAnalysisService (20+ ratios)
- [x] RiskAnalysisService (VaR, Sharpe, stress testing)
- [x] MomentumService (Momentum analysis)
- [x] VolatilityService (Volatility forecasting)

### Tier 4: ML Services (Completed - 6 services)
- [x] PredictionService
- [x] PatternRecognitionService
- [x] AnomalyDetectionService
- [x] RecommendationService
- [x] PortfolioOptimizationService
- [x] TimeSeriesForecastingService

### Tier 5: NLP Services (Completed - 5 services)
- [x] SentimentAnalysisService (Persian sentiment)
- [x] NewsSummarizationService
- [x] DocumentExtractionService
- [x] ChatbotService
- [x] SearchService

### Tier 6: User Services (Completed - 6 services)
- [x] AuthenticationService (`auth_service.py` + `/auth` routes)
- [x] AuthorizationService (`app/services/user/authorization_service.py` - role/permission resolution)
- [x] UserProfileService (`app/services/user/user_profile_service.py`)
- [x] WatchlistService (`app/services/user/watchlist_service.py` + `/watchlists` routes)
- [x] NotificationService (`app/services/user/notification_service.py` + `/notifications` routes)
- [x] PreferenceService (`app/services/user/preference_service.py`)

### Tier 7: Specialized Services (Completed - 5 services, ~1,120 LOC)
- [x] SectorAnalysisService (sector aggregation & ranking)
- [x] ScreeningService (flexible universe filtering)
- [x] ComparisonService (cross-symbol metric comparison)
- [x] CorrelationService (return correlation matrix & pair detection)
- [x] CalendarService (TSE trading days & corporate events)

### Tier 8: Crypto Services (Pending - 5 services)
- [ ] CryptoPriceService
- [ ] CryptoPortfolioService
- [ ] CryptoAnalysisService
- [ ] CryptoNewsService
- [ ] CryptoArbitrageService

### Tier 9: System Services (Pending - 6 services)
- [ ] BackupService
- [ ] LoggingService
- [ ] MetricsService
- [ ] QueueService
- [ ] SchedulerService
- [ ] NotificationDispatcherService

## Backend API
- [x] Implement FastAPI routes for all implemented tiers (`market`, `analysis`, `stocks`, `portfolios`, `history`, `news`, `auth`, `ml`, `live`, `specialized`, `users`, `watchlists`, `notifications`)
- [x] API versioning (`/api/v1` prefix)
- [x] Request/response validation (Pydantic schemas in `app/schemas`)
- [x] Authentication & authorization middleware (global guard via `AuthGuardMiddleware` + router-level `Depends(get_current_active_user)`; gated by `REQUIRE_AUTH`, default off for local dev)
- [x] Rate limiting (`RateLimitMiddleware`, in-memory sliding window)
- [x] API documentation (Swagger/OpenAPI at `/api/v1/docs`)
- [x] Error handling middleware (`app/api/dependencies.py` / exception handlers)
- [x] CORS configuration (`CORSMiddleware` in `main.py`)

## Database
- [x] Alembic migration setup (existing `backend/database/alembic` + initial migration)
- [x] Create migrations for all models (initial migration present)
- [x] Run initial migrations (verified via `alembic current` + `check_tables.py`)
- [ ] Database indexes optimization
- [x] Seed data scripts
- [ ] Backup & restore strategy
- [ ] Performance tuning

## Frontend (Next.js)
- [x] Project setup and configuration (`package.json`, `next.config.ts`, `tsconfig.json`)
- [ ] Component library setup (shadcn/ui or similar)
- [ ] Authentication pages (login/register)
- [x] Dashboard layout
  - **App Shell**: `components/layout/Sidebar.tsx`, `Topbar.tsx`, `DashboardShell.tsx` (RTL, responsive, dark-mode)
  - **Dashboard Widgets**: market stats, top movers, watchlist, ML signals, news (`components/dashboard/*`, `app/dashboard/*`)
  - **Backend Integration**: `lib/api/dashboard.ts` fetches live data from `/market/tse-dashboard` & `/market/latest-prices` with mock fallback
  - **Tooling Fixes**: ESLint flat config repaired; `@tailwindcss/postcss` dependency added; design tokens + dark theme in `globals.css`
- [x] Stock detail pages (`app/stocks/page.tsx`, `app/stocks/[symbol]/page.tsx`, `layout.tsx`)
- [ ] Portfolio management pages
- [x] Charts and visualizations (`components/charts/CandlestickChart.tsx`)
- [ ] News feed page (widget exists; dedicated page pending)
- [ ] Analysis reports pages
- [ ] Admin panel
- [ ] Responsive design
- [x] State management (Zustand — `store/useAppStore.ts`)

## Testing
- [x] Unit tests for Tier 1 services (7 test modules: base, cache, config, database, dependency_container, health_checker, logger)
- [x] Unit tests for Tier 2 services (6 test modules: brs_api_client, history, stock, portfolio, news, market)
- [x] Unit tests for Tier 3 services (6 test modules: technical, scoring, risk, fundamental, volatility, momentum - 174 tests)
- [ ] Unit tests for Tier 4 (ML) services (no test modules yet)
- [~] Unit tests for Tier 5-9 services (Tier 6 modules exist but failing; Tier 7 covered - 24 tests in `test_specialized_services.py`; Tier 5/8/9 missing)
- [ ] Integration tests for API routes
- [ ] Database integration tests
- [ ] E2E tests (Playwright/Cypress)
- [ ] Test coverage reporting (>80%)
- [ ] Mock external API responses

## Documentation
- [x] Project architecture documentation (AGENTS.md)
- [x] Progress tracking (REWRITE_PROGRESS.md)
- [ ] API documentation
- [ ] Deployment guide
- [ ] Developer setup guide
- [ ] User manual
- [ ] Contributing guidelines

## DevOps & Deployment
- [ ] Production environment setup
- [ ] Environment variable management
- [ ] Docker compose for development (optional)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring & logging setup
- [ ] Security audit
- [ ] Performance optimization
- [ ] Load testing

## Known Issues & Technical Debt
- [ ] **Test coverage gap**: `HealthChecker` (Tier 1 system monitoring) uses `psutil` for memory/disk/CPU metrics but has no unit tests. Add tests covering metric collection, thresholds, and failure paths.
- [x] Replace TODO.md with comprehensive project tracker (synced to actual code state — Tiers 1-7 marked complete)
- [~] Implement proper error handling in all services (global exception handlers in `main.py` / `api/dependencies.py`; partial — service-level handling not yet uniform)
- [~] Add comprehensive input validation (Pydantic schemas exist; partial — not yet enforced across all endpoints/services)
- [x] Implement request logging with correlation IDs (`CorrelationIdMiddleware` sets `X-Correlation-ID` on every response)
- [ ] Add metrics collection for all services (MetricsService is Tier 9 — pending)

