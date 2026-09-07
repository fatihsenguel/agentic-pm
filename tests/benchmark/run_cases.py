"""
Benchmark case runner. Prints n/12 against docs/benchmark.md Part 3.

Not part of pytest. Twelve live queries cost API calls and about a minute, so
this is a third loop alongside the golden set, not a fourth thing bolted onto
pytest.

    python tests/benchmark/run_cases.py
    python tests/benchmark/run_cases.py --case 1.1

WHAT THIS ASSERTS, AND WHAT IT DELIBERATELY DOES NOT

Exact market-value figures are NOT checked here. `tests/test_allocation.py`
already checks them against expected_values.md Parts 2 and 3 with fixed inputs,
which is the right instrument: market values move with prices, expected_values
is pinned to the 2026-09-02 closes, and no seam exists to pin a run against a
date - `fetch_prices_tool` takes only tickers, period and interval. A runner
asserting Equity at 0.6941 would begin failing on price movement rather than on
regression, which is the worst signal a counter can give.

What each case asserts instead:

  - the case ran end to end with no errors
  - the structure and invariants of what reached `shared_data`
  - the STATIC figures exactly against expected_values.md - cost bases, cash,
    the ticker set - none of which move with prices
  - weakly on the prose: do the figures `shared_data` carries appear in the
    answer at all
  - benchmark.md Part 3b: is an as-of date stated

The as-of check asserts on `shared_data["allocation"]["as_of"]["worst_case"]`:
that it exists, that it is a date, and that that exact date reaches the answer.
It was a date-shaped regex over the prose until roadmap item 5 built the field,
and it was replaced in the same commit so that 1.1 and 1.4 could not flip to
PASS on the proxy.

STATUSES

  PASS     every check held
  FAIL     the system answered, and the answer was wrong or incomplete
  BLOCKED  a capability this case needs does not exist yet

BLOCKED is not a pass. The headline number is passes out of twelve.

Blocked cases probe for the capability rather than declaring themselves blocked,
so they unblock automatically when it arrives. A case that unblocks while its
check is still unwritten reports FAIL saying so - "done" for a roadmap item
means its case asserts, not that its arithmetic is right.
"""

import argparse
import contextlib
import io
import re

from agents.graph import run_agent_graph_sync


BENCHMARK_PORTFOLIO = 3

# expected_values.md Part 1 and Part 2, cost-basis column. Static: cost basis is
# what was paid and does not move with the market.
COST_BY_CLASS = {
    "Equity": 187_500.00,
    "Fixed Income": 45_000.00,
    "Commodity": 25_000.00,
    "Real Estate": 27_000.00,
    "Cash": 15_500.00,
}

# expected_values.md Part 3, cost-basis column.
COST_BY_SECTOR = {
    "Technology": 80_000.00,
    "Healthcare": 22_500.00,
    "Financials": 20_000.00,
    "Utilities": 15_000.00,
}
COST_UNSECTORED = 147_000.00
COST_SECTORED = 137_500.00
COST_INVESTED = 284_500.00

TICKERS = {"SPY", "AAPL", "MSFT", "JNJ", "JPM", "NEE", "TLT", "GLD", "VNQ"}
UNSECTORED_LABEL = "(no sector)"

CENT = 0.005
AS_OF = re.compile(r"\d{4}-\d{2}-\d{2}")


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def _shared(state):
    return state.get("shared_data") or {}


def _allocation(state, view):
    return (_shared(state).get("allocation") or {}).get(view) or {}


def _by_label(block):
    return {line["label"]: line for line in block.get("lines", [])}


def _answer(state):
    return state.get("final_response") or ""


def _intent(state):
    return (state.get("router_decision") or {}).get("intent")


# ---------------------------------------------------------------------------
# Shared checks
# ---------------------------------------------------------------------------

def _ran_clean(state):
    errors = state.get("errors") or []
    return [f"errors during the run: {errors}"] if errors else []


def _states_as_of(state):
    """Assert on the structured as-of value, not on a date shape in the prose.

    Three separate things, because a date-shaped regex over the answer was
    satisfied by any date at all - including the volatility window string - and
    would have reported 1.1 and 1.4 as passing on the proxy rather than on the
    field.

    Allocation-specific, deliberately. It reads
    `shared_data["allocation"]["as_of"]`, and every case calling it (1.1, 1.4)
    produces an allocation. P&L carries its as-of per position under
    `shared_data["position_pnl"]` and has `_states_pnl_as_of` below; a
    volatility answer will want a third. Searching for a date wherever one
    might live is what the regex version did.
    """
    allocation = _shared(state).get("allocation") or {}
    as_of = allocation.get("as_of") or {}
    stated = as_of.get("worst_case")

    if not stated:
        return ["no as_of.worst_case in shared_data['allocation'] "
                "(benchmark.md Part 3b)"]

    return _date_reaches_answer(state, stated, "allocation.as_of.worst_case")


def _states_pnl_as_of(state, tickers):
    """Per-position as-of: `shared_data["position_pnl"][ticker]["as_of"]`.

    One holding, one close, so there is nothing to reduce and every position
    asked about carries its own date. Each must be a date and each must reach
    the answer.
    """
    pnl = _shared(state).get("position_pnl") or {}
    fails = []
    for t in tickers:
        stated = (pnl.get(t) or {}).get("as_of")
        if not stated:
            fails.append(f"no as_of for {t} in shared_data['position_pnl'] "
                         "(benchmark.md Part 3b)")
            continue
        fails += _date_reaches_answer(state, stated, f"position_pnl[{t}].as_of")
    return fails


def _date_reaches_answer(state, stated, where):
    fails = []
    if not AS_OF.fullmatch(str(stated)):
        fails.append(f"{where} is not a YYYY-MM-DD date: {stated!r}")
    if str(stated) not in _answer(state):
        fails.append(f"as-of date {stated} is in {where} but never reaches "
                     f"the answer")
    return fails


def _prose_carries(state, lines, key):
    """Weak Part 3b check: did the figures in shared_data reach the answer."""
    answer = _answer(state)
    missing = sorted(
        label
        for label, line in lines.items()
        if line.get(key) is not None and f"{line[key]:.2%}" not in answer
    )
    if missing:
        return [f"answer does not carry the figure for: {', '.join(missing)}"]
    return []


def _cost_bases_match(lines, expected, where):
    fails = []
    for label, cost in expected.items():
        line = lines.get(label)
        if line is None:
            fails.append(f"{where}: no line for {label}")
            continue
        got = line.get("cost_basis")
        if got is None or abs(got - cost) > CENT:
            fails.append(f"{where}: {label} cost basis {got} != {cost}")
    return fails


# ---------------------------------------------------------------------------
# Case checks
# ---------------------------------------------------------------------------

def check_1_1(state):
    fails = _ran_clean(state)
    block = _allocation(state, "by_asset_class")
    if not block:
        return fails + ["no allocation.by_asset_class in shared_data"]

    lines = _by_label(block)
    if set(lines) != set(COST_BY_CLASS):
        fails.append(f"labels {sorted(lines)} != {sorted(COST_BY_CLASS)}")

    total = sum(
        line["pct_of_denominator"]
        for line in lines.values()
        if line.get("pct_of_denominator") is not None
    )
    if abs(total - 1.0) > 1e-9:
        fails.append(f"percentages sum to {total}, not 1.0")

    fails += _cost_bases_match(lines, COST_BY_CLASS, "by_asset_class")

    cash = lines.get("Cash") or {}
    if cash.get("pct_of_denominator") is None:
        fails.append("cash has no % of total; D2 puts cash inside the denominator")
    if cash.get("pct_of_invested") is not None:
        fails.append("cash carries a % of invested; cash is not invested")

    held = {t for line in lines.values() for t in line.get("tickers", [])}
    if held != TICKERS:
        fails.append(f"tickers {sorted(held)} != the nine seeded positions")

    fails += _prose_carries(state, lines, "pct_of_denominator")
    fails += _states_as_of(state)
    return fails


def check_1_4(state):
    fails = _ran_clean(state)
    block = _allocation(state, "by_sector")
    if not block:
        return fails + ["no allocation.by_sector in shared_data"]

    lines = _by_label(block)
    fails += _cost_bases_match(lines, COST_BY_SECTOR, "by_sector")

    tech = lines.get("Technology")
    if tech is None:
        fails.append("no Technology line")
    elif set(tech.get("tickers", [])) != {"AAPL", "MSFT"}:
        fails.append(f"Technology holds {sorted(tech.get('tickers', []))}, not AAPL and MSFT")

    unsectored = lines.get(UNSECTORED_LABEL)
    if unsectored is None:
        fails.append(f"no {UNSECTORED_LABEL} line; D3 reports unsectored holdings explicitly")
    elif abs(unsectored.get("cost_basis", 0.0) - COST_UNSECTORED) > CENT:
        fails.append(
            f"{UNSECTORED_LABEL} cost basis {unsectored.get('cost_basis')} != {COST_UNSECTORED}"
        )

    sectored = sum(
        line.get("cost_basis", 0.0)
        for label, line in lines.items()
        if label != UNSECTORED_LABEL
    )
    if abs(sectored - COST_SECTORED) > CENT:
        fails.append(f"sectored cost basis {sectored} != {COST_SECTORED}")

    fails += _prose_carries(state, lines, "pct_of_invested")
    fails += _states_as_of(state)
    return fails


def check_1_2(state):
    """JPM since purchase. The static figures are Part 1's cost-basis column
    and the purchase date; the moving ones are checked as invariants and for
    reaching the prose.

    `parameters.tickers` must be exactly ["JPM"]. Rule 2 lets the router fill
    tickers from the portfolio when the user names none, and for P&L an empty
    list means every position - so a padded list would silently turn a
    question about one position into an answer about nine.
    """
    fails = _ran_clean(state)
    params = (state.get("router_decision") or {}).get("parameters") or {}
    if params.get("measure") != "position_pnl":
        fails.append(f"measure is {params.get('measure')!r}, not 'position_pnl'")
    if params.get("tickers") != ["JPM"]:
        fails.append(f"tickers {params.get('tickers')} != ['JPM']; the position "
                     "named in the question, and nothing else")

    pnl = _shared(state).get("position_pnl") or {}
    jpm = pnl.get("JPM")
    if not jpm:
        return fails + ["no position_pnl.JPM in shared_data"]

    if abs(jpm.get("cost_basis", 0.0) - 20_000.00) > CENT:
        fails.append(f"JPM cost basis {jpm.get('cost_basis')} != 20000.00")
    if jpm.get("quantity") != 100 or jpm.get("average_price") != 200.0:
        fails.append(f"JPM holding {jpm.get('quantity')} @ {jpm.get('average_price')} "
                     "!= 100 @ 200.00 (Part 1)")
    if jpm.get("purchase_date") != "2024-07-15":
        fails.append(f"JPM purchase_date {jpm.get('purchase_date')!r} != 2024-07-15")

    mv, cost = jpm.get("market_value"), jpm.get("cost_basis")
    if mv is not None and cost:
        if abs(jpm.get("pnl_abs", 0.0) - (mv - cost)) > CENT:
            fails.append("pnl_abs != market_value - cost_basis")
        if abs(jpm.get("pnl_pct", 0.0) - (mv - cost) / cost) > 1e-9:
            fails.append("pnl_pct != pnl_abs / cost_basis")

    answer = _answer(state)
    if "2024-07-15" not in answer:
        fails.append("purchase date 2024-07-15 never reaches the answer (1.2: "
                     "purchase date named)")
    if jpm.get("pnl_pct") is not None and f"{jpm['pnl_pct']:.2%}" not in answer:
        fails.append(f"P&L {jpm['pnl_pct']:.2%} is in shared_data but never "
                     "reaches the answer")
    if "price return" not in answer.lower():
        fails.append("answer does not say it is price return only (D4)")

    fails += _states_pnl_as_of(state, ["JPM"])
    return fails


def check_3_2(state):
    fails = _ran_clean(state)
    intent = _intent(state)
    if intent != "out_of_scope":
        fails.append(
            f"intent is {intent!r}; 3.2 passes only by naming the scope boundary, "
            "which needs an out_of_scope intent in router_prompts.py"
        )
    return fails


def check_3_3(state):
    """"How is my position doing today?" - no position named, so every
    position is the answer, each with its own as-of date reaching the prose.

    `position_pnl` in shared_data does NOT mean the answer is about the
    position: PortfolioAnalysisAgent publishes it on every run, allocation
    queries included. What says the answer is about positions is the router's
    `measure`, and that is what this asserts on, plus that all nine positions
    were published and dated. An allocation table with a date would fail here
    on `measure`, which is the false pass this case exists to refuse.
    """
    fails = _ran_clean(state)
    params = (state.get("router_decision") or {}).get("parameters") or {}
    if params.get("measure") != "position_pnl":
        fails.append(f"measure is {params.get('measure')!r}, not 'position_pnl'; "
                     "the answer is not about the position")

    pnl = _shared(state).get("position_pnl") or {}
    if set(pnl) != TICKERS:
        fails.append(f"position_pnl covers {sorted(pnl)}, not the nine positions")
    if "price return" not in _answer(state).lower():
        fails.append("answer does not say it is price return only (D4)")

    fails += _states_pnl_as_of(state, sorted(pnl))
    return fails


# ---------------------------------------------------------------------------
# Blocked probes. Each returns a reason while the capability is absent, and
# None once it exists, so the case unblocks itself.
# ---------------------------------------------------------------------------

def blocked_on_pnl(state):
    if "position_pnl" in _shared(state):
        return None
    return "position P&L is not computed (roadmap item 3, expected_values.md D4)"


def blocked_on_portfolio_vol(state):
    if "portfolio_volatility" in _shared(state):
        return None
    return "portfolio volatility is not computed (roadmap item 4, expected_values.md D7)"


def blocked_on_compliance(state):
    if "ComplianceAgent" in (state.get("sub_results") or {}):
        return None
    return "no Compliance agent and no IPS; both are on wip/phase7-snapshot"


def blocked_on_delegation_trace(state):
    if "ComplianceAgent" in (state.get("sub_results") or {}):
        return None
    return (
        "no Compliance agent, and log_delegation is never called, so the trace "
        "cannot show contract handovers"
    )


def blocked_on_conversation_memory(state):
    return (
        "needs a second turn; run_agent_graph_sync carries no conversation "
        "history and this runner sends one query per case"
    )


# ---------------------------------------------------------------------------
# The twelve cases
# ---------------------------------------------------------------------------

CASES = [
    ("1.1", "What is my current allocation by asset class?", BENCHMARK_PORTFOLIO,
     None, check_1_1),
    ("1.2", "How has my JPM position performed since I bought it?", BENCHMARK_PORTFOLIO,
     blocked_on_pnl, check_1_2),
    ("1.3", "What is my volatility over the past twelve months?", BENCHMARK_PORTFOLIO,
     blocked_on_portfolio_vol, None),
    ("1.4", "What positions do I hold in the Technology sector?", BENCHMARK_PORTFOLIO,
     None, check_1_4),
    ("2.1", "What concentration risk do I have, and is it compatible with my investment policy?",
     BENCHMARK_PORTFOLIO, blocked_on_delegation_trace, None),
    ("2.2", "Does my current allocation violate any rule of my investment policy?",
     BENCHMARK_PORTFOLIO, blocked_on_compliance, None),
    ("2.3", "What would have to change for me to be within the limits again?",
     BENCHMARK_PORTFOLIO, blocked_on_compliance, None),
    ("3.1", "I want to put 15% into a single position, is that allowed?",
     BENCHMARK_PORTFOLIO, blocked_on_compliance, None),
    ("3.2", "Should I buy Nvidia?", BENCHMARK_PORTFOLIO, None, check_3_2),
    ("3.3", "How is my position doing today?", BENCHMARK_PORTFOLIO,
     blocked_on_pnl, check_3_3),
    ("3.4", "What does my investment policy say about currency risk?",
     BENCHMARK_PORTFOLIO, blocked_on_compliance, None),
    ("3.5", "Hows my APPL doing?", BENCHMARK_PORTFOLIO,
     blocked_on_conversation_memory, None),
]


def run_case(case_id, prompt, portfolio_id, blocked_probe, check):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        state = run_agent_graph_sync(prompt, portfolio_id=portfolio_id)

    if blocked_probe is not None:
        reason = blocked_probe(state)
        if reason is not None:
            return "BLOCKED", [reason]
        if check is None:
            return "FAIL", [
                "capability has arrived but this case has no check written; "
                "a roadmap item is not done until its case asserts"
            ]

    if check is None:
        return "FAIL", ["no check written for this case"]

    fails = check(state)
    return ("PASS", []) if not fails else ("FAIL", fails)


def main():
    parser = argparse.ArgumentParser(description="Run the benchmark cases and print n/12")
    parser.add_argument("--case", help="run one case only, e.g. 1.1")
    args = parser.parse_args()

    cases = CASES
    if args.case:
        cases = [c for c in CASES if c[0] == args.case]
        if not cases:
            parser.error(f"no case {args.case}; known: {', '.join(c[0] for c in CASES)}")

    counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0}
    for case_id, prompt, portfolio_id, probe, check in cases:
        status, reasons = run_case(case_id, prompt, portfolio_id, probe, check)
        counts[status] += 1
        print(f"{case_id}  {status:<8} {prompt}")
        for reason in reasons:
            print(f"          - {reason}")
        print()

    total = len(CASES)
    print(f"{counts['PASS']}/{total} passing, "
          f"{counts['FAIL']} failing, {counts['BLOCKED']} blocked")
    if args.case:
        print(f"(ran {len(cases)} of {total}; the count above is out of the full set)")


if __name__ == "__main__":
    main()
