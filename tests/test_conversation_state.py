"""
A second turn sees the first: the state carries the previous turn's
messages and the record of what was asked back, so the next turn can
resolve its reply against it.

No LLM, no database.
"""

import inspect

from agents.graph import run_agent_graph, run_agent_graph_sync
from agents.state import create_initial_state, get_user_message


PENDING = {"kind": "unknown_ticker", "token": "APPL", "candidate": "AAPL",
           "message": "Hows my APPL doing?"}


def _first_turn(pending=PENDING):
    """A first turn as the layer leaves it: the record of what the pre-pass
    asked back under `clarification`, None when the turn answered."""
    state = create_initial_state("Hows my APPL doing?", "t1", portfolio_id=3)
    state["clarification"] = pending
    state["final_response"] = "APPL is not a ticker I know. Did you mean AAPL, which you hold?"
    return state


def test_the_second_turn_carries_the_first_turns_messages_and_record():
    second = create_initial_state("yes", "t2", portfolio_id=3, previous=_first_turn())
    assert [type(m).__name__ for m in second["messages"]] == ["HumanMessage", "AIMessage", "HumanMessage"]
    assert second["messages"][0].content == "Hows my APPL doing?"
    assert second["messages"][1].content.startswith("APPL is not a ticker I know")
    assert second["messages"][2].content == "yes"
    assert second["pending"] == PENDING
    assert second["portfolio_id"] == 3
    assert second["request_id"] == "t2"


def test_the_current_message_is_the_last_human_one():
    """get_user_message returned the first human message, which with a
    history is the previous turn's question, not the reply."""
    second = create_initial_state("yes", previous=_first_turn())
    assert get_user_message(second) == "yes"


def test_a_previous_turn_that_was_answered_leaves_no_record():
    answered = _first_turn(pending=None)
    second = create_initial_state("and MSFT?", previous=answered)
    assert second["pending"] is None
    assert len(second["messages"]) == 3


def test_no_previous_turn_means_no_record_and_one_message():
    first = create_initial_state("Hows my APPL doing?")
    assert first["pending"] is None
    assert len(first["messages"]) == 1


def test_the_entry_points_take_the_previous_state():
    for entry in (run_agent_graph, run_agent_graph_sync):
        assert "previous" in inspect.signature(entry).parameters
