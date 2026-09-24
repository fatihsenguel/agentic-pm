"""
Plans are derived from the tool through the terminal-agent table, closed
upward by REQUIRES (docs/DIRECTION.md: each tool's internal graph). The
table is keyed by tool, one row per tool, and the model never sees a plan
(decision 45).

Every row of the table is pinned here to the plan it derives, so a change
to REQUIRES or to the table moves a test before it moves an answer.
"""

import pytest

from agents import schemas
from agents.tool_inputs import TOOLS


D, A, C = "DataAgent", "PortfolioAnalysisAgent", "ComplianceAgent"
R = "RebalanceAgent"
S = "ScreeningAgent"
RA = "ResearchAgent"
L = "LedgerAgent"

# tool, derived plan
ROWS = [
    ("allocation", [D, A]),
    ("position_pnl", [D, A]),
    ("portfolio_volatility", [D, A]),
    ("compliance_check", [D, A, C]),
    ("hypothetical_weight", [C]),
    ("policy_lookup", [C]),
    # The philosophy check needs no other agent; the ticker is the input's
    # (decision 29).
    ("philosophy_screen", [S]),
    # A thesis reads the filing after the screen (decision 66).
    ("thesis", [S, RA]),
    # A position needs the portfolio computed and the company screened and
    # read, and the gate checks it against the allocation published.
    ("position", [D, A, S, RA]),
    ("rebalance", [D, R]),
    ("ledger", [L]),
]


@pytest.mark.parametrize("tool, plan", ROWS, ids=[r[0] for r in ROWS])
def test_the_table_derives_each_plan(tool, plan):
    assert schemas.derive_plan(tool) == plan


def test_the_table_has_one_row_per_tool_and_no_other():
    assert set(schemas.TERMINAL) == set(TOOLS)
    assert {tool for tool, _ in ROWS} == set(TOOLS)


def test_every_terminal_is_an_agent():
    for tool, (terminal, _closed) in schemas.TERMINAL.items():
        for agent in (terminal if isinstance(terminal, tuple) else (terminal,)):
            assert agent in schemas.AGENTS, (tool, agent)


def test_a_tuple_terminal_closes_over_each_name_once_in_order():
    """`position` needs two things finished and neither requires the other:
    the portfolio computed, and the company screened and read. Each
    requirement appears once and before what needs it."""
    plan = schemas.derive_plan("position")
    assert len(plan) == len(set(plan))
    assert plan.index(D) < plan.index(A)
    assert plan.index(S) < plan.index(RA)


def test_a_shared_requirement_appears_once_in_a_tuple_plan(monkeypatch):
    """No row today has two terminals that need the same agent, so the
    closure's one-name-once rule is held by nothing on the real table. A
    row that does is built here: both terminals require DataAgent, and it
    runs once and before both."""
    monkeypatch.setitem(schemas.TERMINAL, "position", ((A, R), True))
    assert schemas.derive_plan("position") == [D, A, R]


@pytest.mark.parametrize("table,message", [
    ({"thesis": ("NoSuchAgent", True)}, "not in the roster"),
    ({"thesis": ((S, "NoSuchAgent"), True)}, "not in the roster"),
    ({"nosuchtool": (S, True)}, "not a tool"),
])
def test_a_table_that_cannot_route_is_refused(table, message):
    """The import-time check, shown working. On the real table every one of
    these passes trivially and none of them could be seen to hold."""
    with pytest.raises(RuntimeError, match=message):
        schemas.validate_terminal(table)


def test_the_committed_table_passes_its_own_check():
    schemas.validate_terminal(schemas.TERMINAL)


def test_a_closed_plan_respects_requires_and_an_unclosed_one_names_why():
    """Closure puts every requirement before the agent that needs it. The
    two unclosed rows are ComplianceAgent's portfolio-free tools, and the
    requirement they skip is exactly its REQUIRES entry."""
    for tool, plan in ROWS:
        terminal, closed = schemas.TERMINAL[tool]
        if not closed:
            assert plan == [terminal]
            assert schemas.REQUIRES[terminal] == (A,)
            continue
        for i, agent in enumerate(plan):
            for need in schemas.REQUIRES.get(agent, ()):
                assert need in plan[:i], (tool, agent, need)


def test_an_unknown_tool_has_no_plan():
    with pytest.raises(KeyError):
        schemas.derive_plan("not_a_tool")
