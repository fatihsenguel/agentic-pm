# AGENTIC_FINANCE — Session Handoff

**Session date:** 1 September 2026
**Branch:** `baseline-v1`
**State:** Green. 91 tests passing, golden set stable, working tree clean.

This document is written for an LLM assistant picking up cold in a new conversation. It replaces `docs/Phase_6/PROJECT_CONTEXT.py` and the `docs/LLM_Context/` mirrors, which were deleted because they described a January architecture and actively misled.

**Regenerate this document at the end of each session rather than patching it.** Generated context files rot faster than the code they describe — that was the single clearest lesson of this session.

---

## 1. Project and owner intent

**AGENTIC_FINANCE** — a multi-agent portfolio management system built on LangGraph. Owner: Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Machine:** MacBook Air, Apple Silicon. Originally developed on a Windows desktop — expect Windows-era artifacts (all known ones have now been removed).

**Development history:** 11–28 January 2026 (17 commits), abandoned, resumed 1 September 2026.

### Ultimate goal

A **personal portfolio management and equity research assistant**, driven by the owner's own Investment Policy Statement (IPS). Everything below should be read against that target.

### Design principles the owner holds (stated explicitly)

- Strict modularity
- "Hot potato" — a component that can't handle something hands it back rather than guessing
- Strict separation of concerns — policy lives in config, not in code
- **Long-term correctness over short-term working output.** The owner explicitly rejected a quick fix during this session because it would encode a wrong financial model. Honour this.

### What the owner does NOT want

A pure asyncio/regex deterministic version without LangGraph. This was explored during January development and is unwanted.

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

# Unit tests — must stay at 91
pytest tests/ -q --ignore=tests/test_imports.py --continue-on-collection-errors

# Golden set — must produce an empty diff
python tests/golden/run_golden.py 2>/dev/null | diff tests/golden/expected.txt -
```

Both flags on pytest are required: `test_imports.py` is a script with `sys.exit()` at module level that crashes pytest collection (run it as `python tests/test_imports.py`), and `test_router_simple.py` calls `asyncio.run()` at import time.

**Caveat on "91 passing":** see `tests/golden/KNOWN_GAPS.md`. `test_portfolio_integration.py` returns booleans instead of asserting, so its tests pass unconditionally. The real number of meaningful assertions is lower.

### Branches

| Ref | Contents |
|---|---|
| `baseline-v1` | **The working branch.** Everything below happened here. |
| `master` (`b327e80`) | January tip. Contains the RAG subsystem and a `decision_logs` migration not present on `baseline-v1`. |
| `wip/phase7-snapshot` (`b72a7e5`) | Snapshot of Phase 7 work that was uncommitted when the project was abandoned. **UNVERIFIED.** Contains `compliance_agent.py`, `ips_manager.py`, `esg_screener.py`, seed/verify scripts, two test files, `docs/phase7/`. |

Backups outside the repo: `~/AGENTIC_FINANCE_backup_20260901.tar.gz`, `~/portfolio_db_snapshot.db`.

`baseline-v1` branched from `f8f046f` (24 Jan) — the last self-declared-green commit, and deliberately **pre-RAG** to avoid the chromadb/torch dependency surface and `fed_scraper.py`'s dependence on live Fed HTML.

---

## 3. Environment

Reconstructed from scratch; no virtualenv survived. The original `pyproject.toml` declared 5 dependencies while the code imports 23, so it was rewritten.

- **Python 3.10.21** (Homebrew), matching the `cpython-310` bytecode found in the repo
- **88 packages**, frozen in `baseline-v1-lock.txt`
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`, `src/observability` → `observability`, `src/config.py` → `config`. Code never uses `from src.…`
- RAG dependencies deliberately in an optional `[rag]` extra, **not installed**

Key versions, all major jumps from January: langgraph 1.2.11, langchain-core 1.6.1, langchain-anthropic 1.7.0, anthropic 1.2.0, pydantic 2.13.5, numpy 2.2.6, pandas 2.3.3, scipy 1.15.3, yfinance 1.7.0, pytest 9.1.1.

**Notable finding:** all 55 modules import cleanly against this stack. **Not one** of the original 15 test failures was caused by library version drift. Every failure was internal rot from the owner's own January refactoring.

### API keys

`.env` holds `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`. Gitignored.

- **OpenAI: no credits** (HTTP 429 `insufficient_quota`). Do not route there.
- **Anthropic: working.** Must be a **workspace-scoped** key from `platform.claude.com/settings/workspaces/default/keys` — an identity-linked key returns HTTP 400 demanding an `anthropic-workspace-id` header. Choose "continue with an API key", not identity federation (that is for CI/cloud).

### Database

`data/portfolio.db` is **untracked** as of this session — it is runtime state, changes on every test run, and was adding 3MB binary diffs to history. A fresh clone needs `alembic upgrade head` plus seeding. Alembic is healthy: 1 head (`01225e17789b`), `current == head`, 8 migrations, linear chain.

Demo data: portfolio 1 = SPY/TLT/GLD (asset classes corrected this session to equity/fixed_income/commodity), portfolio 2 = AAPL/MSFT with sector metadata.

---

## 4. LLM configuration

`src/agents/config.py` is the **single source of truth**. Neither `config.toml` nor `src/config.py` contains a model name.

| Preset | Model | Status |
|---|---|---|
| `OPENAI_MINI` / `OPENAI_FULL` | gpt-4o-mini / gpt-4o | unused, no credits |
| `ANTHROPIC_HAIKU` | `claude-haiku-4-5-20251001` | **ACTIVE** |
| `ANTHROPIC_SONNET` | `claude-haiku-4-5-20251001` | **placeholder — needs a real Sonnet id** |

`ACTIVE_LLM_CONFIG = ANTHROPIC_HAIKU`. `get_llm()` switches on `config.provider`.

### Three traps in this area

1. **`src/agents/__init__.py` imports all four presets by name.** Deleting one breaks the entire package. This happened during the session. **Always `grep -rn "NAME" src/ tests/` before deleting a symbol.**
2. **`smart_router.py` has a dead hardcoded `ChatOpenAI` branch** in its `llm` property, active when `use_stronger_model=True`. That flag was set to `False` (line 41) so the factory is used. The dead branch should be deleted.
3. **January model ids are retired.** `claude-3-5-*-20241022` returns 404. Never guess a model id; check the console or `GET https://api.anthropic.com/v1/models`.

---

## 5. Bugs fixed this session (10)

**The dominant failure mode of this codebase: renames and moves that left call sites behind.** Nearly every bug traces to commit `34be53f` (config refactoring) or `cccca06` (tools moved into agent methods). Nothing in the codebase catches a mismatch between a producer and its consumers.

### Phase A — getting the test suite green (15 failures → 0)

1. **`tools/__init__.py` exported 10 non-existent names.** Rewritten to export real names plus the curated lists each module maintains (`ALL_DATA_TOOLS`, `FETCH_TOOLS`, `READ_TOOLS`, `ALL_ANALYTICS_TOOLS`, `RISK_TOOLS`, `PERFORMANCE_TOOLS`, `get_macro_tools`). `__all__` is now derived from `dir()` so it cannot drift again.
2. **`max_equity_adjustment` vs `max_equity_adjust`** — `macro_agent.py:580` called a config field that doesn't exist. Cleared 5 failures.
3. **`PortfolioResult` missing required `agent_name`** at `macro_agent.py:321`.
4. **Variable shadowing in `rebalance_agent.py`** — `config = RebalanceConfig(... config.rebalance.x ...)` made `config` local for the whole function, raising `UnboundLocalError`. Renamed the local to `rebalance_config`.
5. **`PortfolioWeights.validate_weights` was a no-op stub** — detected a bad sum then `pass`, and never checked negatives. `{"SPY": 1.2, "TLT": -0.2}` passed validation. **The most consequential bug found:** it produces silently wrong portfolios rather than errors. Now raises.
6. **`RouterDecision.validate_clarification` repaired instead of rejecting** — silently substituted a default clarification question. Now raises, matching the January "Deleting Fallbacks" direction. Malformed responses now hit the router's existing 3-attempt retry loop with repair prompt.

Also: restored alembic migration `67cc3e174858` lost to a macOS NFC/NFD filename encoding conflict (`ü` as `\303\274` vs `\314\210`); deleted `tests/test_langgraph.py`, which tested `should_continue_or_end`, `route_to_agent`, `agent_dispatcher_node`, `run_agent_graph` — none of which exist in the current architecture.

### Phase B — making the system actually work end to end

The unit tests passed while **no agent ever executed**. Found via the golden set, not via tests.

7. **`execution_order` key mismatch** — `_decision_to_dict` in `nodes.py:292` wrote the key `execution_plan` (the `@property` alias on `RouterDecision`), while `state.py:116` and `graph.py:37` both read `execution_order` (the real field). `agents_to_run` was always `[]`, so the graph went straight to the synthesizer. **One line. This was the difference between a system that returned empty headers and one that produces real portfolio optimizations.**
8. **Portfolio invisible to the router** — `portfolio_tickers` was loaded *before* the LLM call but only used to patch `decision.parameters` *after* it. When the LLM said "please provide your holdings" there was nothing to patch. Added a `portfolio_context` parameter to `build_router_prompt` and passed the holdings in. Six queries went from asking the user to paste holdings, to routing correctly.
9. **`period` handling** — `data_agent.py:390` called `period.upper()` on `None` (crash) and used a magic `1825` default for unknown values (silent 5-year fetch when the user asked for 12 months). Now `period or config.data.default_period`, then **raises** on an unrecognised value. The router prompt was also teaching the model invalid periods (`3M`, `30D` are not in `period_days`); it now states the exact vocabulary.
10. **`cache_portfolio_holdings` mutated state instead of returning an update** — LangGraph merges what a node *returns*; the in-place `state["portfolio_holdings"] = holdings` was discarded. Downstream agents never saw holdings. Now returns a dict spread into the node's return value.

---

## 6. The golden set

`tests/golden/run_golden.py` runs 10 representative queries and prints **only stable fields** (intent, plan, period, agents run, error count) — no prices, timestamps, or quota counters, so runs are diffable. `tests/golden/expected.txt` is the committed baseline.

```bash
python tests/golden/run_golden.py 2>/dev/null | diff tests/golden/expected.txt -
```

This costs a few cents and ~40 seconds per run (live LLM + yfinance calls). Run it after any change that could affect routing or agent behaviour.

**It found bug 7, which 91 passing unit tests did not.** Unit tests cover components; the golden set covers whether a real question produces a real answer.

`tests/golden/run_baseline.txt` and `run_after_portfolio_context.txt` are raw diagnostic dumps from before/after the graph fixes, kept as historical evidence.

---

## 7. Known gaps — features, not bugs

Full detail with reasoning in **`tests/golden/KNOWN_GAPS.md`**. Read that file before "fixing" any of these.

- **Rebalance has no target allocation source.** RebalanceAgent needs a fixed target to measure drift against. **DO NOT fix by inserting OptimizationAgent into the chain** — re-optimising on every drift check means the target moves with the covariance matrix, which is not how strategic asset allocation works. Targets belong to the portfolio/IPS. Resolve when Phase 7 lands.
- **RiskManagerAgent is not wired.** The file exists and imports, but has no graph node, no routing map entry, and no mention in `router_prompts.py`. The router correctly classifies `intent: risk_analysis` and then has nowhere to send it. Registered agents are: DataAgent, MacroAgent, OptimizationAgent, RebalanceAgent, BacktestAgent.
- **No position-level performance.** Nothing compares current price against `average_price` to produce P&L.
- **No holdings-metadata queries.** `Asset` carries `asset_class`, `sector`, `industry`, `country`, but no agent reads holdings as *positions* rather than as a ticker list.
- **`test_portfolio_integration.py` doesn't assert.** 18 `return True/False` statements; pytest ignores them. Needs a rewrite, not a mechanical swap.
- **MacroAgent: "Yield curve data missing from snapshot"** on the market-regime query.

---

## 8. Other known issues (unfixed, lower priority)

| Issue | Location |
|---|---|
| **DataAgent fetches prices twice per query** — once before covariance, again before returns. Doubles yfinance calls. | `nodes.py` data path |
| Tests write to the real `data/portfolio.db` | should use a temp DB |
| DB connection opens at import time (`DEBUG: Verbinde mit DB…` on every import) | `src/config.py` |
| `base_agent.py:142` returns unbound names `[fetch_prices_tool, covariance_tool, returns_tool]` — `NameError` waiting to happen | `base_agent.py` |
| `risk_manager_agent.py:342` hardcodes `agent_name="OptimizationAgent"` | possibly copy-paste |
| Pydantic v1-style `class Config` (deprecation warnings) | `schemas.py:50`, `:84` |
| `validate_execution_order` silently auto-corrects LLM mistakes — same repair-vs-raise question as bug 6 | `schemas.py` |
| Router returns `(None, validation)` on total failure; the real error hides in `validation.errors` | `smart_router.py:298` |
| Period vocabulary duplicated between `config.data.period_days` and the router prompt string | should be generated from config |

---

## 9. Cleanup performed

**~10,400 lines removed.** Tests green and golden diff empty after every deletion.

Deleted: `nodes_with_fallbacks.py`, `data_agent_with_fallbacks.py` (2,076 lines, contained a stale mutating copy of `cache_portfolio_holdings`) · `docs/Code_Snippets/` and `docs/LLM_Context/` (25 stale source mirrors) · `docs/Phase_6/` including `PROJECT_CONTEXT.py` · `docs/zusammenfassung.md`, `Claude_Gemini_Motivation.md`, `Data_Manager.md` · `demos/` (3 files, 921 lines — interview-era demos that bypassed the graph via `create_*_agent` factories) · `portfolio_manager_old.py` · `find_violations.ps1`, `violation_report.txt` · `tests/test_langgraph.py` · empty dirs `fed_minutes_cache/`, `src/detection/`.

Also: untracked `data/portfolio.db`; fixed `test_no_self_config_references` to actually assert and to anchor paths to the repo root (it previously passed unconditionally, and silently checked nothing when run from another directory).

**Kept:** `src/api/main.py` and `src/portfolio_tool/scripts/*` — these are entry points, so nothing importing them is expected. `docs/` retains only genuine notes: `BUGS/1.md`, `Tricks.md`, `workflow.md`, `Workflow_with_git.md`, `data_manager_veränderungen.md` (states a real design rule — data methods must return `UpdateResult`/`QueryResult`), `Claude_Golden_Set_Inspection.md`.

### Rules that emerged

1. **`grep -rn "Name" src/ tests/` before deleting any symbol.** A name imported elsewhere is not dead code even when its value is stale.
2. One deletion per commit; verify against tests and the golden set.
3. macOS `sed` needs `-i ''`.
4. Generated LLM-context documents rot faster than code. Regenerate, never patch.
5. When patching a file blind, use `assert s.count(old) == 1` before writing.

---

## 10. Next steps, in order

### 1. Base-agent deduplication — do this before adding any agent

`agent_name=self.name` appears in five agent files. Each builds `PortfolioResult` by hand. `smart_router` constructs its own LLM client rather than using the factory.

**Bug 3 was caused directly by this.** If `base_agent.py` owned result construction, that bug could not have existed. Adding a sixth agent on top of the current duplication multiplies the problem — every new agent copies five stale patterns.

### 2. Wire RiskManagerAgent

Smallest real feature. Needs: a node in `graph.py` (`add_node` + routing map entry), a description in `router_prompts.py`, and a few-shot example showing `[DataAgent, RiskManagerAgent]` — matching the working `[DataAgent, OptimizationAgent]` pattern. The router already classifies `intent: risk_analysis` correctly.

Do this **after** step 1 so the new wiring uses the deduplicated base.

### 3. Point tests at a temporary database

Before larger refactoring, so reference data stops drifting under the golden set.

### 4. Pull Phase 7 forward

One file at a time from `wip/phase7-snapshot`: `ips_manager.py`, `esg_screener.py`, `compliance_agent.py`, then the seed scripts and tests. Expect the same rot found elsewhere — stale imports and renamed config fields.

**This is closer to the owner's ultimate goal than it appears.** IPS-based queries ("does my allocation violate my policy?", "what is my concentration risk?") need structured IPS data and deterministic checks, **not RAG**. RAG is only needed to extract rules from a PDF policy document. Phase 7 also resolves the rebalance-target question in §7.

### 5. Decide on RAG

Exists on `master` (`b327e80`), deliberately excluded here. Requires `pip install -e ".[rag]"` (pulls torch via sentence-transformers) and `fed_scraper.py` targets HTML that has changed since January. Note `vector_store.py` and chromadb do **not** exist at `f8f046f`, so the RAG code on this branch cannot store vectors. Decide whether it is wanted at all before investing time.

### 6. Extend

Owner's stated ideas: merge RebalanceAgent into a broader Quant agent, add agents and tools, iterate on prompts.

The rebalance→Quant merge is a good first refactor — `rebalance_tools.py` is pure deterministic math with a thin agent wrapper, the cleanest module in the project. Use it to establish the rhythm: golden set → change → golden set → commit.

**Prompt iteration specifically needs the golden set.** A worse prompt still returns valid JSON, so unit tests cannot detect prompt regressions. Change the prompt, re-run the same queries, compare routing decisions. Bug 9 is the proof: the prompt was teaching the model invalid period values and nothing caught it.

---

## Addendum (same session, after handoff was written)

- Early RAG code removed from `baseline-v1`, parked at branch `wip/rag-early`
  and tag `rag-early-parked`. See `tests/golden/KNOWN_GAPS.md` for reasoning.
- `find_violations.ps1` and `violation_report.txt` removed (an earlier `git rm`
  had aborted atomically because one path didn't exist).
- `data/chroma/` and `*.egg-info/` added to `.gitignore`.
- Tag `baseline-v1-clean` marks the end of the cleanup phase.

## 11. Quick reference

```bash
# Setup
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

# Verification
pytest tests/ -q --ignore=tests/test_imports.py --continue-on-collection-errors
python tests/golden/run_golden.py 2>/dev/null | diff tests/golden/expected.txt -

# LLM path
python -c "from agents.config import get_llm; print(get_llm().invoke('Reply with just: ok').content)"

# Single query, full output
python -c "
from agents.graph import run_agent_graph_sync
r = run_agent_graph_sync('What is the risk of my portfolio?', portfolio_id=1)
print('PLAN:', r.get('router_decision', {}).get('execution_order'))
print('ERRORS:', r.get('errors'))
print('FINAL:', r.get('final_response'))
"

# Import health across all modules
python - <<'EOF'
import importlib, pkgutil, agents, portfolio_tool, observability
fail = []
for pkg in (agents, portfolio_tool, observability):
    for m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try: importlib.import_module(m.name)
        except Exception as e: fail.append((m.name, type(e).__name__, str(e)[:120]))
print("FAIL:", len(fail))
for f in fail: print(" ", f)
EOF

# Before deleting any symbol
grep -rn "SymbolName" src/ tests/ | grep -v __pycache__
```

**Reference files:** `baseline-v1-lock.txt` (pinned deps) · `tests/golden/expected.txt` (golden baseline) · `tests/golden/KNOWN_GAPS.md` (**read before "fixing" anything in §7**).

---

## Addendum (same session, after handoff was written)

- Early RAG code removed from `baseline-v1`, parked at branch `wip/rag-early`
  and tag `rag-early-parked`. See `tests/golden/KNOWN_GAPS.md` for reasoning.
- `find_violations.ps1` and `violation_report.txt` removed (an earlier `git rm`
  had aborted atomically because one path didn't exist).
- `data/chroma/` and `*.egg-info/` added to `.gitignore`.
- Tag `baseline-v1-clean` marks the end of the cleanup phase.
- RAG is not needed for the IPS work. A self-authored IPS is structured data
  (targets, limits, allowed instruments) checked deterministically. RAG becomes
  relevant for equity research: 10-K filings, earnings transcripts, CEO commentary.
