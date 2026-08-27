"""Crypto Fundamental Analysis Service - Tier 3 Analysis Service

Provides fundamental analysis for cryptocurrency assets based on market cap, supply, and volume.
"""
from typing import Any, Dict, Optional
from collections import deque
from datetime import datetime, timezone

from ..core import AnalysisService
from ..data.crypto_api_client import CryptoApiClient


class CryptoFundamentalAnalysisService(AnalysisService):
    """Fundamental analysis service for cryptocurrencies."""

    def __init__(
        self,
        service_name: str = "CryptoFundamentalAnalysisService",
        crypto_client: Optional[CryptoApiClient] = None,
    ):
        super().__init__(service_name)
        self.crypto_client = crypto_client
        self.historical_data: Dict[str, deque] = {}
        self.peer_metrics_cache: Dict[str, Dict[str, Any]] = {}
        self.max_history_size = 1000

    async def initialize(self) -> None:
        if not self.crypto_client:
            self.logger.warning("CryptoFundamentalAnalysisService initialized without crypto_client")
        self.logger.info("CryptoFundamentalAnalysisService initialized")

    async def shutdown(self) -> None:
        self.logger.info("CryptoFundamentalAnalysisService shutdown")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ticker = data.get("ticker", data.get("symbol", "UNKNOWN"))
        crypto_client = data.get("crypto_client") or self.crypto_client
        use_cache = data.get("use_cache", True)

        if use_cache:
            cache_key = f"fundamental:{ticker}"
            cached_result = self.cache_get(cache_key)
            if cached_result:
                self.logger.info(f"Cache hit for {ticker}")
                return cached_result

        if crypto_client is None:
            raise RuntimeError("CryptoApiClient is not initialized")

        await crypto_client.initialize()
        try:
            raw = await crypto_client.get_market_data(ticker)
        finally:
            await crypto_client.shutdown()

        market_data = raw.get("market_data", {})
        
        current_price = market_data.get("current_price", {})
        usd_price = current_price.get("usd", 0.0) if current_price else 0.0

        market_cap_data = market_data.get("market_cap", {})
        usd_mcap = market_cap_data.get("usd", 0.0) if market_cap_data else 0.0

        supply_data = market_data.get("total_supply", 0.0) or 0.0
        circulating_data = market_data.get("circulating_supply", 0.0) or 0.0

        volume_data = market_data.get("total_volume", {})
        usd_volume = volume_data.get("usd", 0.0) if volume_data else 0.0

        high_24h_data = market_data.get("high_24h", {})
        low_24h_data = market_data.get("low_24h", {})
        usd_high_24h = high_24h_data.get("usd", 0.0) if high_24h_data else 0.0
        usd_low_24h = low_24h_data.get("usd", 0.0) if low_24h_data else 0.0

        price_change_24h = market_data.get("price_change_percentage_24h", 0.0) or 0.0
        market_cap_change_24h = market_data.get("market_cap_change_percentage_24h", 0.0) or 0.0

        liquidity_ratio = (float(usd_volume) / float(usd_mcap)) if float(usd_mcap) > 0 else 0.0
        supply_ratio = (float(circulating_data) / float(supply_data)) if float(supply_data) > 0 else 0.0

        if liquidity_ratio > 0.05:
            liquidity_assessment = "High Liquidity"
        elif liquidity_ratio > 0.01:
            liquidity_assessment = "Moderate Liquidity"
        else:
            liquidity_assessment = "Low Liquidity"

        if supply_ratio > 0.5:
            supply_assessment = "High Circulating Supply"
        elif supply_ratio > 0.0:
            supply_assessment = "Moderate Circulating Supply"
        else:
            supply_assessment = "Low / Unreleased Supply"

        if abs(float(price_change_24h)) > 5:
            volatility_assessment = "High Volatility"
        elif abs(float(price_change_24h)) > 1:
            volatility_assessment = "Moderate Volatility"
        else:
            volatility_assessment = "Low Volatility"

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticker": ticker,
            "price_usd": usd_price,
            "market_cap_usd": usd_mcap,
            "volume_24h_usd": usd_volume,
            "high_24h_usd": usd_high_24h,
            "low_24h_usd": usd_low_24h,
            "price_change_24h_pct": float(price_change_24h),
            "market_cap_change_24h_pct": float(market_cap_change_24h),
            "circulating_supply": float(circulating_data),
            "total_supply": float(supply_data),
            "supply_ratio": supply_ratio,
            "volume_to_market_cap_ratio": liquidity_ratio,
            "peer_comparison": {
                "market_cap_percentile": self._calculate_percentile(ticker, "market_cap"),
                "volume_percentile": self._calculate_percentile(ticker, "volume"),
                "volatility_percentile": self._calculate_percentile(ticker, "volatility"),
            },
            "assessment": {
                "liquidity": liquidity_assessment,
                "supply": supply_assessment,
                "volatility": volatility_assessment,
            },
            "raw": raw,
        }
        
        self.cache_set(f"fundamental:{ticker}", result, ttl_seconds=3600)
        return result
    
    def _calculate_liquidity_ratio(self, volume: float, market_cap: float) -> float:
        """Calculate liquidity ratio (volume / market_cap)."""
        return volume / market_cap if market_cap > 0 else 0.0
    
    def _calculate_supply_ratio(self, circulating_supply: float, total_supply: float) -> float:
        """Calculate circulating supply ratio."""
        return circulating_supply / total_supply if total_supply > 0 else 0.0
    
    def _assess_liquidity(self, liquidity_ratio: float) -> str:
        """Assess liquidity level based on ratio."""
        if liquidity_ratio > 0.05:
            return "High Liquidity"
        elif liquidity_ratio > 0.01:
            return "Moderate Liquidity"
        else:
            return "Low Liquidity"
    
    def _assess_supply(self, supply_ratio: float) -> str:
        """Assess supply level based on ratio."""
        if supply_ratio > 0.5:
            return "High Circulating Supply"
        elif supply_ratio > 0.0:
            return "Moderate Circulating Supply"
        else:
            return "Low / Unreleased Supply"
    
    def _assess_volatility(self, price_change_pct: float) -> str:
        """Assess volatility level based on price change percentage."""
        if abs(float(price_change_pct)) > 5:
            return "High Volatility"
        elif abs(float(price_change_pct)) > 1:
            return "Moderate Volatility"
        else:
            return "Low Volatility"

    def _calculate_percentile(self, ticker: str, metric: str) -> Optional[float]:
        """Calculate percentile ranking for a given ticker and metric."""
        if metric not in self.peer_metrics_cache:
            return None
        peers = self.peer_metrics_cache[metric]
        if not peers or ticker not in [p["ticker"] for p in peers]:
            return None
        # Sort by metric value descending (higher is better)
        sorted_peers = sorted(peers, key=lambda x: x["value"], reverse=True)
        rank = next((i for i, p in enumerate(sorted_peers) if p["ticker"] == ticker), None)
        if rank is None:
            return None
        return 100.0 * (len(sorted_peers) - rank) / len(sorted_peers)

    async def update_peer_metrics(self, ticker: str, metrics: Dict[str, float]) -> None:
        """Update peer metrics cache with new values for a ticker."""
        for metric_name, value in metrics.items():
            if metric_name not in self.peer_metrics_cache:
                self.peer_metrics_cache[metric_name] = []
            # Remove existing entry for this ticker
            self.peer_metrics_cache[metric_name] = [
                p for p in self.peer_metrics_cache[metric_name] if p["ticker"] != ticker
            ]
            self.peer_metrics_cache[metric_name].append({"ticker": ticker, "value": value})
            # Keep only top 1000 entries
            if len(self.peer_metrics_cache[metric_name]) > self.max_history_size:
                self.peer_metrics_cache[metric_name] = self.peer_metrics_cache[metric_name][-self.max_history_size:]