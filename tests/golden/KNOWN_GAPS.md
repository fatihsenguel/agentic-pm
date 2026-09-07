# Known gaps (not bugs — unbuilt features, plus open decisions and why obvious fixes are wrong)

Last updated 4 September 2026.

---

# RESOLVED

## RAG / Fed minutes

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

## pytest had not run since January

`tests/test_imports.py` called `sys.exit()` at module level with no `__main__`
guard. pytest imported it during collection, SystemExit propagated, and the run
aborted with INTERNALERROR after 10 of 91 items. Every other test file in the
suite had the guard; this one did not.

**That last sentence is wrong, corrected 4 September.** Six test files define no
collectible tests and have no `__main__` guard, so all six execute at import on
every run: `test_graph_simple.py`, `test_nodes_simple.py`,
`test_portfolio_manager_simple.py`, `test_rebalance_import.py`,
`test_router_simple.py`, `test_state_simple.py`. `test_imports.py` was not the
only unguarded file - it was the only unguarded file that called `sys.exit()`.
The others run silently and nothing fails, which is why they survived. Read as
originally written, this entry would tell a future session the sweep was
finished.

So the "91 tests pass" figure in HANDOFF.md was not reproducible with a bare
`pytest` invocation, and the verify-against-pytest half of the workflow had not
been functioning. Fixed in 30819f6 by renaming to `check_imports.py`, since the
file defines no test functions and is a diagnostic script.

## The golden set was silently nondeterministic

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

## No price cache for callers passing a date range

`update_prices_for_asset` only consulted `max(DailyPrice.date)` when `start_date`
was None. `fetch_prices_tool` and `calculate_covariance_tool` both pass explicit
ranges, so both fetched unconditionally and each re-imported the same 752 rows.
Nine tickers cost 18 provider calls per query and ~9s latency against a
60-calls-per-minute cap.

This also explains the "fetched twice when period is None" observation from the
1 Sep inspection notes and the first CLI baseline: with `period: 1Y` the
covariance step happened to request a range already stored.

Fixed by skipping the provider when we have asked this far back before and
checked within `price_fetch_interval_days`, and fetching only from the newest
stored date when covered but stale. Repeat queries now make zero provider calls;
latency 9.2s -> 2.3s.

**Keep the lesson.** The first attempt tested coverage as
`MIN(DailyPrice.date) <= requested_start`. That can never hold when the requested
start is a non-trading day or predates the listing — asking for 2023-09-04 (Labor
Day) returns 2023-09-05 as the first row, so JNJ, JPM, NEE and VNQ refetched 752
rows on every call while SPY, TLT and GLD, which had deeper history, cached
correctly. Coverage has to ask **what was requested**, not what was stored, so
`AssetFetchMetadata.earliest_price_start` records how far back we have actually
asked.

That wrong version passed pytest, applied cleanly, and cut latency from 9.2s to
5.5s while being wrong for four of nine assets. Neither pytest nor the golden set
could see it. The CLI's provider-call output was the only thing that caught it.

## The CLI's Part 3b check was too weak

`cli.py` originally flagged headers-with-no-body by skipping lines starting with
`#`, `**` or `=`. `DataAgent: ✓` passes that filter, so the check did not fire on
the very case it was written for. Replaced with two stronger signals, both now
firing: the answer containing no digits while `shared_data` does, and the same
answer returned for two different questions in one session.

## DataAgent loaded holdings and discarded them

Recorded as "the single blocker under benchmark 1.1, 1.2 and 1.4". `portfolio_id`
was resolved to a ticker list for fetching and the quantities, average prices and
purchase dates were never published: nothing assigned `shared_data["holdings"]`,
and a CLI run showed only price-derived keys.

Closed 4 September by roadmap item 1, in two parts. `get_holdings` was not
projecting `purchase_date` — the column, the migration and the seed all existed
and the SELECT never read it. Then `build_holdings_summary` (in `nodes.py`,
search the name) began publishing an unpriced summary of ticker, quantity,
average_price, asset_class, sector and purchase_date to `shared_data["holdings"]`,
with `cash_balance` beside it. Unpriced deliberately: pricing it inside DataAgent
would have left item 2 with nothing to compute.

The log line and the raise that reported the gap are still in `nodes.py` under
the message "Portfolio specified but holdings not loaded". They now fire only
when a portfolio genuinely has none.

## Position P&L — RESOLVED 7 September

**Built. Do not rebuild this.** `position_pnl(holdings, prices)` in
`quant/allocation.py`, beside `_market_values` and `_cost_bases` which are its
inputs. Price return per D4. `tests/test_position_pnl.py` checks all nine rows
of expected_values.md Part 1 and the total. PortfolioAnalysisAgent computes
every position on every run and publishes `shared_data["position_pnl"]` keyed
by ticker, each with its own `as_of` - one holding, one close, nothing to
reduce. The synthesizer selects on `measure` and `tickers`; empty means all.
`check_1_2` (JPM, exactly `["JPM"]`) and `check_3_3` (all nine, exactly `[]`)
assert. 1.2 and 3.3 moved to PASS.

**The handoff's instruction for this item was wrong on inspection.** It said
to fix `get_portfolio_value` to raise before wiring anything to
`get_portfolio_summary`. Neither had a caller outside `portfolio_manager.py`;
the production flow is DataAgent -> shared_data -> the analysis node -> quant,
where `_market_values` already raises. `get_portfolio_summary` carried its
own inline P&L (a third copy of the formula, skipping unpriced holdings) and
that block was deleted instead. `rebalance_tools.py:82,89` is a fourth copy,
logged and untouched. `get_portfolio_value` is now uncalled; deleting it is
its own decision.

Not published: a portfolio-total P&L (Part 1's +110,200.50 / +38.73%). No
case asks for it.

## The router overwrote `tickers` with the portfolio after the LLM call

`smart_router.py` carried a "smart ticker merging" block that ran after the
router's decision validated: with a portfolio set, `parameters.tickers` was
replaced by the portfolio's tickers, or the union if the user had named any.
Added with a "⭐ RECOMMENDED" comment and no consumer - nothing downstream read
`parameters.tickers` while a portfolio was set, because `load_portfolio_context`
takes holdings from the database. Inert for as long as it existed.

Position P&L made it a bug on 7 September: the P&L formatter reads `tickers`
as the selection, where a filled list means "these positions" and an empty one
"every position". "How has my JPM position performed" answered with all nine,
in a random order, with a plausible face. `check_1_2` asserts `tickers ==
["JPM"]` and caught it.

**Two fixes were built before the code was grepped for writers, and both were
wrong.** The first rewrote rule 2 and rule 6 in the router prompt to say
"never fill tickers from the portfolio" (clean on the golden set, no effect).
The second removed the ticker list from the `portfolio_context` string so the
model had nothing to copy - and the rebalance query flipped to
`clarification_needed` on one of two golden runs, and 3.3 lost
`PortfolioAnalysisAgent`. Reverted. The list in the context does routing
work: it tells the router the portfolio is real enough to plan against.

The fix was deleting the block. Same rule as the handoff's `get_portfolio_value`
instruction, which was also carried forward without checking callers: **grep
for readers AND writers before reasoning about where a value comes from.** Two
prompt changes, four golden runs and a reverted commit were the price of
grepping only one side.

The rule 2 rewrite from the first attempt stays, because "use defaults if
none" was wrong on its own: the router has no defaults to use.

## Benchmark 3.3 passed once while `tickers` was padded

The P&L formatter prints every position whether `tickers` is empty or holds
all nine. `check_3_3` asserted `measure`, the nine published positions and
their dates, and not `tickers` - so on 7 September it passed in the same run
that failed 1.2 for padding. Closed by requiring `tickers == []`: the question
names no position, and a filled list means the router copied the portfolio in.

A check that cannot distinguish "empty means all" from "padded to all" is the
false-pass shape on the case benchmark.md calls its most important.

---

# OPEN

## Verification instruments do not cover what they appear to cover

### The golden runner prints five routing fields and nothing else

`run_golden.py` prints `intent`, `plan`, `execution_order`, `period`,
`agents_run` and an error count. It never prints answer content or any numeric
output. Consequences:

  - The MacroAgent confidence change in ccfa1e1 (regime_confidence dropped by
    0.25 on every query) produced NO diff. The golden set cannot see it.
  - benchmark.md Part 3b says a response with a header and no content under it
    is a failure, and notes that is current behaviour for several Level 1
    queries. The runner cannot detect that.
  - The router schema leak was caught only because `period` happens to be one of
    the five printed fields. The same leak on `tickers` and `max_volatility`
    would have been invisible — and `tickers` ordering is still nondeterministic
    across runs, unseen.

Add an answer-body-non-empty check before doing any prompt work. Prompt changes
cannot be evaluated with an instrument this narrow.

### `trace_tool` and `log_delegation` are never called

`observability/tracer.py` fully implements `ToolTrace` and
`AgentTrace.log_delegation`. Nothing invokes either. All 13 call sites across
`nodes.py` and `smart_router.py` use `trace_agent` only.

benchmark.md 2.1 passes only when "trace shows contract handovers" — that is the
`log_delegation` path. **Benchmark 2.1 cannot pass today for tracing reasons
alone, independent of the agents.** Part 4 says tracing is largely done and only
needs verifying; the verification result is that the agent layer is done and the
tool and handover layers are scaffolding.

Wire both when the base-agent deduplication happens, since that touches the same
five agent files. Note the dedup is now scheduled with the Risk and Compliance
work rather than before Level 1 — its original justification was that it would
make `result_type` get set and thereby fix the synthesizer, and that premise was
wrong (see the synthesizer entry below).

`AgentConfig.log_tool_calls` defaults to True and is read nowhere — same gap,
second symptom.

Also worth recording for whoever does the dedup: **DataAgent already uses
`create_result`**, at seven call sites. It is the only agent that does; the other
five hand-build `PortfolioResult` (`backtest_agent:250`, `macro_agent:321`,
`optimization_agent:228`, `rebalance_agent:167`, `risk_manager_agent:341,367,398,416`).
So the job is migrating five files to a helper that exists and works, not
designing one.

### No golden query runs against portfolio 3

`run_golden.py`'s `QUERIES` list runs four of its ten queries against portfolio 1
and one — the Technology-sector query — against portfolio 2. Portfolio 3, the
Benchmark Portfolio and the only one `expected_values.md` was computed against,
appears nowhere.

So the fast loop cannot see a regression in any figure the benchmark is scored
on. Worse, the portfolios it does pin cannot produce those figures at all:
portfolio 1 carries January average prices and `sector` NULL on every holding,
and portfolio 2 is a two-position leaked test artifact with no `asset_class`. The
allocation queries in the golden set therefore run green against data that would
make case 1.1 meaningless.

Recorded, not fixed. Widening the golden set is a decision about what the fast
loop is for: it is the routing instrument, run on every change, and adding a
nine-position portfolio costs time and provider calls on every run. The benchmark
case runner is the instrument that covers portfolio 3, and its being a separate
loop is the reason. Decide once the runner exists, not before.

Note an earlier claim that the golden set uses only portfolio 1 was wrong. Both
1 and 2 appear in `QUERIES`, and `expected.txt` carries `pid=2` on the
Technology-sector query. `run_golden.py` has one commit and has never changed.

### Seeding portfolio 3 rewrites metadata shared with portfolios 1 and 2

`asset_class` and `sector` live on `Asset`, not on `PortfolioHolding`, and
`seed_portfolio.py` always rewrites that metadata. `Asset` rows are shared across
portfolios, so seeding portfolio 3 retroactively changed what portfolios 1 and 2
report - including the two the golden set runs.

Observed 4 September: portfolio 2 now returns `asset_class: "Equity"` and
`sector: "Technology"`, and portfolio 1 returns Equity, Commodity and Fixed
Income. HANDOFF §2's claim that portfolio 2's holdings have no `asset_class` was
true when written and is now false.

So "do not modify or delete portfolio 1" is not sufficient protection. Reseeding
portfolio 3 mutates the data the baseline runs against, silently, and the golden
runner prints no figures that would show it.

### `test_portfolio_integration.py` still does not assert

Confirmed by pytest emitting `PytestReturnNotNoneWarning` for
`test_1_portfolio_crud` and `test_3_state_portfolio_context`. Every test function
returns True/False and a `main()` tallies them; pytest ignores return values, so
all pass unconditionally. 18 return statements, several marked "Skip, not fail".

So "91 passed" means 91 collected and none errored, not 91 things verified.

Fixing means rewriting with real assertions, not a mechanical return -> assert
swap. Expect genuine failures once it does.

---

## Silent-wrong bugs found, not yet fixed

The recurring failure shape in this codebase: repair instead of raise, so a wrong
answer arrives with a plausible face instead of an error. Same family as bugs 5,
6 and 9 from the recovery session.

### CostCalculator reports costs for the wrong model

`observability/tracer.py:406` — `PRICING` is a 2024 table with no Anthropic 4.x
entries, and `estimate_cost` does `PRICING.get(model, PRICING["gpt-4-turbo"])`.
The active model (`claude-haiku-4-5-20251001`) is absent, so every cost figure
silently uses GPT-4-Turbo rates.

Fix the table and raise on unknown models. Matters disproportionately: the target
role names LLM monitoring and evaluation, and this is the monitoring layer.

### `ANTHROPIC_SONNET` points at the Haiku model id

`agents/config.py:73-75`. Flipping `ACTIVE_LLM_CONFIG` would silently give Haiku
with no error. `smart_router.py:104` imports it behind
`self.config.use_stronger_model`, so the path is reachable. Verify the current
Sonnet string against `GET /v1/models` rather than typing one in.

### `cash_balance` cannot be absent, so D2 is unenforceable

`Portfolio.cash_balance` is `Column(Float, nullable=False, default=0.0)`.

D2 says an absent cash balance is an unknown denominator rather than zero, and
`portfolio_analysis_agent_node` enforces it by raising when `cash_balance` is
None. The model can never produce None, so the guard can only fire if
`shared_data` lacks the key - never because a portfolio has no recorded cash.

Observed 4 September: portfolios 1 and 2 both reported Cash 0.00% without
complaint. Nothing distinguishes a portfolio holding no cash from a portfolio
whose cash was never entered, and the second silently shrinks the denominator
for every asset-class percentage. Portfolio 3 is unaffected - its 15,500 is
seeded - so this bites the first real portfolio, not the benchmark one.

Fixing it means a migration to nullable plus a decision about what None means at
every read site. Not blocking; decide before a real portfolio is loaded.

### No FX conversion anywhere

`Asset.currency` is populated at `data_manager.py:413` and read only for display;
`rebalance_tools.py` stamps `cfg.currency_symbol` on numbers regardless of their
actual currency. Blocks a real EUR portfolio: cost basis in EUR against
USD-quoted yfinance prices for US tickers makes 1.2's P&L wrong by the exchange
rate, silently. Severity depends on whether tickers carry an exchange suffix
(`AAPL` vs `AAPL.DE`) — with the suffix, prices come back in EUR and the problem
does not arise.

### Prices are reported as current with no as-of date — RESOLVED 7 September

**Built. Do not rebuild this.** `as_of_dates` is published per ticker from
`data_agent.py` beside `latest_prices`; `portfolio_analysis_agent_node` reduces
it to a worst case and publishes `allocation.as_of`; the synthesizer renders it,
naming the stalest holding only when the dates actually differ. The benchmark
runner asserts the structured value and that it reaches the prose, replacing a
date-shaped regex. 1.1 and 1.4 moved from FAIL to PASS on it.

The reasoning below is kept because the shape it argues for is the shape that was
built, and because the per-holding-versus-per-answer question returns for P&L and
volatility, which will each carry an as-of somewhere other than `allocation`.

---


`latest_prices` carries the most recent `DailyPrice` row, which is the previous
settled close — 2026-09-02 when queried on 2026-09-03. The data is correct;
nothing labels it. Confirmed against a hand-built price series, which matched the
09-02 closes exactly on all nine tickers.

Compounded by the new cache: `price_fetch_interval_days` defaults to 1 and
`_should_fetch` compares whole days, so a new close is not picked up until the
following day. An answer can now be up to two settled closes behind.

This is benchmark 3.3 in the data layer. Resolve in Phase 1 item 5, where the
as-of date starts being reported.

**Two levels, and they were settled separately. Recorded 4 September.**

*The data level was never in question.* Each holding already has its own as-of
date: `latest_prices` is built as `prices[ticker].dropna().iloc[-1]`, per ticker,
so a ticker missing the final close carries an older date than the frame's end
and nothing marks it. That is a property of the data, not a decision.

*The output level was the open question* - whether the answer states a date per
figure, per holding, or as a worst case. `benchmark.md` Part 3b settles it: an
as-of date is required for every figure derived from market data. Per figure and
per holding coincide for the allocation figures, since each derives from one
holding's price, and diverge only for aggregates, which reduce over many.

A single portfolio-level `as_of` is ruled out at both levels: it is not what the
data holds, and it is not what Part 3b asks for. It would be a summary wrong for
exactly the stalest holding - the repair-instead-of-raise shape applied to the
field meant to prevent it.

### The volatility window is anchored to today, not to the last settled close — RESOLVED 7 September

**Fixed, on the third attempt. Do not rebuild this.** The fetch window is
`[today - N - _FETCH_MARGIN_DAYS, today]`; the evaluation window is the last
`years x trading_days_per_year` closes, applied before the frame is cached.
Verified against a live run: the returned frame was 2023-08-31 to 2026-09-04,
exactly 756 closes, ending at Friday's close rather than at a Labor Day on which
the market never opened.

**The two failed attempts are worth more than the fix.** A post-fetch trim alone
was arithmetically inert — the frame arrives bounded by the fetch window, so its
first row is already at or after the evaluation start and the filter dropped
nothing. It passed `pytest`, the golden set and the runner. Separately, resolving
`period` into the variable that keys `_prices_df_cache` split the namespace
between `SPY_None` and `SPY_3Y` and every downstream tool missed; only the golden
set's `errors` field caught it.

The old window was short by three closes at 3Y and one at 1Y, which is why the
frame got slightly *bigger* when it was fixed.

---


`data_agent.py`, `_calculate_period_dates`, sets `end_date = date.today()` and
subtracts `config.data.period_days`. Nothing anchors it to a close.

Observed 4 September on portfolio 3. `period: 1Y` returned **2025-09-04 to
2026-09-02, 251 closes**. `expected_values.md` D8 specifies 2025-09-03 to
2026-09-02, 252 closes and 251 daily returns. One trading day short at the
front.

**Both ends now disagree. Observed again 4 September, later the same day.** The
frame came back ending **2026-09-03**, one close past D8's 2026-09-02. The
earlier note said the end agreed because the data stops at the last settled
close; that held only while the last settled close was still 09-02. A new close
landed between the two runs and the cache picked it up. The start was always
adrift; the end drifts too, one trading day at a time, and D8's instance is now
behind both.

This was invisible until the as-of field existed. It is the first thing that
field caught.

The reference and the code therefore disagree, and the disagreement is visible:
Part 4's sanity check quotes TLT at 9.55% and GLD at 29.21%; the run gave GLD
29.21% and TLT 9.35%. Weighting the run's nine figures by market value gives
20.5254% against Part 4's 20.5408% - 0.0154 percentage points apart. That
pattern says the method is right and the window is not. A ddof or annualisation
difference would move the weighted average much further.

**This blocks roadmap item 4.** `portfolio_volatility` is checked against
10.2936%, and against a window that shifts daily it will not reproduce - today,
tomorrow, or ever except by coincidence. The pressure at that moment will be to
edit `expected_values.md` to match. Do not.

**The decision, to be taken before item 4 and not now.** Either anchor the code
to the last settled close so it matches D8, or change D8 to a trailing window
ending today and recompute Part 4 with the reason recorded. The first is the
stronger option: a reference that moves daily is not a reference, which is why
D8 pinned settled closes in the first place, and benchmark 3.3 wants the system
to know its as-of date regardless.

The first option needs no new seam, but it is **not** a change to
`_calculate_period_dates` alone. That function runs before the fetch, so it
cannot know the last settled close — the dates it returns are what bounds the
fetch that discovers it.

**And a post-fetch trim alone is inert. Tried and reverted, 4 September.** The
frame arrives bounded by the fetch window, so every row is already
`>= today - N`, while the evaluation start `last_close - N` is always
`<= today - N`. The filter drops nothing, on any period. The window is one
trading day *short* at the front, not long, so the missing close was never
fetched and no trim adds it back.

Both halves are needed: widen the fetch to `[today - N - slack, today]`, then
trim to `[last_close - N, last_close]` before the frame is cached. `slack` is
policy and belongs in `DataConfig`; under-fetching reproduces this bug with no
visible symptom, which is how the trim-only version passed review.

Item 5 shares nothing with it: item 5 adds an output field to the price summary.
A caller-facing end-date parameter on `fetch_prices_tool` would only be needed
to pin a run to a fixed date, which the strict runner deliberately avoids
needing.

---

## Unbuilt features

### The synthesizer returns the same answer regardless of the question

All four benchmark Level 1 queries return a byte-identical response:

    Analysis complete. See details below:

    DataAgent: ✓

Cause: `synthesizer_node` dispatches on the router's **intent** (in `nodes.py`,
search `def synthesizer_node`):

    if   intent == "optimization":     _format_optimization_response(...)
    elif intent == "macro_analysis":   _format_macro_response(...)
    elif intent == "rebalancing":      _format_rebalance_response(...)
    elif intent == "backtest":         _format_backtest_response(...)
    elif intent == "combined":         ...

There is no branch for `data_fetch` or `risk_analysis`, which are the two intents
every Level 1 query produces. They fall through to a stub.

This is the benchmark.md Part 3b failure, and it is a synthesizer gap rather than
a data gap. Every number needed to answer 1.3 was already in `shared_data` when
that stub printed.

**An earlier version of this entry blamed `result_type` being unset. That was
wrong** — the synthesizer never reads `result_type`, so setting it fixes nothing.
Corrected 3 Sep after reading `nodes.py:1104`. Worth keeping as a caution: the
field looks like the dispatch key and is not.

The fix is two branches plus formatters, but those formatters must not compute
anything. A formatter doing arithmetic is the separation-of-concerns violation
the project's principles name. An agent computes; the synthesizer formats.

**No longer blocked, 4 September.** The holdings gap it waited on is resolved and
PortfolioAnalysisAgent publishes the allocation, so every number 1.1 and 1.4 need
already exists. This entry stays OPEN — the branches are unwritten and they are
the next commit.

**Branches written, 7 September.** `data_fetch` and `risk_analysis` with
PortfolioAnalysisAgent in `sub_results` go to `_format_analysis_response`,
which selects on the router's `measure`: allocation (narrowed by `group_by`),
position P&L (selected by `tickers`), portfolio volatility. A plan naming the
agent with no `measure` raises rather than guessing a formatter. The stub
below is reached now only by raw price fetches with no analysis agent, which
is the "Get me the last 1 year of prices" shape and still answers nothing
with figures. Entry stays OPEN for that case alone. Note the formatters read `sub_results["PortfolioAnalysisAgent"]`,
not `shared_data`: `mark_agent_complete` stores the node's result dict verbatim,
that result already carries the same allocation object, and every existing
formatter takes `sub_results`. `shared_data` is the channel between agents; it is
not a second input to the synthesizer.

### `shared_data` carries 67KB of raw prices — hot potato violated

`price_data_json` was 67,190 characters of daily OHLC on the 3Y queries and
22,501 on the 1Y query. **Measured again 4 September on portfolio 3: 161,557
characters**, 2.4x the recorded figure — the earlier measurement was taken on
fewer tickers. It scales with the ticker count, so the recorded number is a floor
and not a size. `state.py:50` states shared_data holds summaries, not raw
DataFrames, and the module docstring calls this the Hot Potato principle.

This is the project's first stated design principle violated in the main data
path, on every request. Structural rather than a missing feature.

Fix with the base-agent deduplication, when result and shared_data construction
gets centralised. The agents downstream need returns and covariance, both already
computed and already in shared_data separately.

### Rebalance has no target allocation source

"Should I rebalance my portfolio?" fails with "No target weights from
OptimizationAgent." RebalanceAgent needs a target to measure drift against; the
router plans [DataAgent, RebalanceAgent] and there is no target.

DO NOT fix by inserting OptimizationAgent into the chain. Re-optimising on every
drift check means the target moves with the covariance matrix, which is not how
strategic asset allocation works. Drift must be measured against a fixed target.

Correct fix: targets belong to the portfolio / IPS. See `ips_manager.py` on
`wip/phase7-snapshot`. Resolve when Phase 7 is pulled forward.

### RiskManagerAgent is not a risk agent - it is an unused second orchestrator

`src/agents/risk_manager_agent.py` exists but has no graph node, no routing entry,
and no mention in `router_prompts.py`. The router classifies
`intent: risk_analysis` correctly and then has nowhere to send it. Risk queries
route to DataAgent and stop.

**Corrected 4 September after reading the file.** Wiring it up is not the fix.
It is `class RiskManagerAgent(SupervisorAgent)` at line 36; its own docstring
says it parses mandates, delegates to specialised agents and synthesises results,
and `process()` dispatches on `TaskType` to `_handle_optimization`,
`_handle_backtest`, `_handle_rebalance`, `_handle_regime_analysis`. That is the
router and the graph, written a second time. Outside its own file it is
referenced only by exports in `__init__.py` and by `check_imports.py`; it is
never instantiated. It is the only `SupervisorAgent` subclass.

Note the README, marked outdated, describes it as an active supervisor. On this
one point the README is accurate about the code. Do not let the rewrite delete
the true sentence with the false ones.

**Decision, 4 September: keep the router and graph, do not wire the supervisor,
do not rename it.** Plan-then-execute makes one routing decision that depends
only on the user's words, which is exactly why the golden set can pin it. A
supervisor makes N decisions that depend on data just fetched, which nothing can
pin - not because it is random, but because the market moved. Most of what a
supervisor would do is conditional edges, which LangGraph does natively with a
deterministic predicate; a supervisor earns its place only when a branch needs
judgment no predicate can express, and none of the twelve cases produces one. If
equity research later needs iterative retrieval, that is a loop inside one agent,
not a supervisor above the roster.

What is worth salvaging is `check_concentration_risk` from its tool list, for a
real risk agent when 2.1 is built. The supervisor scaffolding around it is not.
Blocking nothing; do not chase it.

### No API path to set `asset_class` or `sector`

`PortfolioManager.update_holding:456` accepts only `quantity` and
`average_price`. Those fields live on `Asset`, reachable only via SQLAlchemy
directly. `scripts/update_all_assets.py:105` sets `asset_class` but not `sector`.
Close the gap as Phase 1 work; until then seed via a script, not ad hoc row edits.

### No portfolio-level volatility exists — RESOLVED 7 September

**Built. Do not rebuild this.** `portfolio_volatility(weights, cov_matrix)` and
`portfolio_volatility_by_ticker` in `quant/risk_metrics.py`; `optimization/base.py`
delegates to it. PortfolioAnalysisAgent computes it from market-value weights
of the invested assets (cash excluded, Part 4) against `shared_data["covariance_matrix"]`
and publishes `shared_data["portfolio_volatility"]` with the full basis: window
(from `price_window`, which DataAgent now publishes as data), weights and their
pricing date, covariance method, annualisation. `check_1_3` asserts every
element reaches the prose and that the figure sits well below the weighted
average of the single-name volatilities, so an average cannot pass.

`tests/test_portfolio_volatility.py` reproduces 10.2936% two ways from the
committed closes: numpy sample covariance, and the system's own
`CovarianceEstimator`. The second is the one that matters - it shows the
matrix DataAgent publishes carries the reference's conventions (simple daily
returns, sample, x252), which expected_values.md was right not to assume.

Live on 7 September: **10.40%** over 2025-09-05 to 2026-09-04 against the
reference's 10.29% over 09-03 to 09-02. Two closes shifted, weights at Friday's
prices. That is the pin working, and the basis in the answer is what lets a
reader see it.

**The count below was low.** `sqrt(w'Σw)` also sits inline in
`optimization/constraints.py` (four times), `mean_variance.py` and
`risk_parity.py` - inside objective and constraint functions evaluated on
iterates that do not sum to one, so they cannot delegate to a function that
validates the sum. Whether they should is open; see the hygiene entries.

---

Five implementations, none of which computes it:

  - `quant/risk_metrics.py:108` — `calculate_volatility(returns, periods_per_year=252)`
  - `backtest/metrics.py:111` — `calculate_volatility(returns, annualize=True)`
  - `tools/analytics_tools.py:67` — `@tool calculate_volatility(ticker, days=365)`
  - `optimization/base.py:189` — `_calculate_portfolio_volatility`
  - `backtest/engine.py:523` — inline `returns.std() * np.sqrt(252)`

Only the third is exposed as a tool, and it is **per-ticker**. benchmark.md 1.3
asks for portfolio volatility, which needs weights against the covariance matrix,
and passes only when "basis of calculation traceable".

**Decided in `expected_values.md` D7:** `quant/risk_metrics.py` is canonical for
return-series volatility, and a new `portfolio_volatility(weights, cov_matrix)`
goes there. `analytics_tools.py` and `optimization/base.py` delegate to it;
`backtest/metrics.py` and the inline `engine.py:523` are scoped backtest-internal.
Expected answer for portfolio 3: 10.2936%.

### Case 3.2 fails, and not by recommending

"Should I buy Nvidia?" returns `intent: clarification_needed` and offers four ways
to proceed with buying NVDA. 3.2 passes only when the system refers to the scope
boundary and gives no recommendation. It did neither — it treated an out-of-scope
request as an ambiguous in-scope one.

Root cause: `INTENT TYPES` in `router_prompts.py` has no out-of-scope option. The
router has no vocabulary for "this is not something the system does", so the
nearest available label is `clarification_needed`. Needs a new intent plus a
terminal branch, not better wording of the existing ones. Resolve with Part 4
item 4 (the guardrail path).

**This case has a known expiry date.** benchmark.md Part 2 was made phased on
4 September: screening and candidate generation are out of scope for Levels 1-3
and revisited afterwards, because a system that recommends before it can compute
what is already held recommends against a wrong picture. 3.2 tests that boundary,
so when the boundary moves 3.2 is rewritten with its own cases rather than
deleted or quietly relaxed. Until then it is live and passes on merit.

Do not "fix" 3.2 by widening the router toward recommendations. The out_of_scope
intent is still the correct build.

### The router cannot express an absolute date range

`ExtractedParameters.period` is `Optional[str]` with pattern `^\d+[YMD]$`, so a
period is always relative and always anchored to the moment of the query. "My
volatility between 2025-09-03 and 2026-09-02" is unaskable. That is why the D8
reference window is unreachable from a live run and why item 4's check is a
fixture rather than a live comparison.

**A gap on the path to the stated goal, not a volatility detail.** Equity
research asks about defined periods — a quarter, a drawdown, the window between
two events — and none of them are `\d+[YMD]` from today.

**It gets its own decision, not a side entrance through the anchor.** It needs a
schema field, a prompt change (therefore a specification change, therefore
measured on the golden set twice), and plumbing through a cache key and a
coverage check that both assume period strings. Adding an end date to
`fetch_prices_tool` because the volatility window is inconvenient would buy one
figure and leave the router still unable to ask the question.

### When `sector` comes up, weigh `group_by` and `filter` against it first — DECIDED 7 September

**Decided when position P&L arrived, which was this entry's own trigger.**
Three axes on `ExtractedParameters`, two built:

- `measure` - which computation: `allocation`, `position_pnl`,
  `portfolio_volatility`. Each value IS the `shared_data` key the node
  publishes under, so router vocabulary, synthesizer dispatch and runner
  probes share one word and no mapping can drift. A value with no computation
  behind it does not belong in the Literal - the schema must not be wider than
  the code (the "3M" lesson).
- `group_by` - dimension to break down by: `asset_class`, `sector`. Narrows the
  RENDERING, not the computation; both breakdowns are always computed and
  published. `industry` and `country` are deliberately absent until something
  groups by them.
- `filter` - NOT built. "How has my tech sector done" is `position_pnl`
  restricted to `sector = Technology`, which is the same operation `tickers`
  performs on a different dimension. When it comes it is
  `filter: {dimension, values}` with `tickers` as its ticker-dimension special
  case - not `sector` bolted onto `group_by`, not a `sector` field beside
  `tickers`. The slot is reserved so the third axis has somewhere to go that
  is not one of the first two.

Rejected: a new intent per quantity (mixes what-to-run with what-was-asked),
`AgentTask.task_description` (free text, unassertable), dispatching on
`tickers` being non-empty (was never a signal - see the router override entry),
a combined enum (`allocation_by_sector`, `pnl_by_ticker`...) which ratifies
the cross-product this entry warned against.

Field name: `analysis` was rejected because it echoes
`portfolio_analysis_agent_node`; `metric` echoes three `*metrics.py` modules.

**The node does not read `measure`.** It computes everything; `measure` is a
synthesizer signal only. This fell out of "compute all positions always" and
is less coupling than first proposed.

---


Roadmap item 5 proposes a `sector` field on `ExtractedParameters` to narrow the
`data_fetch` branch from both breakdowns to the one asked for. Consider
`group_by` and `filter` instead, and decide deliberately.

One field answers one question; a grouping parameter answers the class of
question. `Asset` already carries country and industry columns that the seed
writes, so those breakdowns come free the moment grouping is a parameter rather
than a function name. The prompt change costs the same either way — it is one
extracted field versus two, measured on the golden set once.

**The tell is already in the output.** The formatter prints both breakdowns and
says so under "Not done", because nothing in the routing decision records which
one was asked for. That is a missing parameter being paid for in noise, not a
limitation of the model.

The cost of getting this wrong is not the field. It is that
`allocation_by_asset_class` and `allocation_by_sector` are already two functions
differing only in their grouping key, and a `sector` field ratifies that shape.
Country and industry would make four.

---

## Where non-determinism is allowed to live

Recorded 4 September, before the Equity Analyst exists, so the boundary is
deliberate rather than discovered.

The Equity Analyst will be genuinely uncertain, will run on a larger model, and
may use a skills-style layer for procedural knowledge. All three are fine and
none of them change the architecture - `AgentConfig` already carries per-agent
model settings, so a different model per agent needs no new machinery.

**The constraint is that its uncertainty must not leak into the deterministic
components.** If it produces a quality score and the optimiser weights on it, a
judgment has been laundered into arithmetic and the trace will not show it. The
number will look like every other number in the output.

So its output crosses the contract boundary marked as an opinion, using
`confidence`, `reasoning` and `warnings` on `PortfolioResult` - fields that
already exist and are currently unused everywhere.

And it will not be reproducible, so **the golden set is the wrong instrument for
it**. The golden set works because one routing decision depends only on the
user's words. An analyst's judgment depends on documents and on the model, and
re-running it will not reproduce the previous answer. Its instrument is the
Phase 4 eval set - expected answer and expected source per question - which is
also the open commitment in benchmark.md Part 1.

Nothing to build now. This exists so that when the analyst arrives, the question
"where may this be uncertain" has already been answered.

---

## Scope conflicts with benchmark.md

### MacroAgent is live but outside the target architecture

Wired into the graph (`graph.py:118`, routing map at 135) and named in
`router_prompts.py`, with two of the four few-shot examples using it. Absent from
benchmark.md Part 2's agent list (Quant, Risk, Compliance, Data) and from every
phase of the roadmap.

Deliberately left in place. After ccfa1e1 it no longer lies — no dead scraper, no
phantom confidence — it is simply out of scope. Revisit only if it blocks a
benchmark case. Deleting it would touch six files and require rewriting router
few-shot examples; that cost is not justified by anything on the list.

Note it is consumed downstream: `nodes.py:903-907` has RebalanceAgent's node
reading `shared["macro_regime"]` for `regime` and `equity_adjustment`,
`nodes.py:1176-1224` formats macro output in the synthesizer, and
`risk_manager_agent.py:374` delegates regime analysis to it.

### `generate_taa_signal_tool` returns allocation recommendations

It returns `action: "INCREASE"/"DECREASE"` with a `recommended_equity_weight`, and
`prompts.py:114` instructs the model to recommend equity weight adjustments.
benchmark.md Part 2 lists buy/sell recommendations as out of scope, and test case
3.2 requires refusing recommendation requests.

A live path contradicts 3.2. Resolve when building 3.2, not before.

---

## Configuration and policy duplication

### Period vocabulary lives in three places

`DataConfig.period_days` (`config.py:40`) holds the valid period keys. The router
prompt hardcodes the same list independently in its extraction rules. Policy
belongs in config, so the prompt should generate that line from
`config.data.period_days.keys()`.

`ROUTER_SYSTEM_PROMPT` is a module-level constant full of JSON braces, so
`.format()` on it would require doubling every brace — which is why `REPAIR_PROMPT`
already uses `{{ }}`. Cleaner route: pull that one line out of the constant and
append it as its own part inside `build_router_prompt`, which already assembles
`parts = [ROUTER_SYSTEM_PROMPT]` and adds sections.

**A fifth site, and a disagreement rather than a duplication. Found
4 September.** `ExtractedParameters.period` is
`pattern=r"^\d+[YMD]$"`, and its own comment offers `"3M"` and `"30D"` as
examples. `config.data.period_days` holds only `1Y, 2Y, 3Y, 5Y, 10Y`. So the
router is free to emit a period the config cannot resolve, and
`_calculate_period_dates` raises `Unknown period '3M'. Valid periods: [...]`.

**The raise is correct and should stay.** Recording it because the schema and the
config are two statements of the same vocabulary that do not match, and the
schema is the wider one — the failure surfaces at the data layer for a decision
the router already made. Whoever adds month periods has to add them in both
places, and will find the evaluation window is defined in years only (see spans
versus counts, below).

This is the gap that bites first when windows widen beyond years — before any
question about absolute date ranges.

**A fourth site, found 4 September.** `fetch_prices_tool`'s signature default is
`period: str = "5Y"`, against `DataConfig.default_period` of `"3Y"` — 1825 days
against 1095. It is unreached: every caller passes `period` explicitly
(`nodes.py:424`, `data_agent.py` at 178, 223, 538, 625 and 700, `__init__.py`,
and the tests), so the truthy `"5Y"` never falls through to
`period or config.data.default_period`. Note it is registered as an LLM-callable
tool at `data_agent.py:103`, so it becomes reachable the day the router calls
tools rather than classifying — see the classifier/tool-caller decision below.
Delete the default rather than align it; a default nothing takes is a second
policy waiting for a caller.

**A third site, found 4 September.** `nodes.py` extracts the period as
`parameters.get("period", "3Y")`. That literal is a second copy of
`config.data.default_period`, and it is also dead: the router always emits the
key with `null`, so `.get` returns None and the real default is applied by
`period or config.data.default_period` in `data_agent.py`, two files away. A
hardcoded policy value that never fires, sitting exactly where a reader would
look for the default.

Do this with the prompt rework, not before.

Note an earlier claim in this file that `default_period` was defined twice with
conflicting values was WRONG: line 28 is `DataConfig` ("3Y") and line 132 is
`BacktestConfig` ("5Y"), different concerns with correctly different defaults.
`default_max_volatility` genuinely does appear twice — `OptimizationConfig:96` and
`RiskManagerConfig:154` — with the same value. Soft duplication, no current
conflict. Decide which owns it before either changes.

### The agent roster is restated in eight places

Recorded 4 September, while adding the sixth agent. Nothing is broken today;
this is about what breaks quietly at the seventh.

The list of agents exists in:

1. `router_prompts.py` - the `AVAILABLE AGENTS` block
2. `router_prompts.py` - "NEVER hallucinate agents - only use the 5 listed
   above", which hardcodes the count in prose
3. `router_prompts.py` - the few-shot examples, which teach by demonstration
4. `graph.py` - `route_next_step`'s `Literal[...]` return annotation
5. `graph.py` - the `add_node` calls
6. `graph.py` - `routing_map`
7. `graph.py` - the `agent_nodes` list used to wire the loop edges
8. `schemas.py` - the `AgentName` Pydantic enum

**Site 8 was missed when this entry was first written, and found the same day by
breaking it.** `AgentTask.agent` is typed against `AgentName`.
Adding the sixth agent to the prompt and the graph but not the enum
meant the router returned a plan naming `PortfolioAnalysisAgent`, Pydantic
rejected the whole response as invalid, all three retries failed identically,
and `route()` returned None.

That failure was loud and immediate, which is the right behaviour. But it
surfaced through `test_router_simple.py`, one of the six unguarded files, which
makes a live router call at import time - so it aborted pytest collection and
the other 105 tests reported nothing. Same shape as the January `sys.exit()`
bug, different file.

This entry missing a site while enumerating them is the argument for the registry.

Adding an agent means finding all eight. Miss the prompt and the router cannot
plan the agent that exists. Miss `routing_map` and LangGraph raises on an
unmapped return value - loud, fine. Miss the prose count and nothing fails at
all: the model is told there are five while being shown six, and the effect is
a slightly worse classifier with no error anywhere. That last one is the
repair-instead-of-raise shape applied to a prompt.

The fix is to derive all eight from one registry - a single mapping of agent
name to node function and description, with the prompt's roster rendered from
it. Same principle as moving the database URL into config: policy stated once,
everything else reads it. Related to the period-vocabulary entry above, which
wants the same treatment for a different list.

Deliberately NOT done while adding the sixth agent. Doing both at once would
mean a golden-set diff that cannot distinguish "the new agent perturbed
classification" from "the regenerated prompt reads differently". One change per
commit exists for exactly this.

Worth doing before the seventh agent, not urgent before then. Note the prompt
text will change when rendered from a registry even if the roster does not, so
the commit that does it should expect a golden diff and be judged on whether
routing decisions moved, not on whether the prompt string changed.

### `hawkish_threshold` and `dovish_threshold` are now unreferenced

`config.py:67-68`, in `MacroConfig`. Their only consumers were the Fed blocks
removed in ccfa1e1. Left in place rather than deleted, because dead config keys
that imply a Fed signal exists are worth one deliberate decision rather than a
drive-by removal.

### `regime_confidence` now derives from VIX alone

After ccfa1e1, `_calculate_regime_confidence` takes only `vix_regime` and returns
0.1, 0.2 or 0.3. The formula was built as a 50/50 Fed/VIX blend; with Fed gone it
caps at 0.3. Not rescaled deliberately — picking a multiplier to make the number
look healthier would fabricate the precision that was just removed.

The yield curve informs the regime (`_determine_regime`) but not the confidence in
it. Making it contribute is a deliberate design change and its own commit.

### Router parameters are restated by hand in two more places

`nodes.py` `_decision_to_dict` listed `parameters` key by key, and would have
validated `measure` in the schema and then dropped it before any node could
read it - a field that exists and does nothing. Replaced with
`parameters.model_dump()` on 7 September. `smart_router.py` `route_sync`'s
return dict (search `"tickers": decision.parameters.tickers`) does the same
and was not touched; check whether anything reads it before it drops a field
for someone.

### `CovarianceResult.to_dict` drops the matrix above ten tickers

`covariance.py`: the covariance and correlation matrices are included in the
dict only when `len(tickers) <= 10`, with a comment about output size. At
eleven holdings `shared_data["covariance_matrix"]` is silently absent.
PortfolioAnalysisAgent now raises on that rather than defaulting, which is
loud and correct, but the limit is one holding away and documented nowhere
but here. The matrix is a summary, not raw data; the hot-potato concern that
motivated the cap is `price_data_json`, not this.

### The returns convention is not published

`portfolio_volatility` states its basis from `shared_data` - window, method,
weights, annualisation - and cannot state whether the covariance is over
simple or log returns, because DataAgent does not publish it. `data_agent.py`
has both branches (`pct_change` and `np.log`, search both); the covariance
path uses `pct_change`. The formatter says "daily returns" and no more. A
`returns_type` beside `covariance_method` would close it.

### Inline `sqrt(w'Σw)` inside optimiser objectives cannot delegate

`optimization/constraints.py` (four sites), `mean_variance.py` and
`risk_parity.py` compute the portfolio variance inline inside objective and
constraint callables that SLSQP evaluates on iterates which do not sum to
one. The canonical `portfolio_volatility` raises on that, correctly - so
these cannot call it as written. Either a non-validating core the validated
function wraps, or accept that objective internals are scoped like the
backtest engine's inline volatility. Decide before the next optimiser change.

### `AgentConfig` fields declared but unenforced

`log_tool_calls` and `max_tool_calls_per_turn` are read nowhere. The first reads
as "tool calls are being logged" and they are not; the second reads as a loop
guard and there isn't one. Kept and marked rather than deleted, because both
describe intended behaviour the dedup work should implement.

`model_name` (defaulting to `gpt-4o-mini`) and `custom_settings` were deleted in
ae6f220 — model identity lives in `agents/config.py`.

---

## Hygiene

### `.gitignore` is corrupted

A PowerShell here-string was written into it literally. Line 1 is `@"`, there is a
`` *`$py.class `` line with a PowerShell escape, and mid-file sits
`"@ | Out-File -FilePath .gitignore -Encoding UTF8data/portfolio.db`. The DB is
still ignored by later standalone entries, so nothing is leaking. Rewrite it.

### `portfolio_tool/__init__.py` opens a database connection at import

Line 43 imports `database_setup`, which prints a German DEBUG line and constructs
an engine as an import side effect; line 52 imports `data_manager`, which needs
`tomli`. So no module under `portfolio_tool` can be imported without sqlalchemy,
pandas and tomli loading first, regardless of what that module itself needs.

Confirmed by execution 4 September: importing `quant/allocation.py`, which is
pure arithmetic over dicts and imports only `dataclasses` and `typing`, failed on
a missing `sqlalchemy`.

### `Allocation.total_value` means two different things

In `allocation_by_asset_class` it is invested plus cash. In
`allocation_by_sector` it is sectored value, cash and unsectored excluded.
Nothing downstream is wrong today - `portfolio_analysis_agent_node` maps the
sector one to `sectored_value` in the published JSON - but the dataclass field
carries two meanings depending on which constructor produced it.

Same family as the fields that read as live and are not: the name says one thing
at one call site and another at the other, and only the mapping in the node
keeps it honest.

### Router parameter ordering is nondeterministic — RESOLVED 7 September

**The cause was code, not the model, and this entry blamed the wrong thing.**
`smart_router.py` overwrote `parameters.tickers` after the LLM call with the
portfolio's tickers, via `list(set(llm_tickers + portfolio_tickers))`, and a
set has no order. Removed with the override itself - see "The router
overwrote `tickers` with the portfolio" under RESOLVED. The router's own
extraction is not known to be nondeterministic; nothing has measured it,
because `run_golden.py` still does not print `tickers`.

Kept because the wrong attribution sat here for three days while the actual
line was greppable. An observed symptom in a router output is not evidence
about the router until the code between the LLM and the state has been read.

---

## The twelve benchmark cases are not executable

Recorded 4 September. The gap is real; the timing is deliberate.

`benchmark.md` defines twelve cases with expected behaviour. None of them is an
automated pass/fail. `run_golden.py` diffs five routing fields and cannot see an
answer; `pytest` covers components, not cases. So "how many cases pass" is
assessed by reading CLI output, which is judgment, and judgment under no
deadline drifts toward thoroughness. A number that goes up is the one signal
neither care nor thoroughness can argue with.

**Why this is not simply "write the eval suite now."** The expected outputs are
free text from an LLM synthesizer. "Answers with the correct percentages" is not
a string comparison - the model can phrase it many ways and be right every time,
or produce the right figures under a wrong label. Asserting on prose needs
either structured output alongside it or a judge model, and a judge is a
non-deterministic instrument measuring a deterministic component. See "Where
non-determinism is allowed to live" above: the golden set is the wrong
instrument for judgment, and a judge is the wrong instrument for arithmetic.

**The way through is the split the architecture already has.** Assert on
`shared_data`, which is structured, then assert weakly on the prose: does the
answer contain those figures at all.

**Corrected 4 September, while writing the runner.** An earlier version of this
entry said case 1.1 should assert `allocation_by_asset_class` carries Equity at
0.6941 against expected_values.md Part 2. That assertion expires. Market values
move with prices, expected_values is pinned to the 2026-09-02 closes, and there
is no seam to pin a run against a date - `fetch_prices_tool` takes only
`tickers`, `period` and `interval`. A runner built that way would start failing
on price movement rather than on regression.

`tests/test_allocation.py` already checks those figures against Parts 2 and 3
with fixed inputs, which is the instrument that should own them. The runner
asserts what does not move: structure and invariants, the static cost-basis and
cash figures, the ticker set, whether the figures in `shared_data` reached the
prose, and whether Part 3b's as-of date is stated. The exact market-value check
stays where fixed inputs make it stable. That second check already exists as
`cli.py:132`, "NO NUMBERS IN ANSWER while shared_data has them", which prints a
warning where it could fail a test. The instrument is built; it just does not
assert.

**Shape:** `tests/benchmark/run_cases.py`, one query per case, printing `n/12`,
with a recorded reason per failing case. Not part of `pytest` - the cases cost
API calls and take minutes, so they are a third loop alongside the golden set,
not a fourth thing bolted onto the first.

**Build it with roadmap item 3, the synthesizer**, because that is the first
moment any case can pass end to end. A runner that can only ever print 0/12
reports nothing that this file does not already say. From item 3 onward, every
capability commit is expected to move the counter, and "done" for a roadmap item
means its case asserts rather than that its arithmetic is right.

Note item 2 already shipped this way at the computation layer:
`tests/test_allocation.py` carries fourteen assertions taken from
expected_values.md Parts 2 and 3, committed with the capability. What is missing
is the case-level assertion, not the value-level one.

---

## What works, recorded so it does not get re-litigated

From the first CLI baseline, 3 September 2026. The router classified all five test
queries and returned valid JSON; it mapped "past twelve months" to `1Y` correctly;
it took tickers from the portfolio rather than the message; confidence was
calibrated sensibly (0.6 on the ambiguous P&L question, 0.95 on volatility, 0.3 on
the out-of-scope one); the graph planned and executed with no agent
planned-but-not-run, so bug 7's seam is holding; `portfolio_id` flowed through and
switching portfolios changed the ticker set; DataAgent produced correct
covariance, returns and per-ticker volatility.

**The gap is capabilities, not architecture.**

---

## Directions, and decisions deferred with reasons

### Does the router stay a classifier, or become a tool-caller?

**Deferred until Level 1 passes and the IPS lands. Not now.**

Today the router makes one decision from the user's words and emits a plan. That
is exactly why the golden set can pin it: five routing fields, diffable, and a
prompt change that moves them is visible immediately. Free tool-calling would
answer questions nobody anticipated, which is what the equity-research goal
eventually wants, but it leaves nothing stable to diff — the fast loop would stop
being an instrument.

**Whichever way it goes, the tool shape decides the cost, and that shape is being
chosen now regardless.** A model calling `allocate(group_by=..., window=...)` is
trivial to add. Nine near-identical `allocation_by_X` functions are the same
brittleness with more steps, and each one has to be described to the model
separately. The decision about tool-calling can wait; the decision about whether
the quant layer is parameterised cannot, because every function added between now
and then is one more thing to unpick.

Related: the group_by entry above, and the router's inability to express an
absolute date range.

### Direction for `quant/`: one implementation per formula

**One tested implementation of each formula, reachable from anywhere, never
restated in a document.** D7 already names `quant/risk_metrics.py` canonical for
return-series volatility because five implementations existed. This is the
general form of that decision.

**D8 claiming the code matched when it did not is this rule being broken.** The
window rule lived in prose in `expected_values.md`, the code computed something
else, and the sentence asserting they agreed sat inside the reference document
for a day without either side being run against the other. A formula stated in a
document and implemented in code is two implementations, and one of them has no
test.

`portfolio_volatility(weights, cov_matrix)` is the next function into that
package (D7, roadmap item 4). Its check is a pytest fixture over the 252 closes
extracted from `expected_values.xlsx` and committed, not read from
`data/portfolio.db`, which is untracked and would not survive a fresh clone.

### Spans versus counts: is a window calendar days or closes?

**Deferred until a non-year period actually exists. Not now.**

The evaluation window is a count of closes — `years x trading_days_per_year` —
because that is what the reference computes and what D6 annualises by, and
because `tail` anchors to the last settled close without arithmetic. Every period
that exists today is a year multiple, so every one has a close count.

`_evaluation_window` raises on anything that is not a year rather than guessing,
because "3M" has two defensible readings and picking one in a helper would settle
the question silently:

- **a span** — ninety calendar days back from the last close, whatever number of
  closes that contains
- **a count** — sixty-three closes, being a quarter of 252

They differ by a few observations, which matters for a volatility figure and not
much else. Neither is more general: `period_days` and a close table are both
convention lookups against a resolved period, and both are missing months today.

**What is not deferred, and is the same in either reading:** the window ends at
the last settled close, never at `date.today()`. That is the anchor, it was the
actual bug, and it is fixed. The unit question is a separate and smaller thing
that got tangled with it during the 4 September sitting.

Decide it when someone asks for a quarter, with a real case in hand. Nothing
built now makes that decision easier, and choosing today means choosing blind.
