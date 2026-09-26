"""
The tracing check: every figure in an answer is a figure a tool printed
that turn, or one the user typed (DIRECTION.md invariant 1; decision 45).

What it reads. The number tokens of the answer, digits with thousands
commas and an optional decimal part as the formatters print them, each
of which must be a token of the allowed text: the rendered text of every
record in the turn's tool-call log, the question, and, under `earlier`,
every earlier turn's records and the question it was checked against
(decision 77: a figure that passed an earlier turn's check may be quoted
in a follow-up). Tokens are compared whole and not as substrings, which
is what catches a rounding: 4.4 is a substring of 4.41 and is not the
same token.

What it cannot see: a coincidence. A clause id the model invented whose
digits match a distance the text printed passes on the token. It is a
membership check over what was printed, not a provenance check.

A date is three tokens and a clause id is one, so the check reads both
without knowing either: a date the text printed passes whole, a date the
model shifted fails on the day, and a clause the tool did not return
fails on its number.
"""

import sys
from pathlib import Path

import pytest

from agents.conversation import untraced_figures

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tests" / "benchmark"))

import run_cases  # noqa: E402


TEXT = ("**ALLOCATION** as of 2026-09-21\n"
        "Equity: 69.41% of total, 284,500.00 USD invested\n"
        "**IPS-4.2** caps any issuer at 10% of total; AAPL is 4.41 pp over.")

RESOLVED = {"reply": "A share.",
            "message": "I want to put 15% into a single position, is that allowed? "
                       "It would be a share."}
POSITION = "**NOT PERMITTED BY THE POLICY**\n**IPS-4.1** caps a position at 12% of total."


def _state(answer, *texts):
    log = [{"tool": "allocation", "inputs": {}, "key": "allocation", "block": {},
            "text": t, "blocks": {}, "agents": {},
            "provenance": {"as_of": None, "source": None, "caveats": ()}} for t in texts]
    return {"tool_calls": log, "final_response": answer, "errors": [], "warnings": []}


def _untraced(fails):
    return [f for f in fails if "no tool printed" in f]


def test_a_figure_the_text_carries_passes():
    answer = "Equity is 69.41% of the total, on 284,500.00 USD invested."
    assert run_cases.figures_trace(_state(answer, TEXT), "What is my allocation?") == []


def test_a_figure_the_text_does_not_carry_fails_by_name():
    answer = "Equity is 69.41% of the total, up 3.2 pp on the month."
    fails = _untraced(run_cases.figures_trace(_state(answer, TEXT), "What is my allocation?"))
    assert fails and "'3.2'" in fails[0] and "'69.41'" not in fails[0]


def test_a_rounded_figure_fails_as_a_token_and_not_a_substring():
    answer = "Equity is about 69.4% of the total, on 284500 USD invested."
    fails = _untraced(run_cases.figures_trace(_state(answer, TEXT), "What is my allocation?"))
    assert fails and "'69.4'" in fails[0] and "'284500'" in fails[0]


def test_a_date_passes_whole_and_fails_on_a_shifted_day():
    assert run_cases.figures_trace(_state("As of 2026-09-21.", TEXT), "q") == []
    fails = _untraced(run_cases.figures_trace(_state("As of 2026-09-22.", TEXT), "q"))
    assert fails and "'22'" in fails[0] and "'2026'" not in fails[0]


def test_a_clause_id_passes_when_returned_and_fails_when_invented():
    assert run_cases.figures_trace(_state("IPS-4.2 caps issuers.", TEXT), "q") == []
    fails = _untraced(run_cases.figures_trace(_state("IPS-4.3 caps issuers.", TEXT), "q"))
    assert fails and "'4.3'" in fails[0]


def test_the_question_s_own_figures_are_allowed():
    question = "I want to put 15% into a single position, is that allowed?"
    text = "**NOT PERMITTED BY THE POLICY**\n**IPS-4.1** caps a position at 12% of total."
    answer = "15% in one position is not permitted under IPS-4.1, which caps it at 12%."
    assert run_cases.figures_trace(_state(answer, text), question) == []
    assert _untraced(run_cases.figures_trace(_state(answer, text), "Is that allowed?"))


def test_every_record_s_text_is_allowed_and_an_empty_log_allows_nothing():
    first = "Equity: 69.41% of total"
    second = "Portfolio volatility 12.30% annualised over 252 closes"
    answer = "Equity is 69.41% and volatility 12.30% over 252 closes."
    assert run_cases.figures_trace(_state(answer, first, second), "q") == []
    assert _untraced(run_cases.figures_trace(_state(answer), "q"))
    assert run_cases.figures_trace(_state("No figures at all."), "q") == []


def test_a_resolved_reply_is_read_against_the_question_it_resolved_into():
    """Case 3.1 of 24 September: the client let "15" through against the
    resolved question and the runner refused it against "A share."."""
    answer = "15% in one position is not permitted under IPS-4.1, which caps it at 12%."
    state = {**_state(answer, POSITION), "resolved": RESOLVED}
    assert untraced_figures(answer, [POSITION], RESOLVED["message"]) == []
    assert run_cases.figures_trace(state, "A share.") == []


def test_a_figure_only_the_typed_reply_carries_is_refused_on_a_resolved_turn():
    """The recorded question is read and never rebuilt from the reply."""
    state = {**_state("A 20% share is not permitted.", POSITION), "resolved": RESOLVED}
    assert _untraced(run_cases.figures_trace(state, "A 20% share."))


def test_a_resolution_with_no_question_raises():
    state = {**_state("No figures.", POSITION), "resolved": {"reply": "A share."}}
    with pytest.raises(KeyError):
        run_cases.figures_trace(state, "A share.")


def test_an_earlier_turns_texts_and_question_are_allowed():
    """S-4's turn 2 quoted turn 1's distances, which turn 1's compliance
    text had printed. The runner allows what the client allows: the
    earlier turns' records and questions, carried under `earlier`."""
    answer = "Equity was 69.41% last turn, and you asked about 15%."
    earlier = [{"question": "Can I put 15% into one position?",
                "tool_calls": _state("", TEXT)["tool_calls"]}]
    state = {**_state(answer), "earlier": earlier}
    assert run_cases.figures_trace(state, "What did we say?") == []
    fails = _untraced(run_cases.figures_trace(_state(answer), "What did we say?"))
    assert fails and "'69.41'" in fails[0] and "'15'" in fails[0]


def test_a_turn_the_pre_pass_answered_is_not_read():
    """A clarification is deterministic text and no narration: it may name
    the vocabulary's spans, and no tool printed them."""
    asked = _state("I can measure over 1Y, 2Y, 3Y, 5Y or 10Y, not over 'last quarter'.")
    assert _untraced(run_cases.figures_trace(asked, "What is my volatility over last quarter?"))
    asked["clarification"] = {"kind": "unknown_span", "message": "..."}
    assert run_cases.figures_trace(asked, "What is my volatility over last quarter?") == []
