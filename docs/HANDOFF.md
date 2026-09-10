# AGENTIC_FINANCE — Session Handoff

**Session date:** 10 September 2026 (tenth session; regenerated at its end)
**Branch:** `selection`, cut from `baseline-v1` at 7fc6474. Sixty-two commits on top, the sweep and this file included. Not merged, not pushed yet.
**State:** Green on every loop. pytest 472 in about 3 seconds. Golden set sixteen queries, every portfolio query on portfolio 3, clean twice after the move, no `retries` line. Runner **12/12** after the ledger became the source of holdings. Commit count: `git rev-list --count baseline-v1..HEAD`.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Grep for the caller, not the registration, and for the reader
of a return value. The previous handoff named portfolio 2 "Demo Portfolio";
it was portfolio 1. Both are gone now, but the claim sat unchecked for a
session.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Order 1 is built; Order 2's first item, the ledger, is built; its second, currency, has a reference and no code. Its last section says when to stop and think. |
| `docs/benchmark.md` | **The definition of done.** 12 cases, 12 pass; the runner is the status. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Every case has a check. Nothing in it changed this session; it ran once, after the holdings reader changed, and held. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Swept at the end of this session: every entry the session touched carries a "10 September (tenth sitting)" paragraph, the file's own convention. Read at minimum: "The `transactions` table has no portfolio" (the ledger, built, and the delete_portfolio bug it exposed), "No FX conversion anywhere" (Part 8 C and the build order), the six new Hygiene entries, and "Decision 16" under Directions (logged, unchanged). |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1–8. **Part 8 C is new: a foreign-currency position in a euro portfolio, decisions D15–D18.** Never update it to match code output. The workbook's `Ledger` sheet carries A, B and C as formulas, not recalculated by openpyxl. |
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
  arrays move through `shared_data`.
- **Policy lives in config, not code.** `ips.toml` holds every number and
  topic word. The vocabularies are registries: `AGENTS`, `INTENTS`,
  `REQUIRES`, `TERMINAL` in `schemas.py`; the period keys in `config.py`.
  An agent computes; the synthesizer formats; the checker reads published
  shares and divides nowhere.
- **Raise, do not repair.** A span the vocabulary lacks, a typo of a holding,
  two weights in one message: extraction asks back. A sale over the
  position, a ledger row with no portfolio, a missing rate: the pipeline
  stops and says why. A default is a wrong answer with a plausible face.
- **Holdings derive from the ledger (D13).** `transactions` is the record
  of what was bought and sold; a holding is computed from it by
  `quant/ledger.py` and there is no holdings table. Cost basis sums the
  row's `amount`, which is data from the statement (D14), never quantity x
  price recomputed - that is how a second currency enters.
- **Extraction and derivation before the model.** Tickers, periods,
  percentages and the compliance mode are read from the message; the plan
  is derived from the intent and those parameters. The model decides
  intent, `measure`, `group_by`, `status`, confidence and a clarification
  question, and nothing else it emits is read.
- **Selection is rendering.** A formatter selects from a block the node
  computed in full; the selection's values are the block's own words.
- **References before code.** Part 8 A and B before the ledger; Part 8 C
  before any FX code.

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
  on a line, stop. No prompt changed this session; the golden move (six
  queries to portfolio 3) carried its prediction and held.
- Never `commit -a`/`-am`, never `add -A`/`.`; name the files. Never
  rebase, amend, reset, stash. Never edit `.gitignore`.
- **The migration and the reseed are run by hand**, from the shell:
  `alembic upgrade head`, then
  `python src/portfolio_tool/scripts/seed_portfolio.py --reset` when the
  seed changed. A migration is committed unexecuted and the schema test
  written before it is the check that it did what it says.
- **The workbook is closed in Excel before any openpyxl write.** `lsof`
  first; if it is open, close it, every time (KNOWN_GAPS records the one
  time this was skipped). A modified tracked binary is its own commit.

### What I do NOT want

A pure asyncio/regex deterministic version without LangGraph. Prompt rules
added to fix a routing defect (DIRECTION.md). My real portfolio's data in
the repo: it enters last, when everything works. Settled this session: no
more concurrency until independent tools exist (Order 4/5) and a
measurement asks for it; no cached holdings table, since a cache is a
second source - holdings are derived on every read.

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

**472 passed, 21 warnings, about 3 seconds.** Up from 405: the ledger
tests (`test_ledger.py`, 30), the schema tests (`test_transactions_schema.py`,
`test_no_holdings_table.py`), the seed test (`test_ledger_seed.py`), the
reader test (`test_holdings_from_ledger.py`), plus one each for reasoning,
the Sonnet id and the denominator headers. Down by
`test_portfolio_integration.py`, deleted: it asserted nothing and made
the suite's last two live model calls. The fourteen seconds earlier
handoffs recorded were uncached provider calls, not work; the suite at the
previous HEAD also runs in three.

**The golden set has sixteen queries, every portfolio query on portfolio 3.**
Two lines pin failures: the macro query (`errors: 1`) and "Should I
rebalance my portfolio?" (`errors: 1`, no target source). Clean twice after
the move (c94603c, 93290af). The set is blind to `tickers`, `measure`,
`group_by`, `status` and the compliance mode; the runner is the loop that
sees those.

**Runner 12/12**, run once, after `get_holdings` began deriving from the
ledger (be14e4b), predicted and held.

### Branches and tags

`selection` is the working branch, cut from `baseline-v1` at 7fc6474.
`vocabulary` and `compliance` are merged into `baseline-v1`.
`wip/phase7-snapshot` holds rejected Compliance/IPS code; nothing on it is
scheduled. `wip/rag-early` and tag `rag-early-parked` hold the deleted RAG
code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`45b959c05420`** (drop portfolio_holdings), 14 migrations, linear, both
of this session's applied. Tables that matter: `portfolios`,
`transactions` (with `portfolio_id` and `amount`, both NOT NULL), `assets`,
`daily_prices`. **There is no holdings table.**

- **Portfolio 3, "Benchmark Portfolio" — the only portfolio.** Nine ledger
  rows, one buy each, Part 8 A; cost basis 284,500 plus 15,500 cash. Every
  golden portfolio query and every runner case runs against it.
- **Portfolios 1 and 2 are deleted** this session: no purchase dates, no
  ledger possible, nothing read them once the golden set moved. The
  thirteen assets and their prices were shared and are untouched.
- **Reseeding rewrites the nine assets' metadata** to the same values, and
  refuses without `--reset` when ledger rows exist (a rerun would double
  every position). `--reset` clears the portfolio's ledger first.
- A leaked `assets` row, id 10, has no ticker; logged, to be deleted by hand.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  (`claude-haiku-4-5-20251001`). `ANTHROPIC_SONNET` is `claude-sonnet-5`
  since fc8c13c, behind `use_stronger_model`, which is off.
- `openpyxl` is in the venv and the `dev` extras, for the workbook's `Ledger`
  sheet. No LibreOffice: a sheet written with it is recalculated by Excel on
  opening, not before.
- `config.features.observability_enabled` is **false** here. Do not turn it
  on without reading the KNOWN_GAPS entry on the router's own span.
- `portfolio_tool/__init__.py` opens a DB connection at import; the router
  prompt and `agents/extraction.py` import nothing from it at module level.

---

## 4. What the tenth session did

`git log --oneline 70f1829..HEAD` for the list, in order.

**The ledger, built end to end (item 1).** The test over Part 8 A and B
first, imported in a fixture so a missing module is 29 errors and not an
interrupted suite (9f629a9). The schema test, then the migration adding
`portfolio_id` and `amount`, NOT NULL in batch mode (aab2ad8, ace01ff).
The derivation, `quant/ledger.py`, pure: rows in date order, a buy adds
its amount to basis, a sale releases basis at the average and realizes the
rest, the first buy is the purchase date, a closed position is not a
holding, raises on an empty ledger, two portfolios, an unknown type, a
sale with no buy, a sale over the position (ab66cc3; one fixture fixed on
the way, 7cbf799). Cost basis sums `amount`: Part 8 A and B cannot see
that choice, Part 8 C can.

**What reads it: holdings as a view of the ledger, chosen over a cache
and over the seed writing both tables.** The seed writes one buy row per
position (fb8a7b5, a46a522). `get_holdings` derives from the rows and
`get_portfolio_tickers`, the router's context list, is its tickers;
`add_holding` and its inline weighted average became `record_transaction`
with every field required; the wrapper, the demo helper and the demo block
went (715a3e0, b4a5bde, be14e4b). The reader exposed a bug and the commit
fixed it: `delete_portfolio` left ledger rows behind, SQLite reuses ids
and does not cascade, and a reused id inherited them as holdings. Runner
12/12 after. Then the holdings table dropped: model, relationship, two
uncalled editors, the seed's writes, migration 45b959c05420 (42d82fb,
db1ce7e, a48050f, 4a3506f).

**Portfolios 1 and 2 gone.** The six golden queries on them moved to
portfolio 3 with the prediction that every routing field holds; two runs,
identical (c94603c, 93290af). The CLI's example line (4686d2b). The rows
deleted through the manager, assets untouched. `test_portfolio_integration.py`
deleted, item 16 brought forward as the demo helper's only caller (c6241a4).

**Currency, as a reference and not code (item 2).** Part 8 C and D15–D18
in expected_values.md (0aa030c) and the workbook's `Ledger` sheet (cf8eb66):
base currency the portfolio's; a price in the asset's currency, a foreign
holding valued at quantity x price x the spot rate on the price's as-of
date; spot rates a price source, dated, a missing rate raises; cost basis,
average and realized in the base currency. 100 AAPL at 200.00 USD at a
stated 0.9200 with 5.00 EUR fees: 18,405.00 EUR; at 324.96 and a stated
0.8500 spot: 27,621.60, +9,216.60, +50.08%.

**The small items (item 3), each a test first and its own commit.**
`reasoning` into the decision dict (d104250, 82d1d8e); the Sonnet id
(3438fa9, fc8c13c); the denominator label dropped, headers from the block
(75cefdf, 3edf370); the two dead duplicates in `graph.py` (be15869).

**Findings logged, not chased** (all in KNOWN_GAPS): two run-by-hand
scripts calling the deleted `add_holding`; `ensure_asset_exists_helper`
uncalled; the leaked asset row; `Transaction.date`'s `utcnow` default and
`fees`' zero default; the workbook written while Excel held it; the
migration and the reseed as by-hand steps.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- Holdings derive from the ledger on every read; no cache, no second
  table. A cache can be added later as a pure function of the ledger if a
  measurement asks; going the other way is the migration just done.
- Cost basis is the sum of `amount`, not quantity x price +/- fees
  recomputed; the FX column is that choice's falsifier.
- `record_transaction` requires every field, fees and amount included: a
  defaulted fee is a free trade with a plausible face.
- A closed position is not a holding; an empty ledger is no holdings and
  the node refuses it, as before.
- Portfolios 1 and 2 deleted; every portfolio loop on portfolio 3.
- The holdings table dropped rather than left unread.
- D15–D18, the currency decisions, in the reference before any code.
- `test_portfolio_integration.py` deleted, not rewritten.
- The denominator label gone; headers name each denominator from the
  block, decision references out of the answer text.
- Async: not more of it until Order 4/5; the nodes are already async.

**Pending — decide before writing code.**
1. **The FX code**, in this order, each a test first: tests over Part 8 C;
   a rate table and its migration (D17); the analysis node multiplying by
   the rate with both as-of dates published; the formatters naming
   currencies (D18); `position_pnl` taking a rate. The runner should not
   move on portfolio 3.
2. **Order 2 items 3 and 4**: the price source; the personal IPS as a
   local file.
3. **`Transaction.date` as a Date with no default, `fees` with none**: a
   model-and-migration change.
4. **The two scripts calling `add_holding`** (`tests/check_portfolio_manager.py`,
   `tests/system_diagnostic.py`): record buys with dates, or delete.
5. **`ensure_asset_exists_helper`**: delete after the grep.
6. **The leaked asset row id 10**: delete by hand.
7. **Records and rules for the span and two-weights clarifications**, when
   a case asks.
8. **A window return** as a measure with a reference; not an extraction rule.
9. Replace the two verbatim benchmark few-shots (1.1, 1.3); the
   rebalancing few-shot with four percentages.
10. The hypothetical mode's instrument type ("11% into a new ETF").
11. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the
    IPS — both edit `docs/IPS.md`.
12. D9's wording; the workbook's `Decisions` sheet (D8, D9, D10–D18, `C91`).
13. "Optimization failed: None": the message, and the two-asset failure.
14. A golden line for 2.3.
15. **Company names, German phrasings, the softer 3.5**: logged, not
    built; decision 16 is their path.
16. **`group_by` as the subject kind of a compliance finding**, when a case asks.
17. **Realized gains and closed positions as figures the system reports**:
    the derivation carries `realized`; no case asks; a closed position's
    realized gain is currently not returned at all.

---

## 6. Where we stand against the benchmark

12/12. Level 1, Level 2 and Level 3 in full. benchmark.md's notes are
current; nothing in it changed this session.

---

## 7. Next steps, in order

**The FX code, against Part 8 C.** First `tests/test_fx.py` over Part 8 C:
the derived holding from one euro-amount row (18,405.00, 184.05 EUR), and
the valuation at a stated rate (27,621.60, +9,216.60, +50.08%), written to
fail before any rate exists. Then the rate table, `fx_rates`
(pair, date, rate, source), with its migration, and the fetch beside the
price fetch with the same cache and as-of rules. Then the analysis node:
market value = quantity x price x rate when the asset's currency differs
from the portfolio's, both as-of dates published, a missing rate raising.
Then the formatters: every figure names its currency. Each a decision
first; the runner is not expected to move, since portfolio 3 is USD
throughout, and a second synthetic portfolio in EUR is the fixture, in
tests, not in the seed.

**Before any of it**, on opening the workbook: section C of the `Ledger`
sheet must show 18,405.00, 184.05, 27,621.60 and 50.08%. If not, the
sheet is wrong and Part 8 C in the markdown stands.

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

**A test that exercises exactly the boundary is not a test of crossing
it.** The first sale-larger fixture sold 300 of 300 held, which closes a
position and is not an error; the derivation was right and the fixture
was wrong. State the quantity held before writing the quantity sold.

**A deleted row's id comes back.** SQLite reuses a deleted portfolio's id
and enforces no cascade unless told to; rows left behind become the next
portfolio's. Every delete deletes its children explicitly, and the test
for it creates, records, deletes and counts.

**A collection error is a blind suite.** A test file importing a module
that does not exist yet stops pytest before the other 405 run. Import the
module under test in a fixture so each test fails for its own reason and
the rest still run.

**Measure a timing change before explaining it.** The suite went from
fourteen seconds to three across a change that could not have removed
work; running the suite at HEAD with the change set aside showed the
fourteen were never the code's.

**A check that says stop has to stop the script.** The workbook write ran
after its own open-file check reported Excel holding the file. The check
was correct; the script did not act on it.

**Read the model's own output before choosing between readings; a record
beats a re-read; prose that names a plan classifies by proxy; a green
suite can hide a broken call site; registration is not reachability;
predict from the whole prompt; a refusal is an honest failure; write the
falsifier; design the failure direction of a model-owned field; a fixture
that passes in both states is no check — still true.** Earlier handoffs'
§8 have the examples.

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

# by hand, after a migration or a seed change:
alembic upgrade head
python src/portfolio_tool/scripts/seed_portfolio.py --reset
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3s, no model calls | Do the components still work; does the ledger reproduce Part 8 A, B to the cent; does the schema have the columns and not the table; does every table row derive its plan; does extraction read every recorded prompt the same way; does the node publish the block the checker reads; does each formatter select what its parameters say |
| CLI | ~3s, one call | What is it actually doing — the plan, the parameters, the reasoning line (prints since 82d1d8e), what was asked back, the answer's header |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines on portfolio 3 or none, two pinned failures, `retries` when a plan was rejected). Blind to `measure`, `group_by`, `status`, `tickers` and the compliance mode |
| Benchmark runner | ~1.5min, cents | How many cases pass; the only loop that sees the compliance mode, the second turn, and a model-owned field set where it should not be |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second
miss on a line. The runner is per capability commit.
