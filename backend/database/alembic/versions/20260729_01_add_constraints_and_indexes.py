"""Add constraints and indexes for data integrity and performance

Revision ID: 20260729_01
Revises: c57c8b5674de
Create Date: 2026-07-29 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260729_01'
down_revision: Union[str, None] = 'c57c8b5674de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    constraints = inspector.get_check_constraints(table_name)
    return any(c['name'] == constraint_name for c in constraints)


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    indexes = inspector.get_indexes(table_name)
    return any(i['name'] == index_name for i in indexes)


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    columns = {col['name'] for col in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade() -> None:
    """Add constraints and indexes for data integrity and performance."""

    # === Candle tables ===
    candle_tables = {
        'ir_price_candles': 'chk_candle',
        'intl_price_candles': 'chk_intl_candle',
        'crypto_price_candles': 'chk_crypto_candle',
        'price_candles': 'chk_legacy_candle',
    }

    for table_name, constraint_prefix in candle_tables.items():
        if not _table_exists(table_name):
            continue

        # Add high >= low constraint
        if not _constraint_exists(table_name, f'{constraint_prefix}_high'):
            op.create_check_constraint(
                f'{constraint_prefix}_high',
                table_name,
                'high >= low'
            )

        # Add volume >= 0 constraint
        if not _constraint_exists(table_name, f'{constraint_prefix}_volume'):
            op.create_check_constraint(
                f'{constraint_prefix}_volume',
                table_name,
                'volume >= 0'
            )

        # Add composite index
        idx_name = f'idx_{table_name}_asset_timeframe_ts'
        if not _index_exists(table_name, idx_name):
            op.create_index(
                idx_name,
                table_name,
                ['asset_id', 'timeframe', 'timestamp'],
                postgresql_using='btree'
            )

    # === JSONB defaults ===
    if _table_exists('assets') and _column_exists('assets', 'metadata'):
        op.alter_column(
            'assets',
            'metadata',
            server_default=sa.text("'{}'::jsonb"),
            existing_type=postgresql.JSONB(),
            existing_nullable=True
        )

    if _table_exists('api_logs') and _column_exists('api_logs', 'metadata'):
        op.alter_column(
            'api_logs',
            'metadata',
            server_default=sa.text("'{}'::jsonb"),
            existing_type=postgresql.JSONB(),
            existing_nullable=True
        )

    # === Audit columns ===
    if _table_exists('api_logs') and not _column_exists('api_logs', 'updated_by'):
        op.add_column(
            'api_logs',
            sa.Column('updated_by', sa.String(100), nullable=True)
        )

    # === Triggers ===
    # Create trigger function (idempotent)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Add triggers for assets and portfolios if tables exist
    if _table_exists('assets'):
        op.execute("""
            DROP TRIGGER IF EXISTS trg_assets_updated_at ON assets;
            CREATE TRIGGER trg_assets_updated_at
            BEFORE UPDATE ON assets
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)

    if _table_exists('portfolios'):
        op.execute("""
            DROP TRIGGER IF EXISTS trg_portfolio_updated_at ON portfolios;
            CREATE TRIGGER trg_portfolio_updated_at
            BEFORE UPDATE ON portfolios
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Downgrade migration."""

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trg_assets_updated_at ON assets;")
    op.execute("DROP TRIGGER IF EXISTS trg_portfolio_updated_at ON portfolios;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    # Drop audit column
    if _table_exists('api_logs') and _column_exists('api_logs', 'updated_by'):
        op.drop_column('api_logs', 'updated_by')

    # Drop indexes and constraints for candle tables
    candle_tables = {
        'ir_price_candles': 'chk_candle',
        'intl_price_candles': 'chk_intl_candle',
        'crypto_price_candles': 'chk_crypto_candle',
        'price_candles': 'chk_legacy_candle',
    }

    for table_name, constraint_prefix in candle_tables.items():
        if not _table_exists(table_name):
            continue

        idx_name = f'idx_{table_name}_asset_timeframe_ts'
        if _index_exists(table_name, idx_name):
            op.drop_index(idx_name, table_name=table_name)

        for suffix in ['_high', '_volume']:
            constraint_name = f'{constraint_prefix}{suffix}'
            if _constraint_exists(table_name, constraint_name):
                op.drop_constraint(constraint_name, table_name, type_='check')