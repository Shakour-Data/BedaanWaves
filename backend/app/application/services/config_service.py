import os
from typing import Any, Dict, Optional, List
from ..interfaces.i_config_service import IConfigService
from ...domain.shared.result import Result

class ConfigService(IConfigService):
    """
    Implementation of IConfigService.
    Follows Clean OO: Encapsulation, Single Responsibility, Short Methods.
    """
    
    def __init__(self, env_vars: Optional[Dict[str, str]] = None):
        """Inject environment variables for testability."""
        self._env = env_vars if env_vars is not None else dict(os.environ)
        self._cache: Dict[str, Any] = {}

    def get_string(self, key: str, default: str = "") -> str:
        return self._env.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        value = self.get_string(key)
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get_string(key).lower()
        if value in ('true', '1', 'yes', 'on'):
            return True
        if value in ('false', '0', 'no', 'off'):
            return False
        return default

    def get_section(self, section_name: str) -> Result[Dict[str, Any]]:
        """Grouped logic for sections to keep methods short."""
        if section_name == "database":
            return Result.success(self._load_database_section())
        if section_name == "api":
            return Result.success(self._load_api_section())
        return Result.failure(f"Section '{section_name}' not found", "CONFIG_SECTION_NOT_FOUND")

    def is_production(self) -> bool:
        return self.get_string("ENVIRONMENT") == "production"

    def _load_database_section(self) -> Dict[str, Any]:
        return {
            "host": self.get_string("DB_HOST", "localhost"),
            "port": self.get_int("DB_PORT", 5432),
            "name": self.get_string("DB_NAME", "bedaanwaves"),
            "user": self.get_string("DB_USER", "postgres"),
            "password": self.get_string("DB_PASSWORD", ""),
            "pool_size": self.get_int("DB_POOL_SIZE", 20)
        }

    def _load_api_section(self) -> Dict[str, Any]:
        return {
            "host": self.get_string("API_HOST", "0.0.0.0"),
            "port": self.get_int("API_PORT", 8000),
            "title": self.get_string("API_TITLE", "BedaanWaves"),
            "version": self.get_string("API_VERSION", "1.0.0"),
            "base_path": self.get_string("API_BASE_PATH", "/api/v1"),
            "cors_origins": self._get_list("CORS_ORIGINS", ["*"])
        }

    def _get_list(self, key: str, default: List[str]) -> List[str]:
        value = self.get_string(key)
        if not value:
            return default
        return [item.strip() for item in value.split(",")]
