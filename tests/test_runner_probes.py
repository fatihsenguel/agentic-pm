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

The log's shape, as decided with the shape of this rewrite and extended
by decision 77: the state key `tool_calls`, a list in call order, emptied
every turn, one record per tool call with `tool`, `inputs`, `key`,
`block`, `text`, `blocks` (every summary block the run published),
`agents` (each agent that ran, with its success) and `provenance` (the
block's as-of, its source, the tool's caveats). The runner reads every
block and every agent from the records and nothing from the state's
`shared_data` or `sub_results`, which a finished turn leaves empty. A
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
    final_response: str


class _DoesNot(TypedDict):
    final_response: str


def test_a_state_type_that_declares_no_log_blocks_before_any_run():
    assert run_cases.state_declares_log(_Declares) is True
    assert run_cases.state_declares_log(_DoesNot) is False


def test_a_state_without_the_log_is_blocked_on_it():
    reason = run_cases.blocked_on_tool_log({"final_response": ""})
    assert reason is not None
    assert "tool-call log" in reason


def test_a_state_with_an_empty_log_is_not_blocked():
    assert run_cases.blocked_on_tool_log({"tool_calls": []}) is None


# ---------------------------------------------------------------------------
# The five input probes: which tool was called with which inputs
# ---------------------------------------------------------------------------

NO_PROVENANCE = {"as_of": None, "source": None, "caveats": ()}


def _record(tool, inputs=None, key=None, block=None, text="", blocks=None, agents=None):
    """A record as the tool runner writes it. `blocks` carries the tool's
    own block under its key when one is given and nothing otherwise, so a
    bare record publishes no block and every block check fails on it."""
    key = key or tool
    if blocks is None:
        blocks = {key: block} if block is not None else {}
    return {"tool": tool, "inputs": inputs or {}, "key": key, "block": block or {},
            "text": text, "blocks": blocks, "agents": agents or {},
            "provenance": dict(NO_PROVENANCE)}


def record_of(tool, inputs, shared, agents=None, text=""):
    """A record as the tool runner writes it from a run's final state, for
    a test that ran the nodes itself and hands the runner's checks the
    result: every block of the tool's table that `shared` carries, the
    tool's own under `block`. A block the test did not publish is left
    out rather than raised on, since the check under test reads only the
    ones it names."""
    from agents.tool_runner import BLOCKS, BLOCK_KEY

    key = BLOCK_KEY[tool]
    blocks = {k: shared[k] for k in BLOCKS[tool] if k in shared}
    return {"tool": tool, "inputs": dict(inputs), "key": key, "block": blocks.get(key) or {},
            "text": text, "blocks": blocks, "agents": dict(agents or {}),
            "provenance": dict(NO_PROVENANCE)}


def _state(log, **extra):
    """The least state that reaches the probe: a log and the keys
    _ran_clean reads. No `shared_data` and no `sub_results`: a finished
    turn leaves both empty, and the runner reads neither."""
    state = {"tool_calls": log, "final_response": "", "errors": [], "warnings": []}
    state.update(extra)
    return state


def _mentions(fails, *words):
    return [f for f in fails if any(w in f for w in words)]


# ---------------------------------------------------------------------------
# The accessors: every block and every agent is read from the records
# ---------------------------------------------------------------------------

def test_a_block_is_read_from_the_record_that_carries_it_and_not_from_the_state():
    left_behind = _state([_record("allocation")],
                         shared_data={"allocation": {"by_sector": {"lines": []}}})
    assert run_cases._block(left_behind, "allocation") == {}
    assert run_cases._published(left_behind, "allocation") is False
    carried = _state([_record("allocation", block={"by_sector": {"lines": []}})])
    assert run_cases._block(carried, "allocation") == {"by_sector": {"lines": []}}
    assert run_cases._published(carried, "allocation") is True


def test_two_records_with_the_same_key_read_as_the_later_one():
    """Two tools in one turn each publishing `compliance`: the later call's
    block is what the turn ended on, as the last run's state was before."""
    first = _record("hypothetical_weight", key="compliance", block={"findings": [1]})
    second = _record("compliance_check", key="compliance", block={"findings": [1, 2]})
    assert run_cases._block(_state([first, second]), "compliance") == {"findings": [1, 2]}
    assert run_cases._block(_state([second, first]), "compliance") == {"findings": [1]}


def test_a_block_beside_the_tools_own_is_read_from_the_same_record():
    """The compliance check's record carries the allocation its run
    published, which the block invariants read for the denominator."""
    record = _record("compliance_check", key="compliance", block={"findings": []},
                     blocks={"compliance": {"findings": []},
                             "allocation": {"by_asset_class": {"total_value": 1.0}}})
    assert run_cases._allocation(_state([record]), "by_asset_class") == {"total_value": 1.0}


def test_the_agents_are_read_from_every_record():
    state = _state([_record("allocation", agents={"DataAgent": True,
                                                  "PortfolioAnalysisAgent": True}),
                    _record("compliance_check", agents={"DataAgent": True,
                                                        "PortfolioAnalysisAgent": False,
                                                        "ComplianceAgent": True})],
                   sub_results={"RebalanceAgent": {"success": True}})
    assert run_cases._agents(state) == {"DataAgent": True, "PortfolioAnalysisAgent": False,
                                        "ComplianceAgent": True}
    assert run_cases._agents(_state([])) == {}


def test_1_2_reads_the_pnl_call_for_jpm_alone():
    good = _state([_record("position_pnl", {"tickers": ["JPM"]})])
    assert _mentions(run_cases.check_1_2(good), "tickers", "tool", "called") == []
    padded = _state([_record("position_pnl", {"tickers": ["JPM", "AAPL"]})])
    assert _mentions(run_cases.check_1_2(padded), "tickers ['JPM', 'AAPL'] != ['JPM']")
    wrong = _state([_record("allocation")])
    assert _mentions(run_cases.check_1_2(wrong), "not 'position_pnl'")
    twice = _state([_record("position_pnl", {"tickers": ["JPM"]}),
                    _record("position_pnl", {"tickers": ["JPM"]})])
    assert _mentions(run_cases.check_1_2(twice), "'position_pnl' was called 2 times")
    none = _state([])
    assert _mentions(run_cases.check_1_2(none), "no tool was called")


# ---------------------------------------------------------------------------
# A case names its tool and allows others beside it (decision 17): the
# model composes, and Part 18 pins the answer whatever routes it. The case
# reads its blocks from its own tool's record, since every portfolio tool
# publishes the same three blocks. 3.2 alone keeps one call, its Part 18
# entry pinning that no other pipeline runs.
# ---------------------------------------------------------------------------

ROUTING = ("tools called", "the case is one call", "not '", "called 2 times")


def test_a_case_allows_other_tools_beside_its_own():
    beside = _record("allocation")
    cases = [
        (run_cases.check_1_2, _state([beside, _record("position_pnl", {"tickers": ["JPM"]})])),
        (run_cases.check_1_3, _state([_record("portfolio_volatility", {"period": "1Y"}), beside])),
        (run_cases.check_3_3, _state([beside, _record("position_pnl", {"tickers": []})])),
        (run_cases.check_2_1, _state([beside, _record("compliance_check",
                                                      key="compliance")])),
    ]
    for check, state in cases:
        assert _mentions(check(state), *ROUTING) == [], check.__name__
    three_one = _type_turns()
    three_one[1]["tool_calls"].insert(0, _record("policy_lookup", {"topic": "limits"},
                                                 key="compliance"))
    assert _mentions(run_cases.check_3_1(three_one), *ROUTING) == []
    three_five = _typo_turns(clarification=ASKED, resolved=RESOLVED)
    three_five[1]["tool_calls"].append(beside)
    assert _mentions(run_cases.check_3_5(three_five), *ROUTING) == []


def test_a_case_reads_its_blocks_from_its_own_tools_record():
    """1.2's P&L for JPM alone, then the allocation, whose run publishes a
    position_pnl block of its own: the case reads the P&L call's."""
    own = {"JPM": {"cost_basis": 20_000.00, "quantity": 100, "average_price": 200.0,
                   "purchase_date": "2024-07-15"}}
    other = {"JPM": {"cost_basis": 1.00, "quantity": 1, "average_price": 1.0,
                     "purchase_date": "2020-01-01"}}
    pnl = _record("position_pnl", {"tickers": ["JPM"]}, block=own)
    allocation = _record("allocation", blocks={"position_pnl": other})
    fails = run_cases.check_1_2(_state([pnl, allocation]))
    assert _mentions(fails, "cost basis", "holding", "purchase_date") == []
    fails = run_cases.check_1_2(_state([allocation, pnl]))
    assert _mentions(fails, "cost basis", "holding", "purchase_date") == []


def test_2_1_reads_the_compliance_block_of_its_own_call():
    """A hypothetical weight after the check publishes a compliance block
    of refused findings; 2.1 reads the check's."""
    own = {"findings": [], "policy": {}}
    other = {"findings": [{"status": "refused", "clause": "IPS-4.1", "subject": "x"}]}
    check = _record("compliance_check", key="compliance", block=own)
    weight = _record("hypothetical_weight", {"weight": 0.15, "instrument_type": "share"},
                     key="compliance", block=other)
    assert _mentions(run_cases.check_2_1(_state([check, weight])), "refused") == []


def test_3_2_is_one_call_alone():
    beside = _state([_record("allocation"), _lookup(["IPS-1.3"])], final_response="IPS-1.3")
    assert _mentions(run_cases.check_3_2(beside), "tools called")


def test_1_3_reads_the_volatility_call_at_one_year():
    good = _state([_record("portfolio_volatility", {"period": "1Y"})])
    assert _mentions(run_cases.check_1_3(good), "period", "tool", "called") == []
    span = _state([_record("portfolio_volatility", {"period": "3Y"})])
    assert _mentions(run_cases.check_1_3(span), "period is '3Y'; 'twelve months' is 1Y")
    wrong = _state([_record("allocation")])
    assert _mentions(run_cases.check_1_3(wrong), "not 'portfolio_volatility'")


def test_1_3_reads_the_block_from_the_record_and_no_single_name_volatilities():
    """The nine single-name volatilities were read beside the block for a
    weighted-average check that tests/test_analysis_node.py now holds
    over the committed closes (decision 77). A figure above that average
    is not this check's to refuse, and nothing beside the record is read."""
    block = {"annualised": 0.5, "weights": {t: 1 / 9 for t in sorted(run_cases.TICKERS)},
             "weights_as_of": "2026-09-21", "annualisation": 252, "covariance_method": "sample",
             "window": {"start": "2025-09-22", "end": "2026-09-21", "closes": 252}}
    state = _state([_record("portfolio_volatility", {"period": "1Y"}, block=block)],
                   shared_data={"volatilities": {t: 0.1 for t in run_cases.TICKERS}})
    fails = run_cases.check_1_3(state)
    assert _mentions(fails, "no portfolio_volatility", "weighted average") == []
    assert _mentions(fails, "never reaches the answer")


def test_3_3_reads_the_pnl_call_with_no_ticker():
    good = _state([_record("position_pnl", {"tickers": []})])
    assert _mentions(run_cases.check_3_3(good), "tickers", "tool", "called") == []
    copied = _state([_record("position_pnl", {"tickers": sorted(run_cases.TICKERS)})])
    assert _mentions(run_cases.check_3_3(copied), "is not empty", "copied the portfolio in")
    wrong = _state([_record("allocation")])
    assert _mentions(run_cases.check_3_3(wrong), "not 'position_pnl'")


def _lookup(clauses, text="", agents=None):
    return _record("policy_lookup", {"topic": "share price"}, key="compliance",
                   block={"topic": {"asked": "share price", "clauses": clauses},
                          "no_clause": not clauses}, text=text,
                   agents=agents or {"ComplianceAgent": True})


def test_3_2_reads_the_lookup_that_found_the_scope_clause():
    good = _state([_lookup(["IPS-1.3"])], final_response="IPS-1.3 says so.")
    assert _mentions(run_cases.check_3_2(good), "IPS-1.3", "tool", "called", "agents ran") == []
    missed = _state([_lookup([])], final_response="Nothing on it.")
    assert _mentions(run_cases.check_3_2(missed), "the lookup matched []")
    uncited = _state([_lookup(["IPS-1.3"])], final_response="The policy forbids it.")
    assert _mentions(run_cases.check_3_2(uncited), "answer does not cite IPS-1.3")
    ran = _state([_lookup(["IPS-1.3"], agents={"ComplianceAgent": True, "DataAgent": True})],
                 final_response="IPS-1.3")
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


QUESTION = "I want to put 15% into a single position, is that allowed?"
ASKED_TYPE = {"kind": "instrument_type", "token": None, "candidate": None,
              "message": QUESTION}
RESOLVED_TYPE = {"reply": "A share.", "message": QUESTION + " A share."}


def _type_turns(first_log=(), clarification=ASKED_TYPE, resolved=RESOLVED_TYPE,
                inputs=None):
    first = _state(list(first_log), clarification=clarification,
                   final_response="Would it be a directly held share or a fund?")
    second = _state([_record("hypothetical_weight",
                             inputs or {"weight": 0.15, "instrument_type": "share"},
                             key="compliance")],
                    resolved=resolved)
    return [first, second]


def test_3_1_reads_the_type_asked_back_and_the_share_call():
    good = _type_turns()
    assert _mentions(run_cases.check_3_1(good), "turn 1", "turn 2 records",
                     "turn 2 inputs", "tool", "called") == []
    guessed = _type_turns(first_log=[_record("hypothetical_weight", {"weight": 0.15})])
    assert _mentions(run_cases.check_3_1(guessed), "turn 1 called")
    unrecorded = _type_turns(clarification=None)
    assert _mentions(run_cases.check_3_1(unrecorded), "turn 1 records no clarification")
    unresolved = _type_turns(resolved=None)
    assert _mentions(run_cases.check_3_1(unresolved), "turn 2 records no resolution")
    assumed = _type_turns(inputs={"weight": 0.15, "instrument_type": "fund"})
    assert _mentions(run_cases.check_3_1(assumed), "turn 2 inputs")
    weight = _type_turns(inputs={"weight": 0.12, "instrument_type": "share"})
    assert _mentions(run_cases.check_3_1(weight), "turn 2 inputs")


# ---------------------------------------------------------------------------
# The four blocked_on probes: the block still decides, the reason names
# what the log shows
# ---------------------------------------------------------------------------

CALLED = "the layer called [('allocation', {})]"


def test_blocked_on_compliance_names_what_the_log_shows():
    assert run_cases.blocked_on_delegation_trace is run_cases.blocked_on_compliance
    ran = _state([_record("compliance_check", agents={"ComplianceAgent": True})])
    assert run_cases.blocked_on_compliance(ran) is None
    left_behind = _state([_record("compliance_check")],
                         sub_results={"ComplianceAgent": {"success": True}})
    assert "ComplianceAgent did not run" in run_cases.blocked_on_compliance(left_behind)
    other = _state([_record("allocation")])
    reason = run_cases.blocked_on_compliance(other)
    assert "ComplianceAgent did not run" in reason and CALLED in reason
    asked = _state([], clarification=ASKED, final_response="Did you mean AAPL?")
    assert "asked back: 'Did you mean AAPL?'" in run_cases.blocked_on_compliance(asked)
    nothing = _state([])
    assert "called no tool" in run_cases.blocked_on_compliance(nothing)


def test_blocked_on_screen_names_what_the_log_shows():
    reached = _state([_record("philosophy_screen", {"ticker": "GOOGL"}, key="screening",
                              block={"subject": {"ticker": "GOOGL"}})])
    assert run_cases.blocked_on_screen(reached) is None
    reason = run_cases.blocked_on_screen(_state([_record("allocation")], errors=["x"]))
    assert "no screening block" in reason and CALLED in reason and "errors: ['x']" in reason


def test_blocked_on_ledger_names_what_the_log_shows():
    reached = _state([_record("ledger", block={"records": []})])
    assert run_cases.blocked_on_ledger(reached) is None
    reason = run_cases.blocked_on_ledger(_state([_record("allocation")]))
    assert "no ledger block" in reason and CALLED in reason


def test_blocked_on_research_names_what_the_log_shows():
    reached = _state([_record("thesis", {"ticker": "GOOGL"}, key="research",
                              block={"asks": "thesis"})])
    assert run_cases.blocked_on_research(reached) is None
    reason = run_cases.blocked_on_research(_state([], clarification=ASKED,
                                                  final_response="Did you mean AAPL?"))
    assert "no research block" in reason and "asked back: 'Did you mean AAPL?'" in reason


# ---------------------------------------------------------------------------
# check_2_1's handover probe: one call, and the steps in plan order from
# the trace, which the trace helper reads as it does today
# ---------------------------------------------------------------------------

def test_2_1_reads_the_compliance_call_and_leaves_the_plan_to_the_trace():
    ran = {a: True for a in run_cases.COMPLIANCE_PLAN}
    good = _state([_record("compliance_check", agents=ran)])
    assert _mentions(run_cases.check_2_1(good), "tool", "called", "plan",
                     "did not run successfully") == []
    unsure = _state([_record("compliance_check", agents={**ran, "DataAgent": False})])
    assert _mentions(run_cases.check_2_1(unsure), "did not run successfully: ['DataAgent']")
    wrong = _state([_record("allocation")])
    assert _mentions(run_cases.check_2_1(wrong), "not 'compliance_check'")
    carried = _state([_record("compliance_check", {"tickers": ["AAPL"]})])
    assert _mentions(run_cases.check_2_1(carried), "compliance_check takes no input")


# ---------------------------------------------------------------------------
# What a case cost: the usage the layer records for every model call
# (decision 45), summed over every turn, in tokens and never in money
# ---------------------------------------------------------------------------

def _calls(*usages):
    return [{"model": "claude-sonnet-5", "input_tokens": i, "output_tokens": o,
             "cache_creation_input_tokens": w, "cache_read_input_tokens": r}
            for i, o, w, r in usages]


def test_the_usage_line_sums_every_call_of_every_turn():
    states = [{"model_calls": _calls((4200, 60, 4000, 0), (300, 40, 0, 4000))},
              {"model_calls": _calls((1250, 35, 0, 4000))}]
    assert run_cases.usage_line(states) == (
        "tokens: 5,750 in, 135 out, 4,000 cache written, 8,000 cache read, 3 calls")


def test_a_turn_the_pre_pass_answered_calls_nothing():
    assert run_cases.usage_line([{"model_calls": []}]) == (
        "tokens: 0 in, 0 out, 0 cache written, 0 cache read, 0 calls")


def test_a_turn_that_recorded_no_usage_says_so():
    """A state without the key is a layer that did not record, which is a
    finding and not a zero."""
    assert run_cases.usage_line([{"model_calls": []}, {}]) == "tokens: not recorded on turn 2"
