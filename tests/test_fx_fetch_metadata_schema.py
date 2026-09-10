"""
The fx_fetch_metadata table: the rate fetch's cache record, per pair.

Coverage means "how far back have we asked the provider", not "do we hold a
row on that date". Those differ whenever the requested start is a weekend or
a holiday, and the price cache learned it the hard way (KNOWN_GAPS, "No
price cache for callers passing a date range"): four of nine assets refetched
their whole history on every call. Prices keep that record on
asset_fetch_metadata, keyed by asset; a currency pair has no asset, so it
gets its own table keyed by (base, quote), with the same two facts:

  base, quote        the pair, as in fx_rates: base per one unit of quote
  last_fetch_time    when the provider was last asked, for the interval rule
  earliest_start     how far back the provider has been asked

The two facts are nullable, as on asset_fetch_metadata: the row is created
before the first fetch and filled by it. Nothing about the rates themselves
lives here; those are fx_rates rows.

Two views of the same fact, both asserted, like test_fx_rates_schema.py.
The model's table definition, which is what the code sees, and the database
the suite runs against, which is what `alembic upgrade head` produces.
"""

import pytest
from sqlalchemy import Date, DateTime, inspect

import portfolio_tool.database_setup as models
from portfolio_tool.database_setup import Base, engine


TABLE = "fx_fetch_metadata"
KEY = ["base", "quote"]
FACTS = {"last_fetch_time", "earliest_start"}


# --- the model -------------------------------------------------------------

@pytest.fixture(scope="module")
def table():
    assert hasattr(models, "FxFetchMetadata"), "no FxFetchMetadata model in database_setup"
    assert TABLE in Base.metadata.tables
    return models.FxFetchMetadata.__table__


def test_model_has_the_columns(table):
    assert set(KEY) | FACTS <= set(table.c.keys())


def test_model_is_keyed_by_the_pair(table):
    assert sorted(c.name for c in table.primary_key.columns) == sorted(KEY)


@pytest.mark.parametrize("column", KEY)
def test_model_pair_column_is_required(table, column):
    assert table.c[column].nullable is False


@pytest.mark.parametrize("column", sorted(FACTS))
def test_model_fact_is_filled_by_the_fetch_not_defaulted(table, column):
    assert table.c[column].nullable is True
    assert table.c[column].default is None
    assert table.c[column].server_default is None


def test_model_fact_types(table):
    assert isinstance(table.c["last_fetch_time"].type, DateTime)
    assert isinstance(table.c["earliest_start"].type, Date)


# --- the database ----------------------------------------------------------

@pytest.fixture(scope="module")
def columns():
    inspector = inspect(engine)
    assert TABLE in inspector.get_table_names(), f"no {TABLE} table; run alembic upgrade head"
    return {c["name"]: c for c in inspector.get_columns(TABLE)}


def test_database_has_the_columns(columns):
    assert set(KEY) | FACTS <= set(columns)


def test_database_is_keyed_by_the_pair():
    assert sorted(inspect(engine).get_pk_constraint(TABLE)["constrained_columns"]) == sorted(KEY)


@pytest.mark.parametrize("column", KEY)
def test_database_pair_column_is_required(columns, column):
    assert columns[column]["nullable"] is False


@pytest.mark.parametrize("column", sorted(FACTS))
def test_database_fact_is_nullable_and_not_defaulted(columns, column):
    assert columns[column]["nullable"] is True
    assert columns[column]["default"] is None
