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
