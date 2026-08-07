"""Create missing partitioned tables for IR, Intl, and Crypto price candles

Revision ID: 20260806_fix_missing_tables
Revises: 20260729_01
Create Date: 2026-08-06 13:10:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260806_fix_missing_tables'
down_revision: Union[str, None] = '20260729_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ir_price_candles if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS ir_price_candles (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER NOT NULL REFERENCES assets(id),
            timeframe VARCHAR(10) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            open NUMERIC(20, 8) NOT NULL,
            high NUMERIC(20, 8) NOT NULL,
            low NUMERIC(20, 8) NOT NULL,
            close NUMERIC(20, 8) NOT NULL,
            volume NUMERIC(20, 8) NOT NULL,
            turnover NUMERIC(20, 8),
            transactions INTEGER
        )
    """)
    
    # Create intl_price_candles if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS intl_price_candles (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER NOT NULL REFERENCES assets(id),
            timeframe VARCHAR(10) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            open NUMERIC(20, 8) NOT NULL,
            high NUMERIC(20, 8) NOT NULL,
            low NUMERIC(20, 8) NOT NULL,
            close NUMERIC(20, 8) NOT NULL,
            volume NUMERIC(20, 8) NOT_NULL,
            turnover NUMERIC(20, 8),
            transactions INTEGER
        )
    """)

    # Create crypto_price_candles if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS crypto_price_candles (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER NOT NULL REFERENCES assets(id),
            timeframe VARCHAR(10) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            open NUMERIC(20, 8) NOT NULL,
            high NUMERIC(20, 8) NOT NULL,
            low NUMERIC(20, 8) NOT NULL,
            close NUMERIC(20, 8) NOT NULL,
            volume NUMERIC(20, 8) NOT NULL,
            turnover NUMERIC(20, 8),
            transactions INTEGER
        )
    """)

def downgrade() -> None:
    op.drop_table('ir_price_candles')
    op.drop_table('intl_price_candles')
    op.drop_table('crypto_price_candles')
