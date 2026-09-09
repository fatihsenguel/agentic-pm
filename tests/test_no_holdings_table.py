"""
There is no holdings table: holdings are a view of the ledger (D13).

Asserted twice, like test_transactions_schema.py: on the models, which is
what the code sees, and on the database the suite runs against, which is
what `alembic upgrade head` produces. Before the migration is applied the
second half fails on the table still being there.
"""

import pytest
from sqlalchemy import inspect

import portfolio_tool.database_setup as models
from portfolio_tool.database_setup import Base, Portfolio, engine


def test_model_has_no_portfolio_holding():
    assert not hasattr(models, "PortfolioHolding")
    assert "portfolio_holdings" not in Base.metadata.tables


def test_portfolio_has_no_holdings_relationship():
    assert "holdings" not in Portfolio.__mapper__.relationships


def test_database_has_no_holdings_table():
    assert "portfolio_holdings" not in inspect(engine).get_table_names()
