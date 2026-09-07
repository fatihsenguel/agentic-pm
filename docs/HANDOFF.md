# AGENTIC_FINANCE — Session Handoff

**Session date:** 8 September 2026 (fifth sitting; the fourth was the evening of 7 September)
**Branch:** `baseline-v1`
**State:** Green, with two pinned failures in the golden set. 132 tests passing at the last code change that touched the graph (the roster registry); the router prompt changed three times after that and pytest was not rerun — rerun it first. Golden set: thirteen queries, clean on two runs against `expected.txt` after the last prompt change. Runner: run it, do not quote it from here. Commit count: `git rev-list --count 270a916..HEAD`.

Written for an LLM assistant picking up cold in a new conversation.

**Regenerate this document at the end of each session rather than patching it.**
Generated context files rot faster than the code they describe. The version this
replaces told the fifth sitting to pull the IPS from `wip/phase7-snapshot`; nobody
had read that branch, and when it was read it was rejected in full (§4). This
version was patched once mid-sitting on the owner's instruction, against its own
rule; the patch is gone in this regeneration.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/benchmark.md` | **The definition of done.** 12 test cases across 3 levels, plus scope boundaries and the output contract. Its Part 2 roster names a "Risk" agent that does not exist as such; which agent plays that role is an open decision (§5). |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Run it before believing anything about what works. Its docstring states what it asserts and what it deliberately does not. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Long, and the most useful file in the repo. Before touching anything read, at minimum: "The agent roster is restated in eight places — RESOLVED", "`wip/phase7-snapshot` was read and rejected", "The router refuses in-scope questions that name a held ticker" (three failed attempts, in full), and "A workbook edit rode into a KNOWN_GAPS commit". |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3: nine decisions (D1–D9), Parts 1–7. **Part 7 is the compliance reference** against `docs/IPS.md`, and it matches the workbook's `Compliance` sheet to the cent. The workbook's `Decisions` sheet lacks D8 and D9; its `C91` "verified by hand on" is blank. |
| `docs/IPS.md` | The Investment Policy Statement, synthetic, for portfolio 3, numbered clauses IPS-1.1 to IPS-6.2. The compliance layer is built against it. A personal IPS replaces it later as a local file without changing code. |
| `docs/PM-Assistant — Roadmap.md` | Phased plan. Carries a header listing superseded points; Phase 3 is superseded (built from the document, not pulled). Its ordering is overridden by §7 below. |

**Do not update `expected_values` to match code output.** If they disagree, one
of the two is wrong and that gets resolved deliberately. The live volatility
figure differs from Part 4's 10.29% because the window has moved; that is the
pin working. Two Part 7 figures are decided by cents (MSFT 12.11% v 12%, JNJ
10.06% v 10%) and will sit on the other side of their limit on a live run; the
reference says so.

---

## 1. Project and owner intent

**AGENTIC_FINANCE** — a multi-agent portfolio management system on LangGraph. Owner: Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public — README is outdated and lies)
**Machine:** MacBook Air, Apple Silicon. Originally developed on Windows; expect Windows-era artifacts.

**History:** 11–28 January 2026 (17 commits), abandoned, resumed 1 September 2026.

### Ultimate goal

A **personal portfolio management and equity research assistant**, driven by the
owner's own Investment Policy Statement. Two halves: a deterministic core
(positions, real computed metrics, IPS rules that block and cite) and an
open-ended half (screening, filings, forming and challenging a thesis), the
boundary between them explicit. The guarantees half is under construction; the
judgement half has not started, deliberately.

There is **no deadline**. Correctness over speed. Scope creep is the live risk
rather than under-delivery.

### Design principles the owner holds

- Strict modularity.
- **Hot potato — agents never see raw data.** Tools return summaries; raw arrays
  move through `shared_data`, never into an LLM context.
- Strict separation of concerns — **policy lives in config, not code**. An
  agent computes, the synthesizer formats; a formatter that does arithmetic is
  a violation.
- **Long-term correctness over short-term working output.** The owner would
  rather leave something broken than encode a wrong model. Repair-instead-of-
  raise is the recurring bug shape. Raise.

### How the owner works

- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting any symbol,
  including lazy imports inside function bodies. **Grep for writers as well as
  readers, and for callers as well as registrations.** Never infer a module's
  purpose or reachability from its name or its registration.
- **Check instructions against the code before acting on them, including the
  owner's and including this file.** The fifth sitting's first instruction was
  to pull three files from a branch; reading them showed the instruction was
  wrong, and correcting five documents was the right response.
- One change per commit. **If the commit message needs an "and", it is two
  commits.** `git status --short` before every `commit -am`: a modified tracked
  binary (the workbook) gets swept in silently (KNOWN_GAPS, 8 September).
- Four loops, run as **separate commands**, never chained with `&&`.
- Patches: `git diff -U0`, downloaded to the repo root, applied by bare filename
  with `git apply --check --unidiff-zero --ignore-whitespace` then without
  `--check`, then committed. New files need `git add` before `git commit -m`.
  After a sitting: `mkdir -p ../patches` and `mv 00*.patch ../patches/`. The
  assistant re-applies every sequence from base and compares trees before
  handing it over, and says which loop can see each change and what it will show.
- Do not paste multi-line blocks containing interactive commands or trailing
  `#` comments into zsh; both get eaten. **A multi-step command block with a
  "stop here" in the middle gets pasted whole** — the fifth sitting's prompt
  fix went in before its pin because the stop was in prose between two blocks.
  Put a stop in its own message, or hand the next block only after the result.

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
instead of asserting, so its seven blocks pass unconditionally. 132 means 132
collected and none errored. The ones that assert against hand-computed figures
are `test_allocation.py` (Parts 2–3), `test_position_pnl.py` (Part 1) and
`test_portfolio_volatility.py` (Part 4). `test_synthesizer_formatters.py` is
the only pytest that touches the synthesizer, two formatters, not the node.
The registry commit added an import-time raise in `graph.py`; under pytest it
would surface at collection of `tests/test_graph_simple.py`, the first file to
import `agents.graph`.

**The golden set has thirteen queries.** Two are pinned failures, not pinned
successes: the macro query has printed `errors: 1` since the first baseline
(KNOWN_GAPS, "The macro path has not produced an answer"), and "How much did
AAPL gain today?" (pid 3) is pinned `out_of_scope` — a known false refusal
after three failed prompt attempts (§4). "Is my AAPL position too big?" (pid 3)
is pinned `clarification_needed`, defensible until there is a policy to judge
size against. Any diff on those lines is news; any diff elsewhere is a regression
or the nondeterminism.

### Branches and tags

`baseline-v1` is the working branch. `wip/phase7-snapshot` holds Compliance/IPS
code that was read on 7 September and rejected in full: a multi-client database
engine with no clause identifiers, six silent defaults, a second arithmetic path
and trade recommendations (KNOWN_GAPS, "`wip/phase7-snapshot` was read and
rejected"). Nothing on it is scheduled; do not read it again for ideas.
`wip/rag-early` and tag `rag-early-parked` hold the deleted RAG code. `master`
(b327e80) has a fuller RAG version with a vector store.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`a7d5e1c04b83`**, 11 migrations, linear chain from `c1e79ae31788`. No
migration this sitting; the next one is `Asset.instrument_type` (§7).

- **Portfolio 3, "Benchmark Portfolio" — use this one.** 9 positions, 4 asset
  classes, 4 sectors, cost basis 284,500 plus 15,500 cash = 300,000 flat.
  Seeded by `src/portfolio_tool/scripts/seed_portfolio.py` (idempotent). The
  two near-miss golden queries run against it, so the golden set now touches
  portfolio 3 for the first time.
- **Portfolio 1, "Demo Portfolio"** — January data; four golden queries run
  against it. **Do not modify or delete it.**
- **Portfolio 2, "Integration Test"** — a leaked test artifact; one golden
  query uses it. Load-bearing by accident.
- **Reseeding portfolio 3 mutates portfolios 1 and 2.** `asset_class` and
  `sector` live on `Asset`, shared across portfolios. `instrument_type` will
  have the same shape.

---

## 3. Environment

- **Python 3.10.21** (Homebrew). `pyproject.toml` pins `>=3.10,<3.11`.
- 88 packages frozen in `baseline-v1-lock.txt`. `asyncio_mode = "auto"`.
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
`.env` contains `sqlite:///./data/portfolio.db`: "relative to the repo", not
"relative to the shell", because SQLite creates a missing file silently.
`alembic.ini:87` and `data_manager.py:25` still carry cwd-relative paths.
Unfixed, deliberately.

### LLM configuration

`src/agents/config.py` is the single source of truth. `ACTIVE_LLM_CONFIG =
ANTHROPIC_HAIKU` (`claude-haiku-4-5-20251001`). **`ANTHROPIC_SONNET` still
points at the Haiku id.** Never guess a model id.

---

## 4. What the fourth and fifth sittings did

`git log --oneline 93da2ff..HEAD` for the list: 29 commits from the previous
handoff to and including this one. By topic:

**The agent roster registry (§7 item 1 of the previous handoff), done.**
`AgentName.ROUTER` deleted first, own commit, no reader. Then `AGENTS` in
`schemas.py`: an ordered dict of name to prompt description; `AgentName` is
derived from it with the functional `Enum` API (validation output checked
identical under `use_enum_values`); `router_prompts.py` assembles the system
prompt from three literal pieces with the roster and its count rendered in
between, **byte-identical** to the hand-written prompt (checked with `diff`);
`graph.py` derives `add_node`, `routing_map` and the loop edges, binds names to
node functions in `AGENT_NODES`, and raises at import if binding and roster
disagree; `route_next_step` returns `str` because LangGraph never reads the
`Literal` when a `path_map` is given (`BranchSpec.from_path`, 1.2.11).
Predicted zero golden diff; observed zero on four runs. The previous
handoff's "expect a golden diff" was corrected in its own commit.

**`wip/phase7-snapshot` read and rejected.** Five documents and one runner
string pointed at it as the IPS source; none had been checked against the
branch. Corrected in six commits, one per document. Decided instead: a prose
IPS with numbered clauses, `ips.toml` derived from it, a closed type
vocabulary with a loader that raises, a pure checker over the allocation block
in `shared_data`, the agent last.

**The IPS and its reference.** `docs/IPS.md` written by the owner (synthetic,
portfolio 3). `expected_values.md` Part 7 computed from Part 1's 09-02 values:
eight breaching findings (IPS-3.1; 4.1 on SPY, AAPL, MSFT; 4.2 on AAPL, MSFT,
JNJ; 4.3 on Technology), two decided by cents. The owner built the workbook's
`Compliance` sheet independently; it agrees on every figure and added three
things the document then adopted: `exempt` as a status, signed distances, and
D9. The assistant wrote "Part 5" into three documents without opening the file
(Part 5 existed); corrected in its own commit.

**Held-ticker false refusal.** Found in the CLI on the evening of 7 September:
"How much did AAPL gain today?" refused at 0.95 with AAPL held. Logged; two
near-miss queries added to the golden set against portfolio 3 and the routing
pinned before any fix. Three prompt attempts followed — a sentence, a rewording,
a few-shot — with six line-level predictions, **six wrong**. Each attempt is
pinned and recorded. Stopped there. The three edits are still in the prompt
(decision pending, §5). Also logged: "last week" → `1Y` is the period rule's
own "nearest valid value" instruction, a repair written into the prompt.

**Two small corrections to loops and records.** The runner's blocked message no
longer points at the rejected branch. KNOWN_GAPS gained: four roster sites the
registry does not read, the dead `prompts.py` module, the unreachable agent
check in `_validate_decision`, and the workbook edit that rode into `22508c9`.

---

## 5. Decisions taken, and decisions pending

**Taken.**
- Registry shape: name → description in `schemas.py`; binding plus import-time
  raise in `graph.py`; not "name to node function" (the schema is a pydantic
  leaf that `smart_router` imports).
- The IPS is built from the owner's document; the wip branch is dead.
- Unnumbered clauses are `statement` entries: citable, not computed, so 3.4
  answers against a visibly full policy.
- IPS-4.1 per instrument, funds included; IPS-4.2 per issuer over directly held
  shares only; no look-through. `Asset.instrument_type` (`share | fund`), set by
  the seed, checker raises when missing — accepted on the strength of the
  sheet's own note.
- D9: exactly at a limit passes; strict, unrounded comparison.
- Sector limits use total value as denominator (IPS), not Part 3's invested;
  both recorded as right for their own question.
- "Is my AAPL position too big?" is a compliance question and gets its next
  routing prediction with the compliance prompt change, not before.
- After three failed prompt edits, no fourth without a diagnostic.

**Pending, owner's call — bring them up before writing any code.**
1. The "Risk" agent 2.1 names: recommended PortfolioAnalysisAgent with a
   `concentration` measure (rejected: a new RiskAgent; RiskManagerAgent).
   benchmark.md Part 2's roster gets corrected when decided.
2. The `shared_data["compliance"]` shape (KNOWN_GAPS, "Status 8 September"
   under the wip entry). The runner checks encode it, so it comes first.
3. The diagnostic golden query "How much has AAPL gained?" (pid 3) — one line,
   no prompt change — to separate "bare ticker" from "today".
4. Keep or revert the three failed prompt edits (6e68c47, d8cd0d6, 31ce272).
   Lean keep, weakly, for the clarification on "too big".
5. The workbook: add D8 and D9 to its `Decisions` sheet, fill `C91`, and commit
   that as its own commit with `git add` — not via `-am`.

---

## 6. Where we stand against the benchmark

Run the runner. At the last run: Level 1 in full; 3.2 and 3.3 pass; 2.1, 2.2,
2.3, 3.1 and 3.4 blocked on "no Compliance agent and no IPS" (the IPS document
now exists; the code does not); 3.5 blocked on conversation memory. The five
compliance cases have hand-computed expected answers in Part 7 and a runner
probe that unblocks on `"ComplianceAgent" in sub_results`; their checks are
unwritten.

---

## 7. Next steps, in order

### 1. Settle pending decisions 1 and 2, then the runner checks

Write `check_2_2`, `check_2_3`, `check_3_1`, `check_3_4` before any capability,
as with 3.2, so each can be seen failing for the right reason. They assert on
structure, not on which clauses breach (two are decided by cents): every
checkable clause has a finding; every finding's clause exists in the loaded
policy; `observed − limit` reconciles with `distance_pp`; status is one of the
closed set; statements have no findings; cited ids reach the answer; no line
matches a trade verb with a ticker (2.3 adds: every breach's distance reaches
the answer, no target weight does; 3.1: a `refused` finding at 0.15 on IPS-4.1
and the id in the answer; 3.4: no findings, a `no_clause` marker, no `IPS-` id
in the answer at all). Own commit. Runner shows five FAILs with reasons instead
of five BLOCKEDs.

### 2. `ips.toml` and the loader

Repo root, derived from `docs/IPS.md`: one entry per clause with `id`, `type`,
parameters, `text`. Types: `statement`, `asset_class_band`,
`max_instrument_weight`, `max_issuer_weight`, `max_sector_weight`, `min_cash`.
The loader raises on any other type and on a checkable type with missing
parameters. pytest: the loaded clause set equals the document's. Policy in
config; the numbers are typed once, here, and cited from `text`.

### 3. `Asset.instrument_type`

One migration, one seed change, the same shared-`Asset` caveat as `sector`.
Own commit. pytest over the seeded DB: no holding of portfolio 3 has it null.

### 4. The checker

Pure functions in `portfolio_tool/` (not `quant/`, which is maths): `check(ips,
allocation_block, position_pnl, instrument_types) -> findings`. Reads
`by_asset_class.lines[].pct_of_denominator`, `by_asset_class.total_value`,
`by_sector.lines[].market_value`, `position_pnl[t].market_value`. One division
per figure, strict unrounded comparison (D9), `exempt` for funds under 4.2.
pytest against Part 7 over the committed closes: eight breaches, four exempt,
distances to the cent. Predict: runner unchanged (no node yet).

### 5. The node, and the roster

`compliance_agent_node`: reads `shared_data`, calls the checker, publishes
`shared_data["compliance"]`. One line in `AGENTS`, one in `AGENT_NODES`; the
raise catches a miss. Wire `trace_tool` and `log_delegation` here; 2.1 cannot
pass without them. Predict: the five probes unblock and the checks fail on
formatting, not on absence.

### 6. Prompt and route — golden twice, predictions written first

A compliance intent enters `IntentType` and the prompt (the intent vocabulary
has the same five-site problem as the roster had; registry treatment as its own
commit first or in the same work, decide). This is where "too big" and "gain
today" get their next prediction, and where the three failed edits get replaced
or kept. Expect movement; predict it line by line.

### 7. The formatter

The synthesizer formats findings and cites clause text from `policy`; no
arithmetic. `OUT_OF_SCOPE_RESPONSE` moves into the IPS as a clause once there
is one to cite. Rebalance targets come from the IPS too (a target-weights
clause), which closes "No target weights".

### Later, with reasons

- **Conversation memory** for 3.5.
- **Intent vocabulary registry**, same shape as the roster's.
- **Delete `prompts.py`**, `build_router_prompt(available_agents=)`,
  `get_graph_mermaid`, the unreachable agent check in `_validate_decision`
  — each its own commit, each after a grep for every re-export.
- **Replace the two verbatim few-shots** (1.1, 1.3).
- **`RouterDecision.validate_execution_order`** repairs; make it raise.
- **The period rule's "nearest valid value"** → `clarification_needed`, with
  the period registry.
- **README rewrite**; `test_portfolio_integration.py`; the inline
  `sqrt(w'Σw)` copies; `IntentType.UNKNOWN`.

---

## 8. Rules learned the hard way

**An instruction is a claim.** The handoff, the roadmap and benchmark.md all
said the IPS comes from a branch; the branch said "UNVERIFIED, do not build on
this" in its own commit message. Read the thing before pulling from it.

**Six for six.** Three prompt edits, six line predictions, all wrong, one in the
opposite direction. A prompt change is a hypothesis; three hypotheses in a row
with no model of the router is chasing. Stop, pin, record, find a diagnostic
that separates the tangled causes, and let the next structural change carry the
next prediction.

**A refusal is an honest failure; a plausible wrong answer is not.** Attempt two
moved a refused position question to a price fetch. On the golden set that
looked like progress. It was a wrong model with a plausible face.

**A check that cannot distinguish two states passes in both.** Still true. The
golden set cannot see `measure`; a right plan with a wrong measure passes it.

**A registry that renders byte-identically is a stronger check than one that
"expects a diff".** Zero diff means any diff is news. Predict zero when zero is
achievable.

**Open the file before citing its section number.** "Part 5" went into three
documents; Part 5 existed.

**`commit -am` stages every modified tracked file**, including a binary you
edited in another application an hour ago. `git status --short` first.

**Two computations that agree are a reference; one is a draft.** Part 7 became
a reference when the owner's sheet matched it to the cent, and the sheet was
better in three places.

**Registration in a tools list is not reachability. Repair-instead-of-raise is
the recurring bug shape. Fields that look like they control something often do
not. Documents rot inside a single session.** All still true; the previous
handoff's §8 has the examples.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 2.2

python src/agents/cli.py --portfolio 3

python src/portfolio_tool/scripts/seed_portfolio.py --show
python src/portfolio_tool/scripts/seed_portfolio.py --reset

python tests/check_imports.py

grep -rn "SymbolName" src/ tests/ --include='*.py'

git apply --check --unidiff-zero --ignore-whitespace 00NN-name.patch
git apply --unidiff-zero --ignore-whitespace 00NN-name.patch
git status --short
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~30s | Do the components still work; does the graph still build |
| CLI | ~4s | What is it actually doing |
| Golden set | ~60s, cents | Did routing change anywhere (thirteen lines, two pinned failures) |
| Benchmark runner | ~1min, cents | How many cases pass |

`golden set → change → golden set → decide whether the diff is an improvement →
then update expected.txt, its own commit`. A prompt change: prediction written
first, golden twice, a line that moves against the prediction is a failed
hypothesis even if the new routing looks defensible. The runner is per
capability commit.
