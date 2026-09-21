"""
Golden set runner.

Prints only stable decision fields (no prices, timestamps or quota counters)
so runs can be diffed against tests/golden/expected.txt.

Usage:
    python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
    diff tests/golden/expected.txt /tmp/golden_now.txt
"""
import contextlib
import io

from agents.graph import run_agent_graph_sync

QUERIES = [
    ("What is the current market regime?", None),
    ("Get me the last 1 year of prices for SPY and TLT", None),
    ("Optimize a portfolio of SPY, TLT and GLD for maximum Sharpe ratio", None),
    ("What is my current allocation by asset class?", 3),
    ("What is my volatility over the past twelve months?", 3),
    ("Should I rebalance my portfolio?", 3),
    ("What is the risk of my portfolio?", 3),
    ("What positions do I hold in the Technology sector?", 3),
    ("Analyze ZZZZFAKE for me", None),
    ("help", None),
    ("Should I buy Nvidia?", 3),
    # Near-miss in-scope queries: a held ticker named without "my". Added
    # 8 September after the router refused the first of them in the CLI.
    # 3.2 cannot see a router that refuses too much; these can.
    ("How much did AAPL gain today?", 3),
    # The diagnostic beside it (KNOWN_GAPS, pending decision 5): the same
    # held ticker without the day, so the in-scope bare-ticker question has
    # a line of its own. Extraction owns the ticker; the model decides the
    # intent; "today" next to a change verb is a span the vocabulary lacks.
    ("How much has AAPL gained?", 3),
    ("Is my AAPL position too big?", 3),
    # Diagnostics for the "too big" flip (KNOWN_GAPS, 8 September): the
    # policy word without "too big", and the concentration word without the
    # policy. No prompt change; if both are stable, the flip is the rule 6 /
    # rule 7 collision alone.
    ("Is my AAPL position within my policy's limits?", 3),
    ("Is AAPL too concentrated?", 3),
    # The philosophy check (decision 29), on a held ticker: before the intent
    # existed this sentence went to the IPS portfolio check (runner 4.6,
    # 16 September). The line pins that the philosophy and the IPS are two
    # intents. Runs the node live: the fetches are under their intervals.
    ("Does JPM clear my philosophy?", 3),
    # The valuation range (case 4.2, Part 11, decision 57), on the watchlist's
    # first candidate. Added 18 September at out_of_scope, where the router
    # put it before the registry described a valuation; the line pins what
    # the registry's correction moves. Routed research it runs the node
    # live: the price fetch is under its interval, the filings fetches too.
    ("What is GOOGL worth?", 3),
    # The prediction ledger (case 4.5, Part 14), naming no company. Added
    # 18 September at clarification_needed, where the runner's first
    # sighting found it before any intent described the ledger; the line
    # pins what the registry's row moves. Routed to the ledger it runs the
    # node live: today nothing is due and nothing is fetched.
    ("How have my predictions done?", 3),
    # The thesis question (case 4.4, Part 15, decision 66), on the
    # watchlist's first candidate. Added 19 September at out_of_scope,
    # where four of five sightings found it, the fifth clarification_needed;
    # the line pins what the routing of decision 66 moves. Routed to the
    # research agent it runs the screen and the research node live: a
    # section not yet read is one request to the stronger model, cached
    # after, and the proposal is one request on every run.
    ("What has to be true in a year for my GOOGL thesis to be right?", 3),
    # The buy question about a company that is a candidate (case 4.3,
    # decision 68), sighted 21 September before the line was written. The
    # routing is line 11's exactly: the same intent, the same four agents,
    # and the two differ in the error count alone, 0 here against 2 where
    # the company is on no entry. What this line pins is that the candidate
    # path still reaches the research agent without an error. It cannot see
    # the asks parameter, so a change that answered the thesis question here
    # would leave all five fields standing (KNOWN_GAPS). Routed to the
    # research agent it runs the screen and the three cached readings, and
    # asks the stronger model twice on every run: the proposal and the view.
    ("Should I buy GOOGL?", 3),
]


def retries(state):
    """How many router attempts the schema rejected before this decision.

    Each rejection reaches state["warnings"] as "Validation: Attempt N: ..."
    (router_node, since the attempts were carried into the state). A routing
    that was rejected and repaired back to the pinned plan prints the same
    five fields as one accepted first time; this is the field that tells them
    apart. Printed only when nonzero, so a line that routes first time is
    unchanged. JSON-parse failures and ticker errors carry no "Attempt"
    prefix and are not counted here.
    """
    return sum(
        1 for w in state.get("warnings") or []
        if w.startswith("Validation: Attempt ")
    )


def main():
    for q, pid in QUERIES:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r = run_agent_graph_sync(q, portfolio_id=pid)
        d = r.get("router_decision") or {}
        print(f"Q: {q} | pid={pid}")
        print(f"  intent: {d.get('intent')}")
        print(f"  plan:   {d.get('execution_order')}")
        print(f"  period: {(d.get('parameters') or {}).get('period')}")
        print(f"  agents_run: {sorted((r.get('sub_results') or {}).keys())}")
        print(f"  errors: {len(r.get('errors') or [])}")
        if retries(r):
            print(f"  retries: {retries(r)}")
        print()


if __name__ == "__main__":
    main()
