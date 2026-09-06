"""merge heads

Revision ID: 20260816_merge_heads
Revises: c57c8b5674de
Create Date: 2026-08-16 08:03:30.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260816_merge_heads'
down_revision: Union[str, None] = 'c57c8b5674de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge the two head revisions."""
    pass


def downgrade() -> None:
    """Downgrade from the merged state."""
    pass