"""
The portfolio a request is about, as the nodes read it.

The module held the task loop's vocabulary as well, tasks and results for
a supervisor to pass between agents, with their enums and supporting
records; it went with the loop (decision 54, the tag agent-loop-parked).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PortfolioContext:
    """
    The portfolio a request is about, resolved once from the database.

    Returned by `load_portfolio_context`. An object rather than a tuple so that
    adding a field later does not break every call site — `cash_balance` was
    added after `tickers` and `holdings` and forced exactly that churn.

    `holdings`, `cash_balance` and `base_currency` are None for ad-hoc queries
    that name tickers without a portfolio. None means "no portfolio, so
    unknown"; it does not mean zero, and it does not mean dollars. A
    portfolio holding no cash reports 0.0. `base_currency` is the
    portfolio's own currency (expected_values.md D15), the one every figure
    about it is reported in.
    """
    tickers: List[str]
    holdings: Optional[List[Dict[str, Any]]] = None
    cash_balance: Optional[float] = None
    base_currency: Optional[str] = None
    portfolio_id: Optional[int] = None
