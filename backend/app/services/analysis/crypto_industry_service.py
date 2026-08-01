from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from ..core import AnalysisService
from ..core.dependency_container import get_global_container


class CryptoIndustryMapperService(AnalysisService):
    """Crypto industry classification using 5-tier hierarchy.

    Classification hierarchy: Layer -> Function -> Usage -> Risk Profile -> Theme
    """

    TIERS = ["layer", "function", "usage", "risk_profile", "theme"]

    LAYER_MAP = {
        "btc": "settlement",
        "eth": "smart_contract_platform",
        "bnb": "smart_contract_platform",
        "ada": "smart_contract_platform",
        "sol": "smart_contract_platform",
        "matic": "scaling_solution",
        "avax": "smart_contract_platform",
        "dot": "interoperability",
        "xrp": "smart_contract_platform",
        "xmr": "privacy",
        "zec": "privacy",
    }

    FUNCTION_MAP = {
        "btc": "digital_gold",
        "eth": "smart_contract",
        "bnb": "smart_contract",
        "ada": "smart_contract",
        "sol": "defi",
        "matic": "scaling",
        "avax": "smart_contract",
        "dot": "interoperability",
        "xrp": "payments",
        "xmr": "privacy",
        "zec": "privacy",
        "usdc": "stablecoin",
        "usdt": "stablecoin",
    }

    USAGE_MAP = {
        "btc": "store_of_value",
        "eth": "programmable_money",
        "sol": "defi_infrastructure",
        "xrp": "payments",
        "xmr": "privacy",
        "dai": "governance",
        "usdc": "payments",
        "usdt": "payments",
    }

    THEME_MAP = {
        "btc": "monetary",
        "eth": "technology",
        "sol": "technology",
        "xrp": "payments",
        "xmr": "privacy",
        "usdc": "stablecoin",
        "usdt": "stablecoin",
    }

    def __init__(self, service_name: str = "CryptoIndustryMapperService"):
        super().__init__(service_name)

    async def initialize(self) -> None:
        self.logger.info("CryptoIndustryMapperService initialized")

    async def shutdown(self) -> None:
        self.logger.info("CryptoIndustryMapperService shutdown")

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify crypto assets into industry buckets."""
        assets = data.get("assets", [])
        results = {}

        for asset in assets:
            symbol = asset.lower() if isinstance(asset, str) else asset.get("symbol", "").lower()
            results[symbol] = await self.classify_asset(symbol)

        return {"classifications": results}

    async def classify_asset(self, symbol: str) -> Dict[str, str]:
        """Classify a single asset into the 5-tier hierarchy."""
        classification = {
            "layer": self.LAYER_MAP.get(symbol, "other"),
            "function": self.FUNCTION_MAP.get(symbol, "other"),
            "usage": self.USAGE_MAP.get(symbol, "trading"),
            "risk_profile": self._determine_risk_profile(symbol),
            "theme": self.THEME_MAP.get(symbol, "other"),
        }
        return classification

    def _determine_risk_profile(self, symbol: str) -> str:
        """Infer risk profile from known market characteristics."""
        low_risk = {"usdc", "usdt", "dai", "busd"}
        medium_risk = {"xrp", "ltc", "link", "matic"}
        high_risk = {"btc", "eth", "sol", "avax", "dot"}

        if symbol in low_risk:
            return "low"
        elif symbol in medium_risk:
            return "moderate"
        elif symbol in high_risk:
            return "high"
        return "moderate"

    async def get_cross_asset_industries(self) -> Dict[str, Any]:
        """Return cross-asset industry buckets blending crypto + stock sectors."""
        return {
            "digital_assets": ["BTC", "ETH", "LTC", "XMR", "ZEC"],
            "blockchain_infrastructure": ["ETH", "BNB", "ADA", "DOT", "AVAX"],
            "decentralized_finance": ["SOL", "UNI", "AAVE", "COMP", "SUSHI"],
            "digital_payments": ["XRP", "XLM", "USDC", "USDT"],
            "privacy_computing": ["XMR", "ZEC", "DASH"],
            "scaling_solutions": ["MATIC", "IMX", "OP", "ARB"],
            "technology_sector_stocks": ["AAPL", "GOOGL", "MSFT", "META", "NVDA"],
            "financial_services_stocks": ["JPM", "GS", "MS", "BLK", "V"],
            "commodity_mining_stocks": ["GOLD", "NEM", "COP", "XOM", "CVX"],
        }


DependencyContainer.get_global_container().register("CryptoIndustryMapperService", CryptoIndustryMapperService, singleton=True)