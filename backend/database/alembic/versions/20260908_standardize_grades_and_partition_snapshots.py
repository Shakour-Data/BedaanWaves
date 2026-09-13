"""Standardize grades in score_history and add partitioning to scoring_snapshots.

This migration:
1. Converts legacy grade values to standardized format
2. Adds CHECK constraint for grade values
3. Converts scoring_snapshots to partitioned table by date

Revision ID: 20260908_standardize_grades_and_partition_snapshots
Revises: 20260907_fix_score_history_and_performance
Create Date: 2026-09-08 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260908_standardize_grades_and_partition_snapshots"
down_revision: Union[str, None] = "20260907_fix_score_history_and_performance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    constraints = inspector.get_check_constraints(table_name)
    return any(c["name"] == constraint_name for c in constraints)


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    indexes = inspector.get_indexes(table_name)
    return any(i["name"] == index_name for i in indexes)


def upgrade() -> None:
    # ============================================================
    # 1. Standardize grades in score_history
    # ============================================================
    if _table_exists("score_history"):
        # Convert legacy grades to standardized format
        op.execute("""
            UPDATE score_history
            SET grade = CASE
                WHEN grade = 'A_STRONG_BUY' THEN 'STRONG_BULLISH'
                WHEN grade = 'B_BUY' THEN 'BULLISH'
                WHEN grade = 'C_HOLD' THEN 'NEUTRAL'
                WHEN grade = 'D_SELL' THEN 'BEARISH'
                WHEN grade = 'E_STRONG_SELL' THEN 'STRONG_BEARISH'
                ELSE grade
            END
        """)

        # Add CHECK constraint for grade values (NOT VALID first, then validate)
        if not _constraint_exists("score_history", "chk_score_history_grade"):
            op.execute("""
                ALTER TABLE score_history
                ADD CONSTRAINT chk_score_history_grade
                CHECK (grade IN ('STRONG_BULLISH', 'BULLISH', 'NEUTRAL', 'BEARISH', 'STRONG_BEARISH'))
                NOT VALID
            """)
            op.execute("ALTER TABLE score_history VALIDATE CONSTRAINT chk_score_history_grade")

    # ============================================================
    # 2. Partition scoring_snapshots by date range
    # ============================================================
    if _table_exists("scoring_snapshots"):
        # Create enum type if not exists
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        enum_exists = 'snapshot_tier' in [e['name'] for e in inspector.get_enums()]
        
        if not enum_exists:
            op.execute("""
                CREATE TYPE snapshot_tier AS ENUM ('daily', 'hourly');
            """)
        
        # Create enum type for snapshot_level if not exists
        level_enum_exists = 'snapshot_level' in [e['name'] for e in inspector.get_enums()]
        if not level_enum_exists:
            op.execute("""
                CREATE TYPE snapshot_level AS ENUM ('overall', 'dimension', 'sub_dimension', 'aspect', 'sub_aspect');
            """)

        # Create a new partitioned table
        op.execute("""
            CREATE TABLE IF NOT EXISTS scoring_snapshots_new (
                id UUID NOT NULL,
                asset_id UUID NOT NULL,
                date DATE NOT NULL,
                snapshot_tier snapshot_tier,
                effective_at TIMESTAMP WITH TIME ZONE,
                level snapshot_level NOT NULL,
                level_key VARCHAR(100) NOT NULL,
                level_name VARCHAR(255) NOT NULL,
                score NUMERIC(8,4) NOT NULL,
                score_change NUMERIC(8,4),
                industry VARCHAR(100),
                company_id VARCHAR(100),
                timestamp TIMESTAMP NOT NULL,
                extra_fields JSONB NOT NULL DEFAULT '{}',
                PRIMARY KEY (id, date)
            ) PARTITION BY RANGE (date);
        """)

        # Create partitions for the last 2 years and future
        op.execute("""
            CREATE TABLE IF NOT EXISTS scoring_snapshots_2025 PARTITION OF scoring_snapshots_new
            FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
        """)

        op.execute("""
            CREATE TABLE IF NOT EXISTS scoring_snapshots_2026 PARTITION OF scoring_snapshots_new
            FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
        """)

        op.execute("""
            CREATE TABLE IF NOT EXISTS scoring_snapshots_2027 PARTITION OF scoring_snapshots_new
            FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');
        """)

        op.execute("""
            CREATE TABLE IF NOT EXISTS scoring_snapshots_default PARTITION OF scoring_snapshots_new
            DEFAULT;
        """)

        # Copy data from old table to new partitioned table
        op.execute("""
            INSERT INTO scoring_snapshots_new
            SELECT * FROM scoring_snapshots;
        """)

        # Drop old table and rename new one
        op.execute("DROP TABLE scoring_snapshots CASCADE;")
        op.execute("ALTER TABLE scoring_snapshots_new RENAME TO scoring_snapshots;")

        # Recreate indexes on the partitioned table
        # Note: unique constraints on partitioned tables must include all partition columns
        op.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uix_scoring_snapshots_asset_date_level_key
            ON scoring_snapshots (asset_id, date, level, level_key);
        """)

        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_scoring_snapshot_level_key
            ON scoring_snapshots (level, level_key);
        """)

        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_scoring_snapshot_asset_level_date
            ON scoring_snapshots (asset_id, level, date);
        """)

        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_scoring_snapshot_asset_date
            ON scoring_snapshots (asset_id, date);
        """)

        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_scoring_snapshot_score_change
            ON scoring_snapshots (score_change);
        """)

        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_scoring_snapshot_metadata
            ON scoring_snapshots USING gin (extra_fields);
        """)

        # The unique constraint on (asset_id, snapshot_tier, effective_at) needs to include date
        # since date is the partition key. We'll make it non-unique and add date as a covering index.
        op.execute("""
            CREATE INDEX IF NOT EXISTS uq_snapshot_asset_tier_effective
            ON scoring_snapshots (asset_id, snapshot_tier, effective_at, date);
        """)


def downgrade() -> None:
    # Remove grade CHECK constraint
    if _constraint_exists("score_history", "chk_score_history_grade"):
        op.drop_constraint("chk_score_history_grade", "score_history", type_="check")

    # Convert grades back to legacy format
    if _table_exists("score_history"):
        op.execute("""
            UPDATE score_history
            SET grade = CASE
                WHEN grade = 'STRONG_BULLISH' THEN 'A_STRONG_BUY'
                WHEN grade = 'BULLISH' THEN 'B_BUY'
                WHEN grade = 'NEUTRAL' THEN 'C_HOLD'
                WHEN grade = 'BEARISH' THEN 'D_SELL'
                WHEN grade = 'STRONG_BEARISH' THEN 'E_STRONG_SELL'
                ELSE grade
            END
        """)

    # Convert partitioned table back to regular table
    if _table_exists("scoring_snapshots"):
        # Check if it's partitioned
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        is_partitioned = any(
            p.get('name') == 'scoring_snapshots' 
            for p in inspector.get_partitions('scoring_snapshots')
        ) if hasattr(inspector, 'get_partitions') else False
        
        if is_partitioned:
            op.execute("""
                CREATE TABLE scoring_snapshots_old AS
                SELECT * FROM scoring_snapshots;
            """)
            op.execute("DROP TABLE scoring_snapshots CASCADE;")
            op.execute("ALTER TABLE scoring_snapshots_old RENAME TO scoring_snapshots;")
            
            # Recreate original unique constraint
            op.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_snapshot_asset_tier_effective
                ON scoring_snapshots (asset_id, snapshot_tier, effective_at);
            """)
