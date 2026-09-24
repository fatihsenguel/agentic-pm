# AGENTIC_FINANCE — Session Handoff

**Session date:** 24 September 2026 (forty-second session), begun about 14:00 UTC. Regenerated twice: once at 02a9e57 after the runner's run, and again here after the corpus run.
**Branch:** `corpus-layer`, cut from `baseline-v1` at **02a9e57** before its first commit; **five commits with this one**, each on the owner's yes after its diff was shown (the corpus transcript, 5,796 lines, as its cut lines and its 57 answers in full, on the owner's word). Not merged, not pushed, **to be merged `--ff-only` by the owner**. The session's first branch, `first-run`, five commits, was merged and pushed by the owner at 02a9e57.

**State:** pytest **2008 passed, 6 xfailed** at every commit. **Two paid loops ran, once each, on the owner's word.**
- **The runner: 5/18**, 10 failing, 3 blocked, against a prediction of 11/18 written before it; $0.14 measured for the layer.
- **The corpus: 33 of 67**, against the fourth block's prediction of 52 and the 22 September baseline of 31. The cost is unmeasured, since the CLI prints no tokens; about $0.55 estimated.

**Nothing was fixed.** The pending list is eight, unchanged: 10, 13, 17, 22, 48, 52, 54 and 76.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session checked:
- the trunk head against the remote;
- pytest before and after every commit;
- the store (closes, readings, assets) before and after both runs;
- that every corpus prompt it sent is in benchmark.md word for word;
- that every title it cites exists once in KNOWN_GAPS;
- which agents each corpus turn ran, read from the transcript.

It did not re-check §3's library versions or the filings clocks.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Unchanged this session. |
| `docs/benchmark.md` | **Part 3c.6's fifth block**: the corpus run after the layer, read line by line against Part 18, each line marked against the fourth block's prediction. Level 4's end carries the runner's prediction of this morning. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. **Start with the twelve entries at the end of the file**: the runner's five and the corpus's seven, logged this session. **202 lines start `**Trigger:**`**, 8,945 lines. |
| `tests/golden/run_corpus_2026-09-24.txt`, `run_cases_2026-09-24.txt` | The two transcripts, whole but for the worktree path cut, said in each commit. The corpus's is the only record of the layer's answers. |
| `tests/golden/expected_values.md` Part 18 | What each corpus answer must carry. Unchanged; read in full for the fifth block. |
| `src/agents/conversation.py`, `graph.py` | The layer, unchanged. `SYSTEM_PROMPT`, the descriptions, `untraced_figures`; `graph._turn`, which keeps the last tool run's state. |

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`; the owner pushes by URL and fetches after.
**Machine:** MacBook Air, Apple Silicon.

### What this session did, in one paragraph

A prediction for the runner, committed; the runner's first paid run
through the layer; its reading, its tokens, its findings. Then, after the
merge, the corpus run: sixty-seven turns through the CLI, one process per
entry, since the CLI carries each turn into the next and the layer sends
it to the model. Every turn read by hand against Part 18 and the fourth
block, written as the fifth block. Nine entries the run triggered were
dated, six of them resolved, and seven findings logged. Between the two
runs, the owner asked for recommendations on the surfaced decisions,
then whether they hold for the long term; §5 records the answer.

### How I work on this

- **The prediction is read against the check or the reference as
  written**, not against the answer the question deserves.
- **Read strictly and say so.** A statement Part 18 pins counts as missed
  when it is absent. That is why the fifth block marks answers that read
  well as missed.
- **A figure in an answer proves which tool ran.** The CLI shows only the
  last tool run's agents. 2.1's "56.75% of sectored value" is printed
  only by the allocation's text, so the model called it.
- **One question per message, asked as a yes or a no.** An either-or
  question answered "yes" had to be asked again.

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/benchmark/run_cases.py        # PAYS, about $0.15: ask first
python src/agents/cli.py --portfolio 3      # PAYS per turn
```

**pytest: 2008 passed, 6 xfailed.**

**The runner: 5/18** (run of 14:16 UTC at 78c61cd). PASS 1.1, 3.3, 3.4,
3.5, 4.5; BLOCKED 2.1 (two tools in one turn), 4.1 and 4.3 (PHI-2.1);
FAIL the rest.

**The corpus: 33 of 67** (run of 15:08 to 15:15 UTC at 02a9e57, 57
processes).
| Section | Matched |
|---|---|
| Spine | 7 of 19 |
| Variations | 7 of 15 |
| Clarifications | 7 of 7 |
| Refusals | 6 of 9 |
| Sequence turns | 6 of 17 |

Against the fourth block's 52: 23 lines moved against it, and 4 moved the
other way (3.1 and V-3.1a to c, by Part 18's correction). No miss was a
reading gap, a guess or a turn that cannot be done: names, German and
referents were all read.

### Branches

`baseline-v1` at **02a9e57**, pushed. `corpus-layer` carries this
branch's five commits, to be merged `--ff-only`; its worktree holds a
symlink `data/portfolio.db`, removed with the worktree after the merge.

### Database

`data/portfolio.db`, untracked.
- `daily_prices` **7,043**, last close **2026-09-23**. The runner fetched
  17 rows and the corpus Adobe's two.
- **No close of 2026-09-22 for JNJ, NEE and VNQ** (logged).
- `document_readings` 7: Adobe's Item 1 was read again on R-9 and refused,
  no row stored.
- `watchlist.toml` unchanged.

---

## 3. Environment

As the handoff at 02a9e57 gave it, and:

- **The corpus is sent one process per entry and per sequence.** The
  driver was a scratch script, not committed. Each process's header in
  the transcript carries the equivalent `printf ... | cli.py` command.
- The CLI's routing block prints the empty fields of a key that no longer
  exists; its answer block is what the corpus reads.
- Sonnet 5: a 2,428-token cached prefix; about $0.008 a model turn with
  the cache warm.

---

## 4. What the forty-second session did

**Ten commits in two branches.** On `first-run`, merged at 02a9e57:

| Commit | What it is |
|---|---|
| 78c61cd | the runner's prediction |
| 1c48090 | the runner's transcript |
| bb077c2 | the three entries it triggered |
| 3bc69d2 | its five findings |
| 02a9e57 | the handoff |

On `corpus-layer`:

| Commit | What it is |
|---|---|
| **0611478** | the corpus transcript, the path cut from 153 lines on the owner's word |
| **c1e85cf** | benchmark.md, the fifth block |
| **9bc1400** | KNOWN_GAPS, the nine entries the corpus run triggered |
| **46e00b3** | KNOWN_GAPS, seven findings |
| **This commit** | the handoff, regenerated |

**Resolved, six:**
- "The extraction bridge reads symbols, not company names"
- "The four phrase rules in extraction read English"
- "A follow-up that depends on the previous turn is asked back by the model"
- "A bare opinion on a company is routed to the philosophy screen"
- "The prediction's 3.1 line names the tool where the pre-pass asks back"
- this morning, "What a turn of the layer costs is an estimate with no thinking tokens in it"

The names, the German, the referents and the bare opinion are the layer's
now, as decision 45 intended.

**What the two runs found**, logged with triggers, nothing fixed:
- **The as-of dropped** from eleven corpus turns and five runner cases.
- **Statements Part 18 pins left out**: no look-through, not an average,
  PHI-6.2.
- **Two tools in one turn keep only the last one's state.** 2.1 did this
  on both draws.
- **3.2 called no tool** once in eight draws of its instruction.
- **The runner's tracing check and the client's read different
  questions** on a resolved reply.
- **German figures are refused by the tracing check.**
- **A follow-up that quotes the previous turn's figures is refused.**
- **3.3 called the tool on one draw and asked back on the other.**
- **"Apple" and "AAPL" moved the tool choice**, V-2.1a against V-2.1b.
- **An answer offered the screen for a company on no entry**, R-2.
- **The narration adds comparisons and summaries no tool printed.**
- **The CLI prints no tokens.**
- **Three closes of the 22nd are missing.**

**Mistakes of this session, recorded:**
- a hand-written hunk header;
- a fetch count read against a wrong expectation (18 for 20);
- 22 lines counted as twenty;
- a proposal in shorthand the owner had to ask about;
- in drafts caught before commit: 2.1's corpus draw first recorded as
  unknowable, "no tool of its own turn" for S-4, which called the lookup,
  eight breaches for seven, ten turns for eleven, and two times not in the
  record.

---

## 5. Decisions taken, and decisions pending

**Taken this session, on the owner's yes:**
- the prediction's place in benchmark.md;
- the path cut in both transcripts;
- one process per corpus entry.

**Pending — eight, unchanged:** 10, 13, 17, 22, 48, 52, 54 and 76. The cap
is 25. None opened or closed.

**Surfaced and not numbered**, each logged with a trigger. The owner
decides whether each becomes a pending decision. The recommendations are
the ones given in conversation after the runner's run and re-checked for
the long term. The owner gave permission to continue on them; none is
taken as a decision.

- **A. What a turn of several tools carries.** Recommended: the tool-call
  log is the turn's result. The runner reads each tool's block from its
  record, and the turn's single `shared_data` goes. It holds more strongly
  as the judgement half makes multi-tool turns normal.
- **B. Which question the tracing check reads on a resolved reply.**
  Recommended: the runner reads the recorded `resolved.message`, and never
  rebuilds it from the reply.
- **C1. The as-of and fixed caveats.** Recommended for the long term:
  provenance as a field of the turn's result, the as-of, source and
  caveats taken from the tool records. The CLI renders it and the check
  asserts on it. It is one design with A, built minimally now and fully
  with the CLI after Order 5. It replaces an earlier recommendation to
  append text.
- **C2. The runner's prose checks against a selecting layer.**
  Recommended: completeness is asserted on the tool records, and the prose
  holds only what its question requires. Case by case against Part 18,
  inside decision 17.
- **New from the corpus:**
  - the German figures, whether the answer's notation or the check's
    reading of it moves;
  - whether a follow-up may quote an earlier turn's tool output, which
    goes with A;
  - what the philosophy screen may be asked, given R-2's pin and 4.6
    screening a held JPM.

---

## 6. Where we stand against the benchmark

**Runner 5/18, corpus 33 of 67.** The layer reads what the router could
not: company names, German, referents, and a bare opinion refused on the
clause. The clarifications are all exact.

What it loses is the formatter's completeness. Dates, caveats and whole
tables are selected away, and nothing but the reading sees it. The model's
tool choice varies between draws of the same question (3.3, 3.2) and
with the wording of one (V-2.1a against V-2.1b).

**What no loop has seen yet:** `rebalance`; a German span question; what
a corpus run costs.

---

## 7. Next steps, in order

**1. The merge.** `corpus-layer` onto the trunk, `--ff-only`, the push by
URL, `git fetch origin`, the worktree removed.

**2. B**, the smallest and clearly right: a shape and its tests, one line
in the runner.

**3. A with C1 as one shape on paper.** The turn's result is the answer
plus the tool records that ground it. The shape includes the follow-up
question and the runner's reads.

**4. C2 inside decision 17's commit**, case by case against Part 18;
decision 54's commit beside it.

**5. The three new surfaced questions**, each a shape before any code.

### Later, with reasons

- **The CLI as the client, the README, the demo recordings**, after
  Order 5. The CLI's tokens and a raise's shape are triggered by it.
- **The console glyphs**, their own session; the CLI's glyphs are in
  both transcripts.
- **Decision 76**, on the owner's word only. **W-2**, out of scope.
  **CLAUDE.md's loop list** names the golden set; it is the owner's file.

---

## 8. Rules learned the hard way

**A batch in one CLI process is a conversation.** Under the layer, every
earlier turn reaches the model; the corpus is sent one entry to a process.

**The tracing check is strict both ways.** It refuses a figure written in
another notation and a figure carried from an earlier turn. Each refusal
is correct by its rule and still an answer the reader never sees.

**A figure proves a tool call the log does not show.** When the log is
not printed, look for a figure only one tool's text carries.

**Count against the record, not the reference's date.** Part 18's eight
breaches are seven at the 23rd's closes.

**Ask a yes-or-no question.** An either-or question answered "yes" is a
question asked twice.

Still true: the handoff at 02a9e57's list, and everything before it.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q          # 2008 passed, 6 xfailed
python tests/benchmark/run_cases.py                # PAYS, about $0.15 a run; ask first
python src/agents/cli.py --portfolio 3             # PAYS per turn; :q to quit
git show golden-parked:tests/golden/run_golden.py  # the parked golden set
git show router-parked:src/agents/smart_router.py  # the parked router
```
