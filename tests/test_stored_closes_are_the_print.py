"""
The stored closes are the committed series, cell for cell (D19, D20, Part 9).

tests/golden/benchmark_closes.csv is the print on every one of Part 4's 252
dates for the nine holdings: Part 9 checked it against the exchange. The
database is what the provider stored, and the twelfth session found 1,629
of its 2,268 cells wrong by a dividend factor while every loop was green,
because nothing compared the two. This test does, on every run: every
cell of the series against the stored close for that ticker and date, to
the cent, one case per holding so a failure names it.

It is the falsifier for "the table holds one convention". It fails the day
a refetch stores an adjusted close again, which no other loop can see: the
schema test sees a source name, the price-source test sees a stand-in for
the library, the runner sees today's close only, and today's close agrees
with the print whether or not the history does (Part 9 A).

Runs against the copy conftest.py makes of data/portfolio.db, like every
schema test. A database that has not been refetched as traded fails here
and says which holding; a clone with no database is refused by conftest
before this file is reached. A stored date the series does not have is not
read; a series date the database lacks is a failure, since the window was
fetched in full.
"""

from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text

from portfolio_tool.database_setup import engine


CLOSES = Path(__file__).parent / "golden" / "benchmark_closes.csv"
HOLDINGS = ["SPY", "AAPL", "MSFT", "JNJ", "JPM", "NEE", "TLT", "GLD", "VNQ"]
DATES_IN_WINDOW = 252


@pytest.fixture(scope="module")
def series():
    frame = pd.read_csv(CLOSES, index_col="date")
    assert list(frame.columns) == HOLDINGS
    assert len(frame) == DATES_IN_WINDOW
    return frame


@pytest.fixture(scope="module")
def stored(series):
    """ticker -> {date: close} for the nine holdings over the series' window."""
    tickers = ", ".join(repr(t) for t in HOLDINGS)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "select a.ticker, p.date, p.close from daily_prices p "
                "join assets a on a.id = p.asset_id "
                f"where a.ticker in ({tickers}) and p.date between :first and :last"
            ),
            {"first": series.index[0], "last": series.index[-1]},
        ).fetchall()
    out = {t: {} for t in HOLDINGS}
    for ticker, date, close in rows:
        out[ticker][str(date)] = close
    return out


@pytest.mark.parametrize("ticker", HOLDINGS)
def test_every_stored_close_is_the_committed_print(series, stored, ticker):
    missing = [d for d in series.index if d not in stored[ticker]]
    assert not missing, f"{ticker}: {len(missing)} series dates with no stored close, first {missing[0]}"
    wrong = [
        (d, round(float(series.at[d, ticker]), 2), round(float(stored[ticker][d]), 2))
        for d in series.index
        if round(float(series.at[d, ticker]), 2) != round(float(stored[ticker][d]), 2)
    ]
    assert not wrong, (
        f"{ticker}: {len(wrong)} of {DATES_IN_WINDOW} stored closes differ from the "
        f"committed print (date, print, stored), first {wrong[0]}; "
        "the provider stored something other than the close as traded"
    )
