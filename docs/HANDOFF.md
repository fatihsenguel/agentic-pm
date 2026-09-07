# AGENTIC_FINANCE — Session Handoff

**Session date:** 7 September 2026 (second sitting)
**Branch:** `baseline-v1`
**State:** Green. 127 tests passing, golden set clean on both runs after the last prompt change, `expected.txt` moved once deliberately (the volatility query now plans PortfolioAnalysisAgent). For the benchmark count, run `python tests/benchmark/run_cases.py` — it is not quoted here. For the commit count, `git rev-list --count 270a916..HEAD`; the previous version of this file quoted one and it was off by one.

Written for an LLM assistant picking up cold in a new conversation.

**Regenerate this document at the end of each session rather than patching it.**
Generated context files rot faster than the code they describe. The previous
version of this file carried four wrong figures by the end of one session.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/benchmark.md` | **The definition of done.** 12 test cases across 3 levels, plus scope boundaries and the output contract. Part 3's Level 1 status note is now stale — 1.1 and 1.4 compute correctly; they fail on the output contract. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Run it before believing anything about what works. Its docstring states what it asserts and what it deliberately does not. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Long, and the most useful file in the repo. Read the RESOLVED entries for P&L, portfolio volatility and the router override before touching any of them. |
| `tests/golden/expected_values.md` | Hand-computed expected answers for portfolio 3, plus eight decisions (D1–D8). `expected_values.xlsx` holds the formulas; the 252 closes are also committed as `tests/golden/benchmark_closes.csv`, which two pytest files read. |
| `docs/PM-Assistant — Roadmap.md` | Phased plan. Carries a header listing superseded points. Its ordering is now overridden by §7 below, which follows the counter. |

**Do not update `expected_values` to match code output.** If they disagree, one
of the two is wrong and that gets resolved deliberately. The live volatility
figure (10.40% on 7 September) differs from Part 4's 10.29% because the window
has moved two closes; that is the pin working, not a disagreement.

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

**Caveat on "127 passing":** `test_portfolio_integration.py` returns booleans
instead of asserting, so its seven blocks pass unconditionally, and TEST 7
returns `True` in both branches. 127 means 127 collected and none errored, not
127 things verified. The ones that do assert against hand-computed figures are
`test_allocation.py` (Parts 2–3), `test_position_pnl.py` (Part 1) and
`test_portfolio_volatility.py` (Part 4, over the committed closes, via both
numpy and the system's own `CovarianceEstimator`). Those three are the only
places exact figures are checked; the runner asserts structure, static
figures and invariants, deliberately.

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

**Second sitting of 7 September, from `270a916`.** Two capabilities, one
structural change to the router's output, one code fix that two prompt
patches had been standing in for, and the document sweep. All four loops
green at the end; the runner moved from 2/12 to 5/12 and Level 1 is complete.

**Position P&L, built (roadmap item 3; benchmark 1.2, 3.3).** `position_pnl`
in `quant/allocation.py`, checked against Part 1. PortfolioAnalysisAgent
computes every position on every run and publishes
`shared_data["position_pnl"]` per ticker with a per-position `as_of`. The
handoff's instruction to go through `get_portfolio_summary` was wrong —
nothing called it — and its inline P&L was deleted instead.

**Portfolio volatility, built (roadmap item 4; benchmark 1.3).**
`portfolio_volatility` in `quant/risk_metrics.py`, the optimiser delegating to
it, the 252 closes committed as a fixture, and the node publishing the figure
with its whole basis: window (DataAgent now publishes `price_window` as data),
weights and their date, covariance method, annualisation. The system's own
covariance estimator reproduces the reference on the fixture, so the live
matrix's conventions are tested rather than assumed.

**`measure` and `group_by` on `ExtractedParameters`.** The router now says
which figure a question asks for; the synthesizer dispatches on it; the node
computes everything regardless. This replaced the "sector on
ExtractedParameters" item with the shape the KNOWN_GAPS entry argued for, and
reserved a third axis (`filter`) without building it. Decision record is in
KNOWN_GAPS under the old `group_by` entry.

**The router was overwriting `tickers` with the portfolio after the LLM
call.** A block in `smart_router.py`, no consumer until P&L read the field.
Found only after two prompt changes failed to fix it and one of them regressed
routing and was reverted. The record of those attempts is in KNOWN_GAPS and is
the most useful thing this sitting produced: grep for writers, not just readers.

**Two runner checks were wrong or blind.** `check_3_3` passed once with a
padded `tickers`; it now requires the list empty. The 1.2 check was right from
the start and is what caught the override.

**Document corrections:** D8's stale "the code does not compute this"; the
handoff's `get_portfolio_value` instruction; the roadmap's Phase 1 status;
benchmark.md's Level 1 status note; KNOWN_GAPS's wrong cause for the
nondeterministic ticker order, and its low count of inline volatility
implementations.

---

## 5. Decisions taken this session

**`measure` values are `shared_data` keys.** `allocation`, `position_pnl`,
`portfolio_volatility` — each is the key the node publishes under, so the
router's vocabulary, the synthesizer's dispatch and the runner's probes share
one word. A value with no computation behind it does not go in the Literal.

**The node computes everything; `measure` is a synthesizer signal.** Both
allocations, all nine P&Ls and the portfolio volatility are published on every
run. Selection is the synthesizer's job. `shared_data` grows by summary data
only; the hot-potato violation is `price_data_json` and nothing added today.

**`group_by` narrows rendering, not computation.** Both breakdowns are always
computed; the one asked for is printed. `industry` and `country` stay out of
the enum until something groups by them.

**`tickers` is what the user named, and empty means every position.** The
router prompt says so (rule 2 no longer offers "defaults"), and the code that
made it untrue is gone. `check_1_2` asserts exactly `["JPM"]`; `check_3_3`
asserts exactly `[]`.

**P&L's as-of is per position; volatility's is a window plus a weights date.**
Each has its own accessor in the runner. No search for dates.

**The optimiser delegates `sqrt(w'Σw)` to the canonical function; the
inline copies inside objective functions do not.** They are evaluated on
iterates that do not sum to one, and the canonical function raises on that.
Open decision, recorded.

**The sweep happened before 3.2, not after.** Twenty-two commits and a
finding list this long would have rotted across another capability.

**Not decided, surfaced:** whether few-shot examples may quote benchmark
prompts; whether the fast loop should print `measure` and `group_by`; whether
`get_portfolio_value` is deleted; the ten-ticker cap on the published
covariance matrix.

---

## 6. Where we stand against the benchmark

```bash
python tests/benchmark/run_cases.py
```

The count is deliberately not written down here. What follows is the shape of
the gap.

**Level 1 passes in full.** 1.1 and 1.4 on allocation with the structured
as-of; 1.2 on JPM with `tickers == ["JPM"]`, the purchase date, the P&L figure
and "price return" reaching the prose; 1.3 on the volatility figure with every
basis element reaching the prose and the figure below the weighted average of
the single names; 3.3 on all nine positions with `tickers == []`.

**3.2 fails** on `intent: clarification_needed` where it needs `out_of_scope`.
**2.1, 2.2, 2.3, 3.1 and 3.4 are blocked** on the Compliance agent and the IPS.
**3.5 is blocked** structurally — it needs a second turn.

The architecture is sound. The gap is now entirely Levels 2 and 3.

---

## 7. Next steps, in order

Roadmap Phase 1 is done. Items 1 and 2 below are the "Later" list from the
previous handoff, now at the top. Neither is unblocked by anything left to
build; both are decisions first.

### 1. `out_of_scope` router intent (benchmark 3.2)

A new `IntentType`, a terminal branch in the graph, a synthesizer response
that names the scope boundary, and a prompt change (golden set twice). Not
better wording of `clarification_needed`. Two traps: `generate_taa_signal_tool`
is a live path that returns allocation recommendations and contradicts 3.2 —
resolve it in the same piece of work, not before; and the case has a known
expiry (benchmark.md Part 2), so build the intent for the boundary as it is
now, not for one that admits screening.

Bring the intent's vocabulary and the terminal branch's shape as a decision
before writing, the way `measure` was brought.

### 2. The IPS from `wip/phase7-snapshot` (2.1–2.3, 3.1, 3.4)

`ips_manager.py`, `esg_screener.py`, `compliance_agent.py`, one file at a
time, expecting stale imports and renamed config fields. Structured rules
with clause identifiers, checked deterministically — not retrieval
(benchmark.md Part 1). Wire `trace_tool` and `log_delegation` at the same
time; 2.1 cannot pass without them. Rebalance targets come from here too.

The seventh agent triggers the roster-registry entry in KNOWN_GAPS — eight
sites, and the eighth was missed last time. Do the registry first, as its own
commit, expecting a golden diff that must be judged on routing rather than on
prompt text.

### Later, with reasons

- **Conversation memory** for 3.5. `AgentState.messages` and
  `build_router_prompt(conversation_history=...)` exist and are never
  populated. The runner sends one query per case and will need a second turn.
- **`filter` on `ExtractedParameters`** when a question restricts P&L by
  sector. The slot is reserved; nothing is built.
- **README rewrite.** Keep its Design Principles section and the one true
  sentence about RiskManagerAgent.
- **`test_portfolio_integration.py`** and the five other unguarded files.
- **The inline `sqrt(w'Σw)` copies** in optimiser objectives — decide
  whether a non-validating core exists or they stay scoped.

---

## 8. Rules learned the hard way

**Every instrument has a blind spot, and they do not overlap.** `run_golden.py`
prints five routing fields and no answer content. `pytest` passes on tests that
never assert, and collects nothing that exercises `synthesizer_node` — both
synthesizer commits this session were invisible to it. The CLI was the only thing
that could see them. The benchmark runner is the fourth loop and the first that
scores cases.

**A prompt change is a specification change, and it must be measured.** Run the
golden set twice — a case that only works most of the time counts as failed.

**Fields that look like they control something often do not.** `model_name`,
`ANTHROPIC_SONNET`, `log_tool_calls`, `max_tool_calls_per_turn`,
`hawkish_threshold`, `result_type`, and now `nodes.py`'s `"3Y"` period default,
which is both a duplicate of config and unreachable. Grep before believing any of
them.

**The recurring bug shape is repair-instead-of-raise.** A wrong answer with a
plausible face rather than an error. This session added two: a volatility figure
with no stated window, and `cash_balance` defaulting to 0.0 so that D2's
"absent is not zero" rule cannot fire.

**Capability exists, wiring does not.** `conversation_history`, `ToolTrace`,
`log_delegation`, the `confidence` / `reasoning` / `warnings` fields on
`PortfolioResult` — and the price frame's date range and observation count, which
were computed on every request and discarded until this session.

**Documents rot inside a single session.** The previous handoff was written on
4 September and by the end of the same day carried a wrong migration count, wrong
line numbers in four places, a wrong claim about portfolio 2, and a wrong
"14 assertions" figure. The one before this carried a wrong commit count, a
wrong instruction for the next task, and its §0 pointed at a document whose D8
cell contradicted itself. Prefer symbol names to line numbers, and regenerate.

**A prompt change is a hypothesis, not an edit.** Two of the three prompt
patches on 7 September were predicted to change router behaviour and did not,
because the behaviour was set in code after the prompt ran. Read everything
between the LLM call and the state before attributing anything to the model,
and treat "the prompt now says X" as a claim the runner tests.

**A check that cannot distinguish two states passes in both.** `check_3_3`
verified nine positions and their dates and passed while the router had
padded `tickers` to all nine — because the formatter prints all nine either
way. When a case's answer looks the same under the bug and under the fix,
assert on the input that differs.

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
