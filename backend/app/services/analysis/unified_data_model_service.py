from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum
import numpy as np

from ..core import AnalysisService
from ..core.dependency_container import get_global_container


class MetricType(str, Enum):
    FLOW = "flow"
    STOCK = "stock"
    NOMINAL = "nominal"
    REAL = "real"
    RATIO = "ratio"
    ABSOLUTE = "absolute"
    RELATIVE = "relative"


class SemanticTag:
    """Semantic tags for unified data model."""

    def __init__(
        self,
        metric_type: MetricType,
        base_unit: str,
        asset_class: str,
        temporal_alignment: str = "quarterly",
    ):
        self.metric_type = metric_type
        self.base_unit = base_unit
        self.asset_class = asset_class
        self.temporal_alignment = temporal_alignment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.metric_type.value,
            "unit": self.base_unit,
            "asset_class": self.asset_class,
            "temporal_alignment": self.temporal_alignment,
        }


class UnifiedDataModelService(AnalysisService):
    """Enhanced unified data model with semantic tags and metric algebra."""

    def __init__(self, service_name: str = "UnifiedDataModelService"):
        super().__init__(service_name)
        self.semantic_tags: Dict[str, SemanticTag] = {}
        self.metric_algebra: Dict[str, str] = {}

    async def initialize(self) -> None:
        """Initialize semantic tags and metric algebra rules."""
        self._initialize_semantic_tags()
        self._initialize_metric_algebra()
        self.logger.info("UnifiedDataModelService initialized")

    def _initialize_semantic_tags(self) -> None:
        """Add semantic annotations to common metrics."""
        self.semantic_tags = {
            "market_cap": SemanticTag(
                metric_type=MetricType.STOCK,
                base_unit="USD",
                asset_class="cross_asset",
            ),
            "revenue": SemanticTag(
                metric_type=MetricType.FLOW,
                base_unit="USD",
                asset_class="stock",
            ),
            "transaction_volume": SemanticTag(
                metric_type=MetricType.FLOW,
                base_unit="USD",
                asset_class="stock",
            ),
            "circulating_supply": SemanticTag(
                metric_type=MetricType.STOCK,
                base_unit="units",
                asset_class="stock",
            ),
            "shares_outstanding": SemanticTag(
                metric_type=MetricType.STOCK,
                base_unit="shares",
                asset_class="stock",
            ),
            "price": SemanticTag(
                metric_type=MetricType.ABSOLUTE,
                base_unit="USD",
                asset_class="cross_asset",
            ),
            "pe_ratio": SemanticTag(
                metric_type=MetricType.RATIO,
                base_unit="dimensionless",
                asset_class="stock",
            ),
            "velocity": SemanticTag(
                metric_type=MetricType.FLOW,
                base_unit="transactions_per_unit",
                asset_class="stock",
            ),
            "dividend_yield": SemanticTag(
                metric_type=MetricType.RATIO,
                base_unit="percent",
                asset_class="stock",
            ),
        }

    def _initialize_metric_algebra(self) -> None:
        """Define metric algebra rules for cross-asset calculations."""
        self.metric_algebra = {
            "pe_equivalent": "market_cap / (revenue * price_per_transaction)",
            "book_value_equivalent": "market_cap / book_value",
            "flow_to_stock_ratio": "transaction_volume / market_cap",
            "velocity_equivalent": "revenue / market_cap",
        }

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform unified data model analysis."""
        return {
            "semantic_tags": {k: v.to_dict() for k, v in self.semantic_tags.items()},
            "metric_algebra": self.metric_algebra,
            "temporal_alignment": await self._check_temporal_alignment(data),
        }

    async def _check_temporal_alignment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if quarterly stock metrics are temporally aligned."""
        stock_quarter = data.get("stock_quarter", "Q1")
        previous_quarter = data.get("previous_quarter", stock_quarter)
        aligned = stock_quarter == previous_quarter

        return {
            "stock_quarter": stock_quarter,
            "previous_quarter": previous_quarter,
            "aligned": aligned,
            "gap_days": 0 if aligned else 90,
        }

    def get_semantic_tag(self, metric_name: str) -> Optional[SemanticTag]:
        """Get semantic tag for a metric."""
        return self.semantic_tags.get(metric_name)

    def add_semantic_tag(self, metric_name: str, tag: SemanticTag) -> None:
        """Add a new semantic tag."""
        self.semantic_tags[metric_name] = tag

    def validate_metric_algebra(self, expression: str) -> bool:
        """Validate a metric algebra expression."""
        return expression in self.metric_algebra.values()


get_global_container().register("UnifiedDataModelService", UnifiedDataModelService, singleton=True)