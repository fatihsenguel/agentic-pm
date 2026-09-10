"""transaction date is a date

A ledger row is a day (expected_values.md D13: the first buy's date is the
purchase date), not a moment. The column was a DateTime with a utcnow
default on the model, so a row written without a date got today with a
plausible face; it becomes a Date with no default, and a row without one
is unstorable.

SQLite holds the existing rows as text timestamps, "2024-01-15
00:00:00.000000", which a Date column cannot read, so the values are
rewritten to their first ten characters as part of the change. No reseed is
needed and no state exists in which the rows are unreadable.

Not done with alter_column. Alembic's batch rebuild copies a column whose
type changes through CAST, and SQLite's CAST(... AS DATE) has numeric
affinity: "2024-01-15" came out as the number 2024 on a scratch copy. So
the new column is added beside the old one, filled from the text with no
cast, and the old one dropped and the new one renamed. The column moves to
the end of the table, which nothing reads by position.

Downgrade restores the type and the midnight timestamp the same way; the
day is the only fact the rows ever carried.

Revision ID: 552ab8900332
Revises: ee845dad889a
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "552ab8900332"
down_revision: Union[str, Sequence[str], None] = "ee845dad889a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.add_column(sa.Column("trade_date", sa.Date(), nullable=True))
    op.execute("UPDATE transactions SET trade_date = substr(date, 1, 10)")
    with op.batch_alter_table("transactions") as batch:
        batch.drop_column("date")
        batch.alter_column("trade_date", new_column_name="date",
                           existing_type=sa.Date(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.add_column(sa.Column("stamp", sa.DateTime(), nullable=True))
    op.execute("UPDATE transactions SET stamp = date || ' 00:00:00.000000'")
    with op.batch_alter_table("transactions") as batch:
        batch.drop_column("date")
        batch.alter_column("stamp", new_column_name="date",
                           existing_type=sa.DateTime(), nullable=False)
