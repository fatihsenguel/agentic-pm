# AGENTIC_FINANCE — Session Handoff

**Session date:** 4 September 2026 (second sitting)
**Branch:** `baseline-v1`
**State:** Green. 105 tests passing, golden set stable over four consecutive runs, working tree clean. **Benchmark: 0/12 passing, 3 failing, 9 blocked** — and for the first time that number is produced by a program rather than by reading CLI output.

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
| `tests/golden/KNOWN_GAPS.md` | Open decisions, resolved decisions, and why obvious fixes are wrong. 29 open entries. Long, and the most useful file in the repo. |
| `tests/golden/expected_values.md` | Hand-computed expected answers for portfolio 3, plus eight decisions (D1–D8). `expected_values.xlsx` alongside it holds the formulas and the 252 closes. |
| `docs/PM-Assistant — Roadmap.md` | Phased plan. Carries a header listing superseded points. Its ordering is now overridden by §7 below, which follows the counter. |

**Do not update `expected_values` to match code output.** If they disagree, one
of the two is wrong and that gets resolved deliberately. There is a live
disagreement right now — see §7 item 2.

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
  imports inside function bodies.
- Never infer a module's purpose or dependencies from its name.
- One change per commit. **If the commit message needs an "and", it is two
  commits.**
- Verify with `pytest` and the golden set as **separate commands** — not chained
  with `&&`, which hides failures.
- Do not paste multi-line blocks containing interactive commands or trailing `#`
  comments into zsh; both get eaten. Patches: `git diff -U0` and
  `git apply --unidiff-zero`, with `--check` first. Note `git commit -am` does
  not stage a new file.

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

**Caveat on "105 passing":** `test_portfolio_integration.py` returns booleans
instead of asserting, so its seven blocks pass unconditionally, and TEST 7
returns `True` in both branches. 105 means 105 collected and none errored, not
105 things verified. 14 of the 105 are `test_allocation.py`, which does assert
against hand-computed figures — and which is now the **only** place exact
market-value figures are checked. See §7 item 1 for why they are not in the
benchmark runner.

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

Fourteen commits. Roughly: corrected the documents, closed the last mile of
Level 1's computation, and built the scoreboard.

**Corrected six document claims that were wrong.** The holdings gap moved to
RESOLVED; the synthesizer entry was corrected to "no longer blocked, still open"
rather than resolved; the roster heading became eight to match its own body; the
stamp date, the migration count (eleven, not ten) and the runner entry were
fixed. Line-number references in touched entries became symbol names, because
`nodes.py` is 1500 lines and every commit moves them.

**Added synthesizer branches for `data_fetch` and `risk_analysis`.** Two
commits, two formatters, reading `sub_results["PortfolioAnalysisAgent"]` rather
than `shared_data` — `mark_agent_complete` stores the node's result verbatim, the
allocation object is already on it, and every existing formatter takes
`sub_results`. `shared_data` is the channel between agents, not a second input to
the synthesizer. Neither branch moved the golden set, as expected: the runner
prints five routing fields and the synthesizer runs after routing.

**Fixed a defect introduced by those branches.** The risk formatter reported a
window it never named, so a query with no timeframe returned three-year figures
under an unlabelled heading. `data_agent.py` already builds the observed range
and observation count and both were being discarded. Now rendered, and it falls
back to saying the window is unreported rather than omitting it.

**Built `tests/benchmark/run_cases.py`.** Twelve cases, one query each,
PASS/FAIL/BLOCKED, printing n/12. Blocked cases probe for the capability they
need rather than declaring themselves blocked, so they unblock automatically; a
case that unblocks with no check written reports FAIL saying so.

**Recorded six new findings** in KNOWN_GAPS at session end, plus two during the
session because they gate queued work.

---

## 5. Decisions taken this session

**The synthesizer reads `sub_results`, not `shared_data`.** Confirmed against
`mark_agent_complete`, which stores the result dict verbatim. Not a trade-off —
`sub_results` is already the synthesizer's input contract.

**The `data_fetch` branch prints both breakdowns.** `ExtractedParameters` has no
`sector` field, so nothing in the decision distinguishes benchmark 1.1 from 1.4.
Defaulting to asset class would answer 1.4 with the wrong table; inspecting the
query text would put classification in the synthesizer. Printing both is never
wrong, needs no prompt change, and narrows later. The CLI's identical-answer
check fires on it, which is the instrument correctly reporting the stopgap.

**The benchmark counter uses the strict definition.** Full Part 3b compliance,
including data age, asserted from the start. The counter reads 0/12 rather than
reporting a number the benchmark's own text does not support. A counter that
drifts ahead of its definition is the same failure shape as everything else being
removed here.

**Exact market-value figures are not asserted in the runner.** They stay in
`test_allocation.py`, where fixed inputs make them stable. Market values move
with prices, `expected_values.md` is pinned to the 2026-09-02 closes, and no seam
exists to pin a run against a date. The runner asserts what does not move:
structure, invariants, static cost bases, the ticker set, whether the figures
reached the prose, and whether Part 3b's as-of date is stated. This corrected an
earlier KNOWN_GAPS entry that specified the expiring assertion.

**Case 3.3 is blocked on position P&L, not merely failing on the date.** It
routes `data_fetch` and returns the allocation table, so an as-of check alone
would flip it to PASS the moment item 5 attaches a date, while the answer was
still a portfolio-wide breakdown. Blocking it on `position_pnl` removes the
false-pass path.

---

## 6. Where we stand against the benchmark

```
0/12 passing, 3 failing, 9 blocked
```

**1.1 and 1.4 fail on the missing as-of date and nothing else.** Every other
assertion holds against portfolio 3: labels, percentages summing to 1.0, all four
cost bases against Part 2, Technology at 80,000 with AAPL and MSFT, unsectored
reported at 147,000 rather than dropped, sectored at 137,500, all nine tickers,
cash inside the denominator with no percent-invested, and the figures reaching
the prose.

**3.2 fails** on `intent: clarification_needed` where it needs `out_of_scope`.
**3.3 is blocked** on position P&L. **1.2 and 1.3 are blocked** on P&L and
portfolio volatility. **2.1, 2.2, 2.3, 3.1 and 3.4 are blocked** on the
Compliance agent and the IPS. **3.5 is blocked** structurally — it needs a second
turn and the runner sends one query per case.

The architecture is sound and this should not be re-litigated. The gap is the
output contract plus the capabilities of Levels 2 and 3.

---

## 7. Next steps, in order

**The ordering below follows the counter, not the roadmap.** Two of the three
failing cases fail on data age, and the two blocked Level 1 cases will fail on it
too once their arithmetic exists.

### 1. Data-age reporting (benchmark 3.3, roadmap item 5)

**The bottleneck.** Unlocks 1.1, 1.4 and 3.3, and is a precondition for 1.2 and
1.3 passing Part 3b when they arrive. benchmark.md Part 4 already promoted it to
second; the counter is now evidence rather than argument.

**It opens with a decision, not with code.** `latest_prices` is built as
`prices[ticker].dropna().iloc[-1]`, per ticker. A ticker missing the final close
reports an older price than the frame's end date, and nothing marks it. A single
`as_of` field on the output would therefore be a summary that is wrong for
exactly the holding that is stalest. Decide whether as-of is per figure, per
holding, or a stated worst case, **before** adding any field.

Note the runner's current as-of check is a date-shaped regex over the prose. When
the structured field exists, the check should assert on that instead.

### 2. The volatility window, before item 4

`_calculate_period_dates` sets `end_date = date.today()`. Observed 4 September:
`period: 1Y` returned 2025-09-04 to 2026-09-02, 251 closes, against D8's
2025-09-03 to 2026-09-02 and 252 closes. One trading day short at the front, and
it moves every day the query runs.

Item 4 checks `portfolio_volatility` against 10.2936% and will not reproduce it.
**Do not resolve that by editing `expected_values.md`.** D8 is already a trailing
window — one calendar year of daily closes ending at the last settled close — so
anchoring the code to that close implements D8 rather than competing with it.
There is no choice to make between the two; the earlier framing of this as
"anchor the code or change D8" was wrong.

What anchoring does not do is restore the 10.2936% check. That figure belongs to
a window whose end has passed, and no live run reaches it again. Item 4's check
is a pytest fixture over the 252 closes in `expected_values.xlsx`, with the
window pinned inside the fixture — no end-date parameter, no live match, and the
reference stays hand-computed. Same pattern as `test_allocation.py`, per §5. The
fixture is committed rather than read from `data/portfolio.db`, which is
untracked and would not survive a fresh clone.

Anchoring is still worth doing on its own merits: the code does not implement
D8's rule today. It is a change inside
`_calculate_period_dates`, not a new parameter: `end_date` is computed
differently, and no caller passes a date. Item 1 shares no seam with this —
item 1 adds an output field, `.index[-1]` on the expression that already
produces `latest_prices`. A caller-facing end-date parameter on
`fetch_prices_tool` is only needed to pin a run to a fixed date, which the
strict runner deliberately avoids needing. Do not build one for these two.

### 3. Position P&L (benchmark 1.2, unblocks 3.3)

`compute_position_pnl` goes in `quant/allocation.py` beside `_market_values` and
`_cost_bases`, which are exactly its inputs. Check against `expected_values.md`
Part 1. Per D4 it is **price return**, forced by the data model: `Dividend` has
no `portfolio_id`. Before wiring anything to `get_portfolio_summary`, fix
`get_portfolio_value` (`portfolio_manager.py`, search the name) to **raise**
rather than log-and-skip on a missing price.

### 4. Portfolio volatility (benchmark 1.3)

Blocked behind item 2. Per D7 a new `portfolio_volatility(weights, cov_matrix)`
goes in `quant/risk_metrics.py`; none of the five existing implementations
computes portfolio-level vol. `shared_data["volatilities"]` carries floats.

### 5. `sector` on `ExtractedParameters`

Narrows the `data_fetch` branch from both breakdowns to the one asked for. A
prompt change, therefore a specification change, therefore measured against the
golden set — which has the Technology query at `pid=2` and can see it. Expect a
diff and judge it on whether routing moved.

### Later, with reasons

- **`out_of_scope` router intent** (benchmark 3.2) — a new intent plus a terminal
  branch, not better wording of the existing ones.
- **The IPS from `wip/phase7-snapshot`** — unlocks 2.1–2.3, 3.1 and 3.4 at once.
  Wire `trace_tool` and `log_delegation` at the same time; 2.1 cannot pass
  without them.
- **Generate the agent roster from a registry.** Eight sites. Before the seventh
  agent, not now.
- **README rewrite.** Keep its Design Principles section. It describes
  RiskManagerAgent as an active supervisor and on that one point it is
  *accurate* — do not delete the true sentence with the false ones.
- **Widen the golden set to portfolio 3,** or decide deliberately that the fast
  loop stays a routing instrument. Not while the synthesizer is changing.
- **`test_portfolio_integration.py`**, which does not assert, and the five other
  unguarded files.

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
"14 assertions" figure. Prefer symbol names to line numbers, and regenerate.

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
command lines.

### The four loops

| Loop | Cost | Answers |
|---|---|---|
| `pytest` | ~35s | Do the components still work |
| CLI | ~4s | What is it actually doing |
| Golden set | ~40s, cents | Did routing change anywhere |
| Benchmark runner | ~1min, cents | How many cases pass |

`golden set → change → golden set → decide whether the diff is an improvement
→ then update `expected.txt``. The runner is per capability commit, not per
change: from here, every capability commit is expected to move the counter, and
"done" for a roadmap item means its case asserts rather than that its arithmetic
is right.
