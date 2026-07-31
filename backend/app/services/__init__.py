"""
BedaanWaves Services Module

Consolidates services from the legacy Bedaan projects into a 9-tier layout:
  Tier 1: Core        (Dependency, Config, Logging, Cache, Database, Health)
  Tier 2: Data        (BRS API, Stock, Market, Portfolio, History, News, Crypto, Intl)
  Tier 3: Analysis    (Scoring, Technical, Fundamental, Risk, Momentum, Volatility)
  Tier 4: ML          (Prediction, Anomaly, Clustering, Ensemble)        [pending]
  Tier 5: NLP         (Sentiment, News, Entity, Summarization)           [pending]
  Tier 6: User        (Auth, Portfolio, Alerts, Notifications)           [pending]
  Tier 7: Specialized (Hierarchy, Backtest, Optimization)                [pending]
  Tier 8: Crypto      (Price, Portfolio, Analysis, News, Arbitrage)      [partial]
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
from .data.brs_api_client import BrsApiClient
from .data.stock_service import StockService
from .data.market_service import MarketService
from .data.portfolio_service import PortfolioService
from .data.history_service import HistoryService
from .data.news_service import NewsService
from .data.crypto_api_client import CryptoApiClient
from .data.intl_api_client import IntlApiClient
from .data.data_validation_service import DataValidationService
from .data.financial_data_ingest_service import (
    FinancialDataIngestService,
    FinancialStatementType,
    MarketType,
    FinancialStatement,
    FinancialDataProvider,
)
from .data.stock_fundamental_ingestion_service import StockFundamentalDataIngestionService

# Tier 3: Analysis Services
from .analysis.scoring_service import ScoringService
from .analysis.technical_service import TechnicalAnalysisService
from .analysis.fundamental_service import FundamentalAnalysisService
from .analysis.risk_service import RiskAnalysisService
from .analysis.momentum_service import MomentumService
from .analysis.volatility_service import VolatilityService
from .analysis.user_filtered_scoring_service import UserFilteredScoringService

# Tier 5: NLP Services
from .nlp.sentiment_analysis_service import SentimentAnalysisService
from .nlp.news_summarization_service import NewsSummarizationService
from .nlp.document_extraction_service import DocumentExtractionService
from .nlp.chatbot_service import ChatbotService
from .nlp.search_service import SearchService
from .nlp.multilingual_news_service import MultiLanguageNewsService

# Tier 8: Crypto Services
from .crypto.price_service import CryptoPriceService
from .crypto.portfolio_service import CryptoPortfolioService
from .crypto.crypto_market_cap_service import CryptoMarketCapService
from .crypto.custom_crypto_selection_service import CustomCryptoSelectionService

# Tier 9: System Services
from .system.scheduler_service import SchedulerService
from .system.metrics_service import MetricsService
from .system.queue_service import QueueService
from .system.data_integrity_service import DataIntegrityService
from .system.settings_migration_service import SettingsMigrationService

__all__ = [
    # Tier 1
    "DependencyContainer",
    "ConfigService",
    "LoggerService",
    "CacheService",
    "MemoryCacheBackend",
    "DatabaseService",
    "HealthChecker",
    "check_database",
    "check_cache",
    "check_memory",
    "check_disk",
    # Tier 2
    "BrsApiClient",
    "StockService",
    "MarketService",
    "PortfolioService",
    "HistoryService",
    "NewsService",
    "CryptoApiClient",
    "IntlApiClient",
    "DataValidationService",
    "FinancialDataIngestService",
    "StockFundamentalDataIngestionService",
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
    "ChatbotService",
    "SearchService",
    "MultiLanguageNewsService",
    # Tier 8: Crypto
    "CryptoPriceService",
    "CryptoPortfolioService",
    "CryptoMarketCapService",
    "CustomCryptoSelectionService",
    # Tier 9: System
    "SchedulerService",
    "MetricsService",
    "QueueService",
    "DataIntegrityService",
    "SettingsMigrationService",
]
