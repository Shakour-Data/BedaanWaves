#!/usr/bin/env python
"""
Creates a new Alembic migration that adds missing partitioned tables for price candles.
"""

import uuid
from datetime import datetime

# Generate a revision ID (12 hex chars)
revision_id = uuid.uuid4().hex[:12]
down_revision = '20260729_01'
create_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

# Use triple double quotes with single quotes inside
migration_content = '''"""Create missing partitioned tables for IR, Intl, and Crypto price candles

Revision ID: {revision_id}
Revises: {down_revision}
Create Date: {create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '{revision_id}'
down_revision: Union[str, None] = '{down_revision}'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Create missing partitioned tables if they don't exist."""
    # Import models here to avoid circular imports
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    
    from app.models.models import IRPriceCandle, IntlPriceCandle, CryptoPriceCandle

    tables = [
        (IRPriceCandle, "ir_price_candles"),
        (IntlPriceCandle, "intl_price_candles"),
        (CryptoPriceCandle, "crypto_price_candles"),
    ]

    for model, table_name in tables:
        if not _table_exists(table_name):
            print(f"Creating table {table_name}")
            op.create_table(
                table_name,
                sa.Column("id", sa.Integer, primary_key=True, index=True),
                sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id"), nullable=False),
                sa.Column("timeframe", sa.String(10), nullable=False),
                sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
                sa.Column("open", sa.Numeric(20, 8), nullable=False),
                sa.Column("high", sa.Numeric(20, 8), nullable=False),
                sa.Column("low", sa.Numeric(20, 8), nullable=False),
                sa.Column("close", sa.Numeric(20, 8), nullable=False),
                sa.Column("volume", sa.Numeric(20, 8), nullable=False),
                sa.Column("turnover", sa.Numeric(20, 8), nullable=True),
                sa.Column("transactions", sa.Integer, nullable=True),
                # Add foreign key relationships properly
                sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id"), nullable=False),
                # Add process_time for crypto prices and other time-based data
            )
        else:
            print(f"Table {table_name} already exists, skipping")


def downgrade() -> None:
    """Drop the partitioned tables if they exist."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    
    from app.models.models import IRPriceCandle, IntlPriceCandle, CryptoPriceCandle

    tables = [
        (IRPriceCandle, "ir_price_candles"),
        (IntlPriceCandle, "intl_price_candles"),
        (CryptoPriceCandle, "crypto_price_candles"),
    ]

    for model, table_name in tables:
        if _table_exists(table_name):
            print(f"Dropping table {table_name}")
            op.drop_table(table_name)
        else:
            print(f"Table {table_name} does not exist, skipping")
'''.format(
    revision_id=revision_id,
    down_revision=down_revision,
    create_date=create_date
)
    
with open(f"{revision_id}_create_missing_partitioned_tables.py", 'w') as f:
    f.write(migration_content.replace('\\', '/'))

print(f"Migration file created: {revision_id}_create_missing_partitioned_tables.py")