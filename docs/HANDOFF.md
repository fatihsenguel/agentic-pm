# AGENTIC_FINANCE — Session Handoff

**Session date:** 22 September 2026 (thirty-sixth session), begun about 18:25 UTC. Regenerated at its end. The thirty-third, thirty-fourth and thirty-fifth sessions ran earlier the same day.
**Branch:** `half-cent`, cut from `baseline-v1` at **dfbc7d2** before the first commit, in a worktree under `.claude/worktrees/` because this session's harness rejects edits outside one; **seven commits with this one**, not merged, not pushed. The brief named 5a2ab7b as the branch point; the trunk had moved to dfbc7d2 by the handoff correction the brief itself called done, and a branch from 5a2ab7b could not have merged fast-forward, so the cut was taken from the trunk head and said so. `origin`'s push URL is `no_push` and the push goes by URL, so the local `origin/baseline-v1` ref lags: it stands at **33769f6**, the "Decision 76" commit, not at b308b71 as the previous handoff said (b308b71 was the first commit of that evening's push, sixteen past the ref); `git rev-list --count origin/baseline-v1..baseline-v1` says thirty-eight for the trunk at dfbc7d2 and forty-four for this branch. The push output is the record.

**State:** pytest **1934 passed, 6 xfailed**, up five from 1929 by the five tests of the one check this session wrote; run at session start in the worktree and again at the end. **Two paid loops ran, one after the other: the runner once at 18:42 UTC, 15/18, every verdict as predicted and as at 12:51; and 2.2 alone through the CLI at 18:49, one Haiku call.** The golden set was not run: no prompt changed. **Step 4 of the interlude is done but for decision 76**: decision 75, the exact half cent, is implemented, its check written first against Part 7 and red for one commit, and the record says what the check found before any code was written. The pending list stands at eleven, unchanged.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Sections whose claims were checked again this session and
still hold are kept word for word; the rest is rewritten. This session
checked the counts, the clocks, the store before and after each paid
loop, the origin ref, and which source tree each loop imports from a
worktree; it did not re-check §3's library versions or the migration
count beyond the head.

**This was a one-item session.** The interlude's rule says only a
pipeline's arithmetic is fixed before Order 5, the corpus run found one
arithmetic miss, and this session fixed it and nothing else: two commits
of code and tests, four of record. Nothing else the run logged was
touched.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1 to 4 are built. The interlude between Orders 4 and 5 is its unnumbered paragraph under Order 4, last revised 22 September. Unchanged this session. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. **176 lines start `**Trigger:**`**, unchanged in count: one changed its text, decision 75's, to "none: implemented". **Start with "The interlude between Order 4 and Order 5, and how the corpus is built"**, whose step 4 now says done but for 76. Then "An exact half cent rounds by the order of the float operations - DECIDED 21 September (thirty-second session)", whose last paragraph is this session's: what the check found that the decision had not anticipated. "Case 3.3's answer carries three exact halves and prints three different roundings" carries a dated line saying its trigger fired on 2c43ad0 and nothing there changes. "Whether money and ratios are computed in decimal - decision 76, pending" is unchanged and reads decision 75's entry. |
| `docs/benchmark.md` | **The definition of done, the corpus, and its runs.** Part 3c.6 now holds two blocks: the run of 22 September at 17:11, 65 turns, and **a second block of one line, 2.2 alone at 18:49 after decision 75**, matched on the two halves. Nothing else changed. **Read Part 2, Part 3c and 3c.6 before Part 3's tables.** |
| `tests/golden/expected_values.md` | Hand-computed reference, Parts 1 to 18. **Unchanged this session.** Part 7 is now pinned to the printed cent by `tests/test_half_cent.py`; before this session no test asserted a printed cent against a Part, and the answer at Part 7's own closes printed IPS-3.1's distance as 18,083.17 against the Part's .18 without anything noticing. Never update it to match code output. |
| `tests/test_half_cent.py` | **New.** Decision 75 held to Part 7 at 2026-09-02, Part 17 B at 2026-09-18 and the corpus run's closes at 2026-09-21: the distance in currency exact as a decimal, the points derived from it, the raise on a line with no market value, and the printed cents at both print sites. Five tests, each one test over its figures so the share-first path fails it whole. Written before the code; sat one commit as xfail strict. |
| `tests/golden/run_corpus_2026-09-22.txt` | **The corpus transcript**, 5,887 lines, the run of 17:11. Unchanged. |
| `tests/golden/run_2.2_2026-09-22.txt` | **New, 187 lines.** 2.2 alone at 18:49, captured whole with the corpus transcript's header shape. Differs from the corpus run's 2.2 answer in exactly two lines, IPS-3.1's 19,552.47 to 19,552.48, checked by diff. |
| `tests/test_corpus_spine.py` | Part 3c.1's eighteen wordings are the runner's `CASES`. Unchanged. |
| `tests/golden/expected.txt` | Twenty-one lines, one pinned failure. Unchanged; not run this session. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Eighteen cases, unchanged, **run once this session: 15/18.** |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets. Not opened this session. |
| `docs/IPS.md`, `docs/PHILOSOPHY.md`, `docs/WATCHLIST.md`, `watchlist.toml` | The owner's. Unchanged, not edited. |
| `docs/PM-Assistant — Roadmap.md` | Stale; DIRECTION.md's Order supersedes it. |
| `docs/workflow.md` | Stale, and a pasted conversational reply with emoji in its headers (KNOWN_GAPS). |

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`.
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

`docs/DIRECTION.md` states it. A conversation with a strong model that calls
deterministic pipelines as tools; a guarantee half that is tools and done,
and a judgement half whose tools are in the graph with their references.
The router is scaffolding until the tool layer is complete.
**No deadline. Correctness over speed. Scope creep is the risk.**

### Why the interlude, in one paragraph

Four reasons, the owner's, recorded in full in KNOWN_GAPS. No loop shows
an answer, so there is no feel for what the system does. Order 5 replaces
the router, which kills the golden set — the loop that cannot verify it —
so a corpus of prompts with hand-written answers is the precondition.
A first demo is a test: recorded runs that stand without narration. And
what is actually missing should be known before anything is added.
**What belongs in the interlude is decided by what survives the refactor**:
the question, the figures, the clauses, the sequences; not the intent and
not the plan. The corpus is written on that rule, run on it, and now the
one arithmetic miss it found is fixed on it.

### What this session found, in one paragraph

Decision 75 said two things: a distance to a limit is the market value
less the limit's share of total, and where it prints it is rounded half-up
on a Decimal built from the figure. The check, written first, showed the
second cannot reach the first as recorded: the float subtraction does not
land on the half either. 0.65 times 410,200.50 is 266,630.325, which a
double does not hold, so Part 7's Equity distance comes out
18083.17499999999 and the corpus run's 19552.474999999977, and a Decimal
built from either rounds to .17. The 09-18 pair the decision's entry
verified lands on the half exactly by the luck of that product. So the one
subtraction is done in decimal inside `_finding` from the block's three
amounts as they print, the float published is that decimal's nearest
double, whose repr is the decimal again, and the print-site helper rounds
that. Read as inside decision 75 and not 76, on the owner's word after
the shape was brought with the rejected alternatives. The runner scored
15/18 afterwards, every verdict as before; the one answer read, 2.2,
traced in every figure, and its two halves printed .48 and .38.

### Design principles

Unchanged in the code. What this session touched against them:

- **Raise, do not repair.** A line with no market value raises in
  `_finding`, as one with no share already did. The verdict stays on the
  published share (D9) and the distance on the published market value;
  in a consistent block they agree, and the checker does not cross-check
  them, which is a guard nobody asked for and is noted here rather than
  built.
- **A formatter does no arithmetic.** `_cents` rounds; it does not
  compute. The distance reaches it unrounded, as the block carries it.
- **One helper, not each call site.** Two sites print a distance in
  currency and both go through `_cents`. The other 44 currency amounts
  formatted to the cent across `nodes.py`, `rebalance_tools.py` and
  `seed_portfolio.py` are totals, market values and prices the block
  already rounds, and were counted and left.
- **A value nobody would set differently is not policy.** The rounding
  rule is in code, not `config.toml`, as the decision's entry says.
- **Every number traces to a tool output.** Held in both paid loops.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
  **This session's one decision, whether the decimal subtraction is 75's
  or 76's, was brought with the arithmetic that forced it, a
  recommendation and three rejected alternatives, and taken before the
  check was committed.**
- **The reference before the code**, each time. **The check before the
  implementation**: five tests, red on the current code, sat one commit
  as xfail strict, the mark removed in the implementing commit.
- **The blast radius before writing anything, and the number said
  twice**: 46 currency amounts on 43 lines in 3 files, 15 `round(` calls
  in the block-publishing stretch, one `_finding` with five callers, 7
  assertions on a printed or rounded cent in 4 files. Two lines and one
  fixture moved.
- **A paid loop says first what it will fetch and store, table by table,
  and afterwards what moved.** Predicted by the clock and held to the
  row: nothing fetched, nothing stored, every count and every clock the
  same before and after both loops. The runner's eighteen verdicts were
  predicted one by one and every one held.
- **A brief's clock is read against the interval's arithmetic.** The
  brief's "having run out on the 23rd" described tonight's state, not the
  session's; at 18:40 UTC on the 22nd no clock had run out, and the
  prediction was written for each branch of the clock.
- **Which source tree a loop imports is checked before it is paid for.**
  See §3: from a worktree the runner imports the checkout's code unless
  told otherwise.
- **The capture is never filtered.** Both paid loops wrote their whole
  output to a file under the job's temporary directory; the 2.2 capture
  is committed beside `expected.txt`.
- **A count in a message is counted.** The runner's 15/18 and the 2.2
  diff's two lines were read from the files before the message named
  them.
- No emoji in anything newly written; the transcript is captured, not
  written.

### What I do NOT want

A pure asyncio/regex version without LangGraph. Prompt rules added to fix a
routing defect. My real portfolio's data in the repo: Order 6, last. No
cached holdings table; no fallback rate, currency or policy; no adjusted
close; no environment switch for which policy runs. **No invented figures as
a runtime source, and no price a stock will reach anywhere.** No widening of
the router's schema to make it a better classifier. No NOPAT at the
company's filed tax rate. No formatter sentence that states the system's
status. No number, threshold or weight from a model; no row written into
the watchlist by the system; no outcome decided by the formatter or the
model. No score written into the ledger by the system; no partial credit;
no prediction scored before its date. No long quote cut in code to pass the
cap, no third wording after two misses. No exception swallowed into a
`None`. No forward return as a number. No sentence in the record that names
an audience instead of a requirement. **No corpus entry fitted to an answer
after the run, and no fix inside the interlude that is not a pipeline's
arithmetic.** **No second rounding rule to make a float land on a half,
and no rounded figure published in a block.**

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

**Three of the five ran.** pytest: **1934 passed, 6 xfailed**, about 6
seconds, at session start (1929) and at the end (1934). The runner:
once, 15/18. The CLI: 2.2 alone, once. The golden set was not run.

**Golden set: twenty-one lines, one pinned failure**, `expected.txt` at
4f7ca89. Not run.

**The runner: 15/18, 0 failing, 3 blocked** by this session's run at
18:42 UTC on the 22nd, from the worktree with `PYTHONPATH=src`. 2.1
blocked on routing, 4.1 and 4.3 on the PHI-2.1 stop. Every verdict as at
12:51.

**The corpus: 30 of 65 turns matched**, by the run at 17:11 and the
reading in benchmark.md Part 3c.6, unchanged. **2.2 alone at 18:49:
matched on the two halves**, 19,552.48 and 15,147.38 in both places, the
rest of the answer byte-identical to the run's; its two other omissions
stand as logged. R-8 and R-9 not run.

### Branches and tags

`baseline-v1` is the trunk at **dfbc7d2**, pushed to that commit on 22
September; `half-cent` is cut from it and carries this session's seven
commits, **to be merged `--ff-only` by the owner**. The `half-cent`
worktree holds a symlink `data/portfolio.db` to the checkout's database,
gitignored, so pytest and the CLI there ran against the real store, and
`.env` was found by walking up from the worktree; the same arrangement
serves any later worktree.
`intents-parked` at addfbc7 holds the tree that still had the three
intents. `corpus-run`, `handoff`, `rounding`, `halves`, `judgement`,
`gate`, `thesis`, `reader`, `research`, `score`, `publish`, `range`,
`keys`, `node`, `filer`, `bridge`, `consolidate`, `selection`,
`compliance`, `vocabulary`, `intents`, `arc`, `counts`, `corpus` and
`direction` are merged and older. `wip/phase7-snapshot` holds rejected
Compliance/IPS code. `wip/rag-early` and tag `rag-early-parked` hold the
RAG code. `quant-inventory-parked` at 8d87455 holds the tree before the
seventeenth session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`2445c12e728c`**, checked; no migration this session. No reseed. **Read
before and after each paid loop, at 18:40, 18:43 and 18:49 UTC: nothing
moved.**

- `daily_prices` **7,019**, last close **2026-09-21**. No fetch: the
  one-day interval, `(utcnow - last).days >= 1` in `data_manager.py`,
  runs out at **17:11 UTC on the 23rd** for the nine holdings and 17:12
  for GOOGL.
- `asset_fetch_metadata` unchanged, stamped 2026-09-22 17:11:38 to
  17:12:02. `api_call_logs` **2,490**. `api_quotas` last row
  `daily_yfinance_2026-09-22` at **10**.
- `filers` 3, `filed_facts` 28,787 (Apple 15,132, Alphabet 13,655),
  `filed_fetch_metadata` 2, `ticker_ciks` 10,422, `filed_documents` 1,
  `document_readings` 5, `assets` 10: **all unchanged.**
- **The filings clocks, as stored and against the whole-days test
  `(now - pulled_at).days < 7` in `filings.py`**: Apple's facts pulled
  2026-09-15 22:17 UTC, so run out at **22:17 UTC on the 22nd**; Apple's
  filer row 09-16 00:03, JPM's filer row 09-16 01:33 and the ticker file
  09-16 01:33, Alphabet's filer row and facts 09-16 01:38, so those run
  out at **00:03, 01:33 and 01:38 UTC on the 23rd**. No runner case reads
  Apple's facts. **The next paid run of a Level 4 question after 01:38
  on the 23rd refetches the ticker file, JPM's and Alphabet's filer rows
  and Alphabet's facts**, which should store zero new rows or raise on a
  changed figure; after 17:11 it also fetches ten closes for the 22nd.
  **R-8 and R-9 still name ADBE, a filer with no facts stored**, and are
  their own yes: the previous handoff's prediction of what that first
  fetch does stands.

Unchanged: `assets` ten rows, GOOGL the tenth and not held; portfolio 3
the only portfolio, nine ledger rows, cost basis 284,500 plus 15,500 cash,
USD, policy `ips.toml`. There is no holdings table.

---

## 3. Environment

Not re-checked this session except where marked; kept from the
thirty-fifth session's handoff.

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- **The venv holds an editable install of the checkout's `src`**
  (`__editable__.agentic_finance-0.1.0.pth`), checked this session.
  From a worktree: pytest imports the worktree's tree because
  `tests/conftest.py` inserts its own `src` first; the CLI does because
  `cli.py` inserts its own parent directory; **`tests/benchmark/run_cases.py`
  inserts nothing and imports the checkout's code**, so from a worktree
  it scores the trunk, not the branch, unless run with `PYTHONPATH=src`.
  This session's runner ran that way, and the import was checked to
  resolve to the worktree before the loop was paid for.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files. `load_dotenv()` in `config.py`
  finds it by walking up from the calling file, so a worktree nested
  under the checkout reads the checkout's `.env` (checked again: both
  paid loops ran from the worktree).
- **Anthropic has credits**; the two loops cost about 0.04 dollars by the
  per-call figures below. An empty balance fails with a 400
  `invalid_request_error` naming the credit balance, and from inside the
  system every question returns `intent: None`.
- `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU` for the router. `ANTHROPIC_SONNET`
  is `claude-sonnet-5`, used by the reader, the proposer and the view, and
  refuses a temperature. The reader's cache is keyed by accession,
  section, model and prompt version; the five stored readings still match
  the current versions, since nothing touched the reader; 4.3 and 4.4
  read from the cache.
- The `anthropic` SDK is 1.2.0; yfinance 1.7.0 with an exclusive `end`.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing. Nothing was fetched from EDGAR this session.
- **The period vocabulary**: `config.DataConfig.period_days`, a default in
  code, keys `1Y, 2Y, 3Y, 5Y, 10Y`, passed to extraction by
  `smart_router.py`. Not in `config.toml`.
- **Extraction** (`src/agents/extraction.py`): as the thirty-fifth
  session's handoff described it, unchanged; a comma after "no" still
  defeats `resolve` (KNOWN_GAPS).
- `config.toml` carries five fetch intervals: prices 1 day, filings 7,
  earnings 7, profile 30, shares 30. Its `[macro]`, `[optimization]` and
  `[backtest]` sections stand although two have no consumer.
- **Decimal in the code, checked this session**: `proposals.py` builds a
  Decimal from a float's repr and quantizes it, and `compliance.py` and
  `nodes.py` now do the same for a distance and its printed cent. As the
  record says and this session did not re-check, the `daily_prices`
  closes carry provider noise and `data_agent.py` rounds the last close
  to two decimals before anything computes with it, so every amount the
  blocks publish is an exact cent, which is what makes a Decimal built
  from its repr the figure itself.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; scripts run from the root. The URL in `.env`
  is relative, so from the worktree it resolves through the symlink.
- The CLI's quit command is `:q`; `exit` goes to the router. Several
  questions go through one process with `printf '%s\n' 'q1' 'q2' ':q' |
  python src/agents/cli.py --portfolio 3`, each its own graph run. The
  CLI passes the previous turn's final state to the next. `input()` at
  end of input returns, so a piped process ends cleanly after `:q`.
- A single benchmark case runs with `--case`, one Haiku routing.
- zsh does not split an unquoted variable into words and has no `tac`; a
  `grep -c` that finds nothing exits 1; `%` in a `printf` format is `%%`;
  BSD `sed` has no `0,/re/`; BSD `cat` has no `-A`; `awk` has no `\s`;
  `--include='*.py'` must be quoted. **This session's harness refused, in
  the worktree, compound commands with a `{ …; }` group, a `for` loop
  ending in a `git` call, and a `sed -n` range built from a shell
  variable; the same work split into plain commands ran.**
- **What is no longer in the tree**: as the thirty-third session's handoff
  listed it, unchanged; nothing was deleted this session.

---

## 4. What the thirty-sixth session did

`git log --oneline dfbc7d2..HEAD`, **seven commits** with this one, the
first six touching eight files, **513 insertions and 28 deletions**, of
which the transcript is 188 lines and the check 191; this handoff is a
rewrite of one file on top. In the owner's order: the blast radius, the
check, the implementation, the two paid loops, the record.

**Read first, and only what the brief named**: DIRECTION.md, the previous
handoff and its §0, then by grep on their headings the decision 75 entry
whole, the 3.3 halves entry, the interlude entry's step 4, and decision
76's entry when the finding made it necessary; Part 7 at its own as-of,
Part 18's 2.2, Part 3c.6's 2.2 line, the transcript's 2.2 answer. Then
the code: `compliance.py` whole, the compliance formatter, the
block-publishing stretch, the gate's synthetic allocation, every fixture
that builds an allocation line, every test that asserts on a cent.
**The brief's claims, checked**: pytest's number held; the branch point
did not (above); the filings clocks were tonight's, not past; the
handoff's origin ref name was wrong and its count right.

**The blast radius, measured before writing** (§1). Counted, then
counted again by a second command before the message named it.

**The commits.**
- **0bbde46** `tests/test_half_cent.py`, the check: five tests, all red
  on the current code, marked xfail strict for this one commit. The file
  alone: 5 xfailed with the mark, 5 failed without it; the suite was not
  rerun whole at this commit.
- **2c43ad0** the implementation: `compliance.py` (`_finding` takes the
  line's market value, computes the distance in decimal, derives the
  points, raises on a line with none; docstrings), `nodes.py` (`_cents`
  and the two print sites; the `decimal` import), the mark off the
  check, `test_compliance_formatter.py` asserting through `_cents`,
  `test_compliance.py`'s at-the-limit fixture setting the market value
  with the share. pytest 1934 passed, 6 xfailed. The runner's reconcile
  tolerances checked offline first over three blocks: 4.4e-15 against
  1e-6 on the points, 1.5e-11 against a cent on the value.
- **2688ea6** benchmark.md Part 3c.6: the second block, 2.2 alone.
- **0cb6bd7** `tests/golden/run_2.2_2026-09-22.txt`, captured whole.
- **f98b9c0** KNOWN_GAPS: decision 75's trigger to "none: implemented",
  the paragraph on what the check found, the dated line on the 3.3 entry.
- **42ce7ba** KNOWN_GAPS: the interlude's step 4 done but for 76.

**The two paid loops, as they were driven.** The runner from the
worktree with `PYTHONPATH=src`, output whole to a file under the job's
temporary directory, 18:42:13 to 18:43:11 UTC: 15/18, every verdict as
predicted. Then 2.2 alone through the CLI, one process, 18:49:14 to
18:49:17, output whole to a file and committed with a four-line header
in the corpus transcript's shape; the answer diffed against the corpus
transcript's 2.2 answer by line range, two lines different.

**What was found and not fixed, by the rule of the interlude.** The
answer at Part 7's own closes had printed 18,083.17 against the Part's
.18 since the formatter existed, unnoticed because the formatter test
formatted the float itself; fixed by the same commit, since it is the
same defect. Nothing else. Decision 76's question, whether a ratio is
computed in decimal, is sharper now: `distance_pp` is derived from an
exact currency figure, but as a float, and a ratio's stored double can
still sit below a tie; 76's entry says so and is unchanged.

**Not done, on purpose.** Decision 76. Every other miss the run logged,
S-2's comma included, all waiting on their triggers. R-8 and R-9. The
cleanup. Order 5, the CLI, the README, the demo recordings. Decisions
12, 13, 16 and 17 as work. The owner's four documents. A cross-check in
`_finding` between the published share and the published market value,
noted in §1 and not built.

---

## 5. Decisions taken, and decisions pending

**Taken this session, the owner's, small and recorded in decision 75's
entry:** the decimal subtraction inside `_finding` is decision 75's, not
76's. Brought with the arithmetic that forced it, a recommendation and
three rejected alternatives (the letter of the decision, which fails
Part 7's own half; a second rounding before the Decimal; waiting for 76).

**Pending — decide before writing code. Eleven by count, unchanged:**
10, 12, 13, 16, 17, 22, 45, 48, 52, 54 and 76. The cap is 25. Nothing was
opened and nothing closed.

10. A window return as a measure with a reference.
12. The hypothetical mode's instrument type.
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the
    IPS.
16. Company names, German phrasings, the softer 3.5.
17. The selection axis.
22. Volatility over as-traded closes or a total-return series.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, 11 and 36.
48. Part 13 E's item 7, second half only.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields.
76. Whether money and ratios are computed in decimal. **Not put on step
    4; stays pending.** What this session adds: the distance is now
    computed in decimal and published as its nearest float, which is
    exact for any amount of two decimals; the ratios the entry names are
    untouched, and its three candidate shapes stand.

- **The interlude between Orders 4 and 5** (owner's): steps 1, 2 and 3
  done; **step 4 done but for 76.** Step 5 the cleanup; then Order 5.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: **11/12**, 2.1 BLOCKED on routing. Level 4: 4.2, 4.4, 4.5
and 4.6 PASS; 4.1 and 4.3 BLOCKED at the PHI-2.1 stop. **15/18, by this
session's run at 18:42 UTC on 22 September.**

**Against the corpus: 30 of 65, by the run at 17:11 on 22 September**,
benchmark.md Part 3c.6, unchanged; **and 2.2 alone at 18:49 matched on
the two halves**, the second block. The spine's 19 turns: 10 matched, 9
missed. The variations: 6 of 15. The clarifications: 7 of 7. The
refusals: 0 of 7 run, every refusal itself right. The sequences: 7 of 17
turns, S-8 whole.

What the runner cannot see and the reading now has: whether an answer
carries the figures its entry pins, whether it cites the clauses, whether
it says what it did not do, **and now whether a printed cent is the
reference's cent, which pytest sees for Part 7 and no loop saw before.**
What neither sees, unchanged: whether the view is a defensible read of
the claims it cites; whether the range's ends are right; any due
prediction until 2027; whether a quote supports its claim; and whether
any answer reads well.

---

## 7. Next steps, in order

**1. The merge.** `half-cent` onto the trunk, `--ff-only`, then the push
by URL; the worktree removed after.

**2. R-8 and R-9, on their own yes**, the first EDGAR pull for Adobe,
with §2's prediction said again against the clocks of the day. Read
against Part 18's R-8 and R-9 and appended to Part 3c.6 as a third
block, two lines, dated the day they run.

**3. Step 5, the cleanup**, then Order 5 may open. When it does, the
record's four entries from the corpus run and the interlude entry close
on its commit, and the run after it is Part 3c.6's next block.

### Later, with reasons

- **Decision 76**, on the owner's word only; its entry lists what it
  owes before it is taken, and this session's finding about the float
  product belongs in that reading.
- **S-2's comma**, one line in `extraction.resolve`, the test first on
  the corpus wording; extraction survives Order 5, so it is worth a
  commit before it, and it is not step 4's.
- **The period vocabulary** in `config.DataConfig.period_days` is printed
  to the user by four clarifications and lives in code.
- **The router's swallowed exception** — a failed model call should raise
  with the provider's own message.
- **The emoji**: the answer-text headers, one commit, the runner run
  against it. The console glyphs are a separate session; the transcripts
  show how many there are.
- **`check_4_3`'s weight_source assertion cannot fail** while the
  candidate's id is printed (KNOWN_GAPS).
- **IPS-2.1 would pass an instrument the policy forbids**, being a
  statement clause (Part 17 G).
- **IPS-5.3's second limb** is not computed (decision 71).
- **Nothing records a model call's tokens**; a run's cost is an estimate
  from per-call figures.
- **`run_cases.py` could insert its own `src`** as `cli.py` does, so a
  worktree's runner scores the worktree without `PYTHONPATH`; one line,
  not this session's.
- **1 February 2027**: W-2.1 and W-2.2 fall due. **1 March 2027**: W-1.1
  and W-1.2.
- Three stale statements, the owner's to fix on the owner's word:
  `watchlist.toml`'s header and `test_watchlist.py`'s docstring, "read by
  nothing yet"; Part 11 D38's "D46".

---

## 8. Rules learned the hard way

**A rounding rule at the print site cannot round a half the arithmetic
never produced.** Decision 75 said half-up on a Decimal built from the
figure, and the figure was a float that sat a few billionths below the
half. The check written first, at the reference's own as-of, is what
showed it; the entry's own verification had been done at one day's
closes where the float product happened to be exact. **Check a
decision's arithmetic at the reference's as-of, not only at the day's.**

**A test that formats the float itself pins nothing.** The formatter test
asserted `f"{value:,.2f}"` was in the answer and passed in every session
since it was written while the answer printed Part 7's Equity distance a
cent short.
A printed figure is pinned against the reference's string, or it is not
pinned.

**Which tree a loop imports is checked before the loop is paid for.** The
editable install points at the checkout; a script with no path insert of
its own, run from a worktree, scores the trunk and reports it as the
branch. pytest and the CLI insert their own paths and were safe; the
runner was not.

**A brief's branch point is checked against the trunk head.** The brief
named the commit before the handoff correction it called done; a branch
from it would have been one commit short and could not have merged
fast-forward.

**The harness's refusals in a worktree are about shape, not intent.** A
`{ …; }` group, a loop ending in `git`, a `sed` range from a variable:
each was refused as too complex to verify, and each ran when split into
plain commands. Split first; do not reach for a script.

Still true, from earlier sessions: **a brief's clock is checked against
the interval's arithmetic, not its date**; **grep the class before
opening an entry**; **a rule that exists can still fail on the corpus
wording**; **count the turns before the run, and count them again
after**; **the capture is never filtered; the reading may be**; **a
worktree nested under the checkout finds the checkout's `.env` and can
share its database through a symlink**; **a brief can carry a line the
re-scope already retired**; **cite an entry by its title, and grep the
title before showing the diff**; **say which sequences work today, and
by what rule**; **a count about the writing includes the writing**;
**measure the cost before the first prompt**; **a pointer is cheaper
than a copy and cannot drift**; **a prompt change can move a question it
does not mention**; **the loop you ran the change against may not be the
loop that sees it**; **do not filter the output of a paid run**; **chase
the evidence, not the story you already have**; **grep the package, not
three files**; **measure a deletion before taking it, and say the number
twice**; **a decision's own arithmetic goes stale too**; **the record
names the requirement, not the audience**; **delete the surface, not the
file**; **a scoreboard that scores well-formedness will score a wrong
answer a pass**; **recompute the answer's arithmetic rather than reading
it**; **an exact half is where a rounding rule announces that it does not
exist**; **an exception swallowed into a `None` crashes somewhere that
cannot explain it**; **when everything fails at once, change one thing
and rerun the thing that worked**; **cut the branch before the first
commit**; **a golden line can be identical to another in four of its
five fields**; **grep the writer the reader reads**; **a test
parametrized over the constant it is checking cannot catch a wrong
constant**; **a check that looks for a word anywhere passes a line that
lost it**; **a wrong version that changes nothing is a finding**; **a
statement clause can carry a finding**; **a rule already implemented is
not implemented again**; **a type guard written against `Sequence` lets
a string through**; **a figure measured before a prompt changed is not a
figure about the call being made**; **a cost you cannot measure is a
cost you will misstate**; **take the shapes a caller actually has**;
**hand arithmetic is checked, and the check is part of the work**; **a
statement about the code goes stale four commits after it was true**;
**a guard that cannot fire is not a guard**; **pass `--color=no` to a
captured pytest run**; **look at a path before writing to it**; **a
refusal that is right can still be shaped wrong**; **a test over the
suite's copy owns the rows it reads**; **a number is measured before it
is written**; **a count in a message is counted**; **sight a new case
before writing its golden line**; **the registry's descriptions are the
prompt**; **add up the pending list**; **the owner's documents are
written on a separate word**; **say which loop cannot see a change**;
**a formatter states what the data says and never what the system is**;
**two paid loops on one SQLite file run one after the other**; **an
instruction with words missing is read against the record**; **a wrong
version checked in place can run the previous version's bytecode**;
**open the definition of done before recommending that something be
deleted for not being in it**; **search the record before logging a
finding**; **a defect found once in one figure is not one figure**; **a
byte-identical pair is one missing axis**; **an intent that answers is
not an intent that works**; **write a prediction where it cannot be
edited afterwards**; **a reference written before the code decides the
code**.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/tmp/golden_err.txt
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 2.1     # one Haiku call, ~$0.001
# from a worktree the runner needs the worktree's src, or it scores the checkout:
PYTHONPATH=src python tests/benchmark/run_cases.py

python src/agents/cli.py --portfolio 3        # :q to quit
# several questions through one process; a corpus sequence is consecutive turns here.
printf '%s\n' 'How has my JPM position performed since I bought it?' 'And MSFT?' 'And JNJ?' ':q' \
  | python src/agents/cli.py --portfolio 3
# the whole corpus: the printf line of every process is in the transcript's headers.
grep '^# printf' tests/golden/run_corpus_2026-09-22.txt

# is the API answering at all, before spending a loop on finding out:
python -c "import anthropic;from dotenv import load_dotenv;load_dotenv();\
print(anthropic.Anthropic().messages.create(model='claude-haiku-4-5-20251001',\
max_tokens=8,messages=[{'role':'user','content':'ok'}]).content[0].text)"

git status --short
git log --oneline dfbc7d2..HEAD
git rev-list --count dfbc7d2..HEAD

# the corpus: prompts, answers, and the runs' readings
grep -n '^### 3c\|^| [VCRS]-\|^\*\*S-' docs/benchmark.md
grep -n '^## Part 18\|^### [0-9]\|^- \*\*[CRS]-' tests/golden/expected_values.md | sed -n '/Part 18/,$p'
grep -n '^\*\*Run of' docs/benchmark.md

# decision 75's check, and the two halves at the print site:
pytest -q tests/test_half_cent.py
python -c "from decimal import Decimal; print(Decimal(repr(286857.5 - 0.65 * 411238.5)))"   # the float misses the half
PYTHONPATH=src python -c "from agents.nodes import _cents; print(_cents(19552.475), _cents(18083.175))"

# what the database says it is at (expected 2445c12e728c):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# the price and filings clocks, which decide what a paid loop fetches:
sqlite3 data/portfolio.db "select a.ticker, m.last_price_fetch_time from asset_fetch_metadata m join assets a on a.id=m.asset_id order by a.ticker;"
sqlite3 data/portfolio.db "select cik, pulled_at from filers; select * from filed_fetch_metadata; select max(pulled_at) from ticker_ciks;"

# what a paid loop wrote, against the prediction (the column is calls_consumed):
sqlite3 data/portfolio.db "select bucket_key, calls_consumed from api_quotas order by id desc limit 1;"
sqlite3 data/portfolio.db "select count(*), max(date) from daily_prices;"
sqlite3 data/portfolio.db "select cik, count(*) from filed_facts group by cik;"

# the intent vocabulary and the roster:
PYTHONPATH=src python -c "from agents.schemas import INTENTS, AGENTS; print(len(INTENTS), sorted(INTENTS)); print(len(AGENTS), sorted(AGENTS))"

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only half-cent
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~6s, no model calls | Do the components still work; does every reference Part reproduce; does each node fetch in order and publish its block; does the gate refuse what it must; does the outcome compose every row of the truth table; do Part 3c.1's wordings match the runner's; **does the compliance answer print Part 7's cents**. Sees nothing of the corpus's answers. |
| CLI | ~2s and one Haiku call for most questions; 4.3 about 15s and two Sonnet calls, 4.4 about 14s and one; a deterministic clarification free; **fetches prices past their interval, which runs out on the 23rd at 17:11 UTC** | What it is actually doing: the plan, the parameters, the reasoning line, the answer text. **The only loop that shows an answer, and therefore the only loop that can be read against Part 18.** The whole corpus is 65 turns, 2 minutes 19 seconds and about 0.15 dollars. |
| Golden set | ~50s, about $0.039 per run; writes to no table since decision 51, prices aside | Did routing change anywhere (twenty-one lines, one pinned failure). Blind to `measure`, `group_by`, `tickers`, answer text, and any wording it does not carry |
| Benchmark runner | ~60s, about $0.039; `--case X` is one routing at about $0.001; **from a worktree, `PYTHONPATH=src`** | How many cases pass, n/18. Its checks read each answer's text and show it to nobody, and cannot tell one cent from another. **Carries none of the 41 corpus additions** |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once. **Never pipe a paid run through a filter.** **The corpus is
read by hand against Part 18; a run gets its dated block in Part 3c.6 and its
transcript beside `expected.txt`; a miss is logged with a trigger, not fixed,
until step 4's rule says it is arithmetic.**
