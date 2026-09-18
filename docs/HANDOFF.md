# AGENTIC_FINANCE — Session Handoff

**Session date:** 18 September 2026 (twenty-fourth session). Regenerated at its end.
**Branch:** `score`, cut from `baseline-v1` at 264aa7a, the trunk's tip at session start. **`baseline-v1` is the trunk**: each session branch is merged into it with `--ff-only` when the loops are green; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count 264aa7a..HEAD` — 21: two carried items, thirteen for case 4.5 including two same-day corrections to its Part, two for decision 48's item 6, the record, benchmark.md, this file, and one fix to the rendering caught on the first live answer. **Not merged and not pushed**: the owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1304 passed, 6 xfailed**, up from 1204 by 100: 41 for the loader's prediction rows, 35 for the scorer against Part 14, 9 for the ledger node, 15 for the rendering through the runner's check, 2 for the routing row's table and prompt, less 2 field-tag tests that left with their fields. **Golden set: nineteen lines.** Zero diff on eighteen at session start; the nineteenth, "How have my predictions done?", recorded at clarification_needed on its baseline run and then at `ledger` on two identical runs after the routing commit, as its message predicted; the pinned rebalance failure throughout. **Runner 15/16 once**, after the routing commit: 4.5 PASS on four open predictions, 4.2 PASS, 4.6 PASS, 4.1 BLOCKED at PHI-2.1 for FY2021, the reason line naming D36. 14/15 at session start. **The CLI twice**: the allocation question at session start; the ledger question after the runner, to read the first live record. **No EDGAR fetch and no price fetch**: every request hit its interval; the database is unchanged from session start in every count. One request to the exchange's historical quotes by hand, for the 17th, storing nothing. **Case 4.5 is in the graph and passes on structure. Decision 58 is taken. Order 4 is not done: the research agent (4.3, 4.4) remains, then the full test before anything of Order 5.**

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Misses of my own this session, caught before or after landing:
the shape predicted the sighting of 4.5 at out_of_scope and the router put
it at clarification_needed; Part 14 was corrected twice the day it was
written, a float written without being computed and a written score dated
before its due date, which the ledger's own test refuses; the ledger node
first skipped the filers row the facts hang off, caught by its test; the
rendering printed the ledger's absolute path in the answer, caught on the
first live record; a note in Part 13 C counted raises wrongly before the
diff was shown; the brief's placeholders for the branch base and the
pending count were unfilled, reconciled here to eleven.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the bridge, the SIC code, the philosophy check node, the metric keys, the valuation range, and, this session, **prediction scoring, step 5 of the judgement half, with its Part first**. Left in Order 4: the research agent (4.3, 4.4), then the full test. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. Level 4: 4.2, 4.5 and 4.6 pass, 4.1 blocked by decision (five dated status notes under Level 4). n/16 since 18 September, the "n/14" sentence carrying its dated notes. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Sixteen cases. `check_4_5` reads watchlist.toml with its own parser and holds the block and the answer to it; `blocked_on_ledger` reads BLOCKED until the block exists. `check_4_2` asserts structure only. 4.1's reason line names D36 until Alphabet's FY2027 report. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 117 lines match `Trigger:`, 80 reading something other than "none", counted by grep. New this session: seven entries; three resolved (§4). |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, Parts 1 to 14. **New this session: Part 14**, prediction scoring by hand, D41 to D45, synthetic predictions over Alphabet's filed FY2025 lines, two dated corrections; Part 9 C's row for the 17th; Parts 12 and 13's notes for decision 48 item 6. Never update it to match code output. |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, saved in Excel at c75b73b. Untouched this session; Parts 9 C, 11 and 14 have no sheet. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. Unchanged. PHI-6.2 is what Part 14 D44 reads: the score is recorded, by me. |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027, none scored. Unchanged this session; **the prediction rows are now read**, by `portfolio_tool/watchlist.py` for the ledger node. No score is written into it by the system, ever. |
| `docs/PM-Assistant — Roadmap.md` | Stale; DIRECTION.md's Order supersedes it. |
| `docs/workflow.md` | Stale: its example plan names RiskManagerAgent, deleted in the seventeenth session. |

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`.
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half that is tools and done,
and a judgement half whose three tools, the philosophy check, the valuation
range and prediction scoring, are in the graph with their references, and
whose remaining tool, the research agent, is not. The router is scaffolding
until the tool layer is complete. **No deadline. Correctness over speed.
Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** This session's form: a
  ledger record carries one reported figure for a due figure prediction,
  the way a finding carries `observed`, since the outcome is the point of
  the answer; no other filed figure, no year's block, no document. The node
  test walks the block and finds no Decimal and no date object.
- **Policy lives in config, not code.** The predictions are the
  watchlist's rows, read by the loader; the score is written into the
  ledger by hand and read out as written. The scorer takes the metric's
  vocabulary from the formulas it can compute (D42) and the loader takes
  any metric name, so the vocabulary lives once.
- **Two policies, two questions; three now.** A question naming one
  company is research; a question about the predictions names none and is
  the ledger (decision 58). The registry says so and the golden line pins it.
- **Raise, do not repair.** This session's form: a prediction whose period
  is not filed is due and unscored with that reason, never wrong; a metric
  with no formula stops naming it; a written score dated before its due
  date does not load; a written score that disagrees with the filing is
  reported beside it, and the answer says they differ; a ticker the file
  lacks is the node's error, as it is for the screen.
- **References before code.** Part 14 before the scorer; the check before
  the capability, sighted BLOCKED; every test seen failing against the
  unchanged source and against a wrong version with bytecode off, one
  wrong version per rule the row catches.
- **The score is mine.** The system computes the filing's verdict and
  writes it nowhere; WATCHLIST.md and watchlist.toml are written by hand.
- **The count is the ledger's.** The scorer counts once; the formatter
  prints; the runner's check counts the file itself.
- **The registry is the prompt.** A sentence describing a capability that
  now exists is allowed where a rule tuned to a case is not, and it is
  still a hypothesis: prediction in the commit, two runs, stop at the
  second miss. Held on the first pair, as last session's did.
- **A value nothing consumes is not stored.** The two marketable
  securities fields left the block (decision 48 item 6); the reported
  figure carries no currency, and the entry says when it would.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
  This session's shape covered the Part, the check, the loader, where the
  score is written and by whom, the scorer, the node, the rendering, the
  routing row with its prediction, the order of commits by the import-time
  checks, and the rejected alternatives, and was taken with one yes.
- **The check first, seen BLOCKED**; the Part before the scorer; the
  loader before the scorer that imports it; the scorer before the node;
  the node unbound before the rendering; the rendering unwired before the
  routing row, since the roster check ties a name to a node and the
  synthesizer check ties an intent to a formatter; the golden line at its
  sighted baseline before the routing commit; expected.txt after two runs,
  its own commit.
- **A live fetch is asked for before the machine is touched.** One asked
  and given: the exchange's quotes for the 17th.
- **The first live record is read against the reference before it is
  believed.** The ledger answer against Part 14 A's row for 18 September:
  four open, the counts 4, 0, 0, 4, nothing fetched.
- **A new case is sighted with `--case` alone before its golden line is
  written**: the runner's 4.5 showed the routing at clarification_needed.
- **Grep the caller, not the registration.** `predictions.ledger` has one
  caller, the ledger node; `watchlist.predictions` one, the same;
  `fundamentals.READS` one, the scorer.
- **CLAUDE.md is mine and untracked.** A session proposes wording; I apply it.
- No emoji in anything newly written. A count I predict is a count I add up.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect. My real portfolio's data in the repo: Order 6, last. No cached
holdings table; no fallback rate, currency or policy; no adjusted close; no
environment switch for which policy runs. **No invented figures as a runtime
source, and no price a stock will reach anywhere.** No mutation testing until
necessary. No widening of the router's schema to make it a better classifier.
No SIC code range recited from memory. No NOPAT at the company's filed tax
rate. No formatter sentence that states the system's status. No model
proposing a valuation assumption before case 4.3 defines how a proposal is
marked; no midpoint, spread or sorted range; no currency the record does not
carry. **No score written into the ledger by the system; no partial credit
and no distance on a prediction; no prediction scored before its date; no
outcome filled to make one scorable; no event scored off filed facts.**

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

**1304 passed, 6 xfailed, 35 warnings, about 4 seconds.** Run at session
start (1204) and after every commit. Red by design nine times: the new
tests against the unchanged source before each code commit, and against
each deliberately wrong version (§4).

**Golden set: nineteen lines, one pinned failure** ("Should I rebalance my
portfolio?", errors 1). Five runs this session: zero diff on eighteen lines
at session start; the nineteenth line's baseline at clarification_needed;
two runs after the routing commit, identical, the line at ledger. Each
run's stderr was the pinned rebalance failure alone. **Runner 15/16** once,
after the routing commit: 4.5 PASS, 4.2 PASS, 4.6 PASS, 4.1 BLOCKED, the
reason line naming D36.

**The CLI, twice.** The allocation question at session start, as the
runner's 1.1 expects; "How have my predictions done?" after the runner,
the answer in §4.

**Level 4: 3 of 6 cases pass (4.2, 4.5, 4.6); 4.1 blocked by decision; two
have no check.** Read n/16 as a count of well-formed answers and never as
the system being good at research (benchmark.md), never as the range being
right, and never as a prediction having been scored: none is due before
February 2027.

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. `score` is this session's branch,
from 264aa7a. `publish`, `range`, `keys`, `node`, `filer`, `bridge`,
`consolidate`, `selection`, `compliance` and `vocabulary` are merged and
older. `wip/phase7-snapshot` holds rejected Compliance/IPS code.
`wip/rag-early` and tag `rag-early-parked` hold the RAG code.
`quant-inventory-parked` at 8d87455 holds the tree before the seventeenth
session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`e289a03682f2`**, 25 migrations, linear, all applied. No migration and no
reseed this session; **no row written by any loop this session**. **The paid
loops write to this file**: the golden lines on JPM and GOOGL and the
runner's 4.1, 4.2 and 4.6 run the screening node live, its filings fetches
under the seven-day interval and its price fetch under the one-day one; the
ledger question fetches nothing until a figure prediction is due. **The
filings interval runs out on 22 and 23 September**: Apple's facts were
pulled 2026-09-15 22:17 UTC, its filer row 2026-09-16 00:03, the ticker
file and JPMorgan's filer row 01:33, Alphabet's filer row and facts 01:38.
**The price interval runs out at 22:54 UTC on the 18th**, every holding's
last fetch, GOOGL's 23:17. A paid run after either instant fetches again,
and a session running one says so first. Tables that matter:

- `portfolios`, `transactions`; **`assets`: 10 rows**, the nine holdings and
  **GOOGL, id 15, created by the node on 17 September**: name "Alphabet
  Inc." from EDGAR, currency USD, asset class, sector and instrument type
  NULL by design (decision 57). A reseed does not touch it.
- `daily_prices`: 6,999 rows and not a fixed count; **GOOGL's six rows, 10
  to 17 September 2026, source yfinance, all six the exchange's print**
  (Part 9 C). `macro_data`: 206 and growing.
- `ticker_ciks`: 10,422 rows, the SEC ticker file as of 2026-09-16 01:33
  UTC. `filers`: three rows, Apple (3571), JPMorgan (6021), Alphabet (7370).
  `filed_facts`: 28,787 rows, Apple's 15,132 and Alphabet's 13,655, us-gaap
  only. `filed_fetch_metadata`: two rows. All unchanged this session.
- `financial_statements`: 65 rows, neither the reader's store nor a source
  (decision 52). `shares_history`: 947 rows, never a source. `fx_rates`,
  `fx_fetch_metadata`: empty.

**There is no holdings table.** Portfolio 3, "Benchmark Portfolio", is the
only portfolio: nine ledger rows, cost basis 284,500 plus 15,500 cash, USD,
policy `ips.toml`. GOOGL is not held: it has an assets row and no ledger row.
Adobe has no assets row, no filers row and no facts.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py`, `test_screening.py` | the screening node, by `nodes.PHILOSOPHY_PATH` (decision 30); PHI-4.1's three parameters by `screening.range_assumptions` |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py`, `test_watchlist_loader.py`, **`test_watchlist_predictions_loader.py`** | the screening node, by `nodes.WATCHLIST_PATH`, through `portfolio_tool/watchlist.py`: the candidates and their growth pairs; **the ledger node, the same path, the prediction rows** |

### The philosophy check, as it stands

Unchanged this session. `screening_agent_node`, intent `research`, plan
`[ScreeningAgent]` alone, one ticker from extraction; the calls in order
are the ticker file, the submissions document, the exclusion on the code,
the company facts, the last close, the range, the screen. Publishes
`shared_data["screening"]` with the block, the price and the range, each
stop published beside what it stops. On Alphabet today: the screen stops
at PHI-2.1 for FY2021 (decision 48, D36), the range publishes regardless,
129.39 to 205.62 on FY2025, the price is the last stored close.

### The ledger, as it stands

`ledger_agent_node`, intent `ledger` (decision 58), plan `[LedgerAgent]`
alone, no parameter read. The calls in order:

| Step | Call | Store | Raises or stops |
|---|---|---|---|
| the ledger | `watchlist.load_watchlist`, `watchlist.predictions` | | a file that does not load: error |
| the date | `nodes.utc_today` | | |
| the figures, **only for a candidate with a figure prediction whose date has come** | `filings.cik_for`, `filings.update_filer`, `filings.update_filed_facts`, `filed_years_for`; `source` put on the block | `ticker_ciks`, `filers`, `filed_facts`, `filed_fetch_metadata` | a ticker the file lacks: error |
| the scoring | `predictions.ledger` over the rows and the blocks | | a designed stop is the record's `unscored` reason; a defect raises |

Publishes `shared_data["ledger"]`: as_of (the UTC date), watchlist (the
path), records (D45: id, candidate, kind, statement, made_on, due, status,
a figure's metric, bound, value and period, `score` as written, `filing`
with reported, result, form, accn, filed and source, `unscored`, `agrees`),
summary (predictions, scored, due, open), figures (per candidate read:
ticker, CIK, name, source, pull instant). Today nothing is due, so the node
fetches nothing and publishes four open records in 8 ms. The formatter
prints the header with the as-of, the count line with the file's name,
one block per prediction with its status line, the figures read, and what
was not done.

**The scorer**, `portfolio_tool/predictions.py`, pure: `status` by the due
date (D43); `verdict` on a figure prediction over the reader's block, the
period's own annual report, `revenue` as a field and the three metric keys
through `metrics_by_year`, strict and unrounded (D41, D42), the filing from
the provenance of the fields the metric reads (`fundamentals.READS`);
`record` and `ledger` assembling the records and the counts once. What it
refuses is Part 14 E's list. `free_cash_flow_yield` is refused by name
since it depends on the price.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing. Three documents: company facts and submissions from
  `data.sec.gov`, the ticker file from `www.sec.gov/files/company_tickers.json`.
  Each request asked for before it was made. **The reader's path is the
  ticker file, then the submissions document, then the facts: the facts
  hang off the filers row**, and a node that skips the second step fails
  on the third.
- **The price provider** is `nodes.price_provider()`, a function so a test
  stands one in; it asks the library for the unadjusted close (Part 9).
- **The exchange's historical table lags by hours, not days**: asked at
  about 22:30 UTC on the 17th it stopped at the 16th; at about 02:00 UTC on
  the 18th it carried the 17th.
- `config.toml` carries five fetch intervals. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; `config.toml` is read relative to the project
  root, so scripts run from the root. The whole suite on a scratch copy:
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest`.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router. A question can
  be piped in: `printf 'question\n:q\n' | python src/agents/cli.py --portfolio 3`.
- **`quant/fundamentals.py` imports `filed_figures.FIELDS`**, the one place
  the block's shape is defined, thirteen fields since this session, and
  carries `READS`, the fields each formula reads; **`predictions.py`
  imports `fundamentals.METRICS`, `READS`, `metrics_by_year` and
  `watchlist.Prediction`, `Score`**; **`agents/nodes.py` imports
  `predictions.ledger`, `status` and `watchlist.predictions` inside the
  ledger node**, so the loader is before the scorer and the scorer before
  the node in any commit order.
- **`nodes.utc_today()`** is the ledger node's clock, a function so a test
  pins the date; the screening node still reads the clock inline.
- **`tests/test_ledger_node.py` imports the `provider` fixture from
  `test_screening_node.py`** by name, and `tests/test_ledger_formatter.py`
  imports the block from `test_predictions.py`; **`check_4_5` runs in
  pytest over the scorer's records**, so a change to the check is seen by
  pytest through the rendering. The runner still is not part of pytest.
- **`tests/golden/edgar_facts_aapl.csv` has mixed line endings**, 97 of 104
  lines CRLF; it is edited on the bytes, each line keeping its own ending.
- **zsh does not split an unquoted variable into words.** Write test paths
  out. **zsh reads a bare `=word` as a command lookup**. **A `grep -c`
  that finds nothing exits 1 and stops a `&&` chain.**
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
  fields of the figures block. `backtest/metrics.py` keeps its own copies of
  the risk metrics for the backtest intent.

---

## 4. What the twenty-fourth session did

`git log --oneline 264aa7a..HEAD`, twenty-one commits with this file. Case
4.5 into the graph, the Part first, then the check, and the two carried
items and decision 48's item 6.

**The loops, first.** pytest 1204, the CLI on the allocation question as
expected, then with a yes the golden set with stderr kept and the runner,
one after the other, inside every interval: zero diff on eighteen lines,
14/15, 4.1 BLOCKED at PHI-2.1 for FY2021 naming D36. The branch the brief
named did not exist and was created on the owner's yes.

**The two carried items.**
- **7d1f3cb** Part 9 C: the exchange asked for the 17th on a yes, its table
  carrying it, 347.33 equal to the stored row, six of six, the note saying
  the provider's figure on that row is the node's stored close.
  **b68c5ad** the candidate closes test pins the date; seen naming the 17th
  on a print a cent off.
- **7744259** `blocked_on_screen` says the question did not reach the check.

**The shape**, one yes: the Part with a synthetic due prediction as the
falsifier; what `check_4_5` asserts and cannot see; the loader's rows and
refusals; where a score is written and by whom; the scorer; the node; the
rendering; the routing row as a new intent, with the prediction that the
sighting would show out_of_scope; which loop sees what; the order of
commits; the rejected alternatives (the model counting or summarising the
ledger, the formatter counting, the system writing a score, a discriminator
row on research, scoring an event off filed facts, a distance, fetching
every candidate's facts on every ledger question, an unfiled period as
wrong, a default as-of).

**Under the yes, in order.**
- **213fbe8** Part 14, D41 to D45, sections A to F: the four real
  predictions at three dates; Alphabet's FY2025 revenue and cost of revenue
  as filed; S-1 to S-7 on them; E-1 to E-3; F1 to F8. **6f20367** the
  ratio's float corrected the same day, written ending 997 without being
  computed, 998 when computed. **88e0e7f** E-1's score dated on the due
  date, not before it, the loader having refused the fixture that carried
  the Part's date.
- **f6d6f4a** `check_4_5` and `blocked_on_ledger`; sixteen cases, n/16.
  Sighted BLOCKED on `--case 4.5` alone: the router at clarification_needed
  with an empty plan, not the out_of_scope the shape predicted.
- **1e544d3** the loader's prediction rows, `Prediction` and `Score`, and
  41 tests; seen failing against the unchanged source (41) and against a
  version accepting a partial score (6), bytecode off. The metric's
  vocabulary left to the scorer.
- **6202ae7** `portfolio_tool/predictions.py`, pure, 35 tests to Part 14,
  and `fundamentals.READS` held to the formulas; seen failing without the
  module (35), against a version reading "at the bound" as wrong (S-3)
  and against one rounding to the million (F7), bytecode off.
- **d03831b** the ledger node, unbound, 9 tests over the screening test's
  stand-in provider with the date pinned; seen failing against the
  committed nodes.py (9) and against a version fetching for open
  predictions (3), bytecode off. The filers row step added after the first
  run failed on the facts.
- **9d28a14** the rendering, unwired, 15 tests through `check_4_5` over the
  scorer's records on the committed ledger and on Part 14's synthetic one
  written to a temporary file; seen failing against the committed
  formatter (15) and against a version dropping the reason (3), bytecode off.
- **aa8e0c0** the golden set's nineteenth line; **972b260** its baseline
  recorded at clarification_needed, one run.
- **38c8647** the routing row: intent `ledger` with its registry sentence,
  `LedgerAgent` in the roster, the graph binding, the terminal row, the
  synthesizer entry and dispatch, the table and prompt tests; the
  prediction in the message. **28192ad** expected.txt after two identical
  runs, the line at ledger with LedgerAgent, nothing else moved.
- **The runner, 15/16**: 4.5 PASS.
- **The first live record, through the CLI**: as of 2026-09-18, four
  predictions, 0 scored, 0 due, 4 open, each with its id, candidate, stated
  figure or event, dates, statement and "open, due <date>"; nothing
  fetched; Part 14 A's row for the day. It printed the ledger's absolute
  path: **b33e582** the file's name instead.
- **e85b170** Parts 12 and 13: the two `marketable_securities` fields leave
  the block, decision 48 item 6, the reference first, the field-list test
  red for one commit. **4d51ddb** the fields out of `FIELDS`, the csv rows'
  field column blanked with a note on the bytes, the pinned counts moved.
- **904b2b9** the record: seven entries, three resolved, the header.
- **cedf0e7** benchmark.md's status note and the count's dated note.

**Not done, on purpose.** The research agent, decisions 51, 52 and 54, the
seven emoji headers, the philosophy topic lookup, the CIK confirmation
against the submissions document's tickers, the currency on the range,
the close and the reported figure: all outside the brief, the last one
logged again.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- **58**: the ledger is its own intent, `ledger`, terminal `LedgerAgent`,
  closed, since research is one named company and a ledger question names
  none. Taken with the shape's yes. Rejected: a discriminator row on
  research, extending ScreeningAgent.
- **48, item 6**: the two `marketable_securities` fields deleted from the
  block; nothing recomputed. Item 7's second half stays pending, so 48 stays
  on the list.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve. **Eleven by count**, unchanged: none opened, none
closed. CLAUDE.md's line reads "10 on 17 September, 12 with 56 and 57
numbered" and is the owner's to reconcile. The cap is 25.

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
  halves before Order 5. Not this session: 4.3 and 4.4 remain.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12. Level 4: 4.2, 4.5 and 4.6 PASS; 4.1 BLOCKED by
decision, the runner's reason line saying why; 4.3 and 4.4 have no check.
The ledger has four open predictions and no scored one, and the first due
date is 1 February 2027. n/16 is a count of well-formed answers. What the
runner cannot see: whether the range's ends are right (Part 11 C in
pytest); whether a filing's verdict is right (Part 14 C in pytest); and any
due prediction at all until 2027, its due branch running in pytest only.

---

## 7. Next steps, in order

**1. The research agent**, cases 4.3 and 4.4, where the compliance gate is
designed for real and a model's proposal gets its vocabulary (Part 11 E).
3.2 is rewritten at the commit that makes 4.3 answerable (benchmark.md).
The reading tool's contract, summary with source and uncertainty, is the
first shape to bring.

**At the end of Order 4: the full test** (§5), before Order 5.

### Later, with reasons

- **1 February 2027**: W-2.1 and W-2.2 fall due. The first ledger question
  on or after it fetches Adobe's submissions document and facts live, a
  session saying so first; the first live due record is read by hand
  against Adobe's 10-K before it is believed (KNOWN_GAPS, four entries).
- The currency on the range, the close and the reported figure, when a
  case asks (KNOWN_GAPS).
- The formatter headers carrying an emoji, seven in `nodes.py`. One commit,
  the runner run against it. Work, not a decision.
- CLAUDE.md, the owner's to change: the pending list line, eleven on 18
  September; the golden command's `2>/tmp/golden_err.txt` in place of
  `2>/dev/null`.
- A philosophy topic lookup: a discriminator row on `research`, when a case asks.
- The node does not confirm the resolved CIK's submissions document lists
  the ticker asked (KNOWN_GAPS, the tickers entry).
- Decisions 51, 52 and 54, each its own sitting.
- The registry text naming VaR, drawdown and risk parity: a prompt change,
  prediction first, two golden runs.
- `operating_margin` and `free_cash_flow` get formulas, and
  `return_on_invested_capital` its tax rate on the ledger node, when a
  prediction names one (KNOWN_GAPS).
- The seven-day cache runs out on 22 and 23 September; the price cache at
  22:54 UTC on the 18th; the next paid run after either fetches, and says
  so first.

---

## 8. Rules learned the hard way

**A prediction about routing before the registry describes the capability
is a guess.** The shape said out_of_scope; the router said
clarification_needed. The hypothesis the rule is for is the one after the
registry sentence, and that one held on two runs. Sight first, predict
from the sighting.

**A reference row is held to the document's rule before it is written.**
E-1's written score was dated before its due date, a shape the ledger's
own test has refused since the ledger existed; the scorer took it because
the scorer never validates a written score, and the loader caught it the
moment a fixture went through the file. Part 14 D was corrected the day it
was written.

**Compute the float you write down.** Part 14 C stated the ratio's float
ending 997 without computing it; the float of the 28-digit quotient ends
998. A digit in the reference is a claim, and a claim is checked.

**The reader's facts hang off the filers row.** The ledger node first
called the ticker file and then the facts, and the facts refused: the
submissions document comes between them, as the screening node's table
already said. The test pins the order.

**An answer prints no path.** The first live ledger answer carried the
watchlist's absolute path with the home directory in it; the record keeps
the path and the answer prints the file's name.

**A note's count is counted.** A Part 13 C note said the reader's raises
for JPMorgan go from nine to seven where the fixture's set was ten; the
sentence was rewritten without a number before the diff was shown.

**One wrong version per rule the row catches.** The scorer was run against
a version reading "at the bound" as wrong and against one rounding to the
million; each failed exactly the row written for it, S-3 and F7.

**A reference row for "the last close" defends a call, not tomorrow's
figure**; **a fixture with two sources finds a rendering that prints one**;
**a designed stop catches the designed error and nothing wider**; **sight a
new case before writing its golden line**; **the registry's descriptions
are the prompt**; **a one-day window on the exchange's table returns
nothing, not an error**; **add up the pending list**; **the owner's
documents are written on a separate word**; **the golden loop's stderr
goes to a file**; **a table-reading test pins a count**; **a pinned csv
can carry two line endings**; **zsh does not word-split an unquoted
variable**; **test regexes say the order the code says it in**; **measure
the brief's expectation before writing the shape**; **a csv with CRLF
endings is edited on the bytes**; **a witness for a list is a same-value
pair on one filing**; **say which loop cannot see a change**; **a test
over the suite's database copy owns the rows it reads**; **a formatter
states what the data says and never what the system is**; **the
import-time checks decide the commit order**; **two paid loops on one
SQLite file run one after the other**; **a typed date is checked against
the row it came from before the test runs**; **an instruction with words
missing is read against the record**; **a claim about the world goes into
the record only after it is checked, or marked as unchecked**; **a schema
test's database half is red between the commit and the owner's
migration**; **a cache row that means "as of this pull" moves its date on
every pull**; **a number in config goes into the document in the same
commit as the code that requires it**; **grep the writer the reader
reads**; **delete the caller before the callee**; **a rule taken from part
of a source is measured over all of it**; **a wrong version checked in
place can run the previous one's bytecode** — still true, from earlier
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
python tests/benchmark/run_cases.py --case 4.5

python src/agents/cli.py --portfolio 3        # :q to quit
printf 'How have my predictions done?\n:q\n' | python src/agents/cli.py --portfolio 3

grep -rn "SymbolName" src/ tests/ --include='*.py'
git status --short

# this session's commits: count from the trunk's tip at session start
git log --oneline $(git merge-base baseline-v1 HEAD)..HEAD
git rev-list --count $(git merge-base baseline-v1 HEAD)..HEAD

# by hand, from the project root, after a migration or a seed change:
alembic upgrade head
python src/portfolio_tool/scripts/seed_portfolio.py --reset

# what the database says it is at (expected e289a03682f2):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# ten assets, GOOGL the tenth and not held; daily_prices and macro_data move;
# the filings tables as of this session's end:
sqlite3 data/portfolio.db "select count(*) from ticker_ciks; select cik, sic, pulled_at from filers; select cik, count(*) from filed_facts group by cik;"
sqlite3 data/portfolio.db "select date, round(close,2), source from daily_prices where asset_id=(select id from assets where ticker='GOOGL') order by date;"

# a check run against an edited, deliberately wrong module:
find src tests -name __pycache__ -type d -prune -exec rm -rf {} +
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/<file>.py

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only score
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~4s, no model calls | Do the components still work; does every reference Part reproduce, Part 11 on typed blocks and the node's assembly, Part 14 on the typed block and the fixture's rows; does each node fetch in order and publish its block; does each rendering pass the runner's check; are the candidate's stored closes the print |
| CLI | ~3s, one call | What it is actually doing: the plan, the parameters, the reasoning line, the answer text |
| Golden set | ~90s, cents, **writes filed and price rows past their intervals** | Did routing change anywhere (nineteen lines, one pinned failure). Blind to parameters and answer text; stderr kept to a file |
| Benchmark runner | ~2min, cents, **writes filed and price rows past their intervals** | How many cases pass, n/16. Blind to the four intents outside the roster, to 4.3 and 4.4, to whether a range's ends are right, and to any due prediction until 2027 |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once.
