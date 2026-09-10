"""
A portfolio names its currency; nothing supplies one (expected_values.md D15).

Every figure the system reports for a portfolio is in `Portfolio.currency`:
the total, the allocation, the P&L, the compliance distances. A portfolio
created without one is therefore not a dollar portfolio with a plausible
face but an error, the way a ledger row without an amount is. The database
column has been NOT NULL with no server default all along; what supplied
the dollars was the model's Python-side default and the manager's
argument default, and both go.

Four views of the one rule: the model column has no default, the database
column has none and is required, the manager refuses a call that names no
currency, and a model row without one cannot be committed.
"""

import datetime

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from portfolio_tool.database_setup import Portfolio, engine, get_session
from portfolio_tool.portfolio_manager import PortfolioManager


NAME = "Currency Test Portfolio"


def _clear(session):
    session.query(Portfolio).filter(Portfolio.name == NAME).delete()
    session.commit()


def test_model_currency_has_no_default():
    column = Portfolio.__table__.c["currency"]
    assert column.nullable is False
    assert column.default is None
    assert column.server_default is None


def test_database_currency_is_required_and_has_no_default():
    columns = {c["name"]: c for c in inspect(engine).get_columns("portfolios")}
    assert columns["currency"]["nullable"] is False
    assert columns["currency"]["default"] is None


def test_manager_refuses_a_portfolio_with_no_currency():
    pm = PortfolioManager()
    with pytest.raises(TypeError):
        pm.create_portfolio(NAME)


def test_a_row_without_a_currency_cannot_be_committed():
    session = get_session()
    _clear(session)
    try:
        session.add(Portfolio(name=NAME, cash_balance=0.0,
                              created_at=datetime.datetime.utcnow(),
                              updated_at=datetime.datetime.utcnow()))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        _clear(session)
        session.close()
