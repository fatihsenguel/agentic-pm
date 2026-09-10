"""transaction fees required

Fees are part of cost basis (expected_values.md D11): what was paid on a
buy, what was received on a sale, fees inside. The column was nullable with
a default of zero on the model, so a row written without a fee was a free
trade with a plausible face. It becomes NOT NULL, defaulted nowhere; a row
without a fee is unstorable, the way one without an amount is.

The nine existing rows carry 0.00, the fees Part 8 A states, so the
constraint holds on them; a NULL here would be a row nobody could have
written through record_transaction, which requires the argument. Batch
mode, since SQLite cannot alter a column in place; the type does not
change, so nothing is cast.

Revision ID: 88d7b7afdce7
Revises: 552ab8900332
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "88d7b7afdce7"
down_revision: Union[str, Sequence[str], None] = "552ab8900332"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.alter_column("fees", existing_type=sa.Float(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch:
        batch.alter_column("fees", existing_type=sa.Float(), nullable=True)
