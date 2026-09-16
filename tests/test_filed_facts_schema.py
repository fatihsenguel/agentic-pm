"""
The filed_facts table: one row per filed fact, keyed by D26.

expected_values.md Part 12 and Part 13. A row is one figure as a filer filed
it, in one filing: the EDGAR provider's record (providers/edgar.py) as
stored. Nothing reads or writes the table at this revision.

Columns and what they mean:

  cik     the filer, by EDGAR number; a watchlist company has no assets row
  tag     the us-gaap tag
  unit    USD, shares, pure
  start   the period's first day; empty for an instant
  end     the period's last day, or the instant's date
  value   the figure as text, exactly the digits EDGAR sent; SQLite has no
          exact decimal type, and a float returns 0.241 as 0.24099999...
  accn    the filing's accession number
  fy, fp, frame   the filing's labels: provenance, never a key (D26, D31)
  form    the filing's form (D29)
  filed   the day the filing was filed
  source  the provider's name

Required and defaulted nowhere, like fx_rates: a figure with no filing, no
date or no source is a claim nobody made. `start`, `fy`, `fp` and `frame`
may be empty because EDGAR leaves them empty.

The key is D26's `(tag, start, end, accn)` per company. SQLite never treats
two empty values as equal inside a unique constraint, so a plain constraint
over those columns would accept one instant twice. The key is therefore two
partial unique indexes, one for instants and one for durations, and the
test for it inserts rows rather than reading the constraint list: a list
that names the right columns passes whether or not an instant can be stored
twice.

Two views, as in test_fx_rates_schema.py: the model's table, created in a
throwaway in-memory database, and the database the suite runs against - the
copy conftest.py makes of data/portfolio.db - which is what `alembic upgrade
head` produces. Before the migration is applied the second half fails on the
table not being there. Every insert into the copy is rolled back.

The database half owns its rows: inside its transaction it first removes
the two fixture companies' rows from the copy, since the fixtures are real
filed facts (Part 12 D F5, Part 13 D F6) and collide with the copy's real
rows on the unique index, and it reads back only what it wrote, by
`source = 'test'`. Until 16 September (twentieth session) it did neither
and passed only inside the full run, where an earlier test had cleared
Apple's rows from the copy: run alone it failed on the collision, and the
first second filer stored in the real database, Alphabet, made two
whole-table reads fail in the full run too.
"""

import datetime as dt

import pytest
from sqlalchemy import Date, Integer, Text, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

import portfolio_tool.database_setup as models
from portfolio_tool.database_setup import Base, engine


TABLE = "filed_facts"
REQUIRED = {"cik", "tag", "unit", "end", "value", "accn", "form", "filed", "source"}
OPTIONAL = {"start", "fy", "fp", "frame"}

INSERT = text(
    "INSERT INTO filed_facts (cik, tag, unit, start, \"end\", value, accn, fy, fp, "
    "form, filed, frame, source) VALUES (:cik, :tag, :unit, :start, :end, :value, "
    ":accn, :fy, :fp, :form, :filed, :frame, :source)"
)

# Part 12 section D, F5: an instant.
EQUITY = {"cik": 320193, "tag": "StockholdersEquity", "unit": "USD", "start": None,
          "end": dt.date(2024, 9, 28), "value": "56950000000",
          "accn": "0000320193-26-000020", "fy": 2026, "fp": "Q3", "form": "10-Q",
          "filed": dt.date(2026, 7, 31), "frame": "CY2024Q3I", "source": "test"}

# Part 13 section D, F6: two durations under one tag, end and filing.
HALF_YEAR = {"cik": 1652044, "tag": "OperatingIncomeLoss", "unit": "USD",
             "start": dt.date(2025, 1, 1), "end": dt.date(2025, 6, 30),
             "value": "61877000000", "accn": "0001652044-25-000062", "fy": 2025,
             "fp": "Q2", "form": "10-Q", "filed": dt.date(2025, 7, 24), "frame": None,
             "source": "test"}
QUARTER = dict(HALF_YEAR, start=dt.date(2025, 4, 1), value="31271000000", frame="CY2025Q2")


# --- the model -------------------------------------------------------------

@pytest.fixture(scope="module")
def table():
    assert hasattr(models, "FiledFact"), "no FiledFact model in database_setup"
    assert TABLE in Base.metadata.tables
    return models.FiledFact.__table__


def test_model_has_the_columns(table):
    assert REQUIRED | OPTIONAL <= set(table.c.keys())


@pytest.mark.parametrize("column", sorted(REQUIRED))
def test_model_column_is_required(table, column):
    assert table.c[column].nullable is False


@pytest.mark.parametrize("column", sorted(OPTIONAL))
def test_model_column_may_be_empty(table, column):
    assert table.c[column].nullable is True


@pytest.mark.parametrize("column", sorted(REQUIRED | OPTIONAL))
def test_model_column_has_no_default(table, column):
    assert table.c[column].default is None
    assert table.c[column].server_default is None


@pytest.mark.parametrize("column, kind", [
    ("cik", Integer), ("start", Date), ("end", Date), ("filed", Date), ("value", Text),
])
def test_model_column_type(table, column, kind):
    assert isinstance(table.c[column].type, kind)


@pytest.fixture
def model_db(table):
    scratch = create_engine("sqlite://")
    table.create(scratch)  # creates the table's indexes with it
    with scratch.connect() as conn:
        yield conn


# --- the database ----------------------------------------------------------

@pytest.fixture(scope="module")
def columns():
    inspector = inspect(engine)
    assert TABLE in inspector.get_table_names(), f"no {TABLE} table; run alembic upgrade head"
    return {c["name"]: c for c in inspector.get_columns(TABLE)}


def test_database_has_the_columns(columns):
    assert REQUIRED | OPTIONAL <= set(columns)


@pytest.mark.parametrize("column", sorted(REQUIRED))
def test_database_column_is_required(columns, column):
    assert columns[column]["nullable"] is False


@pytest.mark.parametrize("column", sorted(OPTIONAL))
def test_database_column_may_be_empty(columns, column):
    assert columns[column]["nullable"] is True


@pytest.mark.parametrize("column", sorted(REQUIRED | OPTIONAL))
def test_database_column_has_no_default(columns, column):
    assert columns[column]["default"] is None


@pytest.fixture
def suite_db(columns):
    """The suite's copy, inside one transaction that is rolled back: the two
    fixture companies' rows are removed first, so the fixtures, which are
    real filed facts, do not collide with the copy's real rows on the
    unique index, and the copy is left as it was."""
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            conn.execute(text("DELETE FROM filed_facts WHERE cik IN (:a, :b)"),
                         {"a": EQUITY["cik"], "b": HALF_YEAR["cik"]})
            yield conn
        finally:
            transaction.rollback()


# --- D26, on both ------------------------------------------------------------

@pytest.fixture(params=["model", "database"])
def db(request):
    return request.getfixturevalue("model_db" if request.param == "model" else "suite_db")


def test_one_instant_is_stored_once(db):
    db.execute(INSERT, EQUITY)
    with pytest.raises(IntegrityError):
        db.execute(INSERT, EQUITY)


def test_one_duration_is_stored_once(db):
    db.execute(INSERT, HALF_YEAR)
    with pytest.raises(IntegrityError):
        db.execute(INSERT, HALF_YEAR)


def test_f6_a_quarter_and_a_half_year_are_two_facts(db):
    db.execute(INSERT, HALF_YEAR)
    db.execute(INSERT, QUARTER)
    count = db.execute(text(
        "SELECT COUNT(*) FROM filed_facts WHERE tag = 'OperatingIncomeLoss' "
        "AND accn = '0001652044-25-000062'"
    )).scalar()
    assert count == 2


def test_a_restatement_is_a_second_row(db):
    db.execute(INSERT, EQUITY)
    db.execute(INSERT, dict(EQUITY, accn="0000320193-25-000079", value="56950000000",
                            form="10-K", filed=dt.date(2025, 10, 31)))
    count = db.execute(text(
        "SELECT COUNT(*) FROM filed_facts WHERE tag = 'StockholdersEquity' AND source = 'test'"
    )).scalar()
    assert count == 2


def test_the_value_comes_back_as_filed(db):
    db.execute(INSERT, dict(EQUITY, tag="EffectiveIncomeTaxRateContinuingOperations",
                            unit="pure", value="0.241"))
    stored = db.execute(text(
        "SELECT value FROM filed_facts WHERE tag = 'EffectiveIncomeTaxRateContinuingOperations' "
        "AND source = 'test'"
    )).scalar()
    assert stored == "0.241"
