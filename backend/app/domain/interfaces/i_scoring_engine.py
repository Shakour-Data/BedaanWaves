from abc import ABC, abstractmethod
from typing import Any

from ..entities.stock_score import StockScore
from ..value_objects.dimension import DimensionType


class IScoringEngine(ABC):
    """Domain interface for the core scoring logic."""

    @abstractmethod
    def score_dimension(self, dimension: DimensionType, data: dict[str, Any], market: str) -> float:
        """Score a single dimension based on input data and market context."""

    @abstractmethod
    def calculate_total_score(self, ticker: str, market: str, dimension_data: dict[DimensionType, dict[str, Any]]) -> StockScore:
        """Perform full 6D scoring for a stock."""
