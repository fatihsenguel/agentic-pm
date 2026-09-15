"""
macro_agent_node over the real snapshot tool: the node reads the key the
tool writes.

The node read `yield_curve["slope_raw"]`, a key nothing has ever written:
`MacroAgent.get_macro_snapshot_tool` writes `slope`. So every live macro
run raised "Yield curve data missing from snapshot", and the golden set
pinned `errors: 1` on the macro query from its first baseline. The test
formatter in test_synthesizer_formatters.py feeds a hand-built snapshot, so
it could not see a node reading a different key from the one the tool
produces.

Here the snapshot comes from the real tool over a stand-in data manager, so
the shape is the tool's and not this file's. No database, no provider, no
model: the fetch is stubbed to report nothing fetched.
"""

from agents import macro_agent
from agents.nodes import _format_macro_response, macro_agent_node
from agents.state import create_initial_state


VIX = 17.10
TEN_YEAR = 4.10
THREE_MONTH = 3.074
SLOPE = 1.026  # round(TEN_YEAR - THREE_MONTH, 4)


class StubDataManager:
    def get_latest_macro_values(self):
        return {
            "success": True,
            "timestamp": "2026-09-15T01:00:00",
            "indicators": {
                "VIX": {"value": VIX, "date": "2026-09-14"},
                "TNX_10Y": {"value": TEN_YEAR, "date": "2026-09-14"},
                "IRX_3M": {"value": THREE_MONTH, "date": "2026-09-14"},
            },
        }


def stub_agent(verbose=False):
    agent = macro_agent.MacroAgent()
    agent._data_manager = StubDataManager()
    agent.fetch_macro_data_tool = lambda **kwargs: {"success": True, "stubbed": True}
    return agent


def state():
    s = create_initial_state("What is the current market regime?")
    s["agents_to_run"] = ["MacroAgent"]
    s["router_decision"] = {"intent": "macro_analysis", "parameters": {}}
    return s


async def test_the_node_assesses_the_regime_from_the_tools_slope(monkeypatch):
    monkeypatch.setattr(macro_agent, "create_macro_agent", stub_agent)

    out = await macro_agent_node(state())

    assert not out.get("errors"), out.get("errors")
    result = out["sub_results"]["MacroAgent"]
    assert result["success"] is True
    assert result["regime"]["yield_curve_slope"] == SLOPE
    assert out["shared_data"]["macro_regime"]["yield_curve_slope"] == SLOPE


async def test_the_answer_carries_the_slope_the_node_read(monkeypatch):
    monkeypatch.setattr(macro_agent, "create_macro_agent", stub_agent)

    out = await macro_agent_node(state())
    answer = "\n".join(_format_macro_response(out["sub_results"]))

    assert f"slope: {SLOPE}" in answer
