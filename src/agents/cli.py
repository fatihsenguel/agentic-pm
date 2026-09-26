"""
Exploratory CLI for the agent graph.

Roadmap 0.3. The golden set answers "did anything change"; this answers
"what is it actually doing". Both are needed.

Runs against the graph via run_agent_graph_sync — NOT against the
create_*_agent factories, which is what the deleted multi_agent_cli.py did
and why it bypassed routing entirely.

Usage:
    python -m agents.cli                # or: python src/agents/cli.py
    python src/agents/cli.py --portfolio 3

Commands:
    :p <id>     switch portfolio (:p with no id clears it)
    :v          toggle verbose (full inputs, and each record's agents)
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
    """Print the routing decision, the records of the tools the turn
    called, and the answer.

    Each record prints as one line, the tool, its inputs and its
    provenance, with the tool's fixed caveats under it (decision 77); an
    as-of or a source the block did not state prints as not recorded. The
    last run's `shared_data` and `sub_results` are empty after a turn and
    are not printed.

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

    records = state.get("tool_calls") or []
    print("\nTOOLS CALLED")
    if not records:
        print("  (none)")
    for record in records:
        provenance = record.get("provenance") or {}
        as_of = provenance.get("as_of") or "not recorded"
        source = provenance.get("source") or "not recorded"
        print(f"  {record.get('tool')} {_fmt(record.get('inputs') or {}, limit)}  "
              f"as of {as_of}; source {source}")
        for caveat in provenance.get("caveats") or ():
            print(f"      {caveat}")
        if verbose:
            agents = record.get("agents") or {}
            ran = ", ".join(f"{name} {'ok' if ok else 'not ok'}" for name, ok in agents.items())
            print(f"      agents: {ran or '(none recorded)'}")

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
        # 1. A tool printed numbers this turn and none reached the answer.
        if not any(c.isdigit() for c in answer):
            if any(c.isdigit() for r in records for c in (r.get("text") or "")):
                print("\n  !! NO NUMBERS IN ANSWER while a tool's text has them"
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
