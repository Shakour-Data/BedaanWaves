"""Drop Iranian (TSE) market tables — scoped to NASDAQ + Crypto only

Drops all tables exclusive to the Tehran Stock Exchange / BRS API data:
  - ir_price_candles
  - ir_order_book
  - ir_major_shareholders
  - ir_free_float
  - ir_retail_institutional

Renames general-purpose tables (which store NASDAQ data) from IR-prefixed names:
  - ir_financial_statements → financial_statements
  - ir_fundamental_ratios → fundamental_ratios

Revision ID: 20260826_drop_ir_market_tables
Revises: 20260828_add_score_history
Create Date: 2026-08-28 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260826_drop_ir_market_tables'
down_revision: Union[str, None] = '20260828_add_score_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


IR_TABLES = [
    'ir_price_candles',
    'ir_order_book',
    'ir_major_shareholders',
    'ir_free_float',
    'ir_retail_institutional',
]

IR_RENAME_MAP = {
    'ir_financial_statements': 'financial_statements',
    'ir_fundamental_ratios': 'fundamental_ratios',
}


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Drop IR-exclusive tables and rename general-purpose tables."""
    for table_name in IR_TABLES:
        if _table_exists(table_name):
            op.drop_table(table_name)

    for old_name, new_name in IR_RENAME_MAP.items():
        if _table_exists(old_name):
            op.rename_table(old_name, new_name)


def downgrade() -> None:
    """Recreate the Iranian market tables (empty — data was synthetic/simulated)."""
    # ir_price_candles — base CANDLE schema
    op.create_table(
        'ir_price_candles',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', sa.UUID(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('open', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('high', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('low', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('close', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=False),
        sa.Column('turnover', sa.Numeric(precision=25, scale=2), nullable=True),
        sa.Column('transactions', sa.Integer(), nullable=True),
        sa.Column('adjusted_close', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('split_ratio', sa.Numeric(precision=10, scale=4), server_default=sa.text('1.0')),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('data_quality', sa.String(length=10), server_default=sa.text("'CONFIRMED'")),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.UniqueConstraint('asset_id', 'timestamp', 'timeframe',
                            name='uix_ir_price_candles_asset_ts_tf'),
    )
    op.create_index('idx_ir_price_candles_asset_id', 'ir_price_candles', ['asset_id'], unique=False)
    op.create_index('idx_ir_price_candles_timestamp', 'ir_price_candles', ['timestamp'], unique=False)

    # ir_order_book
    op.create_table(
        'ir_order_book',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', sa.UUID(), nullable=False),
        sa.Column('snapshot_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('bid_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('bid_volume', sa.BigInteger(), nullable=True),
        sa.Column('ask_price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('ask_volume', sa.BigInteger(), nullable=True),
        sa.Column('source', sa.String(length=20), server_default=sa.text("'BRS'")),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.UniqueConstraint('asset_id', 'snapshot_time', 'rank',
                            name='uix_ir_order_book_snap_rank'),
    )

    # ir_major_shareholders
    op.create_table(
        'ir_major_shareholders',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', sa.UUID(), nullable=False),
        sa.Column('shareholder_name', sa.String(length=255), nullable=False),
        sa.Column('shareholder_type', sa.String(length=10), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('share_count', sa.BigInteger(), nullable=True),
        sa.Column('share_pct', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('change_count', sa.BigInteger(), server_default=sa.text('0')),
        sa.Column('change_pct', sa.Numeric(precision=8, scale=4), server_default=sa.text('0')),
        sa.Column('report_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=20), server_default=sa.text("'BRS'")),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.UniqueConstraint('asset_id', 'shareholder_name', 'report_date',
                            name='uix_ir_major_shareholders_asset_name_date'),
    )

    # ir_free_float
    op.create_table(
        'ir_free_float',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', sa.UUID(), nullable=False),
        sa.Column('free_float_pct', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('base_volume', sa.BigInteger(), nullable=True),
        sa.Column('as_of_date', sa.Date(), nullable=False),
        sa.Column('source', sa.String(length=20), server_default=sa.text("'BRS'")),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.UniqueConstraint('asset_id', 'as_of_date', name='uix_ir_free_float_asset_date'),
    )

    # ir_retail_institutional
    op.create_table(
        'ir_retail_institutional',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', sa.UUID(), nullable=False),
        sa.Column('snapshot_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('retail_buy_volume', sa.BigInteger(), server_default=sa.text('0')),
        sa.Column('retail_sell_volume', sa.BigInteger(), server_default=sa.text('0')),
        sa.Column('institutional_buy_volume', sa.BigInteger(), server_default=sa.text('0')),
        sa.Column('institutional_sell_volume', sa.BigInteger(), server_default=sa.text('0')),
        sa.Column('net_flow', sa.Numeric(precision=25, scale=2), server_default=sa.text('0')),
        sa.Column('source', sa.String(length=20), server_default=sa.text("'BRS'")),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.UniqueConstraint('asset_id', 'snapshot_time', name='uix_ir_retail_inst_asset_snap'),
    )
