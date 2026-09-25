"""
A tool's fixed caveats are the sentences its formatter prints (decision 77).

Each caveated tool carries a tuple beside its formatter in agents/nodes.py,
which the record's provenance carries and the CLI prints. The formatter's
text is where the sentence has always been, so the tuple is held to the
text and not the other way round: a caveat that the text no longer states,
or states differently, fails here. Compared with the emphasis marks and
the line breaks removed, since the formatters wrap their sentences.

Each formatter is rendered over the fixture its own tests use; the two
tools that need no data are rendered by their formatter over the blocks
the compliance formatter's tests build.
"""

import importlib

import pytest

from agents import nodes
from portfolio_tool.compliance import SHARE, check, refuse
from portfolio_tool.ips import load_ips

from test_allocation_formatter import _answer as allocation_answer
from test_answers_state_their_coverage import _vol as volatility_answer
from test_compliance import INSTRUMENT_TYPES, TOTAL, allocation
from test_compliance_formatter import _answer as compliance_answer, _block as compliance_block
from test_pnl_formatter import DOLLAR_JPM, _answer as pnl_answer


def _flat(text):
    return " ".join(text.replace("*", "").split())


def _compliance_check():
    ips = load_ips("ips.toml")
    alloc = allocation()
    return compliance_answer(compliance_block(ips, check(ips, alloc, INSTRUMENT_TYPES), TOTAL,
                                              alloc["as_of"]))


def _hypothetical_weight():
    ips = load_ips("ips.toml")
    return compliance_answer(compliance_block(ips, refuse(ips, 0.15, SHARE), None, None))


def _rebalance():
    return "\n".join(nodes._format_rebalance_response({"RebalanceAgent": {
        "success": True, "decision": {"recommendation": "no_action", "max_drift": 0.01}}}))


RENDERED = {
    "allocation": lambda: allocation_answer(allocation()),
    "position_pnl": lambda: pnl_answer({"JPM": DOLLAR_JPM}, "USD"),
    "portfolio_volatility": volatility_answer,
    "compliance_check": _compliance_check,
    "hypothetical_weight": _hypothetical_weight,
    "rebalance": _rebalance,
}


@pytest.fixture
def caveats():
    return importlib.import_module("agents.tool_runner").CAVEATS


def test_every_caveated_tool_is_rendered_here(caveats):
    assert set(RENDERED) == {tool for tool, stated in caveats.items() if stated}


def test_each_caveat_is_a_sentence_its_formatter_prints(caveats):
    for tool, render in RENDERED.items():
        text = _flat(render())
        for caveat in caveats[tool]:
            assert caveat in text, (tool, caveat)
