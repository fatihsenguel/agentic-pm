"""
The metrics held to tests/golden/expected_values.md Part 10 C.

Every expected figure here is copied from Part 10, computed by hand from the
synthetic figures in Part 10 A by the formulas in Part 10 B (D24). If a test
fails, the module or the reference is wrong and that gets resolved
deliberately. Do NOT update these figures to match code output.

The fixture is the figures block in the shape the screen will read - one
company, its fiscal years with their end and filed dates and reported
figures, the shares, the price and the range with their as-of dates -
typed from Part 10 A by hand.

The module is imported inside a fixture so that, before it exists, this
file is a list of errors and not an interrupted suite.
"""

import datetime as dt

import pytest


AS_OF = dt.date(2026, 9, 10)

YEARS = {
    "FY2021": {"ends": "2021-12-31", "filed": "2022-02-04",
               "operating_income": 20_000.0, "tax_rate": 0.20,
               "equity": 120_000.0, "debt": 20_000.0, "cash": 40_000.0},
    "FY2022": {"ends": "2022-12-31", "filed": "2023-02-03",
               "operating_income": 13_500.0, "tax_rate": 0.20,
               "equity": 128_000.0, "debt": 22_000.0, "cash": 42_000.0},
    "FY2023": {"ends": "2023-12-31", "filed": "2024-02-02",
               "revenue": 100_000.0, "gross_profit": 55_000.0,
               "operating_income": 24_000.0, "tax_rate": 0.20,
               "equity": 140_000.0, "debt": 20_000.0, "cash": 40_000.0},
    "FY2024": {"ends": "2024-12-31", "filed": "2025-02-05",
               "revenue": 112_000.0, "gross_profit": 63_840.0,
               "operating_income": 30_000.0, "tax_rate": 0.20,
               "equity": 150_000.0, "debt": 18_000.0, "cash": 43_000.0},
    "FY2025": {"ends": "2025-12-31", "filed": "2026-02-04",
               "revenue": 125_000.0, "gross_profit": 72_500.0,
               "operating_income": 36_000.0, "tax_rate": 0.20,
               "depreciation_amortisation": 16_000.0,
               "operating_cash_flow": 52_780.0, "capex": 22_000.0,
               "equity": 170_000.0, "debt": 16_000.0, "cash": 42_000.0},
}


def figures(**overrides):
    block = {
        "ticker": "GOOGL",
        "currency": "USD",
        "source": "expected_values.md Part 10",
        "shares_outstanding": 4_000.0,
        "price": {"value": 171.00, "as_of": "2026-09-10"},
        "valuation_range": {"low": 180.00, "high": 240.00, "as_of": "2026-09-10"},
        "years": {label: dict(year) for label, year in YEARS.items()},
    }
    block.update(overrides)
    return block


@pytest.fixture(scope="module")
def fundamentals():
    from portfolio_tool.quant import fundamentals
    return fundamentals


@pytest.fixture(scope="module")
def metrics(fundamentals):
    return fundamentals.metrics_by_year(figures())


# --- Part 10 C -------------------------------------------------------------

@pytest.mark.parametrize("year, roic", [
    ("FY2021", 0.1600), ("FY2022", 0.1000), ("FY2023", 0.1600),
    ("FY2024", 0.1920), ("FY2025", 0.2000),
])
def test_return_on_invested_capital(metrics, year, roic):
    assert metrics[year]["return_on_invested_capital"] == pytest.approx(roic, abs=1e-12)


@pytest.mark.parametrize("year, margin", [
    ("FY2023", 0.5500), ("FY2024", 0.5700), ("FY2025", 0.5800),
])
def test_gross_margin(metrics, year, margin):
    assert metrics[year]["gross_margin"] == pytest.approx(margin, abs=1e-12)


def test_net_debt_to_ebitda(metrics):
    assert metrics["FY2025"]["net_debt_to_ebitda"] == pytest.approx(-0.5000, abs=1e-12)


def test_free_cash_flow_yield(metrics):
    assert metrics["FY2025"]["free_cash_flow_yield"] == pytest.approx(0.0450, abs=1e-12)


def test_a_metric_whose_inputs_a_year_lacks_is_absent_not_zero(metrics):
    """Part 10 A's blank cells: FY2021 has no revenue, so no gross margin;
    only FY2025 has D&A and cash flows. Absent, never zero, never raised
    here - whether the absence matters is the screen's question (D25)."""
    assert "gross_margin" not in metrics["FY2021"]
    assert "gross_margin" not in metrics["FY2022"]
    assert "net_debt_to_ebitda" not in metrics["FY2024"]
    assert "free_cash_flow_yield" not in metrics["FY2024"]
    assert set(metrics) == set(YEARS)


def test_the_vocabulary_is_what_is_computed(fundamentals, metrics):
    """Every metric key the philosophy may name is one this module computes,
    and nothing is computed under a key the vocabulary lacks."""
    assert set(fundamentals.METRICS) == {
        "return_on_invested_capital", "gross_margin",
        "net_debt_to_ebitda", "free_cash_flow_yield",
    }
    for year in metrics.values():
        assert set(year) <= set(fundamentals.METRICS)


# --- D21: which years count -------------------------------------------------

def test_years_filed_by_the_as_of_date(fundamentals):
    assert fundamentals.years_filed_by(figures(), AS_OF) == [
        "FY2021", "FY2022", "FY2023", "FY2024", "FY2025"]


def test_a_year_not_yet_filed_is_not_a_year(fundamentals):
    assert fundamentals.years_filed_by(figures(), dt.date(2025, 6, 30)) == [
        "FY2021", "FY2022", "FY2023", "FY2024"]


def test_years_come_back_in_fiscal_order_whatever_the_file_order(fundamentals):
    shuffled = figures()
    shuffled["years"] = {k: shuffled["years"][k] for k in ["FY2024", "FY2021", "FY2025", "FY2023", "FY2022"]}
    assert fundamentals.years_filed_by(shuffled, AS_OF) == [
        "FY2021", "FY2022", "FY2023", "FY2024", "FY2025"]


# --- Part 10 E, D23's row ---------------------------------------------------

def test_exactly_two_times_ebitda(fundamentals):
    block = figures()
    block["years"]["FY2025"].update({"debt": 120_000.0, "cash": 16_000.0})
    assert fundamentals.metrics_by_year(block)["FY2025"]["net_debt_to_ebitda"] == 2.0


# --- raises -----------------------------------------------------------------

def test_no_years_raises(fundamentals):
    with pytest.raises(fundamentals.FundamentalsError, match="no fiscal years"):
        fundamentals.metrics_by_year(figures(years={}))


@pytest.mark.parametrize("key", ["ends", "filed"])
def test_a_year_without_its_dates_raises(fundamentals, key):
    block = figures()
    del block["years"]["FY2023"][key]
    with pytest.raises(fundamentals.FundamentalsError, match=f"FY2023.*{key}"):
        fundamentals.years_filed_by(block, AS_OF)


def test_zero_ebitda_raises_rather_than_dividing(fundamentals):
    block = figures()
    block["years"]["FY2025"].update({"operating_income": 16_000.0, "depreciation_amortisation": -16_000.0})
    with pytest.raises(fundamentals.FundamentalsError, match="FY2025.*EBITDA"):
        fundamentals.metrics_by_year(block)


def test_zero_invested_capital_raises_rather_than_dividing(fundamentals):
    block = figures()
    block["years"]["FY2021"].update({"cash": 140_000.0})
    with pytest.raises(fundamentals.FundamentalsError, match="FY2021.*invested capital"):
        fundamentals.metrics_by_year(block)


def test_a_figure_that_is_not_a_number_raises(fundamentals):
    block = figures()
    block["years"]["FY2025"]["revenue"] = "125,000"
    with pytest.raises(fundamentals.FundamentalsError, match="FY2025.*revenue"):
        fundamentals.metrics_by_year(block)
