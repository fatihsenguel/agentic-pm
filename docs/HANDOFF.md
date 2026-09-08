# AGENTIC_FINANCE — Session Handoff

**Session date:** 8 September 2026 (sixth sitting; the fifth was earlier the same day)
**Branch:** `compliance`, cut from `baseline-v1` at the fifth sitting's handoff (afdc344). Not merged. The owner merges.
**State:** Green. 220 tests passing at the last code change. Golden set: fifteen queries, clean on two consecutive runs against `expected.txt` after the last prompt change; three lines pin failures (below). Runner: **10/12** at the last run — 2.3 blocked on routing, 3.5 blocked on conversation memory. Commit count this sitting: `git rev-list --count afdc344..HEAD` = 29.

Written for an LLM assistant picking up cold in a new conversation.

**Regenerate this document at the end of each session rather than patching it.**
Generated context files rot faster than the code they describe. The version this
replaces said the agent layer of tracing was done (§4: it was done inside the
router only) and that the "Risk" agent was an open decision (§5: taken). Check
every claim here against the code before acting on it.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/benchmark.md` | **The definition of done.** 12 cases across 3 levels. Part 2's roster now maps roles to nodes; Part 4's tracing sentence was corrected this sitting. |
| `tests/benchmark/run_cases.py` | **The scoreboard.** Every case but 3.5 has a check now. Its docstring says what it asserts and what it deliberately does not; the compliance checks assert structure, never which clauses breach. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Read at minimum: "`wip/phase7-snapshot` was read and rejected" (its Status and Built paragraphs are this sitting's record), "`trace_tool` and `log_delegation` are never called — RESOLVED" (the span bug), "`RouterDecision.validate_execution_order` repairs" (the next structural change), and the two entries under Hygiene on "Is my AAPL position too big?" and on 2.3. |
| `tests/golden/expected_values.md` | Hand-computed reference for portfolio 3, Parts 1–7. Part 7 is the compliance reference; `tests/test_compliance.py` reproduces it to the cent. **Never update it to match code output.** |
| `docs/IPS.md` | The owner's policy, synthetic, IPS-1.1 to IPS-6.2. `ips.toml` is derived from it and `tests/test_ips.py` holds the two together. Do not edit `docs/IPS.md`. |
| `docs/PM-Assistant — Roadmap.md` | Phased plan, stale in places, with a header listing what is superseded. §7 below overrides its ordering. |

Two Part 7 figures are decided by cents (MSFT 12.11% v 12%, JNJ 10.06% v 10%) and sit wherever the day's closes put them; the runner asserts structure and does not care. The live `as_of` was 2026-09-04 at the last run.

---

## 1. Project and owner intent

**AGENTIC_FINANCE** — a multi-agent portfolio management system on LangGraph. Owner: Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public — README is outdated and lies)
**Machine:** MacBook Air, Apple Silicon.

### Ultimate goal

A **personal portfolio management and equity research assistant**, driven by the
owner's own Investment Policy Statement. Two halves: a deterministic core
(positions, real computed metrics, IPS rules that block and cite) and an
open-ended half (screening, filings, forming and challenging a thesis), the
boundary between them explicit. The guarantees half now checks a portfolio
against the policy and cites clauses; the judgement half has not started,
deliberately. **No deadline. Correctness over speed. Scope creep is the risk.**

### Design principles the owner holds

- Strict modularity.
- **Hot potato — agents never see raw data.** Tools return summaries; raw arrays
  move through `shared_data`, never into an LLM context. The compliance block
  carries findings and the owner's clause text; the trace carries counts.
- **Policy lives in config, not code.** `ips.toml` holds every number and every
  topic word; the checker holds none. An agent computes; the synthesizer
  formats; a formatter doing arithmetic is a bug — `test_compliance_formatter.py`
  holds every percentage in the compliance prose to a published finding.
- **Long-term correctness over working output.** Raise rather than repair. The
  checker raises on an unknown instrument type, a class label with no line, a
  fund inside a sector; the loader raises on a type it cannot check; the node
  raises on missing inputs. A plausible wrong answer is worse than a refusal —
  this sitting produced one (3.4 citing IPS-2.1 for currency) and redesigned
  the lookup so it cannot recur.

### How the owner works

- `grep -rn "Name" src/ tests/ --include='*.py'` before deleting any symbol.
  **Grep for the caller, not the registration.** Two of this sitting's own
  commits wired tracing that was unreachable until a third fixed the span.
- **Check instructions against the code before acting on them, including the
  owner's and including this file.**
- One change per commit; a commit message needing "and" is two commits.
  Never `commit -a`/`-am`, never `add -A`/`.`; name the files; `git status
  --short` before every commit. `git diff` and a yes before every commit.
- Four loops, run as **separate commands**, never chained. Golden and runner
  cost money: ask before running either.
- **A prompt change is a hypothesis.** Line-by-line prediction in the commit
  message before the run; golden twice; a line moving against the prediction
  is a failed hypothesis even if the new routing looks defensible. **After the
  second failed prediction on a line, stop:** pin, record, propose a
  diagnostic. This sitting stopped twice under that rule (§4).
- When a step needs the owner's result, ask for it and stop; never hand the
  next block in the same message.
- Never edit `.gitignore`; never run Alembic or reseed without being asked;
  never push, rebase, amend, reset, stash.

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
python tests/benchmark/run_cases.py --case 2.3

python src/agents/cli.py --portfolio 3
```

**220 passed.** The caveat stands: `test_portfolio_integration.py` returns
booleans and passes unconditionally. New this sitting, all asserting:
`test_ips.py` (27: the TOML held to the document, topics, the loader's
raises), `test_instrument_type.py` (3, over the seeded DB), `test_holdings_summary.py`
(3), `test_compliance.py` (26: Part 7 to the cent, D9, the raises, `refuse`),
`test_compliance_node.py` (10: the block, the three modes), `test_handover_trace.py`
(3), `test_request_span.py` (1, the router leaves the request open),
`test_router_prompt.py` (4, the prompt held to its registries, and the
vocabulary NOT shown to the router), `test_compliance_formatter.py` (5, the
prose held to the runner's rules), plus validator tests in
`test_smart_router.py`. Nothing yet exercises `synthesizer_node` itself.

**The golden set has fifteen queries.** Pinned failures, three: the macro
query (`errors: 1`, since the first baseline); "How much did AAPL gain today?"
(pid 3, `out_of_scope`, the false refusal, untouched this sitting); "Should I
rebalance my portfolio?" (`errors: 1`, no target source). Pinned this sitting,
all to `compliance` with the three-agent plan: "Is my AAPL position too big?"
(known to flip to `risk_analysis` / `[PortfolioAnalysisAgent]` / errors 1 on
some runs — KNOWN_GAPS), "Is my AAPL position within my policy's limits?"
(stable), "Is AAPL too concentrated?" (stable after 13d3364, unpredicted). Any
diff on those lines is the known behaviour; any diff elsewhere is a regression
or the nondeterminism.

### Branches and tags

`compliance` is this sitting's branch, 29 commits on `baseline-v1`. `wip/phase7-snapshot`
holds rejected Compliance/IPS code; nothing on it is scheduled, do not read it
for ideas. `wip/rag-early` and tag `rag-early-parked` hold the deleted RAG code.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`05034c6316c8`** (`add instrument_type to assets`), 12 migrations, linear.
Applied and reseeded this sitting by the owner; every held asset in every
portfolio carries `instrument_type` (`share | fund`).

- **Portfolio 3, "Benchmark Portfolio" — use this one.** 9 positions, cost
  basis 284,500 plus 15,500 cash. Seeded by `seed_portfolio.py` (idempotent,
  `--reset` wipes holdings first). Five golden queries run against it.
- **Portfolio 1** — January data; four golden queries. Do not modify.
- **Portfolio 2** — a leaked test artifact; one golden query. Load-bearing.
- **Reseeding portfolio 3 rewrites `Asset` metadata shared with 1 and 2**,
  now including `instrument_type`.

---

## 3. Environment

- Python 3.10.21, `.venv`. `pyproject.toml` pins `>=3.10,<3.11`. `asyncio_mode = "auto"`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never `from src.…`.
- `.env` holds `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`. Never read or print it.
- **OpenAI: no credits.** **Anthropic: working**, workspace-scoped key.
  `ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU` (`claude-haiku-4-5-20251001`).
  `ANTHROPIC_SONNET` still points at the Haiku id.
- `config.py` owns the database URL and anchors a relative SQLite path to the
  project root. `ips.py` anchors `ips.toml` the same way. `alembic.ini` and
  `data_manager.py` still carry cwd-relative paths; `data_manager.load_config`
  is the repair-on-missing-file shape and was deliberately not copied.
- `portfolio_tool/__init__.py` opens a DB connection at import; anything
  importing `portfolio_tool.ips` or `.compliance` pays that. The router prompt
  therefore does not import them at module level.

---

## 4. What the sixth sitting did

`git log --oneline afdc344..HEAD` for the list, 29 commits. By topic:

**The two pending decisions, taken.** Risk is PortfolioAnalysisAgent; the
`concentration` measure deferred with a stated trigger. The
`shared_data["compliance"]` shape accepted with six changes checked against
the block `nodes.py` actually publishes — `total_value` added (every Part 7
distance reproduces as `observed_value − limit × total`), units pinned, `as_of`
copied not reduced, `no_clause` set by the node, two findings per band,
`exempt` with no arithmetic — plus `topic` later. IPS-4.3 must divide
`by_sector.lines[].market_value` by `by_asset_class.total_value`; both
percentages the sector line carries are wrong for it and both are plausible.

**§7 items 1–7, in order, each its own commit.** Four runner checks written
first and seen failing offline for their reasons; `ips.toml` and its loader;
`Asset.instrument_type` (migration, seed, projection); the checker (Part 7 to
the cent, 26 tests); the node with `trace_tool`; the roster line (golden
prediction held, thirteen lines, two runs); the hand-over trace in
`mark_agent_complete`; `check_2_1` reading the stored trace; the compliance
intent with `hypothetical_weight` and `policy_topic`, three plan shapes
enforced by `validate_compliance`; the formatter. Runner 6/12 → 10/12 on the
formatter commit, as predicted.

**The request span.** Found while writing `check_2_1`: the router node opened
the request trace and closed it in its own `finally`, so no agent after it
ever had a trace context on a live run — the agent layer of tracing was done
inside the router only, and two documents said otherwise. `run_agent_graph`
now owns the span. Two of this sitting's own commit messages had claimed the
CLI would show the new events; corrected in KNOWN_GAPS, not rewritten.

**The topic vocabulary, designed twice.** First as a closed set rendered into
the router prompt for the model to pick from: on the live run the router
mapped "currency risk" onto `instruments` and the node cited IPS-2.1 — the
exact nearest-neighbour failure Part 7 names. Redesigned: the router is never
shown the vocabulary, `policy_topic` is the user's own words verbatim, and the
node matches by whole-word containment of the owner's topic words inside the
user's words. The error it can make is a miss, closed by adding a word in
`ips.toml`; never a clause cited for a topic it is not about. 3.4 passes.

**Two stops under the two-failures rule.** "Is my AAPL position too big?"
moved as predicted on run 1 and flipped to an unrunnable plan on run 2 — the
line's fourth failed prediction; pinned to the designed routing, cause named
(rule 6 "concentration → risk_analysis, DataAgent alone" against rule 7 "too
big → compliance"), two diagnostic golden queries added, no rewording. 2.3 was
predicted to route to ComplianceAgent on the roster line and again on the
intent; it did neither; stopped. The diagnostics showed the policy word routes
deterministically and the concentration word never plans a runnable order —
which is a validator gap, not a wording (§7 item 1).

**Corrections to documents:** benchmark.md (roster roles, Level 2 status,
the tracing claim); the runner's blocked reason ("no Compliance agent" was
false after f7ad273; it now prints the intent and plan the router produced);
KNOWN_GAPS swept.

---

## 5. Decisions taken, and decisions pending

**Taken this sitting.**
- Risk = PortfolioAnalysisAgent. `concentration` measure deferred; trigger: a
  concentration question with no policy attached.
- The compliance block: seven keys, four statuses, one finding per (clause,
  subject, bound), `total_value` and `as_of` absent when nothing was priced.
- `min_cash` dropped; cash is an `asset_class_band` with a min only.
- Topics are config, per clause, in `ips.toml`; matched by containment in the
  user's words; the router never sees the list.
- A hypothetical weight is refused or permitted per concentration clause with
  no portfolio measured; both 4.1 and 4.2 apply because the position is unnamed.
- `log_delegation` is emitted at `mark_agent_complete`, for every plan.
- The dependency validator is a finding, not part of §7; it is §7 item 1 below.

**Pending, owner's call — bring them up before writing code.**
1. The diagnostic golden query "How much has AAPL gained?" (pid 3), one line,
   no prompt change, to separate "bare ticker" from "today". Still untaken.
2. Keep or revert the three failed prompt edits (6e68c47, d8cd0d6, 31ce272).
3. A target-weights clause in the IPS (closes "Rebalance has no target
   allocation source") and `OUT_OF_SCOPE_RESPONSE` moving into the IPS — both
   edit `docs/IPS.md`, which is the owner's.
4. D9's wording: "unrounded" means "not rounded beyond the cent-rounded block";
   18,083.175 prints as 18,083.17 against Part 7's 18,083.18.
5. The workbook: D8 and D9 in its `Decisions` sheet, `C91`, own commit via
   `git add`.
6. Merge `compliance` into `baseline-v1`, or not: the owner's.

---

## 6. Where we stand against the benchmark

10/12. Level 1 in full; 2.1, 2.2, 3.1, 3.2, 3.3, 3.4 pass. 2.3 BLOCKED: the
router does not plan ComplianceAgent for "What would have to change for me to
be within the limits again?" — two failed predictions, stopped. 3.5 BLOCKED on
conversation memory. The runner's blocked reason for 2.3 now prints the intent
and plan the router produced; read it before predicting anything about 2.3.

---

## 7. Next steps, in order

### 1. The dependency validator — a structural change, own commit, golden twice

`REQUIRES = {"PortfolioAnalysisAgent": ("DataAgent",)}` beside `AGENTS` (the one
dependency verified to raise at the node); `validate_dependencies` raises when
an agent precedes what it requires and when ComplianceAgent is planned under
any intent but `compliance`. `SmartRouter` retries with `REPAIR_PROMPT` carrying
the error, so a raise is a second attempt with the reason stated. Prediction
before the run, for all fifteen lines; the known "too big" flip is the line
most likely to change form. **The least certain prediction on this list** — it
changes what the router is told after a mistake. If it also moves 2.3, that is
2.3's next prediction, carried by a structural change as the rule requires.

### 2. 2.3 — only after item 1, and only with a diagnostic or structure

Read the runner's blocked reason first. If item 1 did not move it, the next
thing is a golden diagnostic that names the limits without the policy, not a
rewording of the intent line. Two failed predictions are on record.

### 3. Conversation memory, for 3.5

`AgentState.messages` and `build_router_prompt(conversation_history=)` exist
and are never populated; `run_agent_graph_sync` never passes prior turns. The
runner sends one query per case, so 3.5 needs a two-turn case shape as well.

### 4. The intent-vocabulary registry

Five sites, the roster registry is the pattern, `compliance` touched all five
in one commit. Own commit, zero golden diff predicted when rendered byte-identically.

### Later, with reasons

- Pending decisions 1–5 in §5, each small.
- `validate_execution_order`'s reorder-repair → raise.
- Delete `prompts.py`, `build_router_prompt(available_agents=)`,
  `get_graph_mermaid`, the unreachable check in `_validate_decision`,
  `IntentType.UNKNOWN`, `stream_agent_graph` (no caller, no span) — each its own
  commit after a grep for every re-export.
- Replace the two verbatim few-shots (1.1, 1.3).
- The period rule's "nearest valid value" → `clarification_needed`.
- README rewrite; `test_portfolio_integration.py`; the inline `sqrt(w'Σw)` copies.
- A compliance sub-measure if a case ever needs 2.1, 2.2 and 2.3 to read differently.

---

## 8. Rules learned the hard way

**Registration is not reachability — including your own.** Two commits wired
tracing into code no live run reached, and said in their messages that the CLI
would show it. The span was closed three nodes earlier. Read the span before
claiming the event.

**Shown a list, a model picks from it.** The topic vocabulary in the prompt
turned "currency risk" into `instruments`. Keep the user's words, match them
deterministically, and let a miss be the error rather than a match.

**Predict from the whole prompt, not the sentence you just wrote.** Rule 7 was
written without re-reading rule 6; they contradict on "too big", and the router
flips between them. Four failed predictions on one line.

**A check written before the capability catches the capability's own design.**
`check_3_4`'s `no_clause` assertion caught the vocabulary design on its first
live run, and its reason line, once it named the matched topic, was the whole
diagnostic. Make the runner's reasons carry what the next decision needs.

**Structure, not verdicts.** Two clauses are decided by cents; the checks
assert coverage, reconciliation and citation, and passed on the first live run
with different figures from the reference.

**Two hands, one decision.** Every prompt change this sitting had its
prediction in the commit message; every miss is on the record with its count.
The rule to stop at two was applied twice, and the second time the diagnostic
found a code defect the wording never would have.

**Six for six, still true; an instruction is a claim, still true; a refusal is
an honest failure, still true.** The previous handoffs' §8 have the examples.

---

## 9. Quick reference

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt
python tests/benchmark/run_cases.py
python tests/benchmark/run_cases.py --case 2.3

python src/agents/cli.py --portfolio 3

python src/portfolio_tool/scripts/seed_portfolio.py --show

grep -rn "SymbolName" src/ tests/ --include='*.py'
git status --short
git log --oneline afdc344..HEAD
```

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~30s | Do the components still work; does the graph still build; do the checker, loader and formatter hold to the references |
| CLI | ~4s | What is it actually doing — now including agent spans, tool calls and 📤 handovers |
| Golden set | ~70s, cents | Did routing change anywhere (fifteen lines, three pinned failures, one known flip) |
| Benchmark runner | ~1.5min, cents | How many cases pass; a BLOCKED reason names the router's intent and plan |

`golden set → change → golden set → decide → then update expected.txt, its own
commit, with a yes`. Prediction first, twice, stop at the second miss on a line.
The runner is per capability commit.
