"""add earliest_price_start to asset_fetch_metadata

The first cache attempt tested coverage as "do we hold a row on or before the
requested start". That can never be true when the requested start is not a
trading day, or predates the asset's listing. Requesting 2023-09-04 (Labor Day)
returns 2023-09-05 as the first row, so JNJ, JPM, NEE and VNQ re-downloaded 752
rows on every call while SPY, TLT and GLD — which had deeper history from
earlier runs — cached correctly.

This records how far back we have actually asked the provider, which is the
question the cache needs answered. If we asked from a date and got nothing
earlier, there is nothing earlier to get.

Nullable: NULL means never asked, so the first call per asset does one full
fetch and records the result. Self-healing, one fetch per asset, once.

Revision ID: a7d5e1c04b83
Revises: f3b902c17e44
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a7d5e1c04b83"
down_revision: Union[str, Sequence[str], None] = "f3b902c17e44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "asset_fetch_metadata",
        sa.Column("earliest_price_start", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("asset_fetch_metadata", "earliest_price_start")
