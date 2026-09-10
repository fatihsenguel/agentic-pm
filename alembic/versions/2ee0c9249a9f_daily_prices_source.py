"""daily_prices source

A close carries where it came from, as a rate already does (fx_rates.source):
the provider's name, written by the fetch, required and defaulted nowhere
(expected_values.md D17, D19, Part 9). It is the trace a defended price
needs: when a stored close and the exchange's print disagree, the row says
which provider to look at.

The table is populated, so the column is added nullable, filled, then made
NOT NULL in batch mode. Every existing row came from the one provider the
system has ever had, so the fill is the literal "yfinance". What the fill
does not say is under which convention the row was fetched: rows stored
before commit 314b707 hold the dividend-adjusted close on dates before a
holding's latest ex-dividend date (Part 9 B), and the same source name will
sit on as-traded rows after it. That is why the stored history is deleted
and refetched by hand once, after this migration, so the table holds one
convention; the migration itself moves no close.

No CAST anywhere: the column is new and nothing changes type.

Revision ID: 2ee0c9249a9f
Revises: 88d7b7afdce7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2ee0c9249a9f"
down_revision: Union[str, Sequence[str], None] = "88d7b7afdce7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("daily_prices", sa.Column("source", sa.String(50), nullable=True))
    op.execute("UPDATE daily_prices SET source = 'yfinance' WHERE source IS NULL")
    with op.batch_alter_table("daily_prices") as batch:
        batch.alter_column("source", existing_type=sa.String(50), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("daily_prices") as batch:
        batch.drop_column("source")
