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
    assert set(TERMINAL) == set(INTENTS)
    for intent, rows in TERMINAL.items():
        for discriminator, (terminal, closed) in rows.items():
            assert discriminator == "" or discriminator in ExtractedParameters.model_fields
            assert terminal is None or terminal in AGENTS


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
