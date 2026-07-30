"""
Crypto Market Cap Service - Tier 8 Crypto Service

Provides market cap based filtering and ranking of cryptocurrencies.
Supports filtering by market cap tiers, volume, and other metrics.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from app.core import BaseService
import logging

class CryptoMarketCapService(BaseService):
    """
    Crypto Market Cap Service.
    
    Handles:
    - Market cap tier classification
    - Market cap based filtering
    - Volume analysis
    - Market cap change tracking
    - Portfolio allocation by market cap
    """
    
    def __init__(self,
                 service_name: str = "CryptoMarketCapService",
                 crypto_client: Optional[Any] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize crypto market cap service.
        
        Args:
            service_name: Service identifier
            crypto_client: Crypto API client instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.crypto_client = crypto_client
        
        # Market cap tiers (in USD)
        self.market_cap_tiers = {
            "Large Cap": {"min": 10_000_000_000, "max": float('inf')},      # >$10B
            "Mid Cap": {"min": 1_000_000_000, "max": 10_000_000_000},        # $1B-$10B
            "Small Cap": {"min": 100_000_000, "max": 1_000_000_000},         # $100M-$1B
            "Micro Cap": {"min": 50_000_000, "max": 100_000_000},            # $50M-$100M
            "Nano Cap": {"min": 0, "max": 50_000_000}                        # <$50M
        }
        
        # Volume tiers (24h USD)
        self.volume_tiers = {
            "Very High": {"min": 1_000_000_000, "max": float('inf')},       # >$1B
            "High": {"min": 100_000_000, "max": 1_000_000_000},             # $100M-$1B
            "Medium": {"min": 10_000_000, "max": 100_000_000},              # $10M-$100M
            "Low": {"min": 1_000_000, "max": 10_000_000},                   # $1M-$10M
            "Very Low": {"min": 0, "max": 1_000_000}                        # <$1M
        }
        
        # Cache for market data
        self._market_data_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes
    
    async def initialize(self) -> None:
        """Initialize crypto market cap service."""
        self.logger.info("Initializing CryptoMarketCapService")
        self.logger.info("CryptoMarketCapService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown crypto market cap service."""
        self._market_data_cache.clear()
        self.logger.info("CryptoMarketCapService shutdown")
    
    async def get_market_cap_tiers(self) -> Dict[str, Dict[str, float]]:
        """
        Get market cap tier definitions.
        
        Returns:
            Dictionary of tier names to min/max values
        """
        return self.market_cap_tiers
    
    async def get_volume_tiers(self) -> Dict[str, Dict[str, float]]:
        """
        Get volume tier definitions.
        
        Returns:
            Dictionary of tier names to min/max values
        """
        return self.volume_tiers
    
    async def classify_by_market_cap(self, market_cap: float) -> str:
        """
        Classify a cryptocurrency by market cap.
        
        Args:
            market_cap: Market cap in USD
            
        Returns:
            Tier name
        """
        for tier, bounds in self.market_cap_tiers.items():
            if bounds["min"] <= market_cap <= bounds["max"]:
                return tier
        return "Unknown"
    
    async def classify_by_volume(self, volume_24h: float) -> str:
        """
        Classify a cryptocurrency by 24h volume.
        
        Args:
            volume_24h: 24h trading volume in USD
            
        Returns:
            Tier name
        """
        for tier, bounds in self.volume_tiers.items():
            if bounds["min"] <= volume_24h <= bounds["max"]:
                return tier
        return "Unknown"
    
    async def filter_by_market_cap(self,
                                   cryptos: List[Dict[str, Any]],
                                   min_market_cap: float = 0,
                                   max_market_cap: float = None,
                                   tier: str = None) -> List[Dict[str, Any]]:
        """
        Filter cryptocurrencies by market cap.
        
        Args:
            cryptos: List of cryptocurrency data
            min_market_cap: Minimum market cap
            max_market_cap: Maximum market cap
            tier: Market cap tier name
            
        Returns:
            Filtered list
        """
        if tier and tier in self.market_cap_tiers:
            bounds = self.market_cap_tiers[tier]
            min_market_cap = max(min_market_cap, bounds["min"])
            max_market_cap = min(max_market_cap or float('inf'), bounds["max"])
        
        filtered = []
        for crypto in cryptos:
            mc = crypto.get("market_cap", 0)
            if mc >= min_market_cap:
                if max_market_cap is None or mc <= max_market_cap:
                    filtered.append(crypto)
        
        return filtered
    
    async def filter_by_volume(self,
                               cryptos: List[Dict[str, Any]],
                               min_volume: float = 0,
                               max_volume: float = None,
                               tier: str = None) -> List[Dict[str, Any]]:
        """
        Filter cryptocurrencies by 24h volume.
        
        Args:
            cryptos: List of cryptocurrency data
            min_volume: Minimum 24h volume
            max_volume: Maximum 24h volume
            tier: Volume tier name
            
        Returns:
            Filtered list
        """
        if tier and tier in self.volume_tiers:
            bounds = self.volume_tiers[tier]
            min_volume = max(min_volume, bounds["min"])
            max_volume = min(max_volume or float('inf'), bounds["max"])
        
        filtered = []
        for crypto in cryptos:
            vol = crypto.get("volume_24h", 0)
            if vol >= min_volume:
                if max_volume is None or vol <= max_volume:
                    filtered.append(crypto)
        
        return filtered
    
    async def get_market_cap_distribution(self,
                                         cryptos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get market cap distribution of a list of cryptocurrencies.
        
        Args:
            cryptos: List of cryptocurrency data
            
        Returns:
            Distribution statistics
        """
        if not cryptos:
            return {
                "tiers": {},
                "total_market_cap": 0,
                "avg_market_cap": 0,
                "median_market_cap": 0,
                "count": 0
            }
        
        # Classify each crypto
        tier_counts = {tier: 0 for tier in self.market_cap_tiers}
        tier_market_caps = {tier: [] for tier in self.market_cap_tiers}
        
        all_market_caps = []
        
        for crypto in cryptos:
            mc = crypto.get("market_cap", 0)
            all_market_caps.append(mc)
            
            tier = await self.classify_by_market_cap(mc)
            if tier in tier_counts:
                tier_counts[tier] += 1
                tier_market_caps[tier].append(mc)
        
        # Calculate statistics
        all_market_caps.sort()
        total = sum(all_market_caps)
        avg = total / len(all_market_caps) if all_market_caps else 0
        median = all_market_caps[len(all_market_caps) // 2] if all_market_caps else 0
        
        tier_stats = {}
        for tier in self.market_cap_tiers:
            caps = tier_market_caps[tier]
            tier_stats[tier] = {
                "count": len(caps),
                "percentage": round(len(caps) / len(cryptos) * 100, 2) if cryptos else 0,
                "total_market_cap": sum(caps),
                "avg_market_cap": sum(caps) / len(caps) if caps else 0,
                "min": min(caps) if caps else 0,
                "max": max(caps) if caps else 0
            }
        
        return {
            "tiers": tier_stats,
            "total_market_cap": total,
            "avg_market_cap": avg,
            "median_market_cap": median,
            "count": len(cryptos)
        }
    
    async def get_volume_distribution(self,
                                     cryptos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get volume distribution of a list of cryptocurrencies.
        
        Args:
            cryptos: List of cryptocurrency data
            
        Returns:
            Distribution statistics
        """
        if not cryptos:
            return {
                "tiers": {},
                "total_volume": 0,
                "avg_volume": 0,
                "count": 0
            }
        
        tier_counts = {tier: 0 for tier in self.volume_tiers}
        tier_volumes = {tier: [] for tier in self.volume_tiers}
        
        all_volumes = []
        
        for crypto in cryptos:
            vol = crypto.get("volume_24h", 0)
            all_volumes.append(vol)
            
            tier = await self.classify_by_volume(vol)
            if tier in tier_counts:
                tier_counts[tier] += 1
                tier_volumes[tier].append(vol)
        
        total = sum(all_volumes)
        avg = total / len(all_volumes) if all_volumes else 0
        
        tier_stats = {}
        for tier in self.volume_tiers:
            vols = tier_volumes[tier]
            tier_stats[tier] = {
                "count": len(vols),
                "percentage": round(len(vols) / len(cryptos) * 100, 2) if cryptos else 0,
                "total_volume": sum(vols),
                "avg_volume": sum(vols) / len(vols) if vols else 0
            }
        
        return {
            "tiers": tier_stats,
            "total_volume": total,
            "avg_volume": avg,
            "count": len(cryptos)
        }
    
    async def rank_by_market_cap(self,
                                 cryptos: List[Dict[str, Any]],
                                 ascending: bool = False) -> List[Dict[str, Any]]:
        """
        Rank cryptocurrencies by market cap.
        
        Args:
            cryptos: List of cryptocurrency data
            ascending: Sort ascending (smallest first)
            
        Returns:
            Ranked list
        """
        ranked = sorted(
            cryptos, 
            key=lambda x: x.get("market_cap", 0), 
            reverse=not ascending
        )
        
        for i, crypto in enumerate(ranked, 1):
            crypto = crypto.copy()
            crypto["market_cap_rank"] = i
            crypto["market_cap_tier"] = await self.classify_by_market_cap(
                crypto.get("market_cap", 0)
            )
        
        return ranked
    
    async def rank_by_volume(self,
                            cryptos: List[Dict[str, Any]],
                            ascending: bool = False) -> List[Dict[str, Any]]:
        """
        Rank cryptocurrencies by 24h volume.
        
        Args:
            cryptos: List of cryptocurrency data
            ascending: Sort ascending
            
        Returns:
            Ranked list
        """
        ranked = sorted(
            cryptos,
            key=lambda x: x.get("volume_24h", 0),
            reverse=not ascending
        )
        
        for i, crypto in enumerate(ranked, 1):
            crypto = crypto.copy()
            crypto["volume_rank"] = i
            crypto["volume_tier"] = await self.classify_by_volume(
                crypto.get("volume_24h", 0)
            )
        
        return ranked
    
    async def get_market_dominance(self,
                                  cryptos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate market dominance metrics.
        
        Args:
            cryptos: List of cryptocurrency data
            
        Returns:
            Dominance metrics
        """
        total_mc = sum(c.get("market_cap", 0) for c in cryptos)
        
        if total_mc == 0:
            return {
                "btc_dominance": 0,
                "eth_dominance": 0,
                "top_10_dominance": 0,
                "top_50_dominance": 0
            }
        
        # BTC dominance
        btc = next((c for c in cryptos if c.get("symbol") == "BTC"), None)
        btc_dom = (btc.get("market_cap", 0) / total_mc * 100) if btc else 0
        
        # ETH dominance
        eth = next((c for c in cryptos if c.get("symbol") == "ETH"), None)
        eth_dom = (eth.get("market_cap", 0) / total_mc * 100) if eth else 0
        
        # Top 10 dominance
        top_10 = await self.rank_by_market_cap(cryptos)
        top_10_mc = sum(c.get("market_cap", 0) for c in top_10[:10])
        top_10_dom = (top_10_mc / total_mc * 100)
        
        # Top 50 dominance
        top_50_mc = sum(c.get("market_cap", 0) for c in top_10[:50])
        top_50_dom = (top_50_mc / total_mc * 100)
        
        return {
            "btc_dominance": round(btc_dom, 2),
            "eth_dominance": round(eth_dom, 2),
            "top_10_dominance": round(top_10_dom, 2),
            "top_50_dominance": round(top_50_dom, 2),
            "total_market_cap": total_mc,
            "others_dominance": round(100 - btc_dom - eth_dom - (top_10_dom - btc_dom - eth_dom), 2)
        }
    
    async def get_market_cap_change_analysis(self,
                                            current_cryptos: List[Dict[str, Any]],
                                            previous_cryptos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze market cap changes between two snapshots.
        
        Args:
            current_cryptos: Current snapshot
            previous_cryptos: Previous snapshot
            
        Returns:
            Change analysis
        """
        # Create lookup for previous data
        prev_lookup = {c["symbol"]: c for c in previous_cryptos if "symbol" in c}
        
        changes = []
        for crypto in current_cryptos:
            symbol = crypto.get("symbol")
            if not symbol or symbol not in prev_lookup:
                continue
            
            prev = prev_lookup[symbol]
            curr_mc = crypto.get("market_cap", 0)
            prev_mc = prev.get("market_cap", 0)
            
            if prev_mc > 0:
                change_pct = ((curr_mc - prev_mc) / prev_mc) * 100
            else:
                change_pct = 0
            
            changes.append({
                "symbol": symbol,
                "name": crypto.get("name", ""),
                "current_market_cap": curr_mc,
                "previous_market_cap": prev_mc,
                "change_absolute": curr_mc - prev_mc,
                "change_percent": round(change_pct, 2),
                "tier": await self.classify_by_market_cap(curr_mc)
            })
        
        # Sort by change
        changes.sort(key=lambda x: x["change_percent"], reverse=True)
        
        gainers = [c for c in changes if c["change_percent"] > 0]
        losers = [c for c in changes if c["change_percent"] < 0]
        
        return {
            "total_analyzed": len(changes),
            "gainers": len(gainers),
            "losers": len(losers),
            "unchanged": len(changes) - len(gainers) - len(losers),
            "top_gainers": gainers[:10],
            "top_losers": losers[:10],
            "avg_change": round(sum(c["change_percent"] for c in changes) / len(changes), 2) if changes else 0
        }
    
    async def allocate_by_market_cap(self,
                                     portfolio_value: float,
                                     cryptos: List[Dict[str, Any]],
                                     strategy: str = "market_cap_weighted") -> Dict[str, Any]:
        """
        Allocate portfolio by market cap weights.
        
        Args:
            portfolio_value: Total portfolio value
            cryptos: List of available cryptocurrencies
            strategy: Allocation strategy
            
        Returns:
            Allocation plan
        """
        if strategy == "market_cap_weighted":
            total_mc = sum(c.get("market_cap", 0) for c in cryptos)
            if total_mc == 0:
                return {"error": "No valid market caps for allocation"}
            
            allocation = {}
            for crypto in cryptos:
                mc = crypto.get("market_cap", 0)
                weight = mc / total_mc
                allocation[crypto["symbol"]] = {
                    "name": crypto.get("name", ""),
                    "weight": round(weight, 6),
                    "value": round(portfolio_value * weight, 2),
                    "market_cap": mc,
                    "tier": await self.classify_by_market_cap(mc)
                }
            
            return {
                "strategy": "market_cap_weighted",
                "total_value": portfolio_value,
                "allocation": allocation,
                "num_assets": len(allocation)
            }
        
        elif strategy == "equal_weight":
            weight = 1.0 / len(cryptos)
            allocation = {}
            for crypto in cryptos:
                allocation[crypto["symbol"]] = {
                    "name": crypto.get("name", ""),
                    "weight": round(weight, 6),
                    "value": round(portfolio_value * weight, 2),
                    "market_cap": crypto.get("market_cap", 0),
                    "tier": await self.classify_by_market_cap(crypto.get("market_cap", 0))
                }
            
            return {
                "strategy": "equal_weight",
                "total_value": portfolio_value,
                "allocation": allocation,
                "num_assets": len(allocation)
            }
        
        elif strategy == "tier_balanced":
            # Allocate equally across tiers, then within tier by market cap
            tiers = list(self.market_cap_tiers.keys())
            tier_allocation = 1.0 / len(tiers)
            
            allocation = {}
            for tier in tiers:
                tier_cryptos = [c for c in cryptos 
                               if await self.classify_by_market_cap(c.get("market_cap", 0)) == tier]
                
                if not tier_cryptos:
                    continue
                
                tier_weight = tier_allocation
                tier_mc_total = sum(c.get("market_cap", 0) for c in tier_cryptos)
                
                if tier_mc_total == 0:
                    # Equal weight within tier
                    weight_per_crypto = tier_weight / len(tier_cryptos)
                    for crypto in tier_cryptos:
                        allocation[crypto["symbol"]] = {
                            "name": crypto.get("name", ""),
                            "weight": round(weight_per_crypto, 6),
                            "value": round(portfolio_value * weight_per_crypto, 2),
                            "market_cap": crypto.get("market_cap", 0),
                            "tier": tier
                        }
                else:
                    for crypto in tier_cryptos:
                        mc = crypto.get("market_cap", 0)
                        weight = tier_weight * (mc / tier_mc_total)
                        allocation[crypto["symbol"]] = {
                            "name": crypto.get("name", ""),
                            "weight": round(weight, 6),
                            "value": round(portfolio_value * weight, 2),
                            "market_cap": mc,
                            "tier": tier
                        }
            
            return {
                "strategy": "tier_balanced",
                "total_value": portfolio_value,
                "allocation": allocation,
                "num_assets": len(allocation)
            }
        
        else:
            return {"error": f"Unknown strategy: {strategy}"}

# Factory function for dependency injection
def get_crypto_market_cap_service(crypto_client=None,
                                   logger=None) -> CryptoMarketCapService:
    """Factory function to create CryptoMarketCapService instance."""
    return CryptoMarketCapService(
        service_name="CryptoMarketCapService",
        crypto_client=crypto_client,
        logger=logger
    )