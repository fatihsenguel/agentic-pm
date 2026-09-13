# AGENTIC_FINANCE — Session Handoff

**Session date:** begun 11 September 2026, ended 13 September (fifteenth session). Regenerated at its end.
**Branch:** `selection`, at the commit that lands this file (the one after `e318ed8`). **`baseline-v1` is at 20160b0**, and `origin/baseline-v1` and `origin/selection` are both there — confirmed by a fetch this session, which also showed that the fourteenth session's last three commits were never pushed. Local `selection` is thirty commits ahead of the baseline, **none of the fifteenth session is pushed, by the owner's choice**, and it has no upstream configured. `origin`'s push URL is `no_push`; the owner pushes from elsewhere.

**This file was regenerated three times this session**, each time because the session continued past what looked like its end: at e3bfdf6, at 8af72f4, and now. Each was a regeneration and none a patch. This is the one to read.

**State:** Green on every loop. pytest **747 passed, 6 xfailed** in about three seconds, up from 735. The runner ran twice, **12/12** both times; the golden set once, **zero diff on all sixteen lines**. Commit count: `git rev-list --count baseline-v1..HEAD` — 30.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session four of my own claims were wrong and all four
were cheap to check: I said no test asserted the answer's false "Not done"
sentence, and one did by a fragment; I said a string had left the tree when a
copy was still in `risk_manager_agent.py`; I let Part 12 land without the
workbook sheet its own document's rule asks for; and I wrote into KNOWN_GAPS
that the owner had added a line to `.env.example` before anyone had. A record
says what the tree holds, not what the next step is.

**And an invariant is verified, not read.** DIRECTION.md said "compliance is
a gate" for as long as the document has existed and it was false on a live
path the whole time. That was settled this session. Three of the remaining
seven are still sentences no loop can see; §8 has the sweep.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the philosophy check exists as pure modules held to Part 10, the compliance gate is settled, and **the filings reader's decision is taken, Part 12 is written and its second source filled** — the provider method is unblocked (§7). Its last section says when to stop and think. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. **Level 4**: six research cases, none running, the prediction ledger as their eval set, 3.2's expiry rule, and what a passing case does and does not mean. Unchanged this session. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Twelve cases; the Level 4 checks are written first when the node decision starts, blocked probes and all, and the headline becomes n/14. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. **Every open entry carries one line saying what it blocks**, with a count at the top of OPEN: 77 open, 0 blocking the next commit, 15 a named Order, 62 nothing, of which three are closed in their body and unmarked in their heading. Read the Order-4 ones and skip the rest; that is what the tags are for. **New and worth reading whole: "Questions the system cannot express, and which kind each is", and "`config.toml` is tracked and public, so it holds policy and not identity".** |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, **Parts 1 to 12**. Part 10 is the philosophy check; Part 11 is reserved for the valuation range and is not computed; **Part 12 is the filings reader**, with decisions D26 to D33, a committed fixture, its second source filled by the owner, and net debt decided as cash only. The workbook has eleven sheets, `Filings` the newest, with cached values. Never update it to match code output. |
| `docs/IPS.md` | The policy, synthetic. `ips.toml` derived from it and named on portfolio 3's row. Not edited casually. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic: seventeen `PHI-x.y` clauses, five numeric screens and twelve statements. **PHI-3.2 is decided to become a real clause type, `excluded_industry`, and is not yet written** — §5. |
| `docs/WATCHLIST.md` | Two synthetic candidates, Alphabet and Adobe, each a thesis, an entry condition and its predictions; the four predictions are the ledger, due early 2027. Nothing reads it. |
| `docs/PM-Assistant — Roadmap.md` | Stale, header lists what is superseded. DIRECTION.md's Order supersedes its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.16% v 12%, JNJ 10.05% v 10% at the 09-04 closes); the runner asserts structure.

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`.
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half (positions, allocation,
P&L, risk, compliance) that is tools and done, and a judgement half
(research, valuation, a thesis, a prediction) whose first tool exists as pure
modules and whose reader has a reference and no code. The router is
scaffolding until the tool layer is complete. **No deadline. Correctness over
speed. Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** True today by construction:
  one LLM call exists, and it is shown the message and a ticker list. It
  stops being true by construction the day a model reads state.
- **Policy lives in config, not code.** `ips.toml` and `philosophy.toml` hold
  every number of the two synthetic policies; `config.toml` every fetch
  interval; a missing file raises. The vocabularies are registries: `AGENTS`,
  `INTENTS`, `REQUIRES`, `TERMINAL` in `schemas.py`; the period keys in
  `config.py`; the clause types in `ips.py` and `philosophy.py` over one
  loader, `clauses.py`; the metric keys in `quant/fundamentals.METRICS`.
- **Two policies, two questions.** The IPS says what may be held and how
  much; the philosophy says what is worth wanting.
- **The policy belongs to the portfolio.** `portfolios.ips_path` names the
  file; no portfolio is no policy. What a philosophy belongs to is not
  decided (pending 30).
- **Raise, do not repair.**
- **Typed facts are not a source.** A synthetic policy is an honest stand-in
  because the policy is the owner's to state. A company's figures are facts.
- **No answer states a position outside intent `compliance`.** Not because a
  gate exists — §8 — but because the two surfaces that stated one are gone
  and a test fails if either returns.
- **An answer states what it covered, not what it thinks was asked**, and
  names what extraction read and it did not use. Only `tickers` is evidence
  about the question; nothing records a narrowing, so no answer claims one.
- **A figure is as filed, and which vintage is a decision.** D29: latest
  filed, pinned to a pull date, `filed` and `accn` on every row.
- **A reported figure and a modelling choice are different things.** D32: the
  block carries the filer's effective tax rate because it is filed; NOPAT's
  tax rate is a stated assumption in config.
- **Net debt nets cash only** (Part 12 F): the current and non-current split
  on securities is presentation, not liquidity. Revisit only on a candidate
  that fails on that and would pass with current securities netted.
- **`config.toml` holds policy; `.env` holds identity.** A value that names a
  person belongs in the ignored file however mechanical it looks. The tracked
  config and the tracked `.env.example` carry keys and placeholders, never an
  address.
- **Extraction and derivation before the model.**
- **References before code.** Parts 7, 8, 9, 10 and now 12, each before its
  code.
- **No price forecasts as numbers.**

### How I work on this

- Every change starts as a written decision in plain words: what it is, what
  each rule means, what changes on a yes, the rejected alternatives, which
  loop sees it and what it will show. Then one commit per layer, tests
  written first and seen failing, `git status --short` and the diff read
  before each commit, and the word yes before it lands; "okay" is not one.
- **Check a shape against the invariants before bringing it.**
- **Two changes in one file are still two commits.** The split method, used
  twice this session: commit the first, restore the file from HEAD or a saved
  copy, apply only the second, commit. It caught four whitespace-only lines
  that would have ridden into the wrong commit.
- **A claim from memory about an external schema is checked against one
  fetched document before anything is built on it.** This session: five
  predictions about EDGAR's fields, all five confirmed, and a sixth thing
  found that nobody had predicted.
- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting any symbol;
  grep for the caller and the reader; read the plan table before choosing a
  publisher.
- **A prompt change is a hypothesis.** No prompt changed this session.
- Never `commit -a`/`-am`, never `add -A`/`.`; name the files. Never rebase,
  amend, reset, stash. Never edit `.gitignore`.
- **The migration, the reseed and any rewrite of stored rows are run by
  hand**, and **I paste what the command printed, not "done."** None needed
  this session.
- **A test written against data that is already right has not been seen
  failing**, and a test that fails on a signature has not been seen failing
  for its reason.
- A count I predict is a count I add up. No emoji in code.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect. My real portfolio's data in the repo: Order 6, last. No more
concurrency until independent tools exist. No cached holdings table; no
fallback rate, currency or policy; no adjusted close; no environment switch
for which policy runs. **No invented figures as a runtime source, and no
price a stock will reach anywhere.** No mutation testing until necessary.
**And no widening of the router's schema to make it a better classifier** —
the restrictions list in KNOWN_GAPS says which gaps are real and which are
that mistake.

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

**747 passed, 6 xfailed, 26 warnings, about three seconds.** Up from 735: the
invariant-2 file (3), the coverage file (9), and one gained in
`test_synthesizer_formatters.py`. The six expected failures are the
statements-method pin.

**The golden set, sixteen queries on portfolio 3**, two pinned failures (the
macro query; "Should I rebalance my portfolio?"). Run once, after the
answer-text commits: zero diff. `expected.txt` unchanged since 93290af.

**Runner 12/12**, twice. Neither run was expected to move — no case exercises
optimization or rebalancing, and nothing asserts the old allocation wording —
so both are falsifiers for "something else broke", not confirmations.

**Level 4: 0 of 6 cases run.**

### Branches and tags

`selection` is the working branch, thirty commits ahead of the baseline and unpushed. **`baseline-v1` sits at
20160b0**, with `origin/baseline-v1` and `origin/selection` there too.
`compliance` is at `cc7f740`, in sync with its remote and **fully merged into
`baseline-v1`** — zero ahead, 191 behind; `vocabulary` likewise.
`wip/phase7-snapshot` holds rejected Compliance/IPS code. `wip/rag-early` and
tag `rag-early-parked` hold the deleted RAG code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head **`87d3ec68c2ed`**,
21 migrations, linear, all applied. **No migration and no reseed this
session.** Tables that matter: `portfolios` (`currency` and `ips_path` NOT
NULL; row 3 names `ips.toml`), `transactions` (`portfolio_id`, `amount`,
`date` a DATE, `fees`, all NOT NULL), `assets` (9 rows, **no CIK column**,
which the filings reader needs), `daily_prices` (6,939 rows, `source` NOT
NULL, every close a print held to the committed series), `fx_rates` and
`fx_fetch_metadata` (empty), `financial_statements` (65 rows, two tickers,
**no filed date at any grain**, which is why Part 12 makes it neither the
store nor a source), `macro_data` (**191 rows**, was 185 at the fourteenth
session and grows whenever a macro query runs, so it is not a fixed figure),
`shares_history` (947 rows, **no `source` column at all**, its own entry).
**There is no holdings table.**

- **Portfolio 3, "Benchmark Portfolio" — the only portfolio.** Nine ledger
  rows, one buy each, Part 8 A; cost basis 284,500 plus 15,500 cash; USD
  throughout; policy `ips.toml`.

### The documents and their tests

| Document | Config | Held by | Read by |
|---|---|---|---|
| `docs/IPS.md` | `ips.toml` | `test_ips.py` | the compliance node, per portfolio row |
| `docs/PHILOSOPHY.md` | `philosophy.toml` | `test_philosophy.py`, `test_philosophy_loader.py` | nothing yet; `screening.screen` takes it loaded |
| `docs/WATCHLIST.md` | `watchlist.toml` | `test_watchlist.py` | nothing yet |

`tests/golden/edgar_facts_aapl.csv` (86 rows) is Part 12's fixture. Nothing
reads it yet; the provider test reads it when the provider exists, the way
`test_stored_closes_are_the_print.py` reads `benchmark_closes.csv`.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it.
- **OpenAI: no credits.** **Anthropic: working.** `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`
  (`claude-haiku-4-5-20251001`). `ANTHROPIC_SONNET` is `claude-sonnet-5`, behind
  `use_stronger_model`, off.
- **yfinance 1.7.0.** The price method passes `auto_adjust=False`.
- **EDGAR needs a declared User-Agent with a contact.** It is
  `EDGAR_USER_AGENT` in `.env`, never in `config.toml` (tracked, public).
  `.env.example` carries the key with a placeholder (eaa9c23). **The real
  value is not set and nothing reads it yet**; the owner sets it when the
  reader lands. Measured: `data.sec.gov` served a generic User-Agent,
  `www.sec.gov` refused one with HTTP 403. A permission rule denies sessions
  the shell and the editor on `.env*` files.
- `.env.example`, like `.gitignore`, is wrapped in a stray PowerShell
  here-string. Nothing breaks; it is the owner's to fix.
- `openpyxl` in the venv and the `dev` extras. No LibreOffice.
- `config.toml` is required and carries all four fetch intervals.
- `config.features.observability_enabled` is **false** here.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import, so a scratch copy is named in the environment
  before any project import. **The whole suite on a migrated scratch copy**:
  `DATABASE_URL=sqlite:///<copy> USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest`.
- `alembic.ini` names the database by a relative path: run from the project root.
- **The clause loader** is `portfolio_tool/clauses.py`; `ips.py` and
  `philosophy.py` are thin specs over it.
- **The screen's input** is a figures block; its shape is
  `tests/test_fundamentals.py`'s fixture, Part 10 A typed. **No tool publishes
  one yet.** Part 12 says what the reader must return for the `years` half.
- The CLI's quit command is `:q`.

---

## 4. What the fifteenth session did

`git log --oneline 20160b0..HEAD`. Twenty-seven commits of this session's own, of which four touched `src/`; the other three since 20160b0 are the fourteenth session's documentation commits.

**The compliance gate, decided and built (33b31d5, b618ba0, 710e877).**
Invariant 2 was false on a live path: `optimization` printed a weight per
ticker with no clause checked, on the query the golden set pins, while
`validate_compliance` raises if ComplianceAgent is planned there. Shape 2 of
three: the surfaces go rather than a gate being built over them. The check
came first and was seen failing on both, with the offending answers in the
failure output.

**The coverage habit (72a8678, 1e2f045, fcbc0d9).** The allocation answer
claimed "The question named no breakdown, so all three are shown" whenever
`group_by` was null — a guess about the question with a fact's face. It
states its coverage now, counted from the block, and an answer names a ticker
extraction read that the formatter did not select by.

**The rebalance label (91fd126).** A field called Recommendation, against
benchmark.md Part 1, case 2.3 and the system's own refusal text. Renamed to
the drift verdict; the value unchanged.

**The KNOWN_GAPS triage (d121d4f) and the sweep (4533bdd).** Every open entry
tagged with what it blocks; six findings swept in.

**Decision 28 taken, and Part 12 (d7394b6, 8237cdd, 673a929, 04129ea).** One
`companyfacts` document fetched — Apple, CIK 320193, 2026-09-11 — and every
one of five predictions about EDGAR's fields confirmed against it, plus a
sixth found. Eight decisions D26 to D33, a figures table for FY2021 to
FY2025, five falsifier row sets, and an 86-row committed fixture.

**The restrictions list (f2b315a).** From the owner's question about the
schemas: sixteen questions the system cannot express, sorted into expression,
capability and reading, because they have three different answers.

**Part 12 finished (82077c0, c5e46dd, c929cfa, 515732b).** Section E filled
by the owner against Apple's FY2025 10-K: eight of eight to the dollar, the
FY2008 pair confirmed both ways, two label mismatches recorded, three free
cross-checks, and the owner's own caveat that this was a second automated
extraction rather than Part 9's human check. Net debt decided as A, cash only,
with a revisit trigger. D29 gained that the form is not a filter, after a form
type was checked against EDGAR's submissions index. The workbook's `Filings`
sheet written, the ten older sheets compared cell for cell (9,751 cells, zero
differences), then opened and saved in Excel by the owner and compared again
(11 sheets, 9,933 cells, zero differences; 3,048 cached values restored).

**Policy and identity (3100b56, b8584e8, eaa9c23, e318ed8).** I proposed the
SEC contact in `config.toml`; the owner moved it to `.env`, because the config
is tracked and public. Recorded as its own entry. I then wrote that the owner
had added the `.env.example` placeholder before anyone had, and corrected it.
When the owner did add it, the first version carried a real address; the diff
was read before staging and nothing reached the index.

**Invariant sweep**, reported and not committed: no second invariant false.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- The compliance gate: shape 2. A real gate is designed with the research
  node. Shape 3, narrowing invariant 2, rejected.
- A formatter states what it covered, never what the question said, and names
  what extraction read and it did not use.
- The rebalance verdict is not called a recommendation.
- Every open KNOWN_GAPS entry carries what it blocks.
- **Decision 28**: EDGAR company facts; a new table, not `financial_statements`;
  the filer's own fiscal-year label verbatim; the SIC code on the block; D26
  to D33.
- **PHI-3.2 becomes a real clause type, `excluded_industry`** — banks and
  insurers, narrower than Financials, the first consumer of `Asset.industry`,
  with the clause's own expiry recorded. **Decided, not written.**
- The tax rate is a filed figure in the block and a stated assumption in
  config; latest filed wins, pinned to a pull date, whatever form carried it;
  debt reaches the block as filed tags, separately.
- **Net debt is A, cash only.** Revisit on the first candidate that fails on A
  and would pass with current securities netted.
- **`config.toml` holds policy, `.env` holds identity.**

**Pending — decide before writing code.** Old numbers kept so KNOWN_GAPS
references resolve.
6. The rebalance tools' fixed euro sign.
9. Records and rules for the span and two-weights clarifications.
10. A window return as a measure with a reference.
11. Replace the two verbatim benchmark few-shots.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the IPS.
    The rebalance verdict's two defects ride with it (§8).
14. "Optimization failed: None".
15. A golden line for 2.3.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding.
18. Realized gains and closed positions.
22. Volatility over as-traded closes or a total-return series.
23. The answer text naming the price source.
29. **The node for the screen**, after the reader.
30. What a philosophy is bound to.
32. Two formatter headers carry an emoji.
35. A rank selection in extraction.
36. What `reasoning` is for.
38. The CLI's identical-answer check.
39. Three KNOWN_GAPS entries resolved in their body and unmarked in their heading.
40. ~~Part 12 section E~~ filled (82077c0), with the caveat that it was a
    second automated extraction; a figure reaching an answer about a real
    holding wants a human reading first.
41. ~~What nets against debt~~ decided, A (82077c0). **Still the owner's:**
    writing it into PHI-3.1's clause text, which today does not say what nets.
42. **Writing `excluded_industry`** into PHILOSOPHY.md and `philosophy.toml`,
    which needs a bank in the reference first.
43. **The real `EDGAR_USER_AGENT` in `.env`**, set by the owner when the
    reader lands; the placeholder is in `.env.example` (eaa9c23).
44. **A second filer** — a December year end, then a bank. One filer is one
    witness.
45. **The tool-boundary pass**, tagged Order 5, with its trigger written down.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12, twice this session. Level 4: defined, six cases, none
with a check, none running; the ledger has four open predictions and no
scored one, so its score is 0 of 0 until early 2027.

**What a Level 4 pass means, and what it does not.** Every case in Levels 1
to 3 has a hand-computed reference behind its verdict. Level 4's cases pass
on the answer being well-formed, and the only instrument that can say whether
a judgement was any good is the prediction ledger, which holds my predictions
rather than the system's and scores nothing until early 2027. So for months
"4.1 passes" and "the analysis was sound" are the same line on the counter.
Read n/14 as a count of well-formed answers and never as the system being
good at research. benchmark.md's Level 4 states the rule in full (d3ccd86).

---

## 7. Next steps, in order

**Nothing below is blocked on the owner.** The two orders are both
defensible; the second filer first is recommended, because D26 to D33 rest on
one witness and the provider should implement rules two filers agree on.

**1. A second filer** (44): a December year end, checked against D26 to D33
— which the second filer confirms, which it cannot exercise, which it
contradicts. Then a bank, because `excluded_industry` (42) needs one for its
reference row, with the SIC code and where the industry label comes from.
Extend Part 12 or write Part 13; extract a fixture, never commit the document.

**2. The reader, in Part 9's order:** the provider method against a stand-in
for the HTTP layer, held to Part 12 and its fixture; the reader of
`EDGAR_USER_AGENT` with a raise on a missing key, landing with its first
consumer and not before; the table and its migration, committed unexecuted
with its schema test, applied by the owner; the cache record under the price
cache's rules; the assembler that joins `years` to the price source and
shares. Mind the measured unevenness: `www.sec.gov` refuses what
`data.sec.gov` serves.

**3. Decision 29, the node**, after the reader: runner checks for 4.1 and 4.6
first, seen BLOCKED; the intent and agent in the registries with their plan
test; the node over a synthetic state held to Part 10 D; the formatter with
its test; the golden line and the prompt, golden twice with the prediction
written first. **The gate is designed with it, not retrofitted under it** —
that was the whole reason 34 came first.

**4. Then the valuation pipeline** with Part 11 by hand, and prediction
scoring with its Part.

### Later, with reasons

- 3.2's rewrite and Part 2's boundary: at the commit that makes 4.3 answerable.
- The tool-boundary pass (45), before Order 5 rather than at it; its trigger
  is the first benchmark case that fails for want of expression rather than
  capability, and 4.4 and 4.5 are the candidates.
- A total-return series for volatility (22): with a recomputed Part 4.
- More concurrency: when Order 4/5 has independent tools and a measurement asks.
- The inline `sqrt(w'Σw)` copies; the hot-potato violation in `price_data_json`.

---

## 8. Rules learned the hard way

**An invariant is checked against the code, not read as a description.**
Settled this session for invariant 2, and the other seven swept with it:

- **1, every number traces to a tool output** — code plus tests, partially.
  No formatter does arithmetic (grepped). Four of nine formatters have a test.
- **2, compliance is a gate** — was false, now **true by absence**: nothing
  outside intent `compliance` states a position. A gate still does not exist
  and needs three things it has not got — a declared mark for an answer that
  implies a position, a checker entry point taking a proposed weight set with
  its own reference Part, and a policy, which the pinned optimisation query
  has not got at `pid=None`.
- **3, hot potato** — true by construction, unchecked. `price_data_json` is
  161KB in `shared_data` and cannot reach a context window today. The day a
  model reads state, this is a live violation with no test.
- **4, policy in config** — code plus tests.
- **5, raise, do not repair** — code plus tests, 21 files, 85+ `pytest.raises`,
  with two live exceptions on record.
- **6, references before code** — a sentence, enforced by habit. No loop sees
  it. Level 4 is the first place the habit is deliberately suspended.
- **7, no price forecasts** — tests, on the two documents only. Nothing holds
  an answer to it.
- **8, scope is fixed by benchmark.md** — code plus `check_3_2`, the
  strongest of the eight.

**A claim about a test is checked by running it, not by grepping for a
label.** I said no loop asserted the answer's false "Not done" sentence. One
did: `test_allocation_formatter` asserted `"so all three are"`, a fragment,
invisible to a grep for the label.

**A stale remote-tracking ref is not evidence about the remote.** Flagging
that nothing in this clone recorded a push was right; the fetch showed the
push had happened and three later commits had not. Both halves needed the
fetch.

**An external schema is not known until one document is fetched.** Five
claims about EDGAR held; a sixth thing — that instants are quarterly — was
found only by looking, and it is the one that would have silently returned a
quarter's balance sheet for a year. The general form: a secondary source
tells you what to check, not what is true.

**Two changes in one file are still two commits, and the split is mechanical.**
Restoring by hand left four whitespace-only lines that would have ridden into
the wrong commit; splicing the function back from HEAD, after asserting the
two versions differed only in trailing whitespace, was the fix.

**A test that fails on a signature has not been seen failing for its reason.**

**A record says what the tree holds, not what the next step is.** I wrote
that the owner had added a line to `.env.example` when it had only been
arranged. The durable record is exactly where "done" must not mean "planned".

**Read the diff of a file you did not write before you stage it.** The owner's
first `.env.example` line carried a real address into a tracked file in a
public repository, twenty minutes after deciding that was the thing to avoid.
Reading the diff caught it; `git add` would not have.

**A form type in ground truth is checked against the index, not inferred from
a neighbour.** The owner suspected the FY2008 amendment was an 8-K from its
adjacent accession; EDGAR's submissions index said 10-K/A. The check was right
and the inference was wrong, and the question it raised — 8-Ks do carry
restated facts — was worth a decision anyway.

**A restriction is not a defect until its kind is named.** The schema stops
questions being asked, and three different things look identical from the
answer: a capability nothing computes, an expression no field carries, and a
sentence the bridge cannot read. They have three different answers and mixing
them is how a field with no consumer gets added.

**A count is added up, not recalled; a policy is per portfolio, not per
process; a raise is honest and a half-loaded policy is not; the output is the
record, not the word; a check on the most recent date passes in both states;
registration is not reachability; predict from the whole prompt; a refusal is
an honest failure; a fixture that passes in both states is no check; read the
plan table before choosing a publisher; a test against data already right has
not been seen failing — still true.** Earlier handoffs' §8 have the examples.

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

# the price table: nine assets, 6939 rows. macro_data moves; do not pin it.
sqlite3 data/portfolio.db "select count(*) from daily_prices; select count(*) from assets;"

# the whole suite on a migrated scratch copy, while a migration is pending:
DATABASE_URL="sqlite:///$PWD/scratch.db" USE_MOCK_QUOTA=True PYTHONPATH=src pytest -q --noconftest

# the three documents held to their config:
pytest -q tests/test_ips.py tests/test_philosophy.py tests/test_watchlist.py

# the two invariants that now have a loop:
pytest -q tests/test_no_weight_outside_compliance.py tests/test_answers_state_their_coverage.py
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~3s, no model calls | Do the components still work; does the ledger reproduce Part 8, every stored close Part 9, the checker Part 7, the metrics and the screen Part 10; is every document held to its config; **does any answer outside compliance state a position; does an answer state its coverage and name what it dropped** |
| CLI | ~4s, one call | What it is actually doing: the plan, the parameters, the reasoning line, what was asked back, which policy file loaded, whether the provider was called |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines, two pinned failures, `retries`). Blind to `measure`, `group_by`, `status`, `tickers`, the mode, the currencies, the policy file and all answer text |
| Benchmark runner | ~1.5min, cents | How many cases pass; the only loop that sees the compliance mode, the second turn, and the answers' text as a whole. **No case exercises optimization or rebalancing**, so it is blind to those two answers. Level 4's cases join it with decision 29 |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit, and per commit that changes
the answers' text.
