"""
Exploratory CLI for the agent graph.

Roadmap 0.3. The golden set answers "did anything change"; this answers
"what is it actually doing". Both are needed.

Runs against the graph via run_agent_graph_sync — NOT against the
create_*_agent factories, which is what the deleted multi_agent_cli.py did
and why it bypassed routing entirely.

Usage:
    python -m agents.cli                # or: python src/agents/cli.py
    python src/agents/cli.py --portfolio 1

Commands:
    :p <id>     switch portfolio (:p with no id clears it)
    :v          toggle verbose (full shared_data and sub_result payloads)
    :r          show the last raw state dict
    :q          quit
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Match tests/conftest.py: absolute path to src/, so this works whether or not
# the package is pip-installed into the active venv.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.graph import run_agent_graph_sync


DIV = "-" * 72


def _fmt(value, limit=None):
    """Render a value for the console, truncating unless limit is None."""
    if isinstance(value, (dict, list)):
        try:
            text = json.dumps(value, default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            text = repr(value)
    else:
        text = str(value)
    if limit is not None and len(text) > limit:
        return text[:limit] + f"... [{len(text)} chars]"
    return text


def show(state, elapsed, verbose, question, seen):
    """Print the routing decision, what ran, and the answer.

    seen maps an answer body to the first question that produced it, so a
    synthesizer returning boilerplate for every query is detectable.
    """
    limit = None if verbose else 200

    decision = state.get("router_decision") or {}
    print(f"\n{DIV}")
    print("ROUTING")
    print(f"  intent      : {decision.get('intent')}")
    print(f"  confidence  : {decision.get('confidence')}")
    print(f"  plan        : {decision.get('execution_order')}")
    print(f"  parameters  : {_fmt(decision.get('parameters') or {}, limit)}")
    if decision.get("reasoning"):
        print(f"  reasoning   : {_fmt(decision['reasoning'], limit)}")
    if decision.get("clarification_question"):
        print(f"  asked back  : {decision['clarification_question']}")

    sub_results = state.get("sub_results") or {}
    print("\nAGENTS RUN")
    if not sub_results:
        print("  (none — router answered directly or nothing executed)")
    for name, result in sub_results.items():
        ok = result.get("success") if isinstance(result, dict) else None
        rtype = result.get("result_type") if isinstance(result, dict) else None
        print(f"  {name}: success={ok} type={rtype}")
        if isinstance(result, dict):
            if result.get("message"):
                print(f"      message: {_fmt(result['message'], limit)}")
            if result.get("data") is not None:
                print(f"      data:    {_fmt(result['data'], limit)}")

    # Plan vs reality. A plan that lists agents which never ran is bug 7's
    # shape: the router produced a correct plan and nothing consumed it.
    planned = decision.get("execution_order") or []
    missing = [a for a in planned if a not in sub_results]
    if missing:
        print(f"\n  !! PLANNED BUT DID NOT RUN: {missing}")

    shared = state.get("shared_data") or {}
    print("\nSHARED_DATA")
    if not shared:
        print("  (empty)")
    for key, value in shared.items():
        print(f"  {key}: {_fmt(value, limit)}")

    errors = state.get("errors") or []
    warnings = state.get("warnings") or []
    if errors:
        print(f"\nERRORS ({len(errors)})")
        for e in errors:
            print(f"  - {_fmt(e, limit)}")
    if warnings:
        print(f"\nWARNINGS ({len(warnings)})")
        for w in warnings:
            print(f"  - {_fmt(w, limit)}")

    answer = state.get("final_response")
    print(f"\n{DIV}")
    print("ANSWER")
    if answer is None:
        print("  <no final_response set>")
    elif not answer.strip():
        print("  <EMPTY STRING>")
    else:
        print(answer)

    # benchmark.md Part 3b: a response that answers nothing is a failure, not a
    # partial pass. The golden set cannot see this, so check it here.
    #
    # An earlier version skipped lines starting with #, ** or = and called what
    # remained the body. "DataAgent: ✓" survives that filter, so the check
    # missed the exact case it was written for. Two better signals:
    if answer:
        # 1. Numbers exist in shared_data but none reached the answer.
        if not any(c.isdigit() for c in answer):
            if any(c.isdigit() for c in _fmt(shared, None)):
                print("\n  !! NO NUMBERS IN ANSWER while shared_data has them"
                      " — Part 3b failure")

        # 2. The same text came back for a different question.
        prior = seen.get(answer.strip())
        if prior and prior != question:
            print(f"\n  !! IDENTICAL ANSWER to an earlier, different question:"
                  f"\n     {prior!r}")
        seen.setdefault(answer.strip(), question)

    print(f"\n{DIV}")
    print(f"steps={state.get('execution_step')}  "
          f"request_id={state.get('request_id')}  "
          f"{elapsed:.1f}s")
    print(DIV)


def main():
    parser = argparse.ArgumentParser(description="Exploratory CLI for the agent graph")
    parser.add_argument("--portfolio", type=int, default=None,
                        help="portfolio_id held across queries")
    parser.add_argument("--verbose", action="store_true",
                        help="do not truncate payloads")
    args = parser.parse_args()

    portfolio_id = args.portfolio
    verbose = args.verbose
    last_state = None
    seen = {}

    print(DIV)
    print("Agent graph CLI.  :p <id> portfolio   :v verbose   :r raw   :q quit")
    print(f"portfolio_id={portfolio_id}  verbose={verbose}")
    print(DIV)

    while True:
        try:
            line = input(f"\n[pid={portfolio_id}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not line:
            continue

        if line in (":q", ":quit", ":exit"):
            return

        if line == ":v":
            verbose = not verbose
            print(f"verbose={verbose}")
            continue

        if line == ":r":
            if last_state is None:
                print("no query run yet")
            else:
                print(json.dumps(last_state, default=str, indent=2, ensure_ascii=False))
            continue

        if line.startswith(":p"):
            arg = line[2:].strip()
            if not arg:
                portfolio_id = None
                print("portfolio_id cleared")
            elif arg.isdigit():
                portfolio_id = int(arg)
                print(f"portfolio_id={portfolio_id}")
            else:
                print(f"not a number: {arg!r}")
            continue

        if line.startswith(":"):
            print(f"unknown command {line!r}")
            continue

        started = time.time()
        try:
            # The previous turn's state goes in with every turn, so a reply
            # to a clarification is resolved against what was asked.
            last_state = run_agent_graph_sync(line, portfolio_id=portfolio_id, previous=last_state)
        except Exception as exc:
            print(f"\n!! {type(exc).__name__}: {exc}")
            import traceback
            traceback.print_exc()
            continue

        show(last_state, time.time() - started, verbose, line, seen)


if __name__ == "__main__":
    main()
