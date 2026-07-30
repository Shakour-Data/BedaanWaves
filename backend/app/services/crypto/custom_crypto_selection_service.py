"""
Custom Crypto Selection Service - Tier 8 Crypto Service

Allows users to select from top 300 cryptocurrencies for personalized ranking and analysis.
Manages user-defined cryptocurrency portfolios and selections.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from app.core import BaseService
import logging

class CustomCryptoSelectionService(BaseService):
    """
    Custom Crypto Selection Service.
    
    Handles:
    - User selection from top 300 cryptocurrencies
    - Custom portfolio creation
    - Selection validation and management
    - Ranking of user-selected cryptos
    """
    
    def __init__(self,
                 service_name: str = "CustomCryptoSelectionService",
                 crypto_client: Optional[Any] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize custom crypto selection service.
        
        Args:
            service_name: Service identifier
            crypto_client: Crypto API client instance
            logger: Optional logger instance
        """
        super().__init__(service_name, logger=logger)
        self.crypto_client = crypto_client
        
        # Default user selection
        self.default_selection = [
            "BTC", "ETH", "BNB", "ADA", "SOL", "XRP", "DOT", 
            "DOGE", "AVAX", "MATIC", "LINK", "UNI", "LTC", "BCH"
        ]
        
        # Top 300 cryptocurrencies (would be fetched from API in production)
        self.top_300 = self._initialize_top_300()
        
        # Categories for filtering
        self.categories = {
            "Layer 1": ["BTC", "ETH", "BNB", "ADA", "SOL", "AVAX", "DOT", "NEAR", "ATOM", "FTM"],
            "DeFi": ["UNI", "AAVE", "COMP", "MKR", "CRV", "SUSHI", "YFI", "BAL", "SNX", "1INCH"],
            "NFT/Metaverse": ["MANA", "SAND", "AXS", "ENJ", "THETA", "CHZ", "FLOW", "GALA"],
            "Layer 2": ["MATIC", "OP", "ARB", "IMX", "METIS", "BOBA"],
            "Oracles": ["LINK", "BAND", "API3", "TRB"],
            "Exchange Tokens": ["BNB", "FTT", "OKB", "HT", "KCS", "CRO"],
            "Stablecoins": ["USDT", "USDC", "BUSD", "DAI", "FRAX", "TUSD"],
            "Meme Coins": ["DOGE", "SHIB", "FLOKI", "BABYDOGE", "PEPE"],
            "Gaming": ["AXS", "SAND", "MANA", "ENJ", "GALA", "ILV", "YGG"],
            "Web3": ["DOT", "KSM", "ATOM", "NEAR", "FIL", "AR"],
            "Privacy": ["XMR", "ZEC", "DASH", "SCRT"],
            "Storage": ["FIL", "AR", "STORJ", "SIA", "HNT"]
        }
        
        # Risk categories
        self.risk_categories = {
            "Low": ["BTC", "ETH", "USDT", "USDC", "BUSD"],
            "Medium": ["BNB", "ADA", "SOL", "DOT", "AVAX", "MATIC", "LINK"],
            "High": ["DOGE", "SHIB", "FLOKI", "PEPE", "FLOKI"],
            "Very High": ["SHIB", "FLOKI", "PEPE", "BABYDOGE", "FLOKI"]
        }
    
    def _initialize_top_300(self) -> List[Dict[str, Any]]:
        """Initialize default top 300 cryptocurrencies."""
        # In production, would fetch from API
        top_50 = [
            {"symbol": "BTC", "name": "Bitcoin", "rank": 1, "category": "Layer 1", "risk": "Low"},
            {"symbol": "ETH", "name": "Ethereum", "rank": 2, "category": "Layer 1", "risk": "Low"},
            {"symbol": "BNB", "name": "Binance Coin", "rank": 3, "category": "Exchange Tokens", "risk": "Medium"},
            {"symbol": "ADA", "name": "Cardano", "rank": 4, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "SOL", "name": "Solana", "rank": 5, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "XRP", "name": "XRP", "rank": 6, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "DOT", "name": "Polkadot", "rank": 7, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "DOGE", "name": "Dogecoin", "rank": 8, "category": "Meme Coins", "risk": "High"},
            {"symbol": "AVAX", "name": "Avalanche", "rank": 9, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "MATIC", "name": "Polygon", "rank": 10, "category": "Layer 2", "risk": "Medium"},
            {"symbol": "LINK", "name": "Chainlink", "rank": 11, "category": "Oracles", "risk": "Medium"},
            {"symbol": "UNI", "name": "Uniswap", "rank": 12, "category": "DeFi", "risk": "Medium"},
            {"symbol": "LTC", "name": "Litecoin", "rank": 13, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "BCH", "name": "Bitcoin Cash", "rank": 14, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "ATOM", "name": "Cosmos", "rank": 15, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "ETC", "name": "Ethereum Classic", "rank": 16, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "FIL", "name": "Filecoin", "rank": 17, "category": "Storage", "risk": "Medium"},
            {"symbol": "TRX", "name": "TRON", "rank": 18, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "XLM", "name": "Stellar", "rank": 19, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "NEAR", "name": "Near Protocol", "rank": 20, "category": "Layer 1", "risk": "Medium"},
            {"symbol": "MANA", "name": "Decentraland", "rank": 21, "category": "NFT/Metaverse", "risk": "High"},
            {"symbol": "SAND", "name": "The Sandbox", "rank": 22, "category": "NFT/Metaverse", "risk": "High"},
            {"symbol": "AXS", "name": "Axie Infinity", "rank": 23, "category": "Gaming", "risk": "High"},
            {"symbol": "AAVE", "name": "Aave", "rank": 24, "category": "DeFi", "risk": "Medium"},
            {"symbol": "COMP", "name": "Compound", "rank": 25, "category": "DeFi", "risk": "Medium"},
            {"symbol": "MKR", "name": "Maker", "rank": 26, "category": "DeFi", "risk": "Medium"},
            {"symbol": "CRV", "name": "Curve DAO", "rank": 27, "category": "DeFi", "risk": "Medium"},
            {"symbol": "SUSHI", "name": "SushiSwap", "rank": 28, "category": "DeFi", "risk": "Medium"},
            {"symbol": "YFI", "name": "yearn.finance", "rank": 28, "category": "DeFi", "risk": "High"},
            {"symbol": "ENJ", "name": "Enjin Coin", "rank": 29, "category": "NFT/Metaverse", "risk": "High"},
            {"symbol": "THETA", "name": "Theta Network", "rank": 30, "category": "NFT/Metaverse", "risk": "High"},
            # ... would continue to 300
        ]
        
        # Add placeholder for remaining
        for i in range(31, 301):
            top_50.append({
                "symbol": f"CRYPTO{i}",
                "name": f"Cryptocurrency {i}",
                "rank": i,
                "category": "Other",
                "risk": "Medium"
            })
        
        return top_50
    
    async def initialize(self) -> None:
        """Initialize custom crypto selection service."""
        self.logger.info("Initializing CustomCryptoSelectionService")
        
        # Try to fetch latest top 300 from API
        if self.crypto_client:
            try:
                await self._refresh_top_300()
            except Exception as e:
                self.logger.warning(f"Failed to refresh top 300: {str(e)}")
        
        self.logger.info("CustomCryptoSelectionService initialized")
    
    async def shutdown(self) -> None:
        """Shutdown custom crypto selection service."""
        self.logger.info("CustomCryptoSelectionService shutdown")
    
    async def get_top_300(self) -> List[Dict[str, Any]]:
        """
        Get list of top 300 cryptocurrencies.
        
        Returns:
            List of top 300 cryptocurrencies with metadata
        """
        return self.top_300
    
    async def get_available_cryptos(self) -> List[Dict[str, Any]]:
        """
        Get available cryptocurrencies for selection (alias for get_top_300).
        
        Returns:
            List of available cryptocurrencies
        """
        return await self.get_top_300()
    
    async def get_crypto_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cryptocurrency info by symbol.
        
        Args:
            symbol: Crypto symbol
            
        Returns:
            Cryptocurrency info or None
        """
        symbol = symbol.upper()
        for crypto in self.top_300:
            if crypto["symbol"].upper() == symbol:
                return crypto
        return None
    
    async def get_cryptos_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get cryptocurrencies by category.
        
        Args:
            category: Category name
            
        Returns:
            List of cryptocurrencies in category
        """
        symbols = self.categories.get(category, [])
        return [c for c in self.top_300 if c["symbol"] in symbols]
    
    async def get_cryptos_by_risk(self, risk: str) -> List[Dict[str, Any]]:
        """
        Get cryptocurrencies by risk level.
        
        Args:
            risk: Risk level (Low, Medium, High, Very High)
            
        Returns:
            List of cryptocurrencies with specified risk
        """
        return [c for c in self.top_300 if c.get("risk") == risk]
    
    async def validate_selection(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Validate user's cryptocurrency selection.
        
        Args:
            symbols: List of crypto symbols
            
        Returns:
            Validation results
        """
        available_symbols = {c["symbol"].upper() for c in self.top_300}
        
        validated = []
        invalid = []
        warnings = []
        
        for symbol in symbols:
            upper_symbol = symbol.upper()
            if upper_symbol in available_symbols:
                validated.append(upper_symbol)
            else:
                invalid.append(symbol)
        
        # Check for duplicates
        if len(set(validated)) != len(validated):
            warnings.append("Duplicate symbols in selection")
            validated = list(set(validated))
        
        return {
            "validated": validated,
            "invalid": invalid,
            "warnings": warnings,
            "total_valid": len(validated),
            "total_invalid": len(invalid)
        }
    
    async def get_selection_recommendations(self,
                                           current_selection: List[str],
                                           max_recommendations: int = 10) -> List[Dict[str, Any]]:
        """
        Get recommendations to complement current selection.
        
        Args:
            current_selection: User's current crypto selection
            max_recommendations: Maximum recommendations to return
            
        Returns:
            Recommended cryptocurrencies
        """
        current_set = {s.upper() for s in current_selection}
        
        # Find categories in current selection
        current_categories = set()
        for symbol in current_selection:
            crypto = await self.get_crypto_by_symbol(symbol)
            if crypto and crypto.get("category"):
                current_categories.add(crypto["category"])
        
        # Recommend from missing categories
        recommendations = []
        
        for category, symbols in self.categories.items():
            if category not in current_categories and len(recommendations) < max_recommendations:
                for symbol in symbols[:2]:  # Max 2 per category
                    if symbol not in current_set:
                        crypto = await self.get_crypto_by_symbol(symbol)
                        if crypto:
                            recommendations.append({
                                **crypto,
                                "recommendation_reason": f"Diversification into {category}"
                            })
                            if len(recommendations) >= max_recommendations:
                                break
        
        # If still need more, add from top ranked not in selection
        if len(recommendations) < max_recommendations:
            for crypto in self.top_300:
                if crypto["symbol"] not in current_set:
                    if not any(r["symbol"] == crypto["symbol"] for r in recommendations):
                        recommendations.append({
                            **crypto,
                            "recommendation_reason": "Top ranked not in selection"
                        })
                        if len(recommendations) >= max_recommendations:
                            break
        
        return recommendations[:max_recommendations]
    
    async def create_custom_portfolio(self,
                                     name: str,
                                     symbols: List[str],
                                     weights: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Create a custom crypto portfolio.
        
        Args:
            name: Portfolio name
            symbols: List of crypto symbols
            weights: Optional weight for each symbol
            
        Returns:
            Portfolio definition
        """
        validation = await self.validate_selection(symbols)
        
        if not validation["validated"]:
            raise ValueError("No valid cryptocurrencies in selection")
        
        # Normalize weights if provided
        if weights:
            total = sum(weights.get(s, 0) for s in validation["validated"])
            if total > 0:
                weights = {s: weights.get(s, 0) / total for s in validation["validated"]}
            else:
                weights = {s: 1.0 / len(validation["validated"]) for s in validation["validated"]}
        else:
            weights = {s: 1.0 / len(validation["validated"]) for s in validation["validated"]}
        
        return {
            "name": name,
            "symbols": validation["validated"],
            "weights": weights,
            "created_at": datetime.utcnow().isoformat(),
            "category_distribution": self._calculate_category_distribution(validation["validated"]),
            "risk_distribution": self._calculate_risk_distribution(validation["validated"])
        }
    
    def _calculate_category_distribution(self, symbols: List[str]) -> Dict[str, int]:
        """Calculate category distribution for portfolio."""
        dist = {}
        for symbol in symbols:
            crypto = next((c for c in self.top_300 if c["symbol"] == symbol), None)
            if crypto:
                cat = crypto.get("category", "Other")
                dist[cat] = dist.get(cat, 0) + 1
        return dist
    
    def _calculate_risk_distribution(self, symbols: List[str]) -> Dict[str, int]:
        """Calculate risk distribution for portfolio."""
        dist = {}
        for symbol in symbols:
            crypto = next((c for c in self.top_300 if c["symbol"] == symbol), None)
            if crypto:
                risk = crypto.get("risk", "Medium")
                dist[risk] = dist.get(risk, 0) + 1
        return dist
    
    async def rank_user_selection(self,
                                 user_selection: List[str],
                                 ranking_metric: str = "market_cap") -> List[Dict[str, Any]]:
        """
        Rank user's cryptocurrency selection.
        
        Args:
            user_selection: User's selected crypto symbols
            ranking_metric: Metric to rank by (market_cap, volume, price_change)
            
        Returns:
            Ranked selection
        """
        ranked = []
        
        for symbol in user_selection:
            crypto = await self.get_crypto_by_symbol(symbol)
            if crypto:
                metric_value = crypto.get(ranking_metric, 0)
                ranked.append({
                    "symbol": crypto["symbol"],
                    "name": crypto["name"],
                    "rank": crypto.get("rank", 0),
                    ranking_metric: metric_value
                })
        
        # Sort by metric
        reverse = ranking_metric in ["market_cap", "volume"]
        ranked.sort(key=lambda x: x.get(ranking_metric, 0), reverse=reverse)
        
        # Add position rank
        for i, item in enumerate(ranked, 1):
            item["position"] = i
        
        return ranked
    
    async def _refresh_top_300(self) -> None:
        """Refresh top 300 from API."""
        try:
            if self.crypto_client:
                top_cryptos = await self.crypto_client.get_top_cryptocurrencies(limit=300)
                if top_cryptos:
                    self.top_300 = top_cryptos
                    self.logger.info(f"Refreshed top 300: {len(top_cryptos)} items")
        except Exception as e:
            self.logger.error(f"Error refreshing top 300: {str(e)}")

# Factory function for dependency injection
def get_custom_crypto_selection_service(crypto_client=None,
                                         logger=None) -> CustomCryptoSelectionService:
    """Factory function to create CustomCryptoSelectionService instance."""
    return CustomCryptoSelectionService(
        service_name="CustomCryptoSelectionService",
        crypto_client=crypto_client,
        logger=logger
    )