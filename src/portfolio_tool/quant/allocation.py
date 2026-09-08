"""
Portfolio allocation.

Pure arithmetic over holdings, prices and cash. No database, no LLM, no state.
An agent supplies the inputs and publishes the output; this module only computes.

Reference: tests/golden/expected_values.md Parts 2, 3 and 7, and decisions D1-D3.

  D1  Allocation is measured on MARKET VALUE, not cost basis. Cost basis is
      returned alongside because Part 2 tabulates both, but the answer to
      benchmark 1.1 is the market-value column.
  D2  Cash counts in the asset-class denominator. Holding cash is a positioning
      decision and IPS limits are written against total portfolio value.
  D3  Unsectored holdings are reported explicitly, never dropped. With ~47% of
      this portfolio unsectored, excluding it would inflate every sector figure
      roughly twofold.

Note the denominators differ between the two views, and that is deliberate
rather than an oversight: asset-class percentages are of TOTAL (cash included,
per D2), sector percentages are of INVESTED (cash excluded, because cash has no
sector). Part 3 carries both a "% sectored" and a "% invested" column for the
same reason.

Every line also carries `pct_of_total`, its share of total portfolio value
including cash (D2). That is the figure every IPS limit is written against
(Part 7): on an asset-class line it is the same number as `pct_of_denominator`,
on a sector line it is a third figure that neither Part 3 column gives. It is
computed here so that no reader - the checker, a formatter - divides for it.

A third view, by position, is Part 7's IPS-4.1 table: one line per holding,
largest first. Concentration is allocation by position, so it is a view here
and not a second computation elsewhere.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence


UNSECTORED_LABEL = "(no sector)"


class AllocationError(Exception):
    """Raised when allocation cannot be computed correctly."""
    pass


@dataclass
class AllocationLine:
    """One bucket of an allocation breakdown."""

    label: str
    market_value: float
    cost_basis: float
    tickers: List[str] = field(default_factory=list)

    # Percentages are left None where they are not meaningful for the bucket,
    # e.g. cash has no "% invested" and unsectored holdings have no "% sectored".
    pct_of_denominator: Optional[float] = None
    pct_of_invested: Optional[float] = None
    # Share of total portfolio value including cash (D2), on every line.
    pct_of_total: Optional[float] = None


@dataclass
class Allocation:
    """A full breakdown, plus the denominators it was computed against.

    `total_value` is total portfolio value including cash (D2) in both views.
    `sectored_value` is the sector view's own denominator and None in the
    asset-class view, which has no such quantity.
    """

    lines: List[AllocationLine]
    invested_value: float
    cash_balance: float
    total_value: float
    denominator_label: str
    sectored_value: Optional[float] = None


def _market_values(
    holdings: Sequence[Dict],
    prices: Dict[str, float],
) -> Dict[str, float]:
    """
    Market value per ticker.

    Raises rather than skipping when a price is missing. A skipped holding
    shrinks the denominator and moves every percentage in the answer, which
    looks like a valid result and is not.
    """
    if not holdings:
        raise AllocationError("No holdings to allocate.")

    missing = [h["ticker"] for h in holdings if prices.get(h["ticker"]) is None]
    if missing:
        raise AllocationError(
            f"No price for: {', '.join(sorted(missing))}.\n"
            f"Priced: {', '.join(sorted(prices))}\n"
            "\n"
            "Allocation is not computed with a partial denominator. Every "
            "percentage would shift and the result would look valid."
        )

    return {
        h["ticker"]: float(h["quantity"]) * float(prices[h["ticker"]])
        for h in holdings
    }


def _cost_bases(holdings: Sequence[Dict]) -> Dict[str, float]:
    """Cost basis per ticker: quantity times average price paid."""
    return {
        h["ticker"]: float(h["quantity"]) * float(h["average_price"])
        for h in holdings
    }


def allocation_by_asset_class(
    holdings: Sequence[Dict],
    prices: Dict[str, float],
    cash_balance: float,
) -> Allocation:
    """
    Allocation by asset class, as a percentage of total portfolio value.

    Cash is a line of its own and is inside the denominator (D2). This is the
    answer to benchmark case 1.1.

    Args:
        holdings: summary dicts carrying ticker, quantity, average_price,
                  asset_class
        prices: current price per ticker
        cash_balance: portfolio cash

    Returns:
        Allocation whose lines sum to 100% of total_value.
    """
    values = _market_values(holdings, prices)
    costs = _cost_bases(holdings)
    cash = float(cash_balance)

    buckets: Dict[str, AllocationLine] = {}
    for h in holdings:
        label = h.get("asset_class") or "(unclassified)"
        line = buckets.setdefault(
            label, AllocationLine(label=label, market_value=0.0, cost_basis=0.0)
        )
        line.market_value += values[h["ticker"]]
        line.cost_basis += costs[h["ticker"]]
        line.tickers.append(h["ticker"])

    invested = sum(line.market_value for line in buckets.values())
    total = invested + cash

    if total <= 0:
        raise AllocationError(
            f"Total portfolio value is {total}, so percentages are undefined."
        )

    lines = sorted(buckets.values(), key=lambda l: -l.market_value)
    for line in lines:
        line.pct_of_denominator = line.market_value / total
        line.pct_of_invested = line.market_value / invested if invested else None
        line.pct_of_total = line.pct_of_denominator

    # Cash last, and with no "% invested" - it is not invested.
    lines.append(
        AllocationLine(
            label="Cash",
            market_value=cash,
            cost_basis=cash,
            tickers=[],
            pct_of_denominator=cash / total,
            pct_of_invested=None,
            pct_of_total=cash / total,
        )
    )

    return Allocation(
        lines=lines,
        invested_value=invested,
        cash_balance=cash,
        total_value=total,
        denominator_label="total portfolio value (cash included, D2)",
    )


def allocation_by_sector(
    holdings: Sequence[Dict],
    prices: Dict[str, float],
    cash_balance: float,
) -> Allocation:
    """
    Allocation by sector, over invested value, with each sector's share of total.

    Cash is excluded from the sector denominators because cash has no sector.
    Holdings without a sector get their own explicit line (D3) and are counted
    in the invested denominator, but not in the sectored one.

    Each line carries three percentages: `pct_of_denominator` is of sectored
    value, `pct_of_invested` is of all invested value, `pct_of_total` is of
    total portfolio value including cash (D2) - the IPS-4.3 figure, Part 7.
    The unsectored line has the second and third only.

    Args:
        holdings: summary dicts carrying ticker, quantity, average_price, sector
        prices: current price per ticker
        cash_balance: portfolio cash, needed for the total and nothing else

    Returns:
        Allocation whose sectored lines sum to 100% of sectored value.
    """
    values = _market_values(holdings, prices)
    costs = _cost_bases(holdings)

    buckets: Dict[str, AllocationLine] = {}
    unsectored = AllocationLine(
        label=UNSECTORED_LABEL, market_value=0.0, cost_basis=0.0
    )

    for h in holdings:
        sector = h.get("sector")
        line = unsectored if not sector else buckets.setdefault(
            sector, AllocationLine(label=sector, market_value=0.0, cost_basis=0.0)
        )
        line.market_value += values[h["ticker"]]
        line.cost_basis += costs[h["ticker"]]
        line.tickers.append(h["ticker"])

    sectored = sum(line.market_value for line in buckets.values())
    invested = sectored + unsectored.market_value
    cash = float(cash_balance)
    total = invested + cash

    if invested <= 0:
        raise AllocationError(
            f"Invested value is {invested}, so percentages are undefined."
        )

    lines = sorted(buckets.values(), key=lambda l: -l.market_value)
    for line in lines:
        line.pct_of_denominator = line.market_value / sectored if sectored else None
        line.pct_of_invested = line.market_value / invested
        line.pct_of_total = line.market_value / total

    if unsectored.market_value > 0:
        unsectored.pct_of_denominator = None
        unsectored.pct_of_invested = unsectored.market_value / invested
        unsectored.pct_of_total = unsectored.market_value / total
        lines.append(unsectored)

    return Allocation(
        lines=lines,
        invested_value=invested,
        cash_balance=cash,
        total_value=total,
        denominator_label="sectored value (cash excluded, unsectored shown, D3)",
        sectored_value=sectored,
    )


def allocation_by_position(
    holdings: Sequence[Dict],
    prices: Dict[str, float],
    cash_balance: float,
) -> Allocation:
    """
    Allocation by position: one line per holding, labelled by ticker, largest
    market value first, so the biggest position is the first line and no
    reader sorts. Reference: expected_values.md Part 7, the IPS-4.1 table.

    The denominator is total portfolio value including cash (D2), the same
    as the asset-class view, so `pct_of_denominator` equals `pct_of_total`.
    No cash line: cash is not a holding and IPS-4.1 is about instruments; it
    is inside the denominator and reported on the Allocation.

    Args:
        holdings: summary dicts carrying ticker, quantity, average_price
        prices: current price per ticker
        cash_balance: portfolio cash, inside the total

    Returns:
        Allocation whose lines plus cash sum to 100% of total_value.
    """
    values = _market_values(holdings, prices)
    costs = _cost_bases(holdings)
    cash = float(cash_balance)

    invested = sum(values.values())
    total = invested + cash

    if total <= 0:
        raise AllocationError(
            f"Total portfolio value is {total}, so percentages are undefined."
        )

    lines = [
        AllocationLine(
            label=h["ticker"],
            market_value=values[h["ticker"]],
            cost_basis=costs[h["ticker"]],
            tickers=[h["ticker"]],
        )
        for h in holdings
    ]
    lines.sort(key=lambda l: -l.market_value)
    for line in lines:
        line.pct_of_total = line.market_value / total
        line.pct_of_denominator = line.pct_of_total
        line.pct_of_invested = line.market_value / invested if invested else None

    return Allocation(
        lines=lines,
        invested_value=invested,
        cash_balance=cash,
        total_value=total,
        denominator_label="total portfolio value (cash included, D2)",
    )


@dataclass
class PositionPnL:
    """Unrealised profit and loss of one position since purchase."""

    ticker: str
    quantity: float
    average_price: float
    price: float
    cost_basis: float
    market_value: float
    pnl_abs: float
    pnl_pct: float
    purchase_date: Optional[str]


def position_pnl(
    holdings: Sequence[Dict],
    prices: Dict[str, float],
) -> Dict[str, PositionPnL]:
    """
    Unrealised P&L per position: market value against cost basis.

    Reference: expected_values.md Part 1, and D4.

      D4  PRICE return, not total return. Forced by the data model rather than
          chosen: `Dividend` has no `portfolio_id`, so no dividend can be
          attributed to a portfolio. Anything rendering these figures has to
          say so - on JNJ, JPM, NEE, VNQ and TLT this understates the return.

    Every position is computed, whichever one was asked about. Selecting is
    the caller's job. Same inputs as the allocation functions: a holding's
    quantity, average price and purchase date, and a price per ticker.

    Raises through `_market_values` on a missing price, and here on a cost
    basis of zero, where a percentage is undefined.
    """
    values = _market_values(holdings, prices)
    costs = _cost_bases(holdings)

    result: Dict[str, PositionPnL] = {}
    for h in holdings:
        ticker = h["ticker"]
        cost = costs[ticker]
        if cost <= 0:
            raise AllocationError(
                f"{ticker}: cost basis is {cost}, so P&L % is undefined."
            )
        value = values[ticker]
        result[ticker] = PositionPnL(
            ticker=ticker,
            quantity=float(h["quantity"]),
            average_price=float(h["average_price"]),
            price=float(prices[ticker]),
            cost_basis=cost,
            market_value=value,
            pnl_abs=value - cost,
            pnl_pct=(value - cost) / cost,
            purchase_date=h.get("purchase_date"),
        )
    return result
