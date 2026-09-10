"""
A portfolio names the policy it is checked against (DIRECTION.md Order 2,
item 4).

The policy belongs to the portfolio, not to the process: the benchmark
portfolio is scored against docs/IPS.md, and a personal portfolio in the
same database is checked against a personal policy that lives outside the
repository. `portfolios.ips_path` carries the path of that portfolio's
policy file - a relative path is anchored to the project root by the
loader, so the committed `ips.toml` is found from any directory, and an
absolute one names a file the repository never sees. Required and
defaulted nowhere, the way `currency` is: a portfolio with no policy is
not a portfolio checked against the committed one with a plausible face.

Two views of the one fact, both asserted, like test_daily_prices_schema.py:
the model's table definition, and the database the suite runs against, the
copy conftest.py makes of data/portfolio.db, which is what `alembic upgrade
head` produces. Before the migration is applied the second half fails on
the column not being there. The migration fills the one existing row,
portfolio 3, with `ips.toml`, the committed policy it has always been
checked against.
"""

import pytest
from sqlalchemy import String, inspect

from portfolio_tool.database_setup import Portfolio, engine


TABLE = "portfolios"
COLUMN = "ips_path"
COMMITTED = "ips.toml"


# --- the model -------------------------------------------------------------

def test_model_has_ips_path():
    assert COLUMN in Portfolio.__table__.c.keys()


def test_model_ips_path_is_required():
    assert Portfolio.__table__.c[COLUMN].nullable is False


def test_model_ips_path_has_no_default():
    column = Portfolio.__table__.c[COLUMN]
    assert column.default is None
    assert column.server_default is None


def test_model_ips_path_is_a_string():
    assert isinstance(Portfolio.__table__.c[COLUMN].type, String)


# --- the database ----------------------------------------------------------

@pytest.fixture(scope="module")
def columns():
    return {c["name"]: c for c in inspect(engine).get_columns(TABLE)}


def test_database_has_ips_path(columns):
    assert COLUMN in columns, f"no {COLUMN} column on {TABLE}; run alembic upgrade head"


def test_database_ips_path_is_required(columns):
    assert columns[COLUMN]["nullable"] is False


def test_database_ips_path_has_no_default(columns):
    assert columns[COLUMN]["default"] is None


def test_database_no_row_without_a_policy():
    with engine.connect() as conn:
        missing = conn.exec_driver_sql(
            f"select count(*) from {TABLE} where {COLUMN} is null or {COLUMN} = ''"
        ).scalar()
    assert missing == 0


def test_database_benchmark_portfolio_names_the_committed_policy():
    with engine.connect() as conn:
        path = conn.exec_driver_sql(
            f"select {COLUMN} from {TABLE} where id = 3"
        ).scalar()
    assert path == COMMITTED
