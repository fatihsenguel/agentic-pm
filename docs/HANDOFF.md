# AGENTIC_FINANCE — Session Handoff

**Session date:** 22 September 2026 (thirty-seventh session), begun about 20:05 UTC. Regenerated at its end. The thirty-third to thirty-sixth sessions ran earlier the same day.
**Branch:** `adobe`, cut from `baseline-v1` at **8099988** before the first commit, in a worktree under `.claude/worktrees/` because this session's harness rejects edits outside one; **six commits with this one**, not merged, not pushed. The trunk at 8099988 is the thirty-sixth session's handoff commit, merged `--ff-only` from `half-cent` and pushed on the evening of the 22nd, and `git ls-remote` shows the remote's `baseline-v1` at that commit. `origin`'s push URL is `no_push` and the push goes by URL, so the local `origin/baseline-v1` ref lags: it stands at **33769f6**, the "Decision 76" commit; `git rev-list --count origin/baseline-v1..HEAD` says forty-five for the trunk and fifty-one for this branch with this commit. The push output is the record.

**State:** pytest **1934 passed, 6 xfailed**, unchanged; run at session start in the worktree and again after the record commits. **Two paid loops ran, one after the other, on their own yes: R-8 through the CLI at 20:35 UTC, one Haiku call, and R-9 at 21:06, one Haiku call and four Sonnet calls.** The runner was not run: no answer text changed. The golden set was not run: no prompt changed. **Step 3 of the interlude is sent whole: 67 of 67 corpus turns**, 31 matched over the two runs. Step 4 stands done but for decision 76. The pending list stands at eleven, unchanged.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Sections whose claims were checked again this session and
still hold are kept word for word; the rest is rewritten. This session
checked the counts, the clocks, the store before and after each paid
loop, the origin and remote refs, the merge, and which source tree each
loop imports from a worktree; it did not re-check §3's library versions
or the migration count beyond the head.

**This was a two-turn session.** The corpus's last two prompts, both
naming Adobe, a filer with no row and no facts, were sent for the first
time, one process each, the store read before and after each, and the
answers read by hand against Part 18. Nothing was fixed: one commit of
correction to the previous handoff, one transcript, one block in
benchmark.md, two of record, and this.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1 to 4 are built. The interlude between Orders 4 and 5 is its unnumbered paragraph under Order 4, last revised 22 September. Unchanged this session. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. **176 lines start `**Trigger:**`**, unchanged in count: one changed its text, "What W-2 needs before it has a range", whose trigger fired on R-8 and now names the growth pair as the owner's. **Start with "The interlude between Order 4 and Order 5, and how the corpus is built"**, whose step 3 now says sent whole. Three entries carry this session's dated line: that one; "A buy question about a company on no entry arrives shaped as an error", which now holds R-9 as the same shape from the other side of the watchlist check; and "A refused section is asked for again on every run", which now holds Adobe's Item 1. Nothing was opened. |
| `docs/benchmark.md` | **The definition of done, the corpus, and its runs.** Part 3c.6 now holds three blocks: the run of 22 September at 17:11, 65 turns; 2.2 alone at 18:49; and **R-8 and R-9 at 20:35 and 21:06, two lines, the corpus sent whole.** **Read Part 2, Part 3c and 3c.6 before Part 3's tables.** |
| `tests/golden/expected_values.md` | Hand-computed reference, Parts 1 to 18. **Unchanged this session, by a character.** Part 18's R-8 and R-9 are the two entries read against. Never update it to match code output. |
| `tests/golden/run_R-8_R-9_2026-09-22.txt` | **New, 285 lines.** The two turns, one process each, captured whole with the corpus transcript's header shape: R-8 at 20:35 UTC, exit 20:35:54; R-9 21:06:23 to 21:07:18. Each body was diffed against its raw capture before the header was put on it. |
| `tests/golden/run_corpus_2026-09-22.txt` | The corpus transcript, 5,887 lines, the run of 17:11. Unchanged. |
| `tests/golden/run_2.2_2026-09-22.txt` | 2.2 alone at 18:49, 187 lines. Unchanged. |
| `tests/test_half_cent.py` | Decision 75 held to Part 7, Part 17 B and the corpus run's closes. Unchanged. |
| `tests/test_corpus_spine.py` | Part 3c.1's eighteen wordings are the runner's `CASES`. Unchanged. |
| `tests/golden/expected.txt` | Twenty-one lines, one pinned failure. Unchanged; not run this session. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Eighteen cases, unchanged, not run this session; 15/18 by the run at 18:42 on the 22nd. |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets. Not opened this session. |
| `docs/IPS.md`, `docs/PHILOSOPHY.md`, `docs/WATCHLIST.md`, `watchlist.toml` | The owner's. Unchanged, not edited. W-2 still states no growth pair and no weight, which is why R-8 and R-9 refuse. |
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
not the plan. The corpus is written on that rule, run on it, now sent
whole, and the one arithmetic miss it found is fixed on it.

### What this session found, in one paragraph

Two prompts name Adobe, a candidate on the watchlist whose entry states
neither a growth pair nor a weight, and both are pinned as refusals that
name the entry and the gap. R-8, "What is ADBE worth?", refused the range
as pinned: the first EDGAR pull for the filer stored its row, SIC 7372
and not excluded, 17,117 facts across seventeen November fiscal years,
an assets row from W-2's currency and five closes, and the answer names
W-2 and both missing assumptions with no range and no point. R-9,
"Should I buy ADBE?", refused for the pinned reason and in the wrong
shape: the position step asks for the weight only after the research
agent has fetched the 10-K, read its sections on Sonnet and proposed a
prediction, and the weight's raise lands in the node's catch-all, so the
answer is "Some issues occurred" and "Research not done" rather than a
refusal, with the screening block already published and never rendered.
That is R-7's logged shape from the other side of the watchlist check.
Beside it, the reader refused Adobe's Item 1 on a quote whose first words
the model had rewritten, which the record is for, and Items 1A and 7
were accepted first time. Nothing was fixed; three entries grew.

### Design principles

Unchanged in the code. What this session saw them do, live:

- **Raise, do not repair.** The range refused on a missing growth pair,
  the position on a missing weight, a reading on a quote not in the
  section. No default was reached for anywhere.
- **Hot potato.** The 10-K's text went into `filed_documents` and the
  reader; the answer carries none of it, and the refused proposal's
  figure was printed nowhere.
- **A refusal is an honest failure; its shape can still be wrong.** R-9
  is right and reads as a failure. Rendering, not arithmetic; not step
  4's.
- **Every number in an answer traces to a tool output.** R-8's close and
  its date are the row's own.
- **Nothing is written into the ledger or the watchlist by the system.**
  The proposal W-2.3 exists in the transcript and nowhere else.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
  This session took none.
- **A paid loop says first what it will fetch and store, table by table,
  and afterwards what moved.** Predicted by the clock and held to the
  row: every count of R-8's prediction held; R-9's held but for one,
  readings 5 to 7 rather than 8, because a refused section leaves no row.
  **A count of readings is predicted as a range, not a number.**
- **A brief's clock is read against the interval's arithmetic.** The
  brief said every clock had run out since the 23rd; at 20:12 UTC on the
  22nd none had, and the prediction was written per branch of the clock
  and said so before the prompt.
- **Which source tree a loop imports is checked before it is paid for.**
  Both loops ran through `cli.py`, which inserts its own parent, from the
  worktree.
- **The capture is never filtered.** Both processes wrote their whole
  output to a file under the job's temporary directory; the transcript
  is those two files with headers around them, checked by diff.
- **A count in a message is counted.** The store's twelve counts were
  read from the tables before and after each loop and before the message
  named them.
- **Grep the heading before citing it, and grep the class before opening
  an entry.** Three findings, three existing entries; none opened.
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
arithmetic.** No second rounding rule to make a float land on a half, and
no rounded figure published in a block. **No growth pair and no weight
written on W-2 to make an answer pass: the entry is mine.**

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

**Two of the five ran.** pytest: **1934 passed, 6 xfailed**, about 7
seconds, at session start and after the record commits. The CLI: R-8
alone, then R-9 alone. The runner and the golden set were not run.

**Golden set: twenty-one lines, one pinned failure**, `expected.txt` at
4f7ca89. Not run.

**The runner: 15/18, 0 failing, 3 blocked** by the thirty-sixth
session's run at 18:42 UTC on the 22nd. 2.1 blocked on routing, 4.1 and
4.3 on the PHI-2.1 stop. Not run this session.

**The corpus: 67 of 67 sent, 31 matched.** 30 of 65 by the run at 17:11
and the reading in benchmark.md Part 3c.6; 2.2 alone at 18:49 matched on
the two halves; **R-8 matched and R-9 missed by this session's run**, the
third block.

### Branches and tags

`baseline-v1` is the trunk at **8099988**, pushed to that commit on the
evening of 22 September; `adobe` is cut from it and carries this
session's six commits, **to be merged `--ff-only` by the owner**. The
`adobe` worktree holds a symlink `data/portfolio.db` to the checkout's
database, gitignored, so pytest and the CLI there ran against the real
store, and `.env` was found by walking up from the worktree; the same
arrangement serves any later worktree.
`half-cent`, `intents-parked` at addfbc7 (the tree that still had the
three intents), `corpus-run`, `handoff`, `rounding`, `halves`,
`judgement`, `gate`, `thesis`, `reader`, `research`, `score`, `publish`,
`range`, `keys`, `node`, `filer`, `bridge`, `consolidate`, `selection`,
`compliance`, `vocabulary`, `intents`, `arc`, `counts`, `corpus` and
`direction` are merged and older. `wip/phase7-snapshot` holds rejected
Compliance/IPS code. `wip/rag-early` and tag `rag-early-parked` hold the
RAG code. `quant-inventory-parked` at 8d87455 holds the tree before the
seventeenth session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`2445c12e728c`**, checked; no migration this session. No reseed. **Read
before and after each paid loop, at 20:35, 20:36 and 21:07 UTC; what
moved is what the prediction said, one readings row aside.**

- `daily_prices` **7,024**, last close **2026-09-21**; the five new rows
  are ADBE's, 09-15 to 09-21, asset id 16. The one-day interval,
  `(utcnow - last).days >= 1` in `data_manager.py`, runs out at **17:11
  UTC on the 23rd** for the nine holdings, 17:12 for GOOGL and **20:35
  on the 23rd for ADBE**. The provider is asked through today exclusive,
  so a fetch on the 23rd stores the 22nd's close and not the 23rd's.
- `assets` **11**: ADBE the eleventh, id 16, ADOBE INC., USD, no asset
  class, no instrument type, no sector, as decision 57 creates it.
  `asset_fetch_metadata` **11**, ADBE stamped 2026-09-22 20:35:53.
  `api_call_logs` **2,491**. `api_quotas` last row
  `daily_yfinance_2026-09-22` at **11**.
- `filers` **4**: Adobe's row 796343, ADOBE INC., SIC 7372,
  Services-Prepackaged Software, pulled 2026-09-22 20:35:50.
  `filed_facts` **45,904**: Apple 15,132, Adobe 17,117, Alphabet 13,655.
  `filed_fetch_metadata` **3**, Adobe's at 20:35:51. `ticker_ciks`
  10,422, unchanged. `filed_documents` **2**: Alphabet's FY2025 10-K and
  Adobe's, 0000796343-26-000003, 344,376 characters.
  `document_readings` **7**: Alphabet's five, and Adobe's Item 1A and
  Item 7 under the same prompt versions. **Adobe's Item 1 has no row**:
  every thesis or position question about ADBE asks Sonnet for it again
  until a request returns a faithful reading.
- **The filings clocks, as stored and against the whole-days test
  `(now - pulled_at).days < 7` in `filings.py`**: Apple's facts pulled
  2026-09-15 22:17 UTC, so run out at **22:17 UTC on the 22nd**, tonight,
  and are read by no runner case; Apple's filer row 09-16 00:03, JPM's
  filer row 09-16 01:33 and the ticker file 09-16 01:33, Alphabet's
  filer row and facts 09-16 01:38, so those run out at **00:03, 01:33
  and 01:38 UTC on the 23rd**; **Adobe's filer row and facts run out at
  20:35 UTC on the 29th.** The next paid run of a Level 4 question after
  01:38 on the 23rd refetches the ticker file, JPM's and Alphabet's
  filer rows and Alphabet's facts, which should store zero new rows or
  raise on a changed figure; after 17:11 it also fetches the closes for
  the 22nd.

Unchanged: portfolio 3 the only portfolio, nine ledger rows, cost basis
284,500 plus 15,500 cash, USD, policy `ips.toml`. There is no holdings
table. `pipeline_runs` 5, `transactions` 9.

---

## 3. Environment

Not re-checked this session except where marked; kept from the
thirty-sixth session's handoff.

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- **The venv holds an editable install of the checkout's `src`**
  (`__editable__.agentic_finance-0.1.0.pth`). From a worktree: pytest
  imports the worktree's tree because `tests/conftest.py` inserts its
  own `src` first; the CLI does because `cli.py` inserts its own parent
  directory (checked again: both paid loops printed the worktree's
  philosophy and watchlist paths); **`tests/benchmark/run_cases.py`
  inserts nothing and imports the checkout's code**, so from a worktree
  it scores the trunk, not the branch, unless run with `PYTHONPATH=src`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files. `load_dotenv()` in `config.py`
  finds it by walking up from the calling file, so a worktree nested
  under the checkout reads the checkout's `.env` (checked again: both
  paid loops ran from the worktree).
- **Anthropic has credits**; the two loops cost about 0.15 dollars by the
  per-token prices and the section sizes, tokens unrecorded. An empty
  balance fails with a 400 `invalid_request_error` naming the credit
  balance, and from inside the system every question returns `intent:
  None`.
- `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU` for the router. `ANTHROPIC_SONNET`
  is `claude-sonnet-5`, used by the reader, the proposer and the view, and
  refuses a temperature. The reader's cache is keyed by accession,
  section, model and prompt version; Adobe's two readings were stored
  under the same prompt versions as Alphabet's, so nothing about the
  reader moved. A reading of a section is about 15 to 18 seconds.
- The `anthropic` SDK is 1.2.0; yfinance 1.7.0 with an exclusive `end`.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing. This session fetched Adobe's submissions document
  twice (the filer row, then the 10-K's row for the document fetch; the
  second is stored nowhere, KNOWN_GAPS "The filer fetch downloads the
  filings index it discards"), its company facts once and its FY2025
  10-K's primary document once.
- **The period vocabulary**: `config.DataConfig.period_days`, a default in
  code, keys `1Y, 2Y, 3Y, 5Y, 10Y`, passed to extraction by
  `smart_router.py`. Not in `config.toml`.
- **Extraction** (`src/agents/extraction.py`): unchanged; "ADBE" was read
  as the ticker on both prompts and "buy" set `asks` to position.
- `config.toml` carries five fetch intervals: prices 1 day, filings 7,
  earnings 7, profile 30, shares 30. Its `[macro]`, `[optimization]` and
  `[backtest]` sections stand although two have no consumer.
- **Decimal in the code**: as the thirty-sixth session's handoff said,
  not re-checked: `proposals.py`, `compliance.py` and `nodes.py` build a
  Decimal from a float's repr for a distance and its printed cent.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; scripts run from the root. The URL in `.env`
  is relative, so from the worktree it resolves through the symlink.
- The CLI's quit command is `:q`; `exit` goes to the router. Several
  questions go through one process with `printf '%s\n' 'q1' 'q2' ':q' |
  python src/agents/cli.py --portfolio 3`, each its own graph run. The
  CLI passes the previous turn's final state to the next. `input()` at
  end of input returns, so a piped process ends cleanly after `:q`, and
  the capture ends at the prompt with no newline.
- A single benchmark case runs with `--case`, one Haiku routing.
- zsh does not split an unquoted variable into words and has no `tac`; a
  `grep -c` that finds nothing exits 1; `%` in a `printf` format is `%%`;
  BSD `sed` has no `0,/re/`; BSD `cat` has no `-A`; `awk` has no `\s`;
  `--include='*.py'` must be quoted. **This session's harness refused, in
  the worktree, a `source` of the venv's activate script, a quoted
  absolute path to the interpreter, a shell variable standing in a
  path, and any pipe into `od`; the relative interpreter path
  `../../../.venv/bin/python`, literal paths and `tail -c` alone ran.**
- **What is no longer in the tree**: as the thirty-third session's handoff
  listed it, unchanged; nothing was deleted this session.

---

## 4. What the thirty-seventh session did

`git log --oneline 8099988..HEAD`, **six commits** with this one, the
first five touching four files, **370 insertions and 9 deletions**, of
which the transcript is 285 lines; this handoff is a rewrite of one file
on top. In the owner's order: the handoff's branch line, the prediction,
R-8, the store, R-9, the reading, the record.

**Read first, and only what the brief named**: DIRECTION.md, the previous
handoff and its §0, the interlude entry's step 3, Part 18's R-8 and R-9
whole, the previous handoff's §2 paragraph on the first fetch for Adobe,
and, when their triggers fired or the brief pointed at them, the R-7
entry, the two W-2 entries and the refused-section entry. Then the code
the prediction needed: the terminal table and `REQUIRES`, the screening
node whole with `_last_close`, the research node and `_position`, the
gate node, `filings.py`, the reader, the research and thesis formatters,
the price window, the EDGAR provider, and the 4.2, 4.3 and R-7 turns of
the corpus transcript as precedents. **The brief's claims, checked**:
pytest's number held; the merge and the push held and the remote was
asked; **the clocks had not run out**, the brief's "since the 23rd"
describing the next day; ADBE's absence from `filers` and `filed_facts`
held, the ticker file already mapping it to 796343.

**The prediction, before the first prompt.** R-8's plan ScreeningAgent
alone, by 4.2's precedent and the terminal table, so no holding's close;
the ticker file inside its interval; Adobe's filer row created with SIC
7372, none of PHI-3.2's seven codes, all of which are banks, thrifts,
brokers and insurers in the 6000s; its facts fetched, count unknown; an
assets row from W-2's currency and five closes to the 21st on one
yfinance call, the provider being asked through today exclusive; the
range refused naming both ends; the screen unpinned. R-9's plan the four
agents; nothing fetched but the 10-K's document; three sections read and
one proposal made before the weight is asked for; the raise as an error
in R-7's shape; four Sonnet calls, about 15 cents. Every table's count
written before the prompt and read after.

**The commits.**
- **573cc04** `docs/HANDOFF.md`: the branch line and §2 corrected to the
  merged state, dated.
- **96bb5d8** `tests/golden/run_R-8_R-9_2026-09-22.txt`, captured whole.
- **aaefd67** benchmark.md Part 3c.6: the third block, two lines.
- **0a8c8c9** KNOWN_GAPS: dated lines on three existing entries, and one
  trigger's text.
- **2fb46d5** KNOWN_GAPS: the interlude's step 3 sent whole, 67 of 67.

**The two paid loops, as they were driven.** Each one process from the
worktree, `printf` piped into `cli.py`, output whole to a file under the
job's temporary directory, the store read between them. R-8 exited at
20:35:54 UTC after 5.4 seconds of graph time; R-9 ran 21:06:23 to
21:07:18, 54.7 seconds, of which the three readings were 49. The
transcript was assembled from the two captures with cat and printf and
each body diffed against its capture.

**What was found and not fixed, by the rule of the interlude.** R-9's
shape: an error where a refusal was pinned, the screening block
unrendered, the outcome and its grounds absent, and the 10-K read before
the weight was asked for, about 15 cents for an answer the watchlist
loader could have given before the first call; rendering and the order
of the position step, neither arithmetic. Adobe's Item 1 refused on a
rewritten quote and asked for again on every run; the record working.
The screen stopping at PHI-2.1 on FY2021's return on invested capital,
the clause Alphabet stops on; unpinned, and the PHI-2.1 stop is the
runner's known block on 4.1 and 4.3.

**Not done, on purpose.** Decision 76. Every other miss the runs logged,
S-2's comma included, all waiting on their triggers. W-2's weight and
growth pair, the owner's. Step 5, the cleanup. Order 5, the CLI, the
README, the demo recordings. Decisions 12, 13, 16 and 17 as work. The
owner's four documents. The cross-check in `_finding` between the
published share and the published market value, noted by the thirty-sixth
session and not built.

---

## 5. Decisions taken, and decisions pending

**Taken this session:** none. Nothing was opened and nothing closed.

**Pending — decide before writing code. Eleven by count, unchanged:**
10, 12, 13, 16, 17, 22, 45, 48, 52, 54 and 76. The cap is 25.

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
76. Whether money and ratios are computed in decimal. Stays pending on
    the owner's word; its entry is unchanged this session.

- **The interlude between Orders 4 and 5** (owner's): steps 1, 2 and 3
  done, **step 3 now sent whole**; step 4 done but for 76. Step 5 the
  cleanup; then Order 5.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: **11/12**, 2.1 BLOCKED on routing. Level 4: 4.2, 4.4, 4.5
and 4.6 PASS; 4.1 and 4.3 BLOCKED at the PHI-2.1 stop. **15/18, by the
thirty-sixth session's run at 18:42 UTC on 22 September**; not run since.

**Against the corpus: 31 of 67, all 67 sent**, benchmark.md Part 3c.6's
three blocks. The spine's 19 turns: 10 matched, 9 missed. The
variations: 6 of 15. The clarifications: 7 of 7. The refusals: **1 of 9,
every refusal itself right**; R-8 the one, R-9 in R-7's shape. The
sequences: 7 of 17 turns, S-8 whole.

What the runner cannot see and the reading now has: whether an answer
carries the figures its entry pins, whether it cites the clauses, whether
it says what it did not do, whether a printed cent is the reference's
cent, **and now whether a refusal arrives as a refusal or as a failure,
which no check reads.** What neither sees, unchanged: whether the view is
a defensible read of the claims it cites; whether the range's ends are
right; any due prediction until 2027; whether a quote supports its claim;
and whether any answer reads well.

---

## 7. Next steps, in order

**1. The merge.** `adobe` onto the trunk, `--ff-only`, then the push by
URL; the worktree removed after.

**2. Step 5, the cleanup**, then Order 5 may open. When it does, the
record's four entries from the corpus run and the interlude entry close
on its commit, and the run after it is Part 3c.6's next block, all 67
turns. **The closes of the 22nd and the refetch of the ticker file and
two filers' rows and facts come with the first paid Level 4 run after
01:38 UTC on the 23rd**: say so before it, table by table.

### Later, with reasons

- **Decision 76**, on the owner's word only; its entry lists what it
  owes before it is taken.
- **The order of the position step**: the weight is the watchlist
  loader's before any call, and R-9 asks for it after the reading and the
  proposal. Whether the check moves in front of the reading is a shape of
  the research node, logged on the R-7 entry, and Order 5 rebuilds the
  node's frame; not the interlude's.
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
  from per-token prices and section sizes.
- **`run_cases.py` could insert its own `src`** as `cli.py` does, so a
  worktree's runner scores the worktree without `PYTHONPATH`; one line,
  not this session's.
- **1 February 2027**: W-2.1 and W-2.2 fall due; Adobe's facts are now
  stored and go stale on the 29th like any other filer's. **1 March
  2027**: W-1.1 and W-1.2.
- Three stale statements, the owner's to fix on the owner's word:
  `watchlist.toml`'s header and `test_watchlist.py`'s docstring, "read by
  nothing yet"; Part 11 D38's "D46".

---

## 8. Rules learned the hard way

**A refusal can arrive in a failure's shape from either side of a
check.** R-7 fails because the company is on no entry and the screen
raises before the research agent; R-9 fails because the company is on an
entry that states no weight and the research agent raises after reading.
The same catch-all prints both as "Some issues occurred". A shape logged
for one cause is checked against the other before a new entry is opened.

**A count of readings is predicted as a range.** A refused section leaves
no row, and whether the model quotes faithfully is a new draw each
request; readings 5 to 7 was the one line of the prediction that did not
hold as a number, and it could not have.

**The reader's record catches a rewritten sentence start.** "... and
license the majority ..." became "We license the majority ..." in the
model's quote, and the presence check refused it. A quote is checked
against the text, never trusted for reading well.

**The work before a refusal is measured, in calls and cents.** The
watchlist loader knows W-2 states no weight before the first call; the
answer says so after a document fetch, three readings and a proposal.
What a refusal costs is part of its reading.

**A brief's clock is read against the interval's arithmetic, not its
date**, a second time in two sessions: "since the 23rd" on the evening
of the 22nd. Write the prediction per branch of the clock and say which
branch the run took.

Still true, from earlier sessions: **a rounding rule at the print site
cannot round a half the arithmetic never produced**; **a test that
formats the float itself pins nothing**; **which tree a loop imports is
checked before the loop is paid for**; **a brief's branch point is
checked against the trunk head**; **the harness's refusals in a worktree
are about shape, not intent**; **grep the class before opening an
entry**; **a rule that exists can still fail on the corpus wording**;
**count the turns before the run, and count them again after**; **the
capture is never filtered; the reading may be**; **a worktree nested
under the checkout finds the checkout's `.env` and can share its database
through a symlink**; **a brief can carry a line the re-scope already
retired**; **cite an entry by its title, and grep the title before
showing the diff**; **say which sequences work today, and by what rule**;
**a count about the writing includes the writing**; **measure the cost
before the first prompt**; **a pointer is cheaper than a copy and cannot
drift**; **a prompt change can move a question it does not mention**;
**the loop you ran the change against may not be the loop that sees it**;
**do not filter the output of a paid run**; **chase the evidence, not the
story you already have**; **grep the package, not three files**;
**measure a deletion before taking it, and say the number twice**; **a
decision's own arithmetic goes stale too**; **the record names the
requirement, not the audience**; **delete the surface, not the file**;
**a scoreboard that scores well-formedness will score a wrong answer a
pass**; **recompute the answer's arithmetic rather than reading it**;
**an exact half is where a rounding rule announces that it does not
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
statement about the code goes stale four commits after it was true**; **a
guard that cannot fire is not a guard**; **pass `--color=no` to a
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
# the whole corpus: the printf line of every process is in the transcripts' headers.
grep -h '^# printf' tests/golden/run_corpus_2026-09-22.txt tests/golden/run_R-8_R-9_2026-09-22.txt

# is the API answering at all, before spending a loop on finding out:
python -c "import anthropic;from dotenv import load_dotenv;load_dotenv();\
print(anthropic.Anthropic().messages.create(model='claude-haiku-4-5-20251001',\
max_tokens=8,messages=[{'role':'user','content':'ok'}]).content[0].text)"

git status --short
git log --oneline 8099988..HEAD
git rev-list --count 8099988..HEAD

# the corpus: prompts, answers, and the runs' readings
grep -n '^### 3c\|^| [VCRS]-\|^\*\*S-' docs/benchmark.md
grep -n '^## Part 18\|^### [0-9]\|^- \*\*[CRS]-' tests/golden/expected_values.md | sed -n '/Part 18/,$p'
grep -n '^\*\*Run of' docs/benchmark.md

# decision 75's check, and the two halves at the print site:
pytest -q tests/test_half_cent.py
PYTHONPATH=src python -c "from agents.nodes import _cents; print(_cents(19552.475), _cents(18083.175))"

# what the database says it is at (expected 2445c12e728c):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# the price and filings clocks, which decide what a paid loop fetches:
sqlite3 data/portfolio.db "select a.ticker, m.last_price_fetch_time from asset_fetch_metadata m join assets a on a.id=m.asset_id order by a.ticker;"
sqlite3 data/portfolio.db "select cik, name, sic, pulled_at from filers; select * from filed_fetch_metadata; select max(pulled_at) from ticker_ciks;"

# what a paid loop wrote, against the prediction (the column is calls_consumed):
sqlite3 data/portfolio.db "select bucket_key, calls_consumed from api_quotas order by id desc limit 1;"
sqlite3 data/portfolio.db "select count(*), max(date) from daily_prices;"
sqlite3 data/portfolio.db "select cik, count(*) from filed_facts group by cik;"
sqlite3 data/portfolio.db "select accn, section, model from document_readings;"

# the intent vocabulary and the roster:
PYTHONPATH=src python -c "from agents.schemas import INTENTS, AGENTS; print(len(INTENTS), sorted(INTENTS)); print(len(AGENTS), sorted(AGENTS))"

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only adobe
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~7s, no model calls | Do the components still work; does every reference Part reproduce; does each node fetch in order and publish its block; does the gate refuse what it must; does the outcome compose every row of the truth table; do Part 3c.1's wordings match the runner's; does the compliance answer print Part 7's cents. Sees nothing of the corpus's answers. |
| CLI | ~2s and one Haiku call for most questions; a screen of a new filer about 5s and two EDGAR fetches; a position or thesis question about a filer with no cached reading about 55s and four Sonnet calls, about 15 cents; a deterministic clarification free; **fetches prices past their interval, which runs out on the 23rd at 17:11 UTC** | What it is actually doing: the plan, the parameters, the reasoning line, the answer text. **The only loop that shows an answer, and therefore the only loop that can be read against Part 18.** The whole corpus is 67 turns, about 3 and a half minutes and about 0.30 dollars. |
| Golden set | ~50s, about $0.039 per run; writes to no table since decision 51, prices aside | Did routing change anywhere (twenty-one lines, one pinned failure). Blind to `measure`, `group_by`, `tickers`, answer text, and any wording it does not carry |
| Benchmark runner | ~60s, about $0.039; `--case X` is one routing at about $0.001; **from a worktree, `PYTHONPATH=src`** | How many cases pass, n/18. Its checks read each answer's text and show it to nobody, and cannot tell one cent from another, nor a refusal from a failure. **Carries none of the 41 corpus additions** |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once. **Never pipe a paid run through a filter.** **The corpus is
read by hand against Part 18; a run gets its dated block in Part 3c.6 and its
transcript beside `expected.txt`; a miss is logged with a trigger, not fixed,
until step 4's rule says it is arithmetic.**
