"""
The ledger formatter over blocks the scorer produced (case 4.5; Part 14),
run through the runner's check_4_5 over a synthetic state, so that what
"passes" means is stated once, in the runner, and the formatter is held to
it here without a model call.

Two ledgers. The committed one as of 2026-09-18: four open, the check
reading watchlist.toml. And Part 14's synthetic ledger, written to a
temporary file the check is pointed at: S-1's revenue prediction due and
scored by the filing, E-1 written, E-2 due and awaiting the outcome, E-3
open, S-2 with a written score that disagrees with the filing (F6), and F3's
unfiled period. The records come from the real scorer over the typed
Alphabet FY2025 block, assembled the way the node assembles them, so every
figure printed is one Part 14 computed by hand. No figure is invented: the
synthetic predictions are scored on the filed FY2025 lines, and the one
whose period is FY2026 prints the reason it has no figure.

Part 3b: the result, the data age, the source, what was not done.
"""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "benchmark"))
import run_cases  # noqa: E402

from agents import nodes  # noqa: E402
from portfolio_tool import predictions as scorer  # noqa: E402
from portfolio_tool.watchlist import load_watchlist, predictions  # noqa: E402

from test_predictions import block as figures_block, ACCN  # noqa: E402


TODAY = dt.date(2026, 9, 18)
PULLED = "2026-09-16T01:38:52+00:00"

SYNTHETIC = f'''
[[candidate]]
id = "W-1"
ticker = "GOOGL"
name = "Alphabet"
currency = "USD"
asset_class = "Equity"
sector = "Communication Services"
instrument_type = "share"
status = "active"
thesis = "A thesis."

[candidate.entry_condition]
kind = "valuation"
clause = "PHI-4.1"

[[candidate.prediction]]
id = "W-1.1"
made_on = 2026-01-01
due = 2026-03-01
kind = "figure"
metric = "revenue"
bound = "min"
value = 400000000000
period = "FY2025"
statement = "By 1 March 2026 Alphabet will have reported revenue for fiscal 2025 of at least 400 billion dollars."

[[candidate.prediction]]
id = "W-1.2"
made_on = 2026-01-01
due = 2026-03-01
kind = "event"
statement = "By 1 March 2026 the annual report for fiscal 2025 will show the cloud segment profitable at the operating level."
outcome = "the FY2025 annual report's segment note shows the cloud segment with positive operating income for the full year"
source = "10-K {ACCN} filed 2026-02-05, segment note"
scored_on = 2026-03-02
result = "right"

[[candidate.prediction]]
id = "W-1.3"
made_on = 2026-01-01
due = 2026-03-01
kind = "event"
statement = "Something else about the business by 1 March 2026."

[[candidate.prediction]]
id = "W-1.4"
made_on = 2026-01-01
due = 2027-03-01
kind = "event"
statement = "Something about the business by 1 March 2027."

[[candidate.prediction]]
id = "W-1.5"
made_on = 2026-01-01
due = 2026-03-01
kind = "figure"
metric = "revenue"
bound = "min"
value = 410000000000
period = "FY2025"
statement = "By 1 March 2026 Alphabet will have reported revenue for fiscal 2025 of at least 410 billion dollars."
outcome = "revenue 410,200"
source = "press release"
scored_on = 2026-03-02
result = "right"

[[candidate.prediction]]
id = "W-1.6"
made_on = 2026-01-01
due = 2026-03-01
kind = "figure"
metric = "gross_margin"
bound = "min"
value = 0.59
period = "FY2026"
statement = "By 1 March 2026 Alphabet will have reported a gross margin for fiscal 2026 of at least 59%."
'''


def assemble(watchlist, blocks, as_of, figures=None):
    """The block as the node assembles it: the scorer's records made plain."""
    result = scorer.ledger(predictions(watchlist), blocks, as_of)
    return {"as_of": as_of.isoformat(), "watchlist": watchlist.path,
            "records": nodes._plain(result.records), "summary": dict(result.summary),
            "figures": figures or {}}


@pytest.fixture
def committed():
    return assemble(load_watchlist("watchlist.toml"), {}, TODAY)


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    path = tmp_path / "watchlist.toml"
    path.write_text(SYNTHETIC)
    monkeypatch.setattr(run_cases, "LEDGER_PATH", str(path))
    figures = {"W-1": {"ticker": "GOOGL", "cik": 1652044, "name": "Alphabet Inc.",
                       "source": "EDGAR", "facts_as_of": PULLED}}
    return assemble(load_watchlist(str(path)), {"W-1": figures_block()}, TODAY, figures)


def render(block):
    return "\n".join(nodes._format_ledger_response(
        {"LedgerAgent": {"success": True, "ledger": block}}))


def state_for(block, answer):
    from test_runner_probes import record_of

    return {"tool_calls": [record_of("ledger", {}, {"ledger": block}, {"LedgerAgent": True})],
            "final_response": answer, "errors": []}


def _by_id(block):
    return {r["id"]: r for r in block["records"]}


# --- the committed ledger today ---------------------------------------------------------

def test_the_committed_ledger_passes_the_runners_4_5(committed):
    assert run_cases.check_4_5(state_for(committed, render(committed))) == []


def test_four_open_with_their_due_dates_and_the_count(committed):
    answer = render(committed)
    assert "**PREDICTION LEDGER** as of 2026-09-18" in answer
    assert "4 predictions: 0 scored, 0 due, 4 open." in answer
    for pid, due in (("W-1.1", "2027-03-01"), ("W-1.2", "2027-03-01"),
                     ("W-2.1", "2027-02-01"), ("W-2.2", "2027-02-01")):
        assert f"**{pid}** (W-{pid[2]})" in answer
        assert f"Status: open, due {due}." in answer
    assert "Figures read" not in answer, "nothing was read for an open prediction"


def test_the_stated_figures_print_as_the_document_writes_them(committed):
    answer = render(committed)
    assert "figure: revenue at least 420,000,000,000 for FY2026" in answer
    assert "figure: revenue at least 25,500,000,000 for FY2026" in answer
    assert "figure: gross_margin at least 87% for FY2026" in answer
    assert "event. Made 2026-09-10, due 2027-03-01." in answer


# --- Part 14's synthetic ledger ------------------------------------------------------------

def test_the_synthetic_ledger_passes_the_runners_4_5(synthetic):
    assert run_cases.check_4_5(state_for(synthetic, render(synthetic))) == []


def test_the_counts_are_the_scorers(synthetic):
    assert synthetic["summary"] == {"predictions": 6, "scored": 2, "due": 3, "open": 1}
    assert "6 predictions: 2 scored, 3 due, 1 open." in render(synthetic)


def test_s_1_due_and_scored_by_the_filing_not_yet_recorded(synthetic):
    answer = render(synthetic)
    assert ("Status: due since 2026-03-01. The filing says right: reported 402,836,000,000 "
            "against at least 400,000,000,000 for FY2025 (10-K filed 2026-02-05, source "
            "EDGAR). Not yet recorded in the ledger.") in answer


def test_e_1_a_written_score_prints_as_written(synthetic):
    answer = render(synthetic)
    assert ("Status: scored right on 2026-03-02. Outcome: the FY2025 annual report's segment "
            "note shows the cloud segment with positive operating income for the full year "
            f"Source: 10-K {ACCN} filed 2026-02-05, segment note.") in answer


def test_e_2_due_and_awaiting_the_outcome_is_listed_with_the_reason(synthetic):
    answer = render(synthetic)
    reason = _by_id(synthetic)["W-1.3"]["unscored"]
    assert f"Status: due since 2026-03-01, unscored. {reason}" in answer
    assert "outcome" in reason


def test_e_3_open(synthetic):
    assert "**W-1.4** (W-1), event. Made 2026-01-01, due 2027-03-01.\n  Something about the " \
           "business by 1 March 2027.\n  Status: open, due 2027-03-01." in render(synthetic)


def test_f6_a_written_score_that_differs_prints_both_and_says_so(synthetic):
    answer = render(synthetic)
    assert "Status: scored right on 2026-03-02. Outcome: revenue 410,200 Source: press release." in answer
    assert ("The filing says wrong: reported 402,836,000,000 against at least 410,000,000,000 "
            "(10-K filed 2026-02-05, source EDGAR). The ledger and the filing differ.") in answer


def test_f3_an_unfiled_period_prints_the_reason_and_no_verdict(synthetic):
    answer = render(synthetic)
    record = _by_id(synthetic)["W-1.6"]
    assert record["filing"] is None
    assert f"Status: due since 2026-03-01, unscored. {record['unscored']}" in answer
    assert "FY2026 is not filed by 2026-09-18" in answer
    assert "gross_margin at least 59% for FY2026" in answer


def test_the_figures_read_print_with_their_source_and_pull_day(synthetic):
    answer = render(synthetic)
    assert "**Figures read**, each fiscal year's own annual report:" in answer
    assert "  W-1: GOOGL, Alphabet Inc., CIK 1652044, source EDGAR, pulled 2026-09-16 UTC." in answer


def test_what_was_not_done(synthetic):
    answer = render(synthetic)
    assert "**Not done:** no score was written by this system." in answer
    assert "PHI-6.2" in answer
    assert run_cases.PRICE_FORECAST.search(answer) is None


def test_a_failed_agent_prints_its_error_and_nothing_else():
    lines = nodes._format_ledger_response(
        {"LedgerAgent": {"success": False, "error": "LedgerAgent: ZZZZ is not in the file"}})
    assert lines == ["Prediction ledger not read", "", "LedgerAgent: ZZZZ is not in the file"]


def test_a_reported_ratio_prints_as_a_percent():
    assert nodes._reported_figure("gross_margin", 0.5965231508603998) == "59.65%"
    assert nodes._stated_figure("gross_margin", 0.59) == "59%"
    assert nodes._stated_figure("net_debt_to_ebitda", 2) == "2x"
    assert nodes._reported_figure("revenue", 402836000000.0) == "402,836,000,000"
