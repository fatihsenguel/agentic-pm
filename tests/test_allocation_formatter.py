"""
The allocation formatter prints the sector line's share of total.

Over the Part 7 block from test_compliance.py, wrapped the way
mark_agent_complete stores PortfolioAnalysisAgent's result. The formatter
reads; it does not divide. The falsifier below plants a share the market
values do not produce and expects it printed, so a formatter that divided
for the figure would fail.
"""

from agents.nodes import _format_allocation_response

from test_compliance import allocation


def _answer(alloc, group_by=None):
    return "\n".join(_format_allocation_response(
        {"PortfolioAnalysisAgent": {"success": True, "allocation": alloc}}, group_by))


def test_sector_lines_carry_the_share_of_total():
    """Part 7, IPS-4.3 column, beside Part 3's two columns."""
    text = _answer(allocation(), group_by="sector")
    assert "27.96%" in text       # Technology of total
    assert "45.47%" in text       # unsectored of total, reported not counted
    assert "55.08%" in text       # of sectored, unchanged
    assert "29.05%" in text       # of invested, unchanged


def test_sector_header_names_the_total_without_the_asset_class_block():
    """With group_by=sector the asset-class block is not rendered, so the
    total the third column is a share of has to come from the sector block."""
    text = _answer(allocation(), group_by="sector")
    assert "410,200.50" in text
    assert "By asset class" not in text


def test_share_of_total_is_read_not_divided():
    alloc = allocation()
    tech = next(l for l in alloc["by_sector"]["lines"] if l["label"] == "Technology")
    tech["pct_of_total"] = 0.1234
    text = _answer(alloc, group_by="sector")
    assert "12.34%" in text
    assert "27.96%" not in text
