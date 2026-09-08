"""
The router's rejected attempts reach the state.

SmartRouter retries a decision that fails validation and records each failed
attempt on the ValidationResult it returns. router_node used to loop over
those, call add_warning and drop the dict it returned, so no retry ever
reached state["warnings"], the CLI's WARNINGS section or the golden runner.
A plan rejected and repaired back to the same routing was indistinguishable
from a plan accepted first time. These tests run router_node with the smart
router stubbed - no LLM - and assert the attempts come through, on both
return paths, prefixed as the node has always prefixed them.
"""

from types import SimpleNamespace

from agents import smart_router
from agents.nodes import router_node
from agents.schemas import ExtractedParameters
from agents.state import create_initial_state


ATTEMPTS = [
    "Attempt 1: PortfolioAnalysisAgent requires DataAgent before it",
    "Attempt 2: JSON parse error: Expecting value",
]


class _StubRouter:
    def __init__(self, intent, errors, plan=("DataAgent",), question=None):
        self._decision = SimpleNamespace(
            intent=intent,
            confidence=0.9,
            agents_needed=[
                SimpleNamespace(agent=a, task_description="fetch", priority=i + 1)
                for i, a in enumerate(plan)
            ],
            parameters=ExtractedParameters(),
            execution_order=list(plan),
            clarification_question=question,
        )
        self._errors = errors

    async def route(self, user_message, portfolio_id=None, pending=None):
        return self._decision, SimpleNamespace(errors=list(self._errors))


async def test_rejected_attempts_reach_the_state_with_the_plan(monkeypatch):
    monkeypatch.setattr(smart_router, "get_router",
                        lambda: _StubRouter("data_fetch", ATTEMPTS))
    out = await router_node(create_initial_state("what do I hold?"))
    assert out["agents_to_run"] == ["DataAgent"]
    assert out["warnings"] == [f"Validation: {a}" for a in ATTEMPTS]


async def test_rejected_attempts_reach_the_state_with_a_clarification(monkeypatch):
    monkeypatch.setattr(smart_router, "get_router",
                        lambda: _StubRouter("clarification_needed", ATTEMPTS[:1],
                                            plan=(), question="Which position?"))
    out = await router_node(create_initial_state("position?"))
    assert out["final_response"] == "Which position?"
    assert out["warnings"] == [f"Validation: {ATTEMPTS[0]}"]


async def test_a_first_time_route_adds_no_warning(monkeypatch):
    monkeypatch.setattr(smart_router, "get_router",
                        lambda: _StubRouter("data_fetch", []))
    out = await router_node(create_initial_state("what do I hold?"))
    assert out["warnings"] == []


async def test_earlier_warnings_are_kept(monkeypatch):
    monkeypatch.setattr(smart_router, "get_router",
                        lambda: _StubRouter("data_fetch", ATTEMPTS[:1]))
    state = create_initial_state("what do I hold?")
    state["warnings"] = ["earlier"]
    out = await router_node(state)
    assert out["warnings"] == ["earlier", f"Validation: {ATTEMPTS[0]}"]
