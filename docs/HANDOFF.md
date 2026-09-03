# AGENTIC_FINANCE — Session Handoff

**Session date:** 3 September 2026
**Branch:** `baseline-v1` (14 commits ahead of `origin/baseline-v1`, unpushed)
**State:** Green. 91 tests passing, golden set stable over three consecutive runs, working tree clean.

Written for an LLM assistant picking up cold in a new conversation.

**Regenerate this document at the end of each session rather than patching it.**
Generated context files rot faster than the code they describe.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/benchmark.md` | **The definition of done.** 12 test cases across 3 levels, plus scope boundaries and the output contract. Everything is measured against this. |
| `docs/PM-Assistant — Roadmap.md` | Phased plan, ordered by dependency rather than effort. |
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. Long, and the most useful file in the repo. |
| `tests/golden/expected_values.md` | Hand-computed expected answers for portfolio 3, plus eight recorded decisions (D1–D8). The reference the code gets checked against. `expected_values.xlsx` alongside it holds the formulas. |

**Do not update `expected_values` to match code output.** If they disagree, one
of the two is wrong and that gets resolved deliberately.

---

## 1. Project and owner intent

**AGENTIC_FINANCE** — a multi-agent portfolio management system on LangGraph. Owner: Fatih Sengul.

**Path:** `/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE`
**Repo:** https://github.com/fatihsenguel/agentic-pm (public — README is outdated and lies)
**Machine:** MacBook Air, Apple Silicon. Originally developed on Windows; expect Windows-era artifacts.

**History:** 11–28 January 2026 (17 commits), abandoned, resumed 1 September 2026.

### Ultimate goal

A **personal portfolio management and equity research assistant**, driven by the
owner's own Investment Policy Statement. Read everything below against that.

There is **no deadline**. Correctness over speed. This changes benchmark.md
Part 4 from a triage list into an ordering by dependency — nothing gets dropped
for time, but scope creep is now the live risk rather than under-delivery.

### Design principles the owner holds

- Strict modularity.
- **Hot potato — agents never see raw data.** Tools return summaries; raw arrays
  move through `shared_data`, never into an LLM context.
- Strict separation of concerns — **policy lives in config, not code**.
- **Long-term correctness over short-term working output.** The owner would
  rather leave something broken than encode a wrong model. Honour this.

### How the owner works

- `grep -rn "Name" src/ tests/` before deleting any symbol, including lazy
  imports inside function bodies.
- Never infer a module's purpose or dependencies from its name.
- One change per commit.
- Verify against `pytest` and the golden set, run as **separate commands** — not
  chained with `&&`, which hides failures.
- Do not paste multi-line blocks containing interactive commands (`git add -p`)
  or trailing `#` comments into zsh; both get eaten.

### What the owner does NOT want

A pure asyncio/regex deterministic version without LangGraph.

---

## 2. Current state

```bash
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

pytest -q

python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt && echo "NO DIFF"

python src/agents/cli.py --portfolio 3
```

`pytest` now runs with no flags. It previously aborted collection with
INTERNALERROR because `tests/test_imports.py` called `sys.exit()` at module
level; it was renamed `check_imports.py` (it defines no test functions).

**Caveat on "91 passing":** `test_portfolio_integration.py` returns booleans
instead of asserting, so its tests pass unconditionally. 91 means 91 collected
and none errored, not 91 things verified.

### Branches and tags

`baseline-v1` is the working branch. `wip/phase7-snapshot` holds Compliance/IPS
code to pull forward. `wip/rag-early` and tag `rag-early-parked` hold the deleted
RAG code. `master` (b327e80) has a fuller RAG version with a vector store.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`a7d5e1c04b83`**, 10 migrations, linear chain.

- **Portfolio 3, "Benchmark Portfolio" — use this one.** 9 positions, 4 asset
  classes, 4 sectors, cost basis 284,500 plus 15,500 cash = 300,000 flat.
  Synthetic and deliberately round, so `expected_values` can be hand-computed.
  Seeded by `src/portfolio_tool/scripts/seed_portfolio.py` (idempotent).
- Portfolios 1 and 2 are the old demo data. The golden set still uses them, so
  **do not modify them** or the baseline breaks.

---

## 3. Environment

- **Python 3.10.21** (Homebrew). `pyproject.toml` pins `>=3.10,<3.11`.
- 88 packages frozen in `baseline-v1-lock.txt`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never
  `from src.…`.

`.env` holds `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`.

- **OpenAI: no credits** (429). Do not route there.
- **Anthropic: working.** Must be a **workspace-scoped** key.

### LLM configuration

`src/agents/config.py` is the single source of truth. `ACTIVE_LLM_CONFIG =
ANTHROPIC_HAIKU` (`claude-haiku-4-5-20251001`).

**`ANTHROPIC_SONNET` still points at the Haiku id** — a placeholder that would
silently give Haiku if selected. Never guess a model id; check
`GET https://api.anthropic.com/v1/models`.

`src/agents/__init__.py` imports all four presets by name, so deleting one breaks
the package.

---

## 4. What this session did (3 September)

Fourteen commits. Roughly: closed the RAG decision, repaired both verification
instruments, built the tooling and ground truth that Phase 1 will be judged
against.

**Closed the RAG question with evidence.** Ran the January scraper live: the FOMC
calendar returns HTTP 200 and `div.panel` no longer matches, so zero meetings
parse. Removed the Fed capability from MacroAgent and the dead module-level
tools. In the process found that `fed_confidence` was hardcoded to 0.5 and fed a
phantom 0.25 into every `regime_confidence` via a `× 0.5` term, on every macro
query ever run. Code preserved at tag `rag-early-parked`; do not restore it, build
fresh over filings when equity research starts.

**Found both verification loops broken.**
`pytest` had not run since January (module-level `sys.exit()` aborted
collection at 10 of 91 items). The golden set was silently nondeterministic —
the router prompt's OUTPUT FORMAT block carried sample values that the model
copied when it had nothing to extract, contradicting its own extraction rule.
Both fixed. This is the session's most important outcome: everything built
before today was unverifiable.

**Built the CLI** (`src/agents/cli.py`) — roadmap 0.3. Prints routing, agents
run, `shared_data`, and the answer. Flags two things `run_golden.py` structurally
cannot see: agents planned but never run, and answers containing no digits while
`shared_data` does.

**Seeded portfolio 3 and computed expected values** — roadmap 0.1 and 0.2.
Added `purchase_date` to `PortfolioHolding` (benchmark 1.2 needs it and there was
nowhere to store it). Recorded eight decisions, three of which turned out to be
forced by the data model rather than chosen.

**Fixed the price cache.** Callers passing an explicit date range bypassed
caching entirely: 18 provider calls per query on nine tickers, ~9s latency.
Repeat queries now make zero calls; 2.3s.

**Cleaned dead configuration.** `AgentConfig.model_name` defaulted to
`gpt-4o-mini` and was read nowhere.

---

## 5. Where we stand against the benchmark

**Zero of the twelve cases pass.** Routing is correct for all of them; the
capabilities underneath are absent.

The architecture is sound and this should not be re-litigated. The router
classifies correctly, returns valid JSON, maps "past twelve months" to `1Y`, and
takes tickers from the portfolio rather than the message. The graph plans and
executes with no agent planned-but-not-run. `portfolio_id` flows through.
DataAgent produces correct covariance, returns and per-ticker volatility.

**The gap is capabilities, not architecture.**

Every Level 1 query returns a byte-identical stub:

    Analysis complete. See details below:

    DataAgent: ✓

---

## 6. Next steps, in order

### 1. DataAgent must publish holdings to `shared_data`

**The single blocker under benchmark 1.1, 1.2 and 1.4.** `portfolio_id` is
resolved to a ticker list for fetching, then the quantities, average prices and
purchase dates are discarded. Nothing anywhere assigns `shared_data["holdings"]`.
`nodes.py:211` logs "Portfolio N specified but holdings not loaded";
`nodes.py:825` raises it and RebalanceAgent fails on it today.

Decide what a holdings summary contains. That interacts with the hot-potato
violation — `price_data_json` currently puts 67KB of raw daily OHLC into
`shared_data`, against the project's first stated principle.

### 2. An agent computes allocation from holdings and prices

Benchmark 1.1 and 1.4. Check against `expected_values.md` Parts 2 and 3.
Also close the `update_holding` gap: it accepts only `quantity` and
`average_price`, so `asset_class` and `sector` need SQLAlchemy directly.

### 3. Synthesizer branches for `data_fetch` and `risk_analysis`

`synthesizer_node` dispatches on **intent** at `nodes.py:1104`, and those two
intents have no branch. **It does not dispatch on `result_type`** — an earlier
diagnosis said it did and was wrong.

The formatters must not compute anything. An agent computes; the synthesizer
formats.

### 4. Position P&L, then portfolio volatility

Check against `expected_values.md` Part 1 and Part 4 (10.2936%). Per decision D7,
none of the five existing volatility implementations computes portfolio-level
vol; a new `portfolio_volatility(weights, cov_matrix)` goes in
`quant/risk_metrics.py`.

### 5. Data-age reporting

Benchmark 3.3. Build it into the output contract rather than retrofitting.
`latest_prices` is the previous settled close, reported as current with no as-of
date, and the new cache means it can be up to two closes behind.

### Later, with reasons

- **Base-agent deduplication.** Five agents hand-build `PortfolioResult`;
  DataAgent already uses `create_result` at seven sites. Originally scheduled
  first on the premise that it would fix the synthesizer — that premise was
  wrong. Do it when Risk and Compliance arrive, which is its real justification,
  and wire `trace_tool` and `log_delegation` at the same time (benchmark 2.1
  cannot pass without them).
- **README rewrite.** Currently describes RiskManagerAgent as an active
  supervisor, references deleted `demos/` scripts, specifies `gpt-4-turbo`. Left
  until after Phase 1 so it is written once. Keep its Design Principles section.
- **`out_of_scope` router intent.** Benchmark 3.2 fails because the router has no
  vocabulary for "this is not something the system does".
- **Delete `src/portfolio_tool/rag/`** and the `[rag]` extra. Blocking nothing.
- **CostCalculator pricing table**, `.gitignore` rewrite. Ten minutes each.

---

## 7. Rules learned the hard way

**Both instruments have blind spots, and the CLI is the third one.**
`run_golden.py` prints five routing fields and nothing else — no answer content,
no numbers. `pytest` passes on tests that never assert. The price-cache bug that
was wrong for four of nine assets passed pytest, applied cleanly, improved
latency, and was caught only by reading the CLI's provider-call output.

**Coverage checks must ask what was requested, not what was stored.** Asking for
prices from 2023-09-04 (Labor Day) returns 2023-09-05 as the first row, so any
"do we hold a row on or before X" test fails forever.

**Fields that look like they control something often do not.** `model_name`,
`ANTHROPIC_SONNET`, `log_tool_calls`, `max_tool_calls_per_turn`,
`hawkish_threshold`, and `result_type` all read as live and are not. Grep before
believing any of them.

**The recurring bug shape is repair-instead-of-raise.** A wrong answer with a
plausible face rather than an error. `PRICING.get(model, PRICING["gpt-4-turbo"])`,
`fed_confidence = 0.5`, the scraper's `soup.body.get_text()` fallback.

**Capability exists, wiring does not.** RiskManagerAgent, `conversation_history`,
`ToolTrace`, `log_delegation`, and holdings are all built and unconnected. Nothing
fails when the connection is missing, which is why they survive.

---

## 8. Quick reference

```bash
# Setup
cd "/Users/sengul/Programming/AI Engineering/Finance/Korrekte_Versionen/AGENTIC_FINANCE"
source .venv/bin/activate

# Verification — separate commands, never chained with &&
pytest -q
python tests/golden/run_golden.py > /tmp/golden_now.txt 2>/dev/null
diff tests/golden/expected.txt /tmp/golden_now.txt

# Exploratory loop
python src/agents/cli.py --portfolio 3
#   :p <id>  switch portfolio    :v  verbose    :r  raw state    :q  quit

# Re-seed the benchmark portfolio
python src/portfolio_tool/scripts/seed_portfolio.py --show
python src/portfolio_tool/scripts/seed_portfolio.py --reset

# Import health
python tests/check_imports.py

# Before deleting any symbol
grep -rn "SymbolName" src/ tests/ --include='*.py'
```

Note zsh eats `--include=*.py` unquoted, and swallows `#` comments pasted on
command lines.

### The three loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~34s | Do the components still work |
| CLI | ~3s | What is it actually doing |
| Golden set | ~40s, cents | Did routing change anywhere |

`golden set → change → golden set → commit`. When the diff changes, decide
whether it is an improvement **before** updating `expected.txt`. A case that only
works most of the time counts as failed.
