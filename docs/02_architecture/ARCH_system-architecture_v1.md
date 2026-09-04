# BedaanWaves System Documentation

## Overview
A comprehensive guide to the BedaanWaves platform architecture, implementation details, and service interactions.

## Architecture Layers

### Tier 1: Core Services
- **DependencyContainer**: IoC/DI management for all services
- **ConfigService**: Centralized configuration loading from `.env`
- **LoggerService**: Structured JSON logging with structured context
- **CacheService**: Multiple backend caching with Redis fallback to memory
- **DatabaseService**: Connection pooling with SQLAlchemy 2.0
- **HealthChecker**: System-wide health monitoring and status reporting

### Tier 2: Data Services
- **FinancialGraphDB**: Specialized JSONB for asset/indicator relationships
- **DataIngestionPipeline**: Multi-source data collection and validation
- **MarketDataProcessor**: Real-time data cleaning and normalization
- **IntlApiClient**: US/Middle East market API integration
- **FinancialDataIngestService**: Multi-source financial statement ingestion

### Tier 3: Analysis Services
- **ScoringServiceMLIntegration**: Secure ML model invocation with rolling retry
- **TechnicalAnalysisService**: 50+ technical indicators with live dashboard
- **FundamentalAnalysisService**: 20+ financial ratios and metrics
- **RiskAnalysisService**: VaR, Sharpe, stress testing with production-hardened algorithms
- **MomentumService**: Momentum signals with live microforecasting
- **VolatilityService**: Volatility forecasting with ensemble techniques

### Tier 4: ML Services
- **PredictionService**: Price prediction for 1,000+ assets with multi-horizon models
- **PatternRecognitionService**: Chart pattern detection using CNN and feature engineering
- **AnomalyDetectionService**: Statistical and ML-based anomaly detection
- **RecommendationService**: Stock recommendations via content-based filtering
- **PortfolioOptimizationService**: Markowitz-based optimization with constraints
- **TimeSeriesForecastingService**: ARIMA, LSTM, Prophet implementations
- **CoefficientLearningService**: Dynamic coefficient learning for zero-shot forecasting
- **UserFilteredRecommendationService**: Personalized recommendations based on user preferences

### Tier 5: NLP Services
- **SentimentAnalysisService**: News sentiment analysis with Persian language support
- **NewsSummarizationService**: Text summarization with extractive and abstractive methods
- **DocumentExtractionService**: PDF and web content extraction with OCR capabilities
- **ChatbotService**: Conversational AI with domain-specific knowledge
- **SearchService**: Semantic search across market data and news
- **MultiLanguageNewsService**: Country-specific news with language detection and translation

### Tier 6: User Services
- **AuthService**: Authentication with JWT and SSO options
- **AuthorizationService**: RBAC for enterprise feature access
- **UserProfileService**: User profile creation and KYC
- **WatchlistService**: Watchlist management with cross-asset support
- **PreferenceService**: User customization of dashboards and alerts
- **NotificationService**: Multi-channel notifications (email, SMS, push)
- **UserMarketSettingsService**: Country/index/industry selection for personalized feeds

### Tier 7: Specialized Services
- **SectorAnalysisService**: Sector performance metrics and comparisons
- **ScreeningService**: Stock screening filters with custom criteria
- **ComparisonService**: Peer benchmarking with multiple metrics
- **CorrelationService**: Cross-asset correlation analysis
- **CalendarService**: Market calendar integration with holiday detection
- **InternationalMarketService**: Multi-country data integration with localization
- **SectorFilterService**: Industry-based filtering system

### Tier 9: System Services
- **SchedulerService**: Task scheduling pipeline with priority queues
- **MetricsService**: Performance metrics collection and dashboards
- **QueueService**: Async message queuing system for data processing
- **BackupService**: Automated database/file backups with retention policies
- **LoggingService**: Centralized logging aggregation with enrichment
- **NotificationDispatcher**: Multi-channel notification routing
- **DataIntegrityService**: Historical data validation and integrity checks
- **SettingsMigrationService**: User preference migration between versions

## System Flow
1. User Authentication → Core Services
2. Data Ingestion → Data Services Pipeline
3. Analysis Pipeline → Analysis Services
4. User Preference Integration → Preference Service
5. Recommendation Generation → ML Services
6. Delivery to Frontend → Frontend Services
7. Monitoring and Logging → System Services

## API Structure
- Base URL: `/api/v1/`
- Authentication: `/auth/*` endpoints
- Data Exploration: `/data/*` endpoints
- Analysis Tools: `/analyze/*` endpoints
- Portfolio Management: `/portfolio/*` endpoints
- User Management: `/user/*` endpoints
- System Projects: `/project/*` endpoints

## Service Layering
```mermaid
graph TD
    A[User Layer] --> B[Frontend Layer]
    B --> C[API Gateway]
    C --> D[Core Services Layer]
    D --> E[Data Services Layer]
    D --> F[Analysis Services Layer]
    D --> G[ML Services Layer]
    D --> H[Specialized Services Layer]
    F --> I[User Personalization Layer]
    H --> I
    I --> J[Output Delivery]
    J --> K[Monitoring & Metrics]
    J --> L[Notifications]
    J --> M[Data Persistence]
    L --> N[Backup & Retention]