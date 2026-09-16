# AGENTIC_FINANCE — Session Handoff

**Session date:** 16 September 2026 (twentieth session). Regenerated at its end.
**Branch:** `node`, cut from `baseline-v1` at 921d1fe, the trunk's tip at session start. **`baseline-v1` is the trunk**: each session branch is merged into it with `--ff-only` when the loops are green; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count 921d1fe..HEAD` — 15, this file's included, counted after it was added. **Not merged and not pushed**: the owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1094 passed, 6 xfailed**, up from 1019 by 75 tests: 21 for the ticker-file provider method, 11 for its table, 10 for its cache rule and lookup, 5 for `screening.exclude`, 10 for the node, 11 for the formatter, 7 across the registry tests. **Golden set run twice**, both runs identical and exactly the prediction written into 8c63f2f: one new line, sixteen unchanged, the pinned rebalance failure included; `expected.txt` updated (7c984b8). **Runner 13/14**: 4.6 PASS, 4.1 BLOCKED by design. **Migration e289a03682f2 was run by the owner** and its output pasted; the head is e289a03682f2. **Live fetches, each asked for first:** the SEC ticker file, JPMorgan's and Alphabet's submissions documents, Alphabet's company facts (§4). The CLI ran the node once on "Does JPM clear my philosophy?" and answered as 4.6 expects (§4).

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** The nineteenth session's handoff said the golden set and the
runner had not run since 175f439; both ran at this session's start and
were clean, which was news and not a regression. This session's own
misses, corrected before they landed: a filed date typed a day early in
the node test, caught by the csv's own-report row; a formatter sentence
stating that the valuation pipeline does not exist, false in one rendering
and a status line in the others, removed after the first render was read;
"yes0" read as yes with a stray key, and said so. One finding after the
sweep: the suite went red at a documentation commit because a schema test
had been passing on a table another test emptied (§8).

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the bridge (eighteenth session), the SIC code on the block (nineteenth), and now **the philosophy check node, decision 29** (§4). Left in Order 4: the valuation pipeline (Part 11, case 4.2), prediction scoring (4.5), the research agent (4.3, 4.4), and decision 48 before 4.1 can pass. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. Level 4: six research cases; 4.1 and 4.6 have checks on the runner, 4.6 passes, 4.1 blocked by design (status note under Level 4, this session). n/14. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Fourteen cases. 4.1 and 4.6 added this session, written first and seen BLOCKED, then 4.6 PASS. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 94 trigger lines, 64 reading something other than "none", counted by grep. New this session: the schema test that passed on an emptied table. Closed this session: the philosophy question routed to the IPS, the three unreached modules, the UTC pull date, the code's as-of beside the block's, the Part 10 node entry; the gate entry re-triggered on 4.3. |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, Parts 1 to 13. Two dated notes this session: Part 10 F, the first live 4.6 answer against the expected one; Part 13 E item 8, decided and built. Never update it to match code output. |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, saved in Excel at c75b73b. Untouched this session. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. Unchanged this session; **read by the graph for the first time**, through `philosophy.toml`. |
| `docs/WATCHLIST.md` | Two synthetic candidates, four predictions due early 2027. Nothing reads it; the node takes its ticker from the question, not from the watchlist. Unchanged. |
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

- **Hot potato — agents never see raw data.** This session's form: the
  screening block carries the fiscal years as two dates each and no
  figure; the findings are the summary; the runner's checks fail a block
  whose years carry anything else.
- **Policy lives in config, not code.** The philosophy is `philosophy.toml`,
  named once in `nodes.PHILOSOPHY_PATH` until Order 6 (decision 30).
- **Two policies, two questions.** The IPS says what may be held; the
  philosophy says what is worth wanting. Two intents now: `compliance` and
  `research`. Before this session a philosophy question on a held ticker
  ran the IPS check; the golden line pins that it no longer does.
- **Raise, do not repair.** This session's form: a check that stops on a
  missing figure is published as a stop and printed as one, no verdict; a
  ticker the SEC file does not list is an error naming it; none or two
  tickers is an error; a code EDGAR does not state stops the check naming
  PHI-3.2.
- **An excluded company's figures are never asked for.** The exclusion is
  decided on the filers row before the company facts are fetched
  (`screening.exclude`); JPMorgan's first live check read no fact.
- **Typed facts are not a source.** The reader has fetched Apple and
  Alphabet; the tests' figures stay in the tests.
- **References before code.** The runner's checks before the node; each
  test seen failing before its code; the formatter held to the runner's own
  checks over hand-built blocks.
- **No price forecasts as numbers.**
- **A capability nothing reaches is inventory**: deleted behind a tag.
- **A value nothing consumes is not stored.** The ticker file's company
  title is not carried; the filers row holds EDGAR's name.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
  This session's shape ran to twelve numbered parts and was taken with one
  yes; then one commit per part, test first and seen failing for its own
  reason, `git status --short` and the diff read before each commit, and
  the word yes before it lands.
- **Grep for the caller, not the registration, and grep for the writer
  before trusting a reader.**
- **A prompt change is a hypothesis.** The prediction went into 8c63f2f's
  message before the golden run; two runs, both exactly it.
- **A live fetch is asked for before the machine is touched**, once per
  request set, with what will be stored named first. Four this session,
  all yes.
- **The migration is run by hand** and the output pasted. One this
  session, e289a03682f2.
- **An instruction with a stray character is read as what it is**, and the
  reading is said: "yes0" was a yes.
- **The import-time checks decide commit order.** A roster entry with no
  node, or an intent with no synthesizer branch, fails at import, and the
  registry description is the prompt; so the node and the formatter landed
  unbound, and the registries landed last with the golden line.
- **PHILOSOPHY.md and IPS.md are mine to edit.** Untouched this session.
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

**1094 passed, 6 xfailed, 26 warnings, about 3.5 seconds.** Run at session
start (1019) and after every commit; red once by the pattern between the
migration commit and the owner's `alembic upgrade head` (1 failed, 4
errors), and red once by a defect (§8), fixed in 0bd3c45.

**Golden set: zero diff, seventeen lines, one pinned failure** ("Should I
rebalance my portfolio?", errors 1). Run clean at session start against
the sixteen-line file, then twice after 8c63f2f, both identical and as
predicted. `expected.txt` moved once (7c984b8), one block added. **Runner
13/14**: 12/12 at session start, then 4.1 and 4.6 BLOCKED after 873b805,
then 4.6 PASS and 4.1 BLOCKED on the stop at PHI-2.1 after the binding.

**The CLI, twice.** "What is my current allocation by asset class?" at
session start, as the runner's 1.1 expects. "Does JPM clear my philosophy?"
after the binding: intent research at 0.95, plan and agents run
`['ScreeningAgent']`, one step, the answer in §4.

**Level 4: 1 of 6 cases passes (4.6); 4.1 blocked by design; four have no
check.** Read n/14 as a count of well-formed answers and never as the
system being good at research (benchmark.md).

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. `node` is this session's branch,
from 921d1fe. `filer`, `bridge`, `consolidate`, `selection`, `compliance`
and `vocabulary` are merged and older. `wip/phase7-snapshot` holds rejected
Compliance/IPS code. `wip/rag-early` and tag `rag-early-parked` hold the
RAG code. `quant-inventory-parked` at 8d87455 holds the tree before the
seventeenth session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`e289a03682f2`**, 25 migrations, linear, all applied. One migration this
session, run by the owner, output pasted. No reseed. **The paid loops now
write to this file**: the golden line and the runner's 4.1 and 4.6 run the
node live, and its fetches store rows here under the seven-day interval.
Tables that matter:

- `portfolios`, `transactions`, `assets` (9 rows).
- `daily_prices`: 6,966 rows and not a fixed count. `macro_data`: 200 and
  growing.
- **`ticker_ciks`: 10,422 rows, the SEC ticker file as of 2026-09-16 01:33
  UTC**, every listed filer's (ticker, CIK) pair. Rewritten whole past the
  interval.
- **`filers`: three rows**, Apple (3571), JPMorgan (6021, pulled 01:33 UTC),
  Alphabet (7370, pulled 01:38 UTC).
- **`filed_facts`: 28,787 rows, Apple's 15,132 and Alphabet's 13,655.**
  `filed_fetch_metadata`: two rows, Apple 2026-09-15 22:17 UTC, Alphabet
  2026-09-16 01:38 UTC. JPMorgan's facts were never fetched: the exclusion
  decided first.
- `financial_statements`: 65 rows, neither the reader's store nor a source
  (decision 52). `fx_rates`, `fx_fetch_metadata`: empty.

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

## 4. What the twentieth session did

`git log --oneline 921d1fe..HEAD`, 15 commits, this file's included.
Decision 29 and nothing else on the code, in the order the import-time
checks dictate.

**The loops, first.** pytest 1019, the CLI on the allocation question as
expected, then with a yes the golden set (zero diff) and the runner (12/12),
both clean at 921d1fe: the nineteenth session's "nothing since touches
what they see" held.

**873b805, the runner's checks for 4.1 and 4.6**, written first and seen
BLOCKED live. 4.1 routed out_of_scope; **4.6 routed compliance with the
full IPS plan**, the held ticker JPM taking a philosophy question to the
portfolio check, the wrong face KNOWN_GAPS had recorded, now on a runner
prompt. The checks assert on `shared_data["screening"]` and the answer,
never on an agent name; 4.1's probe also blocks on a check that stopped on
a missing figure, naming decision 48. Prompts name tickers: company names
are decision 16.

**The shape of decision 29**, twelve parts, one yes: intent `research`
(4.2 and 4.3 become rows under it), agent `ScreeningAgent`, plan
`[ScreeningAgent]`, the block, the order of calls with `exclude` before
the facts fetch, question 50 by the SEC ticker file, question 30 by the
committed file, the clock UTC, the formatter against Part 3b, the gate idle
by construction, the commit order, three logged items.

**Under the yes, nine commits, each test first and seen failing.**
- **be1158b** `EdgarProvider.tickers`, held to Apple's, Alphabet's and
  JPMorgan's CIKs. 21 tests.
- **3cc410c** `TickerCik` and migration e289a03682f2, committed unexecuted;
  the owner ran it; 11 tests.
- **269bf3e** `filings.update_ticker_ciks` and `cik_for`: the whole table
  rewritten past the interval; fetch before saying unlisted. 10 tests.
- **65cadcf** `screening.exclude`, D34 on the code alone; `screen` calls
  it; no behaviour change. 5 tests.
- **927a6f5** the node, unbound. Over stand-in providers fed from the
  golden csvs: JPM excluded with no facts call; GOOGL fetched and stopped
  on PHI-2.1 at FY2021 (Part 13 B); dates only; both pull instants UTC
  with the offset. 10 tests.
- **f102741** the formatter, three renderings, each held to the runner's
  own check for its case. 11 tests. A status sentence removed after the
  first render was read.
- **8c63f2f** the registries, the graph binding, the synthesizer branch,
  the golden line, the prediction in the message. Out_of_scope description
  byte-identical, no few-shot.
- **7c984b8** `expected.txt`, after two identical runs.
- **0d99940, 2c259ff, 16ebfac** the record, the reference notes, the
  benchmark status note.
- **0bd3c45** the schema test that owned no rows (§8).

**The live runs.** Golden run one fetched the ticker file and JPMorgan's
submissions; run two hit the cache. The runner's 4.1 fetched Alphabet's
submissions and company facts and the check stopped at PHI-2.1 for FY2021,
as the node test had predicted from the csv. The CLI's answer on JPM:

> **PHILOSOPHY CHECK: JPM** — JPMORGAN CHASE & CO, CIK 19617, checked as of
> 2026-09-16 against the philosophy's 17 clauses. JPM is excluded under
> PHI-3.2: SIC 6021, National Commercial Banks, as EDGAR stated it on
> 2026-09-16 UTC. [PHI-3.2's text.] Nothing else is reported about the
> company: no figure was read and no other clause was checked. **Not
> done:** no recommendation. No position is implied, so the investment
> policy was not consulted.

Part 10 F's expected 4.6 answer, with today's pull date; recorded there.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- **29.** The node for the philosophy check, as shaped and built above.
  Inside it: **30**, the philosophy is the committed file until Order 6 (a
  portfolio column, `.env` and a config key rejected); **50**, a ticker
  becomes a CIK through the SEC ticker file (the watchlist's CIK, the
  submissions document's tickers as the forward map, and `assets.cik`
  rejected); the clock, UTC for all three records, the offset in the data,
  the day marked UTC in the answer; the gate, idle by construction, designed
  at 4.3. Rejected on the way: catching the screen's raise as control flow;
  a stub node so the registries could land first; a formatter sentence
  about the system's status.
- **The full test at the end of Order 4** (owner's, unchanged): when Order
  4's last commit lands, the project stops for a full test across both
  halves before Order 5.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve. **Ten**, under the cap of 25 (CLAUDE.md's line reads 12
on 16 September and is the owner's to update to 10).

10. A window return as a measure with a reference.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
16. Company names, German phrasings, the softer 3.5. "Does Alphabet clear
    my philosophy?" extracts no ticker today and the node refuses; the
    runner's 4.1 names GOOGL for that reason.
17. `group_by` as the subject kind of a compliance finding. Absorbs 35.
22. Volatility over as-traded closes or a total-return series.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, 11 and 36.
48. Part 13 E's questions 3, 4, 6 and 7. **4.1 is blocked on 3 and 4**: the
    check stops at PHI-2.1 for Alphabet's FY2021. Once decided, the next
    stop is PHI-4.1 with no valuation range, which is Part 11, and the
    runner's 4.1 probe will misname that stop as 48 until its text moves.
51. The four live intents outside the benchmark roster: delete or keep.
    Trigger: the full test at the end of Order 4.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields: delete, its
    own sitting.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12 at 8c63f2f. Level 4: 4.6 PASS, the first Level 4 pass,
on a refusal decided from stored data with no model in the loop; 4.1
BLOCKED by design on decision 48; 4.2 to 4.5 have no check. The ledger has
four open predictions and no scored one. n/14 is a count of well-formed
answers.

---

## 7. Next steps, in order

**1. Decision 48, items 3 and 4**: the metric keys for a filer presenting
no gross profit and no combined D&A, the owner's, with Part 13 B's rows as
the measurement. Until then 4.1 stays BLOCKED and nothing fills a figure to
move it. When 48 is decided, the 4.1 probe's reason text moves with it.

**2. The valuation pipeline**, Part 11 by hand first, then case 4.2 as a
row under `research`; PHI-4.1 stops on its absence today.

**3. Prediction scoring** with its Part, case 4.5; then the research agent
for 4.3 and 4.4, where the compliance gate is designed for real.

**At the end of Order 4: the full test** (§5), before Order 5.

### Later, with reasons

- The formatter headers carrying an emoji, seven in `nodes.py`; the
  research formatter's header carries none. One commit, the runner run
  against it. Work, not a decision.
- A philosophy topic lookup ("what does my philosophy say about debt?"):
  a discriminator row on `research`, the way `policy_topic` is on
  compliance, when a case asks.
- The node does not confirm the resolved CIK's submissions document lists
  the ticker asked; `filer()` drops that field (KNOWN_GAPS, the tickers
  entry).
- Decisions 51, 52 and 54, each its own sitting.
- The registry text naming VaR, drawdown and risk parity: a prompt change,
  prediction first, two golden runs.
- 3.2's rewrite and Part 2's boundary: at the commit that makes 4.3 answerable.
- PHI-3.2's code list grows by measured filer, by the owner's hand.

---

## 8. Rules learned the hard way

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
git switch baseline-v1 && git merge --ff-only node
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
