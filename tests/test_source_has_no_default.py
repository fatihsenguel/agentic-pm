"""
No table stamps a row with a provider nobody named.

`daily_prices.source` and `fx_rates.source` are required and defaulted
nowhere: a close or a rate whose origin is unknown is a claim nobody made.
The statement and macro tables carried the same column with a default of
the one provider the system has ever had, which no live writer used (both
pass the provider DTO's source) and which would stamp a row written
without one. Pending item 20 of the twelfth session's handoff: the
default is the repair shape, and it goes.

Two views, like test_daily_prices_schema.py: the model, and the database
the suite runs against. The database never had a server default on
either column, so no migration; this is a model change. The macro
column stays nullable here, which is a separate decision.
"""

import pytest
from sqlalchemy import inspect

from portfolio_tool.database_setup import FinancialStatement, MacroData, engine


CASES = [
    (FinancialStatement, "financial_statements"),
    (MacroData, "macro_data"),
]


@pytest.mark.parametrize("model, table", CASES, ids=[t for _, t in CASES])
def test_model_source_has_no_default(model, table):
    column = model.__table__.c["source"]
    assert column.default is None, f"{table}.source has a Python-side default"
    assert column.server_default is None


@pytest.mark.parametrize("model, table", CASES, ids=[t for _, t in CASES])
def test_database_source_has_no_default(model, table):
    columns = {c["name"]: c for c in inspect(engine).get_columns(table)}
    assert columns["source"]["default"] is None


@pytest.mark.parametrize("model, table", CASES, ids=[t for _, t in CASES])
def test_every_stored_row_names_its_source(model, table):
    """Both tables today hold one source on every row; recorded so a row
    without one is seen the day something writes it."""
    with engine.connect() as conn:
        missing = conn.exec_driver_sql(
            f"select count(*) from {table} where source is null or source = ''"
        ).scalar()
    assert missing == 0
