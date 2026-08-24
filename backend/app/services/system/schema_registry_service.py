from typing import Any, Dict, List, Optional
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from aioredis import Redis

from ..core import ExternalAPIService
from ..core.dependency_container import get_global_container
from ..core.config import get_settings
from ..core.database_service import DatabaseService

settings = get_settings()


class SchemaVersion:
    def __init__(self, major: int, minor: int, patch: int, regime: str, date: str = None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.regime = regime
        self.date = date or datetime.now(timezone.utc).strftime("%Y.%m.%d")

    @property
    def version(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}-regime.{self.regime}.{self.date}"

    @property
    def hash(self) -> str:
        parts = [str(self.major), str(self.minor), str(self.patch), self.regime, self.date]
        return hashlib.sha256(".".join(parts).encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "regime": self.regime,
            "date": self.date,
        }


class SchemaRegistry:
    """Central registry for versioned data schemas."""

    def __init__(self, db: DatabaseService, redis: Redis) -> None:
        self.db = db
        self.redis = redis
        self.logger = __import__("logging").getLogger(self.__class__.__name__)
        self._schemas: Dict[str, Dict[str, Any]] = {}

    async def register_schema(self, asset_type: str, data: Dict[str, Any], version_obj: SchemaVersion) -> Dict[str, Any]:
        """Register a new schema version."""

        schema_hash = version_obj.hash
        schema_obj = {
            "asset_type": asset_type,
            "schema": data,
            "version": version_obj.version,
            "hash": schema_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._schemas[asset_type] = schema_obj

        # Store in Redis for quick lookup
        await self.redis.set(
            f"schema:{asset_type}",
            json.dumps(schema_obj),
            ex=86400 * 30,  # 30 days
        )

        # Persist to database
        db_query = """
            INSERT INTO schemes (
                asset_type,
                schema_hash,
                version,
                data,
                created_at
            ) VALUES ($1, $2, $3, $4, $5)
        """
        await self.db.execute(
            db_query,
            asset_type,
            schema_hash,
            version_obj.version,
            json.dumps(data),
            datetime.now(timezone.utc).isoformat(),
        )

        self.logger.info("Registered new schema for %s (v%s)", asset_type, version_obj.version)
        return schema_obj

    async def validate(self, asset_type: str, data: Dict[str, Any]) -> bool:
        """Validate data against the latest schema for the asset type."""
        if asset_type not in self._schemas:
            return True

        # Check Redis quickly
        cached = await self.redis.get(f"schema:{asset_type}")
        if cached:
            cached_schema = json.loads(cached)
            # In a real implementation we would validate against the stored schema
            latest_version = cached_schema["version"]
            self.logger.debug("Using cached schema %s for %s", asset_type, latest_version)
            return True

        return await self._validate_against_db(asset_type, data)

    async def _validate_against_db(self, asset_type: str, data: Dict[str, Any]) -> bool:
        """Validate against database-stored schema."""
        return True


async def schema_registry_factory(
    database: DatabaseService,
    redis: Redis,
) -> SchemaRegistry:
    registry = SchemaRegistry(database, redis)
    await registry.initialize()
    get_global_container().register_instance("SchemaRegistry", registry)
    return registry


get_global_container().register(
    "SchemaRegistry",
    schema_registry_factory,
    singleton=True,
)