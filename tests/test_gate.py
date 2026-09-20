"""
The gate held to Part 17 of `tests/golden/expected_values.md`, computed by
hand on 2026-09-20 from the settled closes of 2026-09-18 before this module
existed.

Every figure asserted here is Part 17's, transcribed from the document and
not from a run. If the module and the Part disagree, one of them is wrong
and the Part does not move to match the code.

The allocation fixture is the block PortfolioAnalysisAgent publishes, built
from Part 17 B: nine holdings at their 09-18 market values, cash 15,500.00,
total 408,447.50. The gate hands it to `compliance.check`, so these tests
also pin that the two Parts are reproduced by one piece of arithmetic.

The module is imported inside a fixture so that, before it exists, this
file is a list of errors and not an interrupted suite.
"""

import pytest


# Part 17 B. Market value, asset class, instrument type, sector.
HOLDINGS = [
    ("SPY", 76169.00, "Equity", "fund", None),
    ("AAPL", 67226.00, "Equity", "share", "Technology"),
    ("MSFT", 49378.00, "Equity", "share", "Technology"),
    ("TLT", 40625.00, "Fixed Income", "fund", None),
    ("JNJ", 40498.50, "Equity", "share", "Healthcare"),
    ("GLD", 40117.00, "Commodity", "fund", None),
    ("JPM", 34967.00, "Equity", "share", "Financials"),
    ("VNQ", 27873.00, "Real Estate", "fund", None),
    ("NEE", 16094.00, "Equity", "share", "Utilities"),
]
CASH = 15500.00
TOTAL = 408447.50
UNSECTORED = "(no sector)"

# Part 17 C.
NEW_MONEY = {0.06: 26071.12, 0.15: 72078.97}
TOTAL_AFTER = {0.06: 434518.62, 0.15: 480526.47}


@pytest.fixture
def gate():
    from portfolio_tool import gate
    return gate


@pytest.fixture
def ips():
    from portfolio_tool.ips import load_ips
    return load_ips("ips.toml")


@pytest.fixture
def candidate():
    """W-1 as the committed watchlist states it (decisions 63 and 65)."""
    from portfolio_tool.watchlist import load_watchlist
    return load_watchlist("watchlist.toml").candidates["W-1"]


# A portfolio inside every limit, to reach the branch where IPS-5.3's first
# limb has nothing to restore. Not a reference: the benchmark portfolio
# cannot reach it, Equity standing above its ceiling at every weight.
INSIDE = [
    ("EQ1", 90000.00, "Equity", "share", "Technology"),
    ("EQ2", 90000.00, "Equity", "share", "Healthcare"),
    ("EQ3", 90000.00, "Equity", "fund", None),
    ("EQ4", 90000.00, "Equity", "fund", None),
    ("EQ5", 90000.00, "Equity", "fund", None),
    ("FI1", 100000.00, "Fixed Income", "fund", None),
    ("FI2", 100000.00, "Fixed Income", "fund", None),
    ("CO1", 100000.00, "Commodity", "fund", None),
    ("RE1", 100000.00, "Real Estate", "fund", None),
]
INSIDE_CASH = 150000.00

# A portfolio with exactly one breach, IPS-4.3 on Technology at 26%, which
# a 6% purchase in another sector dilutes to 24.44% and clears. It reaches
# the branch where the first limb binds and the purchase restores what was
# breached - the one case that tells "fail when something is still
# breached" apart from "fail whenever anything was breached". Not a
# reference: the benchmark portfolio cannot reach it, IPS-3.1 being
# breached there at every weight.
RESTORED = [
    ("TECH1", 90000.00, "Equity", "share", "Technology"),
    ("TECH2", 90000.00, "Equity", "share", "Technology"),
    ("TECH3", 80000.00, "Equity", "share", "Technology"),
    ("EQ4", 90000.00, "Equity", "fund", None),
    ("EQ5", 100000.00, "Equity", "fund", None),
    ("FI1", 100000.00, "Fixed Income", "fund", None),
    ("FI2", 100000.00, "Fixed Income", "fund", None),
    ("CO1", 100000.00, "Commodity", "fund", None),
    ("RE1", 100000.00, "Real Estate", "fund", None),
]
RESTORED_CASH = 150000.00

# A portfolio whose one breach - IPS-4.1 on a fund at 12.5% - is diluted
# away by a 15% purchase that breaches IPS-4.1 itself. The same clause is
# breached before and after on different subjects, which is what tells a
# comparison of (clause, subject) pairs apart from one of clause ids.
CREATED = [
    ("BIG", 125000.00, "Equity", "fund", None),
    ("EQ2", 90000.00, "Equity", "share", "Technology"),
    ("EQ3", 90000.00, "Equity", "fund", None),
    ("EQ4", 95000.00, "Equity", "fund", None),
    ("EQ5", 50000.00, "Equity", "fund", None),
    ("FI1", 100000.00, "Fixed Income", "fund", None),
    ("FI2", 100000.00, "Fixed Income", "fund", None),
    ("CO1", 100000.00, "Commodity", "fund", None),
    ("RE1", 100000.00, "Real Estate", "fund", None),
]
CREATED_CASH = 150000.00


def _line(label, market_value, tickers, total=TOTAL):
    return {"label": label, "market_value": market_value, "cost_basis": market_value,
            "tickers": tickers, "pct_of_sectored": None, "pct_of_invested": None,
            "pct_of_total": market_value / total}


def _allocation(holdings, cash):
    """The block PortfolioAnalysisAgent publishes, from a list of
    (ticker, market value, asset class, instrument type, sector).

    Cash is a line of the asset-class view and of no other: `by_position`
    has no cash line, cash not being a holding and IPS-4.1 being about
    instruments (quant/allocation.py), and `by_sector` counts holdings.
    """
    total = sum(h[1] for h in holdings) + cash
    classes, sectors, positions = {}, {}, []
    for ticker, value, asset_class, _type, sector in holdings:
        classes.setdefault(asset_class, [0.0, []])
        classes[asset_class][0] += value
        classes[asset_class][1].append(ticker)
        label = sector or UNSECTORED
        sectors.setdefault(label, [0.0, []])
        sectors[label][0] += value
        sectors[label][1].append(ticker)
        positions.append(_line(ticker, value, [ticker], total))
    classes["Cash"] = [cash, []]
    invested = total - cash
    return {
        "by_asset_class": {
            "lines": [_line(k, v, t, total) for k, (v, t) in classes.items()],
            "invested_value": invested, "cash_balance": cash, "total_value": total,
        },
        "by_sector": {
            "lines": [_line(k, v, t, total) for k, (v, t) in sectors.items()],
            "invested_value": invested,
            "sectored_value": invested - sectors.get(UNSECTORED, [0.0])[0],
            "total_value": total,
        },
        "by_position": {
            "lines": positions, "invested_value": invested,
            "cash_balance": cash, "total_value": total,
        },
    }


@pytest.fixture
def allocation():
    """Part 17 B as PortfolioAnalysisAgent publishes it."""
    return _allocation(HOLDINGS, CASH)


@pytest.fixture
def types():
    return {ticker: kind for ticker, _v, _c, kind, _s in HOLDINGS}


def _run(gate, ips, allocation, types, candidate, weight):
    return gate.gate(ips, allocation, types, candidate, weight, "W-1")


def _found(result, clause, subject):
    for finding in result.findings:
        if finding.clause == clause and finding.subject == subject:
            return finding
    raise AssertionError(f"no finding for {clause} on {subject}")


def _bound(result, clause, subject, bound):
    for finding in result.findings:
        if (finding.clause, finding.subject, finding.bound) == (clause, subject, bound):
            return finding
    raise AssertionError(f"no {bound} finding for {clause} on {subject}")


# --- the funding (Part 17 A and C) -------------------------------------------------

@pytest.mark.parametrize("weight", [0.06, 0.15])
def test_the_new_money_and_the_grown_total_are_part_17s(gate, ips, allocation, types,
                                                        candidate, weight):
    """Decision 64: M = w x T / (1 - w), T' = T / (1 - w)."""
    result = _run(gate, ips, allocation, types, candidate, weight)
    assert round(result.new_money, 2) == NEW_MONEY[weight]
    assert round(result.total_after, 2) == TOTAL_AFTER[weight]
    assert result.total_before == TOTAL
    assert result.funding == gate.FUNDING


@pytest.mark.parametrize("weight", [0.06, 0.15])
def test_the_candidates_share_is_the_weight_exactly(gate, ips, allocation, types,
                                                    candidate, weight):
    """Not a division that lands a hair off it: the weight is defined as
    that share, so a 12% weight must not read as 12.000000001% and breach
    IPS-4.1 at a limit D9 says passes."""
    result = _run(gate, ips, allocation, types, candidate, weight)
    assert _bound(result, "IPS-4.1", "GOOGL", "max").observed == weight


def test_the_entry_is_cited_as_the_weights_source(gate, ips, allocation, types, candidate):
    result = _run(gate, ips, allocation, types, candidate, 0.06)
    assert (result.ticker, result.weight, result.weight_source) == ("GOOGL", 0.06, "W-1")
    assert (result.asset_class, result.sector, result.instrument_type) == (
        "Equity", "Communication Services", "share")


# --- section 3 (Part 17 D) ---------------------------------------------------------

@pytest.mark.parametrize("weight,pct,pp", [(0.06, 71.4362, 6.4362), (0.15, 74.1710, 9.1710)])
def test_ips_3_1_breaches_at_both_weights(gate, ips, allocation, types, candidate,
                                          weight, pct, pp):
    """Part 17 D: equity is above its ceiling before the purchase and an
    equity purchase funded by new money raises it, so this clause fails at
    every weight. The policy answering, not a defect."""
    result = _run(gate, ips, allocation, types, candidate, weight)
    finding = _bound(result, "IPS-3.1", "Equity", "max")
    assert finding.status == "breach"
    assert round(finding.observed * 100, 4) == pct
    assert round(finding.distance_pp, 4) == pp


@pytest.mark.parametrize("weight,expected", [
    (0.06, {"Fixed Income": 9.3494, "Commodity": 9.2325,
            "Real Estate": 6.4147, "Cash": 3.5672}),
    (0.15, {"Fixed Income": 8.4543, "Commodity": 8.3486,
            "Real Estate": 5.8005, "Cash": 3.2256}),
])
def test_the_other_bands_are_part_17s_and_all_ok(gate, ips, allocation, types, candidate,
                                                 weight, expected):
    result = _run(gate, ips, allocation, types, candidate, weight)
    for label, pct in expected.items():
        for finding in result.findings:
            if finding.clause.startswith("IPS-3.") and finding.subject == label:
                assert finding.status == "ok", (label, finding.bound)
                assert round(finding.observed * 100, 4) == pct, label


# --- section 4 (Part 17 E) ---------------------------------------------------------

def test_msft_crosses_back_inside_ips_4_1_having_traded_nothing(gate, ips, allocation,
                                                                types, candidate):
    """Part 17 E: 12.0892% before, 11.3638% at a 6% purchase. The
    denominator grew and its share fell. The before findings are what make
    this readable rather than an unexplained pass."""
    result = _run(gate, ips, allocation, types, candidate, 0.06)
    before = [f for f in result.findings_before
              if (f.clause, f.subject) == ("IPS-4.1", "MSFT")][0]
    after = _bound(result, "IPS-4.1", "MSFT", "max")
    assert before.status == "breach" and round(before.observed * 100, 4) == 12.0892
    assert after.status == "ok" and round(after.observed * 100, 4) == 11.3638


def test_the_technology_breach_clears_at_fifteen_percent(gate, ips, allocation, types,
                                                         candidate):
    """Part 17 E: 28.5481% before, 24.2659% after. Buying more equity, in
    another sector, with new money, clears a sector breach without a share
    being sold - and IPS-3.1 is worse at the same time. The case for the
    wide gate decision 68 kept."""
    result = _run(gate, ips, allocation, types, candidate, 0.15)
    before = [f for f in result.findings_before
              if (f.clause, f.subject) == ("IPS-4.3", "Technology")][0]
    after = _bound(result, "IPS-4.3", "Technology", "max")
    assert before.status == "breach" and round(before.observed * 100, 4) == 28.5481
    assert after.status == "ok" and round(after.observed * 100, 4) == 24.2659
    assert _bound(result, "IPS-3.1", "Equity", "max").status == "breach"


@pytest.mark.parametrize("weight,clause,status,pp,value", [
    (0.06, "IPS-4.1", "ok", None, None),
    (0.06, "IPS-4.2", "ok", None, None),
    (0.15, "IPS-4.1", "breach", 3.0000, 14415.79),
    (0.15, "IPS-4.2", "breach", 5.0000, 24026.32),
])
def test_the_candidates_own_concentration_clauses(gate, ips, allocation, types, candidate,
                                                  weight, clause, status, pp, value):
    """Part 17 E: clear at 6%, and the candidate's own IPS-4.1 and IPS-4.2
    fail at 15%. This is the difference the two weights were chosen for."""
    result = _run(gate, ips, allocation, types, candidate, weight)
    finding = _bound(result, clause, "GOOGL", "max")
    assert finding.status == status
    if status == "breach":
        assert round(finding.distance_pp, 4) == pp
        assert round(finding.distance_value, 2) == value


def test_the_candidate_opens_its_own_sector(gate, ips, allocation, types, candidate):
    """Part 17 E: Communication Services is a bucket the portfolio does not
    hold, which is why decision 63 states Alphabet's sector rather than
    letting it fall into the breached Technology one."""
    result = _run(gate, ips, allocation, types, candidate, 0.06)
    finding = _bound(result, "IPS-4.3", "Communication Services", "max")
    assert finding.status == "ok"
    assert round(finding.observed * 100, 4) == 6.0000


def test_the_funds_stay_exempt_under_ips_4_2(gate, ips, allocation, types, candidate):
    result = _run(gate, ips, allocation, types, candidate, 0.06)
    for ticker in ("SPY", "TLT", "GLD", "VNQ"):
        finding = _found(result, "IPS-4.2", ticker)
        assert finding.status == "exempt"
        assert finding.observed is None and finding.distance_pp is None


# --- IPS-5.3 (Part 17 F, D59) ------------------------------------------------------

@pytest.mark.parametrize("weight", [0.06, 0.15])
def test_ips_5_3_fails_at_both_weights_with_no_distance(gate, ips, allocation, types,
                                                        candidate, weight):
    """Part 17 F: a limit is breached before the purchase and the money
    goes entirely to Equity, restoring none of them. D59: no distance."""
    result = _run(gate, ips, allocation, types, candidate, weight)
    finding = _found(result, "IPS-5.3", "Equity")
    assert finding.status == "breach"
    assert finding.observed is None and finding.limit is None
    assert finding.distance_pp is None and finding.distance_value is None
    assert result.first_limb_binds is True
    assert ("IPS-3.1", "Equity") in result.unrestored


def test_a_purchase_that_restores_every_breach_satisfies_the_first_limb(
        gate, ips, candidate):
    """The first limb binds - IPS-4.3 is breached on Technology at 26% -
    and the purchase clears it by dilution, leaving nothing breached. The
    clause asks that new money go to whatever restores a breached limit,
    and this money did, so the finding is ok. This is the case that tells
    the rule apart from "fail whenever anything was breached before"."""
    portfolio = _allocation(RESTORED, RESTORED_CASH)
    types = {t: kind for t, _v, _c, kind, _s in RESTORED}
    result = gate.gate(ips, portfolio, types, candidate, 0.06, "W-1")
    before = [(f.clause, f.subject) for f in result.findings_before if f.status == "breach"]
    assert before == [("IPS-4.3", "Technology")]
    assert [f.clause for f in result.findings if f.status == "breach"] == []
    assert result.first_limb_binds is True
    assert result.unrestored == ()
    assert _found(result, "IPS-5.3", "Equity").status == "ok"
    assert result.permits is True


def test_a_breach_the_purchase_creates_is_not_ips_5_3s_to_report(gate, ips, candidate):
    """IPS-4.1 is breached before on BIG and after on the candidate, two
    different subjects. The money restored what was breached, so the first
    limb is satisfied and IPS-5.3 is ok; that the purchase breaches
    IPS-4.1 itself is IPS-4.1's finding to report, and it does, and the
    gate does not permit because of it. Comparing clause ids rather than
    (clause, subject) pairs would blame IPS-5.3 for it as well."""
    portfolio = _allocation(CREATED, CREATED_CASH)
    types = {t: kind for t, _v, _c, kind, _s in CREATED}
    result = gate.gate(ips, portfolio, types, candidate, 0.15, "W-1")
    before = [(f.clause, f.subject) for f in result.findings_before if f.status == "breach"]
    after = sorted((f.clause, f.subject) for f in result.findings if f.status == "breach")
    assert before == [("IPS-4.1", "BIG")]
    assert after == [("IPS-4.1", "GOOGL"), ("IPS-4.2", "GOOGL")]
    assert result.first_limb_binds is True
    assert result.unrestored == ()
    assert _found(result, "IPS-5.3", "Equity").status == "ok"
    assert result.permits is False


def test_the_fixture_inside_the_limits_really_is_inside_them(gate, ips, candidate):
    """The test below is worthless if the portfolio it uses breaches
    something, so the fixture is checked before it is relied on: nothing
    breached before the purchase, and nothing after it either."""
    inside = _allocation(INSIDE, INSIDE_CASH)
    types = {t: kind for t, _v, _c, kind, _s in INSIDE}
    result = gate.gate(ips, inside, types, candidate, 0.06, "W-1")
    assert [f.clause for f in result.findings_before if f.status == "breach"] == []
    assert [f.clause for f in result.findings if f.status == "breach"] == []


def test_the_first_limb_does_not_bind_on_a_portfolio_inside_its_limits(
        gate, ips, candidate):
    """With nothing breached before, the first limb has nothing to restore
    and the second limb is not computed, so the finding is ok and the
    clause is half-applied. `first_limb_binds` is what tells the formatter
    to say so."""
    inside = _allocation(INSIDE, INSIDE_CASH)
    types = {t: kind for t, _v, _c, kind, _s in INSIDE}
    result = gate.gate(ips, inside, types, candidate, 0.06, "W-1")
    finding = _found(result, "IPS-5.3", "Equity")
    assert finding.status == "ok"
    assert result.first_limb_binds is False
    assert result.unrestored == ()


# --- what it refuses ---------------------------------------------------------------

@pytest.mark.parametrize("weight", [0.0, 1.0, 1.5, -0.06, 6])
def test_a_weight_outside_the_open_unit_interval_is_refused(gate, ips, allocation, types,
                                                            candidate, weight):
    with pytest.raises(gate.GateError, match="not a fraction above 0 and below 1"):
        _run(gate, ips, allocation, types, candidate, weight)


def test_a_candidate_already_held_is_refused(gate, ips, allocation, types, candidate):
    """The gate checks a new position. Adding to one already held is a
    different question and no case asks it; answering it here would give a
    verdict on arithmetic nobody computed."""
    import dataclasses
    held = dataclasses.replace(candidate, ticker="AAPL")
    with pytest.raises(gate.GateError, match="AAPL is already a position"):
        _run(gate, ips, allocation, types, held, 0.06)


def test_an_asset_class_the_policy_has_no_band_for_is_refused(gate, ips, allocation,
                                                              types, candidate):
    """Part 17 G's gap in the other direction: a class section 3 states no
    band for cannot be checked, and a position in it is not reported clear."""
    import dataclasses
    crypto = dataclasses.replace(candidate, asset_class="Crypto")
    with pytest.raises(gate.GateError, match="states asset class 'Crypto'"):
        _run(gate, ips, allocation, types, crypto, 0.06)


def test_a_share_whose_sector_is_the_unsectored_label_is_refused(gate, ips, allocation,
                                                                 types, candidate):
    import dataclasses
    odd = dataclasses.replace(candidate, sector=UNSECTORED)
    with pytest.raises(gate.GateError, match="the label IPS-4.3 leaves out"):
        _run(gate, ips, allocation, types, odd, 0.06)


def test_a_fund_candidate_joins_the_unsectored_line(gate, ips, allocation, types, candidate):
    """IPS-4.3's own wording: holdings without a sector are outside the
    count. A fund is not given a sector bucket, which `compliance.check`
    would refuse anyway."""
    import dataclasses
    fund = dataclasses.replace(candidate, instrument_type="fund")
    result = _run(gate, ips, allocation, types, fund, 0.06)
    assert _found(result, "IPS-4.2", "GOOGL").status == "exempt"
    for finding in result.findings:
        assert not (finding.clause == "IPS-4.3"
                    and finding.subject == "Communication Services")


def test_an_allocation_missing_a_view_is_refused(gate, ips, allocation, types, candidate):
    allocation["by_sector"] = {"lines": []}
    with pytest.raises(gate.GateError, match="no by_sector lines"):
        _run(gate, ips, allocation, types, candidate, 0.06)


# --- decision 68's input ------------------------------------------------------------

def test_permits_is_false_while_any_finding_is_a_breach(gate, ips, allocation, types,
                                                        candidate):
    """Decision 68: the gate permits only when every finding is ok or
    exempt. On this portfolio it never does, IPS-3.1 failing at every
    weight."""
    for weight in (0.06, 0.15):
        assert _run(gate, ips, allocation, types, candidate, weight).permits is False
