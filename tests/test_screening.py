"""
The screen held to tests/golden/expected_values.md Part 10 D and E.

Every expected figure here is copied from Part 10, computed by hand before
the screen existed. If a test fails, the screen or the reference is wrong
and that gets resolved deliberately. Do NOT update these figures to match
code output.

The fixture is the figures block of test_fundamentals.py, typed from Part
10 A, and the committed philosophy. The screen reads the metrics
quant/fundamentals.py computes and subtracts once per finding.
"""

import datetime as dt

import pytest

from portfolio_tool.philosophy import load_philosophy
from test_fundamentals import figures, AS_OF


@pytest.fixture(scope="module")
def screening():
    from portfolio_tool import screening
    return screening


@pytest.fixture(scope="module")
def philosophy():
    return load_philosophy("philosophy.toml")


@pytest.fixture(scope="module")
def findings(screening, philosophy):
    return screening.screen(philosophy, figures(), AS_OF)


def _by_clause(findings):
    return {f.clause: f for f in findings}


# --- Part 10 D --------------------------------------------------------------

def test_one_finding_per_numeric_clause_in_policy_order(findings, philosophy):
    assert [f.clause for f in findings] == [c.id for c in philosophy.checkable]
    assert len(findings) == 5
    assert all(f.subject == "GOOGL" for f in findings)


@pytest.mark.parametrize("clause, metric, years, deciding, observed, limit, bound, status, distance", [
    ("PHI-2.1", "return_on_invested_capital", ("FY2021", "FY2022", "FY2023", "FY2024", "FY2025"),
     "FY2022", 0.1000, 0.12, "min", "fail", +0.0200),
    ("PHI-2.2", "gross_margin", ("FY2023", "FY2024", "FY2025"),
     "FY2023", 0.5500, 0.35, "min", "pass", -0.2000),
    ("PHI-3.1", "net_debt_to_ebitda", ("FY2025",),
     "FY2025", -0.5000, 2.0, "max", "pass", -2.5000),
    ("PHI-4.1", "discount_to_range_low", (),
     None, 0.0500, 0.25, "min", "fail", +0.2000),
    ("PHI-4.2", "free_cash_flow_yield", ("FY2025",),
     "FY2025", 0.0450, 0.04, "min", "pass", -0.0050),
])
def test_findings_to_the_reference(findings, clause, metric, years, deciding, observed, limit, bound, status, distance):
    f = _by_clause(findings)[clause]
    assert f.metric == metric
    assert f.years_read == years
    assert f.deciding_year == deciding
    assert f.observed == pytest.approx(observed, abs=1e-12)
    assert f.limit == limit
    assert f.bound == bound
    assert f.status == status
    assert f.distance == pytest.approx(distance, abs=1e-12)


def test_distances_reconcile(findings):
    """Signed so that positive is a failure: limit - observed against a
    floor, observed - limit against a ceiling; status agrees with the sign."""
    for f in findings:
        signed = (f.limit - f.observed) if f.bound == "min" else (f.observed - f.limit)
        assert f.distance == pytest.approx(signed, abs=1e-12), f.clause
        assert (f.status == "fail") == (signed > 0), f.clause


def test_the_margin_of_safety_carries_both_as_of_dates(findings):
    f = _by_clause(findings)["PHI-4.1"]
    assert f.price_as_of == "2026-09-10"
    assert f.range_as_of == "2026-09-10"
    assert all(g.price_as_of is None and g.range_as_of is None for g in findings if g.clause != "PHI-4.1")


def test_statements_produce_nothing(findings, philosophy):
    assert not {f.clause for f in findings} & {c.id for c in philosophy.statements}
    assert len(philosophy.statements) == 12


# --- Part 10 E --------------------------------------------------------------

def test_exactly_at_the_limit_passes(screening, philosophy):
    """D23: 2.0 times EBITDA against a ceiling of 2.0, and a floor met
    exactly (free cash flow 27,360 on 684,000 is 0.04)."""
    block = figures()
    block["years"]["FY2025"].update({"debt": 120_000.0, "cash": 16_000.0, "operating_cash_flow": 49_360.0})
    by = _by_clause(screening.screen(philosophy, block, AS_OF))
    assert by["PHI-3.1"].observed == 2.0 and by["PHI-3.1"].status == "pass" and by["PHI-3.1"].distance == 0.0
    assert by["PHI-4.2"].observed == pytest.approx(0.04, abs=1e-12) and by["PHI-4.2"].status == "pass"


def test_a_missing_figure_stops_the_whole_check(screening, philosophy):
    """D25: FY2024's gross profit absent. The check stops on PHI-2.2 naming
    gross_margin and FY2024, and reports no finding on any clause."""
    block = figures()
    del block["years"]["FY2024"]["gross_profit"]
    with pytest.raises(screening.ScreeningError, match="PHI-2.2.*gross_margin.*FY2024"):
        screening.screen(philosophy, block, AS_OF)


def test_a_year_not_yet_filed_is_not_a_year(screening, philosophy):
    """D21: as of 2025-06-30 PHI-2.1 reads FY2020 to FY2024, and the block
    has no FY2020. It does not read FY2021 to FY2025 and not four years."""
    with pytest.raises(screening.ScreeningError, match="PHI-2.1.*return_on_invested_capital.*FY2020"):
        screening.screen(philosophy, figures(), dt.date(2025, 6, 30))


# --- the screen's own raises --------------------------------------------------

def test_no_price_raises_on_the_margin_of_safety(screening, philosophy):
    block = figures()
    del block["price"]
    with pytest.raises(screening.ScreeningError, match="PHI-4.1.*price"):
        screening.screen(philosophy, block, AS_OF)


def test_no_range_raises_on_the_margin_of_safety(screening, philosophy):
    block = figures()
    del block["valuation_range"]
    with pytest.raises(screening.ScreeningError, match="PHI-4.1.*valuation_range"):
        screening.screen(philosophy, block, AS_OF)


def test_no_ticker_raises(screening, philosophy):
    block = figures()
    del block["ticker"]
    with pytest.raises(screening.ScreeningError, match="ticker"):
        screening.screen(philosophy, block, AS_OF)


def test_a_band_with_both_bounds_emits_one_finding_per_bound(screening, tmp_path):
    p = tmp_path / "p.toml"
    p.write_text('''
[[clause]]
id = "PHI-2.1"
type = "metric_band"
topics = ["quality"]
metric = "gross_margin"
min = 0.50
max = 0.56
years = 3
text = "Gross margin between 50% and 56%."
''', encoding="utf-8")
    out = screening.screen(load_philosophy(str(p)), figures(), AS_OF)
    assert [(f.bound, f.deciding_year, f.status) for f in out] == [
        ("min", "FY2023", "pass"),   # lowest year 0.55 against 0.50
        ("max", "FY2025", "fail"),   # highest year 0.58 against 0.56
    ]
