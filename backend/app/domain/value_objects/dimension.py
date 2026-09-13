from dataclasses import dataclass
from enum import Enum
from ..shared.exceptions import ValidationException

class DimensionType(Enum):
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    RISK = "risk"
    MACRO = "macro"
    AI = "ai"

@dataclass(frozen=True)
class Dimension:
    """Value Object representing a scoring dimension."""
    type: DimensionType
    weight: float

    def __post_init__(self):
        if not (0 <= self.weight <= 1.0):
            raise ValidationException(f"Weight must be between 0 and 1.0, got {self.weight}")
