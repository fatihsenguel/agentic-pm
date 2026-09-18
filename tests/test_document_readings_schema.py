"""
The document_readings table: one reading of one section of a stored
document, as the model supplied it and as `reading.record` accepted it.

expected_values.md Part 15, D47: a reading is cached per accession,
section, model and prompt version, and a reading that was refused is not
cached. Columns:

  accn            the accession, a filed_documents row
  section         Item 1, Item 1A or Item 7
  model           the model's id, which the record keeps (decision 67)
  prompt_version  the version of the section's fixed prompt
  claims          JSON text: the one to twelve entries of claim, quote and
                  uncertainty; read and written whole, and passed through
                  `reading.record` again on a hit, against the stored
                  section

The first four are the key. Every column is required and defaulted
nowhere. When a reading was made and what it cost are not stored; nothing
consumes them.

Two views, as in test_ticker_ciks_schema.py: the model's table and the
database the suite runs against, which is what `alembic upgrade head`
produces. Before the migration is applied the second half fails on the
table not being there.
"""

import pytest
from sqlalchemy import String, Text, inspect

import portfolio_tool.database_setup as models
from portfolio_tool.database_setup import Base, engine


TABLE = "document_readings"
KEY = ["accn", "section", "model", "prompt_version"]
REQUIRED = {"claims"}
COLUMNS = set(KEY) | REQUIRED
PARENT = ("filed_documents", ["accn"])


# --- the model -------------------------------------------------------------

@pytest.fixture(scope="module")
def table():
    assert hasattr(models, "DocumentReading"), "no DocumentReading model in database_setup"
    assert TABLE in Base.metadata.tables
    return models.DocumentReading.__table__


def test_model_has_exactly_the_columns(table):
    assert set(table.c.keys()) == COLUMNS


def test_model_is_keyed_by_accession_section_model_and_prompt_version(table):
    assert [c.name for c in table.primary_key.columns] == KEY


def test_model_column_types(table):
    for column in KEY:
        assert isinstance(table.c[column].type, String)
    assert isinstance(table.c["claims"].type, Text)


def test_model_accession_is_a_stored_document(table):
    targets = [(fk.column.table.name, [fk.column.name]) for fk in table.c["accn"].foreign_keys]
    assert targets == [PARENT]


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


def test_database_is_keyed_by_accession_section_model_and_prompt_version():
    assert inspect(engine).get_pk_constraint(TABLE)["constrained_columns"] == KEY


def test_database_accession_is_a_stored_document():
    keys = inspect(engine).get_foreign_keys(TABLE)
    assert [(k["referred_table"], k["referred_columns"]) for k in keys] == [PARENT]
    assert [k["constrained_columns"] for k in keys] == [["accn"]]


@pytest.mark.parametrize("column", sorted(COLUMNS))
def test_database_column_is_required_and_not_defaulted(columns, column):
    assert columns[column]["nullable"] is False
    assert columns[column]["default"] is None
