# AGENTIC_FINANCE — Session Handoff

**Session date:** 4 September 2026
**Branch:** `baseline-v1`
**State:** Green. 105 tests passing, golden set stable over two consecutive runs, working tree clean.

Written for an LLM assistant picking up cold in a new conversation.

**Regenerate this document at the end of each session rather than patching it.**
Generated context files rot faster than the code they describe.

---

## 0. Read these first, in this order

| File | What it is |
|---|---|
| `docs/benchmark.md` | **The definition of done.** 12 test cases across 3 levels, plus scope boundaries and the output contract. Everything is measured against this. Part 2 is now phased — see §5. |
| `docs/PM-Assistant — Roadmap.md` | Phased plan, ordered by dependency. Committed 4 September after being untracked and nearly lost; carries a header listing the points superseded since it was written. |
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
owner's own Investment Policy Statement. The goal explicitly includes
**screening and stock picking** — not only analysing named instruments. That is
currently out of scope by phase, not permanently; see §5.

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
  imports inside function bodies.
- Never infer a module's purpose or dependencies from its name.
- One change per commit. **If the commit message needs an "and", it is two
  commits.** This rule was adopted on 4 September and settles most scope
  questions on its own.
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

**Caveat on "105 passing":** `test_portfolio_integration.py` returns booleans
instead of asserting, so its tests pass unconditionally, and its TEST 7 catches
every exception and returns `True` in both branches. 105 means 105 collected and
none errored, not 105 things verified. 14 of the 105 are the new allocation
tests, which do assert against hand-computed figures.

### Branches and tags

`baseline-v1` is the working branch. `wip/phase7-snapshot` holds Compliance/IPS
code to pull forward. `wip/rag-early` and tag `rag-early-parked` hold the deleted
RAG code. `master` (b327e80) has a fuller RAG version with a vector store. All
three tags are on the remote.

### Database

`data/portfolio.db` is untracked runtime state. Alembic head is
**`a7d5e1c04b83`**, 11 migrations, linear chain from `c1e79ae31788`.

- **Portfolio 3, "Benchmark Portfolio" — use this one.** 9 positions, 4 asset
  classes, 4 sectors, cost basis 284,500 plus 15,500 cash = 300,000 flat.
  Synthetic and deliberately round, so `expected_values` can be hand-computed.
  Seeded by `src/portfolio_tool/scripts/seed_portfolio.py` (idempotent).
- **Portfolio 1, "Demo Portfolio"** — January data. `run_golden.py:21-24` runs
  four of its ten queries against it, so **do not modify or delete it** or the
  baseline breaks.
- **Portfolio 2, "Integration Test"** — confirmed 4 September to be a *leaked
  test artifact*, not January data. Contains AAPL 10 @ 150.0 and MSFT 5 @ 350.0,
  which is `test_portfolio_integration.py:42-43` verbatim, left behind by a run
  that returned early before its `delete_portfolio`. `run_golden.py:26` uses it
  for the Technology-sector query, so it is load-bearing by accident. Its
  holdings have no `asset_class` set.

---

## 3. Environment

- **Python 3.10.21** (Homebrew). `pyproject.toml` pins `>=3.10,<3.11`.
- 88 packages frozen in `baseline-v1-lock.txt`.
- src-layout: `src/agents` → `agents`, `src/portfolio_tool` → `portfolio_tool`,
  `src/observability` → `observability`, `src/config.py` → `config`. Never
  `from src.…`.

`.env` holds `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`. `.env` is
gitignored.

- **OpenAI: no credits** (429). Do not route there.
- **Anthropic: working.** Must be a **workspace-scoped** key.

### Database URL — changed 4 September

`DATABASE_URL` used to be read by nothing; `database_setup.py` computed its own
path from `__file__`. It is now live. `config.py` owns it via `DatabaseConfig`,
calls `load_dotenv()` itself so load order cannot matter, and
`resolve_database_url` anchors a **relative** SQLite path to the project root.

`.env` contains `sqlite:///./data/portfolio.db`, a relative path. Anchoring is
what makes that safe: SQLite creates a missing file silently, so a cwd-relative
URL would hand out a fresh empty database when run from a subdirectory rather
than failing. `sqlite:///./data/…` therefore means "relative to the repo", not
"relative to the shell" — deliberately the opposite of shell intuition.

`alembic.ini:87` still carries its own relative copy of the path and keeps that
fragility. Unfixed, deliberately: a third change with its own failure mode.

`data_manager.py:25` has the same bug (`CONFIG_PATH = "config.toml"`, cwd
relative) and it is worse, because it warns and continues with default fetch
intervals rather than failing. Demonstrated live on 4 September. One-line fix
using `_PROJECT_ROOT`; not blocking.

### LLM configuration

`src/agents/config.py` is the single source of truth. `ACTIVE_LLM_CONFIG =
ANTHROPIC_HAIKU` (`claude-haiku-4-5-20251001`).

**`ANTHROPIC_SONNET` still points at the Haiku id** — a placeholder that would
silently give Haiku if selected. Never guess a model id; check
`GET https://api.anthropic.com/v1/models`.

`src/agents/__init__.py` imports all four presets by name, so deleting one breaks
the package.

---

## 4. What this session did (4 September)

Roughly: closed roadmap item 1, built and wired item 2, and fixed three
infrastructure faults found on the way.

**Closed the holdings gap (item 1).** `get_holdings` was not projecting
`purchase_date` — the column existed, the migration existed, the seed wrote it,
and the SELECT never read it. Then `build_holdings_summary` publishes an
**unpriced** summary (ticker, quantity, average_price, asset_class, sector,
purchase_date) to `shared_data`. Unpriced deliberately: pricing it inside
DataAgent would leave item 2 with nothing to compute and dissolve the
agent/synthesizer split.

**Introduced `PortfolioContext`.** `load_portfolio_context` returned a
`(tickers, holdings)` tuple and could not carry cash. It now returns a dataclass,
so the next field costs no call sites. Cash reaches `shared_data` as
`cash_balance`; per D2 it is the allocation denominator, and an absent balance is
an unknown denominator rather than zero.

**Built allocation (item 2).** `quant/allocation.py` is pure arithmetic —
`allocation_by_asset_class` and `allocation_by_sector`, with `_market_values` and
`_cost_bases` as shared helpers that item 4's P&L will reuse unchanged.
`tests/test_allocation.py` has 14 assertions taken from `expected_values.md`
Parts 2 and 3, and passed on the first run. Missing prices **raise** rather than
skip.

**Added `PortfolioAnalysisAgent`.** A sixth agent in the router's vocabulary,
with a node reading only `shared_data`. Named for what it does today; it may
become the risk agent 2.1 needs, and renaming is cheaper than a wrong
abstraction. Publishes both breakdowns, since selecting between two computed
breakdowns is formatting rather than computing.

The first prompt version **bled**: the volatility query flipped
`risk_analysis` → `data_fetch`, and the risk query picked up the new agent.
Narrowed by moving the guidance out of the `data_fetch` bullet, dropping
"weighted" as a trigger word, and adding both regressed queries as explicit
counter-examples. Second version was clean and stable over two runs.
`expected.txt` moved by exactly four lines, deliberately.

**Fixed the test suite writing to the live database.** `pytest` created and
deleted a portfolio in `data/portfolio.db` on every run. `conftest.py` now
redirects the whole suite to a temp **copy** — a copy rather than an empty file,
because ~22 tests read cached prices and an empty database would refetch every
series from yfinance. It raises with instructions if the source database is
missing.

**Fixed the volatilities contract.** `shared_data["volatilities"]` carried
`"15.33%"` strings while `expected_returns` was hard-validated as floats.
`CovarianceResult.to_dict` now emits `annualized_volatilities_raw` alongside the
display strings, and the node raises if it is absent.

**Renamed `test_portfolio_manager_simple.py` → `check_portfolio_manager.py`.**
Same treatment as January's `test_imports.py`: no test functions, and it wrote to
the live database at import.

**Docs.** benchmark.md Part 2 made phased. KNOWN_GAPS gained the supervisor
decision, the non-determinism boundary, the agent-roster duplication, the
benchmark-runner entry, and three corrections to its own earlier claims. The
roadmap was recovered from outside the repo and committed.

---

## 5. Decisions taken this session

**Keep the router and graph. Do not wire the supervisor. Do not rename it.**
`RiskManagerAgent` is `class RiskManagerAgent(SupervisorAgent)` — an unused
second orchestrator, not a risk agent. Plan-then-execute makes one routing
decision that depends only on the user's words, which is why the golden set can
pin it; a supervisor makes N decisions that depend on data just fetched, which
nothing can pin. Most of what a supervisor would do is conditional edges, which
LangGraph does natively with a deterministic predicate. Full reasoning in
KNOWN_GAPS. Salvage `check_concentration_risk` for 2.1; discard the scaffolding.

**Scope is phased, not absolute.** Screening, candidate generation and
recommendations on un-named instruments are out of scope for Levels 1–3 and
revisited afterwards — because a system that recommends before it can compute
what is already held recommends against a wrong picture. Case 3.2 tests that
boundary and therefore has a known expiry date. Forecasts, tax, execution,
frontend and multi-user remain permanently out.

**Where non-determinism may live.** The future Equity Analyst may be uncertain
and run on a larger model; its uncertainty must not leak into deterministic
components. Its output crosses the contract boundary marked as opinion via
`confidence`, `reasoning` and `warnings` on `PortfolioResult`. Its instrument is
the Phase 4 eval set, not the golden set.

**Allocation and P&L are separate commits.** Shared inputs are not the same as
one concept; three documents split them the same way, and the commit message
needs an "and".

---

## 6. Where we stand against the benchmark

**Zero of the twelve cases pass.** Routing is correct for all of them, and for
1.1 and 1.4 the numbers are now computed correctly and sit in `shared_data`.
They are invisible because the synthesizer has no branch for them.

Every Level 1 query still returns:

    Analysis complete. See details below:

    DataAgent: ✓

    PortfolioAnalysisAgent: ✓

The architecture is sound and this should not be re-litigated. The gap is the
last mile of Level 1 plus the capabilities of Levels 2 and 3.

---

## 7. Next steps, in order

### 1. Synthesizer branches for `data_fetch` and `risk_analysis`

**The single blocker on every Level 1 case.** `synthesizer_node` dispatches on
**intent** at `nodes.py` (search `def synthesizer_node`), and those two intents
have no branch. **It does not dispatch on `result_type`** — an earlier diagnosis
said it did and was wrong.

The formatters must not compute anything. An agent computes; the synthesizer
formats. For 1.1 that means reading `shared_data["allocation"]["by_asset_class"]`
and rendering it; for 1.4, `by_sector`.

### 2. The benchmark case runner

Ships **with** item 1 above, per the KNOWN_GAPS entry. `tests/benchmark/run_cases.py`,
one query per case, printing `n/12`. Assert on `shared_data`, which is structured
and deterministic; assert weakly on the prose (does it contain the figures at
all). Do not use a judge model — that is a non-deterministic instrument measuring
a deterministic component. `cli.py:132`'s "NO NUMBERS IN ANSWER" check is the
weak assertion already written, currently printing instead of failing.

Not part of `pytest`: the cases cost API calls and minutes. It is a third loop.

### 3. Position P&L

`compute_position_pnl` goes in `quant/allocation.py` beside the existing
helpers — `_market_values` and `_cost_bases` are exactly its inputs, so it adds a
function rather than modifying one. Check against `expected_values.md` Part 1.
Per D4 it is **price return**, forced by the data model: `Dividend` has no
`portfolio_id`.

Before wiring anything to `get_portfolio_summary`, fix `get_portfolio_value`
(`portfolio_manager.py:557`) to **raise** rather than log-and-skip on a missing
price. It currently shrinks the denominator silently.

### 4. Portfolio volatility

Check against `expected_values.md` Part 4 (10.2936%). Per D7, none of the five
existing volatility implementations computes portfolio-level vol; a new
`portfolio_volatility(weights, cov_matrix)` goes in `quant/risk_metrics.py`.
`shared_data["volatilities"]` now carries floats, so no parsing is needed.

### 5. Data-age reporting

Benchmark 3.3. Build it into the output contract rather than retrofitting.
`latest_prices` is the previous settled close, reported as current with no as-of
date, and the cache means it can be up to two closes behind.

### Later, with reasons

- **Generate the agent roster from a registry.** It is restated in **eight**
  places. Do it before the seventh agent, not now.
- **Base-agent deduplication.** Do it when Risk and Compliance arrive, and wire
  `trace_tool` and `log_delegation` at the same time (benchmark 2.1 cannot pass
  without them).
- **README rewrite.** Keep its Design Principles section. Note it describes
  RiskManagerAgent as an active supervisor, and on that one point it is
  *accurate* — do not delete the true sentence with the false ones.
- **`out_of_scope` router intent.** Benchmark 3.2.
- **The five remaining unguarded test files**, and `test_portfolio_integration.py`
  which does not assert.
- **Delete `src/portfolio_tool/rag/`**, `alembic.ini` path, `data_manager.py`
  config path, CostCalculator pricing table, `.gitignore` rewrite.

---

## 8. Rules learned the hard way

**Both instruments have blind spots, and the CLI is the third one.**
`run_golden.py` prints five routing fields and nothing else — no answer content,
no numbers. `pytest` passes on tests that never assert. The price-cache bug that
was wrong for four of nine assets passed pytest, applied cleanly, improved
latency, and was caught only by reading the CLI's provider-call output.

**A prompt change is a specification change, and it must be measured.** Adding
the sixth agent bled into two unrelated queries on the first attempt. The golden
set caught it in forty seconds. Never accept a mixed diff because the good part
is visible; narrow and re-run. Then run it **twice** — a case that only works
most of the time counts as failed.

**Fields that look like they control something often do not.** `model_name`,
`ANTHROPIC_SONNET`, `log_tool_calls`, `max_tool_calls_per_turn`,
`hawkish_threshold`, and `result_type` all read as live and are not. `DATABASE_URL`
was on this list until 4 September. Grep before believing any of them.

**The recurring bug shape is repair-instead-of-raise.** A wrong answer with a
plausible face rather than an error. `PRICING.get(model, PRICING["gpt-4-turbo"])`,
`fed_confidence = 0.5`, the scraper's `soup.body.get_text()` fallback,
`get_portfolio_value` skipping unpriced tickers, `data_manager` warning about a
missing `config.toml` and continuing.

**Capability exists, wiring does not.** `conversation_history`, `ToolTrace`,
`log_delegation`, `get_portfolio_summary`'s P&L arithmetic, and the `confidence`
/ `reasoning` / `warnings` fields on `PortfolioResult` are all built and
unconnected. Nothing fails when the connection is missing, which is why they
survive.

**Duplication is found by breaking it, not by reading.** The roster entry in
KNOWN_GAPS enumerated seven sites and missed the eighth — the Pydantic enum that
then broke the run.

---

## 9. Quick reference

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
| `pytest` | ~30s | Do the components still work |
| CLI | ~3s | What is it actually doing |
| Golden set | ~40s, cents | Did routing change anywhere |

`golden set → change → golden set → commit`. When the diff changes, decide
whether it is an improvement **before** updating `expected.txt`.

A fourth loop arrives with the synthesizer: the benchmark case runner, `n/12`.
