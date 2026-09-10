"""
The macro_data table carries the source of every row, required.

The last of the source columns to become required: fx_rates and
daily_prices already refuse a row that does not name its provider. The
macro column had its Python default dropped in the thirteenth session and
stayed nullable in the database as its own decision; this is that decision
taken (handoff item 25). A row whose origin is unknown is a claim nobody
made, and a column that admits one will eventually store one.

Two views of the same fact, both asserted, like test_daily_prices_schema.py.
The model's table definition, which is what the code sees, and the database
the suite runs against - the copy conftest.py makes of data/portfolio.db -
which is what `alembic upgrade head` produces. Before the migration is
applied the "required" half fails on the column still being nullable.
"""

import pytest
from sqlalchemy import String, inspect

from portfolio_tool.database_setup import MacroData, engine


TABLE = "macro_data"
COLUMN = "source"


# --- the model -------------------------------------------------------------

def test_model_has_source():
    assert COLUMN in MacroData.__table__.c.keys()


def test_model_source_is_required():
    assert MacroData.__table__.c[COLUMN].nullable is False


def test_model_source_has_no_default():
    column = MacroData.__table__.c[COLUMN]
    assert column.default is None
    assert column.server_default is None


def test_model_source_is_a_string():
    assert isinstance(MacroData.__table__.c[COLUMN].type, String)


# --- the database ----------------------------------------------------------

@pytest.fixture(scope="module")
def columns():
    return {c["name"]: c for c in inspect(engine).get_columns(TABLE)}


def test_database_has_source(columns):
    assert COLUMN in columns, f"no {COLUMN} column on {TABLE}"


def test_database_source_is_required(columns):
    assert columns[COLUMN]["nullable"] is False, "run alembic upgrade head"


def test_database_source_has_no_default(columns):
    assert columns[COLUMN]["default"] is None


def test_database_no_row_without_a_source():
    with engine.connect() as conn:
        missing = conn.exec_driver_sql(
            f"select count(*) from {TABLE} where {COLUMN} is null or {COLUMN} = ''"
        ).scalar()
    assert missing == 0
