"""portfolios ips_path

A portfolio names the policy it is checked against (DIRECTION.md Order 2,
item 4): the path of its ips.toml, required and defaulted nowhere, the
way currency is. The benchmark portfolio names the committed file by a
relative path the loader anchors to the project root; a personal
portfolio names, by an absolute path, a file outside the repository. The
policy belongs to the portfolio and not to the process, so two portfolios
in one database are checked against two policies and the benchmark keeps
its own.

The table is populated, so the column is added nullable, filled, then
made NOT NULL in batch mode. The fill names one row by id: portfolio 3,
the Benchmark Portfolio, which has been checked against the committed
`ips.toml` since the checker existed. Any other row is left NULL and the
NOT NULL step then refuses, which is the point: a portfolio this
migration does not know is not given the committed policy by default.

No CAST anywhere: the column is new and nothing changes type.

Revision ID: 7b1c4e2d9a05
Revises: 2ee0c9249a9f
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "7b1c4e2d9a05"
down_revision: Union[str, Sequence[str], None] = "2ee0c9249a9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("portfolios", sa.Column("ips_path", sa.String(500), nullable=True))
    op.execute("UPDATE portfolios SET ips_path = 'ips.toml' WHERE id = 3")
    with op.batch_alter_table("portfolios") as batch:
        batch.alter_column("ips_path", existing_type=sa.String(500), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("portfolios") as batch:
        batch.drop_column("ips_path")
