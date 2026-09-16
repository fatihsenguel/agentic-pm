"""
The ticker_ciks table: the SEC's ticker file as stored, one row per
(ticker, CIK) pair.

Decision 29, question 50: a ticker becomes a CIK through the SEC's
published ticker file, fetched by EdgarProvider.tickers and stored under
the filings fetch interval. The file is one document for every listed
filer, so a refresh rewrites the whole table as the file now states it and
moves every row's date; a ticker the file no longer carries leaves the
table with the refresh. Columns:

  ticker     the ticker as the file states it; the key, since the provider
             refuses a file in which one ticker names two filers
  cik        the filer, by EDGAR number, as on filed_facts and filers
  pulled_at  when the provider last returned the file

Every column is required and defaulted nowhere: a row is written only after
a fetch has returned, and a pair without either half is not a pair. The
file's company title is not stored; nothing consumes it.

Two views, as in test_filers_schema.py: the model's table and the database
the suite runs against, which is what `alembic upgrade head` produces.
Before the migration is applied the second half fails on the table not
being there.
"""

import pytest
from sqlalchemy import DateTime, Integer, String, inspect

import portfolio_tool.database_setup as models
from portfolio_tool.database_setup import Base, engine


TABLE = "ticker_ciks"
KEY = ["ticker"]
REQUIRED = {"cik", "pulled_at"}
COLUMNS = set(KEY) | REQUIRED


# --- the model -------------------------------------------------------------

@pytest.fixture(scope="module")
def table():
    assert hasattr(models, "TickerCik"), "no TickerCik model in database_setup"
    assert TABLE in Base.metadata.tables
    return models.TickerCik.__table__


def test_model_has_exactly_the_columns(table):
    assert set(table.c.keys()) == COLUMNS


def test_model_is_keyed_by_the_ticker(table):
    assert [c.name for c in table.primary_key.columns] == KEY


def test_model_column_types(table):
    assert isinstance(table.c["ticker"].type, String)
    assert isinstance(table.c["cik"].type, Integer)
    assert isinstance(table.c["pulled_at"].type, DateTime)


@pytest.mark.parametrize("column", sorted(COLUMNS))
def test_model_column_is_required_and_not_defaulted(table, column):
    assert table.c[column].nullable is False
    assert table.c[column].default is None
    assert table.c[column].server_default is None


# --- the database ----------------------------------------------------------

@pytest.fixture(scope="module")
def columns():
    inspector = inspect(engine)
    assert TABLE in inspector.get_table_names(), f"no {TABLE} table; run alembic upgrade head"
    return {c["name"]: c for c in inspector.get_columns(TABLE)}


def test_database_has_exactly_the_columns(columns):
    assert set(columns) == COLUMNS


def test_database_is_keyed_by_the_ticker():
    assert inspect(engine).get_pk_constraint(TABLE)["constrained_columns"] == KEY


@pytest.mark.parametrize("column", sorted(COLUMNS))
def test_database_column_is_required_and_not_defaulted(columns, column):
    assert columns[column]["nullable"] is False
    assert columns[column]["default"] is None
