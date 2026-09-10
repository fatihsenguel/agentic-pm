"""
The checker held to tests/golden/expected_values.md Part 7.

Every expected figure here is copied from Part 7, which was computed by hand
from Part 1's 2026-09-02 closes and agrees with the workbook's Compliance
sheet to the cent. If a test fails, the checker or the reference is wrong
and that gets resolved deliberately. Do NOT update these figures to match
code output.

The fixture is the allocation block in the shape PortfolioAnalysisAgent
publishes - three views, each line with its share of total - typed from
Parts 1-3 and 7 by hand rather than produced by allocation.py, so this test
depends on nothing but the checker and the loaded policy.
"""

import pytest

from portfolio_tool.compliance import (
    BREACH, EXEMPT, OK, REFUSED, ComplianceError, check, refuse,
)
from portfolio_tool.ips import load_ips


TOTAL = 410_200.50  # Part 1 total, D2 denominator for every clause
CENT = 0.0051       # Part 7 prints cents; half a cent is the rounding limit

# Part 1, market value at the 09-02 closes.
MV = {
    "SPY": 76_516.00, "AAPL": 64_992.00, "MSFT": 49_682.00, "JNJ": 41_281.50,
    "JPM": 35_622.00, "NEE": 16_620.00, "TLT": 40_975.00, "GLD": 40_278.00,
    "VNQ": 28_734.00,
}
# Part 2, by asset class.
CLASSES = [
    ("Equity", 284_713.50, ["SPY", "AAPL", "MSFT", "JNJ", "JPM", "NEE"]),
    ("Fixed Income", 40_975.00, ["TLT"]),
    ("Commodity", 40_278.00, ["GLD"]),
    ("Real Estate", 28_734.00, ["VNQ"]),
    ("Cash", 15_500.00, []),
]
# Part 3, by sector (invested only; cash has no sector).
SECTORS = [
    ("Technology", 114_674.00, ["AAPL", "MSFT"]),
    ("Healthcare", 41_281.50, ["JNJ"]),
    ("Financials", 35_622.00, ["JPM"]),
    ("Utilities", 16_620.00, ["NEE"]),
    ("(no sector)", 186_503.00, ["SPY", "TLT", "GLD", "VNQ"]),
]
INSTRUMENT_TYPES = {
    "SPY": "fund", "TLT": "fund", "GLD": "fund", "VNQ": "fund",
    "AAPL": "share", "MSFT": "share", "JNJ": "share", "JPM": "share", "NEE": "share",
}


def allocation():
    sectored = sum(v for label, v, _ in SECTORS if label != "(no sector)")
    invested = TOTAL - 15_500.00
    return {
        "by_asset_class": {
            "lines": [
                {"label": label, "market_value": v, "cost_basis": 0.0,
                 "pct_of_sectored": None,
                 "pct_of_invested": (v / invested if label != "Cash" else None),
                 "pct_of_total": v / TOTAL,
                 "tickers": list(tickers)}
                for label, v, tickers in CLASSES
            ],
            "invested_value": invested,
            "cash_balance": 15_500.00,
            "total_value": TOTAL,
        },
        "by_sector": {
            "lines": [
                {"label": label, "market_value": v, "cost_basis": 0.0,
                 "pct_of_sectored": (v / sectored if label != "(no sector)" else None),
                 "pct_of_invested": v / invested,
                 "pct_of_total": v / TOTAL,
                 "tickers": list(tickers)}
                for label, v, tickers in SECTORS
            ],
            "invested_value": invested,
            "sectored_value": sectored,
            "total_value": TOTAL,
        },
        # Part 7, the IPS-4.1 table: one line per holding, largest first.
        "by_position": {
            "lines": [
                {"label": t, "market_value": v, "cost_basis": 0.0,
                 "pct_of_sectored": None,
                 "pct_of_invested": v / invested,
                 "pct_of_total": v / TOTAL,
                 "tickers": [t]}
                for t, v in sorted(MV.items(), key=lambda kv: -kv[1])
            ],
            "invested_value": invested,
            "cash_balance": 15_500.00,
            "total_value": TOTAL,
        },
        "as_of": {"worst_case": "2026-09-02", "stalest": "SPY", "uniform": True},
        # The portfolio's currency, as the analysis node publishes it (D15);
        # every amount above is in it. The checker does not read it.
        "base_currency": "USD",
    }


@pytest.fixture(scope="module")
def ips():
    return load_ips()


@pytest.fixture(scope="module")
def findings(ips):
    return check(ips, allocation(), INSTRUMENT_TYPES)


def by_key(findings):
    return {(f.clause, f.subject, f.bound): f for f in findings}


# --- Part 7 ------------------------------------------------------------------

# clause, subject, bound, % of total, distance pp, distance currency
BREACHES = [
    ("IPS-3.1", "Equity", "max", 69.41, 4.41, 18_083.18),
    ("IPS-4.1", "SPY", "max", 18.65, 6.65, 27_291.94),
    ("IPS-4.1", "AAPL", "max", 15.84, 3.84, 15_767.94),
    ("IPS-4.1", "MSFT", "max", 12.11, 0.11, 457.94),
    ("IPS-4.2", "AAPL", "max", 15.84, 5.84, 23_971.95),
    ("IPS-4.2", "MSFT", "max", 12.11, 2.11, 8_661.95),
    ("IPS-4.2", "JNJ", "max", 10.06, 0.06, 261.45),
    ("IPS-4.3", "Technology", "max", 27.96, 2.96, 12_123.88),
]

# Part 7 §3's headroom, in words there, signed negative here.
HEADROOM = [
    ("IPS-3.2", "Fixed Income", "min", 9.99, -1.99),
    ("IPS-3.3", "Commodity", "max", 9.82, -5.18),
    ("IPS-3.4", "Real Estate", "max", 7.00, -8.00),
    ("IPS-3.5", "Cash", "min", 3.78, -0.78),
]


def test_counts(findings):
    statuses = [f.status for f in findings]
    assert statuses.count(BREACH) == 8
    assert statuses.count(EXEMPT) == 4
    assert len(findings) == 7 + 9 + 9 + 4  # bands, 4.1, 4.2, 4.3


@pytest.mark.parametrize("clause, subject, bound, pct, pp, value", BREACHES)
def test_breaches_to_the_cent(findings, clause, subject, bound, pct, pp, value):
    f = by_key(findings)[(clause, subject, bound)]
    assert f.status == BREACH
    assert f.observed * 100 == pytest.approx(pct, abs=CENT)
    assert f.distance_pp == pytest.approx(pp, abs=CENT)
    assert f.distance_value == pytest.approx(value, abs=CENT)


@pytest.mark.parametrize("clause, subject, bound, pct, pp", HEADROOM)
def test_headroom_is_signed_negative(findings, clause, subject, bound, pct, pp):
    f = by_key(findings)[(clause, subject, bound)]
    assert f.status == OK
    assert f.observed * 100 == pytest.approx(pct, abs=CENT)
    assert f.distance_pp == pytest.approx(pp, abs=CENT)


def test_a_band_emits_one_finding_per_bound(findings):
    keys = by_key(findings)
    assert ("IPS-3.1", "Equity", "min") in keys and ("IPS-3.1", "Equity", "max") in keys
    assert ("IPS-3.2", "Fixed Income", "min") in keys and ("IPS-3.2", "Fixed Income", "max") in keys
    assert ("IPS-3.3", "Commodity", "min") not in keys
    assert ("IPS-3.5", "Cash", "max") not in keys
    assert keys[("IPS-3.1", "Equity", "min")].status == OK


def test_funds_are_exempt_from_the_issuer_clause_only(findings):
    keys = by_key(findings)
    for fund in ("SPY", "TLT", "GLD", "VNQ"):
        exempt = keys[("IPS-4.2", fund, None)]
        assert exempt.status == EXEMPT
        assert (exempt.observed, exempt.limit, exempt.distance_pp, exempt.distance_value) == (None,) * 4
        assert keys[("IPS-4.1", fund, "max")].status in (OK, BREACH)


def test_unsectored_has_no_sector_finding(findings):
    assert not any(f.clause == "IPS-4.3" and f.subject == "(no sector)" for f in findings)
    assert {f.subject for f in findings if f.clause == "IPS-4.3"} == {
        "Technology", "Healthcare", "Financials", "Utilities"}


def test_sector_uses_total_not_the_sector_blocks_own_denominators(findings):
    tech = by_key(findings)[("IPS-4.3", "Technology", "max")]
    # 55.08% of sectored and 29.05% of invested are the two wrong answers.
    assert tech.observed * 100 == pytest.approx(27.96, abs=CENT)


def _line(alloc, view, label):
    return next(l for l in alloc[view]["lines"] if l["label"] == label)


def test_sector_reads_the_published_share_and_does_not_divide(ips):
    """The IPS-4.3 figure is read from `pct_of_total`, not computed here.
    With the market value and both Part 3 percentages made nonsense, the
    finding still carries Part 7's 27.96%."""
    alloc = allocation()
    line = _line(alloc, "by_sector", "Technology")
    line["market_value"] = 1.0
    line["pct_of_sectored"] = None
    line["pct_of_invested"] = None
    tech = by_key(check(ips, alloc, INSTRUMENT_TYPES))[("IPS-4.3", "Technology", "max")]
    assert tech.observed * 100 == pytest.approx(27.96, abs=CENT)


def test_position_reads_the_published_share_and_does_not_divide(ips):
    """IPS-4.1 and 4.2 read `pct_of_total` from the position line; the
    market value is not divided. Same falsifier as the sector arm."""
    alloc = allocation()
    line = _line(alloc, "by_position", "JPM")
    line["market_value"] = 1.0
    line["pct_of_invested"] = None
    keys = by_key(check(ips, alloc, INSTRUMENT_TYPES))
    assert keys[("IPS-4.1", "JPM", "max")].observed * 100 == pytest.approx(8.68, abs=CENT)
    assert keys[("IPS-4.2", "JPM", "max")].observed * 100 == pytest.approx(8.68, abs=CENT)


def test_band_reads_the_same_field(ips):
    """Every clause reads one name for the share of total. The line's other
    share and its market value are not read."""
    alloc = allocation()
    line = _line(alloc, "by_asset_class", "Equity")
    line["market_value"] = 1.0
    line["pct_of_invested"] = 0.5
    equity = by_key(check(ips, alloc, INSTRUMENT_TYPES))[("IPS-3.1", "Equity", "max")]
    assert equity.observed * 100 == pytest.approx(69.41, abs=CENT)


def test_distances_reconcile(findings):
    for f in findings:
        if f.status == EXEMPT:
            continue
        signed = (f.observed - f.limit) if f.bound == "max" else (f.limit - f.observed)
        assert f.distance_pp == pytest.approx(signed * 100, abs=1e-9)
        assert f.distance_value == pytest.approx(signed * TOTAL, abs=1e-6)
        assert (f.status == BREACH) == (signed > 0)


def test_at_the_limit_passes(ips):
    """D9. A position at exactly 12.00% of total is ok under IPS-4.1."""
    alloc = allocation()
    _line(alloc, "by_position", "JPM")["pct_of_total"] = 0.12
    f = by_key(check(ips, alloc, INSTRUMENT_TYPES))[("IPS-4.1", "JPM", "max")]
    assert f.status == OK and f.distance_pp == pytest.approx(0.0, abs=1e-9)


# --- raises -----------------------------------------------------------------

def test_unknown_instrument_type_raises(ips):
    types = {**INSTRUMENT_TYPES, "JNJ": None}
    with pytest.raises(ComplianceError, match="JNJ=None"):
        check(ips, allocation(), types)
    types = {**INSTRUMENT_TYPES, "JNJ": "etf"}
    with pytest.raises(ComplianceError, match="JNJ='etf'"):
        check(ips, allocation(), types)


def test_missing_asset_class_line_raises(ips):
    alloc = allocation()
    for line in alloc["by_asset_class"]["lines"]:
        if line["label"] == "Real Estate":
            line["label"] = "Real estate"
    with pytest.raises(ComplianceError, match="names asset class 'Real Estate'"):
        check(ips, alloc, INSTRUMENT_TYPES)


def test_fund_inside_a_sector_raises(ips):
    alloc = allocation()
    alloc["by_sector"]["lines"][0]["tickers"].append("SPY")
    with pytest.raises(ComplianceError, match="contains funds \\['SPY'\\]"):
        check(ips, alloc, INSTRUMENT_TYPES)


@pytest.mark.parametrize("view, label", [
    ("by_asset_class", "Equity"), ("by_sector", "Technology"), ("by_position", "SPY")])
def test_missing_share_of_total_raises(ips, view, label):
    """A line without `pct_of_total` is not divided for; the checker raises."""
    alloc = allocation()
    del _line(alloc, view, label)["pct_of_total"]
    with pytest.raises(ComplianceError, match=f"{label}.*pct_of_total"):
        check(ips, alloc, INSTRUMENT_TYPES)


def test_missing_position_view_raises(ips):
    alloc = allocation()
    del alloc["by_position"]
    with pytest.raises(ComplianceError, match="by_position"):
        check(ips, alloc, INSTRUMENT_TYPES)


def test_missing_total_raises(ips):
    alloc = allocation()
    del alloc["by_asset_class"]["total_value"]
    with pytest.raises(ComplianceError, match="total_value"):
        check(ips, alloc, INSTRUMENT_TYPES)


# --- refuse: the hypothetical weight of 3.1 ----------------------------------

def test_fifteen_percent_is_refused_on_both_concentration_clauses(ips):
    out = {f.clause: f for f in refuse(ips, 0.15)}
    assert set(out) == {"IPS-4.1", "IPS-4.2"}
    assert out["IPS-4.1"].status == REFUSED
    assert out["IPS-4.1"].distance_pp == pytest.approx(3.00, abs=1e-9)
    assert out["IPS-4.2"].status == REFUSED
    assert out["IPS-4.2"].distance_pp == pytest.approx(5.00, abs=1e-9)
    for f in out.values():
        assert f.distance_value is None and f.observed == 0.15 and f.bound == "max"


def test_a_permitted_weight_is_ok_not_refused(ips):
    out = {f.clause: f.status for f in refuse(ips, 0.10)}
    assert out == {"IPS-4.1": OK, "IPS-4.2": OK}      # 10% is exactly at 4.2 (D9)
    out = {f.clause: f.status for f in refuse(ips, 0.12)}
    assert out == {"IPS-4.1": OK, "IPS-4.2": REFUSED}


def test_refuse_rejects_a_non_fraction(ips):
    with pytest.raises(ComplianceError, match="not a fraction"):
        refuse(ips, 15)
