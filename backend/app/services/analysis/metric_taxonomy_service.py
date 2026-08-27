from typing import Dict, Any, Optional, List
import json
from pathlib import Path
from datetime import datetime
from ..core import BaseService
from ..core.dependency_container import get_global_container


class MetricTaxonomyService(BaseService):
    """Unified metric taxonomy for cross-asset comparison."""

    def __init__(self, service_name: str = "MetricTaxonomyService"):
        super().__init__(service_name)
        self.taxonomy: Dict[str, Any] = {}
        self.mappings: Dict[str, Dict[str, str]] = {
            "crypto_to_stock": {},
            "stock_to_crypto": {}
        }

    async def initialize(self) -> None:
        """Load taxonomy mappings from configuration."""
        self.taxonomy = {
            "FLOW": {
                "description": "Flow variables measured per time period",
                "examples": ["revenue", "dividends", "transaction_volume"]
            },
            "STOCK": {
                "description": "Stock variables measured at a point in time",
                "examples": ["market_cap", "total_supply", "total_assets"]
            },
            "NOMINAL": {
                "description": "Current monetary value without inflation adjustment",
                "examples": ["market_cap", "price", "gdp"]
            },
            "REAL": {
                "description": "Inflation-adjusted value",
                "examples": ["real_gdp", "real_wage", "real_gdp_per_capita"]
            },
            "RATIO": {
                "description": "Dimensionless ratio or percentage",
                "examples": ["pe_ratio", "debt_to_equity", "velocity"]
            }
        }

        # Load mapping files
        await self._load_mappings()
        self.logger.info("MetricTaxonomyService initialized")

    async def _load_mappings(self) -> None:
        """Load predefined mappings between crypto and stock metrics."""
        mapping_path = Path(__file__).parent.parent.parent / "docs" / "analysis" / "metric_taxonomy.json"
        try:
            if mapping_path.exists():
                async with aiofiles.open(mapping_path, 'r') as f:
                    data = json.loads(await f.read())
                    self.mappings = data.get("mappings", self.mappings)
            else:
                # Initialize with default mappings
                await self._initialize_default_mappings()
        except Exception as e:
            self.logger.warning(f"Could not load taxonomy mappings: {e}")
            await self._initialize_default_mappings()

    async def _initialize_default_mappings(self) -> None:
        """Set up default mappings between crypto and stock metrics."""
        self.mappings = {
            "crypto_to_stock": {
                "market_cap": "market_cap",
                "volume_24h": "trading_volume",
                "circulating_supply": "shares_outstanding",
                "price": "price",
                "velocity": "velocity",
                "hash_rate": "hash_rate",
                "nvt_ratio": "pe_ratio",  # Network Value to Transactions = Price/Earnings proxy
                "mvrv_ratio": "pb_ratio",  # Market Value to Realized Value = Price/Book proxy
            },
            "stock_to_crypto": {
                "market_cap": "market_cap",
                "trading_volume": "volume_24h",
                "shares_outstanding": "circulating_supply",
                "price": "price",
                "pe_ratio": "nvt_ratio",
                "pb_ratio": "mvrv_ratio",
                "dividend_yield": "token_velocity",
            }
        }
        self.logger.info("Initialized default metric mappings")

    def map_crypto_to_stock_metric(self, crypto_metric: str) -> Optional[str]:
        """Map a crypto metric to its stock equivalent."""
        return self.mappings["crypto_to_stock"].get(crypto_metric)

    def map_stock_to_crypto_metric(self, stock_metric: str) -> Optional[str]:
        """Map a stock metric to its crypto equivalent."""
        return self.mappings["stock_to_crypto"].get(stock_metric)

    def get_metric_type(self, metric_name: str) -> Optional[str]:
        """Get the semantic type of a metric."""
        for metric_type, info in self.taxonomy.items():
            if metric_name.lower() in [ex.lower() for ex in info["examples"]]:
                return metric_type
        return None

    def validate_mapping(self, crypto_metric: str, stock_metric: str) -> bool:
        """Validate that a crypto-stock metric mapping is semantically consistent."""
        crypto_type = self.get_metric_type(crypto_metric)
        stock_type = self.get_metric_type(stock_metric)
        return crypto_type == stock_type

    async def normalize_cross_asset(
        self,
        crypto_data: Dict[str, float],
        stock_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """Normalize crypto and stock data for cross-asset comparison."""
        normalized = {
            "crypto": {},
            "stock": {},
            "comparisons": {}
        }

        for metric, value in crypto_data.items():
            mapped = self.map_crypto_to_stock_metric(metric)
            if mapped:
                normalized["crypto"][metric] = value
                normalized["comparisons"][f"{metric}_to_{mapped}"] = value

        for metric, value in stock_data.items():
            mapped = self.map_stock_to_crypto_metric(metric)
            if mapped:
                normalized["stock"][metric] = value
                normalized["comparisons"][f"{metric}_to_{mapped}"] = value

        return normalized


get_global_container().register("MetricTaxonomyService", MetricTaxonomyService, singleton=True)