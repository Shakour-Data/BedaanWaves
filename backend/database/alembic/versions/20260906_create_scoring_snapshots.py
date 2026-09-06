"""create_scoring_snapshots

Create the scoring_snapshots table for the advanced hierarchical filter
engine. Each row represents one score at one hierarchical level for one
asset on one date, enabling efficient SQL-based filtering across the
5-level scoring hierarchy.

Revision ID: 20260906_create_scoring_snapshots
Revises: 20260905_add_hierarchy_scores_to_score_history
Create Date: 2026-09-06 08:42:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260906_create_scoring_snapshots'
down_revision: Union[str, None] = '20260905_add_hierarchy_scores_to_score_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'scoring_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('level', sa.Enum('overall', 'dimension', 'sub_dimension', 'aspect', 'sub_aspect', name='snapshot_level'), nullable=False),
        sa.Column('level_key', sa.String(length=100), nullable=False),
        sa.Column('level_name', sa.String(length=255), nullable=False),
        sa.Column('score', sa.Numeric(8, 4), nullable=False),
        sa.Column('score_change', sa.Numeric(8, 4), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('company_id', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('extra_fields', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], name='fk_scoring_snapshots_asset_id'),
        sa.PrimaryKeyConstraint('id', name='pk_scoring_snapshots')
    )
    op.create_index('idx_scoring_snapshot_asset_id', 'scoring_snapshots', ['asset_id'])
    op.create_index('idx_scoring_snapshot_date', 'scoring_snapshots', ['date'])
    op.create_index('idx_scoring_snapshot_level', 'scoring_snapshots', ['level'])
    op.create_index('idx_scoring_snapshot_level_key', 'scoring_snapshots', ['level', 'level_key'])
    op.create_index('idx_scoring_snapshot_asset_level_date', 'scoring_snapshots', ['asset_id', 'level', 'date'])
    op.create_index('idx_scoring_snapshot_score_change', 'scoring_snapshots', ['score_change'])
    op.create_index('idx_scoring_snapshot_industry', 'scoring_snapshots', ['industry'])
    op.create_index('idx_scoring_snapshot_metadata', 'scoring_snapshots', ['extra_fields'], postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('idx_scoring_snapshot_metadata', table_name='scoring_snapshots')
    op.drop_index('idx_scoring_snapshot_industry', table_name='scoring_snapshots')
    op.drop_index('idx_scoring_snapshot_score_change', table_name='scoring_snapshots')
    op.drop_index('idx_scoring_snapshot_asset_level_date', table_name='scoring_snapshots')
    op.drop_index('idx_scoring_snapshot_level_key', table_name='scoring_snapshots')
    op.drop_index('idx_scoring_snapshot_level', table_name='scoring_snapshots')
    op.drop_index('idx_scoring_snapshot_date', table_name='scoring_snapshots')
    op.drop_index('idx_scoring_snapshot_asset_id', table_name='scoring_snapshots')
    op.drop_table('scoring_snapshots')
    op.execute('DROP TYPE IF EXISTS snapshot_level')
