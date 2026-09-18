# AGENTIC_FINANCE — Session Handoff

**Session date:** 18 September 2026 (twenty-fifth session, the second of the day). Regenerated at its end.
**Branch:** `research`, cut at 0e1c1ad, the tip of `score`. **`baseline-v1` is the trunk** and stands at 264aa7a: **it has not merged `score`**, so the twenty-fourth session's 21 commits and this session's are both ahead of it, and one `git merge --ff-only research` brings in both. Each session branch is merged into the trunk with `--ff-only` when the loops are green; the tags `baseline-v1-20160b0`, `baseline-v1-clean`, `baseline-v1-green`, `rag-early-parked` and `quant-inventory-parked` mark older tips and parked code. This session's commits: `git rev-list --count 0e1c1ad..HEAD` — 10: one carried item, Part 15, two for the runner's new cases, three for the pure modules beneath them, the record, benchmark.md, this file. **Not merged and not pushed**: the owner merges and pushes; `origin`'s push URL is `no_push`.

**State:** pytest **1346 passed, 6 xfailed**, up from 1304 by 42: 23 for the prediction frame and 19 for the reading record. **Golden set: nineteen lines**, zero diff on one run at session start, its stderr the pinned rebalance failure alone. **Runner 15/16 once**, at session start: 4.2, 4.5 and 4.6 PASS, 4.1 BLOCKED at PHI-2.1 for FY2021, the reason line naming D36. **The runner now has eighteen cases and has not been run in full since**: 4.4 and 4.3 were each run alone, both BLOCKED, 4.4 at clarification_needed and 4.3 at out_of_scope. **The CLI once**, the allocation question. **No EDGAR fetch and no price fetch**: every request hit its interval; the golden set's regime line rewrote the macro rows, as it does on every run. **The shape of the research agent is taken, decisions 59, 60, 61, 62, 66 and 67; nothing of it is in the graph and no model is called. Order 4 is not done: what is built is the reference, the two checks and two pure modules. Left: the document store and the sectioner, the reader's model call, the research node, the routing for 4.4, then the gate and 4.3, then the full test before anything of Order 5.**

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Sections whose claims were checked again this session and
still hold are kept word for word; the rest is rewritten. Misses of my own
this session, caught before or after landing: the brief named four tests
that pin the committed ledger and the measurement found seven, with one
the brief named staying green by design; the twenty-fourth session's
handoff said no loop wrote a row, and the macro rows were stamped by one;
seven replacements in `run_cases.py` went through a script where the
brief asks for the edit tool, said in the next message, and after saying
it would not happen again it did, twice, on this file's header block and
its sections 4 to 7, said in the message that showed the diff; a diff pasted
into a message carried one mistyped context line, corrected in the same
message from `git diff`; a commit was called the eighth when it was the
seventh, corrected in the next message from `git rev-list`; the shape's
first commit was to carry the outcome's truth table and the gate's stops,
and Part 15 left both to the next Part, since they hang on decisions not
taken; the shape put the migration before the frame, and the frame and
the reading record came first because they are pure and the migration
leaves the suite red until it is run; the brief's placeholders for the
date, the branch base and CLAUDE.md's count were unfilled again.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the bridge, the SIC code, the philosophy check node, the metric keys, the valuation range, prediction scoring, and, this session, **the research agent's shape, its reference, its two checks and two pure modules**. Left in Order 4: the rest of the research agent (4.4 first, then the gate and 4.3), then the full test. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. Level 4: 4.2, 4.5 and 4.6 pass, 4.1 blocked by decision, 4.3 and 4.4 blocked on a capability that does not exist (six dated status notes under Level 4). n/18 since 18 September, the "n/14" sentence carrying its dated notes. Part 2 and the 3.2 row are untouched: their rewrite is at the commit that makes 4.3 answerable. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Eighteen cases. **New this session: `check_4_4` and `check_4_3` with `blocked_on_research` and `blocked_on_recommendation`**, written before any capability; they hold `shared_data["research"]` and `shared_data["gate"]` to Part 15 and to watchlist.toml, read with the runner's own parser, and their docstrings say what they cannot see. `check_4_3` holds one invariant of the outcome and not decision 68's rule. `check_4_5` reads watchlist.toml itself; `check_4_2` asserts structure only. 4.1's reason line names D36 until Alphabet's FY2027 report. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. 129 lines start `**Trigger:**`, 92 reading something other than "none", counted by `grep -c '^\*\*Trigger:\*\*'`; the last handoff's 117 and 80 were that count. New this session: twelve entries, none resolved (§4). **The next session of Order 4 reads "The shape of the research agent: decisions 59 to 69" first.** |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, Parts 1 to 15. **New this session: Part 15**, the reading record and a prediction the system proposes, D47 to D50, rules over text and closed sets and one division, the frame for W-1 on Alphabet's filed FY2025 lines; a dated note on Part 11 E. D46 is unused: Part 11's D38 writes "D46" for pending decision 46. The gate's check and 4.3's outcome are the next Part's. Never update it to match code output. |
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
  reading is a record and never the document. The section's text is an
  argument to `reading.record` and is not in what it returns; a quote is
  at most 300 characters and a section's reading at most twelve claims, so
  the quoted text is bounded at 3,600 characters a section. The ledger's
  form from last session stands: one reported figure for a due figure
  prediction, the way a finding carries `observed`, and nothing else.
- **No number from a model.** A claim's sentence carries no digit and a
  figure appears only inside a quote held to the stored section; a
  proposal on an assumption of mine is a direction from a closed set; a
  proposed prediction's threshold, period, dates, id and sentence are the
  pipeline's, and a `value` from the model is refused.
- **Policy lives in config, not code.** The predictions are the
  watchlist's rows, read by the loader; the score is written into the
  ledger by hand and read out as written. The scorer takes the metric's
  vocabulary from the formulas it can compute (D42) and the loader takes
  any metric name, so the vocabulary lives once.
- **Two policies, two questions; three now.** A question naming one
  company is research; a question about the predictions names none and is
  the ledger (decision 58). The registry says so and the golden line pins it.
- **Raise, do not repair.** This session's form: one claim that fails
  refuses the whole reading, and a failed claim is never dropped with the
  rest kept; a proposal that stops stops the rest, and no other metric is
  tried; the gate, when it exists, raises on each blank of the candidate's
  row, naming it, since a gate that checked the concentration clauses
  alone would call a weight clear while the purchase deepened the Equity
  breach the portfolio check already reports. Last session's form stands:
  a prediction whose period
  is not filed is due and unscored with that reason, never wrong; a metric
  with no formula stops naming it; a written score dated before its due
  date does not load; a written score that disagrees with the filing is
  reported beside it, and the answer says they differ; a ticker the file
  lacks is the node's error, as it is for the screen.
- **References before code.** Part 15 before the frame and the reading
  record; each check before its capability, exercised offline on a
  passing block and on broken ones and then sighted BLOCKED; every test
  seen failing without the module and against a wrong version with
  bytecode off, one wrong version per rule the row catches. A Part covers
  what is decided and built against now: the gate's check and 4.3's
  outcome wait for their decisions and their own Part.
- **The score is mine, and so is a row.** The system computes the filing's
  verdict and writes it nowhere; it proposes a prediction, prints the row
  and the sentence, and writes neither file. WATCHLIST.md and
  watchlist.toml are written by hand.
- **A recommendation exists only with both checks attached.** The model's
  judgement is a view of the thesis from a closed set and never "buy"; the
  outcome is computed in the node from the screen, my entry condition, the
  gate and that view; neither the formatter nor the model decides it.
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
  This session's shape covered the reading tool's contract, a model's
  proposal against an assumption of mine, the gate's seat and what the
  candidate's row lacks, a prediction the system writes and who enters it,
  the two checks, 3.2's rewrite, the routing, the model for the reading,
  the order of commits and the decisions it opens, and was taken with one
  yes. Where a choice put a number in a model's hands, a judgement in the
  formatter's mouth, or a recommendation without both checks, it was said
  and rejected.
- **The check first, seen BLOCKED**; the Part before the scorer; the
  loader before the scorer that imports it; the scorer before the node;
  the node unbound before the rendering; the rendering unwired before the
  routing row, since the roster check ties a name to a node and the
  synthesizer check ties an intent to a formatter; the golden line at its
  sighted baseline before the routing commit; expected.txt after two runs,
  its own commit.
- **A paid loop says first what it will fetch and store.** Said before
  the golden set and the runner: no price, no filing, the macro rows
  rewritten. Each sighting asked for on its own.
- **A claim in a brief is measured before it is written down.** The
  carried entry named four tests; a scratch copy of the tree with one
  score in its ledger found seven, and one of the four green by design.
- **A check is exercised offline before it is sighted.** A hand-built
  passing block and one broken block per rule, from a scratch script that
  is not committed: seventeen for 4.4, sixteen for 4.3.
- **A new case is sighted with `--case` alone before its golden line is
  written**: 4.4 at clarification_needed with no prediction made, 4.3 at
  out_of_scope as predicted from the pinned golden line.
- **The first live record is read against the reference before it is
  believed.** None this session; the first live reading is read by hand
  against the 10-K.
- **Grep the caller, not the registration.** `predictions.ledger` has one
  caller, the ledger node; `watchlist.predictions` one, the same;
  `fundamentals.READS` one, the scorer; `predictions.reported_figure`
  two, `verdict` and `proposals.frame`; `proposals.frame` and
  `reading.record` none outside their tests.
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
carry. **No number, threshold or weight from a model; no second range
from a model's growth pair; no row written into the watchlist by the
system; no outcome decided by the formatter or the model; no gate that
checks the concentration clauses alone; no section truncated to fit and no
failed claim dropped to keep the rest.** **No score written into the ledger by the system; no partial credit
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

**1346 passed, 6 xfailed, 35 warnings, about 4 seconds.** Run at session
start (1304) and after every commit. Red only on a scratch copy of the
tree, never in the repository: the suite with one score written into the
copy's ledger (7 failed), and the two new test files without their module
and against each deliberately wrong version (§4).

**Golden set: nineteen lines, one pinned failure** ("Should I rebalance my
portfolio?", errors 1). One run this session, at its start: zero diff, its
stderr the pinned rebalance failure alone. **Runner 15/16** once, at
session start, on sixteen cases: 4.5 PASS, 4.2 PASS, 4.6 PASS, 4.1
BLOCKED, the reason line naming D36. **Eighteen cases since, not run in
full**: `--case 4.4` and `--case 4.3` once each, both BLOCKED. A full run
should print 15/18 with three blocked, and nobody has seen it.

**The CLI, once.** The allocation question at session start, as the
runner's 1.1 expects: priced as of 2026-09-17, total 409,524.00 USD,
Equity 69.63%, the five lines summing to the total.

**Level 4: 3 of 6 cases pass (4.2, 4.5, 4.6); 4.1 blocked by decision; 4.3
and 4.4 have their checks and are blocked, nothing beneath them in the
graph.** Read n/18 as a count of well-formed answers and never as
the system being good at research (benchmark.md), never as the range being
right, and never as a prediction having been scored: none is due before
February 2027.

### Branches and tags

`baseline-v1` is the trunk; sessions branch from its tip and merge back
`--ff-only` when the loops are green. **The trunk is at 264aa7a and has
not merged `score`.** `research` is this session's branch, cut at 0e1c1ad,
`score`'s tip, on the owner's yes, since the branch the brief named did
not exist and the trunk had not moved; `research` contains `score`, so
merging `research` brings in both sessions. `score` is the twenty-fourth
session's branch, from 264aa7a. `publish`, `range`, `keys`, `node`, `filer`, `bridge`,
`consolidate`, `selection`, `compliance` and `vocabulary` are merged and
older. `wip/phase7-snapshot` holds rejected Compliance/IPS code.
`wip/rag-early` and tag `rag-early-parked` hold the RAG code.
`quant-inventory-parked` at 8d87455 holds the tree before the seventeenth
session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`e289a03682f2`**, 25 migrations, linear, all applied. No migration and no
reseed this session. **No price row and no filed row was written this
session; the macro rows were rewritten**: the golden set's line on the
market regime runs the macro agent, whose update has no interval, so
every golden run upserts thirty days of VIX and the yields, the count
standing at 206 while `created_at` moves (14:55 UTC on the 18th). The
last handoff's "no row written by any loop" was wrong on this table
(KNOWN_GAPS, the regime line entry). **The paid
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
since it depends on the price. **Since this session the lookup of a
reported figure is its own function, `reported_figure`**, returning the
figure, a Decimal for a field and a float for a metric key, and the one
filing it came from; `verdict` calls it and compares. No message changed.

### The research agent, as it stands

**Nothing in the graph, no node, no intent row, no model call.** What
exists is the reference, two checks and two pure modules:

| Piece | Where | Held by |
|---|---|---|
| The reading record: the filing, the section, one to twelve claims, each a sentence with no digit, a quote of at most 300 characters held to the stored section after whitespace collapses, an uncertainty `stated` or `inferred`; the record numbers the claims (`7.1`, `1A.3`); one failed claim refuses the whole reading | `portfolio_tool/reading.py`, `record(filing, section, text, supplied)` | `tests/test_reading.py`, 19, to Part 15 A; its vocabularies held equal to the runner's |
| The prediction frame: the model supplies kind, metric and bound or an event, and reasons; the pipeline the period, the dates, the threshold through `reported_figure`, a ratio cut to four places toward the side that holds, the next free id, the sentence; any other key from the model is refused | `portfolio_tool/proposals.py`, `frame(supplied, candidate, block, as_of, claim_ids)` | `tests/test_proposals.py`, 23, to Part 15 C and D, over Part 14 B's block |
| `check_4_4`, `check_4_3` and their probes | `tests/benchmark/run_cases.py` | an offline exercise from a scratch script, not committed; pytest sees only that the module imports |

Not built: the fourth EDGAR request for a filing's primary document; the
tables for the text and the readings, a migration; the sectioner; the
model call behind a seam a test can stand in for; the node; the
rendering; the extraction rule for `asks`; the routing; the gate. Part 15
F9, a proposal the ledger already carries, has no code: the loader reads
no `author`. Sentences exist for revenue and gross margin only, the two
metrics Part 15 C has rows for.

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
  the block's shape is defined, thirteen fields since the twenty-fourth session, and
  carries `READS`, the fields each formula reads; **`predictions.py`
  imports `fundamentals.METRICS`, `READS`, `metrics_by_year` and
  `watchlist.Prediction`, `Score`**; **`agents/nodes.py` imports
  `predictions.ledger`, `status` and `watchlist.predictions` inside the
  ledger node**, so the loader is before the scorer and the scorer before
  the node in any commit order. **`proposals.py` imports
  `predictions.reported_figure`, `SCORABLE` and `PredictionError`,
  `fundamentals.METRICS` and `years_filed_by`, and `watchlist.Candidate`;
  `reading.py` imports nothing of the repository's.**
- **`tests/test_proposals.py` imports the block from `test_predictions.py`**
  and builds its own candidate, so it does not pin the committed ledger;
  **`tests/test_reading.py` imports `run_cases`** to hold the module's
  vocabularies equal to the runner's repeated ones.
- **The macro update has no interval**: any run of the macro agent, the
  golden set's first line among them, asks the price provider and upserts
  `macro_data`.
- **A scratch copy of the tree runs the suite against a changed file
  without touching the repository**: `rsync` `src`, `tests` and `docs`,
  copy the four toml files, `pyproject.toml` and `data/portfolio.db` into
  a scratch directory, then from inside it
  `DATABASE_URL=sqlite:///<copy>/data/portfolio.db USE_MOCK_QUOTA=True PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 <repo>/.venv/bin/python -m pytest -q -p no:cacheprovider`.
  The control run on the unchanged copy read 1304, the repository's count.
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

## 4. What the twenty-fifth session did

`git log --oneline 0e1c1ad..HEAD`, ten commits with this file. The shape of
the research agent, cases 4.3 and 4.4, and the first of it that landed
cleanly: the reference, the two checks, two pure modules. Nothing reached
the graph.

**The loops, first.** The branch the brief named did not exist and the
trunk had not merged `score`; `research` was cut at 0e1c1ad on the owner's
yes. pytest 1304, the CLI on the allocation question as expected. Before
the paid loops, what each would fetch was read off the store and said: no
price before 22:54 UTC, no filing before 22 September, the macro rows
rewritten by the regime line. Then, with a yes, the golden set with stderr
kept, zero diff on nineteen lines, and the runner, 15/16, 4.1 BLOCKED at
PHI-2.1 for FY2021 naming D36, one after the other. The store's counts
were the same before and after; `macro_data` stood at 206 with its stamps
moved.

**The carried item.**
- **0d95e04** KNOWN_GAPS, trigger "the first score I write into
  watchlist.toml". The brief named the loader's committed-file test, the
  ledger node's today test and the formatter's committed-ledger tests. The
  claim was measured: the suite over a scratch copy of the tree with one
  score under W-2.1 went from 1304 passed to 7 failed. Seven, not four:
  the scorer's three-dates test, three rows, and the node's
  published-under-the-agent test were not in the brief; two of the
  formatter's three committed-ledger tests stay green, correctly, one of
  them the runner's check over the ledger as it is. And
  `tests/test_watchlist.py` stays green with a score in the config that
  the document lacks: nothing holds a score in one file to the other. The
  entry says what each test should pin on that day.

**The shape**, one yes: what a reading returns and refuses, over the
latest 10-K's Items 1, 1A and 7; a model's proposal as a direction and
never a number, and a proposed number refused; the gate as a graph node
on the edge into the synthesizer, keyed on the judgement record, at a
weight I state, raising on the candidate's blanks; the model's judgement
a view of the thesis and the outcome computed in the node from four
inputs; a prediction the system proposes, the model choosing what to test
and the pipeline every number, entered by me; what the two checks assert
and cannot see; one intent with `asks` set by extraction; 4.4's path
first and "should I buy" opened only when the gate can check; 3.2's
rewrite and Part 2 at that commit; the stronger model already in
`agents/config.py` for the reading; the order of commits; the rejected
alternatives; decisions 59 to 68.

**Under the yes, in order.**
- **54aee38** Part 15, D47 to D50: the reading record on a stand-in
  section, R-1 to R-7; a proposal on an assumption, V-1 to V-7; the frame
  for W-1 as of 2026-09-18, P-1 to P-4, gross margin 240,301 over 402,836
  cut to 0.5965 for "at least" and 0.5966 for "at most", revenue
  402,836,000,000 to the unit, due 2027-09-18; F1 to F10. Numbers the
  shape had not stated and the diff did: the 300-character and
  twelve-claim caps, the four decimal places and the side the cut goes,
  29 February to 28 February. The outcome's truth table and the gate's
  stops, which the shape put in this commit, were left to the next Part.
  A dated note on Part 11 E.
- **be7152c** `check_4_4` and `blocked_on_research`; seventeen cases.
  Exercised offline first: a passing block from P-1 and seventeen broken
  ones, each failing on its fault. Sighted BLOCKED on `--case 4.4` alone:
  clarification_needed, plan empty, the model's own clarification; no
  prediction was made.
- **8dd5861** `check_4_3` and `blocked_on_recommendation`; eighteen cases;
  what the two checks share moved into `_research_invariants`. It holds
  what is decided and, of the outcome, one invariant: an entry is
  supported only with the screen clear, the gate clear and my entry
  condition met. Offline: a passing state, sixteen broken ones, and a
  "not now" state that passes. Sighted BLOCKED on `--case 4.3` alone:
  out_of_scope, plan empty, as predicted.
- **55ca52e** `predictions.reported_figure`, the lookup out of `verdict`,
  so that a proposed threshold is the figure the scorer will compare
  against, through one path. pytest unchanged at 1304, bytecode off.
- **90230e9** `portfolio_tool/proposals.py`, the frame, pure, 23 tests to
  Part 15 C and D; seen failing without the module (23 errors) and, on a
  scratch copy with bytecode off, against a version rounding a ratio to
  nearest (P-2 and the equal-year row), one cutting revenue to the
  billion (P-3 and F3) and one taking keys the model may not supply (the
  four F1 rows).
- **3c0b5df** `portfolio_tool/reading.py`, the record's validation, pure,
  19 tests to Part 15 A; seen failing without the module (19 errors) and
  against a version dropping a failed claim and keeping the rest (R-4 and
  the whole-reading row), one normalising case (R-6), one not collapsing
  whitespace (four rows) and one with the cap off by one. Beyond the
  Part: the record numbers the claims itself and keeps the quote
  collapsed to single spaces.
- **0f0de9b** the record: eleven entries, none resolved, the header.
- **38d50f4** benchmark.md's status note and the count's dated note.

**Not done, on purpose.** Anything that touches the outside: the
migration, the fourth EDGAR request, the sectioner, the model call; the
node, the rendering, the golden line for 4.4, the extraction rule, the
routing; the gate and everything of 4.3 beyond its check. Decisions 51,
52 and 54, the seven emoji headers, the philosophy topic lookup, the CIK
confirmation, the currency on the range, the close and the reported
figure, formulas for `operating_margin` and `free_cash_flow`: all outside
the brief. No full run of the eighteen cases.

---

## 5. Decisions taken, and decisions pending

**Taken this session**, with the shape's yes (KNOWN_GAPS, "The shape of
the research agent: decisions 59 to 69", has each with its rejected
alternatives).
- **59**: a model's proposal on an assumption of mine is a direction from
  a closed set, never a number; the range is computed from my five
  numbers only. Closes Part 11 E's open item (Part 15 D48).
- **60**: a prediction the system proposes: the model chooses what to
  test, the pipeline supplies every number, the threshold the last filed
  year's figure (D49).
- **61**: I enter it by hand, the row marked `author = "system"`; the
  system writes neither file (D50). The sentence on authorship in
  `docs/WATCHLIST.md` waits for my word.
- **62**: the gate is a graph node on the one edge into the synthesizer,
  keyed on the judgement record, not a plan step.
- **66**: one intent, `research`; `asks`, set by extraction from closed
  patterns, is a discriminator row whose terminal is the research agent.
- **67**: the reading and the judgement run on the stronger model already
  named in `agents/config.py`, a second constant beside the active one;
  the answer says "the model's reading" and the record keeps the id.
- 56, 57 and 58 were taken in earlier sessions.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve. **Sixteen by count**: the eleven the session started
with, none closed, and five opened. CLAUDE.md's line still reads "10 on 17
September, 12 with 56 and 57 numbered" and is the owner's to reconcile.
The cap is 25.

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
    Trigger: the full test at the end of Order 4. The macro upsert on
    every golden run is one more fact for it.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields: delete, its
    own sitting.
63. Where a candidate's asset class, sector and instrument type are
    stated. The gate raises on each blank until then.
64. How a candidate's purchase is funded in the gate's check: from cash,
    from new money, from a sale. IPS-5.2 leaves it undecided.
65. Where the weight is stated. Recommended: the watchlist entry, by me;
    a weight in a research question is refused by the validator today.
68. The rule that composes 4.3's outcome from the screen, my entry
    condition, the gate and the model's view of the thesis. Its truth
    table is mine to read in the next Part; `check_4_3` holds one
    invariant of it and no more.
69. Whether 4.3 passes on a prediction proposed and not entered, which
    `check_4_3` accepts today, or only on one I have entered.

- **The full test at the end of Order 4** (owner's, unchanged): when Order
  4's last commit lands, the project stops for a full test across both
  halves before Order 5. Not this session: the research agent is not in
  the graph.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12. Level 4: 4.2, 4.5 and 4.6 PASS; 4.1 BLOCKED by
decision, the runner's reason line saying why; 4.3 and 4.4 BLOCKED on a
capability that does not exist, each with its check written and
exercised. The last full run was 15/16, before the two cases were added;
n/18 has not been printed by a full run. The ledger has four open
predictions and no scored one, and the first due date is 1 February 2027.
n/18 is a count of well-formed answers. What the runner cannot see:
whether the range's ends are right (Part 11 C in pytest); whether a
filing's verdict is right (Part 14 C in pytest); any due prediction until
2027; and, once 4.4 answers, whether a summary is faithful to its quote,
which nothing holds.

---

## 7. Next steps, in order

**1. The rest of the research agent, 4.4's path first.** Read KNOWN_GAPS,
"The shape of the research agent: decisions 59 to 69". Then, each with its
tests seen failing twice: the migration for the document and the readings
tables, committed unexecuted with its schema test, run by the owner; the
fourth EDGAR request, asked for before it is made, and the store; the
sectioner, designed against Alphabet's real 10-K and measured over all of
it; the reader, the model behind a function a test can stand in for, its
output through `reading.record`, cached per accession, section, model and
prompt version, the prompt never carrying the question; the research
node, unbound; the rendering, unwired, through `check_4_4`; the golden
line for 4.4 at its sighted baseline, clarification_needed; the
extraction rule for `asks`; the routing commit for `thesis` with its
prediction, two golden runs; the runner; the first live reading read by
hand against the 10-K before it is believed.

**2. The gate and 4.3**, after decisions 63, 64, 65, 68 and 69: the Part
that computes a candidate at a stated weight by hand, with the outcome's
truth table; the gate node and the test that no outcome prints without
its block; the registry's two sentences and the Siemens few-shot, a
prompt hypothesis; 3.2 rewritten to a price forecast and the out-of-scope
paragraph at that commit, Part 2 of benchmark.md in the next.

**At the end of Order 4: the full test** (§5), before Order 5.

### Later, with reasons

- **The trunk.** `git switch baseline-v1 && git merge --ff-only research`
  brings in the twenty-fourth and the twenty-fifth sessions.
- **A full run of the eighteen cases**, expected 15/18 with three
  blocked; it costs eighteen calls and was not asked for.
- **The first score I write**: seven tests go red by design, and the
  document test does not see a score the document lacks (KNOWN_GAPS).
- **The loader's `author`**, with my sentence in WATCHLIST.md, before the
  first system prediction is entered; Part 15 F9 comes with it.
- **1 February 2027**: W-2.1 and W-2.2 fall due. The first ledger question
  on or after it fetches Adobe's submissions document and facts live, a
  session saying so first; the first live due record is read by hand
  against Adobe's 10-K before it is believed (KNOWN_GAPS, four entries).
- The currency on the range, the close and the reported figure, when a
  case asks (KNOWN_GAPS); a proposed revenue sentence carries no currency
  word for the same reason.
- The formatter headers carrying an emoji, seven in `nodes.py`. One commit,
  the runner run against it. Work, not a decision.
- CLAUDE.md, the owner's to change: the pending list line, sixteen on 18
  September; "Sixteen queries" for the golden set, which has nineteen
  lines; the golden command's `2>/tmp/golden_err.txt` in place of
  `2>/dev/null`.
- Three stale statements, mine to fix on my word: `watchlist.toml`'s
  header and `test_watchlist.py`'s docstring, "read by nothing yet"; Part
  11 D38's "D46".
- A philosophy topic lookup: a discriminator row on `research`, when a case asks.
- The node does not confirm the resolved CIK's submissions document lists
  the ticker asked (KNOWN_GAPS, the tickers entry).
- Decisions 51, 52 and 54, each its own sitting.
- The registry text naming VaR, drawdown and risk parity: a prompt change,
  prediction first, two golden runs.
- `operating_margin` and `free_cash_flow` get formulas, and
  `return_on_invested_capital` its tax rate on the ledger node, when a
  prediction names one (KNOWN_GAPS).
- The seven-day cache runs out on 22 and 23 September; the price cache ran
  out at 22:54 UTC on the 18th; the next paid run after either fetches,
  and says so first.

---

## 8. Rules learned the hard way

**A brief's list is a claim, and a claim is measured.** The brief named
four tests that pin the committed ledger. A scratch copy of the tree with
one score in its ledger found seven, one of the four green by design, and
a document test that does not see a score the document lacks. The entry
records the measurement, not the brief.

**A test over a committed file that changes by design has an expiry
date.** Seven tests read the committed watchlist as none scored. The
frame's tests build their candidate and the reading's tests type their
section, so neither goes red on the day the ledger changes.

**A threshold compared strictly is the value its sentence says.** The
scorer compares unrounded, so a gross margin threshold of 0.59652315 under
a sentence saying 59.65% would score a year at 59.651% two ways. The
value is cut to four places toward the side that makes a year equal to
the last one right, down for "at least" and up for "at most", and a test
scores an equal year through the scorer itself.

**A check holds what is decided, and of what is not, the one thing no
decision could break.** `check_4_3` was written with decision 68 open: it
asserts that an entry is supported only with both checks clear and my
entry condition met, and names the undecided rule by its number.

**A Part covers what is built against now.** The shape put the outcome's
truth table and the gate's stops into Part 15; they hang on four pending
decisions and nothing built this session reads them, so they wait for
their own Part, and the message said so.

**"Nothing fetched" is read off the store, table by table.** No price and
no filing moved; the macro rows did, on a line of the golden set nobody
thinks of as a fetch. The last handoff's sentence was wrong on one table.

**A promise about a tool is kept, or the next message says it was not.**
A batch of replacements went through a script, was owned, and the promise
to use the edit tool was then broken twice on this file. Each time it was
said in the message that showed the diff. The rule is not the tool; it is
that the owner is never left to find out.

**A count in a message is counted.** A commit was called the eighth when
`git rev-list --count` said seven.

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
python tests/benchmark/run_cases.py --case 4.4

python src/agents/cli.py --portfolio 3        # :q to quit
printf 'How have my predictions done?\n:q\n' | python src/agents/cli.py --portfolio 3

grep -rn "SymbolName" src/ tests/ --include='*.py'
git status --short

# this session's commits: count from the branch's base, 0e1c1ad. The
# merge-base with the trunk is 264aa7a while the trunk has not merged
# score, and counts the twenty-fourth session's commits too.
git log --oneline 0e1c1ad..HEAD
git rev-list --count 0e1c1ad..HEAD

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

# merge and push, by the owner only; research contains score:
git switch baseline-v1 && git merge --ff-only research
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~4s, no model calls | Do the components still work; does every reference Part reproduce, Part 11 on typed blocks and the node's assembly, Part 14 on the typed block and the fixture's rows, Part 15 A on the stand-in section and C and D on Part 14 B's block; does each node fetch in order and publish its block; does each rendering pass the runner's check; are the candidate's stored closes the print |
| CLI | ~3s, one call | What it is actually doing: the plan, the parameters, the reasoning line, the answer text |
| Golden set | ~90s, cents, **writes filed and price rows past their intervals, and the macro rows on every run** | Did routing change anywhere (nineteen lines, one pinned failure). Blind to parameters and answer text; stderr kept to a file |
| Benchmark runner | ~2min, cents, **writes filed and price rows past their intervals** | How many cases pass, n/18. Blind to the four intents outside the roster, to whether a range's ends are right, to any due prediction until 2027, and, for 4.3 and 4.4, to everything their docstrings list: a quote's presence in the filing, a summary's faithfulness, the outcome's rule |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once.
