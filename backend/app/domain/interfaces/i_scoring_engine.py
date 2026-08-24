from abc import ABC, abstractmethod
from typing import Dict, Any
from ..entities.stock_score import StockScore
from ..value_objects.dimension import DimensionType

class IScoringEngine(ABC):
    """Domain interface for the core scoring logic."""
    
    @abstractmethod
    def score_dimension(self, dimension: DimensionType, data: Dict[str, Any], market: str) -> float:
        """Score a single dimension based on input data and market context."""
        pass
    
    @abstractmethod
    def calculate_total_score(self, ticker: str, market: str, dimension_data: Dict[DimensionType, Dict[str, Any]]) -> StockScore:
        """Perform full 6D scoring for a stock."""
        pass
