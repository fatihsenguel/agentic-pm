"""drop portfolio_holdings

Holdings derive from the ledger (expected_values.md D13): since be14e4b
PortfolioManager.get_holdings reads `transactions` and computes the
position, and nothing reads this table. A table that is written and never
read is a second source of truth with stale numbers, so it goes, as the
purchase_date migration (e4c81a9d3b57) said it would once holdings were
derived from history.

The rows are dropped with it. Portfolio 3's nine were the same nine buys
the seed also wrote to the ledger; nothing is lost that the ledger does not
carry. Downgrade recreates the table empty, with the purchase_date column
e4c81a9d3b57 added; the rows are not recoverable and are not needed.

Revision ID: 45b959c05420
Revises: 65c3de3ff3fd
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "45b959c05420"
down_revision: Union[str, Sequence[str], None] = "65c3de3ff3fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_portfolio_holdings_portfolio_id", table_name="portfolio_holdings")
    op.drop_index("ix_portfolio_holdings_asset_id", table_name="portfolio_holdings")
    op.drop_table("portfolio_holdings")


def downgrade() -> None:
    op.create_table(
        "portfolio_holdings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("average_price", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portfolio_id", "asset_id", name="_portfolio_asset_uc"),
    )
    op.create_index("ix_portfolio_holdings_asset_id", "portfolio_holdings", ["asset_id"], unique=False)
    op.create_index("ix_portfolio_holdings_portfolio_id", "portfolio_holdings", ["portfolio_id"], unique=False)
