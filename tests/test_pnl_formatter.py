"""
The P&L formatter names the currency of every figure it prints (D18).

Over the Part 8 C position as PortfolioAnalysisAgent publishes it, wrapped
the way mark_agent_complete stores the result. The formatter reads; it does
not divide or convert. Cost basis, average price, market value and P&L are
in the base currency; the quote is in the asset's; a position valued
through a rate prints the rate and its date beside the price's (D16). A
same-currency position prints no rate line. Every figure is the block's:
the falsifier plants a rate the market value does not produce and expects
it printed.
"""

import pytest

from agents.nodes import _format_pnl_response


# expected_values.md Part 8 C, as the node publishes it (rounded to cents,
# pnl_pct unrounded), base currency EUR.
EURO_AAPL = {
    "quantity": 100.0, "average_price": 184.05, "price": 324.96, "currency": "USD",
    "cost_basis": 18_405.00, "market_value": 27_621.60, "pnl_abs": 9_216.60,
    "pnl_pct": 0.500766, "purchase_date": "2024-02-20", "as_of": "2026-09-02",
    "rate": 0.8500, "rate_as_of": "2026-09-02",
}

# expected_values.md Part 1, JPM, base currency USD: no rate.
DOLLAR_JPM = {
    "quantity": 100.0, "average_price": 200.0, "price": 356.22, "currency": "USD",
    "cost_basis": 20_000.00, "market_value": 35_622.00, "pnl_abs": 15_622.00,
    "pnl_pct": 0.7811, "purchase_date": "2024-07-15", "as_of": "2026-09-02",
    "rate": None, "rate_as_of": None,
}


def _answer(positions, base_currency, tickers=()):
    result = {"success": True, "base_currency": base_currency, "position_pnl": positions}
    return "\n".join(_format_pnl_response({"PortfolioAnalysisAgent": result}, list(tickers)))


def test_euro_position_names_the_base_on_every_base_figure():
    text = _answer({"AAPL": EURO_AAPL}, "EUR")
    assert "+9,216.60 EUR (+50.08%)" in text
    assert "cost 18,405.00 EUR at 184.05 EUR average" in text
    assert "now 27,621.60 EUR" in text


def test_euro_position_names_the_quotes_currency():
    """324.96 is dollars; 184.05 is euros. Printed side by side, each has
    to say which it is, or the reader compares them (D18)."""
    text = _answer({"AAPL": EURO_AAPL}, "EUR")
    assert "at 324.96 USD" in text
    assert "324.96 EUR" not in text


def test_euro_position_states_the_rate_and_both_dates():
    """D16: the price's as-of date and the rate's, and the rate itself with
    its direction spelled out."""
    text = _answer({"AAPL": EURO_AAPL}, "EUR")
    assert "priced as of 2026-09-02" in text
    assert "converted at 0.8500 EUR per USD as of 2026-09-02" in text


def test_euro_position_says_the_currency_split_is_not_computed():
    """Part 8 C: the gain's split into a price part and a currency part is
    named and not computed; the answer says so when a rate was used."""
    text = _answer({"AAPL": EURO_AAPL}, "EUR")
    assert "price part" in text and "currency part" in text


def test_dollar_position_names_the_currency_and_prints_no_rate_line():
    text = _answer({"JPM": DOLLAR_JPM}, "USD")
    assert "+15,622.00 USD (+78.11%)" in text
    assert "cost 20,000.00 USD at 200.00 USD average" in text
    assert "now 35,622.00 USD at 356.22 USD, priced as of 2026-09-02" in text
    assert "converted" not in text
    assert "currency part" not in text


def test_rate_is_read_not_derived():
    """A rate the figures do not produce is printed as published: the
    formatter states the block, it does not recompute it."""
    planted = {**EURO_AAPL, "rate": 0.9000}
    text = _answer({"AAPL": planted}, "EUR")
    assert "converted at 0.9000 EUR per USD" in text
    assert "27,621.60 EUR" in text


def test_selection_still_reads_tickers():
    text = _answer({"AAPL": EURO_AAPL, "JPM": DOLLAR_JPM}, "EUR", tickers=["JPM"])
    assert "**JPM**" in text and "**AAPL**" not in text


def test_missing_base_currency_raises():
    """A formatter with a fallback would print a currency nobody published."""
    result = {"success": True, "position_pnl": {"JPM": DOLLAR_JPM}}
    with pytest.raises(ValueError, match="base_currency"):
        _format_pnl_response({"PortfolioAnalysisAgent": result}, [])
