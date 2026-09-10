"""
build_holdings_summary: what DataAgent publishes to shared_data["holdings"].

Pure function over get_holdings rows. The one thing worth pinning is which
fields survive the reduction and that an absent value is published as None,
not dropped - every downstream raise-on-missing depends on the absence
reaching it.

`cost_basis` is the ledger's figure (D13, D14) and is carried, not
recomputed from quantity and average price downstream; `realized` is
dropped, since no case asks for it (handoff, pending item 18).
"""

import datetime

from agents.nodes import build_holdings_summary


ROW = {
    "id": 1, "ticker": "AAPL", "name": "Apple Inc.", "quantity": 200, "average_price": 200.0,
    "cost_basis": 40000.0, "realized": 0.0,
    "asset_class": "Equity", "sector": "Technology", "instrument_type": "share",
    "industry": "Consumer Electronics", "country": "US", "currency": "USD",
    "created_at": None, "updated_at": None, "purchase_date": datetime.date(2024, 2, 20),
}


def test_summary_fields():
    [summary] = build_holdings_summary([ROW])
    assert summary == {
        "ticker": "AAPL",
        "quantity": 200.0,
        "average_price": 200.0,
        "cost_basis": 40000.0,
        "asset_class": "Equity",
        "sector": "Technology",
        "instrument_type": "share",
        "purchase_date": "2024-02-20",
        "currency": "USD",
    }


def test_absent_values_are_published_as_none():
    """`currency` too: the rate lookup (quant/fx.py) raises on a holding
    whose currency it does not know, and can only do that if the absence
    reaches it (D16)."""
    row = {**ROW, "sector": None, "instrument_type": None, "purchase_date": None,
           "currency": None}
    [summary] = build_holdings_summary([row])
    assert summary["sector"] is None
    assert summary["instrument_type"] is None
    assert summary["purchase_date"] is None
    assert summary["currency"] is None


def test_no_holdings_is_empty():
    assert build_holdings_summary(None) == []
    assert build_holdings_summary([]) == []
