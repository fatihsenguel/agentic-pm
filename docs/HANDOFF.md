# AGENTIC_FINANCE — Session Handoff

**Session date:** begun 13 September 2026, ended 14 September (sixteenth session). Regenerated at its end.
**Branch:** `selection`, at the commit that lands this file (the one after `f4713d0`). **`baseline-v1` is at 20160b0.** No fetch was made this session; at the fifteenth session's fetch `origin/baseline-v1` and `origin/selection` were both at 20160b0, and a remote-tracking ref that old is not evidence of what the remote holds now. Local `selection` is 65 commits ahead of the baseline with this file, 34 of them this session's, and **none is pushed**. It has no upstream configured, and `origin`'s push URL is `no_push`: the owner pushes, from elsewhere or by naming the URL.

**State:** pytest **918 passed, 6 xfailed**, up from 747. The golden set and the runner were **not run**: nothing in routing, prompts or answer text changed, and both last ran clean in the fifteenth session. One CLI run of three prompts on 13 September, after `config.py` and `database_setup.py` changed, each answer as expected. Commit count: `git rev-list --count baseline-v1..HEAD` — 65.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session five claims of mine were wrong before they were
checked, and each is recorded where it happened: a rule for a fiscal year's
own report committed into two references before it was measured over whole
documents (F11); a count of "the three documents" for forms listed from two;
"the fourteen financial filers" for thirteen; a module docstring describing
work its commit did not hold; and clause wording that said "the codes this
clause lists" in a clause that listed none. A record says what the tree holds,
not what the next step is.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the philosophy check exists as pure modules, now with PHI-3.2's industry exclusion; the filings reader is built as far as its reference allows and cannot yet run against EDGAR or feed the screen (§7). Its last section says when to stop and think. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. Level 4: six research cases, none running, the prediction ledger as their eval set. Unchanged this session. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Twelve cases; Level 4's checks are written first when the node decision starts. Unchanged. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Every open entry carries what it blocks: **84 open, 16 a named Order, 68 nothing, 81 to carry** once the three resolved-in-body entries are discounted. Two of them, a VaR question answered with per-holding volatility and two scripts that cannot run, came from a capability inventory read after this file was regenerated. Read the Order-4 ones. **New and worth reading whole: "Order 4, the filings reader: Parts 12 and 13, and what is built", and "PHI-3.2's code list fails open, and a code carries no date".** |
| `tests/golden/expected_values.md` | Hand-computed and transcribed reference, **Parts 1 to 13**. Part 10 gained **section F**, PHI-3.2 as `excluded_industry` with **D34 and D35**. Part 12's D26, D27, D29 and D30 were revised this session and Part 12 A gained each year's own annual report. **Part 13** holds D26 to D33 against Alphabet and JPMorgan, F6 to F11, each year's own report, and thirteen financial filers' SIC codes. Part 11 is reserved and not computed. Never update it to match code output. |
| `docs/IPS.md` | The policy, synthetic. Unchanged. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen clauses. **PHI-3.2 was rewritten this session** as an industry exclusion that lists its seven SIC codes; six clauses are now checkable and eleven are statements. |
| `docs/WATCHLIST.md` | Two synthetic candidates, Alphabet and Adobe, four predictions due early 2027. Nothing reads it. |
| `docs/PM-Assistant — Roadmap.md` | Stale; DIRECTION.md's Order supersedes it. |

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`.
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half that is tools and done,
and a judgement half whose first tools exist as pure modules - the screen,
and now a reader of filed figures - and are not yet joined to each other or
to the graph. The router is scaffolding until the tool layer is complete.
**No deadline. Correctness over speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** True today by construction.
  The EDGAR document never leaves the provider: it returns filtered facts,
  and nothing stores the document.
- **Policy lives in config, not code.** `ips.toml` and `philosophy.toml` hold
  the two policies' numbers, **and every number is in the document first**:
  PHI-3.2's codes went into PHILOSOPHY.md before `philosophy.toml`.
  `config.toml` holds five fetch intervals, `filings_fetch_interval_days`
  the new one. A definition nobody would set differently is code: the field
  list (`filed_figures.FIELDS`), D27's year window, D29's forms.
- **Two policies, two questions.** The IPS says what may be held; the
  philosophy says what is worth wanting.
- **The policy belongs to the portfolio.** What a philosophy belongs to is
  not decided (pending 30).
- **Raise, do not repair.** This session's form of it: a field no tag yields
  is **named in the block and never filled** (D30 as revised), and the check
  stops where a clause needs it; a company with no SIC code is never assumed
  not to be a bank (D35).
- **Typed facts are not a source.** A company's figures come from the
  reader; typed figures stay in tests.
- **A figure is as filed, and which vintage is a decision.** D29: latest filed
  on a 10-K, 10-Q or 8-K or an amendment, as of the check's date.
- **A year counts from its own annual report** (D21 as measured in Part 12
  A): a filing's own year is the latest year end it carries.
- **A reported figure and a modelling choice are different things** (D32).
- **Net debt nets cash only** (Part 12 F).
- **An exclusion is decided before any figure is read** (D34).
- **`config.toml` holds policy; `.env` holds identity.**
- **References before code, and measured over the whole source.**
- **No price forecasts as numbers.**

### How I work on this

- Every change starts as a written decision in plain words: what it is, what
  changes on a yes, the rejected alternatives, which loop sees it. Then one
  commit per layer, tests written first and **seen failing against a wrong
  version for their own reason**, `git status --short` and the diff read
  before each commit, and the word yes before it lands; "okay" is not one.
- **Check a shape against the invariants before bringing it.**
- **Two changes in one file are still two commits**, split by staging hunks
  (`git apply --cached --unidiff-zero` on a patch of the chosen hunks), used
  three times this session.
- **A claim about an external schema is checked against a fetched document**;
  this session every EDGAR claim came from a document pulled from
  `data.sec.gov`, and nothing from `www.sec.gov`, which refuses a generic
  User-Agent.
- **A rule taken from five years is measured over every year the source
  holds before it goes into a reference.**
- **Checking against a wrong version runs with bytecode caching off**
  (`PYTHONDONTWRITEBYTECODE=1`, the module's cached file deleted).
- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting a symbol;
  grep for the caller and the reader.
- **The migration, the reseed and any rewrite of stored rows are run by
  hand**, and I paste what the command printed. Two migrations this session,
  both applied by me, both outputs pasted.
- **PHILOSOPHY.md and IPS.md are mine to edit.** A session brings the wording.
- No emoji in code. A count I predict is a count I add up.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect. My real portfolio's data in the repo: Order 6, last. No cached
holdings table; no fallback rate, currency or policy; no adjusted close; no
environment switch for which policy runs. **No invented figures as a runtime
source, and no price a stock will reach anywhere.** No mutation testing until
necessary. No widening of the router's schema to make it a better classifier.
**No SIC code range recited from memory, and no number in a TOML that the
document does not state.**

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

**918 passed, 6 xfailed, 26 warnings, about three seconds.** Up from 747 by
the provider (32), the filed-facts table (69), its cache record (9) and fetch
(8), the field list (17), the assembler (18), the loader type (9) and the
screen's exclusion (9, one of which holds the committed philosophy's codes
to Part 10 F). **One run on 14 September took 1 minute 42 seconds** and passed; the
rerun took 3.06 seconds with no test above 0.6. Not diagnosed; the slowest
tests are the macro integration tests in `test_phase5_4_integration.py`,
which reach the macro data path. The six expected failures are the
statements-method pin.

**The golden set: not run.** `expected.txt` unchanged since 93290af.
**The runner: not run.** Both last ran clean in the fifteenth session, and
nothing since has changed routing, a prompt, or an answer's text.
**The CLI, once, 13 September, three prompts:** the allocation answer
(priced at the 2026-09-11 closes, five classes); the policy check (seven
breaches against Part 7's eight, the known cents pair); and "Does Alphabet
clear my philosophy?" routed `out_of_scope`, nothing run, no recommendation,
which is correct until the research node exists.

**Level 4: 0 of 6 cases run.**

### Branches and tags

`selection` is the working branch, 65 ahead of the baseline, unpushed.
`baseline-v1` sits at 20160b0. `compliance` and `vocabulary` are fully merged
into `baseline-v1`. `wip/phase7-snapshot` holds rejected Compliance/IPS code.
`wip/rag-early` and tag `rag-early-parked` hold the deleted RAG code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`97d3708851e5`**, 23 migrations, linear, all applied. **Two migrations this
session, applied by me**: `302903e3d966` (`filed_facts`) and `97d3708851e5`
(`filed_fetch_metadata`). No reseed. Tables that matter:

- `portfolios`, `transactions`, `assets` (9 rows, no CIK column, and an
  `industry` label typed by hand into the seed with no source column).
- `daily_prices`: **6,957 rows and not a fixed count** - it was 6,939 at the
  start of the session and grew by two trading days when the CLI ran.
- `filed_facts`: **empty.** One row per filed fact, `value` as text, D26's key
  as two partial unique indexes.
- `filed_fetch_metadata`: **empty.** One row per company, `last_fetch_time`
  required.
- `fx_rates`, `fx_fetch_metadata`: empty. `financial_statements`: 65 rows,
  neither the reader's store nor a source. `macro_data`: grows, do not pin.
  `shares_history`: no `source` column.

**There is no holdings table.** Portfolio 3, "Benchmark Portfolio", is the
only portfolio: nine ledger rows, cost basis 284,500 plus 15,500 cash, USD,
policy `ips.toml`.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py`, `test_screening.py` | nothing in the graph; `screening.screen` takes it loaded |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py` | nothing |

**Fixtures in `tests/golden/`:** `edgar_facts_aapl.csv` (93 rows),
`edgar_facts_googl.csv` (82), `edgar_facts_jpm.csv` (53), and
`edgar_submissions.csv` (14 rows: Alphabet and thirteen financial filers'
SIC codes). They are samples of documents, not whole documents: a filing is
present only through the rows cited from it, which is why some assembler
checks read chosen sections. The documents themselves are not committed.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`.
- **yfinance 1.7.0.** The price method passes `auto_adjust=False`.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` from the
  environment and raises, naming the key and `.env`, when it is missing or
  blank; `EdgarProvider` calls it before any request. **The real value is not
  set**, so the provider has never fetched from EDGAR. Every document this
  session was fetched by hand from `data.sec.gov` with a generic User-Agent,
  which that host served; `www.sec.gov` refuses one with HTTP 403.
- `config.toml` carries five fetch intervals, `filings_fetch_interval_days = 7`
  the newest. A missing key raises at its reader.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import. The whole suite on a scratch copy:
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest`.
  This session a copy with a new table created from the model, not by
  Alembic, ran the fetch tests before the migration was applied.
- `alembic.ini` names the database by a relative path: run from the project root.
- The CLI's quit command is `:q`.

---

## 4. What the sixteenth session did

`git log --oneline f4713d0~33..f4713d0`, plus the commit that lands this
file. Thirty-four commits, all of them this session's.

**Item 1, the second filer and a bank (5228857 to 8f92f58).** Alphabet and
JPMorgan fetched and held against D26 to D33 as Part 13: which each
confirms, cannot exercise, and contradicts. Contradictions found and decided:
D26's key needs `start` (a 10-Q carries a quarter and a year to date under
one tag, end and accession); D29 needed a list of the forms that file a
figure (JPMorgan's proxy statement repeats five years of net income rounded
to the hundred million, and is the latest filing); D30's premise that the
tags in one list measure one thing fails on a re-presentation that reached
back one year (F7) and on subtotals a filer does not present (F8). On the
owner's two questions: JPMorgan's missing gross profit and operating income
are D30 working, and what they show is an order - the exclusion before the
figures; Alphabet's share count is the filer's own total and not a sum, and
the arithmetic moves into the free cash flow yield's formula.

**Item 2, the reader (8a33ff1 to 98b8ff6).** D27's window, the provider
with the contact reader, `filed_facts`, the cache record and the fetch, the
field list, the reference for each year's own annual report, D30's raise
moved to the check, and the assembler. The first rule for a year's own report
was wrong for every filer's first two years and was corrected the same day
(4afc845, F11). A wrong version run in place once executed a previous
version's bytecode and hid an uncaught case, which then got its test.

**Item 3, `excluded_industry` (c1453cd to 380900c).** Twelve more financial
filers' SIC codes (Goldman Sachs is a broker-dealer by its code, not a bank;
Flagstar's code is out of date), Part 10 F with D34 and D35 and seven codes
(brokers count, insurance brokers do not), the loader type, the screen arm
decided before any figure is read, and PHI-3.2 rewritten by me in
PHILOSOPHY.md with its codes, then `philosophy.toml`.

**The sweep (11aeb4e, f4713d0).** Five KNOWN_GAPS entries added and four
corrected in place; Part 12's caveat pointed at Part 13.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- D26's key is `(tag, start, end, accn)`.
- D27: a year is 350 to 380 days, `end` minus `start`, both included.
- D29: a figure is filed on a 10-K, 10-Q or 8-K or an amendment; any other
  form is not a vintage.
- D30: a field no tag yields is named in the block and not filled; the check
  stops where a clause needs it.
- D21 as measured: a filing's own year is the latest year end it carries; a
  year no filing reports as its own is not a year.
- The provider returns filtered facts and every vintage; the table stores
  every fact it returns; the assembler picks.
- `filed_facts.value` is text; D26's key is two partial unique indexes; the
  cache record has no pull date per row.
- `filings_fetch_interval_days = 7`; the rate limit waits for a caller that
  loops over companies.
- The assembler builds only `years`, as of a date, with provenance, and does
  not feed the screen until the bridge exists.
- **PHI-3.2 is `excluded_industry`** over 6021, 6022, 6035, 6036, 6211, 6311
  and 6331; decided before any figure is read (D34); a listed code is one
  excluded finding and nothing else, an unlisted one a pass, no code a stop
  (D35). Its id is kept, and it expires when the philosophy has clauses for
  banks and insurers.

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve.
6. The rebalance tools' fixed euro sign.
9. Records and rules for the span and two-weights clarifications.
10. A window return as a measure with a reference.
11. Replace the two verbatim benchmark few-shots.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
14. "Optimization failed: None".
15. A golden line for 2.3.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding.
18. Realized gains and closed positions.
22. Volatility over as-traded closes or a total-return series.
23. The answer text naming the price source.
29. **The node for the screen**, after the bridge.
30. What a philosophy is bound to.
32. Two formatter headers carry an emoji.
35. A rank selection in extraction.
36. What `reasoning` is for.
38. The CLI's identical-answer check.
39. Three KNOWN_GAPS entries resolved in their body and unmarked in their heading.
41. **Still mine:** writing what nets against debt (A, cash only) into
    PHI-3.1's clause text, which does not say.
43. **The real `EDGAR_USER_AGENT` in `.env`**, mine; the reader exists.
45. The tool-boundary pass, tagged Order 5, with its trigger written down.
46. **Where NOPAT's stated tax rate lives, and what it is** (D32). Mine.
47. **`net_debt` from the three borrowing fields, as a metric key with its own
    reference row** (D33, Part 12 F's "also open"), and whether a finance
    lease is a borrowing (Part 13 E5).
48. **Part 13 E's questions 3, 4, 6 and 7:** when a tag belongs in a field's
    list; `gross_margin` and `net_debt_to_ebitda` for a filer that presents no
    gross profit or combined D&A; the two securities fields no metric reads;
    which share count, and the free cash flow yield for more than one class.
49. **A SIC code on the block:** a provider method for the submissions
    document, and the field on the block.
50. **Ticker to CIK**, with the node.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12 at the fifteenth session's two runs; not run this
session because nothing they see changed. Level 4: defined, six cases, none
with a check, none running. 4.6's bank variant is now decidable by the screen
on a block that carries a SIC code; no block carries one yet. The ledger has
four open predictions and no scored one.

**What a Level 4 pass means, and what it does not.** Level 4's cases pass on
the answer being well-formed, and the only instrument that can say whether a
judgement was any good is the prediction ledger, which holds my predictions
and scores nothing until early 2027. Read n/14 as a count of well-formed
answers and never as the system being good at research (benchmark.md, d3ccd86).

---

## 7. Next steps, in order

**1. The bridge between the block and the metrics** - the next capability
commit, and blocked on me. `quant/fundamentals.py` reads one `tax_rate` and
one `debt`, as Part 10 A typed them; the reader's block carries
`effective_tax_rate` and three borrowing fields, and Decimals where the
metrics accept floats. Decisions first: 46 and 47, and where a filed figure
stops being exact. Then a reference row by hand for `net_debt` and for NOPAT
at the stated rate, Part 10's recomputation if its synthetic block changes
shape, and only then the code, test first. Until this lands, no filed figure
reaches a finding.

**2. A SIC code on the block** (49): the submissions method on the provider,
held to `edgar_submissions.csv`, and the field the screen already reads.

**3. The real contact and one live fetch.** When I set `EDGAR_USER_AGENT`,
one company fetched through `update_filed_facts` and assembled, its FY2021 to
FY2025 held to Part 12 B or Part 13 B by hand: the first time the pipeline
touches EDGAR instead of a stand-in.

**4. Decision 29, the node**, after the bridge: runner checks for 4.1 and 4.6
written first and seen BLOCKED; the intent and agent in the registries; the
node over a synthetic state; the formatter; the golden line and the prompt,
golden twice with the prediction written first. **The compliance gate is
designed with it, not retrofitted under it.** W-1 cannot clear the screen on
filed figures until 48 is decided: Alphabet stops on PHI-2.1, PHI-2.2 and
PHI-3.1 (Part 13 B).

**5. Then the valuation pipeline** with Part 11 by hand, and prediction
scoring with its Part.

### Later, with reasons

- 3.2's rewrite and Part 2's boundary: at the commit that makes 4.3 answerable.
- The tool-boundary pass (45): its trigger is the first benchmark case that
  fails for want of expression rather than capability.
- PHI-3.2's code list: one measured code at a time; ranges only once the real
  contact can fetch the published SIC list.
- D29's form list: one measured form at a time.
- A total-return series for volatility (22), with a recomputed Part 4.
- The 1:42 suite run, if it recurs: `--durations` on that run.

---

## 8. Rules learned the hard way

**A rule taken from part of a source is measured over all of it before it
enters a reference.** The earliest 10-K carrying a year was the year's own
report on FY2021 to FY2025 for three filers, went into Part 12 A and Part 13
F, and was wrong for every filer's first two years, which only appear as a
later report's comparatives. It was caught before the assembler was written
because the assembler's test demanded the rule on every year, and F11 now
holds it.

**A number the TOML carries is a number the document states.** The approved
PHI-3.2 wording said "the codes this clause lists" and listed none; the codes
would have lived only in config and a test reference. Caught before the TOML
commit, because `test_philosophy.py` copies every number from the document.

**A wrong version checked in place can run the previous one's bytecode.**
Same size, same second, stale compiled file: one wrong version reported
another's failures and hid a real gap. Bytecode caching off, cached file
deleted, before every such run.

**A fixture is a sample of a document, not the document.** A filing appears
in it only through the rows cited, so a rule about a filing (its own year)
is right on the fixture only where every year it reports is cited. The tests
say which sections they read and why.

**One witness is one witness, twice over.** Two more filers contradicted
three of eight decisions taken on Apple, D26, D29 and D30, and showed a
fourth, D33's raise, could not be implemented as written; a bank's SIC code was one of eight
codes the clause needed, and the second financial filer fetched was not a
bank by its code at all.

**A check that passes against every wrong version is not a check.** The
provider's "no two facts share a key" passed against three wrong providers
and was removed; the key is held by the table's schema test, where inserting
rows shows SQLite's two NULLs that never collide.

**A test fixture that leaks a session holds SQLite's write lock**, and an
unrelated committed test fails as "locked": close sessions on every path.

**A form type, a count, a list: add it up from the source, not from what was
listed.** "The three documents" when forms were listed for two; "fourteen
financial filers" for thirteen.

**An invariant is checked against the code, not read as a description**;
**a record says what the tree holds, not what the next step is**; **read the
diff of a file you did not write before staging it** - still true. The
fifteenth session's §8 has the examples. The invariant sweep was not redone
this session; nothing this session touched the graph, and invariant 5's
newest form is D30 as revised: a figure no tag yields is named, never filled.

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

# what the database says it is at (expected 97d3708851e5):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# nine assets; daily_prices and macro_data move, do not pin them:
sqlite3 data/portfolio.db "select count(*) from assets;"

# the filings reader's tables, empty until a live fetch:
sqlite3 data/portfolio.db "select count(*) from filed_facts; select count(*) from filed_fetch_metadata;"

# the whole suite on a scratch copy:
DATABASE_URL="sqlite:///$PWD/scratch.db" USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest

# a check run against an edited, deliberately wrong module:
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/<file>.py

# the reader and the exclusion:
pytest -q tests/test_edgar_provider.py tests/test_filed_facts_schema.py \
  tests/test_filed_fetch_metadata_schema.py tests/test_filed_facts_fetch.py \
  tests/test_filed_fields.py tests/test_filed_years.py tests/test_screening.py

# push, by the owner only, naming the URL because the push URL is no_push:
git push https://github.com/fatihsenguel/agentic-pm.git selection
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3s, no model calls | Do the components still work; does the ledger reproduce Part 8, every stored close Part 9, the checker Part 7, the metrics and the screen Part 10 including PHI-3.2; does the provider return Part 12 and 13's rows and drop what D27 and D29 drop; does the assembler date each year by its own report and name what it cannot fill; is every document held to its config |
| CLI | ~4s, one call | What it is actually doing: the plan, the parameters, the reasoning line, which policy file loaded, whether the provider was called |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines, two pinned failures). Blind to parameters, answer text, and everything under `filed_figures`, `filings`, `providers/edgar` and `screening`, which the graph does not reach |
| Benchmark runner | ~1.5min, cents | How many cases pass. Blind to the judgement half until Level 4's checks exist |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text.
