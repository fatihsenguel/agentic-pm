"""add instrument_type to assets

IPS-4.2 counts an issuer's exposure through directly held shares only, and
IPS-4.3 counts sectors the same way; a fund is exempt from the first and
outside the second. Which holdings are shares and which are funds is data the
code has to carry, not infer (expected_values.md Part 7): inferring it from
"has no sector" would make a share with unknown sector into a fund silently.

Values are `share` or `fund`. The set is enforced where it is consumed - the
compliance checker raises on NULL or anything else - rather than by a CHECK
constraint, which SQLite cannot add through add_column without batch mode,
for two values nothing else reads.

Nullable on purpose, like purchase_date. Existing assets have no known type
and writing one in would invent it. A holding with instrument_type NULL is
one the checker refuses to check, not one it treats as a share.

Shared across portfolios like asset_class and sector: seeding portfolio 3
writes it for the nine tickers, which cover every holding of portfolios 1
and 2 as well (tests/golden/KNOWN_GAPS.md, "Seeding portfolio 3 rewrites
metadata shared with portfolios 1 and 2").

Revision ID: 05034c6316c8
Revises: a7d5e1c04b83
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "05034c6316c8"
down_revision: Union[str, Sequence[str], None] = "a7d5e1c04b83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column("instrument_type", sa.String(10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("assets", "instrument_type")
