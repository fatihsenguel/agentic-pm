"""add fx_fetch_metadata

The rate fetch's cache record, one row per (base, quote): when the provider
was last asked and how far back it has been asked. The same two facts
asset_fetch_metadata keeps for prices, in their own table because a
currency pair has no asset.

Coverage is "how far back have we asked", never "do we hold a row on that
date" (KNOWN_GAPS, "No price cache for callers passing a date range"): a
requested start on a weekend or a holiday has no row, so a row-based check
refetches the pair's whole history on every call and looks like a cache
while it does it. Both facts nullable, as on asset_fetch_metadata: the row
is created before the first fetch and filled by it.

Nothing reads or writes the table at this revision; the fetch is its own
commit. Portfolio 3 is USD throughout and needs no row.

Revision ID: ee845dad889a
Revises: 0f3f60d44ce0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "ee845dad889a"
down_revision: Union[str, Sequence[str], None] = "0f3f60d44ce0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fx_fetch_metadata",
        sa.Column("base", sa.String(3), nullable=False),
        sa.Column("quote", sa.String(3), nullable=False),
        sa.Column("last_fetch_time", sa.DateTime(), nullable=True),
        sa.Column("earliest_start", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("base", "quote"),
    )


def downgrade() -> None:
    op.drop_table("fx_fetch_metadata")
