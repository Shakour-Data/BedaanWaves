"""Add news classification columns and news_sources table.

Revision ID: 20260907_add_news_classification
Revises: 20260906_add_snapshot_tier
Create Date: 2026-09-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260907_add_news_classification"
down_revision = "20260906_add_snapshot_tier"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # 1. Add new columns to news table
    op.add_column(
        "news",
        sa.Column("category", sa.String(50), nullable=False, server_default="ECONOMIC"),
    )
    op.add_column(
        "news",
        sa.Column("sub_category", sa.String(100), nullable=True),
    )
    op.add_column(
        "news",
        sa.Column("region", sa.String(50), nullable=True),
    )
    op.add_column(
        "news",
        sa.Column("priority", sa.String(10), nullable=False, server_default="NORMAL"),
    )
    op.add_column(
        "news",
        sa.Column("is_market_moving", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # 2. Make url non-nullable and unique after ensuring data exists
    # First, backfill any null URLs with a placeholder
    op.execute(
        """
        UPDATE news
        SET url = COALESCE(url, 'https://bedaanwaves.local/news/' || id::text)
        WHERE url IS NULL
        """
    )
    op.alter_column("news", "url", nullable=False)

    # 3. Create composite indexes for filtering performance
    op.create_index(
        "idx_news_category_priority",
        "news",
        ["category", "priority"],
        unique=False,
    )
    op.create_index(
        "idx_news_region_category",
        "news",
        ["region", "category"],
        unique=False,
    )

    # 4. Create news_sources table
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


def downgrade():
    # Drop indexes first
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
