# AGENTIC_FINANCE — Session Handoff

**Session date:** 10 September 2026 (eleventh session; regenerated at its end)
**Branch:** `selection`, cut from `baseline-v1` at 7fc6474. `baseline-v1` was fast-forwarded to 665d033 at the start of this session and both were pushed there; twenty-seven commits since, this file included, not pushed.
**State:** Green on every loop I ran. pytest 572 in about four seconds. Runner **12/12** after the formatters changed the answers' text. The golden set was not run this session: no routing changed, no prompt changed, and `expected.txt` is as it was. Commit count: `git rev-list --count baseline-v1..HEAD`.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Grep for the caller, not the registration, and for the reader
of a return value. This session opened on `baseline-v1`, not `selection`,
while the note I had written said `selection`; the two pointed at the same
commit, so nothing was lost, but the branch name in a note is a claim like
any other.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Order 1 is built; Order 2's first two items, the ledger and the currency, are built; its third, the price source, is next. Its last section says when to stop and think. |
| `docs/benchmark.md` | **The definition of done.** 12 cases, 12 pass; the runner is the status. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Every case has a check. Nothing in it changed this session; it ran once, after the formatters began naming currencies, and held. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Swept at the end of this session: every entry the session touched carries a "10 September (eleventh session)" paragraph. Read at minimum: "No FX conversion anywhere" (built, with the commits and what stays), "The migration and the reseed are run by hand" (two lessons, one of them mine), and the five new Hygiene entries from "`Portfolio.currency` defaults to USD" to "`portfolio_manager.py`'s usage example cannot run". |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1–8. **Part 8 C is now reproduced by the code**, through the node, to the cent and with both dates. Never update it to match code output. The workbook's `Ledger` sheet C carries the same figures as formulas with no cached values; I have not yet opened it in Excel to confirm them. |
| `docs/IPS.md` | The policy, synthetic. `ips.toml` is derived from it. Do not edit `docs/IPS.md` casually; a personal one replaces it later as a local file. |
| `docs/PM-Assistant — Roadmap.md` | Stale, header lists what is superseded. DIRECTION.md's Order supersedes its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.16% v 12%, JNJ 10.05% v 10% at the 09-04 closes); the runner asserts structure.

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public — README is outdated and lies)
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half (positions, allocation,
P&L, risk, compliance) that is tools, and a judgement half (research,
valuation, a thesis) that has not started, on purpose. The router is
scaffolding until the tool layer is complete. **No deadline. Correctness over
speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** Tools return summaries; raw
  arrays move through `shared_data`. A year of spot rates stays in the
  database; DataAgent publishes only the rates on the held tickers' as-of
  dates.
- **Policy lives in config, not code.** `ips.toml` holds every number and
  topic word. The vocabularies are registries: `AGENTS`, `INTENTS`,
  `REQUIRES`, `TERMINAL` in `schemas.py`; the period keys in `config.py`.
  An agent computes; the synthesizer formats; the checker reads published
  shares and divides nowhere; a formatter reads the currency from the block
  and never assumes one.
- **Raise, do not repair.** A span the vocabulary lacks, a typo of a holding,
  two weights in one message: extraction asks back. A sale over the
  position, a ledger row with no portfolio, a missing rate on the price's
  date, a holding with no currency, a total with no currency: the pipeline
  stops and says why. A default is a wrong answer with a plausible face.
- **Holdings derive from the ledger (D13).** `transactions` is the record
  of what was bought and sold; a holding is computed from it by
  `quant/ledger.py` and there is no holdings table. Cost basis sums the
  row's `amount`, which is data from the statement (D14), never quantity x
  price recomputed - that is how a second currency enters, and Part 8 C is
  the test that can tell.
- **A rate is a price source (D17).** Stored per day with a date and a
  source, fetched under the price cache's rules, keyed by base and quote
  with the rate meaning base units per one unit of quote. A foreign holding
  is valued at quantity x price x the rate on the price's as-of date (D16),
  and both dates are published. Same currency means no lookup and no
  fetch.
- **Every figure names its currency (D18).** Cost basis, average price,
  market value and P&L are in the portfolio's base currency; the quote is
  in the asset's; the answer says which is which and prints the rate it
  went through.
- **Extraction and derivation before the model.** Tickers, periods,
  percentages and the compliance mode are read from the message; the plan
  is derived from the intent and those parameters. The model decides
  intent, `measure`, `group_by`, `status`, confidence and a clarification
  question, and nothing else it emits is read.
- **Selection is rendering.** A formatter selects from a block the node
  computed in full; the selection's values are the block's own words.
- **References before code.** Part 8 A and B before the ledger; Part 8 C
  before any FX code, and the code reproduced it.

### How I work on this

- Every change starts as a written decision: what it is, what each rule
  means, what changes if it is taken, the rejected alternatives, which loop
  sees it and what it will show. Then one commit per layer, tests written
  first and seen failing, `git status --short` and the diff read before
  each commit.
- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting any symbol;
  grep for the caller and for the reader of a return value.
- **A prompt change is a hypothesis.** Line-by-line prediction in the commit
  message before the run; golden twice. After the second failed prediction
  on a line, stop. No prompt changed this session and the golden set did
  not run.
- Never `commit -a`/`-am`, never `add -A`/`.`; name the files. Never
  rebase, amend, reset, stash. Never edit `.gitignore`. An edit of mine
  that sits in a file about to change gets its own commit first, so it
  does not ride into another message.
- **The migration and the reseed are run by hand**, from the shell, from
  the project root: `alembic upgrade head`, then
  `python src/portfolio_tool/scripts/seed_portfolio.py --reset` when the
  seed changed. A migration is committed unexecuted; the schema test
  written before it is the check; and it is applied and reverted on a
  scratch copy of the database before it is committed. **I paste what the
  command printed, not "done":** two attempts this session left no trace
  on the file and the cause was never seen.
- **The workbook is closed in Excel before any openpyxl write.** `lsof`
  first; if it is open, close it, every time. A modified tracked binary is
  its own commit. No write this session.
- No emoji in code or comments; I strip the old ones as I go.

### What I do NOT want

A pure asyncio/regex deterministic version without LangGraph. Prompt rules
added to fix a routing defect (DIRECTION.md). My real portfolio's data in
the repo: it enters last, when everything works. No more concurrency until
independent tools exist (Order 4/5) and a measurement asks for it; no
cached holdings table; no currency symbol table, no rate inverted in code,
no fallback rate of 1 and no fallback currency anywhere.

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

**572 passed, 23 warnings, about four seconds.** Up from 472: the FX
reference test (`test_fx.py`, 17), the two rate-table schema tests (38),
the fetch (8), the DataAgent currency tests (8), the analysis node's Part
8 C tests (7), the formatter and compliance currency tests (16), the
transactions schema additions (6), and the summary edit. The suite copies the database, so
the fifty-five of these that read a migrated table were red through the
suite and green on a migrated scratch copy until the migrations ran; all
green now.

**The golden set has sixteen queries, every portfolio query on portfolio
3**, two pinned failures (the macro query; "Should I rebalance my
portfolio?"). Not run this session; `expected.txt` unchanged since 93290af.

**Runner 12/12**, run once, after the allocation and P&L formatters began
naming currencies and before the compliance formatter did; the prose
checks are substring checks on figures and dates, so the codes did not
move them, as predicted. Nothing under `src/` changed the answers after
that run except the compliance report's currency codes, checked offline
by `test_compliance_formatter.py` under the runner's own rules.

### Branches and tags

`selection` is the working branch, cut from `baseline-v1` at 7fc6474;
`baseline-v1` sits at 665d033, where this session began. `vocabulary` and
`compliance` are merged into `baseline-v1`. `wip/phase7-snapshot` holds
rejected Compliance/IPS code; nothing on it is scheduled. `wip/rag-early`
and tag `rag-early-parked` hold the deleted RAG code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`88d7b7afdce7`** (transaction fees required), 18 migrations, linear, all
applied; this session's four applied together with one `upgrade head`.
Tables that matter: `portfolios`, `transactions` (`portfolio_id` and
`amount` NOT NULL; `date` a DATE and `fees` NOT NULL since this session,
neither defaulted), `assets`, `daily_prices`, **`fx_rates`** (base, quote,
date, rate, source; one row per base, quote and day; empty) and
**`fx_fetch_metadata`** (the rate fetch's cache record per pair; empty).
**There is no holdings table.**

- **Portfolio 3, "Benchmark Portfolio" — the only portfolio.** Nine ledger
  rows, one buy each, Part 8 A, dates now stored as days; cost basis
  284,500 plus 15,500 cash; base currency USD, every asset USD, so no rate
  is ever fetched for it.
- **Reseeding rewrites the nine assets' metadata** to the same values, and
  refuses without `--reset` when ledger rows exist. `--reset` clears the
  portfolio's ledger first. No reseed was needed this session.
- The leaked `assets` row 10 is gone: nine child tables counted zero
  against it and I deleted it by hand. Ids run 1 to 14 without it.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  (`claude-haiku-4-5-20251001`). `ANTHROPIC_SONNET` is `claude-sonnet-5`,
  behind `use_stronger_model`, which is off.
- `openpyxl` is in the venv and the `dev` extras, for the workbook's `Ledger`
  sheet. No LibreOffice: a sheet written with it is recalculated by Excel on
  opening, not before.
- `config.features.observability_enabled` is **false** here. Do not turn it
  on without reading the KNOWN_GAPS entry on the router's own span.
- `portfolio_tool/__init__.py` opens a DB connection at import; the router
  prompt and `agents/extraction.py` import nothing from it at module level.
  `config` reads `DATABASE_URL` at import, which is why a scratch copy of
  the database has to be named in the environment before any project
  import.
- `alembic.ini` names the database by a relative path: `alembic upgrade
  head` runs from the project root or touches nothing.
- Yahoo quotes a currency pair as `{quote}{base}=X`: `USDEUR=X` is euros
  per dollar (0.8624 on 2026-09-02), `EURUSD=X` the inverse. Checked live
  this session; the provider asks for the first and inverts nothing.

---

## 4. What the eleventh session did

`git log --oneline 665d033..HEAD` for the list, in order.

**The FX code, against Part 8 C, in the order the tenth session's handoff
set (item 1).** The test first (bf8305c, later extended in d40d4ed): one
euro row derives to 100 at 184.05 EUR and 18,405.00, the falsifier that
the basis is the amount and not 20,005.00 of mixed dollars and euros; at
324.96 USD and a stated 0.8500 on 2026-09-02, 27,621.60 EUR, +9,216.60,
+50.08%, both dates; no rate for the day, or a rate only for the day
before, raises naming USD and the date; a dollar holding in a dollar
portfolio needs no table and reproduces Part 1. The test fixed the shape:
`spot_rates(holdings, as_of_dates, base_currency, fx_rates)` giving one
entry per holding, `None` when the currencies agree, and `rates` as a
required argument on the four computations.

Then the tables, each a schema test then a model and migration:
`fx_rates` (40e0e9d, 210f8c8) with named base and quote columns rather
than a pair string that would read like the market quotation, and
`fx_fetch_metadata` (ca4a90d, 7921d2e), the pair's cache record kept apart
from the asset one because a pair has no asset. Then the fetch (7f9d9e5,
3b3a2a6): `DataManager.update_fx_rates` under the price cache's rules,
coverage meaning "how far back have I asked", the provider method and a
required `name` on every provider written as `source`. Then the arithmetic
(07fa460): `quant/fx.py`, `_market_values` the one place the rate is
applied so the three views and the P&L share one path, `PositionPnL`
carrying the price's currency, the rate and its date; the three fixture
files pass an all-`None` mapping, the honest statement that portfolio 3 is
single-currency. That commit left the analysis node red for one commit,
said so in its message, rather than put a placeholder mapping in the node.
Then the node (f55d600, 116119e): `base_currency` and `fx_rates` required
from `shared_data`, the lookup before anything is valued, the rate and its
date published per position and the base on the blocks; Part 8 C
reproduces through it and the missing-rate case refuses and publishes
nothing. Then DataAgent (8733115, 441f633): the context carries the
portfolio's currency, the summary each holding's, and
`fetch_fx_rates_tool` fetches each foreign currency over the price window
and returns only the rates on the held tickers' as-of dates. One CLI call
on portfolio 3 showed the seam whole: base USD, an empty table, no rate
call, the answer text unchanged. Then the formatters (fdd2acd, 42f3dc9,
4d8d322, 6d86818): the ISO code and not a symbol, once per table header in
the allocation and on every base figure in the P&L, the quote in its own
currency beside the euro average, a "converted at 0.8500 EUR per USD as of
2026-09-02" line, the note that the gain's split into a price part and a
currency part is not computed, and the compliance block carrying
`base_currency` so its total and distances name it; a formatter with no
currency to read raises. Runner 12/12 after.

**The three defaults and the dead code (item 2).** `Transaction.date` a
Date with no default (20fe9c1, 76005d0, migration 552ab8900332) - the
migration rewrites the nine stored timestamps to days as it changes the
type, done as add-fill-drop-rename because alembic's batch `CAST` through
SQLite's numeric-affinity `DATE` turned `2024-01-15` into 2024 on the
scratch copy; `record_transaction` refuses a datetime. `fees` NOT NULL with
no default (fa90f22, 6d04179, migration 88d7b7afdce7). The two hand-run
scripts calling the deleted `add_holding` deleted (20973e8, ae1bbb8), their
checks being the ledger reader tests and `test_strict_nodes.py` one for
one. `ensure_asset_exists_helper` deleted after the grep (282a25d); it had
also been unrunnable. My own emoji edit in `data_agent.py` committed on
its own before the file changed for the fetch (26592b2). The leaked asset
row deleted by hand, after the four migrations applied.

**Findings logged, not chased** (all in KNOWN_GAPS): `Portfolio.currency`
defaulting to USD; `price_fetch_interval_days` absent from `config.toml`
and defaulted in code; cost basis recomputed in the allocation layer from
the average while the summary drops the ledger's figure; `test_shrinkage.py`
collected with a dead call inside a swallowing `try`; the portfolio
manager's docstring example that cannot run; the rebalance tools' fixed
euro sign, still the wrong-currency stamp.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- The rate convention: base units per one unit of the asset's currency,
  as Part 8 C states it; the table keyed by base and quote, never a pair
  string; the provider gets the direction right and nothing downstream
  inverts.
- `rates` is a required mapping on the four computations, one entry per
  holding, `None` meaning the lookup found the currencies equal. A default
  meaning "no conversion" was rejected as the 1.0 with a plausible face.
- The rate fetch has its own cache record per pair, under the price
  cache's rule that coverage is what was asked, not what is stored.
- DataAgent publishes only the rates on the held tickers' as-of dates, and
  the analysis node does the lookup on the price's date; a date with no
  row is absent, and the node's lookup is what raises.
- A formatter reads the currency from the block and raises without one;
  the ISO code, no symbol table; once per table header for allocation,
  on every base figure for the P&L.
- The compliance block carries `base_currency`, one key, copied from the
  allocation; `None` in the two modes that measure nothing.
- With a signature change that breaks a node, the node commit comes
  before the DataAgent commit, so pytest is red for one commit and the
  live path for one, rather than pytest for two.
- A migration is applied and reverted on a scratch copy before it is
  committed; a type change on a populated SQLite column is
  add-fill-drop-rename.
- `date` and `fees` each their own migration; the two scripts deleted
  rather than rewritten.

**Pending — decide before writing code.**
1. **Order 2 items 3 and 4**: the price source that can be defended with
   real money; the personal IPS as a local file. Item 3 is next.
2. **`Portfolio.currency` defaulting to USD** on the model and in
   `create_portfolio`: a model-and-migration change plus a signature
   change, the last repair-shaped default on the ledger's path.
3. **Cost basis recomputed in the allocation layer**: the summary carrying
   `cost_basis` and the layer reading it; a formatter follows.
4. **`test_shrinkage.py`**: delete, or rewrite as an assertion.
5. **`price_fetch_interval_days`** into `config.toml`, the code default
   dropped.
6. **The rebalance tools' fixed euro sign**: the last place a currency is
   assumed; the tools are outside the benchmark and the fix waits for a
   case or for the rebalance target decision (11).
7. **The portfolio manager's docstring**: the `DataManager()` example and
   the emoji.
8. **The workbook's `Ledger` sheet C**: open in Excel, confirm 18,405.00,
   184.05, 27,621.60, 50.08%, save; then the `Decisions` sheet (D8, D9,
   D10–D18, `C91`) and D9's wording.
9. **Records and rules for the span and two-weights clarifications**, when
   a case asks.
10. **A window return** as a measure with a reference; not an extraction rule.
11. Replace the two verbatim benchmark few-shots (1.1, 1.3); the
    rebalancing few-shot with four percentages.
12. The hypothetical mode's instrument type ("11% into a new ETF").
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the
    IPS — both edit `docs/IPS.md`.
14. "Optimization failed: None": the message, and the two-asset failure.
15. A golden line for 2.3.
16. **Company names, German phrasings, the softer 3.5**: logged, not
    built; decision 16 is their path (Order 5, or a case that needs it).
17. **`group_by` as the subject kind of a compliance finding**, when a case asks.
18. **Realized gains and closed positions as figures the system reports**:
    the derivation carries `realized`; no case asks; the currency split of
    a gain sits beside it as a second unreported figure.

---

## 6. Where we stand against the benchmark

12/12. Level 1, Level 2 and Level 3 in full. benchmark.md's notes are
current; nothing in it changed this session. The answers now name the
currency of every amount, which no case asserts and none forbids.

---

## 7. Next steps, in order

**Order 2, item 3: a price source that can be defended with real money.**
DIRECTION.md's words; nothing is designed yet. The decision to bring first
is what "defended" means as a check: which figure of Part 1 a second
source must reproduce, to what tolerance, on which date, and what the
system says when the two sources disagree. A reference for that check goes
into expected_values.md before any code, the way Part 8 did. Not a second
provider bolted beside yfinance for its own sake: the cache, the as-of
dates and now the rate fetch all assume one provider, and a second one is
a decision about which figure wins, not about plumbing.

**Then Order 2, item 4: the personal IPS as a local file**, the type
vocabulary grown one clause at a time, and the Part 8 reference for the
real portfolio before any figure about it is trusted.

**The small items above (2 to 8) when convenient**, each its own decision
and commit; none blocks item 3.

### Later, with reasons

- The judgement half stays unstarted until benchmark.md has a Level 4 and
  the prediction ledger exists (DIRECTION.md).
- `measure`, `group_by` and `status` are the model's classification beyond
  intent; whether they become extraction is a question for the tool
  boundary, not for a prompt.
- More concurrency: when Order 4/5 has independent tools and a measurement
  says a request waits on several things at once.
- README rewrite; the inline `sqrt(w'Σw)` copies; the hot-potato violation
  in `price_data_json`.

---

## 8. Rules learned the hard way

**The output is the record, not the word.** Two runs of the migration
this session left no trace on the database, and I reported each as done.
The third, pasted in full, showed four `Running upgrade` lines and the
file changed. A command that changes state is confirmed by what it
printed and by reading the state, never by having been typed.

**SQLite's `CAST(... AS DATE)` has numeric affinity.** Alembic's batch
rebuild copies a column whose type changes through a cast, and
`2024-01-15` came out as 2024. Seen on a scratch copy, which is the only
reason it was not seen on the database. A type change on a populated
column is add a column, fill it without a cast, drop the old one, rename.

**A scratch copy is the instrument while a migration is pending.** The
suite copies the real database, so every test that reads a migrated table
is red through the suite until the owner's command runs; the migrated
scratch copy, with the database URL set before any project import, is
where the code is seen right in the meantime. Fifty-five tests this
session.

**A required argument breaks the callers, and that is the point.** Adding
`rates` to the four computations turned the analysis node red for exactly
one commit, and the suite showed it. The alternative, a placeholder
mapping in the node, would have been the default the change exists to
remove.

**A formatter with a fallback prints a currency nobody published.** Every
amount's currency is read from the block; an amount with no currency
raises. The rebalance tools' fixed euro sign is what the other choice
looks like after a year.

**Read the model's own output before choosing between readings; a record
beats a re-read; prose that names a plan classifies by proxy; a green
suite can hide a broken call site; registration is not reachability;
predict from the whole prompt; a refusal is an honest failure; write the
falsifier; design the failure direction of a model-owned field; a fixture
that passes in both states is no check; a test that exercises exactly the
boundary is not a test of crossing it; a deleted row's id comes back; a
collection error is a blind suite; measure a timing change before
explaining it; a check that says stop has to stop the script — still
true.** Earlier handoffs' §8 have the examples.

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

python src/agents/cli.py --portfolio 3

grep -rn "SymbolName" src/ tests/ --include='*.py'
git status --short
git log --oneline baseline-v1..HEAD

# by hand, from the project root, after a migration or a seed change:
alembic upgrade head
python src/portfolio_tool/scripts/seed_portfolio.py --reset

# what the database says it is at:
sqlite3 data/portfolio.db "select version_num from alembic_version;"
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~4s, no model calls | Do the components still work; does the ledger reproduce Part 8 A, B to the cent and the rate arithmetic Part 8 C; does the schema have the tables and columns and not the defaults; does every table row derive its plan; does extraction read every recorded prompt the same way; does the node publish the block the checker reads, both dates included; does each formatter select what its parameters say and name the currency it was given |
| CLI | ~4s, one call | What it is actually doing — the plan, the parameters, the reasoning line, what was asked back, the answer's header, and since this session `base_currency` and `fx_rates` in `shared_data` |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines on portfolio 3 or none, two pinned failures, `retries` when a plan was rejected). Blind to `measure`, `group_by`, `status`, `tickers`, the compliance mode and every currency |
| Benchmark runner | ~1.5min, cents | How many cases pass; the only loop that sees the compliance mode, the second turn, a model-owned field set where it should not be, and the answers' text as a whole |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second
miss on a line. The runner is per capability commit, and per commit that
changes the answers' text.
