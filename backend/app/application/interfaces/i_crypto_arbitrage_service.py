from abc import ABC, abstractmethod
from typing import List, Dict, Any
from decimal import Decimal
from ...domain.shared.result import Result
from ...domain.value_objects.crypto.arbitrage_opportunity import ArbitrageOpportunity

class ICryptoArbitrageService(ABC):
    """Application-level interface for arbitrage detection."""
    
    @abstractmethod
    async def get_opportunities(self) -> Result[List[ArbitrageOpportunity]]:
        """Detect current arbitrage opportunities."""
        pass
    
    @abstractmethod
    async def simulate_trade(self, opportunity: ArbitrageOpportunity, amount: Decimal) -> Result[Dict[str, Any]]:
        """Simulate a trade for a given opportunity."""
        pass
