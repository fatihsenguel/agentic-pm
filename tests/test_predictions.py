"""
The prediction scorer held to expected_values.md Part 14 (case 4.5; PHI-6.2;
D41 to D45): the ledger's statuses at three dates (A), the synthetic figure
predictions against Alphabet's filed FY2025 lines (B, C), the event shapes
(D) and the falsifier rows (E).

The block is hand-built in the reader's shape with the filed Decimals and
their provenance, so that this file holds the arithmetic and the source
without a database; the node's test holds the same scorer over the
fixture's stored rows. The score in the ledger is mine and is never
computed here: a scored prediction's four fields come out as they went in.

The module is imported inside a fixture so that, before it exists, this
file is a list of errors and not an interrupted suite.
"""

import datetime as dt
from decimal import Decimal

import pytest

from portfolio_tool.watchlist import Prediction, Score, load_watchlist, predictions as ledger_rows


AS_OF = dt.date(2026, 9, 18)
FILED = dt.date(2026, 2, 5)
ACCN = "0001652044-26-000018"

# Part 14 B: Alphabet's FY2025 lines as filed, USD, on the year's own 10-K.
FY2025 = {"ends": dt.date(2025, 12, 31), "filed": FILED,
          "revenue": Decimal("402836000000"), "cost_of_revenue": Decimal("162535000000")}
PROVENANCE = {
    "revenue": {"tag": "Revenues", "accn": ACCN, "form": "10-K", "filed": FILED},
    "cost_of_revenue": {"tag": "CostOfRevenue", "accn": ACCN, "form": "10-K", "filed": FILED},
}


def block(years=None, provenance=None, source="EDGAR"):
    out = {"currency": "USD", "as_of": AS_OF,
           "years": {"FY2025": dict(FY2025)} if years is None else years,
           "provenance": {"FY2025": dict(PROVENANCE)} if provenance is None else provenance}
    if source is not None:
        out["source"] = source
    return out


def figure(pid="S-1", metric="revenue", bound="min", value=400_000_000_000, period="FY2025",
           made_on=dt.date(2026, 1, 1), due=dt.date(2026, 3, 1), score=None):
    return Prediction(id=pid, candidate="W-1", made_on=made_on, due=due, kind="figure",
                      statement=f"{metric} {bound} {value} for {period}.", metric=metric,
                      bound=bound, value=value, period=period, score=score)


def event(pid="E-2", due=dt.date(2026, 3, 1), score=None):
    return Prediction(id=pid, candidate="W-1", made_on=dt.date(2026, 1, 1), due=due,
                      kind="event", statement="Something about the business.", score=score)


E1_SCORE = Score(outcome="the FY2025 annual report's segment note shows the cloud segment "
                         "with positive operating income for the full year",
                 source=f"10-K {ACCN} filed 2026-02-05, segment note",
                 scored_on=dt.date(2026, 3, 2), result="right")


@pytest.fixture
def scorer():
    from portfolio_tool import predictions
    return predictions


# --- A. the ledger as of three dates -------------------------------------------

@pytest.mark.parametrize("as_of, statuses, summary", [
    (dt.date(2026, 9, 18), ["open", "open", "open", "open"],
     {"predictions": 4, "scored": 0, "due": 0, "open": 4}),
    (dt.date(2027, 2, 1), ["open", "open", "due", "due"],
     {"predictions": 4, "scored": 0, "due": 2, "open": 2}),
    (dt.date(2027, 3, 1), ["due", "due", "due", "due"],
     {"predictions": 4, "scored": 0, "due": 4, "open": 0}),
])
def test_the_committed_ledger_at_three_dates(scorer, as_of, statuses, summary):
    rows = ledger_rows(load_watchlist("watchlist.toml"))
    result = scorer.ledger(rows, {}, as_of)
    assert [r.id for r in result.records] == ["W-1.1", "W-1.2", "W-2.1", "W-2.2"]
    assert [r.status for r in result.records] == statuses
    assert result.summary == summary
    for r in result.records:
        assert r.score is None and r.filing is None
        if r.status == "due":
            assert r.unscored, r.id
        else:
            assert r.unscored is None, r.id


def test_the_count_is_the_ledgers_and_the_four_counts_sum(scorer):
    rows = ledger_rows(load_watchlist("watchlist.toml"))
    for as_of in (dt.date(2026, 9, 18), dt.date(2027, 2, 1), dt.date(2027, 3, 1)):
        s = scorer.ledger(rows, {}, as_of).summary
        assert s["predictions"] == len(rows) == s["scored"] + s["due"] + s["open"]


# --- C. figure predictions against the filed figure ----------------------------

@pytest.mark.parametrize("pid, metric, bound, value, result", [
    ("S-1", "revenue", "min", 400_000_000_000, "right"),
    ("S-2", "revenue", "min", 410_000_000_000, "wrong"),
    ("S-3", "revenue", "min", 402_836_000_000, "right"),
    ("S-4", "revenue", "max", 400_000_000_000, "wrong"),
    ("S-5", "revenue", "max", 402_836_000_000, "right"),
    ("S-6", "gross_margin", "min", 0.59, "right"),
    ("S-7", "gross_margin", "min", 0.60, "wrong"),
])
def test_part_14_c(scorer, pid, metric, bound, value, result):
    p = figure(pid, metric, bound, value)
    filing = scorer.verdict(p, block(), AS_OF)
    assert filing.result == result
    assert (filing.form, filing.accn, filing.filed, filing.source) == ("10-K", ACCN, FILED, "EDGAR")


def test_the_s_1_record(scorer):
    r = scorer.record(figure(), block(), AS_OF)
    assert r.status == "due" and r.score is None and r.unscored is None and r.agrees is None
    assert r.filing.reported == 402_836_000_000.0 and isinstance(r.filing.reported, float)
    assert r.filing.result == "right"
    assert (r.id, r.candidate, r.kind, r.metric, r.bound, r.value, r.period) == (
        "S-1", "W-1", "figure", "revenue", "min", 400_000_000_000, "FY2025")
    assert (r.made_on, r.due) == (dt.date(2026, 1, 1), dt.date(2026, 3, 1))


def test_the_s_6_reported_figure_is_the_ratio_as_a_float(scorer):
    filing = scorer.verdict(figure("S-6", "gross_margin", "min", 0.59), block(), AS_OF)
    assert filing.reported == 0.5965231508603998


def test_no_decimal_reaches_a_record(scorer):
    r = scorer.record(figure(), block(), AS_OF)
    for v in (r.filing.reported, r.value):
        assert not isinstance(v, Decimal)


# --- D. event predictions ----------------------------------------------------------

def test_e_1_a_written_score_is_reported_as_written_and_nothing_is_computed(scorer):
    r = scorer.record(event("E-1", score=E1_SCORE), block(), AS_OF)
    assert r.status == "scored" and r.score == E1_SCORE
    assert r.filing is None and r.unscored is None and r.agrees is None


def test_e_2_a_due_event_awaits_the_outcome_and_is_listed(scorer):
    r = scorer.record(event("E-2"), block(), AS_OF)
    assert r.status == "due" and r.filing is None and r.score is None
    assert "2026-03-01" in r.unscored and "outcome" in r.unscored


def test_e_3_an_open_event_is_open(scorer):
    r = scorer.record(event("E-3", due=dt.date(2027, 3, 1)), block(), AS_OF)
    assert r.status == "open" and r.unscored is None and r.filing is None


def test_verdict_refuses_an_event(scorer):
    with pytest.raises(scorer.PredictionError) as e:
        scorer.verdict(event(), block(), AS_OF)
    assert "event" in str(e.value)


# --- E. falsifier rows ---------------------------------------------------------------

def test_f1_before_the_due_date_nothing_is_scored(scorer):
    r = scorer.record(figure(), block(), dt.date(2026, 2, 28))
    assert r.status == "open" and r.filing is None and r.unscored is None


def test_f2_on_the_due_date_it_is_due_and_scored(scorer):
    r = scorer.record(figure(), block(), dt.date(2026, 3, 1))
    assert r.status == "due" and r.filing.result == "right"


def test_f3_an_unfiled_period_is_never_wrong(scorer):
    r = scorer.record(figure(period="FY2026"), block(), AS_OF)
    assert r.status == "due" and r.filing is None
    assert "FY2026" in r.unscored and "2026-09-18" in r.unscored


def test_f3_verdict_names_the_period(scorer):
    with pytest.raises(scorer.PredictionError) as e:
        scorer.verdict(figure(period="FY2026"), block(), AS_OF)
    assert "FY2026" in str(e.value) and "not filed" in str(e.value)


@pytest.mark.parametrize("metric", ["operating_margin", "free_cash_flow", "free_cash_flow_yield"])
def test_f4_a_metric_with_no_formula_stops_naming_it(scorer, metric):
    r = scorer.record(figure(metric=metric, value=0.1), block(), AS_OF)
    assert r.filing is None and metric in r.unscored


def test_f5_a_filed_period_missing_the_field_stops_naming_it(scorer):
    years = {"FY2025": {k: v for k, v in FY2025.items() if k != "cost_of_revenue"}}
    r = scorer.record(figure("S-6", "gross_margin", "min", 0.59), block(years=years), AS_OF)
    assert r.filing is None and "cost_of_revenue" in r.unscored and "FY2025" in r.unscored


def test_f5_revenue_missing_stops_naming_it(scorer):
    years = {"FY2025": {k: v for k, v in FY2025.items() if k != "revenue"}}
    r = scorer.record(figure(), block(years=years), AS_OF)
    assert r.filing is None and "revenue" in r.unscored


def test_f6_a_written_score_that_disagrees_is_reported_not_repaired(scorer):
    written = Score(outcome="revenue 410,200", source="press release",
                    scored_on=dt.date(2026, 3, 2), result="right")
    r = scorer.record(figure("S-2", value=410_000_000_000, score=written), block(), AS_OF)
    assert r.status == "scored" and r.score == written
    assert r.filing.result == "wrong" and r.agrees is False


def test_a_written_score_that_agrees_says_so(scorer):
    written = Score(outcome="revenue 402,836", source="10-K", scored_on=dt.date(2026, 3, 2),
                    result="right")
    r = scorer.record(figure(score=written), block(), AS_OF)
    assert r.agrees is True and r.filing.result == "right"


def test_f7_strict_and_unrounded(scorer):
    assert scorer.verdict(figure(value=402_835_999_000), block(), AS_OF).result == "right"
    assert scorer.verdict(figure(value=402_836_001_000), block(), AS_OF).result == "wrong"


def test_f8_every_prediction_has_a_record_in_order(scorer):
    rows = [figure(), event("E-2"), figure("S-6", "gross_margin", "min", 0.59)]
    result = scorer.ledger(rows, {"W-1": block()}, AS_OF)
    assert [r.id for r in result.records] == ["S-1", "E-2", "S-6"]
    assert result.summary == {"predictions": 3, "scored": 0, "due": 3, "open": 0}


# --- what the scorer refuses beyond the rows -----------------------------------------

def test_a_due_figure_whose_candidate_has_no_block_is_unscored_naming_it(scorer):
    result = scorer.ledger([figure()], {}, AS_OF)
    r = result.records[0]
    assert r.status == "due" and r.filing is None and "W-1" in r.unscored


def test_a_block_without_a_source_is_an_error_not_a_reason(scorer):
    with pytest.raises(scorer.PredictionError) as e:
        scorer.verdict(figure(), block(source=None), AS_OF)
    assert "source" in str(e.value)


def test_fields_on_two_filings_stop(scorer):
    prov = {"FY2025": {**PROVENANCE, "cost_of_revenue": {**PROVENANCE["cost_of_revenue"],
                                                          "accn": "0001652044-27-000001",
                                                          "filed": dt.date(2027, 2, 4)}}}
    with pytest.raises(scorer.PredictionError) as e:
        scorer.verdict(figure("S-6", "gross_margin", "min", 0.59), block(provenance=prov), AS_OF)
    assert "two filings" in str(e.value)


def test_the_fields_each_metric_reads_are_the_formulas(scorer):
    """quant/fundamentals.READS, the fields the scorer cites as a metric's
    source, held to the formulas: a year lacking any one of them yields
    no value for that metric."""
    from portfolio_tool.quant.fundamentals import READS, metrics_by_year
    full = {"ends": dt.date(2025, 12, 31), "filed": FILED, "revenue": 100.0, "cost_of_revenue": 40.0,
            "operating_income": 30.0, "depreciation_amortisation": 5.0, "equity": 200.0,
            "cash": 20.0, "commercial_paper": 1.0, "long_term_debt_current": 2.0,
            "long_term_debt_noncurrent": 50.0, "operating_cash_flow": 35.0, "capex": 10.0,
            "shares_outstanding": 10.0}
    assumptions = {"tax_rate": 0.20}
    for metric, fields in READS.items():
        if metric == "free_cash_flow_yield":
            continue
        assert metric in metrics_by_year({"years": {"FY2025": full}}, assumptions)["FY2025"]
        for field in fields:
            year = {k: v for k, v in full.items() if k != field}
            assert metric not in metrics_by_year({"years": {"FY2025": year}}, assumptions)["FY2025"], (metric, field)
