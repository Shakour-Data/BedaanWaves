"""Consolidate migrations 20260729_01, 20260906_create_scoring_snapshots,
20260906_add_snapshot_tier, and 20260907_add_news_classification into a single file.

Revision ID: 20260907_consolidate_migrations
Revises: 20260905_add_hierarchy_scores_to_score_history
Create Date: 2026-09-07 00:01:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260907_consolidate_migrations"
down_revision: Union[str, None] = "20260905_add_hierarchy_scores_to_score_history"
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


def _fk_exists(table_name: str, fk_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    return fk_name in {fk["name"] for fk in inspector.get_foreign_keys(table_name)}


# === Part 1: Constraints and indexes (was 20260729_01) ===

_CANDLE_TABLES = {
    "ir_price_candles": "chk_candle",
    "intl_price_candles": "chk_intl_candle",
    "crypto_price_candles": "chk_crypto_candle",
    "price_candles": "chk_legacy_candle",
}


def _add_candle_constraints() -> None:
    for table_name, constraint_prefix in _CANDLE_TABLES.items():
        if not _table_exists(table_name):
            continue
        if not _constraint_exists(table_name, f"{constraint_prefix}_high"):
            op.create_check_constraint(
                f"{constraint_prefix}_high", table_name, "high >= low"
            )
        if not _constraint_exists(table_name, f"{constraint_prefix}_volume"):
            op.create_check_constraint(
                f"{constraint_prefix}_volume", table_name, "volume >= 0"
            )
        idx_name = f"idx_{table_name}_asset_timeframe_ts"
        if not _index_exists(table_name, idx_name):
            op.create_index(
                idx_name,
                table_name,
                ["asset_id", "timeframe", "timestamp"],
                postgresql_using="btree",
            )


def _add_jsonb_defaults() -> None:
    if _table_exists("assets") and _column_exists("assets", "metadata"):
        op.alter_column(
            "assets",
            "metadata",
            server_default=sa.text("'{}'::jsonb"),
            existing_type=postgresql.JSONB(),
            existing_nullable=True,
        )
    if _table_exists("api_logs") and _column_exists("api_logs", "metadata"):
        op.alter_column(
            "api_logs",
            "metadata",
            server_default=sa.text("'{}'::jsonb"),
            existing_type=postgresql.JSONB(),
            existing_nullable=True,
        )


def _add_audit_columns() -> None:
    if _table_exists("api_logs") and not _column_exists("api_logs", "updated_by"):
        op.add_column(
            "api_logs",
            sa.Column("updated_by", sa.String(100), nullable=True),
        )


def _add_triggers() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )
    if _table_exists("assets"):
        op.execute(
            """
            DROP TRIGGER IF EXISTS trg_assets_updated_at ON assets;
            CREATE TRIGGER trg_assets_updated_at
            BEFORE UPDATE ON assets
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
            """
        )
    if _table_exists("portfolios"):
        op.execute(
            """
            DROP TRIGGER IF EXISTS trg_portfolio_updated_at ON portfolios;
            CREATE TRIGGER trg_portfolio_updated_at
            BEFORE UPDATE ON portfolios
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
            """
        )


# === Part 2: Scoring snapshots (was 20260906_create + 20260906_add_snapshot_tier) ===

SnapshotTier = sa.Enum("daily", "hourly", name="snapshot_tier")
SnapshotLevel = sa.Enum(
    "overall", "dimension", "sub_dimension", "aspect", "sub_aspect",
    name="snapshot_level",
)


def _create_scoring_snapshots() -> None:
    SnapshotTier.create(op.get_bind(), checkfirst=True)
    SnapshotLevel.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "scoring_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("level", SnapshotLevel, nullable=False),
        sa.Column("level_key", sa.String(length=100), nullable=False),
        sa.Column("level_name", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Numeric(8, 4), nullable=False),
        sa.Column("score_change", sa.Numeric(8, 4), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("company_id", sa.String(length=100), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("extra_fields", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("snapshot_tier", SnapshotTier, nullable=True, server_default="daily"),
        sa.Column("effective_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], name="fk_scoring_snapshots_asset_id"),
        sa.PrimaryKeyConstraint("id", name="pk_scoring_snapshots"),
    )

    op.create_index("idx_scoring_snapshot_asset_id", "scoring_snapshots", ["asset_id"])
    op.create_index("idx_scoring_snapshot_date", "scoring_snapshots", ["date"])
    op.create_index("idx_scoring_snapshot_level", "scoring_snapshots", ["level"])
    op.create_index("idx_scoring_snapshot_level_key", "scoring_snapshots", ["level", "level_key"])
    op.create_index("idx_scoring_snapshot_asset_level_date", "scoring_snapshots", ["asset_id", "level", "date"])
    op.create_index("idx_scoring_snapshot_score_change", "scoring_snapshots", ["score_change"])
    op.create_index("idx_scoring_snapshot_industry", "scoring_snapshots", ["industry"])
    op.create_index("idx_scoring_snapshot_metadata", "scoring_snapshots", ["extra_fields"], postgresql_using="gin")

    op.create_index("ix_scoring_snapshots_effective_at", "scoring_snapshots", ["effective_at"], unique=False)

    # Backfill existing rows
    op.execute(
        """
        UPDATE scoring_snapshots
        SET
            snapshot_tier = 'daily'::snapshot_tier,
            effective_at = (date::timestamp AT TIME ZONE 'UTC')
        WHERE snapshot_tier IS NULL OR effective_at IS NULL
        """
    )

    op.create_index(
        "uq_snapshot_asset_tier_effective",
        "scoring_snapshots",
        ["asset_id", "snapshot_tier", "effective_at"],
        unique=True,
    )


# === Part 3: News classification (was 20260907_add_news_classification) ===


def _add_news_classification() -> None:
    op.add_column("news", sa.Column("category", sa.String(50), nullable=False, server_default="ECONOMIC"))
    op.add_column("news", sa.Column("sub_category", sa.String(100), nullable=True))
    op.add_column("news", sa.Column("region", sa.String(50), nullable=True))
    op.add_column("news", sa.Column("priority", sa.String(10), nullable=False, server_default="NORMAL"))
    op.add_column("news", sa.Column("is_market_moving", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.execute(
        """
        UPDATE news
        SET url = COALESCE(url, 'https://bedaanwaves.local/news/' || id::text)
        WHERE url IS NULL
        """
    )
    op.alter_column("news", "url", nullable=False)

    op.create_index("idx_news_category_priority", "news", ["category", "priority"], unique=False)
    op.create_index("idx_news_region_category", "news", ["region", "category"], unique=False)

    op.create_table(
        "news_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("region", sa.String(50), nullable=True),
        sa.Column("interval_seconds", sa.Integer(), nullable=False, server_default="900"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("max_concurrent_requests", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("last_success_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_error_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("success_count_24h", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count_24h", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_news_source_name"),
    )
    op.create_index("idx_news_source_enabled", "news_sources", ["enabled"], unique=False)
    op.create_index("idx_news_source_category", "news_sources", ["category"], unique=False)


def upgrade() -> None:
    _add_candle_constraints()
    _add_jsonb_defaults()
    _add_audit_columns()
    _add_triggers()
    _create_scoring_snapshots()
    _add_news_classification()


def downgrade() -> None:
    # === News classification ===
    op.drop_index("idx_news_source_category", table_name="news_sources")
    op.drop_index("idx_news_source_enabled", table_name="news_sources")
    op.drop_table("news_sources")
    op.drop_index("idx_news_region_category", table_name="news")
    op.drop_index("idx_news_category_priority", table_name="news")
    op.drop_column("news", "is_market_moving")
    op.drop_column("news", "priority")
    op.drop_column("news", "region")
    op.drop_column("news", "sub_category")
    op.drop_column("news", "category")

    # === Scoring snapshots ===
    op.drop_index("uq_snapshot_asset_tier_effective", table_name="scoring_snapshots")
    op.drop_index("ix_scoring_snapshots_effective_at", table_name="scoring_snapshots")
    op.drop_index("idx_scoring_snapshot_metadata", table_name="scoring_snapshots")
    op.drop_index("idx_scoring_snapshot_industry", table_name="scoring_snapshots")
    op.drop_index("idx_scoring_snapshot_score_change", table_name="scoring_snapshots")
    op.drop_index("idx_scoring_snapshot_asset_level_date", table_name="scoring_snapshots")
    op.drop_index("idx_scoring_snapshot_level_key", table_name="scoring_snapshots")
    op.drop_index("idx_scoring_snapshot_level", table_name="scoring_snapshots")
    op.drop_index("idx_scoring_snapshot_date", table_name="scoring_snapshots")
    op.drop_index("idx_scoring_snapshot_asset_id", table_name="scoring_snapshots")
    op.drop_table("scoring_snapshots")
    SnapshotTier.drop(op.get_bind(), checkfirst=True)
    SnapshotLevel.drop(op.get_bind(), checkfirst=True)

    # === Constraints and indexes ===
    op.execute("DROP TRIGGER IF EXISTS trg_assets_updated_at ON assets;")
    op.execute("DROP TRIGGER IF EXISTS trg_portfolio_updated_at ON portfolios;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    if _table_exists("api_logs") and _column_exists("api_logs", "updated_by"):
        op.drop_column("api_logs", "updated_by")

    for table_name, constraint_prefix in _CANDLE_TABLES.items():
        if not _table_exists(table_name):
            continue
        idx_name = f"idx_{table_name}_asset_timeframe_ts"
        if _index_exists(table_name, idx_name):
            op.drop_index(idx_name, table_name=table_name)
        for suffix in ["_high", "_volume"]:
            constraint_name = f"{constraint_prefix}{suffix}"
            if _constraint_exists(table_name, constraint_name):
                op.drop_constraint(constraint_name, table_name, type_="check")
