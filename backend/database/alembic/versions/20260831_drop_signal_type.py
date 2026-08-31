"""drop signal_type columns from ml_signals and crypto_ml_signals

Revision ID: 20260831_drop_signal_type
Revises: 20260828_add_score_history
Create Date: 2026-08-31 21:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260831_drop_signal_type'
down_revision: Union[str, None] = '20260828_add_score_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('idx_crypto_signal_model', table_name='crypto_ml_signals')
    op.drop_column('crypto_ml_signals', 'signal_type')
    op.drop_index('ix_crypto_ml_signals_signal_type', table_name='crypto_ml_signals')
    op.drop_column('ml_signals', 'signal_type')


def downgrade() -> None:
    op.add_column(
        'ml_signals',
        sa.Column('signal_type', sa.String(length=20), nullable=False, server_default='HOLD'),
    )
    op.add_column(
        'crypto_ml_signals',
        sa.Column('signal_type', sa.String(length=20), nullable=False, server_default='HOLD'),
    )
    op.create_index('ix_crypto_ml_signals_signal_type', 'crypto_ml_signals', ['signal_type'])
    op.create_index('idx_crypto_signal_model', 'crypto_ml_signals', ['model_version'])