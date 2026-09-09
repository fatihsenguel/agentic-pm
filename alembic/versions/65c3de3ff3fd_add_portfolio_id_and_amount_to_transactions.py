"""add portfolio_id and amount to transactions

A ledger row belongs to a portfolio (expected_values.md D14). The table had
an asset and no portfolio, the shape that makes `Dividend` unattributable
(Part 6): a row without a portfolio cannot be summed into one. `amount` is
the settled figure in the portfolio's currency - quantity x price + fees on
a buy, minus fees on a sale, taken from the statement for a real portfolio
and equal to that arithmetic for a synthetic one. It is data, never computed
here; it is where a second currency enters (Part 8, "What Part 8 does not
cover").

Both NOT NULL, unlike purchase_date and instrument_type, which were nullable
because existing rows had no known value. This table has no rows and no
writer, so there is nothing a NULL would stand in for, and a row that
belongs to no portfolio or has no amount must be unstorable rather than
refused later by every reader.

Batch mode because SQLite cannot add a NOT NULL column without a default in
place; the table is rebuilt, which on an empty table is safe. The migration
does not check the table is empty: a row here that predates this column has
no portfolio and no amount to invent, and the rebuild fails on it, which is
the right outcome.

Revision ID: 65c3de3ff3fd
Revises: 05034c6316c8
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "65c3de3ff3fd"
down_revision: Union[str, Sequence[str], None] = "05034c6316c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.add_column(sa.Column("portfolio_id", sa.Integer(), nullable=False))
        batch.add_column(sa.Column("amount", sa.Float(), nullable=False))
        batch.create_foreign_key(
            "fk_transactions_portfolio_id_portfolios",
            "portfolios",
            ["portfolio_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_index("ix_transactions_portfolio_id", ["portfolio_id"])


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.drop_index("ix_transactions_portfolio_id")
        batch.drop_constraint("fk_transactions_portfolio_id_portfolios", type_="foreignkey")
        batch.drop_column("amount")
        batch.drop_column("portfolio_id")
