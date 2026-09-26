"""
A turn through the conversation layer (Order 5, decision 45): the entry
point the runner and the CLI call, with the router gone from its path.

A turn resolves a reply against the record the previous turn asked back,
then runs the pre-pass: where extraction asks back, that is the answer, no
model is called, and the record is written under `clarification`.
Otherwise the layer answers with the tools, and the turn's state carries
the tool-call log and the usage of every call. The records carry every
block a run published; the state's `shared_data` and `sub_results` are
the tool graph's inside a run and a finished turn leaves them empty
(decision 77). The layer is stood in here, so nothing is paid for;
extraction and the tools' context are read for real, from the suite's
copy of the database and the committed watchlist.
"""

import pytest

from agents import graph
from agents.state import AgentState

TYPE_QUESTION = "I want to put 15% into a single position, is that allowed?"
LOG = [{"tool": "hypothetical_weight", "inputs": {"weight": 0.15, "instrument_type": "share"},
        "key": "compliance", "block": {"findings": []}, "text": "IPS-4.1 15.00% refused",
        "blocks": {"compliance": {"findings": []}}, "agents": {"ComplianceAgent": True},
        "provenance": {"as_of": None, "source": None, "caveats": ()}}]
CALLS = [{"model": "claude-sonnet-5", "input_tokens": 1, "output_tokens": 1,
          "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}]


@pytest.fixture
def layer(monkeypatch):
    """The conversation layer stood in: every call it is asked records what
    it was given and answers with one hypothetical_weight call. It returns
    what the layer returns and no run's state: the record carries the
    block."""
    asked = []

    async def answer(message, *, history, context, portfolio_id, model, request_id=None,
                     earlier=()):
        asked.append({"message": message, "history": list(history), "context": context,
                      "portfolio_id": portfolio_id, "model": model, "earlier": list(earlier)})
        return {"text": "Refused under IPS-4.1.", "tool_calls": LOG, "model_calls": CALLS}

    monkeypatch.setattr(graph, "answer", answer)
    monkeypatch.setattr(graph, "conversation_model", lambda: "the conversation model")
    return asked


def test_the_state_declares_the_log_and_what_the_pre_pass_writes():
    declared = AgentState.__annotations__
    for key in ("tool_calls", "clarification", "resolved", "model_calls", "earlier"):
        assert key in declared, key


async def test_a_question_the_pre_pass_asks_about_calls_no_model(layer):
    state = await graph.run_agent_graph(TYPE_QUESTION, portfolio_id=3)
    assert layer == []
    assert "share" in state["final_response"] and "fund" in state["final_response"]
    assert state["clarification"]["kind"] == "instrument_type"
    assert (state["tool_calls"], state["model_calls"], state["resolved"]) == ([], [], None)
    assert state["sub_results"] == {}


async def test_the_reply_is_resolved_and_answered_as_the_question_it_stands_for(layer):
    first = await graph.run_agent_graph(TYPE_QUESTION, portfolio_id=3)
    second = await graph.run_agent_graph("A share.", portfolio_id=3, previous=first)
    [call] = layer
    assert call["message"] == TYPE_QUESTION + " It would be a share."
    assert second["resolved"] == {"reply": "A share.", "message": call["message"]}
    assert second["clarification"] is None
    assert (second["tool_calls"], second["model_calls"]) == (LOG, CALLS)
    assert second["final_response"] == "Refused under IPS-4.1."


async def test_a_finished_turn_leaves_the_runs_state_empty(layer):
    """The block is on the record; `shared_data` and `sub_results` are the
    tool graph's inside a run, and a turn copies nothing out of the last
    run into the state it returns (decision 77)."""
    state = await graph.run_agent_graph("What is my allocation?", portfolio_id=3)
    assert state["tool_calls"] == LOG
    assert (state["shared_data"], state["sub_results"]) == ({}, {})


async def test_the_layer_is_given_the_portfolio_the_vocabulary_and_the_watchlist(layer):
    await graph.run_agent_graph("What is my allocation by asset class?", portfolio_id=3)
    [call] = layer
    context = call["context"]
    assert {"AAPL", "JPM", "SPY"} <= set(context.held)
    assert "1Y" in context.periods and "10Y" in context.periods
    assert {"GOOGL", "ADBE"} <= set(context.watchlist)
    assert (call["portfolio_id"], call["model"]) == (3, "the conversation model")


async def test_the_history_is_the_previous_turns_question_and_answer(layer):
    first = await graph.run_agent_graph("How has my JPM position performed?", portfolio_id=3)
    await graph.run_agent_graph("And MSFT?", portfolio_id=3, previous=first)
    assert layer[1]["history"] == [
        {"role": "user", "content": "How has my JPM position performed?"},
        {"role": "assistant", "content": "Refused under IPS-4.1."},
    ]
    assert layer[1]["message"] == "And MSFT?"


async def test_the_earlier_turns_records_and_questions_are_carried_and_given_to_the_layer(layer):
    """Decision 77's follow-up: S-4's turn 2 quoted figures from turn 1's
    answer, each of which had passed turn 1's check against turn 1's
    records and question. The turn carries every earlier turn's question
    and records under `earlier`, and gives the layer their texts as the
    figures the answer may carry beside this turn's own. The model's
    history stays answers only."""
    first = await graph.run_agent_graph("How has my JPM position performed?", portfolio_id=3)
    assert first["earlier"] == []
    second = await graph.run_agent_graph("And MSFT?", portfolio_id=3, previous=first)
    assert second["earlier"] == [{"question": "How has my JPM position performed?",
                                  "tool_calls": LOG}]
    assert layer[1]["earlier"] == ["How has my JPM position performed?", "IPS-4.1 15.00% refused"]
    assert layer[1]["history"][0]["content"] == "How has my JPM position performed?"
    assert all("15.00%" not in m["content"] for m in layer[1]["history"])


async def test_a_resolved_turn_is_carried_under_the_question_it_was_checked_against(layer):
    """A clarification turn carries its typed question and no record; the
    reply's turn carries the message it was resolved into, which is the
    question its answer was checked against, and not the reply."""
    first = await graph.run_agent_graph(TYPE_QUESTION, portfolio_id=3)
    second = await graph.run_agent_graph("A share.", portfolio_id=3, previous=first)
    third = await graph.run_agent_graph("And at 10%?", portfolio_id=3, previous=second)
    assert third["earlier"] == [
        {"question": TYPE_QUESTION, "tool_calls": []},
        {"question": TYPE_QUESTION + " It would be a share.", "tool_calls": LOG},
    ]
    assert layer[1]["earlier"] == [TYPE_QUESTION, TYPE_QUESTION + " It would be a share.",
                                   "IPS-4.1 15.00% refused"]


async def test_an_ask_back_with_no_rule_records_no_kind_and_resolves_nothing(layer):
    first = await graph.run_agent_graph("Put 15% into AAPL and 20% into MSFT", portfolio_id=3)
    assert layer == []
    assert first["clarification"] == {"kind": None, "token": None, "candidate": None,
                                      "message": "Put 15% into AAPL and 20% into MSFT"}
    second = await graph.run_agent_graph("What is my allocation?", portfolio_id=3, previous=first)
    assert second["resolved"] is None
    assert layer[0]["message"] == "What is my allocation?"


async def test_a_turn_the_layer_could_not_finish_is_an_error_shown_and_its_calls_counted(
        layer, monkeypatch):
    """The calls made before the model stopped were paid for, so they are
    recorded with the error and not lost with the answer."""
    from agents.conversation import ConversationError

    async def unfinished(message, **kwargs):
        raise ConversationError("The model stopped on 'max_tokens'; nothing is shown.",
                                model_calls=CALLS)

    monkeypatch.setattr(graph, "answer", unfinished)
    state = await graph.run_agent_graph("What is my allocation?", portfolio_id=3)
    assert state["final_response"] == "The model stopped on 'max_tokens'; nothing is shown."
    assert state["errors"] == [state["final_response"]]
    assert state["tool_calls"] == [] and state["model_calls"] == CALLS
