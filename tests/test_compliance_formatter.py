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


def _answer(block, tickers=None, status=None):
    """The formatter reads the decision for the selection: `tickers` filled
    means the findings on those subjects, empty means every finding;
    `status` set means the findings of that status only."""
    decision = {"parameters": {"tickers": list(tickers or []), "status": status}}
    return "\n".join(_format_compliance_response(
        decision, {"ComplianceAgent": {"success": True, "compliance": block}}))


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
    lines = _format_compliance_response(
        {"parameters": {}}, {"ComplianceAgent": {"success": False, "error": "boom"}})
    assert "failed" in lines[0].lower() and "boom" in "\n".join(lines)


# --- the selection axis: a named position renders its own findings only ---
#
# "Is my JNJ position over any limit?" carries JNJ in `tickers` from
# extraction and got the full report (KNOWN_GAPS, "Four wrong-faced
# answers"). Selection is rendering: the block is the full check, the
# formatter shows the findings whose subject is named. IPS-4.3 limits the
# sector, not the position, so it is not a finding on JNJ.


def test_named_position_renders_its_findings_only():
    ips = load_ips()
    alloc = allocation()
    findings = check(ips, alloc, INSTRUMENT_TYPES)
    answer = _answer(_block(ips, findings, TOTAL, alloc["as_of"]), tickers=["JNJ"])

    on_jnj = [f for f in findings if f.subject == "JNJ"]
    assert {f.clause for f in on_jnj} == {"IPS-4.1", "IPS-4.2"}
    # IPS-5.2 is cited because the conditions section is its own; no other clause.
    assert set(CLAUSE.findall(answer)) == {"IPS-4.1", "IPS-4.2", "IPS-5.2"}
    assert re.search(r"\bJNJ\b", answer)
    for t in TICKERS - {"JNJ"}:
        assert not re.search(rf"\b{t}\b", answer), t
    for f in on_jnj:
        if f.status == "breach":
            assert f"{f.distance_pp:.2f}" in answer, f
    assert _unexplained(answer, on_jnj) == []          # figures from JNJ's findings only
    assert "2026-09-02" in answer                       # priced, so dated (Part 3b)
    assert "What would have to change" in answer
    assert "Policy statements" not in answer            # not asked about
    assert not TRADE.search(answer)
    assert not HEDGE.search(answer)


def test_empty_tickers_renders_every_finding():
    ips = load_ips()
    alloc = allocation()
    findings = check(ips, alloc, INSTRUMENT_TYPES)
    block = _block(ips, findings, TOTAL, alloc["as_of"])
    answer = _answer(block, tickers=[])
    assert answer == _answer(block)                     # absent and empty are the same
    for c in ips:
        assert c.id in answer, c.id
    assert "Policy statements" in answer


def test_named_ticker_with_no_finding_says_so():
    """A known symbol that is not held: the check has no finding on it and
    the answer says exactly that - no clause, no figure, no other holding."""
    ips = load_ips()
    alloc = allocation()
    findings = check(ips, alloc, INSTRUMENT_TYPES)
    answer = _answer(_block(ips, findings, TOTAL, alloc["as_of"]), tickers=["NVDA"])
    assert re.search(r"\bNVDA\b", answer)
    assert "no finding" in answer.lower()
    assert CLAUSE.findall(answer) == []
    assert PCT.findall(answer) == []
    assert not any(re.search(rf"\b{t}\b", answer) for t in TICKERS)


# --- the selection axis, second value: the findings in breach only ---
#
# "Which of my positions are over the limit?" is the breach list, which the
# full report carries inside 63 lines (KNOWN_GAPS, the same entry). `status`
# is the finding's own field and its one allowed value; the model sets it.
#
# The model sets it on 2.2 and 2.3 as well (read from its own output,
# 9 September), so the rendering's failure direction is part of its design:
# the body is the breach rows and their conditions, and the check's coverage
# stays visible in one line each - the clauses within their limits by id
# with their subjects, the exempt funds by name, the statements by id - so
# "all rules" is visibly all of them whatever the model set, and 2.2 cannot
# be hidden by a field.

WITHIN_ROW = "→ within."
EXEMPT_ROW = "exempt — a fund"


def test_breaches_only_renders_the_breach_findings():
    ips = load_ips()
    alloc = allocation()
    findings = check(ips, alloc, INSTRUMENT_TYPES)
    answer = _answer(_block(ips, findings, TOTAL, alloc["as_of"]), status="breach")

    breaches = [f for f in findings if f.status == "breach"]
    assert breaches, "Part 7 has eight breaches at the 09-02 closes"
    assert "breach" in answer.splitlines()[0].lower()          # the header says so
    for f in breaches:
        assert f"{f.distance_pp:.2f}" in answer, f
    assert WITHIN_ROW not in answer and EXEMPT_ROW not in answer   # body: breaches only
    for c in ips:
        assert c.id in answer, c.id                            # coverage: all rules, visibly
    for f in findings:
        if f.status == "exempt":
            assert re.search(rf"\b{f.subject}\b", answer), f  # funds named (2.1)
    for st in ips.statements:
        assert st.text not in answer                           # by id, not quoted
    # A band clause emits one finding per bound. "Within" means every bound
    # within: Equity is under IPS-3.1's minimum and over its maximum, and is
    # not within; Fixed Income is within both bounds and is named once.
    within_line = [l for l in answer.splitlines() if l.startswith("**Within their limits:**")][0]
    within = {}
    for part in within_line.split(":**", 1)[1].split(";"):
        cid, _, subs = part.strip().partition(" ")
        within[cid] = [x.strip() for x in subs.split(",")]
    for cid, subs in within.items():
        assert len(subs) == len(set(subs)), (cid, subs)
    for f in breaches:
        assert f.subject not in within.get(f.clause, []), (f.clause, f.subject)
    assert "Fixed Income" in within["IPS-3.2"]
    # Explained against the block's findings, as the runner does: IPS-3.1's
    # clause text quotes its 40% minimum, whose finding is within and not a row.
    assert _unexplained(answer, findings) == []
    assert "2026-09-02" in answer
    assert "What would have to change" in answer
    assert "Not shown" in answer
    assert not TRADE.search(answer)
    assert not HEDGE.search(answer)


def test_breaches_on_a_named_position():
    """Both selections at once: the breach findings on the named subject.
    JNJ, not AAPL: AAPL breaches both of its clauses at the 09-02 closes,
    so its rendering is the same whether status is read or ignored. JNJ is
    within IPS-4.1 and over IPS-4.2 (Part 7), so only the second may show."""
    ips = load_ips()
    alloc = allocation()
    findings = check(ips, alloc, INSTRUMENT_TYPES)
    answer = _answer(_block(ips, findings, TOTAL, alloc["as_of"]),
                     tickers=["JNJ"], status="breach")
    on_jnj = [f for f in findings if f.subject == "JNJ" and f.status == "breach"]
    assert {f.clause for f in on_jnj} == {"IPS-4.2"}
    # IPS-4.1 is named in the coverage line as within, not as a row.
    assert set(CLAUSE.findall(answer)) == {"IPS-4.1", "IPS-4.2", "IPS-5.2"}
    assert WITHIN_ROW not in answer
    for t in TICKERS - {"JNJ"}:
        assert not re.search(rf"\b{t}\b", answer), t
    assert _unexplained(answer, on_jnj) == []


def test_no_breach_says_so_and_still_names_every_rule():
    """The day nothing breaches, 2.2's wording still gets the list: one line
    saying so, then the coverage, no figure."""
    ips = load_ips()
    alloc = allocation()
    findings = [f for f in check(ips, alloc, INSTRUMENT_TYPES) if f.status != "breach"]
    answer = _answer(_block(ips, findings, TOTAL, alloc["as_of"]), status="breach")
    assert "no finding is in breach" in answer.lower()
    for c in ips:
        assert c.id in answer, c.id
    assert WITHIN_ROW not in answer and EXEMPT_ROW not in answer
    assert PCT.findall(answer) == []
    assert "2026-09-02" in answer                                # still priced, so dated
