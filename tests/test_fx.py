"""
The currency arithmetic checked against tests/golden/expected_values.md Part 8 C.

Every expected number here is copied from that document, which was computed by
hand before any FX code existed (decisions D15 to D18). If a test fails, one
of the two is wrong and that gets resolved deliberately. Do NOT update these
figures to match code output.

Pure, like test_ledger.py: one ledger row, one price, one stated rate, no
database. The position is synthetic - 100 AAPL in a euro portfolio - and every
rate is stated and synthetic; nothing here is a market rate.

  D15  The base currency is the portfolio's. Every figure reported for a
       portfolio is in it.
  D16  A price is in the asset's currency. A foreign holding's value in the
       base currency is quantity x price x the spot rate on the price's as-of
       date, and both dates are stated.
  D17  A spot rate is a price source: per day, dated. A missing rate raises;
       nothing falls back to yesterday's rate or to 1. When the two currencies
       are the same there is no lookup.
  D18  Cost basis, average price and realized gain are in the base currency,
       because they come from `amount` (D14). The average of a foreign holding
       is therefore not comparable to its quoted price.

The rate convention, pinned here because the reference states it: a rate is
units of BASE currency per one unit of the ASSET's currency, so Part 8 C's
"0.9200 EUR/USD" is euros per dollar and market value = quantity x price x
rate. The table `spot_rates` reads is keyed by the asset's currency under a
given base: {"USD": {"2026-09-02": 0.85}} means 0.85 euros per dollar on that
date when the base is EUR.

What this file cannot see: the rate table, its migration, and the fetch are
step 2; the node publishing both dates is step 3; the formatters naming
currencies are step 4. Portfolio 3 is USD throughout, so the same-currency
test below is the pin that the runner does not move.
"""

from dataclasses import asdict

import pytest

from portfolio_tool.quant.allocation import AllocationError, position_pnl
from portfolio_tool.quant.ledger import derive_holdings


@pytest.fixture
def fx():
    """The module under test, imported per test rather than at collection.

    An import at module level would be a collection error, and pytest stops
    the whole run on one. Importing here makes each of these tests fail on
    its own for the honest reason while the rest of the suite still runs.
    """
    from portfolio_tool.quant import fx as module
    return module


PORTFOLIO = 7          # synthetic; not portfolio 3
BASE = "EUR"           # D15
PRICE_AS_OF = "2026-09-02"
CENT = 0.005

# expected_values.md Part 8 C, the one row: 100 AAPL at 200.00 USD, at a
# stated 0.9200 with 5.00 EUR fees. The amount is the settled euro figure
# (D14); the rate on the row is shown in the reference and not stored.
PART_8_C_ROW = {
    "portfolio_id": PORTFOLIO,
    "date": "2024-02-20",
    "type": "buy",
    "ticker": "AAPL",
    "quantity": 100,
    "price": 200.00,
    "fees": 5.00,
    "amount": 18_405.00,
}
ROW_RATE = 0.9200

# Part 8 C valuation: the 2026-09-02 close (Part 1) and a stated spot on the
# same date (D17).
AAPL_CLOSE_USD = 324.96
SPOT = {"USD": {PRICE_AS_OF: 0.8500}}

# expected_values.md Part 8 A, AAPL's row, for the same-currency contrast
# Part 8 C draws: 200 @ 200.00 USD, 40,000.00, and at the 09-02 close
# 64,992.00, +24,992.00, +62.48% (Part 1).
PART_8_A_AAPL_ROW = {
    "portfolio_id": 3,
    "date": "2024-02-20",
    "type": "buy",
    "ticker": "AAPL",
    "quantity": 200,
    "price": 200.00,
    "fees": 0.00,
    "amount": 40_000.00,
}


def euro_holdings(currency="USD"):
    """The Part 8 C position as the holding row the analysis reads: the
    derived holding plus the asset's currency (D16), which get_holdings
    joins from Asset.currency."""
    h = derive_holdings([PART_8_C_ROW])["AAPL"]
    return [{**asdict(h), "currency": currency}]


def usd_holdings():
    h = derive_holdings([PART_8_A_AAPL_ROW])["AAPL"]
    return [{**asdict(h), "currency": "USD"}]


# ---------------------------------------------------------------------------
# The position after the row (D13, D18): in euros
# ---------------------------------------------------------------------------

def test_part_8_c_row_derives_the_euro_position():
    """100 @ 184.05 EUR, cost basis 18,405.00 EUR, bought 2024-02-20."""
    h = derive_holdings([PART_8_C_ROW])["AAPL"]
    assert h.quantity == 100
    assert h.average_price == pytest.approx(184.05, abs=CENT)
    assert h.cost_basis == pytest.approx(18_405.00, abs=CENT)
    assert h.purchase_date == "2024-02-20"
    assert h.realized == 0.0


def test_cost_basis_is_the_amount_and_not_the_dollar_arithmetic():
    """The falsifier Part 8 A and B could not provide: quantity x price + fees
    in the row's own columns is 20,005.00, which is dollars plus euros and
    not a figure in any currency. The basis is the settled euro amount, and
    the reference's stated rate reproduces it."""
    h = derive_holdings([PART_8_C_ROW])["AAPL"]
    row = PART_8_C_ROW
    assert row["quantity"] * row["price"] + row["fees"] == pytest.approx(20_005.00, abs=CENT)
    assert h.cost_basis != pytest.approx(20_005.00, abs=CENT)
    assert h.cost_basis == pytest.approx(
        row["quantity"] * row["price"] * ROW_RATE + row["fees"], abs=CENT
    )


# ---------------------------------------------------------------------------
# Valuation at a stated spot rate (D16, D17)
# ---------------------------------------------------------------------------

def test_spot_rate_is_the_one_on_the_price_as_of_date(fx):
    rates = fx.spot_rates(euro_holdings(), {"AAPL": PRICE_AS_OF}, BASE, SPOT)
    assert set(rates) == {"AAPL"}
    assert rates["AAPL"].rate == pytest.approx(0.8500, abs=1e-9)
    assert rates["AAPL"].as_of == PRICE_AS_OF


def test_part_8_c_valuation(fx):
    """100 x 324.96 x 0.8500 = 27,621.60 EUR; +9,216.60 EUR; +50.08%
    (9,216.60 / 18,405.00 = 0.500766). The quote stays in dollars and the
    average stays in euros (D18): 324.96 against 184.05 is not a P&L."""
    rates = fx.spot_rates(euro_holdings(), {"AAPL": PRICE_AS_OF}, BASE, SPOT)
    p = position_pnl(euro_holdings(), {"AAPL": AAPL_CLOSE_USD}, rates)["AAPL"]

    assert p.market_value == pytest.approx(27_621.60, abs=CENT)
    assert p.pnl_abs == pytest.approx(9_216.60, abs=CENT)
    assert p.pnl_pct == pytest.approx(0.500766, abs=0.0000005)

    assert p.price == 324.96
    assert p.average_price == pytest.approx(184.05, abs=CENT)
    assert p.cost_basis == pytest.approx(18_405.00, abs=CENT)
    assert p.quantity == 100
    assert p.purchase_date == "2024-02-20"


def test_valuation_carries_both_dates(fx):
    """D16: the answer states the price's as-of date and the rate's. The
    position carries the rate it was valued at and that rate's date, so the
    node publishes both without arithmetic."""
    rates = fx.spot_rates(euro_holdings(), {"AAPL": PRICE_AS_OF}, BASE, SPOT)
    p = position_pnl(euro_holdings(), {"AAPL": AAPL_CLOSE_USD}, rates)["AAPL"]
    assert p.rate == pytest.approx(0.8500, abs=1e-9)
    assert p.rate_as_of == PRICE_AS_OF


# ---------------------------------------------------------------------------
# Raise, do not repair (D17)
# ---------------------------------------------------------------------------

def test_no_rate_on_the_date_raises_and_yesterday_is_not_used(fx):
    """Part 8 C: with no rate for 2026-09-02 the position has no market
    value. A rate for the day before is present and must not be used."""
    day_before_only = {"USD": {"2026-09-01": 0.8600}}
    with pytest.raises(fx.FXError) as excinfo:
        fx.spot_rates(euro_holdings(), {"AAPL": PRICE_AS_OF}, BASE, day_before_only)
    assert "USD" in str(excinfo.value)
    assert PRICE_AS_OF in str(excinfo.value)


def test_no_table_at_all_raises_and_one_is_not_used(fx):
    """Not a value at 1.0000 either."""
    with pytest.raises(fx.FXError) as excinfo:
        fx.spot_rates(euro_holdings(), {"AAPL": PRICE_AS_OF}, BASE, {})
    assert "USD" in str(excinfo.value)
    assert PRICE_AS_OF in str(excinfo.value)


def test_holding_without_a_currency_raises(fx):
    """A holding whose currency is unknown cannot be valued in any base.
    Asset.currency is filled by the price source (D16); NULL is not USD."""
    with pytest.raises(fx.FXError, match="AAPL"):
        fx.spot_rates(euro_holdings(currency=None), {"AAPL": PRICE_AS_OF}, BASE, SPOT)


def test_holding_without_a_price_date_raises(fx):
    """The rate is looked up on the price's as-of date; with no date there is
    nothing to look up."""
    with pytest.raises(fx.FXError, match="AAPL"):
        fx.spot_rates(euro_holdings(), {}, BASE, SPOT)


def test_position_with_no_rate_entry_raises():
    """`rates` states, per holding, either the rate or that none is needed.
    A holding absent from it was never compared with the base currency, and
    valuing it at the quote would be the silent 1.0 that D17 forbids."""
    with pytest.raises(AllocationError, match="AAPL"):
        position_pnl(euro_holdings(), {"AAPL": AAPL_CLOSE_USD}, {})


# ---------------------------------------------------------------------------
# Same currency: no lookup (D17), and portfolio 3 is untouched
# ---------------------------------------------------------------------------

def test_same_currency_is_no_lookup(fx):
    """A dollar holding in a dollar portfolio needs no table: the entry is
    None, and None is the lookup's finding, not a default."""
    rates = fx.spot_rates(usd_holdings(), {"AAPL": PRICE_AS_OF}, "USD", {})
    assert rates == {"AAPL": None}


def test_same_currency_reproduces_part_1(fx):
    """Part 8 C's contrast line: the same shares in dollars went from
    40,000.00 to 64,992.00, +62.48% (Part 1's AAPL row). No rate, no date."""
    rates = fx.spot_rates(usd_holdings(), {"AAPL": PRICE_AS_OF}, "USD", {})
    p = position_pnl(usd_holdings(), {"AAPL": AAPL_CLOSE_USD}, rates)["AAPL"]
    assert p.market_value == pytest.approx(64_992.00, abs=CENT)
    assert p.pnl_abs == pytest.approx(24_992.00, abs=CENT)
    assert p.pnl_pct == pytest.approx(0.6248, abs=0.00005)
    assert p.rate is None
    assert p.rate_as_of is None
