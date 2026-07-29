"""Add constraints and indexes for data integrity and performance

This migration adds:
- Check constraints for candle data integrity (high >= low, volume >= 0)
- Composite indexes for price queries
- JSONB server defaults
- Audit trail columns

Revision ID: 20260729_01
Revises: c57c8b5674de
Create Date: 2026-07-29 14:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260729_01"
down_revision = "c57c8b5674de"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add CheckConstraints for candle tables (there are multiple candle tables per market)
    # We'll add them for the main TSE candle table first
    op.create_check_constraint(
        "chk_candle_high_ge_low",
        "tse_candles",
        "high >= low",
        postgresql_check="high >= low"
    )
    op.create_check_constraint(
        "chk_candle_volume_non_negative",
        "tse_candles",
        "volume >= 0",
        postgresql_check="volume >= 0"
    )
    
    # Add composite indexes for price queries
    op.create_index(
        "idx_tse_candles_asset_timeframe_ts",
        "tse_candles",
        ["asset_id", "timeframe", "timestamp"],
        postgresql_using="btree"
    )
    
    # Ensure JSONB columns have proper defaults
    op.alter_column(
        "assets",
        "metadata",
        server_default=sa.text("'{}'::jsonb"),
        existing_type=postgresql.JSONB(),
        existing_nullable=True
    )
    op.alter_column(
        "notifications",
        "metadata",
        server_default=sa.text("'{}'::jsonb"),
        existing_type=postgresql.JSONB(),
        existing_nullable=True
    )
    op.alter_column(
        "portfolio_positions",
        "tags",
        server_default=sa.text("'[]'::jsonb"),
        existing_type=postgresql.JSONB(),
        existing_nullable=True
    )
    
    # Add audit trail columns to important tables
    op.add_column(
        "api_logs",
        sa.Column("updated_by", sa.String(100), nullable=True)
    )
    
    # Create a trigger function for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Add triggers for updated_at
    op.execute("""
        CREATE TRIGGER trg_assets_updated_at
        BEFORE UPDATE ON assets
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    op.execute("""
        CREATE TRIGGER trg_portfolio_updated_at
        BEFORE UPDATE ON portfolios
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trg_assets_updated_at ON assets;")
    op.execute("DROP TRIGGER IF EXISTS trg_portfolio_updated_at ON portfolios;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop audit column
    op.drop_column("api_logs", "updated_by")
    
    # Drop indexes
    op.drop_index("idx_tse_candles_asset_timeframe_ts", table_name="tse_candles")
    
    # Drop check constraints
    op.drop_constraint("chk_candle_high_ge_low", "tse_candles", type_="check")
    op.drop_constraint("chk_candle_volume_non_negative", "tse_candles", type_="check")