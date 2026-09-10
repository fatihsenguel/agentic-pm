"""
A portfolio names the policy it is checked against; nothing supplies one
(DIRECTION.md Order 2, item 4).

The column is held to the schema by test_portfolio_ips_path_schema.py.
This file holds the manager and the model to it, the way
test_portfolio_currency.py holds them to the currency: the manager refuses
a call that names no policy file, projects the path it stored, and a model
row without one cannot be committed. The benchmark portfolio's path is the
committed `ips.toml`; a personal portfolio's is a file outside the
repository, and the manager does not care which.
"""

import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from portfolio_tool.database_setup import Portfolio, engine, get_session
from portfolio_tool.portfolio_manager import PortfolioManager


NAME = "Policy Path Test Portfolio"
COMMITTED = "ips.toml"
PERSONAL = "/somewhere/outside/the/repository/ips.toml"


def _clear(session):
    session.query(Portfolio).filter(Portfolio.name == NAME).delete()
    session.commit()


@pytest.fixture(autouse=True)
def clean():
    session = get_session()
    _clear(session)
    yield
    _clear(session)
    session.close()


def test_manager_refuses_a_portfolio_with_no_policy_path():
    pm = PortfolioManager()
    with pytest.raises(TypeError):
        pm.create_portfolio(NAME, currency="USD")


@pytest.mark.parametrize("path", [COMMITTED, PERSONAL])
def test_manager_stores_and_projects_the_policy_path(path):
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio(NAME, currency="USD", ips_path=path)
    assert pm.get_portfolio(portfolio_id)["ips_path"] == path


def test_a_row_without_a_policy_path_cannot_be_committed():
    session = get_session()
    try:
        session.add(Portfolio(name=NAME, currency="USD", cash_balance=0.0,
                              created_at=datetime.datetime.utcnow(),
                              updated_at=datetime.datetime.utcnow()))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()
