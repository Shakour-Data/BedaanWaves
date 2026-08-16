from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataService(ABC):
    """Base service for all data based services"""
    
    def __init__(self, service_name: str = "DataService"):
        self.service_name = service_name
        self.shutdown_completed = False
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service connections"""
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        """Clean shutdown process"""
        pass
        
    def is_shutdown(self) -> bool:
        return self.shutdown_completed