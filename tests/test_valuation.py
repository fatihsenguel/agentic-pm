"""
quant/valuation.py held to tests/golden/expected_values.md Part 11.

Every expected figure here is copied from Part 11, computed by hand on
Alphabet's and Apple's filed FY2025 figures with the synthetic assumptions
of Part 11 A. If a test fails, the module or the reference is wrong and
that gets resolved deliberately. Do NOT update these figures to match code
output.

  D37  One formula, run once at each of two stated growth rates: the low
       end is the low rate, the high end the high rate. No midpoint, no
       spread.
  D38  Five assumptions, each with the id of the clause or entry that
       states it, reaching the record as name, value and source.
  D39  The latest fiscal year filed by the as-of date, for every input at
       once; net debt as quant/fundamentals computes it; the year's own
       share count.
  D40  The record carries low, high, as-of, the year with its dates, the
       source and the assumptions, and no filed figure. Six conditions
       raise, naming which; nothing is sorted, clamped or filled.

The blocks are typed from Part 11 B in whole dollars and whole shares, as
the reader carries them. The module is imported inside a fixture so that,
before it exists, this file is a list of errors and not an interrupted
suite.
"""

import datetime as dt
from decimal import Decimal

import pytest


AS_OF = dt.date(2026, 9, 17)

# Part 11 A. Values as the documents would state them, with their sources.
ASSUMPTIONS = {
    "required_return": {"value": 0.09, "source": "PHI-4.3"},
    "terminal_growth": {"value": 0.03, "source": "PHI-4.3"},
    "horizon_years": {"value": 10, "source": "PHI-4.3"},
    "growth_low": {"value": 0.06, "source": "W-1"},
    "growth_high": {"value": 0.12, "source": "W-1"},
}


def _million(n):
    return Decimal(n) * Decimal(1_000_000)


# Part 11 B, whole dollars; the count in whole shares.
ALPHABET_FY2025 = {
    "ends": dt.date(2025, 12, 31), "filed": dt.date(2026, 2, 5),
    "operating_cash_flow": _million(164_713), "capex": _million(91_447),
    "commercial_paper": Decimal(0), "long_term_debt_current": _million(1_996),
    "long_term_debt_noncurrent": _million(46_547), "cash": _million(30_708),
    "shares_outstanding": Decimal(12_088_000_000),
}
ALPHABET_FY2024 = {
    "ends": dt.date(2024, 12, 31), "filed": dt.date(2025, 2, 5),
    "operating_cash_flow": _million(125_299), "capex": _million(52_535),
    "commercial_paper": _million(2_300), "long_term_debt_current": _million(999),
    "long_term_debt_noncurrent": _million(10_883), "cash": _million(23_466),
    "shares_outstanding": Decimal(12_211_000_000),
}
APPLE_FY2025 = {
    "ends": dt.date(2025, 9, 27), "filed": dt.date(2025, 10, 31),
    "operating_cash_flow": _million(111_482), "capex": _million(12_715),
    "commercial_paper": _million(7_979), "long_term_debt_current": _million(12_350),
    "long_term_debt_noncurrent": _million(78_328), "cash": _million(35_934),
    "shares_outstanding": Decimal(14_773_260_000),
}


def alphabet(**overrides):
    block = {"ticker": "GOOGL", "currency": "USD", "source": "EDGAR company facts",
             "years": {"FY2024": dict(ALPHABET_FY2024), "FY2025": dict(ALPHABET_FY2025)}}
    block.update(overrides)
    return block


def apple():
    return {"ticker": "AAPL", "currency": "USD", "source": "EDGAR company facts",
            "years": {"FY2025": dict(APPLE_FY2025)}}


def assumptions(**changes):
    out = {name: dict(entry) for name, entry in ASSUMPTIONS.items()}
    for name, value in changes.items():
        out[name] = {"value": value, "source": out[name]["source"]}
    return out


@pytest.fixture(scope="module")
def valuation():
    from portfolio_tool.quant import valuation
    assert hasattr(valuation, "valuation_range"), "no valuation_range in valuation"
    return valuation


@pytest.fixture(scope="module")
def alphabet_range(valuation):
    return valuation.valuation_range(alphabet(), ASSUMPTIONS, AS_OF)


@pytest.fixture(scope="module")
def apple_range(valuation):
    return valuation.valuation_range(apple(), ASSUMPTIONS, AS_OF)


# --- Part 11 B: the inputs -----------------------------------------------------

def test_free_cash_flow_is_exact(valuation):
    assert valuation.free_cash_flow("FY2025", ALPHABET_FY2025) == _million(73_266)
    assert valuation.free_cash_flow("FY2025", APPLE_FY2025) == _million(98_767)


def test_net_debt_is_the_metrics_own(valuation):
    """D39: one arithmetic path. Alphabet 17,835, Apple 62,723 (Part 12 G)."""
    from portfolio_tool.quant.fundamentals import net_debt
    assert net_debt("FY2025", ALPHABET_FY2025) == _million(17_835)
    assert net_debt("FY2025", APPLE_FY2025) == _million(62_723)


# --- Part 11 C: the range ------------------------------------------------------

def test_the_alphabet_range(alphabet_range):
    assert round(alphabet_range["low"], 2) == 129.39
    assert round(alphabet_range["high"], 2) == 205.62
    assert alphabet_range["low"] == pytest.approx(129.3871305225, abs=1e-9)
    assert alphabet_range["high"] == pytest.approx(205.6162184284, abs=1e-9)


def test_the_apple_range(apple_range):
    assert round(apple_range["low"], 2) == 140.10
    assert round(apple_range["high"], 2) == 224.18
    assert apple_range["low"] == pytest.approx(140.0996741701, abs=1e-9)
    assert apple_range["high"] == pytest.approx(224.1826772441, abs=1e-9)


@pytest.mark.parametrize("fcf0, g, pv_years, ev", [
    (_million(73_266), "0.06", 630_425.0, 1_581_866.6),
    (_million(73_266), "0.12", 853_248.8, 2_503_323.8),
    (_million(98_767), "0.06", 849_851.1, 2_132_451.9),
    (_million(98_767), "0.12", 1_150_231.0, 3_374_632.0),
])
def test_the_steps_to_the_dollar_of_a_tenth_of_a_million(valuation, fcf0, g, pv_years, ev):
    """Part 11 C's totals: the sum of the ten discounted years and the
    enterprise value, each to a tenth of a million."""
    years, enterprise = valuation.enterprise_value(
        fcf0, Decimal(g), Decimal("0.09"), Decimal("0.03"), 10)
    assert float(years / 1_000_000) == pytest.approx(pv_years, abs=0.05)
    assert float(enterprise / 1_000_000) == pytest.approx(ev, abs=0.05)


def test_the_ends_are_two_runs_of_one_formula(valuation, alphabet_range):
    """D37: the low end is the formula at growth_low and the high end at
    growth_high; nothing sits between them."""
    low = valuation.valuation_range(alphabet(), assumptions(growth_high=0.07), AS_OF)
    assert low["low"] == alphabet_range["low"]
    high = valuation.valuation_range(alphabet(), assumptions(growth_low=0.11), AS_OF)
    assert high["high"] == alphabet_range["high"]


# --- Part 11 D: falsifiers -----------------------------------------------------

@pytest.mark.parametrize("fcf0, g, expected", [
    (_million(73_266), "0.06", "862910.6666666666666666666667"),
    (_million(73_266), "0.12", "911754.6666666666666666666667"),
    (_million(98_767), "0.06", "1163255.777777777777777777778"),
    (_million(98_767), "0.12", "1229100.444444444444444444444"),
])
def test_a_one_year_horizon_with_no_terminal_growth_collapses_to_one_line(valuation, fcf0, g, expected):
    """N = 1 and gT = 0: enterprise value is FCF0 x (1 + g) / r. A terminal
    value discounted a year too many or too few, or grown once more, misses
    by 1.09, 1.06 or 1.12."""
    _, enterprise = valuation.enterprise_value(fcf0, Decimal(g), Decimal("0.09"), Decimal(0), 1)
    assert enterprise / 1_000_000 == pytest.approx(Decimal(expected), rel=Decimal("1e-12"))


def test_swapped_rates_raise_and_are_not_sorted(valuation):
    with pytest.raises(valuation.ValuationError, match="growth_low.*growth_high"):
        valuation.valuation_range(alphabet(), assumptions(growth_low=0.12, growth_high=0.06), AS_OF)


def test_equal_rates_raise_as_a_point(valuation):
    with pytest.raises(valuation.ValuationError, match="growth_low.*growth_high"):
        valuation.valuation_range(alphabet(), assumptions(growth_low=0.06, growth_high=0.06), AS_OF)


@pytest.mark.parametrize("r", [0.03, 0.02])
def test_a_required_return_at_or_below_the_terminal_growth_raises(valuation, r):
    with pytest.raises(valuation.ValuationError, match="required_return.*terminal_growth"):
        valuation.valuation_range(alphabet(), assumptions(required_return=r), AS_OF)


@pytest.mark.parametrize("capex", [164_713, 170_000])
def test_a_non_positive_free_cash_flow_raises(valuation, capex):
    block = alphabet()
    block["years"]["FY2025"]["capex"] = _million(capex)
    with pytest.raises(valuation.ValuationError, match="FY2025.*free cash flow"):
        valuation.valuation_range(block, ASSUMPTIONS, AS_OF)


def test_a_non_positive_low_end_raises(valuation):
    """Net debt of 1,581,866.6 million or more leaves nothing at the low end;
    the high end is positive and is not printed alone. Non-current debt of
    1,650,000 million puts net debt at 1,621,288."""
    block = alphabet()
    block["years"]["FY2025"]["long_term_debt_noncurrent"] = _million(1_650_000)
    with pytest.raises(valuation.ValuationError, match="FY2025.*low end"):
        valuation.valuation_range(block, ASSUMPTIONS, AS_OF)


def test_a_missing_count_raises(valuation):
    block = alphabet()
    del block["years"]["FY2025"]["shares_outstanding"]
    with pytest.raises(valuation.ValuationError, match="FY2025.*shares_outstanding"):
        valuation.valuation_range(block, ASSUMPTIONS, AS_OF)


def test_the_as_of_date_moves_the_year(valuation):
    """D39, D21: as of 2026-01-31 Alphabet's latest filed year is FY2024."""
    record = valuation.valuation_range(alphabet(), ASSUMPTIONS, dt.date(2026, 1, 31))
    assert (record["year"], record["ends"], record["filed"]) == (
        "FY2024", dt.date(2024, 12, 31), dt.date(2025, 2, 5))
    assert record["as_of"] == dt.date(2026, 1, 31)


def test_no_year_filed_by_the_as_of_date_raises(valuation):
    with pytest.raises(valuation.ValuationError, match="no fiscal year"):
        valuation.valuation_range(alphabet(), ASSUMPTIONS, dt.date(2025, 1, 1))


# --- D38 and D40: the assumptions and the record -------------------------------

@pytest.mark.parametrize("name", sorted(ASSUMPTIONS))
def test_an_unstated_assumption_raises(valuation, name):
    stated = assumptions()
    del stated[name]
    with pytest.raises(valuation.ValuationError, match=name):
        valuation.valuation_range(alphabet(), stated, AS_OF)


def test_an_assumption_no_formula_reads_raises(valuation):
    stated = assumptions()
    stated["exit_multiple"] = {"value": 15, "source": "PHI-4.3"}
    with pytest.raises(valuation.ValuationError, match="exit_multiple"):
        valuation.valuation_range(alphabet(), stated, AS_OF)


@pytest.mark.parametrize("name, value", [
    ("required_return", "9%"), ("horizon_years", 0), ("horizon_years", 2.5), ("growth_low", True),
])
def test_an_assumption_that_is_not_a_number_of_its_kind_raises(valuation, name, value):
    with pytest.raises(valuation.ValuationError, match=name):
        valuation.valuation_range(alphabet(), assumptions(**{name: value}), AS_OF)


def test_an_assumption_without_a_source_raises(valuation):
    stated = assumptions()
    stated["growth_low"] = {"value": 0.06}
    with pytest.raises(valuation.ValuationError, match="growth_low.*source"):
        valuation.valuation_range(alphabet(), stated, AS_OF)


def test_the_record_carries_d40_and_no_filed_figure(alphabet_range):
    assert set(alphabet_range) == {"low", "high", "as_of", "year", "ends", "filed", "source",
                                   "assumptions"}
    assert isinstance(alphabet_range["low"], float) and isinstance(alphabet_range["high"], float)
    assert alphabet_range["low"] < alphabet_range["high"]
    assert alphabet_range["as_of"] == AS_OF
    assert (alphabet_range["year"], alphabet_range["ends"], alphabet_range["filed"]) == (
        "FY2025", dt.date(2025, 12, 31), dt.date(2026, 2, 5))
    assert alphabet_range["source"] == "EDGAR company facts"
    assert alphabet_range["assumptions"] == ASSUMPTIONS


def test_a_block_without_a_source_raises(valuation):
    block = alphabet()
    del block["source"]
    with pytest.raises(valuation.ValuationError, match="source"):
        valuation.valuation_range(block, ASSUMPTIONS, AS_OF)
