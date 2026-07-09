"""
BedaanWaves Services Module

This module consolidates 50+ services from 5 OldFils projects into:
- Tier 1: Core Services (Dependency, Config, Logging, Cache, Database, Health)
- Tier 2: Data Services (APIs, Data Management)
- Tier 3: Analysis Services (Scoring, Technical, Fundamental, Risk)
- Tier 4: ML Services (Prediction, Anomaly, Clustering, Ensemble)
- Tier 5: NLP Services (Sentiment, News, Entity, Summarization)
- Tier 6: User Services (Auth, Portfolio, Alerts, Notifications)
- Tier 7: Specialized Services (Hierarchy, Backtest, Optimization)
- Tier 8: Crypto Services (Multi-asset support)
- Tier 9: System Services (Monitoring, Backup, Recovery)
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

# Tier 3: Analysis Services
from .analysis.scoring_service import ScoringService
from .analysis.technical_analysis_service import TechnicalAnalysisService
from .analysis.fundamental_analysis_service import FundamentalAnalysisService
from .analysis.risk_analysis_service import RiskAnalysisService

# Tier 4: ML Services
from .ml.ml_service import MLService
from .ml.price_prediction_service import PricePredictionService
from .ml.anomaly_detection_service import AnomalyDetectionService

# Tier 5: NLP Services
from .nlp.sentiment_analysis_service import SentimentAnalysisService
from .nlp.news_analysis_service import NewsAnalysisService

# Tier 6: User Services
from .user.user_service import UserService
from .user.auth_service import AuthService
from .user.alert_service import AlertService

# Tier 7: Specialized Services
from .specialized.hierarchy_service import HierarchyService
from .specialized.backtest_service import BacktestService

# Tier 8: Crypto Services
from .crypto.crypto_analysis_service import CryptoAnalysisService

# Tier 9: System Services
from .system.performance_monitor import PerformanceMonitor
from .system.error_handler import ErrorHandler

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
    
    # Tier 3
    "ScoringService",
    "TechnicalAnalysisService",
    "FundamentalAnalysisService",
    "RiskAnalysisService",
    
    # Tier 4
    "MLService",
    "PricePredictionService",
    "AnomalyDetectionService",
    
    # Tier 5
    "SentimentAnalysisService",
    "NewsAnalysisService",
    
    # Tier 6
    "UserService",
    "AuthService",
    "AlertService",
    
    # Tier 7
    "HierarchyService",
    "BacktestService",
    
    # Tier 8
    "CryptoAnalysisService",
    
    # Tier 9
    "PerformanceMonitor",
    "ErrorHandler",
]
