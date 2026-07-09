"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application Settings"""
    
    # App
    APP_NAME: str = "BedaanWaves"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/bedaanwaves_db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # API
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 3000
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:3005",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3005",
    ]
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External APIs
    BRS_API_KEY: Optional[str] = None
    BRS_API_BASE_URL: str = "https://api.brsapi.ir"
    BRS_API_TIMEOUT: int = 30
    
    # ML
    ML_MODEL_PATH: str = "./models"
    ML_UPDATE_INTERVAL_HOURS: int = 1
    ML_SIGNAL_THRESHOLD: float = 0.65
    
    # Cache
    REDIS_URL: Optional[str] = None
    CACHE_ENABLED: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
