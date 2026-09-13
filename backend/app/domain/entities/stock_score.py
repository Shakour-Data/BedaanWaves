from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List
from ..value_objects.dimension import DimensionType

@dataclass
class StockScore:
    """Domain Entity representing a stock's total score across dimensions."""
    ticker: str
    market: str
    dimension_scores: Dict[DimensionType, float]
    overall_score: float = 0.0
    grade: str = ""
    signals: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def calculate_overall(self, weights: Dict[DimensionType, float]):
        """Business logic for aggregating scores."""
        weighted_sum = 0.0
        for dim, score in self.dimension_scores.items():
            weight = weights.get(dim, 0.0)
            weighted_sum += score * weight
        self.overall_score = round(weighted_sum, 2)
        self._assign_grade()

    def _assign_grade(self):
        if self.overall_score >= 85: self.grade = "STRONG_BULLISH"
        elif self.overall_score >= 70: self.grade = "BULLISH"
        elif self.overall_score >= 55: self.grade = "NEUTRAL"
        elif self.overall_score >= 40: self.grade = "BEARISH"
        else: self.grade = "STRONG_BEARISH"
