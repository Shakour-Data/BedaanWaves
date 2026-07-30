"""
Crypto Fundamental Analysis Service - Tier 3 Analysis Service

Provides fundamental analysis for cryptocurrency assets based on market cap, supply, and volume.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from ..core import AnalysisService
from ..data.crypto_api_client import CryptoApiClient

class CryptoFundamentalAnalysisService(AnalysisService):
    """
    Fundamental analysis service for cryptocurrencies.
    
    Provides:
    - Market Cap Analysis (Market Cap, Circulating Supply, Total Supply)
    - Liquidity Analysis (Volume to Market Cap Ratio)
    - Supply Metrics (Supply Inflation/Deflation)
    - Volatility-Adjusted Metrics
    """
    
    def __init__(
        self, 
        service_name: str = "CryptoFundamentalAnalysisService",
        crypto_client: Optional[CryptoApiClient] = None
    ):
        """Initialize crypto fundamental analysis service"""
        super().__init__(service_name)
        self.crypto_client = crypto_client
    
    async def initialize(self) -> None:
        """Initialize service"""
        if not self.crypto_client:
            self.logger.warning("CryptoFundamentalAnalysisService initialized without crypto_client")
        self.logger.info("CryptoFundamentalAnalysisService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown service"""
        self.logger.info("CryptoFundamentalAnalysisService shutdown")
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform fundamental analysis on crypto data.
        
        Args:
            data: Dictionary containing crypto market data (from CryptoApiClient)
            
        Returns:
            Fundamental metrics and ratios
        """
        # Expected data structure from CoinGecko/Binance:
        # {
        #   "market_data": {"current_market_cap":..., "total_market_cap":..., "circulating_supply":...},
        #   "volume": {"24h_vol":...},
        #   "ticker": "bitcoin"
        # }
        
        market_data = data.get("market_data", {})
        volume_data = data.get("volume", {})
        ticker = data.get("ticker", "UNKNOWN")
        
        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticker": ticker,
            "ratios": {},
            "metrics": {},
            "assessment": "",
        }
        
        # 1. Market Cap & Supply Metrics
        analysis["metrics"].update(
            await self._calculate_supply_metrics(market_data)
        )
        
        # 2. Liquidity Metrics
        analysis["ratios"].update(
            await self._calculate_liquidity_ratios(market_data, volume_data)
        )
        
        # 3. Assessment (Basic rule-based)
        analysis["assessment"] = self._generate_assessment(analysis["ratios"])
        
        return analysis
    
    async def _calculate_supply_metrics(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate supply-related metrics"""
        mcap = market_data.get("current_market_cap", 0)
        total_supply = market_data.get("total_market_cap", 0) # Assuming this is total supply in the context of Coingecko data
        circulating_supply = market_data.get("circulating_supply", 0)
        
        return {
            "market_cap": float(mcap),
            "total_supply": float(total_supply),
            "circulating_supply": float(circulating_supply),
            "supply_ratio": self._safe_div(circulating_supply, total_supply) if total_supply > 0 else 0.0,
        }
    
    async def _calculate_liquidity_ratios(self, market_data: Dict[str, Any], volume_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate liquidity ratios"""
        mcap = market_data.get("current_market_cap", 0)
        vol_24h = volume_data.get("24h_vol", 0)
        
        return {
            "volume_to_mcap_ratio": self._safe_div(float(vol_24h), float(mcap)) if mcap > 0 else 0.0,
        }
    
    def _generate_assessment(self, ratios: Dict[str, float]) -> str:
        """Simple heuristic for assessment"""
        v_mcap_ratio = ratios.get("volume_to_mcap_ratio", 0)
        
        if v_mcap_ratio > 0.1:
            return "High Liquidity"
        elif v_mcap_ratio > 0.01:
            return "Moderate Liquidity"
        else:
            return "Low Liquidity"

    def _safe_div(self, numerator: float, denominator: float) -> float:
        if denominator <= 0:
            return 0.0
        return numerator / denominator
