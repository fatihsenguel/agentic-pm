"""
The transaction ledger: holdings derived from rows.

Pure arithmetic over ledger rows. No database, no LLM, no state. Something
else loads one portfolio's rows and publishes the result; this module only
computes.

Reference: tests/golden/expected_values.md Part 8, and decisions D10-D14.

  D10  Average cost. One average price per position, which is what a holding
       row and every P&L figure use.
  D11  Fees are part of cost basis: what was paid on a buy, what was received
       on a sale, fees inside both.
  D12  A sale lowers quantity by the quantity sold and cost basis by the basis
       released at the average; the average price is unchanged. The realized
       gain is proceeds minus the basis released.
  D13  Holdings derive from rows: quantity = buys - sells, cost basis per D11
       and D12, average = cost basis / quantity, purchase date = the first
       buy, reported and never used in arithmetic.
  D14  A row belongs to a portfolio, and its `amount` is the settled figure in
       the portfolio's currency, taken from the statement.

Cost basis is summed from `amount`, never recomputed from quantity x price
+/- fees. For a single-currency row the two are equal by construction (Part
8 A and B); for a foreign-currency row they differ by the historical rate,
which is data (D14). Nothing here checks one against the other: where rows
are written is where that check belongs.

No rounding anywhere. The average is an unrounded division; rounding is a
formatter's job (D9's lesson on the compliance checker).

Raises, never repairs: a sale larger than the position, a sale of something
never bought, rows from two portfolios, an unknown row type, a missing
column, an empty ledger. A portfolio that appears to hold nothing is a wrong
picture with a plausible face, so an empty row list is an error and not an
empty result.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Sequence


class LedgerError(Exception):
    """Raised when holdings cannot be derived correctly from ledger rows."""
    pass


@dataclass
class DerivedHolding:
    """One position as its ledger rows leave it.

    The first four fields are what a holding row carries today and what
    `allocation.py` reads; `cost_basis` is what the rows summed to and
    `realized` is D12's figure, stated because the reference states it.
    """

    ticker: str
    quantity: float
    average_price: float
    purchase_date: Optional[str]
    cost_basis: float
    realized: float


ROW_COLUMNS = ("portfolio_id", "date", "type", "ticker", "quantity", "price", "fees", "amount")
ROW_TYPES = ("buy", "sell")


def derive_holdings(rows: Sequence[Dict]) -> Dict[str, DerivedHolding]:
    """
    Holdings of one portfolio from its ledger rows (D13).

    Args:
        rows: dicts carrying portfolio_id, date, type ('buy' or 'sell'),
              ticker, quantity, price, fees and amount. Read in date order;
              rows on the same date keep the order given.

    Returns:
        One DerivedHolding per ticker still held, keyed by ticker. A position
        sold down to nothing is not a holding and is not returned.

    Raises:
        LedgerError on an empty ledger, a missing column, rows from more than
        one portfolio, an unknown row type, a sale of a ticker never bought,
        or a sale larger than the quantity held.
    """
    if not rows:
        raise LedgerError("No ledger rows: nothing to derive holdings from.")

    for row in rows:
        missing = [c for c in ROW_COLUMNS if c not in row]
        if missing:
            raise LedgerError(f"Ledger row lacks {', '.join(missing)}: {row!r}")

    portfolios = {row["portfolio_id"] for row in rows}
    if len(portfolios) != 1:
        raise LedgerError(
            f"Ledger rows from more than one portfolio: {sorted(map(str, portfolios))}. "
            "Holdings are derived per portfolio."
        )

    quantity: Dict[str, float] = {}
    cost_basis: Dict[str, float] = {}
    realized: Dict[str, float] = {}
    first_buy: Dict[str, str] = {}

    for row in sorted(rows, key=lambda r: r["date"]):
        ticker, kind = row["ticker"], row["type"]
        qty, amount = float(row["quantity"]), float(row["amount"])

        if kind == "buy":
            if ticker not in first_buy:
                first_buy[ticker] = str(row["date"])
            quantity[ticker] = quantity.get(ticker, 0.0) + qty
            cost_basis[ticker] = cost_basis.get(ticker, 0.0) + amount
            realized.setdefault(ticker, 0.0)

        elif kind == "sell":
            held = quantity.get(ticker, 0.0)
            if ticker not in quantity:
                raise LedgerError(
                    f"{ticker}: sale of {qty} on {row['date']} with no prior buy."
                )
            if qty > held:
                raise LedgerError(
                    f"{ticker}: sale of {qty} on {row['date']} exceeds the {held} held."
                )
            # D12: basis released at the average, so the average is unchanged.
            released = cost_basis[ticker] * qty / held
            quantity[ticker] = held - qty
            cost_basis[ticker] -= released
            realized[ticker] += amount - released

        else:
            raise LedgerError(
                f"{ticker}: unknown row type {kind!r} on {row['date']}; "
                f"a ledger row is one of {', '.join(ROW_TYPES)}."
            )

    return {
        ticker: DerivedHolding(
            ticker=ticker,
            quantity=quantity[ticker],
            average_price=cost_basis[ticker] / quantity[ticker],
            purchase_date=first_buy[ticker],
            cost_basis=cost_basis[ticker],
            realized=realized[ticker],
        )
        for ticker in quantity
        if quantity[ticker] > 0
    }
