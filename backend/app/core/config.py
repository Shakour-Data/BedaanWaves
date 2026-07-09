"""
Application Configuration - BedaanWaves Unified Platform

This configuration consolidates settings from:
- Bedaan4D-ML backend
- Bedaan6D-project frontend
- CryptoAndStocks multi-asset
- Bedaan_4D_AI analysis
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application Settings - Consolidated from 5 OldFils projects"""
    
    # ============================================================
    # APPLICATION METADATA
    # ============================================================
    APP_NAME: str = "BedaanWaves"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Unified Bedaan Ecosystem - Capital Market Analysis & AI Trading Platform"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # ============================================================
    # DATABASE CONFIGURATION
    # ============================================================
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/bedaanwaves_db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # ============================================================
    # REDIS & CACHE CONFIGURATION
    # ============================================================
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    CACHE_TTL_MINUTES: int = 60
    CACHE_SCORE_TTL_HOURS: int = 24
    CACHE_API_RESPONSE_TTL_MINUTES: int = 5
    
    # ============================================================
    # API CONFIGURATION
    # ============================================================
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 3000
    API_TITLE: str = "BedaanWaves API"
    DOCS_URL: str = "/api/v1/docs"
    OPENAPI_URL: str = "/api/v1/openapi.json"
    
    # ============================================================
    # CORS CONFIGURATION
    # ============================================================
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3005",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3005",
        "http://127.0.0.1:3000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # ============================================================
    # SECURITY & AUTHENTICATION
    # ============================================================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 5000
    
    # ============================================================
    # EXTERNAL APIs (BedaanWaves Integration)
    # ============================================================
    # Tehran Stock Exchange (BrsApi.ir)
    BRS_API_BASE_URL: str = "https://api.brsapi.ir"
    BRS_API_KEY: Optional[str] = None
    BRS_API_TIMEOUT: int = 30
    BRS_REFRESH_INTERVAL_MINUTES: int = 5
    
    # Financial Disclosures (Codal)
    CODAL_API_BASE_URL: str = "https://api.codal.ir"
    CODAL_API_KEY: Optional[str] = None
    CODAL_REFRESH_INTERVAL_HOURS: int = 24
    
    # News APIs
    NEWS_SOURCES: List[str] = ["tehran-news", "financial-news", "market-news"]
    NEWS_REFRESH_INTERVAL_MINUTES: int = 30
    
    # Cryptocurrency APIs
    CRYPTO_ENABLED: bool = True
    COINGECKO_API_BASE_URL: str = "https://api.coingecko.com/api/v3"
    BINANCE_API_BASE_URL: str = "https://api.binance.com/api/v3"
    CRYPTO_REFRESH_INTERVAL_MINUTES: int = 5
    
    # ============================================================
    # MACHINE LEARNING CONFIGURATION (Bedaan4D-ML)
    # ============================================================
    ML_ENABLED: bool = True
    ML_MODEL_PATH: str = "./models"
    ML_MODELS_VERSION: str = "1.0.0"
    
    # Model Training
    ML_TRAINING_ENABLED: bool = True
    ML_UPDATE_INTERVAL_HOURS: int = 1
    ML_RETRAINING_INTERVAL_DAYS: int = 7
    
    # Model Performance
    ML_SIGNAL_THRESHOLD: float = 0.65
    ML_CONFIDENCE_THRESHOLD: float = 0.60
    ML_PREDICTION_CONFIDENCE_WEIGHTS: dict = {
        "random_forest": 0.20,
        "xgboost": 0.25,
        "lightgbm": 0.25,
        "neural_network": 0.20,
        "svm": 0.10,
    }
    
    # Feature Engineering
    ML_LOOKBACK_DAYS: int = 252  # One trading year
    ML_FEATURES_NORMALIZATION: str = "zscore"  # zscore or minmax
    
    # ============================================================
    # 6D SCORING SYSTEM CONFIGURATION (Bedaan6D-project)
    # ============================================================
    SCORING_ENABLED: bool = True
    
    # 6D Dimension Weights
    SCORING_WEIGHTS: dict = {
        "fundamental": 0.25,      # Financial health
        "technical": 0.20,        # Chart patterns
        "sentiment": 0.15,        # News & sentiment
        "risk": 0.20,             # Volatility & drawdown
        "macro": 0.10,            # Economic indicators
        "ai": 0.10,               # ML prediction
    }
    
    # Scoring Hierarchy (305 nodes)
    SCORING_HIERARCHY_ENABLED: bool = True
    SCORING_HIERARCHY_DEPTH: int = 4  # 4 levels
    SCORING_HIERARCHY_CACHE_TTL_HOURS: int = 24
    
    # ============================================================
    # TECHNICAL ANALYSIS CONFIGURATION
    # ============================================================
    TECHNICAL_ANALYSIS_ENABLED: bool = True
    TECHNICAL_INDICATORS_COUNT: int = 50
    
    # Indicator Defaults
    TECHNICAL_SMA_PERIODS: List[int] = [20, 50, 200]
    TECHNICAL_EMA_PERIODS: List[int] = [12, 26]
    TECHNICAL_RSI_PERIOD: int = 14
    TECHNICAL_MACD_FAST: int = 12
    TECHNICAL_MACD_SLOW: int = 26
    TECHNICAL_MACD_SIGNAL: int = 9
    TECHNICAL_BOLLINGER_PERIOD: int = 20
    TECHNICAL_BOLLINGER_STD_DEV: float = 2.0
    TECHNICAL_ATR_PERIOD: int = 14
    
    # ============================================================
    # NLP & SENTIMENT ANALYSIS (Bedaan_4D_AI)
    # ============================================================
    NLP_ENABLED: bool = True
    SENTIMENT_ANALYSIS_ENABLED: bool = True
    
    # Persian NLP
    PERSIAN_STOPWORDS_ENABLED: bool = True
    PERSIAN_LEMMATIZATION_ENABLED: bool = True
    
    # Sentiment Model
    SENTIMENT_MODEL_PATH: str = "./models/sentiment_model.pkl"
    SENTIMENT_KEYWORDS_PATH: str = "./data/sentiment_keywords.json"
    SENTIMENT_IMPACT_THRESHOLD: float = 0.5
    
    # ============================================================
    # PORTFOLIO & RISK MANAGEMENT
    # ============================================================
    PORTFOLIO_ENABLED: bool = True
    PORTFOLIO_OPTIMIZATION_ENABLED: bool = True
    
    # Portfolio Constraints
    PORTFOLIO_MIN_POSITION_SIZE: float = 0.01  # 1%
    PORTFOLIO_MAX_POSITION_SIZE: float = 0.10  # 10%
    PORTFOLIO_MAX_CONCENTRATION: float = 0.30  # 30%
    
    # Risk Management
    RISK_MANAGEMENT_ENABLED: bool = True
    PORTFOLIO_VAR_CONFIDENCE: float = 0.95  # 95% VaR
    PORTFOLIO_MAX_DRAWDOWN: float = 0.20    # 20% max drawdown
    PORTFOLIO_VOLATILITY_TARGET: float = 0.15  # 15% annual volatility
    
    # ============================================================
    # ALERTS & NOTIFICATIONS
    # ============================================================
    ALERTS_ENABLED: bool = True
    
    # Alert Types
    ALERT_TYPES: List[str] = [
        "price_change",
        "technical_signal",
        "portfolio_alert",
        "ml_prediction",
        "sentiment_shift",
        "anomaly_detection",
        "risk_warning",
    ]
    
    # Notification Channels
    NOTIFICATIONS_EMAIL_ENABLED: bool = True
    NOTIFICATIONS_SMS_ENABLED: bool = False
    NOTIFICATIONS_PUSH_ENABLED: bool = False
    NOTIFICATIONS_WEBHOOK_ENABLED: bool = True
    
    # ============================================================
    # LOGGING & MONITORING
    # ============================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_ENABLED: bool = True
    LOG_FILE_PATH: str = "./logs/bedaanwaves.log"
    LOG_ROTATION: str = "midnight"  # midnight, weekly, or size
    LOG_RETENTION_DAYS: int = 30
    
    # Monitoring & Metrics
    METRICS_ENABLED: bool = True
    PROMETHEUS_METRICS_ENABLED: bool = True
    PROMETHEUS_METRICS_PORT: int = 9090
    
    # ============================================================
    # DATA PERSISTENCE & BACKUP
    # ============================================================
    BACKUP_ENABLED: bool = True
    BACKUP_INTERVAL_HOURS: int = 24
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_PATH: str = "./backups"
    
    # ============================================================
    # CRYPTO FEATURES (CryptoAndStocks Integration)
    # ============================================================
    CRYPTO_SUPPORT_ENABLED: bool = True
    CRYPTO_PORTFOLIOS_ENABLED: bool = True
    CRYPTO_ALERTS_ENABLED: bool = True
    
    # Supported Cryptocurrencies
    SUPPORTED_CRYPTOCURRENCIES: List[str] = [
        "BTC", "ETH", "BNB", "XRP", "SOL", "ADA", "DOT", "DOGE",
        "MATIC", "UNI", "LINK", "AVAX", "FTM", "ATOM",
    ]
    
    # ============================================================
    # PAGINATION & LIMITS
    # ============================================================
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    DEFAULT_LOOKBACK_DAYS: int = 365
    MAX_LOOKBACK_DAYS: int = 10 * 365  # 10 years
    
    # ============================================================
    # PYDANTIC CONFIG
    # ============================================================
    class Config:
        env_file = ".env"
        case_sensitive = True
        str_strip_whitespace = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
