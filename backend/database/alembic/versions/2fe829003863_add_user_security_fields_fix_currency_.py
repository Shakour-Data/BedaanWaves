"""add_user_security_fields_fix_currency_defaults_add_indexes_ohlc_constraints

Revision ID: 2fe829003863
Revises: 20260908_standardize_grades_and_partition_snapshots
Create Date: 2026-09-08 13:22:26.240987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2fe829003863'
down_revision: Union[str, None] = '20260908_standardize_grades_and_partition_snapshots'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    indexes = inspector.get_indexes(table_name)
    return any(i["name"] == index_name for i in indexes)


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _table_exists(table_name):
        return False
    constraints = inspector.get_check_constraints(table_name)
    return any(c["name"] == constraint_name for c in constraints)


def upgrade() -> None:
    # ============================================================
    # 1. Add security fields to users table
    # ============================================================
    if _table_exists("users"):
        # Add email_verified
        if not _column_exists("users", "email_verified"):
            op.add_column("users", sa.Column("email_verified", sa.Boolean(), default=False, server_default=sa.false()))
            op.execute("UPDATE users SET email_verified = FALSE WHERE email_verified IS NULL")
            op.alter_column("users", "email_verified", nullable=False)

        # Add failed_login_attempts
        if not _column_exists("users", "failed_login_attempts"):
            op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), default=0, server_default="0"))
            op.execute("UPDATE users SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL")
            op.alter_column("users", "failed_login_attempts", nullable=False)

        # Add locked_until
        if not _column_exists("users", "locked_until"):
            op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))

        # Add indexes for new columns
        if not _index_exists("users", "idx_users_email_verified"):
            op.create_index("idx_users_email_verified", "users", ["email_verified"])

        if not _index_exists("users", "idx_users_locked_until"):
            op.create_index("idx_users_locked_until", "users", ["locked_until"])

        # Add comments
        op.execute("COMMENT ON COLUMN users.email_verified IS 'Whether user email has been verified'")
        op.execute("COMMENT ON COLUMN users.failed_login_attempts IS 'Consecutive failed login attempts for lockout'")
        op.execute("COMMENT ON COLUMN users.locked_until IS 'Account locked until this timestamp'")

    # ============================================================
    # 2. Remove plaintext auth_token from data_sources
    # ============================================================
    if _table_exists("data_sources"):
        # Add auth_token_encrypted column if not exists
        if not _column_exists("data_sources", "auth_token_encrypted"):
            op.add_column("data_sources", sa.Column("auth_token_encrypted", sa.String(1000), nullable=True))
        # Migrate data from plaintext to encrypted (noop - data should already be encrypted by app layer)
        if _column_exists("data_sources", "auth_token"):
            op.execute("""
                UPDATE data_sources
                SET auth_token_encrypted = auth_token
                WHERE auth_token IS NOT NULL AND auth_token_encrypted IS NULL
            """)
        # Drop dependent view first
        op.execute("DROP VIEW IF EXISTS v_data_sources_decrypted")
        # Drop plaintext column
        if _column_exists("data_sources", "auth_token"):
            op.drop_column("data_sources", "auth_token")
        # Recreate view using auth_token_encrypted
        op.execute("""
            CREATE OR REPLACE VIEW v_data_sources_decrypted AS
            SELECT
                id,
                source_name,
                source_type,
                base_url,
                api_key_required,
                CASE
                    WHEN auth_token_encrypted IS NOT NULL THEN pgp_sym_decrypt(auth_token_encrypted::bytea, 'bedaanwaves_master_key')
                    ELSE NULL::text
                END AS auth_token,
                data_format,
                last_verification,
                verification_count,
                is_active,
                info,
                created_at,
                updated_at
            FROM data_sources
        """)

    # ============================================================
    # 3. Fix currency defaults for assets and portfolios
    # ============================================================
    if _table_exists("assets"):
        # Update existing IRR to USD
        op.execute("UPDATE assets SET currency = 'USD' WHERE currency = 'IRR'")
        # Change default
        op.alter_column("assets", "currency", server_default="USD")
        # Add CHECK constraint
        if not _constraint_exists("assets", "chk_assets_currency"):
            op.create_check_constraint("chk_assets_currency", "assets", "currency IN ('USD')")

    if _table_exists("portfolios"):
        op.execute("UPDATE portfolios SET base_currency = 'USD' WHERE base_currency = 'IRR'")
        op.alter_column("portfolios", "base_currency", server_default="USD")
        if not _constraint_exists("portfolios", "chk_portfolio_currency"):
            op.create_check_constraint("chk_portfolio_currency", "portfolios", "base_currency IN ('USD')")

    # ============================================================
    # 4. Add composite indexes for raw_market_data
    # ============================================================
    if _table_exists("raw_market_data"):
        if not _index_exists("raw_market_data", "idx_raw_market_lookup"):
            op.create_index(
                "idx_raw_market_lookup",
                "raw_market_data",
                ["raw_symbol", "market", "data_type", "source_timestamp"]
            )
        if not _index_exists("raw_market_data", "idx_raw_market_recent"):
            # Note: INCLUDE not supported in all PG versions via alembic, use raw SQL
            op.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_market_recent
                ON raw_market_data (source_timestamp DESC)
                INCLUDE (raw_symbol, data_type, price, volume)
            """)

    # ============================================================
    # 5. Add covering indexes for score_history
    # ============================================================
    if _table_exists("score_history"):
        if not _index_exists("score_history", "idx_score_history_trend"):
            op.execute("""
                CREATE INDEX IF NOT EXISTS idx_score_history_trend
                ON score_history (asset_id, date DESC)
                INCLUDE (overall_score, grade, data_quality)
            """)
        if not _index_exists("score_history", "idx_score_history_dim_date"):
            op.execute("""
                CREATE INDEX IF NOT EXISTS idx_score_history_dim_date
                ON score_history (asset_id, date)
                INCLUDE (dimension_scores)
            """)

    # ============================================================
    # 6. Add OHLC CHECK constraints for market_data_snapshots
    # ============================================================
    if _table_exists("market_data_snapshots"):
        if not _constraint_exists("market_data_snapshots", "chk_snapshot_ohlc"):
            op.create_check_constraint(
                "chk_snapshot_ohlc",
                "market_data_snapshots",
                "high >= open AND high >= close AND high >= low AND low <= open AND low <= close AND low >= 0 AND open >= 0 AND close >= 0"
            )
        if not _constraint_exists("market_data_snapshots", "chk_snapshot_volume"):
            op.create_check_constraint(
                "chk_snapshot_volume",
                "market_data_snapshots",
                "volume >= 0"
            )


def downgrade() -> None:
    # Remove OHLC constraints
    if _constraint_exists("market_data_snapshots", "chk_snapshot_volume"):
        op.drop_constraint("chk_snapshot_volume", "market_data_snapshots", type_="check")
    if _constraint_exists("market_data_snapshots", "chk_snapshot_ohlc"):
        op.drop_constraint("chk_snapshot_ohlc", "market_data_snapshots", type_="check")

    # Remove indexes
    if _index_exists("score_history", "idx_score_history_dim_date"):
        op.drop_index("idx_score_history_dim_date", table_name="score_history")
    if _index_exists("score_history", "idx_score_history_trend"):
        op.drop_index("idx_score_history_trend", table_name="score_history")

    if _index_exists("raw_market_data", "idx_raw_market_recent"):
        op.drop_index("idx_raw_market_recent", table_name="raw_market_data")
    if _index_exists("raw_market_data", "idx_raw_market_lookup"):
        op.drop_index("idx_raw_market_lookup", table_name="raw_market_data")

    # Remove currency constraints and revert defaults
    if _constraint_exists("portfolios", "chk_portfolio_currency"):
        op.drop_constraint("chk_portfolio_currency", "portfolios", type_="check")
    op.alter_column("portfolios", "base_currency", server_default="IRR")
    op.execute("UPDATE portfolios SET base_currency = 'IRR' WHERE base_currency = 'USD'")

    if _constraint_exists("assets", "chk_assets_currency"):
        op.drop_constraint("chk_assets_currency", "assets", type_="check")
    op.alter_column("assets", "currency", server_default="IRR")
    op.execute("UPDATE assets SET currency = 'IRR' WHERE currency = 'USD'")

    # Restore auth_token column
    if _table_exists("data_sources"):
        # Drop view first
        op.execute("DROP VIEW IF EXISTS v_data_sources_decrypted")
        # Add back plaintext auth_token if missing
        if not _column_exists("data_sources", "auth_token"):
            op.add_column("data_sources", sa.Column("auth_token", sa.String(500), nullable=True))
        # Recreate view using auth_token (plaintext)
        op.execute("""
            CREATE OR REPLACE VIEW v_data_sources_decrypted AS
            SELECT
                id,
                source_name,
                source_type,
                base_url,
                api_key_required,
                CASE
                    WHEN auth_token IS NOT NULL THEN pgp_sym_decrypt(auth_token, 'bedaanwaves_master_key'::text)
                    ELSE NULL::text
                END AS auth_token,
                data_format,
                last_verification,
                verification_count,
                is_active,
                info,
                created_at,
                updated_at
            FROM data_sources
        """)

    # Remove user security fields
    if _index_exists("users", "idx_users_locked_until"):
        op.drop_index("idx_users_locked_until", table_name="users")
    if _index_exists("users", "idx_users_email_verified"):
        op.drop_index("idx_users_email_verified", table_name="users")

    if _column_exists("users", "locked_until"):
        op.drop_column("users", "locked_until")
    if _column_exists("users", "failed_login_attempts"):
        op.drop_column("users", "failed_login_attempts")
    if _column_exists("users", "email_verified"):
        op.drop_column("users", "email_verified")