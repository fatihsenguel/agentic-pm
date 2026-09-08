# AGENTIC_FINANCE — Session Handoff

**Session date:** 8 September 2026 (seventh sitting; regenerated after the merge and `docs/DIRECTION.md`)
**Branch:** `baseline-v1`. `compliance` was merged into it by the owner (fast-forward, all 41 commits, tip cc7f740); 5840cd6 renamed the inspection note; df1bcef added `docs/DIRECTION.md`; 51c3c70 is the sweep; this file follows. The owner pushes and merges.
**State:** Green. 232 tests passing at the last code change. Golden set: fifteen queries, clean on all five runs this sitting against `expected.txt`, no `retries` line on any; three lines pin failures (below). Runner: **11/12** — 2.3 passes (twice), 3.5 blocked on conversation memory. Nine CLI prompts after the runner found four wrong-faced answers behind that 11/12 (KNOWN_GAPS). Commit count this sitting: `git rev-list --count fa5c34e..HEAD` = 15 before this file's commit.

Written for whoever picks this up cold.

**Regenerate this document at the end of each session rather than patching it.**
Generated context files rot faster than the code they describe. The version this
replaces said the branch was unmerged and listed the merge as pending (both
false since 5840cd6), and its §7 order is superseded by `docs/DIRECTION.md`
(§7 below). Check every claim here against the code before acting on it.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Written by the owner, dated, not regenerated. Wins over this file on direction; this file wins on state. Its last section says when to stop and ask. |
| `docs/benchmark.md` | **The definition of done.** 12 cases across 3 levels. Its Level 2 status note still says 2.3 is blocked; the runner is the status, and it says PASS. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Every case but 3.5 has a check. Its docstring says what it asserts and what it deliberately does not. A compliance case that blocks on a clarification prints the question the router asked back. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Read at minimum: "Four wrong-faced answers behind 11/12, from the CLI" (the block-shape decisions in §5 come from it), "`ExtractedParameters` fields with no reader" and "BaseAgent's tool-calling loop has no live caller" (the router restructure's two greps), "`RouterDecision.validate_execution_order` repairs" (the second gap built, the first still open), "A router failure becomes a clarification" (corrected; and the context-free repair prompt beneath it), and "Does the router stay a classifier" (answered by DIRECTION.md). |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1–7. Part 7 is the compliance reference; `tests/test_compliance.py` reproduces it to the cent. Part 7's IPS-4.3 column is the reference for the sector share of total; its IPS-4.1 column for the per-position share of total. **Never update it to match code output.** |
| `docs/IPS.md` | The owner's policy, synthetic, IPS-1.1 to IPS-6.2. `ips.toml` is derived from it and `tests/test_ips.py` holds the two together. Do not edit `docs/IPS.md`. |
| `docs/PM-Assistant — Roadmap.md` | Phased plan, stale in places, with a header listing what is superseded. DIRECTION.md's Order supersedes its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.11% v 12%, JNJ 10.06% v 10%) and sit wherever the day's closes put them; the runner asserts structure and does not care. The live `as_of` was 2026-09-04 on the owner's CLI session.

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

`baseline-v1` is the working branch and matches `origin/baseline-v1` at the
last fetch. `compliance` is merged into it and no longer diverges; its 41
commits are `afdc344..cc7f740`. On top: 5840cd6 (rename of the inspection
note), df1bcef (`docs/DIRECTION.md`), the sweep, this file.
`wip/phase7-snapshot` holds rejected Compliance/IPS code; nothing on it is
scheduled, do not read it for ideas. `wip/rag-early` and tag
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

`git log --oneline fa5c34e..HEAD` for the list. By topic:

**Stale hashes.** The branch had been rebased after the sixth handoff; the
thirteen hashes cited in HANDOFF and KNOWN_GAPS were replaced (011c744).
benchmark.md and the runner cited none of them.

**The dependency validator, in three commits after two findings.**
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
2.3 PASS; held on golden twice, runner 11/12, and 2.3 again alone. Recorded
in KNOWN_GAPS as the last prompt rule of its kind under DIRECTION.md.

**A test passing for the wrong reason.** `test_execution_order_mismatch`
raised on a four-character `reasoning`, not on the order; with a valid
reasoning the mismatch is silently repaired. Pinned as it is (8f99b04) with
the later raise named.

**KNOWN_GAPS swept (36fe55e):** two corrections to its own record (2.3's
cause; three rejections end in a "Router error", not the fallback
clarification), four new hygiene entries, the resolved warnings entry.

**After the merge.** The two docs lost their workflow "assistant" wording
before the push (53fc445, cc7f740). The owner merged `compliance` into
`baseline-v1`, renamed the inspection note (5840cd6) and wrote
`docs/DIRECTION.md` (df1bcef). The owner ran nine CLI prompts; four answered
a different question from the one asked, with a plausible face, behind a
runner at 11/12. Swept into KNOWN_GAPS with the exact prompts, the
hypothetical mode's missing instrument type, the allocation formatter's
false "named no breakdown" line, the two greps the restructure needs
(BaseAgent's loop has no live caller; `target_return`, `rebalance_threshold`
and `parameters.portfolio_id` have no reader), the rule 7 sentence recorded
as the last prompt rule, and the classifier-or-tool-caller question marked
answered by DIRECTION.md.

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
  found, and is the last prompt rule added to fix a routing defect
  (DIRECTION.md). A regression there goes to conversation memory.
- The router's direction: scaffolding, replaced by tool calling in the end
  state (DIRECTION.md, answering the deferred KNOWN_GAPS question).

**Pending, owner's call — bring them up before writing code.** Each comes as
the shape, a recommendation, the rejected alternatives, which loop sees it
and what it will show.
1. **Share of total on the sector line.** A block widening with two consumers
   already: the IPS-4.3 check divides for it, and "what share of my portfolio
   is technology" has no answer without it. One figure the checker then reads
   instead of computing. Reference: Part 7's IPS-4.3 column.
2. **The concentration measure.** Its trigger fired ("what's my biggest
   position?"). Per-position share of total from published market values;
   the IPS-4.1 check reads the same figure. Includes what `group_by` or
   `measure` value names it and which formatter prints it. Reference: Part
   7's IPS-4.1 column.
3. **The router restructure, four separate decisions and commits, in order:**
   the intent registry (predict zero golden diff, the way the roster did);
   deterministic extraction of tickers, weights, periods and topics before
   the LLM (golden once, predict zero diff, since `period` is a printed
   field); plans derived from intent and the extracted parameters through a
   terminal-agent table closed by `REQUIRES` (predict every pinned plan
   holds; a diff is brought with both readings, wrong pin or wrong table,
   and `expected.txt` moves only on a yes); then the prompt shrink, golden
   twice. The JNJ ticker defect and the period-to-1Y repair are extraction.
   Before the first of these, confirm from the code the two greps KNOWN_GAPS
   now records.
4. A golden line for 2.3, so its routing is pinned somewhere. Moves
   `expected.txt` by one query.
5. The diagnostic golden query "How much has AAPL gained?" (pid 3), one line,
   no prompt change, to separate "bare ticker" from "today". Still untaken.
6. Keep or revert the three failed prompt edits (6e68c47, d8cd0d6, 31ce272).
   Under DIRECTION.md they are prompt rules; the prompt shrink is where they
   are decided.
7. The hypothetical mode's instrument type ("11% into a new ETF" is refused
   under IPS-4.2 today, wrongly).
8. A target-weights clause in the IPS and `OUT_OF_SCOPE_RESPONSE` moving into
   the IPS — both edit `docs/IPS.md`, which is the owner's.
9. D9's wording ("unrounded" means "not rounded beyond the cent-rounded block").
10. The workbook: D8 and D9 in its `Decisions` sheet, `C91`, own commit via
    `git add`.

---

## 6. Where we stand against the benchmark

11/12. Level 1 in full; Level 2 in full; 3.1 to 3.4. 3.5 BLOCKED on
conversation memory. benchmark.md's Level 2 status note still says 2.3 is
blocked; the runner is the status and the note is a correction for whoever
next touches that file.

---

## 7. Next steps, in order

**`docs/DIRECTION.md`'s Order 1 supersedes the §7 that stood here** (the 2.3
golden line, conversation memory, the intent registry). Its order:

### 1. The block shapes the CLI questions exposed

Pending decisions 1 and 2 in §5: the sector share of total, then the
concentration measure. Each is a decision first, then a hand-checked
reference (Part 7 already carries both figures), then the block, the
checker reading the figure instead of dividing, the formatter, the runner.
The CLI is the loop that sees the answer change; the runner sees 2.1, 2.2
and 2.3 keep passing; pytest holds Part 7 to the cent.

### 2. The router restructure

Pending decision 3 in §5, in its four steps: registry → extraction →
derived plans → prompt shrink. Each its own decision and commit. Stop after
the second failed prediction on any golden line and bring a diagnostic. If
a step makes the router smarter rather than smaller, stop and ask.

### 3. Conversation memory, as an extraction rule

Only after 2. Write the runner's two-turn case shape for 3.5 first so it
can fail for the right reason; 3.5 is a typo of a ticker the portfolio does
not hold, so the first turn is a clarification naming AAPL and the second
turn is the owner's reply resolved against the question that was asked.
`AgentState.messages` and `build_router_prompt(conversation_history=)`
exist and are never populated; `_decision_to_dict` drops
`clarification_question`, and today only `final_response` carries it.

### Later, with reasons

- Pending decisions 4–10 in §5, each small.
- `validate_execution_order`'s reorder-repair → raise, now that the
  dependency validator shows the shape.
- The repair prompt carrying the full system prompt plus the error was listed
  here before DIRECTION.md. It makes the router smarter; under DIRECTION.md it
  is debt, and the prompt shrink is where a retry's fate is decided. Not
  before a retry has been observed live.
- Rule 6 and rule 7 still collide on "too big"; under DIRECTION.md the
  resolution is derivation, not a reconciled sentence.
- Deletions, each its own commit after a grep for every re-export:
  `prompts.py`, `build_router_prompt(available_agents=)`, `get_graph_mermaid`,
  the unreachable check in `_validate_decision`, `IntentType.UNKNOWN`,
  `stream_agent_graph`, `AgentTask.depends_on`, `state.add_warning` (no
  caller since 0f86384), `target_return`, `rebalance_threshold`,
  `parameters.portfolio_id` (no reader), `route_sync` and
  `detect_intent_simple` (no caller in the graph).
- `_decision_to_dict` carrying `reasoning` and `clarification_question`, so
  the CLI's two lines for them print.
- Replace the two verbatim few-shots (1.1, 1.3); under DIRECTION.md the
  prompt shrink may remove them instead.
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
