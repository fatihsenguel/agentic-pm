# AGENTIC_FINANCE — Session Handoff

**Session date:** 10 September 2026 (thirteenth session; regenerated at its end)
**Branch:** `selection`. `baseline-v1` was fast-forwarded to 191829b before this session and both were pushed there; fifteen commits since, this file included, not pushed.
**State:** Green on every loop I ran. pytest 645 passed and 6 expected failures in about three seconds, nine on some runs. The runner and the golden set were not run this session: no routing changed, no prompt changed, no answer text changed, and `expected.txt` is as it was. Commit count: `git rev-list --count baseline-v1..HEAD`.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Grep for the caller, not the registration, and for the reader
of a return value; and read the plan table before choosing who publishes a
value. This session I had DataAgent publish the policy path and found on
inspection that two of the three compliance modes never run DataAgent; the
commit and its removal are both in the history. A claim in a document is a
claim like any other, and so is a plan I wrote an hour ago.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Order 1 is built; Order 2's first three items, the ledger, the currency and the price source, are built; its fourth, the personal IPS, has its binding built and its document and portfolio still to come, which are mine. Its last section says when to stop and think. |
| `docs/benchmark.md` | **The definition of done.** 12 cases, 12 pass on the last run (eleventh session); the runner is the status. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Every case has a check. Nothing in it changed this session and it did not run: nothing under `src/` changed an answer's text. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Swept at the end of this session. Read at minimum: "The personal IPS: bound to the portfolio, grown one clause at a time" under Directions (the whole of this session's main item, with the rejected shapes), "`get_financial_statements` returns nothing, on every call, silently" under Hygiene, "The tables the agents do not read" and "Mutation testing, once, over the pure modules" under Directions. |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1–9. **Part 9 is reproduced by the database, and since this session the suite says so on every run**: `test_stored_closes_are_the_print.py` holds all 2,268 committed cells to the stored closes. Never update it to match code output. The workbook was opened and saved in Excel last session. |
| `docs/IPS.md` | The policy, synthetic. `ips.toml` is derived from it and is the policy portfolio 3's row names. Do not edit `docs/IPS.md` casually; my personal one is a separate file outside the repository, named on my portfolio's row. |
| `docs/PM-Assistant — Roadmap.md` | Stale, header lists what is superseded. DIRECTION.md's Order supersedes its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.16% v 12%, JNJ 10.05% v 10% at the 09-04 closes); the runner asserts structure. Today's CLI run reported seven breaches against Part 7's eight, which is that pair crossing.

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public; the README is the short one from ab813ed)
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
  topic word of the synthetic policy; `config.toml` holds every fetch
  interval, and a missing file raises. The vocabularies are registries:
  `AGENTS`, `INTENTS`, `REQUIRES`, `TERMINAL` in `schemas.py`; the period
  keys in `config.py`; the clause types in `ips.py`. An agent computes;
  the synthesizer formats; the checker reads published shares and divides
  nowhere; a formatter reads the currency from the block and never assumes
  one.
- **The policy belongs to the portfolio (this session).** `portfolios.ips_path`
  names the file a portfolio is checked against: the committed `ips.toml`
  for the benchmark portfolio, by a relative path the loader anchors to the
  project root; a personal file outside the repository, by an absolute
  path, for mine. The compliance node resolves it from the row in every
  mode; the loader has no default; no portfolio is no policy. Two
  portfolios in one database are checked against two policies, and the
  benchmark keeps its own.
- **Raise, do not repair.** A span the vocabulary lacks, a typo of a holding,
  two weights in one message: extraction asks back. A sale over the
  position, a ledger row with no portfolio, a missing rate on the price's
  date, a holding with no currency, a portfolio with no currency or no
  policy, a holding with no cost basis, a config with no interval, a
  policy clause with a type the checker does not know: the pipeline stops
  and says why. A default is a wrong answer with a plausible face.
- **Holdings derive from the ledger (D13).** `transactions` is the record
  of what was bought and sold; a holding is computed from it by
  `quant/ledger.py` and there is no holdings table. Cost basis sums the
  row's `amount`, which is data from the statement (D14), carried on the
  summary and read by the allocation layer, never recomputed.
- **A rate is a price source (D17).** Stored per day with a date and a
  source, fetched under the price cache's rules, keyed by base and quote
  with the rate meaning base units per one unit of quote. A foreign holding
  is valued at quantity x price x the rate on the price's as-of date (D16),
  and both dates are published.
- **A close is the print (D19).** The exchange's official closing price as
  traded, split-adjusted and nothing else. The provider asks for it
  unadjusted; every row carries its source; when two sources disagree the
  exchange's print wins and nothing averages (D20). Part 9 is the
  check, and since this session the suite holds every stored cell of the
  window to it.
- **Every figure names its currency (D18).** Cost basis, average price,
  market value and P&L are in the portfolio's base currency; the quote is
  in the asset's; the answer says which is which and prints the rate it
  went through.
- **Every row names its source, from one statement of the name.** Price,
  rate, statement and macro rows carry the provider's name, written from
  `provider.name`, defaulted nowhere on any model or DTO (this session
  closed the last two).
- **Extraction and derivation before the model.** Tickers, periods,
  percentages and the compliance mode are read from the message; the plan
  is derived from the intent and those parameters. The model decides
  intent, `measure`, `group_by`, `status`, confidence and a clarification
  question, and nothing else it emits is read.
- **Selection is rendering.** A formatter selects from a block the node
  computed in full; the selection's values are the block's own words.
- **References before code.** Part 8 A and B before the ledger; Part 8 C
  before any FX code; Part 9 before the provider changed. For the
  personal policy: a Part 7-style reference for a clause before its
  checker, and a Part 8 reference for my real portfolio before any figure
  about it is trusted.

### How I work on this

- Every change starts as a written decision: what it is, what each rule
  means, what changes if it is taken, the rejected alternatives, which loop
  sees it and what it will show, in plain words. Then one commit per
  layer, tests written first and seen failing, `git status --short` and
  the diff read before each commit, and a yes before it lands.
- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting any symbol;
  grep for the caller and for the reader of a return value; **read the
  plan table (`TERMINAL`, `REQUIRES`) before deciding which agent
  publishes a value the next one reads.**
- **A prompt change is a hypothesis.** Line-by-line prediction in the commit
  message before the run; golden twice. After the second failed prediction
  on a line, stop. No prompt changed this session and the golden set did
  not run.
- Never `commit -a`/`-am`, never `add -A`/`.`; name the files. Never
  rebase, amend, reset, stash. Never edit `.gitignore`. An edit of mine
  that sits in a file about to change gets its own commit first, so it
  does not ride into another message.
- **The migration, the reseed and any rewrite of stored rows are run by
  hand**, from the shell, from the project root: `alembic upgrade head`;
  `python src/portfolio_tool/scripts/seed_portfolio.py --reset` when the
  seed changed; a delete of rows when the stored convention changed. A
  migration is committed unexecuted; the schema test written before it is
  the check; it is applied and reverted on a scratch copy of the database
  before it is committed, and the schema is read back after each
  direction. **I paste what the command printed, not "done."** This
  session: one migration, one upgrade line pasted, the schema read back.
- **A test written against a database that is already right cannot be
  seen failing for its own reason.** Make a scratch copy, break the one
  thing the test is for, and run it there; this session the stored-closes
  test failed on a copy with one JNJ close scaled by a dividend factor,
  naming the row.
- **The workbook is closed in Excel before any openpyxl write.** `lsof`
  first. No workbook write this session.
- A count I predict is a count I add up. The delete statement in §9 has
  its expected results computed from the file, not recalled.
- No emoji in code or comments; I strip the old ones as I go.

### What I do NOT want

A pure asyncio/regex deterministic version without LangGraph. Prompt rules
added to fix a routing defect (DIRECTION.md). My real portfolio's data in
the repo: it enters last, when everything works, as a row whose policy
path points outside the tree. No more concurrency until independent tools
exist (Order 4/5) and a measurement asks for it; no cached holdings table;
no currency symbol table, no rate inverted in code, no fallback rate of 1
and no fallback currency anywhere; no fallback policy: a portfolio names
its file or is refused; no adjusted close in the price table; no second
live provider bolted on for its own sake; no environment-wide switch for
which policy runs.

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

**645 passed, 6 xfailed, 26 warnings, about three seconds; nine on some
runs, unmeasured, entry under the warning inventory.** Up from 606: the
policy-path schema test (9), the manager test (4), the loader's three new
tests, the node's four, the stored-closes test (9), the source-default
test (6), the provider-name test (4 passing, 6 pinned as strict expected
failures on the statements defect), and one folded context test. The
six expected failures are a pin, like the golden set's two: they go red
the day `get_financial_statements` returns rows, and the marker comes
off then.

**The golden set has sixteen queries, every portfolio query on portfolio
3**, two pinned failures (the macro query; "Should I rebalance my
portfolio?"). Not run this session; `expected.txt` unchanged since 93290af.

**Runner 12/12** on its last run, in the eleventh session. Not run this
session: nothing under `src/` changed an answer's text. The compliance
node's console line now names the policy file it loaded; the answer does
not.

### Branches and tags

`selection` is the working branch. `baseline-v1` sits at 191829b, where
this session began, and both are pushed there. `vocabulary` and
`compliance` are merged into `baseline-v1`. `wip/phase7-snapshot` holds
rejected Compliance/IPS code; nothing on it is scheduled. `wip/rag-early`
and tag `rag-early-parked` hold the deleted RAG code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`7b1c4e2d9a05`** (`portfolios.ips_path`), 20 migrations, linear, all
applied; this session's one applied by hand, output pasted, schema read
back. Tables that matter: `portfolios` (`currency` and **`ips_path`**
NOT NULL, no default anywhere; row 3 names `ips.toml`), `transactions`
(`portfolio_id`, `amount`, `date` a DATE, `fees`, all NOT NULL, none
defaulted), `assets`, `daily_prices` (`source` NOT NULL; every close as
traded for the nine holdings, held to the committed series by the suite),
`fx_rates` and `fx_fetch_metadata` (empty), `financial_statements`
(`source` NOT NULL, no default since this session; 102 rows from before
the statements method broke), `macro_data` (`source` nullable, no default
since this session; 185 rows). **There is no holdings table.**

- **Portfolio 3, "Benchmark Portfolio" — the only portfolio.** Nine ledger
  rows, one buy each, Part 8 A; cost basis 284,500 plus 15,500 cash; base
  currency USD, every asset USD; policy `ips.toml`.
- **The nine holdings' price history** is 771 rows each, 2023-08-14 to
  2026-09-09, every row a cent print with source `yfinance`, and the 252
  cells per holding inside Part 4's window equal the committed series to
  the cent on every pytest run.
- **Four leftover tickers** from the deleted portfolios 1 and 2 (AMZN,
  PLTR, SAP, VWO), ids 3, 5, 4 and 9, still hold 9,140 price rows and 632
  rows in six other tables, read by nothing. The delete statement with its
  expected counts is in §9; mine to run, then paste the two counts. 16,079
  price rows and 13 assets in all until then.
- Reseeding rewrites the nine assets' metadata to the same values, writes
  `ips_path = "ips.toml"` on the portfolio row, and refuses without
  `--reset` when ledger rows exist. No reseed this session and none needed:
  the migration filled row 3.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  (`claude-haiku-4-5-20251001`). `ANTHROPIC_SONNET` is `claude-sonnet-5`,
  behind `use_stronger_model`, which is off.
- **yfinance 1.7.0.** `Ticker.history()` defaults to `auto_adjust=True`.
  The price method passes `auto_adjust=False` and reads `Close`; the rate
  and VIX methods take the default, having nothing to adjust.
- `openpyxl` is in the venv and the `dev` extras. No LibreOffice.
- `config.toml` is required: `data_manager.py` raises without it, and its
  `[data_fetch]` carries all four intervals.
- `config.features.observability_enabled` is **false** here. Do not turn it
  on without reading the KNOWN_GAPS entry on the router's own span.
- `portfolio_tool/__init__.py` opens a DB connection at import. `config`
  reads `DATABASE_URL` at import, which is why a scratch copy of the
  database has to be named in the environment before any project import.
  **The whole suite runs on a migrated scratch copy** with
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest
  -q --noconftest`; `conftest.py` would otherwise copy the real file.
- `alembic.ini` names the database by a relative path: `alembic upgrade
  head` runs from the project root or touches nothing. The alembic API
  with `sqlalchemy.url` overridden is how a migration runs on a scratch
  copy.
- **A policy path on a portfolio row** is relative to the project root or
  absolute; `ips.resolve_ips_path` anchors it, the way
  `config.resolve_database_url` anchors the database. The compliance
  node's tests name portfolio 3 on the suite's copy, so they are no longer
  database-free.
- Yahoo quotes a currency pair as `{quote}{base}=X`.
- The CLI's quit command is `:q`. `exit` is sent to the router as a
  question and refused as an order (KNOWN_GAPS, Hygiene). With the
  portfolio cleared (`:p`), a policy question is now refused: no
  portfolio, no policy.

---

## 4. What the thirteenth session did

`git log --oneline 191829b..HEAD` for the list, in order.

**Order 2, item 4: the personal IPS's binding (adec72f to 90fd67c, with
482d3e4).** The decision first, in four questions, before any code. Where
the file lives so that it never enters the repository and the code still
finds it: on the portfolio's row, `portfolios.ips_path`, required and
defaulted nowhere; the migration fills row 3 with `ips.toml` by id and
refuses any other row. `create_portfolio` requires it; the seed writes it.
A relative path is anchored to the project root; the loader lost its
default. Who resolves it: the compliance node, from the row, in every
mode, through `load_portfolio_policy_path`, because the hypothetical and
lookup modes plan ComplianceAgent alone. My first shape had DataAgent
publish it to `shared_data` (c18054c); reading the plan table showed the
hole and I took it back out (352104c) before the node change. What the
system says on a type the checker does not know: the file refuses to
load, as before, and the message now ends with the growth rule. How the
vocabulary grows: one clause at a time through the statement type, the
reference for that clause first, the order in the loader's docstring.
Where my Part 8 reference lives: the same private directory, outside the
repository, with a committed check script when the portfolio enters. The
CLI on portfolio 3 showed the policy line on both modes. Golden set and
runner not run: nothing routed or rendered differently.

**The three small items from §5 (cc3d432 to 71962cf).** Item 24: the
stored closes held to the committed series, cell for cell, on every
pytest run; seen failing on a scratch copy with one JNJ close scaled by a
dividend factor. Item 20: the two `source` model defaults dropped, no
migration needed, checked; then the provider's four literal `yfinance`
sites became `self.name` and the macro DTO's own default went. The
stand-in library that test needed found `get_financial_statements`
returning nothing on every call, a DTO narrower than its writer behind a
blanket except; pinned as six strict expected failures, logged, not
fixed. Item 21: the delete statement, every count added up, mine to run.

**The sweep (5666ee0).** Everything above in KNOWN_GAPS, with the two
Directions entries the owner's questions asked for: mutation testing,
logged with a trigger, and the tables the agents do not read, checked
against callers.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- The policy a portfolio is checked against is named on its row; a
  portfolio names its file or is refused; a relative path is the project
  root's, an absolute one is taken as given. Rejected: an environment
  variable, a home-directory fallback, an ignored file in the tree, a
  `config.toml` mapping.
- The compliance node resolves the policy from the row in every mode; the
  node's "no database" rule narrowed to "no second arithmetic path".
  Rejected: DataAgent in every compliance plan, two sources by mode, the
  committed file when no portfolio is set, a graph-entry resolution.
- A clause with a type the checker does not know refuses the whole file;
  a rule the checker cannot check yet is written as a statement until its
  checker and its reference exist. Rejected: an `unchecked` status.
- The stored closes are held to the committed series by the suite, to the
  cent, not by a script run by hand.
- The two `source` defaults are gone; the macro column stays nullable
  as its own decision; the provider's name is stated once.
- The statements defect is pinned, not fixed.
- Mutation testing is a one-off diagnostic over five pure modules, logged
  with a trigger, not a fifth loop.

**Pending — decide before writing code.** Numbers kept from the twelfth
session's list so that KNOWN_GAPS references still resolve; done items
are struck.
1. **Order 2 item 4, the rest, all mine and outside the repository**: the
   private directory; the personal document in docs/IPS.md's shape; its
   TOML, loaded once by hand so every type is known or a statement; my
   real portfolio's ledger rows from my statements and the Part 8
   reference for them, hand-computed first; then the row with its absolute
   path, and the committed check script (the shape of item 24, on a path I
   give it). Each clause that is to become checkable is its own decision
   in the order the loader's docstring states. **Next, when I say.**
6. **The rebalance tools' fixed euro sign**: logged, not built; the path is
   dead until decision 11.
8. ~~The workbook in Excel~~ done (191829b).
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
18. **Realized gains and closed positions as figures the system reports.**
19. ~~A short README~~ done (ab813ed).
20. ~~Two more `source` columns~~ done (dda3e24, 71962cf).
21. **The four leftover tickers' rows**: the statement is in §9; mine to
    run, and I paste the two counts.
22. **Volatility over as-traded closes or over a total-return series**: a
    Part 4 decision with a recomputed Part 4 beside the present one.
23. **The answer text naming the price source**: a rendering; the runner
    sees it.
24. ~~The csv-versus-database comparison as a committed check~~ done (cc3d432).
25. **`macro_data.source` NOT NULL**: the mirror of the price column; a
    migration filling 185 rows, all one source. Off the benchmark's path.
26. **`get_financial_statements` returning nothing**: the DTO is narrower
    than its writer and reader, and the blanket except hides it. Whether
    the fix is the DTO regaining its fields or the provider passing fewer
    is a decision with Order 4, when it is known whether these tables are
    the judgement half's source at all; the six pinned tests are the
    check.
27. **Mutation testing, once**, over the five pure modules, survivors read
    and logged. Trigger: when I say, or before the checker grows its first
    personal clause type.

---

## 6. Where we stand against the benchmark

12/12 on the last run, in the eleventh session. Level 1, Level 2 and Level
3 in full. benchmark.md's notes are current; nothing in it changed this
session. Not run this session because no answer's text changed; the first
change that touches a formatter runs it.

---

## 7. Next steps, in order

**Order 2, item 4, the rest: mine, outside the repository.** The private
directory and the personal document first; then its TOML and one by-hand
load; then the real portfolio's rows and reference; the row and the check
script last. The code is ready for it: a second portfolio row with an
absolute `ips_path` needs no code change.

**Item 21 when convenient**: the statement in §9, the two counts pasted.

**The first personal clause type, when the document exists**: reference,
type, checker arm, test, flip; and mutation testing (27) over the checker
before it, if I want the survivors read first.

### Later, with reasons

- The judgement half stays unstarted until benchmark.md has a Level 4 and
  the prediction ledger exists (DIRECTION.md).
- `measure`, `group_by` and `status` are the model's classification beyond
  intent; whether they become extraction is a question for the tool
  boundary, not for a prompt.
- A total-return series for volatility (22): with a recomputed Part 4, not
  by flipping the provider flag back.
- The statements defect (26) and the macro column (25): with Order 4, or
  when a case reads those tables.
- More concurrency: when Order 4/5 has independent tools and a measurement
  says a request waits on several things at once.
- The inline `sqrt(w'Σw)` copies; the hot-potato violation in
  `price_data_json`.

---

## 8. Rules learned the hard way

**Read the plan table before choosing a publisher.** I had DataAgent
publish the policy path because DataAgent publishes the currency, and
the hypothetical and lookup modes plan ComplianceAgent alone. The value
would have been absent in exactly the two cases that ask a policy
question without a portfolio check. The plan table was one grep away
and I wrote the commit first. Committed, then taken out, both in the
history.

**A test written against data that is already right has not been seen
failing.** The stored-closes test was green on its first run because the
history was refetched last session. That is not evidence it can fail. A
scratch copy with one close scaled by a dividend factor was, and it
failed naming Part 9 B's row.

**A stand-in finds what the network hid.** The provider test needed a
stand-in library for the statements method, and the method returned
nothing from it: it has returned nothing from the real library too, for
as long as the DTO has lacked the fields the provider passes, and a
blanket except turned the error into an empty list every time. Nothing
reads the table, so nothing noticed. A tool that returns an empty list
on any exception is the repair shape at the boundary.

**Check the schema before promising a migration, again.** The two
`source` defaults were Python-side only; the database had no server
default on either. Checked this time before the decision was brought,
not after.

**A count is added up, not recalled; a policy is per portfolio, not per
process; a raise is honest and a half-loaded policy is not; the output is
the record, not the word; a check on the most recent date passes in both
states; a library default is a claim to check; a required argument breaks
the callers, and that is the point; registration is not reachability;
predict from the whole prompt; a refusal is an honest failure; a fixture
that passes in both states is no check; a collection error is a blind
suite; measure a timing change before explaining it — still true.**
Earlier handoffs' §8 have the examples.

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

# which policy each portfolio is checked against:
sqlite3 data/portfolio.db "select id, name, currency, ips_path from portfolios;"

# the whole suite on a migrated scratch copy, while a migration is pending:
DATABASE_URL="sqlite:///$PWD/scratch.db" USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest

# item 21: the four leftover tickers, every child table by name (foreign keys
# are off). Expected after: 6939 price rows, 9 assets. Paste both counts.
sqlite3 data/portfolio.db "delete from daily_prices where asset_id in (3,4,5,9); delete from shares_history where asset_id in (3,4,5,9); delete from financial_statements where asset_id in (3,4,5,9); delete from quarterly_earnings where asset_id in (3,4,5,9); delete from corporate_actions where asset_id in (3,4,5,9); delete from fundamentals where asset_id in (3,4,5,9); delete from asset_fetch_metadata where asset_id in (3,4,5,9); delete from dividends where asset_id in (3,4,5,9); delete from transactions where asset_id in (3,4,5,9); delete from assets where id in (3,4,5,9); select count(*) from daily_prices; select count(*) from assets;"
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3s, no model calls | Do the components still work; does the ledger reproduce Part 8 A, B to the cent and the rate arithmetic Part 8 C; does every stored close in Part 4's window equal the committed print and does the provider return the print; does the schema have the tables and columns and not the defaults; does every portfolio name its policy and does the compliance node load that file and refuse without one; does every table row derive its plan; does extraction read every recorded prompt the same way; does the node publish the block the checker reads; does each formatter select what its parameters say and name the currency it was given |
| CLI | ~4s, one call | What it is actually doing — the plan, the parameters, the reasoning line, what was asked back, the answer's header, `base_currency` and `fx_rates` in `shared_data`, which policy file the compliance node loaded, and whether the provider was called at all and with which flag |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines on portfolio 3 or none, two pinned failures, `retries` when a plan was rejected). Blind to `measure`, `group_by`, `status`, `tickers`, the compliance mode, every currency and the policy file |
| Benchmark runner | ~1.5min, cents | How many cases pass; the only loop that sees the compliance mode, the second turn, a model-owned field set where it should not be, and the answers' text as a whole |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second
miss on a line. The runner is per capability commit, and per commit that
changes the answers' text.
