# AGENTIC_FINANCE — Session Handoff

**Session date:** 17 to 18 September 2026 (twenty-third session). Regenerated at its end.
**Branch:** `publish`, cut from `baseline-v1` at cb3de91, the trunk's tip at session start. **`baseline-v1` is the trunk**: each session branch is merged into it with `--ff-only` when the loops are green; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count cb3de91..HEAD` — 14: ten for the case, the record, benchmark.md, this file, and the correction of this count, which was first written as 14 when it was 13 and corrected 18 September in a commit of its own. **Not merged and not pushed**: the owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1204 passed, 6 xfailed**, up from 1156 by 48: 26 for the watchlist loader, 7 for the node's range and price, 3 for the investor's assumptions read off PHI-4.1, 9 for the rendering, 3 for the candidate's stored closes against Part 9 C. **Golden set: eighteen lines.** Zero diff on seventeen at session start; the eighteenth, "What is GOOGL worth?", recorded at out_of_scope on its baseline run and then at research on two identical runs after the registry's correction, as predicted; the pinned rebalance failure throughout. **Runner 14/15 once**, after the rendering landed: 4.2 PASS on the live answer, 4.6 PASS, 4.1 BLOCKED at PHI-2.1 for FY2021, the reason line naming D36. 13/14 at session start. **The CLI three times**: the allocation question at session start; "What is GOOGL worth?" twice after the runner, to read the first live record. **No EDGAR fetch**: every filings request hit the seven-day cache. **One live price fetch**: the node stored GOOGL's closes for 10 to 17 September through the price provider on the golden set's first run after the correction; cached since. Three requests to the exchange's historical quotes by hand for Part 9 C, and one call to the provider's library from the shell, storing nothing. **Case 4.2 is in the graph and passes on structure. Decisions 56 and 57 are taken. Order 4 is not done: prediction scoring (4.5) and the research agent (4.3, 4.4) remain, then the full test before anything of Order 5.**

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Misses of my own this session, caught before or after landing:
the brief named a branch that did not exist, created on the owner's yes,
the second session running; the brief's placeholders for decisions 56 and
57 were unfilled again, and the owner delegated 57 with the design
principles as the rule; the rendering printed the block's source and not
the record's own until a fixture whose two sources differed failed the
runner's check; the price step first caught every exception as a stop,
narrowed to the designed error before the diff was shown; the reference row
for the candidate's close was written for the 16th and the first live run,
after the 17th's close, stated the 17th, which no exchange row covers and
which the exchange's table did not carry when asked the same evening; the
previous handoff counted the pending list as ten where its own numbers add
to eleven (§5).

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the bridge, the SIC code, the philosophy check node, the metric keys, the valuation range by hand (Part 11) and, this session, **the range published for case 4.2 with the candidate's price**. Left in Order 4: prediction scoring (4.5), the research agent (4.3, 4.4), then the full test. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. Level 4: 4.2 and 4.6 pass, 4.1 blocked by decision (four dated status notes under Level 4). n/15 since 18 September, the "n/14" sentence carrying its dated note. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Fifteen cases. `check_4_2` asserts structure and says in its docstring that it cannot see the arithmetic; `blocked_on_range` reads BLOCKED until the block carries a record or a stop. 4.1's reason line names D36 until Alphabet's FY2027 report. The `blocked_on_screen` reason's last clause is stale (KNOWN_GAPS). |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 114 lines match `Trigger:`, 78 reading something other than "none", counted by grep. New this session: five entries; four resolved (§4). |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, Parts 1 to 13. **New this session: Part 9 C**, the candidate's closes against the exchange, GOOGL 10 to 16 September, five of five. Never update it to match code output. |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, saved in Excel at c75b73b. Untouched this session; Part 9 C and Part 11 have no sheet. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. Unchanged this session; PHI-4.1's three parameters are now read by the node. |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027. Unchanged this session; **`portfolio_tool/watchlist.py` now reads the candidates and their growth pairs**, the prediction rows still read by nothing. Alphabet stays X (decision 56). |
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
and a judgement half whose first two tools, the philosophy check and the
valuation range, are in the graph with their references, and whose
remaining tools, prediction scoring and the research agent, are not. The
router is scaffolding until the tool layer is complete. **No deadline.
Correctness over speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** This session's form: the
  range record on `shared_data` carries two floats, the year with its
  dates, the source and the five assumptions, and no filed figure (D40);
  the price record carries the close, its date, its source and the ticker.
  Free cash flow, net debt and the count stay in the module and the
  database; the node test asserts no Decimal reaches the record.
- **Policy lives in config, not code.** The investor's three assumptions
  are read off PHI-4.1's parameters and the candidate's pair off its
  watchlist entry, each carried with the id that states it. The node
  originates no number. `LAST_CLOSE_WINDOW_DAYS` is a window nobody would
  set differently and is not config.
- **Two policies, two questions.** Unchanged. A valuation question is
  research, not compliance and not out_of_scope; the registry says so
  since a23a680 and the golden line pins it.
- **Raise, do not repair.** This session's form: a candidate stating no
  growth pair stops with both ends named; a ticker neither held nor on
  the watchlist gets no assets row and no price, since there is no
  currency to store a close under; a price provider that fails is a stop
  with its message, not an error and not a default; the assets row the
  node creates carries no asset class and no instrument type, and the IPS
  check raises on the blank when 4.3 asks it to size. The DataAgent's
  price route was rejected because it defaults both.
- **A range, never a point, never a price.** The rendering prints the two
  ends, and a version that printed their middle fails three tests. The
  runner's check refuses the midpoint at the printed precision and any
  phrase of the form "will reach".
- **One arithmetic path.** The range takes net debt from
  `quant/fundamentals.net_debt`, the price from the provider the holdings'
  closes come from, into the table the holdings' closes are in.
- **A designed stop is the designed error.** The price step catches
  `DataCalculationError` and nothing wider; a defect in the path is the
  node's error, not a stop with a plausible reason.
- **References before code.** Part 9 C before the node stored a close;
  the node's test pins the ends on the fixture's stored rows to Part 11 C,
  the seam the typed blocks cannot see; every test seen failing against
  the unchanged source and against a wrong version with bytecode off.
- **The registry is the prompt.** A sentence describing a capability that
  now exists is allowed where a rule tuned to a case is not, and it is
  still a hypothesis: prediction in the commit, two runs, stop at the
  second miss.
- **A value nothing consumes is not stored.** The record carries no
  currency; the rendering prints none rather than invent one, and the
  entry says what the record could carry when a case asks.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
  This session's shape covered the check, the loader, the node, the
  rendering, the routing row with its prediction, the order of commits
  and the rejected alternatives, and was taken with one yes; decision 57
  was decided by me on the owner's delegation, with the design principles
  as the rule, and stated in plain words before any code.
- **The check first, seen BLOCKED**; the reference row before the code
  that stores the figure; the loader before the node that imports it; the
  node before the rendering that reads its record; the routing row last,
  recorded at its baseline before the change and at its new state after
  two runs, each state its own commit.
- **A live fetch is asked for before the machine is touched.** Two asked
  and given this session: the exchange's quotes and the provider's library
  for Part 9 C; the exchange again for the 17th.
- **The first live record is read against the reference before it is
  believed.** Part 11 C's ends to the cent on the stored rows; Part 9 C's
  closes on every covered date; the 17th unchecked and logged.
- **A new case is sighted with `--case` alone before its golden line is
  written**: the runner's 4.2 showed the routing before a line existed.
- **Grep the caller, not the registration.** `quant/valuation.py` has one
  caller now, the screening node; `watchlist.growth_pair` one, the same.
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
as a method; no currency the record does not carry; no default asset class
on a row the node creates.**

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

**1204 passed, 6 xfailed, 35 warnings, about 4 seconds.** Run at session
start (1156) and after every commit. Red by design five times: the new
tests against the unchanged source before each code commit, and against
each deliberately wrong version (§4).

**Golden set: eighteen lines, one pinned failure** ("Should I rebalance my
portfolio?", errors 1). Four runs this session: zero diff on seventeen at
session start; the eighteenth line's baseline at out_of_scope; two runs
after the registry's correction, identical, the line at research. The
command keeps stderr to a file now, and each run's stderr was the pinned
rebalance failure alone. **Runner 14/15** once, after the rendering
landed: 4.2 PASS, 4.6 PASS, 4.1 BLOCKED, the reason line naming D36.

**The CLI, three times.** The allocation question at session start, as the
runner's 1.1 expects; "What is GOOGL worth?" twice after the runner, the
answer in §4.

**Level 4: 2 of 6 cases pass (4.2, 4.6); 4.1 blocked by decision; three
have no check.** Read n/15 as a count of well-formed answers and never as
the system being good at research (benchmark.md), and never as the range
being right (KNOWN_GAPS, "The runner's 4.2 check cannot see the
arithmetic").

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. `publish` is this session's branch,
from cb3de91. `range`, `keys`, `node`, `filer`, `bridge`, `consolidate`,
`selection`, `compliance` and `vocabulary` are merged and older.
`wip/phase7-snapshot` holds rejected Compliance/IPS code. `wip/rag-early`
and tag `rag-early-parked` hold the RAG code. `quant-inventory-parked` at
8d87455 holds the tree before the seventeenth session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`e289a03682f2`**, 25 migrations, linear, all applied. No migration and no
reseed this session. **The paid loops write to this file**: the golden
lines on JPM and GOOGL and the runner's 4.1, 4.2 and 4.6 run the node live;
its filings fetches store rows here under the seven-day interval and its
price fetch under the one-day one. **The filings interval runs out on 22
and 23 September**: Apple's facts were pulled 2026-09-15 22:17 UTC, its
filer row 2026-09-16 00:03, the ticker file and JPMorgan's filer row 01:33,
Alphabet's filer row and facts 01:38, unchanged this session. A paid run
after those instants fetches again, and a session running one says so
first. Tables that matter:

- `portfolios`, `transactions`; **`assets`: 10 rows**, the nine holdings and
  **GOOGL, id 15, created by the node on 17 September**: name "Alphabet
  Inc." from EDGAR, currency USD, asset class, sector and instrument type
  NULL by design (decision 57). A reseed does not touch it: the seed
  clears the ledger and finds assets by ticker.
- `daily_prices`: 6,999 rows and not a fixed count; **GOOGL's six rows, 10
  to 17 September 2026, source yfinance**, the five Part 9 C covers equal
  to the exchange's print, the 17th's 347.33 unchecked. `macro_data`: 206
  and growing.
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

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py`, `test_screening.py` | the screening node, by `nodes.PHILOSOPHY_PATH` (decision 30); **PHI-4.1's three parameters by `screening.range_assumptions`** |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py`, **`test_watchlist_loader.py`** | **the screening node, by `nodes.WATCHLIST_PATH`, through `portfolio_tool/watchlist.py`**: the candidates and their growth pairs. The prediction rows are read by nothing (case 4.5). |

### The philosophy check, as it stands

`screening_agent_node`, intent `research`, plan `[ScreeningAgent]` alone.
One ticker from extraction. The calls in order, the filings ones under
`filings_fetch_interval_days`, the price one under `price_fetch_interval_days`:

| Step | Call | Store | Raises or stops |
|---|---|---|---|
| ticker to CIK | `filings.cik_for` over `EdgarProvider.tickers` | `ticker_ciks` | a ticker the file lacks: error |
| name and code | `filings.update_filer` over `EdgarProvider.filer` | `filers` | |
| the exclusion | `screening.exclude` on ticker and code | | listed code: one excluded finding, done, nothing below runs; no code: stop naming PHI-3.2 |
| the figures | `filings.update_filed_facts`, `filed_years_for`; `source` put on the block | `filed_facts`, `filed_fetch_metadata` | |
| **the price** | `nodes._last_close`: the assets row found or created, `DataManager.update_prices_for_asset` over `nodes.price_provider()`, the latest stored row | `assets`, `daily_prices`, `asset_fetch_metadata` | neither held nor listed, a failed fetch, no row: `price_stopped` with the reason |
| **the range** | `screening.range_assumptions` and `watchlist.growth_pair`, then `quant/valuation.valuation_range` | | no pair, not listed, a philosophy stating none, any of D40's six: `valuation_stopped` with the reason |
| the screen | `screening.screen` | | a missing figure: stop naming the clause (PHI-1.2, D25); no price or no range: stop at PHI-4.1 |

Publishes `shared_data["screening"]`: philosophy, statements, subject
(ticker, CIK, EDGAR's name), as_of (the UTC date of the run), sic,
sic_description, sic_as_of, years (dates only), findings, stopped, source,
facts_as_of, **price (ticker, value, as_of, source), price_stopped,
valuation (D40's record with the dates as strings), valuation_stopped**.
The formatter has three renderings, excluded, stopped, screened, and beside
the last two the range section: the ends, the year with its dates and the
record's source, each assumption as the document writes it with its source,
PHI-4.3's words, the close with its date and source, or the stop's reason
where each would be. The compliance gate is idle by construction; the gate
is designed at 4.3.

**On Alphabet today:** the screen stops at PHI-2.1 for FY2021 (decision 48,
D36), the range publishes regardless, 129.39 to 205.62 on FY2025, the
price is the last stored close. 4.2 passes on that answer while 4.1 waits
for the FY2027 report.

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
- **The price provider** the node stores a candidate's close through is the
  one the holdings' closes come from, `nodes.price_provider()`, a function
  so a test stands one in; it asks the library for the unadjusted close
  (Part 9). The library's `end` is exclusive: a run before local midnight
  stores that day's close once the market has closed and never an
  intraday figure.
- **The exchange's historical table lags**: asked at about 22:30 UTC on
  the 17th it carried the 16th and not the 17th. A one-day window
  returned an empty table rather than an error; widen the window before
  concluding a date is absent.
- `config.toml` carries five fetch intervals. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; `config.toml` is read relative to the project
  root, so scripts run from the root. The whole suite on a scratch copy:
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest`.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router. A question can
  be piped in: `printf 'question\n:q\n' | python src/agents/cli.py --portfolio 3`.
- **`quant/fundamentals.py` imports `filed_figures.FIELDS`**, the one place
  the block's shape is defined; **`quant/valuation.py` imports
  `fundamentals.net_debt`, `_figure`, `_date` and `years_filed_by`**;
  **`agents/nodes.py` imports `valuation.valuation_range`,
  `screening.range_assumptions` and `watchlist.growth_pair`** inside the
  node, so the loader is before the node in any commit order.
- **`filed_figures.NON_MONEY_UNITS`** is `pure` and `shares`; every other
  unit is a currency and a block has one.
- **The four-digit SIC rule is held twice**: `screening._SIC_CODE` and
  `providers/edgar.SIC_CODE`, the same regex.
- **`tests/test_research_formatter.py` imports `run_cases`** from
  `tests/benchmark` by a path insert; **`check_4_2` runs there over
  hand-built blocks**, so a change to the check is seen by pytest through
  the rendering. The runner still is not part of pytest.
- **`tests/test_candidate_close_is_the_print.py` reads the suite's database
  copy** and fails, naming the dates, on a database in which the node has
  not stored GOOGL's closes, as a schema test fails before its migration.
- **zsh does not split an unquoted variable into words.** Write test paths
  out. **zsh reads a bare `=word` as a command lookup**: `echo =====` fails
  and everything after `&&` on that line does not run.
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

## 4. What the twenty-third session did

`git log --oneline cb3de91..HEAD`, fourteen commits with this file and
the correction of this count (first written as fourteen when it was
thirteen, corrected 18 September). Case 4.2 into the graph, the check
first, and nothing else.

**The loops, first.** pytest 1156, the CLI on the allocation question as
expected, then with a yes the golden set with stderr kept and the runner,
one after the other on the cache: zero diff on seventeen lines, stderr
the pinned rebalance failure alone; 13/14, 4.1 BLOCKED at PHI-2.1 for
FY2021 naming D36. The branch the brief named did not exist and was
created on the owner's yes.

**Decisions 56 and 57**, the brief's placeholders unfilled. The owner took
56, Alphabet stays, and delegated 57 with the rule that a short-term option
is not to be taken. Taken as: the last close of the ticker the question
named, from the existing price provider, in the existing closes table, on
an assets row the node creates from what it knows and nothing more; the
exchange's quotes stay the reference and never become the source; item 7's
second half with it, the named ticker's close.

**The shape**, one yes: what `check_4_2` asserts and cannot see; the loader
and what it refuses; the node's five assumptions with their sources, the
price under 57, the record and the stop published the way the screen's
are; the rendering; the routing row with its prediction; which loop sees
what; the order of commits by the import-time checks; the rejected
alternatives. Rejected: a model proposing an assumption, a midpoint or
spread in the formatter, the DataAgent's price route, a default pair, a
separate valuation intent, filed figures on the record, running the
runner between the node and the rendering.

**Under the yes, in order.**
- **3f4e4f4** `check_4_2` and `blocked_on_range` in the runner; the
  percentage check lets the record's rates through; fifteen cases, n/15.
  Seen BLOCKED on `--case 4.2` alone, and the reason showed the router at
  out_of_scope with an empty plan: the first sighting of the routing.
- **4e2385f** Part 9 C: GOOGL's closes 10 to 16 September, the exchange's
  print against the provider's library called unadjusted from the shell,
  five of five to the cent, both fetched on the owner's yes.
- **09808b4** `portfolio_tool/watchlist.py` and its 26 tests; the two
  sentences saying no loader reads the file corrected. Seen failing without
  the module (26) and against a version handing a candidate the first
  stated pair (1), bytecode off.
- **0456484** the node: `source` on the block, `_last_close` and
  `price_provider()`, `range_assumptions` in the screen module with three
  tests, the record and the price published with a stop beside each; the
  ends on the fixture's stored rows Part 11 C's. Seen failing against the
  unchanged node (17) and against a version filling the candidate's row
  with a default asset class (1), bytecode off. The price step's catch
  narrowed to `DataCalculationError` before the diff.
- **f29ee84** the rendering, `_format_valuation` and `_rate`, held to the
  runner's 4.1 and 4.2 over hand-built blocks; the record's own source in
  the header after a fixture with two sources failed the check. Seen
  failing against the unchanged formatter (8) and against a version
  printing the middle of the range (3), bytecode off.
- **d0adf70** the golden set's eighteenth line, "What is GOOGL worth?";
  **1dac03e** its baseline recorded at out_of_scope, one run.
- **a23a680** the registry: two sentences, on research and on
  out_of_scope, saying a company's worth is a range from the owner's
  assumptions and not a forecast; the prediction in the message.
  **bc2530d** expected.txt after two identical runs, the line at research
  with ScreeningAgent, nothing else moved.
- **The runner, 14/15**, after the rendering and the routing: 4.2 PASS.
- **The first live record, through the CLI**: 129.39 to 205.62 on FY2025,
  Part 11 C to the cent on the stored rows; the five assumptions with their
  sources; the last close 347.33 on 2026-09-17, source yfinance, the 17th
  past Part 9 C's dates; the screen stopped at PHI-2.1 beside it; no
  currency on either figure. GOOGL's assets row: name, USD, nothing else.
- **295a101** `test_candidate_close_is_the_print.py`: the stored rows for
  Part 9 C's five dates against the print, the assets row against 57.
- The exchange asked for the 17th on a yes: its table stopped at the 16th.
  Logged, not repaired.
- **f3112d4** the record: five entries, four resolved, the header.
- **b33c164** benchmark.md's status note and the count's dated note.

**Not done, on purpose.** Part 13 E item 6, the owner's call, not started.
Prediction scoring, the research agent, decisions 51, 52 and 54, the seven
emoji headers, the philosophy topic lookup, the CIK confirmation against
the submissions document's tickers, the `blocked_on_screen` wording: all
outside the brief, the last one logged.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- **56**: Alphabet stays case 4.1's X. 4.1 blocked by decision until the
  FY2027 report; nothing in the watchlist or the runner changes.
- **57**: the price for a candidate not held, as §4 says; Part 9 C its
  reference. Item 7's second half with it: the close of the ticker the
  question named, the count covering every class.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve. **Eleven by count**: the previous handoff said ten
numbered by the owner and listed these same eleven, so one of the two was
wrong; CLAUDE.md's line reads ten and is the owner's to reconcile. The cap
is 25.

10. A window return as a measure with a reference.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding. Absorbs 35.
22. Volatility over as-traded closes or a total-return series.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, 11 and 36.
48. Part 13 E's item 6 only, shaped in the twenty-first session's handoff
    and unchanged: delete the two `marketable_securities` fields no metric
    reads, reference note first, then the field list, two commits. Items
    3, 4 and 7 decided.
51. The four live intents outside the benchmark roster: delete or keep.
    Trigger: the full test at the end of Order 4.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields: delete, its
    own sitting.

- **The full test at the end of Order 4** (owner's, unchanged): when Order
  4's last commit lands, the project stops for a full test across both
  halves before Order 5. Not this session: 4.3, 4.4 and 4.5 remain.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12. Level 4: 4.2 and 4.6 PASS; 4.1 BLOCKED by decision,
the runner's reason line saying why; 4.3 to 4.5 have no check. The ledger
has four open predictions and no scored one. n/15 is a count of
well-formed answers. What the runner cannot see: whether the range's ends
are right; pytest holds that through Part 11 C on typed blocks and on the
node's assembly of the fixture's rows, and the first live record was read
against Part 11 C by hand.

---

## 7. Next steps, in order

**1. Prediction scoring**, case 4.5, its Part first: a stated outcome
against a stated condition, by hand, for each of the four predictions'
shapes (a figure with a bound, an event with a source), then the check,
then the scorer over the watchlist's prediction rows, which the loader
leaves alone today.

**2. The research agent**, cases 4.3 and 4.4, where the compliance gate is
designed for real and a model's proposal gets its vocabulary (Part 11 E).
3.2 is rewritten at the commit that makes 4.3 answerable (benchmark.md).

**At the end of Order 4: the full test** (§5), before Order 5.

### Later, with reasons

- The 17th's close against the exchange, by hand, when the table carries
  it: one row in Part 9 C; the candidate closes test then pins it.
- The `blocked_on_screen` wording, its own commit (KNOWN_GAPS).
- Item 6, decision 48, as shaped.
- The currency on the range and the price records, when a case asks
  (KNOWN_GAPS, "The range and the close print without a currency").
- The formatter headers carrying an emoji, seven in `nodes.py`. One commit,
  the runner run against it. Work, not a decision.
- CLAUDE.md's golden command: `2>/tmp/golden_err.txt` in place of
  `2>/dev/null`, as the brief and §2 already have it; the owner's to change.
- A philosophy topic lookup: a discriminator row on `research`, when a case asks.
- The node does not confirm the resolved CIK's submissions document lists
  the ticker asked (KNOWN_GAPS, the tickers entry).
- Decisions 51, 52 and 54, each its own sitting.
- The registry text naming VaR, drawdown and risk parity: a prompt change,
  prediction first, two golden runs.
- PHI-3.2's code list grows by measured filer, by the owner's hand; the
  field lists grow by witnessed tag (D36), the same way.
- W-2 before any question names it: its filer row and facts, a live fetch
  each, and its growth pair on the owner's word (KNOWN_GAPS).
- The seven-day cache runs out on 22 and 23 September; the next paid run
  after that fetches, and says so first.

---

## 8. Rules learned the hard way

**A reference row for "the last close" defends a call, not tomorrow's
figure.** Part 9 C was written for the 16th and the first live run stated
the 17th, which the exchange's table did not yet carry. The row still
holds every date it covers, the test pins only those, and the entry says
what is defended: the provider's unadjusted call on this ticker, with
Part 9 B as the convention's falsifier.

**A fixture with two sources finds a rendering that prints one.** The
screened fixture's block named Part 10 as its source and the record named
EDGAR; the runner's check asked for the record's source in the answer and
the rendering had printed only the block's. The fix was in the rendering,
not the fixture: a range names its own source.

**A designed stop catches the designed error and nothing wider.** The
price step first read `except Exception`, which would have published a
defect in the path as a stop with a plausible reason. Narrowed before the
diff was shown; the node test's failing provider still lands as a stop
because the data manager turns it into a failed result.

**Sight a new case before writing its golden line.** `--case 4.2` alone
showed the routing at out_of_scope on the day the check was written, so
the golden line was added at its true baseline and the registry's
correction had a recorded state to move.

**The registry's descriptions are the prompt.** Adding a sentence that
describes a capability the system now has is the allowed shape, and it is
still run as a hypothesis: the prediction in the commit before the run,
two runs, the line pinned after two misses. It held on the first pair.

**A one-day window on the exchange's table returns nothing, not an
error.** Widen the window and read what the table's last row is before
saying a date is absent.

**Add up the pending list.** The previous handoff wrote "ten" above a list
of eleven numbers; this one counts them and says the two disagree.

**The owner's documents are written on a separate word**; **a shape's home
for a number is measured against the loader before the shape is brought**;
**the golden loop's stderr goes to a file**; **a table-reading test pins a
count**; **a pinned csv can carry two line endings**; **zsh does not
word-split an unquoted variable**; **test regexes say the order the code
says it in**; **measure the brief's expectation before writing the shape**;
**a csv with CRLF endings is edited on the bytes**; **a witness for a list
is a same-value pair on one filing**; **say which loop cannot see a
change**; **a test over the suite's database copy owns the rows it reads**;
**a formatter states what the data says and never what the system is**;
**the import-time checks decide the commit order**; **two paid loops on one
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
python tests/benchmark/run_cases.py --case 4.2

python src/agents/cli.py --portfolio 3        # :q to quit
printf 'What is GOOGL worth?\n:q\n' | python src/agents/cli.py --portfolio 3

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
find src -name __pycache__ -type d -prune -exec rm -rf {} +
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/<file>.py

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only publish
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~4s, no model calls | Do the components still work; does every reference Part reproduce, Part 11 on typed blocks and on the node's assembly of the fixture's rows; does the node fetch in order and publish the block, the record and the price; does each rendering pass the runner's check; are the candidate's stored closes the print |
| CLI | ~3s, one call | What it is actually doing: the plan, the parameters, the reasoning line, the answer text |
| Golden set | ~90s, cents, **writes filed and price rows** | Did routing change anywhere (eighteen lines, one pinned failure). Blind to parameters and answer text; stderr kept to a file |
| Benchmark runner | ~2min, cents, **writes filed and price rows** | How many cases pass, n/15. Blind to the four intents outside the roster, to 4.3 to 4.5, and to whether a range's ends are right |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once.
