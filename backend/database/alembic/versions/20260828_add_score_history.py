"""add_score_history_table

Add ScoreHistory model for daily score snapshots.

Revision ID: 20260828_add_score_history
Revises: 20260816_merge_heads
Create Date: 2026-08-28 03:50:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260828_add_score_history'
down_revision: Union[str, None] = '20260816_merge_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'score_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('dimension_scores', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('overall_score', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('grade', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.UniqueConstraint('asset_id', 'date', name='uix_score_history_asset_date'),
    )
    op.create_index('idx_score_history_asset_date', 'score_history', ['asset_id', 'date'])
    op.create_index('idx_score_history_date', 'score_history', ['date'])


def downgrade() -> None:
    op.drop_index('idx_score_history_date', table_name='score_history')
    op.drop_index('idx_score_history_asset_date', table_name='score_history')
    op.drop_table('score_history')
