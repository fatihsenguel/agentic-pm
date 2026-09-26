"""
The rendering of a thesis question's research block, held by the runner's
check_4_4 and by Part 15 C's row (case 4.4; Part 15 D47 to D50 and F).

The block is the research node's own, run over test_research_node's
stand-ins, so the rendering is held over what the node publishes and not
over a block written for the rendering. The answer is the formatter's
lines joined as the synthesizer joins them. *Corrected 2026-09-21: the
synthesizer does call this formatter, for a thesis question, and has since
the commit that put the research agent in the graph; the sentence here said
it did not. A position question goes to `_format_position_response`
instead, held in test_position_formatter.py.*

The rules, each a test:

  - the node's block, rendered, passes check_4_4 with no failure
  - each reading's line carries its own form, fiscal year, accession,
    filed date and source, and the proposal's lines their own dates and
    statement, since the check would take a field from another line
  - a claim is printed on one line with its id and its uncertainty, its
    quote beneath it, and the readings are named the model's
  - a section not read prints its reason, and the answer still passes
  - the proposal prints Part 15 C's row for watchlist.toml character for
    character, and the sentence for docs/WATCHLIST.md; it is marked
    proposed and not entered
  - a proposal refused prints its reason and the check fails on the
    missing prediction, which is the honest answer
  - the node's error prints as an error
"""

import sys
from pathlib import Path

import tomli

sys.path.insert(0, str(Path(__file__).parent / "benchmark"))
import run_cases  # noqa: E402

from agents import nodes  # noqa: E402

from test_reader import CLAIMS as ITEM_1A  # noqa: E402
from test_research_node import (  # noqa: E402,F401  the fixtures
    FIGURE, Proposer, Reader, edgar, models, provider, state,
)

ROW_P_1 = '''[[candidate.prediction]]
id = "W-1.3"
made_on = 2026-09-18
due = 2027-09-18
kind = "figure"
metric = "gross_margin"
bound = "min"
value = 0.5965
period = "FY2026"
author = "system"
statement = """By 18 September 2027 Alphabet will have reported a gross margin for fiscal 2026 of at least 59.65%."""'''


async def _answered():
    from test_runner_probes import record_of

    out = await nodes.research_agent_node(state())
    text = "\n".join(nodes._format_thesis_response(out["sub_results"]))
    # The record the turn would carry, which the runner's checks read;
    # `shared_data` stays for the assertions here that read the block.
    record = record_of("thesis", {"ticker": "GOOGL"}, out["shared_data"],
                       {name: bool(r.get("success")) for name, r in out["sub_results"].items()},
                       text)
    return {"final_response": text, "shared_data": out["shared_data"],
            "errors": out.get("errors") or [], "tool_calls": [record]}


async def test_the_nodes_block_rendered_passes_the_runners_4_4(edgar, models):
    answered = await _answered()
    assert run_cases.check_4_4(answered) == []


async def test_the_runner_caps_a_readings_quoted_text_and_not_a_quote(edgar, models):
    """Decision 70, as the runner holds it: a quote of 301 characters
    raises nothing, and a reading's quotes past 3,600 characters together
    fail naming the section and the total."""
    answered = await _answered()
    reading = answered["shared_data"]["research"]["readings"][0]
    claims = reading["claims"]
    claims[0]["quote"] = "x" * 301
    assert run_cases._readings_invariants(answered)[0] == []
    claims[0]["quote"] = "x" * (3600 - sum(len(c["quote"]) for c in claims[1:]))
    assert run_cases._readings_invariants(answered)[0] == []
    claims[0]["quote"] += "x"
    assert run_cases._readings_invariants(answered)[0] == [
        f"reading {reading['section']!r}: its quotes hold 3,601 characters together; "
        "the cap is 3,600 and a record is not the document"]


async def test_each_heading_line_carries_its_own_fields(edgar, models):
    """The check asks that each field reach the answer somewhere; a line
    that loses its accession or its date can pass it on another line's.
    Each reading's line and the proposal's lines are held whole here."""
    lines = (await _answered())["final_response"].splitlines()
    assert "**THESIS: GOOGL** (W-1), as of 2026-09-18" in lines
    for section in ("Item 1", "Item 1A", "Item 7"):
        assert (f"**{section}** of the 10-K for FY2025, accession 0001652044-26-000018, "
                "filed 2026-02-05, source EDGAR filing archive:") in lines
    assert ("**W-1.3**, proposed, not entered. Made 2026-09-18, due 2027-09-18; chosen by "
            "the model (stand-in-proposer), every number in it the pipeline's.") in lines
    assert ("  By 18 September 2027 Alphabet will have reported a gross margin for fiscal "
            "2026 of at least 59.65%.") in lines


async def test_a_claim_is_one_line_with_its_uncertainty_and_its_quote_beneath(edgar, models):
    answer = (await _answered())["final_response"]
    lines = answer.splitlines()
    for n, line in enumerate(lines):
        if line.strip().startswith("[1A.2]"):
            assert line.strip() == f"[1A.2] (stated) {ITEM_1A[1]['claim']}"
            assert lines[n + 1].strip() == f"\"{ITEM_1A[1]['quote']}\""
            break
    else:
        raise AssertionError("claim 1A.2 is not printed")
    assert "the model's reading (stand-in-reader)" in answer
    assert "chosen by the model (stand-in-proposer)" in answer


async def test_a_section_not_read_prints_its_reason(edgar, models):
    digit = [dict(ITEM_1A[0], claim="The company lists twelve risks in 2025.")]
    models["reader"] = Reader(refuse={"Item 1A": digit})
    models["proposer"] = Proposer(dict(FIGURE, reasons=["1.1"]))
    answered = await _answered()
    reason = answered["shared_data"]["research"]["not_read"][0]["reason"]
    assert f"**Item 1A** not read: {reason}" in answered["final_response"]
    assert run_cases.check_4_4(answered) == []


async def test_the_proposal_prints_part_15_cs_row_and_its_sentence(edgar, models):
    answer = (await _answered())["final_response"]
    lines = answer.splitlines()
    start = lines.index("  The row for watchlist.toml, if I enter it:") + 2
    row = "\n".join(line[4:] for line in lines[start:start + 11])
    assert row == ROW_P_1
    assert tomli.loads(row)["candidate"]["prediction"][0]["author"] == "system"
    assert ("    **W-1.3** By 18 September 2027 Alphabet will have reported a gross margin "
            "for fiscal 2026 of at least 59.65%.") in lines
    assert "**W-1.3**, proposed, not entered." in answer


async def test_the_threshold_names_its_filing(edgar, models):
    answer = (await _answered())["final_response"]
    assert ("The threshold, gross_margin at least 59.65% for FY2026, is the last filed "
            "year's figure: the 10-K accession 0001652044-26-000018, filed 2026-02-05, source "
            "stand-in filings.") in answer


async def test_a_proposal_refused_prints_its_reason_and_the_case_fails(edgar, models):
    models["proposer"] = Proposer(dict(FIGURE, metric="return_on_invested_capital"))
    answered = await _answered()
    stopped = answered["shared_data"]["research"]["proposal_stopped"]
    assert f"  {stopped}" in answered["final_response"].splitlines()
    assert "**No prediction proposed.**" in answered["final_response"]
    assert any("carries no prediction" in f for f in run_cases.check_4_4(answered))


def test_the_nodes_error_prints_as_an_error():
    lines = nodes._format_thesis_response(
        {"ResearchAgent": {"success": False, "error": "the screen did not run"}})
    assert lines == ["Research not done", "", "the screen did not run"]
