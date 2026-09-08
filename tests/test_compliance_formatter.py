"""
The compliance formatter held to the runner's prose rules, offline.

Three renderings over the Part 7 block from test_compliance.py and the
checker's own output: the portfolio check, the hypothetical, the lookup.
The rules are the ones tests/benchmark/run_cases.py applies to the live
answer, repeated here so a formatter change fails before it costs a run:
every percentage or pp figure is a finding's observed, limit or distance;
no trade verb with a ticker; no weighing-up word; the lookup's sentence;
no clause id at all when the policy has nothing.
"""

import re
from dataclasses import asdict

from agents.nodes import _format_compliance_response
from portfolio_tool.compliance import check, refuse
from portfolio_tool.ips import load_ips

from test_compliance import INSTRUMENT_TYPES, TOTAL, allocation


TICKERS = set(INSTRUMENT_TYPES)
PCT = re.compile(r"(\d+(?:\.(\d+))?)\s*(?:%|pp\b|percentage points)")
TRADE = re.compile(r"\b(buy|sell|purchase|trim|liquidate|short)\b.*\b(" + "|".join(sorted(TICKERS)) + r")\b", re.I)
HEDGE = re.compile(r"\b(depends|however|consider|alternatively|weigh|on balance|that said|trade-?off)\b", re.I)
CLAUSE = re.compile(r"IPS-\d+\.\d+")


def _policy(ips):
    return {c.id: {"type": c.type, "text": c.text} for c in ips}


def _block(ips, findings, total, as_of, topic=None, no_clause=False):
    return {"policy": _policy(ips),
            "statements": [{"clause": c.id, "text": c.text} for c in ips.statements],
            "total_value": total, "as_of": as_of,
            "findings": [asdict(f) for f in findings], "no_clause": no_clause, "topic": topic}


def _answer(block):
    return "\n".join(_format_compliance_response(
        {"ComplianceAgent": {"success": True, "compliance": block}}))


def _unexplained(answer, findings):
    allowed = set()
    for f in findings:
        if f.status == "exempt":
            continue
        allowed |= {f.observed * 100, f.limit * 100, f.distance_pp}
    out = []
    for m in PCT.finditer(answer):
        tol = 0.5 * 10 ** -len(m.group(2) or "") + 1e-9
        if not any(abs(float(m.group(1)) - a) <= tol for a in allowed):
            out.append(m.group(0))
    return out


def test_portfolio_check_answer():
    ips = load_ips()
    alloc = allocation()
    findings = check(ips, alloc, INSTRUMENT_TYPES)
    answer = _answer(_block(ips, findings, TOTAL, alloc["as_of"]))

    for c in ips:
        assert c.id in answer, c.id                       # all rules, visibly all
    assert "2026-09-02" in answer
    for f in findings:
        if f.status == "breach":
            assert f"{f.distance_pp:.2f}" in answer, f
        if f.status == "exempt":
            assert re.search(rf"\b{f.subject}\b", answer)
    assert _unexplained(answer, findings) == []
    assert not TRADE.search(answer)
    assert not HEDGE.search(answer)
    assert "What would have to change" in answer
    assert set(CLAUSE.findall(answer)) <= {c.id for c in ips}


def test_hypothetical_answer():
    ips = load_ips()
    findings = refuse(ips, 0.15)
    answer = _answer(_block(ips, findings, None, None))
    assert "NOT PERMITTED" in answer
    assert "IPS-4.1" in answer and "IPS-4.2" in answer
    assert "3.00 pp" in answer and "5.00 pp" in answer
    assert _unexplained(answer, findings) == []
    assert not HEDGE.search(answer)
    assert not TRADE.search(answer)

    permitted = refuse(ips, 0.10)
    answer = _answer(_block(ips, permitted, None, None))
    assert "PERMITTED" in answer and "NOT PERMITTED" not in answer
    assert _unexplained(answer, permitted) == []


def test_lookup_with_nothing_on_the_topic():
    ips = load_ips()
    block = _block(ips, [], None, None,
                   topic={"asked": "currency risk", "clauses": []}, no_clause=True)
    answer = _answer(block)
    assert "contains nothing on currency risk" in answer
    assert CLAUSE.findall(answer) == []
    assert not any(re.search(rf"\b{t}\b", answer) for t in TICKERS)
    assert PCT.findall(answer) == []


def test_lookup_with_clauses_on_the_topic():
    ips = load_ips()
    on = [c.id for c in ips.clauses_on("my concentration risk")]
    block = _block(ips, [], None, None, topic={"asked": "my concentration risk", "clauses": on})
    answer = _answer(block)
    assert "contains nothing" not in answer
    for cid in on:
        assert cid in answer and ips[cid].text in answer


def test_failed_agent_is_reported_not_formatted():
    lines = _format_compliance_response({"ComplianceAgent": {"success": False, "error": "boom"}})
    assert "failed" in lines[0].lower() and "boom" in "\n".join(lines)
