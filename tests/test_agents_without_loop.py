"""
The agents are their tool functions and nothing else (decision 54).

BaseAgent carried a tool-calling loop for a supervisor to delegate into:
`process`, `get_tools`, `get_system_prompt`, `capabilities`, roles and a
registry. Nothing called the loop after the graph's nodes began calling
the tools directly, and the conversation layer replaced the router that
might have. The loop went behind the tag `agent-loop-parked`; the two
agents keep the tools the nodes call, and DataAgent keeps the one thing
its tools used from the base class, a log that prints only when asked.
"""

import importlib.util
import inspect

from agents.data_agent import DataAgent, create_data_agent
from agents.rebalance_agent import RebalanceAgent, create_rebalance_agent

LOOP = ("process", "get_tools", "get_system_prompt", "capabilities", "create_result",
        "validate_task", "can_handle", "tool_map", "get_tool", "role", "config")


def test_the_base_agent_module_is_gone():
    assert importlib.util.find_spec("agents.base_agent") is None


def test_the_agents_subclass_nothing():
    assert DataAgent.__mro__ == (DataAgent, object)
    assert RebalanceAgent.__mro__ == (RebalanceAgent, object)


def test_the_agents_carry_no_loop():
    for cls in (DataAgent, RebalanceAgent):
        carried = [name for name in LOOP if hasattr(cls, name)]
        assert carried == [], f"{cls.__name__} carries {carried}"


def test_the_agents_keep_the_tools_the_nodes_call():
    for name in ("fetch_prices_tool", "fetch_fx_rates_tool", "calculate_returns_tool",
                 "calculate_covariance_tool"):
        assert callable(getattr(DataAgent, name)), name
    assert callable(RebalanceAgent.analyze_rebalance_tool)


def test_the_rebalance_factory_takes_no_verbose():
    """RebalanceAgent logged only inside `process`, so `verbose` has no
    reader left."""
    assert list(inspect.signature(create_rebalance_agent).parameters) == []


def test_the_data_agents_log_prints_only_when_verbose(capsys):
    create_data_agent(verbose=False).log("quiet")
    assert capsys.readouterr().out == ""
    create_data_agent(verbose=True).log("loud")
    out = capsys.readouterr().out
    assert "[DataAgent] loud" in out
    assert out.isascii(), out
