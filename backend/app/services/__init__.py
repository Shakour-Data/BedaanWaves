"""
BedaanWaves Services Module

Consolidates services from the legacy Bedaan projects into a 9-tier layout:
  Tier 1: Core        (Dependency, Config, Logging, Cache, Database, Health)
  Tier 2: Data        (BRS API, Stock, Market, Portfolio, History, News)
  Tier 3: Analysis    (Scoring, Technical, Fundamental, Risk, Momentum, Volatility)
  Tier 4: ML          (Prediction, Anomaly, Clustering, Ensemble)        [pending]
  Tier 5: NLP         (Sentiment, News, Entity, Summarization)           [pending]
  Tier 6: User        (Auth, Portfolio, Alerts, Notifications)           [pending]
  Tier 7: Specialized (Hierarchy, Backtest, Optimization)                [pending]
  Tier 8: Crypto      (Multi-asset analysis)                             [pending]
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

# Tier 3: Analysis Services
from .analysis.scoring_service import ScoringService
from .analysis.technical_service import TechnicalAnalysisService
from .analysis.fundamental_service import FundamentalAnalysisService
from .analysis.risk_service import RiskAnalysisService
from .analysis.momentum_service import MomentumService
from .analysis.volatility_service import VolatilityService

__all__ = [
    # Tier 1
    "DependencyContainer",
    "ConfigService",
    "LoggerService",
    "CacheService",
    "DatabaseService",
    "HealthChecker",
    # Tier 2
    "BrsApiClient",
    "StockService",
    "MarketService",
    "PortfolioService",
    "HistoryService",
    "NewsService",
    # Tier 3
    "ScoringService",
    "TechnicalAnalysisService",
    "FundamentalAnalysisService",
    "RiskAnalysisService",
    "MomentumService",
    "VolatilityService",
]
