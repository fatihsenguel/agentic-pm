# AGENTIC_FINANCE — Session Handoff

**Session date:** 15 September 2026 (seventeenth session). Regenerated at its end.
**Branch:** `consolidate`, cut from `selection` at 00a7f92, the trunk's tip at session start. **`baseline-v1` is the trunk**: each session branch is merged into it with `--ff-only` when the loops are green, so 20160b0 and d9b5954 are history on it, not orphaned, and the tags `baseline-v1-20160b0`, `baseline-v1-clean` and `baseline-v1-green` mark the older tips. At session start `baseline-v1` and `selection` both stood at 00a7f92. This session's commits: `git rev-list --count 00a7f92..HEAD` — 22, plus the one that lands this file. **Not merged and not pushed**: the owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **922 passed, 6 xfailed**, up from 918 by the macro node test and the risk formatter test. **The golden set ran four times** (twice before any change, twice after the macro fix) and the **runner once, 12/12**: the sixteenth session's "not run, nothing they see changed" was checked and held. `expected.txt` moved once, on the macro line, as predicted. Tag **`quant-inventory-parked`** at 8d87455 keeps the deleted quant code a checkout away.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session the owner's own instruction was wrong on a line
number and I checked it before acting: item 1 said the macro node reads
`slope_raw` and `data_manager.py:1049` writes `slope_10y_3m`, both true, and
neither the writer the node reads; the snapshot tool writes `slope`, and the
fix as written would have raised the same error. The test was run against all
three keys. A claim about a reader is checked by grepping the writer it reads.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress** and was not advanced this session: the philosophy check and the filings reader exist as pure modules nothing in the graph reaches (§7). |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass, run this session. Level 4: six research cases, none running. Unchanged. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Twelve cases. Unchanged. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line, from this session.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 65 open entries carry a live trigger; a marked heading keeps a line reading "none". Log a finding only with a trigger or a decision number. New this session and worth reading: "The backtest tests the weights on the window they were estimated on", "The registry text names what the system does not compute", "What the seventeenth session's deletions left behind". |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, Parts 1 to 13. Unchanged this session. Part 13 C names two deleted paths (`update_all_assets.py`, `tools/data_tools.py`) as the way to `force_update_asset_info`; the owner decides whether it gets a dated note (§5, item 55). Never update it to match code output. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. Unchanged. |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027. Nothing reads it. Unchanged. |
| `docs/PM-Assistant — Roadmap.md` | Stale; DIRECTION.md's Order supersedes it. |
| `docs/workflow.md` | Stale: its example plan names RiskManagerAgent, deleted this session. |

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`.
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half that is tools and done,
and a judgement half whose first tools exist as pure modules and are not yet
joined to the graph. The router is scaffolding until the tool layer is
complete. **No deadline. Correctness over speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.**
- **Policy lives in config, not code**, and every number in config is in the
  document first. `config.toml` holds policy; `.env` holds identity.
- **Two policies, two questions.** The IPS says what may be held; the
  philosophy says what is worth wanting.
- **Raise, do not repair.** A refusal is an honest failure; a plausible wrong
  answer is not. This session's form: an answer that computes per-holding
  volatility under a VaR question now says it computed no VaR.
- **Typed facts are not a source.** A company's figures come from the
  reader; typed figures stay in tests.
- **References before code**, measured over the whole source.
- **No price forecasts as numbers.**
- **A capability nothing reaches is inventory, and inventory costs every
  session that reads it.** Decided this session: code no question reaches
  and no benchmark case asks for is deleted behind a tag, not kept with a
  note. The four live intents outside the benchmark roster are a separate
  decision (51).

### How I work on this

- Every change starts as a written decision in plain words: what it is, what
  changes on a yes, the rejected alternatives, which loop sees it. One commit
  per change, test first and seen failing for its own reason, `git status
  --short` and the diff read before each commit, and the word yes before it
  lands; "okay" is not one.
- **Grep for the caller, not the registration, and grep for the writer
  before trusting a reader.** Every deletion this session was preceded by a
  grep for the symbol across `src/` and `tests/`, and the tools package init
  was the one importer that would have broken.
- **Checking against a wrong version runs with bytecode caching off**
  (`PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`, `__pycache__` deleted).
- **Two changes in one file are still two commits.** This session the tools
  package init was split across three commits by writing each commit's
  version of the file into the index with `git hash-object -w` and
  `git update-index --cacheinfo`, which stages a chosen content without
  touching the working tree; `git apply --cached` is the other way.
- **The migration, the reseed and any rewrite of stored rows are run by
  hand**, and the output is pasted. None this session.
- **PHILOSOPHY.md and IPS.md are mine to edit.** A session brings the wording.
- **CLAUDE.md is mine and untracked.** A session proposes wording; I apply it.
- No emoji in anything newly written. A count I predict is a count I add up.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect. My real portfolio's data in the repo: Order 6, last. No cached
holdings table; no fallback rate, currency or policy; no adjusted close; no
environment switch for which policy runs. **No invented figures as a runtime
source, and no price a stock will reach anywhere.** No mutation testing until
necessary. No widening of the router's schema to make it a better classifier.
No SIC code range recited from memory. **No "inventory, not capability"
notes on dead code: delete it behind a tag.**

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q

python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py

python src/agents/cli.py --portfolio 3
```

**922 passed, 6 xfailed, 26 warnings, about 3.5 seconds.** One run at
session start took 34.06 seconds and the next 3.67 with nothing changed
between them: the sixteenth session's 1:42 shape again, not measured.

**The golden set: four runs, all as predicted.** Twice at session start
against the sixteenth session's tree: zero diff both times, the two pinned
failures printing as pinned. Twice after db567c8: the macro line moved from
`errors: 1` to `errors: 0` and nothing else, identical runs; `expected.txt`
moved on that line in 2ac821d. **One pinned failure is left**, "Should I
rebalance my portfolio?" at `errors: 1`, waiting on decisions 13 and 51.

**The runner: 12/12** at session start. Not run after: no case reaches
anything this session changed, and 1.3's `covariance_method` check reads a
value that is still `sample`.

**The CLI, twice, "What's the market regime?":** before db567c8 the error and
a header with nothing under it; after, `neutral`, VIX 17.1 (printed
unrounded), yield curve normal with slope 1.026, a "Risk Stance" line, no
as-of date. All three logged, not chased (KNOWN_GAPS, "The macro answer, now
that it prints").

**Level 4: 0 of 6 cases run.**

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. `consolidate` is this session's
branch, from 00a7f92. `selection` is the sixteenth session's branch at the
same commit, merged. `compliance` and `vocabulary` are merged and older.
`wip/phase7-snapshot` holds rejected Compliance/IPS code. `wip/rag-early` and
tag `rag-early-parked` hold the RAG code, whose package is now deleted from
the tree. **`quant-inventory-parked`** at 8d87455 holds the tree before the
eight quant deletions of this session.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`97d3708851e5`**, 23 migrations, linear, all applied. No migration and no
reseed this session. Tables that matter:

- `portfolios`, `transactions`, `assets` (9 rows).
- `daily_prices`: 6,957 rows and not a fixed count; it grows when a query runs
  after new closes.
- `filed_facts`, `filed_fetch_metadata`: **empty.** The reader has never
  fetched from EDGAR (decision 43).
- `financial_statements`: 65 rows, neither the reader's store nor a source
  (decision 52 decides whether the Yahoo-fed tables stay). `macro_data`: 197
  rows and growing; the macro path reads it and now answers.
- `fx_rates`, `fx_fetch_metadata`: empty. `shares_history`: no `source`
  column.

**There is no holdings table.** Portfolio 3, "Benchmark Portfolio", is the
only portfolio: nine ledger rows, cost basis 284,500 plus 15,500 cash, USD,
policy `ips.toml`.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py`, `test_screening.py` | nothing in the graph |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py` | nothing |

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`.
- **yfinance 1.7.0.** The price method passes `auto_adjust=False`.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing; the real value is not set.
- `config.toml` carries five fetch intervals. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import. The whole suite on a scratch copy:
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest`.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router.
- **What is no longer in the tree** (do not look for it): `portfolio_tool/rag/`,
  `tools/data_tools.py`, `tools/macro_tools.py`, `tools/analytics_tools.py`,
  `portfolio_tool/analytics/`, `scripts/run_metrics_update.py`,
  `scripts/update_all_assets.py`, `agents/risk_manager_agent.py`,
  `optimization/risk_parity.py`, `tests/test_design_violations.py`,
  `tests/violation_detector.py`; and inside surviving files, VaR, CVaR,
  drawdown, Sharpe, Sortino, Calmar and `RiskMetricsCalculator` from
  `quant/risk_metrics.py`, shrinkage and exponential covariance, the frontier,
  min-vol, target-return and target-volatility optimisers, and
  `DataAgent.get_risk_metrics_tool`. `backtest/metrics.py` keeps its own
  copies of the risk metrics for the backtest intent.

---

## 4. What the seventeenth session did

`git log --oneline 00a7f92..HEAD`, 22 commits, plus the one that lands this
file. No capability, no reference part, no intent: a clearing session.

**The loops, first.** pytest, golden twice, runner, CLI on the macro
question: all clean, the macro CLI answer the known error. The handoff's
assumption held and is now a measurement.

**Item 1, the macro key (db567c8, 2ac821d, a042d77).** The node read
`yield_curve["slope_raw"]`; `MacroAgent.get_macro_snapshot_tool` writes
`slope`; `DataManager.get_yield_curve_status` writes `slope_10y_3m` and the
node does not call it. `tests/test_macro_node.py` runs the node over the real
snapshot tool with a stand-in data manager and was seen failing on the first
two keys before passing on the third. Golden twice: the macro line moved
exactly as predicted; `expected.txt` moved in its own commit; the KNOWN_GAPS
entry resolved with the cause, correcting its own wording.

**Item 2, seven deletions no question reaches (76fa6f5 to 04d98f1).** The rag
package; `data_tools`, `macro_tools` and `analytics_tools` (their only
importer the tools package init, split across three commits); the two scripts
that could not run; RiskManagerAgent with its export, diagram, schema comment
and import-check entry. Each commit imports cleanly in a throwaway worktree.

**Item 3, the VaR wrong face (8d87455).** Option A taken: the general risk
answer names the three figures it does not compute, on every answer from that
path, since the formatter cannot read the question. `tests/test_risk_formatter.py`,
the first test of that formatter, failed on the line's absence. The registry
text that still advertises VaR is its own KNOWN_GAPS entry (owner's
instruction).

**Item 4, the unreachable quant code (f4829f9 to 7e30184, eight commits).**
Group 1, code no intent reaches: deleted behind tag `quant-inventory-parked`,
caller before callee. Group 2, the four live intents outside the benchmark
roster, is decision 51 and was not touched. Two docstring leftovers from one
commit were caught and named in the next.

**Item 5, KNOWN_GAPS (c45d1c3, f606d84).** Option A: every open entry's
`Blocks:` line became a `Trigger:` line, one line each, no body moved; the 23
untriggered entries went to the owner as a batch and the answers were applied
in the sweep, with five entries added and eight dated notes.

**Also (729340e):** the two design-violation scripts deleted on the owner's
batch answer.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- The macro node reads `slope`, the key the snapshot writes.
- A VaR or drawdown question is answered with per-holding volatility and a
  sentence naming the three figures not computed (option A); option B, a
  routed VaR with a reference Part, waits for a benchmark case.
- Unreachable quant code is deleted behind a tag, not kept with a note
  (group 1). The four live intents outside the roster are decision 51.
- KNOWN_GAPS keeps one file; every open entry carries a trigger; a session
  reads the triggered ones (option A over a split).
- The 23 untriggered entries: 14 closed, 2 resolved by deletion, 4 promoted,
  3 kept, as recorded in the file's OPEN paragraph.
- Decision 39 closed: the resolved-in-body headings are marked.
- **The full test at the end of Order 4** (owner's, recorded here): when
  Order 4's last commit lands, the project stops for a full test. The owner
  runs their own CLI session across both halves; findings are logged; triage
  is against the benchmark cases and DIRECTION.md's invariants, not against
  the record's length. **Order 5 begins only when**: Levels 1 to 3 still pass;
  all six Level 4 cases are well-formed; no wrong face is left in the owner's
  notes; no invariant is violated; and the open record is under a number the
  owner sets then.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve. Closed this session: 39.
6. The rebalance tools' fixed euro sign.
9. Records and rules for the span and two-weights clarifications.
10. A window return as a measure with a reference.
11. Replace the two verbatim benchmark few-shots.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
14. "Optimization failed: None".
15. A golden line for 2.3.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding.
18. Realized gains and closed positions.
22. Volatility over as-traded closes or a total-return series.
23. The answer text naming the price source.
29. **The node for the screen**, after the bridge.
30. What a philosophy is bound to.
32. Formatter headers carry an emoji: the entry counts two, and a grep of
    `nodes.py` this session shows one on each of the policy-lookup,
    optimization, macro, rebalance and backtest headers beside them. One
    commit, the runner run against it.
35. A rank selection in extraction.
36. What `reasoning` is for.
38. The CLI's identical-answer check.
41. Writing what nets against debt into PHI-3.1's clause text. Mine.
43. **The real `EDGAR_USER_AGENT` in `.env`.** Mine.
45. The tool-boundary pass, tagged Order 5.
46. Where NOPAT's stated tax rate lives, and what it is (D32). Mine.
47. `net_debt` as a metric key with its own reference row (D33).
48. Part 13 E's questions 3, 4, 6 and 7.
49. A SIC code on the block.
50. Ticker to CIK, with the node.
51. **The four live intents outside the benchmark roster** — optimization
    (max Sharpe, golden-pinned, runs with no portfolio), rebalancing (raises
    on a missing target; two known defects behind it), backtest (in-sample by
    construction), macro (answers since db567c8, prints a risk stance):
    delete or keep, each moving golden lines and an agent in `AGENTS`. My
    lean, deletion where no benchmark case asks; rebalancing first, since
    decision 13 would rebuild it from a reference. Trigger: the full test at
    the end of Order 4, or earlier if one of them produces a wrong face.
52. **The Yahoo-fed tables** — `financial_statements`, `fundamentals`,
    `quarterly_earnings`, with `get_financial_statements` returning nothing
    and its six xfails: delete or keep. Their last readers went with
    `data_tools.py`.
53. **CostCalculator**: raise on an unknown model, or delete the cost
    tracker. Lean delete; nothing reads a cost figure.
54. **BaseAgent's tool loop** (`process`, `get_tools`, `tool_map`,
    `get_system_prompt`, `TaskType`, the protocol enums) and the three
    `AgentConfig` fields that describe it: delete. Lean delete, **its own
    sitting**: it touches every agent class.
55. Whether `expected_values.md` Part 13 C gets a dated note where it names
    `update_all_assets.py` and `tools/data_tools.py`, both deleted. Mine.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12, run this session. Level 4: defined, six cases, none
with a check, none running. The ledger has four open predictions and no
scored one. Read n/14 as a count of well-formed answers and never as the
system being good at research (benchmark.md).

---

## 7. Next steps, in order

Unchanged from the sixteenth session; this session cleared ground and built
nothing toward them.

**1. The bridge between the block and the metrics**, blocked on decisions 46
and 47. `quant/fundamentals.py` reads one `tax_rate` and one `debt`; the
reader's block carries `effective_tax_rate` and three borrowing fields, and
Decimals where the metrics accept floats. Reference rows by hand first.

**2. A SIC code on the block** (49).

**3. The real contact and one live fetch** (43).

**4. Decision 29, the node**, after the bridge: runner checks for 4.1 and 4.6
written first and seen BLOCKED; the intent and agent in the registries; the
node; the formatter; the golden line and the prompt, golden twice with the
prediction written first. The compliance gate is designed with it. W-1 cannot
clear the screen on filed figures until 48 is decided.

**5. Then the valuation pipeline** with Part 11 by hand, and prediction
scoring with its Part.

**At the end of Order 4: the full test** (§5), before Order 5.

### Later, with reasons

- Decisions 51 to 54, each its own sitting; 54 touches every agent class.
- The registry text naming VaR, drawdown and risk parity: a prompt change,
  prediction first, two golden runs (KNOWN_GAPS).
- 3.2's rewrite and Part 2's boundary: at the commit that makes 4.3 answerable.
- The tool-boundary pass (45): the first benchmark case that fails for want
  of expression rather than capability.
- The 34-second suite run, if it recurs: `--durations` on that run.

---

## 8. Rules learned the hard way

**Grep the writer the reader reads, not a writer of the same name.** The
macro fix as instructed named a real writer of a differently named key in a
function the node never calls. The test against three keys settled it in one
run; a fix committed on the instruction would have failed the same way with a
different name.

**A formatter test with a hand-built input holds the formatter to a shape,
not the node to the tool.** `test_synthesizer_formatters.py` fed the macro
formatter a snapshot with `slope` in it and passed for two weeks while the
node read `slope_raw`. `test_macro_node.py` runs the node over the real tool.

**Delete the caller before the callee, and grep the package init.** Three
tool modules had one importer, their own package's `__init__.py`, which every
import of the surviving `rebalance_tools` ran; deleting a module without its
import line would have broken the graph at import while pytest's collection
named a different file.

**A deletion commit leaves docstrings behind; the next commit names them.**
Twice this session a module or class docstring still listed what the previous
commit deleted. Caught by grepping the deleted name after each commit, not
before.

**A rule taken from part of a source is measured over all of it**; **a
record says what the tree holds, not what the next step is**; **a wrong
version checked in place can run the previous one's bytecode**; **an
invariant is checked against the code, not read as a description** — still
true, from earlier sessions.

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

python src/agents/cli.py --portfolio 3        # :q to quit

grep -rn "SymbolName" src/ tests/ --include='*.py'
git status --short

# this session's commits: count from the trunk's tip at session start
git log --oneline $(git merge-base baseline-v1 HEAD)..HEAD
git rev-list --count $(git merge-base baseline-v1 HEAD)..HEAD

# the deleted quant code, if a benchmark case ever asks for it:
git show quant-inventory-parked:src/portfolio_tool/quant/risk_metrics.py

# by hand, from the project root, after a migration or a seed change:
alembic upgrade head
python src/portfolio_tool/scripts/seed_portfolio.py --reset

# what the database says it is at (expected 97d3708851e5):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# nine assets; daily_prices and macro_data move, do not pin them:
sqlite3 data/portfolio.db "select count(*) from assets;"

# a check run against an edited, deliberately wrong module:
find src -name __pycache__ -type d -prune -exec rm -rf {} +
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/<file>.py

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only consolidate
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3.5s, no model calls | Do the components still work; does every reference Part reproduce; does the macro node read the tool's key; does the risk answer name what it did not compute |
| CLI | ~3s, one call | What it is actually doing: the plan, the parameters, the reasoning line, the answer text |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines, one pinned failure left). Blind to parameters, answer text and everything under the judgement half's modules |
| Benchmark runner | ~1.5min, cents | How many cases pass. Blind to the four intents outside the roster and to the judgement half |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text.
