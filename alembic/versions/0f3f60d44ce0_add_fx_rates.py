"""add fx_rates

A spot rate is a price source like a close (expected_values.md D17): stored
per day with an as-of date, fetched from a provider, and a missing one raises
rather than falling back to yesterday's rate or to 1. This is the record; the
lookup is quant/fx.py's and the fetch is DataManager's, each its own commit.

`rate` is units of `base` per one unit of `quote` - with base EUR and quote
USD, 0.85 is 0.85 euros per dollar - so a foreign holding's value in the
portfolio's currency is quantity x price x rate on the price's as-of date
(D16). Named columns rather than a pair string, because the string would
look like the market quotation, which runs the other way round.

Every column NOT NULL and none defaulted, like the ledger's portfolio_id and
amount: the table has no rows, so there is nothing a NULL would stand in
for, and a rate with no date or no source must be unstorable rather than
refused later by every reader. One row per (base, quote, date).

Nothing reads or writes the table at this revision. Portfolio 3 is USD
throughout and needs no row; the seed does not touch it.

Revision ID: 0f3f60d44ce0
Revises: 45b959c05420
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0f3f60d44ce0"
down_revision: Union[str, Sequence[str], None] = "45b959c05420"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fx_rates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("base", sa.String(3), nullable=False),
        sa.Column("quote", sa.String(3), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("base", "quote", "date", name="_fx_base_quote_date_uc"),
    )


def downgrade() -> None:
    op.drop_table("fx_rates")
