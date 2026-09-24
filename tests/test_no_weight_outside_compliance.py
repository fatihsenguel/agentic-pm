"""
No answer outside intent compliance states a position.

docs/DIRECTION.md invariant 2: an answer that implies a position is checked
against the IPS before it is shown, and the model cannot route around it.
Until the fourteenth session that sentence read as a description of the
system and was false. Intent `optimization` derived
[DataAgent, OptimizationAgent] and its formatter printed a weight per ticker
with no clause checked, on the path the golden set pinned, while
`validate_compliance` raises if ComplianceAgent is planned there at all.
`rebalancing` carries the same surface, hidden only because RebalanceAgent
errors on a missing target. Decision 51 deleted the optimisation intent on
21 September; `rebalancing` is the surface that remains and the assertion
below is what is left of this file's question.

It survived four sessions because every loop asks its own question. The
runner's twelve cases are portfolio and policy questions and none names a
weight outside the compliance intent; the golden set prints five routing
fields and no answer text; pytest had one formatter test. This file is the
loop that asks it, and it makes no model call.

What is asserted is the narrow form the code can carry today: an intent that
cannot plan the checker renders no proposed weight and no trade. A share of
something the portfolio already holds is not a proposed position - the
allocation answer's per-position table is the reference figure IPS-4.1 is one
subtraction from, and it stays. So the assertion is against figures that
reach a formatter as a proposal and nothing else: the rebalancer's
`trades`. The values below are
distinctive so that a formatter printing them fails on the figure rather than
on a wording, and the metrics beside them are asserted present so that this
cannot be satisfied by a formatter that prints nothing at all.
"""

import re

from agents.nodes import _format_rebalance_response
from agents.schemas import TERMINAL, derive_plan

REBALANCE_SUCCESS = {
    "RebalanceAgent": {
        "success": True,
        "decision": {"recommendation": "partial_rebalance", "max_drift": 0.0713},
        "trades": [
            {"action": "SELL", "shares": 37, "ticker": "SPY", "value": 12345.0},
            {"action": "BUY", "shares": 12, "ticker": "TLT", "value": 987.0},
        ],
        "total_cost": 4.44,
    }
}

TRADE = re.compile(r"\b(BUY|SELL|buy|sell)\b[^\n]{0,30}\b(SPY|TLT|GLD)\b")


def test_the_checker_is_reachable_from_the_compliance_tools_only():
    """The premise of this file, derived from the table rather than listed.

    Every other tool runs no checker, so an answer from one of them either
    states a position nothing checked or states none; `position` is checked
    by the gate on its edge, which is not a plan step. This passes today -
    it is not the falsifier for the defect, it is the reason the two below
    are the right assertions - and it fails if a later tool gains or loses
    the checker without this file being revisited.
    """
    planned_by = {tool for tool in TERMINAL if "ComplianceAgent" in derive_plan(tool)}
    assert planned_by == {"compliance_check", "hypothetical_weight", "policy_lookup"}


def test_the_rebalance_answer_states_no_trades():
    text = "\n".join(_format_rebalance_response(REBALANCE_SUCCESS))

    assert not TRADE.search(text), TRADE.search(text)
    for absent in ("SPY", "TLT", "37", "12,345", "987", "4.44"):
        assert absent not in text, f"{absent!r} is part of a trade nothing checked"

    # Still an answer: drift is a figure about the portfolio as it stands.
    assert "7.1%" in text
    assert "Not shown" in text
