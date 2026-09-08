"""
A second turn sees the first: the state carries the previous turn's
messages and the record of what was asked, and the decision dict carries
the question and the record so the CLI and the next turn can read them.

No LLM, no database. The router is stubbed where a node is run.
"""

import inspect
from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage

from agents import smart_router
from agents.extraction import Extraction
from agents.graph import run_agent_graph, run_agent_graph_sync
from agents.nodes import router_node
from agents.schemas import ExtractedParameters, RouterDecision
from agents.smart_router import _with_extraction
from agents.state import create_initial_state, get_user_message


PENDING = {"kind": "unknown_ticker", "token": "APPL", "candidate": "AAPL",
           "message": "Hows my APPL doing?"}


def _first_turn(intent="clarification_needed", pending=PENDING):
    state = create_initial_state("Hows my APPL doing?", "t1", portfolio_id=3)
    state["router_decision"] = {"intent": intent, "parameters": {}, "execution_order": [],
                                "clarification_question": "Did you mean AAPL?", "pending": pending}
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
    answered = _first_turn(intent="data_fetch", pending=None)
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


class _StubRouter:
    def __init__(self, pending):
        self._pending = pending

    async def route(self, user_message, portfolio_id=None, **kwargs):
        decision = SimpleNamespace(
            intent="clarification_needed", confidence=1.0, agents_needed=[],
            parameters=ExtractedParameters(), execution_order=[],
            clarification_question="Did you mean AAPL?", pending=self._pending,
        )
        return decision, SimpleNamespace(errors=[])


async def test_the_decision_dict_carries_the_question_and_the_record(monkeypatch):
    """_decision_to_dict dropped clarification_question (KNOWN_GAPS): the
    CLI's "asked back" line never printed and the next turn had nothing
    structured to resolve against."""
    monkeypatch.setattr(smart_router, "get_router", lambda: _StubRouter(PENDING))
    out = await router_node(create_initial_state("Hows my APPL doing?", portfolio_id=3))
    decision = out["router_decision"]
    assert decision["clarification_question"] == "Did you mean AAPL?"
    assert decision["pending"] == PENDING
    assert out["final_response"] == "Did you mean AAPL?"


def test_the_schema_holds_a_record_the_model_cannot_write():
    decision = RouterDecision.model_validate({
        "intent": "clarification_needed", "confidence": 1.0, "parameters": {},
        "reasoning": "extraction asked about a typo", "clarification_question": "Did you mean AAPL?",
        "pending": PENDING})
    assert decision.pending == PENDING
    extraction = Extraction(tickers=[], period=None, max_volatility=None,
                            hypothetical_weight=None, clarification=None)
    raw = {"intent": "out_of_scope", "parameters": {}, "pending": {"kind": "planted by the model"}}
    assert _with_extraction(raw, extraction, "Should I buy Nvidia?")["pending"] is None
