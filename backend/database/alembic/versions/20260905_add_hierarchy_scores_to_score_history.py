"""add_hierarchy_scores_to_score_history

Add sub_dimension_scores, aspect_scores, and sub_aspect_scores columns
to ScoreHistory so per-stock hierarchical historical data is persisted
alongside the existing dimension_scores.

Revision ID: 20260905_add_hierarchy_scores_to_score_history
Revises: 20260903_add_market_score_trend
Create Date: 2026-09-05 20:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260905_add_hierarchy_scores_to_score_history'
down_revision: Union[str, None] = '20260903_add_market_score_trend'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('score_history', sa.Column('sub_dimension_scores', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column('score_history', sa.Column('aspect_scores', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column('score_history', sa.Column('sub_aspect_scores', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")))


def downgrade() -> None:
    op.drop_column('score_history', 'sub_aspect_scores')
    op.drop_column('score_history', 'aspect_scores')
    op.drop_column('score_history', 'sub_dimension_scores')
