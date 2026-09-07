"""
Formatter tests for the synthesizer, with synthetic successful sub_results.

The first pytest that touches anything in synthesizer_node. Recorded reason:
on 7 September (third sitting) two formatter lines were deleted (the macro Recommendation line
and the rebalance Tactical Signal line) and no loop could see the deletion -
the golden set prints no answer, the runner has no macro or rebalance case, and
every live macro and rebalance run in the CLI errored before reaching the
branch. A check that cannot distinguish two states passes in both; this one
feeds the branch directly.

The sub_results here are shaped like what the nodes publish on success, with a
non-zero equity_adjustment and a taa_signal present, so that the assertion
fails if either line comes back.
"""

from agents.nodes import _format_macro_response, _format_rebalance_response


MACRO_SUCCESS = {
    "MacroAgent": {
        "success": True,
        "snapshot": {
            "vix": {"value": 28.4, "regime": "elevated"},
            "yield_curve": {"status": "inverted", "slope": -0.35},
        },
        "regime": {
            "success": True,
            "regime": "risk_off",
            "risk_stance": "defensive",
            "equity_adjustment": -0.15,
        },
    }
}

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


def test_macro_formatter_prints_regime_without_an_equity_recommendation():
    text = "\n".join(_format_macro_response(MACRO_SUCCESS))
    assert "risk_off" in text
    assert "28.4" in text
    assert "Recommendation" not in text
    assert "Adjust equity" not in text


def test_rebalance_formatter_prints_trades_without_a_tactical_signal():
    text = "\n".join(_format_rebalance_response(REBALANCE_SUCCESS))
    assert "SELL 10 AAPL" in text
    assert "Tactical Signal" not in text
    assert "risk_off" not in text


def test_macro_formatter_on_failure_is_header_only():
    lines = _format_macro_response({"MacroAgent": {"success": False}})
    assert lines == ["🌍 **MACRO ENVIRONMENT ANALYSIS**", ""]
