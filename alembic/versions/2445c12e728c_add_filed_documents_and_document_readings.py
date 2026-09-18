"""add filed_documents and document_readings

filed_documents: one filing's primary document as text, one row per
accession, written once (expected_values.md Part 16, D51). The whole text,
not its sections, so a change to the sectioner needs no fetch. No interval
and no pull date: an accession never changes. The filer, the form and the
filed date are not stored; filed_facts names the filing by the same
accession.

document_readings: one reading of one section as the model supplied it and
as `reading.record` accepted it (Part 15, D47), JSON text, keyed by
accession, section, model and prompt version. A refused reading leaves no
row.

Every column is NOT NULL and defaulted nowhere: a row is written only after
the thing it records exists.

No rows are written here, and nothing reads or writes either table at this
revision.

Revision ID: 2445c12e728c
Revises: e289a03682f2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2445c12e728c"
down_revision: Union[str, Sequence[str], None] = "e289a03682f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "filed_documents",
        sa.Column("accn", sa.String(20), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("accn"),
    )
    op.create_table(
        "document_readings",
        sa.Column("accn", sa.String(20), nullable=False),
        sa.Column("section", sa.String(10), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("claims", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["accn"], ["filed_documents.accn"]),
        sa.PrimaryKeyConstraint("accn", "section", "model", "prompt_version"),
    )


def downgrade() -> None:
    op.drop_table("document_readings")
    op.drop_table("filed_documents")
