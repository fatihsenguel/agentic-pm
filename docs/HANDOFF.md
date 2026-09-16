# AGENTIC_FINANCE — Session Handoff

**Session date:** 16 September 2026 (nineteenth session). Regenerated at its end.
**Branch:** `filer`, cut from `baseline-v1` at c75b73b, the trunk's tip at session start, which was the owner's Excel save of the workbook after the eighteenth session's merge. **`baseline-v1` is the trunk**: each session branch is merged into it with `--ff-only` when the loops are green; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count c75b73b..HEAD` — 9, plus the one that lands this file. **Not merged and not pushed**: the owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1019 passed, 6 xfailed**, up from 958 by 61 tests: 34 for the provider method, 15 for the filers schema, 8 for the cache rule, 4 for the reader's code keys. **The golden set and the runner were not run**, on the owner's instruction and my agreement: nothing this session touched routing, a prompt or an answer's text, and no graph node imports the provider, the filings module, the reader, the philosophy loader or the screen; a run would pass in both states and distinguish nothing. The CLI ran once at session start on the allocation question and answered as the runner's 1.1 expects. **Migration c8dd6b3dc535 was run by the owner** and its output pasted; the head is c8dd6b3dc535. **Two live submissions fetches and one read of the published SIC list** (§4).

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** The eighteenth session's handoff said CLAUDE.md's pending-list
line still read 32; it read 14, and had since the owner updated it. The
instruction for this session also came through with words missing in two
places (the reader's output in step 4, the live check's targets in step 5);
both were read against the shape §5 held for decision 49 and the reading
was stated before building. A claim written into the record before it was
checked ("EDGAR publishes no lighter document that carries the code") was
caught on reading the diff back and replaced with "not looked up". A count
written as "four years in five" was added up against Part 12 A and became
"every one of the five".

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: step 1, the bridge, landed in the eighteenth session; the SIC code on the block landed this session (§4). The philosophy check and the filings reader are pure modules nothing in the graph reaches; the node is decision 29, next. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass at 175f439, not run since. Level 4: six research cases, none running. Unchanged. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Twelve cases. Unchanged. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 93 trigger lines, 69 reading something other than "none", counted by grep. Log a finding only with a trigger or a decision number. New this session: "The submissions document carries the tickers, and more Part 13 C did not record", "The filer fetch downloads the filings index it discards", "The code on the block is as of its pull, not as of the block's as-of". The fails-open entry now records what the published list says. |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, Parts 1 to 13. Part 12 F carries a dated note that PHI-3.1's text now states what nets against debt. Never update it to match code output. |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, saved in Excel at c75b73b with its cached values back. Untouched this session. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. **PHI-3.1 now states what nets against debt**, cash and cash equivalents only, the one edit this session made to the owner's document, on the owner's yes to the sentence brought (f3b0deb). |
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
  document first. This session's form: PHI-3.1's definition of net debt went
  into the document's sentence and the clause's `text` in one commit, and
  no parameter was added, because the definition is carried by the metric
  key.
- **Two policies, two questions.** The IPS says what may be held; the
  philosophy says what is worth wanting.
- **Raise, do not repair.** A refusal is an honest failure; a plausible wrong
  answer is not. This session's form: a company with no filers row raises in
  the reader, because never having asked EDGAR is not EDGAR stating no code;
  a code EDGAR does not state comes through as None and the screen stops on
  it naming PHI-3.2; a submissions document for another CIK raises.
- **Typed facts are not a source.** A company's figures come from the
  reader; typed figures stay in tests. The reader has fetched twice.
- **References before code.** Part 13 C's fourteen rows before the provider
  method; the schema test before the migration; each rule of the cache
  before the function.
- **No price forecasts as numbers.**
- **A capability nothing reaches is inventory**: deleted behind a tag, not
  kept with a note.
- **A value nothing consumes is not stored.** The submissions document
  carries some twenty fields; four are read and stored. The record names
  the rest and what each would be for.

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
- **An instruction with words missing is read against the record, and the
  reading is stated before anything is built.** Step 4's sentence lost its
  middle; the handoff's shape under decision 49 said what the reader returns
  and what stays the node's, and the commit said which reading was built.
- **A live fetch is asked for before the machine is touched**, once per
  request set, with the script written and described first. Two this
  session, both yes.
- **The migration, the reseed and any rewrite of stored rows are run by
  hand**, and the output is pasted. One migration this session, c8dd6b3dc535,
  run by the owner after the commit that carried it unexecuted.
- **PHILOSOPHY.md and IPS.md are mine to edit.** A session brings the wording.
  This session the sentence for PHI-3.1 was brought with Part 12 F as its
  source, the owner said yes, and the edit is in the same commit as the
  config that reads it.
- **CLAUDE.md is mine and untracked.** A session proposes wording; I apply it.
- No emoji in anything newly written. A count I predict is a count I add up.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect. My real portfolio's data in the repo: Order 6, last. No cached
holdings table; no fallback rate, currency or policy; no adjusted close; no
environment switch for which policy runs. **No invented figures as a runtime
source, and no price a stock will reach anywhere.** No mutation testing until
necessary. No widening of the router's schema to make it a better classifier.
No SIC code range recited from memory, and **no code added to PHI-3.2 from
the published list alone: a code enters with a filer measured under it.**
**No "inventory, not capability" notes on dead code: delete it behind a
tag.** No NOPAT at the company's filed tax rate: the rate is mine and stated
in the clause.

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

**1019 passed, 6 xfailed, 26 warnings, about 3.5 seconds.** Run at session
start (958), after each of the four decision-49 commits (992; then 1000
passed, 1 failed, 6 errors with the migration unexecuted; 1015 with it
applied; 1019) and after the PHI-3.1 commit (1019).

**The golden set and the runner: not run.** Last run at 175f439, the
seventeenth session's tip: golden zero diff with one pinned failure, runner
12/12. Nothing since touches what they see. The commits between 175f439 and
c75b73b were checked at session start: two trunk rewrites of `.gitignore`
and `.env.example`, the record, the reference, the workbook, the philosophy
document and config, and four modules under `portfolio_tool` that no graph
node imports (`quant/fundamentals.py`, `philosophy.py`, `screening.py`,
`filed_figures.py`; grep over `src/` finds no importer outside the four).
This session added to that set: `providers/edgar.py`, `filings.py`,
`filed_figures.py`, `provider_models.py`, `database_setup.py`, the
philosophy document and config. The router, the prompt, the nodes and every
formatter are byte-identical to 175f439.

**The CLI, once, "What is my current allocation by asset class?":** intent
`data_fetch`, plan DataAgent then PortfolioAnalysisAgent, five asset classes
summing to 408,080.00 USD, priced as of 2026-09-14, the look-through caveat
printed. As the runner's 1.1 expects.

**Level 4: 0 of 6 cases run.**

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. `filer` is this session's branch,
from c75b73b. `bridge`, `consolidate`, `selection`, `compliance` and
`vocabulary` are merged and older. `wip/phase7-snapshot` holds rejected
Compliance/IPS code. `wip/rag-early` and tag `rag-early-parked` hold the
RAG code. `quant-inventory-parked` at 8d87455 holds the tree before the
seventeenth session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`c8dd6b3dc535`**, 24 migrations, linear, all applied. One migration this
session, run by the owner, output pasted. No reseed. Tables that matter:

- `portfolios`, `transactions`, `assets` (9 rows).
- `daily_prices`: 6,966 rows and not a fixed count; it grows when a query runs
  after new closes.
- **`filed_facts`: 15,132 rows, all Apple's (CIK 320193)**, from the
  eighteenth session's live fetch. `filed_fetch_metadata`: one row, Apple,
  `last_fetch_time` 2026-09-15 22:17 UTC.
- **`filers`: one row, Apple, 3571, Electronic Computers, `pulled_at`
  2026-09-16 00:03 UTC**, from this session's live fetch through
  `update_filer`. Not asked again within `filings_fetch_interval_days`, 7.
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

### The filings reader, as it stands

Two fetches per company, both from `data.sec.gov` with `EDGAR_USER_AGENT`,
both under `filings_fetch_interval_days`:

| Fetch | Method | Store | Cache rule | Reader |
|---|---|---|---|---|
| Company facts | `EdgarProvider.annual_facts` | `filed_facts`, `filed_fetch_metadata` | `filings.update_filed_facts` | `filed_figures.filed_years_for`: `currency`, `as_of`, `years`, `provenance`, `unresolved` |
| Submissions | `EdgarProvider.filer` | `filers` | `filings.update_filer` | the same call: `sic`, `sic_description`, `sic_as_of` |

`filed_years_for` raises on a company with no filers row. `sic_as_of` is
`pulled_at` as stored, a UTC datetime, not a calendar day. The ticker, the
price, the shares and the valuation range are still the node's to assemble.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing; the real value is set. `data.sec.gov` has served three
  requests with it (one company facts, two submissions), `www.sec.gov` one
  (the SIC list page, HTTP 200 on the first URL tried). Each request was
  asked for before it was made.
- `config.toml` carries five fetch intervals. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import. The whole suite on a scratch copy:
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest`.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`; `exit` goes to the router.
- **`quant/fundamentals.py` imports `filed_figures.FIELDS`** for the block's
  figure vocabulary, since a16dbdd: the one place the block's shape is
  defined.
- **The four-digit SIC rule is held twice**: `screening._SIC_CODE` and
  `providers/edgar.SIC_CODE`, the same regex. The provider importing the
  screen would point the wrong way; named here so the copy is not found by
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

## 4. What the nineteenth session did

`git log --oneline c75b73b..HEAD`, 9 commits, plus the one that lands this
file. Decision 49 and nothing else on the code: no node, no intent, no
prompt change.

**The loops, first.** pytest 958, the CLI on the allocation question as
expected. The golden set and the runner: agreed not run, the reason in §2,
the importer check done by grep rather than taken from the handoff.

**Decision 49, four commits, each test first and seen failing for its own
reason.**

- **48e6ff0, the provider method.** `EdgarProvider.filer(cik)` fetches
  `data.sec.gov/submissions/CIK{cik:010d}.json` with the same contact and
  returns a `ProviderFiler` record of exactly cik, name, sic and
  sic_description. Held to the fourteen rows of `edgar_submissions.csv`
  through a stand-in session. A document for another CIK raises; a missing
  name raises; a code that is missing, empty, not four digits or not a
  string comes back as None, the form the screen already stops on. The two
  methods share one private request helper. 34 tests.
- **ba60cfe, the filers table.** `Filer` model and migration c8dd6b3dc535:
  cik, name, sic, sic_description, pulled_at; the two code columns nullable
  because EDGAR leaves them empty for some filers and storing that emptiness
  records what the document said. Committed unexecuted with its schema
  test, whose database half was red (1 failed, 6 errors) until the owner's
  `alembic upgrade head`, pasted, turned it green. 15 tests.
- **6e2553a, the cache rule.** `filings.update_filer` in the shape of
  `update_filed_facts`: not asked again within the interval; past it the row
  is rewritten as the document now states it and `pulled_at` moves whether
  or not the code changed, since EDGAR keeps no history and the row means
  "the code as of this pull". A failing provider leaves the row as it was or
  absent. `pulled_at` on `utcnow()`, the clock `last_fetch_time` is on; read
  against the UTC entry first, and since it does not differ from what
  `update_filed_facts` does it was not brought as a decision. 8 tests.
- **df08e54, the reader's output.** `filed_years_for` carries `sic`,
  `sic_description` and `sic_as_of` beside its five keys, from the filers
  row; raises on a company with no row; `filed_years` itself untouched. The
  stored-rows test moved onto a fixture storing both companies' facts and
  filers. 4 tests.

**The live check, 4630805 for the record it left.** Two requests, asked
for first: JPMorgan through the method alone, equal to Part 13 C's row in
every field; Apple through `update_filer`, stored, then `filed_years_for`
over the real rows returned the seventeen years with 3571 Electronic
Computers beside them and exactly the eight keys the test names. The
document's `cik` is the ten-digit zero-padded string and `sic` a string,
the csv's forms; the test's docstring, which had marked the form as an
assumption, now says what was found. Sizes: JPMorgan's document 4.6 MB,
Apple's 164 KB, for a name and a code.

**The published SIC list, read once.** One request to `www.sec.gov` with
the contact, HTTP 200, 439 codes. Every code PHI-3.2 lists is there with its
title; the range carries codes the clause does not list, 6029 and 6099 for
banks, 6321, 6324, 6351, 6361 and 6399 for insurers, and the credit and
brokerage codes between. Recorded in the fails-open entry, nothing added to
the clause: a code enters with a filer measured under it.

**Decision 41, f3b0deb.** PHI-3.1's text now states what nets against
debt, cash and cash equivalents only, with Part 12 F's reason as the
clause's own; the same sentence in `philosophy.toml`; no parameter. The
same-text test seen failing on the document alone. Part 12 F's note
(0c426de).

**The record (780b461).** The sweep listed in §0.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- **49.** The SIC code on the block, as §5 of the eighteenth session's
  handoff shaped it, built as four commits. Inside it: the code columns
  nullable; `sic_as_of` the pull time as stored, a UTC datetime, the clock
  question left with decision 29; a company with no filers row raises in
  the reader; a later pull rewrites the row and moves the date whether or
  not the code changed; `update_filer` returns the stored row. Rejected on
  the way: a `source` field on the filer record (nothing stores it); a
  NOT NULL code (the store refusing a fact EDGAR states); the reader
  importing the screen's regex (wrong direction, so the four-digit rule is
  held twice, §3).
- **41.** PHI-3.1's clause text names what nets against debt: cash and
  cash equivalents only, marketable securities never, with the
  presentation-choice reason. No config parameter: the definition lives in
  the metric key.
- The published SIC list is read and recorded, and no code is added from
  it; the clause grows by measured filer, as the seven did.
- **The full test at the end of Order 4** (owner's, recorded in the
  seventeenth session, unchanged): when Order 4's last commit lands, the
  project stops for a full test across both halves; Order 5 begins only
  when Levels 1 to 3 still pass, all six Level 4 cases are well-formed, no
  wrong face is left in the owner's notes, no invariant is violated, and
  the open record is under a number the owner sets then.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve. **Twelve**, under the cap of 25 (CLAUDE.md's line reads
14 on 15 September and is the owner's to update to 12 on 16 September).

10. A window return as a measure with a reference.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding. Absorbs 35, a
    rank selection in extraction: one selection axis.
22. Volatility over as-traded closes or a total-return series.
29. **The node for the screen**, next. Absorbs 30, what a philosophy is
    bound to, and 50, ticker to CIK: both are read by the node and decided
    when it is built. Three KNOWN_GAPS entries wait on it: the UTC pull
    date, the code's as-of against the block's, and the submissions
    document's `tickers` as a source for 50. The compliance gate is designed
    with it.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, the span and
    two-weights clarification rules; 11, the two verbatim benchmark
    few-shots; and 36, what `reasoning` is for.
48. Part 13 E's questions 3, 4, 6 and 7 (5 decided with 47, 8 with D34).
    W-1 cannot be screened on filed figures until 3 and 4 are answered.
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
(benchmark.md). 4.6's bank variant is now decidable from stored data with
no model in the loop: the block carries the code, and the screen stops on
PHI-3.2 before any year is read.

---

## 7. Next steps, in order

**1. Decision 29, the node**: runner checks for 4.1 and 4.6 written first
and seen BLOCKED; the intent and agent in the registries; the node; the
formatter; the golden line and the prompt, golden twice with the prediction
written first. The compliance gate is designed with it. The node assembles
the block: `filed_years_for`'s years and code, the ticker (50; the
submissions document's `tickers` is one candidate source, the reverse map),
the price with its date, the range (Part 11) and the shares (48, item 7).
It calls `update_filer` before `update_filed_facts` or after, and
`filed_years_for` raises if it forgets the first. Which clock the pull dates
are printed on is decided here, for both records at once. W-1 cannot clear
the screen on filed figures until 48's items 3 and 4 are decided: Alphabet
files no gross profit and no combined D&A.

**2. Then the valuation pipeline** with Part 11 by hand, and prediction
scoring with its Part.

**At the end of Order 4: the full test** (§5), before Order 5.

### Later, with reasons

- The formatter headers carrying an emoji, seven in `nodes.py`: compliance
  and out-of-scope (the KNOWN_GAPS entry), policy lookup, optimization,
  macro, rebalance and backtest. One commit, the runner run against it.
  Work, not a decision.
- Decisions 51, 52 and 54, each its own sitting; 54 touches every agent
  class. 53 is closed: delete behind a tag, when a session takes it.
- The registry text naming VaR, drawdown and risk parity: a prompt change,
  prediction first, two golden runs (KNOWN_GAPS).
- 3.2's rewrite and Part 2's boundary: at the commit that makes 4.3 answerable.
- The tool-boundary pass (45): the first benchmark case that fails for want
  of expression rather than capability.
- PHI-3.2's code list: a code the published list carries and the clause
  does not enters when a filer is measured under it, by the owner's hand
  (the fails-open entry has the candidates).
- The 34-second suite run, if it recurs: `--durations` on that run.

---

## 8. Rules learned the hard way

**An instruction with words missing is read against the record, and the
reading is written into the commit before the code.** Two sentences of this
session's instruction arrived incomplete. The handoff's shape for decision
49 said what the reader returns; the commit message named the reading, and
the report to the owner said where the reading differed from the text. The
alternative, building the sentence as it stood, would have put the ticker,
the price, the shares and the range into the reader, which is decision 29.

**A claim about the world goes into the record only after it is checked,
or marked as unchecked.** "EDGAR publishes no lighter document that carries
the code" was written from a guess and caught on reading the diff back; the
record now says it was not looked up. A count is added up before it is
written: "four years in five" became "every one of the five" against Part
12 A's dates.

**A schema test's database half is red between the commit and the owner's
migration, and that is the pattern, not a failure to fix.** The commit
message states the counts with it red; the paste turns it green; the next
commit's message states the counts with it green.

**A cache row that means "as of this pull" moves its date on every pull.**
An unchanged code on a new pull is a new statement of the code; keeping the
old date would say the code was last confirmed earlier than it was.

**A number in config goes into the document in the same commit as the code
that requires it, and not before**; **a scripted edit is checked at the
place it landed**; **a count is added up, twice**; **grep the writer the
reader reads, not a writer of the same name**; **a formatter test with a
hand-built input holds the formatter to a shape, not the node to the tool**;
**delete the caller before the callee, and grep the package init**; **a rule
taken from part of a source is measured over all of it**; **a record says
what the tree holds, not what the next step is**; **a wrong version checked
in place can run the previous one's bytecode** — still true, from earlier
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

# what the database says it is at (expected c8dd6b3dc535):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# nine assets; daily_prices and macro_data move, do not pin them;
# filed_facts holds Apple's 15,132 rows and filers Apple's one row:
sqlite3 data/portfolio.db "select count(*) from assets; select count(*) from filed_facts; select * from filers;"

# a check run against an edited, deliberately wrong module:
find src -name __pycache__ -type d -prune -exec rm -rf {} +
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/<file>.py

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only filer
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3.5s, no model calls | Do the components still work; does every reference Part reproduce; does the provider return Part 13 C's rows; does the reader carry the code and refuse a company never asked for |
| CLI | ~3s, one call | What it is actually doing: the plan, the parameters, the reasoning line, the answer text |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines, one pinned failure left). Blind to parameters, answer text and everything under the judgement half's modules |
| Benchmark runner | ~1.5min, cents | How many cases pass. Blind to the four intents outside the roster and to the judgement half |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text.
