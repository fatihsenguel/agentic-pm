"""
The request trace outlives the router node.

The router used to open the request span and close it in its own finally,
so every agent after it found no current request and traced nothing. Now
run_agent_graph owns the span. This test runs router_node inside an open
request with the smart router stubbed - no LLM - and asserts the request
is still open afterwards and holds the Router's span.
"""

from types import SimpleNamespace

from agents import smart_router
from agents.nodes import router_node
from agents.schemas import ExtractedParameters
from agents.state import create_initial_state
from observability import Tracer, TraceLevel, get_tracer, set_tracer
from observability.tracer import TraceEventType


class _StubRouter:
    async def route(self, user_message, portfolio_id=None, pending=None):
        decision = SimpleNamespace(
            intent="data_fetch",
            confidence=0.9,
            parameters=ExtractedParameters(),
            execution_order=["DataAgent"],
            clarification_question=None,
        )
        return decision, SimpleNamespace(errors=[])


async def test_router_leaves_the_request_open(monkeypatch):
    monkeypatch.setattr(smart_router, "get_router", lambda: _StubRouter())
    previous = get_tracer()
    tracer = Tracer(level=TraceLevel.VERBOSE, console_output=False)
    set_tracer(tracer)
    try:
        with tracer.trace_request("span_test", "what do I hold?"):
            out = await router_node(create_initial_state("what do I hold?", "span_test"))
            assert out["agents_to_run"] == ["DataAgent"]
            assert tracer.get_current_request() is not None, "router closed the request"
        [trace] = tracer.get_traces()[-1:]
        assert trace.request_id == "span_test"
        assert [e.agent_name for e in trace.events
                if e.event_type == TraceEventType.AGENT_START] == ["Router"]
    finally:
        set_tracer(previous)
