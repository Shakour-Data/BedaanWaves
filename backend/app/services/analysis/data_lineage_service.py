from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
from app.core.utils import utc_now_iso

from ..core import AnalysisService
from ..core.dependency_container import get_global_container
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class DataLineageService(AnalysisService):
    """Comprehensive data lineage tracking for macroeconomic indicators."""

    def __init__(self, service_name: str = "DataLineageService"):
        super().__init__(service_name)
        self.lineage_graph: Dict[str, Dict[str, Any]] = {}  # Tracks all data transformations
        self.transformation_log: List[Dict[str, Any]] = []  # Log of all transformations
        self.indicator_sources: Dict[str, Dict[str, Any]] = {}  # Source definitions

    async def initialize(self) -> None:
        """Initialize with predefined data sources."""
        self.indicator_sources = {
            "cpi": {
                "name": "Consumer Price Index",
                "source_type": "government_api",
                "update_frequency": "monthly",
                "description": "Measure of average change in prices over time",
                "last_updated": utc_now_iso()
            },
            "gdp": {
                "name": "Gross Domestic Product",
                "source_type": "government_api",
                "update_frequency": "quarterly",
                "description": "Total value of goods and services produced",
                "last_updated": utc_now_iso()
            },
            "unemployment": {
                "name": "Unemployment Rate",
                "source_type": "government_api",
                "update_frequency": "monthly",
                "description": "Percentage of labor force without work",
                "last_updated": utc_now_iso()
            }
        }
        
        self.logger.info("DataLineageService initialized with core economic indicators")

    async def shutdown(self) -> None:
        """Cleanup resources."""
        self.logger.info("DataLineageService shutdown")

    async def track_origin(self, indicator: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track the origin of an indicator.
        
        Args:
            indicator: Name of the indicator (e.g., 'cpi', 'gdp')
            source_data: Raw data from source system
            
        Returns:
            Origin tracking record with hash and metadata
        """
        if indicator not in self.indicator_sources:
            self.indicator_sources[indicator] = {
                "name": indicator.upper(),
                "source_type": "unknown",
                "description": f"Indicator {indicator}",
                "last_updated": utc_now_iso()
            }
        
        # Create content hash for data integrity
        content_str = json.dumps(source_data, sort_keys=True, default=str)
        data_hash = hashlib.sha256(content_str.encode()).hexdigest()
        
        origin_record = {
            "indicator": indicator,
            "source_info": self.indicator_sources[indicator].copy(),
            "data_hash": data_hash,
            "timestamp": utc_now_iso(),
            "record_id": hashlib.md5(f"{indicator}{datetime.now()}".encode()).hexdigest()[:8]
        }
        
        # Store in lineage graph
        self.lineage_graph[origin_record["record_id"]] = {
            "type": "origin",
            "data": origin_record,
            "connections": []  # Will be populated when transformed
        }
        
        self.logger.info(f"Tracked origin for {indicator} (record: {origin_record['record_id']})")
        
        return origin_record

    async def track_transformation(
        self, 
        input_ids: List[str], 
        transformation: str, 
        parameters: Dict[str, Any],
        output_data: Any
    ) -> Dict[str, Any]:
        """
        Track a data transformation step.
        
        Args:
            input_ids: List of record IDs that were inputs to this transformation
            transformation: Description of the transformation applied
            parameters: Parameters used in the transformation
            output_data: Result of the transformation
            
        Returns:
            Transformation record with output ID
        """
        # Create hash for output data
        if isinstance(output_data, (dict, list)):
            content_str = json.dumps(output_data, sort_keys=True, default=str)
        else:
            content_str = str(output_data)
        
        output_hash = hashlib.sha256(content_str.encode()).hexdigest()
        output_id = hashlib.md5(f"{transformation}{datetime.now()}".encode()).hexdigest()[:8]
        
        # Create transformation record
        transformation_record = {
            "transformation_id": output_id,
            "input_ids": input_ids,
            "transformation": transformation,
            "parameters": parameters,
            "output_hash": output_hash,
            "timestamp": utc_now_iso(),
            "record_id": output_id
        }
        
        # Log transformation
        self.transformation_log.append(transformation_record)
        
        # Update lineage graph
        self.lineage_graph[output_id] = {
            "type": "transformation",
            "data": transformation_record,
            "connections": input_ids
        }
        
        # Update input nodes to point to this output
        for input_id in input_ids:
            if input_id in self.lineage_graph:
                if "outputs" not in self.lineage_graph[input_id]:
                    self.lineage_graph[input_id]["outputs"] = []
                self.lineage_graph[input_id]["outputs"].append(output_id)
        
        self.logger.info(f"Tracked transformation {transformation} (output: {output_id})")
        
        return transformation_record

    async def get_lineage(self, indicator: str, depth: int = 3) -> Dict[str, Any]:
        """
        Get full lineage for an indicator.
        
        Args:
            indicator: Name of the indicator to trace
            depth: How many generations back to trace (0 = just origin)
            
        Returns:
            Lineage tree showing data flow from source to current state
        """
        # Find all records for this indicator
        indicator_records = [
            (record_id, record_data) 
            for record_id, record_data in self.lineage_graph.items() 
            if isinstance(record_data.get("data", {}), dict) 
            and record_data["data"].get("indicator") == indicator
        ]
        
        if not indicator_records:
            return {"error": f"No lineage found for indicator: {indicator}"}
        
        # Build lineage tree from the most recent record
        latest_record_id, latest_record_data = max(
            indicator_records, 
            key=lambda x: x[1]["data"].get("timestamp", "")
        )
        
        lineage_tree = self._build_lineage_tree(latest_record_id, depth)
        
        return {
            "indicator": indicator,
            "root_source": latest_record_data["data"].get("source_info", {}),
            "lineage_tree": lineage_tree,
            "generated_at": utc_now_iso()
        }

    def _build_lineage_tree(self, record_id: str, depth: int, visited: Optional[set] = None) -> Dict[str, Any]:
        """Recursively build lineage tree."""
        if visited is None:
            visited = set()
        
        if depth < 0 or record_id in visited:
            return {"node": record_id, "truncated": True}
        
        visited.add(record_id)
        
        if record_id not in self.lineage_graph:
            return {"error": f"Record {record_id} not found"}
        
        node_data = self.lineage_graph[record_id]
        
        tree = {
            "node": record_id,
            "type": node_data["type"],
            "data": node_data["data"],
            "connections": []
        }
        
        # Add input connections
        if node_data["type"] == "transformation":
            input_ids = node_data["data"].get("input_ids", [])
            for input_id in input_ids:
                tree["connections"].append({
                    "direction": "input",
                    "node": self._build_lineage_tree(input_id, depth - 1, visited.copy())
                })
        
        # Add output connections
        if "outputs" in node_data:
            for output_id in node_data["outputs"]:
                if output_id not in visited:  # Prevent cycles
                    tree["connections"].append({
                        "direction": "output",
                        "node": self._build_lineage_tree(output_id, depth - 1, visited.copy())
                    })
        
        return tree

    async def get_transformation_log(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get transformation log for audit trail."""
        start = max(0, len(self.transformation_log) - offset - limit)
        end = len(self.transformation_log) - offset
        return list(reversed(self.transformation_log[start:end]))

    async def verify_data_integrity(self, indicator: str, expected_hash: str) -> Dict[str, Any]:
        """Verify that data hasn't been altered since origin."""
        # Find origin record for this indicator
        origin_records = [
            record for record_id, record in self.lineage_graph.items() 
            if record["type"] == "origin" 
            and record["data"].get("indicator") == indicator
        ]
        
        if not origin_records:
            return {"valid": False, "error": "No origin record found"}
        
        # Use most recent origin
        latest_origin = max(origin_records, key=lambda x: x["data"]["timestamp"])
        actual_hash = latest_origin["data"]["data_hash"]
        
        return {
            "valid": actual_hash == expected_hash,
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
            "record_id": list(self.lineage_graph.keys())[
                list(self.lineage_graph.values()).index(latest_origin)
            ],
            "timestamp": latest_origin["data"]["timestamp"]
        }

    async def get_impact_analysis(self, change_point: str) -> Dict[str, Any]:
        """Analyze impact of a change at a specific point in the lineage."""
        if change_point not in self.lineage_graph:
            return {"error": f"Change point {change_point} not found in lineage"}
        
        # Find all downstream dependencies
        downstream = self._find_downstream(change_point)
        
        return {
            "change_point": change_point,
            "affected_indicators": list(set([
                node["data"].get("indicator") 
                for node_id, node in self.lineage_graph.items() 
                if node_id in downstream 
                and node["type"] == "origin"
                and node["data"].get("indicator")
            ])),
            "total_affected_nodes": len(downstream),
            "change_point_info": self.lineage_graph[change_point]["data"]
        }

    def _find_downstream(self, start_id: str) -> Set[str]:
        """Find all nodes that depend on the given node."""
        visited = set()
        to_visit = [start_id]
        
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)
            
            # Find all nodes that have current as input
            for node_id, node_data in self.lineage_graph.items():
                if node_data["type"] == "transformation":
                    input_ids = node_data["data"].get("input_ids", [])
                    if current in input_ids and node_id not in visited:
                        to_visit.append(node_id)
        
        return visited


get_global_container().register("DataLineageService", DataLineageService, singleton=True)