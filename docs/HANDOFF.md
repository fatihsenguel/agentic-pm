# AGENTIC_FINANCE — Session Handoff

**Session date:** 11 September 2026 (fifteenth session). Regenerated at its end, not patched.
**Branch:** `selection`, at `4533bdd`. **`baseline-v1` is at 20160b0**, where the fourteenth session ended, and `origin/baseline-v1` and `origin/selection` are both there too — confirmed by a fetch this session, which also showed that the fourteenth session's last three commits (a40cbc3, d3ccd86, d7632b6) were never pushed. Local `selection` is fourteen commits ahead of the baseline and has no upstream configured. `origin`'s push URL is `no_push`; the owner pushes from elsewhere.

**State:** Green on every loop. pytest **747 passed, 6 xfailed** in about three seconds, up from 735. The runner ran twice, **12/12** both times, and the golden set once, **zero diff on all sixteen lines**. Commit count: `git rev-list --count baseline-v1..HEAD` — 14.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session two of my own claims were wrong and both were
cheap to check: I said no test asserted the answer's false "Not done"
sentence, and one did, by a fragment a grep for the label could not see; and
I said a string had left the tree when a copy of it was still in
`risk_manager_agent.py`. Grep for the caller, not the registration; read the
plan table before choosing who publishes a value; and check a shape against
DIRECTION.md's invariants, not only against the pattern used all day.

**And an invariant is verified, not read.** DIRECTION.md said "compliance is
a gate" for as long as the document has existed and it was false on a live
path the whole time, because the sentence reads as a description of the
system rather than as a claim to check. That was settled this session. Three
of the remaining seven are still sentences no loop can see; §8 has the sweep.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1, 2 and 3 are built. **Order 4 is in progress**: the philosophy check exists as pure modules held to Part 10, the compliance gate is settled, and **the filings reader is the next decision** (§7), then the node that answers cases 4.1 and 4.6. Its last section says when to stop and think. |
| `docs/benchmark.md` | **The definition of done.** Levels 1 to 3: 12 cases, 12 pass. **Level 4**: six research cases, none running yet, the prediction ledger as their eval set, the rule for when 3.2 expires, and what a passing case does and does not mean. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Twelve cases; the Level 4 checks are written first when the node decision starts, blocked probes and all, and the headline becomes n/14. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. **Every open entry now carries one line saying what it blocks**, with a count at the top of OPEN: 75 open, 0 blocking the next commit, 13 a named Order, 62 nothing. Read the Order-4 ones and skip the rest; that is what the tags are for. |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1 to 10. Part 10 is the philosophy check, with decisions D21 to D25. Never update it to match code output. |
| `docs/IPS.md` | The policy, synthetic. `ips.toml` is derived from it and named on portfolio 3's row. Not edited casually. |
| `docs/PHILOSOPHY.md` | What is worth wanting, synthetic, the IPS pattern: seventeen `PHI-x.y` clauses, five numeric screens and twelve statements; `philosophy.toml` derived and held to it. Not yet bound to anything. |
| `docs/WATCHLIST.md` | Two synthetic candidates, Alphabet and Adobe, each a thesis, an entry condition and its predictions; the predictions across the file are the prediction ledger, four of them, due in early 2027. Nothing reads it. |
| `docs/PM-Assistant — Roadmap.md` | Stale, header lists what is superseded. DIRECTION.md's Order supersedes its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.16% v 12%, JNJ 10.05% v 10% at the 09-04 closes); the runner asserts structure.

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is set to `no_push`.
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half (positions, allocation,
P&L, risk, compliance) that is tools and done, and a judgement half
(research, valuation, a thesis, a prediction) whose first tool exists as pure
modules and whose reader is the next decision. The router is scaffolding
until the tool layer is complete. **No deadline. Correctness over speed.
Scope creep is the risk.**

### Design principles

- **Hot potato — agents never see raw data.** Tools return summaries; raw
  arrays move through `shared_data`. True today by construction: one LLM
  call exists, and it is shown the message and a ticker list. It stops being
  true by construction the day a model reads state.
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
  year not yet filed: the pipeline stops and says why.
- **Typed facts are not a source.** A synthetic policy is an honest
  stand-in because the policy is the owner's to state. A company's figures
  are facts; typed ones live in tests as references and never in a file
  the system reads to answer.
- **No answer states a position outside intent `compliance`**, as of this
  session. Not because a gate exists — see §5 and §8 — but because the two
  surfaces that stated one are gone and a test fails if either returns.
- **An answer states what it covered, not what it thinks was asked.** A
  formatter may say which views it rendered and how many lines each carries.
  It may say a ticker extraction read was not used. It may not say what the
  question named, because only `tickers` is evidence about the question and
  nothing records a narrowing.
- **Extraction and derivation before the model.** Tickers, periods,
  percentages and the compliance mode are read from the message; the plan
  is derived. The model decides intent, `measure`, `group_by`, `status`,
  confidence and a clarification question.
- **References before code.** Part 7 before the checker; Part 8 before the
  ledger; Part 9 before the provider changed; Part 10 before the screen.
  The filings reader gets its own Part before a line of it is written.
- **No price forecasts as numbers.** A prediction is about the business
  with a date; a valuation is a range from stated assumptions.

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
- **Two changes in one file are still two commits.** This session's split
  method, twice: commit the first, restore the file from HEAD or from a
  saved copy, apply only the second, commit. It caught four
  whitespace-only lines that would otherwise have ridden into the wrong
  commit, and the restored copy was diffed against the tested one first.
- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting any
  symbol; grep for the caller and for the reader; read the plan table
  before choosing a publisher.
- **A prompt change is a hypothesis.** Line-by-line prediction in the
  commit message before the run; golden twice; stop after the second
  failed prediction on a line. No prompt changed this session.
- Never `commit -a`/`-am`, never `add -A`/`.`; name the files. Never
  rebase, amend, reset, stash; a wrong turn is taken back by a new
  commit that says why. Never edit `.gitignore`.
- **The migration, the reseed and any rewrite of stored rows are run by
  hand** from the project root; **I paste what the command printed, not
  "done."** None needed this session.
- **A test written against data that is already right has not been seen
  failing.** This session: both invariant-2 falsifiers seen failing with the
  offending answers printed, and the coverage assertion seen failing on the
  false sentence rather than on a signature.
- A count I predict is a count I add up. No emoji in code.

### What I do NOT want

A pure asyncio/regex deterministic version without LangGraph. Prompt rules
added to fix a routing defect. My real portfolio's data in the repo: Order 6,
last. No more concurrency until independent tools exist. No cached holdings
table; no currency symbol table; no fallback rate, currency or policy; no
adjusted close in the price table; no environment switch for which policy
runs. **No invented figures as a runtime source, and no price a stock will
reach anywhere in a document or an answer.** No mutation testing until it is
necessary.

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
`test_synthesizer_formatters.py`'s rebalance case. The six expected failures
are the statements-method pin, as before.

**The golden set, sixteen queries on portfolio 3**, two pinned failures (the
macro query; "Should I rebalance my portfolio?"). Run once this session,
after the answer-text commits: zero diff. `expected.txt` unchanged since
93290af.

**Runner 12/12**, twice: once after the two answer surfaces were deleted and
once after the coverage habit landed. Neither was expected to move it — no
case exercises optimization or rebalancing, and nothing asserts the old
allocation wording — so both runs are falsifiers for "something else broke",
not confirmations of the change.

**Level 4: 0 of 6 cases run.** No check exists for them yet.

### Branches and tags

`selection` is the working branch, at `4533bdd`. **`baseline-v1` sits at
20160b0**, and `origin/baseline-v1` and `origin/selection` are there too.
`compliance` is at `cc7f740`, in sync with its remote and **fully merged into
`baseline-v1`** — zero ahead, 191 behind; `vocabulary` likewise.
`wip/phase7-snapshot` holds rejected Compliance/IPS code; nothing on it is
scheduled. `wip/rag-early` and tag `rag-early-parked` hold the deleted RAG
code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`87d3ec68c2ed`** (`macro_data.source` NOT NULL), 21 migrations, linear, all
applied. No migration and no reseed this session. Tables that matter:
`portfolios` (`currency` and `ips_path` NOT NULL; row 3 names `ips.toml`),
`transactions` (`portfolio_id`, `amount`, `date` a DATE, `fees`, all NOT
NULL), `assets` (9 rows, **no CIK column**, which the filings reader will
need), `daily_prices` (6,939 rows, `source` NOT NULL, every close a print
held to the committed series by the suite), `fx_rates` and
`fx_fetch_metadata` (empty), `financial_statements` (`source` NOT NULL, 65
rows, two tickers, untrusted, **no filed date at any grain**), `macro_data`
(`source` NOT NULL, **191 rows**, all `yfinance`; it was 185 at the last
handoff and grows whenever a macro query runs, so it is not a fixed figure),
`shares_history` (947 rows, **no `source` column at all**, its own KNOWN_GAPS
entry). **There is no holdings table.** The watchlist, the philosophy and the
ledger are files, not tables.

- **Portfolio 3, "Benchmark Portfolio" — the only portfolio.** Nine ledger
  rows, one buy each, Part 8 A; cost basis 284,500 plus 15,500 cash; USD
  throughout; policy `ips.toml`.
- Reseeding rewrites the nine assets' metadata to the same values and
  refuses without `--reset`.

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
  head` runs from the project root.
- **The clause loader** is `portfolio_tool/clauses.py`; `ips.py` and
  `philosophy.py` are thin specs over it.
- **The screen's input** is a figures block: ticker, currency, source,
  fiscal years with `ends` and `filed` dates and reported figures by name,
  `shares_outstanding`, `price` and `valuation_range` with `as_of`. Its
  shape is `tests/test_fundamentals.py`'s fixture, Part 10 A typed. **No
  tool publishes one yet; the filings reader is the decision that starts to.**
- The CLI's quit command is `:q`.

---

## 4. What the fifteenth session did

`git log --oneline 20160b0..HEAD` for the list. Eleven commits, of which
three touched `src/`.

**The compliance gate, decided and built (33b31d5, b618ba0, 710e877).**
DIRECTION.md invariant 2 was false on a live path: `optimization` printed a
weight per ticker with no clause checked, on the query the golden set pins,
while `validate_compliance` raises if ComplianceAgent is planned there.
Shape 2 of the three recorded: the surfaces go rather than a gate being built
over them. The check came first and was seen failing on both, with the
offending answers in the failure output. The optimiser keeps its return,
volatility and Sharpe; the rebalancer keeps its drift; each answer names what
it did not show and why.

**The coverage habit (72a8678, 1e2f045, fcbc0d9).** The allocation answer
claimed "The question named no breakdown, so all three are shown" whenever
`group_by` was null — a guess about the question with a fact's face, false
for every question that named one. It states its coverage now, counted from
the block. And an answer names a ticker extraction read that the formatter
did not select by, in the allocation views and in the portfolio volatility.
The other half — saying what the question asked for and did not get — is not
buildable and is not faked: nothing records a narrowing.

**The rebalance label (91fd126).** The answer printed a field called
Recommendation while benchmark.md Part 1, case 2.3 and the system's own
refusal text all say it gives none. Renamed to the drift verdict; the value
is unchanged and still the tool's.

**The KNOWN_GAPS triage (d121d4f)** and **the sweep (4533bdd)**, then this
file. Plus `1f4fb84`, what a Level 4 pass means, in §6, and `0f36f1a`,
recording that shape 2 was taken.

**The invariant sweep**, reported and not committed: no second invariant
turned out false. §8 has the result.

**Decision 28, the filings reader, brought and not taken.** Its shape,
recommendations and rejected alternatives are in KNOWN_GAPS under Directions
so they survive this document.

---

## 5. Decisions taken, and decisions pending

**Taken this session.**
- The compliance gate: shape 2. Delete the answer surfaces that state a
  position rather than build a gate over surfaces benchmark.md's roster does
  not name. A real gate is designed with the research node, where case 4.3
  defines what checked means. Shape 3, narrowing the invariant in
  DIRECTION.md, rejected — nothing needed narrowing once the surfaces went.
- A formatter states what it covered, never what the question said; and it
  names what extraction read and it did not use. The other half waits for
  `filter`.
- The rebalance verdict is not called a recommendation.
- Every open KNOWN_GAPS entry carries a line saying what it blocks.

**Pending — decide before writing code.** Old numbers kept so that KNOWN_GAPS
references resolve; done items struck.
6. **The rebalance tools' fixed euro sign**: logged, not built. Two of its
   instances left the answer text with the trades.
9. Records and rules for the span and two-weights clarifications, when a case asks.
10. A window return as a measure with a reference.
11. Replace the two verbatim benchmark few-shots.
12. The hypothetical mode's instrument type ("11% into a new ETF").
13. **A target-weights clause** and `OUT_OF_SCOPE_RESPONSE` moving into the
    IPS. The rebalance verdict's two defects ride with it (§8).
14. "Optimization failed: None".
15. A golden line for 2.3.
16. Company names, German phrasings, the softer 3.5.
17. `group_by` as the subject kind of a compliance finding, when a case asks.
18. Realized gains and closed positions.
22. Volatility over as-traded closes or a total-return series: a Part 4 decision.
23. The answer text naming the price source.
25. ~~`macro_data.source` NOT NULL~~ done.
26. ~~`get_financial_statements` returning nothing~~ folded into 28: the
    recommendation is that the table is neither the store nor a source.
27. ~~Mutation testing~~ only when necessary; off this list.
28. **The filings reader, the next decision** (§7).
29. **The node for the screen**, after the reader.
30. **What a philosophy is bound to.** The committed file by path until Order 6.
31. ~~The bank variant of 4.6~~ folded into 28: the SIC code on the block,
    with one question left — whether PHI-3.2 becomes a clause type or stays a
    statement the screen refuses on.
32. **Two formatter headers carry an emoji**: an answer-text change, own
    commit, the runner sees it.
33. ~~The workbook's cached values~~ done.
34. ~~The compliance gate~~ settled this session, shape 2.
35. **A rank selection in extraction** ("my two biggest holdings"): the third
    value of the selection axis, with `filter`. The coverage line makes the
    widening visible; it does not make it expressible.
36. **What `reasoning` is for**: a debugging artifact no answer may carry, or
    something checked against what ran. Before Level 4's prose fields.
37. ~~A tagging pass over KNOWN_GAPS~~ done (d121d4f).
38. **The CLI's identical-answer check** fires on two correct refusals.
39. **Three KNOWN_GAPS entries are resolved in their body and unmarked in
    their heading**, so every count of the file is three high. Marking them is
    one line each and its own commit; it was out of scope for an
    insertions-only pass.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: 12/12, twice this session. Level 4: defined, six cases, none
with a check, none running; the ledger has four open predictions and no
scored one, so its score is 0 of 0 and stays so until early 2027.

**What a Level 4 pass means, and what it does not.** Every case in Levels 1
to 3 has a hand-computed reference behind its verdict. Level 4's cases pass
on the answer being well-formed, and the only instrument that can say
whether a judgement was any good is the prediction ledger, which holds my
predictions rather than the system's and scores nothing until early 2027.
So for months "4.1 passes" and "the analysis was sound" are the same line
on the counter. Read n/14 as a count of well-formed answers and never as
the system being good at research. benchmark.md's Level 4 states the rule
in full (d3ccd86); it is not restated here.

---

## 7. Next steps, in order

**Decision 28, the filings reader, before any node.** The shape, the three
questions inside it and the rejected alternatives are in KNOWN_GAPS under
Directions, brought and not taken. In short: EDGAR company-facts, because
every fact carries a filed date and D21 counts a fiscal year by it; a new
table rather than `financial_statements`, which has no filed date at any
grain and spreads a year over three rows; the filer's own fiscal-year label
verbatim, never computed; the SIC code on the block so 4.6's bank variant is
decidable with no model.

**Two things block it and both are the owner's.** Whether PHI-3.2 becomes a
real clause type (`excluded_industry`, with its own reference row) or stays a
statement the screen refuses on — it changes `docs/PHILOSOPHY.md`. And **one
`companyfacts` document fetched by hand** to confirm the field names, in
particular whether `fy` on a fact is the fiscal year of the fact or of the
filing it appeared in; everything written down about EDGAR's schema is from
memory and nothing is built on it until that is checked.

Then, in Part 9's order: a reference Part by hand, a few rows for one real
filer taken from the company's own 10-K to the dollar with filed dates; the
provider method against a stand-in for the HTTP layer, held to that Part; the
table and its migration, committed unexecuted with its schema test; the cache
record under the price cache's rules; the assembler that joins years to price
and shares. Part 11 is the valuation range, so this reference needs its own
number.

**Decision 29, the node**, after the reader: runner checks for 4.1 and 4.6
first, seen BLOCKED; the intent and agent in the registries with their plan
test; the node with a test over a synthetic state held to Part 10 D; the
formatter with its test; the golden line and the prompt, golden twice with
the prediction written first. **The gate is designed with it, not retrofitted
under it** — that was the whole reason 34 came first.

**Then the valuation pipeline** with Part 11 by hand, and prediction scoring
with its Part.

### Later, with reasons

- 3.2's rewrite and Part 2's boundary: at the commit that makes 4.3 answerable.
- `measure`, `group_by` and `status` are the model's; whether they become extraction is a tool-boundary question.
- A total-return series for volatility (22): with a recomputed Part 4.
- More concurrency: when Order 4/5 has independent tools and a measurement asks.
- The inline `sqrt(w'Σw)` copies; the hot-potato violation in `price_data_json`.

---

## 8. Rules learned the hard way

**An invariant is checked against the code, not read as a description.**
Settled this session for invariant 2, and the other seven were swept with it.
The result, so nobody has to redo it:

- **1, every number traces to a tool output** — code plus tests, partially.
  No formatter does arithmetic (grepped; every hit is a comment). Four of
  nine formatters have a test.
- **2, compliance is a gate** — was false, now **true by absence**: nothing
  outside intent `compliance` states a position. A gate still does not exist,
  and needs three things it has not got — a declared mark for an answer that
  implies a position, a checker entry point taking a proposed weight set with
  its own reference Part, and a policy, which the pinned optimisation query
  has not got at `pid=None`.
- **3, hot potato** — true by construction, unchecked. One LLM call exists
  and is shown the message and a ticker list. `price_data_json` is 161KB in
  `shared_data` and cannot reach a context window today. The day a model
  reads state, this is a live violation with no test.
- **4, policy in config** — code plus tests.
- **5, raise, do not repair** — code plus tests, 21 files, 85+ `pytest.raises`,
  with two live exceptions already on record.
- **6, references before code** — a sentence, enforced by habit. No loop sees
  it. Level 4 is the first place the habit is deliberately suspended.
- **7, no price forecasts** — tests, on the two documents only. Nothing holds
  an answer to it. The market-timing surface is dead code, and its being dead
  is a fact nothing checks.
- **8, scope is fixed by benchmark.md** — code plus `check_3_2`, the
  strongest of the eight.

**A claim about a test is checked by running it, not by grepping for a
label.** I said no loop asserted the answer's false "Not done" sentence. One
did: `test_allocation_formatter` asserted `"so all three are"`, a fragment,
invisible to a grep for the label. The sentence had a pin and I reported it
did not.

**A stale remote-tracking ref is not evidence about the remote.** I flagged
that nothing in this clone recorded the fourteenth session's push, which was
the right thing to say; the fetch showed the push had happened and that three
later commits had not. Both halves needed the fetch.

**Two changes in one file are still two commits, and the split is mechanical.**
Commit the first, restore the file from HEAD or a saved copy, apply the
second. Restoring by hand left four whitespace-only lines that would have
ridden into the wrong commit; splicing the function back from HEAD, after
asserting the two versions differed only in trailing whitespace, was the fix.

**A test that fails on a signature has not been seen failing for its reason.**
The coverage cases were restructured to pass `tickers` only where the case is
about it, so the first case fails on the false sentence being present rather
than on arity.

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

# every source column required (macro_data, daily_prices, fx_rates, financial_statements):
sqlite3 data/portfolio.db ".schema macro_data" | grep source

# the price table: nine assets, 6939 rows, one convention. macro_data moves.
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
| `pytest` | ~3s, no model calls | Do the components still work; does the ledger reproduce Part 8, the rate arithmetic Part 8 C, every stored close Part 9, the checker Part 7, the metrics and the screen Part 10; does the schema have the columns and not the defaults; is every document held to its config; does every table row derive its plan; does extraction read every recorded prompt the same way; **does any answer outside compliance state a position; does an answer state its coverage and name what it dropped** |
| CLI | ~4s, one call | What it is actually doing: the plan, the parameters, the reasoning line, what was asked back, the answer's header, which policy file the compliance node loaded, whether the provider was called |
| Golden set | ~70s, cents | Did routing change anywhere (sixteen lines or none, two pinned failures, `retries` when a plan was rejected). Blind to `measure`, `group_by`, `status`, `tickers`, the mode, the currencies, the policy file and all answer text |
| Benchmark runner | ~1.5min, cents | How many cases pass; the only loop that sees the compliance mode, the second turn, a model-owned field set where it should not be, and the answers' text as a whole. **No case exercises optimization or rebalancing**, so it is blind to those two answers. Level 4's cases join it with decision 29 |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second
miss on a line. The runner is per capability commit, and per commit that
changes the answers' text.
