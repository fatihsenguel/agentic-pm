"""
Spot rates for valuing foreign holdings in a portfolio's base currency.

Pure arithmetic over holdings, price dates and a rate table. No database, no
LLM, no state. DataAgent fetches and publishes the table; this module only
looks up; `allocation.py` multiplies.

Reference: tests/golden/expected_values.md Part 8 C, and decisions D15-D18.

  D15  The base currency is the portfolio's.
  D16  A price is in the asset's currency. A foreign holding's value in the
       base currency is quantity x price x the spot rate on the price's
       as-of date, and both dates are stated.
  D17  A spot rate is a price source: per day, dated. A missing rate raises;
       nothing falls back to yesterday's rate or to 1. When the two
       currencies are the same there is no lookup.
  D18  Cost basis, average price and realized gain are in the base currency
       already (they come from `amount`); only market value needs a rate.

The rate convention: units of BASE currency per one unit of the ASSET's
currency, so Part 8 C's "0.9200 EUR/USD" is euros per dollar. The table is
keyed by the asset's currency under the given base:
{"USD": {"2026-09-02": 0.85}} is 0.85 euros per dollar on that date when
the base is EUR. Dates are YYYY-MM-DD strings, as DataAgent publishes them.

Raises, never repairs: a holding with no currency, a holding with no price
date, a currency the table lacks, a date the table lacks. A `None` entry is
not a default of 1.0; it is this module's finding, after comparing the two
currencies, that no lookup is needed (D17).
"""

from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence


class FXError(Exception):
    """Raised when a holding cannot be valued in the base currency."""
    pass


@dataclass
class SpotRate:
    """The rate one holding is valued at, and the day it is for (D16)."""

    quote: str      # the asset's currency
    rate: float     # base units per one unit of `quote`
    as_of: str      # the price's as-of date, which is the rate's


def spot_rates(
    holdings: Sequence[Dict],
    as_of_dates: Mapping[str, str],
    base_currency: str,
    fx_rates: Mapping[str, Mapping[str, float]],
) -> Dict[str, Optional[SpotRate]]:
    """
    One entry per holding: None when its currency is the base (no lookup,
    D17), otherwise the rate on its price's as-of date (D16).

    Args:
        holdings: summary dicts carrying ticker and currency
        as_of_dates: the date of each ticker's latest price, YYYY-MM-DD
        base_currency: the portfolio's currency (D15)
        fx_rates: {asset currency: {date: rate}}, base units per one unit

    Raises:
        FXError naming the ticker when a holding has no currency or no
        price date, and naming the currency and the date when the table
        has no rate for that day.
    """
    if not base_currency:
        raise FXError("No base currency: a holding cannot be valued in an unnamed currency.")

    result: Dict[str, Optional[SpotRate]] = {}
    for h in holdings:
        ticker = h["ticker"]
        currency = h.get("currency")
        if not currency:
            raise FXError(
                f"{ticker}: no currency on the holding, so it cannot be valued in "
                f"{base_currency}. Asset.currency is filled by the price source (D16)."
            )
        if currency == base_currency:
            result[ticker] = None
            continue

        as_of = as_of_dates.get(ticker)
        if not as_of:
            raise FXError(
                f"{ticker}: no price as-of date, so there is no day to look a "
                f"{base_currency}/{currency} rate up on (D16)."
            )
        rate = (fx_rates.get(currency) or {}).get(as_of)
        if rate is None:
            raise FXError(
                f"{ticker}: no {base_currency}/{currency} rate for {as_of}. "
                f"A holding priced in {currency} has no value in {base_currency} "
                f"without the spot rate on the price's date; nothing falls back to "
                f"another day's rate or to 1 (D17)."
            )
        result[ticker] = SpotRate(quote=currency, rate=float(rate), as_of=as_of)

    return result
