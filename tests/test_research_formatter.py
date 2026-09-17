"""
The research formatter over hand-built screening blocks, in its three
renderings: a company excluded on its code, a check that stopped, and a
company screened clause by clause (decision 29; benchmark 4.1 and 4.6);
and, beside the stopped and the screened renderings, the valuation range
with its assumptions and the last close (case 4.2, Part 11, decision 57),
or the stop that stands where each would be.

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


# Part 11 C, Alphabet FY2025, as valuation_range returns it: the unrounded
# quotients, the year with its dates, the source, the five assumptions.
def valuation_record():
    return {
        "low": 129.3871305225, "high": 205.6162184284, "as_of": "2026-09-16",
        "year": "FY2025", "ends": "2025-12-31", "filed": "2026-02-05",
        "source": "EDGAR companyfacts",
        "assumptions": {
            "required_return": {"value": 0.09, "source": "PHI-4.1"},
            "terminal_growth": {"value": 0.03, "source": "PHI-4.1"},
            "horizon_years": {"value": 10, "source": "PHI-4.1"},
            "growth_low": {"value": 0.06, "source": "W-1"},
            "growth_high": {"value": 0.12, "source": "W-1"},
        },
    }


# Part 9 C: the last close before 2026-09-17.
def price_record():
    return {"ticker": "GOOGL", "value": 342.87, "as_of": "2026-09-16", "source": "yfinance"}


def valued_block(base=stopped_block):
    """Alphabet as the node publishes it today: the screen stopped at
    PHI-2.1, the range and the price beside it (the range does not depend
    on the screen)."""
    block = base()
    block["years"]["FY2025"] = {"ends": "2025-12-31", "filed": "2026-02-05"}
    block.update({"valuation": valuation_record(), "valuation_stopped": None,
                  "price": price_record(), "price_stopped": None})
    return block


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


# --- the range and the price, beside the screen (case 4.2) ---------------------------

def test_the_valued_rendering_passes_the_runners_4_2():
    block = valued_block()
    assert run_cases.check_4_2(state_for(block, render(block))) == []


def test_the_screened_rendering_with_a_range_passes_both_4_1_and_4_2():
    block = valued_block(screened_block)
    text = render(block)
    assert run_cases.check_4_1(state_for(block, text)) == []
    assert run_cases.check_4_2(state_for(block, text)) == []


def test_the_range_prints_both_ends_the_year_and_its_dates_and_no_middle():
    text = render(valued_block())
    assert "129.39" in text and "205.62" in text
    assert "FY2025" in text and "2025-12-31" in text and "2026-02-05" in text
    assert "167.50" not in text and "167.51" not in text
    assert "PHI-4.1" in text and "PHI-4.3" in text
    assert PHILOSOPHY["PHI-4.3"].text in text


def test_every_assumption_prints_as_the_document_writes_it_with_its_source():
    text = render(valued_block())
    for line in ("required_return 9% (PHI-4.1)", "terminal_growth 3% (PHI-4.1)",
                 "horizon_years 10 years (PHI-4.1)", "growth_low 6% (W-1)",
                 "growth_high 12% (W-1)"):
        assert line in text, line
    assert "mine" in text


def test_the_price_prints_with_its_date_and_source():
    text = render(valued_block())
    assert "GOOGL 342.87 on 2026-09-16" in text and "yfinance" in text


def test_a_stopped_range_prints_where_it_stopped_and_no_end():
    block = valued_block()
    block["valuation"] = None
    block["valuation_stopped"] = ("W-2 (ADBE) states no growth_low and growth_high; a "
                                  "candidate under a valuation condition states the growth "
                                  "I assume for it, and until it does it has no range.")
    text = render(block)
    assert "no growth_low and growth_high" in text
    assert "129.39" not in text and "205.62" not in text and "PHI-4.3" not in text
    assert "GOOGL 342.87 on 2026-09-16" in text


def test_a_missing_price_prints_why_and_the_range_stands():
    block = valued_block()
    block["price"] = None
    block["price_stopped"] = ("GOOGL is neither held nor on the watchlist, so there is no "
                              "currency to store a close under; no price is fetched (decision 57).")
    text = render(block)
    assert "no price is fetched" in text
    assert "342.87" not in text
    assert "129.39" in text and "205.62" in text


def test_a_block_without_the_range_keys_renders_as_before():
    """The excluded rendering and blocks published before 4.2: no range
    section at all, not a sentence about one."""
    for block in (bank_block(), stopped_block()):
        text = render(block)
        assert "VALUATION" not in text and "Last close" not in text


def test_the_valued_rendering_forecasts_no_price():
    text = render(valued_block())
    assert run_cases.PRICE_FORECAST.search(text) is None
    assert "never a forecast of a price" in text
