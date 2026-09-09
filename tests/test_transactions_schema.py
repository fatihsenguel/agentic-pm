"""
The transactions table carries a portfolio and an amount (expected_values.md D14).

A ledger row belongs to a portfolio: without `portfolio_id` no row can be
summed into one, which is the shape that makes `Dividend` unattributable
(Part 6). `amount` is the settled figure in the portfolio's currency, data
and never computed by the database. Both required: the table has no rows,
so there is nothing a NULL would stand in for.

Two views of the same fact, both asserted. The model's table definition,
which is what the code sees, and the database the suite runs against - the
copy conftest.py makes of data/portfolio.db - which is what a migration
applied with `alembic upgrade head` produces. Before the migration is
applied the second half fails with the columns missing, as
test_instrument_type.py did for its column.
"""

import pytest
from sqlalchemy import inspect

from portfolio_tool.database_setup import Transaction, engine


REQUIRED = {"portfolio_id", "amount"}


# --- the model -------------------------------------------------------------

def test_model_has_portfolio_id_and_amount():
    assert REQUIRED <= set(Transaction.__table__.c.keys())


@pytest.mark.parametrize("column", sorted(REQUIRED))
def test_model_column_is_required(column):
    assert Transaction.__table__.c[column].nullable is False


def test_model_portfolio_id_references_portfolios():
    targets = {fk.column.table.name for fk in Transaction.__table__.c["portfolio_id"].foreign_keys}
    assert targets == {"portfolios"}


# --- the database ----------------------------------------------------------

@pytest.fixture(scope="module")
def columns():
    return {c["name"]: c for c in inspect(engine).get_columns("transactions")}


@pytest.fixture(scope="module")
def foreign_keys():
    return inspect(engine).get_foreign_keys("transactions")


def test_database_has_portfolio_id_and_amount(columns):
    assert REQUIRED <= set(columns)


@pytest.mark.parametrize("column", sorted(REQUIRED))
def test_database_column_is_required(columns, column):
    assert columns[column]["nullable"] is False


def test_database_portfolio_id_references_portfolios(foreign_keys):
    referring = [fk for fk in foreign_keys if fk["constrained_columns"] == ["portfolio_id"]]
    assert [fk["referred_table"] for fk in referring] == ["portfolios"]
