"""macro_data source required

The last source column to become required: fx_rates and daily_prices
already refuse a row that does not name its provider. The macro column
lost its Python default in the thirteenth session and stayed nullable as
its own decision; this takes it (handoff item 25).

No fill. The price migration filled its new column because every row's
origin was known; here a row with no source would be a row of unknown
origin, and stamping a name on it is the repair shape. The migration
counts null rows first and refuses if any exist, naming the count. On the
day this was written the count was zero: 185 rows, every one "yfinance".

Nullability only, in batch mode, no type change and no CAST.

Revision ID: 87d3ec68c2ed
Revises: 7b1c4e2d9a05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "87d3ec68c2ed"
down_revision: Union[str, Sequence[str], None] = "7b1c4e2d9a05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    missing = op.get_bind().exec_driver_sql(
        "SELECT COUNT(*) FROM macro_data WHERE source IS NULL OR source = ''"
    ).scalar()
    if missing:
        raise RuntimeError(
            f"{missing} macro_data rows have no source; their origin is unknown "
            "and this migration will not invent one. Delete or source them by "
            "hand first."
        )
    with op.batch_alter_table("macro_data") as batch:
        batch.alter_column("source", existing_type=sa.String(50), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("macro_data") as batch:
        batch.alter_column("source", existing_type=sa.String(50), nullable=True)
