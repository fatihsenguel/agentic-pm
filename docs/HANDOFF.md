# AGENTIC_FINANCE — Session Handoff

**Session date:** 26 September 2026 (forty-fifth session), the afternoon, UTC.
**Branch:** `checks`, cut from `baseline-v1` at **41a6d19** in the worktree `.claude/worktrees/checks`, **eight commits with this one**. Built under CLAUDE.md as revised on 26 September: the shape approved once, then one part per commit without a yes each, then the branch shown for review. `checks` is not merged, not pushed, **to be merged `--ff-only` by the owner**.

**State:** pytest **2052 passed, 6 xfailed** (2036 at 41a6d19). **The runner: 8 of 18** (run of 26 September, 15:43 UTC, at 22063f6), against a prediction of 9. The corpus at 33 of 67, not re-run.

**Decision 17 is taken and built, as C2, the runner's checks.** The pending list is seven: 10, 13, 22, 48, 52, 54 and 76.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session checked:
- the trunk against the remote at the start: `baseline-v1` and `origin/baseline-v1` both at 41a6d19, so the previous handoff's "`run-record` ... to be merged" was stale by one merge and its worktree already gone;
- pytest at the branch point, 2036 passed, and red before and green after each of the four code parts;
- every caller of each check and accessor the parts moved, by grep, in the runner and in six test files;
- that every portfolio tool's run publishes the same three blocks, in `tool_runner.BLOCKS`, before letting a case call two tools;
- that the turn carries one trace and the layer runs its tools one after another, before reading 2.1's run as a stretch of it;
- that the screen's range carries the screen's own as-of and source in the node, before correcting a test fixture that did not;
- that every holding's last stored close was 2026-09-25, by query, before the paid run;
- that the worktree's `run_cases.py` imports the worktree's `src`, by printing the path, before the paid run;
- that each KNOWN_GAPS title cited exists, by grep.

It did not re-check §3's library versions, the filings clocks or the store beyond the closes.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Unchanged this session. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. **Start with the last two entries:** "The runner's checks against a selecting layer - decision 17, TAKEN 26 September (forty-fifth session)", with its four rules and their commits, and "The runner after decision 17: 8 of 18 against a prediction of 9". **209 lines start `**Trigger:**`**, 9,425 lines. |
| `tests/benchmark/run_cases.py` | `_the_call` and `_of` (a case's own record), `_one_call` (3.2 alone), `_trace_shows_handovers` (the run as a stretch), `_date_shown` and `_source_shown` (the record's provenance), `_date_reaches_answer` (the prose). |
| `tests/test_runner_probes.py` | The four rules' tests, and `record_of`, which now writes the provenance the tool runner derives. |
| `src/agents/tool_runner.py` | The record and `_provenance`: one as-of and one source per record. |
| `docs/benchmark.md` Part 3, the block written at c153d73 | The prediction the run was read against. |
| `tests/golden/expected_values.md` Part 18 | What each answer must carry; the checks moved toward it and only toward it. Part 18 is here and not in benchmark.md. |

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`; the owner pushes by URL and fetches after.
**Machine:** MacBook Air, Apple Silicon.

### What this session did, in one paragraph

C2, inside decision 17, case by case against Part 18. Decision 17's
shape, the tool returning its whole block and the layer selecting, was
taken inside decision 45 and built with Order 5; what it left was the
runner's rules, written when the answer was the formatter's whole text.
On the owner's yes, four rules: a case names its tool and allows others,
reading its blocks from its own tool's record (a reading the owner
approved separately before the first commit); 2.1's run is found as one
unbroken stretch of the turn's trace; the as-of and source a record's
provenance carries are read from the record and not the prose; a prose
check asks what Part 18 pins and no more. Then the record, the
prediction (9 of 18), and one paid run on the owner's word: 8 of 18.

### How I work on this

- **Say the decision in plain words before the yes**, and stop again
  when building finds something the shape did not foresee: the blocks
  every portfolio tool publishes were that here.
- **A check moves toward its reference and never toward the output.**
  Part 18 was written before any run; the checks were narrowed to it
  and not widened in the same decision.
- **A paid run is read against a prediction written before it**, and a
  verdict against its line is a failed hypothesis.
- **One question per message, asked as a yes or a no.**

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/benchmark/run_cases.py        # PAYS, about $0.14: ask first
python src/agents/cli.py --portfolio 3      # PAYS per turn
```

**pytest: 2052 passed, 6 xfailed.**

**The runner: 8 of 18, 7 failing, 3 blocked** (26 September, 15:43:10
to 15:45:02 UTC, at 22063f6, about $0.14). Predicted 9 of 18. 2.3 moved
to PASS as predicted, its one failure having been the as-of in the
prose. 3.3 moved against the prediction to BLOCKED: the model called no
tool, the second of four draws to do so. 2.1 failed as predicted on
another reason: the client refused an answer carrying the figure 48. No
case failed on a rule decision 17 moved. The output was not kept as a
file; the entry carries every verdict and reason.

**The corpus: 33 of 67** (the forty-second session's run, unchanged).
Decision 17 changes nothing the model is sent or the client prints.

### Branches

`baseline-v1` at **41a6d19**, pushed. `checks` carries eight commits, to
be merged `--ff-only`. Its worktree has a `data/portfolio.db` symlink,
which must go before the worktree can be removed (§7).

### Database

`data/portfolio.db`, untracked. Every holding's last stored close is
2026-09-25; the run fetched nothing, no market having closed since.

---

## 3. Environment

As the handoff at 41a6d19 gave it, and:

- **CLAUDE.md holds no pending list since 26 September**; the list is in
  §5 here only. The previous handoff's §3 line about it was stale.
- **In this worktree a heredoc into python ran**, where CLAUDE.md says
  the harness refuses heredoc appends; `git stash list` was refused.
  The rule stands as written for appends.
- From a worktree, pytest and `run_cases.py` import the worktree's
  `src`, checked again by printing the path.

---

## 4. What the forty-fifth session did

**On `checks`, eight commits:**

| Commit | What it is | pytest |
|---|---|---|
| **dcded39** | run_cases: a case names its tool, called once, and allows others beside it; its blocks and agents from its own record; 3.2 one call alone | 4 failed, 2036 passed, then 2040 |
| **3249dae** | run_cases: 2.1 finds its run as one unbroken stretch of the turn's trace | 2 failed, 2041 passed, then 2044 |
| **0fb0dcc** | run_cases: the as-of and the source read from the record's provenance; `record_of` writes the runner's provenance; the screen fixture's range built as the node builds it | 4 failed, 2045 passed, then 2049 |
| **a5f46ac** | run_cases: the prose checks of 1.4, 4.2 and 4.4 ask what Part 18 pins | 3 failed, 2049 passed, then 2052 |
| **c153d73** | KNOWN_GAPS: decision 17 taken as the runner's checks, its entries read against it | document |
| **22063f6** | benchmark: the runner's prediction after decision 17, 9 of 18 | document |
| **9723c0f** | KNOWN_GAPS: the runner after decision 17, 8 of 18 against a prediction of 9 | document |
| **This commit** | the handoff, regenerated | document |

**Mistakes of this session, recorded:**
- The instruction pointed to "Part 18 in benchmark.md"; it is in
  `expected_values.md`. Said before the shape.
- Part 2's first red test asserted that the allocation's run followed
  by ComplianceAgent alone breaks the stretch; it does not, and the
  missing handover fails that turn. Corrected before the commit, named
  in it.
- Part 3's first test block for 1.1 lacked the view the check returns
  early without; part 4's first 1.4 test filtered on sector names and
  caught the cost-basis checks. Both corrected before their commits.
- Writing the KNOWN_GAPS notes I first read a prediction table of the
  corpus as the run of 24 September, and would have closed "Cases 4.1
  and 4.2 return the same answer" on it; the run itself printed the
  range beside 4.1's stop. Caught before the commit. I also first wrote
  that the CLI had not run since the layer, when the corpus runs through
  it; removed before the commit.
- In the message after the run I said sixteen verdicts matched their
  lines; seventeen did. The entry says seventeen.

**Resolved, three:** "The synthesizer returns the same answer regardless
of the question", "`measure` set by the model under intent compliance is
unread", "The runner's first run through the layer: 5 of 18 against a
prediction of 11".

**Logged, three, each with a trigger:** "A one-ticker P&L record's
provenance states the earliest close of all nine", "Whether a record's
provenance should carry every date its block states", "1.3's basis
check asks for the covariance method, which Part 18 does not name".

---

## 5. Decisions taken, and decisions pending

**Taken this session, on the owner's yes:**
- **Decision 17, as C2, in six parts, as brought.** Decision 54 left
  out, to be brought as its own question.
- **The reading added before part 1:** a case reads its blocks from its
  own tool's record, since every portfolio tool publishes the same three.
- **The paid run**, about $0.14.

**Pending — seven:** 10, 13, 22, 48, 52, 54 and 76. The cap is 25.
None opened, one closed.

**Surfaced and not numbered:**
- **The German figures**, whether the answer's notation or the check's
  reading of it moves. Unchanged.
- **What the philosophy screen may be asked**, given R-2's pin and 4.6
  screening a held JPM. Unchanged.
- **Whether provenance should carry every date a block states**, logged
  with a trigger; it would take the last dates out of the narration.

---

## 6. Where we stand against the benchmark

**Runner 8 of 18, corpus 33 of 67.** Every failure the runner now shows
is the answer carrying less than Part 18 pins, or no tool called: 1.4's
unsectored share, 2.2's clauses, 4.2's assumptions and the fiscal year's
dates, 4.4's readings and proposal, 4.6's pull date, 3.2's and 3.3's
missing calls, and 2.1's refused answer. None is a rule written for the
formatter's whole text. What remains is the prompt's and the layer's,
and a prompt change is a hypothesis with its own prediction.

**What no loop has seen yet:** `rebalance`; a German span question; what
a corpus run costs; a one-figure question through the layer; the CLI's
per-record lines on a live turn read by hand.

---

## 7. Next steps, in order

**1. The branch review and the merge.** `checks` onto the trunk,
`--ff-only`, the push by URL, `git fetch origin`. The worktree's
database link first, from the VS Code terminal, then the worktree:

```
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE/.claude/worktrees/checks" && rm data/portfolio.db && rmdir data
```
```
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE" && git merge --ff-only checks && git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1 && git fetch origin && git worktree remove .claude/worktrees/checks
```

**2. Decision 54 as its own question**, its blast radius measured
first: `base_agent.py`, 409 lines; `DataAgent` and `RebalanceAgent`
subclass it; `agents/__init__.py`'s exports; `AgentSettings` in
`src/agents/config.py`; `tests/test_all_configs.py` and
`tests/test_phase5_4_integration.py`.

**3. The two surfaced questions**, the German figures and the screen's
scope, each a shape before any code.

### Later, with reasons

- **A prompt change**, on the owner's word only: 3.3's missing call,
  2.1's figure of its own, and the prose Part 18 pins, each a hypothesis
  with a prediction first.
- **The CLI as the client, the README, the demo recordings**, after
  Order 5.
- **The console glyphs**, their own session; "Statements about the
  router and the synthesizer outlive them" is read in it.
- **Decision 76**, on the owner's word only. **W-2**, out of scope.

---

## 8. Rules learned the hard way

**Allowing a second call changes what "the block" means.** When one
case may call two tools, a block read from "the last record carrying
it" may be another tool's. Find the reader of every shared key before
loosening the rule that made it unique.

**A test fixture can be a state the code cannot produce.** A new check
that fails a fixture is read against the node before either is changed.

**A prediction table is not a run.** Read the block's heading before
citing a verdict from it.

Still true: the handoff at 41a6d19's list, and everything before it.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q          # 2052 passed, 6 xfailed
python tests/benchmark/run_cases.py                # PAYS, about $0.14 a run; ask first
python src/agents/cli.py --portfolio 3             # PAYS per turn; :q to quit
git show golden-parked:tests/golden/run_golden.py  # the parked golden set
git show router-parked:src/agents/smart_router.py  # the parked router
```
