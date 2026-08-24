from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ...domain.shared.result import Result

class IConfigService(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def get_string(self, key: str, default: str = "") -> str:
        """Get a string configuration value."""
        pass
    
    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value."""
        pass
    
    @abstractmethod
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value."""
        pass
    
    @abstractmethod
    def get_section(self, section_name: str) -> Result[Dict[str, Any]]:
        """Get a specific configuration section."""
        pass
    
    @abstractmethod
    def is_production(self) -> bool:
        """Check if the environment is production."""
        pass
