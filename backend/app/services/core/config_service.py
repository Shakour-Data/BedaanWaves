"""
Configuration Service - Tier 1 Core Service

Centralized configuration management for the entire BedaanWaves platform.
Handles environment variables, settings, and feature flags.
"""

from typing import Any, Dict, Optional
import os
from pathlib import Path
import json
from .base_service import BaseService


class ConfigService(BaseService):
    """
    Manages all configuration for BedaanWaves application.
    
    Provides:
    - Environment variable management
    - Configuration sections (database, cache, API, ML, etc.)
    - Feature flags
    - Settings validation
    """
    
    def __init__(self, service_name: str = "ConfigService", env_file: Optional[str] = None):
        """
        Initialize configuration service.
        
        Args:
            service_name: Service identifier
            env_file: Optional path to .env file
        """
        super().__init__(service_name)
        self.env_file = env_file or self._find_env_file()
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    @staticmethod
    def _find_env_file() -> Optional[str]:
        """Find .env file in project structure"""
        possible_paths = [
            Path.cwd() / '.env',
            Path.cwd().parent / '.env',
            Path('/app/.env'),
        ]
        for path in possible_paths:
            if path.exists():
                return str(path)
        return None
    
    async def initialize(self) -> None:
        """Initialize configuration service"""
        self.logger.info("ConfigService initialized")
        self._config.update(self._load_environment_variables())
    
    async def shutdown(self) -> None:
        """Shutdown configuration service"""
        self.logger.info("ConfigService shutdown")
    
    def _load_config(self) -> None:
        """Load all configuration"""
        self._config = {
            'environment': self.get('ENVIRONMENT', 'development'),
            'debug': self.get_bool('DEBUG', False),
            'log_level': self.get('LOG_LEVEL', 'INFO'),
            'api': self._load_api_config(),
            'database': self._load_database_config(),
            'cache': self._load_cache_config(),
            'ml': self._load_ml_config(),
            'security': self._load_security_config(),
            'services': self._load_services_config(),
        }
    
    def _load_environment_variables(self) -> Dict[str, Any]:
        """Load environment variables"""
        if self.env_file and os.path.exists(self.env_file):
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            os.environ.setdefault(key.strip(), value.strip())
                self.logger.info(f"Loaded environment from {self.env_file}")
            except Exception as e:
                self.logger.warning(f"Failed to load .env file: {e}")
        
        return os.environ.copy()
    
    def _load_api_config(self) -> Dict[str, Any]:
        """Load API configuration"""
        return {
            'host': self.get('API_HOST', '0.0.0.0'),
            'port': self.get_int('API_PORT', 8000),
            'title': self.get('API_TITLE', 'BedaanWaves'),
            'version': self.get('API_VERSION', '1.0.0'),
            'base_path': self.get('API_BASE_PATH', '/api/v1'),
            'timeout': self.get_int('API_TIMEOUT', 30),
            'max_connections': self.get_int('API_MAX_CONNECTIONS', 100),
            'cors_origins': self.get_list('CORS_ORIGINS', ['*']),
        }
    
    def _load_database_config(self) -> Dict[str, Any]:
        """Load database configuration"""
        return {
            'driver': self.get('DB_DRIVER', 'postgresql'),
            'host': self.get('DB_HOST', 'localhost'),
            'port': self.get_int('DB_PORT', 5432),
            'name': self.get('DB_NAME', 'bedaanwaves'),
            'user': self.get('DB_USER', 'postgres'),
            'password': self.get('DB_PASSWORD', ''),
            'pool_size': self.get_int('DB_POOL_SIZE', 20),
            'max_overflow': self.get_int('DB_MAX_OVERFLOW', 10),
            'echo': self.get_bool('DB_ECHO', False),
        }
    
    def _load_cache_config(self) -> Dict[str, Any]:
        """Load cache configuration"""
        return {
            'backend': self.get('CACHE_BACKEND', 'memory'),
            'redis_url': self.get('REDIS_URL', 'redis://localhost:6379/0'),
            'ttl_seconds': self.get_int('CACHE_TTL', 3600),
            'max_size': self.get_int('CACHE_MAX_SIZE', 1000),
        }
    
    def _load_ml_config(self) -> Dict[str, Any]:
        """Load machine learning configuration"""
        return {
            'models_dir': self.get('ML_MODELS_DIR', './models'),
            'batch_size': self.get_int('ML_BATCH_SIZE', 32),
            'learning_rate': self.get_float('ML_LEARNING_RATE', 0.001),
            'epochs': self.get_int('ML_EPOCHS', 100),
            'ensemble_enabled': self.get_bool('ML_ENSEMBLE_ENABLED', True),
        }
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration"""
        return {
            'jwt_secret': self.get('JWT_SECRET', 'your-secret-key-change-in-production'),
            'jwt_algorithm': self.get('JWT_ALGORITHM', 'HS256'),
            'jwt_expiration_hours': self.get_int('JWT_EXPIRATION_HOURS', 24),
            'password_min_length': self.get_int('PASSWORD_MIN_LENGTH', 8),
            'enable_https': self.get_bool('ENABLE_HTTPS', False),
        }
    
    def _load_services_config(self) -> Dict[str, Any]:
        """Load services configuration"""
        return {
            'brs_api_url': self.get('BRS_API_URL', 'https://api.brs.ir'),
            'brs_api_timeout': self.get_int('BRS_API_TIMEOUT', 10),
            'news_api_url': self.get('NEWS_API_URL', 'https://newsapi.org'),
            'news_api_key': self.get('NEWS_API_KEY', ''),
            'nlp_model': self.get('NLP_MODEL', 'persian-bert'),
        }
    
    # Get methods with type conversion
    
    def get(self, key: str, default: Any = None) -> str:
        """Get string value from environment"""
        return os.environ.get(key, default or '')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer value from environment"""
        try:
            return int(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float value from environment"""
        try:
            return float(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment"""
        value = self.get(key, '').lower()
        if value in ('true', '1', 'yes', 'on'):
            return True
        elif value in ('false', '0', 'no', 'off'):
            return False
        return default
    
    def get_list(self, key: str, default: list = None) -> list:
        """Get comma-separated list from environment"""
        value = self.get(key)
        if not value:
            return default or []
        return [item.strip() for item in value.split(',')]
    
    def get_json(self, key: str, default: dict = None) -> dict:
        """Get JSON object from environment"""
        try:
            value = self.get(key)
            if not value:
                return default or {}
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default or {}
    
    # Configuration access
    
    def get_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration.
        
        Args:
            section: Optional section name (e.g., 'database', 'api')
            
        Returns:
            Configuration dictionary
        """
        if section:
            return self._config.get(section, {})
        return self._config.copy()
    
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value at runtime"""
        self._config[key] = value
        self.logger.debug(f"Set config: {key}")
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self._config.get('environment') == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self._config.get('environment') == 'development'
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self._config.get('debug', False)
