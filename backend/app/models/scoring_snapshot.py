"""Filterable scoring snapshot model.

Flattens the 5-level scoring hierarchy into queryable rows so that
advanced filters can be expressed with standard SQL predicates instead
of deep JSONB traversal.

Each row represents one score at one hierarchical level for one asset
on one date.
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, validates

from app.db.base import Base


class SnapshotLevel(enum.StrEnum):
    OVERALL = "overall"
    DIMENSION = "dimension"
    SUB_DIMENSION = "sub_dimension"
    ASPECT = "aspect"
    SUB_ASPECT = "sub_aspect"


class SnapshotTier(enum.StrEnum):
    DAILY = "daily"
    HOURLY = "hourly"


class ScoringSnapshot(Base):
    """One row per (asset, date, level, level_key)."""

    __tablename__ = "scoring_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)

    date = Column(Date, nullable=False, index=True)
    snapshot_tier = Column(
        Enum("daily", "hourly", name="snapshot_tier", native_enum=False),
        nullable=True,
        default="daily"
    )
    effective_at = Column(DateTime(timezone=True), nullable=True, index=True)
    level = Column(Enum(SnapshotLevel, name="snapshot_level"), nullable=False, index=True)
    level_key = Column(String(100), nullable=False, index=True)
    level_name = Column(String(255), nullable=False)

    score = Column(Numeric(8, 4), nullable=False, index=True)
    score_change = Column(Numeric(8, 4), nullable=True)

    industry = Column(String(100), nullable=True, index=True)
    company_id = Column(String(100), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)

    extra_fields = Column("extra_fields", JSONB, nullable=False, default={})

    asset = relationship("Asset")

    __table_args__ = (
        UniqueConstraint('asset_id', 'date', 'level', 'level_key', name='uix_scoring_snapshots_asset_date_level_key'),
        Index("idx_scoring_snapshot_level_key", "level", "level_key"),
        Index("idx_scoring_snapshot_asset_level_date", "asset_id", "level", "date"),
        Index("idx_scoring_snapshot_score_change", "score_change"),
        Index("idx_scoring_snapshot_metadata", "extra_fields", postgresql_using="gin"),
        Index("uq_snapshot_asset_tier_effective", "asset_id", "snapshot_tier", "effective_at", unique=True),
    )

    @validates("level")
    def _validate_level(self, key: str, value: SnapshotLevel) -> SnapshotLevel:
        if isinstance(value, str):
            return SnapshotLevel(value)
        return value

    @validates("snapshot_tier")
    def _validate_snapshot_tier(self, key: str, value: str) -> str:
        return value.lower()
