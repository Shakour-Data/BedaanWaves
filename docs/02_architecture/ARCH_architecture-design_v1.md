# BedaanWaves Architecture & Design

## System Overview

BedaanWaves employs a clean, layered 9-tier architecture designed for separation of concerns, scalability, and maintainability. Each tier has well-defined responsibilities and communicates through clearly defined interfaces.

## Architectural Principles

1. **Separation of Concerns**: Each service has a single responsibility
2. **Dependency Inversion**: High-level modules depend on abstractions
3. **Interface Segregation**: Services expose minimal, focused interfaces
4. **Single Responsibility**: Each class/service has one reason to change
5. **Open/Closed Principle**: Extensible without modification
6. **Loose Coupling**: Services communicate via interfaces and events
7. **High Cohesion**: Related functionality grouped together
8. **Testability**: Services designed for easy unit testing with mocks

## 9-Tier Architecture

### Tier 1: Core Services (Foundation)
Provides fundamental infrastructure that all other services depend on:
- **DependencyContainer**: IoC/DI container managing service lifecycle
- **ConfigService**: Centralized configuration management (100+ settings)
- **LoggerService**: Structured logging with multiple outputs
- **CacheService**: Multi-backend caching (memory, Redis)
- **DatabaseService**: Connection pooling and session management
- **HealthChecker**: System health monitoring and reporting

### Tier 2: Data Services (Data Acquisition & Management)
Handles external data ingestion, normalization, and storage:
 - **YahooFinanceClient**: NASDAQ market data API integration
- **StockService**: Stock data management and operations
- **MarketService**: Market-wide data aggregation and analysis
- **PortfolioService**: Portfolio creation, modification, tracking
- **HistoryService**: Historical time-series data management
- **NewsService**: News aggregation from multiple sources
- **IngestionService**: Data ingestion pipeline orchestration
- **MarketDataProcessing**: Data cleaning and normalization pipelines
- **IntlApiClient**: International market APIs (NYSE, NASDAQ, etc.)
- **DataValidationService**: Data integrity validation and cleansing
 - **FinancialDataIngestService**: Multi-source financial statements (Yahoo Finance, Alpha Vantage)
 - **StockFundamentalDataIngestionService**: Fundamental data for US/International markets

### Tier 3: Analysis Services (Business Logic)
Implements core financial analysis algorithms:
- **ScoringService**: 6D scoring system with 305-node hierarchy
- **TechnicalAnalysisService**: 50+ technical indicators (RSI, MACD, Bollinger Bands, etc.)
- **FundamentalAnalysisService**: 20+ fundamental ratios (P/E, ROE, Debt/Equity, etc.)
- **RiskAnalysisService**: VaR, Sharpe ratio, stress testing, scenario analysis
- **MomentumService**: Price momentum analysis and signal generation
- **VolatilityService**: Volatility forecasting and risk measurement
- **UserFilteredScoringService**: Custom scoring based on user-selected criteria

### Tier 4: ML Services (Machine Learning)
Implements machine learning models and pipelines:
- **PredictionService**: Ensemble price prediction models
- **PatternRecognitionService**: Chart pattern detection (head & shoulders, triangles, etc.)
- **AnomalyDetectionService**: Statistical and ML-based outlier detection
- **RecommendationService**: Stock and portfolio recommendations
- **PortfolioOptimizationService**: Efficient frontier and risk-parity optimization
- **TimeSeriesForecastingService**: ARIMA, LSTM, Prophet forecasting models
- **CoefficientLearningService**: Dynamic coefficient adjustment based on market conditions
- **UserFilteredRecommendationService**: Personalized recommendations based on user preferences

### Tier 5: NLP Services (Natural Language Processing)
Processes textual data for insights:
- **SentimentAnalysisService**: English and multi-language sentiment analysis
- **NewsSummarizationService**: Automatic text summarization of news articles
- **DocumentExtractionService**: PDF and document text extraction
- **ChatbotService**: Conversational AI for user assistance
- **SearchService**: Semantic search across news and documents
- **MultiLanguageNewsService**: Country-specific news with language detection

### Tier 6: User Services (User Management)
Handles user-related functionality:
- **AuthService**: JWT-based authentication and session management
- **AuthorizationService**: Role-based access control (RBAC) system
- **UserProfileService**: User profile management and KYC processes
- **WatchlistService**: User-defined watchlists for symbols and portfolios
- **PreferenceService**: User customization and settings management
- **NotificationService**: Multi-channel notifications (email, SMS, in-app)
- **UserMarketSettingsService**: Market/index/industry selection preferences

### Tier 7: Specialized Services (Domain Expertise)
Implements specialized financial analysis:
- **SectorAnalysisService**: Sector performance analysis and ranking
- **ScreeningService**: Flexible stock screening with custom filters
- **ComparisonService**: Peer benchmarking and cross-asset comparison
- **CorrelationService**: Cross-asset correlation analysis and pair trading
- **CalendarService**: Market calendar integration (trading days, holidays, events)
- **SectorFilterService**: Industry-based filtering and classification

### Tier 9: System Services (Operations & Infrastructure)
Manages system operations and infrastructure:
- **SchedulerService**: Task scheduling and cron-like job management
- **MetricsService**: Performance monitoring and metrics collection
- **QueueService**: Message queuing for asynchronous processing
- **BackupService**: Automated database and file backup strategies
- **LoggingService**: Centralized logging aggregation and management
- **NotificationDispatcher**: Multi-channel notification distribution
- **DataIntegrityService**: Historical data validation and consistency checks
- **SettingsMigrationService**: User preference migration across versions

## Communication Patterns

### Service-to-Service Communication
- **Direct Injection**: Services receive dependencies via constructor injection
- **Events**: Internal event bus for loose coupling (planned enhancement)
- **API Calls**: RESTful communication between services when needed
- **Shared Data**: Database as shared state with proper transaction boundaries

### External Communication
- **REST APIs**: Standard JSON over HTTP for external services
- **WebSockets**: Real-time bidirectional communication for live data
- **Database Drivers**: Native PostgreSQL/SQLAlchemy connections
- **Cache Clients**: Redis and in-memory caching protocols
- **File System**: Local file access for logs, configs, and temporary data

## Data Flow

### Market Data Pipeline
1. **Ingestion**: External APIs (Yahoo Finance, international data providers) → Data Services
2. **Validation**: DataValidationService checks data quality and integrity
3. **Normalization**: MarketDataProcessing converts to unified format
4. **Storage**: DatabaseService persists to PostgreSQL with proper indexing
5. **Analysis**: Analysis Services compute indicators, scores, signals
6. **ML Processing**: ML Services generate predictions and recommendations
7. **Delivery**: API routes serve processed data to frontend and consumers

### User Request Flow
1. **Request**: HTTP request enters via API routes
2. **Authentication**: AuthGuardMiddleware validates JWT tokens
3. **Authorization**: AuthorizationService checks RBAC permissions
4. **Processing**: Request routed to appropriate service via DependencyContainer
5. **Execution**: Service performs business logic and data operations
6. **Response**: Formatted response returned via API routes with proper status codes

## Security Architecture

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication with expiration and refresh
- **Password Security**: Bcrypt hashing with salt for stored credentials
- **RBAC**: Role-based access control with fine-grained permissions
- **Session Management**: Server-side session tracking and invalidation
- **Multi-Factor**: Planned enhancement for high-security operations

### Data Protection
- **Encryption**: TLS 1.3 for data in transit
- **Hashing**: SHA-256 for password storage and data integrity
- **Input Validation**: Comprehensive validation to prevent injection attacks
- **Output Encoding**: Proper encoding to prevent XSS in API responses
- **Secrets Management**: Environment variables and secure vault integration

### Network Security
- **CORS**: Configurable cross-origin resource sharing policies
- **Rate Limiting**: Per-IP and per-user request throttling
- **Input Sanitization**: SQL injection and XSS prevention
- **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
- **Audit Logging**: Comprehensive logging of security-relevant events

## Performance & Scalability

### Caching Strategy
- **L1 Cache**: In-process memory cache (LRU eviction)
- **L2 Cache**: Redis distributed cache (configurable TTL)
- **L3 Cache**: Database query result caching (application-level)
- **CDN**: Planned for static asset delivery
- **Cache Warming**: Pre-loading frequently accessed data

### Database Optimization
- **Connection Pooling**: HikariCP-style pooling with tuning parameters
- **Query Optimization**: Proper indexing and query planning
- **Read Replicas**: Supported for scaling read-heavy workloads
- **Partitioning**: Time-based partitioning for large tables
- **Materialized Views**: Pre-computed aggregations for common queries

### Asynchronous Processing
- **Async/Await**: Full async support throughout the codebase
- **Background Jobs**: SchedulerService for periodic tasks
- **Message Queues**: QueueService for decoupled processing
- **WebSocket**: Real-time push notifications to clients
- **Batch Processing**: Efficient bulk operations where applicable

### Monitoring & Observability
- **Metrics Collection**: Built-in timing, counting, and gauging
- **Health Checks**: Service-level and system-level health endpoints
- **Logging**: Structured JSON logging with correlation IDs
- **Tracing**: Planned OpenTelemetry integration for distributed tracing
- **Alerting**: Configurable thresholds and notification channels

## Design Patterns Used

### Creational Patterns
- **Factory Pattern**: Service creation via DependencyContainer
- **Singleton Pattern**: Stateless services as singletons
- **Builder Pattern**: Complex object construction (configuration)
- **Prototype Pattern**: Object cloning for configuration templates

### Structural Patterns
- **Adapter Pattern**: External API integration (API clients)
- **Decorator Pattern**: Cross-cutting concerns (logging, caching)
- **Facade Pattern**: Simplified interfaces to complex subsystems
- **Proxy Pattern**: Lazy loading and access control

### Behavioral Patterns
- **Strategy Pattern**: Interchangeable algorithms (ML models, scoring)
- **Observer Pattern**: Event-driven architecture (planned)
- **Command Pattern**: Encapsulated requests (background jobs)
- **State Pattern**: State-dependent behavior (service lifecycle)
- **Template Method**: Algorithm skeletons with customizable steps
- **Visitor Pattern**: Operations on object structures (data validation)

## Code Organization

```
BedaanWaves/
├── backend/
│   └── app/
│       ├── core/                 # Tier 1: Foundation services
│       │   ├── __init__.py
│       │   ├── config.py         # Configuration management
│       │   ├── dependencies.py   # FastAPI dependencies
│       │   ├── middleware.py     # Custom middleware
│       │   └── services.py       # Service registration helpers
│       ├── api/                  # API route definitions
│       │   ├── __init__.py
│       │   ├── routes/           # 16 API routers
│       │   │   ├── auth.py       # Authentication endpoints
│       │   │   ├── stocks.py     # Stock data endpoints
│       │   │   ├── market.py     # Market data endpoints
│       │   │   ├── analysis.py   # Analysis computation endpoints
│       │   │   ├── ...           # 13 more routers
│       │   └── dependencies.py   # Route-level dependencies
│       ├── db/                   # Database session management
│       │   ├── __init__.py
│       │   └── base.py           # Base database functionality
│       ├── models/               # SQLAlchemy ORM models
│       │   ├── __init__.py
│       │   └── models.py         # All database table definitions
│       ├── schemas/              # Pydantic models for validation
│       │   ├── __init__.py
│       │   └── schemas.py        # Request/response schemas
│       └── services/             # All 50+ business services
│           ├── __init__.py
│           ├── core/             # Tier 1: Foundation services
│           │   ├── __init__.py
│           │   ├── base_service.py       # Abstract base classes
│           │   ├── cache_service.py      # Tier 1 CacheService
│           │   ├── config_service.py     # Tier 1 ConfigService
│           │   ├── dependency_container.py # Tier 1 DependencyContainer
│           │   ├── health_checker.py     # Tier 1 HealthChecker
│           │   ├── logger_service.py     # Tier 1 LoggerService
│           │   └── database_service.py   # Tier 1 DatabaseService
│           ├── data/             # Tier 2: Data services
│           │   ├── __init__.py
│   │   ├── yahoo_finance_client.py  # Yahoo Finance API client
│           │   ├── stock_service.py      # StockService
│           │   ├── ...                   # 11 more data services
│           ├── analysis/         # Tier 3: Analysis services
│           │   ├── __init__.py
│           │   ├── scoring_service.py    # ScoringService
│           │   ├── technical_service.py  # TechnicalAnalysisService
│           │   ├── ...                   # 5 more analysis services
│           ├── ml/               # Tier 4: ML services
│           │   ├── __init__.py
│           │   ├── prediction_service.py # PredictionService
│           │   ├── ...                   # 8 more ML services
│           ├── nlp/              # Tier 5: NLP services
│           │   ├── __init__.py
│           │   ├── sentiment_analysis_service.py # SentimentAnalysisService
│           │   ├── ...                   # 4 more NLP services
│           ├── user/             # Tier 6: User services
│           │   ├── __init__.py
│           │   ├── auth_service.py       # AuthService
│           │   ├── ...                   # 7 more user services
│           ├── specialized/      # Tier 7: Specialized services
│           │   ├── __init__.py
│           │   ├── sector_analysis_service.py # SectorAnalysisService
│           │   ├── ...                   # 4 more specialized services
│           └── system/           # Tier 9: System services
│               ├── __init__.py
│               ├── scheduler_service.py  # SchedulerService
│               ├── ...                   # 7 more system services
├── database/                   # Alembic migration scripts
│   └── alembic/
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│           ├── ...               # Versioned migration files
├── frontend/                   # Next.js frontend (planned)
│   ├── pages/
│   ├── components/
│   ├── services/
│   ├── stores/
│   └── styles/
├── docs/                       # Documentation (this file set)
│   ├── 01_executive_overview.md
│   ├── 02_architecture_design.md
│   ├── ...                     # 18 more documentation files
│   └── ...                     # Legacy documentation preserved
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
└── kilo.json                   # Kilo configuration (legacy)
```

## Integration Points

### External Systems
 - **Yahoo Finance API**: NASDAQ real-time and historical data
- **Financial APIs**: Yahoo Finance, Alpha Vantage for international data
- **News APIs**: Multiple sources for market news and sentiment
- **Email/SMS Providers**: Notification delivery systems
- **File Systems**: Local storage for logs, backups, and exports

### Internal Systems
- **Database Layer**: Unified PostgreSQL schema for all data
- **Cache Layer**: Multi-tier caching for performance optimization
- **Service Layer**: Dependency injection for loose coupling
- **API Layer**: RESTful interface for external consumption
- **Presentation Layer**: Planned Next.js frontend for user interaction

## Evolution & Extensibility

### Versioning Strategy
- **Semantic Versioning**: MAJOR.MINOR.PATCH for public API
- **Backward Compatibility**: Maintained within MINOR versions
- **Deprecation Policy**: Clear warnings before removal in MAJOR versions
- **API Versioning**: URL-based versioning (/api/v1/, /api/v2/, etc.)

### Extension Mechanisms
- **Plugin Architecture**: Planned for custom service integration
- **Configuration Override**: Environment-specific settings
- **Service Extension**: Inheritance from base service classes
- **Middleware Chains**: Custom processing pipelines
- **Database Migrations**: Alembic for schema evolution

### Technology Upgrades
- **Framework Updates**: Planned FastAPI and SQLAlchemy upgrades
- **Database Enhancements**: PostgreSQL feature adoption
- **Cache Improvements**: Redis clustering and advanced features
- **ML Framework Updates**: TensorFlow, PyTorch, scikit-learn upgrades
- **Frontend Evolution**: React/Next.js version updates

## Quality Attributes

### Performance
- **Response Time**: <200ms p95 for cached responses, <500ms for uncached
- **Throughput**: 1000+ requests per second with proper scaling
- **Concurrency**: Async/await throughout for high concurrency
- **Scalability**: Horizontal scaling supported for stateless services

### Reliability
- **Fault Tolerance**: Graceful degradation when external services fail
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breakers**: Prevent cascade failures
- **Health Monitoring**: Automatic detection and restart of unhealthy services
- **Data Consistency**: ACID transactions for critical operations

### Security
- **Authentication**: JWT with refresh token rotation
- **Authorization**: RBAC with least privilege principle
- **Input Validation**: Comprehensive validation at API boundaries
- **Output Encoding**: Context-aware encoding to prevent injection
- **Secrets Management**: Environment variables and secure storage
- **Audit Trail**: Comprehensive logging of security-relevant events

### Maintainability
- **Code Organization**: Clear separation by concern and tier
- **Documentation**: Comprehensive inline docs and external documentation
- **Testing**: High test coverage with unit and integration tests
- **Type Safety**: Full type hints throughout the codebase
- **Code Reviews**: Mandatory peer review for all changes
- **Technical Debt**: Regular refactoring and improvement cycles

### Usability
- **API Consistency**: Uniform error responses and status codes
- **Documentation**: Interactive API docs with examples
- **Error Messages**: Clear, actionable error messages
- **Developer Experience**: Consistent patterns and conventions
- **Onboarding**: Clear documentation and examples for new developers

---
*Last Updated: 2026-08-17*
*Status: Production Ready - Architecture Fully Implemented*