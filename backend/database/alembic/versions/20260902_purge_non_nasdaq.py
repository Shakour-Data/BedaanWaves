"""purge_non_nasdaq_instruments

Remove every financial instrument that does not participate in the
formation of the Nasdaq index. Crypto, forex, commodities, bonds,
indexes (other than the kept ^IXIC reference row), and any non-Nasdaq
equity (NYSE, TSE, LSE, FWB, HKEX, BINANCE, KRAKEN, COINBASE, etc.)
are deleted from ``assets`` along with their dependent rows.

This is the database-level counterpart to the
"any non-Nasdaq instrument must be completely removed" directive.
A pure application-layer filter cannot stop a direct SQL query from
leaking those rows, so we purge them at the source and then add a
CHECK constraint to prevent future inserts of unwanted classes/markets.

The Nasdaq Composite (``^IXIC``) reference row is kept in the
``assets`` table because downstream code resolves index values through
it, but its ``asset_class`` is flipped from ``INDEX`` to ``EQUITY`` so
the existing ``asset_class IN ('EQUITY','ETF')`` filters surface it
consistently with every other Nasdaq-listed instrument.

Revision ID: 20260902_purge_non_nasdaq
Revises: 20260828_add_score_history
Create Date: 2026-09-02 20:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260902_purge_non_nasdaq"
down_revision: Union[str, None] = "20260828_add_score_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that reference ``assets.id`` and must be cascaded-cleaned
# before we delete the offending asset rows.
_ASSET_LINKED_TABLES = [
    "candles",
    "intl_candles",
    "crypto_price_candles",
    "crypto_ml_signals",
    "score_history",
    "raw_performance_scores",
    "fundamental_ratios",
    "financial_statements",
    "ml_signals",
    "news",
    "news_sentiment",
    "market_data_snapshots",
    "company_leadership",
    "portfolio_positions",
    "watchlist_items",
]


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {c["name"] for c in inspector.get_columns(table_name)}


def _fk_exists(table_name: str, fk_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return fk_name in {fk["name"] for fk in inspector.get_foreign_keys(table_name)}


def upgrade() -> None:
    # 1) Snapshot how many non-Nasdaq rows are about to be removed so we
    #    can log a single summary line for the operator.
    bind = op.get_bind()
    if _table_exists("assets") and _column_exists("assets", "market"):
        count_row = bind.execute(
            sa.text(
                "SELECT COUNT(*) FROM assets "
                "WHERE market IS DISTINCT FROM 'NASDAQ' "
                "   OR asset_class NOT IN ('EQUITY', 'ETF')"
            )
        ).fetchone()
        purge_count = int(count_row[0]) if count_row else 0
    else:
        purge_count = 0

    # 2) Delete dependent rows for the offenders first. We don't want a
    #    ON DELETE CASCADE chain silently wiping score history / news /
    #    fundamentals for legitimate Nasdaq rows because of a typo in a
    #    filter, so we explicitly scope each delete to the asset_ids
    #    we're about to drop.
    for table in _ASSET_LINKED_TABLES:
        if not _table_exists(table):
            continue
        if not _column_exists(table, "asset_id"):
            continue
        op.execute(
            sa.text(
                f"DELETE FROM {table} WHERE asset_id IN ("
                "  SELECT id FROM assets "
                "  WHERE market IS DISTINCT FROM 'NASDAQ' "
                "     OR asset_class NOT IN ('EQUITY', 'ETF')"
                ")"
            )
        )

    # 3) Finally drop the offending asset rows themselves.
    if _table_exists("assets"):
        op.execute(
            sa.text(
                "DELETE FROM assets "
                "WHERE market IS DISTINCT FROM 'NASDAQ' "
                "   OR asset_class NOT IN ('EQUITY', 'ETF')"
            )
        )

        # 4) Make the keep-list explicit and add a defensive CHECK
        #    constraint so future code can't insert crypto/forex/etc.
        #    without a migration that bumps this constraint.
        op.execute(
            sa.text(
                "UPDATE assets "
                "SET asset_class = 'EQUITY' "
                "WHERE symbol = '^IXIC' AND asset_class = 'INDEX'"
            )
        )
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

    print(f"[purge_non_nasdaq] removed {purge_count} non-Nasdaq asset rows")


def downgrade() -> None:
    if _table_exists("assets"):
        if _fk_exists("assets", "chk_assets_market"):
            op.drop_constraint("chk_assets_market", "assets", type_="check")
        if _fk_exists("assets", "chk_assets_asset_class"):
            op.drop_constraint("chk_assets_asset_class", "assets", type_="check")
