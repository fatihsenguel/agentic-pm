"""
mark_agent_complete emits one DELEGATION event per hand-over.

The trace is what benchmark 2.1 reads for "contract handovers": when an
agent finishes and another is still planned, the finishing agent delegates
to the next one, naming the keys it published. The last agent delegates to
nobody, and outside a request nothing is emitted.
"""

from agents.state import create_initial_state, mark_agent_complete
from observability import Tracer, TraceLevel, get_tracer, set_tracer
from observability.tracer import TraceEventType


def _state(plan):
    state = create_initial_state("check my policy")
    state["agents_to_run"] = list(plan)
    return state


def _delegations(trace):
    return [(e.agent_name, e.metadata["to_agent"], e.metadata["task"])
            for e in trace.events if e.event_type == TraceEventType.DELEGATION]


def test_finishing_agent_delegates_to_the_next_in_plan():
    previous = get_tracer()
    tracer = Tracer(level=TraceLevel.VERBOSE, console_output=False)
    set_tracer(tracer)
    try:
        with tracer.trace_request("handover_test", "check my policy"):
            state = _state(["DataAgent", "PortfolioAnalysisAgent", "ComplianceAgent"])
            out = mark_agent_complete(state, "DataAgent",
                                      {"success": True, "agent_name": "DataAgent",
                                       "latest_prices": {}, "holdings": []})
            state.update(out)
            out = mark_agent_complete(state, "PortfolioAnalysisAgent",
                                      {"success": True, "allocation": {}, "position_pnl": {}})
            state.update(out)
            out = mark_agent_complete(state, "ComplianceAgent",
                                      {"success": True, "compliance": {}})
        [trace] = tracer.get_traces()[-1:]
        assert _delegations(trace) == [
            ("DataAgent", "PortfolioAnalysisAgent", "via shared_data: holdings, latest_prices"),
            ("PortfolioAnalysisAgent", "ComplianceAgent", "via shared_data: allocation, position_pnl"),
        ]
        assert out["agents_to_run"] == []
    finally:
        set_tracer(previous)


def test_a_failed_agent_hands_over_nothing_but_still_delegates():
    previous = get_tracer()
    tracer = Tracer(level=TraceLevel.VERBOSE, console_output=False)
    set_tracer(tracer)
    try:
        with tracer.trace_request("handover_fail", "check my policy"):
            mark_agent_complete(_state(["DataAgent", "ComplianceAgent"]), "DataAgent",
                                {"success": False, "error": "boom"})
        [trace] = tracer.get_traces()[-1:]
        assert _delegations(trace) == [("DataAgent", "ComplianceAgent", "no data published")]
    finally:
        set_tracer(previous)


def test_no_request_no_event():
    out = mark_agent_complete(_state(["DataAgent", "ComplianceAgent"]), "DataAgent",
                              {"success": True, "latest_prices": {}})
    assert out["agents_to_run"] == ["ComplianceAgent"]
