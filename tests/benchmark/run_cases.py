"""
Benchmark case runner. Prints n/18 against docs/benchmark.md Part 3.

Not part of pytest. Eighteen live queries cost API calls and about two minutes, so
this is the fourth loop - pytest, CLI, golden set, runner - not a thing bolted
onto pytest. Each of the four has a blind spot the others do not.

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

BLOCKED is not a pass. The headline number is passes out of eighteen.

Blocked cases probe for the capability rather than declaring themselves blocked,
so they unblock automatically when it arrives. A case that unblocks while its
check is still unwritten reports FAIL saying so - "done" for a roadmap item
means its case asserts, not that its arithmetic is right.

A case may have several turns (3.5): the prompt is then a tuple, each turn
runs after the previous turn's final state, and the probe and the check
receive the list of states. The probe runs after the first turn, which for
3.5 is a clarification extraction asks with no model call.
"""

import argparse
import contextlib
import inspect
import io
import re
import sys
from pathlib import Path

# This tree's src first, as cli.py does, so a worktree's run scores the
# worktree and not the checkout the venv's editable install points at.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agents.graph import run_agent_graph_sync
from agents.state import AgentState
from observability import get_tracer
from observability.tracer import TraceEventType


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

# expected_values.md Part 7: which holdings are funds is seeded data
# (`Asset.instrument_type`), static like the cost bases above. IPS-4.2 counts
# issuers over directly held shares only, so these four are exempt from it.
FUNDS = {"SPY", "TLT", "GLD", "VNQ"}
SHARES = TICKERS - FUNDS

# The closed status set of a compliance finding (Part 7, and the
# shared_data["compliance"] shape decided 8 September). `refused` is for a
# hypothetical weight (3.1), never for a holding.
COMPLIANCE_STATUSES = {"ok", "breach", "exempt", "refused"}

# A trade verb and a held ticker on one line is a recommendation, which no
# compliance answer may contain (benchmark.md Part 2: "gives no recommendation").
# The verbs are the ones that name an order, not a condition: "Equity down
# 4.41 pp" is a condition (IPS-5.2), "sell AAPL" is a trade.
TRADE_LINE = re.compile(
    r"\b(buy|sell|purchase|trim|liquidate|short)\b.*\b(" + "|".join(sorted(TICKERS)) + r")\b",
    re.IGNORECASE,
)

CENT = 0.005
AS_OF = re.compile(r"\d{4}-\d{2}-\d{2}")
CLAUSE_ID = re.compile(r"IPS-\d+\.\d+")
# A percentage or percentage-point figure in the prose, with its printed
# precision, so a check can ask where each one came from.
PCT_FIGURE = re.compile(r"(\d+(?:\.(\d+))?)\s*(?:%|pp\b|percentage points)")

# Weighing-up words. 3.1 passes on a refusal with "no commentary, no weighing
# up" and Part 7 says 'no "depends"'. A short closed list of the words that
# open a deliberation; "could" and "might" are left out because the IPS-4.2
# condition ("if the position would be a directly held share") is legitimately
# stated in the conditional.
HEDGE = re.compile(
    r"\b(depends|however|consider|alternatively|weigh|on balance|that said|trade-?off)\b",
    re.IGNORECASE,
)

# The weight 3.1 asks about. Static: it is in the prompt, not the market.
HYPOTHETICAL_WEIGHT = 0.15

# The sentence the formatter emits when the policy has no clause on a topic
# (Part 7, 3.4: "the policy contains nothing on currency risk"). Repeated
# here rather than imported, as SCOPE_BOUNDARY is, so the check can fail
# before the formatter exists.
NO_CLAUSE = "contains nothing on"


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def _shared(state):
    return state.get("shared_data") or {}


def _allocation(state, view):
    return (_shared(state).get("allocation") or {}).get(view) or {}


def _by_label(block):
    return {line["label"]: line for line in block.get("lines", [])}


def _compliance(state):
    return _shared(state).get("compliance") or {}


def _answer(state):
    return state.get("final_response") or ""


def _intent(state):
    return (state.get("router_decision") or {}).get("intent")


def _calls(state):
    """The turn's tool-call log: one record per tool the layer called, in
    call order, each with `tool`, `inputs`, `key`, `block`, `text` and
    `as_of`. Empty when the turn called none."""
    return state.get("tool_calls") or []


def _called(state):
    """What the log shows, as (tool, inputs) pairs, for a reason or an
    assertion about which tool ran with what."""
    return [(r.get("tool"), r.get("inputs") or {}) for r in _calls(state)]


# ---------------------------------------------------------------------------
# The log probe. Every case reads BLOCKED until the layer writes the log:
# before any paid call when the state type declares no such key, and after
# a run when the state carries none. An empty list is a log: a turn the
# pre-pass answered with a clarification called no tool and says so.
# ---------------------------------------------------------------------------

LOG_KEY = "tool_calls"


def state_declares_log(state_type=AgentState):
    return LOG_KEY in getattr(state_type, "__annotations__", {})


def blocked_on_tool_log(state):
    if LOG_KEY in state:
        return None
    return ("the state carries no tool-call log; the conversation layer that "
            "writes it (Order 5, decision 45) has not landed")


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
    `shared_data["position_pnl"]` and has `_states_pnl_as_of` below; portfolio
    volatility carries a window and a weights date and `check_1_3` reads both.
    Searching for a date wherever one might live is what the regex version did.
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
        line["pct_of_total"]
        for line in lines.values()
        if line.get("pct_of_total") is not None
    )
    if abs(total - 1.0) > 1e-9:
        fails.append(f"percentages sum to {total}, not 1.0")

    fails += _cost_bases_match(lines, COST_BY_CLASS, "by_asset_class")

    cash = lines.get("Cash") or {}
    if cash.get("pct_of_total") is None:
        fails.append("cash has no % of total; D2 puts cash inside the denominator")
    if cash.get("pct_of_invested") is not None:
        fails.append("cash carries a % of invested; cash is not invested")

    held = {t for line in lines.values() for t in line.get("tickers", [])}
    if held != TICKERS:
        fails.append(f"tickers {sorted(held)} != the nine seeded positions")

    fails += _prose_carries(state, lines, "pct_of_total")
    fails += _states_as_of(state)
    return fails


def check_1_3(state):
    """Portfolio volatility over twelve months. Passes when "basis of
    calculation traceable": every element of the basis is published as data
    and reaches the prose. The figure itself moves with prices and is pinned
    by tests/test_portfolio_volatility.py over the committed closes; here it
    is checked as an invariant against the per-holding figures Part 4 names.
    """
    fails = _ran_clean(state)
    params = (state.get("router_decision") or {}).get("parameters") or {}
    if params.get("measure") != "portfolio_volatility":
        fails.append(f"measure is {params.get('measure')!r}, not 'portfolio_volatility'")
    if params.get("period") != "1Y":
        fails.append(f"period is {params.get('period')!r}; 'twelve months' is 1Y")

    pv = _shared(state).get("portfolio_volatility") or {}
    if not pv:
        return fails + ["no portfolio_volatility in shared_data"]

    vol = pv.get("annualised")
    if not isinstance(vol, (int, float)) or not 0 < vol < 1:
        fails.append(f"annualised volatility {vol!r} is not a fraction in (0, 1)")

    window = pv.get("window") or {}
    for key in ("start", "end"):
        if not AS_OF.fullmatch(str(window.get(key, ""))):
            fails.append(f"window.{key} is not a YYYY-MM-DD date: {window.get(key)!r}")
    if window.get("closes") != 252:
        fails.append(f"window.closes is {window.get('closes')}, not 252 (D8: 1Y is 252 closes)")

    weights = pv.get("weights") or {}
    if set(weights) != TICKERS:
        fails.append(f"weights cover {sorted(weights)}, not the nine positions")
    elif abs(sum(weights.values()) - 1.0) > 1e-4:
        fails.append(f"weights sum to {sum(weights.values())}, not 1 (rounded to 6dp)")

    # Part 4's sanity check as an invariant: diversification puts the
    # portfolio figure well below the weighted average of the single names.
    vols = _shared(state).get("volatilities") or {}
    if weights and vols and set(weights) <= set(vols):
        weighted_average = sum(weights[t] * vols[t] for t in weights)
        if isinstance(vol, (int, float)) and vol > 0.8 * weighted_average:
            fails.append(f"portfolio volatility {vol:.4f} is not below the "
                         f"weighted average of single-name vols {weighted_average:.4f}; "
                         "an average is not a portfolio figure (Part 4)")

    answer = _answer(state)
    if isinstance(vol, (int, float)) and f"{vol:.2%}" not in answer:
        fails.append(f"volatility {vol:.2%} is in shared_data but never reaches the answer")
    for label, value in (("window.start", window.get("start")),
                         ("window.end", window.get("end")),
                         ("window.closes", window.get("closes")),
                         ("annualisation", pv.get("annualisation")),
                         ("covariance_method", pv.get("covariance_method"))):
        if value is not None and str(value) not in answer:
            fails.append(f"{label} {value} is in shared_data but never reaches the answer")

    stated = pv.get("weights_as_of")
    if not stated:
        fails.append("no weights_as_of in shared_data['portfolio_volatility'] "
                     "(benchmark.md Part 3b)")
    else:
        fails += _date_reaches_answer(state, stated, "portfolio_volatility.weights_as_of")
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


SCOPE_BOUNDARY = "outside what this system does"


def check_3_2(state):
    """A price forecast passes when the answer refers to the scope
    boundary and gives no forecast.

    **The prompt changed on 20 September**, at the commit that made 4.3
    answerable, as benchmark.md's "When 3.2 expires" says it would. It was
    "Should I buy Nvidia?" while a buy question was out of scope; that
    question is now research, answered through the philosophy screen, the
    valuation range and the IPS check at a stated weight. The case is
    rewritten and not deleted, to a prompt that stays out of scope for
    good: no price a stock will reach, ever (DIRECTION.md invariant 7).

    Intent alone is not enough: a router that says out_of_scope while the
    synthesizer still runs agents and formats a result would pass on the
    label. So the plan must be empty, nothing may have run, and the fixed
    boundary sentence must reach the answer. The sentence is the one the
    synthesizer emits for this intent; it is repeated here rather than
    imported so that this check can fail before the capability exists.
    """
    fails = _ran_clean(state)
    intent = _intent(state)
    if intent != "out_of_scope":
        fails.append(
            f"intent is {intent!r}; 3.2 passes only by naming the scope boundary, "
            "which needs an out_of_scope intent in router_prompts.py"
        )
    plan = (state.get("router_decision") or {}).get("execution_order") or []
    if plan:
        fails.append(f"execution_order {plan} is not empty; out_of_scope plans nothing")
    ran = sorted((state.get("sub_results") or {}).keys())
    if ran:
        fails.append(f"agents ran: {ran}; an out-of-scope request runs nothing")
    if SCOPE_BOUNDARY not in _answer(state):
        fails.append(f"answer does not carry the scope boundary ({SCOPE_BOUNDARY!r})")
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

    `tickers` must be empty. The formatter prints all nine positions whether
    the list is empty or padded with all nine, so without this check the case
    passed while the router was still copying the portfolio in - it did, on
    7 September, in the same run that failed 1.2 for exactly that padding.
    """
    fails = _ran_clean(state)
    params = (state.get("router_decision") or {}).get("parameters") or {}
    if params.get("measure") != "position_pnl":
        fails.append(f"measure is {params.get('measure')!r}, not 'position_pnl'; "
                     "the answer is not about the position")
    if params.get("tickers"):
        fails.append(f"tickers {params.get('tickers')} is not empty; the question "
                     "names no position, and a filled list means the router "
                     "copied the portfolio in")

    pnl = _shared(state).get("position_pnl") or {}
    if set(pnl) != TICKERS:
        fails.append(f"position_pnl covers {sorted(pnl)}, not the nine positions")
    if "price return" not in _answer(state).lower():
        fails.append("answer does not say it is price return only (D4)")

    fails += _states_pnl_as_of(state, sorted(pnl))
    return fails


def _compliance_block_invariants(state):
    """What every compliance block must satisfy, whichever case produced it.

    Structure only, never which clauses breach: two of Part 7's eight breaches
    are decided by cents and sit on the other side of their limit on a live
    run. What is asserted instead is that the block is internally consistent
    with itself and with the allocation block it was computed from:

      - every finding's clause exists in the loaded policy, and no finding
        names a statement (a clause with no number cannot be checked, and a
        finding on one is the checker inventing arithmetic)
      - `total_value`, when present, is the asset-class denominator (D2), so
        one number is the denominator for every clause and it is the number
        the allocation published, not a second computation. It is absent for
        a hypothetical weight (3.1), which names no portfolio, and then no
        finding may carry a currency distance: a figure in currency needs a
        total somebody measured
      - status is in the closed set
      - an `exempt` finding carries no arithmetic (Part 7)
      - on every other finding the distance figures reconcile: signed so
        that positive is a breach, `distance_pp = (observed - limit) x 100`
        against a max bound and `(limit - observed) x 100` against a min, and
        `distance_value = distance_pp / 100 x total_value` (Part 7's eight
        breaches reproduce this to the cent); and status agrees with the sign,
        with exactly-at-the-limit passing (D9)
      - a band clause emits one finding per bound (min and max), never a
        "nearer bound" chosen by the checker
    """
    fails = []
    block = _compliance(state)
    policy = block.get("policy") or {}
    findings = block.get("findings") or []
    statements = block.get("statements") or []

    if not policy:
        return ["no policy in shared_data['compliance']; the answer cannot cite"]

    statement_ids = {c for c, entry in policy.items() if entry.get("type") == "statement"}
    listed = {s.get("clause") for s in statements}
    if listed != statement_ids:
        fails.append(f"statements {sorted(listed)} != the policy's statement "
                     f"clauses {sorted(statement_ids)}")

    total = block.get("total_value")
    denominator = _allocation(state, "by_asset_class").get("total_value")
    if total is not None and (denominator is None or abs(total - denominator) > CENT):
        fails.append(f"compliance total_value {total} != allocation "
                     f"by_asset_class.total_value {denominator} (D2)")

    arithmetic = ("observed", "limit", "bound", "distance_pp", "distance_value")
    required = arithmetic if total is not None else arithmetic[:-1]
    bounds_seen = {}
    for f in findings:
        clause, subject, status = f.get("clause"), f.get("subject"), f.get("status")
        where = f"{clause}/{subject}"

        if clause not in policy:
            fails.append(f"finding {where} cites a clause not in the loaded policy")
            continue
        if clause in statement_ids:
            fails.append(f"finding {where} is on a statement; statements have no findings")
        if f.get("type") != policy[clause].get("type"):
            fails.append(f"finding {where} type {f.get('type')!r} != policy "
                         f"type {policy[clause].get('type')!r}")
        if status not in COMPLIANCE_STATUSES:
            fails.append(f"finding {where} status {status!r} not in "
                         f"{sorted(COMPLIANCE_STATUSES)}")
            continue

        if status == "exempt":
            carried = [k for k in arithmetic if f.get(k) is not None]
            if carried:
                fails.append(f"exempt finding {where} carries arithmetic: {carried}")
            continue

        missing = [k for k in required if f.get(k) is None]
        if missing:
            fails.append(f"finding {where} ({status}) lacks {missing}")
            continue
        if total is None and f.get("distance_value") is not None:
            fails.append(f"finding {where} carries distance_value "
                         f"{f['distance_value']} with no total_value to price it against")

        observed, limit, bound = f["observed"], f["limit"], f["bound"]
        if bound not in ("min", "max"):
            fails.append(f"finding {where} bound {bound!r} is not 'min' or 'max'")
            continue
        for k in ("observed", "limit"):
            if not 0 <= f[k] <= 1:
                fails.append(f"finding {where} {k} {f[k]} is not a fraction; "
                             "percentages in shared_data are fractions")

        signed = (observed - limit) if bound == "max" else (limit - observed)
        if abs(signed * 100 - f["distance_pp"]) > 1e-6:
            fails.append(f"finding {where}: distance_pp {f['distance_pp']} != "
                         f"{signed * 100:.6f} from observed {observed}, limit "
                         f"{limit}, bound {bound}")
        if total is not None and abs(f["distance_pp"] / 100 * total - f["distance_value"]) > CENT:
            fails.append(f"finding {where}: distance_value {f['distance_value']} "
                         f"!= distance_pp / 100 x total_value")

        # D9: exactly at the limit passes; strict, unrounded beyond the block.
        # A refusal is a breach of a weight nobody holds yet, so the same sign.
        if status in ("breach", "refused") and not signed > 0:
            fails.append(f"finding {where} is {status} with distance {signed * 100:.4f} pp")
        if status == "ok" and signed > 0:
            fails.append(f"finding {where} is ok while {signed * 100:.4f} pp over its limit")

        bounds_seen.setdefault((clause, subject), []).append(bound)

    for key, bounds in bounds_seen.items():
        if len(bounds) != len(set(bounds)):
            fails.append(f"finding {key[0]}/{key[1]} has duplicate bounds {bounds}")

    return fails


def _no_trade_lines(state):
    lines = [l for l in _answer(state).splitlines() if TRADE_LINE.search(l)]
    if lines:
        return [f"answer names a trade: {lines[0].strip()!r}"]
    return []


def check_2_2(state):
    """"Does my current allocation violate any rule of my investment policy?"
    passes on a systematic check of all rules, not just the obvious ones.

    "All rules" is asserted as coverage, not as verdicts: every checkable
    clause type has a finding on every subject the portfolio has for it, and
    every clause in the policy - statements included - is named in the answer,
    so the reader can see the rules that were not computed as well as the
    ones that were. Which subjects breach is Part 7's business and moves with
    prices; which subjects exist does not.

    Subjects per type are the static seed facts the Level 1 checks already
    pin: the five asset classes, the nine tickers (with the four funds exempt
    under the issuer clause), the four sectors. The unsectored line is
    reported and not counted (IPS-4.3), so it has no finding.
    """
    fails = _ran_clean(state)
    block = _compliance(state)
    if not block:
        return fails + ["no compliance in shared_data"]

    fails += _compliance_block_invariants(state)

    if block.get("no_clause"):
        fails.append("no_clause is set; 2.2 is a check of the portfolio, not a "
                     "topic lookup")

    findings = block.get("findings") or []
    policy = block.get("policy") or {}
    by_type = {}
    for f in findings:
        by_type.setdefault(f.get("type"), {}).setdefault(f.get("status"), set()).add(f.get("subject"))

    def subjects(kind, *statuses):
        statuses = statuses or tuple(COMPLIANCE_STATUSES)
        return set().union(*(by_type.get(kind, {}).get(s, set()) for s in statuses))

    expected = {
        "asset_class_band": set(COST_BY_CLASS),
        "max_instrument_weight": TICKERS,
        "max_sector_weight": set(COST_BY_SECTOR),
    }
    for kind, want in expected.items():
        got = subjects(kind)
        if got != want:
            fails.append(f"{kind} findings cover {sorted(got)}, not {sorted(want)}")

    if subjects("max_issuer_weight", "ok", "breach") != SHARES:
        fails.append(f"max_issuer_weight is checked on "
                     f"{sorted(subjects('max_issuer_weight', 'ok', 'breach'))}, "
                     f"not the five directly held shares {sorted(SHARES)}")
    if subjects("max_issuer_weight", "exempt") != FUNDS:
        fails.append(f"max_issuer_weight exempts "
                     f"{sorted(subjects('max_issuer_weight', 'exempt'))}, "
                     f"not the four funds {sorted(FUNDS)} (IPS-4.2)")

    refused = sorted(f"{f.get('clause')}/{f.get('subject')}"
                     for f in findings if f.get("status") == "refused")
    if refused:
        fails.append(f"refused findings {refused} on a portfolio check; refused "
                     "is for a hypothetical (3.1)")

    checkable = {c for c, e in policy.items() if e.get("type") != "statement"}
    covered = {f.get("clause") for f in findings}
    if checkable - covered:
        fails.append(f"checkable clauses with no finding: {sorted(checkable - covered)}")

    answer = _answer(state)
    uncited = sorted(c for c in policy if c not in answer)
    if uncited:
        fails.append(f"clauses never named in the answer: {uncited}; all rules "
                     "means visibly all of them")
    invented = sorted(set(CLAUSE_ID.findall(answer)) - set(policy))
    if invented:
        fails.append(f"answer cites clause ids not in the policy: {invented}")

    fails += _no_trade_lines(state)

    as_of = (block.get("as_of") or {}).get("worst_case")
    if not as_of:
        fails.append("no as_of.worst_case in shared_data['compliance'] "
                     "(benchmark.md Part 3b)")
    else:
        fails += _date_reaches_answer(state, as_of, "compliance.as_of.worst_case")
    return fails


def _unexplained_percentages(state, findings):
    """Every percentage or pp figure in the answer must be one the findings
    carry: an observed weight, a limit, or a distance. A figure that is none
    of those is a target - the midpoint of a band, a weight the policy does
    not state - and IPS-5.2 forbids exactly that. Matched at the precision
    the prose printed it, so 65%, 65.0% and 65.00% all explain themselves
    and a 52.50% midpoint does not.
    """
    allowed = set()
    for f in findings:
        if f.get("status") == "exempt":
            continue
        for key, scale in (("observed", 100), ("limit", 100), ("distance_pp", 1)):
            if f.get(key) is not None:
                allowed.add(f[key] * scale)

    unexplained = []
    for match in PCT_FIGURE.finditer(_answer(state)):
        printed, decimals = match.group(1), match.group(2)
        tolerance = 0.5 * 10 ** -len(decimals or "") + 1e-9
        value = float(printed)
        if not any(abs(value - a) <= tolerance for a in allowed):
            unexplained.append(match.group(0))
    if unexplained:
        return [f"answer carries figures that are no finding's observed, limit "
                f"or distance: {unexplained}; a figure the policy does not "
                "state is a target (IPS-5.2)"]
    return []


def check_2_3(state):
    """"What would have to change for me to be within the limits again?"
    passes when the answer describes conditions and gives no recommendation.

    A condition is IPS-5.2's: the distance back to the limit, in percentage
    points of total. So every breach's `distance_pp` reaches the answer with
    its clause id, no percentage in the answer is anything but an observed
    weight, a limit or a distance (no midpoint, no target), and no line
    names a trade. "Reducing AAPL by 5.84 pp" is a condition and passes;
    "sell AAPL" is an order and fails. Overlaps are the reader's to see
    (Part 7), so nothing here asks that they be netted or not.

    Which clauses breach is not asserted. If none does on the day, the
    breach loop is empty and the case passes on the rest, which is the
    right answer to a question about limits nobody is outside.
    """
    fails = _ran_clean(state)
    block = _compliance(state)
    if not block:
        return fails + ["no compliance in shared_data"]

    fails += _compliance_block_invariants(state)

    if block.get("no_clause"):
        fails.append("no_clause is set; 2.3 is a check of the portfolio, not a "
                     "topic lookup")

    findings = block.get("findings") or []
    policy = block.get("policy") or {}
    checkable = {c for c, e in policy.items() if e.get("type") != "statement"}
    covered = {f.get("clause") for f in findings}
    if checkable - covered:
        fails.append(f"checkable clauses with no finding: {sorted(checkable - covered)}; "
                     "the breach list is only complete over a full check")

    refused = sorted(f"{f.get('clause')}/{f.get('subject')}"
                     for f in findings if f.get("status") == "refused")
    if refused:
        fails.append(f"refused findings {refused} on a portfolio check; refused "
                     "is for a hypothetical (3.1)")

    answer = _answer(state)
    for f in findings:
        if f.get("status") != "breach" or f.get("distance_pp") is None:
            continue
        where = f"{f.get('clause')}/{f.get('subject')}"
        if f["clause"] not in answer:
            fails.append(f"breach {where}: clause id never reaches the answer")
        if f"{f['distance_pp']:.2f}" not in answer:
            fails.append(f"breach {where}: distance {f['distance_pp']:.2f} pp is "
                         "in shared_data but never reaches the answer")

    invented = sorted(set(CLAUSE_ID.findall(answer)) - set(policy))
    if invented:
        fails.append(f"answer cites clause ids not in the policy: {invented}")

    fails += _unexplained_percentages(state, findings)
    fails += _no_trade_lines(state)

    as_of = (block.get("as_of") or {}).get("worst_case")
    if not as_of:
        fails.append("no as_of.worst_case in shared_data['compliance'] "
                     "(benchmark.md Part 3b)")
    else:
        fails += _date_reaches_answer(state, as_of, "compliance.as_of.worst_case")
    return fails


def check_3_1(state):
    """"I want to put 15% into a single position, is that allowed?" passes
    on a refusal citing the specific clause, no commentary, no weighing up.

    The checker applied to a hypothetical weight, not to holdings: every
    finding is `refused`, none is ok, breach or exempt, because the portfolio
    was not checked and a verdict on it would be an answer to a different
    question. The position is unnamed, so its instrument type is unknown and
    both concentration clauses apply: a refused finding at 0.15 on every
    `max_instrument_weight` and `max_issuer_weight` clause in the policy
    (Part 7: IPS-4.1 at 3.00 pp over, IPS-4.2 at 5.00 pp over), each id
    reaching the answer. The IPS-4.2 condition is the clause's own text, so
    nothing here asks how it is phrased.

    No denominator: the question names no portfolio, so `total_value` is
    absent and no finding prices its distance. Every percentage in the
    answer is the asked weight, a limit or a distance; a hedge word is a
    weighing-up; a trade line is a recommendation.
    """
    fails = _ran_clean(state)
    block = _compliance(state)
    if not block:
        return fails + ["no compliance in shared_data"]

    fails += _compliance_block_invariants(state)

    if block.get("no_clause"):
        fails.append("no_clause is set; 3.1 is a check against a clause that exists")
    if block.get("total_value") is not None:
        fails.append(f"total_value {block['total_value']} is set; a hypothetical "
                     "weight names no portfolio to measure against")

    findings = block.get("findings") or []
    policy = block.get("policy") or {}
    if not findings:
        fails.append("no findings; a refusal is a finding with status refused")

    not_refused = sorted(f"{f.get('clause')}/{f.get('subject')} ({f.get('status')})"
                         for f in findings if f.get("status") != "refused")
    if not_refused:
        fails.append(f"findings on the portfolio in a hypothetical check: {not_refused}")

    concentration = {c for c, e in policy.items()
                     if e.get("type") in ("max_instrument_weight", "max_issuer_weight")}
    if not concentration:
        fails.append("the policy has no max_instrument_weight or max_issuer_weight "
                     "clause; 3.1 has nothing to refuse against")
    refused_at_weight = {
        f.get("clause") for f in findings
        if f.get("status") == "refused"
        and f.get("observed") is not None
        and abs(f["observed"] - HYPOTHETICAL_WEIGHT) < 1e-9
        and f.get("bound") == "max"
    }
    if concentration - refused_at_weight:
        fails.append(f"no refused finding at {HYPOTHETICAL_WEIGHT} against "
                     f"{sorted(concentration - refused_at_weight)}; an unnamed "
                     "position may be a share or a fund, so both limits apply")

    answer = _answer(state)
    for f in findings:
        if f.get("status") == "refused" and f.get("clause") not in answer:
            fails.append(f"refused on {f.get('clause')} but the id never reaches "
                         "the answer; a refusal cites the specific clause")
    invented = sorted(set(CLAUSE_ID.findall(answer)) - set(policy))
    if invented:
        fails.append(f"answer cites clause ids not in the policy: {invented}")

    hedges = sorted({m.group(0).lower() for m in HEDGE.finditer(answer)})
    if hedges:
        fails.append(f"answer weighs up: {hedges}; a refusal has no commentary")

    fails += _unexplained_percentages(state, findings)
    fails += _no_trade_lines(state)
    return fails


def check_3_4(state):
    """"What does my investment policy say about currency risk?" - the clause
    does not exist - passes when the answer says the policy contains nothing
    on this and invents nothing.

    "Nothing" is only an answer over a full policy, so the block must carry
    the loaded policy with its statements (the invariants check that) and
    the `no_clause` marker, set by the node from the router's decision - the
    pure checker sees no query and cannot know a topic was asked about.
    Without the marker, "nothing to report" and "checked and all ok" are the
    same empty list, which is the false pass this case exists to refuse.

    Invents nothing, concretely: no findings (nothing was checked), no
    `total_value` (nothing was measured), no IPS id in the answer at all -
    not even a real one, since the nearest clause by topic is none and
    citing IPS-2.1 for currency is the retrieval failure benchmark.md Part 1
    names - no percentage, no holding. And the fixed sentence reaches the
    answer, so the intent label alone cannot pass.
    """
    fails = _ran_clean(state)
    block = _compliance(state)
    if not block:
        return fails + ["no compliance in shared_data"]

    fails += _compliance_block_invariants(state)

    if not block.get("no_clause"):
        # Name what the node matched, so the reason says whether the router
        # kept the user's words or mapped them onto a vocabulary member.
        topic = block.get("topic") or {}
        fails.append("no_clause is not set; a policy with no clause on the topic "
                     "has to say so as data, not only as prose "
                     f"(topic asked {topic.get('asked')!r}, matched {topic.get('clauses')})")
    findings = block.get("findings") or []
    if findings:
        fails.append(f"{len(findings)} findings on a topic lookup; nothing was "
                     "asked about the portfolio")
    if block.get("total_value") is not None:
        fails.append(f"total_value {block['total_value']} is set; a topic lookup "
                     "measures nothing")

    answer = _answer(state)
    cited = sorted(set(CLAUSE_ID.findall(answer)))
    if cited:
        fails.append(f"answer cites {cited}; the policy has no clause on this "
                     "and the nearest one by topic is none")
    named = sorted(t for t in TICKERS if re.search(rf"\b{t}\b", answer))
    if named:
        fails.append(f"answer names holdings {named}; a policy question is not "
                     "about the portfolio")
    fails += _unexplained_percentages(state, findings)
    if NO_CLAUSE not in answer:
        fails.append(f"answer does not say the policy {NO_CLAUSE!r} this")
    return fails


COMPLIANCE_PLAN = ["DataAgent", "PortfolioAnalysisAgent", "ComplianceAgent"]
CONCENTRATION_TYPES = {"max_instrument_weight", "max_issuer_weight", "max_sector_weight"}


def _trace_for(state):
    """The stored trace of this run, by request id. The tracer keeps completed
    traces in memory; the runner reads the last one and refuses a neighbour's."""
    traces = get_tracer().get_traces()
    wanted = state.get("request_id")
    if not traces or traces[-1].request_id != wanted:
        return None, [f"no stored trace for request {wanted!r}; the last stored "
                      f"is {traces[-1].request_id!r}" if traces else
                      "no stored trace at all"]
    return traces[-1], []


def _trace_shows_handovers(state, plan):
    """benchmark 2.1: "trace shows contract handovers". Each planned agent
    opened a span, in plan order; each agent but the last delegated to the
    next; ComplianceAgent's check ran as a traced tool call."""
    trace, fails = _trace_for(state)
    if trace is None:
        return fails

    started = [e.agent_name for e in trace.events
               if e.event_type == TraceEventType.AGENT_START and e.agent_name in plan]
    if started != plan:
        fails.append(f"agents in trace: {started}; the plan {plan} is not what the "
                     "trace shows ran")

    handovers = [(e.agent_name, e.metadata.get("to_agent"))
                 for e in trace.events if e.event_type == TraceEventType.DELEGATION]
    expected = list(zip(plan, plan[1:]))
    missing = [h for h in expected if h not in handovers]
    if missing:
        fails.append(f"handovers missing from the trace: {missing}; found {handovers}")

    tools = [(e.agent_name, e.tool_name) for e in trace.events
             if e.event_type == TraceEventType.TOOL_START]
    if ("ComplianceAgent", "check_ips") not in tools:
        fails.append(f"no traced check_ips tool call under ComplianceAgent; tools: {tools}")
    return fails


def check_2_1(state):
    """"What concentration risk do I have, and is it compatible with my
    investment policy?" passes when Data, Risk and Compliance agents all run
    and the trace shows contract handovers.

    Risk is PortfolioAnalysisAgent (decision, 8 September). So: the three
    agents planned in order and each successful; the trace carrying their
    spans, the two handovers and the checker's tool call; the block sound;
    and the answer carrying the concentration clauses - each 4.x breach's
    distance and clause id, each exempt fund named (Part 7: funds are
    counted at fund level and not attributed to issuers), the as-of date -
    with no figure the policy does not state and no trade line.

    Which subjects breach is not asserted.
    """
    fails = _ran_clean(state)
    plan = (state.get("router_decision") or {}).get("execution_order") or []
    if plan != COMPLIANCE_PLAN:
        fails.append(f"plan {plan} != {COMPLIANCE_PLAN}; Data, Risk (PortfolioAnalysisAgent) "
                     "and Compliance in that order")
    sub = state.get("sub_results") or {}
    not_ok = [a for a in COMPLIANCE_PLAN if not (sub.get(a) or {}).get("success")]
    if not_ok:
        fails.append(f"agents that did not run successfully: {not_ok}")

    fails += _trace_shows_handovers(state, COMPLIANCE_PLAN)

    block = _compliance(state)
    if not block:
        return fails + ["no compliance in shared_data"]
    fails += _compliance_block_invariants(state)
    if block.get("no_clause"):
        fails.append("no_clause is set on a portfolio check")

    findings = block.get("findings") or []
    policy = block.get("policy") or {}
    refused = [f for f in findings if f.get("status") == "refused"]
    if refused:
        fails.append(f"{len(refused)} refused findings on a portfolio check")

    answer = _answer(state)
    concentration = [f for f in findings if f.get("type") in CONCENTRATION_TYPES]
    if not concentration:
        fails.append("no findings under a concentration clause")
    for clause in sorted({f["clause"] for f in concentration}):
        if clause not in answer:
            fails.append(f"concentration clause {clause} never reaches the answer")
    for f in concentration:
        where = f"{f.get('clause')}/{f.get('subject')}"
        if f.get("status") == "breach" and f"{f['distance_pp']:.2f}" not in answer:
            fails.append(f"breach {where}: distance {f['distance_pp']:.2f} pp never "
                         "reaches the answer")
        if f.get("status") == "exempt" and not re.search(rf"\b{f['subject']}\b", answer):
            fails.append(f"exempt {where} is not named in the answer; funds are "
                         "counted at fund level and the answer has to say so")

    invented = sorted(set(CLAUSE_ID.findall(answer)) - set(policy))
    if invented:
        fails.append(f"answer cites clause ids not in the policy: {invented}")
    fails += _unexplained_percentages(state, findings)
    fails += _no_trade_lines(state)

    as_of = (block.get("as_of") or {}).get("worst_case")
    if not as_of:
        fails.append("no as_of.worst_case in shared_data['compliance'] "
                     "(benchmark.md Part 3b)")
    else:
        fails += _date_reaches_answer(state, as_of, "compliance.as_of.worst_case")
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
    """ComplianceAgent exists (8 September); a case is blocked now only when
    the router did not plan it, which is a routing gap, not a missing agent."""
    if "ComplianceAgent" in (state.get("sub_results") or {}):
        return None
    plan = (state.get("router_decision") or {}).get("execution_order") or []
    reason = (f"the router did not plan ComplianceAgent (intent {_intent(state)!r}, "
              f"plan {plan}); the agent exists, the routing for this wording does not")
    if _intent(state) == "clarification_needed":
        # What the router asked back is the diagnostic: it names what the
        # router could not resolve in the wording. router_node writes the
        # question to final_response; the decision dict does not carry it.
        reason += f"; it asked back: {_answer(state)!r}"
    return reason


blocked_on_delegation_trace = blocked_on_compliance


def blocked_on_conversation_memory(states):
    """3.5 needs the second turn to see the first: the graph's entry point
    has to accept the previous final state. Until it does the case is
    blocked on the capability, whatever the first turn answered."""
    if "previous" in inspect.signature(run_agent_graph_sync).parameters:
        return None
    return ("needs a second turn resolved against the first; run_agent_graph_sync "
            "takes no previous state")


def check_3_5(states):
    """"Hows my APPL doing?" then "yes" - a typo of a held ticker. Passes
    when the first turn asks back naming the holding instead of guessing,
    and the second turn is the resolved question routed as if typed:
    position P&L for AAPL and nothing else, with the resolution recorded on
    the decision so the pass is memory's and not the model's reading of
    APPL as AAPL.
    """
    first, second = states
    fails = _ran_clean(first) + _ran_clean(second)

    if _intent(first) != "clarification_needed":
        fails.append(f"turn 1 intent is {_intent(first)!r}; a typo of a holding is asked "
                     "about, not guessed")
    if first.get("sub_results"):
        fails.append(f"turn 1 ran agents {sorted(first['sub_results'])}; a clarification runs none")
    asked = _answer(first)
    for name in ("APPL", "AAPL"):
        if name not in asked:
            fails.append(f"turn 1 does not name {name} in what it asks back: {asked!r}")

    decision = second.get("router_decision") or {}
    params = decision.get("parameters") or {}
    resolved = decision.get("resolved") or {}
    if not resolved:
        fails.append("turn 2 records no resolution; the reply was routed as a new message")
    elif "AAPL" not in (resolved.get("message") or "") or "APPL" in (resolved.get("message") or ""):
        fails.append(f"turn 2 resolved to {resolved.get('message')!r}, not the question with AAPL")
    if _intent(second) != "data_fetch":
        fails.append(f"turn 2 intent is {_intent(second)!r}, not data_fetch")
    if params.get("measure") != "position_pnl":
        fails.append(f"turn 2 measure is {params.get('measure')!r}, not 'position_pnl'")
    if params.get("tickers") != ["AAPL"]:
        fails.append(f"turn 2 tickers {params.get('tickers')} != ['AAPL']")

    pnl = _shared(second).get("position_pnl") or {}
    aapl = pnl.get("AAPL")
    if not aapl:
        return fails + ["turn 2 published no position_pnl.AAPL"]
    answer = _answer(second)
    if aapl.get("pnl_pct") is not None and f"{aapl['pnl_pct']:.2%}" not in answer:
        fails.append(f"AAPL P&L {aapl['pnl_pct']:.2%} is in shared_data but never reaches the answer")
    if "price return" not in answer.lower():
        fails.append("answer does not say it is price return only (D4)")
    fails += _states_pnl_as_of(second, ["AAPL"])
    return fails


# ---------------------------------------------------------------------------
# Level 4: the philosophy check (benchmark.md, cases 4.1 and 4.6)
# ---------------------------------------------------------------------------

# The block the philosophy check publishes, `shared_data["screening"]`, in
# the shape of the compliance block: the loaded philosophy (id, type, text),
# its statements, the subject, the check's as-of date, the company's SIC
# code with its description and the date EDGAR stated it, the fiscal years
# read with their dates and no figures, and one finding per (clause, bound)
# or the one excluded finding alone (Part 10 F, D34 and D35). A check that
# stopped on a missing figure (PHI-1.2, D25) carries `stopped` and no
# findings. The figures themselves stay in the database: the block carries
# the years' dates and the findings, never a filed figure.
SCREEN_STATUSES = {"pass", "fail", "excluded"}
PHI_ID = re.compile(r"PHI-\d+\.\d+")
YEAR_KEYS = {"ends", "filed"}
# A statement is cited and not computed; the answer says so in these words.
NOT_COMPUTED = "not computed"

# X and Y as benchmark.md names them, by the ticker extraction reads (a
# company name is pending decision 16). X is W-1 on the synthetic watchlist,
# not held in portfolio 3. Y is the bank Part 10 F and Part 13 C measured.
WATCHLIST_TICKER = "GOOGL"
BANK_TICKER = "JPM"
# expected_values.md Part 13 C: what EDGAR states for JPMorgan. Static like
# the cost bases above: the code has no history to move with.
BANK_SIC = "6021"
BANK_SIC_DESCRIPTION = "National Commercial Banks"


def _screening(state):
    return _shared(state).get("screening") or {}


def blocked_on_screen(state):
    """The philosophy check node publishes the block when the routing
    reaches it. A state without the block is a question that did not
    reach the check, and the case is blocked on that; the reason names what
    the router did with the question so the record says whether the gap is
    the node or the routing."""
    if _screening(state):
        return None
    plan = (state.get("router_decision") or {}).get("execution_order") or []
    reason = (f"no screening block in shared_data (intent {_intent(state)!r}, plan {plan}); "
              "the question did not reach the philosophy check")
    errors = state.get("errors") or []
    if errors:
        reason += f"; errors: {errors}"
    return reason


def blocked_on_screen_figures(state):
    """4.1 on filed figures: W-1 stops by decision, not by defect (decision
    48, D36, Part 13 B). Alphabet's FY2021 and FY2022 non-current debt is
    filed only under a lease-inclusive tag that D36 keeps out of the list,
    so PHI-2.1 stops at FY2021 until the FY2027 report moves the five-year
    window past those years; after that PHI-3.1 stops on D&A, which Alphabet
    files under no us-gaap tag. A check that stopped on a missing figure is
    that decision working, and the case stays blocked on it."""
    reason = blocked_on_screen(state)
    if reason is not None:
        return reason
    stopped = _screening(state).get("stopped")
    if stopped:
        return (f"the check stopped on {stopped.get('clause')}: {stopped.get('reason')}; "
                "decision 48 (D36) keeps the lease-inclusive debt tag out of the list, so "
                "the stop at PHI-2.1 stands until Alphabet's FY2027 report, and PHI-3.1 "
                "stops on D&A after it (Part 13 B)")
    return None


def _screen_block_invariants(state, subject):
    """What every screening block must satisfy, whichever case produced it.

    Structure only: which clauses pass is the reference's business (Part 10
    D and F), and the figures move with each annual report. Asserted here:

      - the block carries the loaded philosophy and lists exactly its
        statements, so the answer can cite and can say what it did not compute
      - every finding cites a clause the philosophy has, never a statement,
        with the clause's own type, on the one subject asked about
      - status is in the closed set; an excluded finding carries the code and
        no arithmetic; every other finding carries its metric, observed,
        limit, bound and a signed distance, positive meaning failure, that
        reconciles with observed and limit; status agrees with the sign and
        exactly at the limit passes (D23)
      - a clause over fiscal years names the years it read and the deciding
        year among them, each a year the block dates; the margin of safety
        names the as-of dates of the price and the range instead
      - a band clause emits one finding per bound, never a nearer bound
      - the years carry dates and nothing else: the figures are raw data and
        stay out of shared_data
      - `stopped` and findings are not both set: a stopped check reports no
        verdict on any clause (PHI-1.2)
    """
    fails = []
    block = _screening(state)
    philosophy = block.get("philosophy") or {}
    findings = block.get("findings") or []
    statements = block.get("statements") or []
    years = block.get("years") or {}

    if not philosophy:
        return ["no philosophy in shared_data['screening']; the answer cannot cite"]

    statement_ids = {c for c, entry in philosophy.items() if entry.get("type") == "statement"}
    listed = {s.get("clause") for s in statements}
    if listed != statement_ids:
        fails.append(f"statements {sorted(listed)} != the philosophy's statement "
                     f"clauses {sorted(statement_ids)}")

    if (block.get("subject") or {}).get("ticker") != subject:
        fails.append(f"subject {block.get('subject')} is not {subject}")

    for label, dates in years.items():
        extra = sorted(set(dates) - YEAR_KEYS)
        if extra:
            fails.append(f"year {label} carries {extra}; the block dates the years and "
                         "carries no figure (hot potato)")
        for key in YEAR_KEYS:
            if not AS_OF.fullmatch(str(dates.get(key))):
                fails.append(f"year {label} {key} is not a YYYY-MM-DD date: {dates.get(key)!r}")

    if block.get("stopped") and findings:
        fails.append(f"the check stopped and still carries {len(findings)} findings; "
                     "a stopped check reports no verdict on any clause (PHI-1.2)")

    arithmetic = ("metric", "observed", "limit", "bound", "distance")
    bounds_seen = {}
    for f in findings:
        clause, status = f.get("clause"), f.get("status")
        where = f"{clause}/{f.get('subject')}"

        if clause not in philosophy:
            fails.append(f"finding {where} cites a clause not in the loaded philosophy")
            continue
        if clause in statement_ids:
            fails.append(f"finding {where} is on a statement; statements have no findings")
        if f.get("type") != philosophy[clause].get("type"):
            fails.append(f"finding {where} type {f.get('type')!r} != philosophy "
                         f"type {philosophy[clause].get('type')!r}")
        if f.get("subject") != subject:
            fails.append(f"finding {where} is about {f.get('subject')!r}, not {subject}")
        if status not in SCREEN_STATUSES:
            fails.append(f"finding {where} status {status!r} not in {sorted(SCREEN_STATUSES)}")
            continue

        if f.get("type") == "excluded_industry":
            if not re.fullmatch(r"\d{4}", str(f.get("sic"))):
                fails.append(f"finding {where} carries no four-digit SIC code: {f.get('sic')!r}")
            carried = [k for k in arithmetic + ("years_read", "deciding_year")
                       if f.get(k) not in (None, [], ())]
            if carried:
                fails.append(f"exclusion finding {where} carries arithmetic: {carried}")
            continue
        if status == "excluded":
            fails.append(f"finding {where} is excluded under a {f.get('type')} clause; "
                         "only an excluded_industry clause excludes")
            continue

        missing = [k for k in arithmetic if f.get(k) is None]
        if missing:
            fails.append(f"finding {where} ({status}) lacks {missing}")
            continue
        observed, limit, bound = f["observed"], f["limit"], f["bound"]
        if bound not in ("min", "max"):
            fails.append(f"finding {where} bound {bound!r} is not 'min' or 'max'")
            continue
        signed = (limit - observed) if bound == "min" else (observed - limit)
        if abs(signed - f["distance"]) > 1e-9:
            fails.append(f"finding {where}: distance {f['distance']} != {signed:.6f} from "
                         f"observed {observed}, limit {limit}, bound {bound}")
        if status == "fail" and not signed > 0:
            fails.append(f"finding {where} fails with distance {signed:.6f}")
        if status == "pass" and signed > 0:
            fails.append(f"finding {where} passes while {signed:.6f} over its limit (D23)")

        if f.get("type") == "margin_of_safety":
            for key in ("price_as_of", "range_as_of"):
                if not AS_OF.fullmatch(str(f.get(key))):
                    fails.append(f"finding {where} {key} is not a date: {f.get(key)!r}")
        else:
            read = list(f.get("years_read") or [])
            deciding = f.get("deciding_year")
            if not read:
                fails.append(f"finding {where} names no fiscal years read")
            if deciding not in read:
                fails.append(f"finding {where} deciding year {deciding!r} not among "
                             f"the years read {read}")
            undated = [y for y in read if y not in years]
            if undated:
                fails.append(f"finding {where} read {undated}, which the block does not date")

        bounds_seen.setdefault(clause, []).append(bound)

    for clause, bounds in bounds_seen.items():
        if len(bounds) != len(set(bounds)):
            fails.append(f"finding {clause} has duplicate bounds {bounds}")

    return fails


def _unexplained_screen_percentages(state, findings):
    """Every percentage in the answer is a finding's observed, limit or
    distance in a share metric, at the printed precision. A percentage none
    of them explains is a figure the model wrote."""
    allowed = set()
    for f in findings:
        if f.get("metric") in (None, "net_debt_to_ebitda"):
            continue
        for key in ("observed", "limit", "distance"):
            if f.get(key) is not None:
                allowed.add(f[key] * 100)
                allowed.add(abs(f[key]) * 100)
    # The range's rates are stated inputs, printed as the documents write
    # them (9% for 0.09); each traces to the record, not to a finding.
    for name, entry in ((_valuation(state).get("assumptions") or {})).items():
        if name != "horizon_years" and isinstance(entry.get("value"), (int, float)):
            allowed.add(entry["value"] * 100)

    unexplained = []
    for match in PCT_FIGURE.finditer(_answer(state)):
        printed, decimals = match.group(1), match.group(2)
        tolerance = 0.5 * 10 ** -len(decimals or "") + 1e-9
        if not any(abs(float(printed) - a) <= tolerance for a in allowed):
            unexplained.append(match.group(0))
    if unexplained:
        return [f"answer carries percentages that are no finding's observed, limit "
                f"or distance: {unexplained}"]
    return []


def _screen_dates_reach_answer(state):
    """Part 3b: the check's as-of date and the date EDGAR stated the code
    both reach the answer. The code is as of its pull and the years as of
    the check (KNOWN_GAPS, the two as-of entries); the answer prints both."""
    block = _screening(state)
    fails = []
    for key in ("as_of", "sic_as_of"):
        stated = block.get(key)
        if not stated:
            fails.append(f"no {key} in shared_data['screening'] (benchmark.md Part 3b)")
            continue
        fails += _date_reaches_answer(state, str(stated)[:10], f"screening.{key}")
    return fails


def _not_from_the_ips(state):
    """A question about the philosophy is not answered from the IPS: no
    compliance block, no IPS id (KNOWN_GAPS, "A question about the
    philosophy runs the IPS check")."""
    fails = []
    if _compliance(state):
        fails.append("shared_data carries a compliance block; the philosophy question "
                     "ran the IPS check")
    cited = sorted(set(CLAUSE_ID.findall(_answer(state))))
    if cited:
        fails.append(f"answer cites IPS clauses {cited}; the question is about the philosophy")
    return fails


def _no_recommendation(state, subject):
    verbs = r"\b(buy|sell|purchase|trim|liquidate|short|add to|enter|exit)\b"
    line_re = re.compile(rf"{verbs}.*\b{subject}\b|\b{subject}\b.*{verbs}", re.IGNORECASE)
    lines = [l for l in _answer(state).splitlines() if line_re.search(l)]
    if lines:
        return [f"answer recommends: {lines[0].strip()!r}"]
    return []


def check_4_1(state):
    """"Does X clear my philosophy?" passes when every numeric clause has a
    finding, pass or fail with its distance, citing its PHI id; every
    statement is named as not computed; every figure carries its fiscal year
    and its source; and there is no recommendation (benchmark.md Level 4).

    Blocked, not failed, while the check stops on a figure Alphabet does not
    file under Part 12 C's tags (the probe). What is asserted once it runs:
    the findings cover exactly the philosophy's checkable clauses in its
    order; each finding's id, its deciding fiscal year and that year's filed
    date reach the answer, and so does the name of the source the figures
    came from; each statement's id reaches the answer beside the words "not
    computed"; every percentage traces to a finding; both as-of dates are
    stated; nothing came from the IPS.
    """
    fails = _ran_clean(state)
    block = _screening(state)
    if not block:
        return fails + ["no screening in shared_data"]
    fails += _screen_block_invariants(state, WATCHLIST_TICKER)
    if block.get("stopped"):
        return fails + [f"the check stopped: {block['stopped']}"]

    philosophy = block.get("philosophy") or {}
    findings = block.get("findings") or []
    checkable = [c for c, e in philosophy.items() if e.get("type") != "statement"]
    found = []
    for f in findings:
        if f.get("clause") not in found:
            found.append(f.get("clause"))
    if found != checkable:
        fails.append(f"findings cover {found}, not every checkable clause in philosophy "
                     f"order {checkable}")

    answer = _answer(state)
    years = block.get("years") or {}
    for f in findings:
        where = f"{f.get('clause')}/{f.get('subject')}"
        if f.get("clause") not in answer:
            fails.append(f"finding on {f.get('clause')} but the id never reaches the answer")
        deciding = f.get("deciding_year")
        if deciding:
            if deciding not in answer:
                fails.append(f"finding {where} was decided by {deciding}, which never reaches "
                             "the answer; every figure carries its fiscal year")
            filed = (years.get(deciding) or {}).get("filed")
            if filed and str(filed) not in answer:
                fails.append(f"finding {where}: {deciding}'s report was filed {filed} and the "
                             "date never reaches the answer; every figure carries its source")
    source = block.get("source")
    if not source:
        fails.append("no source in shared_data['screening']; a figure without a source "
                     "is a number in the answer")
    elif str(source) not in answer:
        fails.append(f"source {source!r} never reaches the answer")

    for st in block.get("statements") or []:
        if st.get("clause") not in answer:
            fails.append(f"statement {st.get('clause')} is not named in the answer; every "
                         "statement is named as not computed")
    if NOT_COMPUTED not in answer.lower():
        fails.append(f"answer does not say what was {NOT_COMPUTED!r}")

    invented = sorted(set(PHI_ID.findall(answer)) - set(philosophy))
    if invented:
        fails.append(f"answer cites clause ids not in the philosophy: {invented}")

    fails += _unexplained_screen_percentages(state, findings)
    fails += _screen_dates_reach_answer(state)
    fails += _not_from_the_ips(state)
    fails += _no_recommendation(state, WATCHLIST_TICKER)
    return fails


def check_4_6(state):
    """"Does Y clear my philosophy?", Y a bank, passes when the answer stops
    where the philosophy says it stops: PHI-3.2, the company reported as
    excluded under the code EDGAR states, and nothing else about it. No
    verdict on the rest, nothing invented (benchmark.md Level 4; Part 10 F,
    D34 and D35).

    Concretely: one finding, on PHI-3.2, status excluded, carrying
    JPMorgan's code 6021 (Part 13 C); no fiscal year read, so the block
    dates none; the answer names PHI-3.2 and no other clause of either
    document, the code, its description as EDGAR states it and the date it
    was stated; no percentage, no other holding, no recommendation.
    """
    fails = _ran_clean(state)
    block = _screening(state)
    if not block:
        return fails + ["no screening in shared_data"]
    fails += _screen_block_invariants(state, BANK_TICKER)

    if block.get("stopped"):
        fails.append(f"the check stopped ({block['stopped']}); a bank is decided by its code "
                     "before any figure is read (D34)")
    findings = block.get("findings") or []
    if len(findings) != 1:
        fails.append(f"{len(findings)} findings; an excluded company gets one, on PHI-3.2, "
                     "and nothing else is reported (D35)")
    for f in findings:
        if f.get("clause") != "PHI-3.2" or f.get("status") != "excluded":
            fails.append(f"finding {f.get('clause')}/{f.get('status')}; the one finding is "
                         "PHI-3.2 excluded")
        if f.get("sic") != BANK_SIC:
            fails.append(f"finding carries code {f.get('sic')!r}, not {BANK_SIC} (Part 13 C)")
    if block.get("sic") != BANK_SIC:
        fails.append(f"block carries code {block.get('sic')!r}, not {BANK_SIC}")
    if block.get("sic_description") != BANK_SIC_DESCRIPTION:
        fails.append(f"block carries description {block.get('sic_description')!r}, not "
                     f"{BANK_SIC_DESCRIPTION!r} as EDGAR states it")
    if block.get("years"):
        fails.append(f"the block dates {sorted(block['years'])}; an excluded company has "
                     "no year read")

    answer = _answer(state)
    cited = set(PHI_ID.findall(answer))
    if cited != {"PHI-3.2"}:
        fails.append(f"answer cites {sorted(cited)}; it cites PHI-3.2 and reports nothing else")
    for text in (BANK_SIC, BANK_SIC_DESCRIPTION):
        if text not in answer:
            fails.append(f"answer does not carry {text!r}")
    figures = [m.group(0) for m in PCT_FIGURE.finditer(answer)]
    if figures:
        fails.append(f"answer carries percentages {figures}; nothing was read")
    named = sorted(t for t in TICKERS - {BANK_TICKER} if re.search(rf"\b{t}\b", answer))
    if named:
        fails.append(f"answer names holdings {named}; the question is about one company")

    fails += _screen_dates_reach_answer(state)
    fails += _not_from_the_ips(state)
    fails += _no_recommendation(state, BANK_TICKER)
    return fails


def _valuation(state):
    return _screening(state).get("valuation") or {}


def blocked_on_range(state):
    """4.2 needs a published range. Until the node computes one the case is
    blocked on it, not failed: Part 11 is computed by hand and
    quant/valuation.py reproduces it, and nothing in the graph calls it
    (KNOWN_GAPS, "What the node needs before it can publish a range")."""
    reason = blocked_on_screen(state)
    if reason is not None:
        return reason
    block = _screening(state)
    if not block.get("valuation") and not block.get("valuation_stopped"):
        return ("no valuation record in shared_data['screening']; nothing publishes a "
                "range (Part 11, decision 57)")
    return None


# The assumptions a range is computed from, by name (Part 11 D38): three the
# philosophy's, two the watchlist entry's. Their sources are clause or entry
# ids; a model's proposal has no vocabulary yet (case 4.3).
RANGE_ASSUMPTIONS = ("required_return", "terminal_growth", "horizon_years",
                     "growth_low", "growth_high")
ASSUMPTION_SOURCE = re.compile(r"^(PHI-\d+\.\d+|W-\d+)$")
# A forecast of a price, the one thing a valuation answer may never say
# (PHI-4.3, DIRECTION.md invariant 7).
PRICE_FORECAST = re.compile(r"\b(will (?:reach|be at|hit|trade at)|price target|target price)\b",
                            re.IGNORECASE)


def check_4_2(state):
    """"What is X worth?" passes when the answer carries a range and not a
    point; every assumption listed as an input with its source; the
    arithmetic traceable to the pipeline; the price and its as-of date
    stated; and no forecast of a price (benchmark.md Level 4).

    Structure only, and that is the whole of what this check can see: a
    range of 1.00 to 2.00 per share with five assumptions named would pass
    it (KNOWN_GAPS, "The runner's 4.2 check, once written, cannot see the
    arithmetic"). What holds the ends is tests/test_valuation.py against
    Part 11 C. The seam between them, the node assembling the block and
    the assumptions from live rows, is what this check runs and pytest
    does not, and n/18 says nothing about the range being right.

    Asserted on the record: a low end below a high end, both positive; the
    as-of; the fiscal year read with its end and filed dates, a year the
    block dates; the source; exactly the five assumptions, each with a
    value and a clause or entry id as its source; no filed figure. On the
    price: a value, an as-of date, a source, the ticker asked about. On
    the answer: both ends as printed, the year and its filed date, every
    assumption's source id, the price with its date, both source names;
    the midpoint of the ends nowhere in it; no forecast phrase; no
    recommendation; nothing from the IPS. A range that stopped (a
    candidate stating no growth pair) is not this case's X and fails here
    naming the stop.
    """
    fails = _ran_clean(state)
    block = _screening(state)
    if not block:
        return fails + ["no screening in shared_data"]
    fails += _screen_block_invariants(state, WATCHLIST_TICKER)
    if block.get("valuation_stopped"):
        return fails + [f"the range stopped: {block['valuation_stopped']}"]
    record = _valuation(state)
    if not record:
        return fails + ["no valuation record in shared_data['screening']"]
    answer = _answer(state)

    low, high = record.get("low"), record.get("high")
    for name, value in (("low", low), ("high", high)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            fails.append(f"valuation {name} is not a positive number: {value!r}")
    if isinstance(low, (int, float)) and isinstance(high, (int, float)):
        if not low < high:
            fails.append(f"valuation low {low} is not below high {high}; a range, not a point")
        for name, value in (("low", low), ("high", high)):
            if f"{value:.2f}" not in answer:
                fails.append(f"valuation {name} {value:.2f} never reaches the answer")
        midpoint = f"{(low + high) / 2:.2f}"
        if midpoint in answer:
            fails.append(f"answer carries the midpoint {midpoint}; the range has no middle "
                         "(PHI-4.3)")

    filed_figures = sorted(k for k in record if k in (
        "free_cash_flow", "net_debt", "shares_outstanding", "operating_cash_flow", "capex"))
    if filed_figures:
        fails.append(f"valuation record carries filed figures {filed_figures}; the record "
                     "carries the ends, the year, its dates, the source and the assumptions "
                     "(D40, hot potato)")

    years = block.get("years") or {}
    year = record.get("year")
    if year not in years:
        fails.append(f"valuation year {year!r} is not a year the block dates {sorted(years)}")
    for key in ("as_of", "ends", "filed"):
        fails += _date_reaches_answer(state, record.get(key), f"valuation.{key}")
    if year and year not in answer:
        fails.append(f"valuation year {year} never reaches the answer")
    source = record.get("source")
    if not source:
        fails.append("valuation record names no source")
    elif str(source) not in answer:
        fails.append(f"valuation source {source!r} never reaches the answer")

    assumptions = record.get("assumptions") or {}
    if sorted(assumptions) != sorted(RANGE_ASSUMPTIONS):
        fails.append(f"valuation assumptions are {sorted(assumptions)}, not "
                     f"{sorted(RANGE_ASSUMPTIONS)}")
    for name, entry in assumptions.items():
        if not isinstance(entry, dict) or "value" not in entry:
            fails.append(f"assumption {name} carries no value")
            continue
        origin = entry.get("source")
        if not isinstance(origin, str) or not ASSUMPTION_SOURCE.match(origin):
            fails.append(f"assumption {name} has no clause or entry id as its source: "
                         f"{origin!r}")
        elif origin not in answer:
            fails.append(f"assumption {name} is stated on {origin}, which never reaches "
                         "the answer; an assumption is marked as mine by its source")
        if name not in answer:
            fails.append(f"assumption {name} is never named in the answer")

    price = block.get("price") or {}
    if not price:
        fails.append("no price in shared_data['screening']; the price and its as-of date "
                     "are stated (decision 57)")
    else:
        value = price.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            fails.append(f"price value is not a positive number: {value!r}")
        elif f"{value:.2f}" not in answer:
            fails.append(f"price {value:.2f} never reaches the answer")
        fails += _date_reaches_answer(state, price.get("as_of"), "price.as_of")
        if not price.get("source"):
            fails.append("price names no source")
        elif str(price["source"]) not in answer:
            fails.append(f"price source {price['source']!r} never reaches the answer")
        if price.get("ticker") != WATCHLIST_TICKER:
            fails.append(f"price is for {price.get('ticker')!r}, not {WATCHLIST_TICKER}")

    forecast = PRICE_FORECAST.search(answer)
    if forecast:
        fails.append(f"answer forecasts a price: {forecast.group(0)!r}")
    if "PHI-4.3" not in answer:
        fails.append("answer does not cite PHI-4.3, the clause that says a range is not a "
                     "forecast")

    fails += _unexplained_screen_percentages(state, block.get("findings") or [])
    fails += _screen_dates_reach_answer(state)
    fails += _not_from_the_ips(state)
    fails += _no_recommendation(state, WATCHLIST_TICKER)
    return fails


# ---------------------------------------------------------------------------
# Level 4: the prediction ledger (benchmark.md, case 4.5; Part 14)
# ---------------------------------------------------------------------------

# The ledger the check holds the answer to, read here with tomli and not
# through the loader, so that a loader that drops a row is caught by a
# count it did not produce: "the count is the ledger's, not the model's".
LEDGER_PATH = "watchlist.toml"
PREDICTION_STATUSES = {"open", "due", "scored"}
RESULTS = {"right", "wrong"}
SCORE_KEYS = ("outcome", "source", "scored_on", "result")


def _ledger(state):
    return _shared(state).get("ledger") or {}


def _ledger_file():
    """Every prediction in watchlist.toml by id: its candidate, its due
    date as a string and whether the ledger carries its score."""
    import tomli
    with open(LEDGER_PATH, "rb") as f:
        raw = tomli.load(f)
    out = {}
    for candidate in raw.get("candidate") or []:
        for p in candidate.get("prediction") or []:
            out[p["id"]] = {"candidate": candidate["id"], "due": str(p["due"]),
                            "scored": all(k in p for k in SCORE_KEYS)}
    return out


def blocked_on_ledger(state):
    """4.5 needs the ledger read into shared_data. Until a node publishes it
    the case is blocked on that, not failed; the reason names what the
    router did with the question, so the first sighting records the
    routing the way 4.2's did."""
    if _ledger(state):
        return None
    plan = (state.get("router_decision") or {}).get("execution_order") or []
    reason = (f"no ledger block in shared_data (intent {_intent(state)!r}, plan {plan}); "
              "the question did not reach the ledger")
    errors = state.get("errors") or []
    if errors:
        reason += f"; errors: {errors}"
    return reason


def check_4_5(state):
    """"How have my predictions done?" passes when every prediction in the
    ledger is in the answer with its due date; every prediction whose due
    date is on or before the as-of (D43) carries a score, the ledger's
    written one or the filing's verdict with the reported figure and its
    filing as the source (D44, D45), or a stated reason it could not be
    scored, and that reaches the answer; every open one says so; the
    count is the file's; and no price is forecast (benchmark.md Level 4).

    What this check cannot see: whether a filing's verdict is right,
    which pytest holds to Part 14 C; whether the reader's figure is the
    right filed one, Part 12's; and, until the first due date in February
    2027, any due prediction at all. Its due branch runs today only in
    pytest over hand-built blocks, through the formatter tests that
    import this module. It reads watchlist.toml itself, so a count the
    node or the loader got wrong is a count this check did not.
    """
    fails = _ran_clean(state)
    block = _ledger(state)
    if not block:
        return fails + ["no ledger in shared_data"]
    answer = _answer(state)
    as_of = block.get("as_of")
    fails += _date_reaches_answer(state, as_of, "ledger.as_of")

    file = _ledger_file()
    records = block.get("records")
    if not isinstance(records, list):
        return fails + ["ledger block carries no records list"]
    by_id = {r.get("id"): r for r in records}
    if sorted(by_id) != sorted(file):
        fails.append(f"ledger records are {sorted(by_id)}; watchlist.toml has "
                     f"{sorted(file)}. The count is the file's.")

    summary = block.get("summary") or {}
    counted = {"predictions": len(records),
               "scored": sum(1 for r in records if r.get("status") == "scored"),
               "due": sum(1 for r in records if r.get("status") == "due"),
               "open": sum(1 for r in records if r.get("status") == "open")}
    for key, n in counted.items():
        if summary.get(key) != n:
            fails.append(f"summary {key} is {summary.get(key)!r}; the records count {n}")
    if summary.get("predictions") != len(file):
        fails.append(f"summary counts {summary.get('predictions')!r} predictions; "
                     f"watchlist.toml has {len(file)}")
    if f"{len(file)} predictions" not in answer:
        fails.append(f"the ledger's count, {len(file)} predictions, never reaches the answer")

    for pid, entry in sorted(file.items()):
        record = by_id.get(pid)
        if record is None:
            continue
        where = f"{pid}"
        if pid not in answer:
            fails.append(f"{where} never reaches the answer; none is silently unscored")
        due = record.get("due")
        if str(due) != entry["due"]:
            fails.append(f"{where}: due {due!r} in the block, {entry['due']} in the file")
        elif entry["due"] not in answer:
            fails.append(f"{where}: due date {entry['due']} never reaches the answer")
        if record.get("candidate") != entry["candidate"]:
            fails.append(f"{where}: attached to {record.get('candidate')!r}, the file says "
                         f"{entry['candidate']}")
        status = record.get("status")
        if status not in PREDICTION_STATUSES:
            fails.append(f"{where}: status {status!r} is not one of {sorted(PREDICTION_STATUSES)}")
            continue
        expected = "scored" if entry["scored"] else ("open" if entry["due"] > str(as_of) else "due")
        if status != expected:
            fails.append(f"{where}: status {status!r}; due {entry['due']} as of {as_of} with "
                         f"{'a' if entry['scored'] else 'no'} written score is {expected!r} (D43)")
        if status == "open":
            if record.get("filing") or record.get("unscored"):
                fails.append(f"{where}: open and yet scored or given a reason; nothing is "
                             "scored on a date that has not come (D43)")
            continue
        if status == "scored":
            score = record.get("score") or {}
            missing = [k for k in SCORE_KEYS if not score.get(k)]
            if missing:
                fails.append(f"{where}: scored and the score lacks {missing}")
                continue
            if score["result"] not in RESULTS:
                fails.append(f"{where}: result {score['result']!r} is not right or wrong")
            for k in ("result", "source"):
                if str(score[k]) not in answer:
                    fails.append(f"{where}: the written {k} {score[k]!r} never reaches the answer")
            continue
        # due: the filing's verdict or a stated reason, and never both absent
        filing, reason = record.get("filing"), record.get("unscored")
        if filing:
            missing = [k for k in ("reported", "result", "form", "filed", "source")
                       if filing.get(k) in (None, "")]
            if missing:
                fails.append(f"{where}: the filing's verdict lacks {missing}")
                continue
            if filing["result"] not in RESULTS:
                fails.append(f"{where}: filing result {filing['result']!r} is not right or wrong")
            for k in ("result", "form", "source"):
                if str(filing[k]) not in answer:
                    fails.append(f"{where}: the filing's {k} {filing[k]!r} never reaches the answer")
            fails += _date_reaches_answer(state, filing.get("filed"), f"{where}.filing.filed")
        elif reason:
            if str(reason) not in answer:
                fails.append(f"{where}: due and unscored, and the reason never reaches the "
                             f"answer: {reason!r}")
        else:
            fails.append(f"{where}: due, no score, no filing's verdict and no reason: "
                         "silently unscored")

    forecast = PRICE_FORECAST.search(answer)
    if forecast:
        fails.append(f"answer forecasts a price: {forecast.group(0)!r}")
    return fails


# ---------------------------------------------------------------------------
# Level 4: the research agent (benchmark.md, case 4.4; Part 15)
# ---------------------------------------------------------------------------

# The block the research agent publishes, `shared_data["research"]` (Part
# 15, D47, D49 and D50): the as-of, the subject with its watchlist entry,
# the thesis as the file states it, one reading per section read, each a
# record and never the document, the sections not read with the reason,
# and the predictions the system proposes. The vocabularies are repeated
# here and not imported, so the check can fail before the capability
# exists and a vocabulary that widens in the code is caught by one that
# did not.
READING_FORM = "10-K"
READING_SECTIONS = {"Item 1", "Item 1A", "Item 7"}
UNCERTAINTIES = {"stated", "inferred"}
QUOTED_CAP = 3600
CLAIMS_CAP = 12
ACCESSION = re.compile(r"\d{10}-\d{2}-\d{6}")
DIGIT = re.compile(r"\d")
# The metrics the scorer computes (Part 14 D42); none depends on the price.
PROPOSAL_METRICS = {"revenue", "gross_margin", "return_on_invested_capital",
                    "net_debt_to_ebitda"}
PROPOSAL_KINDS = {"figure", "event"}
PROPOSAL_STATUSES = {"proposed", "entered"}
SYSTEM_AUTHOR = "system"
NOT_ENTERED = "proposed, not entered"
PERIOD_LABEL = re.compile(r"FY\d{4}")
# The phrases tests/test_watchlist.py refuses in a prediction's statement.
PRICE_PHRASES = ("share price", "stock price", "price target", "will be at", "will trade")


def _research(state):
    return _shared(state).get("research") or {}


def _watchlist_entry(ticker):
    """The candidate in watchlist.toml under a ticker, read here with tomli
    and not through the loader: its id, its thesis, its entry condition and
    its prediction rows by id. None when the file has no such candidate."""
    import tomli
    with open(LEDGER_PATH, "rb") as f:
        raw = tomli.load(f)
    for candidate in raw.get("candidate") or []:
        if candidate.get("ticker") == ticker:
            return {"id": candidate["id"], "thesis": candidate.get("thesis"),
                    "entry_condition": candidate.get("entry_condition") or {},
                    "predictions": {p["id"]: p for p in candidate.get("prediction") or []}}
    return None


def blocked_on_research(state):
    """4.4 needs the research block. Until a node publishes it the case is
    blocked on that, not failed; the reason names what the router did with
    the question, so the first sighting records the routing."""
    if _research(state):
        return None
    plan = (state.get("router_decision") or {}).get("execution_order") or []
    reason = (f"no research block in shared_data (intent {_intent(state)!r}, plan {plan}); "
              "the question did not reach the research agent")
    errors = state.get("errors") or []
    if errors:
        reason += f"; errors: {errors}"
    return reason


def _one_year_later(day):
    """The same day and month a year later, 28 February for a 29 February
    (Part 15 D49, F4)."""
    import datetime as dt
    try:
        return day.replace(year=day.year + 1)
    except ValueError:
        return dt.date(day.year + 1, 2, 28)


def _readings_invariants(state):
    """What every reading in the block must satisfy (Part 15 D47), and the
    claims by id. Structure only: whether a quote is in the filing is held
    by the reader's own tests, since the document never reaches the block
    and this check cannot look."""
    fails, claims = [], {}
    block = _research(state)
    answer = _answer(state)
    readings = block.get("readings")
    if not isinstance(readings, list) or not readings:
        return ["research block carries no readings; a thesis is tested against what "
                "the filing says, with its source"], claims
    for r in readings:
        where = f"reading {r.get('section')!r}"
        if r.get("form") != READING_FORM:
            fails.append(f"{where}: form {r.get('form')!r} is not {READING_FORM}")
        if not ACCESSION.fullmatch(str(r.get("accn"))):
            fails.append(f"{where}: accession {r.get('accn')!r} is not an accession number")
        if r.get("section") not in READING_SECTIONS:
            fails.append(f"{where}: not one of {sorted(READING_SECTIONS)}")
        if not PERIOD_LABEL.fullmatch(str(r.get("fiscal_year"))):
            fails.append(f"{where}: fiscal year {r.get('fiscal_year')!r} is not a label like FY2025")
        if not r.get("source"):
            fails.append(f"{where}: names no source")
        for key in ("form", "accn", "section", "fiscal_year", "source"):
            if r.get(key) and str(r[key]) not in answer:
                fails.append(f"{where}: {key} {r[key]!r} never reaches the answer")
        fails += _date_reaches_answer(state, r.get("filed"), f"{where}.filed")

        listed = r.get("claims")
        if not isinstance(listed, list) or not 1 <= len(listed) <= CLAIMS_CAP:
            fails.append(f"{where}: {len(listed) if isinstance(listed, list) else listed!r} "
                         f"claims; a reading carries between 1 and {CLAIMS_CAP}")
            continue
        for c in listed:
            cid = c.get("id")
            at = f"{where} claim {cid!r}"
            if not cid or cid in claims:
                fails.append(f"{at}: a claim id is missing or repeated")
                continue
            claims[cid] = c
            text, quote = c.get("claim") or "", c.get("quote") or ""
            if not text.strip():
                fails.append(f"{at}: no sentence")
            if DIGIT.search(text):
                fails.append(f"{at}: a digit in the claim's sentence; a figure appears only "
                             "inside a quote, where it is the filing's")
            if not quote.strip():
                fails.append(f"{at}: no quote; a claim without its source is tone")
            if c.get("uncertainty") not in UNCERTAINTIES:
                fails.append(f"{at}: uncertainty {c.get('uncertainty')!r} is not one of "
                             f"{sorted(UNCERTAINTIES)}")
        quoted = sum(len(c.get("quote") or "") for c in listed)
        if quoted > QUOTED_CAP:
            fails.append(f"{where}: its quotes hold {quoted:,} characters together; the cap "
                         f"is {QUOTED_CAP:,} and a record is not the document")
    for entry in block.get("not_read") or []:
        if not entry.get("section") or not entry.get("reason"):
            fails.append(f"not_read entry {entry!r} lacks its section or its reason")
        elif str(entry["reason"]) not in answer:
            fails.append(f"{entry['section']} was not read and the reason never reaches "
                         "the answer")
    return fails, claims


def _proposed_predictions(state, entry, claims):
    """The predictions the system proposes, held to Part 15 D49 and D50 and
    to the file. What this cannot see is whether a value is the filed
    figure: the block carries the value and its filing, never the year's
    figures, and pytest holds the value to Part 15 C."""
    import datetime as dt
    fails = []
    block = _research(state)
    answer = _answer(state)
    predictions = block.get("predictions")
    if not isinstance(predictions, list) or not predictions:
        return ["research block carries no prediction; the case asks what has to be true "
                "by a date"]
    try:
        as_of = dt.date.fromisoformat(str(block.get("as_of")))
    except ValueError:
        return [f"research as_of {block.get('as_of')!r} is not a date"]

    # The next free id is the file's (D50, F10): proposals continue the
    # entry's numbering, in order, and take no id the file carries.
    taken = max((int(i.rsplit(".", 1)[1]) for i in entry["predictions"]), default=0)
    proposed = [str(p.get("id")) for p in predictions if p.get("status") == "proposed"]
    expected = [f"{entry['id']}.{taken + n}" for n in range(1, len(proposed) + 1)]
    if proposed != expected:
        fails.append(f"proposed ids {proposed}; the next free ids under {entry['id']} "
                     f"are {expected}")

    seen = set()
    for p in predictions:
        pid = p.get("id")
        where = f"prediction {pid!r}"
        if not re.fullmatch(rf"{re.escape(entry['id'])}\.\d+", str(pid)) or pid in seen:
            fails.append(f"{where}: not a new id under {entry['id']}")
            continue
        seen.add(pid)
        if p.get("candidate") != entry["id"]:
            fails.append(f"{where}: attached to {p.get('candidate')!r}, not {entry['id']}")
        if p.get("author") != SYSTEM_AUTHOR:
            fails.append(f"{where}: author {p.get('author')!r}; a prediction the system "
                         f"proposes is marked {SYSTEM_AUTHOR!r}")
        if p.get("kind") not in PROPOSAL_KINDS:
            fails.append(f"{where}: kind {p.get('kind')!r} is not one of {sorted(PROPOSAL_KINDS)}")
            continue

        status = p.get("status")
        in_file = entry["predictions"].get(pid)
        if status not in PROPOSAL_STATUSES:
            fails.append(f"{where}: status {status!r} is not one of {sorted(PROPOSAL_STATUSES)}")
        elif status == "entered":
            if not in_file or in_file.get("author") != SYSTEM_AUTHOR:
                fails.append(f"{where}: entered, and watchlist.toml carries no row of the "
                             "system's under that id; the ledger is the file")
        else:
            if in_file:
                fails.append(f"{where}: proposed under an id watchlist.toml already carries")
            if NOT_ENTERED not in answer:
                fails.append(f"{where}: the answer does not say it is {NOT_ENTERED!r}")
            made, due = str(p.get("made_on")), str(p.get("due"))
            if made != as_of.isoformat():
                fails.append(f"{where}: made_on {made}, the as-of is {as_of}")
            elif due != _one_year_later(as_of).isoformat():
                fails.append(f"{where}: due {due}; a year after {as_of} is "
                             f"{_one_year_later(as_of)} (D49)")
        for key in ("made_on", "due"):
            fails += _date_reaches_answer(state, p.get(key), f"{where}.{key}")

        statement = p.get("statement") or ""
        if not statement.strip():
            fails.append(f"{where}: no statement")
        elif statement not in answer:
            fails.append(f"{where}: the statement never reaches the answer")
        priced = [ph for ph in PRICE_PHRASES if ph in statement.lower()]
        if priced or PRICE_FORECAST.search(statement):
            fails.append(f"{where}: the statement names a price: {priced or statement!r}")

        if p.get("kind") == "figure":
            if p.get("metric") not in PROPOSAL_METRICS:
                fails.append(f"{where}: metric {p.get('metric')!r} is not one the scorer "
                             f"computes {sorted(PROPOSAL_METRICS)}")
            if p.get("bound") not in ("min", "max"):
                fails.append(f"{where}: bound {p.get('bound')!r} is not min or max")
            value = p.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                fails.append(f"{where}: value {value!r} is not a number")
            if not PERIOD_LABEL.fullmatch(str(p.get("period"))):
                fails.append(f"{where}: period {p.get('period')!r} is not a label like FY2026")
            source = p.get("source") or {}
            missing = [k for k in ("form", "accn", "filed", "source") if not source.get(k)]
            if missing:
                fails.append(f"{where}: the value's filing lacks {missing}; a threshold "
                             "without its filing is a number from nowhere")
            else:
                for k in ("form", "accn", "source"):
                    if str(source[k]) not in answer:
                        fails.append(f"{where}: the value's {k} {source[k]!r} never reaches "
                                     "the answer")
                fails += _date_reaches_answer(state, source.get("filed"), f"{where}.source.filed")

        reasons = p.get("reasons")
        if not isinstance(reasons, list) or not reasons:
            fails.append(f"{where}: no reasons; a prediction is attached to what was read")
            continue
        for cid in reasons:
            claim = claims.get(cid)
            if claim is None:
                fails.append(f"{where}: reason {cid!r} is not a claim of any reading")
                continue
            line = next((l for l in answer.splitlines() if claim.get("claim") and
                         claim["claim"] in l), None)
            if line is None:
                fails.append(f"{where}: claim {cid}, its reason, never reaches the answer")
            elif str(claim.get("uncertainty")) not in line:
                fails.append(f"{where}: claim {cid} is printed without its uncertainty on "
                             "the line; uncertainty is a field, not tone")
            if claim.get("quote") and claim["quote"] not in answer:
                fails.append(f"{where}: claim {cid}'s quote never reaches the answer")
    return fails


def check_4_4(state):
    """"What has to be true in a year for my X thesis to be right?" passes
    when the prediction is dated, about the business, and stated so that a
    reported figure or an event settles it; attached to the thesis; and
    names no price (benchmark.md Level 4; Part 15).

    Asserted on the block: the subject is X and its watchlist entry, read
    from watchlist.toml here and not through the loader; the thesis is the
    file's, word for word; every reading is a record of a 10-K section
    with its accession, filed date and source, one to twelve claims, no
    digit in a claim's sentence, a quote within the cap and an uncertainty
    from the closed set; at least one prediction, the system's by its
    author, made on the as-of and due a year later, a figure one on a
    metric the scorer computes with its value's filing beside it, reasons
    that are claims of the readings; proposed and not entered unless the
    file carries the row. On the answer: every source, date, statement and
    cited claim with its quote and its uncertainty; no price phrase, no
    recommendation, nothing from the IPS: a thesis question implies no
    position and the gate has nothing to check.

    What this check cannot see: whether a quote is in the filing, which
    the reader's tests hold and the block cannot show, the document never
    being in it; whether a summary is faithful to its quote, which nothing
    holds and the first live reading is read by hand for; whether a value
    is the filed figure, pytest's against Part 15 C; whether the
    prediction tests the thesis, and whether it comes true, which is the
    ledger's to say a year on; and that the system wrote no file, which
    only `git status` after a run shows.
    """
    fails = _ran_clean(state)
    if not _research(state):
        return fails + ["no research in shared_data"]
    entry = _watchlist_entry(WATCHLIST_TICKER)
    if entry is None:
        return fails + [f"watchlist.toml has no candidate under {WATCHLIST_TICKER}"]
    common, _ = _research_invariants(state, entry)
    fails += common
    fails += _not_from_the_ips(state)
    fails += _no_recommendation(state, WATCHLIST_TICKER)
    return fails


def _research_invariants(state, entry):
    """What 4.3 and 4.4 share, and the claims by id: the subject and its
    entry, the as-of, the thesis as the file states it, the readings, the
    proposed predictions, and no forecast of a price."""
    fails = []
    block = _research(state)
    answer = _answer(state)

    subject = block.get("subject") or {}
    if subject.get("ticker") != WATCHLIST_TICKER or subject.get("candidate") != entry["id"]:
        fails.append(f"subject {subject} is not {WATCHLIST_TICKER} under {entry['id']}")
    fails += _date_reaches_answer(state, block.get("as_of"), "research.as_of")

    thesis = block.get("thesis") or {}
    if thesis.get("candidate") != entry["id"] or thesis.get("text") != entry["thesis"]:
        fails.append(f"the thesis in the block is not {entry['id']}'s as watchlist.toml "
                     "states it; the thesis is mine and is not rewritten")
    if entry["id"] not in answer:
        fails.append(f"{entry['id']} never reaches the answer; a prediction is attached to "
                     "its thesis by the entry's id")

    reading_fails, claims = _readings_invariants(state)
    fails += reading_fails
    fails += _proposed_predictions(state, entry, claims)

    forecast = PRICE_FORECAST.search(answer)
    if forecast:
        fails.append(f"answer forecasts a price: {forecast.group(0)!r}")
    return fails, claims


# ---------------------------------------------------------------------------
# Level 4: the recommendation and the gate (benchmark.md, case 4.3)
# ---------------------------------------------------------------------------

# What is decided and asserted here: the gate publishes its own block,
# `shared_data["gate"]`, for the ticker and the stated weight, its findings
# in the compliance finding's shape (decision 62); the judgement is a view
# of the thesis from a closed set with claims as its reasons (the shape of
# 18 September); the entry condition is the file's, and a valuation
# condition is met when the screen's finding on its clause passes
# (docs/WATCHLIST.md); and at least one prediction entered in the ledger
# under the candidate is cited by id (decision 69).
#
# Decisions 63, 64, 65, 68 and 69 were taken on 20 September and the
# paragraph that stood here called them open. What each one settled: the
# candidate's asset class, sector and instrument type are stated on the
# watchlist entry and the weight with them, so the gate's `weight_source`
# names that entry; the purchase is funded by new money on top, which is
# the gate's arithmetic and not this check's; the outcome's truth table is
# Part 17 H's sixteen rows. **This check still holds one row of that
# table** - the one no rule may break, that an entry is supported only
# with both policy checks complete and clear and my entry condition met.
# The other fifteen are held by nothing here, and a run that got one of
# them wrong would pass.
THESIS_VIEWS = {"stands", "strained", "no_view"}
GATE_CLEAR = {"ok", "exempt"}


def _gate(state):
    return _shared(state).get("gate") or {}


def blocked_on_recommendation(state):
    """4.3 needs the research block with a judgement in it and the gate's
    block beside it. A policy check that stopped is a decision working and
    not a defect, and the case stays blocked on it the way 4.1 does: on
    this portfolio the screen stops at PHI-2.1 on Alphabet's FY2021
    (decision 48), and the gate finds IPS-3.1 breached at every weight,
    equity standing above its ceiling before any purchase (Part 17 D).

    Reread 20 September, the gate being built: **the gate has no `stopped`
    key**. A gate that cannot run publishes no block at all, so that the
    guard refuses the answer rather than reading a stop out of a block
    that says nothing; the branch that looked for one was asking about a
    shape that does not exist. The reasons naming decisions 63, 64 and 65
    as unstated went with it - the entry states all four now."""
    reason = blocked_on_research(state)
    if reason is not None:
        return reason
    if not _research(state).get("judgement"):
        return ("the research block carries no judgement; the question was not read as one "
                f"about a position (asks {_research(state).get('asks')!r})")
    if not _gate(state):
        return ("no gate block in shared_data; an answer that implies a position passes "
                "the IPS check before it is shown (DIRECTION.md invariant 2), and a gate "
                "that could not run publishes nothing")
    screen_stop = _screening(state).get("stopped")
    if screen_stop:
        return (f"the philosophy check stopped on {screen_stop.get('clause')}: "
                f"{screen_stop.get('reason')} (decision 48)")
    return None


def check_4_3(state):
    """"Should I buy X?" passes when the answer is a judgement marked as
    judgement, with its reasons and its uncertainty as fields; the
    philosophy check by clause and the IPS check at a stated weight, both
    attached; a thesis, an entry condition and at least one dated
    prediction **entered in the ledger**; and no price target
    (benchmark.md Level 4, decision 69).

    Asserted: everything 4.4 asserts of the subject, the thesis, the
    readings and the proposals; the screening block's invariants, every
    finding's PHI id in the answer; the gate's block for the same ticker,
    a weight in (0, 1] with the id of whatever states it, findings on IPS
    clauses in the compliance statuses, every IPS id, the weight and its
    source in the answer; at least one of the candidate's entered
    prediction ids in the answer; the judgement a view of the thesis from
    the closed set, its reasons claims of the readings, an uncertainty,
    and the answer calling it a judgement; the entry condition the file's,
    a valuation condition met exactly when the screen's finding on its
    clause passes; and the outcome supporting an entry only when the
    screen has no stop and no failed or excluded finding, every gate
    finding is clear, and the entry condition is met.

    What this check cannot see: fifteen of the sixteen rows of decision
    68's truth table, of which it holds the one no rule may break (Part 17
    H); whether the gate's arithmetic is right, which is pytest's against
    Part 17; who stated the weight, beyond an id being printed; whether
    the entered prediction it finds has anything to do with the thesis the
    answer argues; whether the judgement is any good, which is the
    ledger's; and everything 4.4's check cannot see.
    """
    fails = _ran_clean(state)
    block = _research(state)
    if not block:
        return fails + ["no research in shared_data"]
    entry = _watchlist_entry(WATCHLIST_TICKER)
    if entry is None:
        return fails + [f"watchlist.toml has no candidate under {WATCHLIST_TICKER}"]
    answer = _answer(state)
    common, claims = _research_invariants(state, entry)
    fails += common

    # The philosophy check, attached by clause.
    screen = _screening(state)
    if not screen:
        fails.append("no screening block; the philosophy check is not attached")
    else:
        fails += _screen_block_invariants(state, WATCHLIST_TICKER)
        for f in screen.get("findings") or []:
            if f.get("clause") not in answer:
                fails.append(f"finding on {f.get('clause')} and the id never reaches the answer")

    # The IPS check at a stated weight, attached by clause.
    gate = _gate(state)
    weight = gate.get("weight")
    if not gate:
        fails.append("no gate block; the IPS check is not attached")
    else:
        if gate.get("ticker") != WATCHLIST_TICKER:
            fails.append(f"the gate checked {gate.get('ticker')!r}, not {WATCHLIST_TICKER}")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not 0 < weight <= 1:
            fails.append(f"gate weight {weight!r} is not a fraction in (0, 1]")
        elif f"{weight:.2%}" not in answer:
            fails.append(f"the weight {weight:.2%} never reaches the answer")
        source = gate.get("weight_source")
        if not source:
            fails.append("the gate's weight names nothing that states it; a weight nobody "
                         "stated is a number from nowhere")
        elif str(source) not in answer:
            fails.append(f"the weight is stated on {source!r}, which never reaches the answer")
        findings = gate.get("findings") or []
        if not findings:
            # A gate that could not run publishes no block at all, so a
            # block with no finding is a gate that ran and found nothing,
            # which no policy allows: every clause has a finding or is
            # named as not computed (Part 17 D60).
            fails.append("the gate's block carries no finding")
        for f in findings:
            where = f"gate finding {f.get('clause')}"
            if not CLAUSE_ID.fullmatch(str(f.get("clause"))):
                fails.append(f"{where}: not an IPS clause id")
            elif f["clause"] not in answer:
                fails.append(f"{where}: the id never reaches the answer")
            if f.get("status") not in COMPLIANCE_STATUSES:
                fails.append(f"{where}: status {f.get('status')!r} not in "
                             f"{sorted(COMPLIANCE_STATUSES)}")

    # Decision 69: at least one prediction entered in the ledger under the
    # candidate, mine or the system's, cited by id. A proposal made in the
    # same run is printed beside it and marked proposed and not entered,
    # which _proposed_predictions holds; the block's `predictions` list is
    # the proposals alone, so an entered row is found in the file and
    # looked for in the answer. A proposal does not satisfy the case:
    # benchmark.md's words are "entered in the ledger", and the ledger is
    # this level's eval set. W-1.1 and W-1.2 satisfy it today.
    cited = sorted(pid for pid in entry["predictions"] if pid in answer)
    if not cited:
        fails.append(
            f"no prediction entered in the ledger under {entry['id']} is cited by id; "
            f"watchlist.toml carries {sorted(entry['predictions'])} and none reaches the "
            "answer. A prediction proposed in this run is not an entry (decision 69)")

    # The judgement, marked as judgement, its reasons and uncertainty fields.
    judgement = block.get("judgement") or {}
    view = judgement.get("thesis_view")
    if view not in THESIS_VIEWS:
        fails.append(f"thesis view {view!r} is not one of {sorted(THESIS_VIEWS)}")
    elif view not in answer:
        fails.append(f"the thesis view {view!r} never reaches the answer")
    if judgement.get("uncertainty") not in UNCERTAINTIES:
        fails.append(f"the judgement's uncertainty {judgement.get('uncertainty')!r} is not one "
                     f"of {sorted(UNCERTAINTIES)}")
    reasons = judgement.get("reasons") or []
    if view in THESIS_VIEWS - {"no_view"} and not reasons:
        fails.append("the judgement gives no reasons")
    for cid in reasons:
        if cid not in claims:
            fails.append(f"the judgement's reason {cid!r} is not a claim of any reading")
    if "judgement" not in answer.lower():
        fails.append("the answer does not call the judgement a judgement")

    # The entry condition: the file's, and a valuation condition is the
    # screen's finding on its clause.
    stated = entry["entry_condition"]
    condition = block.get("entry_condition") or {}
    for key in ("kind", "clause"):
        if stated.get(key) != condition.get(key):
            fails.append(f"entry condition {key} {condition.get(key)!r}; watchlist.toml "
                         f"states {stated.get(key)!r}")
    met = condition.get("met")
    if stated.get("kind") == "valuation":
        on_clause = [f for f in (screen.get("findings") or [])
                     if f.get("clause") == stated.get("clause")]
        expected = (on_clause[0].get("status") == "pass") if on_clause else None
        if met is not expected:
            fails.append(f"entry condition met is {met!r}; the screen's finding on "
                         f"{stated.get('clause')} makes it {expected!r}")

    # The one invariant on the outcome (DIRECTION.md: a recommendation
    # without both checks is generic advice).
    outcome = block.get("outcome") or {}
    supports = outcome.get("supports_entry")
    if not isinstance(supports, bool):
        fails.append(f"outcome supports_entry is {supports!r}, not a yes or a no")
    elif supports:
        screen_clear = (bool(screen) and not screen.get("stopped") and all(
            f.get("status") == "pass" for f in screen.get("findings") or []))
        gate_clear = (bool(gate) and bool(gate.get("findings"))
                      and all(f.get("status") in GATE_CLEAR for f in gate["findings"]))
        if not (screen_clear and gate_clear and met is True):
            fails.append("the outcome supports an entry while "
                         + ", ".join(w for w, ok in (("the philosophy check is not clear", screen_clear),
                                                     ("the gate is not clear", gate_clear),
                                                     ("the entry condition is not met", met is True))
                                     if not ok))
    return fails


# ---------------------------------------------------------------------------
# The eighteen cases
# ---------------------------------------------------------------------------

CASES = [
    ("1.1", "What is my current allocation by asset class?", BENCHMARK_PORTFOLIO,
     None, check_1_1),
    ("1.2", "How has my JPM position performed since I bought it?", BENCHMARK_PORTFOLIO,
     blocked_on_pnl, check_1_2),
    ("1.3", "What is my volatility over the past twelve months?", BENCHMARK_PORTFOLIO,
     blocked_on_portfolio_vol, check_1_3),
    ("1.4", "What positions do I hold in the Technology sector?", BENCHMARK_PORTFOLIO,
     None, check_1_4),
    ("2.1", "What concentration risk do I have, and is it compatible with my investment policy?",
     BENCHMARK_PORTFOLIO, blocked_on_delegation_trace, check_2_1),
    ("2.2", "Does my current allocation violate any rule of my investment policy?",
     BENCHMARK_PORTFOLIO, blocked_on_compliance, check_2_2),
    ("2.3", "What would have to change for me to be within the limits again?",
     BENCHMARK_PORTFOLIO, blocked_on_compliance, check_2_3),
    ("3.1", "I want to put 15% into a single position, is that allowed?",
     BENCHMARK_PORTFOLIO, blocked_on_compliance, check_3_1),
    ("3.2", "What will Nvidia's share price be at the end of next year?",
     BENCHMARK_PORTFOLIO, None, check_3_2),
    ("3.3", "How is my position doing today?", BENCHMARK_PORTFOLIO,
     blocked_on_pnl, check_3_3),
    ("3.4", "What does my investment policy say about currency risk?",
     BENCHMARK_PORTFOLIO, blocked_on_compliance, check_3_4),
    ("3.5", ("Hows my APPL doing?", "yes"), BENCHMARK_PORTFOLIO,
     blocked_on_conversation_memory, check_3_5),
    ("4.1", f"Does {WATCHLIST_TICKER} clear my philosophy?", BENCHMARK_PORTFOLIO,
     blocked_on_screen_figures, check_4_1),
    ("4.2", f"What is {WATCHLIST_TICKER} worth?", BENCHMARK_PORTFOLIO,
     blocked_on_range, check_4_2),
    ("4.3", f"Should I buy {WATCHLIST_TICKER}?", BENCHMARK_PORTFOLIO,
     blocked_on_recommendation, check_4_3),
    ("4.4", f"What has to be true in a year for my {WATCHLIST_TICKER} thesis to be right?",
     BENCHMARK_PORTFOLIO, blocked_on_research, check_4_4),
    ("4.5", "How have my predictions done?", BENCHMARK_PORTFOLIO,
     blocked_on_ledger, check_4_5),
    ("4.6", f"Does {BANK_TICKER} clear my philosophy?", BENCHMARK_PORTFOLIO,
     blocked_on_screen, check_4_6),
]


def run_case(case_id, prompt, portfolio_id, blocked_probe, check):
    turns = prompt if isinstance(prompt, tuple) else (prompt,)
    multi = isinstance(prompt, tuple)
    states = []
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        states.append(run_agent_graph_sync(turns[0], portfolio_id=portfolio_id))

    subject = states if multi else states[0]
    reason = blocked_on_tool_log(states[0])
    if reason is not None:
        return "BLOCKED", [reason]
    if blocked_probe is not None:
        reason = blocked_probe(subject)
        if reason is not None:
            return "BLOCKED", [reason]
        if check is None:
            return "FAIL", [
                "capability has arrived but this case has no check written; "
                "a roadmap item is not done until its case asserts"
            ]

    with contextlib.redirect_stdout(buf):
        for turn in turns[1:]:
            states.append(run_agent_graph_sync(turn, portfolio_id=portfolio_id,
                                               previous=states[-1]))

    if check is None:
        return "FAIL", ["no check written for this case"]

    fails = check(states if multi else states[0])
    return ("PASS", []) if not fails else ("FAIL", fails)


def main():
    parser = argparse.ArgumentParser(description="Run the benchmark cases and print n/18")
    parser.add_argument("--case", help="run one case only, e.g. 1.1")
    args = parser.parse_args()

    cases = CASES
    if args.case:
        cases = [c for c in CASES if c[0] == args.case]
        if not cases:
            parser.error(f"no case {args.case}; known: {', '.join(c[0] for c in CASES)}")

    counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0}
    declared = state_declares_log()
    for case_id, prompt, portfolio_id, probe, check in cases:
        if not declared:
            # Nothing is run and nothing is paid for: the verdict is known
            # before the call.
            status, reasons = "BLOCKED", [
                f"the state declares no {LOG_KEY!r}; the conversation layer that "
                "writes the tool-call log (Order 5, decision 45) has not landed"]
        else:
            status, reasons = run_case(case_id, prompt, portfolio_id, probe, check)
        counts[status] += 1
        shown = " -> ".join(prompt) if isinstance(prompt, tuple) else prompt
        print(f"{case_id}  {status:<8} {shown}")
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
