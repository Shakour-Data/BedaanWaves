"""add macroeconomic section (free, no-API-key) data model.

Adds:
- ``uix_macro_indicator`` unique constraint on ``(indicator_code, period)``
  for the ``macro_indicators`` table. The daily scheduler job referenced this
  constraint name via ``ON CONFLICT`` but it was never created, so the macro
  refresh has been silently failing; this fixes that.
- index for latest-per-indicator lookups.
- ``macro_forecasts`` table storing in-process (ARIMA/naive) macro forecasts
  derived from locally-stored ``MacroIndicator`` history. No external API is
  used.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260907_add_macro_section"
down_revision: Union[str, None] = "20260907_consolidate_migrations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Collapse any pre-existing duplicate (indicator_code, period) rows,
    #    keeping the most recent (highest id). Only affects non-null periods.
    op.execute(
        """
        DELETE FROM macro_indicators
        WHERE period IS NOT NULL
          AND id NOT IN (
            SELECT MAX(id)
            FROM macro_indicators
            WHERE period IS NOT NULL
            GROUP BY indicator_code, period
          )
        """
    )

    # 2. Add the unique constraint the scheduler relies on (previously missing).
    op.create_unique_constraint(
        "uix_macro_indicator", "macro_indicators", ["indicator_code", "period"]
    )

    # 3. Index for fast "latest value per indicator" lookups.
    op.create_index(
        "idx_macro_indicator_code_as_of",
        "macro_indicators",
        ["indicator_code", "as_of"],
    )

    # 4. Forecast table for in-process macro forecasts (no external API).
    op.create_table(
        "macro_forecasts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("indicator_code", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False, server_default="ARIMA"),
        sa.Column("horizon", sa.Integer(), nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("forecast_value", sa.Numeric(20, 6)),
        sa.Column("lower_ci", sa.Numeric(20, 6)),
        sa.Column("upper_ci", sa.Numeric(20, 6)),
        sa.Column("confidence", sa.Numeric(5, 2), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "indicator_code",
            "model_name",
            "horizon",
            "forecast_date",
            name="uix_macro_forecast",
        ),
    )
    op.create_index(
        "idx_macro_forecasts_code_date",
        "macro_forecasts",
        ["indicator_code", "forecast_date", "horizon"],
    )


def downgrade() -> None:
    op.drop_index("idx_macro_forecasts_code_date", table_name="macro_forecasts")
    op.drop_table("macro_forecasts")
    op.drop_index("idx_macro_indicator_code_as_of", table_name="macro_indicators")
    op.drop_constraint("uix_macro_indicator", "macro_indicators", type_="unique")
