"""
Plans are derived from intent and the extracted parameters through the
terminal-agent table, closed upward by REQUIRES (docs/DIRECTION.md: this
becomes each tool's internal graph).

Every row of the table is pinned here to the plan it derives, so a change
to REQUIRES or to the table moves a test before it moves a golden line.
"""

import pytest

from agents.schemas import (
    AGENTS, INTENTS, REQUIRES, TERMINAL, ExtractedParameters, derive_plan,
)


D, A, C = "DataAgent", "PortfolioAnalysisAgent", "ComplianceAgent"
O, B, R, M = "OptimizationAgent", "BacktestAgent", "RebalanceAgent", "MacroAgent"
S = "ScreeningAgent"

# intent, parameters, derived plan
ROWS = [
    ("optimization", {}, [D, O]),
    ("backtest", {}, [D, O, B]),
    ("rebalancing", {}, [D, R]),
    ("macro_analysis", {}, [M]),
    ("data_fetch", {}, [D]),
    ("data_fetch", {"measure": "allocation"}, [D, A]),
    ("data_fetch", {"measure": "position_pnl"}, [D, A]),
    ("risk_analysis", {}, [D]),
    ("risk_analysis", {"measure": "portfolio_volatility"}, [D, A]),
    ("compliance", {}, [D, A, C]),
    ("compliance", {"hypothetical_weight": 0.15}, [C]),
    ("compliance", {"policy_topic": "what does my policy say about cash"}, [C]),
    # The philosophy check needs no other agent: no portfolio, no price until
    # Part 11; the ticker is extraction's (decision 29).
    ("research", {"tickers": ["JPM"]}, [S]),
    ("research", {}, [S]),
    # A thesis question reads the filing after the screen (decision 66); the
    # value is extraction's.
    ("research", {"tickers": ["GOOGL"], "asks": "thesis"}, [S, "ResearchAgent"]),
    ("ledger", {}, ["LedgerAgent"]),
    ("clarification_needed", {}, []),
    ("out_of_scope", {}, []),
]


@pytest.mark.parametrize("intent, params, plan", ROWS,
                         ids=[f"{r[0]}:{'/'.join(r[1]) or '-'}" for r in ROWS])
def test_the_table_derives_each_plan(intent, params, plan):
    assert derive_plan(intent, ExtractedParameters(**params)) == plan


def test_every_intent_derives_a_plan():
    """No intent keeps the model's plan: combined, the last one that did,
    is retired. derive_plan never returns None."""
    for intent in INTENTS:
        assert isinstance(derive_plan(intent, ExtractedParameters()), list)


def test_every_intent_has_a_row_and_every_terminal_is_an_agent():
    """A key names a parameter, or a parameter and the value it matches; a
    terminal is one agent or a tuple of them."""
    assert set(TERMINAL) == set(INTENTS)
    for intent, rows in TERMINAL.items():
        for discriminator, (terminal, closed) in rows.items():
            name, sep, value = discriminator.partition("=")
            assert name == "" or name in ExtractedParameters.model_fields
            assert not sep or value, f"{intent}: {discriminator!r} matches an empty value"
            names = terminal if isinstance(terminal, tuple) else (terminal,)
            for agent in names:
                assert agent is None or agent in AGENTS


def test_a_value_keyed_row_decides_before_the_parameter_alone():
    """The two values of `asks` take different plans: a thesis question
    implies no position and reads no allocation, a position question is
    checked by the gate against the allocation PortfolioAnalysisAgent
    published. The narrower key is written above the wider one, so the
    order of the rows is the rule and not an accident of the dict."""
    rows = list(TERMINAL["research"])
    assert rows.index("asks=position") < rows.index("asks")
    assert derive_plan("research", {"asks": "thesis"}) == ["ScreeningAgent", "ResearchAgent"]
    assert derive_plan("research", {"asks": "position"}) == [
        "DataAgent", "PortfolioAnalysisAgent", "ScreeningAgent", "ResearchAgent"]
    assert derive_plan("research", {}) == ["ScreeningAgent"]


def test_a_tuple_terminal_closes_over_each_name_once_in_order():
    """`asks=position` needs two things finished and neither requires the
    other: the portfolio computed, and the company screened and read. Each
    requirement appears once and before what needs it."""
    plan = derive_plan("research", {"asks": "position"})
    assert len(plan) == len(set(plan))
    assert plan.index("DataAgent") < plan.index("PortfolioAnalysisAgent")
    assert plan.index("ScreeningAgent") < plan.index("ResearchAgent")


def test_a_shared_requirement_appears_once_in_a_tuple_plan(monkeypatch):
    """No row today has two terminals that need the same agent, so the
    closure's one-name-once rule is held by nothing on the real table. A
    row that does is built here: both terminals require DataAgent, and it
    runs once and before both."""
    from agents import schemas
    row = dict(schemas.TERMINAL["research"])
    row["asks=position"] = (("PortfolioAnalysisAgent", "OptimizationAgent"), True)
    monkeypatch.setitem(schemas.TERMINAL, "research", row)
    assert derive_plan("research", {"asks": "position"}) == [
        "DataAgent", "PortfolioAnalysisAgent", "OptimizationAgent"]


@pytest.mark.parametrize("table,message", [
    ({"research": {"nosuchparam": ("ResearchAgent", True)}}, "not a parameter"),
    ({"research": {"asks=": ("ResearchAgent", True)}}, "matches an empty value"),
    ({"research": {"": ("NoSuchAgent", True)}}, "not in the roster"),
    ({"research": {"": (("ScreeningAgent", "NoSuchAgent"), True)}}, "not in the roster"),
])
def test_a_table_that_cannot_route_is_refused(table, message):
    """The import-time check, shown working. On the real table every one of
    these passes trivially and none of them could be seen to hold."""
    from agents.schemas import validate_terminal
    with pytest.raises(RuntimeError, match=message):
        validate_terminal(table)


def test_the_committed_table_passes_its_own_check():
    from agents.schemas import validate_terminal
    validate_terminal(TERMINAL)


def test_a_value_the_table_does_not_name_falls_to_the_wider_row():
    """A row keyed on a value matches that value alone. Nothing sets `asks`
    to anything but the two, the schema refusing it, so this says what the
    table does rather than what can happen today."""
    assert derive_plan("research", {"asks": "something else"}) == [
        "ScreeningAgent", "ResearchAgent"]


def test_a_closed_plan_respects_requires_and_an_unclosed_one_names_why():
    """Closure puts every requirement before the agent that needs it. The
    two unclosed rows are ComplianceAgent's portfolio-free modes, and the
    requirement they skip is exactly its REQUIRES entry."""
    for intent, params, plan in ROWS:
        row = TERMINAL[intent]
        discriminator = next((k for k in row if k and params.get(k) is not None), "")
        terminal, closed = row[discriminator]
        if not closed:
            assert plan == [terminal]
            assert REQUIRES[terminal] == (A,)
            continue
        for i, agent in enumerate(plan):
            for need in REQUIRES.get(agent, ()):
                assert need in plan[:i], (intent, agent, need)


def test_an_unknown_intent_has_no_plan():
    with pytest.raises(KeyError):
        derive_plan("not_an_intent", ExtractedParameters())
