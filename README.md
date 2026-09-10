# AGENTIC_FINANCE

A portfolio-management and equity-research assistant on LangGraph, driven by
my own written Investment Policy Statement. Underneath it is a deterministic
core: positions derived from a transaction ledger, allocation, P&L, portfolio
volatility, and a compliance check that blocks a request and cites the clause
it breaks. The portfolio is the example, not the point. What this is, is an
agent system over my own documents, with source attribution for every policy
claim and a hand-computed reference for every figure.

## Two halves

**The guarantee half is built.** Everything the system says about what I
hold is computed by a fixed pipeline, checked against a reference computed
by hand before the code existed, and scored by a benchmark of twelve cases
that all pass. Three of the twelve are cases where the right answer is a
refusal.

**The judgement half is not started, on purpose.** Research, valuation, a
thesis, a sized position: that is a model reading and reasoning with further
tools, marked as judgement, and it starts only when the benchmark defines
what a good research answer is and a prediction ledger exists to score it. A
system that recommends before it can correctly compute what is already held
recommends against a wrong picture.

## What holds it up

- **Agents never see raw data.** Tools return summaries; raw arrays move
  through shared state and never into a context window.
- **Policy lives in a document, not in code.** The policy has numbered
  clauses and a derived config file; a check cites the clause, never a
  paraphrase; a personal policy replaces the synthetic one as a file, with
  no code change.
- **Every number traces to a tool output.** The model narrates around
  figures; it never produces one.
- **Raise, do not repair.** A missing input, a value the vocabulary lacks,
  a holding of unknown type: the pipeline stops and says why. A default is
  a wrong answer with a plausible face.
- **References before code.** `tests/golden/expected_values.md` holds the
  figures, computed by hand, that the code has to reproduce to the cent;
  when code and reference disagree, one of them is wrong and the reference
  is never edited to match.

## Where to read

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | The end state, the invariants, and the order of work. |
| `docs/benchmark.md` | The definition of done: the twelve cases and what each passes on. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved ones, and why the obvious fixes were wrong. |
| `docs/HANDOFF.md` | The state of the code, regenerated at the end of every session. |

## Running it

```bash
source .venv/bin/activate
pytest -q                                   # no model calls, a few seconds
python src/agents/cli.py --portfolio 3      # one model call per question; :q to quit
```

The golden set (`tests/golden/run_golden.py`) and the benchmark runner
(`tests/benchmark/run_cases.py`) make model calls and cost money. A
synthetic portfolio and a synthetic policy are in the repository; my real
ones are not, and enter last.

## Status

The benchmark passes twelve of twelve. The ledger, the base currency with
its exchange rates, and the price source are built against their
references; the personal policy is next. This file says less than the
documents above on purpose, and is dated: 10 September 2026.
