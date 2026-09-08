"""Fix score_history missing columns and add performance improvements.

This migration:
1. Adds missing columns to score_history (sub_dimension_scores, aspect_scores, sub_aspect_scores, data_quality)
   NOTE: Columns are added as nullable to avoid full table rewrite on large datasets.
   Backfill these columns via the daily scoring pipeline.
2. Adds GIN indexes for JSONB columns
3. Adds CHECK constraints
4. Adds covering indexes
5. Adds column comments

Revision ID: 20260907_fix_score_history_and_performance
Revises: 20260907_add_macro_section
Create Date: 2026-09-07 22:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260907_fix_score_history_and_performance"
down_revision: Union[str, None] = "20260907_add_macro_section"
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


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if _column_exists(table_name, column.name):
        return
    op.add_column(table_name, column)


def _add_index_if_missing(table_name: str, index_name: str, columns: list[str], unique: bool = False, using: str | None = None) -> None:
    if _index_exists(table_name, index_name):
        return
    op.create_index(
        index_name,
        table_name,
        columns,
        unique=unique,
        postgresql_using=using,
    )


def _add_check_if_missing(table_name: str, constraint_name: str, expression: str) -> None:
    if _constraint_exists(table_name, constraint_name):
        return
    op.create_check_constraint(constraint_name, table_name, expression)


def upgrade() -> None:
    # ============================================================
    # 1. Add missing columns to score_history (nullable, no default to avoid table rewrite)
    # ============================================================
    if _table_exists("score_history"):
        _add_column_if_missing("score_history", sa.Column("sub_dimension_scores", postgresql.JSONB()))
        _add_column_if_missing("score_history", sa.Column("aspect_scores", postgresql.JSONB()))
        _add_column_if_missing("score_history", sa.Column("sub_aspect_scores", postgresql.JSONB()))
        _add_column_if_missing("score_history", sa.Column("data_quality", sa.String(20)))

    # ============================================================
    # 2. GIN indexes for JSONB columns
    # ============================================================
    _gin_indexes = [
        ("score_history", "idx_score_history_dims_gin", ["dimension_scores"]),
        ("score_history", "idx_score_history_sub_dims_gin", ["sub_dimension_scores"]),
        ("raw_performance_scores", "idx_raw_perf_dims_gin", ["dimension_scores"]),
        ("raw_performance_scores", "idx_raw_perf_sub_dims_gin", ["sub_dimension_scores"]),
        ("raw_performance_scores", "idx_raw_perf_aspects_gin", ["aspect_scores"]),
        ("raw_performance_scores", "idx_raw_perf_sub_aspects_gin", ["sub_aspect_scores"]),
        ("ml_signals", "idx_signal_technical_gin", ["technical_factors"]),
        ("ml_signals", "idx_signal_fundamental_gin", ["fundamental_factors"]),
        ("ml_signals", "idx_signal_sentiment_gin", ["sentiment_factors"]),
        ("market_data_snapshots", "idx_snapshot_ml_features_gin", ["features"]),
    ]

    for table, index_name, columns in _gin_indexes:
        _add_index_if_missing(table, index_name, columns, using="gin")

    # ============================================================
    # 3. Additional covering / composite indexes
    # ============================================================
    _covering_indexes = [
        ("scoring_snapshots", "idx_scoring_snapshot_asset_date", ["asset_id", "date"]),
    ]

    for table, index_name, columns in _covering_indexes:
        _add_index_if_missing(table, index_name, columns)

    # ============================================================
    # 4. CHECK constraints
    # ============================================================
    _checks = [
        ("score_history", "chk_score_history_data_quality", "data_quality IN ('RAW', 'CLEANED', 'VALIDATED', 'CONFIRMED')"),
        ("ml_signals", "chk_signal_confidence", "confidence >= 0 AND confidence <= 100"),
        ("ml_signals", "chk_signal_risk_score", "risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)"),
    ]

    for table, constraint_name, expression in _checks:
        _add_check_if_missing(table, constraint_name, expression)

    # ============================================================
    # 5. Column comments (PostgreSQL COMMENT)
    # ============================================================
    comments = [
        ("assets", "symbol", "Ticker symbol, unique per asset"),
        ("assets", "name", "Display name of the asset"),
        ("users", "username", "Unique login username"),
        ("users", "email", "User email address"),
        ("users", "hashed_password", "Bcrypt-hashed password"),
        ("raw_performance_scores", "data_quality", "RAW, VALIDATED, CLEANED, EXCLUDED"),
    ]

    for table, column, comment in comments:
        if _table_exists(table) and _column_exists(table, column):
            op.execute(f"COMMENT ON COLUMN {table}.{column} IS '{comment}'")


def downgrade() -> None:
    # Remove comments
    comments = [
        ("assets", "symbol", "Ticker symbol, unique per asset"),
        ("assets", "name", "Display name of the asset"),
        ("users", "username", "Unique login username"),
        ("users", "email", "User email address"),
        ("users", "hashed_password", "Bcrypt-hashed password"),
        ("raw_performance_scores", "data_quality", "RAW, VALIDATED, CLEANED, EXCLUDED"),
    ]
    for table, column, _ in comments:
        if _table_exists(table) and _column_exists(table, column):
            op.execute(f"COMMENT ON COLUMN {table}.{column} IS NULL")

    # Drop CHECK constraints
    checks = [
        ("score_history", "chk_score_history_data_quality"),
        ("ml_signals", "chk_signal_confidence"),
        ("ml_signals", "chk_signal_risk_score"),
    ]
    for table, constraint_name in checks:
        if _constraint_exists(table, constraint_name):
            op.drop_constraint(constraint_name, table, type_="check")

    # Drop indexes
    indexes = [
        ("score_history", "idx_score_history_dims_gin"),
        ("score_history", "idx_score_history_sub_dims_gin"),
        ("raw_performance_scores", "idx_raw_perf_dims_gin"),
        ("raw_performance_scores", "idx_raw_perf_sub_dims_gin"),
        ("raw_performance_scores", "idx_raw_perf_aspects_gin"),
        ("raw_performance_scores", "idx_raw_perf_sub_aspects_gin"),
        ("ml_signals", "idx_signal_technical_gin"),
        ("ml_signals", "idx_signal_fundamental_gin"),
        ("ml_signals", "idx_signal_sentiment_gin"),
        ("market_data_snapshots", "idx_snapshot_ml_features_gin"),
        ("scoring_snapshots", "idx_scoring_snapshot_asset_date"),
    ]
    for table, index_name in indexes:
        if _index_exists(table, index_name):
            op.drop_index(index_name, table_name=table)

    # Drop added columns
    if _column_exists("score_history", "data_quality"):
        op.drop_column("score_history", "data_quality")
    if _column_exists("score_history", "sub_aspect_scores"):
        op.drop_column("score_history", "sub_aspect_scores")
    if _column_exists("score_history", "aspect_scores"):
        op.drop_column("score_history", "aspect_scores")
    if _column_exists("score_history", "sub_dimension_scores"):
        op.drop_column("score_history", "sub_dimension_scores")
