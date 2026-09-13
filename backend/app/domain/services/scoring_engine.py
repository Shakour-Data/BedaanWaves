from typing import Dict, Any, List
from ..interfaces.i_scoring_engine import IScoringEngine
from ..entities.stock_score import StockScore
from ..value_objects.dimension import DimensionType
from .scoring_strategies import IScoringStrategy, TseScoringStrategy, GlobalScoringStrategy

class ScoringEngine(IScoringEngine):
    """
    Domain service for 6D scoring.
    Uses Strategy pattern to handle different markets.
    """
    
    def __init__(self, strategies: Dict[str, IScoringStrategy]):
        self._strategies = strategies
        self._default_weights = {
            DimensionType.FUNDAMENTAL: 0.25,
            DimensionType.TECHNICAL: 0.20,
            DimensionType.SENTIMENT: 0.15,
            DimensionType.RISK: 0.20,
            DimensionType.MACRO: 0.10,
            DimensionType.AI: 0.10
        }

    def calculate_total_score(
        self, 
        ticker: str, 
        market: str, 
        dimension_data: Dict[DimensionType, Dict[str, Any]]
    ) -> StockScore:
        dimension_scores = {}
        for dim_type, data in dimension_data.items():
            score = self.score_dimension(dim_type, data, market)
            dimension_scores[dim_type] = score
            
        stock_score = StockScore(ticker=ticker, market=market, dimension_scores=dimension_scores)
        stock_score.calculate_overall(self._default_weights)
        return stock_score

    def score_dimension(self, dimension: DimensionType, data: Dict[str, Any], market: str) -> float:
        strategy = self._get_strategy(market)
        scores = []
        for key, value in data.items():
            if not isinstance(value, (int, float)): continue
            
            if "rsi" in key: scores.append(strategy.score_rsi(value))
            elif "pe_ratio" in key: scores.append(strategy.score_pe(value))
            else: scores.append(min(100.0, max(0.0, float(value))))
            
        return round(sum(scores) / len(scores), 2) if scores else 0.0

    def _get_strategy(self, market: str) -> IScoringStrategy:
        return self._strategies.get(market.upper(), GlobalScoringStrategy())
