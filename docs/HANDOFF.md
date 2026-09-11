# AGENTIC_FINANCE — Session Handoff

**Session date:** 11 September 2026 (fourteenth session, begun 10 September; regenerated at its end)
**Branch:** `selection`. `baseline-v1` is at 191829b and pushed; forty-four commits since, this file included, not pushed, deliberately.
**State:** Green on every loop. pytest 735 passed and 6 expected failures in about three seconds. The runner ran once this session, 12/12, and the golden set once, zero diff, both before the first change that will touch routing; neither has run since, because nothing under `src/` changed an answer or a route after them. Commit count: `git rev-list --count baseline-v1..HEAD`.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** The thirteenth session's handoff said `financial_statements`
held 102 rows; it held 65, the item 21 delete having removed 37 after the
paragraph was written. Grep for the caller, not the registration; read the
plan table before choosing who publishes a value; and check a shape against
DIRECTION.md's invariants, not only against the pattern used all day. This
session I brought a directory of invented company figures as a runtime
source, by analogy to the synthetic policy files, and the owner caught it
before I did; the commit and its reversal are both in the history and the
entry is under Directions in KNOWN_GAPS.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the philosophy check exists as pure modules held to Part 10; the filings reader is the next decision, then the node that answers cases 4.1 and 4.6. Its last section says when to stop and think. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass on this session's run. **Level 4, added this session**: six research cases, none running yet, the prediction ledger as their eval set, and the rule for when 3.2 expires. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Twelve cases; the Level 4 checks are written first when the node decision starts, blocked probes and all, and the headline becomes n/14. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Swept at the end of this session. Read at minimum, under Directions: "Order 3", "Order 4, the philosophy check" (the three questions left inside the node decision), and "The judgement half's figures come from a reader, never a file"; under Hygiene: "A question about the philosophy runs the IPS check" and the prompt batch. |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1 to 9, and since this session **Part 10, the philosophy check** on synthetic figures for the watchlist's first candidate, with decisions D21 to D25. Never update it to match code output. The workbook has a `Philosophy` sheet with the same formulas and has not been opened in Excel since, so its cached values are absent until it is. |
| `docs/IPS.md` | The policy, synthetic. `ips.toml` is derived from it and named on portfolio 3's row. Not edited casually. |
| `docs/PHILOSOPHY.md` | **New.** What is worth wanting, synthetic, first person, the IPS pattern: seventeen `PHI-x.y` clauses, five numeric screens and twelve statements; `philosophy.toml` derived and held to it. Not yet bound to anything; the committed file by path until Order 6 decides what a philosophy belongs to. |
| `docs/WATCHLIST.md` | **New.** Two synthetic candidates, Alphabet and Adobe, each a thesis, an entry condition, and its predictions; the predictions across the file are the prediction ledger, four of them, due in early 2027. `watchlist.toml` derived and held to it. Nothing reads it. |
| `docs/PM-Assistant — Roadmap.md` | Stale, header lists what is superseded. DIRECTION.md's Order supersedes its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.16% v 12%, JNJ 10.05% v 10% at the 09-04 closes); the runner asserts structure. This session's batch reported seven breaches against Part 7's eight, JNJ at 9.87% on the other side of its limit.

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public; the README is the short one from ab813ed). The push URL of `origin` is set to `no_push`.
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half (positions, allocation,
P&L, risk, compliance) that is tools and done, and a judgement half
(research, valuation, a thesis, a prediction) whose first tool now exists as
pure modules. The router is scaffolding until the tool layer is complete.
**No deadline. Correctness over speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** Tools return summaries; raw
  arrays move through `shared_data`.
- **Policy lives in config, not code.** `ips.toml` and `philosophy.toml`
  hold every number of the two synthetic policies; `config.toml` every
  fetch interval; a missing file raises. The vocabularies are registries:
  `AGENTS`, `INTENTS`, `REQUIRES`, `TERMINAL` in `schemas.py`; the period
  keys in `config.py`; the clause types in `ips.py` and `philosophy.py`
  over one loader, `clauses.py`; the metric keys in
  `quant/fundamentals.METRICS`. An agent computes; the synthesizer
  formats; a checker reads published figures and subtracts once.
- **Two policies, two questions.** The IPS says what may be held and how
  much; the philosophy says what is worth wanting. A company clears the
  philosophy before the IPS sizes it; neither overrides the other.
- **The policy belongs to the portfolio.** `portfolios.ips_path` names the
  file; no portfolio is no policy. What a philosophy belongs to is not
  decided (pending 30).
- **Raise, do not repair.** A span the vocabulary lacks, a typo of a
  holding, a missing rate, a holding with no currency, a clause with an
  unknown type, a metric key nothing computes, a figure a year lacks, a
  year not yet filed: the pipeline stops and says why. A default is a
  wrong answer with a plausible face.
- **Typed facts are not a source.** A synthetic policy is an honest
  stand-in because the policy is the owner's to state. A company's figures
  are facts; typed ones live in tests as references and never in a file
  the system reads to answer (this session's reversal).
- **Holdings derive from the ledger (D13); a rate is a price source (D17);
  a close is the print (D19); every figure names its currency (D18); every
  row names its source, and now every table's source column is NOT NULL.**
- **Extraction and derivation before the model.** Tickers, periods,
  percentages and the compliance mode are read from the message; the plan
  is derived. The model decides intent, `measure`, `group_by`, `status`,
  confidence and a clarification question.
- **References before code.** Part 7 before the checker; Part 8 before the
  ledger; Part 9 before the provider changed; **Part 10 before the
  screen**, this session, with the metrics' formulas written out as the
  definition of each metric key (D24).
- **No price forecasts as numbers.** A prediction is about the business
  with a date; a valuation is a range from stated assumptions.
  `test_philosophy.py` and `test_watchlist.py` hold the documents to it.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what each rule means, what changes on a yes, the rejected alternatives,
  which loop sees it and what it will show. Then one commit per layer,
  tests written first and seen failing, `git status --short` and the diff
  read before each commit, and the word yes before it lands; "okay" is not
  one.
- **Check a shape against the invariants before bringing it.** The
  pattern used all day is not the rule; DIRECTION.md's eight invariants
  are, and they take a minute to reread.
- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting any
  symbol; grep for the caller and for the reader; read the plan table
  before choosing a publisher.
- **A prompt change is a hypothesis.** Line-by-line prediction in the
  commit message before the run; golden twice; stop after the second
  failed prediction on a line. No prompt changed this session; the next
  decision changes one.
- Never `commit -a`/`-am`, never `add -A`/`.`; name the files. Never
  rebase, amend, reset, stash; a wrong turn is taken back by a new
  commit that says why. Never edit `.gitignore`. A modified tracked binary
  is its own commit.
- **The migration, the reseed and any rewrite of stored rows are run by
  hand** from the project root; the migration is committed unexecuted,
  the schema test before it is the check, and it is applied and reverted
  on a scratch copy first with the schema read back each way. **I paste
  what the command printed, not "done."** This session: one migration,
  one upgrade line pasted, the column read back NOT NULL.
- **A test written against data that is already right has not been seen
  failing.** Break the one thing on a scratch copy and run it there. This
  session: a nulled macro source, an altered clause text, a due date
  before its made-on date, a price metric on a prediction.
- **The workbook is closed in Excel before any openpyxl write**, `lsof`
  first; the nine older sheets are compared cell for cell after.
- A count I predict is a count I add up. No emoji in code; two formatter
  headers still carry one (KNOWN_GAPS, Hygiene).

### What I do NOT want

A pure asyncio/regex deterministic version without LangGraph. Prompt rules
added to fix a routing defect (DIRECTION.md). My real portfolio's data in
the repo: Order 6, last. No more concurrency until independent tools exist.
No cached holdings table; no currency symbol table; no fallback rate,
currency or policy; no adjusted close in the price table; no environment
switch for which policy runs. **No invented figures as a runtime source, and
no price a stock will reach anywhere in a document or an answer.** No
mutation testing until it is necessary.

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q

python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 2.2

python src/agents/cli.py --portfolio 3
```

**735 passed, 6 xfailed, 26 warnings, about three seconds.** Up from 645:
the philosophy document test (8), the watchlist test (6), the macro schema
test (8), the fundamentals test (22), the loader raise tests (30), the
screening test (16), and the philosophy test gaining one and losing one on
its move. The six expected failures are the statements-method pin, as
before.

**The golden set, sixteen queries on portfolio 3**, two pinned failures
(the macro query; "Should I rebalance my portfolio?"). Run once this
session before any routing change: zero diff. `expected.txt` unchanged
since 93290af.

**Runner 12/12** on this session's run, the first since the eleventh
session and three sessions of data changes: the as-traded refetch, the
ledger's date and fees columns, three required source columns, the policy
binding, the loader refactor. None moved a case.

**Level 4: 0 of 6 cases run.** No check exists for them yet; the node
decision writes the checks first.

### Branches and tags

`selection` is the working branch. `baseline-v1` sits at 191829b, pushed.
`vocabulary` and `compliance` are merged into `baseline-v1`.
`wip/phase7-snapshot` holds rejected Compliance/IPS code; nothing on it is
scheduled. `wip/rag-early` and tag `rag-early-parked` hold the deleted RAG
code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`87d3ec68c2ed`** (`macro_data.source` NOT NULL), 21 migrations, linear,
all applied; this session's one applied by the owner, output pasted,
schema read back. Tables that matter: `portfolios` (`currency` and
`ips_path` NOT NULL; row 3 names `ips.toml`), `transactions`
(`portfolio_id`, `amount`, `date` a DATE, `fees`, all NOT NULL), `assets`
(9 rows), `daily_prices` (6,939 rows, `source` NOT NULL, every close a
print held to the committed series by the suite), `fx_rates` and
`fx_fetch_metadata` (empty), `financial_statements` (`source` NOT NULL, 65
rows, untrusted), `macro_data` (**`source` NOT NULL since this session**,
185 rows, all `yfinance`). **There is no holdings table.** The watchlist,
the philosophy and the ledger are files, not tables.

- **Portfolio 3, "Benchmark Portfolio" — the only portfolio.** Nine ledger
  rows, one buy each, Part 8 A; cost basis 284,500 plus 15,500 cash; USD
  throughout; policy `ips.toml`.
- Reseeding rewrites the nine assets' metadata to the same values and
  refuses without `--reset`. No reseed this session and none needed.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py` | nothing yet; `screening.screen` takes it loaded |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py` | nothing yet |

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  (`claude-haiku-4-5-20251001`). `ANTHROPIC_SONNET` is `claude-sonnet-5`,
  behind `use_stronger_model`, off.
- **yfinance 1.7.0.** The price method passes `auto_adjust=False`.
- `openpyxl` in the venv and the `dev` extras. No LibreOffice. No mutation tool.
- `config.toml` is required and carries all four fetch intervals.
- `config.features.observability_enabled` is **false** here.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config`
  reads `DATABASE_URL` at import, so a scratch copy is named in the
  environment before any project import. **The whole suite on a migrated
  scratch copy**: `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True
  PYTHONPATH=src pytest -q --noconftest`.
- `alembic.ini` names the database by a relative path: `alembic upgrade
  head` runs from the project root. The alembic API with `sqlalchemy.url`
  overridden is how a migration runs on a scratch copy.
- **The clause loader** is `portfolio_tool/clauses.py`; `ips.py` and
  `philosophy.py` are thin specs over it (prefix, type table, parameter
  checks, error class). A relative document path anchors to the project
  root through `clauses.resolve_path`; `ips.resolve_ips_path` is the same
  function under its old name.
- **The screen's input** is a figures block: ticker, currency, source,
  fiscal years with `ends` and `filed` dates and reported figures by name,
  `shares_outstanding`, `price` and `valuation_range` with `as_of`. Its
  shape is `tests/test_fundamentals.py`'s fixture, Part 10 A typed. No
  tool publishes one yet.
- The CLI's quit command is `:q`.

---

## 4. What the fourteenth session did

`git log --oneline 4ca00b0..HEAD` for the list, in order.

**Order 3, three decisions, each a shape before its file (94ac112 to
67210aa).** The philosophy in the IPS pattern: two documents because they
change for different reasons and the compliance loader refuses a type it
cannot check; seventeen clauses, three types, first person, synthetic. Level
4 in benchmark.md: six cases, Part 3b's research lines, the ledger as the
eval set, 3.2's expiry rule. The watchlist with its ledger: a prediction
nested under its thesis, dated, about the business, figure or event, scored
all four fields or none, never a price; two candidates, four predictions
due in early 2027; the check record absent and saying so. Each document
held to its TOML by a test seen failing on an altered copy first.

**Item 25 (bd2d04a, ced6bee).** `macro_data.source` NOT NULL: schema test
first, model and migration 87d3ec68c2ed with no fill and a refusal on any
null row, applied and reverted on a scratch copy, then by the owner. The
last source column.

**Order 4, the philosophy check (c0b9d13 to 70c993a).** Part 10 by hand
with D21 to D25, D25 corrected before it was written from "that clause" to
"the whole check". The workbook's `Philosophy` sheet, then a `Filed` column
in both for D21. `clauses.py` extracted from `ips.py`, no behaviour change.
Then, test first each and in this order because the loader checks metric
keys against the metrics module: `quant/fundamentals.py` (Part 10 B and C,
D21's year selection, divisions by zero raise, blanks do not),
`philosophy.py`, `screening.py` (Part 10 D and E: worst year per bound,
strict comparison, the whole check stopping on a missing figure or a year
not yet filed, the margin of safety carrying both as-of dates).

**The runs, before any routing change.** Runner 12/12, golden zero diff,
and a fourteen-prompt batch read in full: nine as designed, four known
wrong faces standing, two new before-faces (KNOWN_GAPS, Hygiene).

**The wrong turn (19de4a5, reversed by f865bac).** Invented figures per
watchlist candidate as a runtime source, brought as a decision, one commit
landed, caught by the owner's question, taken back with the reason in the
commit and the entry under Directions.

**Mutation testing** brought as a decision and not run: only when
necessary, the owner's decision; it leaves §5.

**The sweep (75bcb62)**, then this file.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- The philosophy is a second clause document, not a section of the IPS;
  three types; metric keys are a closed vocabulary owned by the metrics
  module; first person.
- Level 4 is six cases scored on structure by the runner and on outcomes
  by the ledger; a judge model and price-based scoring rejected; 3.2
  expires at the first Order 4 commit that makes 4.3 answerable.
- The ledger lives on the watchlist, a prediction under its thesis; figure
  or event; no partial credit; never edited; never a price; the range is
  never typed into the file.
- Part 10 before the screen; D21 to D25; the screen after the metrics
  module, the metrics module before the loader.
- One clause loader for both documents.
- Invented figures are not a runtime source; a reader with a defended
  source comes before the node.
- The macro column is required, with no fill.
- Mutation testing only when necessary.

**Pending — decide before writing code.** Old numbers kept so that
KNOWN_GAPS references resolve; done items struck.
6. **The rebalance tools' fixed euro sign**: logged, not built.
9. Records and rules for the span and two-weights clarifications, when a case asks.
10. A window return as a measure with a reference.
11. Replace the two verbatim benchmark few-shots.
12. The hypothetical mode's instrument type ("11% into a new ETF"), seen again this session.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
14. "Optimization failed: None".
15. A golden line for 2.3.
16. Company names, German phrasings, the softer 3.5: decision 16's path.
17. `group_by` as the subject kind of a compliance finding, when a case asks.
18. Realized gains and closed positions.
22. Volatility over as-traded closes or a total-return series: a Part 4 decision.
23. The answer text naming the price source.
25. ~~`macro_data.source` NOT NULL~~ done (ced6bee, applied).
26. `get_financial_statements` returning nothing: with the reader decision, since the reader decides whether those tables are a source at all.
27. ~~Mutation testing~~ only when necessary; off this list.
28. **The filings reader, the next decision** (§7).
29. **The node for the screen**, after the reader: intent `research`, `ScreeningAgent` alone in its plan, the runner checks for 4.1 and 4.6 first, a golden line, golden twice. Inside it: which document the word "philosophy" routes to (today the IPS check, KNOWN_GAPS Hygiene).
30. **What a philosophy is bound to.** It is the investor's, not the portfolio's, so `ips_path`'s shape does not transfer. The committed file by path until Order 6; not a column invented now.
31. **The bank variant of 4.6.** PHI-3.2 is a statement and cannot decide "bank" without data on the figures block; a decision with the reader, which is where such data would come from.
32. **Two formatter headers carry an emoji**: an answer-text change, own commit, the runner sees it.
33. **The workbook's cached values**: absent since the openpyxl writes; return when the workbook is opened and saved in Excel.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12 on this session's run. Level 4: defined, six cases,
none with a check, none running; the ledger has four open predictions and
no scored one, so its score is 0 of 0 and stays so until early 2027.

---

## 7. Next steps, in order

**Decision 28, the filings reader, before any node.** Reported figures per
fiscal year for a company from a structured, free source (DIRECTION.md
names EDGAR; its company-facts data is filed figures with the fiscal
period and the filing date on each), published in the figures block's
shape with a source and a filed date on every figure, cached under the
price cache's rules, and defended the way Part 9 defended the closes: a
reference Part with a few rows fetched by the owner from a second source
by hand, to the dollar, before the provider method is trusted. Open inside
it: whether the existing `financial_statements` table is the store or a new
one is (26); how a fiscal year is labelled when the filer's year does not
end in December (the watchlist's second candidate does not); what the
block carries for a bank (31). Bring the shape, a recommendation and the
rejected alternatives; compute nothing until the owner says.

**Decision 29, the node**, after the reader: runner checks for 4.1 and 4.6
first, seen BLOCKED; the intent and agent in the registries with their
plan test; the node with a test over a synthetic state held to Part 10 D;
the formatter with its test; the golden line and the prompt, golden twice
with the prediction written first.

**Then the valuation pipeline** with Part 11 by hand, and prediction
scoring with its Part.

### Later, with reasons

- 3.2's rewrite and Part 2's boundary: at the commit that makes 4.3 answerable, not before.
- `measure`, `group_by` and `status` are the model's; whether they become extraction is a tool-boundary question.
- A total-return series for volatility (22): with a recomputed Part 4.
- More concurrency: when Order 4/5 has independent tools and a measurement asks.
- The inline `sqrt(w'Σw)` copies; the hot-potato violation in `price_data_json`.

---

## 8. Rules learned the hard way

**A shape is checked against the invariants, not against the day's
pattern.** Three synthetic documents in a row made "a synthetic file,
replaced later" feel like the rule. The rule is invariant 1, and it
distinguishes a policy the owner states from a fact the world provides. I
brought invented figures as a source; the owner asked whether that broke
a principle; it broke three. The check takes a minute and belongs before
the decision reaches the owner.

**A decision's wording is checked against the documents it cites before
it is written down.** D25 as brought said the check stops "on that
clause"; PHI-1.2 and case 4.6 say the whole check stops. Caught while
writing the reference, not after.

**A regex in a test asserts the message's order.** Two raise tests
failed on "EBITDA.*FY2025" because the module, like every other message
in it, puts the year first. The module was right; the test moved.

**Dependencies decide the order, not the list.** The loader holds metric
keys to the metrics module, so the metrics module came first, against the
order I had written down an hour earlier.

**Two statements of one source line are both right.** The typed
reference and a file both said where their figures came from, in
different words; the comparison excludes provenance and holds the cells.

**A count is added up, not recalled; a policy is per portfolio, not per
process; a raise is honest and a half-loaded policy is not; the output is
the record, not the word; a check on the most recent date passes in both
states; registration is not reachability; predict from the whole prompt;
a refusal is an honest failure; a fixture that passes in both states is
no check; read the plan table before choosing a publisher; a test against
data already right has not been seen failing — still true.** Earlier
handoffs' §8 have the examples.

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
git log --oneline baseline-v1..HEAD

# by hand, from the project root, after a migration or a seed change:
alembic upgrade head
python src/portfolio_tool/scripts/seed_portfolio.py --reset

# what the database says it is at (expected 87d3ec68c2ed):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# every source column required:
sqlite3 data/portfolio.db ".schema macro_data" | grep source

# the price table: nine assets, 6939 rows, one convention
sqlite3 data/portfolio.db "select count(*) from daily_prices; select count(*) from assets;"

# the whole suite on a migrated scratch copy, while a migration is pending:
DATABASE_URL="sqlite:///$PWD/scratch.db" USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest

# the three documents held to their config:
pytest -q tests/test_ips.py tests/test_philosophy.py tests/test_watchlist.py
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3s, no model calls | Do the components still work; does the ledger reproduce Part 8, the rate arithmetic Part 8 C, every stored close Part 9, the checker Part 7, **the metrics and the screen Part 10**; does the schema have the columns and not the defaults; is every document held to its config; does every table row derive its plan; does extraction read every recorded prompt the same way; does each formatter select what its parameters say |
| CLI | ~4s, one call | What it is actually doing: the plan, the parameters, the reasoning line, what was asked back, the answer's header, which policy file the compliance node loaded, whether the provider was called |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines or none, two pinned failures, `retries` when a plan was rejected). Blind to `measure`, `group_by`, `status`, `tickers`, the mode, the currencies and the policy file |
| Benchmark runner | ~1.5min, cents | How many cases pass; the only loop that sees the compliance mode, the second turn, a model-owned field set where it should not be, and the answers' text as a whole. Level 4's cases join it with decision 29 |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second
miss on a line. The runner is per capability commit, and per commit that
changes the answers' text.
