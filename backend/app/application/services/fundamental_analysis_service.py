from typing import Dict, Any
from ..interfaces.i_logger import ILogger
from ...domain.services.analysis.fundamental.valuation_engine import ValuationEngine
from ...domain.services.analysis.fundamental.profitability_engine import ProfitabilityEngine
from ...domain.shared.result import Result

class FundamentalAnalysisService:
    """
    Application service for fundamental analysis.
    Follows Clean OO: Composition, DI, Result Pattern.
    """
    
    def __init__(
        self,
        valuation_engine: ValuationEngine,
        profitability_engine: ProfitabilityEngine,
        logger: ILogger
    ):
        self._valuation = valuation_engine
        self._profitability = profitability_engine
        self._logger = logger

    async def analyze_fundamentals(self, ticker: str, financials: Dict[str, Any]) -> Result[Dict[str, Any]]:
        if not financials:
            return Result.failure("No financial data provided", "INVALID_DATA")
            
        stock_price = financials.get("stock_price", 0.0)
        eps = financials.get("eps", 0.0)
        
        ratios = {
            "pe_ratio": self._valuation.calculate_pe(stock_price, eps),
            "net_margin": self._profitability.calculate_net_margin(
                financials.get("net_income", 0.0),
                financials.get("revenue", 1.0)
            )
        }
        
        return Result.success({
            "ticker": ticker,
            "ratios": ratios,
            "status": self._determine_status(ratios)
        })

    def _determine_status(self, ratios: Dict[str, float]) -> str:
        net_margin = ratios.get("net_margin", 0.0)
        if net_margin > 15:
            return "Strong"
        if net_margin > 5:
            return "Moderate"
        return "Weak"
