"""add purchase_date to portfolio_holdings

Benchmark case 1.2 passes only when the purchase date is named, and there was
nowhere to store it: PortfolioHolding had quantity, average_price, created_at
and updated_at; Transaction had a date but no portfolio_id, so it could not say
which portfolio bought what.

Nullable on purpose. Existing rows have no known purchase date, and writing
created_at into it would invent one — the exact failure this project keeps
finding. A holding with purchase_date IS NULL must be reported as "purchase
date unknown", not silently defaulted.

Deliberate limitation: one date plus one average_price cannot represent a
position built in tranches. Accepted because benchmark.md Part 2 puts tax
assessment out of scope. If lot-level cost basis is ever needed, add
portfolio_id to Transaction and derive holdings from history; this column then
becomes redundant and can be dropped without touching the holdings table.

Revision ID: e4c81a9d3b57
Revises: 01225e17789b
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e4c81a9d3b57"
down_revision: Union[str, Sequence[str], None] = "01225e17789b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "portfolio_holdings",
        sa.Column("purchase_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("portfolio_holdings", "purchase_date")
