"""Add snapshot_tier and effective_at to scoring_snapshots.

Revision ID: 20260906_add_snapshot_tier
Revises: 20260905_add_hierarchy_scores_to_score_history
Create Date: 2026-09-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import enum


# revision identifiers, used by Alembic.
revision = "20260906_add_snapshot_tier"
down_revision = "20260905_add_hierarchy_scores_to_score_history"
branch_labels = None
depends_on = None


SnapshotTier = sa.Enum("daily", "hourly", name="snapshot_tier")


def upgrade():
    # 1. Create the enum type first (idempotent: do nothing if exists)
    SnapshotTier.create(op.get_bind(), checkfirst=True)

    # 2. Add nullable columns with default
    op.add_column(
        "scoring_snapshots",
        sa.Column(
            "snapshot_tier",
            SnapshotTier,
            nullable=True,
            server_default="daily",
        ),
    )
    op.add_column(
        "scoring_snapshots",
        sa.Column(
            "effective_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )

    # 3. Create an index on effective_at before backfill to speed it up
    op.create_index(
        "ix_scoring_snapshots_effective_at",
        "scoring_snapshots",
        ["effective_at"],
        unique=False,
    )

    # 4. Backfill existing rows: effective_at = date at 00:00 UTC (date + 00:00 UTC)
    op.execute(
        """
        UPDATE scoring_snapshots
        SET
            snapshot_tier = 'daily'::snapshot_tier,
            effective_at = (date::timestamp AT TIME ZONE 'UTC')
        WHERE snapshot_tier IS NULL OR effective_at IS NULL
        """
    )

    # 5. Add unique composite index (asset_id, snapshot_tier, effective_at
    op.create_index(
        "uq_snapshot_asset_tier_effective",
        "scoring_snapshots",
        ["asset_id", "snapshot_tier", "effective_at"],
        unique=True,
    )


def downgrade():
    # Reverse order of upgrade
    op.drop_index(
        "uq_snapshot_asset_tier_effective", table_name="scoring_snapshots")
    op.drop_index(
        "ix_scoring_snapshots_effective_at", table_name="scoring_snapshots")

    op.drop_column("scoring_snapshots", "effective_at")
    op.drop_column("scoring_snapshots", "snapshot_tier")

    # Drop enum type (with checkfirst true to avoid errors if still referenced
    SnapshotTier.drop(op.get_bind(), checkfirst=True)
