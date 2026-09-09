# AGENTIC_FINANCE — Session Handoff

**Session date:** 9 September 2026 (ninth sitting; regenerated at its end)
**Branch:** `selection`, cut from `baseline-v1` at 7fc6474 (where `vocabulary` had already been merged and pushed). Thirty-one commits on top, the sweep included. Not merged, not pushed; the owner merges and pushes.
**State:** Green on every loop. pytest 405 in 14 seconds. Golden set sixteen queries, clean twice after the one prompt change, no `retries` line. Runner **12/12** on the last run, after one failed prediction fixed in the formatter. Commit count: `git rev-list --count baseline-v1..HEAD`.

Written for whoever picks this up cold.

**Regenerate this document at the end of each session rather than patching it.**
The previous version was patched between sittings and said so nowhere;
its branch claims were a day stale when this sitting opened. **Check every
claim here against the code before acting on it, including the owner's,
including this file.** Grep for the caller, not the registration, and for
the reader of a return value.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Owner's, dated, not regenerated. Wins over this file on direction; this file wins on state. Order 1 is built; Order 2 has begun with a reference, not code. Its last section says when to stop and ask. |
| `docs/benchmark.md` | **The definition of done.** 12 cases, 12 pass; the runner is the status. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Every case has a check. 2.2's every-clause-cited check is the falsifier that caught this sitting's one failed prediction. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Swept at the end of this sitting: every entry the sitting touched carries a "9 September (ninth sitting)" paragraph. Read at minimum: the `group_by`/`filter` entry (the selection axis, its failed prediction, and the fix in the formatter), "Decision 16" under Directions (logged, with its trigger and cost), "The `transactions` table has no portfolio" (what Order 2 starts from), "pytest had not run since January" (the five files that ran live at collection). |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1–8. **Part 8 is new: the transaction ledger, decisions D10–D14, before the ledger exists.** Never update it to match code output. The workbook's `Ledger` sheet carries the same as formulas, not recalculated by this sitting. |
| `docs/IPS.md` | The owner's policy, synthetic. `ips.toml` is derived from it. Do not edit `docs/IPS.md`. |
| `docs/PM-Assistant — Roadmap.md` | Stale, header lists what is superseded. DIRECTION.md's Order supersedes its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.16% v 12%, JNJ 10.05% v 10% at the 09-04 closes); the runner asserts structure. The live `as_of` was 2026-09-04 on every run this sitting.

---

## 1. Project and owner intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Owner: Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public — README is outdated and lies)
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half (positions, allocation,
P&L, risk, compliance) that is tools, and a judgement half (research,
valuation, a thesis) that has not started, on purpose. The router is
scaffolding until the tool layer is complete. **No deadline. Correctness over
speed. Scope creep is the risk.**

### Design principles the owner holds

- **Hot potato — agents never see raw data.** Tools return summaries; raw
  arrays move through `shared_data`.
- **Policy lives in config, not code.** `ips.toml` holds every number and
  topic word. The vocabularies are registries: `AGENTS`, `INTENTS`,
  `REQUIRES`, `TERMINAL` in `schemas.py`; the period keys in `config.py`.
  An agent computes; the synthesizer formats; the checker reads published
  shares and divides nowhere.
- **Raise, do not repair.** A span the vocabulary lacks, a typo of a holding,
  two weights in one message: extraction asks back, naming what it can do.
  A default is a wrong answer with a plausible face.
- **Extraction and derivation before the model.** Tickers, periods,
  percentages and the compliance mode are read from the message; the plan
  is derived from the intent and those parameters. The model decides
  intent, `measure`, `group_by`, `status`, confidence and a clarification
  question, and nothing else it emits is read.
- **Selection is rendering.** A formatter selects from a block the node
  computed in full; the selection's values are the block's own words
  (`tickers` for subjects, a finding's `status`), never a new measure.
- **The failure direction of a model-owned field is designed in the
  formatter.** A field the model over-sets must shorten the answer and hide
  nothing (this sitting's lesson, §8).

### How the owner works

- Every item comes as a decision first: the shape, a recommendation, the
  rejected alternatives, which loop sees it and what it will show. Then a
  yes. Then one commit per layer, tests written first and seen failing,
  `git status --short` and the diff before each commit, and a yes on each.
- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting any symbol;
  grep for the caller and for the reader of a return value. Eleven
  deletions this sitting went that way, one commit each.
- **A prompt change is a hypothesis.** Line-by-line prediction in the commit
  message before the run; golden twice. **After the second failed
  prediction on a line, stop:** no rewording, bring a diagnostic that reads
  the model's own output. This sitting the `status` prompt's prediction
  failed on 2.2 and 2.3 at the first run; the fix was the formatter's
  failure direction, not a wording.
- Never `commit -a`/`-am`, never `add -A`/`.`; name the files. Never push,
  rebase, amend, reset, stash. Never edit `.gitignore`; never reseed or run
  Alembic unasked. No attribution trailers.
- When a step needs the owner's result, ask for it and stop. The owner
  asked "what is Part 8, what are the decisions, what changes if I say
  yes" before the reference landed; explain in plain words before asking
  for a yes on a document.

### What the owner does NOT want

A pure asyncio/regex deterministic version without LangGraph. Prompt rules
added to fix a routing defect (DIRECTION.md). The real portfolio's data in
the repo or in this sitting: it enters last, when everything works.

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q

python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt

python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 2.2

python src/agents/cli.py --portfolio 3
```

**405 passed, 23 warnings, 14 seconds.** Down from 408 in 24 seconds: five
unguarded files that ran at import were deleted (33f09b5), two of which
made live model calls twice per run. New this sitting: the selection tests
in `test_compliance_formatter.py` (a named position, breaches only, both,
no breach, the coverage line), the `status` schema and plan tests, the
prompt tests for the `status` line. The caveat stands and is sharper:
`test_portfolio_integration.py` returns booleans, passes unconditionally,
and still routes live through the model on every run (KNOWN_GAPS).

**The golden set has sixteen queries.** Two lines pin failures: the macro
query (`errors: 1`) and "Should I rebalance my portfolio?" (`errors: 1`,
no target source). Clean twice after the only prompt change this sitting
(b4aada5). The set is blind to `tickers`, `measure`, `group_by`, `status`
and the compliance mode; the runner is the loop that sees those.

**Runner 12/12.** It fell to 11/12 once this sitting, on 2.2, when the
model set `status: breach` on "does my allocation violate any rule"; the
formatter's coverage line (27a2ec0) put it back and it holds whatever the
model sets there.

### Branches and tags

`selection` is the working branch, cut from `baseline-v1` at 7fc6474.
`baseline-v1` matched `origin/baseline-v1` at 7fc6474 when the sitting
opened; `vocabulary` is merged into it. `compliance` is merged.
`wip/phase7-snapshot` holds rejected Compliance/IPS code; nothing on it is
scheduled. `wip/rag-early` and tag `rag-early-parked` hold the deleted RAG
code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`05034c6316c8`**, 12 migrations, linear. Not touched this sitting. The
`transactions` table exists in the models with no portfolio column and no
caller; Part 8 is written against the shape it will need.

- **Portfolio 3, "Benchmark Portfolio" — use this one.** 9 positions, cost
  basis 284,500 plus 15,500 cash. Five golden queries run against it.
- **Portfolio 1** — January data; five golden queries. Do not modify.
- **Portfolio 2** — "Demo Portfolio", a leaked test artifact; one golden
  query. Load-bearing. No longer touched by pytest collection.
- **Reseeding portfolio 3 rewrites `Asset` metadata shared with 1 and 2.**

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never read or print it.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  (`claude-haiku-4-5-20251001`). `ANTHROPIC_SONNET` still points at the Haiku id;
  `claude-sonnet-5` is a live id (the token counter accepted it).
- `openpyxl` is in the venv and in the `dev` extras (f6fe39a), for the
  workbook's `Ledger` sheet. No LibreOffice on the machine: a sheet written
  here is not recalculated here.
- `config.features.observability_enabled` is **false** here. Do not turn it
  on without reading the KNOWN_GAPS entry on the router's own span.
- `portfolio_tool/__init__.py` opens a DB connection at import; the router
  prompt and `agents/extraction.py` import nothing from it at module level.

---

## 4. What the ninth sitting did

`git log --oneline baseline-v1..HEAD` for the list, in the owner's order.

**Decision 16, brought and logged.** A stronger reader producing a typed
request, extraction reduced to validation. Brought with what it does to
the golden set (seven of sixteen lines become model-dependent), the cost
per call measured with the token counter (Haiku $0.003, Sonnet 5 $0.008,
Opus 5 $0.021), and what it changes in DIRECTION.md's Order (Order 5's
shape built early, the "bigger model is debt" sentence). Logged with the
trigger: Order 5, or a benchmark case that needs a name, German or a typo
read. KNOWN_GAPS, "Decision 16".

**The compliance selection axis, two values (item 2).** A named position:
the formatter takes the decision and reads `tickers` as the P&L formatter
does; "Is my JNJ position over any limit?" answers with JNJ's two rows
and one condition (2e7fd63, c620275, c0886c2). Breaches only: `status`,
Literal `"breach"`, the model's field beside `measure` and `group_by`,
held to intent compliance and rejected beside a mode, not a plan
discriminator (a40b277, 7232ecb, c637152, cb3e1c1, b4aada5). The prompt
commit's prediction, "status null on 2.2 and 2.3", failed on both at the
first runner run, read from the model's own output; the fix was the
rendering's failure direction: the breach body keeps the check's coverage
in one line each, so 2.2 passes whatever the model sets (fdcd9a2,
3c67ced, 27a2ec0). Golden clean twice; runner 12/12 after.

**The rename to named denominators (item 3), one commit (0c9f833).**
`pct_of_denominator` gone; `pct_of_sectored` on sector lines only;
`pct_of_total` everywhere. Runner 12/12, 1.1's own check moved.

**The deletions (item 4), each after a grep, one commit each.** The `"3Y"`
default (043ed55); `state.add_warning` (6d82220); the two unreachable
checks in `_validate_decision` (300af9e); the stream entry point and the
mermaid diagram (61158e1); `prompts.py` (536a357); `route_sync`,
`detect_intent_simple`, `route_message` (a60d0ad); `conversation_history`
and `available_agents` (1320913); `is_multi_step` (2a7dd47);
`requires_confirmation` (696ef6a); `target_return` (dccb201);
`rebalance_threshold` (7b9db26); the five test files that ran at import
(33f09b5, a finding, not on the list); `parameters.portfolio_id`
(1238792); `AgentTask` and the task list (a7a24bc).

**Order 2 begun with a reference (item 5).** The ledger is first, with
its reasons; Part 8 in expected_values.md, decisions D10–D14, portfolio 3
as nine buys reproducing Part 1 and one synthetic tranche-and-sale
position exact to the cent (c4c4920); the workbook's `Ledger` sheet
(64a9bec); openpyxl declared (f6fe39a).

**Findings logged, not chased** (all in KNOWN_GAPS): the unguarded files
and the double-collected coroutine; the integration file's swallowed
assert and live calls; `load_portfolio_context` without an asserting
test; `max_conversation_history` unread; the SQLAlchemy warning count as
a floor; the `transactions` table's shape.

---

## 5. Decisions taken, and decisions pending

**Taken this sitting, each on a yes.**
- Decision 16 logged, not taken; its trigger is Order 5 or a case.
- The selection axis has two values, `tickers` (extraction's) and `status`
  (the model's); selection is rendering; the block is always the full
  check; a model-owned field's over-setting hides nothing.
- The one-figure principle: a total and a cost are selections, never
  measures; built when a case asks.
- The rename to named denominators; the `denominator` label stays.
- The deletions, all of §5 item 5 of the previous handoff, plus the five
  unguarded files and `route_message`.
- Order 2's first item is the ledger; D10 average cost, D11 fees in basis,
  D12 what a sale does, D13 holdings derive from rows, D14 a row belongs
  to a portfolio and its amount is data. The real portfolio's own Part 8
  comes last, when the system works, and is the owner's.
- One departure from tests-first, stated: the rename's fixtures moved in
  the same commit as the code, since a rename has no failing test but the
  missing attribute.

**Pending, owner's call — bring them up before writing code.**
1. **The ledger's code**, in this order: a pytest over Part 8 A and B that
   fails before the ledger exists; the migration adding `portfolio_id`
   and `amount` to `transactions`; the derivation of holdings from rows
   (D13); then what reads it. Each a decision first.
2. **Order 2 items 2 to 4** after it: base currency and spot FX (its
   reference is a Part 8 column at a stated rate on a stated date); the
   price source; the personal IPS as a local file.
3. **Records and rules for the span and two-weights clarifications**, when
   a case asks.
4. **A window return** as a measure with a reference; not an extraction rule.
5. `reasoning` carried into the decision dict, so the CLI's line prints.
6. Replace the two verbatim benchmark few-shots (1.1, 1.3); the
   rebalancing few-shot with four percentages.
7. The hypothetical mode's instrument type ("11% into a new ETF").
8. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the
   IPS — both edit `docs/IPS.md`.
9. D9's wording; the workbook's `Decisions` sheet (D8, D9, D10–D14, `C91`).
10. "Optimization failed: None": the message, and the two-asset failure.
11. A golden line for 2.3.
12. **Company names, German phrasings, the softer 3.5**: logged, not
    built; decision 16 is their path (§5 items 13–15 of the previous
    handoff, unchanged).
13. **`group_by` as the subject kind of a compliance finding**, narrowing
    "which of my *positions* are over" to ticker subjects; the values
    already match. When a case asks.
14. **Dropping the block's `denominator` label** now that every share
    names its own.
15. **The two dead duplicates in `graph.py`** (`_get_next_agent_internal`,
    `_is_execution_complete_internal`), still uncalled.
16. **`test_portfolio_integration.py`**: rewrite with assertions or delete;
    it routes live on every pytest run.
17. **`ANTHROPIC_SONNET`'s id**: a one-line config fix, independent of
    decision 16.

---

## 6. Where we stand against the benchmark

12/12. Level 1, Level 2 and Level 3 in full. benchmark.md's notes are
current; nothing in it changed this sitting.

---

## 7. Next steps, in order

**The ledger's code, against Part 8.** First the test: `tests/test_ledger.py`
over Part 8 A (portfolio 3 as nine buys reproduces Part 1 to the cent)
and B (250 @ 80.01, cost basis 20,002.50, realized 247.50), written to
fail before any ledger function exists. Then the migration: `transactions`
gains `portfolio_id` and `amount`; a Dividend follows the same rule later.
Then the derivation, pure like `quant/allocation.py`: rows in, holdings
out, per D10–D13, raising on a sale that exceeds the quantity held. Then
the question of what reads it — whether `PortfolioHolding` becomes a
view of the ledger or the seed writes both — is its own decision. Each
comes as a decision first, with the loops named; the runner is not
expected to move until something reads the ledger.

**Before any of it**, if the owner opens the workbook: the `Ledger` sheet's
difference column must show zeros and its P&L % must read 9.99%. If not,
the sheet is wrong and Part 8 in the markdown stands.

### Later, with reasons

- The judgement half stays unstarted until benchmark.md has a Level 4 and
  the prediction ledger exists (DIRECTION.md).
- `measure`, `group_by` and `status` are the model's classification beyond
  intent; whether they become extraction is a question for the tool
  boundary, not for a prompt.
- README rewrite; `test_portfolio_integration.py`; the inline `sqrt(w'Σw)`
  copies; the hot-potato violation in `price_data_json`.

---

## 8. Rules learned the hard way

**Design the failure direction of a model-owned field.** The `status`
rule's "which are over" against "whether it complies" is not a line the
model draws; it set `breach` on 2.2, 2.3 and the list question alike. The
fix that held was not a wording but a rendering in which an over-set
field shortens the answer and hides nothing. Two readings, same hit rate,
different failure direction: choose the one whose miss is honest.

**A fixture that passes in both states is no check.** The first combined
test named AAPL, which breaches both of its clauses, so its rendering was
the same whether `status` was read or ignored. JNJ, within one clause and
over the other, was the fixture that could fail.

**Explain figures against the block, not the selection.** The clause text
a breach row cites quotes the band's other bound; the runner explains
every figure against `shared_data`'s findings, which are always the full
check. A test stricter than its instrument fails on a design that is
right.

**A "free" loop can be spending.** Five files with no test function and no
guard ran at collection; two routed live through the model, and pytest
collected their bare `test()` coroutine as a test as well, so each call
ran twice per run. The suite was ten seconds and two Haiku calls heavier
than anyone believed. Look for module-level calls in every `test_*.py`.

**Read the model's own output before choosing between readings; a record
beats a re-read; prose that names a plan classifies by proxy; a green
suite can hide a broken call site; registration is not reachability;
predict from the whole prompt; a refusal is an honest failure; write the
falsifier — still true.** Earlier handoffs' §8 have the examples.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 2.2

python src/agents/cli.py --portfolio 3

grep -rn "SymbolName" src/ tests/ --include='*.py'
git status --short
git log --oneline baseline-v1..HEAD
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~14s, still a few live calls from `test_portfolio_integration.py` | Do the components still work; does every table row derive its plan; does extraction read every recorded prompt the same way; does the node publish the block the checker reads; does each formatter select what its parameters say |
| CLI | ~3s, one call | What is it actually doing — the plan, the parameters (truncated before `measure`, `group_by`, `status`), what was asked back, the answer's header |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines, two pinned failures, `retries` when a plan was rejected). Blind to `measure`, `group_by`, `status`, `tickers` and the compliance mode |
| Benchmark runner | ~1.5min, cents | How many cases pass; the only loop that sees the compliance mode, the second turn, and a model-owned field set where it should not be (2.1, 2.2) |

`golden set → change → golden set → decide → then update expected.txt, its own
commit, with a yes`. Prediction first, twice for a prompt change, stop at
the second miss on a line. The runner is per capability commit.
