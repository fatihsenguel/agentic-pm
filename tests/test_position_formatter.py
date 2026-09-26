"""
The rendering of a position question's answer, held by the runner's
check_4_3 (case 4.3; decisions 61, 65, 67, 68 and 69; Part 15 G; Part 17).

Three real nodes and no LLM: the screening node over conftest's copy of
the database, the research node over test_research_node's stand-in models,
and the gate node over test_gate.py's allocation, which is Part 17 B. So
the rendering is held over what the pipeline publishes and not over a
block written for it, and the state the check reads is the state a live
run reaches the synthesizer with.

**The screen stops at PHI-2.1 here, as it does live** (decision 48, D36),
so the answer this file renders is the blocked one Part 17 I computes:
supports no entry, with the grounds naming the screen, the gate and the
entry condition. **`check_4_3` passes on that answer**, every assertion of
it - the outcome supports no entry, so the check's one invariant on the
outcome does not fire, and every clause it asks to reach the answer does.
What reports the case as blocked is the runner's probe,
`blocked_on_recommendation`, naming the screen's stop. A blocked case with
the right reason is the right answer.

Where the assertions cannot be read apart from the policy's stop, a
clear-screen variant of the state is built: only the verdicts are
replaced, never a figure, and Part 10 says what the real ones are.

The rules, each a test:

  - the check's answer-facing assertions all pass on the rendering: every
    philosophy clause id, every IPS clause id, the weight, every entered
    prediction's id, the thesis view, the word judgement and the as-of
  - each of those fails when its piece is taken out of the answer, one at
    a time - except the weight's source, which cannot be made to fail
    while the candidate's id is printed, and which has its own test
    saying so
  - the live answer passes the check and the probe blocks the case
  - the outcome, the grounds and the not-established wording are printed
    as the blocks state them
  - both policies are attached, with the statements that carry no finding
    named as not computed and IPS-5.3, which carries one, left out of that
    list
  - no price is forecast and the emoji rule holds
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "benchmark"))
import run_cases  # noqa: E402

from agents import nodes  # noqa: E402

from test_gate import CASH, HOLDINGS, _allocation  # noqa: E402
from test_research_node import (  # noqa: E402,F401  the fixtures
    Viewer, edgar, models, provider, screened, state,
)
from test_screening_node import state_with  # noqa: E402

# What the check asserts of the answer, and the piece of the answer each
# one reads. The key is the test id; the value is a callable that takes
# the rendered answer and returns it with that piece removed.
ANSWER_PIECES = {
    "a philosophy clause id": lambda a, s: a.replace("PHI-4.1", "the price clause"),
    "an IPS clause id": lambda a, s: a.replace("IPS-3.1", "the equity band"),
    "the weight": lambda a, s: a.replace("6.00%", "the stated weight"),
    # Both entered ids at once: the check asks for any one of them, so
    # taking one away leaves the other satisfying it.
    "every entered prediction's id": lambda a, s: a.replace("W-1.1", "the first").replace(
        "W-1.2", "the second"),
    "the thesis view": lambda a, s: a.replace("stands", "holds up"),
    "the word judgement": lambda a, s: a.replace("judgement", "call").replace(
        "Judgement", "Call"),
    # The as-of is the screen's, read off the clock on the day of the run,
    # so it is read from the block and not written here.
    "the as-of": lambda a, s: a.replace(s["shared_data"]["research"]["as_of"], "that day"),
}


@pytest.fixture
def policy(monkeypatch):
    monkeypatch.setattr(nodes, "load_portfolio_policy_path", lambda state: "ips.toml")


async def _answered(models, clear_screen=False):
    """The state the synthesizer reaches for "Should I buy GOOGL?", built
    by running the three nodes in the order the graph runs them, with the
    rendering as `final_response`."""
    screening = (await nodes.screening_agent_node(state_with(["GOOGL"])))["shared_data"]["screening"]
    if clear_screen:
        # Every clause passing, so that the answer-facing assertions can
        # be read apart from the policy's stop. The figures are not
        # touched: only the verdicts, and the reference says what the real
        # ones are (Part 10).
        screening = {**screening, "stopped": None,
                     "findings": [{"clause": "PHI-4.1", "type": "margin_of_safety",
                                   "subject": "GOOGL", "status": "pass", "metric": None,
                                   "years_read": [], "deciding_year": None,
                                   "observed": 0.9, "limit": 0.25, "bound": "min",
                                   "distance": -0.65, "price_as_of": "2026-09-18",
                                   "range_as_of": "2026-09-18", "sic": None}]}

    s = state(asks="position", screening=screening)
    out = await nodes.research_agent_node(s)
    s["shared_data"] = {**out["shared_data"],
                        "allocation": _priced_allocation(),
                        "holdings": [{"ticker": t, "instrument_type": kind}
                                     for t, _v, _c, kind, _s in HOLDINGS]}
    s["sub_results"] = out["sub_results"]
    s["errors"] = out.get("errors") or []

    gated = await nodes.gate_node(s)
    s["shared_data"] = gated["shared_data"]
    gate_block = s["shared_data"]["gate"]
    # The published block and not `sub_results`, as the synthesizer does:
    # the gate wrote the outcome onto the published one.
    lines = nodes._format_position_response(nodes.judgement_record(s), gate_block, screening)
    s["final_response"] = "\n".join(lines)
    # The record the turn would carry, which the runner's checks read;
    # `shared_data` stays on the state for the assertions here that read
    # the blocks directly.
    from test_runner_probes import record_of

    s["tool_calls"] = [record_of("position", {"ticker": "GOOGL"}, s["shared_data"],
                                 {name: bool(r.get("success")) for name, r in s["sub_results"].items()},
                                 s["final_response"])]
    return s


def _priced_allocation():
    allocation = _allocation(HOLDINGS, CASH)
    allocation["base_currency"] = "USD"
    allocation["as_of"] = "2026-09-18"
    return allocation


def _answer_failures(state):
    """The check's failures that name a piece of the answer rather than a
    verdict of the policy."""
    return [f for f in run_cases.check_4_3(state)
            if "never reaches the answer" in f or "does not call the judgement" in f
            or "is cited by id" in f]


# --- the answer-facing assertions ----------------------------------------------------

async def test_every_answer_facing_assertion_passes_on_the_rendering(edgar, models, policy):
    answered = await _answered(models, clear_screen=True)
    assert _answer_failures(answered) == []


@pytest.mark.parametrize("piece", sorted(ANSWER_PIECES))
async def test_the_check_fails_without_each_piece(edgar, models, policy, piece):
    """Each assertion seen failing with its piece taken out of the answer
    and nothing else changed, so that none of them is passing on another's
    text."""
    answered = await _answered(models, clear_screen=True)
    answered["final_response"] = ANSWER_PIECES[piece](answered["final_response"], answered)
    assert _answer_failures(answered) != [], piece


# --- the live answer on this portfolio ----------------------------------------------

async def test_the_live_answer_passes_the_check_and_the_probe_blocks_the_case(edgar,
                                                                              models,
                                                                              policy):
    """What 4.3 reads on this portfolio, and where the block comes from.

    **check_4_3 passes on the live answer**, every assertion of it: the
    outcome supports no entry, so the check's one invariant on the outcome
    does not fire, and every clause it asks to reach the answer does. What
    reports the case as blocked is the runner's probe,
    `blocked_on_recommendation`, which names the screen's stop. That is
    Part 17 I arriving at the runner: a blocked case with the right reason
    is the right answer, and no figure is filled to move it."""
    answered = await _answered(models)
    assert run_cases.check_4_3(answered) == []
    reason = run_cases.blocked_on_recommendation(answered)
    assert reason is not None
    assert "the philosophy check stopped on PHI-2.1" in reason
    assert "decision 48" in reason


async def test_the_weight_source_assertion_cannot_fail_while_the_id_is_printed(edgar,
                                                                               models,
                                                                               policy):
    """A finding about the check, not about the rendering. `check_4_3`
    asks that `gate["weight_source"]` reach the answer, and the source is
    the candidate's id, which the answer must print anyway - the thesis is
    attached to it and `_research_invariants` asks for it. So that
    assertion holds on the id and cannot be made to fail by taking the
    weight's own sentence away. It is in the piece list as nothing, and
    this test is what says so."""
    answered = await _answered(models, clear_screen=True)
    without = answered["final_response"].replace(
        "The weight is W-1's, my watchlist entry", "The weight is my watchlist entry")
    assert "W-1" in without
    answered["final_response"] = without
    assert _answer_failures(answered) == []


async def test_the_outcome_and_its_grounds_are_printed(edgar, models, policy):
    answered = await _answered(models)
    answer = answered["final_response"]
    outcome = answered["shared_data"]["research"]["outcome"]
    assert outcome["supports_entry"] is False
    assert "**The outcome: this supports no entry.**" in answer
    assert "the philosophy screen stopped at PHI-2.1" in answer
    assert "the investment policy does not clear the position at this weight" in answer


async def test_a_condition_the_screen_did_not_reach_prints_as_not_established(edgar, models,
                                                                              policy):
    """Not as a no: the screen reported no finding on PHI-4.1, so there is
    no verdict to report (decision 68, Part 17 I's note)."""
    answered = await _answered(models)
    answer = answered["final_response"]
    assert answered["shared_data"]["research"]["entry_condition"]["met"] is None
    assert "valuation on PHI-4.1: not established" in answer
    assert "the screen reported no finding on that clause" in answer


async def test_a_view_the_model_did_not_give_prints_as_not_established(edgar, models, policy):
    models["viewer"] = Viewer(answer={"thesis_view": "holds", "reasons": [],
                                      "uncertainty": "stated"})
    answered = await _answered(models)
    answer = answered["final_response"]
    assert "not established" in answer
    assert "The system did not make this judgement" in answer
    assert "'holds' is not one of" in answer


async def test_the_view_says_it_can_only_take_away(edgar, models, policy):
    answered = await _answered(models, clear_screen=True)
    assert "It can only take away" in answered["final_response"]


# --- the policy checks, both attached ------------------------------------------------

async def test_both_policies_are_attached_with_their_statements_named(edgar, models, policy):
    """A recommendation without both checks is generic advice
    (DIRECTION.md). Every clause of each policy is either a finding or is
    named as not computed (Part 17 D60)."""
    answered = await _answered(models)
    answer = answered["final_response"]
    for clause in ("PHI-1.1", "PHI-4.3", "IPS-1.1", "IPS-2.1", "IPS-6.2"):
        assert clause in answer, clause
    assert "Not computed, being statements of what I look for" in answer
    assert "Not computed, being statements of policy" in answer


async def test_the_weight_its_source_and_the_funding_are_printed(edgar, models, policy):
    answered = await _answered(models)
    answer = answered["final_response"]
    gate_block = answered["shared_data"]["gate"]
    assert "with GOOGL at 6.00% of it" in answer
    assert "The weight is W-1's, my watchlist entry" in answer
    assert f"funded by {gate_block['funding']}" in answer
    assert f"{gate_block['new_money']:,.2f} USD on top of" in answer


async def test_the_entered_predictions_are_printed_with_their_dates(edgar, models, policy):
    answered = await _answered(models)
    answer = answered["final_response"]
    for row in answered["shared_data"]["research"]["entered"]:
        assert f"**{row['id']}** due {row['due']}: {row['statement']}" in answer
    assert "proposed, not entered" in answer


# --- the prohibitions ----------------------------------------------------------------

async def test_no_price_is_forecast(edgar, models, policy):
    answered = await _answered(models)
    assert run_cases.PRICE_FORECAST.search(answered["final_response"]) is None


async def test_the_answer_carries_no_emoji(edgar, models, policy):
    """Newly written text carries none. The seven headers KNOWN_GAPS
    records are elsewhere in this file and are their own commit."""
    answer = await _answered(models)
    for ch in answer["final_response"]:
        assert ord(ch) < 0x2190 or ch in "—–‘’“”…", repr(ch)


async def test_a_gate_that_could_not_run_prints_nothing_about_the_position(edgar, models,
                                                                           policy):
    """The guard, decision 62: with no gate block the synthesizer refuses
    rather than printing an answer whose policy check is missing."""
    answered = await _answered(models)
    shared = {**answered["shared_data"]}
    del shared["gate"]
    with pytest.raises(nodes.DataCalculationError, match="No gate block in shared_data"):
        nodes.require_gate(shared, answered["shared_data"]["research"])


async def test_a_statement_clause_with_a_finding_is_not_also_named_uncomputed(edgar, models,
                                                                              policy):
    """IPS-5.3 states no number, so the loader reads it as a statement,
    and decision 64's funding makes it directly applicable, so D59 gives
    it a finding. It must not appear in the not-computed line beside its
    own finding."""
    answered = await _answered(models)
    answer = answered["final_response"]
    gate_block = answered["shared_data"]["gate"]
    assert "IPS-5.3" in {f["clause"] for f in gate_block["findings"]}
    assert "IPS-5.3" in {s["clause"] for s in gate_block["statements"]}
    uncomputed = [line for line in answer.splitlines()
                  if "Not computed, being statements of policy" in line]
    assert len(uncomputed) == 1
    assert "IPS-5.3" not in uncomputed[0]
    assert "IPS-2.1" in uncomputed[0]
