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
