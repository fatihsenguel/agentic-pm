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


def test_position_view_prints_largest_first_with_share_of_total():
    """Part 7, IPS-4.1 column: "what is my biggest position" is the first
    line, with its share of total; the header names the total."""
    text = _answer(allocation(), group_by="position")
    lines = [l for l in text.splitlines() if l.startswith("  - ")]
    assert lines[0].startswith("  - SPY")
    assert "18.65%" in lines[0]
    assert "4.05%" in lines[-1] and lines[-1].startswith("  - NEE")
    assert len(lines) == 9
    assert "410,200.50" in text
    assert "By sector" not in text and "By asset class" not in text


def test_position_share_is_read_not_divided():
    alloc = allocation()
    spy = next(l for l in alloc["by_position"]["lines"] if l["label"] == "SPY")
    spy["pct_of_total"] = 0.4321
    text = _answer(alloc, group_by="position")
    assert "43.21%" in text
    assert "18.65%" not in text


def test_no_group_by_renders_all_three_views():
    text = _answer(allocation())
    assert "By asset class" in text
    assert "By sector" in text
    assert "By position" in text
    assert "so all three are" in text   # the sentence wraps after "are"



def _without_labels(alloc):
    for view in alloc.values():
        view.pop("denominator", None)
    return alloc


def test_headers_name_each_denominator_from_the_block_itself():
    """No prose label in the block: the formatter writes each header from
    the share fields' own names and the block's amounts."""
    text = _answer(_without_labels(allocation()))
    assert "% of total portfolio value 410,200.50" in text
    assert "sectored value 208,197.50" in text
    assert "invested value 394,700.50" in text
    assert "D2" not in text and "D3" not in text
