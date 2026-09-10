"""
The daily_prices table carries the source of every close (D17, D19, Part 9).

A rate row already names where it came from (fx_rates.source); a close did
not, and a close whose origin is unknown is a claim nobody made. `source`
is the provider's name, written by the fetch, required and defaulted
nowhere, the way fx_rates has it. It is the trace a defended price needs:
when a stored close and the exchange's print disagree, the row says which
provider to look at.

Two views of the same fact, both asserted, like test_fx_rates_schema.py.
The model's table definition, which is what the code sees, and the database
the suite runs against - the copy conftest.py makes of data/portfolio.db -
which is what `alembic upgrade head` produces. Before the migration is
applied the second half fails on the column not being there.
"""

import pytest
from sqlalchemy import String, inspect

from portfolio_tool.database_setup import DailyPrice, engine


TABLE = "daily_prices"
COLUMN = "source"


# --- the model -------------------------------------------------------------

def test_model_has_source():
    assert COLUMN in DailyPrice.__table__.c.keys()


def test_model_source_is_required():
    assert DailyPrice.__table__.c[COLUMN].nullable is False


def test_model_source_has_no_default():
    column = DailyPrice.__table__.c[COLUMN]
    assert column.default is None
    assert column.server_default is None


def test_model_source_is_a_string():
    assert isinstance(DailyPrice.__table__.c[COLUMN].type, String)


# --- the database ----------------------------------------------------------

@pytest.fixture(scope="module")
def columns():
    return {c["name"]: c for c in inspect(engine).get_columns(TABLE)}


def test_database_has_source(columns):
    assert COLUMN in columns, f"no {COLUMN} column on {TABLE}; run alembic upgrade head"


def test_database_source_is_required(columns):
    assert columns[COLUMN]["nullable"] is False


def test_database_source_has_no_default(columns):
    assert columns[COLUMN]["default"] is None


def test_database_no_row_without_a_source():
    with engine.connect() as conn:
        missing = conn.exec_driver_sql(
            f"select count(*) from {TABLE} where {COLUMN} is null or {COLUMN} = ''"
        ).scalar()
    assert missing == 0
