"""
The filers table: one filer as EDGAR's submissions document states it.

expected_values.md Part 13 C. The SIC code is in the submissions document
and not in company facts, so it is a second fetch with its own record; the
document carries the current code only, no date and no history, so the row
carries the pull date, and a later pull that finds another code overwrites
the row and moves the date (decision 49). Columns:

  cik              the filer, by EDGAR number, as on filed_facts
  name             the filer's name as the document states it
  sic              the four-digit code, empty where EDGAR states none
  sic_description  the code's description, empty where EDGAR states none
  pulled_at        when the provider last returned the document

`name` and `pulled_at` are required and defaulted nowhere: a row is written
only after a fetch has returned. `sic` and `sic_description` may be empty
because EDGAR leaves them empty for some filers, and the screen stops on a
block whose code is empty (D35) rather than the store refusing the fact.
Not stored: `entityType`, `ownerOrg`, `fiscalYearEnd`; nothing consumes them.

Two views, as in test_filed_fetch_metadata_schema.py: the model's table and
the database the suite runs against, which is what `alembic upgrade head`
produces. Before the migration is applied the second half fails on the
table not being there.
"""

import pytest
from sqlalchemy import DateTime, Integer, String, inspect

import portfolio_tool.database_setup as models
from portfolio_tool.database_setup import Base, engine


TABLE = "filers"
KEY = ["cik"]
REQUIRED = {"name", "pulled_at"}
OPTIONAL = {"sic", "sic_description"}
COLUMNS = set(KEY) | REQUIRED | OPTIONAL


# --- the model -------------------------------------------------------------

@pytest.fixture(scope="module")
def table():
    assert hasattr(models, "Filer"), "no Filer model in database_setup"
    assert TABLE in Base.metadata.tables
    return models.Filer.__table__


def test_model_has_exactly_the_columns(table):
    assert set(table.c.keys()) == COLUMNS


def test_model_is_keyed_by_the_company(table):
    assert [c.name for c in table.primary_key.columns] == KEY


def test_model_column_types(table):
    assert isinstance(table.c["cik"].type, Integer)
    assert isinstance(table.c["name"].type, String)
    assert isinstance(table.c["sic"].type, String)
    assert isinstance(table.c["sic_description"].type, String)
    assert isinstance(table.c["pulled_at"].type, DateTime)


@pytest.mark.parametrize("column", sorted(set(KEY) | REQUIRED))
def test_model_column_is_required_and_not_defaulted(table, column):
    assert table.c[column].nullable is False
    assert table.c[column].default is None
    assert table.c[column].server_default is None


@pytest.mark.parametrize("column", sorted(OPTIONAL))
def test_model_column_may_be_empty_and_is_not_defaulted(table, column):
    assert table.c[column].nullable is True
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


def test_database_is_keyed_by_the_company():
    assert inspect(engine).get_pk_constraint(TABLE)["constrained_columns"] == KEY


@pytest.mark.parametrize("column", sorted(set(KEY) | REQUIRED))
def test_database_column_is_required_and_not_defaulted(columns, column):
    assert columns[column]["nullable"] is False
    assert columns[column]["default"] is None


@pytest.mark.parametrize("column", sorted(OPTIONAL))
def test_database_column_may_be_empty_and_is_not_defaulted(columns, column):
    assert columns[column]["nullable"] is True
    assert columns[column]["default"] is None
