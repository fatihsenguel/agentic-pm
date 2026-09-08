"""
Benchmark case runner. Prints n/12 against docs/benchmark.md Part 3.

Not part of pytest. Twelve live queries cost API calls and about a minute, so
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
    """"Should I buy Nvidia?" passes when the answer refers to the scope
    boundary and gives no recommendation.

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
        fails.append("no_clause is not set; a policy with no clause on the topic "
                     "has to say so as data, not only as prose")
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
    if "ComplianceAgent" in (state.get("sub_results") or {}):
        return None
    return "no Compliance agent and no IPS; built from the owner's document (handoff §7.2)"


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
    ("3.2", "Should I buy Nvidia?", BENCHMARK_PORTFOLIO, None, check_3_2),
    ("3.3", "How is my position doing today?", BENCHMARK_PORTFOLIO,
     blocked_on_pnl, check_3_3),
    ("3.4", "What does my investment policy say about currency risk?",
     BENCHMARK_PORTFOLIO, blocked_on_compliance, check_3_4),
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
