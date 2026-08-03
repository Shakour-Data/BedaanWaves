from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path

from ..core import AnalysisService
from ..core.dependency_container import get_global_container
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class SemanticVersioningService(AnalysisService):
    """Implement semantic versioning for regime classifications and data pipelines."""

    def __init__(self, service_name: str = "SemanticVersioningService"):
        super().__init__(service_name)
        self.version_history: Dict[str, List[Dict]] = {
            "regime_classification": [],  # MAJOR.MINOR.PATCH-regime
            "data_pipeline": []  # MAJOR.MINOR.PATCH-type
        }
        self.current_version: Dict[str, str] = {
            "regime": "1.0.0-base",  # Initial version format
            "pipeline": "1.0.0-full"
        }

    async def initialize(self) -> None:
        """Initialize with historical version records."""
        self.logger.info("SemanticVersioningService initialized with version tracking")

    async def shutdown(self) -> None:
        """Shutdown service."""
        self.logger.info("SemanticVersioningService shutdown")

    async def update_version(self, context: str, new_version: str) -> Dict[str, Any]:
        """Update version with semantic versioning rules."""
        # Validate version format (MAJOR.MINOR.PATCH-regime or MAJOR.MINOR.PATCH-type)
        if not self._is_valid_semantic_version(new_version, context):
            raise ValueError("Invalid semantic version format")
        
        # Increment version
        current = self._parse_version(self.current_version[context])
        new = self._parse_version(new_version)
        
        # Increment major if context changed
        if context != self.current_version.get("last_context"):
            new['major'] += 1
            new['minor'] = 0
            new['patch'] = 0
        else:
            # Increment minor if type changed
            if context == "pipeline" and new['type'] != self._get_pipeline_type(current['minor']):
                new['minor'] += 1
                new['patch'] = 0
            else:
                new['patch'] += 1
        
        # Update history
        self.current_version[context] = self._format_version(new)
        self.version_history[context].append(self._format_version(new))  # Keep last 100 records
        if len(self.version_history[context]) > 100:
            self.version_history[context] = self.version_history[context][-100:]
        
        # Store context
        self.current_version["last_context"] = context
        
        self.logger.info(f"Updated {context} version to {self.current_version[context]}")
        
        return {
            "context": context,
            "old_version": self._format_version(current),
            "new_version": self.current_version[context],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _is_valid_semantic_version(self, version: str, context: str) -> bool:
        """Validate version format based on context."""
        parts = version.split('-')
        if len(parts) < 5:  # MAJOR.MINOR.PATCH-PATH-REGIME
            return False
        
        try:
            major, minor, patch = map(int, parts[:3])
            path = parts[3].split('/') if '/' in parts[3] else [parts[3]]
            regime = parts[-1]
            
            if context == "regime_classification":
                # Regime versions follow: MAJOR.MINOR.PATCH-REGIME-TYPE
                return len(parts) >= 5 and regime in {"base", "expansion", "contraction"}
            else:
                # Pipeline versions follow: MAJOR.MINOR.PATCH-TYPE
                return len(parts) == 4 and all(p.isdigit() for p in parts[:3])
        except (ValueError, IndexError):
            return False

    def _parse_version(self, version: str) -> Dict[str, int]:
        """Parse version into components."""
        parts = version.split('-')[:3]
        return {"major": int(parts[0]), "minor": int(parts[1]), "patch": int(parts[2])}

    def _format_version(self, components: Dict[str, int]) -> str:
        """Format version back to string."""
        return f"{components['major']}.{components['minor']}.{components['patch']}"

    def _get_pipeline_type(self, minor: int) -> str:
        """Determine pipeline type based on minor version."""
        # Pipeline type mapping: minor 0 = full, 1 = incremental, 2 = reduced
        types = {"0": "full", "1": "incremental", "2": "reduced"}
        return types.get(str(minor), "full")

    async def get_version_history(self, context: str, limit: int = 10) -> List[Dict[str, Any]]:    
        """Get historical version records."""
        return list(reversed(self.version_history[context][-min(limit, len(self.version_history[context])):]))

    async def check_version_compatibility(self, required: str, current: str) -> bool:
        """Check if current version meets required version."""
        try:
            req_parts = self._parse_version(required)
            curr_parts = self._parse_version(current)
            
            # Major must be >= required
            if curr_parts['major'] < req_parts['major']:
                return False
            # Minor must be >= required if major equal
            if curr_parts['major'] == req_parts['major'] and curr_parts['minor'] < req_parts['minor']:
                return False
            # Patch must be >= required if major/minor equal
            if curr_parts['major'] == req_parts['major'] and curr_parts['minor'] == req_parts['minor'] and curr_parts['patch'] < req_parts['patch']:
                return False
            
            return True
        except ValueError:
            return False


get_global_container().register("SemanticVersioningService", SemanticVersioningService, singleton=True)