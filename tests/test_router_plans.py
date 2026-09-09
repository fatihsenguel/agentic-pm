"""
SmartRouter replaces the model's plan with the derived one on every attempt.

Stubbed model, stubbed portfolio manager, no LLM, no database. The model's
execution_order and agents_needed are never read for a derived intent: the
flip plan ([PortfolioAnalysisAgent] alone) and a compliance check planned
as DataAgent alone both come out as the derived plan with no repair.
"""

import json
from types import SimpleNamespace

import pytest

import portfolio_tool.portfolio_manager as pm_module
from agents.smart_router import RouterConfig, SmartRouter


P3 = ["SPY", "AAPL", "MSFT", "JNJ", "JPM", "NEE", "TLT", "GLD", "VNQ"]
COMPLIANCE = ["DataAgent", "PortfolioAnalysisAgent", "ComplianceAgent"]
ANALYSIS = ["DataAgent", "PortfolioAnalysisAgent"]


class _StubPM:
    def get_portfolio_tickers(self, portfolio_id):
        return list(P3) if portfolio_id == 3 else []


class _FakeLLM:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.prompts = []

    async def ainvoke(self, prompt):
        self.prompts.append(prompt)
        return SimpleNamespace(content=self.responses.pop(0))


def _json(intent, plan, **parameters):
    return json.dumps({
        "intent": intent, "confidence": 0.9,
        "agents_needed": [{"agent": a, "task_description": "the model's idea", "priority": 9}
                          for a in plan],
        "execution_order": list(plan),
        "parameters": parameters,
        "reasoning": "a stubbed decision for the test", "clarification_question": None,
    })


@pytest.fixture
def router(monkeypatch):
    monkeypatch.setattr(pm_module, "PortfolioManager", _StubPM)
    return SmartRouter(RouterConfig(enable_tracing=False))


async def test_the_flip_plan_is_derived_away_without_a_repair(router):
    """The 'too big' flip: risk_analysis with the analysis agent alone. The
    derived plan is DataAgent then the analysis agent; no retry."""
    router._llm = _FakeLLM(_json("risk_analysis", ["PortfolioAnalysisAgent"],
                                 measure="portfolio_volatility"))
    decision, validation = await router.route("Is my AAPL position too big?", portfolio_id=3)
    assert decision.execution_order == ANALYSIS
    assert validation.errors == []
    assert len(router._llm.prompts) == 1


async def test_a_compliance_check_planned_short_is_derived_full(router):
    router._llm = _FakeLLM(_json("compliance", ["DataAgent"]))
    decision, validation = await router.route(
        "Does my current allocation violate any rule of my investment policy?", portfolio_id=3)
    assert decision.execution_order == COMPLIANCE
    assert validation.errors == []


async def test_status_does_not_change_the_plan(router):
    """The breach selection is rendering; the check is the full one."""
    router._llm = _FakeLLM(_json("compliance", ["ComplianceAgent"], status="breach"))
    decision, validation = await router.route(
        "Which of my positions are over the limit?", portfolio_id=3)
    assert decision.execution_order == COMPLIANCE
    assert decision.parameters.status == "breach"
    assert validation.errors == []


async def test_a_hypothetical_weight_derives_the_agent_alone(router):
    router._llm = _FakeLLM(_json("compliance", COMPLIANCE))
    decision, _ = await router.route(
        "I want to put 15% into a single position, is that allowed?", portfolio_id=3)
    assert decision.execution_order == ["ComplianceAgent"]
    assert decision.parameters.hypothetical_weight == 0.15


async def test_the_models_task_list_is_not_read(router):
    """The stub still sends agents_needed, as an older model output would;
    the decision carries no such field and the plan is the table's."""
    router._llm = _FakeLLM(_json("data_fetch", ["DataAgent"], measure="allocation", group_by="sector"))
    decision, _ = await router.route("What share of my portfolio is technology?", portfolio_id=3)
    assert decision.execution_order == ANALYSIS
    assert not hasattr(decision, "agents_needed")


async def test_a_weight_under_the_wrong_intent_is_repaired_by_changing_the_intent(router):
    """Extraction sets the weight; the model said data_fetch. The validator
    rejects the mode under that intent, the repair changes the intent, and
    the derived plan follows the new intent."""
    router._llm = _FakeLLM(
        _json("data_fetch", ["DataAgent"]),
        _json("compliance", ["DataAgent"]),
    )
    decision, validation = await router.route("Could I put 11% into a new stock?", portfolio_id=3)
    assert decision.intent == "compliance"
    assert decision.execution_order == ["ComplianceAgent"]
    assert len(validation.errors) == 1 and "belong to intent compliance" in validation.errors[0]
