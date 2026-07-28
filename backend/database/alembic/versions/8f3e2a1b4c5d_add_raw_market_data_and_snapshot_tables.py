"""Add Raw Market Data and Snapshot tables for Crypto/Intl integration

Adds tables for storing raw market data from external APIs (CoinGecko, Binance)
and processed snapshots for ML analysis.

Revision ID: 8f3e2a1b4c5d
Revises: c57c8b5674de
Create Date: 2026-07-27 11:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8f3e2a1b4c5d'
down_revision: Union[str, None] = 'c57c8b5674de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'raw_market_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('raw_symbol', sa.String(length=50), nullable=False),
        sa.Column('market', sa.String(length=20), nullable=False),
        sa.Column('exchange', sa.String(length=50), nullable=True),
        sa.Column('data_type', sa.String(length=30), nullable=False),
        sa.Column('raw_payload', postgresql.JSONB(), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('volume', sa.Numeric(precision=25, scale=2), nullable=True),
        sa.Column('quote_volume', sa.Numeric(precision=25, scale=2), nullable=True),
        sa.Column('source_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('ingestion_id', sa.String(length=100), nullable=True),
        sa.Column('data_quality', sa.String(length=10), server_default='RAW'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.UniqueConstraint('raw_symbol', 'market', 'exchange', 'data_type', 'source_timestamp', name='uix_raw_market'),
    )
    op.create_index('idx_raw_asset', 'raw_market_data', ['asset_id'])
    op.create_index('idx_raw_market_type', 'raw_market_data', ['market', 'data_type'])
    op.create_index('idx_raw_ingested', 'raw_market_data', ['ingested_at'])

    op.create_table(
        'market_data_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('interval', sa.String(length=10), nullable=False),
        sa.Column('open', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('high', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('low', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('close', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('volume', sa.Numeric(precision=25, scale=2), nullable=True),
        sa.Column('turnover', sa.Numeric(precision=25, scale=2), nullable=True),
        sa.Column('rsi', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('macd', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('macd_signal', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('macd_histogram', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('bb_upper', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('bb_middle', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('bb_lower', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('atr', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('ma_7', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('ma_14', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('ma_30', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('volatility', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('volume_ma_7', sa.Numeric(precision=25, scale=2), nullable=True),
        sa.Column('volume_ratio', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('features', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('source', sa.String(length=20), server_default='BRS'),
        sa.Column('is_fresh', sa.Boolean(), server_default='true'),
        sa.Column('freshness_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.UniqueConstraint('asset_id', 'snapshot_time', 'interval', name='uix_snapshot'),
    )
    op.create_index('idx_snapshot_fresh', 'market_data_snapshots', ['asset_id', 'is_fresh', 'snapshot_time'])
    op.create_index('idx_snapshot_interval', 'market_data_snapshots', ['asset_id', 'interval', 'snapshot_time'])

    op.create_table(
        'crypto_ml_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('signal_type', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('expected_return', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('expected_volatility', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('risk_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('features_used', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('technical_indicators', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.ForeignKeyConstraint(['snapshot_id'], ['market_data_snapshots.id']),
    )
    op.create_index('idx_crypto_signal_active', 'crypto_ml_signals', ['asset_id', 'is_active', 'valid_until'])
    op.create_index('idx_crypto_signal_model', 'crypto_ml_signals', ['model_version'])


def downgrade() -> None:
    op.drop_table('crypto_ml_signals')
    op.drop_table('market_data_snapshots')
    op.drop_table('raw_market_data')