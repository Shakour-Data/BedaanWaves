"""add_market_score_trend_table

Precomputed per-day market-wide score aggregates populated by
``MarketScoreTrendService``. The dashboard score-trend endpoint reads from
here instead of aggregating ``score_history`` on every request.

Revision ID: 20260903_add_market_score_trend
Revises: 20260902_purge_non_nasdaq
Create Date: 2026-09-03 11:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '20260903_add_market_score_trend'
down_revision: Union[str, None] = '20260902_purge_non_nasdaq'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'market_score_trend',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('market', sa.String(length=32), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('avg_score', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('avg_dimensions', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('symbol_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('market', 'date', name='uix_market_score_trend_market_date'),
    )
    op.create_index(
        'idx_market_score_trend_market_date',
        'market_score_trend',
        ['market', 'date'],
    )


def downgrade() -> None:
    op.drop_index('idx_market_score_trend_market_date', table_name='market_score_trend')
    op.drop_table('market_score_trend')