"""add_tse_support

Add Tehran Stock Exchange (TSE) market support:
- Modify CHECK constraints on assets table to allow TSE market and INDEX asset class
- Create tse_price_candles table for TSE market data
- Create tse_order_book table for TSE market depth

Revision ID: 20260908_add_tse_support
Revises: 20260902_purge_non_nasdaq
Create Date: 2026-09-08 18:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260908_add_tse_support"
down_revision: Union[str, None] = "20260902_purge_non_nasdaq"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    constraints = inspector.get_check_constraints(table_name)
    return any(c["name"] == constraint_name for c in constraints)


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Drop old CHECK constraints if they exist
    if _table_exists("assets"):
        if _constraint_exists("assets", "chk_assets_market"):
            op.drop_constraint("chk_assets_market", "assets", type_="check")
        if _constraint_exists("assets", "chk_assets_asset_class"):
            op.drop_constraint("chk_assets_asset_class", "assets", type_="check")

        # 2) Recreate with expanded allow-list
        op.create_check_constraint(
            "chk_assets_market",
            "assets",
            "market IN ('NASDAQ', 'TSE')",
        )
        op.create_check_constraint(
            "chk_assets_asset_class",
            "assets",
            "asset_class IN ('EQUITY', 'ETF', 'INDEX')",
        )

    # 3) Create TSE price candles table
    if not _table_exists("tse_price_candles"):
        op.create_table(
            "tse_price_candles",
            sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("asset_id", sa.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("timeframe", sa.String(10), nullable=False),
            sa.Column("open", sa.Numeric(20, 8), nullable=False),
            sa.Column("high", sa.Numeric(20, 8), nullable=False),
            sa.Column("low", sa.Numeric(20, 8), nullable=False),
            sa.Column("close", sa.Numeric(20, 8), nullable=False),
            sa.Column("volume", sa.BigInteger(), nullable=False),
            sa.Column("turnover", sa.Numeric(25, 2)),
            sa.Column("transactions", sa.Integer()),
            sa.Column("adjusted_close", sa.Numeric(20, 8)),
            sa.Column("split_ratio", sa.Numeric(10, 4), server_default=sa.text("1.0")),
            sa.Column("source", sa.String(20), nullable=False),
            sa.Column("data_quality", sa.String(10), server_default=sa.text("'CONFIRMED'::text")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.UniqueConstraint("asset_id", "timestamp", "timeframe", name="uix_tse_price_candles_asset_ts_tf"),
            sa.Index("idx_tse_price_candles_asset_ts", "asset_id", "timestamp"),
            sa.Index("idx_tse_price_candles_tf_ts", "timeframe", "timestamp"),
            sa.CheckConstraint("high >= open AND high >= close AND high >= low", name="chk_tse_price_candles_high"),
            sa.CheckConstraint("low <= open AND low <= close AND low <= high", name="chk_tse_price_candles_low"),
            sa.CheckConstraint("volume >= 0", name="chk_tse_price_candles_volume_non_negative"),
            sa.CheckConstraint("open >= 0 AND close >= 0", name="chk_tse_price_candles_price_non_negative"),
        )

    # 4) Create TSE order book table
    if not _table_exists("tse_order_book"):
        op.create_table(
            "tse_order_book",
            sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("asset_id", sa.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
            sa.Column("snapshot_time", sa.DateTime(), nullable=False),
            sa.Column("rank", sa.Integer(), nullable=False),
            sa.Column("bid_price", sa.Numeric(20, 8)),
            sa.Column("bid_volume", sa.BigInteger()),
            sa.Column("ask_price", sa.Numeric(20, 8)),
            sa.Column("ask_volume", sa.BigInteger()),
            sa.Column("source", sa.String(20), server_default=sa.text("'BRS'::text")),
            sa.UniqueConstraint("asset_id", "snapshot_time", "rank", name="uix_tse_order_book_snap_rank"),
            sa.Index("idx_tse_order_book_asset_snap", "asset_id", "snapshot_time"),
        )

    print("[add_tse_support] TSE market support added")


def downgrade() -> None:
    bind = op.get_bind()

    # Drop TSE tables
    if _table_exists("tse_order_book"):
        op.drop_table("tse_order_book")
    if _table_exists("tse_price_candles"):
        op.drop_table("tse_price_candles")

    # Restore original CHECK constraints
    if _table_exists("assets"):
        if _constraint_exists("assets", "chk_assets_market"):
            op.drop_constraint("chk_assets_market", "assets", type_="check")
        if _constraint_exists("assets", "chk_assets_asset_class"):
            op.drop_constraint("chk_assets_asset_class", "assets", type_="check")

        op.create_check_constraint(
            "chk_assets_market",
            "assets",
            "market = 'NASDAQ'",
        )
        op.create_check_constraint(
            "chk_assets_asset_class",
            "assets",
            "asset_class IN ('EQUITY', 'ETF')",
        )

    print("[add_tse_support] TSE support removed")
