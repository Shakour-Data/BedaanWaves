"""
Schema Registry Service - Data contract validation at ingestion.

Provides schema validation for all incoming data using JSON Schema draft-07.
Integrates with ingestion pipelines to reject non-conforming data early.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, ValidationError
from jsonschema.exceptions import best_match

from app.core.config import get_settings
from app.services.core.base_service import BaseService

logger = logging.getLogger(__name__)


class SchemaRegistryService(BaseService):
    """
    Manages JSON schemas for data contracts and validates payloads.

    Features:
    - Schema versioning and evolution (backward/forward compatibility)
    - Pre-registered schemas for all data types
    - Fast validation with detailed error reporting
    - Schema registry API for external consumers
    """

    def __init__(self, service_name: str = "SchemaRegistryService"):
        super().__init__(service_name)
        self._settings = get_settings()
        self._schemas: dict[str, dict[str, Any]] = {}
        self._validators: dict[str, Draft7Validator] = {}
        self._schema_dir = Path(__file__).parent.parent / "schemas"

    async def initialize(self) -> None:
        await self._load_schemas()
        self.logger.info(f"SchemaRegistryService initialized with {len(self._schemas)} schemas")

    async def shutdown(self) -> None:
        self._schemas.clear()
        self._validators.clear()
        self.logger.info("SchemaRegistryService shutdown")

    async def _load_schemas(self) -> None:
        """Load all schemas from the schemas directory."""
        if not self._schema_dir.exists():
            self._schema_dir.mkdir(parents=True, exist_ok=True)
            await self._create_default_schemas()

        for schema_file in self._schema_dir.glob("*.json"):
            try:
                with open(schema_file, "r") as f:
                    schema = json.load(f)
                schema_id = schema.get("$id") or schema_file.stem
                self._schemas[schema_id] = schema
                self._validators[schema_id] = Draft7Validator(schema)
                self.logger.debug(f"Loaded schema: {schema_id}")
            except Exception as exc:
                self.logger.error(f"Failed to load schema {schema_file}: {exc}")

    async def _create_default_schemas(self) -> None:
        """Create default schemas for core data types."""
        schemas = {
            "quote": {
                "$id": "quote",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Real-time Quote",
                "type": "object",
                "required": ["symbol", "current_price", "timestamp"],
                "properties": {
                    "symbol": {"type": "string", "pattern": "^[A-Z]{1,5}$"},
                    "current_price": {"type": "number", "minimum": 0},
                    "change_value": {"type": "number"},
                    "change_percent": {"type": "number"},
                    "open": {"type": "number", "minimum": 0},
                    "high": {"type": "number", "minimum": 0},
                    "low": {"type": "number", "minimum": 0},
                    "previous_close": {"type": "number", "minimum": 0},
                    "volume": {"type": "integer", "minimum": 0},
                    "adjusted_close": {"type": ["number", "null"], "minimum": 0},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "market_status": {"type": "string", "enum": ["OPEN", "CLOSED", "PRE_MARKET", "AFTER_HOURS"]},
                    "data_source": {"type": "string"},
                },
                "additionalProperties": False,
            },
            "historical_candle": {
                "$id": "historical_candle",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Historical OHLCV Candle",
                "type": "object",
                "required": ["timestamp", "open", "high", "low", "close", "adjusted_close", "volume"],
                "properties": {
                    "timestamp": {"type": "string", "format": "date-time"},
                    "open": {"type": "number", "minimum": 0},
                    "high": {"type": "number", "minimum": 0},
                    "low": {"type": "number", "minimum": 0},
                    "close": {"type": "number", "minimum": 0},
                    "adjusted_close": {"type": "number", "minimum": 0},
                    "volume": {"type": "integer", "minimum": 0},
                    "split_ratio": {"type": ["number", "null"], "minimum": 0},
                    "source": {"type": "string"},
                },
                "additionalProperties": False,
            },
            "financial_statement": {
                "$id": "financial_statement",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Financial Statement",
                "type": "object",
                "required": ["asset_id", "period", "statement_type", "data"],
                "properties": {
                    "asset_id": {"type": "string", "format": "uuid"},
                    "market": {"type": "string", "enum": ["NASDAQ"]},
                    "period": {"type": "string", "pattern": "^\\d{4}Q[1-4]$"},
                    "statement_type": {"type": "string", "enum": ["INCOME", "BALANCE_SHEET", "CASH_FLOW"]},
                    "fiscal_year": {"type": "integer", "minimum": 1900, "maximum": 2100},
                    "data": {"type": "object"},
                    "as_of": {"type": ["string", "null"], "format": "date"},
                },
                "additionalProperties": False,
            },
            "fundamental_ratio": {
                "$id": "fundamental_ratio",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Fundamental Ratios",
                "type": "object",
                "required": ["asset_id", "period"],
                "properties": {
                    "asset_id": {"type": "string", "format": "uuid"},
                    "market": {"type": "string", "enum": ["NASDAQ"]},
                    "period": {"type": "string", "pattern": "^\\d{4}Q[1-4]$"},
                    "eps": {"type": ["number", "null"]},
                    "pe": {"type": ["number", "null"], "minimum": 0},
                    "pb": {"type": ["number", "null"], "minimum": 0},
                    "dps": {"type": ["number", "null"]},
                    "roe": {"type": ["number", "null"]},
                    "profit_margin": {"type": ["number", "null"]},
                    "market_cap": {"type": ["number", "null"], "minimum": 0},
                    "book_value": {"type": ["number", "null"]},
                    "as_of": {"type": ["string", "null"], "format": "date"},
                },
                "additionalProperties": False,
            },
            "news_item": {
                "$id": "news_item",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "News Item",
                "type": "object",
                "required": ["source", "title", "url", "published_at"],
                "properties": {
                    "source": {"type": "string"},
                    "title": {"type": "string", "maxLength": 512},
                    "body": {"type": ["string", "null"]},
                    "url": {"type": "string", "format": "uri", "maxLength": 1024},
                    "category": {"type": "string"},
                    "sub_category": {"type": ["string", "null"]},
                    "region": {"type": ["string", "null"]},
                    "priority": {"type": "string", "enum": ["LOW", "NORMAL", "HIGH", "CRITICAL"]},
                    "language": {"type": "string", "pattern": "^[a-z]{2}$"},
                    "asset_id": {"type": ["string", "null"], "format": "uuid"},
                    "published_at": {"type": "string", "format": "date-time"},
                    "is_market_moving": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
            "market_snapshot": {
                "$id": "market_snapshot",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Market Data Snapshot",
                "type": "object",
                "required": ["asset_id", "snapshot_time", "interval", "close", "volume"],
                "properties": {
                    "asset_id": {"type": "string", "format": "uuid"},
                    "snapshot_time": {"type": "string", "format": "date-time"},
                    "interval": {"type": "string", "enum": ["1m", "5m", "15m", "1h", "4h", "1d"]},
                    "open": {"type": ["number", "null"], "minimum": 0},
                    "high": {"type": ["number", "null"], "minimum": 0},
                    "low": {"type": ["number", "null"], "minimum": 0},
                    "close": {"type": "number", "minimum": 0},
                    "volume": {"type": "number", "minimum": 0},
                    "turnover": {"type": ["number", "null"], "minimum": 0},
                    "rsi": {"type": ["number", "null"]},
                    "macd": {"type": ["number", "null"]},
                    "bb_upper": {"type": ["number", "null"]},
                    "bb_middle": {"type": ["number", "null"]},
                    "bb_lower": {"type": ["number", "null"]},
                    "atr": {"type": ["number", "null"]},
                    "features": {"type": "object"},
                    "source": {"type": "string"},
                    "is_fresh": {"type": "boolean"},
                    "freshness_score": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
                },
                "additionalProperties": False,
            },
            "scoring_input": {
                "$id": "scoring_input",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Scoring Service Input",
                "type": "object",
                "required": ["ticker", "market"],
                "properties": {
                    "ticker": {"type": "string", "pattern": "^[A-Z]{1,5}$"},
                    "market": {"type": "string", "enum": ["NASDAQ"]},
                    "fundamental": {"type": "object"},
                    "technical": {"type": "object"},
                    "sentiment": {"type": "object"},
                    "risk": {"type": "object"},
                    "macro": {"type": "object"},
                    "ai": {"type": "object"},
                },
                "additionalProperties": False,
            },
        }

        for schema_id, schema in schemas.items():
            file_path = self._schema_dir / f"{schema_id}.json"
            with open(file_path, "w") as f:
                json.dump(schema, f, indent=2)
            self._schemas[schema_id] = schema
            self._validators[schema_id] = Draft7Validator(schema)
            self.logger.info(f"Created default schema: {schema_id}")

    def validate(self, schema_id: str, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate data against a registered schema.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        validator = self._validators.get(schema_id)
        if not validator:
            return False, [f"Schema not found: {schema_id}"]

        errors = []
        for error in validator.iter_errors(data):
            # Use best_match to get the most relevant error
            path = " -> ".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"{path}: {error.message}")

        return len(errors) == 0, errors

    def validate_or_raise(self, schema_id: str, data: dict[str, Any]) -> None:
        """Validate and raise ValidationError if invalid."""
        is_valid, errors = self.validate(schema_id, data)
        if not is_valid:
            raise ValidationError(f"Schema validation failed for {schema_id}: {'; '.join(errors)}")

    def get_schema(self, schema_id: str) -> dict[str, Any] | None:
        """Get a schema by ID."""
        return self._schemas.get(schema_id)

    def list_schemas(self) -> list[dict[str, Any]]:
        """List all registered schemas with metadata."""
        return [
            {
                "id": schema_id,
                "title": schema.get("title", ""),
                "version": schema.get("version", "1.0.0"),
            }
            for schema_id, schema in self._schemas.items()
        ]

    async def register_schema(self, schema: dict[str, Any], schema_id: str | None = None) -> str:
        """Register a new schema or update existing."""
        schema_id = schema_id or schema.get("$id")
        if not schema_id:
            raise ValueError("Schema must have an $id field")

        # Validate the schema itself
        Draft7Validator.check_schema(schema)

        # Check compatibility with existing version
        if schema_id in self._schemas:
            if not self._is_compatible(self._schemas[schema_id], schema):
                raise ValueError(f"Schema {schema_id} is not backward compatible")

        self._schemas[schema_id] = schema
        self._validators[schema_id] = Draft7Validator(schema)

        # Persist to file
        file_path = self._schema_dir / f"{schema_id}.json"
        with open(file_path, "w") as f:
            json.dump(schema, f, indent=2)

        self.logger.info(f"Registered schema: {schema_id}")
        return schema_id

    def _is_compatible(self, old_schema: dict[str, Any], new_schema: dict[str, Any]) -> bool:
        """
        Check if new schema is backward compatible with old schema.

        Rules:
        - Required fields cannot be added
        - Field types cannot be changed to narrower types
        - Enum values cannot be removed
        """
        # Simplified compatibility check
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))

        # Cannot add required fields
        if not old_required.issuperset(new_required):
            return False

        # Check properties
        old_props = old_schema.get("properties", {})
        new_props = new_schema.get("properties", {})

        for prop_name, old_prop in old_props.items():
            if prop_name not in new_props:
                # Property removed - check if it was required
                if prop_name in old_required:
                    return False
                continue

            new_prop = new_props[prop_name]
            # Type cannot be narrowed
            if not self._is_type_compatible(old_prop.get("type"), new_prop.get("type")):
                return False

        return True

    def _is_type_compatible(self, old_type: Any, new_type: Any) -> bool:
        """Check if new type is compatible with old type."""
        if old_type == new_type:
            return True
        # Allow nullable extensions
        if isinstance(old_type, str) and isinstance(new_type, list):
            return old_type in new_type or "null" in new_type
        if isinstance(old_type, list) and isinstance(new_type, list):
            return set(old_type).issubset(set(new_type))
        return False


# Global instance
_schema_registry: SchemaRegistryService | None = None


def get_schema_registry() -> SchemaRegistryService:
    """Get the global schema registry instance."""
    global _schema_registry
    if _schema_registry is None:
        _schema_registry = SchemaRegistryService()
    return _schema_registry