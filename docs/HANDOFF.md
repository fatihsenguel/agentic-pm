# AGENTIC_FINANCE — Session Handoff

**Session date:** 15 and 16 September 2026 (eighteenth session; it crossed midnight). Regenerated at its end.
**Branch:** `bridge`, cut from `baseline-v1` at b0f1499, the trunk's tip at session start. **`baseline-v1` is the trunk**: each session branch is merged into it with `--ff-only` when the loops are green; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count b0f1499..HEAD` — 10, plus the one that lands this file. **Not merged and not pushed**: the owner merges and pushes; `origin`'s push URL is `no_push`. **One commit is the owner's to make before the merge**: the workbook opened and saved in Excel, which restores the cached values the openpyxl write at 78c8b02 dropped (the pattern of 515732b).

**State:** pytest **958 passed, 6 xfailed**, up from 922 by the bridge's 36 tests. **The golden set and the runner were not run**, on the owner's instruction and my agreement: nothing this session touched routing, a prompt or an answer's text, and neither loop reaches the metrics, the loader, the screen or the reader. The CLI ran once at session start on the allocation question and answered as the runner's 1.1 expects. **The first live EDGAR request this project has made** stored Apple's facts and reproduced Part 12 B, 70 cells of 70.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session's instruction counted the pending decisions at
41 and the list held 32; the count was checked before the triage and the
correction is in f3bb3d0. And my own triage paragraph in that commit said
seventeen remained when sixteen did, an addition not done: corrected here.
A count you state is a count you add up, including your own.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: step 1, the bridge between the reader's block and the metrics, landed this session (§4). The philosophy check and the filings reader are pure modules nothing in the graph reaches; the node is decision 29. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass at 175f439, not run since. Level 4: six research cases, none running. Unchanged. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Twelve cases. Unchanged. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 66 trigger lines read something other than "none", counted by grep; a marked heading keeps a line reading "none". Log a finding only with a trigger or a decision number. New this session: "The pull date the filings record keeps is UTC", "Apple's FY2014 operating cash flow does not resolve under Part 12 C's tag". |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, Parts 1 to 13. **Part 12 G is new**: net debt and NOPAT at the stated rate on Apple's five years, the bridge's rows. Part 10 A carries a dated note on the block's shape; D32 and D33 carry their decisions; Part 13 C and E5 carry dated notes. Never update it to match code output. |
| `tests/golden/expected_values.xlsx` | The workbook. `Filings` sheet gained section D for Part 12 G, fifteen verdict cells. **Its cached values are gone until the owner saves it in Excel** (§2). |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. **PHI-2.1 now states the tax rate**, 20%, the one edit this session made to the owner's document, on the owner's word (a16dbdd). |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027. Nothing reads it. Unchanged. |
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
and a judgement half whose first tools exist as pure modules and are not yet
joined to the graph. The router is scaffolding until the tool layer is
complete. **No deadline. Correctness over speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.**
- **Policy lives in config, not code**, and every number in config is in the
  document first. This session's form: the tax rate went into PHI-2.1's
  sentence before it went into `philosophy.toml`, and the TOML could not
  move first because the loader would have refused the committed document
  either way.
- **Two policies, two questions.** The IPS says what may be held; the
  philosophy says what is worth wanting.
- **Raise, do not repair.** A refusal is an honest failure; a plausible wrong
  answer is not. This session's form: a metric whose assumption nobody
  stated is absent, never computed at the company's filed rate; a year
  carrying a figure key the reader's fields do not name raises rather than
  being read around.
- **Typed facts are not a source.** A company's figures come from the
  reader; typed figures stay in tests. The reader has now fetched once.
- **References before code**, measured over the whole source. Part 12 G
  before the bridge, each row its own commit, the workbook beside it.
- **No price forecasts as numbers.**
- **A capability nothing reaches is inventory**: deleted behind a tag, not
  kept with a note.
- **Where a filed figure stops being exact**: every figure is read as a
  Decimal, a sum, a difference and a product with a stated rate are exact,
  and the ratio is the first float (Part 12 G, `quant/fundamentals.py`).

### How I work on this

- Every change starts as a written decision in plain words: what it is, what
  changes on a yes, the rejected alternatives, which loop sees it. One commit
  per change, test first and seen failing for its own reason, `git status
  --short` and the diff read before each commit, and the word yes before it
  lands; "okay" is not one.
- **Grep for the caller, not the registration, and grep for the writer
  before trusting a reader.**
- **Checking against a wrong version runs with bytecode caching off**
  (`PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`, `__pycache__` deleted).
- **A field, not a layer, is the unit of a bridge commit.** The borrowing
  fields landed in one commit across module, fixture and tests; the tax
  rate in the next across document, config, loader, metrics, screen and
  tests. Ten files in one commit is one change when it is one field.
- **A scripted edit names the fixture it landed in.** A search string that
  matches the first of two fixtures puts the lines in the wrong one; this
  session that was caught by the metrics coming back absent, not by reading
  the diff. Check the target after every scripted insertion.
- **The migration, the reseed and any rewrite of stored rows are run by
  hand**, and the output is pasted. None this session.
- **PHILOSOPHY.md and IPS.md are mine to edit.** A session brings the wording.
  This session the owner said to go ahead with the wording brought, and the
  edit is in the same commit as the config that reads it.
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
notes on dead code: delete it behind a tag.** No NOPAT at the company's
filed tax rate: the rate is mine and stated in the clause.

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

**958 passed, 6 xfailed, 26 warnings, about 3.8 seconds.** Run at session
start (922), after the borrowings commit (936) and after the tax rate commit
(958). No 34-second run this session.

**The golden set and the runner: not run.** Last run at 175f439, the
seventeenth session's tip: golden zero diff with one pinned failure, runner
12/12. Nothing since touches what they see: the two trunk commits after
175f439 rewrote `.gitignore` and `.env.example`, and this session's commits
touch the record, the reference, the workbook, the philosophy document and
config, and four modules under `portfolio_tool` that no graph node imports
(`quant/fundamentals.py`, `philosophy.py`, `screening.py`,
`filed_figures.py`). The router, the prompt, the nodes and every formatter
are byte-identical to 175f439. A run would pass in both states and
distinguish nothing.

**The CLI, once, "What is my current allocation by asset class?":** intent
`data_fetch`, plan DataAgent then PortfolioAnalysisAgent, five asset classes
summing to 408,080.00 USD, priced as of 2026-09-14, the look-through caveat
printed. As the runner's 1.1 expects.

**Level 4: 0 of 6 cases run.**

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. `bridge` is this session's branch,
from b0f1499. `consolidate`, `selection`, `compliance` and `vocabulary` are
merged and older. `wip/phase7-snapshot` holds rejected Compliance/IPS code.
`wip/rag-early` and tag `rag-early-parked` hold the RAG code.
`quant-inventory-parked` at 8d87455 holds the tree before the seventeenth
session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`97d3708851e5`**, 23 migrations, linear, all applied. No migration and no
reseed this session. Tables that matter:

- `portfolios`, `transactions`, `assets` (9 rows).
- `daily_prices`: 6,966 rows and not a fixed count; it grows when a query runs
  after new closes.
- **`filed_facts`: 15,132 rows, all Apple's (CIK 320193), from the first
  live fetch on 16 September.** `filed_fetch_metadata`: one row, Apple,
  `last_fetch_time` 2026-09-15 22:17 UTC (KNOWN_GAPS, the UTC entry). The
  fetch is not asked again within `filings_fetch_interval_days`, 7.
- `financial_statements`: 65 rows, neither the reader's store nor a source
  (decision 52). `macro_data`: 197 rows and growing.
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

### The workbook

`tests/golden/expected_values.xlsx`, eleven sheets. 78c8b02 wrote section D
onto `Filings` with openpyxl, which drops every cached value in the file
(136,802 bytes to 102,911). **The owner opens and saves it in Excel and
commits that save as its own commit**, the pattern of 515732b; until then
the fifteen new verdict cells and every older formula show no value outside
Excel. The write was verified against HEAD: 6,856 non-empty cells over
eleven sheets, zero differences outside the new rows.

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
  when it is missing; **the real value is set** (decision 43 closed) and
  `data.sec.gov` served one request with it. `www.sec.gov` has not been
  asked yet.
- `config.toml` carries five fetch intervals. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import. The whole suite on a scratch copy:
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest`.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router.
- **`quant/fundamentals.py` imports `filed_figures.FIELDS`** for the block's
  figure vocabulary, since a16dbdd: the one place the block's shape is
  defined. A quant module depending on the reader's module was a choice
  over a second copy of the list; it is named here so it is not found by
  surprise.
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

## 4. What the eighteenth session did

`git log --oneline b0f1499..HEAD`, 10 commits, plus the one that lands this
file. Order 4 step 1, and nothing else: no node, no intent, no prompt change.

**The loops, first.** pytest 922, the CLI on the allocation question as
expected. The golden set and the runner: agreed not run, the reason in §2.

**The record catches up (be6c436).** The `.gitignore` entry closed on
41b03d5, the `.env.example` paragraph on b0f1499, decision 55 answered
yes with a dated note in Part 13 C; `force_update_asset_info` has no
caller since the seventeenth session's deletions and the note says so.

**The triage (f3bb3d0).** The pending list held 32, not 41. Seven closed
(15, 18, 23, 38, 43, 53, 55), eight merged (6 and 14 into 51; 9, 11 and 36
into 45; 30 and 50 into 29; 35 into 17), one moved to §7 as work (32, the
emoji headers), sixteen kept. Nine KNOWN_GAPS triggers repointed. 38's
entry keeps a live trigger on the owner's amendment: the check stays, since
it found the JNJ wrong face on 9 September. The commit's paragraph says
seventeen kept; sixteen is right.

**Decisions 46 and 47, taken (§5).** Then the reference: Part 12 G's net
debt row (2173643), its NOPAT row (dba9104), Part 10 A's shape note
(4e9398d), the workbook's `Filings` section D (78c8b02).

**The bridge, by field.** 9d176e2: `net_debt` over the three borrowing
fields, invested capital from the same three, every figure a Decimal and
the ratio the first float, Part 10's fixture in the block's shape; 28
failures and 10 errors seen first. a16dbdd: the stated rate as PHI-2.1's
parameter, the document's sentence first, the loader requiring it, `nopat`
a named function, the screen collecting the stated assumptions and
refusing two rates, a year carrying a key the reader's fields do not name
refused; 52 failures and 22 errors seen first, then only the tests loading
the committed TOML, green the moment it carried the rate. One slip on the
way, caught before the diff: a scripted insertion put Apple's filed rates
into Part 10's fixture (§8).

**Decision 49, brought and deferred.** Four commits (provider method, a
`filers` table, the cache rule, the code on the reader's output); the
owner's yes was to the fetch, so the item moves whole to the next session.

**The first live fetch.** Apple's company facts through
`update_filed_facts`: 15,132 rows in 1.6 seconds, seventeen fiscal years
assembled, 70 of 70 Part 12 B cells and all five year ends and filed dates
equal to the reference. Two observations logged, not chased (KNOWN_GAPS).

**Also:** Part 13 E5 marked decided (de0d439); the KNOWN_GAPS sweep
(b6912dd).

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- **46.** The rate NOPAT is taxed at is a parameter of the clause that
  names the metric, `tax_rate` on PHI-2.1 in `philosophy.toml`, stated in
  the document's sentence first; 0.20 for the synthetic philosophy, the
  rate Part 10 was computed at. The metrics take the stated assumptions
  beside the block; the block's `effective_tax_rate` is carried as filed
  and not read. Rejected: `config.toml` (values the same for anyone, and a
  personal philosophy could not carry its own rate); a document-level
  table outside every clause and PHI-7.1; a constant in code.
- **47.** `net_debt` is a named function in `quant/fundamentals.py` with
  its own reference row, not a key a clause may name; a borrowing is one
  of the three named fields and a finance lease is not one; D33's "a
  borrowing tag the block does not name is a raise" is a known limit, the
  list grows one measured tag at a time; the revisit trigger for leases is
  the first candidate whose PHI-3.1 verdict moves when they are counted.
  The key stays `net_debt_to_ebitda`; a formula netting securities would
  be a new key (D24).
- Where a filed figure stops being exact: at the first ratio.
- The triage's fifteen closures and merges, listed in §4.
- 43 closed: the contact is set. 55 closed: done. 38 closed, the check
  stays. 53 closed: delete behind a tag, when a session takes it.
- **The full test at the end of Order 4** (owner's, recorded in the
  seventeenth session, unchanged): when Order 4's last commit lands, the
  project stops for a full test across both halves; Order 5 begins only
  when Levels 1 to 3 still pass, all six Level 4 cases are well-formed, no
  wrong face is left in the owner's notes, no invariant is violated, and
  the open record is under a number the owner sets then.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve. **Fourteen**, under the cap of 25 (CLAUDE.md's line
still reads 32 and is the owner's to update).

10. A window return as a measure with a reference.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding. Absorbs 35, a
    rank selection in extraction: one selection axis.
22. Volatility over as-traded closes or a total-return series.
29. **The node for the screen**, next after decision 49. Absorbs 30, what a
    philosophy is bound to, and 50, ticker to CIK: both are read by the node
    and decided when it is built. The UTC pull date entry waits on it too.
41. Writing what nets against debt into PHI-3.1's clause text. Mine. Part
    12 F has the wording; PHI-2.1 got its sentence this session and PHI-3.1
    could get its own the same way.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, the span and
    two-weights clarification rules; 11, the two verbatim benchmark
    few-shots; and 36, what `reasoning` is for.
48. Part 13 E's questions 3, 4, 6 and 7 (5 decided with 47, 8 with D34).
    W-1 cannot be screened on filed figures until 3 and 4 are answered.
49. **A SIC code on the block**, brought this session, four commits:
    `EdgarProvider.filer(cik)` returning cik, name, sic, sic_description
    from the submissions document, held to `edgar_submissions.csv` through
    a stand-in session; a `filers` table (cik, name, sic, sic_description,
    pulled_at), migration unexecuted with its schema test; `filings.update_filer`
    on `filings_fetch_interval_days`, a changed code overwriting and moving
    the date; `filed_years_for` returning `sic`, `sic_description` and
    `sic_as_of` beside `years`. Not stored: `ownerOrg`, `entityType`,
    `fiscalYearEnd`, nothing consumes them. Rejected: fetch at screen time;
    columns on `filed_fetch_metadata`; the `assets` row. The first commit
    stands on its own if only one fits.
51. **The four live intents outside the benchmark roster** — optimization
    (max Sharpe, golden-pinned, runs with no portfolio), rebalancing (raises
    on a missing target; two known defects behind it), backtest (in-sample by
    construction), macro (answers since db567c8, prints a risk stance):
    delete or keep, each moving golden lines and an agent in `AGENTS`. My
    lean, deletion where no benchmark case asks; rebalancing first, since
    decision 13 would rebuild it from a reference. Trigger: the full test at
    the end of Order 4, or earlier if one of them produces a wrong face.
    Absorbs 6, the rebalance tools' fixed euro sign, and 14, "Optimization
    failed: None".
52. **The Yahoo-fed tables** — `financial_statements`, `fundamentals`,
    `quarterly_earnings`, with `get_financial_statements` returning nothing
    and its six xfails: delete or keep. Their last readers went with
    `data_tools.py`.
54. **BaseAgent's tool loop** (`process`, `get_tools`, `tool_map`,
    `get_system_prompt`, `TaskType`, the protocol enums) and the three
    `AgentConfig` fields that describe it: delete. Lean delete, **its own
    sitting**: it touches every agent class.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12 at 175f439, not run since and nothing they see
changed. Level 4: defined, six cases, none with a check, none running. The
ledger has four open predictions and no scored one. Read n/14 as a count of
well-formed answers and never as the system being good at research
(benchmark.md).

---

## 7. Next steps, in order

**1. Decision 49, the SIC code on the block**, four commits as §5 states,
each test first. The owner runs the migration and pastes the output.

**2. Decision 29, the node**, after 49: runner checks for 4.1 and 4.6
written first and seen BLOCKED; the intent and agent in the registries; the
node; the formatter; the golden line and the prompt, golden twice with the
prediction written first. The compliance gate is designed with it. The node
assembles the block: `filed_years_for`'s years and code, the ticker (50),
the price with its date, the range (Part 11) and the shares (48, item 7).
W-1 cannot clear the screen on filed figures until 48's items 3 and 4 are
decided: Alphabet files no gross profit and no combined D&A.

**3. Then the valuation pipeline** with Part 11 by hand, and prediction
scoring with its Part.

**At the end of Order 4: the full test** (§5), before Order 5.

### Later, with reasons

- The workbook's Excel save, the owner's own commit, before the merge.
- PHI-3.1's clause text naming what nets against debt (41): the owner's
  sentence, then `philosophy.toml`'s text, one commit, `test_philosophy.py`
  the loop.
- The formatter headers carrying an emoji, seven in `nodes.py`: compliance
  and out-of-scope (the KNOWN_GAPS entry), policy lookup, optimization,
  macro, rebalance and backtest. One commit, the runner run against it.
  Work, not a decision (was item 32).
- Decisions 51, 52 and 54, each its own sitting; 54 touches every agent
  class. 53 is closed: delete behind a tag, when a session takes it.
- The registry text naming VaR, drawdown and risk parity: a prompt change,
  prediction first, two golden runs (KNOWN_GAPS).
- 3.2's rewrite and Part 2's boundary: at the commit that makes 4.3 answerable.
- The tool-boundary pass (45): the first benchmark case that fails for want
  of expression rather than capability.
- The published SIC list on `www.sec.gov`, now that the contact is set
  (KNOWN_GAPS, the fails-open entry).
- The 34-second suite run, if it recurs: `--durations` on that run.

---

## 8. Rules learned the hard way

**A number in config goes into the document in the same commit as the code
that requires it, and not before.** The loader now refuses a clause naming
ROIC without a rate; had the TOML gained the rate first the loader would
have refused it as unknown, and had the loader landed first it would have
refused the committed TOML. One field, one commit, the document's sentence
inside it.

**A scripted edit is checked at the place it landed, not at the place it
was aimed.** An insertion keyed on `"FY2021": {"ends":` matched Part 10's
fixture before Apple's and put filed tax rates and equity into the
synthetic block, where a field the vocabulary allows and nothing reads
would have sat unnoticed. The metrics coming back absent for Apple was the
only signal. After a scripted insertion, print the keys of the fixture it
was meant for.

**A count is added up, twice.** 41 was the instruction's count of a list
that held 32; seventeen was my count of a list that held sixteen. Both
were caught after they were written down, the first before the triage and
the second only when regenerating this file.

**Grep the writer the reader reads, not a writer of the same name**; **a
formatter test with a hand-built input holds the formatter to a shape, not
the node to the tool**; **delete the caller before the callee, and grep the
package init**; **a deletion commit leaves docstrings behind; the next
commit names them**; **a rule taken from part of a source is measured over
all of it**; **a record says what the tree holds, not what the next step
is**; **a wrong version checked in place can run the previous one's
bytecode** — still true, from earlier sessions.

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

# nine assets; daily_prices and macro_data move, do not pin them;
# filed_facts holds Apple's 15,132 rows since 16 September:
sqlite3 data/portfolio.db "select count(*) from assets; select count(*) from filed_facts;"

# a check run against an edited, deliberately wrong module:
find src -name __pycache__ -type d -prune -exec rm -rf {} +
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/<file>.py

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only bridge
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3.8s, no model calls | Do the components still work; does every reference Part reproduce, Part 12 G included; does the bridge read the block's shape and refuse the old one |
| CLI | ~3s, one call | What it is actually doing: the plan, the parameters, the reasoning line, the answer text |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines, one pinned failure left). Blind to parameters, answer text and everything under the judgement half's modules |
| Benchmark runner | ~1.5min, cents | How many cases pass. Blind to the four intents outside the roster and to the judgement half |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text.
