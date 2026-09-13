"""add_nerk_support

Add Neark (نزدک) index constituent support to the assets table.

This migration adds two nullable columns to the ``assets`` table:
- ``is_nerk_constituent``: boolean flag indicating whether the asset
  is a constituent of the Neark index.
- ``nerk_weight``: numeric weight of the asset within the Neark index.

No new market values are added — Neark constituents remain regular
NASDAQ-listed assets (market='NASDAQ', asset_class='EQUITY' or 'ETF').
This keeps the market taxonomy clean while still allowing Neark
index membership to be queried and displayed.

Revision ID: 20260908_add_nerk_support
Revises: 20260908_standardize_grades_and_partition_snapshots
Create Date: 2026-09-08 22:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260908_add_nerk_support"
down_revision: Union[str, None] = "20260908_standardize_grades_and_partition_snapshots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {c["name"] for c in inspector.get_columns(table_name)}


def upgrade() -> None:
    if _column_exists("assets", "is_nerk_constituent"):
        return

    op.add_column(
        "assets",
        sa.Column("is_nerk_constituent", sa.Boolean(), server_default=sa.text("false"), nullable=True),
    )
    op.create_index(
        "idx_asset_nerk_constituent",
        "assets",
        ["is_nerk_constituent"],
    )
    op.add_column(
        "assets",
        sa.Column("nerk_weight", sa.Numeric(10, 4), nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "assets" not in inspector.get_table_names():
        return

    if _column_exists("assets", "is_nerk_constituent"):
        op.drop_index("idx_asset_nerk_constituent", table_name="assets")
        op.drop_column("assets", "is_nerk_constituent")
    if _column_exists("assets", "nerk_weight"):
        op.drop_column("assets", "nerk_weight")