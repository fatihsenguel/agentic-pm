# AGENTIC_FINANCE — Session Handoff

**Session date:** 8 September 2026 (eighth sitting; regenerated at its end)
**Branch:** `vocabulary`, cut from `baseline-v1` at 3bebeb3. Twenty-five commits on top, plus the three sweep commits (KNOWN_GAPS, the benchmark notes, this file). Not merged, not pushed; the owner merges and pushes.
**State:** Green on every loop. pytest 397. Golden set sixteen queries, clean on the last three runs against `expected.txt`, no `retries` line ever printed; two lines pin failures (below). Runner **12/12** for the first time; 3.5 passes as a two-turn case. Commit count: `git rev-list --count baseline-v1..HEAD`.

Written for whoever picks this up cold.

**Regenerate this document at the end of each session rather than patching it.**
Generated context files rot faster than the code they describe. The version
this replaces described a router that planned, extracted and classified in
one model call; that router no longer exists. **Check every claim here
against the code before acting on it, including the owner's, including this
file.** Grep for the caller, not the registration, and for the reader of a
return value.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Owner's, dated, not regenerated. Wins over this file on direction; this file wins on state. Its Order 1 was built this sitting; Order 2 is next. Its last section says when to stop and ask. |
| `docs/benchmark.md` | **The definition of done.** 12 cases, 12 pass. Two status notes carry dated corrections rather than rewrites; the runner is the status. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Every case has a check. 3.5 is a tuple of two turns, each run after the previous final state; its check demands a resolution recorded on the decision, so the pass is memory's and not the model's reading of a typo. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Swept at the end of this sitting: every entry the sitting touched carries an "8 September (eighth sitting)" paragraph. Read at minimum: "The prompt shrink moved two lines" (the sitting's one failed prediction and what it taught), "Four wrong-faced answers" (three resolved, one half open), "`Allocation.total_value`" (the duplicate the fix left, and the rename decision), "Does the router stay a classifier" (what the model still decides). |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1–7. Part 7's IPS-4.1 and IPS-4.3 columns are now published figures the checker reads, not divisions it makes. **Never update it to match code output.** |
| `docs/IPS.md` | The owner's policy, synthetic. `ips.toml` is derived from it. Do not edit `docs/IPS.md`. |
| `docs/PM-Assistant — Roadmap.md` | Stale, header lists what is superseded. DIRECTION.md's Order supersedes its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.11% v 12%, JNJ 10.06% v 10%) and sit wherever the day's closes put them; the runner asserts structure. The live `as_of` was 2026-09-04 on every run this sitting (Labor Day on the 7th).

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
  intent, `measure`, `group_by`, confidence and a clarification question,
  and nothing else it emits is read.

### How the owner works

- Every item comes as a decision first: the shape, a recommendation, the
  rejected alternatives, which loop sees it and what it will show. Then a
  yes. Then one commit per layer, tests written first and seen failing,
  `git status --short` and the diff before each commit, and a yes on each.
- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting any symbol;
  grep for the caller and for the reader of a return value.
- **A prompt change is a hypothesis.** Line-by-line prediction in the commit
  message before the run; golden twice. **After the second failed
  prediction on a line, stop:** no rewording, bring a diagnostic that reads
  the model's own output. This sitting the shrink's prediction failed on a
  line that already carried two; the fix was structural (the mode moved
  into extraction), not a wording, and the owner chose fix-forward over a
  revert with the tree red on two loops in between.
- Never `commit -a`/`-am`, never `add -A`/`.`; name the files. Never push,
  rebase, amend, reset, stash. Never edit `.gitignore`; never reseed or run
  Alembic unasked. No attribution trailers.
- When a step needs the owner's result, ask for it and stop.

### What the owner does NOT want

A pure asyncio/regex deterministic version without LangGraph. Prompt rules
added to fix a routing defect (DIRECTION.md).

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q

python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt

python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 3.5

python src/agents/cli.py --portfolio 3
```

**397 passed.** New this sitting, all asserting: `test_analysis_node.py`
(the first pytest that runs the analysis node; it caught a broken call site
the suite had passed), `test_allocation_formatter.py`, `test_extraction.py`
(every golden query, benchmark prompt and recorded CLI prompt pinned to its
extraction, plus the clarifying cases and the reply vocabulary),
`test_router_extraction.py` and `test_router_plans.py` (the router with a
stubbed model: extracted fields and derived plans written over the model's),
`test_derived_plans.py` (every table row), `test_conversation_state.py`
(the previous turn carried, the record handed on). The caveat stands:
`test_portfolio_integration.py` returns booleans and passes unconditionally.

**The golden set has sixteen queries.** Two lines pin failures: the macro
query (`errors: 1`, since the first baseline) and "Should I rebalance my
portfolio?" (`errors: 1`, no target source). "How much did AAPL gain today?"
is pinned as the deterministic clarification extraction asks (a one-day
span), no longer the false refusal; "How much has AAPL gained?" beside it
pins the in-scope bare-ticker question as `data_fetch` with the analysis
plan. The three compliance lines pin the three-agent plan and have held on
every run since the derivation landed. `retries` has never printed.

**Runner 12/12.** 3.5: "Hows my APPL doing?" then "yes".

### Branches and tags

`vocabulary` is the working branch, cut from `baseline-v1` at 3bebeb3.
`baseline-v1` matches `origin/baseline-v1` at the last fetch. `compliance`
is merged into it. `wip/phase7-snapshot` holds rejected Compliance/IPS code;
nothing on it is scheduled. `wip/rag-early` and tag `rag-early-parked` hold
the deleted RAG code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`05034c6316c8`**, 12 migrations, linear. Not touched this sitting.

- **Portfolio 3, "Benchmark Portfolio" — use this one.** 9 positions, cost
  basis 284,500 plus 15,500 cash. Five golden queries run against it.
- **Portfolio 1** — January data; five golden queries. Do not modify.
- **Portfolio 2** — a leaked test artifact; one golden query. Load-bearing.
- **Reseeding portfolio 3 rewrites `Asset` metadata shared with 1 and 2.**

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never read or print it.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  (`claude-haiku-4-5-20251001`). `ANTHROPIC_SONNET` still points at the Haiku id.
- `config.features.observability_enabled` is **false** here. Do not turn it
  on without reading the KNOWN_GAPS entry on the router's own span.
- `portfolio_tool/__init__.py` opens a DB connection at import; the router
  prompt and `agents/extraction.py` import nothing from it at module level.

---

## 4. What the eighth sitting did

`git log --oneline baseline-v1..HEAD` for the list, in DIRECTION.md's Order 1.

**The block shapes the CLI questions exposed (decisions 1 and 2, nine commits).**
Every allocation line carries `pct_of_total`, the D2 share; the sector view
takes cash, its `total_value` is the D2 total and `sectored_value` is its own
denominator (4b003be); the node publishes the field and the sector block's
total (60c0df0); the checker's sector arm reads it instead of dividing
(62ddbcd); the formatter prints it (dbb8bc2) — "What share of my portfolio
is technology?" answers 27.73% of total at the 09-04 closes. Then
concentration as a view: `allocation_by_position`, Part 7's IPS-4.1 table
largest first (d361520), published (7958af5), read by the IPS-4.1 and 4.2
arms with the last division and `position_pnl` leaving the checker
(9c11bd1), rendered (317f4eb), named by `group_by: position` (f465e13) —
"What's my biggest position?" answers the table, SPY first. The checker's
only arithmetic is a subtraction per finding.

**The router restructure (decision 3, four steps, eleven commits).**
Registry: `IntentType.UNKNOWN` deleted (795f5e8), then `INTENTS` with both
prompts rendered from it and the synthesizer chain held to it at import,
byte-identical prompt, zero golden diff (8c35dee). Extraction:
`agents/extraction.py`, pure, tickers from the held and known symbols with a
typo of a holding asked about by name, periods from config's keys with any
other span asked about, a percentage near "vol" the cap and any other the
weight (56caa2c); wired before the model with every attempt's JSON
overwritten (f099101) — "Is my JNJ position over any limit?" carries JNJ,
"last month" asks which of five spans with no model call. Derived plans:
`REQUIRES` closed to the four dependencies the nodes raise on (0d60f18);
`TERMINAL`, intent and discriminator to terminal agent closed upward, the
plan written over the model's on every attempt, `validate_plan` replacing
two validators (bc2b555). Shrink: `combined` retired as the last intent
whose plan was the model's (ce7032f); the reorder-repair and the plan
alias deleted (e86841c); the prompt cut from 1574 to 1107 words (9364d24).

**The one failed prediction, and the fix.** The shrink moved "Is AAPL too
concentrated?" and runner 2.1 to `[ComplianceAgent]` alone: the model set
`policy_topic` on both once rule 7's plan brackets were gone, and the
lookup answered "the policy contains nothing on is aapl too concentrated?".
Read from the model's own output in one CLI session; the line was on its
third failed prediction; stopped. Fixed forward on the owner's call: the
lookup became extraction's — a saying verb after policy/IPS/investment
policy statement, or "anything in my policy about" (55dd80c), two golden
runs returning the line to its pin and 2.1 to PASS; then the topic left the
prompt as dead text, 1063 words (4d69e47).

**"today", and the pins that moved.** "today" next to a change verb is a
one-day span the vocabulary lacks; "today" alone is "as of now", so 3.3
holds (9c9be90). `expected.txt` moved by two lines on a yes: the false
refusal became the clarification, and the diagnostic "How much has AAPL
gained?" entered, pinned as designed (c086cd7).

**Conversation memory (decision 4, three commits).** The runner's two-turn
case first, its check demanding a recorded resolution (7c7fb16). Then the
state carries the previous turn's messages and the record of what it asked,
`run_agent_graph(previous=)`, `get_user_message` returning the last human
message (it returned the first), the decision dict carrying
`clarification_question` and `pending`, the CLI passing its last state
(1e00bc2). Then `resolve()`: a confirmation or a named ticker substitutes
into the original question, routed as if typed, the resolution recorded;
anything else is a new message (5fca3bd). Runner 12/12. Only the
unknown-ticker clarification has a record and a rule.

**Findings logged, not chased** (all in KNOWN_GAPS): "Optimization failed:
None" on a two-asset five-year backtest, the node formatting an absent
error key; the rebalancing few-shot names four percentages extraction would
ask about; `measure` set by the model under compliance is unread; the
duplicate `pct_of_denominator`/`pct_of_total` on total-denominated lines;
the BaseAgent grep was one file short (`risk_manager_agent.py`, itself
uninstantiated).

---

## 5. Decisions taken, and decisions pending

**Taken this sitting, each on a yes.**
- Share of total on every allocation line as `pct_of_total`; the checker
  reads it for every clause and divides nowhere.
- Concentration is allocation by position: a third view, the same line
  shape, named by `group_by: position`; no cash line, no new `measure`.
- Extraction owns tickers, periods, the two percentages and the compliance
  mode; the model's values for them are never read. A typo within one edit
  of a holding asks by name, no stoplist. "today" with a change verb is a
  span; alone it is not.
- Plans are derived: `TERMINAL` and `REQUIRES`; `combined` retired; the
  reorder-repair and the `execution_plan` alias deleted.
- The prompt shrunk to what the model decides. Pending decision 6 decided
  keep: the three failed edits stay as registry text and an intent example.
- The two `expected.txt` moves.
- Memory as an extraction rule over a record of what was asked; the model
  never sees the history.
- Three departures from one commit per step, each stated: the node's call
  site inside the quant commit (4b003be); two commits for extraction and
  for derivation; the alias deleted with the repair.

**Pending, owner's call — bring them up before writing code.**
1. **A selection axis for the compliance report** (`filter`, or reading
   `tickers` in the compliance formatter): "Is my JNJ position over any
   limit?" carries JNJ and still gets the full report. The `group_by`/
   `filter` entry in KNOWN_GAPS has the shape.
2. **The rename to named denominators**: `pct_of_denominator` equals
   `pct_of_total` on asset-class and position lines. Touches the runner,
   two fixtures and the formatter.
3. **Records and rules for the span and two-weights clarifications**, when a
   case asks; today a reply to either is a new message.
4. **A window return** as a measure with a reference, the capability behind
   "last month" and "today"; not an extraction rule.
5. **Deletions**, each its own commit after a grep: `AgentTask` and the
   task list (router-written, unread), `target_return`,
   `rebalance_threshold`, `parameters.portfolio_id`, `is_multi_step`,
   `requires_confirmation`, `conversation_history` and `available_agents`
   on the prompt builder, `route_sync`, `detect_intent_simple`,
   `stream_agent_graph`, `get_graph_mermaid`, `prompts.py`, the unreachable
   check in `_validate_decision`, `state.add_warning`, the dead `"3Y"`
   period default in `nodes.py`.
6. `reasoning` carried into the decision dict, so the CLI's line prints.
7. Replace the two verbatim benchmark few-shots (1.1, 1.3); the
   rebalancing few-shot with four percentages.
8. The hypothetical mode's instrument type ("11% into a new ETF").
9. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the
   IPS — both edit `docs/IPS.md`.
10. D9's wording; the workbook's `Decisions` sheet (D8, D9, `C91`), own
    commit via `git add`.
11. "Optimization failed: None": the message, and the two-asset failure.
12. A golden line for 2.3.

---

## 6. Where we stand against the benchmark

12/12. Level 1, Level 2 and Level 3 in full. benchmark.md's Level 2 note and
the 3.5 note carry dated corrections; Part 4's item 5 is marked done.

---

## 7. Next steps, in order

**DIRECTION.md's Order 1 is built.** Order 2 is next: make it the owner's —
a transaction ledger and cost-basis method; a base currency and FX source;
a price source that can be defended with real money; the personal IPS, the
type vocabulary grown one clause at a time; a Part 8 reference for the real
portfolio before any figure about it is trusted. Each is a decision first,
a hand-computed reference before code, and the loops named.

Before or beside it, the small items from §5 that the sitting's work
exposed: the compliance selection axis (1), the rename (2), and the
deletions (5), which are the cheapest way to make the router's surface
match what is read.

### Later, with reasons

- The judgement half stays unstarted until benchmark.md has a Level 4 and
  the prediction ledger exists (DIRECTION.md).
- `measure` and `group_by` are the model's last classification beyond
  intent; whether they become extraction is a question for the tool
  boundary, not for a prompt.
- README rewrite; `test_portfolio_integration.py`; the inline `sqrt(w'Σw)`
  copies; the hot-potato violation in `price_data_json`.

---

## 8. Rules learned the hard way

**Prose that names a plan classifies by proxy.** Rule 7's brackets held the
model's topic flag in place; removing them as dead text moved two lines
the text never mentioned. A shrink is a hypothesis about every line the
removed text touched, not only the lines that quote it.

**A green suite can hide a broken call site.** `allocation_by_sector` gained
a parameter and pytest stayed green because nothing ran the node. Write the
test that runs the node before changing what it calls.

**The failure direction of a rule is part of its design.** The lookup
pattern misses into the fuller portfolio check; the model's flag missed into
"the policy contains nothing on this". Two rules with the same hit rate are
not the same rule.

**Read the model's own output before choosing between readings.** One CLI
session showed `policy_topic` set on both moved lines; no golden field could
have. The runner and the CLI see fields the golden set does not print.

**A record beats a re-read.** The clarification's text was not the memory;
a structured record of what was asked was, and the resolution rule needed
only that.

**Registration is not reachability; shown a list, a model picks from it;
predict from the whole prompt; structure, not verdicts; a refusal is an
honest failure; write the falsifier — still true.** Earlier handoffs' §8
have the examples.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 3.5

python src/agents/cli.py --portfolio 3

grep -rn "SymbolName" src/ tests/ --include='*.py'
git status --short
git log --oneline baseline-v1..HEAD
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~25s | Do the components still work; does every table row derive its plan; does extraction read every recorded prompt the same way; does the node publish the block the checker reads |
| CLI | ~3s | What is it actually doing — the plan, the parameters, what was asked back, what a reply resolved to |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines, two pinned failures, `retries` when a plan was rejected). Blind to `measure`, `group_by`, `tickers` and the compliance mode |
| Benchmark runner | ~1.5min, cents | How many cases pass; the only loop that sees the compliance mode and the second turn |

`golden set → change → golden set → decide → then update expected.txt, its own
commit, with a yes`. Prediction first, twice for a prompt change, stop at
the second miss on a line. The runner is per capability commit.
