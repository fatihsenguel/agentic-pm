"""
The filed_documents table: one filing's primary document as text, one row
per accession, written once.

expected_values.md Part 16, D51: the text is what the standard library's
parser yields from the document, the whole of it and not its sections, so
the sectioner runs at read time and a change to it needs no fetch. An
accession never changes, so there is no interval and no pull date. Columns:

  accn    the accession, the key; the same accession filed_facts carries,
          which is how a filing's document is found from its figures
  text    the document's text under D51; read by the sectioner, published
          nowhere
  source  the provider's name, the source a reading record states (Part
          15 D47)

Every column is required and defaulted nowhere: a row is written only after
a fetch has returned and the text has been extracted. The filer, the form,
the filed date and the file's name are not stored: filed_facts names the
filing, and nothing consumes the file's name once the text is here.

Two views, as in test_ticker_ciks_schema.py: the model's table and the
database the suite runs against, which is what `alembic upgrade head`
produces. Before the migration is applied the second half fails on the
table not being there.
"""

import pytest
from sqlalchemy import String, Text, inspect

import portfolio_tool.database_setup as models
from portfolio_tool.database_setup import Base, engine


TABLE = "filed_documents"
KEY = ["accn"]
REQUIRED = {"text", "source"}
COLUMNS = set(KEY) | REQUIRED


# --- the model -------------------------------------------------------------

@pytest.fixture(scope="module")
def table():
    assert hasattr(models, "FiledDocument"), "no FiledDocument model in database_setup"
    assert TABLE in Base.metadata.tables
    return models.FiledDocument.__table__


def test_model_has_exactly_the_columns(table):
    assert set(table.c.keys()) == COLUMNS


def test_model_is_keyed_by_the_accession(table):
    assert [c.name for c in table.primary_key.columns] == KEY


def test_model_column_types(table):
    assert isinstance(table.c["accn"].type, String)
    assert isinstance(table.c["text"].type, Text)
    assert isinstance(table.c["source"].type, String)


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


def test_database_is_keyed_by_the_accession():
    assert inspect(engine).get_pk_constraint(TABLE)["constrained_columns"] == KEY


@pytest.mark.parametrize("column", sorted(COLUMNS))
def test_database_column_is_required_and_not_defaulted(columns, column):
    assert columns[column]["nullable"] is False
    assert columns[column]["default"] is None
