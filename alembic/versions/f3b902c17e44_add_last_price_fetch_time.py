"""add last_price_fetch_time to asset_fetch_metadata

Callers passing an explicit start_date to update_prices_for_asset bypassed the
cache entirely and hit the provider unconditionally, so fetch_prices_tool and
calculate_covariance_tool each downloaded the same window. Nine tickers cost 18
provider calls per query and roughly 33s of latency against a 60-calls-per-minute
cap.

AssetFetchMetadata already tracks last_earnings_fetch_time, last_profile_fetch_time
and last_shares_fetch_time on the same pattern; prices were simply never added.

Nullable: existing rows have never recorded a price fetch, and NULL correctly
means "never checked", which _should_fetch already treats as fetch.

Revision ID: f3b902c17e44
Revises: e4c81a9d3b57
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f3b902c17e44"
down_revision: Union[str, Sequence[str], None] = "e4c81a9d3b57"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "asset_fetch_metadata",
        sa.Column("last_price_fetch_time", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("asset_fetch_metadata", "last_price_fetch_time")
