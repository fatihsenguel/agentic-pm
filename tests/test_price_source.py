"""
The price source, against expected_values.md Part 9 (D19, D20).

D19: a close is the exchange's official closing price on that date, as
traded, adjusted for splits and for nothing else. D20: when two sources
disagree, the exchange's print wins; nothing averages and the reference
does not move.

Two things are held here.

  1. The committed series (tests/golden/benchmark_closes.csv, Part 4's 252
     closes) is the print on the dates Part 9 checked against the exchange:
     the nine 2026-09-02 closes and the two falsifier rows before a
     dividend. This is documents against documents, the Part 8 A shape; it
     exists so that the series can never be "refreshed" from a provider
     that adjusts, and pass.

  2. The provider returns the print. Yahoo's library replaces the close
     with the dividend-adjusted close unless asked not to, and the stub
     below does exactly what the library's default does, so the test fails
     on a provider that takes the default and passes on one that asks for
     the unadjusted close. No network; the figures are Part 9 B's JNJ row.

Nothing here asserts that a stored row carries its source; that is the
schema test's.
"""

import datetime
from pathlib import Path

import pandas as pd
import pytest


CLOSES = Path(__file__).parent / "golden" / "benchmark_closes.csv"

# Part 9 A: the exchange's 2026-09-02 closes, nine of nine agreeing with Part 1.
PART_9_A = {
    "SPY": 765.16, "AAPL": 324.96, "MSFT": 496.82, "JNJ": 275.21, "JPM": 356.22,
    "NEE": 83.10, "TLT": 81.95, "GLD": 402.78, "VNQ": 95.78,
}
VALUATION_DATE = "2026-09-02"

# Part 9 B: dates before a dividend, where the adjusted close and the print differ.
PART_9_B = [("JNJ", "2026-08-21", 270.24), ("TLT", "2026-08-28", 82.88)]


def _cents(x):
    return round(float(x), 2)


# --- 1. the committed series is the print --------------------------------

@pytest.fixture(scope="module")
def series():
    return pd.read_csv(CLOSES, index_col="date")


@pytest.mark.parametrize("ticker", sorted(PART_9_A))
def test_committed_series_holds_the_print_on_the_valuation_date(series, ticker):
    assert _cents(series.at[VALUATION_DATE, ticker]) == PART_9_A[ticker]


@pytest.mark.parametrize("ticker,day,print_", PART_9_B)
def test_committed_series_holds_the_print_before_a_dividend(series, ticker, day, print_):
    assert _cents(series.at[day, ticker]) == print_


# --- 2. the provider returns the print -----------------------------------

PRINT = 270.24        # JNJ 2026-08-21, the exchange (Part 9 B)
ADJUSTED = 268.91     # the same row after the library's dividend adjustment
DAY = datetime.date(2026, 8, 21)


class _LibraryTicker:
    """Stands in for yfinance.Ticker. `history` does what the library's
    documented default does: unless auto_adjust is False, the Close column
    is replaced by the dividend-adjusted close and Adj Close is dropped."""

    calls = []

    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, start=None, end=None, auto_adjust=True, **kwargs):
        _LibraryTicker.calls.append({"start": start, "end": end, "auto_adjust": auto_adjust})
        frame = pd.DataFrame(
            {"Open": [269.50], "High": [271.00], "Low": [269.00],
             "Close": [PRINT], "Adj Close": [ADJUSTED], "Volume": [1_000_000]},
            index=pd.DatetimeIndex([pd.Timestamp(DAY)]),
        )
        if auto_adjust:
            frame["Close"] = frame["Adj Close"]
            frame = frame.drop(columns=["Adj Close"])
        return frame


class _Library:
    Ticker = _LibraryTicker


class _NoQuota:
    """A quota manager that always allows the call and records nothing."""

    def can_consume_credit(self):
        return True

    def log_api_call(self, **kwargs):
        return None


@pytest.fixture
def provider(monkeypatch):
    import portfolio_tool.providers.yfinance_provider as module
    monkeypatch.setattr(module, "yf", _Library)
    _LibraryTicker.calls.clear()
    return module.YFinanceProvider(quota_manager=_NoQuota())


def test_provider_returns_the_print_not_the_adjusted_close(provider):
    rows = provider.get_daily_prices("JNJ", DAY, DAY + datetime.timedelta(days=1))
    assert [r.date for r in rows] == [DAY]
    assert _cents(rows[0].close) == PRINT, (
        f"provider returned {rows[0].close}, the dividend-adjusted close; "
        f"D19 says a close is the print, {PRINT}")


def test_provider_asks_the_library_for_the_unadjusted_close(provider):
    provider.get_daily_prices("JNJ", DAY, DAY + datetime.timedelta(days=1))
    assert _LibraryTicker.calls and _LibraryTicker.calls[0]["auto_adjust"] is False
