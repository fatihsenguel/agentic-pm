"""add ticker_ciks

The SEC's published ticker file as stored: one row per (ticker, CIK) pair,
keyed by ticker, with the pull date (decision 29, question 50). The file is
one document for every listed filer, so a refresh rewrites the whole table
as the file now states it and moves every row's date; a ticker the file no
longer carries leaves the table with the refresh.

Every column is NOT NULL and defaulted nowhere: a row is written only after
a fetch has returned. The file's company title is not stored; nothing
consumes it.

No rows are written here, and nothing reads or writes the table at this
revision.

Revision ID: e289a03682f2
Revises: c8dd6b3dc535
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e289a03682f2"
down_revision: Union[str, Sequence[str], None] = "c8dd6b3dc535"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticker_ciks",
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column("cik", sa.Integer(), nullable=False),
        sa.Column("pulled_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("ticker"),
    )


def downgrade() -> None:
    op.drop_table("ticker_ciks")
