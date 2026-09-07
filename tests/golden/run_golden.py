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
    ("What is my current allocation by asset class?", 1),
    ("What is my volatility over the past twelve months?", 1),
    ("Should I rebalance my portfolio?", 1),
    ("What is the risk of my portfolio?", 1),
    ("What positions do I hold in the Technology sector?", 2),
    ("Analyze ZZZZFAKE for me", None),
    ("help", None),
    ("Should I buy Nvidia?", 1),
    # Near-miss in-scope queries: a held ticker named without "my". Added
    # 8 September after the router refused the first of them in the CLI.
    # 3.2 cannot see a router that refuses too much; these can.
    ("How much did AAPL gain today?", 3),
    ("Is my AAPL position too big?", 3),
]


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
        print()


if __name__ == "__main__":
    main()
