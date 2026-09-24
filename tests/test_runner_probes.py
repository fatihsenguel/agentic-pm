"""
The runner's routing probes, read against a tool-call log (decision 45).

Why this file exists. Ten of the runner's probes and checks read
`router_decision`, which Order 5 deletes. Each is rewritten here first,
over a synthetic state that carries the log the conversation layer will
write, so that the runner is an instrument on the day the layer lands and
not a thing repaired after it. The states are the least that reach the
probe under test; every other assertion of the check fails on them, so
each test asserts on the presence or absence of one failure and never on
the list being empty.

The log's shape, as decided with the shape of this rewrite: the state key
`tool_calls`, a list in call order, emptied every turn, one record per
tool call with `tool`, `inputs`, `key`, `block`, `text` and `as_of`. A
turn the pre-pass answers with a clarification carries an empty list and
the record it asked back under `clarification`; a turn whose reply was
resolved into a question carries that under `resolved`.

Until the layer writes the log every case reads BLOCKED on it, before
any paid call when the state type declares no such key, and after the
run when the state carries none.
"""

import sys
from pathlib import Path
from typing import List, TypedDict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tests" / "benchmark"))

import run_cases  # noqa: E402


# ---------------------------------------------------------------------------
# The log probe
# ---------------------------------------------------------------------------

class _Declares(TypedDict):
    tool_calls: List[dict]
    shared_data: dict


class _DoesNot(TypedDict):
    shared_data: dict


def test_a_state_type_that_declares_no_log_blocks_before_any_run():
    assert run_cases.state_declares_log(_Declares) is True
    assert run_cases.state_declares_log(_DoesNot) is False


def test_a_state_without_the_log_is_blocked_on_it():
    reason = run_cases.blocked_on_tool_log({"shared_data": {}, "final_response": ""})
    assert reason is not None
    assert "tool-call log" in reason


def test_a_state_with_an_empty_log_is_not_blocked():
    assert run_cases.blocked_on_tool_log({"tool_calls": [], "shared_data": {}}) is None


# ---------------------------------------------------------------------------
# The five input probes: which tool was called with which inputs
# ---------------------------------------------------------------------------

def _record(tool, inputs=None, key=None, block=None, text=""):
    return {"tool": tool, "inputs": inputs or {}, "key": key or tool,
            "block": block or {}, "text": text, "as_of": None}


def _state(log, **extra):
    """The least state that reaches the probe: a log, an empty shared_data
    so every block check fails, and the keys _ran_clean reads."""
    state = {"tool_calls": log, "shared_data": {}, "final_response": "",
             "sub_results": {}, "errors": [], "warnings": []}
    state.update(extra)
    return state


def _mentions(fails, *words):
    return [f for f in fails if any(w in f for w in words)]


def test_1_2_reads_the_pnl_call_for_jpm_alone():
    good = _state([_record("position_pnl", {"tickers": ["JPM"]})])
    assert _mentions(run_cases.check_1_2(good), "tickers", "tool", "called") == []
    padded = _state([_record("position_pnl", {"tickers": ["JPM", "AAPL"]})])
    assert _mentions(run_cases.check_1_2(padded), "tickers ['JPM', 'AAPL'] != ['JPM']")
    wrong = _state([_record("allocation")])
    assert _mentions(run_cases.check_1_2(wrong), "not 'position_pnl'")
    two = _state([_record("allocation"), _record("position_pnl", {"tickers": ["JPM"]})])
    assert _mentions(run_cases.check_1_2(two), "tools called")
    none = _state([])
    assert _mentions(run_cases.check_1_2(none), "no tool was called")


def test_1_3_reads_the_volatility_call_at_one_year():
    good = _state([_record("portfolio_volatility", {"period": "1Y"})])
    assert _mentions(run_cases.check_1_3(good), "period", "tool", "called") == []
    span = _state([_record("portfolio_volatility", {"period": "3Y"})])
    assert _mentions(run_cases.check_1_3(span), "period is '3Y'; 'twelve months' is 1Y")
    wrong = _state([_record("allocation")])
    assert _mentions(run_cases.check_1_3(wrong), "not 'portfolio_volatility'")


def test_3_3_reads_the_pnl_call_with_no_ticker():
    good = _state([_record("position_pnl", {"tickers": []})])
    assert _mentions(run_cases.check_3_3(good), "tickers", "tool", "called") == []
    copied = _state([_record("position_pnl", {"tickers": sorted(run_cases.TICKERS)})])
    assert _mentions(run_cases.check_3_3(copied), "is not empty", "copied the portfolio in")
    wrong = _state([_record("allocation")])
    assert _mentions(run_cases.check_3_3(wrong), "not 'position_pnl'")


def _lookup(clauses, text=""):
    return _record("policy_lookup", {"topic": "share price"}, key="compliance",
                   block={"topic": {"asked": "share price", "clauses": clauses},
                          "no_clause": not clauses}, text=text)


def test_3_2_reads_the_lookup_that_found_the_scope_clause():
    good = _state([_lookup(["IPS-1.3"])], final_response="IPS-1.3 says so.",
                  sub_results={"ComplianceAgent": {"success": True}})
    assert _mentions(run_cases.check_3_2(good), "IPS-1.3", "tool", "called", "agents ran") == []
    missed = _state([_lookup([])], final_response="Nothing on it.")
    assert _mentions(run_cases.check_3_2(missed), "the lookup matched []")
    uncited = _state([_lookup(["IPS-1.3"])], final_response="The policy forbids it.")
    assert _mentions(run_cases.check_3_2(uncited), "answer does not cite IPS-1.3")
    ran = _state([_lookup(["IPS-1.3"])], final_response="IPS-1.3",
                 sub_results={"ComplianceAgent": {}, "DataAgent": {}})
    assert _mentions(run_cases.check_3_2(ran), "agents ran: ['DataAgent']")
    none = _state([], final_response="IPS-1.3 forbids a forecast.")
    assert _mentions(run_cases.check_3_2(none), "no tool was called")
    forecast = _state([_lookup(["IPS-1.3"])], final_response="IPS-1.3; it will reach 200.")
    assert _mentions(run_cases.check_3_2(forecast), "answer forecasts a price")


def _typo_turns(first_log=(), clarification=None, resolved=None, tickers=("AAPL",)):
    first = _state(list(first_log), final_response="Did you mean AAPL, not APPL?",
                   clarification=clarification)
    second = _state([_record("position_pnl", {"tickers": list(tickers)})],
                    resolved=resolved)
    return [first, second]


ASKED = {"kind": "unknown_ticker", "token": "APPL", "candidate": "AAPL",
         "message": "Hows my APPL doing?"}
RESOLVED = {"reply": "yes", "message": "Hows my AAPL doing?"}


def test_3_5_reads_the_clarification_and_the_resolved_call():
    good = _typo_turns(clarification=ASKED, resolved=RESOLVED)
    fails = run_cases.check_3_5(good)
    assert _mentions(fails, "turn 1 called", "clarification", "turn 2 tickers",
                     "not 'position_pnl'", "resolution") == []
    guessed = _typo_turns(first_log=[_record("position_pnl", {"tickers": ["AAPL"]})],
                          clarification=ASKED, resolved=RESOLVED)
    assert _mentions(run_cases.check_3_5(guessed), "turn 1 called")
    unrecorded = _typo_turns(clarification=None, resolved=RESOLVED)
    assert _mentions(run_cases.check_3_5(unrecorded), "turn 1 records no clarification")
    other = _typo_turns(clarification={**ASKED, "candidate": "AMZN"}, resolved=RESOLVED)
    assert _mentions(run_cases.check_3_5(other), "turn 1 asked back about 'APPL' for 'AMZN'")
    unresolved = _typo_turns(clarification=ASKED, resolved=None)
    assert _mentions(run_cases.check_3_5(unresolved), "turn 2 records no resolution")
    wrong = _typo_turns(clarification=ASKED, resolved=RESOLVED, tickers=("MSFT",))
    assert _mentions(run_cases.check_3_5(wrong), "turn 2 tickers ['MSFT'] != ['AAPL']")
