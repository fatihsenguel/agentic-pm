"""
The research formatter over hand-built screening blocks, in its three
renderings: a company excluded on its code, a check that stopped, and a
company screened clause by clause (decision 29; benchmark 4.1 and 4.6).

Hand-built input holds the formatter to a shape, not the node to the tool
(the handoff's rule); the node's own test is test_screening_node.py. The
findings for the screened rendering come from the real screen over Part 10
A's typed figures with Alphabet's code, so every figure printed is one the
screen produced and the reference computed by hand.

Each rendering is also run through the runner's check for its case,
imported from tests/benchmark/run_cases.py over a synthetic state, so that
what "passes" means is stated once, in the runner, and the formatter is
held to it here without a model call. Part 3b: the result, the data age,
the source by clause id, what was not done.
"""

import datetime as dt
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "benchmark"))
import run_cases  # noqa: E402

from agents import nodes  # noqa: E402
from portfolio_tool import screening  # noqa: E402
from portfolio_tool.philosophy import load_philosophy  # noqa: E402

from test_screening import alphabet, AS_OF  # noqa: E402


PHILOSOPHY = load_philosophy("philosophy.toml")
PULLED = "2026-09-16T00:03:12+00:00"


def _document():
    return ({c.id: {"type": c.type, "text": c.text} for c in PHILOSOPHY},
            [{"clause": c.id, "text": c.text} for c in PHILOSOPHY.statements])


def bank_block():
    philosophy, statements = _document()
    return {
        "philosophy": philosophy, "statements": statements,
        "subject": {"ticker": "JPM", "cik": 19617, "name": "JPMORGAN CHASE & CO"},
        "as_of": "2026-09-16", "sic": "6021", "sic_description": "National Commercial Banks",
        "sic_as_of": PULLED, "years": {}, "stopped": None,
        "source": "EDGAR companyfacts", "facts_as_of": None,
        "findings": [{"clause": "PHI-3.2", "type": "excluded_industry", "subject": "JPM",
                      "metric": None, "years_read": [], "deciding_year": None, "observed": None,
                      "limit": None, "bound": None, "status": "excluded", "distance": None,
                      "price_as_of": None, "range_as_of": None, "sic": "6021"}],
    }


def stopped_block():
    philosophy, statements = _document()
    return {
        "philosophy": philosophy, "statements": statements,
        "subject": {"ticker": "GOOGL", "cik": 1652044, "name": "Alphabet Inc."},
        "as_of": "2026-09-16", "sic": "7370",
        "sic_description": "Services-Computer Programming, Data Processing, Etc.",
        "sic_as_of": PULLED,
        "years": {"FY2021": {"ends": "2021-12-31", "filed": "2022-02-02"},
                  "FY2022": {"ends": "2022-12-31", "filed": "2023-02-03"}},
        "findings": [],
        "stopped": {"clause": "PHI-2.1",
                    "reason": "PHI-2.1: return_on_invested_capital for FY2021 is not in the "
                              "figures. The check stops here and reports no finding on any "
                              "clause (PHI-1.2, D25)."},
        "source": "EDGAR companyfacts", "facts_as_of": "2026-09-15T22:17:00+00:00",
    }


def screened_block():
    """Part 10 A's typed figures through the real screen: five findings and
    PHI-3.2 pass on 7370, in philosophy order (Part 10 D and F)."""
    philosophy, statements = _document()
    block = alphabet()
    findings = [{**asdict(f), "years_read": list(f.years_read)}
                for f in screening.screen(PHILOSOPHY, block, AS_OF)]
    years = {label: {"ends": str(y["ends"]), "filed": str(y["filed"])}
             for label, y in block["years"].items()}
    return {
        "philosophy": philosophy, "statements": statements,
        "subject": {"ticker": "GOOGL", "cik": 1652044, "name": "Alphabet Inc."},
        "as_of": str(AS_OF), "sic": "7370",
        "sic_description": "Services-Computer Programming, Data Processing, Etc.",
        "sic_as_of": PULLED, "years": years, "findings": findings, "stopped": None,
        "source": "expected_values.md Part 10", "facts_as_of": "2026-09-15T22:17:00+00:00",
    }


def render(block):
    return "\n".join(nodes._format_research_response(
        {"ScreeningAgent": {"success": True, "screening": block}}))


def state_for(block, answer):
    return {"shared_data": {"screening": block}, "final_response": answer, "errors": [],
            "router_decision": {"intent": "research", "execution_order": ["ScreeningAgent"],
                                "parameters": {"tickers": [block["subject"]["ticker"]]}}}


# --- excluded: PHI-3.2 and nothing else ------------------------------------------------

def test_the_excluded_rendering_passes_the_runners_4_6():
    block = bank_block()
    assert run_cases.check_4_6(state_for(block, render(block))) == []


def test_the_excluded_rendering_names_the_code_its_description_and_its_date():
    text = render(bank_block())
    assert "PHI-3.2" in text
    assert "6021" in text and "National Commercial Banks" in text
    assert "2026-09-16" in text and "UTC" in text
    assert "JPMORGAN CHASE & CO" in text and "19617" in text
    assert set(run_cases.PHI_ID.findall(text)) == {"PHI-3.2"}
    assert "not consulted" in text.lower()


def test_the_excluded_rendering_quotes_the_clause_and_reports_nothing_else():
    text = render(bank_block())
    assert PHILOSOPHY["PHI-3.2"].text in text
    assert "nothing else" in text.lower()
    assert "%" not in text


# --- stopped: the clause, the reason, no verdict ------------------------------------

def test_the_stopped_rendering_names_where_and_why_and_gives_no_verdict():
    text = render(stopped_block())
    assert "stopped" in text.lower()
    assert "PHI-2.1" in text and "FY2021" in text
    assert "return_on_invested_capital" in text
    assert "PHI-1.2" in text
    assert set(run_cases.PHI_ID.findall(text)) == {"PHI-1.2", "PHI-2.1"}
    for word in ("pass", "fail", "clears"):
        assert word not in text.lower().replace("passes or fails", "")
    assert "%" not in text


def test_the_stopped_rendering_states_both_pull_dates_and_the_as_of():
    text = render(stopped_block())
    assert "2026-09-16" in text           # the check's as-of and the code's pull day
    assert "2026-09-15" in text           # the facts' pull day
    assert text.count("UTC") >= 2


# --- screened: every clause a finding, every figure its year and source ------------

def test_the_screened_rendering_passes_the_runners_4_1():
    block = screened_block()
    assert run_cases.check_4_1(state_for(block, render(block))) == []


def test_every_finding_prints_its_id_year_and_filed_date():
    block = screened_block()
    text = render(block)
    for f in block["findings"]:
        assert f["clause"] in text
        if f["deciding_year"]:
            assert f["deciding_year"] in text
            assert block["years"][f["deciding_year"]]["filed"] in text
    assert block["source"] in text


def test_the_reference_figures_reach_the_answer_as_the_screen_produced_them():
    """Part 10 D: ROIC 10.00% in FY2022 against 12%, 2.00 pp short; gross
    margin 55.00%; net debt to EBITDA -0.50x against 2.0x; discount 5.00%
    against 25%; FCF yield 4.50% against 4%."""
    text = render(screened_block())
    for figure in ("10.00%", "12%", "2.00 pp", "55.00%", "35%", "-0.50", "2.00x",
                   "5.00%", "25%", "4.50%", "4%"):
        assert figure in text, figure


def test_every_statement_is_named_as_not_computed():
    text = render(screened_block())
    assert "not computed" in text.lower()
    for st in PHILOSOPHY.statements:
        assert st.id in text


def test_the_screened_rendering_gives_no_recommendation():
    text = render(screened_block()).lower()
    assert "no recommendation" in text
    assert "not consulted" in text
    assert run_cases._no_recommendation(state_for(screened_block(), text), "GOOGL") == []


# --- a failed agent -------------------------------------------------------------------

def test_a_failed_agent_prints_its_error_and_nothing_else():
    lines = nodes._format_research_response(
        {"ScreeningAgent": {"success": False, "error": "ZZZZ: the SEC's ticker file lists no filer"}})
    text = "\n".join(lines)
    assert "ZZZZ" in text and "lists no filer" in text
    assert "PHI-" not in text
