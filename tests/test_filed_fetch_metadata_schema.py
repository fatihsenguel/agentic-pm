"""
The filed_fetch_metadata table: the filings fetch's cache record, per company.

One company-facts document is the company's whole history, so there is no
"how far back have we asked" to keep, the fact fx_fetch_metadata needs. What
is left is when the company was last fetched, for the interval rule
(filings_fetch_interval_days in config.toml), and that date is also the pull
date an answer states:

  cik              the filer, by EDGAR number, as on filed_facts
  last_fetch_time  when the provider last returned the document

Unlike fx_fetch_metadata, the time is required and defaulted nowhere. That
record is created before its first fetch and filled by it; this one is
written only after a fetch has returned, so an empty time would stand for
nothing, and a fetch that fails leaves no record and is retried.

Two views, as in test_fx_fetch_metadata_schema.py: the model's table and the
database the suite runs against, which is what `alembic upgrade head`
produces. Before the migration is applied the second half fails on the
table not being there.
"""

import pytest
from sqlalchemy import DateTime, Integer, inspect

import portfolio_tool.database_setup as models
from portfolio_tool.database_setup import Base, engine


TABLE = "filed_fetch_metadata"
KEY = ["cik"]
FACTS = {"last_fetch_time"}


# --- the model -------------------------------------------------------------

@pytest.fixture(scope="module")
def table():
    assert hasattr(models, "FiledFetchMetadata"), "no FiledFetchMetadata model in database_setup"
    assert TABLE in Base.metadata.tables
    return models.FiledFetchMetadata.__table__


def test_model_has_the_columns(table):
    assert set(KEY) | FACTS <= set(table.c.keys())


def test_model_is_keyed_by_the_company(table):
    assert [c.name for c in table.primary_key.columns] == KEY


def test_model_column_types(table):
    assert isinstance(table.c["cik"].type, Integer)
    assert isinstance(table.c["last_fetch_time"].type, DateTime)


@pytest.mark.parametrize("column", sorted(set(KEY) | FACTS))
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


def test_database_has_the_columns(columns):
    assert set(KEY) | FACTS <= set(columns)


def test_database_is_keyed_by_the_company():
    assert inspect(engine).get_pk_constraint(TABLE)["constrained_columns"] == KEY


@pytest.mark.parametrize("column", sorted(set(KEY) | FACTS))
def test_database_column_is_required_and_not_defaulted(columns, column):
    assert columns[column]["nullable"] is False
    assert columns[column]["default"] is None
