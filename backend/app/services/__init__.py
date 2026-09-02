"""
BedaanWaves Services Module

Consolidates services from the legacy Bedaan projects into a 9-tier layout:
  Tier 1: Core        (Dependency, Config, Logging, Cache, Database, Health)
  Tier 2: Data        (BRS API, Stock, Market, Portfolio, History, News, Intl)
  Tier 3: Analysis    (Scoring, Technical, Fundamental, Risk, Momentum, Volatility)
  Tier 4: ML          (Prediction, Anomaly, Clustering, Ensemble)        [pending]
  Tier 5: NLP         (Sentiment, News, Entity, Summarization)           [pending]
  Tier 6: User        (Auth, Portfolio, Alerts, Notifications)           [pending]
  Tier 7: Specialized (Hierarchy, Backtest, Optimization)                [pending]
  Tier 9: System      (Monitoring, Backup, Recovery)                     [pending]

Only implemented tiers are imported here so the package stays importable as
the remaining tiers are filled in.
"""

# Tier 1: Core Services
from .core.dependency_container import DependencyContainer
from .core.config_service import ConfigService
from .core.logger_service import LoggerService
from .core.cache_service import CacheService
from .core.database_service import DatabaseService
from .core.health_checker import HealthChecker

# Tier 2: Data Services
from .data.stock_service import StockService
from .data.market_service import MarketService
from .data.portfolio_service import PortfolioService
from .data.history_service import HistoryService
from .data.news_service import NewsService
from .data.intl_api_client import IntlApiClient
try:
    from .data.data_validation_service import DataValidationService
except Exception:
    pass
from .data.financial_data_ingest_service import (
    FinancialDataIngestService,
    FinancialStatementType,
    MarketType,
    FinancialStatement,
    FinancialDataProvider,
)
from .data.stock_fundamental_ingestion_service import StockFundamentalDataIngestionService
from .data.symbol_service import SymbolService

# Tier 3: Analysis Services
try:
    from .analysis.scoring_service import ScoringService
    from .analysis.technical_service import TechnicalAnalysisService
    from .analysis.fundamental_service import FundamentalAnalysisService
    from .analysis.risk_service import RiskAnalysisService
    from .analysis.momentum_service import MomentumService
    from .analysis.volatility_service import VolatilityService
    from .analysis.user_filtered_scoring_service import UserFilteredScoringService
except Exception:
    pass

# Tier 4: ML Services
try:
    from .ml import CoefficientLearningService
except Exception:
    pass

# Tier 5: NLP Services
try:
    from .nlp.sentiment_analysis_service import SentimentAnalysisService
    from .nlp.news_summarization_service import NewsSummarizationService
    from .nlp.document_extraction_service import DocumentExtractionService
    from .nlp.multilingual_news_service import MultilingualNewsService
except Exception:
    pass

# Tier 9: System Services
try:
    from .system.scheduler_service import SchedulerService
    from .system.metrics_service import MetricsService
    from .system.queue_service import QueueService
    from .system.data_integrity_service import DataIntegrityService
    from .system.settings_migration_service import SettingsMigrationService
except Exception:
    pass

__all__ = [
    # Tier 1
    "DependencyContainer",
    "ConfigService",
    "LoggerService",
    "CacheService",
    "DatabaseService",
    "HealthChecker",
    # Tier 2
    "StockService",
    "MarketService",
    "PortfolioService",
    "HistoryService",
    "NewsService",
    "IntlApiClient",
    "DataValidationService",
    "FinancialDataIngestService",
    "StockFundamentalDataIngestionService",
    "SymbolService",
    "FinancialStatementType",
    "MarketType",
    "FinancialStatement",
    "FinancialDataProvider",
    # Tier 3
    "ScoringService",
    "TechnicalAnalysisService",
    "FundamentalAnalysisService",
    "RiskAnalysisService",
    "MomentumService",
    "VolatilityService",
    "UserFilteredScoringService",
    # Tier 5: NLP
    "SentimentAnalysisService",
    "NewsSummarizationService",
    "DocumentExtractionService",
    "MultilingualNewsService",
    # Tier 9: System
    "SchedulerService",
    "MetricsService",
    "QueueService",
    "DataIntegrityService",
    "SettingsMigrationService",
]
