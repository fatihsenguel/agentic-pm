# AGENTIC_FINANCE — Session Handoff

**Session date:** 10 September 2026 (twelfth session; regenerated at its end)
**Branch:** `selection`. `baseline-v1` was fast-forwarded to 68b0539 before this session and both were pushed there; eighteen commits since, this file included, not pushed.
**State:** Green on every loop I ran. pytest 606 in about three seconds. The runner and the golden set were not run this session: no routing changed, no prompt changed, no answer text changed, and `expected.txt` is as it was. Commit count: `git rev-list --count baseline-v1..HEAD`.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Grep for the caller, not the registration, and for the reader
of a return value. This session found the plan I had written wrong on
inspection twice (a migration promised where the database already refused
the value; a red count predicted at two where three were red) and a
library default I had assumed was harmless and was not. A claim in a
document is a claim like any other.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Order 1 is built; Order 2's first three items, the ledger, the currency and the price source, are built; its fourth, the personal IPS, is next. Its last section says when to stop and think. |
| `docs/benchmark.md` | **The definition of done.** 12 cases, 12 pass on the last run (eleventh session); the runner is the status. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Every case has a check. Nothing in it changed this session and it did not run: nothing under `src/` changed an answer's text. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Swept at the end of this session. Read at minimum: "The stored closes were dividend-adjusted" (the whole story of Order 2 item 3), "The migration and the reseed are run by hand" (the fetch that ran before the delete), the four new Hygiene entries from "Two more `source` columns" to "The CLI reads `exit`", and "Volatility over as-traded closes or over a total-return series?" under Directions. |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1–9. **Part 9 is reproduced by the database**: every one of the 2,268 committed closes, and the two rows before a dividend that the old provider call got wrong. Never update it to match code output. The workbook's `Ledger` sheet C and `Prices` sheet carry the same figures as formulas with no cached values; neither has been opened in Excel yet. |
| `docs/IPS.md` | The policy, synthetic. `ips.toml` is derived from it. Do not edit `docs/IPS.md` casually; a personal one replaces it later as a local file. |
| `docs/PM-Assistant — Roadmap.md` | Stale, header lists what is superseded. DIRECTION.md's Order supersedes its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.16% v 12%, JNJ 10.05% v 10% at the 09-04 closes); the runner asserts structure.

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public — README is outdated and says so in its first line; a short replacement is a pending decision)
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
  topic word; `config.toml` holds every fetch interval, the price one
  included since this session, and a missing file raises. The vocabularies
  are registries: `AGENTS`, `INTENTS`, `REQUIRES`, `TERMINAL` in
  `schemas.py`; the period keys in `config.py`. An agent computes; the
  synthesizer formats; the checker reads published shares and divides
  nowhere; a formatter reads the currency from the block and never assumes
  one.
- **Raise, do not repair.** A span the vocabulary lacks, a typo of a holding,
  two weights in one message: extraction asks back. A sale over the
  position, a ledger row with no portfolio, a missing rate on the price's
  date, a holding with no currency, a portfolio with no currency, a holding
  with no cost basis, a config with no interval: the pipeline stops and says
  why. A default is a wrong answer with a plausible face.
- **Holdings derive from the ledger (D13).** `transactions` is the record
  of what was bought and sold; a holding is computed from it by
  `quant/ledger.py` and there is no holdings table. Cost basis sums the
  row's `amount`, which is data from the statement (D14), and since this
  session that figure is carried on the summary and read by the allocation
  layer, never recomputed from quantity and average.
- **A rate is a price source (D17).** Stored per day with a date and a
  source, fetched under the price cache's rules, keyed by base and quote
  with the rate meaning base units per one unit of quote. A foreign holding
  is valued at quantity x price x the rate on the price's as-of date (D16),
  and both dates are published.
- **A close is the print (D19).** The exchange's official closing price as
  traded, split-adjusted and nothing else: the figure a broker statement
  values the position at. The provider asks for it unadjusted; every row
  carries its source; when two sources disagree the exchange's print wins
  and nothing averages (D20). Part 9 is the check.
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
  before any FX code; Part 9 before the provider changed, with the rows
  that could tell the old figure from the print.

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
- **The migration, the reseed and any rewrite of stored prices are run by
  hand**, from the shell, from the project root: `alembic upgrade head`;
  `python src/portfolio_tool/scripts/seed_portfolio.py --reset` when the
  seed changed; a delete of price rows and their fetch records when the
  stored convention changed. A migration is committed unexecuted; the
  schema test written before it is the check; and it is applied and
  reverted on a scratch copy of the database before it is committed.
  **I paste what the command printed, not "done":** this session the
  first CLI run after the migration showed at once that the delete had
  not happened yet, because the output had no provider line.
- **The workbook is closed in Excel before any openpyxl write.** `lsof`
  first; if it is open, close it, every time. A modified tracked binary is
  its own commit. One write this session, the `Prices` sheet, checked
  twice.
- A count I predict is a count I add up. 8,760 was a guess; the file said
  9,140.
- No emoji in code or comments; I strip the old ones as I go.

### What I do NOT want

A pure asyncio/regex deterministic version without LangGraph. Prompt rules
added to fix a routing defect (DIRECTION.md). My real portfolio's data in
the repo: it enters last, when everything works. No more concurrency until
independent tools exist (Order 4/5) and a measurement asks for it; no
cached holdings table; no currency symbol table, no rate inverted in code,
no fallback rate of 1 and no fallback currency anywhere; no adjusted close
in the price table, and no second live provider bolted on for its own sake.
The old README scrubbed from history: no. A rewrite of history for a
document is worse than the document.

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

**606 passed, 26 warnings, about three seconds.** Up from 572: the price
source tests (`test_price_source.py`, 13), the price schema test
(`test_daily_prices_schema.py`, 8), the price fetch test
(`test_price_fetch.py`, 2), the portfolio currency test (4), the cost basis
contract test (5), the interval test (3), the summary test's extension,
and one fewer from `test_shrinkage.py` deleted. Seven tests were red
through the suite between the `source` model commit and my running the
migration; the migrated scratch copy ran the whole suite green meanwhile.

**The golden set has sixteen queries, every portfolio query on portfolio
3**, two pinned failures (the macro query; "Should I rebalance my
portfolio?"). Not run this session; `expected.txt` unchanged since 93290af.

**Runner 12/12** on its last run, in the eleventh session after the
compliance formatter began naming currencies. Not run this session:
nothing under `src/` changed an answer's text. The allocation and P&L
blocks carry the same cost figures as before, now read from the ledger's
own number instead of recomputed from it, and the formatters print the
same words.

### Branches and tags

`selection` is the working branch. `baseline-v1` sits at 68b0539, where
this session began, and both are pushed there. `vocabulary` and
`compliance` are merged into `baseline-v1`. `wip/phase7-snapshot` holds
rejected Compliance/IPS code; nothing on it is scheduled. `wip/rag-early`
and tag `rag-early-parked` hold the deleted RAG code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`2ee0c9249a9f`** (`daily_prices.source`), 19 migrations, linear, all
applied; this session's one applied by hand, output pasted. Tables that
matter: `portfolios` (`currency` NOT NULL, no default anywhere since this
session), `transactions` (`portfolio_id`, `amount`, `date` a DATE, `fees`,
all NOT NULL, none defaulted), `assets`, `daily_prices` (**`source` NOT
NULL** since this session; every close as traded for the nine holdings),
`fx_rates` and `fx_fetch_metadata` (empty). **There is no holdings table.**

- **Portfolio 3, "Benchmark Portfolio" — the only portfolio.** Nine ledger
  rows, one buy each, Part 8 A; cost basis 284,500 plus 15,500 cash; base
  currency USD, every asset USD, so no rate is ever fetched for it.
- **The nine holdings' price history was deleted and refetched this
  session**, by hand, after the provider stopped asking for adjusted
  closes: 771 rows each, 2023-08-14 to 2026-09-09, every row a cent print
  with source `yfinance`. The database reproduces all 2,268 cells of
  `tests/golden/benchmark_closes.csv`. Older history (AAPL and MSFT back to
  2000) was not refetched; nothing asks for it, and the cache extends the
  day a question does.
- **Four leftover tickers** from the deleted portfolios 1 and 2 (AMZN,
  PLTR, SAP, VWO) still hold 9,140 rows, most of them adjusted, read by
  nothing. Deleting the four assets and their rows is mine, by hand, when
  convenient (KNOWN_GAPS, Hygiene). 16,079 rows in the table in all.
- Reseeding rewrites the nine assets' metadata to the same values, and
  refuses without `--reset` when ledger rows exist. No reseed this session.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  (`claude-haiku-4-5-20251001`). `ANTHROPIC_SONNET` is `claude-sonnet-5`,
  behind `use_stronger_model`, which is off.
- **yfinance 1.7.0.** `Ticker.history()` defaults to `auto_adjust=True`,
  which replaces the close with the dividend-adjusted close. The price
  method passes `auto_adjust=False` and reads `Close`; the rate and VIX
  methods take the default, having nothing to adjust. A library default is
  a claim to check, not a fact to assume.
- `openpyxl` is in the venv and the `dev` extras, for the workbook's
  `Ledger` and `Prices` sheets. No LibreOffice: a sheet written with it is
  recalculated by Excel on opening, not before.
- `config.toml` is required: `data_manager.py` raises without it, and its
  `[data_fetch]` carries all four intervals.
- `config.features.observability_enabled` is **false** here. Do not turn it
  on without reading the KNOWN_GAPS entry on the router's own span.
- `portfolio_tool/__init__.py` opens a DB connection at import; the router
  prompt and `agents/extraction.py` import nothing from it at module level.
  `config` reads `DATABASE_URL` at import, which is why a scratch copy of
  the database has to be named in the environment before any project
  import. **The whole suite runs on a migrated scratch copy** with
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest
  -q --noconftest`; `conftest.py` would otherwise copy the real file.
- `alembic.ini` names the database by a relative path: `alembic upgrade
  head` runs from the project root or touches nothing. The alembic API
  with `sqlalchemy.url` overridden is how a migration runs on a scratch
  copy.
- Yahoo quotes a currency pair as `{quote}{base}=X`: `USDEUR=X` is euros
  per dollar. The provider asks for the first and inverts nothing.
- The CLI's quit command is `:q`. `exit` is sent to the router as a
  question and refused as an order (KNOWN_GAPS, Hygiene).

---

## 4. What the twelfth session did

`git log --oneline 68b0539..HEAD` for the list, in order.

**Order 2, item 3: the price source (items 608d5be to b3f245a).** The
decision first, before any code: what "defended with real money" means as
a check. Reading the price path for it found the defect the check had to
see: the provider took the library's default and stored dividend-adjusted
closes, so 1,629 of the 2,268 committed cells disagreed with the database
and Part 1's nine closes agreed only because 09-02 was after every
holding's latest ex-dividend date. Then the reference: Part 9 with D19 (a
close is the print, split-adjusted only) and D20 (the exchange's print
wins, nothing averages), the nine 09-02 closes from the listing exchange's
own quotes, fetched by me from the shell, against Part 1, nine of nine;
and two rows before a dividend, JNJ 2026-08-21 and TLT 2026-08-28, where
the database was wrong by exactly one dividend factor - the falsifier,
because a check on the latest date passes in both states. The workbook's
`Prices` sheet (57a3966). Then the code, test first each: the provider
test with a stand-in for the library that does what the documented default
does (d79a1e0), the one flag (314b707); the `source` schema test (9d3cb6f),
the model and migration (736d8fa, applied and reverted on a scratch copy);
the fetch test (614c5fb) and the fetch writing `provider.name` (b3f245a).
Then by hand: the migration, the delete of the nine holdings' rows and
fetch records, one CLI question refetching 771 rows per holding as traded;
the comparison after it, zero mismatches on 2,268 cells. A second live
provider was rejected: it would agree with Yahoo on every recent date, the
blind spot itself.

**The six small items from the eleventh session's §5 (ba73fa1 to 7a3c054),
each its own decision, test first where a test was possible.**
`Portfolio.currency`: both defaults dropped, `currency` keyword-only and
required, no migration since the database already refused a NULL (a
correction of my own plan). Cost basis: carried on the summary from the
ledger and read by the allocation layer, the falsifier a holding whose
stated basis is not quantity times average, thirty fixture holdings
gaining the key at their own product. `test_shrinkage.py` deleted. The
price fetch interval into `config.toml`, the code default and the fallback
table gone. The docstring fixed. The rebalance euro sign logged, not built:
its path is dead until the rebalance target exists.

**The sweep (0c01dc1).** Everything above in KNOWN_GAPS, with what I got
wrong: the migration I promised and did not need, the red count of two
that was three, the row count of 8,760 that was 9,140, the regex pass that
doubled a key in two fixture files while the suite stayed green.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- D19 and D20 (expected_values.md Part 0): a close is the exchange's
  as-traded print, split-adjusted only; the print wins a disagreement;
  nothing averages; the reference does not move to match a provider.
- The check for a price source is a second, independent source's print on
  the valuation date and on dates before a dividend; tolerance one cent
  after rounding; the exchange's own quotes as the source.
- The fix is at the provider, one flag; not a second provider, not a
  vendor change, not an adjusted-close column beside the print.
- `daily_prices.source`, required, defaulted nowhere, the mirror of
  `fx_rates.source`; existing rows filled with the literal `yfinance` by
  the migration; the stored history refetched by hand so the table holds
  one convention.
- A portfolio names its currency; nothing supplies one.
- The allocation layer reads the ledger's cost basis and computes none.
- Fetch intervals are `config.toml`'s; a missing file raises.
- The old README is replaced, not scrubbed from history.

**Pending — decide before writing code.** Numbers kept from the eleventh
session's list so that KNOWN_GAPS references still resolve; done items
are struck.
1. **Order 2 item 4**: the personal IPS as a local file, the type
   vocabulary grown one clause at a time, and the Part 8 reference for
   the real portfolio before any figure about it is trusted. **Next.**
2. ~~`Portfolio.currency` defaulting to USD~~ done (ee9659d).
3. ~~Cost basis recomputed in the allocation layer~~ done (244645d).
4. ~~`test_shrinkage.py`~~ deleted (5849c7d).
5. ~~`price_fetch_interval_days` into `config.toml`~~ done (a12e4ed).
6. **The rebalance tools' fixed euro sign**: logged this session, not
   built; the path is dead until decision 11.
7. ~~The portfolio manager's docstring~~ done (7a3c054).
8. **The workbook in Excel**: open, confirm `Ledger` sheet C (18,405.00,
   184.05, 27,621.60, 50.08%) and the `Prices` sheet (`B15` = 9, both
   verdicts in H "database wrong, series is the print"), save; then the
   `Decisions` sheet (D8 to D20) and D9's wording.
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
19. **A short README** replacing the outdated one: my ask at the end of
    this session; the outline is a decision, its own commit.
20. **Two more `source` columns** (`FinancialStatement`, `MacroData`) with
    a `yfinance` default: the repair shape, off the benchmark's path.
21. **The four leftover tickers' rows**: mine to delete by hand.
22. **Volatility over as-traded closes or over a total-return series**: a
    Part 4 decision with a recomputed Part 4 beside the present one.
23. **The answer text naming the price source**: a rendering; the runner
    sees it.
24. **The csv-versus-database comparison as a committed check**: this
    session it was a script of mine run by hand; the suite copies the real
    database, so a test could hold the copy to the committed series, and
    would fail on a fresh clone with no database, which `conftest.py`
    already refuses.

---

## 6. Where we stand against the benchmark

12/12 on the last run, in the eleventh session. Level 1, Level 2 and Level
3 in full. benchmark.md's notes are current; nothing in it changed this
session. Not run this session because no answer's text changed; the first
change that touches a formatter runs it.

---

## 7. Next steps, in order

**Order 2, item 4: the personal IPS as a local file.** The type vocabulary
grows one clause at a time, each clause a decision with its checker and
its Part 7-style reference; the file replaces `docs/IPS.md` without a code
change (DIRECTION.md invariant 4). With it, the Part 8 reference for the
real portfolio: my ledger rows, my base currency, the rates on the dates,
hand-computed before any figure about it is trusted. The real portfolio's
data stays out of the repository.

**The short README (19)** when the owner says; the outline first.

**The small items (8, 20, 21) when convenient**, each its own decision
and commit; none blocks item 4. Item 8 needs Excel and nothing else.

### Later, with reasons

- The judgement half stays unstarted until benchmark.md has a Level 4 and
  the prediction ledger exists (DIRECTION.md).
- `measure`, `group_by` and `status` are the model's classification beyond
  intent; whether they become extraction is a question for the tool
  boundary, not for a prompt.
- A total-return series for volatility (22): with a recomputed Part 4, not
  by flipping the provider flag back.
- More concurrency: when Order 4/5 has independent tools and a measurement
  says a request waits on several things at once.
- The inline `sqrt(w'Σw)` copies; the hot-potato violation in
  `price_data_json`.

---

## 8. Rules learned the hard way

**A check on the most recent date passes in both states.** The nine 09-02
closes agreed with the exchange before and after the fix, because 09-02
lay after every holding's latest ex-dividend date. The rows that could
tell the adjusted figure from the print were the ones before a dividend,
and Part 9 has them because I looked for where the two disagreed most
before choosing the check. Write the falsifier where the two states
differ, not where they coincide.

**A library default is a claim to check.** `auto_adjust=True` had been the
provider's silent choice since the first fetch, and 1,629 stored cells
were wrong by it while every loop was green. The reference was right, the
database was not, and nothing compared them until this session did.

**The output showed the missing step.** The CLI run after the migration
had no provider line and finished in 204 ms: the cache had found every row
and fetched nothing, because the delete had not happened yet. The output
is the record; "the refetch ran" would have been false and unfalsifiable.

**Check the schema before promising a migration.** `portfolios.currency`
was NOT NULL with no server default all along; the dollars came from the
model and the manager. The plan said migration; the file said otherwise.

**A count is added up, not recalled.** 8,760 was what I remembered of the
four leftover tickers; 9,140 was their sum. Predict from arithmetic.

**A regex pass over fixtures needs its lines read.** Two files came out
with a doubled key and a truncated average, and the suite stayed green
because Python accepted both. The diff is read line by line, especially
the mechanical part.

**A red count is a prediction too.** Two of four was the call; three of
four was the fact, because the model's default filled the value in before
the database could refuse it. The extra red was the defect seen from the
other side, and worth recording as such.

**The output is the record, not the word; SQLite's `CAST(... AS DATE)` has
numeric affinity; a scratch copy is the instrument while a migration is
pending; a required argument breaks the callers, and that is the point; a
formatter with a fallback prints a currency nobody published; read the
model's own output before choosing between readings; a record beats a
re-read; prose that names a plan classifies by proxy; a green suite can
hide a broken call site; registration is not reachability; predict from
the whole prompt; a refusal is an honest failure; design the failure
direction of a model-owned field; a fixture that passes in both states is
no check; a test that exercises exactly the boundary is not a test of
crossing it; a deleted row's id comes back; a collection error is a blind
suite; measure a timing change before explaining it; a check that says
stop has to stop the script — still true.** Earlier handoffs' §8 have the
examples.

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

# what the database says it is at:
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# the whole suite on a migrated scratch copy, while a migration is pending:
DATABASE_URL="sqlite:///$PWD/scratch.db" USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest

# after a change to what the provider stores: delete the nine holdings'
# rows and their price-fetch records by hand, then one CLI question refetches
sqlite3 data/portfolio.db "delete from daily_prices where asset_id in (select id from assets where ticker in ('SPY','AAPL','MSFT','JNJ','JPM','NEE','TLT','GLD','VNQ')); update asset_fetch_metadata set last_price_fetch_time=null, earliest_price_start=null where asset_id in (select id from assets where ticker in ('SPY','AAPL','MSFT','JNJ','JPM','NEE','TLT','GLD','VNQ'));"
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3s, no model calls | Do the components still work; does the ledger reproduce Part 8 A, B to the cent and the rate arithmetic Part 8 C; does the committed series hold Part 9's prints and does the provider return the print; does the schema have the tables and columns and not the defaults; does every table row derive its plan; does extraction read every recorded prompt the same way; does the node publish the block the checker reads, both dates included; does each formatter select what its parameters say and name the currency it was given |
| CLI | ~4s, one call | What it is actually doing — the plan, the parameters, the reasoning line, what was asked back, the answer's header, `base_currency` and `fx_rates` in `shared_data`, and whether the provider was called at all and with which flag |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines on portfolio 3 or none, two pinned failures, `retries` when a plan was rejected). Blind to `measure`, `group_by`, `status`, `tickers`, the compliance mode and every currency |
| Benchmark runner | ~1.5min, cents | How many cases pass; the only loop that sees the compliance mode, the second turn, a model-owned field set where it should not be, and the answers' text as a whole |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second
miss on a line. The runner is per capability commit, and per commit that
changes the answers' text.
