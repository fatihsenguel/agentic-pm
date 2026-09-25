"""
`check_4_3`'s prediction requirement, held in pytest (decision 69).

Why this file exists. `check_4_4` is exercised by test_thesis_formatter.py
over a rendered answer; `check_4_3` was exercised by nothing, the case
being blocked at out_of_scope before the check ever runs. A rule nothing
runs is a rule nobody can be wrong about, so the requirement decision 69
put into the check is run here directly.

What this holds: that a prediction **entered** in the ledger under the
candidate, cited by id, satisfies the case, and that a prediction proposed
in the same run does not. W-1.1 and W-1.2 are the entered rows today.

What this does not hold: the rest of check_4_3, which needs the whole 4.3
answer and gets its harness when the answer exists. These states are built
to reach one branch and fail every other, so each test asserts on the
presence or absence of that one failure and never on the list being empty.
"""

import sys
from pathlib import Path

import pytest
import tomli

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tests" / "benchmark"))

import run_cases  # noqa: E402


MISSING = "no prediction entered in the ledger under"


def _entered_ids():
    with open(ROOT / "watchlist.toml", "rb") as f:
        raw = tomli.load(f)
    for candidate in raw["candidate"]:
        if candidate["ticker"] == run_cases.WATCHLIST_TICKER:
            return [p["id"] for p in candidate["prediction"]]
    raise AssertionError(f"watchlist.toml has no {run_cases.WATCHLIST_TICKER}")


def _state(answer):
    """The least state that reaches the prediction branch: a position
    record carrying a research block so the check does not stop at the
    top, and an answer to look in. Everything else fails, which is what
    the tests below rely on. The block is on the record and nowhere else:
    the runner reads the records (decision 77)."""
    research = {"asks": "position", "subject": {}}
    return {
        "tool_calls": [{"tool": "position", "inputs": {"ticker": run_cases.WATCHLIST_TICKER},
                        "key": "research", "block": research, "text": "",
                        "blocks": {"research": research}, "agents": {},
                        "provenance": {"as_of": None, "source": None, "caveats": ()}}],
        "final_response": answer,
        "errors": [],
    }


def test_the_committed_ledger_has_rows_to_cite():
    """The tests below are vacuous if the candidate carries no entered
    prediction, so the fixture is checked before it is relied on."""
    assert _entered_ids() == ["W-1.1", "W-1.2"]


def test_an_entered_prediction_cited_by_id_satisfies_the_case():
    fails = run_cases.check_4_3(_state("... as W-1.1 says, by 1 March 2027 ..."))
    assert not any(MISSING in f for f in fails)


def test_a_proposal_alone_does_not():
    """benchmark.md's words are "entered in the ledger", and the ledger is
    this level's eval set: a row the system proposed and I have not typed
    is not in it (decision 69)."""
    fails = run_cases.check_4_3(_state("... proposed, not entered: W-1.3 ..."))
    assert any(MISSING in f for f in fails)


def test_an_answer_citing_no_prediction_does_not():
    fails = run_cases.check_4_3(_state("Alphabet clears nothing and the gate refuses."))
    assert any(MISSING in f for f in fails)


def test_the_failure_names_what_the_ledger_carries():
    """A refusal that does not say what it wanted is a refusal nobody can
    act on."""
    fails = run_cases.check_4_3(_state("nothing cited"))
    named = [f for f in fails if MISSING in f]
    assert len(named) == 1
    for pid in _entered_ids():
        assert pid in named[0]


def test_a_prediction_of_another_candidate_does_not_satisfy_it():
    """W-2.1 is Adobe's. The case is about this candidate's thesis."""
    fails = run_cases.check_4_3(_state("... W-2.1 falls due in February ..."))
    assert any(MISSING in f for f in fails)
