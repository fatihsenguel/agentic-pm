# AGENTIC_FINANCE — Session Handoff

**Session date:** 4 September 2026 (second sitting)
**Branch:** `baseline-v1`
**State:** Green. 105 tests passing, golden set stable over four consecutive runs, working tree clean. For the benchmark count, run `python tests/benchmark/run_cases.py` — it is not quoted here, because it changes on every capability commit and this line was stale twice in two days.

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

**Twenty-nine commits, 7 September.** Two capabilities and about twenty document
corrections. All four loops green at the end: 105 tests, empty golden diff,
2/12 on the runner, CLI verified by hand.

**Data-age reporting, built (roadmap item 5).** `as_of_dates` per ticker from
`data_agent.py`, `.index[-1]` on the same expression that already produced
`latest_prices`. `portfolio_analysis_agent_node` reduces them to a worst case and
publishes `allocation.as_of`; the synthesizer renders it. **1.1 and 1.4 moved
from FAIL to PASS — the counter's first real movement.**

**The runner's as-of check was replaced in the same commit that built the
field**, deliberately, so the two cases could not flip to PASS on the old
date-shaped regex and leave nobody able to tell which had happened. It now
asserts the structured value, that it is a date, and that that exact string
reaches the answer.

**The volatility window anchor, built on the third attempt.** Fetch window is
`[today - N - _FETCH_MARGIN_DAYS, today]`; evaluation window is the last
`years x trading_days_per_year` closes, trimmed before the frame is cached so
covariance, returns and the per-name volatilities all read it. Verified live:
756 closes exactly, ending at Friday's close rather than at Labor Day.

**Two of the three attempts failed, and how they failed is the useful part.**
The first was arithmetically inert — a post-fetch trim cannot drop rows, because
the frame arrives bounded by the fetch window. It passed `pytest`, the golden set
and the runner, and would have shipped as a fix. The second split the
`_prices_df_cache` key namespace by rebinding `period`; only the golden set's
`errors` field caught it. **Neither would have been caught by reasoning about the
code, and one was not caught by three of the four loops.**

**About twenty document corrections**, including two that were wrong in this
file, one in `expected_values.md` and two in the roadmap. Listed in §5.

---

## 5. Decisions taken this session

**As-of is per holding at the source, reduced for aggregates by the agent.**
`benchmark.md` Part 3b settles the shape — a date for every figure derived from
market data. The reduction is computed in `portfolio_analysis_agent_node`, not
the synthesizer, because anything the synthesizer derives exists only as text and
the runner cannot assert on it. Compliance will need the same number.

**The stalest holding is named only when the dates differ.** `min` returns the
first minimal element, so on the normal case — nine holdings, one close — naming
a ticker invents a staleness distinction that does not exist.

**D8 is a count of closes, not a calendar year.** 252, because that is D6's
annualisation factor and D5's observation count, so the window and the
annualisation cannot drift apart. Stated as "one calendar year" before, which is
the same thing only on average and is exactly what the code was implementing when
it came up short.

**Item 4's check is a pytest fixture, not a live comparison.** 10.2936% belongs
to a window whose end has passed and no live run reaches it again. The fixture
holds the 252 closes extracted from `expected_values.xlsx` and committed — not
read from `data/portfolio.db`, which is untracked and would not survive a fresh
clone. Same pattern as `test_allocation.py`.

**The fetch margin is not policy and is not in config.** Policy is something you
would want to set differently; nobody has a preference about a fetch margin. It
exists only because the fetch precedes knowledge of the last settled close. Named
constant in `data_agent.py` with its reasoning attached. Its value need not be
right, only sufficient, because a shortfall raises.

**The benchmark count is no longer written in this file.** It changed on every
capability commit and was stale twice in two days. §0 says to run the runner;
a number copied into prose is the belief that outlives its evidence.

**Deferred, with reasons, in KNOWN_GAPS:** spans versus counts for non-year
windows; `group_by`/`filter` weighed against a `sector` field; whether the router
stays a classifier or becomes a tool-caller. Each has a written reason for
waiting and a note on what decides it.

**Direction for `quant/`:** one tested implementation per formula, reachable from
anywhere, never restated in a document. D8 claiming the code matched when it did
not was that rule being broken.

---

## 6. Where we stand against the benchmark

```bash
python tests/benchmark/run_cases.py
```

The count is deliberately not written down here. §0 says to run the runner before
believing anything about what works, and a number copied into prose is exactly
the belief that outlives its evidence. What follows is the shape of the gap,
which moves more slowly than the count.

**1.1 and 1.4 pass** as of the data-age commit. Every assertion holds against
portfolio 3: labels, percentages summing to 1.0, all four cost bases against
Part 2, Technology at 80,000 with AAPL and MSFT, unsectored reported at 147,000
rather than dropped, sectored at 137,500, all nine tickers, cash inside the
denominator with no percent-invested, the figures reaching the prose, and an
as-of date asserted from `shared_data` rather than matched as a date shape in
the answer.

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
D8's rule today.

**It is not a change inside `_calculate_period_dates`.** That function runs
before the fetch — line 427 computes the dates, 432 fetches against them, 437
reads against them — so the dates it returns are what bounds the fetch that
discovers the last settled close. It cannot know that date. Reading the database
maximum before fetching would bound the fetch by yesterday's data and never pick
up a new close.

Separate the two windows, which is most of the fix:

- The **fetch window** bounds what is asked of the provider and the database. It
  ends at today, and must, because that is the only way a close that landed
  since the last run is picked up at all.
- The **evaluation window** is what the figures are computed over. It ends at
  the last close that actually settled, which is `prices.index[-1]` and is not
  known until the frame is in hand.

One date range is currently doing both jobs, and that is the bug.

**A post-fetch trim alone does nothing. Tried and reverted, 4 September.** The
frame arrives bounded by the fetch window, so every row is already
`>= today - N`. The evaluation start is `last_close - N`, and since
`last_close <= today` that is always `<= today - N`. The filter's lower bound
sits at or below the frame's first row every time, and it drops nothing. Zero
rows removed on both 1Y and 3Y.

The direction was wrong too. The window is one trading day **short** at the
front — 251 closes against D8's 252 — so the missing day was never fetched, and
no trim adds rows.

**The fetch window has to be wider than the evaluation window.** Built
4 September:

- fetch `[today - N - _FETCH_MARGIN_DAYS, today]`
- trim to the last `years x trading_days_per_year` closes, before the frame is
  cached, so covariance, returns and the per-name volatilities read the
  evaluation window

**The evaluation window is counted in closes, not calendar days.** That is what
Part 4 computes — 251 returns from 252 closes — and what D6 annualises by.
`tail` is anchored to the end of the frame by construction, so the last settled
close needs no arithmetic and no calendar. Measured: 252 closes and 251 returns
at 1Y, matching D8's shape.

**An earlier draft of this section said the margin is policy belonging in
`DataConfig`. It is not.** Policy is something you would want to set
differently; nobody has a preference about a fetch margin. It exists only
because the fetch has to happen before the last settled close is known. It is a
named constant in `data_agent.py` with its reasoning attached, and config keeps
holding the things that are actually choices — `trading_days_per_year`,
`period_days`. A margin in the config file would only make config the place
fudge factors go to look legitimate.

Its value does not need to be right, only sufficient: 30 days buys 22 to 37
closes of headroom across 1Y through 10Y, and a shortfall **raises** rather than
silently narrowing the window. That raise is the point. The trim-only version
had no symptom, which is how it passed pytest, the golden set and review.

Item 1 shares no seam with this —
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
