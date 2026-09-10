"""
The fx_rates table: one spot rate per day, dated, with its source (D17).

A spot rate is a price source like a close: stored per day with an as-of
date, fetched from a provider, and a missing one raises rather than falling
back to yesterday's rate or to 1. The table is the record; the lookup is
quant/fx.py's (tests/test_fx.py) and the fetch is DataManager's.

Columns and what they mean:

  base    the portfolio's currency (D15)
  quote   the asset's currency (D16)
  date    the day the rate is for - a Date, not a timestamp
  rate    units of BASE per one unit of QUOTE, the convention test_fx.py
          pins: 0.85 with base EUR and quote USD is 0.85 euros per dollar
  source  where the rate came from

Every column required, and no default on any of them: a rate with no date
is not a price source, and a rate with no source is a claim nobody made.
One row per (base, quote, date), enforced by a unique constraint.

Two views of the same fact, both asserted, like test_transactions_schema.py.
The model's table definition, which is what the code sees, and the database
the suite runs against - the copy conftest.py makes of data/portfolio.db -
which is what `alembic upgrade head` produces. Before the migration is
applied the second half fails on the table not being there.
"""

import pytest
from sqlalchemy import Date, inspect

import portfolio_tool.database_setup as models
from portfolio_tool.database_setup import Base, engine


TABLE = "fx_rates"
REQUIRED = {"base", "quote", "date", "rate", "source"}
KEY = ["base", "quote", "date"]


# --- the model -------------------------------------------------------------

@pytest.fixture(scope="module")
def table():
    assert hasattr(models, "FxRate"), "no FxRate model in database_setup"
    assert TABLE in Base.metadata.tables
    return models.FxRate.__table__


def test_model_has_the_columns(table):
    assert REQUIRED <= set(table.c.keys())


@pytest.mark.parametrize("column", sorted(REQUIRED))
def test_model_column_is_required(table, column):
    assert table.c[column].nullable is False


@pytest.mark.parametrize("column", sorted(REQUIRED))
def test_model_column_has_no_default(table, column):
    assert table.c[column].default is None
    assert table.c[column].server_default is None


def test_model_date_is_a_date_not_a_timestamp(table):
    assert isinstance(table.c["date"].type, Date)


def test_model_one_rate_per_base_quote_and_day(table):
    uniques = [sorted(c.name for c in u.columns) for u in table.constraints
               if u.__class__.__name__ == "UniqueConstraint"]
    assert sorted(KEY) in uniques


# --- the database ----------------------------------------------------------

@pytest.fixture(scope="module")
def columns():
    inspector = inspect(engine)
    assert TABLE in inspector.get_table_names(), f"no {TABLE} table; run alembic upgrade head"
    return {c["name"]: c for c in inspector.get_columns(TABLE)}


def test_database_has_the_columns(columns):
    assert REQUIRED <= set(columns)


@pytest.mark.parametrize("column", sorted(REQUIRED))
def test_database_column_is_required(columns, column):
    assert columns[column]["nullable"] is False


@pytest.mark.parametrize("column", sorted(REQUIRED))
def test_database_column_has_no_default(columns, column):
    assert columns[column]["default"] is None


def test_database_one_rate_per_base_quote_and_day():
    uniques = [sorted(u["column_names"]) for u in inspect(engine).get_unique_constraints(TABLE)]
    assert sorted(KEY) in uniques
