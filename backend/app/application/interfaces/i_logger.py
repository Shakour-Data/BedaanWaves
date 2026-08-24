from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class ILogger(ABC):
    """Interface for structured logging."""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log an error message with optional exception."""
        pass
    
    @abstractmethod
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log a critical message."""
        pass
