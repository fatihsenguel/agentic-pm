"""
compliance_agent_node over a synthetic state: what it publishes, that it
refuses to run without PortfolioAnalysisAgent's output, and that the policy
it loads is the portfolio's.

No LLM. The allocation is the Part 7 fixture from test_compliance.py; the
holdings summary carries the instrument types the way
build_holdings_summary publishes them. One database read: the policy file
is named on the portfolio row (DIRECTION.md Order 2, item 4), and the node
resolves it from the portfolio the state names, in every mode, since the
hypothetical and lookup modes plan no DataAgent and nothing else has read
the row. The states here name portfolio 3 on the suite's copy of the
database, whose row names the committed `ips.toml`.
"""

import pytest

from agents.nodes import compliance_agent_node
from agents.state import create_initial_state
from portfolio_tool.portfolio_manager import PortfolioManager

from test_compliance import INSTRUMENT_TYPES, TOTAL, allocation


BENCHMARK_PORTFOLIO = 3


def holdings():
    return [{"ticker": t, "quantity": 1.0, "average_price": 1.0, "cost_basis": 1.0, "asset_class": "Equity",
             "sector": None, "instrument_type": kind, "purchase_date": None}
            for t, kind in INSTRUMENT_TYPES.items()]


def state_with(_params=None, portfolio_id=BENCHMARK_PORTFOLIO, **shared):
    state = create_initial_state("Does my allocation violate any rule of my policy?",
                                 portfolio_id=portfolio_id)
    state["shared_data"] = shared
    state["agents_to_run"] = ["ComplianceAgent"]
    state["router_decision"] = {"intent": "compliance", "parameters": _params or {}}
    return state


BLOCK_KEYS = {"policy", "statements", "total_value", "as_of", "findings", "no_clause", "topic",
              "base_currency"}


async def test_publishes_the_compliance_block():
    out = await compliance_agent_node(
        state_with(allocation=allocation(), holdings=holdings())
    )
    assert out.get("errors") is None
    block = out["shared_data"]["compliance"]
    assert set(block) == BLOCK_KEYS
    assert len(block["policy"]) == 17
    assert {c for c, e in block["policy"].items() if e["type"] == "statement"} == \
        {s["clause"] for s in block["statements"]}
    assert block["total_value"] == TOTAL
    assert block["as_of"] == allocation()["as_of"]
    # The currency of the total and of every distance in currency: the
    # allocation's, copied, never decided here (D15, D18).
    assert block["base_currency"] == "USD"
    assert block["no_clause"] is False
    assert block["topic"] is None
    statuses = [f["status"] for f in block["findings"]]
    assert statuses.count("breach") == 8 and statuses.count("exempt") == 4
    # The same block on the result, as every node publishes its result.
    assert out["sub_results"]["ComplianceAgent"]["compliance"] is block
    assert out["sub_results"]["ComplianceAgent"]["success"] is True
    assert out["agents_to_run"] == []


@pytest.mark.parametrize("missing", ["allocation", "holdings"])
async def test_refuses_without_the_analysis_output(missing):
    shared = {"allocation": allocation(), "holdings": holdings()}
    del shared[missing]
    out = await compliance_agent_node(state_with(**shared))
    assert "compliance" not in (out.get("shared_data") or {})
    assert out["sub_results"]["ComplianceAgent"]["success"] is False
    [error] = out["errors"]
    assert f"No {missing} in shared_data" in error
    assert "PortfolioAnalysisAgent" in error


async def test_an_allocation_without_a_base_currency_is_an_error():
    """A total with no currency is not a figure; the node copies the
    allocation's currency and refuses when there is none to copy."""
    alloc = allocation()
    del alloc["base_currency"]
    out = await compliance_agent_node(state_with(allocation=alloc, holdings=holdings()))
    assert "compliance" not in (out.get("shared_data") or {})
    [error] = out["errors"]
    assert "base_currency" in error


async def test_an_unknown_instrument_type_is_an_error_not_a_verdict():
    rows = holdings()
    rows[1]["instrument_type"] = None
    out = await compliance_agent_node(
        state_with(allocation=allocation(), holdings=rows)
    )
    assert "compliance" not in (out.get("shared_data") or {})
    [error] = out["errors"]
    assert "Instrument type" in error


# --- the two modes that measure no portfolio ---------------------------------

async def test_hypothetical_weight_refuses_without_a_portfolio():
    out = await compliance_agent_node(state_with({"hypothetical_weight": 0.15}))
    assert out.get("errors") is None
    block = out["shared_data"]["compliance"]
    assert set(block) == BLOCK_KEYS
    assert block["total_value"] is None and block["as_of"] is None
    assert block["base_currency"] is None   # no portfolio, so no currency to report in
    assert block["no_clause"] is False and block["topic"] is None
    assert {f["clause"]: f["status"] for f in block["findings"]} == {
        "IPS-4.1": "refused", "IPS-4.2": "refused"}
    assert all(f["distance_value"] is None for f in block["findings"])


async def test_topic_the_policy_is_silent_on_sets_no_clause():
    out = await compliance_agent_node(state_with({"policy_topic": "currency risk"}))
    assert out.get("errors") is None
    block = out["shared_data"]["compliance"]
    assert block["findings"] == []
    assert block["no_clause"] is True
    assert block["topic"] == {"asked": "currency risk", "clauses": []}
    assert block["total_value"] is None and block["as_of"] is None
    assert block["base_currency"] is None
    assert len(block["policy"]) == 17   # nothing, said over a visibly full policy


async def test_topic_the_policy_has_names_its_clauses():
    out = await compliance_agent_node(state_with({"policy_topic": " Concentration "}))
    block = out["shared_data"]["compliance"]
    assert block["no_clause"] is False
    assert block["topic"] == {"asked": "concentration", "clauses": ["IPS-4.1", "IPS-4.2", "IPS-4.3"]}
    assert block["findings"] == []


async def test_a_lookup_or_hypothetical_needs_no_analysis_output():
    out = await compliance_agent_node(state_with({"policy_topic": "cash"}))
    assert out.get("errors") is None
    out = await compliance_agent_node(state_with({"hypothetical_weight": 0.05}))
    assert out.get("errors") is None
    assert {f["status"] for f in out["shared_data"]["compliance"]["findings"]} == {"ok"}


async def test_both_modes_is_an_error():
    out = await compliance_agent_node(
        state_with({"hypothetical_weight": 0.15, "policy_topic": "cash"}))
    [error] = out["errors"]
    assert "Both" in error


# --- the policy is the portfolio's -------------------------------------------

ONE_CLAUSE = """
[[clause]]
id = "IPS-9.1"
type = "max_instrument_weight"
topics = ["concentration"]
max = 0.20
text = "No single instrument exceeds 20% of total portfolio value."
"""


@pytest.fixture
def portfolio_naming(tmp_path):
    """A portfolio whose row names a policy file outside the repository."""
    pm = PortfolioManager()
    created = []

    def make(path):
        portfolio_id = pm.create_portfolio("Policy Node Test", currency="USD", ips_path=path)
        created.append(portfolio_id)
        return portfolio_id

    yield make
    for portfolio_id in created:
        pm.delete_portfolio(portfolio_id)


@pytest.mark.parametrize("params", [{"policy_topic": "concentration"}, {"hypothetical_weight": 0.15}])
async def test_the_policy_loaded_is_the_portfolios(tmp_path, portfolio_naming, params):
    """A personal file, one clause, named on the row: every mode loads it and
    not the committed policy."""
    personal = tmp_path / "ips.toml"
    personal.write_text(ONE_CLAUSE, encoding="utf-8")
    out = await compliance_agent_node(state_with(params, portfolio_id=portfolio_naming(str(personal))))
    assert out.get("errors") is None, out.get("errors")
    block = out["shared_data"]["compliance"]
    assert list(block["policy"]) == ["IPS-9.1"]


async def test_no_portfolio_is_no_policy():
    """A policy question with no portfolio set has no policy to answer from:
    a refusal, not the committed file with a plausible face."""
    out = await compliance_agent_node(state_with({"policy_topic": "cash"}, portfolio_id=None))
    assert "compliance" not in (out.get("shared_data") or {})
    [error] = out["errors"]
    assert "no portfolio" in error.lower() and "policy" in error.lower()


async def test_a_portfolio_naming_an_absent_file_is_refused_by_name(tmp_path, portfolio_naming):
    absent = str(tmp_path / "absent.toml")
    out = await compliance_agent_node(state_with({"policy_topic": "cash"}, portfolio_id=portfolio_naming(absent)))
    assert "compliance" not in (out.get("shared_data") or {})
    [error] = out["errors"]
    assert absent in error
