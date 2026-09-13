"""add index for raw_performance_scores captured_at data_quality

Revision ID: 20260913_add_perf_score_idx
Revises: 20260908_add_nerk_support
Create Date: 2026-09-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260913_add_perf_score_idx"
down_revision = "20260908_add_nerk_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite index to speed up the hierarchical trend aggregation which
    # filters on captured_at range + data_quality IN ('VALIDATED','CLEANED').
    op.create_index(
        "idx_raw_perf_captured_quality",
        "raw_performance_scores",
        ["captured_at", "data_quality"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_raw_perf_captured_quality",
        table_name="raw_performance_scores",
    )