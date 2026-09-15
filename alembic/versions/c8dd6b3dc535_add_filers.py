"""add filers

One filer as EDGAR's submissions document states it (expected_values.md
Part 13 C): the name, the SIC code and its description, with the pull
date. The code is in the submissions document and not in company facts,
so it has its own fetch and its own record; the document carries the
current code only, so the row is the code as of `pulled_at`, and a later
pull that finds another code overwrites the row (decision 49).

`sic` and `sic_description` are nullable because EDGAR leaves them empty
for some filers; `name` and `pulled_at` are NOT NULL and defaulted
nowhere, since the row is written only after a fetch has returned.

No rows are written here, and nothing reads or writes the table at this
revision.

Revision ID: c8dd6b3dc535
Revises: 97d3708851e5
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c8dd6b3dc535"
down_revision: Union[str, Sequence[str], None] = "97d3708851e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "filers",
        sa.Column("cik", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sic", sa.String(4), nullable=True),
        sa.Column("sic_description", sa.String(200), nullable=True),
        sa.Column("pulled_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("cik"),
    )


def downgrade() -> None:
    op.drop_table("filers")
