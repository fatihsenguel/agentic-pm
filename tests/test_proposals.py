"""
The prediction frame held to expected_values.md Part 15 C and D (cases 4.3
and 4.4; D49 and D50): a model chooses what to test, the pipeline supplies
every number, and nothing is entered anywhere.

The block is Part 14 B's, Alphabet's FY2025 lines as filed with their
provenance, imported from the scorer's test so that the frame and the
scorer are held over one set of figures. The candidate is built here and
not read from the committed watchlist: a test over the committed ledger
goes red the day the ledger changes (KNOWN_GAPS, the seven tests entry).

F9, a proposal the ledger already carries, has no test: the loader reads
no `author` yet and the module says so.

The module is imported inside a fixture so that, before it exists, this
file is a list of errors and not an interrupted suite.
"""

import datetime as dt
from decimal import Decimal

import pytest

from portfolio_tool.watchlist import Candidate, Prediction

from test_predictions import ACCN, FILED, FY2025, PROVENANCE, block

AS_OF = dt.date(2026, 9, 18)
DUE = dt.date(2027, 9, 18)
CLAIMS = ("C-1", "C-2")


def candidate(rows=2):
    taken = tuple(
        Prediction(id=f"W-1.{n}", candidate="W-1", made_on=dt.date(2026, 9, 10),
                   due=dt.date(2027, 3, 1), kind="event", statement="Something.")
        for n in range(1, rows + 1))
    return Candidate(id="W-1", ticker="GOOGL", name="Alphabet", currency="USD",
                     status="active", thesis="A thesis.", predictions=taken)


def figure(metric="gross_margin", bound="min", **extra):
    return {"kind": "figure", "metric": metric, "bound": bound, "reasons": ["C-1"], **extra}


def event(text="the cloud segment profitable at the operating level for the full year", **extra):
    return {"kind": "event", "event": text, "reasons": ["C-2"], **extra}


@pytest.fixture
def proposals():
    from portfolio_tool import proposals
    return proposals


@pytest.fixture
def frame(proposals):
    def _frame(supplied, cand=None, blk=None, as_of=AS_OF):
        return proposals.frame(supplied, cand or candidate(), block() if blk is None else blk,
                               as_of, CLAIMS)
    return _frame


# --- C. the frame for W-1 as of 2026-09-18 ---------------------------------------

def test_p_1_gross_margin_min_is_cut_down(frame):
    (p,) = frame([figure()])
    assert (p.id, p.candidate, p.kind, p.author, p.status) == (
        "W-1.3", "W-1", "figure", "system", "proposed")
    assert (p.made_on, p.due, p.period) == (AS_OF, DUE, "FY2026")
    assert (p.metric, p.bound, p.value) == ("gross_margin", "min", 0.5965)
    assert p.statement == ("By 18 September 2027 Alphabet will have reported a gross margin "
                           "for fiscal 2026 of at least 59.65%.")
    assert p.reasons == ("C-1",)
    assert dict(p.source) == {"form": "10-K", "accn": ACCN, "filed": FILED, "source": "EDGAR"}


def test_p_2_gross_margin_max_is_cut_up(frame):
    (p,) = frame([figure(bound="max")])
    assert p.value == 0.5966
    assert p.statement == ("By 18 September 2027 Alphabet will have reported a gross margin "
                           "for fiscal 2026 of at most 59.66%.")


def test_p_3_revenue_is_the_filed_figure_to_the_unit(frame):
    (p,) = frame([figure(metric="revenue")])
    assert p.value == 402836000000 and isinstance(p.value, int)
    assert p.statement == ("By 18 September 2027 Alphabet will have reported revenue for "
                           "fiscal 2026 of at least 402,836,000,000.")


def test_p_4_an_event_carries_no_figure(frame):
    (p,) = frame([event()])
    assert (p.kind, p.metric, p.bound, p.value, p.period, p.source) == (
        "event", None, None, None, None, None)
    assert p.statement == ("By 18 September 2027 Alphabet's annual report for fiscal 2026 will "
                           "show the cloud segment profitable at the operating level for the "
                           "full year.")


def test_a_year_equal_to_the_last_scores_right_on_all_three(proposals, frame):
    from portfolio_tool.predictions import verdict
    fy2026 = {"FY2025": dict(FY2025),
              "FY2026": {**FY2025, "ends": dt.date(2026, 12, 31), "filed": dt.date(2027, 2, 4)}}
    provenance = {"FY2025": dict(PROVENANCE), "FY2026": dict(PROVENANCE)}
    later = block(years=fy2026, provenance=provenance)
    for supplied in (figure(), figure(bound="max"), figure(metric="revenue")):
        (p,) = frame([supplied])
        row = Prediction(id=p.id, candidate=p.candidate, made_on=p.made_on, due=p.due,
                         kind=p.kind, statement=p.statement, metric=p.metric, bound=p.bound,
                         value=p.value, period=p.period)
        assert verdict(row, later, dt.date(2027, 9, 18)).result == "right", supplied


# --- D. falsifier rows ----------------------------------------------------------------

@pytest.mark.parametrize("extra", [{"value": 0.6}, {"statement": "Margins hold."},
                                   {"due": "2027-01-01"}, {"period": "FY2027"}])
def test_f1_a_number_or_a_sentence_from_the_model_is_refused(proposals, frame, extra):
    with pytest.raises(proposals.ProposalError, match=list(extra)[0]):
        frame([figure(**extra)])


def test_f1_a_digit_in_an_event_is_refused(proposals, frame):
    with pytest.raises(proposals.ProposalError, match="digit"):
        frame([event("cloud revenue above 60 billion")])


def test_f3_a_field_is_not_cut(frame):
    years = {"FY2025": {**FY2025, "revenue": Decimal("402836123456")}}
    (p,) = frame([figure(metric="revenue")], blk=block(years=years))
    assert p.value == 402836123456


def test_f4_a_year_later_within_a_year(proposals):
    assert proposals.one_year_later(dt.date(2028, 2, 29)) == dt.date(2029, 2, 28)
    assert proposals.one_year_later(dt.date(2026, 9, 18)) == dt.date(2027, 9, 18)


def test_f5_a_metric_outside_the_vocabulary_stops_naming_it(proposals, frame):
    with pytest.raises(proposals.ProposalError, match="operating_margin"):
        frame([figure(metric="operating_margin")])


def test_f6_a_metric_the_price_enters_stops_by_name(proposals, frame):
    with pytest.raises(proposals.ProposalError, match="the price enters free_cash_flow_yield"):
        frame([figure(metric="free_cash_flow_yield")])


def test_f7_a_figure_the_latest_year_lacks_stops_naming_it(proposals, frame):
    years = {"FY2025": {k: v for k, v in FY2025.items() if k != "cost_of_revenue"}}
    with pytest.raises(proposals.ProposalError, match=r"FY2025.*cost_of_revenue"):
        frame([figure()], blk=block(years=years))


def test_f8_a_price_in_an_event_stops(proposals, frame):
    with pytest.raises(proposals.ProposalError, match="share price"):
        frame([event("the share price above its level today")])


def test_the_price_phrases_are_the_ledgers(proposals):
    import inspect

    import test_watchlist
    source = inspect.getsource(test_watchlist.test_no_prediction_names_a_price)
    for phrase in proposals.PRICE_PHRASES:
        assert f'"{phrase}"' in source, phrase


def test_f10_the_next_free_ids_are_the_files(frame):
    first, second = frame([figure(), event()])
    assert (first.id, second.id) == ("W-1.3", "W-1.4")
    (only,) = frame([figure()], cand=candidate(rows=0))
    assert only.id == "W-1.1"


# --- the rest of D49 ---------------------------------------------------------------------

def test_a_reason_that_is_no_claim_is_refused(proposals, frame):
    with pytest.raises(proposals.ProposalError, match="C-9"):
        frame([{**figure(), "reasons": ["C-9"]}])
    with pytest.raises(proposals.ProposalError, match="no reasons"):
        frame([{**figure(), "reasons": []}])


def test_a_metric_without_a_sentence_row_stops(proposals, frame):
    years = {"FY2025": {**FY2025, "total_debt": Decimal("1"), "cash": Decimal("1")}}
    with pytest.raises(proposals.ProposalError):
        frame([figure(metric="net_debt_to_ebitda")], blk=block(years=years))


def test_the_first_stop_stops_the_rest(proposals, frame):
    with pytest.raises(proposals.ProposalError, match="operating_margin"):
        frame([figure(metric="operating_margin"), figure()])


def test_no_year_filed_by_the_as_of_stops(proposals, frame):
    with pytest.raises(proposals.ProposalError, match="no fiscal year is filed"):
        frame([figure()], as_of=dt.date(2026, 1, 1))


def test_nothing_is_written(frame, tmp_path, monkeypatch):
    import builtins
    opened = []
    real = builtins.open
    monkeypatch.setattr(builtins, "open", lambda *a, **k: opened.append(a) or real(*a, **k))
    frame([figure(), event()])
    assert opened == []
