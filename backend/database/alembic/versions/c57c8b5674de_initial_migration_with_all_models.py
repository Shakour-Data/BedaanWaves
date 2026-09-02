"""Initial migration — all models (generated from metadata)

This migration creates all tables directly from model metadata so it always
matches the models.py definitions (including separate candle tables per market,
market depth, shareholders, fundamental, news, ML, and security tables).

Revision ID: c57c8b5674de
Revises:
Create Date: 2026-07-09 20:43:13.219558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable, DropTable

from app.models.models import Base


# revision identifiers, used by Alembic.
revision: str = 'c57c8b5674de'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect = postgresql.dialect()
    for table in Base.metadata.sorted_tables:
        op.execute(CreateTable(table, if_not_exists=True).compile(dialect=dialect))


def downgrade() -> None:
    dialect = postgresql.dialect()
    for table in reversed(Base.metadata.sorted_tables):
        op.execute(DropTable(table, if_exists=True).compile(dialect=dialect))
