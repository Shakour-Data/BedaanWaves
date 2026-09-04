from typing import Any, Dict, List, Optional
import json
import hashlib
from datetime import datetime, timezone
from enum import Enum
from app.core.utils import utc_now_iso

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import BaseService
from ..core.dependency_container import get_global_container
from ..core.database_service import DatabaseService
from ..core.config import get_settings

settings = get_settings()


class ModelStatus(str, Enum):
    TRAINING = "training"
    READY = "ready"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ModelVersion:
    def __init__(
        self,
        name: str,
        version: str,
        training_data_hash: str,
        git_hash: str,
        metrics: Dict[str, float],
        status: ModelStatus = ModelStatus.READY,
    ):
        self.name = name
        self.version = version
        self.training_data_hash = training_data_hash
        self.git_hash = git_hash
        self.metrics = metrics
        self.status = status
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "training_data_hash": self.training_data_hash,
            "git_hash": self.git_hash,
            "metrics": self.metrics,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelVersion":
        obj = cls(
            name=data["name"],
            version=data["version"],
            training_data_hash=data["training_data_hash"],
            git_hash=data["git_hash"],
            metrics=data["metrics"],
            status=ModelStatus(data.get("status", "ready")),
        )
        obj.created_at = datetime.fromisoformat(data["created_at"])
        return obj


class ModelRegistry(BaseService):
    """ML model version registry with drift detection."""

    def __init__(
        self,
        service_name: str = "ModelRegistry",
        database: Optional[DatabaseService] = None,
        drift_threshold: float = 0.1,
    ):
        super().__init__(service_name)
        self.database = database or DatabaseService()
        self.drift_threshold = drift_threshold
        self._models: Dict[str, List[ModelVersion]] = {}

    async def initialize(self) -> None:
        self.logger.info("ModelRegistry initialized")
        # Load existing models from DB
        await self._load_models()

    async def shutdown(self) -> None:
        self.logger.info("ModelRegistry shutdown")

    async def _load_models(self) -> None:
        query = """
            SELECT name, version, training_data_hash, git_hash, metrics, status, created_at
            FROM ml_models
            ORDER BY name, created_at DESC
        """
        async with self.database.session() as session:
            result = await session.execute(query)
            rows = result.fetchall()
            for row in rows:
                mv = ModelVersion.from_dict(
                    {
                        "name": row[0],
                        "version": row[1],
                        "training_data_hash": row[2],
                        "git_hash": row[3],
                        "metrics": json.loads(row[4]),
                        "status": row[5],
                        "created_at": row[6],
                    }
                )
                self._models.setdefault(mv.name, []).append(mv)

    async def register_model(
        self,
        name: str,
        version: str,
        training_data_hash: str,
        git_hash: str,
        metrics: Dict[str, float],
        status: ModelStatus = ModelStatus.READY,
    ) -> ModelVersion:
        """Register a new model version."""
        mv = ModelVersion(
            name=name,
            version=version,
            training_data_hash=training_data_hash,
            git_hash=git_hash,
            metrics=metrics,
            status=status,
        )
        self._models.setdefault(name, []).insert(0, mv)

        # Persist to DB
        query = """
            INSERT INTO ml_models (
                name, version, training_data_hash, git_hash, metrics, status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        async with self.database.session() as session:
            await session.execute(
                query,
                mv.name,
                mv.version,
                mv.training_data_hash,
                mv.git_hash,
                json.dumps(mv.metrics),
                mv.status.value,
                mv.created_at.isoformat(),
            )
            await session.commit()

        self.logger.info("Registered model %s v%s", name, version)
        return mv

    async def get_latest(self, name: str) -> Optional[ModelVersion]:
        """Get the latest READY model version."""
        models = self._models.get(name, [])
        for m in models:
            if m.status == ModelStatus.READY:
                return m
        return None

    async def get_all_versions(self, name: str) -> List[ModelVersion]:
        return self._models.get(name, [])

    async def deprecate(self, name: str, version: str) -> bool:
        """Mark a model version as deprecated."""
        for m in self._models.get(name, []):
            if m.version == version:
                m.status = ModelStatus.DEPRECATED
                await self._persist_status(name, version, ModelStatus.DEPRECATED)
                self.logger.info("Deprecated %s v%s", name, version)
                return True
        return False

    async def _persist_status(
        self, name: str, version: str, status: ModelStatus
    ) -> None:
        query = "UPDATE ml_models SET status = $1 WHERE name = $2 AND version = $3"
        async with self.database.session() as session:
            await session.execute(query, status.value, name, version)
            await session.commit()

    def _psi(self, expected: List[float], actual: List[float]) -> float:
        """Population Stability Index."""
        import numpy as np

        if not expected or not actual:
            return 0.0
        e_hist, _ = np.histogram(expected, bins=10, range=(0, 1))
        a_hist, _ = np.histogram(actual, bins=10, range=(0, 1))
        e_pct = e_hist / len(expected)
        a_pct = a_hist / len(actual)
        eps = 1e-6
        e_pct = np.where(e_pct == 0, eps, e_pct)
        a_pct = np.where(a_pct == 0, eps, a_pct)
        return float(np.sum((e_pct - a_pct) * np.log(e_pct / a_pct)))

    async def check_drift(
        self, model_name: str, live_features: List[float], training_features: List[float]
    ) -> Dict[str, Any]:
        """Check for data drift using PSI."""
        psi = self._psi(training_features, live_features)
        drift_detected = psi > self.drift_threshold
        return {
            "model": model_name,
            "psi": psi,
            "threshold": self.drift_threshold,
            "drift_detected": drift_detected,
            "checked_at": utc_now_iso(),
        }


async def model_registry_factory(database: DatabaseService) -> ModelRegistry:
    registry = ModelRegistry(database=database)
    await registry.initialize()
    get_global_container().register_instance("ModelRegistry", registry)
    return registry


get_global_container().register_factory(
    "ModelRegistry",
    model_registry_factory,
    singleton=True,
)