"""
SmartRouter runs extraction before the model and the model's extracted
fields are never read.

The model is a stub returning fixed JSON; the portfolio manager is a stub
returning portfolio 3's tickers. No LLM, no database. What is asserted:
tickers, period, volatility cap and hypothetical weight in the decision are
extraction's, whatever the model emitted, on the first attempt and on a
repair; a clarification from extraction is returned without calling the
model; the policy topic, when the model sets it, carries the user's own
words and not the model's paraphrase.
"""

import json
from types import SimpleNamespace

import pytest

import portfolio_tool.portfolio_manager as pm_module
from agents.smart_router import RouterConfig, SmartRouter


P3 = ["SPY", "AAPL", "MSFT", "JNJ", "JPM", "NEE", "TLT", "GLD", "VNQ"]


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
        "intent": intent,
        "confidence": 0.9,
        "agents_needed": [{"agent": a, "task_description": "do it", "priority": i + 1}
                          for i, a in enumerate(plan)],
        "execution_order": list(plan),
        "parameters": parameters,
        "is_multi_step": False,
        "requires_confirmation": False,
        "reasoning": "a stubbed decision for the test",
        "clarification_question": None,
    })


@pytest.fixture
def router(monkeypatch):
    monkeypatch.setattr(pm_module, "PortfolioManager", _StubPM)
    return SmartRouter(RouterConfig(enable_tracing=False))


COMPLIANCE = ("DataAgent", "PortfolioAnalysisAgent", "ComplianceAgent")
ANALYSIS = ("DataAgent", "PortfolioAnalysisAgent")


async def test_the_models_extracted_fields_are_replaced(router):
    """JNJ is named and the model dropped it; the period is the model's
    invention. The decision carries what the message states."""
    router._llm = _FakeLLM(_json("compliance", COMPLIANCE, tickers=[], period="3Y",
                                 max_volatility=0.3, hypothetical_weight=None))
    decision, validation = await router.route("Is my JNJ position over any limit?", portfolio_id=3)
    assert decision.parameters.tickers == ["JNJ"]
    assert decision.parameters.period is None
    assert decision.parameters.max_volatility is None
    assert validation.errors == []


async def test_a_clarification_from_extraction_skips_the_model(router):
    llm = _FakeLLM(_json("data_fetch", ANALYSIS, measure="position_pnl"))
    router._llm = llm
    decision, validation = await router.route("Hows my APPL doing?", portfolio_id=3)
    assert decision.intent == "clarification_needed"
    assert "AAPL" in decision.clarification_question and "APPL" in decision.clarification_question
    assert decision.execution_order == []
    assert llm.prompts == []
    assert validation.errors == []


async def test_a_repair_attempt_carries_extraction_too(router):
    """The first response fails the schema; the repaired one carries the
    model's own period, which is replaced the same way."""
    router._llm = _FakeLLM(
        _json("not_an_intent", ANALYSIS),
        _json("risk_analysis", ANALYSIS, measure="portfolio_volatility", period="5Y"),
    )
    decision, validation = await router.route(
        "What is my volatility over the past twelve months?", portfolio_id=3)
    assert decision.intent == "risk_analysis"
    assert decision.parameters.period == "1Y"
    assert len(validation.errors) == 1 and "Attempt 1" in validation.errors[0]


async def test_the_lookup_is_extractions_and_carries_the_users_words(router):
    """The model's topic - value and flag - is not read. A question about
    what the policy says carries the whole message as the topic whatever
    the model emitted; a question about the portfolio carries none even
    when the model flagged one (the shrink's failure, 8 September)."""
    router._llm = _FakeLLM(_json("compliance", ("ComplianceAgent",), policy_topic="currency"))
    decision, _ = await router.route("What does my investment policy say about currency risk?",
                                     portfolio_id=3)
    assert decision.parameters.policy_topic == "What does my investment policy say about currency risk?"
    assert decision.execution_order == ["ComplianceAgent"]

    router._llm = _FakeLLM(_json("compliance", ("ComplianceAgent",)))
    decision, _ = await router.route("What does my policy say about cash?", portfolio_id=3)
    assert decision.parameters.policy_topic == "What does my policy say about cash?"

    router._llm = _FakeLLM(_json("compliance", ("ComplianceAgent",), policy_topic="concentration"))
    decision, _ = await router.route("Is AAPL too concentrated?", portfolio_id=3)
    assert decision.parameters.policy_topic is None
    assert decision.execution_order == list(COMPLIANCE)


async def test_a_portfolio_check_carries_no_mode(router):
    router._llm = _FakeLLM(_json("compliance", COMPLIANCE))
    decision, _ = await router.route("Does my allocation violate any rule of my policy?",
                                     portfolio_id=3)
    assert decision.parameters.policy_topic is None
    assert decision.parameters.hypothetical_weight is None


async def test_a_weight_in_the_message_reaches_the_decision(router):
    router._llm = _FakeLLM(_json("compliance", ("ComplianceAgent",)))
    decision, _ = await router.route("I want to put 15% into a single position, is that allowed?",
                                     portfolio_id=3)
    assert decision.parameters.hypothetical_weight == 0.15
    assert decision.parameters.tickers == []


async def test_without_a_portfolio_known_tickers_and_the_period_are_extracted(router):
    router._llm = _FakeLLM(_json("data_fetch", ("DataAgent",), tickers=["SPY"]))
    decision, _ = await router.route("Get me the last 1 year of prices for SPY and TLT")
    assert decision.parameters.tickers == ["SPY", "TLT"]
    assert decision.parameters.period == "1Y"


PENDING = {"kind": "unknown_ticker", "token": "APPL", "candidate": "AAPL",
           "message": "Hows my APPL doing?"}


async def test_a_clarification_about_a_typo_carries_its_record(router):
    router._llm = _FakeLLM()
    decision, _ = await router.route("Hows my APPL doing?", portfolio_id=3)
    assert decision.intent == "clarification_needed"
    assert decision.pending == PENDING
    assert decision.resolved is None


async def test_a_reply_is_resolved_before_extraction_and_the_model(router):
    """"yes" against the record becomes the question with AAPL: extraction
    reads AAPL from it, the model is shown it, and the decision records
    what was resolved from what."""
    llm = _FakeLLM(_json("data_fetch", ANALYSIS, measure="position_pnl"))
    router._llm = llm
    decision, validation = await router.route("yes", portfolio_id=3, pending=PENDING)
    assert decision.parameters.tickers == ["AAPL"]
    assert decision.intent == "data_fetch"
    assert decision.resolved == {"reply": "yes", "message": "Hows my AAPL doing?"}
    assert decision.pending is None
    assert 'User: "Hows my AAPL doing?"' in llm.prompts[0]
    assert validation.errors == []


async def test_a_reply_that_resolves_nothing_is_a_new_message(router):
    llm = _FakeLLM(_json("data_fetch", ANALYSIS, measure="allocation"))
    router._llm = llm
    decision, _ = await router.route("What is my allocation?", portfolio_id=3, pending=PENDING)
    assert decision.resolved is None
    assert 'User: "What is my allocation?"' in llm.prompts[0]

