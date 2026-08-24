from typing import List, Dict, Any
from ..interfaces.i_logger import ILogger
from ...domain.services.analysis.moving_average_engine import MovingAverageEngine
from ...domain.services.analysis.momentum_engine import MomentumEngine
from ...domain.value_objects.analysis.technical_indicators import TechnicalIndicators
from ...domain.shared.result import Result

class TechnicalAnalysisService:
    """
    Application service for technical analysis.
    Orchestrates specialized engines to provide full analysis.
    """
    
    def __init__(
        self,
        ma_engine: MovingAverageEngine,
        momentum_engine: MomentumEngine,
        logger: ILogger
    ):
        self._ma_engine = ma_engine
        self._momentum_engine = momentum_engine
        self._logger = logger

    async def analyze_ticker(self, ticker: str, data: Dict[str, Any]) -> Result[TechnicalIndicators]:
        prices = data.get("prices", [])
        if not prices or len(prices) < 30:
            return Result.failure("Insufficient price data", "INVALID_DATA")
            
        current_price = prices[-1]
        
        moving_averages = {
            "sma_20": self._ma_engine.calculate_sma(prices, 20),
            "sma_50": self._ma_engine.calculate_sma(prices, 50),
            "ema_20": self._ma_engine.calculate_ema(prices, 20)
        }
        
        momentum = {
            "rsi_14": self._momentum_engine.calculate_rsi(prices, 14),
            "macd": self._momentum_engine.calculate_macd(prices)[0]
        }
        
        result = TechnicalIndicators(
            ticker=ticker,
            current_price=current_price,
            moving_averages=moving_averages,
            momentum=momentum
        )
        
        return Result.success(result)
