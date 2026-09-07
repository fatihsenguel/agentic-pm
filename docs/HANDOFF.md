# AGENTIC_FINANCE — Session Handoff

**Session date:** 7 September 2026 (third sitting)
**Branch:** `baseline-v1`
**State:** Green. 132 tests passing, golden set clean on two runs after the last prompt change, `expected.txt` moved once deliberately (an eleventh query, benchmark 3.2's prompt, routes `out_of_scope`). For the benchmark count, run `python tests/benchmark/run_cases.py` — it is not quoted here. For the commit count, `git rev-list --count 270a916..HEAD`.

Written for an LLM assistant picking up cold in a new conversation.

**Regenerate this document at the end of each session rather than patching it.**
Generated context files rot faster than the code they describe. The version
this replaces was written at the end of the second sitting and by the start of
the third asserted that a tool was a live path without a grep — the rule
against doing that is in its own §8.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/benchmark.md` | **The definition of done.** 12 test cases across 3 levels, plus scope boundaries and the output contract. Part 2's Levels 1–3 boundary is now drawn at security selection versus portfolio mechanics (7 September, third sitting). |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Run it before believing anything about what works. Its docstring states what it asserts and what it deliberately does not. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Long, and the most useful file in the repo. Read the RESOLVED entries for P&L, portfolio volatility and the router override, and the third-sitting entries on the `out_of_scope` prompt and the CLI blind spot, before touching any of them. |
| `tests/golden/expected_values.md` | Hand-computed expected answers for portfolio 3, plus eight decisions (D1–D8). `expected_values.xlsx` holds the formulas; the 252 closes are also committed as `tests/golden/benchmark_closes.csv`, which two pytest files read. |
| `docs/PM-Assistant — Roadmap.md` | Phased plan. Carries a header listing superseded points. Its ordering is overridden by §7 below, which follows the counter. |

**Do not update `expected_values` to match code output.** If they disagree, one
of the two is wrong and that gets resolved deliberately. The live volatility
figure differs from Part 4's 10.29% because the window has moved; that is the
pin working, not a disagreement.

---

## 1. Project and owner intent

**AGENTIC_FINANCE** — a multi-agent portfolio management system on LangGraph. Owner: Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public — README is outdated and lies)
**Machine:** MacBook Air, Apple Silicon. Originally developed on Windows; expect Windows-era artifacts.

**History:** 11–28 January 2026 (17 commits), abandoned, resumed 1 September 2026.

### Ultimate goal

A **personal portfolio management and equity research assistant**, driven by the
owner's own Investment Policy Statement. The goal explicitly includes
**screening and stock picking**. That is out of scope by phase, not permanently.

There is **no deadline**. Correctness over speed. Scope creep is the live risk
rather than under-delivery.

### Design principles the owner holds

- Strict modularity.
- **Hot potato — agents never see raw data.** Tools return summaries; raw arrays
  move through `shared_data`, never into an LLM context.
- Strict separation of concerns — **policy lives in config, not code**.
- **Long-term correctness over short-term working output.** The owner would
  rather leave something broken than encode a wrong model. Honour this.

### How the owner works

- `grep -rn "Name" src/ tests/` before deleting any symbol, including lazy
  imports inside function bodies. **Grep for writers as well as readers**
  before reasoning about where a value comes from — two prompt changes and a
  reverted commit on 7 September were built against an unread line of code
  that overwrote the value after the prompt was done.
- Never infer a module's purpose or dependencies from its name.
- One change per commit. **If the commit message needs an "and", it is two
  commits.**
- Verify with `pytest` and the golden set as **separate commands** — not chained
  with `&&`, which hides failures.
- Do not paste multi-line blocks containing interactive commands or trailing `#`
  comments into zsh; both get eaten. Patches: `git diff -U0` and
  `git apply --unidiff-zero --ignore-whitespace`, with `--check` first —
  without `--ignore-whitespace`, a patch removing an indented blank line fails
  on the owner's machine. Every patch comes with its apply and commit
  commands. Note `git commit -am` does not stage a new file.

### What the owner does NOT want

A pure asyncio/regex deterministic version without LangGraph.

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q

python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt

python tests/benchmark/run_cases.py

python src/agents/cli.py --portfolio 3
```

**Caveat on "132 passing":** `test_portfolio_integration.py` returns booleans
instead of asserting, so its seven blocks pass unconditionally, and TEST 7
returns `True` in both branches. 132 means 132 collected and none errored, not
132 things verified. The ones that assert against hand-computed figures are
`test_allocation.py` (Parts 2–3), `test_position_pnl.py` (Part 1) and
`test_portfolio_volatility.py` (Part 4). `test_synthesizer_formatters.py`
(new, third sitting) is the only pytest that touches the synthesizer, and it
touches two formatters, not the node. The runner asserts structure, static
figures and invariants, deliberately.

**The golden set has eleven queries.** The eleventh is benchmark 3.2's prompt
against portfolio 1 and prints `intent: out_of_scope`, `plan: []`. The macro
query has printed `errors: 1` since the first baseline; that is a pinned
failure, not a pinned success (KNOWN_GAPS, "The macro path has not produced an
answer").

### Branches and tags

`baseline-v1` is the working branch. `wip/phase7-snapshot` holds Compliance/IPS
code to pull forward (`ips_manager.py`, `esg_screener.py`,
`compliance_agent.py`). `wip/rag-early` and tag `rag-early-parked` hold the
deleted RAG code. `master` (b327e80) has a fuller RAG version with a vector
store. Tags on the remote: `baseline-v1-clean`, `baseline-v1-green`,
`rag-early-parked`.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`a7d5e1c04b83`**, 11 migrations, linear chain from `c1e79ae31788`.

- **Portfolio 3, "Benchmark Portfolio" — use this one.** 9 positions, 4 asset
  classes, 4 sectors, cost basis 284,500 plus 15,500 cash = 300,000 flat.
  Seeded by `src/portfolio_tool/scripts/seed_portfolio.py` (idempotent).
- **Portfolio 1, "Demo Portfolio"** — January data. `run_golden.py` runs four of
  its ten queries against it (`QUERIES` lines 20–23), so **do not modify or
  delete it** or the baseline breaks.
- **Portfolio 2, "Integration Test"** — a leaked test artifact, AAPL 10 @ 150 and
  MSFT 5 @ 350, left behind by a run that returned early before its
  `delete_portfolio`. `run_golden.py`'s line 24 uses it for the Technology-sector
  query, so it is load-bearing by accident.
- **Reseeding portfolio 3 mutates portfolios 1 and 2.** `asset_class` and
  `sector` live on `Asset`, which is shared across portfolios, and the seed
  always rewrites that metadata. Both now report asset classes they did not have
  on 3 September. Recorded in KNOWN_GAPS.
- **No golden query runs against portfolio 3.** The fast loop cannot see a
  regression in any figure the benchmark scores. That is the runner's job.

---

## 3. Environment

- **Python 3.10.21** (Homebrew). `pyproject.toml` pins `>=3.10,<3.11`.
- 88 packages frozen in `baseline-v1-lock.txt`. `asyncio_mode = "auto"`, so the
  async tests do run.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never
  `from src.…`.

`.env` holds `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and is
gitignored.

- **OpenAI: no credits** (429). Do not route there.
- **Anthropic: working.** Must be a **workspace-scoped** key.

### Database URL

`config.py` owns it via `DatabaseConfig`, calls `load_dotenv()` itself, and
`resolve_database_url` anchors a **relative** SQLite path to the project root.
`.env` contains `sqlite:///./data/portfolio.db`, so that means "relative to the
repo", not "relative to the shell" — deliberately the opposite of shell
intuition, because SQLite creates a missing file silently.

`alembic.ini:87` and `data_manager.py:25` both still carry their own cwd-relative
paths. Unfixed, deliberately.

### LLM configuration

`src/agents/config.py` is the single source of truth. `ACTIVE_LLM_CONFIG =
ANTHROPIC_HAIKU` (`claude-haiku-4-5-20251001`).

**`ANTHROPIC_SONNET` still points at the Haiku id** — a placeholder that would
silently give Haiku if selected. Never guess a model id; check
`GET https://api.anthropic.com/v1/models`.

---

## 4. What this session did

**Third sitting of 7 September, from `b732c25`.** One capability (benchmark
3.2), one document boundary redrawn, three cuts to a recommendation surface,
one formatter test, and the sweep. All four loops green at the end; the runner
moved from 5/12 to 6/12.

**`out_of_scope` intent, built (benchmark 3.2).** `IntentType.OUT_OF_SCOPE`
with a validator that raises on a non-empty plan; the synthesizer emits a fixed
`OUT_OF_SCOPE_RESPONSE` for it; the router prompt defines it against
`clarification_needed` with one German refusal example on a different
instrument. No graph change: an empty plan already flows Router → synthesizer
→ END. `check_3_2` asserts intent, empty plan, no agents run, and that the
boundary sentence reaches the answer, and was strengthened *before* the
capability so it could be seen failing for the right reasons.

**The first prompt wording moved a golden line, deterministically.** "Should
I rebalance my portfolio?" went to `clarification_needed` on both runs under
the first definition ("rebalancing trades to a target" plus "ambiguity wins
over refusal"). Fixed in its own commit by naming the query as in-scope
mechanics. The prediction for that patch was "ten existing lines unchanged";
it was wrong. Record in KNOWN_GAPS.

**benchmark.md Part 2 redrawn.** "Buy or sell recommendations on instruments
the owner has not named" contradicted 3.2 (Nvidia is named) and, corrected to
"held or not", would have put 2.3's rebalance-to-compliance out of scope. The
line is now security selection (out) versus portfolio mechanics on what is
held (in). Regime-driven tactical adjustments were added to the permanent
forecast bullet.

**The recommendation surface cut, in three commits after 3.2.** The macro
formatter's `**Recommendation:** Adjust equity by ±X%` line; the rebalance
formatter's Tactical Signal line; the "mehr in Bonds" example in all three
places it appeared in the router prompt. `generate_taa_signal_tool` was not
the live path — it is registered in a tools list nobody calls — and the
handoff that said it was is the one this replaces.

**Rule 6 of the router prompt moved** from after EXAMPLES, where it sat
numbered 6 with no list around it, to under CRITICAL RULES. Zero golden diff,
which is the expected result and says nothing about the hypothesis that its
placement was why it lost to rule 2 (KNOWN_GAPS).

**Document corrections:** handoff §7.1 (no terminal branch needed; wrong tool
named); the KNOWN_GAPS TAA entry (rewritten around `equity_adjustment`); the
hot-potato entry's heading (67KB was the January figure; 162KB is current);
the date on every entry written this sitting, which was first recorded as
8 September.

## 5. Decisions taken this session

**`out_of_scope` plans nothing and the synthesizer writes the refusal.** The
text is a constant next to the formatter, not config: it is prose about the
boundary, not a parameter anyone tunes. Its eventual home is a clause in the
IPS, cited like any other; coupling 3.2 to the IPS now was rejected as scope
creep. No `scope_reason` field: nothing consumes it.

**Few-shots may not quote benchmark prompts verbatim.** A benchmark prompt in
the golden set is a test; in a few-shot it is the router passing by
recognition. The two existing verbatim examples (1.1, 1.3) get replaced in
their own commit, later. The `out_of_scope` fix does quote a *golden* query
verbatim inside the definition text — same problem one level down, left in
because it is the phrasing that flipped, recorded.

**`IntentType.UNKNOWN` stays for now.** No reader; safe to delete; not
deleted alongside adding an intent, because that is two vocabulary changes
with one case behind them.

**`taa_signal` stays on the rebalance result.** Its formatter line went;
removing the field is a RebalanceAgent change and MacroAgent is tolerated,
not targeted.

**The scope boundary is selection versus mechanics.** Rebalance trade lists
and 2.3 are in; whether to own a security is out; regime-driven allocation
shifts are permanently out as forecasts.

## 6. Where we stand against the benchmark

```bash
python tests/benchmark/run_cases.py
```

The count is deliberately not written down here. What follows is the shape of
the gap.

**Level 1 passes in full.** As before: 1.1 and 1.4 on allocation with the
structured as-of; 1.2 on JPM with `tickers == ["JPM"]`; 1.3 on the volatility
figure with its basis; 3.3 on all nine positions with `tickers == []`.

**3.2 passes** on `intent: out_of_scope`, empty plan, no agents run, and the
boundary sentence in the answer. It has a known expiry (benchmark.md Part 2);
when the boundary moves it gets rewritten, not relaxed.

**2.1, 2.2, 2.3, 3.1 and 3.4 are blocked** on the Compliance agent and the
IPS. **3.5 is blocked** structurally — it needs a second turn.

The gap is now entirely the IPS and conversation memory.

---

## 7. Next steps, in order

### 1. The agent roster registry, as its own commit

Before the seventh agent. KNOWN_GAPS "The agent roster is restated in eight
places" has the list; site 8 (`AgentName` in `schemas.py`) is the one missed
last time. Derive prompt roster, `Literal`, `add_node`, `routing_map`,
`agent_nodes` and the enum from one mapping. Expect a golden diff because the
rendered prompt text changes even if the roster does not; judge it on whether
routing moved, not on the prompt string. Golden set twice.

The intent vocabulary has the same problem in five places (KNOWN_GAPS). Not
the same commit.

### 2. The IPS from `wip/phase7-snapshot` (2.1–2.3, 3.1, 3.4)

`ips_manager.py`, `esg_screener.py`, `compliance_agent.py`, one file at a
time, expecting stale imports and renamed config fields. Structured rules
with clause identifiers, checked deterministically — not retrieval
(benchmark.md Part 1). Wire `trace_tool` and `log_delegation` at the same
time; 2.1 cannot pass without them. Rebalance targets come from here too,
which also closes the standing "No target weights" error on the golden
rebalance query. The `OUT_OF_SCOPE_RESPONSE` constant moves into the IPS as
a clause when there is one to cite.

The runner's blocked probes for these cases unblock on `"ComplianceAgent" in
sub_results`; their checks are unwritten and will report FAIL saying so until
written. Write each check before its capability, as with 3.2.

### Later, with reasons

- **Conversation memory** for 3.5. `AgentState.messages` and
  `build_router_prompt(conversation_history=...)` exist and are never
  populated. The runner sends one query per case and will need a second turn.
  When built, consider moving clarification's exit onto the intent rather
  than the `final_response` proxy (KNOWN_GAPS).
- **Replace the two verbatim few-shots** (1.1, 1.3) with paraphrases; the
  runner shows whether the cases survive without recognition.
- **`RouterDecision.validate_execution_order`** repairs instead of raising.
  Make it raise once the golden set has shown how often it fires.
- **`filter` on `ExtractedParameters`** when a question restricts P&L by
  sector. The slot is reserved; nothing is built.
- **README rewrite.** Keep its Design Principles section and the one true
  sentence about RiskManagerAgent.
- **`test_portfolio_integration.py`** and the five other unguarded files.
- **The inline `sqrt(w'Σw)` copies** in optimiser objectives.
- **`IntentType.UNKNOWN`**, deletion, own commit.

---

## 8. Rules learned the hard way

**Registration in a tools list is not reachability.** `generate_taa_signal_tool`
is in MacroAgent's `get_tools()` and no node calls it; the BaseAgent
tool-calling loop has no caller from the graph. The previous handoff said it
was a live path, and the assistant that read it repeated the claim before
grepping. Grep for the caller, not the registration.

**A check that cannot distinguish two states passes in both — including a
CLI check.** Two formatter lines were deleted and the instruction was to
confirm in the CLI. Both live paths errored before the branch, so the answer
was a bare header with and without the deletion. The formatter test exists
because of this. Before proposing "check it in the CLI", read the guard above
the changed line.

**A prompt change is a hypothesis, not an edit.** Two prompt predictions this
sitting, one wrong: the first `out_of_scope` definition moved a golden line
that was predicted to hold, on both runs. Same rate as the second sitting.

**Every instrument has a blind spot, and they do not overlap.** `run_golden.py`
prints five routing fields and no answer content. `pytest` passes on tests
that never assert and, until this sitting, collected nothing in the
synthesizer; it still collects nothing that exercises `synthesizer_node`. The
CLI shows the answer but cannot show `measure` or `group_by`. The runner is
the first loop that scores cases.

**Fields that look like they control something often do not.** `model_name`,
`ANTHROPIC_SONNET`, `log_tool_calls`, `max_tool_calls_per_turn`,
`hawkish_threshold`, `result_type`, `nodes.py`'s `"3Y"` literal, and
`IntentType.UNKNOWN`. Grep before believing any of them.

**The recurring bug shape is repair-instead-of-raise.** Two more named this
sitting: `validate_execution_order` rewriting the plan, and every router
exception becoming a clarification with confidence 0.0.

**Documents rot inside a single session.** This file's predecessor was written
at the end of the second sitting and carried a wrong reachability claim by
the start of the third. Entries written this sitting were dated 8 September
for most of it. Prefer symbol names to line numbers, and regenerate.

**One change per commit means one change per patch, too.** An amend without
`-a` swept a template rewrite into the next commit; caught on export because
the patch sequence was re-applied from base and compared. Re-apply from base
before handing patches over.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 1.1

python src/agents/cli.py --portfolio 3

python src/portfolio_tool/scripts/seed_portfolio.py --show
python src/portfolio_tool/scripts/seed_portfolio.py --reset

python tests/check_imports.py

grep -rn "SymbolName" src/ tests/ --include='*.py'
```

Note zsh eats `--include=*.py` unquoted, and swallows `#` comments pasted on
command lines. Apply patches with
`git apply --unidiff-zero --ignore-whitespace <file>` after `--check`; new
files need `git add` before `git commit -m`.

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~30s | Do the components still work |
| CLI | ~4s | What is it actually doing |
| Golden set | ~40s, cents | Did routing change anywhere |
| Benchmark runner | ~1min, cents | How many cases pass |

`golden set → change → golden set → decide whether the diff is an improvement
→ then update `expected.txt``. The runner is per capability commit, not per
change: from here, every capability commit is expected to move the counter, and
"done" for a roadmap item means its case asserts rather than that its arithmetic
is right.
