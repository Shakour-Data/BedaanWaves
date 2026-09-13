from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class TechnicalIndicators:
    """Value Object containing all technical indicator results."""
    ticker: str
    current_price: float
    moving_averages: Dict[str, float] = field(default_factory=dict)
    momentum: Dict[str, float] = field(default_factory=dict)
    volatility: Dict[str, float] = field(default_factory=dict)
    trend: Dict[str, float] = field(default_factory=dict)
    volume: Dict[str, float] = field(default_factory=dict)
    support_resistance: Dict[str, float] = field(default_factory=dict)
