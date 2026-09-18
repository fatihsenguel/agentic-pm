"""
The candidate's stored closes are the exchange's print (Part 9 C, D19, D20;
decision 57).

Part 9 C checked GOOGL's closes for 10 to 16 September 2026 against the
exchange by hand, before the node stored one. The node stores the last
close for a candidate through the same provider as the holdings' closes,
on an assets row it creates, and this test holds what it stored to the
row, cell for cell, the way test_stored_closes_are_the_print.py holds the
holdings' closes to the committed series. It is the falsifier for "the
candidate's close is the print": a refetch that stores an adjusted close,
or a provider that returns something other than the close as traded for
a ticker nothing held, fails here and names the date.

Runs against conftest's copy of data/portfolio.db. A database in which
the node has not yet stored GOOGL's closes fails here naming the missing
dates, as a schema test fails between its commit and the migration; the
node's own test stands a provider in and cannot see the live figure. A
stored date the row does not cover, the 18th onward, is not read: the
reference covers what was checked by hand, and a later close gets its
row before it is trusted.
"""

import datetime as dt

import pytest
from sqlalchemy import text

from portfolio_tool.database_setup import engine


CANDIDATE = "GOOGL"
# Part 9 C, the exchange's Close/Last; the 17th's row added 2026-09-18.
PART_9_C = {
    dt.date(2026, 9, 10): 332.60,
    dt.date(2026, 9, 11): 338.50,
    dt.date(2026, 9, 14): 349.39,
    dt.date(2026, 9, 15): 344.98,
    dt.date(2026, 9, 16): 342.87,
    dt.date(2026, 9, 17): 347.33,
}


@pytest.fixture(scope="module")
def stored():
    with engine.connect() as conn:
        rows = conn.execute(
            text("select p.date, p.close, p.source from daily_prices p "
                 "join assets a on a.id = p.asset_id "
                 "where a.ticker = :ticker and p.date between :first and :last"),
            {"ticker": CANDIDATE, "first": min(PART_9_C), "last": max(PART_9_C)},
        ).fetchall()
    return {dt.date.fromisoformat(str(date)): (close, source) for date, close, source in rows}


def test_the_candidates_row_carries_no_holding_fields():
    """Decision 57: the row the node creates carries the ticker, EDGAR's
    name and the watchlist entry's currency, and no asset class, sector or
    instrument type, since nothing reads them on a company not held."""
    with engine.connect() as conn:
        row = conn.execute(
            text("select name, currency, asset_class, sector, instrument_type from assets "
                 "where ticker = :ticker"), {"ticker": CANDIDATE}).fetchone()
    assert row is not None, f"no assets row for {CANDIDATE}; the node has not stored a close"
    name, currency, asset_class, sector, instrument_type = row
    assert (currency, asset_class, sector, instrument_type) == ("USD", None, None, None)
    assert name == "Alphabet Inc."


def test_every_stored_close_on_a_part_9_c_date_is_the_print(stored):
    missing = [d for d in PART_9_C if d not in stored]
    assert not missing, f"{CANDIDATE}: no stored close on {missing}; Part 9 C covers them"
    wrong = [(d, PART_9_C[d], round(float(stored[d][0]), 2))
             for d in PART_9_C if round(float(stored[d][0]), 2) != PART_9_C[d]]
    assert not wrong, (f"{CANDIDATE}: stored closes differ from the exchange's print "
                       f"(date, print, stored): {wrong}")


def test_every_stored_close_names_its_source(stored):
    assert {source for _, source in stored.values()} == {"yfinance"}
