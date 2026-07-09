"""
Scoring Service - Tier 3 Analysis Service

6D Scoring System with 305-node hierarchy.
Comprehensive stock scoring and ranking.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from ..core import AnalysisService


class ScoringService(AnalysisService):
    """
    6D Scoring service for stock analysis.
    
    Provides:
    - 6D scoring system (305-node hierarchy)
    - Multi-factor analysis
    - Stock ranking and comparison
    - Hierarchy management
    """
    
    # 6D Scoring Dimensions
    DIMENSIONS = [
        "technical",      # Technical indicators
        "fundamental",    # Financial metrics
        "sentiment",      # Market sentiment
        "momentum",       # Momentum indicators
        "risk",          # Risk metrics
        "growth",        # Growth potential
    ]
    
    def __init__(
        self,
        service_name: str = "ScoringService",
        hierarchy_service=None,
    ):
        """
        Initialize scoring service.
        
        Args:
            service_name: Service identifier
            hierarchy_service: Hierarchy service for node management
        """
        super().__init__(service_name)
        self.hierarchy_service = hierarchy_service
        self._hierarchy_nodes: Dict[str, Dict[str, Any]] = {}
        self._scores_cache: Dict[str, Dict[str, float]] = {}
    
    async def initialize(self) -> None:
        """Initialize scoring service"""
        self._initialize_hierarchy()
        self.logger.info("ScoringService initialized with 6D scoring system")
    
    async def shutdown(self) -> None:
        """Shutdown scoring service"""
        self._scores_cache.clear()
        self.logger.info("ScoringService shutdown")
    
    def _initialize_hierarchy(self) -> None:
        """Initialize 305-node scoring hierarchy"""
        # This would typically load from database/hierarchy service
        # For now, create basic structure
        
        node_id = 0
        for dimension in self.DIMENSIONS:
            # Each dimension has ~50 nodes (51 * 6 = 306 total)
            for i in range(51):
                node_id += 1
                self._hierarchy_nodes[f"{dimension}_{i}"] = {
                    "id": node_id,
                    "dimension": dimension,
                    "index": i,
                    "weight": 1.0 / 51,  # Equal weight initially
                    "description": f"{dimension.title()} Factor {i}",
                }
        
        self.logger.info(f"Initialized {len(self._hierarchy_nodes)} hierarchy nodes")
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze stock using 6D scoring system.
        
        Args:
            data: Stock data with indicators
            
        Returns:
            6D score breakdown
        """
        ticker = data.get("ticker", "UNKNOWN")
        
        scores = {
            "ticker": ticker,
            "timestamp": datetime.utcnow().isoformat(),
            "scores": {},
            "overall_score": 0.0,
        }
        
        # Calculate score for each dimension
        for dimension in self.DIMENSIONS:
            dimension_data = data.get(dimension, {})
            score = await self._score_dimension(dimension, dimension_data)
            scores["scores"][dimension] = score
        
        # Calculate weighted overall score
        overall = sum(scores["scores"].values()) / len(self.DIMENSIONS)
        scores["overall_score"] = overall
        
        # Cache the result
        self._scores_cache[ticker] = scores["scores"]
        
        return scores
    
    async def _score_dimension(self, dimension: str, data: Dict[str, Any]) -> float:
        """Score a single dimension"""
        if not data:
            return 0.0
        
        scores = []
        
        # Get all nodes for this dimension
        dimension_nodes = [
            v for k, v in self._hierarchy_nodes.items()
            if v["dimension"] == dimension
        ]
        
        # Calculate weighted average of dimension factors
        for node in dimension_nodes:
            # This would be replaced with actual scoring logic
            # based on the specific metrics for each dimension
            factor_value = data.get(f"factor_{node['index']}", 0.0)
            weighted_score = factor_value * node["weight"]
            scores.append(weighted_score)
        
        return sum(scores) if scores else 0.0
    
    async def score_multiple(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score multiple stocks.
        
        Args:
            stocks: List of stock data
            
        Returns:
            List of score results
        """
        results = []
        for stock in stocks:
            try:
                score = await self.analyze(stock)
                results.append(score)
            except Exception as e:
                self.logger.error(f"Error scoring {stock.get('ticker')}: {e}")
                results.append({"error": str(e)})
        
        return results
    
    async def rank_stocks(
        self,
        stocks: List[Dict[str, Any]],
        dimension: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Rank stocks by score.
        
        Args:
            stocks: List of stock data
            dimension: Optional specific dimension to rank by
            limit: Number of top stocks to return
            
        Returns:
            Ranked stock scores
        """
        scored = await self.score_multiple(stocks)
        
        # Sort by overall score or specific dimension
        if dimension:
            scored.sort(
                key=lambda x: x.get("scores", {}).get(dimension, 0),
                reverse=True
            )
        else:
            scored.sort(
                key=lambda x: x.get("overall_score", 0),
                reverse=True
            )
        
        return scored[:limit]
    
    def get_hierarchy_info(self) -> Dict[str, Any]:
        """Get hierarchy information"""
        return {
            "total_nodes": len(self._hierarchy_nodes),
            "dimensions": len(self.DIMENSIONS),
            "nodes_per_dimension": len(self._hierarchy_nodes) // len(self.DIMENSIONS),
            "dimensions_list": self.DIMENSIONS,
        }
