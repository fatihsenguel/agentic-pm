# AGENTIC_FINANCE — Session Handoff

**Session date:** 17 September 2026 (twenty-second session). Regenerated at its end.
**Branch:** `range`, cut from `baseline-v1` at 7edc7f9, the trunk's tip at session start. **`baseline-v1` is the trunk**: each session branch is merged into it with `--ff-only` when the loops are green; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count 7edc7f9..HEAD` — 13 with this file. **Not merged and not pushed**: the owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1156 passed, 6 xfailed**, up from 1102 by 54: 36 for the valuation module against Part 11, 13 for the loader's three new parameters, three for the share count as a field, one for the yield reading the year's count, one for the watchlist's growth pair. **Golden set run twice**, at session start: the first run's first line, the macro question, came back at intent None with one error and the text of the error is gone (§4, §8); the second run, zero diff, seventeen lines, the pinned rebalance failure included. Nothing since touched what it sees. **Runner 13/14 once**, at session start: 4.6 PASS, 4.1 BLOCKED at PHI-2.1 for FY2021, the reason line naming D36. Not run again: no commit reached the graph (§4). **No live fetch**: every request hit the seven-day cache. The CLI ran once, at session start, on the allocation question, and once more on the macro question to see the golden failure not reproduce. **Part 11 is computed and its module exists; nothing in the graph calls it. Decision 48's item 7 is half taken; 56 stays pending; 57, a price for a candidate not held, is surfaced and numbered for the record.**

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session's shape put three assumptions on a statement
clause, and the loader refuses a number on a statement; the correction is
dated in Part 11 (§4). Misses of my own, caught before or after landing:
three regexes in the valuation tests with the year and the input in the
wrong order and one typed debt too small to cross the reference's
threshold, all four fixed in the tests before the commit; a test pinning
Part 12 C's row count at 14 that I did not move with the fifteenth row,
caught on the first green run; a targeted pytest run that ran nothing
because zsh does not split an unquoted variable, caught by reading "no
tests ran" and rerun with explicit paths; the brief said the branch
existed and it did not, created on the owner's yes.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the bridge, the SIC code, the philosophy check node, the metric keys, and now **the valuation range by hand (Part 11) with its pure module, not yet in the graph**. Left in Order 4: the range published for case 4.2, prediction scoring (4.5), the research agent (4.3, 4.4), decisions 56 and 57. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. Level 4: 4.6 passes, 4.1 blocked by decision (three dated status notes under Level 4, this session's saying Part 11 is computed and nothing publishes a range). n/14. The "none computed yet" sentence carries a dated correction. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Fourteen cases. 4.1's reason line names D36 until Alphabet's FY2027 report, PHI-3.1 after it. No `check_4_2` yet; when written it will see structure and not the arithmetic (KNOWN_GAPS). |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 109 lines match `Trigger:`, 78 reading something other than "none", counted by grep. New this session: six entries (§4); one resolved. |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, Parts 1 to 13. **New this session: Part 11**, the valuation range, D37 to D40, Alphabet and Apple FY2025 step by step, seven falsifiers; notes in Parts 10 A and B, 12 B and C, 13 B, 13 C and 13 E for the share count. Never update it to match code output. |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, saved in Excel at c75b73b. Untouched this session; Part 11 has no sheet, like Part 12 G and H. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. **PHI-4.1 gained the range's method and my three assumptions this session** (8c51221), written on the owner's word. |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027. **W-1 states its growth pair this session** (e131b32), on the owner's word; W-2 states none. Nothing reads it. Decision 56 asks whether W-1 stays X. |
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
and a judgement half whose first tool, the philosophy check, is in the
graph and whose second, the valuation range, exists as a module with its
reference and no caller. The router is scaffolding until the tool layer is
complete. **No deadline. Correctness over speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** This session's form: the
  range record carries two floats, the year with its dates, the source and
  the assumptions, and no filed figure (D40); free cash flow and net debt
  stay in the module and the database.
- **Policy lives in config, not code.** The method is a formula in Part 11
  D37 and PHI-4.1's text names it; the investor's three assumptions are
  PHI-4.1's parameters and the candidate's growth pair is the watchlist
  entry's (D38). A statement carries no number, which is why D38 was
  corrected the day it was written.
- **Two policies, two questions.** The IPS says what may be held; the
  philosophy says what is worth wanting. Two intents, `compliance` and
  `research`; a philosophy question on a held ticker does not run the IPS
  check, and the golden line pins it.
- **Raise, do not repair.** This session's form: reversed growth rates
  raise rather than sort, equal rates raise as a point, a return at or
  below the terminal growth raises, a non-positive free cash flow or low
  end raises, a missing count raises, an unstated assumption raises, a
  block without a source raises. Nothing is defaulted.
- **A range, never a point, never a price.** The low end is the formula at
  the low growth rate and the high end at the high one; there is no
  midpoint and no spread (PHI-4.3, D37).
- **One arithmetic path.** The range takes net debt from
  `quant/fundamentals.net_debt`, the function PHI-3.1 reads (D39).
- **An excluded company's figures are never asked for.** Unchanged.
- **Typed facts are not a source.** The valuation tests type Part 11 B's
  filed figures; the module reads a block, not a file.
- **References before code.** Part 11 before the module; the share count's
  rows before the field; the Part 10 note before the metric moved; every
  test seen failing against the unchanged source and against a wrong
  version with bytecode off.
- **No price forecasts as numbers.** Rejected this session on those
  grounds: a multiple of free cash flow, which is what the market pays.
- **A value nothing consumes is not stored.** The record carries no method
  name and no intermediate.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
  This session's shape stated the formula over named inputs, the five
  assumptions with values and homes, what the block lacked item by item,
  and how the ends come from the assumptions; it was taken with one yes,
  and one of its homes was corrected against the loader before a line of
  config was written.
- **A shape's home for a number is checked against the loader's rule
  before it is written down.** D38 said PHI-4.3; the loader says a
  statement carries no number. The correction is dated in the reference
  and the commit.
- **The reference first, then the field, then the metric, then the
  module, then the config**, each its own commit, each test first.
- **The owner's documents are written on the owner's explicit word**, not
  on a yes to the shape that mentions them: PHI-4.1's sentence and W-1's
  line were each asked for separately.
- **A live fetch is asked for before the machine is touched.** None this
  session.
- **A csv with mixed endings is edited line by line on the bytes.**
  Apple's csv has CRLF rows and seven LF rows from 13 September; the new
  rows follow their neighbours and the diff is ten added lines.
- **Grep the caller, not the registration.** Nothing calls
  `quant/valuation.py`; the handoff says so rather than implying a
  pipeline.
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
rate. No formatter sentence that states the system's status. **No model
proposing a valuation assumption before case 4.3 defines how a proposal is
marked; no midpoint, spread or sorted range; no multiple of free cash flow
as a method.**

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

**1156 passed, 6 xfailed, 26 warnings, about 3.5 seconds.** Run at session
start (1102) and after every commit. Red by design six times: the new tests
against the unchanged source before each code commit, and against each
deliberately wrong version (§4).

**Golden set: zero diff, seventeen lines, one pinned failure** ("Should I
rebalance my portfolio?", errors 1), on the second run at session start;
the first run's first line was a transient router error whose text the
loop discards (KNOWN_GAPS, "The golden loop discards the text of a
transient error"). Not run since: no registry, prompt, router or intent
changed. **Runner 13/14** once, at session start: 4.6 PASS, 4.1 BLOCKED,
the reason line naming D36. Not run since: nothing this session reaches
the graph. `philosophy.toml`, which the node loads live, gained PHI-4.1's
three parameters; `tests/test_philosophy.py` loads the same file, so a
load failure would be red in pytest.

**The CLI, twice.** The allocation question at session start, as the
runner's 1.1 expects; the macro question once, routed `macro_analysis`,
MacroAgent, no error.

**Level 4: 1 of 6 cases passes (4.6); 4.1 blocked by decision; four have no
check.** Read n/14 as a count of well-formed answers and never as the
system being good at research (benchmark.md).

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. `range` is this session's branch,
from 7edc7f9. `keys`, `node`, `filer`, `bridge`, `consolidate`,
`selection`, `compliance` and `vocabulary` are merged and older.
`wip/phase7-snapshot` holds rejected Compliance/IPS code. `wip/rag-early`
and tag `rag-early-parked` hold the RAG code. `quant-inventory-parked` at
8d87455 holds the tree before the seventeenth session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`e289a03682f2`**, 25 migrations, linear, all applied. No migration and no
reseed this session. **The paid loops write to this file**: the golden line
and the runner's 4.1 and 4.6 run the node live, and its fetches store rows
here under the seven-day interval; this session every fetch was inside the
interval and no filed row moved. **The interval runs out on 22 and 23
September**: Apple's facts were pulled 2026-09-15 22:17 UTC, its filer row
2026-09-16 00:03, the ticker file and JPMorgan's filer row 01:33,
Alphabet's filer row and facts 01:38. A paid run after those instants
fetches again, and a session running one says so first. Tables that matter:

- `portfolios`, `transactions`, `assets` (9 rows).
- `daily_prices`: 6,975 rows and not a fixed count. `macro_data`: 203 and
  growing.
- **`ticker_ciks`: 10,422 rows, the SEC ticker file as of 2026-09-16 01:33
  UTC**, 8,022 distinct CIKs; Alphabet's carries GOOG, GOOGL, GOOGM and
  GOOGN, JPMorgan's nine tickers, mostly preferred series (decision 57's
  question of which ticker's close, §5).
- **`filers`: three rows**, Apple (3571), JPMorgan (6021), Alphabet (7370).
- **`filed_facts`: 28,787 rows, Apple's 15,132 and Alphabet's 13,655**,
  us-gaap only. `filed_fetch_metadata`: two rows. JPMorgan's facts were
  never fetched: the exclusion decides first. **Both filers' year-end
  share counts are in these rows** and Part 11 B and Part 12 B's and 13
  B's notes were read from them.
- `financial_statements`: 65 rows, neither the reader's store nor a source
  (decision 52). `shares_history`: 947 rows, no source column, never a
  source, and now not needed for the count (KNOWN_GAPS, resolved).
  `fx_rates`, `fx_fetch_metadata`: empty.

**There is no holdings table.** Portfolio 3, "Benchmark Portfolio", is the
only portfolio: nine ledger rows, cost basis 284,500 plus 15,500 cash, USD,
policy `ips.toml`.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py`, `test_screening.py` | **the screening node**, by `nodes.PHILOSOPHY_PATH` (decision 30). PHI-4.1's three parameters are loaded and read by nothing yet. |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py` | nothing. W-1's growth pair is held to its line and read by nothing yet. |

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

The block the reader returns now has **fifteen fields**, `shares_outstanding`
the fifteenth, `CommonStockSharesOutstanding` at the year end in whole
shares, its unit `shares` and not a currency. The node puts neither price
nor range on the block, so PHI-4.1 would stop on the range's absence if the
check ever reached it; on Alphabet it does not, PHI-2.1 stopping first.

Publishes `shared_data["screening"]`: philosophy, statements, subject
(ticker, CIK, EDGAR's name), as_of (the UTC date of the run), sic,
sic_description, sic_as_of, years (dates only), findings, stopped, source,
facts_as_of. The formatter has three renderings: excluded, stopped,
screened. The compliance gate is idle by construction; the gate is
designed at 4.3.

### The valuation range, as it stands

`quant/valuation.py`, pure, held to Part 11 by `tests/test_valuation.py`.
`valuation_range(block, assumptions, as_of)` reads the latest year filed
by the as-of date, that year's operating cash flow less capex, net debt
through the metrics' function, and the year's count; the five assumptions
come in as a mapping of name to value and source; the record is D40's.
**No caller.** What the node needs before it can call it is one record
entry (KNOWN_GAPS, "What the node needs before it can publish a range"):
the block's `source`, a watchlist loader for the growth pair, the record
published as a summary, and a price, decision 57.

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
  Each request asked for before it was made.
- `config.toml` carries five fetch intervals. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; `config.toml` is read relative to the project
  root, so scripts run from the root. The whole suite on a scratch copy:
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest`.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router.
- **`quant/fundamentals.py` imports `filed_figures.FIELDS`**, the one place
  the block's shape is defined; **`quant/valuation.py` imports
  `fundamentals.net_debt`, `_figure`, `_date` and `years_filed_by`**, so
  the range and the metrics read a year the same way.
- **`filed_figures.NON_MONEY_UNITS`** is `pure` and `shares`; every other
  unit is a currency and a block has one.
- **The four-digit SIC rule is held twice**: `screening._SIC_CODE` and
  `providers/edgar.SIC_CODE`, the same regex.
- **The node reaches the provider through `nodes.edgar_provider()`**, a
  function so a test stands one in.
- **`tests/test_research_formatter.py` imports `run_cases`** from
  `tests/benchmark` by a path insert. The runner still is not part of pytest.
- **zsh does not split an unquoted variable into words.** A pytest command
  built as `pytest $FILES` runs one path that does not exist and prints
  "no tests ran"; write the paths out or quote-split them.
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

## 4. What the twenty-second session did

`git log --oneline 7edc7f9..HEAD`, thirteen commits with this file. Part
11 and decision 48's item 7, first half, and nothing on the graph.

**The loops, first.** pytest 1102, the CLI on the allocation question as
expected, then with a yes the golden set and the runner, one after the
other on the cache. The golden set's first run put its first line at
intent None with one error; one CLI call on the same question routed it as
expected; a second golden run with stderr kept was zero diff and its
stderr was the pinned rebalance failure alone. The runner 13/14, 4.1
BLOCKED at PHI-2.1 for FY2021.

**Two placeholders in the brief were unfilled**: decision 56's outcome and
the pending count. Neither was taken by me: the session worked on Alphabet
as X because that is the state today and changes no file, and 56 stays
pending.

**The shape of Part 11**, one yes: a discounted cash flow over the latest
filed year's free cash flow, run once at each of two stated growth rates;
five assumptions, three the investor's and two the business's; every filed
input the latest year's, net debt as PHI-3.1 computes it, the year's own
count; a record with no filed figure; six raises. Rejected: a multiple of
free cash flow, a one-stage perpetuity, a pair of discount rates, the
model proposing a rate, free cash flow computed on the way into the block,
a midpoint in the formatter, filed figures on the record for traceability.

**Under the yes, in order.**
- **2823a7e** Part 11 by hand: D37 to D40; the stand-in assumptions;
  Alphabet's and Apple's FY2025 inputs at their vintages; four ten-row
  tables; Alphabet 129.39 to 205.62, Apple 140.10 to 224.18 per share;
  seven falsifiers, the one-year identity among them; what the Part does
  not cover, the price first.
- **3ce2425** item 7's reference: the year-end count by filer, Apple's five
  and Alphabet's five with their vintages, Alphabet's FY2021 the
  split-adjusted count of the FY2022 10-K (F9); the unit rule; JPMorgan's
  fixture without it; Part 13 E item 7 half decided.
- **730fd2d** the field: `shares_outstanding` in `FIELDS`; the one-currency
  rule reading money units only; five csv rows each, Apple's CRLF beside
  seven LF rows left as they were; Part 12 C's row and note; the tests.
  Seen failing against the unchanged source (8) and against the field
  without the unit rule (16, every one raising on `USD` and `shares`).
- **9eaaabe** Part 10's note: the count a figure of the year.
- **1682d3a** the yield reading the year's count. Seen failing against the
  unchanged source (9 failed, 10 errors, the screen stopping on PHI-4.2)
  and against a version falling back to a block-level count (the new test
  alone).
- **cf9e8da** `quant/valuation.py` and its 36 tests. Seen failing without
  the module, with the terminal value discounted a year too many (the ten
  value rows) and with reversed rates sorted (the two rate tests).
- **4b93594** D38 corrected: the three investor assumptions on PHI-4.1, the
  clause that reads the range, not on PHI-4.3, a statement.
- **9e64312** the loader: `margin_of_safety` takes `required_return`,
  `terminal_growth` and `horizon_years`, all three or none. Seen failing
  against the unchanged source (12) and against a version accepting one
  alone (3).
- **8c51221** PHI-4.1's sentence in `docs/PHILOSOPHY.md` and the values in
  `philosophy.toml`, on the owner's word.
- **e131b32** W-1's growth pair in `docs/WATCHLIST.md` and `watchlist.toml`,
  on the owner's word; W-2 states none.
- **04ad56a** the record: six entries, one resolved, the reader entry's
  trigger narrowed.
- **da019f7** benchmark.md's status note and the dated correction.

**Not done, on purpose.** Nothing reaches the graph: no node calls the
module, no watchlist loader exists, no range is published, no `check_4_2`.
Part 13 E item 6 was not started; the record's pending list carries it.
The runner was not run after the config commits because nothing they
changed is read by the node's path today.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- **Part 11's D37 to D40**, as shaped above, with **D38 corrected** the same
  day: the investor's three on PHI-4.1.
- **48, item 7, first half**: the filer's own year-end count as a field,
  the yield reading the year's. The second half, the price and a filer
  with more than one class, is open and is now also decision 57's.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve. **Ten numbered by the owner; twelve with 56 and 57,
which I numbered for the record**; the cap is 25. CLAUDE.md's line reads
10 on 16 September and is the owner's to update.

10. A window return as a measure with a reference.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding. Absorbs 35.
22. Volatility over as-traded closes or a total-return series.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, 11 and 36.
48. Part 13 E's item 6, shaped in the twenty-first session's handoff and
    unchanged, and item 7's second half. Items 3, 4 and 7's first half
    decided.
51. The four live intents outside the benchmark roster: delete or keep.
    Trigger: the full test at the end of Order 4.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields: delete, its
    own sitting.
56. **Whether Alphabet stays case 4.1's X.** Under D36 W-1 cannot pass 4.1
    before its FY2027 report, and not then, on PHI-3.1. The choices are in
    the record's entry. Part 11's rows are on Alphabet because it is the
    state today; a change of X changes `docs/WATCHLIST.md`, the runner's
    `WATCHLIST_TICKER`, and needs a live fetch of the new candidate before
    any reference row.
57. **A price for a candidate not held**, surfaced this session and
    numbered by me; the owner's to confirm or renumber. The last close of
    the ticker the question named, stored with its source and date, a
    Part 9 row first; which ticker for a CIK with several is item 7's
    second half. The record's entry has the choices.

- **The full test at the end of Order 4** (owner's, unchanged): when Order
  4's last commit lands, the project stops for a full test across both
  halves before Order 5. Asked about this session; the record places it
  after Order 4, and that is where it stays.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12. Level 4: 4.6 PASS; 4.1 BLOCKED by decision, the
runner's reason line saying why; 4.2 has its reference and its module and
no check and no node; 4.3 to 4.5 have no check. The ledger has four open
predictions and no scored one. n/14 is a count of well-formed answers.
What the runner cannot see, now or once 4.2's check exists: whether the
range's arithmetic is right; pytest holds that through Part 11.

---

## 7. Next steps, in order

**1. Decisions 56 and 57**, the owner's. 57 first if 4.2 is next: without
a price the answer cannot state one and PHI-4.1 cannot find.

**2. Case 4.2 into the graph**, the check first: `check_4_2` in the runner,
seen BLOCKED; a watchlist loader for the growth pair, test first; the node
assembling the five assumptions with their sources, putting `source` on
the block, calling `valuation_range`, publishing the record and the stop;
the formatter's rendering, which states the assumptions with their sources
and the arithmetic as the pipeline's, never a midpoint; the routing row
for "What is X worth?", prediction first, two golden runs. The runner after
the commit that publishes.

**3. Prediction scoring** with its Part, case 4.5; then the research agent
for 4.3 and 4.4, where the compliance gate is designed for real.

**At the end of Order 4: the full test** (§5), before Order 5.

### Later, with reasons

- Item 6, shaped in the twenty-first session's handoff: delete the two
  `marketable_securities` fields no metric reads; reference note first.
- The formatter headers carrying an emoji, seven in `nodes.py`. One commit,
  the runner run against it. Work, not a decision.
- The golden loop's `2>/dev/null`: keeping stderr to a file beside the
  output would have named this session's transient error. CLAUDE.md's
  line and the handoff's; the owner's to change.
- A philosophy topic lookup ("what does my philosophy say about debt?"):
  a discriminator row on `research`, when a case asks.
- The node does not confirm the resolved CIK's submissions document lists
  the ticker asked (KNOWN_GAPS, the tickers entry).
- Decisions 51, 52 and 54, each its own sitting.
- The registry text naming VaR, drawdown and risk parity: a prompt change,
  prediction first, two golden runs.
- 3.2's rewrite and Part 2's boundary: at the commit that makes 4.3 answerable.
- PHI-3.2's code list grows by measured filer, by the owner's hand; the
  field lists grow by witnessed tag (D36), the same way; a new field's
  first tag is the taxonomy's element for the line, with its falsifier.
- The seven-day cache runs out on 22 and 23 September; the next paid run
  after that fetches, and says so first.

---

## 8. Rules learned the hard way

**A shape's home for a number is measured against the loader before the
shape is brought.** D38 put three assumptions on PHI-4.3, a statement, and
the loader refuses a number on a statement for a reason that is right.
Found by reading the loader before writing config, corrected in the
reference the same day, its own commit. Read the validator for the type
before naming a clause as a home.

**The golden loop discards the reason for a transient failure.** The
first run's first line failed at the router and the command sends stderr
to /dev/null, so a diff with no cause is all that is left. A second run
held, and the record says what it cannot say.

**A table-reading test pins a count.** `test_the_reference_table_is_read`
asserts Part 12 C's row count, and a fifteenth row is a failed test until
the count moves; the row-count assertion is the one to look for when a
field is added.

**A pinned csv can carry two line endings.** Apple's csv is CRLF except
the seven rows added on 13 September, which are LF, and an edit that
assumes one convention asserts before it writes. Edit line by line,
keeping each line's own ending.

**zsh does not word-split an unquoted variable.** A targeted test run
built with a variable ran nothing and printed "no tests ran"; the wrong
version's check that run was meant to be did not happen until the paths
were written out. Read the summary line, not the exit code.

**Test regexes say the order the code says it in.** Four valuation tests
failed on the real code for the tests' own reasons: three regexes with
the input before the year where the code names the year first, and one
typed debt below the reference's threshold. The reference was right and
the tests were fixed to it, not the code to the tests.

**The owner's documents are written on a separate word.** A yes to the
shape that mentions a sentence for PHILOSOPHY.md is not a yes to writing
it; PHI-4.1's sentence and W-1's line were each asked for and each
answered.

**Measure the brief's expectation before writing the shape**; **a note
that replaces text up to a heading puts the heading back**; **a csv with
CRLF endings is edited on the bytes**; **a witness for a list is a
same-value pair on one filing**; **say which loop cannot see a change**;
**a test over the suite's database copy owns the rows it reads**; **a
formatter states what the data says and never what the system is**; **the
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
git switch baseline-v1 && git merge --ff-only range
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3.5s, no model calls | Do the components still work; does every reference Part reproduce, Part 11 included; does the node fetch in order and publish the block; does each formatter rendering pass the runner's check |
| CLI | ~3s, one call | What it is actually doing: the plan, the parameters, the reasoning line, the answer text |
| Golden set | ~80s, cents, **writes filed rows** | Did routing change anywhere (seventeen lines, one pinned failure). Blind to parameters and answer text, and its stderr is discarded |
| Benchmark runner | ~2min, cents, **writes filed rows** | How many cases pass, n/14. Blind to the four intents outside the roster, to 4.2 to 4.5, and to whether a range's arithmetic is right |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once.
