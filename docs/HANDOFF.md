# AGENTIC_FINANCE — Session Handoff

**Session date:** 22 September 2026 (thirty-fifth session), begun about 16:40 UTC. Regenerated at its end. The thirty-third and thirty-fourth sessions ran earlier the same day.
**Branch:** `corpus-run`, cut from `baseline-v1` at **630dc42** before the first commit, in a worktree under `.claude/worktrees/` because this session's harness rejects edits outside one; **eight commits with this one**. The owner merges and pushes; `origin`'s push URL is `no_push`. **The trunk is twenty-nine ahead of `origin/baseline-v1`**, and `corpus-run` adds eight on top of it.

**State:** pytest **1929 passed, 6 xfailed**, up three from 1926 by the one test this session wrote; run at session start in the checkout and in the worktree, and again at the end. **One paid loop ran: the corpus, once, through the CLI**, 65 turns in fifteen processes, 17:11 to 17:13 UTC, R-8 and R-9 not sent. **The golden set and the runner were not run; the runner is 15/18 by the thirty-third session's run.** Step 3 of the interlude is **done**: the corpus's baseline is captured in benchmark.md Part 3c.6 and `tests/golden/run_corpus_2026-09-22.txt`, **30 of 65 turns matched**, every miss logged by class with a trigger, nothing fixed. The pending list stands at eleven, unchanged.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** Sections whose claims were checked again this session and
still hold are kept word for word; the rest is rewritten. This session
checked the counts, the clocks, the store before and after the run, and
the reading cache; it did not re-check §3's library versions or the
migration count beyond the head.

**This was a running and reading session.** One test was written before
the run and nothing else that runs was touched. The run's answers were
read by hand against expected_values.md Part 18, content against content,
and Part 18 was not changed by a character. What the run found is in the
record, by class, and step 4's list has one arithmetic item on it.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Dated, not regenerated. Wins over this file on direction; this file wins on state. Orders 1 to 4 are built. The interlude between Orders 4 and 5 is its unnumbered paragraph under Order 4, last revised 22 September. Unchanged this session. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. **176 lines start `**Trigger:**`**, up from 172: four entries opened this session, all at the end of the file. **Start with "The interlude between Order 4 and Order 5, and how the corpus is built"**, whose step 3 now says run and whose step 4 carries the list. Then the four new entries, by title: A follow-up that depends on the previous turn is asked back by the model; The unknown-ticker correction fails on the comma after "no"; Three Level 4 answers leave out content Part 18 pins; A bare opinion on a company is routed to the philosophy screen. Thirteen older entries carry a dated line headed "22 September 2026 (thirty-fifth session), the corpus run". |
| `docs/benchmark.md` | **The definition of done, the corpus, and now its first run.** Part 3c unchanged in its five subsections but for one dated correction in 3c.3 (C-2's clarification is the model's). **New 3c.6, Runs**: one dated block per run, one line per entry and turn, `matched` or `missed` and what was missing. The run of 22 September is its first block. **Read Part 2, Part 3c and 3c.6 before Part 3's tables.** |
| `tests/golden/expected_values.md` | Hand-computed reference, Parts 1 to 18. **Unchanged this session, and compared for the first time**: every entry of Part 18 was read against an answer. Never update it to match code output. |
| `tests/golden/run_corpus_2026-09-22.txt` | **The transcript**, 5,887 lines, the CLI's stdout and stderr whole for the 65 turns, each process headed by the printf line that produced it. Captured, not written: it carries the console glyphs and the German debug strings the source prints, request ids and timings. Evidence for the reading, not a reference. |
| `tests/test_corpus_spine.py` | **New.** Holds that Part 3c.1's eighteen wordings are the runner's `CASES`, character for character, 3.5's two turns included. Written before the run. |
| `tests/golden/expected.txt` | Twenty-one lines, one pinned failure. Unchanged; not run this session. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Eighteen cases, unchanged, not run. |
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
not the plan. The corpus is written on that rule, and now run on it.

### What the run showed, in one paragraph

The answers the owner wants are reachable wherever a rule reaches them:
every fixed figure printed matched Part 18 to the cent, every market
figure read correctly against the 2026-09-21 close the run fetched, the
seven clarifications and the Level 4 stop, exclusion and ledger came back
as pinned, and the one sequence that rests on nothing carrying over,
S-8, held. Where the model decides, it asks back: every follow-up that
depends on the previous turn became a clarification, which is the honest
failure and the baseline Order 5 is judged against. The misses proper are
routing (2.1, R-2, R-7), selection (1.4, the 2.2/2.3 and 4.1/4.2 pairs,
three Level 4 omissions), wording (the out-of-scope list, the lookup
sentence, 1.3's basis line), the pending decisions 12 and 16, and one
extraction defect (S-2's comma). **One arithmetic finding**: 2.2 prints
two exact half-cents two ways in one answer, which is decision 75, already
on step 4's list.

### The record's shape, decided this session

The owner's, brought as a recommendation with the rejected alternatives
and taken on a yes before the first prompt was sent. **Where a run is
read:** benchmark.md Part 3c.6, one dated block per run, one line per
entry and turn, three kinds of miss kept distinct (on the guess, cannot
be done, reading gap); not a status column, not in Part 18, not only in
KNOWN_GAPS, not a document of its own. **The transcript:** kept whole
beside `expected.txt`, dated, one file per run, as the three `run_*.txt`
files of 1 September already are. **A miss is logged by class**, an
existing entry grown with a dated line before a new one is opened, each
new entry with a trigger naming when its class ends: step 4's commit for
arithmetic, the commit that opens Order 5 for routing and memory, the
presentation rebuild for layout. **The step 4 list** lives under step 4
in the interlude entry's arc and is restated in §7.

### Design principles

Unchanged in the code. What the run found against them:

- **Raise, do not repair.** Held everywhere it was tested: no figure was
  guessed, no span rounded to the nearest, no ticker inferred from a
  company name; the model's clarifications guessed nothing. R-7 and the
  three company-name Level 4 variations arrive as errors rather than
  refusals, the shape already logged.
- **A formatter states what the data says and never what the system
  is.** The out-of-scope answer still lists capabilities on six corpus
  prompts; logged, pending decision 13.
- **Policy lives in config.** The period vocabulary printed by C-3 to C-6
  is still `config.DataConfig.period_days`, a default in code.
- **Every number traces to a tool output.** Every figure in 65 answers
  did, the model's proposal and view included.

### How I work on this

- Every change starts as a written decision in plain words: what it is,
  what changes on a yes, the rejected alternatives, which loop sees it.
  **This session's one decision, the record's shape in three parts, was
  brought and taken before a prompt was sent.**
- **The reference before the code**, each time. **The corpus before the
  run, and the run before the reading**: Part 18 was not touched, and
  where an answer and an entry disagreed the entry's source Part was the
  arbiter, not the answer.
- **A paid loop says first what it will fetch and store, table by table,
  and afterwards what moved.** Predicted and held to the row: prices
  7,009 to 7,019, the quota bucket at 10, the call log 2,480 to 2,490,
  every EDGAR table and the readings unchanged. Cost estimated before at
  under 0.20 dollars and stated after at about 0.15 by the handoff's
  per-call figures; nothing records tokens.
- **Its own yes for a first fetch.** R-8 and R-9 name Adobe, a filer with
  no facts stored; they were left out of the run and are still to be run
  on their own yes.
- **A count in a message is counted.** The brief's 67 turns were 65 once
  the two Adobe prompts were left out; the reading's 30 and 35 were
  counted by grep on the table before the commit message named them.
- **Grep the heading before citing it, and grep the class before opening
  an entry.** "The lookup sentence quotes the whole question" already
  existed and was found in the diff of the confirmation commit, so the
  echoed topic got a dated line and not a duplicate entry.
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
arithmetic.**

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

**Two of the five ran.** pytest: **1929 passed, 6 xfailed**, about 7
seconds, at session start (1926) and at the end (1929, the new test's
three). The CLI: the corpus, once, 65 turns. The golden set and the
runner were not run.

**Golden set: twenty-one lines, one pinned failure**, `expected.txt` at
4f7ca89. Not run.

**The runner: 15/18, 0 failing, 3 blocked** by the thirty-third session's
run at 12:51. Not rerun. 2.1 blocked on routing, 4.1 and 4.3 on the
PHI-2.1 stop.

**The corpus: 30 of 65 turns matched**, by the run at 17:11 and the
reading in benchmark.md Part 3c.6. Of the 35 misses, 4 are on the model's
guess (S-1's two follow-ups, S-4's, S-5's), 3 cannot be done (S-3, S-6,
S-7), 7 are the reading gaps under decision 16, and 21 are misses proper.
R-8 and R-9 not run.

### Branches and tags

`baseline-v1` is the trunk at **630dc42**, twenty-nine ahead of
`origin/baseline-v1`, unpushed. **`corpus-run` is cut from it in a
worktree at `.claude/worktrees/corpus-run` and carries eight commits**,
this handoff the eighth. The worktree holds a symlink `data/portfolio.db`
to the checkout's database, gitignored, so pytest and the CLI there run
against the real store; `.env` is found by walking up from the worktree.
`intents-parked` at addfbc7 holds the tree that still had the three
intents. `rounding`, `halves`, `judgement`, `gate`, `thesis`, `reader`,
`research`, `score`, `publish`, `range`, `keys`, `node`, `filer`,
`bridge`, `consolidate`, `selection`, `compliance`, `vocabulary`,
`intents`, `arc`, `counts`, `corpus` and `direction` are merged and
older. `wip/phase7-snapshot` holds rejected Compliance/IPS code.
`wip/rag-early` and tag `rag-early-parked` hold the RAG code.
`quant-inventory-parked` at 8d87455 holds the tree before the seventeenth
session's quant deletions.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head
**`2445c12e728c`**, checked; no migration this session. No reseed. **What
the run wrote, read at 17:14 UTC and again at 17:39:**

- `daily_prices` **7,009 to 7,019**, last close **2026-09-21**: one row
  per holding for the 21st and one for GOOGL, the 18th's rows upserted
  unchanged. No row for the 22nd, yfinance's end being exclusive.
- `asset_fetch_metadata`: the nine holdings restamped **2026-09-22
  17:11:38 to 17:11:39**, GOOGL **17:12:02**. The one-day interval runs
  out at those minutes on the 23rd.
- `api_call_logs` **2,480 to 2,490**. `api_quotas` has a new row
  `daily_yfinance_2026-09-22` at **10**: nine holdings and GOOGL. EDGAR
  is not quota-counted.
- `filers` 3, `filed_facts` 28,787, `filed_fetch_metadata` 2,
  `ticker_ciks` 10,422, `filed_documents` 1, `document_readings` 5,
  `assets` 10, `transactions` 9, `macro_data` 209: **all unchanged.** The
  run finished before any filings interval ran out, and the three stored
  reading prompt versions equal the current ones, so 4.3 and 4.4 read
  from the cache.
- **The filings clocks have now run out or run out tonight**: Apple's
  facts at 22:17 UTC on the 22nd, JPM's filer row and the SEC ticker file
  at 01:33 on the 23rd, Alphabet's filer row and facts at 01:38. The
  interval test is whole days, `(now - pulled_at).days < 7`. **The next
  paid run of any Level 4 question refetches the ticker file, the filer
  it touches and, for Alphabet, its facts**, which should store zero new
  rows or raise on a changed figure. **R-8 and R-9 still name ADBE, a
  filer with no facts stored**: the ticker file already maps it to
  796343; a run would fetch its submissions document, its company facts
  unless EDGAR's SIC for it is one of PHI-3.2's seven codes, create an
  `assets` row from the watchlist's currency with about five closes and
  one yfinance call, and R-9 may fetch its latest 10-K and read three
  sections on Sonnet before refusing on W-2's missing weight. Their own
  yes.

Unchanged: `assets` ten rows, GOOGL the tenth and not held; portfolio 3
the only portfolio, nine ledger rows, cost basis 284,500 plus 15,500 cash,
USD, policy `ips.toml`. There is no holdings table.

---

## 3. Environment

Not re-checked this session except where marked; kept from the
thirty-fourth session's handoff.

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds keys. Never print it. A permission rule denies sessions the
  shell and the editor on `.env*` files. **`load_dotenv()` in `config.py`
  finds it by walking up from the calling file, so a worktree nested
  under the checkout reads the checkout's `.env`** (checked: the key and
  the EDGAR contact resolve from the worktree without a copy).
- **Anthropic has credits**; the run cost about 0.15 dollars. An empty
  balance fails with a 400 `invalid_request_error` naming the credit
  balance, and from inside the system every question returns `intent:
  None`.
- `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU` for the router. `ANTHROPIC_SONNET`
  is `claude-sonnet-5`, used by the reader, the proposer and the view, and
  refuses a temperature. **The reader's cache is keyed by accession,
  section, model and prompt version** (`reader.prompt_version`); the
  five stored readings match the current versions.
- The `anthropic` SDK is 1.2.0; yfinance 1.7.0 with an exclusive `end`.
- **EDGAR.** `config.edgar_user_agent()` reads `EDGAR_USER_AGENT` and raises
  when it is missing. Nothing was fetched from EDGAR this session.
- **The period vocabulary** (checked): `config.DataConfig.period_days`,
  a default in code, keys `1Y, 2Y, 3Y, 5Y, 10Y`, passed to extraction by
  `smart_router.py`. Not in `config.toml`.
- **Extraction** (checked, `src/agents/extraction.py`): tickers by symbol
  only; a one-edit typo of a holding asks back with a record; spans in
  years and "twelve months" resolve, months, weeks, days, "since 2025",
  year to date and a change verb with "today" ask back; a percentage next
  to "vol" is a cap, any other single one the hypothetical weight,
  outside 0 to 100 asks back; the policy lookup's topic reaching the node
  is the whole message; `resolve` handles only the unknown-ticker record,
  a reply outside its vocabulary is routed as typed, and **a comma after
  "no" defeats it** (KNOWN_GAPS, the new entry). A message that no rule
  reads, ZZZZFAKE, goes to the model, which asked back.
- `config.toml` carries five fetch intervals: prices 1 day, filings 7,
  earnings 7, profile 30, shares 30. Its `[macro]`, `[optimization]` and
  `[backtest]` sections stand although two have no consumer.
- `portfolio_tool/__init__.py` opens a DB connection at import; `config` reads
  `DATABASE_URL` at import; scripts run from the root. The URL in `.env`
  is relative, so from the worktree it resolves through the symlink.
- The CLI's quit command is `:q`; `exit` goes to the router. Several
  questions go through one process with `printf '%s\n' 'q1' 'q2' ':q' |
  python src/agents/cli.py --portfolio 3`, each its own graph run, and the
  identical-answer check works across them: **it flagged 2.3 against 2.2,
  4.2 against 4.1, and the three variations that fell to the same error.**
  The CLI passes the previous turn's final state to the next, which is
  what a corpus sequence needs and what the run used. `input()` at end of
  input returns, so a piped process ends cleanly after `:q`.
- A single benchmark case runs with `--case`, one Haiku routing.
- zsh does not split an unquoted variable into words and has no `tac`; a
  `grep -c` that finds nothing exits 1; `%` in a `printf` format is `%%`;
  BSD `sed` has no `0,/re/`; BSD `cat` has no `-A`; `awk` has no `\s`;
  `--include='*.py'` must be quoted. **This session's harness refused
  compound shell commands with `source`, `awk -v` or a computed path
  inside the worktree; a script file under the job's temp directory,
  invoked by path, ran.**
- **What is no longer in the tree**: as the thirty-third session's handoff
  listed it, unchanged; nothing was deleted this session.

---

## 4. What the thirty-fifth session did

`git log --oneline 630dc42..HEAD`, **eight commits** with this one, the
first seven touching four files, **6,266 insertions and 3 deletions**, of
which the transcript is 5,887 lines; this handoff is a rewrite of one
file on top. In the owner's order: the shape, the drift test, the run,
the reading, the record.

**Read first, and only what the brief named**: DIRECTION.md, the previous
handoff and its §0, the interlude entry, benchmark.md Part 3c whole,
expected_values.md Part 18 whole and the head of the document. Then, for
the prediction, the runner's `CASES`, the CLI, the data manager's
interval, the filings module, the screening node's fetch order, the
reader's cache and the store. **The brief's claims, checked**: pytest's
number held; the price clocks held; **the filings clocks were right as
times but lay in the future**, not the past, since the interval test is
whole days, so the run refetched nothing from EDGAR; ADBE's absence from
`filers` and `filed_facts` held, and the ticker file already maps it.

**The shape decision (the owner's, brought and taken):** §1 above.

**The commits.**
- **e53475b** `tests/test_corpus_spine.py`: Part 3c.1's eighteen wordings
  are the runner's `CASES`, 3.5's two turns included. Checked to fail on
  a drifted copy with two wordings changed. pytest 1926 to 1929.
- **a98da9b** the transcript, `tests/golden/run_corpus_2026-09-22.txt`,
  captured whole.
- **13bc6ba** benchmark.md Part 3c.6: the run's block, 65 lines, 30
  matched and 35 missed, counted by grep before the message named them.
- **3132875** benchmark.md Part 3c.3: C-2's clarification is the model's,
  not extraction's; a statement about the code corrected and dated.
- **9b45532** KNOWN_GAPS: dated confirmation lines on thirteen existing
  entries, every heading found by grep before the line was written.
- **ebe4bcc** KNOWN_GAPS: four entries opened, one per class with none.
- **cb12f66** KNOWN_GAPS: the interlude entry's step 3 marked run, the
  step 4 list under step 4.

**The run, as it was driven.** Fifteen CLI processes from the worktree
against the real store: the eleven single-turn spine cases; 3.5's two
turns; 4.1 to 4.6; the fifteen variations; the seven clarifications; R-1
to R-7; each sequence in its own process. A shell script under the job's
temporary directory, not in the repository, wrote the header lines and
appended each process's stdout and stderr; the printf line for every
process is in the transcript's headers, so the run is reproducible from
the file alone.

**What was found and not fixed, by the rule of the interlude.** Twenty-one
misses proper, four on the guess, three that cannot be done, seven reading
gaps; §1's paragraph and Part 3c.6 list them. One arithmetic finding,
decision 75's. Two facts about the code not previously recorded: the
comma in S-2's reply, and C-2's clarification being the model's.

**Not done, on purpose.** Fixing anything. R-8 and R-9. Decision 75's
implementation and the rest of step 4. The cleanup. Decisions 17, 75 and
76 as work, the rebalancing dependency-table bug, Order 5, the CLI, the
README, the demo recordings, and the owner's four documents, all out of
scope by the owner's word. The span clarification's record for S-3,
which the corpus names and step 4 does not cover.

---

## 5. Decisions taken, and decisions pending

**Taken this session, the owner's, small and recorded where it applies:**
the record's shape (benchmark.md Part 3c.6; a dated transcript beside
`expected.txt`; misses logged by class, existing entries grown first).

**Pending — decide before writing code. Eleven by count, unchanged:**
10, 12, 13, 16, 17, 22, 45, 48, 52, 54 and 76. The cap is 25. Nothing was
opened and nothing closed. What the run added to each:

10. A window return as a measure with a reference. **C-4 and C-5 asked
    back as pinned; confirmed.**
12. The hypothetical mode's instrument type. **3.1, V-3.1a and V-3.1c
    missed on it: IPS-4.2 applied to every instrument type, the fund
    refused at 12%.**
13. A target-weights clause and `OUT_OF_SCOPE_RESPONSE` moving into the
    IPS. **3.2 and five refusals printed the capability list; R-2's
    refusal would be this answer too.**
16. Company names, German phrasings, the softer 3.5. **Seven reading gaps
    missed as written; V-1.1a, the German allocation question, answered.**
17. The selection axis. **V-2.1a answered AAPL's two clauses alone and
    matched; not pinned either way.**
22. Volatility over as-traded closes or a total-return series.
45. The tool-boundary pass, tagged Order 5. Absorbs 9, 11 and 36.
48. Part 13 E's item 7, second half only.
52. The Yahoo-fed tables: delete or keep.
54. BaseAgent's tool loop and the three `AgentConfig` fields.
76. Whether money and ratios are computed in decimal. **On step 4's list
    on the owner's word.**

- **The interlude between Orders 4 and 5** (owner's): steps 1, 2 and 3
  done. **Step 4 is next**: decision 75's implementation, its check
  written first against Part 7; decision 76 if the owner puts it there;
  nothing else, by the list under step 4 in the entry. Step 5 the
  cleanup; then Order 5.

---

## 6. Where we stand against the benchmark

Levels 1 to 3: **11/12**, 2.1 BLOCKED on routing. Level 4: 4.2, 4.4, 4.5
and 4.6 PASS; 4.1 and 4.3 BLOCKED at the PHI-2.1 stop. **15/18, by the run
at 12:51 on 22 September; not rerun.**

**Against the corpus: 30 of 65, by the run at 17:11 on 22 September**,
benchmark.md Part 3c.6. The spine's 19 turns: 10 matched (1.1, 1.2, 1.3,
3.3, 3.4, both turns of 3.5, 4.1, 4.5, 4.6), 9 missed. The variations: 6
of 15, seven reading gaps and the two instrument-type rows. The
clarifications: 7 of 7. The refusals: 0 of 7 run, on the capability list,
the screen and the error shape, with every refusal itself right. The
sequences: 7 of 17 turns, S-8 whole.

What the runner cannot see and the reading now has: whether an answer
carries the figures its entry pins, whether it cites the clauses, whether
it says what it did not do. What neither sees, unchanged: whether the view
is a defensible read of the claims it cites; whether the range's ends are
right; any due prediction until 2027; whether a quote supports its claim;
and whether any answer reads well.

---

## 7. Next steps, in order

**1. Step 4, the narrow fix list, and it is short.** Decision 75, the
exact half cent: the check first, against Part 7 at its own as-of, then
the implementation; the runner runs against it since answer text
changes, and 2.2's two halves at the 2026-09-21 closes, 19,552.475 and
15,147.375, are the falsifier the corpus adds. Decision 76 only on the
owner's word. Nothing else on the list is arithmetic.

**2. R-8 and R-9, on their own yes**, the first EDGAR pull for Adobe,
with the prediction in §2 said again against the clocks of the day.
Read against Part 18's R-8 and R-9 and appended to Part 3c.6's block as
two lines dated the day they run.

**3. Step 5, the cleanup**, then Order 5 may open. When it does, the
record's four new entries and the interlude entry close on its commit,
and the run after it is Part 3c.6's second block.

### Later, with reasons

- **The push.** The trunk is twenty-nine ahead, and `corpus-run` adds
  eight.
- **S-2's comma**, one line in `extraction.resolve`, the test first on
  the corpus wording; extraction survives Order 5, so it is worth a
  commit before it, and it is not step 4's.
- **The period vocabulary** in `config.DataConfig.period_days` is printed
  to the user by four clarifications and lives in code.
- **The router's swallowed exception** — a failed model call should raise
  with the provider's own message.
- **The emoji**: the answer-text headers, one commit, the runner run
  against it. The console glyphs are a separate session; the transcript
  shows how many there are.
- **`check_4_3`'s weight_source assertion cannot fail** while the
  candidate's id is printed (KNOWN_GAPS).
- **IPS-2.1 would pass an instrument the policy forbids**, being a
  statement clause (Part 17 G).
- **IPS-5.3's second limb** is not computed (decision 71).
- **Nothing records a model call's tokens**; the run's cost is an
  estimate from per-call figures.
- **1 February 2027**: W-2.1 and W-2.2 fall due. **1 March 2027**: W-1.1
  and W-1.2.
- Three stale statements, the owner's to fix on the owner's word:
  `watchlist.toml`'s header and `test_watchlist.py`'s docstring, "read by
  nothing yet"; Part 11 D38's "D46".

---

## 8. Rules learned the hard way

**A brief's clock is checked against the interval's arithmetic, not its
date.** The filings intervals "ran out at 22:17 on the 22nd" read as past
and were future: the test is whole days, so 22:17 tonight, and the run
fetched nothing from EDGAR. Had the prediction taken the brief's tense,
the after-run store would have looked wrong for the right reason.

**Grep the class before opening an entry.** The lookup sentence's entry
was found in the diff of another commit, one grep short of a duplicate.
Thirteen entries grew and four opened; a fourteenth grew instead of a
fifth opening.

**A rule that exists can still fail on the corpus wording.** S-2 rests on
a rule, Part 3c says so, and a comma defeated it; the corpus is the test
the rule never had. Check the rule directly after the run, in the shell,
before writing what failed.

**Count the turns before the run, and count them again after.** 67 in the
brief, 65 sent: the two Adobe prompts. The reading's 30 and 35 were
counted by grep on the table before the message named them.

**The capture is never filtered; the reading may be.** The transcript is
kept whole, and the run was read through a display script that dropped
the provider's repeated lines, which is not the same thing. What was
dropped is in the file.

**A worktree nested under the checkout finds the checkout's `.env` and
can share its database through a symlink.** pytest copies the file it
finds at `data/portfolio.db`, so the symlink is safe there; the CLI writes
through it to the real store, which is what a paid run must do.

Still true, from earlier sessions: **a brief can carry a line the re-scope
already retired**; **cite an entry by its title, and grep the title
before showing the diff**; **say which sequences work today, and by what
rule**; **a count about the writing includes the writing**; **measure the
cost before the first prompt**; **a pointer is cheaper than a copy and
cannot drift**; **a prompt change can move a question it does not
mention**; **the loop you ran the change against may not be the loop that
sees it**; **do not filter the output of a paid run**; **chase the
evidence, not the story you already have**; **grep the package, not three
files**; **measure a deletion before taking it, and say the number
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
# the whole corpus: the printf line of every process is in the transcript's headers.
grep '^# printf' tests/golden/run_corpus_2026-09-22.txt

# is the API answering at all, before spending a loop on finding out:
python -c "import anthropic;from dotenv import load_dotenv;load_dotenv();\
print(anthropic.Anthropic().messages.create(model='claude-haiku-4-5-20251001',\
max_tokens=8,messages=[{'role':'user','content':'ok'}]).content[0].text)"

git status --short
git log --oneline 630dc42..HEAD
git rev-list --count 630dc42..HEAD

# the corpus: prompts, answers, and the run's reading
grep -n '^### 3c\|^| [VCRS]-\|^\*\*S-' docs/benchmark.md
grep -n '^## Part 18\|^### [0-9]\|^- \*\*[CRS]-' tests/golden/expected_values.md | sed -n '/Part 18/,$p'
sed -n '/^### 3c.6/,/^## Part 4/p' docs/benchmark.md | grep -c '| matched'

# the spine's wordings in the two places they live, held by pytest:
pytest -q tests/test_corpus_spine.py

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
git switch baseline-v1 && git merge --ff-only corpus-run
git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1
```
### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~7s, no model calls | Do the components still work; does every reference Part reproduce; does each node fetch in order and publish its block; does the gate refuse what it must; does the outcome compose every row of the truth table; **do Part 3c.1's wordings match the runner's**. Sees nothing of the corpus's answers. |
| CLI | ~2s and one Haiku call for most questions; 4.3 about 15s and two Sonnet calls, 4.4 about 14s and one; a deterministic clarification free; **fetches prices past their interval, which runs out on the 23rd at 17:11** | What it is actually doing: the plan, the parameters, the reasoning line, the answer text. **The only loop that shows an answer, and therefore the only loop that can be read against Part 18.** The whole corpus is 65 turns, 2 minutes 19 seconds and about 0.15 dollars. |
| Golden set | ~50s, about $0.039 per run; writes to no table since decision 51, prices aside | Did routing change anywhere (twenty-one lines, one pinned failure). Blind to `measure`, `group_by`, `tickers`, answer text, and any wording it does not carry |
| Benchmark runner | ~50s, about $0.039; `--case X` is one routing at about $0.001 | How many cases pass, n/18. Its checks read each answer's text and show it to nobody. **Carries none of the 41 corpus additions** |

`golden set → change → golden set → decide → then update expected.txt, its own
commit`. Prediction first, twice for a prompt change, stop at the second miss
on a line. The runner is per capability commit that reaches the graph, and per
commit that changes an answer's text. The two paid loops one after the other,
never at once. **Never pipe a paid run through a filter.** **The corpus is
read by hand against Part 18; a run gets its dated block in Part 3c.6 and its
transcript beside `expected.txt`; a miss is logged with a trigger, not fixed,
until step 4's rule says it is arithmetic.**
