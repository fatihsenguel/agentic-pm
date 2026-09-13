"""add filed_fetch_metadata

The filings fetch's cache record, one row per company. A company-facts
document is the company's whole history, so the one fact to keep is when
the company was last fetched: for filings_fetch_interval_days, and as the
pull date an answer states.

`last_fetch_time` is NOT NULL, unlike fx_fetch_metadata's: the row is
written only after a fetch has returned, so an empty time would stand for
nothing, and a fetch that fails leaves no record and is retried.

No rows are written here.

Revision ID: 97d3708851e5
Revises: 302903e3d966
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "97d3708851e5"
down_revision: Union[str, Sequence[str], None] = "302903e3d966"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "filed_fetch_metadata",
        sa.Column("cik", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("last_fetch_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("cik"),
    )


def downgrade() -> None:
    op.drop_table("filed_fetch_metadata")
