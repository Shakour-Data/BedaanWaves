from dataclasses import dataclass, field


@dataclass(frozen=True)
class TechnicalIndicators:
    """Value Object containing all technical indicator results."""
    ticker: str
    current_price: float
    moving_averages: dict[str, float] = field(default_factory=dict)
    momentum: dict[str, float] = field(default_factory=dict)
    volatility: dict[str, float] = field(default_factory=dict)
    trend: dict[str, float] = field(default_factory=dict)
    volume: dict[str, float] = field(default_factory=dict)
    support_resistance: dict[str, float] = field(default_factory=dict)
