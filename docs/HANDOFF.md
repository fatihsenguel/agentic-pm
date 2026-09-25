# AGENTIC_FINANCE — Session Handoff

**Session date:** 24 September 2026 (forty-third session), begun about 17:40 local time.
**Branch:** `tracing-question`, cut from `baseline-v1` at **a66bc02** before its first commit, in the worktree `.claude/worktrees/tracing-question`; **five commits with this one**, each on the owner's yes after its diff was shown. Not merged, not pushed, **to be merged `--ff-only` by the owner**.

**State:** pytest **2011 passed, 6 xfailed** (2008 at a66bc02). **No paid loop ran.** The runner stands at 5/18 and the corpus at 33 of 67, both from the forty-second session's runs.

**B is taken and done.** **A with C1 is decision 77, numbered and pending.** The pending list is nine: 10, 13, 17, 22, 48, 52, 54, 76 and 77.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session checked:
- the trunk head against the remote: `baseline-v1` and `origin/baseline-v1` both at a66bc02, where the last handoff said 02a9e57 (the merge after it was written);
- pytest at the branch point, at the red commit and after the change;
- that the client checks the resolved question (`graph._turn`, `conversation.answer`) and the runner the typed one, before changing the runner;
- that `resolved` is reset to `None` on every turn (`create_initial_state`);
- every call site the blast radius of decision 77 counts, by grep;
- that every title it cites exists once in KNOWN_GAPS.

It did not re-check §3's library versions, the filings clocks or the store.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Unchanged this session. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. **Start with "What a turn's result carries - decision 77, pending"**, the last entry in the file. **203 lines start `**Trigger:**`**, 9,049 lines. |
| `tests/benchmark/run_cases.py` | `figures_trace`, changed this session; the accessors `_shared`, `_compliance` and the rest, which decision 77 would move. |
| `src/agents/graph.py`, `conversation.py`, `tool_runner.py` | `graph._turn` keeps the last tool run's `shared_data` and `sub_results`; `run_tool` builds the record decision 77 would extend. |
| `docs/benchmark.md` Part 3c.6, the fifth block | The corpus run of the forty-second session, unchanged. |

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`; the owner pushes by URL and fetches after.
**Machine:** MacBook Air, Apple Silicon.

### What this session did, in one paragraph

B on paper, then on the owner's yes, its tests red and its change: the
runner's tracing check now reads a resolved reply against the question
it was resolved into, the one the client already checks against. Then A
with C1 on paper, measured before it was proposed, and numbered decision
77 on the owner's word, pending. Then the record swept for B. Nothing was
paid for, no prompt changed, and nothing of A was built.

### How I work on this

- **Measure before proposing.** Decision 77's blast radius was counted by
  grep, and the count found a read the shape had not accounted for (1.3's
  single-name volatilities, §5).
- **One question per message, asked as a yes or a no.**
- **A decision that touches the state gets a number; one that makes a
  check agree with a rule already decided does not.** B was the second
  kind, 77 the first.

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/benchmark/run_cases.py        # PAYS, about $0.15: ask first
python src/agents/cli.py --portfolio 3      # PAYS per turn
```

**pytest: 2011 passed, 6 xfailed.**

**The runner: 5/18** (run of 14:16 UTC at 78c61cd, unchanged). **Predicted
for its next run: 3.1 PASS**, the one line it failed on, `['15']`, being
the line this session's change removes, provided the model again calls
`hypothetical_weight` at 0.15 and cites IPS-4.1. Nothing else is
predicted to move from B. The prediction is written here and in
KNOWN_GAPS, not in benchmark.md; it goes there before a run the owner
orders.

**The corpus: 33 of 67** (the forty-second session's run, unchanged). B
moves nothing the corpus reads: the client's check did not change.

### Branches

`baseline-v1` at **a66bc02**, pushed. `tracing-question` carries this
session's five commits, to be merged `--ff-only`; its worktree holds a
symlink `data/portfolio.db`, removed with the worktree after the merge.

### Database

`data/portfolio.db`, untracked, not touched this session. Still no close
of 2026-09-22 for JNJ, NEE and VNQ (logged).

---

## 3. Environment

As the handoff at a66bc02 gave it, and:

- **From a worktree, pytest and `run_cases.py` import the worktree's
  `src`**: `tests/conftest.py` and `run_cases.py` each put their own
  checkout's `src` first. Checked this session by printing
  `run_cases.__file__` before running anything.
- **CLAUDE.md says the pending list "stands at 8".** It is nine now. The
  file is the owner's and excluded from the repository; not edited.

---

## 4. What the forty-third session did

**Five commits on `tracing-question`:**

| Commit | What it is |
|---|---|
| **5cc3a9a** | three tests of `figures_trace` on a resolved reply, red: pytest 3 failed, 2008 passed |
| **d893747** | `figures_trace` reads `state["resolved"]["message"]` where a reply was resolved; 2011 passed |
| **11bee81** | KNOWN_GAPS, decision 77 numbered and pending |
| **709c4af** | KNOWN_GAPS, B's entry resolved and the runner's entry read against it |
| **This commit** | the handoff, regenerated |

**What the three tests pin:**
- the runner reads a resolved reply against the resolved question, as the
  client does (3.1's "15" passes, and `untraced_figures` is asserted on the
  same input);
- the typed reply is not what is read on a resolved turn;
- a resolution with no message raises, rather than falling back to the
  typed turn.

**Resolved, one:** "The runner's tracing check and the client's read
different questions on a resolved reply".

**Mistakes of this session, recorded:** none found. The blast radius's
line counts for the layer and the CLI (about 60 and about 40) are
estimates from reading, not a diff; the runner's and the tests' are
counted.

---

## 5. Decisions taken, and decisions pending

**Taken this session, on the owner's yes:**
- **B**, on the recommendation and without a number: the runner reads the
  question the turn recorded. It applies decision 45's rule, which the
  client already enforces; nothing about the state, the tools or the
  roster moved.
- **Decision 77 numbered**, pending, with its recommendation recorded.

**Pending — nine:** 10, 13, 17, 22, 48, 52, 54, 76 and **77**. The cap is
25. One opened, none closed.

**Decision 77, what a turn's result carries.** In KNOWN_GAPS under "What a
turn's result carries - decision 77, pending", with the shape, the
rejected alternatives, the blast radius and what each loop would show.
In one breath: the tool records replace the turn's one `shared_data`;
each record carries every summary block its run published, the agents
that ran, and its provenance (as-of, source where the block states one,
fixed caveats per tool); the CLI prints a line per record; the tracing
check allows the records of the conversation's earlier turns, which
answers S-4's follow-up. **One sub-question inside it:** 1.3's check
reads the nine single-name volatilities from `shared_data`, which no
block carries; recommended, to pytest.

**Surfaced and not numbered, unchanged from the forty-second session:**
- **C2. The runner's prose checks against a selecting layer**, inside
  decision 17.
- **The German figures**, whether the answer's notation or the check's
  reading of it moves.
- **What the philosophy screen may be asked**, given R-2's pin and 4.6
  screening a held JPM.

The follow-up question the forty-second session surfaced is now part of
decision 77.

---

## 6. Where we stand against the benchmark

**Runner 5/18, corpus 33 of 67**, neither re-run. One runner failure,
3.1's, was the runner's own check disagreeing with the client's, and is
removed. The rest of the forty-second session's reading stands: the
layer reads names, German and referents, and loses the formatters'
completeness, dates and caveats first.

**What no loop has seen yet:** `rebalance`; a German span question; what
a corpus run costs; the runner after B.

---

## 7. Next steps, in order

**1. The merge.** `tracing-question` onto the trunk, `--ff-only`, the push
by URL, `git fetch origin`, the worktree removed.

**2. Decision 77**, the owner's. If taken: tests first, per tool record
and per runner accessor, then the change, one change per commit. The
record's fields, the runner's reads and the CLI's lines are separate
commits.

**3. C2 inside decision 17's commit**, case by case against Part 18;
decision 54's commit beside it. After 77, since the runner's reads move
under it.

**4. The runner's next paid run**, on the owner's word, with 3.1's
prediction written into benchmark.md first.

**5. The two remaining surfaced questions**, the German figures and the
screen's scope, each a shape before any code.

### Later, with reasons

- **The CLI as the client, the README, the demo recordings**, after
  Order 5.
- **The console glyphs**, their own session.
- **Decision 76**, on the owner's word only. **W-2**, out of scope.

---

## 8. Rules learned the hard way

**Grep the reader before proposing to move what it reads.** The shape of
decision 77 assumed each tool's block was what the runner read; 1.3 reads
a DataAgent key beside the block, and `position`'s record needs three
blocks, not one. Both showed up only when every read site was listed.

**A check and its client read the same input or they are two rules.** B
was a runner that enforced invariant 1 on a different question from the
one the client enforced it on; each was right by its own reading.

Still true: the handoff at a66bc02's list, and everything before it.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q          # 2011 passed, 6 xfailed
python tests/benchmark/run_cases.py                # PAYS, about $0.15 a run; ask first
python src/agents/cli.py --portfolio 3             # PAYS per turn; :q to quit
git show golden-parked:tests/golden/run_golden.py  # the parked golden set
git show router-parked:src/agents/smart_router.py  # the parked router
```
