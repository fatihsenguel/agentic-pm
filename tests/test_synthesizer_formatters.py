"""
Formatter tests for the synthesizer, with synthetic successful sub_results.

The first pytest that touches anything in synthesizer_node. Recorded reason:
on 7 September (third sitting) two formatter lines were deleted (the macro
Recommendation line and the rebalance Tactical Signal line) and no loop could
see the deletion - the golden set prints no answer, the runner has no macro or
rebalance case, and every live macro and rebalance run in the CLI errored
before reaching the branch. A check that cannot distinguish two states passes
in both; this one feeds the branch directly.

Decision 51 deleted the macro intent and its formatter on 21 September, and
the two macro assertions went with them. The rebalance half is what is left,
and it keeps its original job: the sub_results below are shaped like what the
node publishes on success, with a taa_signal present, so the assertion fails
if the tactical line comes back. Nothing writes that key any more either -
the block that copied the regime into it went with the macro node - which is
why the assertion is now about a formatter that must ignore a field rather
than about a field that exists.
"""

from agents.nodes import _format_rebalance_response


REBALANCE_SUCCESS = {
    "RebalanceAgent": {
        "success": True,
        "decision": {"recommendation": "rebalance", "max_drift": 0.07},
        "trades": [
            {"action": "SELL", "shares": 10, "ticker": "AAPL", "value": 3200.0},
        ],
        "total_cost": 3.2,
        "taa_signal": {"regime": "risk_off", "equity_adjustment": -0.15},
    }
}


def test_rebalance_formatter_prints_drift_without_trades_or_a_tactical_signal():
    """This asserted "SELL 10 AAPL" until the trades went (invariant 2, and
    tests/test_no_weight_outside_compliance.py). It keeps its original job -
    the tactical signal stays gone - over an answer that now states the drift
    and no position."""
    text = "\n".join(_format_rebalance_response(REBALANCE_SUCCESS))
    assert "7.0%" in text
    assert "SELL 10 AAPL" not in text
    assert "AAPL" not in text
    assert "Tactical Signal" not in text
    assert "risk_off" not in text
    # benchmark.md Part 1 says investment recommendations are not built, 2.3
    # passes only on giving none, and the refusal this system prints ends "No
    # recommendation is given here." The drift verdict is a threshold word
    # from a tool; the label said Recommendation.
    assert "Recommendation" not in text
    assert "Drift verdict" in text


