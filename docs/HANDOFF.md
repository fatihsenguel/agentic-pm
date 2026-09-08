# AGENTIC_FINANCE — Session Handoff

**Session date:** 8 September 2026 (seventh sitting; the fifth and sixth were earlier the same day)
**Branch:** `compliance`, cut from `baseline-v1` at the fifth sitting's handoff (afdc344). Not merged. The owner pushes and merges.
**State:** Green. 232 tests passing at the last code change. Golden set: fifteen queries, clean on all five runs this sitting against `expected.txt`, no `retries` line on any; three lines pin failures (below). Runner: **11/12** — 2.3 passes (twice), 3.5 blocked on conversation memory. Commit count this sitting: `git rev-list --count fa5c34e..HEAD` = 8 before this file's commit.

Written for whoever picks this up cold.

**Regenerate this document at the end of each session rather than patching it.**
Generated context files rot faster than the code they describe. The version this
replaces said 2.3 was blocked because "no word in it names the policy" (§4:
the router named the policy itself; the mode was the problem) and called the
dependency validator's prediction the least certain on the list (§4: it held,
and the rejection was never exercised live). Check every claim here against
the code before acting on it.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/benchmark.md` | **The definition of done.** 12 cases across 3 levels. Its Level 2 status note still says 2.3 is blocked; the runner is the status, and it says PASS. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Every case but 3.5 has a check. Its docstring says what it asserts and what it deliberately does not. A compliance case that blocks on a clarification now prints the question the router asked back. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Read at minimum: "`RouterDecision.validate_execution_order` repairs" (the second gap built, the first still open), "A router failure becomes a clarification" (corrected; and the context-free repair prompt beneath it), the four hygiene entries dated the seventh sitting, and the two entries under Hygiene on "Is my AAPL position too big?" and on 2.3 (RESOLVED, with the corrected cause). |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1–7. Part 7 is the compliance reference; `tests/test_compliance.py` reproduces it to the cent. **Never update it to match code output.** |
| `docs/IPS.md` | The owner's policy, synthetic, IPS-1.1 to IPS-6.2. `ips.toml` is derived from it and `tests/test_ips.py` holds the two together. Do not edit `docs/IPS.md`. |
| `docs/PM-Assistant — Roadmap.md` | Phased plan, stale in places, with a header listing what is superseded. §7 below overrides its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.11% v 12%, JNJ 10.06% v 10%) and sit wherever the day's closes put them; the runner asserts structure and does not care. The live `as_of` was not read this sitting.

---

## 1. Project and owner intent

**AGENTIC_FINANCE** — a multi-agent portfolio management system on LangGraph. Owner: Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public — README is outdated and lies)
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

A **personal portfolio management and equity research assistant**, driven by the
owner's own Investment Policy Statement. Two halves: a deterministic core
(positions, real computed metrics, IPS rules that block and cite) and an
open-ended half (screening, filings, forming and challenging a thesis), the
boundary between them explicit. The guarantees half checks a portfolio against
the policy, cites clauses, and states the conditions to return inside a limit;
the judgement half has not started, deliberately. **No deadline. Correctness
over speed. Scope creep is the risk.**

### Design principles the owner holds

- Strict modularity.
- **Hot potato — agents never see raw data.** Tools return summaries; raw arrays
  move through `shared_data`, never into an LLM context.
- **Policy lives in config, not code.** `ips.toml` holds every number and every
  topic word; the checker holds none. `REQUIRES` in `schemas.py` holds what an
  agent needs before it; the validator holds none of the names. An agent
  computes; the synthesizer formats; a formatter doing arithmetic is a bug.
- **Long-term correctness over working output.** Raise rather than repair. The
  router's plan is now rejected before the graph runs when it cannot run, and
  never reordered. A plausible wrong answer is worse than a refusal.

### How the owner works

- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting any symbol.
  **Grep for the caller, not the registration**, and for the reader of a
  return value: this sitting found a helper that was called and whose result
  went nowhere, and a dict key the CLI reads that nothing ever writes.
- **Check instructions against the code before acting on them, including the
  owner's and including this file.** Two claims in KNOWN_GAPS were wrong this
  sitting and are corrected there, not rewritten.
- One change per commit; a commit message needing "and" is two commits.
  Never `commit -a`/`-am`, never `add -A`/`.`; name the files; `git status
  --short` before every commit. `git diff` and a yes before every commit.
- Four loops, run as **separate commands**, never chained. Golden and runner
  cost money: ask before running either.
- **A prompt change is a hypothesis.** Line-by-line prediction in the commit
  message before the run; golden twice; a line moving against the prediction
  is a failed hypothesis even if the new routing looks defensible. **After the
  second failed prediction on a line, stop:** pin, record, propose a
  diagnostic. This sitting the diagnostic was one runner call that printed
  the router's own question, and it found a cause the two guesses had missed.
- When a step needs the owner's result, ask for it and stop; never hand the
  next block in the same message.
- Never edit `.gitignore`; never run Alembic or reseed without being asked;
  never push, rebase, amend, reset, stash.

### What the owner does NOT want

A pure asyncio/regex deterministic version without LangGraph.

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q

python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt

python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 2.3

python src/agents/cli.py --portfolio 3
```

**232 passed.** The caveat stands: `test_portfolio_integration.py` returns
booleans and passes unconditionally. New this sitting, all asserting:
`test_router_warnings.py` (4: rejected router attempts reach the state on
both return paths), `TestDependencies` in `test_smart_router.py` (8: the
three diagnostic plan shapes rejected, six shapes still accepted, `REQUIRES`
held to the roster), and `test_execution_order_mismatch_is_repaired_today`
(renamed: it had been passing on `reasoning` length, not on the order).
Nothing yet exercises `synthesizer_node` itself.

**The golden set has fifteen queries and six fields.** The sixth, `retries`,
prints only when the schema rejected a router attempt before the printed
decision; it has not printed on any run yet. Pinned failures, three: the
macro query (`errors: 1`, since the first baseline); "How much did AAPL gain
today?" (pid 3, `out_of_scope`, the false refusal, untouched); "Should I
rebalance my portfolio?" (`errors: 1`, no target source). Three lines pinned
to `compliance` with the three-agent plan: "Is my AAPL position too big?"
(known to flip on some runs; a flip is now rejected by the validator and
would print `retries: 1` with the repaired plan — not yet observed), "Is my
AAPL position within my policy's limits?" (stable), "Is AAPL too
concentrated?" (stable). Any diff on those lines is the known behaviour; any
diff elsewhere is a regression or the nondeterminism.

### Branches and tags

`compliance` is this sitting's branch, 38 commits on `baseline-v1` before this
file's commit. `wip/phase7-snapshot` holds rejected Compliance/IPS code;
nothing on it is scheduled, do not read it for ideas. `wip/rag-early` and tag
`rag-early-parked` hold the deleted RAG code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`05034c6316c8`** (`add instrument_type to assets`), 12 migrations, linear.
Not touched this sitting.

- **Portfolio 3, "Benchmark Portfolio" — use this one.** 9 positions, cost
  basis 284,500 plus 15,500 cash. Seeded by `seed_portfolio.py` (idempotent,
  `--reset` wipes holdings first). Five golden queries run against it.
- **Portfolio 1** — January data; four golden queries. Do not modify.
- **Portfolio 2** — a leaked test artifact; one golden query. Load-bearing.
- **Reseeding portfolio 3 rewrites `Asset` metadata shared with 1 and 2**,
  including `instrument_type`.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`. Never read or print it.
- **OpenAI: no credits.** **Anthropic: working**, workspace-scoped key.
  `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU` (`claude-haiku-4-5-20251001`).
  `ANTHROPIC_SONNET` still points at the Haiku id.
- `config.features.observability_enabled` is **false** here (env
  `ENABLE_OBSERVABILITY`). `run_agent_graph` opens the request span
  unconditionally, so tracing works; `SmartRouter.route` would open and close
  its own span if the flag were true, re-breaking the fix a07c523 made
  (KNOWN_GAPS). Do not turn it on without reading that entry.
- `config.py` owns the database URL and anchors a relative SQLite path to the
  project root. `ips.py` anchors `ips.toml` the same way.
- `portfolio_tool/__init__.py` opens a DB connection at import; anything
  importing `portfolio_tool.ips` or `.compliance` pays that. The router prompt
  therefore does not import them at module level.

---

## 4. What the seventh sitting did

`git log --oneline fa5c34e..HEAD` for the list, 8 commits. By topic:

**Stale hashes.** The branch had been rebased after the sixth handoff; the
thirteen hashes cited in HANDOFF and KNOWN_GAPS were replaced (011c744).
benchmark.md and the runner cited none of them.

**The dependency validator, §7 item 1, in three commits after two findings.**
Reading before writing found that (a) the repair retry sends `REPAIR_PROMPT`
alone — no roster, no rules, no portfolio context — and (b) no loop could see
a retry: `router_node` computed its validation warnings and dropped the
returned dict. So first the warnings were carried into the state (0f86384),
then the golden runner learned to print `retries` when nonzero (83de9d9,
zero diff predicted and observed), then the validator (d4c102d): `REQUIRES`
beside `AGENTS`, one entry, `validate_dependencies` raising when an agent
precedes what it requires, ComplianceAgent under any intent but `compliance`
raising in `validate_compliance`. Golden twice: fifteen lines held, no
`retries`. The prediction that mattered was the falsifier — no line may show
a rejected shape — and it held; the flip did not occur, so the rejection has
no live observation yet.

**2.3, from BLOCKED to PASS.** The validator did not move it: the runner
showed its first attempt was `clarification_needed` with an empty plan. The
runner then learned to print what the router asked back (60f4b62), and one
`--case 2.3` run read: "Are you asking whether your current portfolio
complies with your Investment Policy Statement, or are you proposing a
specific position weight…" — the router had the intent and could not choose
the mode. One sentence in rule 7 (a3bad06): the hypothetical shape needs a
weight stated in the message; with none, a question about complying, limits
or what must change is the portfolio check. Predicted fifteen lines hold and
2.3 PASS; held on golden twice, runner 11/12, and 2.3 again alone. Declared
the last prompt edit for 2.3.

**A test passing for the wrong reason.** `test_execution_order_mismatch`
raised on a four-character `reasoning`, not on the order; with a valid
reasoning the mismatch is silently repaired. Pinned as it is (8f99b04) with
the later raise named.

**KNOWN_GAPS swept (36fe55e):** two corrections to its own record (2.3's
cause; three rejections end in a "Router error", not the fallback
clarification), four new hygiene entries, the resolved warnings entry.

---

## 5. Decisions taken, and decisions pending

**Taken this sitting.**
- `REQUIRES` has one entry, `PortfolioAnalysisAgent: (DataAgent,)`. The
  optimiser, rebalance and backtest dependencies also raise at their nodes but
  contradict two examples the router is shown; each is a prompt change with
  its own golden prediction, one per commit.
- The ComplianceAgent-only-under-compliance rule lives in
  `validate_compliance`, not in `REQUIRES`: it is an intent constraint, and
  ComplianceAgent's own needs are conditional on mode.
- The validator never reorders. The reorder-repair in
  `validate_execution_order` stays as it is until its own commit.
- `retries` is printed only when nonzero, so `expected.txt` did not move.
- The third prompt edit for 2.3 was taken, aimed at the cause the diagnostic
  found, and is the last: a regression there goes to conversation memory.

**Pending, owner's call — bring them up before writing code.**
1. A golden line for 2.3, so its routing is pinned somewhere. A benchmark
   prompt in the golden set, as 3.2 and the four Level 1 prompts already are;
   moves `expected.txt` by one query.
2. The diagnostic golden query "How much has AAPL gained?" (pid 3), one line,
   no prompt change, to separate "bare ticker" from "today". Still untaken.
3. Keep or revert the three failed prompt edits (6e68c47, d8cd0d6, 31ce272).
4. A target-weights clause in the IPS and `OUT_OF_SCOPE_RESPONSE` moving into
   the IPS — both edit `docs/IPS.md`, which is the owner's.
5. D9's wording ("unrounded" means "not rounded beyond the cent-rounded block").
6. The workbook: D8 and D9 in its `Decisions` sheet, `C91`, own commit via
   `git add`.
7. Merge `compliance` into `baseline-v1`, or not.

---

## 6. Where we stand against the benchmark

11/12. Level 1 in full; Level 2 in full; 3.1 to 3.4. 3.5 BLOCKED on
conversation memory. benchmark.md's Level 2 status note still says 2.3 is
blocked; the runner is the status and the note is a correction for whoever
next touches that file.

---

## 7. Next steps, in order

### 1. Pending decision 1 — pin 2.3's routing

One golden line, no prompt change, own commit, `expected.txt` updated with a
yes. Until it exists, a regression on 2.3 is visible only on the runner.

### 2. Conversation memory, for 3.5

`AgentState.messages` and `build_router_prompt(conversation_history=)` exist
and are never populated; `run_agent_graph_sync` never passes prior turns. The
runner sends one query per case, so 3.5 needs a two-turn case shape as well.
Note `_decision_to_dict` drops `clarification_question` (KNOWN_GAPS): a
second turn needs the question the first turn asked, and today only
`final_response` carries it.

### 3. The intent-vocabulary registry

Five sites, the roster registry is the pattern, `compliance` touched all five
in one commit. Own commit, zero golden diff predicted when rendered byte-identically.

### Later, with reasons

- **The repair prompt carrying the full system prompt plus the error.** Not
  before a retry has been observed live: the first `retries: 1` on a golden
  line is the first data on what the context-free repair produces, and the
  change is a hypothesis about that.
- `validate_execution_order`'s reorder-repair → raise, now that the
  dependency validator shows the shape.
- Rule 6 and rule 7 still collide on "too big"; reconciling them is a prompt
  change with its own prediction.
- Pending decisions 2–6 in §5, each small.
- Deletions, each its own commit after a grep for every re-export:
  `prompts.py`, `build_router_prompt(available_agents=)`, `get_graph_mermaid`,
  the unreachable check in `_validate_decision`, `IntentType.UNKNOWN`,
  `stream_agent_graph`, `AgentTask.depends_on`, `state.add_warning` (no
  caller since 0f86384).
- `_decision_to_dict` carrying `reasoning` and `clarification_question`, so
  the CLI's two lines for them print.
- Replace the two verbatim few-shots (1.1, 1.3).
- The period rule's "nearest valid value" → `clarification_needed`.
- README rewrite; `test_portfolio_integration.py`; the inline `sqrt(w'Σw)` copies.

---

## 8. Rules learned the hard way

**Read the question the router asked before predicting what it thinks.** Two
predictions on 2.3 guessed the router did not see a policy question. One
runner call printed its clarification, which named the Investment Policy
Statement and offered two compliance readings. The cause was the mode, which
no edit had addressed. A diagnostic that reads the model's own output costs
one call; a golden diagnostic query would have cost fifteen per run and
answered a question the router had already answered.

**A value computed and dropped is registration, one level down.** The
warnings loop existed, `add_warning` was called, and its return went nowhere;
the CLI reads two dict keys nothing writes. Grep for the reader of a return
value, not only the caller of a function.

**A check that cannot distinguish two states passes in both.** Without
`retries`, a plan rejected and repaired back to the pin was identical to a
plan accepted first time. The instrument was widened before the change it
was meant to see, and printed nothing, which is the result it was built for.

**A test can pass for a reason it does not name.** The order-mismatch test
raised on a short `reasoning`, not on the order it was written about. Read
the error a `pytest.raises` actually catches.

**Write the falsifier, not only the expected value.** The validator's
fifteen-line prediction could not be wrong on a run where nothing flipped;
"no line may show a rejected shape" could, and that is what the run tested.

**Registration is not reachability; shown a list, a model picks from it;
predict from the whole prompt; structure, not verdicts; two hands, one
decision; six for six; a refusal is an honest failure — still true.** The
previous handoffs' §8 have the examples.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 2.3

python src/agents/cli.py --portfolio 3

python src/portfolio_tool/scripts/seed_portfolio.py --show

grep -rn "SymbolName" src/ tests/ --include='*.py'
git status --short
git log --oneline fa5c34e..HEAD
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~30s | Do the components still work; does the graph still build; does the validator reject what it should and accept what it must |
| CLI | ~4s | What is it actually doing — agent spans, tool calls, handovers, and now a WARNINGS section on a router retry |
| Golden set | ~70s, cents | Did routing change anywhere (fifteen lines, three pinned failures, one known flip, `retries` when a plan was rejected) |
| Benchmark runner | ~1.5min, cents | How many cases pass; a BLOCKED reason names the router's intent and plan, and the question it asked back |

`golden set → change → golden set → decide → then update expected.txt, its own
commit, with a yes`. Prediction first, twice, stop at the second miss on a line.
The runner is per capability commit.
