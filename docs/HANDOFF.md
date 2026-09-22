# AGENTIC_FINANCE — Session Handoff

**Session date:** 22 September 2026 (thirty-fourth session), begun about 14:20 UTC. Regenerated at its end. The thirty-third session ran earlier the same day and executed decision 51.
**Branch:** `corpus`, cut from `baseline-v1` at **b308b71** before the first commit, **eleven commits** counting this one. The owner merges and pushes; `origin`'s push URL is `no_push`. **The trunk is still sixteen ahead of `origin/baseline-v1`** from the previous session, and `corpus` adds eleven on top of it.

**State:** pytest **1926 passed, 6 xfailed**, run once at session start and matching the previous handoff's number; nothing that runs was touched. **No paid loop ran**: the golden set, the runner and the CLI were not started, and every table of the store is where the previous session left it. **The runner is 15/18 by the previous session's run and was not rerun.** Step 2 of the interlude, the corpus, is **written**: benchmark.md Part 3c and expected_values.md Part 18. The pending list stands at eleven, unchanged.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Sections whose claims were checked again this session and
still hold are kept word for word; the rest is rewritten. This session
checked the counts, the tag, the clocks and the store; it did not re-check
§3's library versions or the migration count beyond the head.

**This was a writing session.** Nothing was run against the system and
nothing was fixed. The corpus was written before any of it is executed,
which is the reference rule and the whole point: a corpus written after a
run is a transcript. **Step 3, running it once to capture the baseline, is
the next session**, and it is the first paid run since the clocks ran out.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1 to 4 are built. The interlude between Orders 4 and 5 is its unnumbered paragraph under Order 4; **its sentence "what is pinned exactly against what is pinned by invariants" is now stale**, the entry it points at having been corrected on the 22nd, and it is the owner's to revise. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. **172 lines start `**Trigger:**`**, unchanged. **Start with "The interlude between Order 4 and Order 5, and how the corpus is built"**, whose step 2 now says written and whose verbosity line was corrected this session. Then "Deleting three intents moved case 2.1 to risk_analysis", which carries a dated note that the wording is pinned. |
| `docs/benchmark.md` | **The definition of done, and now the corpus.** Levels 1 to 4 unchanged. **New Part 3c, after 3b**: the rules of the corpus, the eighteen spine wordings verbatim as the runner sends them, fifteen extraction variations, seven clarifications, nine refusals, eight sequences. No status column; the runner is still the status of Levels 1 to 4. **Read Part 2 and Part 3c before Part 3's tables.** |
| `tests/golden/expected_values.md` | Hand-computed reference, **Parts 1 to 18**. **New Part 18**: one entry per corpus prompt and turn, pinned by required content. Never update it to match code output. Part 18 carries no figure that Parts 1 to 17 do not, except the two subtractions of the 12% row, written out. |
| `tests/golden/expected.txt` | Twenty-one lines, one pinned failure. Unchanged; not run this session. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Eighteen cases, unchanged, not run. Its `CASES` list is the source of the spine's wordings, which Part 3c.1 now restates verbatim; the two can drift and nothing checks that they agree. |
| `tests/golden/expected_values.xlsx` | The workbook, eleven sheets, **read once, read-only, through openpyxl, to compare the `Answers` sheet's 1.1 to 1.4 text against Part 5**; not written. Parts 9 C, 11, 14, 15, 16, 17 and 18 have no sheet. |
| `docs/IPS.md` | The policy, synthetic, 17 clauses. Unchanged. Read whole this session. |
| `docs/PHILOSOPHY.md` | Seventeen clauses. Unchanged. Read whole this session. |
| `docs/WATCHLIST.md` | Two candidates, four predictions due early 2027, none scored. Unchanged. **W-2 states no growth pair and no weight**, checked in `watchlist.toml`, which is why corpus R-8 and R-9 refuse. |
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
not the plan. The corpus is written on that rule.

### The corpus, as written

- **Where.** benchmark.md Part 3c holds the prompts, expected_values.md
  Part 18 the answers. A prompt points at its answer; an answer points at
  the Part and table of every figure. Rejected: new Levels under Part 3,
  which are capabilities with a runner status; a column on the Level
  tables, which cannot hold a sequence; full text on the workbook sheet.
- **What an answer pins.** Every figure with its Part and table, the
  as-of date, every clause cited, what it did not do or refuses, and a
  quoted phrase only where one matters ("outside what this system does").
  **Not the prose**, which is rebuilt after Order 5. The owner corrected
  the brief on this at the start of the session: the line "the quiet
  answer is pinned exactly" predated the re-scope and contradicted it.
- **Two price dates.** Levels 1 to 3 at the 2026-09-02 closes of Parts 1
  to 7; Level 4 at the 2026-09-18 closes and filings of Parts 9 C, 11, 13,
  14, 15 and 17. A run prints a third date and the reference's own intro
  rule governs the comparison. This is what let the whole corpus be
  written with no new reference Part.
- **The count.** The eighteen, plus 41: fifteen extraction variations (one
  line each, answer by pointer), seven clarifications, nine refusals, and
  ten second or third turns across eight sequences. Above the twenty to
  thirty the brief named; the excess is the variations, which cost a line
  each.
- **The trace** is pinned by invariants once, in Part 3c's intro, and
  never byte for byte.

### Design principles

Unchanged in the code, since no code was touched. What the writing found:

- **Policy lives in config, not code.** The period vocabulary a
  clarification prints to the user, `1Y, 2Y, 3Y, 5Y, 10Y`, is a default
  in `config.DataConfig.period_days` and not a value in `config.toml`.
  Noted, not moved.
- **Raise, do not repair.** Corpus entries R-7 and S-6 pin that a buy
  question with no ticker read from it is a refusal naming the missing
  entry, not an error; today it arrives shaped as an error (KNOWN_GAPS).
- **The registry is the prompt.** Case 2.1's wording is pinned with its
  answer and without its routing, so the corpus records what survives.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
  **This session's two decisions, the structure and the cost split, were
  each brought as a recommendation with the rejected alternatives and
  waited on a yes before a line was written.**
- **The reference before the code**, each time, in its own commit. **And
  the corpus before the run**: nothing in Part 18 has been compared to an
  answer.
- **A paid loop says first what it will fetch and store, table by table.**
  None ran. The next one fetches: the price interval ran out on the 22nd
  at 14:24 and 14:28, the filings intervals at 22:17 on the 22nd and
  between 00:03 and 01:38 on the 23rd.
- **A count in a message is counted, and a count about the writing
  includes the writing**: eleven commits on `corpus`, this one included.
- **Check the citation, not the memory of it.** Two KNOWN_GAPS titles were
  cited from memory as paraphrases and caught by grep before the diff was
  shown; a third had already landed in e782bda and got its own commit.
- No emoji in anything newly written.

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
an audience instead of a requirement. **And no corpus entry fitted to an
answer after the run: Part 18 is a reference and follows the reference
rule.**

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

**One of the five ran.** pytest: **1926 passed, 6 xfailed**, about 6
seconds, at session start. The golden set, the runner and the CLI were
not run; no answer was read by hand; nothing here about answer text is
newer than the thirty-second session's reading.

**Golden set: twenty-one lines, one pinned failure**, `expected.txt` at
4f7ca89. Not run.

**The runner: 15/18, 0 failing, 3 blocked** by the thirty-third session's
run at 12:51. Not rerun. 2.1 blocked on routing, 4.1 and 4.3 on the
PHI-2.1 stop.

### Branches and tags

`baseline-v1` is the trunk at **b308b71**, sixteen ahead of
`origin/baseline-v1`, unpushed. **`corpus` is cut from it and carries
eleven commits**, this handoff the eleventh. `intents-parked` at addfbc7
holds the tree that still had the three intents. `rounding`, `halves`,
`judgement`, `gate`, `thesis`, `reader`, `research`, `score`, `publish`,
`range`, `keys`, `node`, `filer`, `bridge`, `consolidate`, `selection`,
`compliance`, `vocabulary`, `intents`, `arc` and `counts` are merged and
older. `wip/phase7-snapshot` holds rejected Compliance/IPS code.
`wip/rag-early` and tag `rag-early-parked` hold the RAG code.
`quant-inventory-parked` at 8d87455 holds the tree before the seventeenth
session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`2445c12e728c`**, checked; no migration this session. No reseed. **What
this session wrote: nothing**, and read at 16:07 UTC:

- `daily_prices` **7,009, unchanged**, last close still 2026-09-18.
- `asset_fetch_metadata`: the nine holdings stamped **2026-09-21 14:24:06
  to 14:24:09**, GOOGL **14:28:40**. **The one-day interval has run out**
  and Monday the 21st has closed, so the next session's first paid run
  stores a close.
- `api_call_logs` **2,480, unchanged**. `api_quotas`'s last row is still
  `daily_yfinance_2026-09-21` at 19; no row for the 22nd.
- `macro_data` **209, unchanged**. `document_readings` **5, unchanged**.
- `filers`: 19617 pulled 2026-09-16 01:33, 320193 at 00:03, 1652044 at
  01:38; `filed_fetch_metadata` 320193 at 2026-09-15 22:17 and 1652044 at
  2026-09-16 01:38. **The seven-day intervals ran out on the 22nd at 22:17
  and on the 23rd between 00:03 and 01:38**, so a run of any Level 4 case
  after that refetches filings for the filer it touches. **Corpus R-8 and
  R-9 name ADBE, a filer with no facts stored: a run of either is the first
  EDGAR pull for Adobe**, and the prediction for step 3 has to say so.

Unchanged: `assets` ten rows, GOOGL the tenth and not held; portfolio 3
the only portfolio, nine ledger rows, cost basis 284,500 plus 15,500 cash,
USD, policy `ips.toml`. There is no holdings table.

---

## 3. Environment

Not re-checked this session except where marked; kept from the thirty-third
session's handoff.

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files.
- **Anthropic has credits** as of the thirty-third session; the one-line
  check in §9 costs nothing. An empty balance fails with a 400
  `invalid_request_error` naming the credit balance, and from inside the
  system every question returns `intent: None`.
- `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU` for the router. `ANTHROPIC_SONNET`
  is `claude-sonnet-5`, used by the reader, the proposer and the view, and
  refuses a temperature.
- The `anthropic` SDK is 1.2.0; yfinance 1.7.0 with an exclusive `end`.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing. Nothing was fetched this session.
- **What this session cost: nothing.** No model call was made.
- **The period vocabulary** (checked): `config.DataConfig.period_days`,
  a default in code, keys `1Y, 2Y, 3Y, 5Y, 10Y`, passed to extraction by
  `smart_router.py`. Not in `config.toml`.
- **Extraction** (checked, `src/agents/extraction.py`, 338 lines): tickers
  by symbol only; a one-edit typo of a holding asks back with a record;
  spans in years and "twelve months" resolve, months, weeks, days, "since
  2025", year to date and a change verb with "today" ask back; a
  percentage next to "vol" is a cap, any other single one the
  hypothetical weight, outside 0 to 100 asks back; the policy lookup is a
  saying verb after "policy" or "anything in my policy about"; `resolve`
  handles only the unknown-ticker record, and the docstring says the span
  and percentage clarifications get theirs when a case asks. **Corpus S-3
  now asks.**
- `config.toml` carries five fetch intervals: prices 1 day, filings 7,
  earnings 7, profile 30, shares 30. Its `[macro]`, `[optimization]` and
  `[backtest]` sections stand although two have no consumer.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; scripts run from the root.
- The CLI's quit command is `:q`; `exit` goes to the router. Several
  questions go through one process with `printf '%s\n' 'q1' 'q2' ':q' |
  python src/agents/cli.py --portfolio 3`, each its own graph run, and the
  identical-answer check works across them. **That is how a corpus
  sequence is run: the CLI passes the previous turn's final state to the
  next**, which is what `run_agent_graph_sync`'s `previous` parameter
  takes and the runner's 3.5 uses.
- A single benchmark case runs with `--case`, one Haiku routing.
- zsh does not split an unquoted variable into words and has no `tac`; a
  `grep -c` that finds nothing exits 1; `%` in a `printf` format is `%%`;
  BSD `sed` has no `0,/re/`; BSD `cat` has no `-A`; `awk` has no `\s`;
  `--include='*.py'` must be quoted.
- **What is no longer in the tree**: as the thirty-third session's handoff
  listed it, unchanged; nothing was deleted this session.

---

## 4. What the thirty-fourth session did

`git log --oneline b308b71..HEAD`, **eleven commits** with this one, the
first ten touching three files, **807 insertions and 6 deletions**; this
handoff is a rewrite of one file on top. In the owner's order: the
structure decision, the cost split, then the corpus by kind, then the
record.

**Read first, and only what the brief named**: DIRECTION.md, the
previous handoff and its §0, three KNOWN_GAPS entries, benchmark.md Parts
2, 3 and 5. Then, for the writing, Parts 0 to 17 of expected_values.md by
their headings and figures, IPS.md, PHILOSOPHY.md, WATCHLIST.md,
`extraction.py`, the runner's `CASES` and four of its checks. **Every
claim in the brief that could be checked held**: eight intents, seven
agents, 172 triggers, the tag, the expected.txt date, the clocks.

**The structure decision (the owner's, brought and taken).** Part 3c in
benchmark.md, not a new Level and not a column; Part 18 in
expected_values.md, not the workbook and not each Part's own "Expected
answers" subsection; the runner's wordings as the spine. **With one
change from the owner**: the answer pins required content, not text.

**The cost split (measured before writing).** Every spine case and every
proposed addition lands on figures Parts 1 to 17 already hold, provided
Levels 1 to 3 stay at 09-02 and Level 4 at 09-18. Ten spine cases had a
written expected answer already, in Parts 5, 7 and 10; eight had none:
3.2, 3.3, 3.5, 4.1 on the real filer, 4.2, 4.3, 4.4 and 4.5. Left out as
new arithmetic: any
Level 1 to 3 figure restated at 09-18, any other volatility window,
Adobe's screen or range.

**The commits.**
- **c9a66e1** KNOWN_GAPS: the interlude entry's verbosity line corrected
  to the re-scope. The owner's correction of the owner's brief.
- **c1c7ef3** benchmark.md Part 3c: rules, trace invariants, the two
  price dates, the spine of eighteen verbatim, case 2.1 pinned first. One
  claim written and found wrong before the diff was shown: the runner has
  sent 2.1's wording since 4 September (129f0a0), not 7 September.
- **e782bda** Part 18: the frame and nineteen spine entries, 3.5 as two
  turns.
- **3edd9db** fifteen extraction variations and seven clarifications; two
  new answers, 2.1a (the AAPL rows of Part 7) and 3.1c (12%, the
  at-the-limit row the owner allowed).
- **b2c9b29** nine refusals, R-1 to R-9.
- **240131e** entry 3.2's citation, by title.
- **3921bcc** eight sequences, seventeen turns, nine new entries.
- **5b6c46e** six lines grown into "Questions the system cannot express",
  by kind.
- **68d562e** the 2.1 entry's dated note: pinned, without the routing.
- **d11455d** step 2 marked written on the interlude entry's arc.

**What was found and not fixed, by the rule of the interlude.** The
spine's wordings live in two places now, Part 3c.1 and `CASES`, with no
check that they agree. The period vocabulary is in code, not config. The
sequences S-3, S-6 and S-7 cannot be done today, S-1, S-4 and S-5 pass
or fail on the model's guess, and Part 3c says so. Only 1.1 to 1.4 had
full answer text anywhere before this session, on a binary sheet.

**Not done, on purpose.** Running anything. Decision 75's implementation
and the rest of step 4. The cleanup. Decisions 17, 75 and 76, the
rebalancing dependency-table bug, Order 5, and the owner's four documents,
all out of scope by the owner's word.

---

## 5. Decisions taken, and decisions pending

**Taken this session, the owner's, both small and both recorded in the
documents they shape:** the corpus's structure (benchmark.md Part 3c,
expected_values.md Part 18, the runner's wordings as the spine, required
content and not text) and the cost split (two price dates, no new
reference Part, the 12% row as the one exception).

**Pending — decide before writing code. Eleven by count, unchanged:**
10, 12, 13, 16, 17, 22, 45, 48, 52, 54 and 76. The cap is 25. Nothing was
opened and nothing closed.

10. A window return as a measure with a reference. **Corpus C-4 names it.**
12. The hypothetical mode's instrument type. **Corpus 3.1 and 3.1c stop
    where it starts.**
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the
    IPS. **Corpus 3.2 and R-6 pin what the refusal must name.**
16. Company names, German phrasings, the softer 3.5. **Written out as
    corpus variations V-1.2a, V-2.1b, V-3.1b, V-3.4b, V-4.1a, V-4.2a,
    V-4.6a, V-1.1a and V-3.4a; still logged, not taken.**
17. The selection axis. **Corpus 2.1a and the new "Compare AAPL and
    MSFT" line sit on it; not pinned either way.**
22. Volatility over as-traded closes or a total-return series.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, 11 and 36.
48. Part 13 E's item 7, second half only.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields.
76. Whether money and ratios are computed in decimal.

- **The interlude between Orders 4 and 5** (owner's): steps 1 and 2 done.
  **Step 3 is the next session**: run the corpus once, end to end, through
  the CLI, and log what it finds. Step 4 is a rule, only pipeline
  arithmetic; step 5 the cleanup; then Order 5.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: **11/12**, 2.1 BLOCKED on routing. Level 4: 4.2, 4.4, 4.5
and 4.6 PASS; 4.1 and 4.3 BLOCKED at the PHI-2.1 stop. **15/18, by the run
at 12:51 on 22 September; not rerun.**

**Against the corpus: nothing yet.** Part 3c has no status column and
Part 18 has been compared to no answer. What the previous full test found,
eight defects in cases the runner passes, is now pinned as required
content where it belongs: 1.4's per-position figures, 2.2 against 2.3, 4.1
against 4.2, 3.2's subject, 3.3's as-of, 1.3's basis.

What the runner cannot see, unchanged: whether the view is a defensible
read of the claims it cites; whether the gate's arithmetic is right, which
is pytest's against Part 17; whether the range's ends are right; any due
prediction until 2027; whether a quote supports its claim; and whether any
answer reads well.

---

## 7. Next steps, in order

**1. Step 3: run the corpus once, and it is a paid session.** Before the
first prompt: read the clocks off the store (§9), and say table by table
what the run will fetch. Prices will be fetched on the first question that
needs them, one close per holding for the 21st and whatever has closed
since; filings for any Level 4 filer touched after the seven-day interval;
**Adobe's facts for the first time if R-8 or R-9 is run**, and that one
deserves its own yes. Run the eighteen and the 41 through the CLI, several
questions per process, the sequences as consecutive turns in one process,
and **never pipe the output through a filter**. Read every answer against
its Part 18 entry, by hand, recomputing nothing and matching content. Log
every miss with a trigger; fix nothing. A corpus prompt is not in the
golden set and not in the runner, so **no loop sees a corpus miss but the
reading**.

**2. Then step 4's narrow fix list**: decision 75's implementation, the
check written first against Part 7; decision 76 if the owner wants it
there. Answer text changes, so the runner runs against it.

**3. Step 5, the cleanup**, then Order 5 may open.

### Later, with reasons

- **The push.** The trunk is sixteen ahead, and `corpus` eleven on top.
- **DIRECTION.md's interlude paragraph** says "what is pinned exactly";
  the entry it points at now says required content. The owner's to
  revise, dated.
- **Part 3c.1 and `CASES` can drift.** A pytest test that reads both and
  asserts the eighteen wordings agree is cheap and adds no capability;
  proposed, not built, because the session was writing.
- **The period vocabulary** in `config.DataConfig.period_days` is printed
  to the user by a clarification and lives in code.
- **The router's swallowed exception** — a failed model call should raise
  with the provider's own message.
- **The emoji**: four answer-text headers, one commit, the runner run
  against it. The console glyphs are a separate session.
- **`check_4_3`'s weight_source assertion cannot fail** while the
  candidate's id is printed (KNOWN_GAPS).
- **IPS-2.1 would pass an instrument the policy forbids**, being a
  statement clause (Part 17 G).
- **IPS-5.3's second limb** is not computed (decision 71).
- **Nothing records a model call's tokens.**
- **1 February 2027**: W-2.1 and W-2.2 fall due. **1 March 2027**: W-1.1
  and W-1.2.
- Three stale statements, the owner's to fix on the owner's word:
  `watchlist.toml`'s header and `test_watchlist.py`'s docstring, "read by
  nothing yet"; Part 11 D38's "D46".

---

## 8. Rules learned the hard way

**A brief can carry a line the re-scope already retired.** "The quiet
answer is pinned exactly" was written before the decision that prose does
not survive the refactor, approved, and carried into the next session's
brief. The owner caught it on the first proposal; the entry is corrected
and the correction says where the line came from.

**Cite an entry by its title, and grep the title before showing the
diff.** Three citations were written as paraphrases of what an entry
says. Two were caught before the diff went out; one had landed and cost a
commit.

**Say which sequences work today, and by what rule.** The first draft of
Part 3c.5 said three of eight could not be done, which implied five could.
Two rest on a rule; three pass or fail on the model's guess, which the
golden set already has a name for.

**A count about the writing includes the writing.** Eleven commits, with
this one; the previous session got the same count wrong three times.

**Measure the cost before the first prompt.** The split, written before a
line of corpus, is what let 59 prompts be written with no new reference
Part and no run: every figure was already somewhere.

**A pointer is cheaper than a copy and cannot drift.** Fifteen variations
cost fifteen lines because their answers are the spine's; the one place
the corpus copies rather than points, the spine's wordings, is the one
place it can now disagree with the runner.

Still true, from earlier sessions: **a prompt change can move a question
it does not mention**; **the loop you ran the change against may not be
the loop that sees it**; **do not filter the output of a paid run**;
**chase the evidence, not the story you already have**; **grep the
package, not three files**; **measure a deletion before taking it, and
say the number twice**; **a decision's own arithmetic goes stale too**;
**the record names the requirement, not the audience**; **delete the
surface, not the file**; **a scoreboard that scores well-formedness will
score a wrong answer a pass**; **recompute the answer's arithmetic rather
than reading it**; **an exact half is where a rounding rule announces
that it does not exist**; **an exception swallowed into a `None` crashes
somewhere that cannot explain it**; **when everything fails at once,
change one thing and rerun the thing that worked**; **cut the branch
before the first commit**; **a golden line can be identical to another
in four of its five fields**; **grep the writer the reader reads**; **a
test parametrized over the constant it is checking cannot catch a wrong
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
is written**; **a brief's claim about an interval is checked against the
clock**; **a count in a message is counted**; **sight a new case before
writing its golden line**; **the registry's descriptions are the
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

python src/agents/cli.py --portfolio 3        # :q to quit
# several questions through one process; a corpus sequence is consecutive turns here.
printf '%s\n' 'How has my JPM position performed since I bought it?' 'And MSFT?' 'And JNJ?' ':q' \
  | python src/agents/cli.py --portfolio 3

# is the API answering at all, before spending a loop on finding out:
python -c "import anthropic;from dotenv import load_dotenv;load_dotenv();\
print(anthropic.Anthropic().messages.create(model='claude-haiku-4-5-20251001',\
max_tokens=8,messages=[{'role':'user','content':'ok'}]).content[0].text)"

git status --short
git log --oneline b308b71..HEAD
git rev-list --count b308b71..HEAD

# the corpus: prompts, and answers
grep -n '^### 3c\|^| [VCRS]-\|^\*\*S-' docs/benchmark.md
grep -n '^## Part 18\|^### [0-9]\|^- \*\*[CRS]-' tests/golden/expected_values.md | sed -n '/Part 18/,$p'

# the spine's wordings in the two places they now live:
grep -n '^    ("' tests/benchmark/run_cases.py
sed -n '/^### 3c.1/,/^### 3c.2/p' docs/benchmark.md | grep '^| [0-9]'

# what the database says it is at (expected 2445c12e728c):
sqlite3 data/portfolio.db "select version_num from alembic_version;"

# the price and filings clocks, which decide what a paid loop fetches:
sqlite3 data/portfolio.db "select a.ticker, m.last_price_fetch_time from asset_fetch_metadata m join assets a on a.id=m.asset_id order by a.ticker;"
sqlite3 data/portfolio.db "select cik, pulled_at from filers; select * from filed_fetch_metadata;"

# what a paid loop wrote, against the prediction (the column is calls_consumed):
sqlite3 data/portfolio.db "select bucket_key, calls_consumed from api_quotas order by id desc limit 1;"
sqlite3 data/portfolio.db "select count(*), max(date) from daily_prices;"

# the intent vocabulary and the roster:
PYTHONPATH=src python -c "from agents.schemas import INTENTS, AGENTS; print(len(INTENTS), sorted(INTENTS)); print(len(AGENTS), sorted(AGENTS))"

# the workbook: never write while Excel holds it
lsof tests/golden/expected_values.xlsx

# merge and push, by the owner only:
git switch baseline-v1 && git merge --ff-only corpus
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~6s, no model calls | Do the components still work; does every reference Part reproduce; does each node fetch in order and publish its block; does the gate refuse what it must; does the outcome compose every row of the truth table. **Sees nothing of the corpus.** |
| CLI | ~2s and one Haiku call for most questions; a thesis question about $0.014 and a position question about $0.025 on Sonnet; **fetches prices past their interval, which ran out on 22 September at 14:24** | What it is actually doing: the plan, the parameters, the reasoning line, the answer text. **The only loop that shows an answer, and therefore the only loop that can be read against Part 18** |
| Golden set | ~50s, about $0.039 per run; writes to no table since decision 51, prices aside | Did routing change anywhere (twenty-one lines, one pinned failure). Blind to `measure`, `group_by`, `tickers`, answer text, and any wording it does not carry |
| Benchmark runner | ~50s, about $0.039; `--case X` is one routing at about $0.001 | How many cases pass, n/18. Its checks read each answer's text and show it to nobody. **Carries none of the 41 corpus additions** |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once. **Never pipe a paid run through a filter.** **The corpus is
read by hand against Part 18, and a corpus miss is logged with a trigger,
not fixed, until step 4's rule says it is arithmetic.**
