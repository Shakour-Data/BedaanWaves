from typing import List, Dict, Any
from ..interfaces.i_logger import ILogger
from ...domain.services.analysis.moving_average_engine import MovingAverageEngine
from ...domain.services.analysis.momentum_engine import MomentumEngine
from ...domain.value_objects.analysis.technical_indicators import TechnicalIndicators
from ...domain.shared.result import Result
from app.services.data.adjusted_price_validator import AdjustedPriceValidator


class TechnicalAnalysisService:
    """
    Application service for technical analysis.
    Orchestrates specialized engines to provide full analysis.
    ALL price inputs MUST be adjusted close prices.
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
        close_prices = data.get("close_prices", [])

        if not prices or len(prices) < 30:
            return Result.failure("Insufficient price data", "INVALID_DATA")

        AdjustedPriceValidator.validate_price_array(prices, f"technical_analysis:{ticker}")
        if close_prices and len(close_prices) == len(prices):
            AdjustedPriceValidator.warn_if_unadjusted(prices, close_prices, f"technical_analysis:{ticker}")

        current_price = prices[-1]

        moving_averages = {
            "sma_20": self._ma_engine.calculate_sma(prices, 20, f"technical_analysis:{ticker}"),
            "sma_50": self._ma_engine.calculate_sma(prices, 50, f"technical_analysis:{ticker}"),
            "ema_20": self._ma_engine.calculate_ema(prices, 20, f"technical_analysis:{ticker}")
        }

        momentum = {
            "rsi_14": self._momentum_engine.calculate_rsi(prices, 14, f"technical_analysis:{ticker}"),
            "macd": self._momentum_engine.calculate_macd(prices, f"technical_analysis:{ticker}")[0]
        }

        result = TechnicalIndicators(
            ticker=ticker,
            current_price=current_price,
            moving_averages=moving_averages,
            momentum=momentum
        )

        return Result.success(result)
