from typing import Dict, Any, Optional, List
import json
import aiofiles
from pathlib import Path
from datetime import datetime
from ..core import BaseService
from ..core.dependency_container import get_global_container


class MetricTaxonomyService(BaseService):
    """Unified metric taxonomy for cross-asset comparison."""

    def __init__(self, service_name: str = "MetricTaxonomyService"):
        super().__init__(service_name)
        self.taxonomy: Dict[str, Any] = {}
        self.mappings: Dict[str, Dict[str, str]] = {}

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
        """Load predefined mappings between metrics."""
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
        """Set up default mappings between metrics."""
        self.mappings = {
            "market_cap": "market_cap",
            "volume_24h": "trading_volume",
            "circulating_supply": "shares_outstanding",
            "price": "price",
            "velocity": "velocity",
            "nvt_ratio": "pe_ratio",
            "mvrv_ratio": "pb_ratio",
        }
        self.logger.info("Initialized default metric mappings")

    def get_metric_type(self, metric_name: str) -> Optional[str]:
        """Get the semantic type of a metric."""
        for metric_type, info in self.taxonomy.items():
            if metric_name.lower() in [ex.lower() for ex in info["examples"]]:
                return metric_type
        return None

    def validate_mapping(self, source_metric: str, target_metric: str) -> bool:
        """Validate that a metric mapping is semantically consistent."""
        source_type = self.get_metric_type(source_metric)
        target_type = self.get_metric_type(target_metric)
        return source_type == target_type

    async def normalize_cross_asset(
        self,
        source_data: Dict[str, float],
        target_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """Normalize data for cross-asset comparison."""
        normalized = {
            "source": {},
            "target": {},
            "comparisons": {}
        }

        for metric, value in source_data.items():
            mapped = self.mappings.get(metric)
            if mapped:
                normalized["source"][metric] = value
                normalized["comparisons"][f"{metric}_to_{mapped}"] = value

        for metric, value in target_data.items():
            mapped = self.mappings.get(metric)
            if mapped:
                normalized["target"][metric] = value
                normalized["comparisons"][f"{metric}_to_{mapped}"] = value

        return normalized


get_global_container().register("MetricTaxonomyService", MetricTaxonomyService, singleton=True)
