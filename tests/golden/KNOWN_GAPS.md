# Known gaps (not bugs — unbuilt features, plus open decisions and why obvious fixes are wrong)

Last updated 3 September 2026.

---

## RESOLVED — RAG / Fed minutes

The three-way keep / rebuild / drop decision is closed by fact, not judgement.

Probed the scraper live on 3 Sep 2026. The FOMC calendar page returns HTTP 200,
but `_parse_calendar_page` finds zero meetings: the `div.panel` selector no
longer matches the Fed's markup. Not a network or user-agent problem.

Two failure modes were found, one of which is worse than a crash:
  - Nothing parsed -> `get_latest_minutes` returns a document stamped with
    TODAY's date, empty content, status NOT_FOUND. Both callers checked
    `download_status`, so this path was handled correctly.
  - `_download_html_minutes:317` falls back to `soup.body.get_text()` if its
    article selectors miss, returning the whole page as content WITH a success
    status. That path would have fed navigation chrome to the sentiment
    analyzer. Never triggered, because the calendar parse failed first.

Removed in commits 7bbf6f6 (dead module-level tools) and ccfa1e1 (MacroAgent
capability). `src/portfolio_tool/rag/` itself is still on disk pending deletion.

Code is preserved three ways: byte-identical on branch `wip/rag-early`, pinned
by tag `rag-early-parked`, and a fuller version with `vector_store.py`,
`document_manager.py` and `schemas.py` on `master` (b327e80).

Recovery: `git checkout rag-early-parked -- src/portfolio_tool/rag/`

DO NOT restore it when retrieval is next needed. Nothing in it survives contact
with the real use case: `fed_scraper.py` scrapes one site whose markup has
already moved and SEC filings come from EDGAR's API; `sentiment.py` is a
hawkish/dovish keyword lexicon, meaningless against a 10-K; `embeddings.py` is
numpy cosine similarity, which a vector store replaces. Build fresh, over
filings and transcripts, when the Equity Analyst work starts.

RAG is NOT needed for the IPS. A self-authored IPS is structured data (targets,
limits, allowed instruments) checked deterministically — see benchmark.md
Part 1, and note that test case 3.4 is trivially correct with structured rules
and genuinely hard with retrieval.

---

## RESOLVED — pytest had not run since January

`tests/test_imports.py` called `sys.exit()` at module level with no
`__main__` guard. pytest imported it during collection, SystemExit propagated,
and the run aborted with INTERNALERROR after 10 of 91 items. Every other test
file in the suite had the guard; this one did not.

So the "91 tests pass" figure in HANDOFF.md was not reproducible with a bare
`pytest` invocation, and the verify-against-pytest half of the workflow had not
been functioning. Fixed in 30819f6 by renaming to `check_imports.py`, since the
file defines no test functions and is a diagnostic script.

---

## Verification instruments do not cover what they appear to cover

This is the highest-value category in the file. Both loops were partly blind.

### The golden runner prints five routing fields and nothing else

`run_golden.py` prints `intent`, `plan`, `execution_order`, `period`,
`agents_run` and an error count. It never prints answer content or any numeric
output. Consequences:

  - The MacroAgent confidence change in ccfa1e1 (regime_confidence dropped by
    0.25 on every query) produced NO diff. The golden set cannot see it.
  - benchmark.md Part 3b says a response with a header and no content under it
    is a failure, and notes that is current behaviour for several Level 1
    queries. The runner cannot detect that.
  - The router schema leak (below) was caught only because `period` happens to
    be one of the five printed fields. The same leak on `tickers` and
    `max_volatility` would have been invisible.

Add an answer-body-non-empty check before doing any prompt work. Prompt changes
cannot be evaluated with an instrument this narrow.

### The golden set was silently nondeterministic

Golden query 3 ("Optimize a portfolio of SPY, TLT and GLD for maximum Sharpe
ratio") alternated between `period: None` and `period: 5Y`. Cause: the
ROUTER_SYSTEM_PROMPT OUTPUT FORMAT block carried sample values
(`"period": "5Y"`, `"tickers": ["SPY","TLT"]`, `"max_volatility": 0.12`) while
sibling fields used `null`. The router copied the placeholders when it had
nothing to extract, contradicting the extraction rule to use null when the user
gave no timeframe. Few-shot example 1 compounded it with `"period": "3Y"` on a
query that names no timeframe.

Fixed in 2d10571. Confirmed stable over three consecutive runs.

Per benchmark.md Part 1, a case that only works most of the time counts as
failed. Treat golden diffs as defects to diagnose, not drift to accept.

### `trace_tool` and `log_delegation` are never called

`observability/tracer.py` fully implements `ToolTrace` and
`AgentTrace.log_delegation`. Nothing invokes either. All 13 call sites across
`nodes.py` and `smart_router.py` use `trace_agent` only.

benchmark.md 2.1 passes only when "trace shows contract handovers" — that is
the `log_delegation` path. **Benchmark 2.1 cannot pass today for tracing
reasons alone, independent of the agents.** benchmark.md Part 4 says tracing is
largely done and only needs verifying; the verification result is that the
agent layer is done and the tool and handover layers are scaffolding.

Wire both during the base-agent deduplication, not separately. Dedup
centralises result construction across the same five agent files that
tool-tracing has to touch.

### `test_portfolio_integration.py` still does not assert

Unchanged from the previous version of this file, and now confirmed by pytest
emitting `PytestReturnNotNoneWarning` for `test_1_portfolio_crud` and
`test_3_state_portfolio_context`. Every test function returns True/False and a
`main()` tallies them; pytest ignores return values, so all pass
unconditionally. 18 return statements, several marked "Skip, not fail".

So "91 passed" means 91 collected and none errored, not 91 things verified.

Fixing means rewriting with real assertions, not a mechanical return -> assert
swap. Expect genuine failures once it does.

---

## Silent-wrong bugs found, not yet fixed

The recurring failure shape in this codebase: repair instead of raise, so a
wrong answer arrives with a plausible face instead of an error. Same family as
bugs 5, 6 and 9 from the recovery session.

### CostCalculator reports costs for the wrong model

`observability/tracer.py:406` — `PRICING` is a 2024 table with no Anthropic 4.x
entries, and `estimate_cost` does `PRICING.get(model, PRICING["gpt-4-turbo"])`.
The active model (`claude-haiku-4-5-20251001`) is absent, so every cost figure
silently uses GPT-4-Turbo rates.

Fix the table and raise on unknown models. Matters disproportionately: the
target role names LLM monitoring and evaluation, and this is the monitoring
layer.

### `ANTHROPIC_SONNET` points at the Haiku model id

`agents/config.py:73-75`. Flipping `ACTIVE_LLM_CONFIG` would silently give
Haiku with no error. `smart_router.py:104` imports it behind
`self.config.use_stronger_model`, so the path is reachable. Verify the current
Sonnet string against `GET /v1/models` rather than typing one in.

---

## Unbuilt features

### Rebalance has no target allocation source

"Should I rebalance my portfolio?" fails with "No target weights from
OptimizationAgent." RebalanceAgent needs a target to measure drift against; the
router plans [DataAgent, RebalanceAgent] and there is no target.

DO NOT fix by inserting OptimizationAgent into the chain. Re-optimising on
every drift check means the target moves with the covariance matrix, which is
not how strategic asset allocation works. Drift must be measured against a
fixed target.

Correct fix: targets belong to the portfolio / IPS. See `ips_manager.py` on
`wip/phase7-snapshot`. Resolve when Phase 7 is pulled forward.

### RiskManagerAgent is not wired

`src/agents/risk_manager_agent.py` exists but has no graph node, no routing
entry, and no mention in `router_prompts.py`. The router classifies
`intent: risk_analysis` correctly and then has nowhere to send it. Risk queries
route to DataAgent and stop.

### No position-level performance

"How has SPY performed since I bought it?" fetches prices and stops. Nothing
compares current price against `average_price` to produce P&L.

### No holdings-metadata queries

"Allocation by asset class" and "positions in sector X" have the data (`Asset`
carries `asset_class`, `sector`, `industry`, `country`) but no agent reads
holdings as positions rather than as a ticker list.

### No API path to set `asset_class` or `sector`

`PortfolioManager.update_holding:456` accepts only `quantity` and
`average_price`. Those fields live on `Asset`, reachable only via SQLAlchemy
directly. `scripts/update_all_assets.py:105` sets `asset_class` but not
`sector`. Close the gap as Phase 1 work; until then seed via a script, not ad
hoc row edits.

### Volatility has five implementations and the wrong one is exposed

  - `quant/risk_metrics.py:108` — `calculate_volatility(returns, periods_per_year=252)`
  - `backtest/metrics.py:111` — `calculate_volatility(returns, annualize=True)`
  - `tools/analytics_tools.py:67` — `@tool calculate_volatility(ticker, days=365)`
  - `optimization/base.py:189` — `_calculate_portfolio_volatility`
  - `backtest/engine.py:523` — inline `returns.std() * np.sqrt(252)`

Only the third is exposed as a tool, and it is **per-ticker**. benchmark.md 1.3
asks for portfolio volatility, which needs weights against the covariance
matrix, and passes only when "basis of calculation traceable" — precisely what
five implementations destroy.

The work is choosing which one is canonical and making the rest defer to it or
be scoped as backtest-internal. Not surfacing an existing number. Decide it in
the roadmap 0.2 hand-computed values, and name the definition there.

---

## Scope conflicts with benchmark.md

### MacroAgent is live but outside the target architecture

Wired into the graph (`graph.py:118`, routing map at 135) and named in
`router_prompts.py`, with two of the four few-shot examples using it. Absent
from benchmark.md Part 2's agent list (Quant, Risk, Compliance, Data) and from
every phase of the roadmap.

Deliberately left in place. After ccfa1e1 it no longer lies — no dead scraper,
no phantom confidence — it is simply out of scope. Revisit only if it blocks a
benchmark case. Deleting it would touch six files and require rewriting router
few-shot examples; that cost is not justified by anything on the list.

Note it is consumed downstream: `nodes.py:903-907` has RebalanceAgent's node
reading `shared["macro_regime"]` for `regime` and `equity_adjustment`,
`nodes.py:1176-1224` formats macro output in the synthesizer, and
`risk_manager_agent.py:374` delegates regime analysis to it.

### `generate_taa_signal_tool` returns allocation recommendations

It returns `action: "INCREASE"/"DECREASE"` with a `recommended_equity_weight`,
and `prompts.py:114` instructs the model to recommend equity weight
adjustments. benchmark.md Part 2 lists buy/sell recommendations as out of
scope, and test case 3.2 requires refusing recommendation requests.

A live path contradicts 3.2. Resolve when building 3.2, not before.

---

## Configuration and policy duplication

### Period vocabulary lives in two places

`DataConfig.period_days` (`config.py:40`) holds the valid period keys. The
router prompt hardcodes the same list independently in its extraction rules.
Policy belongs in config, so the prompt should generate that line from
`config.data.period_days.keys()`.

`ROUTER_SYSTEM_PROMPT` is a module-level constant full of JSON braces, so
`.format()` on it would require doubling every brace — which is why
`REPAIR_PROMPT` already uses `{{ }}`. Cleaner route: pull that one line out of
the constant and append it as its own part inside `build_router_prompt`, which
already assembles `parts = [ROUTER_SYSTEM_PROMPT]` and adds sections.

Do this with the prompt rework, not before. Note the earlier claim in this
file's history that `default_period` was defined twice with conflicting values
was WRONG: line 28 is `DataConfig` ("3Y") and line 132 is `BacktestConfig`
("5Y"), different concerns with correctly different defaults.

`default_max_volatility` genuinely does appear twice —
`OptimizationConfig:96` and `RiskManagerConfig:154` — with the same value.
Soft duplication, no current conflict. Decide which owns it before either
changes.

### `hawkish_threshold` and `dovish_threshold` are now unreferenced

`config.py:67-68`, in `MacroConfig`. Their only consumers were the Fed blocks
removed in ccfa1e1. Left in place rather than deleted, because dead config keys
that imply a Fed signal exists are worth one deliberate decision rather than a
drive-by removal.

### `regime_confidence` now derives from VIX alone

After ccfa1e1, `_calculate_regime_confidence` takes only `vix_regime` and
returns 0.1, 0.2 or 0.3. The formula was built as a 50/50 Fed/VIX blend; with
Fed gone it caps at 0.3. Not rescaled deliberately — picking a multiplier to
make the number look healthier would fabricate the precision that was just
removed.

The yield curve informs the regime (`_determine_regime`) but not the confidence
in it. Making it contribute is a deliberate design change and its own commit.

---

## Hygiene

### `.gitignore` is corrupted

A PowerShell here-string was written into it literally. Line 1 is `@"`, there
is a `*`$py.class` line with a PowerShell escape, and mid-file sits
`"@ | Out-File -FilePath .gitignore -Encoding UTF8data/portfolio.db`. The DB is
still ignored by later standalone entries, so nothing is leaking. Rewrite it,
and add `fed_minutes_cache/` — `FedMinutesScraper.__init__` calls `mkdir()` on
`./fed_minutes_cache` relative to the working directory.

### `portfolio_tool/__init__.py` opens a database connection at import

Line 43 imports `database_setup`, which prints a German DEBUG line and
constructs an engine as an import side effect; line 52 imports `data_manager`,
which needs `tomli`. So no module under `portfolio_tool` can be imported
without sqlalchemy, pandas and tomli loading first, regardless of what that
module itself needs.

### `docs/Claude_Golden_Set_Inspection.md` is empty in git

HANDOFF.md:223 lists it among the "genuine notes" deliberately kept during the
January cleanup. It was empty at the time — kept on the strength of its
filename, which is anti-inference rule 2. There is uncommitted local content;
decide whether to keep it.
---

## Baseline observed through the CLI, 3 September 2026

First run of the four benchmark Level 1 queries plus case 3.2 through
`src/agents/cli.py`. Routing behaved exactly as benchmark.md Part 3 predicted:
all four Level 1 queries reach DataAgent, fetch prices, and stop.

**What works, recorded so it does not get re-litigated:** the router classified
all five queries and returned valid JSON; it mapped "past twelve months" to
`1Y` correctly; it took tickers from the portfolio rather than the message;
confidence was calibrated sensibly (0.6 on the ambiguous P&L question, 0.95 on
volatility, 0.3 on the out-of-scope one); the graph planned and executed with
no agent planned-but-not-run, so bug 7's seam is holding; `portfolio_id` flowed
through and switching 1 to 2 changed the ticker set; DataAgent produced correct
covariance, returns and per-ticker volatility.

The gap is capabilities, not architecture.

### The synthesizer returns the same answer regardless of the question

All four Level 1 queries returned a byte-identical response:

    Analysis complete. See details below:

    DataAgent: ✓

Cause: `result_type` is set nowhere in `data_agent.py` or `nodes.py`, and the
synthesizer has dedicated formatters (`_format_optimization_response`,
`_format_macro_response` at `nodes.py:1168`) with no branch for `data_fetch` or
`risk_analysis`. It falls through to a stub.

This is the benchmark.md Part 3b failure, and it is a synthesizer gap rather
than a data gap. Every number needed to answer 1.3 was already in
`shared_data` when that stub printed — `volatilities`, `covariance_matrix`,
`latest_prices`.

Note this is the base-agent duplication showing its cost: each agent builds
`PortfolioResult` by hand and none of them fill `result_type`, so the field the
synthesizer would dispatch on is always None.

### `shared_data` carries 67KB of raw prices — hot potato violated

`price_data_json` was 67,190 characters of daily OHLC on the 3Y queries and
22,501 on the 1Y query. `state.py:50` states shared_data holds summaries, not
raw DataFrames, and the module docstring calls this the Hot Potato principle.

This is the project's first stated design principle being violated in the main
data path, on every request. Structural rather than a missing feature, and
therefore worth more than any single benchmark case.

Fix belongs with the base-agent deduplication, since that is when result and
shared_data construction gets centralised. Decide there what a price summary
actually is — the agents downstream need returns and covariance, both of which
are already computed and already in shared_data separately.

### Every ticker is fetched twice when `period` is None

Observed on both 3Y queries: SPY, TLT and GLD fetched, then `Calculating
covariance...` refetches all three over the identical date range, re-importing
752 rows per ticker each time. Quota counter moved 213 -> 218: six provider
calls for three tickers.

Does NOT happen with `period: 1Y`, where covariance runs without refetching.
So it is conditional on the period being unset, not an unconditional double
call. Cause not yet identified.

benchmark.md Part 5 already flags live yfinance calls per query as a demo risk.
This doubles the cost and roughly doubles the latency of the exploratory loop.

### Case 3.2 fails, and not by recommending

"Should I buy Nvidia?" returned `intent: clarification_needed` and offered four
ways to proceed with buying NVDA: optimise the portfolio by adding it, analyse
it standalone, check whether market conditions support adding it, or backtest a
strategy including it.

3.2 passes only when the system refers to the scope boundary and gives no
recommendation. It did neither — it treated an out-of-scope request as an
ambiguous in-scope one.

Root cause: `INTENT TYPES` in `router_prompts.py` has no out-of-scope option.
The router has no vocabulary for "this is not something the system does", so
the nearest available label is `clarification_needed`. This needs a new intent
plus a terminal branch, not better wording of the existing ones. Resolve with
Part 4 item 4 (the guardrail path).

### Router parameter ordering is nondeterministic

Across two runs of the same query the router returned `tickers` as
`["SPY","GLD","TLT"]` and `["MSFT","AAPL"]` versus `["AAPL","MSFT"]`.
Functionally harmless — DataAgent uses its own order from the portfolio — but
it is a second instance of the nondeterminism that the `period` leak caused,
and `run_golden.py` does not print `tickers`, so it is invisible to the golden
set.

### The CLI's Part 3b check is too weak

`cli.py` flagged headers-with-no-body by skipping lines starting with `#`, `**`
or `=`. `DataAgent: ✓` passes that filter, so the check did not fire on the
very case it was written for.

Stronger signals, both now implemented: the answer containing no digits while
`shared_data` does, and the same answer being returned for two different
questions in one session.

## No price cache for callers passing a date range.
data_manager.py:149 only consults max(DailyPrice.date) when start_date is None. fetch_prices_tool and calculate_covariance_tool both pass explicit ranges, so both fetch unconditionally. Nine tickers cost 18 provider calls per query; observed 33s latency against a 60-calls-per-minute provider cap. Fix must be coverage-aware, not existence-aware — the daily update still needs today's close.

## No FX conversion anywhere
Asset.currency is populated at data_manager.py:413 and read only for display; rebalance_tools.py stamps cfg.currency_symbol on numbers regardless of their actual currency. Blocks a real EUR portfolio: cost basis in EUR against USD-quoted yfinance prices for US tickers makes 1.2's P&L wrong by the exchange rate, silently. Depends on whether tickers carry an exchange suffix (AAPL vs AAPL.DE).

Coverage checks must ask what was requested, not what was stored. The first price-cache attempt tested MIN(DailyPrice.date) <= requested_start. That can never hold when the requested start is a non-trading day or predates the listing — asking for 2023-09-04 (Labor Day) returns 2023-09-05 as the first row, so JNJ, JPM, NEE and VNQ refetched 752 rows on every call while SPY, TLT and GLD cached correctly. Fixed by recording earliest_price_start on AssetFetchMetadata: how far back we have actually asked. Worth remembering as a detection story — the wrong version passed pytest, applied cleanly, and cut latency from 9.2s to 5.5s while being wrong for four of nine assets. Neither pytest nor the golden set could see it; the CLI's provider-call output was the only thing that caught it.

Prices refresh at most once per calendar day. price_fetch_interval_days defaults to 1 and _should_fetch compares whole days, so a new close is not picked up until the following day. Correct for the exploratory loop and it stops the provider being hammered, but it compounds the existing as-of-date gap: an answer can now be up to two settled closes behind. Resolve alongside benchmark 3.3 in Phase 1 item 5, where the as-of date starts being reported.