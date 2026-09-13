"""add filed_facts

One row per figure as a filer filed it, in one filing (expected_values.md
Parts 12 and 13): the EDGAR provider's record as stored. Decision 28 made it
a new table rather than financial_statements, which has no filed date at any
grain and spreads a fiscal year over three rows.

`value` is Text, the digits EDGAR sent: SQLite has no exact decimal type, a
Float column returns 0.241 as 0.24099999..., and Numeric stores a float
underneath. `start` is nullable because an instant has none; `fy`, `fp` and
`frame` because EDGAR leaves them empty, a proxy statement's `fy` and `fp`
among them. Every other column NOT NULL and none defaulted, like fx_rates.
No pull date on the row: when a company was fetched is the cache record's.

The key is D26's (tag, start, end, accn) per company, as two partial unique
indexes. SQLite never counts two NULLs as equal inside a unique constraint,
so a plain constraint over those five columns would store an instant twice.

No rows are written here, and nothing reads or writes the table at this
revision.

Revision ID: 302903e3d966
Revises: 87d3ec68c2ed
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "302903e3d966"
down_revision: Union[str, Sequence[str], None] = "87d3ec68c2ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "filed_facts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cik", sa.Integer(), nullable=False),
        sa.Column("tag", sa.String(200), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("start", sa.Date(), nullable=True),
        sa.Column("end", sa.Date(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("accn", sa.String(20), nullable=False),
        sa.Column("fy", sa.Integer(), nullable=True),
        sa.Column("fp", sa.String(2), nullable=True),
        sa.Column("form", sa.String(10), nullable=False),
        sa.Column("filed", sa.Date(), nullable=False),
        sa.Column("frame", sa.String(20), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "_filed_fact_instant_uc", "filed_facts", ["cik", "tag", "end", "accn"],
        unique=True, sqlite_where=sa.text("start IS NULL"),
    )
    op.create_index(
        "_filed_fact_duration_uc", "filed_facts", ["cik", "tag", "start", "end", "accn"],
        unique=True, sqlite_where=sa.text("start IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("_filed_fact_duration_uc", table_name="filed_facts")
    op.drop_index("_filed_fact_instant_uc", table_name="filed_facts")
    op.drop_table("filed_facts")
