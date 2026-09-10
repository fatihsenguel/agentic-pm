"""
Every DTO the provider returns carries the provider's own name as source.

The price and rate rows write `provider.name`; the statement and macro
DTOs carried the literal "yfinance" typed at four sites in the provider,
which agrees with the name today and stops agreeing the day the name
changes or a second provider is built from this one. Pending item 20's
second half: one statement of the name, read everywhere it is written.

No network: the library is a stand-in whose `history` returns one close
and whose statement attributes return one period, the pattern of
test_price_source.py. The falsifier is a provider whose name is not
"yfinance": a literal would still say "yfinance" and fail here.
"""

import datetime

import pandas as pd
import pytest


DAY = datetime.date(2026, 8, 21)


class _LibraryTicker:
    """Stands in for yfinance.Ticker for what the four methods read."""

    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, start=None, end=None, **kwargs):
        return pd.DataFrame(
            {"Open": [1.0], "High": [1.0], "Low": [1.0], "Close": [17.25], "Volume": [1]},
            index=pd.DatetimeIndex([pd.Timestamp(DAY)]),
        )

    @property
    def _statement(self):
        # yfinance shape: index = line items, columns = period timestamps.
        return pd.DataFrame({pd.Timestamp(DAY): [100.0, 10.0]},
                            index=["Total Revenue", "Net Income"])

    financials = quarterly_financials = _statement
    balance_sheet = quarterly_balance_sheet = _statement
    cashflow = quarterly_cashflow = _statement


class _Library:
    Ticker = _LibraryTicker


class _NoQuota:
    def can_consume_credit(self):
        return True

    def log_api_call(self, **kwargs):
        return None


STAND_IN = "stand-in provider"


@pytest.fixture
def provider(monkeypatch):
    import portfolio_tool.providers.yfinance_provider as module
    monkeypatch.setattr(module, "yf", _Library)
    p = module.YFinanceProvider(quota_manager=_NoQuota())
    p.name = STAND_IN
    return p


def _sources(dtos):
    return {d.source for d in dtos}


def test_vix_rows_carry_the_providers_name(provider):
    rows = provider.get_vix_data(DAY, DAY + datetime.timedelta(days=1))
    assert rows and _sources(rows) == {STAND_IN}


def test_treasury_yield_rows_carry_the_providers_name(provider):
    by_name = provider.get_treasury_yields(DAY, DAY + datetime.timedelta(days=1))
    assert by_name
    for name, rows in by_name.items():
        assert rows and _sources(rows) == {STAND_IN}, name


def test_macro_indicator_rows_carry_the_providers_name(provider):
    rows = provider.get_macro_indicator("VIX", DAY, DAY + datetime.timedelta(days=1))
    assert rows and _sources(rows) == {STAND_IN}


@pytest.mark.xfail(
    strict=True,
    reason="get_financial_statements builds its DTO with 26 keyword arguments "
           "ProviderFinancialStatement does not have, raises inside, and its "
           "blanket except returns []; it has returned nothing on every call "
           "since the DTO lost those fields (KNOWN_GAPS). The site writes "
           "self.name; this pin turns red the day the method returns rows.",
)
@pytest.mark.parametrize("report_type", ["income", "balance_sheet", "cash_flow"])
@pytest.mark.parametrize("period_type", ["annual", "quarterly"])
def test_statement_rows_carry_the_providers_name(provider, report_type, period_type):
    rows = provider.get_financial_statements("JNJ", report_type, period_type)
    assert rows and _sources(rows) == {STAND_IN}


def test_the_macro_dto_requires_a_source():
    """The DTO carried a default of "yfinance" too; a row whose origin
    nobody stated cannot be built."""
    from portfolio_tool.provider_models import ProviderMacroData
    with pytest.raises(TypeError):
        ProviderMacroData(date=DAY, indicator="VIX", value=17.25)
