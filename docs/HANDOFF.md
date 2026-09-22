# AGENTIC_FINANCE — Session Handoff

**Session date:** 22 September 2026 (thirty-third session), begun about 11:50 UTC. Regenerated at its end. The thirty-second session ran on the 21st and closed the full test at the end of Order 4.
**Branches:** `intents`, cut from `baseline-v1` at **33769f6** before the first commit, eleven commits — **merged `--ff-only` by the owner after this document was first written**, so the trunk stands at **8201102**, one ahead of `origin/baseline-v1`. Then `arc`, cut from the trunk at 8201102, **two further commits, unmerged**: the interlude was re-scoped after the merge. **Thirteen commits in the session.** The owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1926 passed, 6 xfailed**, down from 1943 by the seventeen tests decision 51's deletion took with it — the measured number and the corrected prediction agreeing exactly. **The runner is 15/18, 0 failing, 3 blocked**, down from 16/18: case 2.1 now routes `risk_analysis` instead of `compliance` and that is this session's real finding. **The golden set ran twice, byte-identical, and `expected.txt` moved six lines across two queries.** Decision 51 is **executed**; the pending list stands at eleven, unchanged.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Sections whose claims were checked again this session and
still hold are kept word for word; the rest is rewritten.

**The interlude between Orders 4 and 5 has begun.** DIRECTION.md now
carries it as an unnumbered paragraph under Order 4 (d221a8a), and
KNOWN_GAPS holds the four reasons, the eight steps and how the corpus is
built. **Step 1, the deletion, is done. Step 2 is the corpus and is the
next session.**

**And the arc was re-scoped at the very end of the session, after the
merge, on the owner's question: if Order 5 changes so much, why test and
fix what will change?** The answer is that a corpus entry's parts have
different lifespans — the question, the figures, the cited clauses and
the turn sequences survive the refactor; the intent and the plan do not.
**So Order 5 now sits between steps five and six.** Before it: the
deletion, the corpus, one run to capture the baseline, a fix list narrowed
to pipeline arithmetic, the cleanup. After it: the CLI as the client, the
front door and the public repository. **The rule that decides future cases
too: what belongs in the interlude is decided by what survives the
refactor.**

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1 to 4 are built and Order 4's closing condition is met. **Revised twice on 22 September**: an unnumbered interlude between Orders 4 and 5, and then re-scoped so that **what belongs in it is decided by what survives the refactor** — the corpus and its one run before Order 5, the CLI, the README and the demo recordings after it. The Order numbers did not move, and the direction did not change. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. **172 lines start `**Trigger:**`.** **Start with "The interlude between Order 4 and Order 5, and how the corpus is built"** — it is the frame for every session until Order 5 opens. Then "Deleting three intents moved case 2.1 to risk_analysis", which is this session's finding. **No entry names "pending decision 51" any more**: eleven are RESOLVED and five moved to decisions 13, 45 and 52. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, **11 pass, 2.1 blocked**. Level 4: 4.2, 4.4, 4.5 and 4.6 pass; 4.1 and 4.3 blocked. **15/18, as the runner reported it at 12:51 on 22 September.** Unchanged this session and out of its scope; its status column is not maintained by hand — the runner is the status. **Read Part 2, not only the case list**, and **Part 5, which is the demo plan the interlude executes rather than replaces.** |
| `tests/golden/expected_values.md` | Hand-computed reference, Parts 1 to 17. **Not opened this session.** Never update it to match code output. |
| `tests/golden/expected.txt` | **Twenty-one lines**, one pinned failure. **Six lines changed on 22 September** — the macro and optimisation queries now refuse. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Eighteen cases, unchanged, **run once at 12:51 and four single cases after it**. **Its checks read every answer** — `_answer(state)` at line 160 is `state["final_response"]`, read at thirty-two sites — but it **shows** nobody one: `redirect_stdout` (2501, 2515) discards the printed console trace and the run prints verdict lines alone. |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, **not opened this session**. Saved in Excel at b07bc33 by the owner at the end of the twenty-ninth session. Parts 9 C, 11, 14, 15, 16 and 17 have no sheet. |
| `docs/IPS.md` | The policy, synthetic, 17 clauses. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. Unchanged. |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027, none scored. Unchanged. No score is written into it by the system, ever. |
| `docs/PM-Assistant — Roadmap.md` | Stale; DIRECTION.md's Order supersedes it. |
| `docs/workflow.md` | Stale, and a pasted conversational reply with emoji in its headers (KNOWN_GAPS). |

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`.
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half that is tools and done,
and a judgement half whose tools are in the graph with their references.
The router is scaffolding until the tool layer is complete.
**No deadline. Correctness over speed. Scope creep is the risk.**

### Why the interlude, in one paragraph

Four reasons, the owner's, recorded in full in KNOWN_GAPS. No loop shows
an answer, so there is no feel for what the system does. Order 5 replaces
the router, which kills the golden set — the loop that cannot verify it —
so a corpus of prompts with hand-written answers is the precondition.
A first demo is a test: recorded runs that stand without narration. And
what is actually missing should be known before anything is added.
**The corpus grows inside benchmark.md and expected_values.md, hand-written
before it is run, never updated to match output.**

### Design principles

Checked against the code again this session; what the deletion adds is marked.

- **Hot potato — agents never see raw data.** Unchanged and unexercised
  this session: no CLI run was made.
- **No number from a model.** **The deletion removed the one live path
  that broke it**: `_format_optimization_response` printed "Return:
  26.49%", a forward return stated as a number, which invariant 7 forbids.
  The query that reached it now refuses.
- **Policy lives in config, not code.** **Read live in the scoping:**
  `config.MacroConfig`, `OptimizationConfig` and `BacktestConfig` were
  deliberately left standing when their agents went, because a config
  decision does not belong inside a code deletion. `config.macro` still
  has a live reader — `data_agent.py:818` takes the risk-free rate from
  the 10Y Treasury yield in `macro_data`.
- **One arithmetic path.** Unchanged; `distance_value` still has exactly
  one writer, `compliance.py:102`.
- **Raise, do not repair.** **Held through the deletion.**
  `rebalance_agent_node` had its target read rewritten rather than
  repaired: it reads `shared["target_weights"]`, a key nothing publishes,
  and raises. No default target was invented. **Still broken where it
  matters most:** the router catches every exception from the model call
  and returns `None`.
- **Compliance is a gate, not a tool.** `gate_node` is in neither
  `schemas.AGENTS` nor `graph.AGENT_NODES`. Unchanged.
- **References before code.** Unexercised this session.
- **The registry is the prompt.** **This session is the evidence, and it
  cost a benchmark case.** Removing three intent descriptions moved case
  2.1 — a question mentioning none of them — from `compliance` to
  `risk_analysis`. `compliance` and `risk_analysis` keep their
  descriptions byte for byte. **With an LLM classifier there is no local
  change to the prompt.**
- **A formatter states what the data says and never what the system is.**
  Still broken in two places, and one of them gained a third instance:
  `OUT_OF_SCOPE_RESPONSE` now answers "What is the current market
  regime?" with a sentence listing screening, forecasts, tax and orders,
  none of which is market conditions.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
- **The reference before the code**, each time, in its own commit.
- **A paid loop says first what it will fetch and store, table by table**,
  read off the store and the clock, and says after what moved. **Five paid
  runs this session and every table prediction exact** — and the
  prediction was "nothing", which held: the golden set now writes to no
  table at all.
- **A prompt change is a hypothesis, written before the run.** The
  prediction for this deletion went into commit 7e27d47's message before
  any of it ran. **One of the two lines missed**, to its stated second
  guess.
- **Measure before deleting, and say the number twice.** The measurement
  before said seventeen tests would fall; pytest said 1926. It was wrong
  once by one and corrected mid-session, in a commit message, before the
  run that would have exposed it.
- **Grep the caller, not the registration**, and **grep the writer the
  reader reads** — and now **grep the package, not three files**: the
  first deletion broke collection at 34 errors because
  `agents/__init__.py` re-exported the agent.
- No emoji in anything newly written. A count I predict is a count I add up.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect — **and this session declined to add one even at the cost of
a benchmark case**. My real portfolio's data in the repo: Order 6, last. No
cached holdings table; no fallback rate, currency or policy; no adjusted
close; no environment switch for which policy runs. **No invented figures as
a runtime source, and no price a stock will reach anywhere.** No widening of
the router's schema to make it a better classifier. No NOPAT at the
company's filed tax rate. No formatter sentence that states the system's
status. **No number, threshold or weight from a model; no row written into
the watchlist by the system; no outcome decided by the formatter or the
model.** **No score written into the ledger by the system; no partial
credit; no prediction scored before its date.** **No long quote cut in code
to pass the cap, no third wording after two misses.** **No exception
swallowed into a `None` that crashes somewhere it cannot be explained.**
**No forward return as a number** — the one path that printed one is
deleted. **And no sentence in the record that names an audience instead of
a requirement.**

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q

python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/tmp/golden_err.txt
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py

python src/agents/cli.py --portfolio 3
```

**Four of the five run. The CLI was not run this session at all** — no
answer was read by hand, which is worth knowing before trusting anything
here about answer text.

**pytest: 1926 passed, 6 xfailed**, about 6 seconds. Was 1943 at session
start. The seventeen that went are decision 51's, itemised in §4.

**Golden set: twenty-one lines, one pinned failure** ("Should I rebalance
my portfolio?", errors 1). **Run twice on 22 September at 12:43 and 12:45,
byte-identical to each other.** `expected.txt` updated at 4f7ca89.

**The runner: 15/18, 0 failing, 3 blocked**, run once at 12:51. 4.1 and
4.3 blocked as before on the PHI-2.1 stop; **2.1 newly blocked** because
the router plans `[DataAgent]` under `risk_analysis` and ComplianceAgent
never runs.

### What the deletion did, and what it cost

**Decision 51 executed in three commits**, backtest then optimisation then
macro, each leaving the tree green. **4,459 lines by `wc -l` on the day**
— the decision's own total of 4,094 was 365 short of its own five
components, corrected at 2cbecca.

| Measure | Before | After |
|---|---|---|
| `schemas.INTENTS` | 11 | **8** |
| `schemas.AGENTS` | 10 | **7** |
| `schemas.REQUIRES` | 6 entries | **4** |
| pytest | 1943 | **1926** |
| runner | 16/18 | **15/18** |
| glyphed answer headers | 7 | **4** |

The eight intents: `clarification_needed`, `compliance`, `data_fetch`,
`ledger`, `out_of_scope`, `rebalancing`, `research`, `risk_analysis`.
The seven agents: `ComplianceAgent`, `DataAgent`, `LedgerAgent`,
`PortfolioAnalysisAgent`, `RebalanceAgent`, `ResearchAgent`,
`ScreeningAgent`.

**The finding, and it is the session's most important output.** Case 2.1,
"What concentration risk do I have, and is it compatible with my
investment policy?", routed `compliance` with the three agents and now
routes `risk_analysis` with `[DataAgent]` alone. **Deterministic over
three runs.** Nothing that decides it changed: `compliance` and
`risk_analysis` keep their descriptions byte for byte, `TERMINAL`,
`REQUIRES` and `derive_plan` are untouched and pytest holds all three.
What changed is the number of options the one LLM call chooses between.
**Not fixed**: narrowing `risk_analysis`'s description is a prompt rule
bought to fix a routing defect, which DIRECTION.md forbids and Order 5
would make us pay for twice. Logged at bb163b3 with what it owes the
corpus session.

### Branches and tags

`baseline-v1` is the trunk and stands level with `origin/baseline-v1` at
**8201102**, one ahead of `origin/baseline-v1`: the owner merged `intents`
`--ff-only` after this document was first written. `arc` carries the two
re-scope commits and is unmerged.
**`intents-parked` is cut at addfbc7**, the parent of the first deletion
commit: it holds the tree that still had the three intents. `rounding`,
`halves` and `judgement` are merged and older, with `gate`, `thesis`,
`reader`, `research`, `score`, `publish`, `range`, `keys`, `node`,
`filer`, `bridge`, `consolidate`, `selection`, `compliance` and
`vocabulary`. `wip/phase7-snapshot` holds rejected Compliance/IPS code.
`wip/rag-early` and tag `rag-early-parked` hold the RAG code.
`quant-inventory-parked` at 8d87455 holds the tree before the seventeenth
session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`2445c12e728c`**, 26 migrations, linear, all applied; no migration this
session. No reseed. **What this session wrote: nothing.** Five paid runs
— two golden, one runner, four single cases — and every table is where it
was:

- `daily_prices` **7,009, unchanged**, last close still 2026-09-18.
- `asset_fetch_metadata`: the nine holdings still stamped **2026-09-21
  14:24:06 to 14:24:09**, GOOGL **14:28:40**. **The one-day price
  interval ran out on 22 September at 14:24 and 14:28** — every run this
  session was before that, which is why nothing was fetched. **The next
  session's first paid run will fetch**, and Monday the 21st has closed
  since, so a close will be stored.
- `api_call_logs` **2,480, unchanged**. `api_quotas`'s last row is still
  `daily_yfinance_2026-09-21` at 19; **no row exists for the 22nd**.
- `macro_data` **209, unchanged**, newest `created_at` still 2026-09-21
  14:33:47 from the previous session's CLI batch. **A golden run no
  longer writes here at all** — three KNOWN_GAPS entries closed on that
  measurement.
- `document_readings` **5 rows, unchanged**; `filed_facts` 28,787,
  `filers` three rows, `filed_documents` one, `filed_fetch_metadata` two.
  **The seven-day filings intervals ran out on 22 September at 22:17 and
  run out on 23 September between 00:03 and 01:38** — the first of them
  after this session ended.

Unchanged: `assets` ten rows, GOOGL the tenth and not held, its asset
class, sector and instrument type still blank — the watchlist entry
states them (decision 63); `financial_statements` 65 and `shares_history`
947, neither a source.

**There is no holdings table.** Portfolio 3, "Benchmark Portfolio", is the
only portfolio: nine ledger rows, cost basis 284,500 plus 15,500 cash,
USD, policy `ips.toml`. GOOGL is not held. Adobe has no assets row and no
facts.

**The live figures, from the thirty-second session's hand recomputation
and not re-checked here:** invested **392,947.50**, cash 15,500.00, total
**408,447.50**, Equity 284,332.50, Technology 116,604.00, at the
2026-09-18 closes.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row; the gate, over the portfolio as it would be |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py`, `test_screening.py` | the screening node, by `nodes.PHILOSOPHY_PATH` (decision 30) |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py`, `test_watchlist_loader.py`, `test_watchlist_predictions_loader.py` | the screening node, the ledger node, the research node, the gate node |

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files.
- **Anthropic has credits.** The one-line check in §9 costs nothing; run it
  before spending a loop on finding out. **When the balance is empty it
  fails with a 400 `invalid_request_error` naming the credit balance** —
  not a 401. **From inside the system it looks like nothing of the sort:**
  every question returns `intent: None` and `Router error: 'NoneType'
  object has no attribute 'intent'` (KNOWN_GAPS).
- `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU` for the router. **`ANTHROPIC_SONNET`
  is `claude-sonnet-5`**, used by the reader, the proposer and the view, and
  **it refuses a temperature**; none of the three sends one. The router's
  stronger-model switch sends 0.0 and would fail (KNOWN_GAPS).
- **The `anthropic` SDK is 1.2.0**: `messages.create` takes `output_config`
  for structured output, and a schema's `anyOf` of two object shapes is
  held by it.
- **yfinance is 1.7.0 and its `end` is exclusive**, which is why a fetch on
  an open trading day stores nothing new.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing. Nothing was fetched from EDGAR this session.
- **What this session cost.** Five paid runs: two golden at about $0.039
  each, one runner at about $0.039, and four single-case runs at roughly
  $0.001. **On the order of $0.12.** Treat it as an estimate: **nothing
  records a model call's tokens** and `api_call_logs` is provider calls
  only (KNOWN_GAPS).
- **The price provider** is `nodes.price_provider()`; **the models** are
  `nodes.reading_model()`, `nodes.proposal_model()` and
  `nodes.view_model()`; the EDGAR provider is `nodes.edgar_provider()`.
- `config.toml` carries five fetch intervals: prices 1 day, filings 7,
  earnings 7, profile 30, shares 30. A missing key raises at its reader.
  **Its `[macro]`, `[optimization]` and `[backtest]` sections stand**
  although two of the three now have no consumer — left deliberately, and
  `hawkish_threshold`/`dovish_threshold` moved to decision 52.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; `config.toml` is read relative to the project
  root, so scripts run from the root.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router.
- **Several questions can be sent to one CLI process** with
  `printf '%s\n' 'q1' 'q2' ':q' | python src/agents/cli.py --portfolio 3`.
  Each is its own graph run with its own request id, and **the CLI's
  identical-answer check works across them**. Use `printf '%s\n'` with each
  question as its own argument: a question containing an apostrophe breaks a
  single-quoted format string.
- **A single benchmark case runs with `--case`**, one Haiku routing, about
  $0.001 — far cheaper than repeating the whole runner to chase one case.
- **Tests import from other tests.** The last sessions' imports stand.
- **Tests delete rows from the suite's copy they did not write**:
  `test_screening_node.py` Alphabet's and JPMorgan's facts, filers and the
  ticker table, `test_filed_facts_fetch.py` Apple's facts.
- **A scratch copy of the tree runs the suite against a changed file
  without touching the repository.** From the working tree,
  `cp -R src tests docs alembic config.toml ips.toml philosophy.toml
  watchlist.toml pyproject.toml <copy>/`; copy `data/portfolio.db` into
  `<copy>/data/`, then from inside it
  `DATABASE_URL=sqlite:///<copy>/data/portfolio.db USE_MOCK_QUOTA=True PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 <repo>/.venv/bin/python -m pytest -q -p no:cacheprovider --color=no <tests>`
  after deleting its `__pycache__`. **Pass `--color=no`** or the failing
  tests' names come back as colour codes.
- **`nodes.utc_today()`** is the ledger node's clock; the screening node
  reads the clock inline, so **a research answer's as-of is the day of the
  run**.
- **zsh does not split an unquoted variable into words**, and **has no
  `tac`**. **A `grep -c` that finds nothing exits 1 and stops a `&&`
  chain.** **A `%` inside a `printf` format is written `%%`.** **BSD `sed`'s
  `0,/re/` first-occurrence form is a GNU extension and silently matches
  nothing on macOS.** **`cat -A` is GNU; BSD `cat` has no `-A`.** **A
  backslash inside an f-string expression is a syntax error in 3.10.**
  **`awk`'s POSIX regex has no `\s`** — use `[ \t]*`, or a pattern anchored
  with `^\s*` silently matches every line.
  **`--include='*.py'` must be quoted in zsh** or it is glob-expanded and
  grep reports "no matches found".
- **What is no longer in the tree** (do not look for it). From earlier
  sessions: `portfolio_tool/rag/`, `tools/data_tools.py`,
  `tools/macro_tools.py`, `tools/analytics_tools.py`,
  `portfolio_tool/analytics/`, `scripts/run_metrics_update.py`,
  `scripts/update_all_assets.py`, `agents/risk_manager_agent.py`,
  `optimization/risk_parity.py`, `tests/test_design_violations.py`,
  `tests/violation_detector.py`; and inside surviving files, VaR, CVaR,
  drawdown, Sharpe, Sortino, Calmar and `RiskMetricsCalculator` from
  `quant/risk_metrics.py`, shrinkage and exponential covariance, the
  frontier, min-vol, target-return and target-volatility optimisers,
  `DataAgent.get_risk_metrics_tool`, and the two `marketable_securities`
  fields of the figures block. **New on 22 September, decision 51:**
  `agents/macro_agent.py`, `agents/optimization_agent.py`,
  `agents/backtest_agent.py`, `portfolio_tool/backtest/` and
  `portfolio_tool/optimization/` whole; `tests/test_macro_node.py`;
  `macro_agent_node`, `optimization_agent_node`, `backtest_agent_node`,
  `_format_macro_response`, `_format_optimization_response` and
  `_format_backtest_response` in `nodes.py`; `protocols.BacktestMetrics`,
  `RegimeType`, `RegimeSignal`, `TaskType.BACKTEST`,
  `TaskType.ANALYZE_REGIME`, `TaskType.MACRO_ANALYSIS`,
  `AgentRole.BACKTEST`, `AgentRole.OPTIMIZATION`, `AgentRole.MACRO`; and
  four router-prompt teachings, two German one-liners and two few-shots.
  **No live answer path computes or prints Sharpe or Max Drawdown any
  more** — the backtest answer was the last, and it went with
  `portfolio_tool/backtest/metrics.py`. Checked rather than assumed:
  what survives is `PortfolioResult.to_summary` in the BaseAgent DTO
  layer, which would print a Sharpe line if it were ever called with one,
  and nothing in the graph calls it (decision 54); and `config`'s dead
  `target_sharpe_ratio`, `calculate_rolling_sharpe` and
  `max_drawdown_threshold`, left standing with their sections. The risk
  formatter states in words that VaR, expected shortfall and drawdown are
  not computed, which is Part 3b working.

---

## 4. What the thirty-third session did

`git log --oneline 33769f6..HEAD`, **eleven commits**, 36 files, 566
insertions and 5,844 deletions. Three tasks, in the owner's order.

**The loops.** pytest at session start 1943, at the end **1926**, run
after every deletion commit. The golden set ran **twice** at 12:43 and
12:45, byte-identical. The runner ran **once** at 12:51, then four single
cases to chase what had moved. **Every paid run's table prediction was
exact, and the prediction was "nothing".**

**Task 1 — the why and the arc, recorded.**
- **3ac93ea** one KNOWN_GAPS entry carrying the four reasons for pausing,
  the eight steps of the interlude, and how the corpus is built: inside
  benchmark.md and expected_values.md, five kinds not to be mixed, the
  size discipline, what is pinned exactly against what is pinned by
  invariants. **Step 6's count was stated as absent rather than carried**:
  "22 German debug strings across five files" could not be reproduced, a
  grep finding German console text in seven files under `src/`.
- **d221a8a** DIRECTION.md gains the interlude as an **unnumbered**
  paragraph under Order 4. Unnumbered so that nothing already written
  about Order 5 has to be read twice: decision 45, this file, benchmark.md
  and the new entry all name it.
- **0c4dba9** the owner's correction, and the better rule came from it.
  Reason 3 was written as recorded runs "that make a hiring manager
  interested". That is a reaction standing in for a specification: it
  carries the quality bar by implication and leaves it unwritten. **The
  record names the requirement, not the audience** — the bar is that the
  runs stand without narration, and both terms are out of the repository.

**Task 2 — the correction owed.**
- **addfbc7** the claim that the runner discards every answer is false.
  `_answer(state)` at `run_cases.py:160` is `state["final_response"]` and
  the checks read it at thirty-two sites. `redirect_stdout` discards the
  printed console trace. The true part survives on its own: the answer
  reaches the checks and reaches no person. The entry was retitled, its
  old title having been the false claim, and §0, §1, §7 and §9 of the
  previous handoff corrected.

**Task 3 — decision 51's deletion.**
- **`intents-parked`** cut at addfbc7 before the first deletion commit.
- **The measurement first.** Thirty collected tests touched the three
  intents, not the nine the entry estimated — `test_rebalance.py` has zero
  references to any of them and all seven of its tests survive.
  **Sixteen of the thirty had no subject left; fourteen were edited in
  place.** Predicted 1926 after one correction mid-session; measured
  **1926**.
- **7e27d47** backtest first, because `backtest_agent_node` reads
  `optimal_weights` and cannot outlive the optimiser. **The prediction for
  the golden set was written into this message before anything ran.**
- **aa6ed13** optimisation. Its one non-deletion is
  `rebalance_agent_node`'s target read, rewritten to
  `shared["target_weights"]` so the raise stops naming a deleted agent.
- **868e9f5** macro, with the `taa_signal` block, flagged and scoped
  rather than swept in.
- **4f7ca89** `expected.txt`, six lines across two queries, on the owner's
  yes after the diff was judged an improvement.
- **bb163b3** the finding: the runner falls to 15/18.
- **2cbecca** decision 51's two arithmetic errors corrected: 4,458 from
  its own components and 4,459 measured, not 4,094; eleven intents to
  eight, not seven.
- **ea68a7d** the sweep: eleven of the sixteen "pending decision 51"
  entries RESOLVED, five moved to decisions 13, 45 and 52.

**What the deletion was wider than.** The entry named five files. The
first commit needed seventeen, because `agents/__init__.py` re-exports
each agent and deleting the file without the export gives **34 collection
errors**, not a working tree. The rest of each agent's surface came with
it: DTOs in `protocols.py`, enum members, the tracer's colours, the router
prompt's teachings, and two module docstrings describing packages that no
longer exist.

**Not done, on purpose.** The corpus, which is the next session. Decision
75's implementation. Decisions 17, 75 and 76, all out of scope by the
owner's word. The rebalancing dependency-table bug, the owner's and not
this session's. The four remaining glyphed headers. `config`'s three dead
sections and `validators.validate_optimization_request`, left by the
owner's scoping. **And no CLI run at all**, so nothing in this session
read an answer by hand.

---

## 5. Decisions taken, and decisions pending

**Executed this session: one.**

- **51. The four intents outside the benchmark roster.** Decided on the
  21st, executed on the 22nd in three commits. `macro_analysis`,
  `optimization` and `backtest` deleted with their agents and the two
  packages only they imported; `rebalancing` kept, because benchmark.md
  Part 2 puts drift in scope in words. **Cost: one benchmark case.**

**Pending — decide before writing code. Eleven by count, unchanged:**
10, 12, 13, 16, 17, 22, 45, 48, 52, 54 and 76. The cap is 25. **Nothing
was opened and nothing closed**: 51 was decided rather than pending when
this session began.

10. A window return as a measure with a reference.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the
    IPS. **Now carrying more weight than before:** `rebalance_agent_node`
    reads `shared["target_weights"]`, which nothing publishes, and the
    out-of-scope text has a third question reaching it whose subject it
    does not name.
16. Company names, German phrasings, the softer 3.5. **The corpus session
    is where this is written out**, extraction variations generously.
17. **The selection axis.** Four sites. Three values logged, `filter`
    never built. **Case 2.1 now lands in the synthesizer's stub**, which
    is that entry's neighbourhood.
22. Volatility over as-traded closes or a total-return series.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, 11 and 36.
    **`ExtractedParameters` moved onto this trigger**: `portfolio_value`
    and `max_volatility` both lost their last reader to the deletion.
48. Part 13 E's item 7, second half only.
52. The Yahoo-fed tables: delete or keep. **`hawkish_threshold` and
    `dovish_threshold` moved onto this trigger.**
54. BaseAgent's tool loop and the three `AgentConfig` fields: delete, its
    own sitting. `protocols.OptimizationMethod`, `PortfolioConstraints`
    and `TAARule` survive here.
76. Whether money and ratios are computed in decimal. Three candidate
    shapes, none costed, no recommendation attached.

- **The interlude between Orders 4 and 5** (owner's): **step 1 done, and
  the arc re-scoped after the merge** so that Order 5 falls between steps
  five and six. Step 2, the corpus, is the next session. **Step 4 is now a
  rule rather than a queue**: only pipeline arithmetic is fixed before
  Order 5, so decisions 75 and 76 belong there and decision 17, a
  selection axis across four formatters, probably does not.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: **11/12**, 2.1 newly BLOCKED. Level 4: 4.2, 4.4, 4.5 and
4.6 PASS; 4.1 BLOCKED by decision naming D36; 4.3 BLOCKED at the policy.
**15/18, confirmed by a run at 12:51 on 22 September.**

**The fall from 16 is a routing regression and not a lost capability.**
`ComplianceAgent` runs, its arithmetic is unchanged, and the three
compliance wordings the golden set pins still reach it. One wording of one
case does not. The runner's own message says so: *the agent exists, the
routing for this wording does not*.

What the runner cannot see, unchanged: whether the view is a defensible
read of the claims it cites; whether the gate's arithmetic is right, which
is pytest's against Part 17; whether the range's ends are right; any due
prediction until 2027; whether a quote supports its claim; and whether any
answer it renders reads well — its checks ask for a date, a clause id, a
trade line or a percentage, and no more.

**The eight findings from the full test are all still open**, none of
them fixed this session and none of them meant to be.

---

## 7. Next steps, in order

**1. The corpus — step 2 of the interlude, and the next session.** Prompts
with the answers the owner wants back, hand-written before any are run,
grown inside `docs/benchmark.md` and `tests/golden/expected_values.md`.
Five kinds, not mixed: the eighteen spine cases unchanged; extraction
variations generously and intent-classification variations sparingly;
refusals; questions nothing handles, grown into the existing entry;
and **multi-turn sequences, which matter most and barely exist** — one
benchmark case is two turns. **Read the interlude entry in KNOWN_GAPS
first.** **And it owes case 2.1 a pinned wording**, this session having
shown that a spine case can move on a prompt change that does not mention
it.

**2. Decision 75's implementation.** The check written first against Part
7, then `compliance._finding` taking the line's market value and raising
without it, then the rounding helper. Answer text changes, so the runner
runs against it.

**3. Then step 4's narrow fix list and step 5's cleanup, and Order 5 may
open.** Decision 17 is not in that list under the re-scope: it is a
selection axis across four formatters, and presentation is rebuilt after
Order 5 rather than before it.

### Later, with reasons

- **The trunk.** `intents` is merged; **`arc` is not**.
  `git switch baseline-v1 && git merge --ff-only arc` takes the two
  re-scope commits. The trunk is one ahead of `origin/baseline-v1` and
  the runner is 15/18 on it.
- **The first paid run of the next session will fetch prices.** The
  one-day interval ran out at 14:24 and 14:28 on 22 September, and Monday
  the 21st has closed since, so a close will be stored.
- **The filings intervals ran out on 22 September at 22:17 and run out on
  23 September between 00:03 and 01:38.**
- **The router's swallowed exception** — a failed model call should raise
  with the provider's own message.
- **The emoji**: **four** answer-text headers now, not seven — the
  out-of-scope header, the policy lookup at two sites, the compliance
  check at two sites, and the rebalancing header. One commit, the runner
  run against it. The console glyphs are a separate session, and
  `docs/workflow.md` belongs to it.
- **`check_4_3`'s weight_source assertion cannot fail** while the
  candidate's id is printed (KNOWN_GAPS).
- **`outcome.compose` is stricter than `check_4_3`** on a screen with no
  finding, named in both (KNOWN_GAPS).
- **An event entry condition stops** and no candidate states one.
- **A buy question about a company on no entry reads as an error**, not as
  a refusal.
- **IPS-2.1 would pass an instrument the policy forbids**, being a
  statement clause (Part 17 G).
- **IPS-5.3's second limb** is not computed; its trigger is the first
  portfolio state with no limit breached (decision 71).
- **Nothing records a model call's tokens**, so no figure in this
  repository would warn that the balance was running out.
- **The golden set costs about $0.039 a run**; a prompt change wants two.
- **The loader's `author`**, with the owner's sentence in WATCHLIST.md,
  before the first system prediction is entered; Part 15 F9 comes with it.
- **1 February 2027**: W-2.1 and W-2.2 fall due. **1 March 2027**: W-1.1
  and W-1.2.
- Three stale statements, the owner's to fix on the owner's word:
  `watchlist.toml`'s header and `test_watchlist.py`'s docstring, "read by
  nothing yet"; Part 11 D38's "D46".
- A philosophy topic lookup; the CIK confirmation; decisions 52 and 54.
- `operating_margin` and `free_cash_flow` get formulas, and
  `return_on_invested_capital` its tax rate, when a prediction names one.

---

## 8. Rules learned the hard way

**A prompt change can move a question it does not mention.** Deleting
three intent descriptions moved case 2.1, which mentions none of them,
from `compliance` to `risk_analysis` — while the descriptions of both
those intents stayed byte for byte identical. With an LLM classifier there
is no local change to the prompt: every question's routing depends on
every other option in the list. **Predict the lines you changed, then run
the loop that asks the wordings you did not.**

**The loop you ran the change against may not be the loop that sees it.**
The golden set was run twice, moved exactly where predicted, and said
nothing about case 2.1, whose wording it does not carry. pytest held every
table and derivation and was green. Only the runner asks that wording, and
only the runner moved.

**Do not filter the output of a paid run.** The runner's output was piped
through `tail -30`, which cut off the five cases containing the finding,
and three further runs were spent recovering what one unfiltered run had
already printed.

**Chase the evidence, not the story you already have.** The first guess at
which case had moved was 1.3, reasoned from the golden set's documented
blindness to `measure`. It was a good story and the wrong case.

**Grep the package, not three files.** The first deletion commit was
verified against `nodes.py`, `graph.py` and `schemas.py` and gave 34
collection errors, because `agents/__init__.py` re-exports every agent.

**Measure a deletion before taking it, and say the number twice.** The
decision estimated nine tests from two files; thirty collected tests
touched the three intents, sixteen had no subject left, and
`test_rebalance.py` — named in the estimate — had zero references to any
of them.

**A decision's own arithmetic goes stale too.** Decision 51 stated 4,094
lines across five components that sum to 4,458, and an intent vocabulary
falling from eleven to seven when three of eleven leave eight.

**The record names the requirement, not the audience.** A sentence about
who is to be impressed is a reaction standing in for a specification: it
carries the quality bar by implication and leaves the bar unwritten.

**Delete the surface, not the file.** An agent is its module, its node,
its formatter, its registrations, its package exports, its DTOs, its enum
members, its tracer colour, its prompt teachings and the docstrings that
describe it.

Still true, from earlier sessions: **a scoreboard that scores
well-formedness will score a wrong answer a pass**; **recompute the
answer's arithmetic rather than reading it**; **an exact half is where a
rounding rule announces that it does not exist**; **an exception swallowed
into a `None` crashes somewhere that cannot explain it**; **when
everything fails at once, change one thing and rerun the thing that
worked**; **cut the branch before the first commit**; **a golden line can
be identical to another in four of its five fields**; **grep the writer
the reader reads**; **a test parametrized over the constant it is checking
cannot catch a wrong constant**; **a check that looks for a word anywhere
passes a line that lost it**; **a wrong version that changes nothing is a
finding**; **a statement clause can carry a finding**; **a rule already
implemented is not implemented again**; **a type guard written against
`Sequence` lets a string through**; **a figure measured before a prompt
changed is not a figure about the call being made**; **a cost you cannot
measure is a cost you will misstate**; **take the shapes a caller actually
has**; **hand arithmetic is checked, and the check is part of the work**;
**a statement about the code goes stale four commits after it was true**;
**a guard that cannot fire is not a guard**; **pass `--color=no` to a
captured pytest run**; **look at a path before writing to it**; **a
refusal that is right can still be shaped wrong**; **a test over the
suite's copy owns the rows it reads**; **a number is measured before it is
written**; **a brief's claim about an interval is checked against the
clock**; **a count in a message is counted**; **sight a new case before
writing its golden line**; **the registry's descriptions are the prompt**;
**add up the pending list**; **the owner's documents are written on a
separate word**; **say which loop cannot see a change**; **a formatter
states what the data says and never what the system is**; **two paid loops
on one SQLite file run one after the other**; **an instruction with words
missing is read against the record**; **a wrong version checked in place
can run the previous version's bytecode**; **open the definition of done
before recommending that something be deleted for not being in it**;
**search the record before logging a finding**; **a defect found once in
one figure is not one figure**; **a byte-identical pair is one missing
axis**; **an intent that answers is not an intent that works**; **write a
prediction where it cannot be edited afterwards**; **a reference written
before the code decides the code**.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/tmp/golden_err.txt
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 2.1     # one Haiku call, ~$0.001

python src/agents/cli.py --portfolio 3        # :q to quit
# several questions through one process, which is how the full test is run.
printf '%s\n' 'Does GOOGL clear my philosophy?' 'What is GOOGL worth?' ':q' \
  | python src/agents/cli.py --portfolio 3

# is the API answering at all, before spending a loop on finding out:
python -c "import anthropic;from dotenv import load_dotenv;load_dotenv();\
print(anthropic.Anthropic().messages.create(model='claude-haiku-4-5-20251001',\
max_tokens=8,messages=[{'role':'user','content':'ok'}]).content[0].text)"

git status --short
git log --oneline 33769f6..HEAD
git rev-list --count 33769f6..HEAD

# the tree that still had the three intents:
git show intents-parked --stat | head -5

# by hand, from the project root, after a migration or a seed change:
alembic upgrade head
python src/portfolio_tool/scripts/seed_portfolio.py --reset

# what the database says it is at (expected 2445c12e728c):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# the reading tool's two tables:
sqlite3 data/portfolio.db "select accn, length(text), source from filed_documents; select accn, section, model, substr(prompt_version,1,12) from document_readings;"

# the price and filings clocks, which decide what a paid loop fetches:
sqlite3 data/portfolio.db "select a.ticker, m.last_price_fetch_time from asset_fetch_metadata m join assets a on a.id=m.asset_id order by a.ticker;"
sqlite3 data/portfolio.db "select cik, pulled_at from filers; select * from filed_fetch_metadata;"

# what a paid loop wrote, against the prediction (the column is calls_consumed):
sqlite3 data/portfolio.db "select bucket_key, calls_consumed from api_quotas order by id desc limit 1;"

# the intent vocabulary and the roster, after decision 51:
PYTHONPATH=src python -c "from agents.schemas import INTENTS, AGENTS; print(len(INTENTS), sorted(INTENTS)); print(len(AGENTS), sorted(AGENTS))"

# a check run against an edited, deliberately wrong module:
find src tests -name __pycache__ -type d -prune -exec rm -rf {} +
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider --color=no tests/<file>.py

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only intents
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~6s, no model calls | Do the components still work; does every reference Part reproduce; does each node fetch in order and publish its block; does the gate refuse what it must; does the outcome compose every row of the truth table |
| CLI | ~2s and one Haiku call for most questions; **a thesis question about $0.014 and a position question about $0.025 on Sonnet**; **fetches prices past their interval, which ran out on 22 September at 14:24** | What it is actually doing: the plan, the parameters, the reasoning line, the answer text. **The only loop that shows a live reading, proposal or view, the only one that shows an answer at all, and the only one that flags two questions answered identically** |
| Golden set | ~50s, **about $0.039 on Sonnet per run** and Haiku. **It no longer writes to any table**: the macro line that rewrote `macro_data` on every run is deleted, and prices are fetched only past their interval | Did routing change anywhere (twenty-one lines, one pinned failure). **Blind to `measure`, `group_by`, `tickers` and answer text, and to any wording it does not carry** — which is how case 2.1 moved unseen; stderr kept to a file |
| Benchmark runner | ~50s, **about $0.039 on Sonnet** and Haiku. `--case X` is one routing at about $0.001 | How many cases pass, n/18. Blind to whether a view or a proposal is any good, to whether a range's ends are right, and to any due prediction until 2027. **Its checks read each answer's text — a date, a clause id, a trade line, a percentage — and it shows the answer to nobody** |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once. **Never pipe a paid run through a filter.** **A live reading,
proposal or view made on its own is not a loop**: it is asked for, said
first, and read by hand.
