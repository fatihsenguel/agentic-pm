# AGENTIC_FINANCE — Session Handoff

**Session date:** 20 September 2026 (twenty-ninth session), begun at 12:49 UTC. Regenerated at its end.
**Branch:** `gate`, cut from `baseline-v1` at **641b492** on the owner's word, the branch not existing before. **`baseline-v1` is the trunk** and stood at 641b492 at session start, level with `origin/baseline-v1`. The previous session's branches `cap` and `values` are deleted and their commits are on the trunk; 641b492 landed on the trunk directly rather than through a branch. Each session branch is merged into the trunk with `--ff-only` when the loops are green; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count 641b492..HEAD` — 17, and 18 with this file. The owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1761 passed, 6 xfailed**, up from 1650 by 111. **Golden set: twenty lines, three runs** — one at session start with zero diff, then two for the prompt hypothesis, identical to each other, **one line of twenty moved exactly as predicted**; `expected.txt` updated on its own commit. **Runner 16/18, twice**: at session start 4.1 BLOCKED at PHI-2.1, 4.3 BLOCKED at out_of_scope, 4.4 PASS; at session end the same count with **two different cases** — 3.2 passing on a new prompt and 4.3 blocked at a new place. **The CLI once**, the allocation question, which fetched the holdings' closes, its interval having run out. **The gate is built**: Part 17, the pure module, the node on the edge into the synthesizer, the guard, and `asks` gaining "position" so that "should I buy X" reaches it. **Decisions 71, 72 and 73 taken**, each with a word, numbered here and the owner's to renumber. **Order 4 is not done. Left: the research node's half of case 4.3 — the model's view, the weight on the block, the entry condition and the outcome — then the full test before anything of Order 5.**

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Sections whose claims were checked again this session and
still hold are kept word for word; the rest is rewritten. Misses of my own
this session, caught before or after landing: **my hand arithmetic for Part
17 was wrong in the fourth decimal on seven figures and by a cent on one**,
all at the 15% weight, where multiplying rounded percentages compounded —
the calculator check caught them and the Part carries the checked values;
**three wrong versions changed nothing** and were rewritten rather than
counted, each a finding about a test (a cash line invented in a
`by_position` fixture the real block does not carry; nothing holding the
case where a purchase restores every breach; nothing holding that findings
are compared by clause *and subject*); **two weight cases were written as
TOML integers**, so the type check refused them before either range guard
was reached and both guards were held by nothing; **a bool guard I wrote
could never fire**, `bool` not being a subclass of `float`; **`weight`
first landed inside `[candidate.entry_condition]`** rather than on the
candidate, caught by loading the file before running anything; **a dead
loop with a `pass`** was left in `gate.py` and removed before the commit;
**one wrong-version patch did not apply** and its "6 passed" meant nothing
until the escaping was fixed; **a routing test used `execution_plan`**, a
key `route_next_step` does not read, so it passed for the wrong reason;
**two extraction assertions were simply wrong**; and **the research node's
refusal said the gate "is not built"** four commits after it was, caught
only while predicting the runner.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the bridge, the SIC code, the philosophy check node, the metric keys, the valuation range, prediction scoring, the research agent's shape and its thesis answer, the reading tool, and, this session, **the gate: its Part, its module, its node, its guard and the routing that reaches it**. Left in Order 4: the research node's half of 4.3, then the full test. **Invariant 8 is stale in its tense** — it says "should I buy X" is refused until Level 4 defines it; Level 4 defines it and the refusal is gone. One dated sentence, the owner's. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass, **3.2 on a new prompt** since this session. Level 4: 4.2, 4.4, 4.5 and 4.6 pass, 4.1 blocked by decision, 4.3 blocked at the research node. n/18. **Part 2 is rewritten**: security selection is in scope through Level 4's checks and no further, and what stays out has no timetable. Ten dated status notes under Level 4, the tenth this session's. |
| `tests/golden/expected_values.md` | Hand-computed reference, Parts 1 to 17. **New this session: Part 17**, the gate's check of a candidate at a stated weight, computed by hand on the 09-18 closes before the module, with decisions D59 and D60. Never update it to match code output. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Eighteen cases. This session: **3.2's prompt is a price forecast**, rewritten and not deleted; `check_4_3` asks for a prediction **entered** in the ledger (decision 69); its probe stopped looking for a `stopped` key the gate does not have; and the section header no longer calls decisions 63, 64, 65 and 68 open. `check_4_3` is exercised by `tests/test_check_4_3.py`, which is new because nothing ran it. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 153 lines start `**Trigger:**`, counted by `grep -c '^\*\*Trigger:\*\*'`. New this session: five entries. **The next session reads "The gate is built: decisions 71, 72 and 73, and what the first runs showed" first.** |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, saved in Excel at c75b73b. Untouched this session and not opened; Parts 9 C, 11, 14, 15, 16 and **17** have no sheet. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. Unchanged. |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027, none scored. **Changed this session on the owner's word for the sentence: a paragraph on the weight, and a `Weight.` line under W-1, 6% of the portfolio after the purchase.** No score is written into it by the system, ever. |
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
and a judgement half whose tools — the philosophy check, the valuation
range, prediction scoring, the research agent for a thesis and, since this
session, **the gate for a position** — are in the graph with their
references. The router is scaffolding until the tool layer is complete.
**No deadline. Correctness over speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** The last sessions' forms
  stand: a filing's document is text in `filed_documents` returned to no
  agent; what leaves the reader is the record, at most twelve claims a
  section and at most 3,600 characters of quotation in them together. **The
  gate's form:** it reads the allocation block as published and the
  candidate's entry, and publishes findings and figures, never a holdings
  table.
- **No number from a model.** A claim's sentence carries no digit and a
  figure appears only inside a quote held to the stored section; a proposed
  prediction's metric is one of the two the frame writes. **The gate's
  numbers are one multiplication from the allocation**: every existing
  share is its old share times (1 - w) and the candidate's is w exactly.
  **A number written in words is not caught.**
- **Policy lives in config, not code.** The thesis, the growth pair, the
  classification and the weight are the watchlist's, loaded as written; the
  IPS's words are the IPS's. **The loader checks presence and shape; the
  check that reads a word is where that word's vocabulary lives** — the
  loader takes any non-empty asset class and the gate raises on one the
  policy has no band for, the shape D42 gave the prediction metric.
- **One arithmetic path.** The gate is **not** a second checker: it builds
  the allocation the portfolio would have and hands it to
  `compliance.check`, so Part 7 and Part 17 are reproduced by one piece of
  clause arithmetic and there is one place to be wrong.
- **Raise, do not repair.** The gate raises on a candidate already held, an
  asset class no band names, a share whose sector is the label IPS-4.3
  leaves out, a weight outside (0, 1) and a view it cannot build. A gate
  that cannot run **publishes no block at all**, so the guard stops the
  answer rather than reading a verdict out of a block that says nothing.
- **Compliance is a gate, not a tool.** `gate_node` is in neither
  `schemas.AGENTS` nor `graph.AGENT_NODES`: the router cannot plan it,
  cannot be asked for it and cannot route around it. It sits on the edge
  into the synthesizer, and `require_gate` refuses to print anything that
  implies a position without its block **for the same ticker and the same
  weight** — the verdict is a verdict at one weight.
- **References before code.** Part 17 before the module, hand-computed and
  then checked; every test seen failing without its module and against one
  wrong version per rule with bytecode off; **a wrong version that changes
  nothing is a finding about the test, and three of them were.**
- **The score is mine, and so is a row.** The system proposes a prediction,
  prints it marked proposed and not entered, and writes neither file.
  Case 4.3 passes on a prediction **entered** in the ledger (decision 69).
- **A recommendation exists only with both checks attached.** Not built:
  the research node's half of 4.3.
- **The registry is the prompt.** A sentence describing a capability that
  now exists is allowed where a rule tuned to a case is not, and it is
  still a hypothesis: prediction in the commit, two runs, stop at the
  second miss. This session's held on both runs, on all twenty lines.
- **A value nothing consumes is not stored.** `weight` landed in the config
  one commit before its loader and its loader one commit before the node
  that reads it; `asks` took "position" only when a row and a pattern
  consumed it.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
- **The reference before the code**, each time, in its own commit.
- **A paid loop says first what it will fetch and store, table by table**,
  read off the store and the clock, and says after what moved. Five paid
  loops this session, every prediction exact.
- **A prompt change is a hypothesis** with a line-by-line prediction
  written before the run.
- **A check is exercised against wrong versions**, one per rule, and one
  that changes nothing is rewritten, not counted.
- **Say which loop can see a change.** Several this session could be seen
  by pytest alone, and two by nothing until a harness was written for them.
- **Grep the caller, not the registration.** `gate.gate` has one caller,
  `gate_node`; `gate_node` is bound in `graph.py` and in no roster;
  `require_gate` has one caller, the synthesizer's research branch;
  `judgement_record` has two, the guard's caller and `route_next_step`;
  `position_weight` has one, the gate node.
- **CLAUDE.md is mine and untracked.** A session proposes wording; I apply it.
- No emoji in anything newly written. A count I predict is a count I add up.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect. My real portfolio's data in the repo: Order 6, last. No cached
holdings table; no fallback rate, currency or policy; no adjusted close; no
environment switch for which policy runs. **No invented figures as a runtime
source, and no price a stock will reach anywhere.** No widening of the
router's schema to make it a better classifier. No NOPAT at the company's
filed tax rate. No formatter sentence that states the system's status.
**No number, threshold or weight from a model; no row written into the
watchlist by the system; no outcome decided by the formatter or the model;
no gate that checks the concentration clauses alone; no second arithmetic
path beside the allocation the analysis agent publishes; no verdict on a
clause nobody has decided how to check.** **No score written into the
ledger by the system; no partial credit; no prediction scored before its
date.** **No nearest heading, no page furniture removed by a rule measured
on one filer, and no question in a reading's prompt.** **No long quote cut
in code to pass the cap, no third wording after two misses, and no `asks`
value nothing consumes.**

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

**1761 passed, 6 xfailed, 35 warnings, about 5 seconds.** Run at session
start (1650) and after every commit. The 111 are the classification, the
weight, the gate's module (34), its node and guard (24), `check_4_3`'s
harness (6), the terminal table and the extraction pattern.

**Golden set: twenty lines, one pinned failure** ("Should I rebalance my
portfolio?", errors 1). **Three runs this session.** The first, at session
start, zero diff. Then the prompt hypothesis: two runs, **identical to each
other**, one line of twenty moved and it was the predicted one —
"Should I buy Nvidia?" from `out_of_scope` with an empty plan to `research`
with `['DataAgent', 'PortfolioAnalysisAgent', 'ScreeningAgent',
'ResearchAgent']`, all four run, **errors 2**. `expected.txt` carries it.

**The runner twice: 16/18 both times, and not the same eighteen
questions.** 3.2's prompt is now "What will Nvidia's share price be at the
end of next year?" and passes, sighted for the first time. 4.3 no longer
stops at out_of_scope: it routes, derives the four-agent plan, screens
Alphabet and stops at the research agent, whose refusal names what is
missing. 4.1 is blocked at PHI-2.1 naming D36, unchanged.

**The CLI, once.** The allocation question: priced as of 2026-09-18, total
408,447.50 USD, Equity 69.61%. It fetched the nine holdings' closes, the
one-day interval having run out at 02:51 that morning, and added no row —
the newest stored close was Friday the 18th and the run was on a Sunday.

**Level 4: 4 of 6 cases pass (4.2, 4.4, 4.5, 4.6); 4.1 blocked by
decision; 4.3 blocked at the research node.** Read n/18 as a count of
well-formed answers and never as the system being good at research.

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. **The trunk stood at 641b492** at
session start and is level with `origin/baseline-v1`. `gate` is this
session's branch, cut there on the owner's word. `cap` and `values`, the
previous session's, are deleted and their commits are on the trunk.
`thesis`, `reader`, `research`, `score`, `publish`, `range`, `keys`,
`node`, `filer`, `bridge`, `consolidate`, `selection`, `compliance` and
`vocabulary` are merged and older. `wip/phase7-snapshot` holds rejected
Compliance/IPS code. `wip/rag-early` and tag `rag-early-parked` hold the
RAG code. `quant-inventory-parked` at 8d87455 holds the tree before the
seventeenth session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`2445c12e728c`**, 26 migrations, linear, all applied; no migration this
session. No reseed. **What this session wrote:**
- `daily_prices`: **7,009, unchanged**, the last close 2026-09-18. The CLI
  fetched the nine holdings and the first golden run fetched GOOGL, and
  neither added a row: no trading day had closed since Friday. **The
  holdings' stamps are 2026-09-20 12:53 UTC and GOOGL's 12:56, so the
  price interval runs out on the 21st.**
- `macro_data`: **209, unchanged**, as predicted on every run — no trading
  day closed. The stamps were rewritten by each golden run.
- `api_call_logs`: 2,439 to **2,458**. Nine for the CLI's price fetches,
  three macro indicators on each of three golden runs, one for GOOGL's
  price. `api_quotas` for the 20th: **19**.
- `document_readings`: **5 rows, unchanged.** Item 1 under `1b2d86a8ba32`,
  `ba9a7051eeca` and `a64f51fde1eb` (the one the node serves); Item 1A
  under `903e89b123b5`; Item 7 under `54b0dba223f4`. All three sections
  the reader reads are cached, so a run asks the model only for its
  proposal.
- **No EDGAR fetch at all.** `filers` three rows, `filed_facts` 28,787,
  `ticker_ciks` 10,422, `filed_documents` one row, `filed_fetch_metadata`
  two. **The filings interval runs out on 22 and 23 September.** The
  golden set's Nvidia line routes to research now and **does not** pull
  NVDA: the screen refuses a ticker on no watchlist entry before its first
  call (decision 73).

Unchanged: `assets` ten rows, GOOGL the tenth and not held, its asset
class, sector and instrument type still blank — **the watchlist entry
states them now, not the assets row** (decision 63);
`financial_statements` 65 and `shares_history` 947, neither a source.

**There is no holdings table.** Portfolio 3, "Benchmark Portfolio", is the
only portfolio: nine ledger rows, cost basis 284,500 plus 15,500 cash, USD,
policy `ips.toml`. GOOGL is not held. Adobe has no assets row and no facts.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row; **the gate, over the portfolio as it would be** |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py`, `test_screening.py` | the screening node, by `nodes.PHILOSOPHY_PATH` (decision 30) |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py`, `test_watchlist_loader.py`, `test_watchlist_predictions_loader.py` | the screening node, the candidates and their growth pairs; the ledger node, the prediction rows; the research node, the candidate and its thesis; **the gate node, the classification and the weight** |

### The gate, as it stands

**Built this session, and reached by "Should I buy X?".**

| Piece | Where | Held by |
|---|---|---|
| The reference | `expected_values.md` Part 17, D59 and D60 | itself; hand-computed then checked |
| The check | `portfolio_tool/gate.py`, `gate`, `Gate`, `GateError` | `tests/test_gate.py`, 34, to Part 17 |
| The node and the guard | `agents/nodes.py`, `gate_node`, `judgement_record`, `require_gate` | `tests/test_gate_node.py`, 24 |
| The edge | `agents/graph.py`, `GATE`, `_gate_or_synthesizer` | the same file |
| The weight | `portfolio_tool/watchlist.py`, `Candidate.weight`, `position_weight` | `tests/test_watchlist_loader.py` |
| The classification | the same, `_HEADER` | the same, and `test_watchlist.py` to the document |
| The routing | `schemas.TERMINAL["research"]["asks=position"]`, `validate_terminal` | `tests/test_derived_plans.py` |
| The pattern | `agents/extraction.py`, `_POSITION`, `_asks` | `tests/test_extraction.py` |
| The case | `run_cases.check_4_3`, `blocked_on_recommendation` | `tests/test_check_4_3.py`, 6 |

**What it does on this portfolio.** Equity is 69.61% against IPS-3.1's 65%
before any purchase, and new money into equity only raises it, so the gate
**fails IPS-3.1 at every weight above zero**, and IPS-5.3 with it under
decision 64's funding. At 6% the candidate's own IPS-4.1 and IPS-4.2 are
clear; at 15% both fail. Two findings worth knowing because they look like
bugs and are not: **MSFT crosses back inside IPS-4.1 having traded
nothing** (12.0892% to 11.3638% at a 6% purchase, the denominator having
grown), and **the Technology breach clears at 15%** while IPS-3.1 gets
worse — which is why decision 68 rejected a gate that checked the
concentration clauses alone.

**What is not built:** the research node's half of case 4.3. It refuses a
position question and names what is missing — the model's view of the
thesis, the weight the answer is about, the entry condition read against
the screen, and the outcome composed from the four (decision 68).

### The research agent, the screen and the ledger, as they stand

Unchanged this session except as noted. `screening_agent_node`, intent
`research`, plan `[ScreeningAgent]` alone when `asks` is unset; **new: it
refuses a ticker on no watchlist entry when `asks` is "position", before
its first EDGAR call** (decision 73), and not otherwise — 4.6 screens JPM,
which is held and is on no entry. On Alphabet the screen stops at PHI-2.1
for FY2021 (decision 48, D36); the range publishes regardless, 129.39 to
205.62 on FY2025. `research_agent_node` answers `asks` "thesis" and
refuses "position". `ledger_agent_node`, intent `ledger`, unchanged.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  for the router. **`ANTHROPIC_SONNET` is `claude-sonnet-5`**, used by the
  reader and the proposer, and **it refuses a temperature**; neither sends
  one. The router's stronger-model switch sends 0.0 and would fail (KNOWN_GAPS).
- **The `anthropic` SDK is 1.2.0**: `messages.create` takes `output_config`
  for structured output, and a schema's `anyOf` of two object shapes is
  held by it.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing. **Nothing was fetched from EDGAR this session.**
- **Measured costs on `claude-sonnet-5`, $2 and $10 a million:** a proposal
  over cached readings about $0.007. With all three sections cached, a
  golden run and a runner run each ask for one proposal. **Spent this
  session: about $0.035** — three golden runs and two runner runs — plus a
  handful of Haiku router calls.
- **The price provider** is `nodes.price_provider()`; **the models** are
  `nodes.reading_model()` and `nodes.proposal_model()`; the EDGAR provider
  is `nodes.edgar_provider()`.
- **The allocation question fetches prices** when the one-day interval has
  run out. The CLI is a paid loop in that case, and is said first.
- `config.toml` carries five fetch intervals. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; `config.toml` is read relative to the project
  root, so scripts run from the root.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router.
- **Import order, for any commit sequence.** The last sessions' order
  stands. **New: `portfolio_tool/gate.py` imports `compliance`, `ips`,
  `quant.allocation` and `watchlist`, and nothing of `agents`;
  `agents/nodes.py` imports `gate` inside the gate node; `agents/graph.py`
  imports `gate_node` and `judgement_record` from `nodes` at module level.**
- **Tests import from other tests.** The last sessions' imports stand.
  **New: `test_gate_node.py` imports `_allocation`, `HOLDINGS`, `CASH`,
  `TOTAL`, `NEW_MONEY` and `TOTAL_AFTER` from `test_gate.py`;
  `test_check_4_3.py` puts `tests/benchmark` on `sys.path` and imports
  `run_cases`.**
- **Tests delete rows from the suite's copy they did not write**:
  `test_screening_node.py` Alphabet's and JPMorgan's facts, filers and the
  ticker table, `test_filed_facts_fetch.py` Apple's facts. `test_gate.py`
  and `test_gate_node.py` touch no table: their allocation is a fixture and
  the policy path is monkeypatched.
- **A scratch copy of the tree runs the suite against a changed file
  without touching the repository.** From the working tree,
  `cp -R src tests docs alembic config.toml ips.toml philosophy.toml
  watchlist.toml pyproject.toml <copy>/`; copy `data/portfolio.db` into
  `<copy>/data/`, then from inside it
  `DATABASE_URL=sqlite:///<copy>/data/portfolio.db USE_MOCK_QUOTA=True PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 <repo>/.venv/bin/python -m pytest -q -p no:cacheprovider --color=no <tests>`
  after deleting its `__pycache__`. **Pass `--color=no`** or the failing
  tests' names come back as colour codes. Nine copies this session.
- **`nodes.utc_today()`** is the ledger node's clock; the screening node
  reads the clock inline, and the research node reads the screen's as-of.
- **zsh does not split an unquoted variable into words.** **A `grep -c`
  that finds nothing exits 1 and stops a `&&` chain.** **BSD `sed`'s
  `0,/re/` first-occurrence form is a GNU extension and silently matches
  nothing on macOS** — a wrong version built with it tests the patch, not
  the rule. **A backslash inside an f-string expression is a syntax error
  in 3.10**, which turns a wrong version into a broken module.
- **What is no longer in the tree** (do not look for it): `portfolio_tool/rag/`,
  `tools/data_tools.py`, `tools/macro_tools.py`, `tools/analytics_tools.py`,
  `portfolio_tool/analytics/`, `scripts/run_metrics_update.py`,
  `scripts/update_all_assets.py`, `agents/risk_manager_agent.py`,
  `optimization/risk_parity.py`, `tests/test_design_violations.py`,
  `tests/violation_detector.py`; and inside surviving files, VaR, CVaR,
  drawdown, Sharpe, Sortino, Calmar and `RiskMetricsCalculator` from
  `quant/risk_metrics.py`, shrinkage and exponential covariance, the frontier,
  min-vol, target-return and target-volatility optimisers,
  `DataAgent.get_risk_metrics_tool`, and the two `marketable_securities`
  fields of the figures block.

---

## 4. What the twenty-ninth session did

`git log --oneline 641b492..HEAD`, 17 commits and 18 with this file. **The
gate, end to end**, in the order the brief set: the reference before the
code each time, and each commit on its own word.

**The loops, first.** `gate` cut from the trunk at 641b492. pytest 1650.
The CLI on the allocation question, said first to fetch the nine holdings'
closes, its interval having run out at 02:51 — and it did, adding no row.
Then, on a word and one after the other, the golden set once (twenty
lines, zero diff) and the runner once (16/18), each predicted table by
table and each holding: no price row, no filing row, macro still 209.

**Under the word, in order.**
- **e96570a** `watchlist.toml` states each candidate's asset class, sector
  and instrument type; `test_watchlist.py` holds the config's three words
  to the document's Classification line.
- **f94836f** the loader reads them and refuses a candidate missing one or
  stating it blank. The words are not validated there: the check that
  reads them stops on one the IPS has no band for, D42's shape. Eight
  candidate fixtures in seven test files gain the three.
- **591d0cc** **Part 17**, the gate's check by hand at 6% and at 15%: the
  portfolio as it would be with new money on top, every clause's finding
  and its distance with the figure before the purchase beside it, decision
  68's truth table as sixteen rows, and D59 and D60.
- **7504fb4** a watchlist entry may state the weight, W-1 at 6%, on the
  owner's word for the sentence. Optional, the growth pair's shape and not
  the classification's: a classification is a fact about the instrument, a
  weight a decision I may not have made.
- **bfb0ac3** the loader reads it; `position_weight` raises naming the
  candidate that states none.
- **5a18a09** `portfolio_tool/gate.py` and its 34 tests, held to Part 17.
- **ac8e8d7** `gate_node` and the edge into the synthesizer.
- **db8af02** `require_gate`: no outcome prints without a block for the
  same ticker and weight.
- **0ef4d4c** `check_4_3` asks for a prediction entered in the ledger, its
  probe reread, and `tests/test_check_4_3.py`, new because nothing ran the
  check.
- **2a06c59** the terminal table discriminates on a parameter's **value**
  and a row may name two terminals; `validate_terminal` is a function so
  its checks can be shown working.
- **1bdfe28** extraction reads "should I buy" as a position question.
- **c3d4cc4** the prompt hypothesis: the registry's two entries, the
  Siemens few-shot flipped with a sell example beside it, the screen's
  refusal of a non-candidate before EDGAR, and 3.2's new prompt.
- **af43de4** `expected.txt`, one line of twenty.
- **f0eed48** benchmark.md Part 2 rewritten.
- **a3f9aaa** the research node's refusal names what is actually missing,
  its old sentence having said the gate was not built.
- **78d6f1a** the record: five entries, decisions 71, 72 and 73.
- **ed2adc7** benchmark.md's status note.

**The prompt hypothesis, in full.** Predicted before running: nineteen
golden lines unchanged and line 11 moving to research with the four-agent
plan, all four run, errors 2. **Two runs, identical to each other, and
exactly that.** The lines nearest the rewritten paragraph — 6, and 14 to
16 — did not move.

**Spent:** about **$0.035** on Sonnet across three golden runs and two
runner runs, plus Haiku router calls. **Nothing was fetched from EDGAR.**

**Not done, on purpose.** The research node's half of 4.3; the loader's
`author` and Part 15 F9; the seven emoji headers; decisions 51, 52 and 54;
the currency; the philosophy topic lookup; the CIK confirmation; formulas
for `operating_margin` and `free_cash_flow`; any change to the reading or
proposal prompts for faithfulness.

---

## 5. Decisions taken, and decisions pending

**Taken this session**, each with the owner's word, **numbered here and
his to renumber**:
- **71**: IPS-5.3's **first** limb is computed and its second is not. The
  first is a guardrail; the second is an allocation preference, and
  enforcing it would block a purchase for being a worse use of the next
  dollar rather than for breaking a limit. `Gate.first_limb_binds` says
  when the clause is half-applied. Rejected: computing both and blocking
  on the second; raising when the first does not bind, which misapplies
  "raise, do not repair" — that rule is about missing data — and which
  would break the gate exactly when the portfolio came back inside its
  limits.
- **72**: a terminal-table key may name a parameter **and a value**, tried
  before the key naming the parameter alone, and a row's terminal may be a
  tuple closed over each name once. Rejected: a second intent; ResearchAgent
  requiring the portfolio agents; the gate computing the allocation itself.
- **73**: the screening node refuses a ticker on no watchlist entry when
  `asks` is "position", before its first EDGAR call. Narrowed to that
  question: 4.6 screens JPM, which is held and is on no entry.

**Pending — decide before writing code. Eleven by count, unchanged: none
closed, none opened.** CLAUDE.md's line reads "The list stands at 11 on
20 September: 10, 12, 13, 16, 17, 22, 45, 48, 51, 52 and 54" and matches on
both the count and the members. The cap is 25.

10. A window return as a measure with a reference.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding. Absorbs 35.
22. Volatility over as-traded closes or a total-return series.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, 11 and 36.
48. Part 13 E's item 7, second half only: the price and a filer with more
    than one class. Items 3, 4, 6 and 7's first half decided.
51. The four live intents outside the benchmark roster: delete or keep.
    Trigger: the full test at the end of Order 4.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields: delete, its
    own sitting.

- **The full test at the end of Order 4** (owner's, unchanged): when Order
  4's last commit lands, the project stops for a full test across both
  halves before Order 5. **Not this session: the research node's half of
  4.3 is not built.**

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12, **3.2 on a new prompt** — a price forecast, sighted
for the first time this session, rewritten and not deleted because the
question it used to ask is one the system now answers. Level 4: 4.2, 4.4,
4.5 and 4.6 PASS; 4.1 BLOCKED by decision, the runner's reason naming D36;
**4.3 BLOCKED at the research node** rather than at out_of_scope. 16/18.

What the runner cannot see: **fifteen of the sixteen rows of decision 68's
truth table**, of which `check_4_3` holds the one no rule may break;
whether the gate's arithmetic is right, which is pytest's against Part 17;
whether the range's ends are right; any due prediction until 2027; and,
for 4.4, whether a quote supports its claim and whether a prediction's
reasons support it.

**On this portfolio 4.3 may read BLOCKED with the gate working
perfectly.** IPS-3.1 fails at every weight and the screen stops at PHI-2.1.
A blocked case with the right reason is the right answer.

---

## 7. Next steps, in order

**1. The research node's half of case 4.3.** In order: the model's view of
the thesis, from the closed set `{stands, strained, no_view}`, with claims
of the readings as its reasons and an uncertainty; the weight carried onto
the research block, which `require_gate` already refuses to print without;
my entry condition read against the screen's finding on its clause; and
the outcome composed from the four by decision 68's truth table, **Part 17
H's sixteen rows**, with a pytest harness over the composition, since
`check_4_3` holds one row of it (KNOWN_GAPS). Then the rendering, and
`check_4_3`'s remaining assertions seen passing.

**On this portfolio the gate will fail IPS-3.1 at every weight** and the
screen will stop at PHI-2.1, so the first live 4.3 answer supports no
entry and names both. That is the policy answering; do not fill a figure
or soften a clause to move it.

**At the end of Order 4: the full test** (§5), before Order 5.

### Later, with reasons

- **The trunk.** `git switch baseline-v1 && git merge --ff-only gate`.
- **DIRECTION.md invariant 8** says "should I buy X" is refused until
  Level 4 defines it. It defines it. One dated sentence, the owner's.
- **Decisions 71, 72 and 73's numbers** are mine to propose and the
  owner's to set; they appear in one KNOWN_GAPS entry and in §5 here.
- **A buy question about a company on no entry reads as an error**, not as
  a refusal, and two agents compute a portfolio for it first (KNOWN_GAPS).
- **The golden set pins only the refusal branch** of a buy question; no
  line covers a candidate (KNOWN_GAPS). A new line wants sighting first.
- **IPS-2.1 would pass an instrument the policy forbids**, being a
  statement clause (Part 17 G, KNOWN_GAPS).
- **IPS-5.3's second limb** is not computed; its trigger is the first
  portfolio state with no limit breached (decision 71).
- **Every paid loop still costs Sonnet**: each golden run and runner run
  proposes once over three cached readings, about $0.007.
- **The next paid loop fetches the holdings' closes**: the interval runs
  out on 21 September at 12:53 UTC, GOOGL's at 12:56. **The filings
  interval runs out on 22 and 23 September.**
- **The loader's `author`**, with my sentence in WATCHLIST.md, before the
  first system prediction is entered; Part 15 F9 comes with it.
- **1 February 2027**: W-2.1 and W-2.2 fall due.
- The proposals' reasons and the readings' faithfulness: each a hypothesis,
  each on its own trigger (KNOWN_GAPS).
- The router's stronger-model switch and `ANTHROPIC_SONNET`'s temperature.
- The currency on the range, the close and the reported figure.
- The formatter headers carrying an emoji, seven in `nodes.py`. One commit,
  the runner run against it. `docs/workflow.md` in the console-glyph session.
- Three stale statements, mine to fix on my word: `watchlist.toml`'s
  header and `test_watchlist.py`'s docstring, "read by nothing yet"; Part
  11 D38's "D46".
- A philosophy topic lookup; the CIK confirmation; decisions 51, 52 and 54.
- `operating_margin` and `free_cash_flow` get formulas, and
  `return_on_invested_capital` its tax rate, when a prediction names one.

---

## 8. Rules learned the hard way

**A wrong version that changes nothing is a finding about the test.**
Three times this session. A fixture invented a cash line the real
`by_position` block does not carry. Nothing held the case where a purchase
restores every breach, so "fail whenever anything was breached" passed.
Nothing held that findings are compared by clause **and subject**, so
blaming IPS-5.3 for a breach the purchase created passed. Each cost a new
fixture and each was a real rule nobody was holding.

**A boundary case written in the wrong type tests something else.** Zero
and one as TOML integers were refused by the type check before either
range guard was reached; as floats they reach it. Both guards had been
held by nothing and neither of us would have known.

**An import-time check cannot be shown working on the table it guards.**
`validate_terminal` runs on the real table, which passes it trivially. Take
the table as an argument and a test can hand it one that breaks each rule.

**A guard that cannot fire is not a guard.** `isinstance(value, bool)`
beside `isinstance(value, float)` can never fire: `bool` subclasses `int`,
not `float`.

**Hand arithmetic is checked, and the check is part of the work.** Seven
figures of Part 17 were wrong in the fourth decimal and one by a cent, all
where rounded percentages were multiplied. The hand pass is what makes the
reference independent; the calculator is what makes it right.

**A statement about the code goes stale four commits after it was true.**
The research node's refusal said the gate "is not built" while the gate had
a Part, a module, a node and a guard. It was caught while predicting a
runner run, not while reading the file.

**A tool's first-occurrence flag may not be the tool's.** BSD `sed`'s
`0,/re/` is a GNU extension; on macOS it silently matches nothing, and a
wrong version built with it tests the patch and not the rule.

**Pass `--color=no` to a captured pytest run**, or the failing tests' names
come back as colour codes.

**A routing test that sets the wrong key passes for the wrong reason.**
`route_next_step` reads `agents_to_run`, not `execution_plan`.

**Look at a path before writing to it**, and **load a config file after
editing it**: `weight` first landed inside `[candidate.entry_condition]`,
where TOML put it and where nothing would have found it.

**A refusal that is right can still be shaped wrong.** "Should I buy
Nvidia?" now refuses correctly and arrives as a failure report.

**A check that looks for a field anywhere passes a line that lost it**;
**a test over the suite's copy owns the rows it reads**; **a number is
measured before it is written**; **a brief's claim about an interval is
checked against the clock**; **a quote is judged with the lines around
it**; **a count in a message is counted**; **sight a new case before
writing its golden line**; **the registry's descriptions are the prompt**;
**add up the pending list**; **the owner's documents are written on a
separate word**; **the golden loop's stderr goes to a file**; **say which
loop cannot see a change**; **a formatter states what the data says and
never what the system is**; **two paid loops on one SQLite file run one
after the other**; **an instruction with words missing is read against the
record**; **grep the writer the reader reads**; **a wrong version checked
in place can run the previous one's bytecode** — still true, from earlier
sessions.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/tmp/golden_err.txt
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 4.3

python src/agents/cli.py --portfolio 3        # :q to quit
printf 'Should I buy GOOGL?\n:q\n' | python src/agents/cli.py --portfolio 3

git status --short
git log --oneline 641b492..HEAD
git rev-list --count 641b492..HEAD

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

# a check run against an edited, deliberately wrong module:
find src tests -name __pycache__ -type d -prune -exec rm -rf {} +
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider --color=no tests/<file>.py

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only gate
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~5s, no model calls | Do the components still work; does every reference Part reproduce, **Part 17 among them**; does each node fetch in order and publish its block; **does the gate refuse what it must and does the guard stop an outcome without a block** |
| CLI | ~3s and one Haiku call for most questions; **the thesis question ~45s and about $0.007 on Sonnet**; **fetches prices past their interval** | What it is actually doing: the plan, the parameters, the reasoning line, the answer text |
| Golden set | ~2 min, **about $0.007 on Sonnet per run** and Haiku, **writes price rows past their interval, the macro rows, the call log and the quota counter on every run** | Did routing change anywhere (twenty lines, one pinned failure). Blind to parameters and answer text; stderr kept to a file |
| Benchmark runner | ~2 min, **about $0.007 on Sonnet for 4.4** and Haiku | How many cases pass, n/18. Blind to fifteen of decision 68's sixteen rows, to whether a range's ends are right, to any due prediction until 2027, and, for 4.4, to a quote's support for its claim |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once. **A live reading or proposal made on its own is not a loop**:
it is asked for, said first, and read by hand.
