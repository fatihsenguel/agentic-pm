# AGENTIC_FINANCE — Session Handoff

**Session date:** 16 September 2026 (twenty-first session). Regenerated at its end.
**Branch:** `keys`, cut from `baseline-v1` at df22b44, the trunk's tip at session start. **`baseline-v1` is the trunk**: each session branch is merged into it with `--ff-only` when the loops are green; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count df22b44..HEAD` — 8, this file's included, counted after it was added. **Not merged and not pushed**: the owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1102 passed, 6 xfailed**, up from 1094 by 8: five for Part 12 H's margins, one for a year without a cost of revenue, one for a block still carrying `gross_profit`, one for the cost-of-revenue field resolving from each filer's own tag. **Golden set run once**, at session start, zero diff, seventeen lines, the pinned rebalance failure included; nothing since touched what it sees, so it was not run again. **Runner 13/14 three times**: at session start, after the code commit and after the probe text; 4.6 PASS, 4.1 BLOCKED at PHI-2.1 for FY2021 every time, by decision since 6e9cc03. **No live fetch**: every request hit the seven-day cache. The CLI ran once, at session start, on the allocation question. **Decision 48's items 3 and 4 are decided (D36, Part 12 H); 48 stays pending on items 6 and 7, brought as a shape and not taken.**

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session's brief expected the 4.1 stop to move from
PHI-2.1 to PHI-4.1 once the metric keys were decided; measured against the
stored facts before the shape, the stop turned out to be F7, the
lease-inclusive debt tag, not the keys, and it does not move (§4). Misses of
my own, caught before or after landing: the reference commit's note under
Part 12 B swallowed Part 12 C's heading, found by the field-list test at
the next commit and restored as its own commit (03ad5ac); a rewrite of the
Apple csv converted its CRLF endings, seen in the diff and redone on the
bytes before the commit; an assertion in a new test held for Alphabet and
not for JPMorgan, fixed before it landed; a margin quoted as 0.4690 in the
shape and 0.4691 in the reference, the reference being right.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the bridge, the SIC code, the philosophy check node, and now **the metric keys for a filer presenting no gross profit (decision 48, items 3 and 4)**. Left in Order 4: the valuation pipeline (Part 11, case 4.2), prediction scoring (4.5), the research agent (4.3, 4.4), and decision 56, whether Alphabet stays case 4.1's X. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. Level 4: 4.6 passes, 4.1 blocked by decision (two dated status notes under Level 4, the twenty-first session's saying why). n/14. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Fourteen cases. 4.1's reason line names the cause of its stop: D36 on the debt tag until Alphabet's FY2027 report, PHI-3.1 on D&A after it. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 103 lines match `Trigger:`, 73 reading something other than "none", counted by grep. New this session: five entries under decision 48 (§4). |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, Parts 1 to 13. New this session: D36 in Part 12's decision table; Part 12 H, gross margin on Apple's filed figures; Part 13 B's note with Alphabet's cost of revenue and margins; Part 10 A, B and E moved to the new formula; Part 13 E items 3 and 4 marked decided. Never update it to match code output. |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, saved in Excel at c75b73b. Untouched this session; Part 12 H has no sheet, like Part 12 G. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. **PHI-2.2 gained its measure this session** (798d20e), written under the owner's yes. |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027. Nothing reads it. Unchanged; decision 56 asks whether W-1 stays X. |
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
and a judgement half whose first tool, the philosophy check, is now joined
to the graph. The router is scaffolding until the tool layer is complete.
**No deadline. Correctness over speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** Unchanged in form this
  session: the block carries the fiscal years as two dates each and no
  figure; the gross margin change is invisible to the runner for that
  reason and for the stop's order (§4).
- **Policy lives in config, not code.** The philosophy is `philosophy.toml`,
  named once in `nodes.PHILOSOPHY_PATH` until Order 6 (decision 30). A
  metric's definition is its formula in Part 10 B and the clause's text
  names it (PHI-2.1, PHI-3.1 and now PHI-2.2); no parameter carries a
  definition.
- **Two policies, two questions.** The IPS says what may be held; the
  philosophy says what is worth wanting. Two intents now: `compliance` and
  `research`. Since the twentieth session a philosophy question on a held
  ticker no longer runs the IPS check; the golden line pins it.
- **Raise, do not repair.** This session's form: a figure the filer does
  not present is not derived on the way into the block, and a tag that
  measures something else is not admitted to fill a year; the D&A refusal
  stays and the debt stop stands until the filer's own reports move it.
  The standing forms: a check that stops on a missing figure is published
  as a stop and printed as one, no verdict; a ticker the SEC file does not
  list is an error naming it; a code EDGAR does not state stops the check
  naming PHI-3.2.
- **An excluded company's figures are never asked for.** The exclusion is
  decided on the filers row before the company facts are fetched
  (`screening.exclude`); JPMorgan's first live check read no fact.
- **Typed facts are not a source.** The reader has fetched Apple and
  Alphabet; the tests' figures stay in the tests.
- **References before code.** Part 12 H and Part 13 B's rows before the
  formula moved; each test seen failing against the unchanged source and
  two wrong versions before its code landed.
- **No price forecasts as numbers.**
- **A capability nothing reaches is inventory**: deleted behind a tag.
- **A value nothing consumes is not stored.** `gross_profit` left the block
  once no formula read it; the ticker file's company title is not carried.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
  This session's shape covered two items of one decision, was measured on
  the stored facts before it was written, corrected the brief's
  expectation, and was taken with one yes; then the reference commit
  first, and one commit per change, test first and seen failing against
  the unchanged source and against two deliberately wrong versions with
  bytecode off, `git status --short` and the diff read before each commit,
  and the word yes before it lands.
- **A tag joins a field's list on a witness** (D36): a filer that files
  it beside a listed tag for the same period at the same value. A wider
  or narrower measure stays out and its year raises. One exception,
  recorded as one: Alphabet's cost-of-revenue tag.
- **Grep for the caller, not the registration, and grep for the writer
  before trusting a reader.** This session's form: what stops 4.1 is read
  from the stored facts and the node's stop, not from the brief.
- **A live fetch is asked for before the machine is touched.** None this
  session; every run hit the cache.
- **PHILOSOPHY.md and IPS.md are the owner's.** A sentence for PHI-2.2 was
  brought as text, and written into the document only on the owner's
  explicit word.
- **A csv with CRLF endings is edited on the bytes.** `Path.read_text`
  converts them silently and the diff shows every line changed.
- **CLAUDE.md is mine and untracked.** A session proposes wording; I apply it.
- No emoji in anything newly written. A count I predict is a count I add up.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect. My real portfolio's data in the repo: Order 6, last. No cached
holdings table; no fallback rate, currency or policy; no adjusted close; no
environment switch for which policy runs. **No invented figures as a runtime
source, and no price a stock will reach anywhere.** No mutation testing until
necessary. No widening of the router's schema to make it a better classifier.
No SIC code range recited from memory, and no code added to PHI-3.2 from the
published list alone. No "inventory, not capability" notes on dead code. No
NOPAT at the company's filed tax rate. **No formatter sentence that states
the system's status**: a claim like "the valuation pipeline does not exist"
is false in one rendering and rots in all; the data carries the fact.

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

**1102 passed, 6 xfailed, 26 warnings, about 3.5 seconds.** Run at session
start (1094) and after every commit. Red once by design: the new tests
against the unchanged source, 37 failed and 22 errored, before the code
commit.

**Golden set: zero diff, seventeen lines, one pinned failure** ("Should I
rebalance my portfolio?", errors 1), run once at session start. Not run
since: no registry, prompt, router or intent changed, and `expected.txt`
did not move. **Runner 13/14** three times, the last after a593c9e: 4.6
PASS, 4.1 BLOCKED with the reason line naming D36.

**The CLI, once.** "What is my current allocation by asset class?" at
session start, as the runner's 1.1 expects.

**Level 4: 1 of 6 cases passes (4.6); 4.1 blocked by decision; four have no
check.** Read n/14 as a count of well-formed answers and never as the
system being good at research (benchmark.md).

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. `keys` is this session's branch,
from df22b44. `node`, `filer`, `bridge`, `consolidate`, `selection`,
`compliance` and `vocabulary` are merged and older. `wip/phase7-snapshot`
holds rejected Compliance/IPS code. `wip/rag-early` and tag
`rag-early-parked` hold the RAG code. `quant-inventory-parked` at 8d87455
holds the tree before the seventeenth session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`e289a03682f2`**, 25 migrations, linear, all applied. No migration and no
reseed this session. **The paid loops write to this file**: the golden line
and the runner's 4.1 and 4.6 run the node live, and its fetches store rows
here under the seven-day interval; this session every fetch was inside
the interval and no filed row moved. **The interval runs out on 22 and 23
September**: Apple's facts were pulled 2026-09-15 22:17 UTC, its filer row
2026-09-16 00:03, the ticker file and JPMorgan's filer row 01:33,
Alphabet's filer row and facts 01:38. A paid run after those instants
fetches again, and a session running one says so first. Tables that matter:

- `portfolios`, `transactions`, `assets` (9 rows).
- `daily_prices`: 6,966 rows and not a fixed count. `macro_data`: 200 and
  growing.
- **`ticker_ciks`: 10,422 rows, the SEC ticker file as of 2026-09-16 01:33
  UTC**, 8,022 distinct CIKs; Alphabet's carries GOOG, GOOGL, GOOGM and
  GOOGN, JPMorgan's nine tickers, mostly preferred series (Part 13 E item
  7's shape, §5).
- **`filers`: three rows**, Apple (3571), JPMorgan (6021), Alphabet (7370).
- **`filed_facts`: 28,787 rows, Apple's 15,132 and Alphabet's 13,655**,
  us-gaap only. `filed_fetch_metadata`: two rows. JPMorgan's facts were
  never fetched: the exclusion decides first.
- `financial_statements`: 65 rows, neither the reader's store nor a source
  (decision 52). `shares_history`: 947 rows, no source column, never a
  source. `fx_rates`, `fx_fetch_metadata`: empty.

**There is no holdings table.** Portfolio 3, "Benchmark Portfolio", is the
only portfolio: nine ledger rows, cost basis 284,500 plus 15,500 cash, USD,
policy `ips.toml`.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py`, `test_screening.py` | **the screening node**, by `nodes.PHILOSOPHY_PATH` (decision 30) |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py` | nothing |

### The philosophy check, as it stands

`screening_agent_node`, intent `research`, plan `[ScreeningAgent]` alone.
One ticker from extraction. The calls in order, each under
`filings_fetch_interval_days`:

| Step | Call | Store | Raises or stops |
|---|---|---|---|
| ticker to CIK | `filings.cik_for` over `EdgarProvider.tickers` | `ticker_ciks` | a ticker the file lacks: error |
| name and code | `filings.update_filer` over `EdgarProvider.filer` | `filers` | |
| the exclusion | `screening.exclude` on ticker and code | | listed code: one excluded finding, done; no code: stop naming PHI-3.2 |
| the figures | `filings.update_filed_facts`, `filed_years_for`, `screening.screen` | `filed_facts`, `filed_fetch_metadata` | a missing figure: stop naming the clause (PHI-1.2, D25) |

Publishes `shared_data["screening"]`: philosophy, statements, subject
(ticker, CIK, EDGAR's name), as_of (the UTC date of the run), sic,
sic_description, sic_as_of, years (dates only), findings, stopped, source,
facts_as_of. Every pull instant carries `+00:00`; the formatter prints the
day marked UTC. The formatter has three renderings: excluded, stopped,
screened. The compliance gate is idle by construction: the validator
refuses ComplianceAgent under research, and the answer says no position is
implied; the gate is designed at 4.3.

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
  `data.sec.gov`, the ticker file from `www.sec.gov/files/company_tickers.json`,
  an object keyed by position with `cik_str`, `ticker`, `title`, 10,422
  entries on 16 September. Each request asked for before it was made.
- `config.toml` carries five fetch intervals. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; `config.toml` is read relative to the project
  root, so scripts run from the root. The whole suite on a scratch copy:
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest`.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router.
- **`quant/fundamentals.py` imports `filed_figures.FIELDS`**, the one place
  the block's shape is defined.
- **The four-digit SIC rule is held twice**: `screening._SIC_CODE` and
  `providers/edgar.SIC_CODE`, the same regex.
- **The node reaches the provider through `nodes.edgar_provider()`**, a
  function so a test stands one in; the node test's stand-in answers the
  three EDGAR methods from the golden csvs.
- **`tests/test_research_formatter.py` imports `run_cases`** from
  `tests/benchmark` by a path insert, so the runner's checks hold the
  formatter without a model call. The runner still is not part of pytest.
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

## 4. What the twenty-first session did

`git log --oneline df22b44..HEAD`, 8 commits, this file's included.
Decision 48, items 3 and 4, and nothing else on the code.

**The loops, first.** pytest 1094, the CLI on the allocation question as
expected, then with a yes the golden set (zero diff, seventeen lines) and
the runner (13/14, 4.1 BLOCKED at PHI-2.1 for FY2021, the probe naming
decision 48), both clean at df22b44 and both on the cache.

**The measurement before the shape.** The brief expected the stop to move
to PHI-4.1 once the keys were decided. Read from the stored facts: PHI-2.1
stops at FY2021 because return on invested capital needs FY2021's
borrowings, and Alphabet's non-current debt for FY2021 and FY2022 is filed
only under `LongTermDebtAndCapitalLeaseObligations`, F7's lease-inclusive
tag; on the FY2024 report the same tag carries the lease-exclusive figure
for 2023, so the tag is not even consistent with itself. Alphabet files
`CostOfRevenue` in every year and no `GrossProfit`; `Depreciation` in every
year (FY2021's only as a comparative on the FY2023 report, its own report
having tagged the line outside us-gaap) and no amortisation expense tag at
all. Apple's cost of sales less revenue equals its filed gross profit to
the dollar in five years, and revenue less cost of sales less
`OperatingExpenses` equals operating income in five years; Alphabet's
revenue less `CostsAndExpenses` equals operating income in five years.

**The shape of decision 48, items 3 and 4**, one yes. Item 3, D36: a tag
joins a field's list on a witness, a filer filing it beside a listed tag
for the same period at the same value; a filer filing both at different
values has shown two measures and the tag stays out (F7: 13,253 against
11,870; F8: 9,500 against 11,284 and apart every year); a tag no filer
files beside a listed one stays out, with the cost-of-revenue list the one
recorded exception. Item 4: `gross_margin` becomes revenue less cost of
revenue over revenue, the block carrying `cost_of_revenue` and not
`gross_profit`, the measure unchanged for a filer that presents both;
`net_debt_to_ebitda` keeps its formula and the refusal stays, Alphabet
filing no D&A under any us-gaap tag. Rejected on the way: the wider debt
tag in the list, which errs in the safe direction and joins two measures
without a raise; splitting it by the finance-lease liability, arithmetic
on the way in for two years only; `Depreciation` in the D&A list; two D&A
fields with a sum, which Alphabet cannot fill and Apple cannot witness; a
key over operating income plus depreciation alone, a philosophy change;
keeping `gross_profit` beside the new field with no formula reading it;
two formulas under one key; a second key PHI-2.2 would have to name.

**Under the yes, in order.**
- **567ca58** the reference: D36 in Part 12's table; Part 12 B's note with
  Apple's cost of sales; Part 12 H, the identity table and five margins
  0.4178, 0.4331, 0.4413, 0.4621, 0.4691; Part 13 B's note with Alphabet's
  cost of revenue and margins 0.5694, 0.5538, 0.5663, 0.5820, 0.5965; Part
  10 A, B and E moved; Part 13 E items 3 and 4 decided.
- **03ad5ac** Part 12 C's heading, which the note above it had swallowed,
  restored; found by `test_filed_fields.py` at the next step.
- **6e9cc03** the code, one change: `filed_figures.FIELDS` carries
  `cost_of_revenue` (`CostOfRevenue`, `CostOfGoodsAndServicesSold`) where
  `gross_profit` stood; `_gross_margin` divides the difference by revenue;
  Apple's five gross profit rows in the csv keep their provenance as the
  witness and five cost of sales rows join them, CRLF preserved;
  Alphabet's csv gains five cost of revenue rows; Part 12 C's row; the
  tests. Seen failing against the unchanged source (37 failed, 22 errors),
  against the inverted formula (10 failed: Part 10 C's three margins, Part
  12 H's five, the PHI-2.2 finding, the band test) and against a one-tag
  list (3 failed). 8 tests more.
- **a593c9e** the 4.1 probe's reason line: D36 on the debt tag, the stop
  standing until Alphabet's FY2027 report, PHI-3.1 on D&A after it.
- **798d20e** PHI-2.2's sentence in `docs/PHILOSOPHY.md`, written on the
  owner's "write it, yes", and the same words in `philosophy.toml`.
- **b1328a1** the record: the node entry's claim about the next stop
  corrected; the reader entry's trigger narrowed to items 6 and 7; five
  entries with triggers (§5).
- **5151f23** benchmark.md's status note under Level 4.

**The runner, twice more.** After 6e9cc03: 13/14, the same stop, the old
reason line; after a593c9e: 13/14, the new reason line. The golden set
sees none of this and was not run again.

**Items 6 and 7, brought as a shape and not taken** (the brief's third
item, no code): §5.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- **48, items 3 and 4**, as shaped and built above. Inside them: **D36**,
  the witness rule for a field's list; the key `gross_margin` reading cost
  of revenue; the refusal on `net_debt_to_ebitda` standing. 48 is not
  closed: items 6 and 7 remain.

**Brought as a shape, not taken, on the owner's instruction that they come
as a shape only.**
- **Item 6**, the two `marketable_securities` fields no metric reads under
  Part 12 F's decision A. Recommended: delete both; Part 12 C to twelve
  rows, the figures kept in Part 12 B and the csvs as witnesses, the
  unresolved sets shrinking by one for Alphabet and two for JPMorgan;
  Part 12 F's revisit trigger brings the current field back with its
  reference row. Rejected: carried-not-read on D32's precedent, which had
  a contrast row and this has none; kept for a hypothetical.
- **Item 7**, `shares_outstanding`. Not reachable before Part 11: the node
  puts neither price nor shares nor range on the block, so PHI-4.1 stops
  first. Recommended in two halves: the count now, `shares_outstanding` a
  field of the block, instant, `CommonStockSharesOutstanding`, per year,
  the metric reading the latest year's (Apple 14,773,260,000 at
  2025-09-27, Alphabet 12,088,000,000 at 2025-12-31, F9's split on FY2021),
  reference rows in Part 12 B and Part 13 B first; the price with Part 11,
  the last close of the ticker the question named, the finding carrying
  that ticker, the count's date and that the count covers every class,
  the price gap between classes a known limit with a trigger. Rejected:
  the dei cover-page count; the weighted average; summing classes, which
  the artifact cannot; refusing multi-ticker CIKs, which refuses preferreds;
  the Yahoo shares table.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve. **Ten, eleven if 56 is numbered**; the cap is 25.
CLAUDE.md's line reads 10 and is the owner's to update.

10. A window return as a measure with a reference.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding. Absorbs 35.
22. Volatility over as-traded closes or a total-return series.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, 11 and 36.
48. Part 13 E's items 6 and 7, shaped above. Items 3 and 4 decided.
51. The four live intents outside the benchmark roster: delete or keep.
    Trigger: the full test at the end of Order 4.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields: delete, its
    own sitting.
56. **Whether Alphabet stays case 4.1's X**, surfaced this session and
    numbered by me for the record; the owner's to confirm or renumber.
    Under D36 W-1 cannot pass 4.1 before its FY2027 report, and not then,
    on PHI-3.1. The choices are in the record's entry.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12. Level 4: 4.6 PASS; 4.1 BLOCKED by decision, the
runner's reason line saying why; 4.2 to 4.5 have no check. The ledger has
four open predictions and no scored one. n/14 is a count of well-formed
answers. What the runner cannot see: that PHI-2.2 would now compute for
Alphabet, since PHI-2.1 stops first; pytest sees it through the csv rows
and Part 12 H.

---

## 7. Next steps, in order

**1. Decision 56**, the owner's: another candidate as X, X unchanged and
4.1 blocked by decision, or a PHI-7.1 change to PHI-3.1's measure. Not a
code question until taken.

**2. The valuation pipeline**, Part 11 by hand first, then case 4.2 as a
row under `research`; the price on the block comes with it, and item 7's
second half.

**3. Prediction scoring** with its Part, case 4.5; then the research agent
for 4.3 and 4.4, where the compliance gate is designed for real.

**At the end of Order 4: the full test** (§5 of the twentieth session's
handoff, unchanged), before Order 5.

### Later, with reasons

- Items 6 and 7's first half, shaped in §5, each its own reference rows
  first and its own commits.
- The formatter headers carrying an emoji, seven in `nodes.py`. One commit,
  the runner run against it. Work, not a decision.
- A philosophy topic lookup ("what does my philosophy say about debt?"):
  a discriminator row on `research`, when a case asks.
- The node does not confirm the resolved CIK's submissions document lists
  the ticker asked (KNOWN_GAPS, the tickers entry).
- Decisions 51, 52 and 54, each its own sitting.
- The registry text naming VaR, drawdown and risk parity: a prompt change,
  prediction first, two golden runs.
- 3.2's rewrite and Part 2's boundary: at the commit that makes 4.3 answerable.
- PHI-3.2's code list grows by measured filer, by the owner's hand; the
  field lists grow by witnessed tag (D36), the same way.
- The seven-day cache runs out on 22 and 23 September; the next paid run
  after that fetches, and says so first.

---

## 8. Rules learned the hard way

**Measure the brief's expectation before writing the shape.** The brief
said the stop would move to PHI-4.1 once the keys were decided; the stored
facts said the stop was F7, the debt tag, and the keys were not what 4.1
was waiting on. A shape built on the brief would have decided the wrong
question and been surprised by the runner.

**A note that replaces text up to a heading puts the heading back.** The
reference commit's note under Part 12 B consumed Part 12 C's heading; the
diff was shown and read and neither of us saw it; the test that reads the
document by that heading found it one commit later. A heading in a
replaced span is part of the span.

**A csv with CRLF endings is edited on the bytes.** `Path.read_text`
converts the endings silently and the diff shows every line as changed.
Read the diff's shape before its content: a whole-file diff on a five-row
edit is the first sign.

**A witness for a list is a same-value pair on one filing.** Equal values
under two tags for one period admit the second tag; different values show
two measures and keep it out, however much the filer's other years need
it. The exception is recorded as one, not folded into the rule.

**Say which loop cannot see a change.** The gross margin change is
invisible to the runner because the check stops in philosophy order and
PHI-2.1 comes first; a session that read 13/14 as "nothing changed" would
be wrong in both directions.

**A test over the suite's database copy owns the rows it reads.** The copy
is the real database, and the real database grows: the first second filer
stored in it made a schema test's whole-table reads fail at a documentation
commit, and the same test had been failing alone for two sessions behind a
fetch test that emptied the table before it. Delete inside a rolled-back
transaction, read back by a marker you wrote.

**A formatter states what the data says and never what the system is.** "The
valuation pipeline does not exist yet" was true of the system and false of
the one rendering where a range had been typed, and would have stayed in
the answer after Part 11. The stop on PHI-4.1 carries the fact from the
data.

**The import-time checks decide the commit order.** A roster entry without
a node and an intent without a synthesizer branch both fail at import, and
the registry description is the prompt: so the node and the formatter land
unbound, tested as functions, and the registries land last with the golden
line and the prediction.

**Two paid loops on one SQLite file run one after the other.** Golden and
runner both write prices and now filed rows; run together they would race
on the lock and report nothing about the code.

**A typed date is checked against the row it came from before the test
runs**: a filed date one day off was caught by the csv, not by memory.

**An instruction with words missing is read against the record**; **a claim
about the world goes into the record only after it is checked, or marked as
unchecked** (the ticker file's URL and shape were marked from memory until
the first fetch confirmed them); **a schema test's database half is red
between the commit and the owner's migration, and that is the pattern**; **a
cache row that means "as of this pull" moves its date on every pull**; **a
number in config goes into the document in the same commit as the code that
requires it**; **grep the writer the reader reads**; **a formatter test with a
hand-built input holds the formatter to a shape, not the node to the tool**;
**delete the caller before the callee**; **a rule taken from part of a source
is measured over all of it**; **a wrong version checked in place can run the
previous one's bytecode** — still true, from earlier sessions.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 4.6

python src/agents/cli.py --portfolio 3        # :q to quit

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

# nine assets; daily_prices and macro_data move, do not pin them;
# the filings tables as of this session's end:
sqlite3 data/portfolio.db "select count(*) from ticker_ciks; select cik, sic, pulled_at from filers; select cik, count(*) from filed_facts group by cik;"

# a check run against an edited, deliberately wrong module:
find src -name __pycache__ -type d -prune -exec rm -rf {} +
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/<file>.py

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only keys
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3.5s, no model calls | Do the components still work; does every reference Part reproduce; does the node fetch in order and publish the block; does each formatter rendering pass the runner's check |
| CLI | ~3s, one call | What it is actually doing: the plan, the parameters, the reasoning line, the answer text |
| Golden set | ~80s, cents, **writes filed rows** | Did routing change anywhere (seventeen lines, one pinned failure). Blind to parameters and answer text |
| Benchmark runner | ~2min, cents, **writes filed rows** | How many cases pass, n/14. Blind to the four intents outside the roster and to 4.2 to 4.5 |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once.
