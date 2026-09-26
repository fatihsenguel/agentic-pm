# AGENTIC_FINANCE — Session Handoff

**Session date:** 26 September 2026 (forty-fifth session), the afternoon and evening, UTC.
**Branches:** `checks`, cut from `baseline-v1` at 41a6d19, ten commits, **merged `--ff-only` and pushed by the owner at 61265ff**, its worktree removed. Then the tag **`agent-loop-parked`** at 61265ff, local and not pushed, and `loop`, cut from 61265ff in the worktree `.claude/worktrees/loop`, **six commits with this one**. Built under CLAUDE.md as revised on 26 September: each shape approved once, then one part per commit, then the branch shown for review. `loop` is not merged, not pushed, **to be merged `--ff-only` by the owner**.

**State:** pytest **2060 passed, 6 xfailed** (2052 at 61265ff, 2036 at the session's start). **The runner: 8 of 18** (run of 26 September, 15:43 UTC, at 22063f6), against a prediction of 9. The corpus at 33 of 67, not re-run.

**Decisions 17 and 54 are taken and built.** The pending list is six: 10, 13, 22, 48, 52 and 76.

Written for whoever picks this up cold, myself included.

**Regenerate this document at the end of each session rather than patching it.**
**Check every claim here against the code before acting on it, including
this file.** This session checked:
- the trunk against the remote at the start and after the owner's merge: 41a6d19, then 61265ff on both;
- pytest at each branch point and red before and green after each of the eight code parts;
- every caller of each check, accessor, class and export the parts moved or deleted, by grep, in `src/` and `tests/`;
- that `agents.base_agent` cannot be imported once the file is gone, with bytecode writing off, the orphan `.pyc` in `__pycache__` notwithstanding;
- that `DataAgent`'s tools call `self.log` and nothing else of the base class, and that the nodes build both agents with `verbose=False`;
- that only `PortfolioContext` of `protocols.py`'s eleven types has a reader outside the deleted loop;
- that the tracer's `CostCalculator` runs on every trace, before leaving it out of decision 54;
- that every holding's last stored close was 2026-09-25 and that the worktree's `run_cases.py` imports the worktree's `src`, before the paid run;
- that each KNOWN_GAPS title cited exists, by grep.

It did not re-check §3's library versions, the filings clocks or the store beyond the closes.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/DIRECTION.md` | **The end state and the invariants.** Unchanged this session. |
| `tests/golden/KNOWN_GAPS.md` | **Every open entry carries a `Trigger:` line.** Read the entries whose trigger has fired or whose decision is on §5's list, and no other. **Start with the last four entries:** "The runner's checks against a selecting layer - decision 17, TAKEN 26 September (forty-fifth session)", "The runner after decision 17: 8 of 18 against a prediction of 9", "BaseAgent's loop and the config fields that describe it - decision 54, TAKEN 26 September (forty-fifth session)" and "`_get_prices_from_db` reports any database error as no data". Then "CostCalculator reports costs for the wrong model", whose trigger fired. **211 lines start `**Trigger:**`**, 9,531 lines. |
| `tests/benchmark/run_cases.py` | `_the_call` and `_of` (a case's own record), `_one_call` (3.2 alone), `_trace_shows_handovers` (the run as a stretch), `_date_shown` and `_source_shown` (the record's provenance), `_date_reaches_answer` (the prose). |
| `tests/test_agents_without_loop.py` | What decision 54 left: two agents that subclass nothing, `protocols.py` with `PortfolioContext` alone, no `AgentSettings`. |
| `src/observability/tracer.py` | `CostCalculator` at 393 and its use at 386: the one price the code still computes. |
| `docs/benchmark.md` Part 3, the block written at c153d73 | The prediction the last run was read against. |
| `tests/golden/expected_values.md` Part 18 | What each answer must carry. Part 18 is here and not in benchmark.md. |

---

## 1. Project and intent

**AGENTIC_FINANCE** — a portfolio-management and equity-research assistant on LangGraph. Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public). The push URL of `origin` is `no_push`; the owner pushes by URL and fetches after.
**Machine:** MacBook Air, Apple Silicon.

### What this session did, in one paragraph

Two decisions, each brought in plain words and built in parts. First
decision 17 as C2 on `checks`: the runner's rules, written when the
answer was the formatter's whole text, moved case by case toward Part
18 and never past it; one paid run, 8 of 18 against 9; merged. Then
decision 54 on `loop`: `BaseAgent`'s tool-calling loop, which nothing had
called since the graph's nodes began calling the agents' tools
directly, deleted behind the tag `agent-loop-parked` with the task
loop's vocabulary, the settings describing it and the token counter.
1,684 lines under `src/` that no question reached are gone; no live path
changed.

### How I work on this

- **Say the decision in plain words before the yes**, and stop again
  when building finds something the shape did not foresee: the blocks
  every portfolio tool publishes under decision 17, the tracer's price
  under decision 54.
- **A check moves toward its reference and never toward the output.**
- **A deletion is measured before it is brought**: files, lines,
  importers, tests, what each loop loses, and any prompt hidden in it.
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

**pytest: 2060 passed, 6 xfailed.**

**The runner: 8 of 18, 7 failing, 3 blocked** (26 September, 15:43:10
to 15:45:02 UTC, at 22063f6, about $0.14). Predicted 9 of 18. 2.3 moved
to PASS as predicted; 3.3 to BLOCKED against it, the model calling no
tool; 2.1 failed on the client refusing an answer that carried the
figure 48. Decision 54 touched nothing the runner reaches, so no run
followed it.

**The corpus: 33 of 67** (the forty-second session's run, unchanged).

### Branches and tags

`baseline-v1` at **61265ff**, pushed. `loop` carries six commits, to be
merged `--ff-only`. **`agent-loop-parked`** is a local tag at 61265ff,
holding the deleted loop, to be pushed with the branch. The `loop`
worktree has a `data/portfolio.db` symlink, which must go before the
worktree can be removed (§7). `checks` is merged and can be deleted with
`git branch -d checks`.

### Database

`data/portfolio.db`, untracked. Every holding's last stored close is
2026-09-25.

---

## 3. Environment

As the handoff at 41a6d19 gave it, and:

- **CLAUDE.md holds no pending list since 26 September**; the list is in
  §5 here only.
- **In a worktree a heredoc into python ran**, where CLAUDE.md says the
  harness refuses heredoc appends; `git stash list` was refused.
- **A deleted module leaves its `.pyc` in `__pycache__`**; Python 3 does
  not import it without the source, checked with bytecode writing off.

---

## 4. What the forty-fifth session did

**On `checks`, ten commits, merged at 61265ff:**

| Commit | What it is | pytest |
|---|---|---|
| **dcded39** | run_cases: a case names its tool, called once, and allows others; its blocks and agents from its own record; 3.2 one call alone | 4 failed, 2036 passed, then 2040 |
| **3249dae** | run_cases: 2.1 finds its run as one unbroken stretch of the turn's trace | 2 failed, 2041 passed, then 2044 |
| **0fb0dcc** | run_cases: the as-of and the source read from the record's provenance | 4 failed, 2045 passed, then 2049 |
| **a5f46ac** | run_cases: the prose checks of 1.4, 4.2 and 4.4 ask what Part 18 pins | 3 failed, 2049 passed, then 2052 |
| **c153d73** | KNOWN_GAPS: decision 17 taken as the runner's checks | document |
| **22063f6** | benchmark: the runner's prediction after decision 17, 9 of 18 | document |
| **9723c0f** | KNOWN_GAPS: the runner after decision 17, 8 of 18 against 9 | document |
| **dd719c5** | the handoff, regenerated | document |
| **57dbdb0** | KNOWN_GAPS: 3.3's draw called no tool; whether it asked back is not recorded | document |
| **61265ff** | the handoff, regenerated again | document |

**On `loop`, six commits, behind `agent-loop-parked`:**

| Commit | What it is | pytest |
|---|---|---|
| **3657afb** | agents: DataAgent and RebalanceAgent lose BaseAgent, and base_agent.py goes | 5 failed, 2053 passed, then 2058 |
| **0e6ce46** | protocols: the portfolio context alone; the task loop's vocabulary goes | 2 failed, 2058 passed, then 2060 |
| **2cac7b4** | agents/config: AgentSettings goes | 1 failed, 2060 passed, then 2061 |
| **c9da39c** | observability: the token counter goes | 1 failed, 2061 passed, then 2060, two tests deleted |
| **84410af** | KNOWN_GAPS: decision 54 taken, its four entries resolved, two findings logged | document |
| **This commit** | the handoff, regenerated | document |

**Mistakes of this session, recorded:**
- The instruction pointed to "Part 18 in benchmark.md"; it is in
  `expected_values.md`. Said before the shape.
- Three test mistakes under decision 17 and one under 54 were caught
  before their commits: a trace case that was not broken, a 1.1 block
  missing a view, a 1.4 filter catching the cost-basis checks, and two
  trivially true assertions written in place of `.name` in
  `test_all_configs.py`, removed rather than kept.
- A prediction table of the corpus was first read as the run of 24
  September; the CLI was first said not to have run since the layer;
  sixteen matched verdicts were said where there were seventeen; the
  run's entry first said 3.3's draw asked back. Each corrected, the last
  at 57dbdb0.
- Decision 54's entry first counted eight tests added where there were
  ten; corrected before the commit. The first handoff regeneration's
  KNOWN_GAPS counts were wrong; corrected before its commit.
- `max_conversation_history`'s entry placed it on `AgentConfig`; it was
  on `AgentSettings`. Corrected in the entry.

**Resolved, seven:** under decision 17, "The synthesizer returns the
same answer regardless of the question", "`measure` set by the model
under intent compliance is unread" and "The runner's first run through
the layer: 5 of 18 against a prediction of 11"; under decision 54,
"`AgentConfig` fields declared but unenforced", "BaseAgent's tool-calling
loop has no live caller", "`max_conversation_history` is read by nothing"
and "The token counter prices a model it does not know at a default".

**Logged, four, each with a trigger:** "A one-ticker P&L record's
provenance states the earliest close of all nine", "Whether a record's
provenance should carry every date its block states", "1.3's basis
check asks for the covariance method, which Part 18 does not name",
"`_get_prices_from_db` reports any database error as no data".

---

## 5. Decisions taken, and decisions pending

**Taken this session, on the owner's yes:**
- **Decision 17, as C2, in six parts**, with the reading added before
  part 1 that a case reads its blocks from its own tool's record.
- **The paid run**, about $0.14.
- **Decision 54, in six parts**, the token counter included, tagged
  `agent-loop-parked` first.

**Pending — six:** 10, 13, 22, 48, 52 and 76. The cap is 25. None
opened, two closed.

**Surfaced and not numbered:**
- **Deleting the tracer's `CostCalculator`**, which estimates every
  trace's cost at `gpt-4-turbo` rates. Decision 53 said delete behind a
  tag; the trace the runner reads carries the figure, so it is its own
  question. Its entry's trigger waits on it.
- **The German figures**, whether the answer's notation or the check's
  reading of it moves.
- **What the philosophy screen may be asked**, given R-2's pin and 4.6
  screening a held JPM.
- **Whether provenance should carry every date a block states**, logged.

---

## 6. Where we stand against the benchmark

**Runner 8 of 18, corpus 33 of 67.** Every failure the runner shows is
the answer carrying less than Part 18 pins, or no tool called: 1.4's
unsectored share, 2.2's clauses, 4.2's assumptions and dates, 4.4's
readings and proposal, 4.6's pull date, 3.2's and 3.3's missing calls,
and 2.1's refused answer. What remains is the prompt's and the layer's.
Decision 54 moved no figure and no answer.

**What no loop has seen yet:** `rebalance`; a German span question; what
a corpus run costs; a one-figure question through the layer.

---

## 7. Next steps, in order

**1. The branch review and the merge.** The worktree's database link
first, from the VS Code terminal, then the merge, the push of the branch
and of the tag, and the worktree:

```
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE/.claude/worktrees/loop" && rm data/portfolio.db && rmdir data
```
```
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE" && git merge --ff-only loop && git push https://github.com/fatihsenguel/agentic-pm.git baseline-v1 && git push https://github.com/fatihsenguel/agentic-pm.git agent-loop-parked && git fetch origin && git worktree remove .claude/worktrees/loop
```

**2. The tracer's `CostCalculator`**, as its own question, its blast
radius measured: the trace's `total_cost_usd`, `format_summary`'s line,
the export, and what the runner reads from the trace.

**3. The two surfaced questions**, the German figures and the screen's
scope, each a shape before any code.

### Later, with reasons

- **A prompt change**, on the owner's word only: 3.3's missing call,
  2.1's figure of its own, and the prose Part 18 pins, each a hypothesis
  with a prediction first.
- **`_get_prices_from_db`'s swallowed error**, a change to what live
  code raises, on its trigger.
- **The CLI as the client, the README, the demo recordings**, after
  Order 5.
- **The console glyphs**, their own session, fewer than before: the ones in the deleted files went with them.
- **Decision 76**, on the owner's word only. **W-2**, out of scope.

---

## 8. Rules learned the hard way

**Allowing a second call changes what "the block" means.** Find the
reader of every shared key before loosening the rule that made it
unique.

**A test fixture can be a state the code cannot produce.** A new check
that fails a fixture is read against the node before either is changed.

**A prediction table is not a run.** Read the block's heading first.

**A dead class can still be holding up a live one.** `DataAgent`'s
tools called the base class's `log`; the grep for callers of the loop
did not show it, the grep for `self.` in the tools did.

**A deleted test assertion is not replaced by a true one.** When the
attribute an assertion read is gone by design, the assertion goes.

Still true: the handoff at 41a6d19's list, and everything before it.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q          # 2060 passed, 6 xfailed
python tests/benchmark/run_cases.py                # PAYS, about $0.14 a run; ask first
python src/agents/cli.py --portfolio 3             # PAYS per turn; :q to quit
git show golden-parked:tests/golden/run_golden.py  # the parked golden set
git show router-parked:src/agents/smart_router.py  # the parked router
git show agent-loop-parked:src/agents/base_agent.py  # the parked agent loop
```
