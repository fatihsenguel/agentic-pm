"""
The allocation layer reads a holding's cost basis; it does not recompute it.

The ledger states each holding's cost basis as the sum of its rows' amounts
(expected_values.md D13, D14). Quantity times average price is the same
number today only because the average is the basis divided by the quantity;
a layer that multiplies them back is a second arithmetic path for a figure
the ledger already states, and the path a second currency would enter by.

The falsifier is a holding whose stated basis is deliberately not quantity
times average: 10 shares, average 5.00, cost basis 60.00. Every view that
carries a cost figure must carry 60.00, and a holding that states no basis
must raise rather than fall back to the product. Part 8 B cannot tell the
two apart (250 x 80.01 is exactly 20,002.50), which is why this is a
contract test and not a reference one.
"""

import pytest

from portfolio_tool.quant.allocation import (
    allocation_by_asset_class,
    allocation_by_position,
    allocation_by_sector,
    position_pnl,
)


HOLDING = {
    "ticker": "ZZZ", "quantity": 10.0, "average_price": 5.0, "cost_basis": 60.0,
    "asset_class": "Equity", "sector": "Technology", "instrument_type": "share",
    "purchase_date": "2024-01-02", "currency": "USD",
}
PRICES = {"ZZZ": 7.0}
RATES = {"ZZZ": None}
STATED = 60.0
PRODUCT = 50.0


def _line(allocation, label):
    return next(line for line in allocation.lines if line.label == label)


def test_asset_class_view_carries_the_stated_basis():
    line = _line(allocation_by_asset_class([HOLDING], PRICES, 0.0, RATES), "Equity")
    assert line.cost_basis == STATED
    assert line.cost_basis != PRODUCT


def test_sector_view_carries_the_stated_basis():
    line = _line(allocation_by_sector([HOLDING], PRICES, 0.0, RATES), "Technology")
    assert line.cost_basis == STATED


def test_position_view_carries_the_stated_basis():
    line = _line(allocation_by_position([HOLDING], PRICES, 0.0, RATES), "ZZZ")
    assert line.cost_basis == STATED


def test_position_pnl_carries_the_stated_basis():
    p = position_pnl([HOLDING], PRICES, RATES)["ZZZ"]
    assert p.cost_basis == STATED
    assert p.pnl_abs == pytest.approx(70.0 - STATED)


def test_a_holding_with_no_basis_raises():
    without = {k: v for k, v in HOLDING.items() if k != "cost_basis"}
    with pytest.raises(KeyError):
        position_pnl([without], PRICES, RATES)
