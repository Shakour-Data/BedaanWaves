from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ...domain.shared.result import Result

class IHttpClient(ABC):
    """Interface for making HTTP requests."""
    
    @abstractmethod
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None) -> Result[Any]:
        """Perform a GET request."""
        pass
    
    @abstractmethod
    async def post(self, url: str, data: Any = None, json: Any = None, headers: Optional[Dict[str, Any]] = None) -> Result[Any]:
        """Perform a POST request."""
        pass
