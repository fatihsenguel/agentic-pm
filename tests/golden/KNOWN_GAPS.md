# Known gaps (not bugs — unbuilt features, plus open decisions and why obvious fixes are wrong)

Last updated 10 September 2026, thirteenth session, on branch `selection`, after the personal IPS's binding (the policy a portfolio is checked against is named on its row, `portfolios.ips_path`, migrated; the compliance node loads that file in every mode; the loader has no default) and the growth rule for the type vocabulary, entry under Directions.

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

**9 September (ninth sitting).** Five of the six unguarded files still
existed (`test_portfolio_manager_simple.py` did not), and two of them
routed a live question through the model on the Demo Portfolio at every
collection; pytest also collected their bare `test()` coroutine, so each
ran its call twice per run. All five deleted (33f09b5): the suite went
from 408 in 24 seconds to 405 in 14, and no longer spends on Haiku or
touches portfolio 2. What `test_nodes_simple.py` alone exercised,
`load_portfolio_context`, has its own entry under Hygiene.

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

**7 September: four prompt changes, none visible to it.** `measure` and
`group_by` were added to the router's output, and `tickers` changed meaning,
and `run_golden.py` prints none of the three. Every one of the day's golden
diffs was empty except the one where a plan changed - which is the right
instrument for plans and no instrument at all for the fields the synthesizer
now dispatches on. The benchmark runner sees them; the fast loop does not.
Widening the printed fields is a decision about what the fast loop is for
and would move `expected.txt` for every query.

The CLI truncates `parameters` at roughly 260 characters, which is before
`measure` and `group_by`. It cannot show the field that selects the answer.

**A sixth field, 8 September (seventh sitting), printed only when nonzero.**
`retries: N` counts the router attempts the schema rejected before the
printed decision (83de9d9), read from the `Validation: Attempt N:` warnings
the router node now carries into the state (0f86384; it used to compute
them and drop them). Before this, a plan rejected by a validator and
repaired back to the pinned routing printed the same five fields as one
accepted first time, and the dependency validator below would have had no
instrument. Nonzero-only so that `expected.txt` did not move: zero diff on
the run after the commit, and no `retries` line on any of the five golden
runs this sitting. Parse failures and ticker errors carry no `Attempt`
prefix and are not counted.

**7 September (third sitting): a CLI check that could not distinguish two
states.** Two formatter lines were deleted (macro Recommendation, rebalance
Tactical Signal) and the instruction was to confirm in the CLI. Both live
runs errored before the branch - the macro path on "Yield curve data missing
from snapshot", the rebalance path on the missing target - so the answer was
a bare header with and without the deletion. `tests/test_synthesizer_formatters.py`
now feeds `_format_macro_response` and `_format_rebalance_response` a
synthetic successful `sub_results` and was checked to fail on the pre-deletion
source and pass on the current one. It is the first pytest that touches
anything in the synthesizer. It does not cover `synthesizer_node` itself, the
intent dispatch chain, or any other formatter; the note in §8 of the handoff
that pytest "collects nothing that exercises synthesizer_node" is still true
of the node.

**8 September (eighth sitting).** Sixteen queries: "How much has AAPL gained?" (pid 3) entered as the
diagnostic beside "gain today". `period` is now extraction's on every line,
so the field the runner prints is deterministic for the two `1Y` lines; it
still cannot see `measure`, `group_by` or `tickers`, and the prompt shrink
showed why that matters: the model's `policy_topic` flag moved two plan lines
and only the plan told. The runner is the loop that saw the mode.

**9 September (ninth sitting).** A seventh model-owned field, `status`, is
as invisible to the runner as `measure`; the benchmark runner saw its one
failed prediction (2.2 failing on clauses uncited) and the golden set,
run twice, saw nothing. Sixteen lines held both times.


### `trace_tool` and `log_delegation` are never called — RESOLVED 8 September (sixth sitting)

**Built, and the sentence below about the agent layer was wrong.** The
router node opened the request span and closed it in its own `finally`
(`RequestTraceContext.__exit__` sets `_current_trace = None`), so every
node after the router asked `get_current_request()` and got None: no
agent spans, no tool calls, no handovers in any live trace, `agents_used`
== `["Router"]`. The 13 `trace_agent` call sites were reachable inside the
router only. Fixed in a07c523: `run_agent_graph` owns one span under the
state's request id, the router traces its own span like every other node.
`ComplianceAgent` traces its checker call (`trace_tool("check_ips")`,
bb52a01) and `mark_agent_complete` emits one DELEGATION event to the next
agent in the plan, naming the result keys handed over (8e32a25). `check_2_1`
reads the stored trace by request id and asserts spans, handovers and the
tool call; 2.1 passes. Two commit messages (8e32a25, bb52a01) claimed the
CLI would show the new events before the span was fixed; both were
registration, not reachability, and are corrected here, not rewritten.

`stream_agent_graph` (graph.py) is a second entry point; it has no caller
and opens no span. Recorded, not wired.

---

`observability/tracer.py` fully implements `ToolTrace` and
`AgentTrace.log_delegation`. Nothing invokes either. All 13 call sites across
`nodes.py` and `smart_router.py` use `trace_agent` only.

benchmark.md 2.1 passes only when "trace shows contract handovers" — that is the
`log_delegation` path. **Benchmark 2.1 cannot pass today for tracing reasons
alone, independent of the agents.** Part 4 says tracing is largely done and only
needs verifying; the verification result was recorded as "the agent layer is
done" — false on a live run, see above.

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

### No golden query runs against portfolio 3 - RESOLVED 10 September (tenth sitting)

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

**Resolved 10 September (tenth sitting), the other way round (c94603c,
93290af).** The six queries on portfolios 1 and 2 moved to portfolio 3
with the prediction that all five routing fields hold on all sixteen
lines; two runs, identical, only the printed pid moved. Then portfolios 1
and 2 were deleted from the database on the owner's decision: they had no
purchase dates and could have no ledger. Every portfolio query in the fast
loop now runs on the portfolio the benchmark is scored on; the extraction
table mirrors it (its `SOME` tuple is a held set that is no portfolio).

### Seeding portfolio 3 rewrites metadata shared with portfolios 1 and 2 - MOOT 10 September (tenth sitting)

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

**Moot 10 September (tenth sitting).** Portfolios 1 and 2 are deleted;
the nine assets are shared with nothing. The reseed still rewrites their
metadata, to the same values; `--reset` is run by hand.

### `test_portfolio_integration.py` still does not assert - RESOLVED 10 September (tenth sitting)

Confirmed by pytest emitting `PytestReturnNotNoneWarning` for
`test_1_portfolio_crud` and `test_3_state_portfolio_context`. Every test function
returns True/False and a `main()` tallies them; pytest ignores return values, so
all pass unconditionally. 18 return statements, several marked "Skip, not fail".

So "91 passed" means 91 collected and none errored, not 91 things verified.

Fixing means rewriting with real assertions, not a mechanical return -> assert
swap. Expect genuine failures once it does.

**9 September (ninth sitting).** Its `test_2` routes live twice per pytest
run, and asserts the router filled `tickers` on "Analyze my portfolio",
false since the padding block went; the `except Exception` swallows the
error and the function returns False, which pytest ignores. Two asserts
on the deleted `parameters.portfolio_id` were removed from it (1238792);
the rest is untouched and still passes unconditionally.

**Resolved 10 September (tenth sitting), by deletion (c6241a4).** The
round trip it checked is covered with assertions by
`test_holdings_from_ledger.py`; the suite lost its last two live model
calls and its two return-value warnings. The demo helper it alone called,
`get_or_create_demo_portfolio`, went with `add_holding` (be14e4b).

---

## Silent-wrong bugs found, not yet fixed

The recurring failure shape in this codebase: repair instead of raise, so a wrong
answer arrives with a plausible face instead of an error. Same family as bugs 5,
6 and 9 from the recovery session.


### The stored closes were dividend-adjusted, and changed after the fact - RESOLVED 10 September (twelfth session)

Found 10 September (twelfth session) while designing DIRECTION.md Order 2
item 3, before any code. `YFinanceProvider.get_daily_prices` called the
library's `history()` with its default, and the default replaces the close
with the dividend-adjusted close: every stored figure for a date before a
holding's latest ex-dividend date was lower than the exchange's print by
the product of the later dividend factors, and changed on each refetch
after a new ex-dividend date. Measured against the committed 252-close
series (`benchmark_closes.csv`, as-traded prints): 1,629 of 2,268 cells
disagreed, every holding except GLD, which pays no dividend, up to 4.4% on
TLT; 1,124 of the 1,579 rows dated 2026 were not on a cent. Part 1's nine
09-02 closes still agreed only because 09-02 lay after each holding's
latest ex-dividend date at the time they were fetched. The valuation on the
as-of date was therefore right by coincidence, and the volatility ran on a
series that was not the reference's.

**What "defended with real money" came to mean.** expected_values.md Part 9
(608d5be), decisions D19 and D20: a close is the exchange's official
closing price as traded, split-adjusted and nothing else, the figure a
broker statement values the position at; when two sources disagree the
exchange's print wins, nothing averages, and the reference does not move.
The second source is the listing exchange's own historical quotes, fetched
by the owner from the shell on 2026-09-10, 99 rows: all nine 09-02 closes
agree with Part 1 to the cent, all 90 rows inside the committed series
agree with it, and the two falsifier rows before a dividend (JNJ
2026-08-21, TLT 2026-08-28) showed the database wrong by exactly one
dividend factor. A check on the most recent date alone passes in both
states, which is why the falsifier rows exist. The workbook's `Prices`
sheet carries the same rows as formulas (57a3966), unopened in Excel.

**Built, one commit per layer, test first.** `tests/test_price_source.py`
(d79a1e0): Part 9's figures against the csv, and a stand-in for the
library whose `history` does what the documented default does, so the test
failed on the provider that took the default and passed on the one flag
(`auto_adjust=False`, 314b707). Then `daily_prices.source`, the mirror of
`fx_rates.source`: schema test (9d3cb6f), model and migration 2ee0c9249a9f
(736d8fa; applied and reverted on a scratch copy first, the existing rows
filled with the literal `yfinance`), the fetch writing `provider.name`
instead of a literal (614c5fb, b3f245a). Then, by the owner's hand and
with the output pasted: the migration applied, the nine holdings' price
rows and their fetch records deleted, one CLI question refetching 771 rows
per holding as traded. After it the database reproduces every one of the
2,268 committed cells, every row is a cent print, and the two falsifier
rows read the exchange's figures. Suite 595 after this item.

**What stays.** The rate fetch and the VIX fetch are untouched: nothing to
adjust. Whether the covariance should run on a total-return series built
from prints and the dividends table is a Part 4 decision (D5 to D8 are
silent; Part 4 was computed on prints; entry under Directions). The answer
text does not name the source (entry under Hygiene). The four leftover
tickers still hold adjusted rows (entry under Hygiene). A held instrument
that splits gets its Part 9 row before the code is trusted on it.

### `RouterDecision.validate_execution_order` repairs instead of raising - RESOLVED 8 September (eighth sitting)

Recorded 7 September (third sitting). When `execution_order` disagrees with `agents_needed`
and the two have the same length, the validator overwrites `execution_order`
from `agents_needed` and returns valid. A router that named the right agents
in the wrong order is silently reordered; a router that named different
agents in the two fields is silently corrected to one of them. Nothing in the
trace records that this happened. Repair-instead-of-raise, on the contract
that the whole graph is planned from. The `out_of_scope` validator added the
same day raises instead; this one should too, once the golden set has shown
how often Haiku actually triggers it.

**A second gap in the same validator, 8 September (sixth sitting).** It
checks that the order matches the task list and nothing about whether the
order can run. The "too big" diagnostics produced `[PortfolioAnalysisAgent]`
alone (no DataAgent; the node raised on missing holdings) and
`[ComplianceAgent]` alone under `risk_analysis` (an agent no formatter reads
under that intent; the node raised on missing allocation), both accepted by
validation and discovered by a node. Proposed shape, not built: a
`REQUIRES` mapping beside `AGENTS` (`PortfolioAnalysisAgent` needs
`DataAgent` before it - the one dependency verified to raise), a validator
that raises when an agent precedes what it requires and when ComplianceAgent
is planned under any intent but `compliance` (`validate_compliance` covers
that intent already). A raise there is a second attempt: `SmartRouter`
retries with `REPAIR_PROMPT` carrying the error text. Golden twice, with the
prediction written first; it is the least certain prediction on the list
because it changes what the router is told after a mistake.

**The second gap is built, 8 September (seventh sitting), d4c102d.**
`REQUIRES` beside `AGENTS`, one entry, checked against the roster at
import; `validate_dependencies` raises when an agent precedes what it
requires, never reorders; `validate_compliance`'s non-compliance branch
raises on ComplianceAgent under any other intent. The error names the plan
and was seen reaching the repair prompt's ERROR line. Eight tests hold the
three diagnostic shapes rejected and six shapes deliberately still
accepted - `[OptimizationAgent]` alone and a backtest with no optimiser are
what the prompt's own examples plan, so those dependencies contradict a
shown example and wait for their own prompt commits. Golden twice: all
fifteen lines held, no `retries`; the flip did not occur on either run, so
the rejection was exercised offline only. The prediction that mattered was
the falsifier - no line may show a rejected shape - and it held.

**The first gap stays open.** The reorder-repair is untouched. Note that
`test_execution_order_mismatch` had been passing on `reasoning` being four
characters, below the schema's minimum, not on the order; with a valid
reasoning the mismatched order validates and is repaired. Pinned as it is
in 8f99b04 so the test sees the validator it names.

**Resolved by deletion, 8 September (eighth sitting), e86841c.** Once every plan is derived from the
terminal table (bc2b555) the router writes `execution_order` and
`agents_needed` before validation, and after `combined` was retired
(ce7032f) no intent's plan was the model's; the repair had nothing to fire
on. Deleted with the `execution_plan` alias validator and property, which
accepted a plan under another name from a model no longer asked for one.
`validate_plan` replaces it: a derived intent must carry its derived plan
exactly, the error naming both plans; nothing reorders.


### A router failure becomes a clarification with confidence 0.0

Recorded 7 September (third sitting). `SmartRouter.route` catches every exception and returns
`_create_fallback_decision`, which is `clarification_needed` with a fixed
German apology. Any failure between the LLM call and the decision - parse,
validation, network - reaches the user as "could you be more specific" and
reaches the trace as a routed clarification. Same shape as above.

**Not quite, read again 8 September (seventh sitting).** Three rejected
attempts do not reach the fallback. `_call_llm_with_retry` returns
`(None, validation)` without raising, `route` passes the None through, and
`router_node` then fails on `decision.intent` and records "Router error:
'NoneType' object has no attribute 'intent'". On the golden set that is
`intent: None`, `plan: None`, no agents, `errors: 1`. The fallback above is
reached only by an exception inside `route` itself. Two failure paths, two
faces, neither naming the three rejections; the warnings carrying them
(0f86384) are lost on this path because the node returns before merging
them. Not chased.

**The repair prompt is context-free.** Attempts 2 and 3 send
`REPAIR_PROMPT` alone: the error, a schema skeleton, the original request.
No roster, no rules 1-7, no few-shots, no portfolio context. A validator
rejection is therefore answered by a model that has never seen the rule it
broke. Untested live: no golden line has retried since the dependency
validator landed. When one does, the repaired plan is the first observation
of what this path produces, and if it is runnable but wrong the fix is
structural - the repair carrying the full system prompt plus the error -
not a wording.

**A third face, 8 September (eighth sitting).** Extraction now returns a `clarification_needed`
decision of its own, at confidence 1.0, with no model call, for a typo of a
holding, a span the vocabulary lacks, or two weights; it carries a
`reasoning` beginning "Extraction could not resolve" and, for the typo, a
`pending` record. So three paths produce the intent: extraction's (honest,
deterministic), the model's, and the fallback above (an exception wearing a
question). The fallback is still confidence 0.0 with the German apology.


### CostCalculator reports costs for the wrong model

`observability/tracer.py:406` — `PRICING` is a 2024 table with no Anthropic 4.x
entries, and `estimate_cost` does `PRICING.get(model, PRICING["gpt-4-turbo"])`.
The active model (`claude-haiku-4-5-20251001`) is absent, so every cost figure
silently uses GPT-4-Turbo rates.

Fix the table and raise on unknown models. Matters disproportionately: the target
role names LLM monitoring and evaluation, and this is the monitoring layer.

### `ANTHROPIC_SONNET` points at the Haiku model id - RESOLVED 10 September (tenth sitting)

`agents/config.py:73-75`. Flipping `ACTIVE_LLM_CONFIG` would silently give Haiku
with no error. `smart_router.py:104` imports it behind
`self.config.use_stronger_model`, so the path is reachable. Verify the current
Sonnet string against `GET /v1/models` rather than typing one in.

**9 September (ninth sitting).** `claude-sonnet-5` is accepted by the
token counter, so the id is known; the config line is unchanged, since
decision 16 was logged rather than taken (its entry under Directions).

**Resolved 10 September (tenth sitting), fc8c13c.** `claude-sonnet-5`,
with a test that the two configs no longer share an id. The switch stays
off; decision 16 is still logged, not taken.

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

### No FX conversion anywhere - RESOLVED 10 September (eleventh session)

`Asset.currency` is populated at `data_manager.py:413` and read only for display;
`rebalance_tools.py` stamps `cfg.currency_symbol` on numbers regardless of their
actual currency. Blocks a real EUR portfolio: cost basis in EUR against
USD-quoted yfinance prices for US tickers makes 1.2's P&L wrong by the exchange
rate, silently. Severity depends on whether tickers carry an exchange suffix
(`AAPL` vs `AAPL.DE`) — with the suffix, prices come back in EUR and the problem
does not arise.

**10 September (tenth sitting): the reference exists, the code does
not.** expected_values.md Part 8 C and decisions D15-D18 (0aa030c; the
workbook's `Ledger` sheet section C, cf8eb66): the base currency is the
portfolio's; a price is in the asset's currency and a foreign holding's
value is quantity x price x the spot rate on the price's as-of date, both
dates stated; spot rates are a price source, per day, dated, a missing
rate raises; cost basis, average price and realized gain are in the base
currency, so a foreign holding's average is not comparable to its quote
and a formatter names the currency of every figure. One buy of 100 AAPL at
200.00 USD at a stated 0.9200 with 5.00 EUR fees is 18,405.00 EUR, 184.05
average; at 324.96 and a stated 0.8500 spot, 27,621.60, +9,216.60,
+50.08%. The order when built: tests over Part 8 C, a rate table and its
migration, the analysis node multiplying by the rate, the formatters
naming currencies. Not started; the runner should not move on portfolio 3,
which is USD throughout. The currency split of a gain is named and not
computed.

**Built 10 September (eleventh session), in that order, each step a test
first.** `tests/test_fx.py` over Part 8 C (bf8305c, d40d4ed), which fixed
the shape before any code: one rate entry per holding, None when the
currencies agree, the rate on the price's as-of date otherwise, and a
missing one raising. The tables: `fx_rates` (base, quote, date, rate,
source; every column required, rate meaning base units per one unit of
quote, so Part 8 C's "EUR/USD 0.85" is euros per dollar; 210f8c8) and
`fx_fetch_metadata`, the pair's cache record kept apart from
`asset_fetch_metadata` because a pair has no asset (7921d2e). The fetch,
`DataManager.update_fx_rates`, under the price cache's rules, and the
provider method asking Yahoo for `{quote}{base}=X`: `USDEUR=X` quotes
euros per dollar, checked live against `EURUSD=X` (3b3a2a6). The lookup,
`quant/fx.py`, and `rates` as a required argument on the three allocation
views and `position_pnl`, `_market_values` the one place the rate is
applied (07fa460). The analysis node reading `base_currency` and
`fx_rates` from `shared_data`, valuing through the rate and publishing
the rate and its date beside the price's (116119e); DataAgent publishing
the two keys, the holdings' currencies, and only the rates on the held
tickers' as-of dates (441f633). The formatters naming the currency of
every amount: the allocation total and each table's header, the P&L with
the quote in the asset's currency beside the euro average and a
"converted at 0.8500 EUR per USD as of" line, the compliance total and
distances (42f3dc9, 6d86818). Part 8 C reproduces through the node:
27,621.60 EUR, +9,216.60, +50.08%, both dates; without the rate the node
refuses naming USD and 2026-09-02 and publishes nothing. Runner 12/12
after the formatters, as predicted; the golden set was not run, since
no routing changed. What stays: the rebalance tools' fixed euro sign
below is untouched and still the wrong-currency stamp; the currency
split of a gain is named in the answer and not computed; a euro
portfolio exists as fixtures only, and the workbook's `Ledger` sheet C
still has no cached values until it is opened and saved in Excel.

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

**Compliance branch, 8 September (sixth sitting).** `intent == "compliance"`
goes to `_format_compliance_response`, which renders by what the block
carries: a topic lookup, a hypothetical weight, or the portfolio check. It
prints the published figures and computes none; `test_compliance_formatter.py`
holds every percentage in its prose to a finding. One report serves 2.1, 2.2
and 2.3 - they ask the same check from three angles and the router carries
no sub-measure for compliance. Recorded, not hidden; a `measure`-like axis
for compliance is a decision when a case needs one.

**8 September (eighth sitting).** The `combined` branch is gone with the intent (ce7032f). The stub
below is still reached by a price fetch with no analysis agent, and now also
by any derived plan whose agents all fail: "Backtest SPY and TLT over 5
years" ran DataAgent, OptimizationAgent and BacktestAgent, the optimiser
failed, and the answer was a header with nothing under it (its own entry
under Hygiene, "Optimization failed: None").


### `shared_data` carries 160KB of raw prices — hot potato violated

`price_data_json` was 67,190 characters of daily OHLC on the 3Y queries and
22,501 on the 1Y query. **Measured again 4 September on portfolio 3: 161,557
characters**, 2.4x the recorded figure — the earlier measurement was taken on
fewer tickers. It scales with the ticker count, so the recorded number is a floor
and not a size. `state.py:50` states shared_data holds summaries, not raw
DataFrames, and the module docstring calls this the Hot Potato principle.
Seen again 7 September (third sitting) at 162,186 characters in the CLI on a
rebalance query; the heading used to say 67KB, which was the January figure.

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

Correct fix: targets belong to the IPS - a clause with target weights per
asset class, in `ips.toml`. Not `ips_manager.py` on `wip/phase7-snapshot`,
which was read and rejected (entry below). The IPS is built (8 September);
a target-weights clause is a change to `docs/IPS.md`, which is the owner's,
and a new clause type for the loader. Owner's decision, still open. The
same is true of moving `OUT_OF_SCOPE_RESPONSE` into the IPS (handoff §7.7).

**8 September (eighth sitting).** `REQUIRES` was closed to what the nodes raise on (0d60f18) and
deliberately carries no entry from RebalanceAgent to the optimiser; the
derived plan for `rebalancing` is `[DataAgent, RebalanceAgent]` and the
golden line keeps its pinned `errors: 1`. The target is still the IPS's to
state (pending decision 8).


### `wip/phase7-snapshot` was read and rejected - DECIDED 7 September (fourth sitting)

Every document said the IPS comes from this branch: handoff §2 and §7.2,
benchmark.md Part 1, Part 3's Level 2 status note and Part 4 item 3, the
roadmap's ordering principle and Phase 3, the rebalance entry below, and the
runner's blocked-probe message. None of them had been checked against the
branch. Its own commit message says "UNVERIFIED, do not build on this", and
that is right for a stronger reason than staleness.

What is there (`ips_manager.py` read in full, `compliance_agent.py`'s
structure and `run_compliance_check`, `esg_screener.py` by name only):

- A multi-client engine: `Client` and `ClientIPS` tables, `jurisdiction`,
  `tax_status`, five risk profiles, an ESG exclusion table. benchmark.md
  promises no multi-user operation and no case needs ESG.
- Rules are database rows with a `constraint_name` label. No clause
  identifier and no clause text, so 3.1 cannot cite and 3.4 cannot say
  "nothing", which needs a closed, identifiable set of clauses.
- Repair-instead-of-raise, six places seen: no client -> invented default
  constraints and a compliance verdict against a policy nobody wrote;
  unknown severity -> `HIGH`; missing tolerance -> `0.05`; unknown risk
  profile -> `"moderate"`; empty portfolio -> `COMPLIANT`; policy numbers in
  a `profiles` dict inside the manager.
- A second arithmetic path: `_load_holdings` and `_get_current_price`
  recompute the market values and weights PortfolioAnalysisAgent already
  publishes, with no reference in expected_values.md.
- It recommends: `_generate_recommendations` and `_breach_to_trade` produce
  trades, the surface the third sitting cut and the thing 2.3 forbids.
- Every import is `from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src...`;
  it needs `config.compliance` and three tables baseline-v1 does not have.

Pulling it "one file at a time" would mean deleting all of the above and
keeping three enum names. Decided instead:

- The IPS is a prose document with numbered clauses, written by the owner;
  `ips.toml` at the repo root is derived from it, one entry per clause with
  the clause id, a type, parameters and the clause text so a citation is
  the owner's words. Policy in config, not code and not the database.
- The type vocabulary is closed and the loader raises on anything the
  checker cannot check. Currency risk has no type on purpose; that is what
  makes 3.4 pass on merit.
- A pure `load_ips()` and `check(ips, allocation)` over the allocation
  block PortfolioAnalysisAgent publishes to `shared_data` - no second
  arithmetic path - returning per clause: id, observed, limit, status, and
  for a breach the distance to the limit (2.3 is a condition, not a trade).
  Denominator is D2's, total value including cash. Unit-tested against an
  expected_values.md Part 7 computed by hand first.
- The ComplianceAgent node last: reads `shared_data`, calls the checker,
  publishes `shared_data["compliance"]`; the synthesizer formats and cites.
  It enters `AGENTS` then, one line and one binding. `trace_tool` and
  `log_delegation` are wired with it, for 2.1. 3.1 is the checker applied to
  a hypothetical weight, not to holdings.
- Order: Part 7 -> runner checks for 2.2, 2.3, 3.1, 3.4 (structure: a
  clause id is cited and exists in the loaded file, status is a breach or
  refusal, no trade line) -> `ips.toml` and loader -> checker -> node ->
  prompt and route, golden twice -> formatter. Each its own commit. The
  runner is expected to move at the node commit and not before.

Open at the time of writing, decided before any TOML: whether a clause the
checker cannot check is still citable (a type with no checker, or a
checker-only file); instrument limit versus issuer limit as separate types
(SPY is 500 issuers) and what each needs from the allocation block; which
agent is the "Risk" agent 2.1 names on this branch.

**Status 8 September.** `docs/IPS.md` exists (synthetic, for portfolio 3;
a personal one replaces it later as a local file) and settled the first
two: unnumbered clauses are `statement` entries, citable and not computed,
so the policy is visibly full and still silent on currency (3.4); IPS-4.1
is per instrument, funds included, and IPS-4.2 is per issuer over directly
held shares only, so there is no look-through and no gap to report. Which
holdings are shares is carried data - `Asset.instrument_type`, `share` or
`fund`, set by the seed, checker raises when missing - accepted on the
strength of the `Compliance` sheet's own note. The third, the Risk agent,
is PortfolioAnalysisAgent - **accepted 8 September (sixth sitting)**, with
the `concentration` measure deferred: 2.1's concentration figures are the
IPS-4.x findings, and a second place for the same division is the
second-arithmetic-path shape this entry rejects; the trigger to add it is
the first concentration question with no policy attached. The
`shared_data["compliance"]` shape was **accepted the same day with six
changes**, all checked against the block `nodes.py` publishes: `total_value`
added (every Part 7 distance reproduces as `observed_value - limit x
total`), units pinned (observed and limit fractions, `distance_pp` in
points, `distance_value` currency), `as_of` copied from the allocation and
absent when nothing was priced, `no_clause` set by the node and never by
the pure checker, one finding per (clause, subject, bound) so a band emits
two, and `exempt` carrying no arithmetic; a seventh key `topic` arrived
with the lookup mode. expected_values.md Part 7 and the workbook's
`Compliance` sheet agree on every figure; D9 (at the limit passes, strict,
unrounded) came from the sheet.

**Built, 8 September (sixth sitting), in §7's order:** the four runner
checks first (3567e0e..18b5fbe, each seen failing offline for its reason),
`ips.toml` and the loader (92639af), `Asset.instrument_type` (2ceea01,
22f3e41), the checker (30af89c, Part 7 to the cent), the node (bb52a01),
the compliance intent with `hypothetical_weight` and `policy_topic`
(b0807f5, b7a92bd), the formatter (6128c4f). Runner: 6/12 -> 10/12. Two
things learned on the way are their own entries: the request span (tracing
entry above) and the topic vocabulary (below, under "Is my AAPL position
too big?").

**D9's "unrounded" means "not rounded beyond the block".** The checker
consumes the cent-rounded market values and total the analysis node
publishes; the only unrounded path would be a second computation. So
18,083.175 prints as 18,083.17 where Part 7 says 18,083.18 - half a cent,
inside the runner's tolerance, visible in prose. The wording of D9 in
expected_values.md is the owner's to adjust; noted, not changed.

The branch stays where it is. Nothing on it is scheduled.

**8 September (eighth sitting).** The deferred `concentration` measure's trigger fired ("What's my
biggest position?") and it was built as a view of the one allocation
computation, `allocation.by_position`, Part 7's IPS-4.1 table largest first
(d361520, 7958af5), with `group_by: position` naming it (f465e13). Every
allocation line now carries `pct_of_total` (4b003be) and the checker reads
it for every clause: the sector arm (62ddbcd) and the concentration arms
(9c11bd1) stopped dividing, `position_pnl` left the checker's inputs, and
the module's only arithmetic is one subtraction per finding. The three
compliance modes are derived too: the weight from the message (f099101),
the lookup from its phrasing (55dd80c), otherwise the portfolio check.


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

**The Risk role is PortfolioAnalysisAgent, decided 8 September (sixth
sitting).** benchmark.md Part 2's roster names roles; the mapping is
recorded there. Nothing from this file was salvaged for it: the
concentration figures 2.1 needs are the compliance findings.

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

**8 September (eighth sitting).** "since 2021" is no longer repaired to `5Y`: extraction treats an
absolute year as a span the vocabulary lacks and asks naming the spans
(56caa2c). The gap itself - a defined window as an input - is unchanged.


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

**8 September (eighth sitting).** `group_by` gained `position` (f465e13), the third view, each value
still the key the agent publishes under (`by_asset_class`, `by_sector`,
`by_position`). `filter` is still not built; "Is my JNJ position over any
limit?" now carries `JNJ` in `tickers` from extraction and the compliance
formatter still has no selection axis to read it (the "Four wrong-faced
answers" entry).

**9 September, a second shape for the selection axis.** "Which of my
positions are over the limit?" routes to the portfolio check and answers
with the full 63-line report; the answer is inside it. So the axis the
compliance formatter lacks has at least two values: a named position
("Is my JNJ position over any limit?", `tickers` carries it since f099101)
and breaches only. The handoff names this the first code change of the
next sitting.

**9 September (ninth sitting), built.** Two values, two readers. A named
position is `tickers`, extraction's, read by the compliance formatter the
way the P&L formatter reads it (c0886c2): "Is my JNJ position over any
limit?" answers with JNJ's IPS-4.1 and 4.2 rows, its condition, the as-of
and the total, and a "Not shown" line. Breaches only is `status`, a
Literal with the one value `breach`, the model's like `measure` and
`group_by`, held to intent compliance and rejected beside a mode
(7232ecb, cb3e1c1, b4aada5). The prompt commit's prediction failed on
2.2 and 2.3 on the first run: read from the model's own output, it sets
`breach` on "does my allocation violate any rule" and "what would have to
change" as readily as on "which are over". Not reworded. The failure
direction moved instead (27a2ec0): the breach rendering keeps the
check's coverage in one line each - clauses within their limits by id
with their subjects, exempt funds by name, statements by id - so a
status the model over-sets shortens the answer and hides nothing, and
2.2 passes whatever it sets. Runner 12/12 after. `filter` is still not
built. Noted for a case that asks: `group_by`'s three values are exactly
the subject kinds of the findings, so "which of my *positions*" would
narrow the breach list by it; the model once set `group_by: position`
under compliance unasked. The one-figure entry's principle was decided
with this: selection is a parameter the formatter reads, its values the
block's own words, never a new measure.


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

### The macro path has not produced an answer since at least 3 September

Recorded 7 September (third sitting). Every live macro run ends in
`MacroAgent error: Yield curve data missing from snapshot`: `fetch_macro_data_tool`
reports 60 rows imported, `get_macro_snapshot_tool` returns a yield curve
block without `slope_raw`, and `macro_agent_node` raises on it - correctly.
`expected.txt` has recorded `errors: 1` on the macro golden query since the
first baseline, so the golden set has been pinning a failure as the expected
routing outcome. Not a routing defect and not chased: MacroAgent is tolerated,
not targeted (next entry). Recorded because it means the macro formatter's
success branch has not run in a month, which is why a CLI check of it could
not see anything.

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

### The macro `equity_adjustment` surface is a market-timing recommendation

Rewritten 7 September. The entry used to be titled after
`generate_taa_signal_tool`, and the 7 September handoff turned that into
"`generate_taa_signal_tool` is a live path". It is not. `macro_agent_node`
calls `assess_regime_tool`; nothing in `nodes.py` or `graph.py` calls
`generate_taa_signal_tool`, and the BaseAgent tool-calling loop (`get_tools`,
`tool_map`, the system prompt in `prompts.py`) has no caller from the graph.
Its only caller is `tests/test_phase5_4_integration.py`.

**Registration in a tools list is not reachability.** Grep for the caller.

The live surface is: `assess_regime_tool` → `MacroSignal.equity_adjustment`
→ `shared_data["macro_regime"]` → `_format_macro_response`, which prints
`**Recommendation:** Adjust equity by ±X%`, and `rebalance_agent_node`, which
copies it into `taa_signal` for `_format_rebalance_response`'s "Tactical
Signal" line. The router prompt teaches the same thing: the MULTI-STEP line
"Sollte ich bei diesem VIX-Level mehr in Bonds gehen?" → "allocation
recommendation", and few-shot example 4 (not rendered; the builder takes
three).

A regime-driven equity adjustment is a market-timing call. That sits under
"price or return forecasts" in benchmark.md Part 2's permanent list, not the
Levels 1–3 list, so it is a defect on its own terms rather than a 3.2
dependency. Resolution, decided 7 September, after 3.2 and as separate
commits so the 3.2 golden diff is not confounded: drop the macro
Recommendation line; drop the Tactical Signal line and leave the
`taa_signal` field in the rebalance result (removing the field is a
RebalanceAgent change, and MacroAgent is already recorded as tolerated);
retire the MULTI-STEP line and example 4. `generate_taa_signal_tool`,
`MacroSignal.equity_adjustment` and `prompts.py` stay as dead code, recorded
here.

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

**"last week" becomes `1Y`. Found 8 September** in a CLI session the evening
before. Not a router mistake: the extraction rule says "map natural language
to the nearest valid value", and for any span shorter than a year the nearest
valid value is `1Y`. A question about a week gets an answer about a year and
no error, because the prompt told the router to repair rather than refuse.
Same shape as the `3M` case above from the other side: there the schema is
wider than the config and the data layer raises; here the prompt is narrower
than the question and nothing raises. Fix belongs with the period-vocabulary
registry, not before: a span the vocabulary does not have is
`clarification_needed` naming the spans it does, never the nearest one.

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

**8 September (eighth sitting).** The prompt's period line is gone with the shrink (9364d24);
extraction reads `config.data.period_days.keys()` and never restates them
(56caa2c), so "last week becomes 1Y" is resolved: a span the vocabulary
lacks, months, weeks, days, an absolute year, "today" next to a change verb
(9c9be90), is a clarification naming the spans, before any model call. Two
sites remain: `nodes.py`'s dead `"3Y"` default on the period read, and the
schema's `^\d+[YMD]$` pattern, wider than the config, now unreachable
because extraction only ever writes a vocabulary key or None.

**9 September (ninth sitting).** The dead `"3Y"` default in `nodes.py`
deleted (043ed55). The schema's `^\d+[YMD]$` pattern remains, wider than
the config and unreachable.


### The agent roster is restated in eight places — RESOLVED 7 September (fourth sitting)

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

Worth doing before the seventh agent, not urgent before then. An earlier
version of this paragraph said the prompt text would change when rendered
from a registry and the commit should expect a golden diff. That was wrong:
rendering `N. Name - description` and the count from the same strings
reproduces the hand-written prompt byte for byte (checked with `diff` on the
rendered prompt before and after), so the correct expectation is zero golden
diff, and a moved line is the nondeterminism or a regression, never the
rerender. Observed 7 September (fourth sitting): empty diff on four runs, two
after each of the two commits.

**Resolved 7 September (fourth sitting), two commits.** First `AgentName.ROUTER`
was deleted on its own: no reader, and not a name the graph can run, so the
enum stopped accepting it before the enum was derived from anything. Then the
registry: `AGENTS` in `schemas.py`, an ordered dict of name to the one-line
prompt description. `AgentName` is built from it with the functional `Enum`
API (validation output checked identical under `use_enum_values`: plain
strings in `execution_order` and `agents_needed[].agent` before and after).
`router_prompts.py` assembles `ROUTER_SYSTEM_PROMPT` at import from three
literal pieces with the roster and its count rendered in between, plain
concatenation because of the JSON braces. `graph.py` derives `add_node`,
`routing_map` and the loop edges from `AGENTS`, and `route_next_step` returns
`str`: with an explicit `path_map`, LangGraph's `BranchSpec.from_path` never
reads the `Literal` annotation (langgraph 1.2.11), so it was a copy of the
roster that checked nothing. Sites 1, 2, 4, 5, 6, 7 and 8 read the registry;
3 (the few-shots, and the MULTI-STEP and EXECUTION ORDER prose) does not and
should not - it teaches plans by demonstration, not a roster.

**Not "name to node function", as this entry proposed.** The node binding
stays in `graph.py` as `AGENT_NODES`, with a `RuntimeError` at import if its
key set differs from `AGENTS` in either direction. `schemas.py` is a
pydantic-only leaf that `smart_router` imports; putting node coroutines in it
would pull `nodes.py`, `config` and langchain into the validation schema. So a
name is stated twice - roster and binding - and the second statement is
checked, which is the point: a missed site now aborts pytest collection at
`tests/test_graph_simple.py` (the first file to import `agents.graph`) with a
message naming both sets, instead of failing on the first live route as site
8 did on 4 September.

Four more places name the roster than the eight above, none of which the
registry reads; see "Roster sites the registry does not read" under Hygiene.

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

### The intent vocabulary is restated in five places - RESOLVED 8 September (eighth sitting)

Recorded 7 September (third sitting), while adding `out_of_scope`. `IntentType` in
`schemas.py`; the `INTENT TYPES` list in `ROUTER_SYSTEM_PROMPT`; the
`"intent": "a|b|c"` line in the same prompt's OUTPUT FORMAT; the same line in
`REPAIR_PROMPT`; and the `if intent == ...` chain in `synthesizer_node`. Same
shape as the agent roster. Adding `out_of_scope` touched four of the five in
three commits. Registry treatment wanted eventually; the roster registry
landed 7 September (fourth sitting) as its own commit and is the pattern:
one mapping in `schemas.py`, the prompt rendered from it, the chain in
`synthesizer_node` checked against it at import rather than derived.

Adding `compliance` on 8 September (sixth sitting) touched all five sites in
one commit (b0807f5) plus `validate_compliance`, which is per-intent logic
rather than a restatement. Still five sites, still by hand, still pending.

**Resolved 8 September (eighth sitting), 8c35dee.** `INTENTS` in `schemas.py`, value to prompt
description in prompt order; `IntentType` built from it; the INTENT TYPES
block and the schema's intent line in both prompts rendered from it;
`nodes.SYNTHESIZER_INTENTS` held to it at import, checked and not derived
(three branches condition on what ran). The rendered prompt was captured
before and compared after: byte-identical, zero golden diff. Six sites read
one statement. `UNKNOWN` was deleted first on its own (795f5e8), the way
`AgentName.ROUTER` was; `combined` was retired later (ce7032f) as a
vocabulary decision, being the last intent whose plan was the model's.


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

### Two router few-shot examples are benchmark prompts verbatim

"What is my current allocation by asset class?" and "What is my volatility
over the past twelve months?" appear in `router_prompts.py` word for word as
1.1 and 1.3. The router passes those cases partly by recognition. A third
example added on 7 September is a paraphrase of 3.3 ("How are my positions
doing?").

**Decided 7 September (third sitting): few-shots may not quote benchmark prompts verbatim.**
A benchmark prompt in the golden set is a test; the same prompt in a few-shot
is the router passing by recognition. The `out_of_scope` example added that
day uses a different instrument in German for this reason, and 3.2's prompt
went into the golden set, not the prompt. Replacing the two existing verbatim
examples is its own commit, later, golden set twice, and the runner is the
loop that shows whether 1.1 and 1.3 survive without recognition.

**8 September (eighth sitting).** Still there, now as intent examples: the shrink (9364d24) stripped
every `agents:`, `tickers:`, `period:` and weight field from the examples
and left the wordings. Replacing the two verbatim ones is still its own
commit. New: the third few-shot dictionary the builder appends ("Mein
Portfolio ist SPY 45%, TLT 25%, GLD 20%, VWO 10% ...") names four
percentages, which extraction would now ask about if a user typed it; it
teaches an intent from a shape the system cannot route. Logged, not changed.


### A second turn after a clarification hits the stub - RESOLVED 8 September (eighth sitting)

CLI, 7 September: "How is my position doing today?" (before the routing fix)
asked which position; the reply "AAPL for today" routed `data_fetch` with
`[DataAgent]` alone and produced the header-only stub. Conversation memory,
not a P&L defect; recorded so the shape is on file when 3.5 is built.

**Resolved 8 September (eighth sitting)**, as an extraction rule and not as prompt context
(docs/DIRECTION.md). The runner's two-turn case came first (7c7fb16): "Hows
my APPL doing?" then "yes", the check demanding a resolution recorded on the
decision so the pass is memory's and not the model reading the typo. Then
the state carries the previous turn's messages and the record of what it
asked (1e00bc2: `state["pending"]`, `run_agent_graph(previous=)`,
`get_user_message` now the last human message - it returned the first),
and extraction resolves the reply against the record before anything else
(5fca3bd): a confirmation or a named ticker substitutes into the original
question, which is routed as if typed; anything else is a new message. The
model never sees the history; `conversation_history` on the prompt builder
is dead. Runner 12/12. Only the unknown-ticker clarification has a record
and a rule; a reply to a span or a two-weights clarification is a new
message until a case asks for more.


### Patches that delete whitespace-only lines need `--ignore-whitespace`

`git apply --unidiff-zero` matches removed lines exactly. A patch removing
indented blank lines failed on 7 September on the owner's machine and applied
with `--ignore-whitespace`; every patch since has been applied that way.

### `IntentType.UNKNOWN` has no reader - RESOLVED 8 September (eighth sitting)

Recorded 7 September (third sitting). In the enum, absent from the prompt, referenced
nowhere (`_create_fallback_decision` uses `CLARIFICATION_NEEDED`). Deletion is
safe. Not done alongside adding `out_of_scope`: two vocabulary changes, one
case behind them.

**Resolved 8 September (eighth sitting), 795f5e8.** Deleted on its own before the registry; a
decision carrying it is rejected at the schema.


### `_decision_to_dict` drops `reasoning` and `clarification_question` - RESOLVED 10 September (tenth sitting)

Recorded 8 September (seventh sitting). The dict `router_node` stores
carries intent, confidence, agents_needed, parameters and execution_order.
`cli.py` prints `reasoning` and "asked back" from that dict, so neither
line has ever printed; the clarification text reaches the CLI only as the
answer. The runner's blocked reason reads it from `final_response` for the
same reason (60f4b62). Putting the two keys back is a state-shape change,
own commit, and would make the CLI's lines reachable.

**8 September (eighth sitting).** `clarification_question` is carried since 1e00bc2, with the new
`pending` record, and `resolved` since 5fca3bd; the CLI's "asked back" line
printed for the first time. `reasoning` is still dropped.

**9 September (ninth sitting).** Still dropped: the diagnostic that read
the model's `status` printed `reasoning: None` from the decision dict.
Pending decision 6, unchanged.

**Resolved 10 September (tenth sitting), 82d1d8e.** `reasoning` carried;
the CLI's line prints. The golden runner does not print it, so no line
moved.


### `AgentTask.depends_on` has no reader

Recorded 8 September (seventh sitting). Declared on the schema, filled by
the model if it chooses, read nowhere. The dependency validator holds the
plan to `REQUIRES`, the code's facts, and deliberately not to this field,
which is the model asserting its own dependencies. Deletion is safe; own
commit.

**8 September (eighth sitting).** Wider now: the whole `agents_needed` list is written by the router
from the derived plan (`task_description` "derived for intent X", `priority`
by position) and the model is not asked for it; `AgentTask` exists to carry
three fields nothing reads. Deletion of the task list is a state-shape
change, own decision.

**Resolved 9 September (ninth sitting), a7a24bc.** `AgentTask` and the
task list deleted: the graph's fallback to it was dead by derivation, the
tracer line and the out-of-scope validator read the plan, the decision
dict drops a key nothing read. A task list the model still sends is an
extra field, ignored; two tests send one to prove it.


### `SmartRouter.route` opens its own request span behind the observability flag

Recorded 8 September (seventh sitting). `route` calls
`self.tracer.trace_request(...)` and closes it in its own `finally` when
`self.tracer` is set, and `self.tracer` is set only when
`config.features.observability_enabled` is true. It is false here, so the
router traces nothing and `run_agent_graph`'s span survives. Turned on, the
router's `__exit__` would set `_current_trace = None` three nodes early -
the exact bug a07c523 fixed, one environment variable away.
`test_request_span.py` stubs the router and cannot see it.

### `router_node` computed its validation warnings and dropped them - RESOLVED 8 September (seventh sitting)

The loop `for error in validation.errors: add_warning(state, ...)` discarded
the dict `add_warning` returned, so no rejected router attempt ever reached
`state["warnings"]`, the CLI's WARNINGS section or the golden runner.
Fixed in 0f86384: the list is built once and returned on both paths, four
tests. Registration, not reachability, one level down from the span:
the helper existed, the call existed, the value went nowhere.
`state.add_warning` now has no caller.

### Four wrong-faced answers behind 11/12, from the CLI, 8 September

Recorded 8 September (seventh sitting, after the merge). The owner ran nine
prompts in `cli.py` against portfolio 3. Four came back correct, one was the
pinned false refusal ("How much did AAPL gain today?"), and four answered a
different question from the one asked, each with a plausible face - while
the runner stood at 11/12. No loop asks these questions: the golden set pins
routing, the runner asks its twelve, pytest asks components. The CLI is the
loop that found them, which is what it is for. Prompts verbatim:

- **"Is my JNJ position over any limit?"** - the full policy report, thirty
  lines, flagged by the CLI as identical to the answer for "What
  concentration risk do I have, and is it compatible with my investment
  policy?". Two defects. The router returned `tickers: []` although JNJ is
  named (rule 2 says extract what the user names), so the decision carries
  no selection. And the compliance formatter has no selection axis: the
  "one report serves 2.1, 2.2 and 2.3" note under the synthesizer entry said
  a measure-like axis for compliance is a decision when a case needs one.
  A question needs one. Under `docs/DIRECTION.md` the ticker half is
  extraction, not a prompt sentence.
- **"What's my biggest position?"** - both allocation breakdowns; SPY's
  18.74% of total appears nowhere in the answer. No per-position view is
  published: allocation is by class and by sector, and the only per-position
  shares of total are inside the IPS-4.1 findings. This is the trigger the
  sixth sitting set for the deferred `concentration` measure - a
  concentration question with no policy attached - and it has fired. Also:
  the formatter's "Not done" line said "The question named no breakdown, so
  both are shown", which is false for a question that names positions; the
  line is emitted whenever `group_by` is null and does not read the question.
- **"What share of my portfolio is technology?"** - 54.84% of sectored value
  and 28.82% of invested value. "My portfolio" under D2 is total value
  including cash, and that figure, 27.73%, is computed only inside the
  IPS-4.3 check, which divides `by_sector.lines[].market_value` by
  `by_asset_class.total_value` itself. The sixth handoff recorded that both
  percentages the sector line carries are wrong for the checker; they are
  also wrong for the plain question. Part 7's IPS-4.3 column is the
  hand-computed reference for the missing figure (27.96% at the 09-02
  closes).
- **"How has my portfolio done over the last month?"** - position P&L since
  purchase, with `period` silently set to `1Y`. Two recorded gaps meeting:
  the period rule's "nearest valid value" repair ("last week becomes 1Y",
  under Configuration) and the absence of any window return. The header
  says "since purchase"; nothing says the month was not answered. Under
  `docs/DIRECTION.md` the period half is extraction: a span the vocabulary
  lacks is a clarification naming the spans it has.

Two more from the same session, correct answers with a limit worth naming:

- **"Could I put 11% into a new stock?"** was refused under IPS-4.2, correctly:
  a stock is a directly held share. But the hypothetical mode carries no
  instrument type - an unnamed position is treated as possibly a share, so
  "11% into a new ETF" would be refused the same way and wrongly. The mode
  needs the type when the user states it, and the schema has no field for
  it. A decision, not built.
- The nine prompts fetched nothing from the provider (every series cached)
  and every answer priced as of 2026-09-04, two closes past the reference.

**8 September (eighth sitting), each addressed, one half open.** "What share of my portfolio is
technology?" answers 27.73% of total beside the two Part 3 shares (4b003be
to dbb8bc2). "What's my biggest position?" answers the position table
largest first, SPY at its share of total (d361520 to f465e13). "How has my
portfolio done over the last month?" asks which of the five spans, with no
model call (56caa2c, f099101). "Is my JNJ position over any limit?" now
carries `tickers: ["JNJ"]` from extraction; the compliance formatter still
has no selection axis and answers with the full report - that half is the
open item, with `filter` (the `group_by`/`filter` entry). "Could I put 11%
into a new ETF?" still lacks the instrument type (pending decision 7).

**9 September session.** "Could I put 11% into a new ETF?" seen again,
refused under IPS-4.2 as before (pending decision 7). The JNJ question
carries `tickers: ["JNJ"]` and still gets the full report (the selection
axis, above).

**9 September (ninth sitting).** The JNJ half is closed by c0886c2: its two
rows and one condition, no other holding named.


### `ExtractedParameters` fields with no reader - grep, 8 September

Recorded 8 September (seventh sitting, after the merge), from
`grep -rnE '(parameters|params)(\.get\("F"|\["F"\]|\.F\b)' src/` for each
field F, excluding the schema and the router prompt. Readers exist for
`tickers` (`nodes.py` portfolio context and the P&L formatter), `period`
(DataAgent node), `max_volatility` (optimization node), `portfolio_value`
(backtest node), `measure`, `group_by` (`_format_analysis_response`),
`hypothetical_weight` and `policy_topic` (ComplianceAgent node). No reader:

- `target_return` - extracted, validated, read nowhere.
- `rebalance_threshold` - the same.
- `portfolio_id` - written by `SmartRouter.route` after the LLM call and
  never read from `parameters`: every node reads `state["portfolio_id"]`.
  A field that exists so that a copy of a value can be made.

`route_sync`'s return dict in `smart_router.py` restates `tickers`, `period`
and `max_volatility` by hand (recorded under Configuration); it is reached
only through `detect_intent_simple`, and both are convenience functions
with no caller in the graph. Relevant to the router restructure: extraction
before the LLM should carry only fields something reads.

**8 September (eighth sitting).** The model is no longer asked for any of `tickers`, `period`,
`max_volatility`, `hypothetical_weight`, `policy_topic`, `target_return`,
`portfolio_value`, `rebalance_threshold`, `is_multi_step` or
`requires_confirmation` (9364d24, 4d69e47): the first five are extraction's,
the rest are dead on both ends. `portfolio_value` keeps its reader in the
backtest node and no writer. `portfolio_id` on `parameters` is still written
by the router and read by nothing. Deletion candidates, each its own commit
after the grep.

**9 September (ninth sitting).** `target_return` (dccb201),
`rebalance_threshold` (7b9db26) and `portfolio_id` (1238792) deleted, each
after the grep. `portfolio_value` keeps its reader in the backtest node
and no writer, and stays.


### BaseAgent's tool-calling loop has no live caller - confirmed, 8 September

Grep run 8 September (seventh sitting, after the merge): `.process(` is
called on an agent nowhere in `src/`; the only caller is
`tests/test_phase5_4_integration.py:332`. `get_tools` is called from
`tests/test_rebalance.py` only. The graph's nodes in `nodes.py` call the
agents' tool functions directly and never the loop. This is the same fact
the macro `equity_adjustment` entry records ("the BaseAgent tool-calling
loop ... has no caller from the graph. Its only caller is
`tests/test_phase5_4_integration.py`"); it is confirmed here because the
router restructure under `docs/DIRECTION.md` must know that nothing live
depends on `BaseAgent.process`, `get_system_prompt` or `tool_map`.

**Corrected 8 September (eighth sitting).** "Called nowhere in `src/`" was one file short: `.process(`
is called at four sites in `risk_manager_agent.py`, which is itself never
instantiated (its own entry). The conclusion stands: nothing the graph runs
reaches the loop.


### Roster sites the registry does not read

Recorded 7 September (fourth sitting), while building the registry. Each
names agents by hand, none is read by anything live, and none was in the
eight-site list:

- `graph.py` `get_graph_mermaid()` - a ninth restatement, already stale (no
  PortfolioAnalysisAgent). Only reader is `print_graph`, only under
  `__main__`. Delete, or render from `AGENTS`; not worth rendering.
- `router_prompts.py` `build_router_prompt(available_agents=...)` - the
  docstring says "for dynamic routing"; the body never reads it.
  `SmartRouter.route` and `route_sync` thread it through and `router_node`
  never passes it. A dead parameter shaped like the registry's hook. Delete,
  own commit.
- `prompts.py` `get_agent_prompt` - a name-to-prompt map with a `RiskManager`
  key (no `Agent` suffix, matches nothing the graph has ever named) and no
  PortfolioAnalysisAgent. See the next entry: no live caller.
- `observability/tracer.py` `ConsoleFormatter.COLORS` - a consumer, not a
  roster; PortfolioAnalysisAgent simply has no colour. Cosmetic.

The per-node strings (`mark_agent_complete(state, "MacroAgent", ...)`,
`trace_agent("MacroAgent")`, the formatters' `sub_results.get("MacroAgent")`)
are each agent's own identity, three or four times inside its own node, not
the roster. The registry does not fix a typo there and was not meant to.

**8 September (eighth sitting).** The prompt no longer renders the roster at all (9364d24): the model
names no agent, so `build_router_prompt(available_agents=)` is dead twice
over, and `conversation_history=` joined it when memory became an extraction
rule. The out-of-scope description in `INTENTS` still names DataAgent and
PortfolioAnalysisAgent in one sentence (d8cd0d6's), left verbatim on purpose.

**9 September (ninth sitting).** `get_graph_mermaid` and `print_graph`
deleted (61158e1); `available_agents` and `conversation_history` deleted
from the builder and from `route()` (1320913); `prompts.py` deleted
(536a357). The tracer's `COLORS` map is the one site left.


### `get_agent_prompt`, `build_agent_prompt` and `build_system_prompt` have no caller

Recorded 7 September (fourth sitting). `prompts.py`: `get_agent_prompt` is
read only by `build_agent_prompt`, which nothing calls. `build_system_prompt`
is a separate function - it does not call `get_agent_prompt` - exported from
`agents/__init__.py` and also called by nothing. Each agent inlines its own
prompt in its `get_system_prompt`, and nothing outside `agents/__init__.py`
imports `prompts.py` - the `*_AGENT_PROMPT` constants are re-exported and
otherwise unread. Three dead functions, a stale map and a dead module;
deletion is safe and is its own commit, after a grep for every name the
`__init__` re-exports.

**Resolved 9 September (ninth sitting), 536a357.** The module, the import
and the export deleted; nothing outside the package `__init__` named any
of it.

### `_validate_decision`'s agent check is unreachable

Recorded 7 September (fourth sitting). `smart_router.py` `_validate_decision`
builds `valid_agents` from `AgentName` and errors on a task naming anything
else. It cannot fire: `AgentTask.agent` and `RouterDecision.execution_order`
are typed against `AgentName`, so Pydantic has already rejected the whole
response before this runs. Harmless, but a check that cannot fail is a check
nobody will notice going wrong. Delete with the next `smart_router.py` change.

**Resolved 9 September (ninth sitting), 300af9e.** Both the agent loop and
the length warning deleted, with the `AgentName` import that served only
the first.

### A workbook edit rode into a KNOWN_GAPS commit

Recorded 8 September. Commit `22508c9` ("Record that the router refuses
in-scope questions naming a held ticker...") reports two files changed,
34 insertions and 1 deletion. The patch it applied changed one file with
exactly those line counts, so the second file contributed no lines: a
binary, and the only tracked binary that was open at the time was
`tests/golden/expected_values.xlsx`, where the `Compliance` sheet was being
built. `git commit -am` staged it. The sheet is wanted; the commit message
does not mention it, and the history says a KNOWN_GAPS entry changed the
workbook. Not rewritten - rewriting four commits back for a message is more
risk than the record is worth. The rule it adds to the brief: `git status
--short` before every `commit -am`, and a modified tracked binary is its
own commit with its own message. Confirm with `git show --stat 22508c9`.

### `graph.py` carries dead duplicates of the state helpers - RESOLVED 10 September (tenth sitting)

`_get_next_agent_internal` and `_is_execution_complete_internal` duplicate
`state.get_next_agent` / `state.is_execution_complete` and have no caller;
`route_next_step` imports the `state.py` versions.

**9 September (ninth sitting).** The task-list fallback inside
`_get_next_agent_internal` went with the task list (a7a24bc); the two
dead duplicates themselves remain, still with no caller.

**Resolved 10 September (tenth sitting), be15869.** Both deleted after
the grep: the first was called only by the second, the second by nothing.

### Clarification exits the graph on a proxy, not on the intent

`router_node` writes `final_response` for `clarification_needed` and
`route_next_step` exits on "`final_response` set and no `sub_results`".
`out_of_scope` exits differently: empty plan → synthesizer → END, with the
synthesizer choosing the text. Aligning clarification with that shape would
move its text out of the LLM's `clarification_question` and into a formatter,
which is a conversation-memory question (3.5), not a 3.2 one.

**8 September (eighth sitting).** Extraction's clarifications take the same exit, and now carry the
question in the decision dict as well as in `final_response`. Unchanged
otherwise.


### `taa_signal` is still attached to the rebalance result

`rebalance_agent_node` copies `shared_data["macro_regime"]`'s regime and
`equity_adjustment` into `result["taa_signal"]`. The formatter line that
printed it went on 7 September (third sitting); the field stays because removing it is a
RebalanceAgent change. No reader.

### The first `out_of_scope` definition moved "Should I rebalance?" to clarification

Recorded 7 September (third sitting). The first wording listed in-scope
mechanics as "drift, rebalancing trades to a target" and closed with "if a
request could be an in-scope question, that is clarification_needed:
ambiguity wins over refusal". On the golden set "Should I rebalance my
portfolio?" moved from `rebalancing` / `[DataAgent, RebalanceAgent]` to
`clarification_needed` / `[]` - on both runs, so deterministic, not noise.
Reading: "should I" plus no stated target plus a rule that ambiguity resolves
to asking. The prediction for that patch was "the ten existing lines are
unchanged"; it was wrong. The fix (commit "Keep 'should I rebalance' on the
rebalancing intent") dropped "to a target", named the query as an in-scope
mechanic, and narrowed the ambiguity rule to in-scope-versus-out-of-scope.
Held on two runs afterwards. That fix quotes a golden query verbatim in the
prompt - the recognition problem the few-shot decision above forbids, one
level down. Left in because it is the phrasing that flipped; a paraphrase is
the thing to try when the two verbatim few-shots are replaced.

Note the query's `errors: 1` was and is real: RebalanceAgent runs with no
target source (see "Rebalance has no target allocation source"). The golden
set pins the routing, not the outcome.

### The router refuses in-scope questions that name a held ticker - RESOLVED 8 September (eighth sitting)

Recorded 8 September. A CLI session on the evening of 7 September routed
"How much did AAPL gain today?" to `out_of_scope` at confidence 0.95, with
a portfolio holding AAPL active. The question is about a position's P&L -
the same measure as 1.2 and 3.3 - and the router had the holdings list in
its context. It refused because the ticker is named without "my".

Two things the record needs to say. First, the `out_of_scope` rule's
sentence "Held or not held makes no difference" is about the ownership
judgement (buy/sell/hold), but it sits directly after the refusal list and
reads as "a question naming a stock is refused whether held or not". The
in-scope sentence that follows lists "its allocation, P&L, risk" but only
under "a portfolio the user already holds", which the router did not
connect to a bare ticker. Second, and the reason this was invisible: 3.2
asserts that an out-of-scope question is refused. It cannot see a router
that refuses too much, and neither could the golden set, which had no
in-scope query that names a held ticker without "my". Every refusal the
loops could see was a correct one.

Fix in two commits. Golden set first: "How much did AAPL gain today?" and
"Is my AAPL position too big?" added against portfolio 3 (the one that
holds AAPL and that the benchmark is scored on), run twice, and today's
routing pinned in `expected.txt` as it is, the way the macro query pins its
error, so the fix has something to be seen against. Then the prompt: one
sentence in the `out_of_scope` rule saying that a question about how a
ticker the portfolio holds has performed, gained, lost, or how large it is,
is a question about that position without the word "my" - `data_fetch`
with PortfolioAnalysisAgent, `measure` `position_pnl` or `allocation`,
`tickers` the named symbol. No few-shot, and not the golden wording:
a golden query in a few-shot is the router passing by recognition. The
prompt commit is its own commit before any compliance prompt change so the
two golden diffs stay separable. Prediction recorded with the commit.

**First attempt failed, 8 September.** The sentence went in (6e68c47) with
the prediction that both queries move to `data_fetch`. Neither moved: the
golden run with the sentence live routed both `out_of_scope`, identical to
the pinned pre-fix lines. Zero effect, wrong on both. Likely cause is
placement: the sentence sits at the end of the paragraph, after "Held or
not held makes no difference", which the router reads as the scope of the
refusal before it reaches the exception. Second hypothesis, its own commit:
reword that one counter-sentence so it scopes only the ownership judgement.
If that does not move both lines, the third is a few-shot with a different
ticker and wording, not stacked on the second. Each attempt is one change.

**Second attempt: partial, 8 September.** Rewording the counter-sentence
(d8cd0d6) moved "How much did AAPL gain today?" out of `out_of_scope` - to
`data_fetch` with `['DataAgent']` alone: a price fetch for AAPL, no
PortfolioAnalysisAgent, so no `measure` and an answer about the stock's
price rather than the position's gain. Not the plan predicted, and by this
project's standard a wrong answer with a plausible face is not better than
a refusal. "Is my AAPL position too big?" did not move. Both runs agreed;
the eleven old lines held. Pinned as it stands in the commit after d8cd0d6.

Two things decided from it. "Too big" is a compliance question - a size
against a limit - and it moves when the compliance intent enters the prompt,
with its own prediction, not now: routing it to `allocation` today and to
compliance next week is two prompt changes for one line. And the third
attempt for "gain today" is a few-shot: every in-scope rule in this prompt
that routes reliably has one, and the two sentence-level attempts show the
rule text alone does not reach a bare ticker. Different ticker, different
wording, "(active portfolio holding X)" annotation as the existing
examples use. Prediction: "gain today" gains PortfolioAnalysisAgent;
"too big" holds; eleven hold.

**Third attempt: wrong on both lines, 8 September.** The few-shot
("Is NEE up or down?", 31ce272) sent "How much did AAPL gain today?" back
to `out_of_scope`, and moved "Is my AAPL position too big?" - the line
predicted to hold - to `clarification_needed`. Both runs agreed; the
eleven old lines held. Pinned as it stands, and kept rather than reverted:
a refusal is an honest failure, and clarification on "too big" is
defensible while there is no policy to judge size against (the rule says
ambiguity wins over refusal). Attempt 2's state - a price fetch answering a
position question - was the worse of the three.

**Score for the sitting: three prompt edits, six line predictions, six
wrong.** Stopped. The lesson is not a fourth wording: two hypotheses are
tangled in the query and no edit so far could tell them apart. "Bare
ticker" is one; "today" is the other - the router may be reading "gain
today" as an intraday move, which the system does not compute, and
refusing that. A golden query with the ticker and without the word ("How
much has AAPL gained?") separates them at the cost of one line and no
prompt change. Whichever it is, the next edit to this paragraph is the
compliance one, and "too big" and "gain today" get their next prediction
there, not before. The false refusal stays pinned meanwhile, like the
macro line.

**8 September (sixth sitting).** The compliance intent (b0807f5) predicted
"too big" moves to `compliance` and "gain today" holds at `out_of_scope`.
"Gain today" held on every run since - still the pinned false refusal, its
diagnostic query still the pending decision. "Too big" moved and flipped;
its own entry follows. The three failed prompt edits (6e68c47, d8cd0d6,
31ce272) are still in the prompt; keep or revert is still the owner's.


Hypothesis, stated 7 September (third sitting), not believed. The PortfolioAnalysisAgent
rule sat after EXAMPLES and before a CRITICAL RULES list numbered 1-5,
numbered 6 with no list around it. The ticker-padding fix was in code
(`smart_router.py`) and stands regardless; the placement was fixed as its own
commit before the 3.2 prompt change so that the 3.2 golden diff is clean.

**Resolved 8 September (eighth sitting), by extraction and a pin that moved on a yes.** Extraction
reads the ticker (f099101); the shrink (9364d24) moved "How much did AAPL
gain today?" off the refusal to the position, answering P&L since purchase
for a question about the day; "today" next to a change verb is now a span
the vocabulary lacks (9c9be90) and the line is pinned as the deterministic
clarification (c086cd7), with "How much has AAPL gained?" beside it pinned
`data_fetch` with the analysis plan - the in-scope bare-ticker question
routed as designed. Pending decision 6 decided keep: the two sentence edits
are registry text and the NEE few-shot an intent example, and a change to
either is a fourth wording on this line.


### "Is my AAPL position too big?" flips between compliance and risk_analysis

Recorded 8 September (sixth sitting), after the compliance intent landed
(b0807f5). Prediction for that commit: the line moves to `compliance` /
`[DataAgent, PortfolioAnalysisAgent, ComplianceAgent]` / errors 0. Run 1
gave exactly that. Run 2 gave `risk_analysis` / `[PortfolioAnalysisAgent]` /
errors 1 - the analysis agent planned without DataAgent, which nothing in
`validate_execution_order` rejects, and the node raised on missing
holdings. A line that holds once in two has failed; this is the line's
fourth failed prediction (three on the record above) and the sitting
stopped there: no rewording.

The cause is readable in the prompt and was not read before predicting.
Rule 6 says concentration questions "keep intent risk_analysis and are
DataAgent alone"; rule 7 (b0807f5) says "a position is too big" is
compliance with the three-agent plan. "Too big" is both, and the router
picks one per run. The second rule was written without re-reading the
first.

Pinned as run 1 - the designed routing - so a diff on this line is the
known flip, the way the macro line pins its known error. Not pinned as
the old `clarification_needed`, which no run has produced since.

Next is a diagnostic, not a wording: two golden queries against portfolio
3 that separate the causes - one naming the policy without "too big"
("Is my AAPL position within my policy's limits?", predicted `compliance`,
stable) and one naming concentration without the policy ("Is AAPL too
concentrated?", predicted `risk_analysis` / `[DataAgent]` by rule 6). If
both are stable the collision is the two rules alone, and reconciling rule
6 with rule 7 - concentration now has a home - is one later, separate
change with its own prediction. Also noted for that change: a plan naming
PortfolioAnalysisAgent without DataAgent should be rejected by the
validator, not discovered by the node.

**Diagnostic run, 8 September, two runs.** "Is my AAPL position within
my policy's limits?" routed `compliance` / the three-agent plan / errors 0
both times: the policy word is deterministic. "Is AAPL too concentrated?"
routed `risk_analysis` both times and never produced a runnable plan:
`[PortfolioAnalysisAgent]` alone on run 1 (no DataAgent, node raised on
missing holdings), `[ComplianceAgent]` alone on run 2 (an agent no
formatter reads under that intent, node raised on missing allocation).
Rule 6's "DataAgent alone" appeared on neither. Pinned as run 1, a
failure like the macro line. So the "too big" flip is the two wordings
meeting, and beneath it is a code defect independent of wording:
`validate_execution_order` accepts a plan that cannot run - an agent
before what it requires, ComplianceAgent under another intent - and the
node discovers it. The next change is that validator, with a dependency
registry beside AGENTS, not a wording; the router's repair loop already
carries a validation error back to the model, so a raise becomes a second
attempt with the reason stated.

**Moved on b7a92bd, 8 September.** The commit that took the topic
vocabulary out of the prompt predicted all fifteen lines hold; "Is AAPL
too concentrated?" moved to `compliance` / the three-agent plan / errors 0
and held there on both runs, where it had been pinned as a failure. Second
failed prediction on the line; stopped, and pinned as observed. No cause
is recorded because none was established: the only removed text that
named concentration was the rendered topic list, and that is an
observation, not a model.

**The validator is built, 8 September (seventh sitting), d4c102d.** The
flip's plan, `[PortfolioAnalysisAgent]` alone, is now rejected before the
graph runs and sent back to the router as a repair attempt with the reason
stated; a flip run prints `retries: 1` and the repaired plan instead of an
unrunnable one. The flip itself was not observed on any of the five golden
runs this sitting, so the line has held at its pin and the repair path has
no live observation yet. Rule 6 and rule 7 still collide on "too big";
reconciling them is still the later, separate change.

**8 September (eighth sitting).** The flip is derived away: the plan is the table's for the intent and
parameters (bc2b555), so `[PortfolioAnalysisAgent]` alone cannot reach the
graph under any intent, with or without a retry. What remains is the
intent, and rule 6 and rule 7 (rules 3 and 4 since the shrink) still both
speak to "too big"; the line has held on every run this sitting. "Is AAPL
too concentrated?" took its third failed prediction on the shrink and is
the subject of the next entry.


### 2.3 does not route to ComplianceAgent, two failed predictions, stopped - RESOLVED 8 September (seventh sitting)

Recorded 8 September (sixth sitting). "What would have to change for me to
be within the limits again?" was predicted to plan ComplianceAgent twice:
on the roster line (bb52a01) and on the compliance intent (b0807f5), whose
INTENT TYPES entry names "what would have to change to be within its
limits" in so many words. It stayed BLOCKED both times - the router does
not read that wording as a policy question; no word in it names the
policy. Stopped after the second miss. The runner's blocked reason now
prints the intent and plan the router did produce (d79bd0f), so the next
sitting starts from what it routes to, not from a guess. Its next
prediction rides on a structural change - the dependency validator, or a
diagnostic query naming the limits without the policy - never on a
rewording of the intent line.

**The sentence above about the cause was wrong.** The dependency validator
(d4c102d) did not move 2.3 and could not have: the runner showed its first
attempt was `clarification_needed` with an empty plan, which validates.
The runner then learned to print what the router asked back (60f4b62), and
one `--case 2.3` run showed it: "Are you asking whether your current
portfolio complies with your Investment Policy Statement, or are you
proposing a specific position weight and want to know if it would be
allowed?" The router names the policy unprompted and offers two compliance
readings. The intent was never the problem after the second edit; the mode
was. Rule 7 gives compliance exactly one of three shapes, the message states
no weight, and the router asked about a weight rather than choose the
portfolio check. Neither failed prediction had addressed the mode.

**Third prompt edit, a3bad06, aimed at that cause and declared the last.**
One sentence in rule 7: the hypothetical shape needs a weight stated in the
message; with none, a question about complying, limits or what must change
is the portfolio check, not a clarification. No benchmark wording quoted.
Prediction: fifteen golden lines hold, no `retries`; 2.3 PASS, 11/12. Held:
golden clean twice, runner 11/12, and 2.3 PASS again on a second `--case`
run. Two of two is all the record has; 2.3's routing is pinned nowhere,
since no golden line carries it. A golden line for 2.3 is a benchmark
prompt in the golden set, as 3.2 and the four Level 1 prompts already are,
and moves `expected.txt` by one query - the owner's decision, alongside the
"How much has AAPL gained?" diagnostic still pending. If 2.3 ever flips
back to the clarification, the next step is conversation memory, not a
fourth edit.

**The last prompt rule of its kind.** `docs/DIRECTION.md` (df1bcef, written
the same day, after a3bad06) says: do not add prompt rules to fix a routing
defect; move the defect into extraction or derivation, or log it. The rule 7
sentence predates the document, held its prediction on every loop, and is
not reverted. It is recorded here as the last prompt rule added to fix a
routing defect. The two defects of that shape found since - JNJ dropped from
`tickers`, "last month" repaired to `1Y` - go to extraction, not to the
prompt.

### The prompt shrink moved two lines: the plan text was doing the mode's work

Recorded 8 September (eighth sitting). The shrink (9364d24) predicted all fifteen golden lines hold.
Two moved, identically on both runs, and the runner fell to 10/12: "Is AAPL
too concentrated?" and runner 2.1 both came back as `[ComplianceAgent]`
alone, the lookup, answering "The investment policy contains nothing on is
aapl too concentrated?". One CLI session read the model's own output: it
set `policy_topic` on both. Rule 7's plan brackets had been holding the flag
in place - the model chose the three-agent bracket for a portfolio question
and the flag followed the plan - and with the brackets gone the flag was the
only lever, pulled on any sentence naming the policy. "Too concentrated"
was on its third failed prediction; stopped, no wording. Fixed forward, not
reverted: the lookup became extraction's (55dd80c, a saying verb after
"policy", "IPS" or "investment policy statement", or "anything in my
policy about"), whose miss is the fuller check rather than "nothing on
this"; then the topic left the prompt as dead text (4d69e47). Lesson for
the record: prose that names a plan can classify by proxy, and a shrink
that removes it is a hypothesis about every line the proxy touched, not
only the lines that mention it.

### "Optimization failed: None": the node formats an absent error key

Recorded 8 September (eighth sitting), from the CLI. "Backtest SPY and TLT over 5 years" with no
portfolio ran the derived plan `[DataAgent, OptimizationAgent,
BacktestAgent]`; the optimiser returned `success: False` with no `error`
key, the node raised `Optimization failed: None`, and the backtest raised
correctly on missing weights. Two things: the optimiser's failure on a
two-asset five-year set is undiagnosed (the pinned golden line optimises
three assets with no period and succeeds), and the node's message hides
its cause. Before the derived plan the prompt's example planned the
backtest without the optimiser and the run raised on missing weights every
time, so this is a failure made visible, not a regression. Not chased.

### No window return exists, so "last month" and "today" clarify

Recorded 8 September (eighth sitting). "How has my portfolio done over the last month?" and "How
much did AAPL gain today?" are now honest clarifications naming the five
spans, because the only return the system computes is P&L since purchase
and the only windows it knows are year multiples for volatility. A return
over a stated span is a capability, a measure with a reference in
expected_values.md, not an extraction rule; the clarification is what the
system can say until it exists. The change-verb list that reads "today" as
a span is in `extraction.py`; its miss is the since-purchase answer.

### `measure` set by the model under intent compliance is unread

Recorded 8 September (eighth sitting). On "Is my JNJ position over any limit?" the model set
`measure: allocation, group_by: position` under `compliance`; the terminal
table discriminates compliance rows on the mode only and the compliance
formatter reads neither field. Harmless, and a sign the measure rule's
"ONLY for a question about an existing portfolio's own figures" reads a
compliance question as one. Logged for the `filter` decision, where a
selection axis for the compliance report would give the field a reader.

**9 September (ninth sitting).** Still unread. The reader the compliance
report gained is `status`, not `measure`; a `measure` set under
compliance stays a sign of the rule's wording and nothing else.

### No pytest reached the analysis node's allocation call - RESOLVED 8 September (eighth sitting)

Found when `allocation_by_sector` gained a parameter (4b003be): the suite
stayed green with the node's call site broken, since nothing ran the node.
`tests/test_analysis_node.py` (60c0df0) runs it on a synthetic state and
holds the published block to Part 7; it is the instrument that then caught
each later change to the block.


### The extraction bridge reads symbols, not company names

Recorded 9 September (between sittings), from conversation with the owner.
`agents/extraction.py` recognises a holding by its symbol only: an all-caps
token that is held or known. "How is my Apple Inc. position doing?" extracts
no ticker; the model classifies position P&L; an empty ticker list means
every position; the answer is the P&L table for all nine holdings under a
header that never names Apple. Under a compliance phrasing ("Is my Apple
Inc. position too big?") it is the full policy report. Before the restructure
Haiku sometimes put AAPL into `tickers` from the name and sometimes not; now
the miss is deterministic, and its direction is the bad one.

The fix that was brought and rejected: match the message against the names
of the held positions, from `Asset.name`, which
`PortfolioManager.get_holdings` already projects and `build_holdings_summary`
drops on purpose because nothing reads it. The owner's objection: "what if
there is a completely new stock? do I have to add every combination of
names?" - a name list is a bridge that grows with every holding, and under
`docs/DIRECTION.md` resolving a name is the reader model's job while the tool
validates the ticker. Logged, not built. If it is ever wanted before the
reader changes, the projection exists and the rule is a closed vocabulary
from the owner's own rows, not a world list; the risk to name then is a
holding whose first word is an English word.

**Seen in the 9 September session.** "How is my Apple Inc. position
doing?" -> `data_fetch`, `position_pnl`, `tickers: []`, the P&L block for
all nine positions, AAPL first only because the block is in the model's
order. Owner's decision the same day (handoff §5 item 13): not resolved by
extraction; item 16 is the path that would resolve it.

**9 September (ninth sitting).** Decision 16 logged with its trigger, not
taken; entry under Directions.


### The four phrase rules in extraction read English

Recorded 9 September (between sittings). Intent in German works: the
prompt's few-shots are German and the model reads it. Tickers, percentages
and the typo rule are language-free. Four rules read English phrasing and
nothing else: the span patterns (`_SPAN`, `_BARE_SPAN`, `_SINCE_YEAR`,
`_YTD`), the change-verb-with-"today" rule (`_DAY_MOVE`), the policy
saying-verb pattern (`_POLICY_SAYS`) and the reply confirmations
(`_CONFIRM`). "Wie lief mein Portfolio im letzten Monat?" sees no span and
answers P&L since purchase with a plausible face, which is the miss the
English span rule was written to prevent; "was sagt meine Policy zu Cash?"
runs the full portfolio check; "ja" happens to be in `_CONFIRM`, an accident
and not a policy. The owner uses German occasionally. Logged, not built: the
fix is the reader model that replaces the bridge, not German rows in four
patterns, which would double a bridge that is meant to be deleted in one
sitting. Until then a German span question is a known wrong face.

**Seen in the 9 September session.** "Wie ist meine Allokation nach
Anlageklasse?" answered correctly (intent and measure are the model's, in
German). "Wie lief mein Portfolio im letzten Monat?" -> `position_pnl`,
no period, the since-purchase block for all nine positions: the wrong face
the English span rule prevents, in German.

**9 September (ninth sitting).** Same: decision 16 logged, entry under
Directions.


### The lookup sentence quotes the whole question

Recorded 9 September, from the CLI session. Since f099101 the topic the
compliance node receives is the user's whole message, and the lookup
formatter's sentence was written for a phrase: "The investment policy
contains nothing on what does my investment policy say about currency
risk?." The answer is right and the runner's 3.4 still passes on "contains
nothing on"; the sentence reads badly. A formatter wording, no arithmetic:
say the policy contains nothing on this and name what was asked on its own
line, or nothing at all. Logged, not chased.

### One-figure questions get the whole block

Recorded 9 September, from the CLI session. "How much is my portfolio
worth?" is `measure: allocation` with no `group_by`, so the answer is the
total on its third line and then all three allocation views, 31 lines, and
the "Not done" line says the question named no breakdown. "What did I pay
for my JPM shares?" is `position_pnl` for JPM: the cost basis is in the
block's second line, and the CLI's identical-answer check fired because
the block is the same one the P&L question got. Both answers carry the
figure asked for; neither is shaped like the question. The `measure`
vocabulary has no `total` and no `cost`; a total is published inside the
allocation block and a cost inside each position, so either would be a
rendering of an existing figure, not a computation, and belongs with the
selection-axis decision rather than as new measures. Logged.

**9 September (ninth sitting).** The principle is decided with the
selection axis: a total and a cost are selections on the allocation and
P&L renderings, read from a parameter, never new measures. Not built
until a case asks.

### CLI session, 9 September: twenty-seven prompts

Run after the eighth sitting's sweep, against portfolio 3, with the nine
recorded CLI prompts, three typo pairs, three name-and-language prompts,
four compliance phrasings in plain words, three span-and-figure prompts and
two scope prompts. Nineteen answered the question asked, among them every
case the sitting built: the sector share of total, the position table, the
"last month" clarification with no model call, "APPL"/"yes" and
"MSTF"/"no, JNJ" resolved, a new question after a clarification routed as
new, "three years" as a 3Y window, German intent, two refusals. The eight
that did not, each in its entry: the full report for a named position and
for "which positions are over the limit" (the selection axis, above); the
lookup miss "What are my policy's rules on cash?" (pinned as the honest
miss under the derived lookup); the ETF refused as an issuer (pending
decision 7); "Apple Inc." and the German span (the two bridge entries); the
lookup sentence quoting the question; the whole block for one-figure
questions. Every answer carried its as-of date. No golden or runner run was
needed: nothing under `src/` changed.


### `load_portfolio_context` has no asserting test

Recorded 9 September (ninth sitting), when the five unguarded files were
deleted. The only exercise of `load_portfolio_context` outside
`test_portfolio_integration.py`, whose functions return booleans, was
`test_nodes_simple.py`, a module body that hit the database at
collection. The right instrument is a pytest with a stubbed portfolio
manager, the way `test_router_plans.py` stubs it. Not built.

**10 September (tenth sitting).** Still not built with a stub; it is
exercised live by `test_strict_nodes.py` over the database copy, through
`record_transaction` since be14e4b.

### `max_conversation_history` is read by nothing

Recorded 9 September (ninth sitting), seen while deleting
`conversation_history` from the router path (1320913). `AgentConfig`
(`agents/config.py`) carries it with a default of 10; no reader. Same
family as `log_tool_calls`. Logged, not chased.

### The `transactions` table has no portfolio - RESOLVED 10 September (tenth sitting)

Recorded 9 September (ninth sitting), for Order 2's first item. The
models carry a `Transaction` with asset, date, type, quantity, price and
fees, no portfolio and no currency, and no caller anywhere - the shape
that makes `Dividend` unattributable (expected_values.md Part 6).
expected_values.md Part 8 pins the ledger before it is built: decisions
D10 to D14 (average cost, fees in basis, what a sale does, holdings
derived from rows, a row belongs to a portfolio and its amount is data),
portfolio 3 as nine buys that must reproduce Part 1 to the cent, and one
synthetic position built in two tranches and partly sold, exact to the
cent. The workbook's `Ledger` sheet carries the same as formulas (64a9bec),
not recalculated here. The code is next: a test over Part 8 that fails
before the ledger exists, then the migration, then the derivation.

**Built 10 September (tenth sitting), in the handoff's order, each step
a test first.** `tests/test_ledger.py` over Part 8 A and B (9f629a9, the
module imported in a fixture so a missing module is 29 errors and not an
interrupted suite); the migration adding `portfolio_id` and `amount`, both
NOT NULL in batch mode (ace01ff; applied by hand); `quant/ledger.py`,
pure, `derive_holdings(rows)`
(ab66cc3) - cost basis sums `amount` and never recomputes quantity x price
+/- fees, so a second currency enters as data, and Part 8 A and B cannot
tell the two apart, which Part 8 C now can; a closed position is not a
holding; one fixture error on the way (7cbf799: selling exactly what is
held closes the position and is not an error). Then the reader: the seed
writes one buy row per position (a46a522, and refuses a rerun without
`--reset`, which would double every position); `get_holdings` derives from
the rows and `get_portfolio_tickers` is its tickers, `add_holding` and
its inline weighted average became `record_transaction` with every field
required (be14e4b). Runner 12/12 after, as predicted. Then the holdings
table dropped (4a3506f, migration 45b959c05420), D13 in the schema and not
only in the reader.

**A bug the reader exposed, fixed in be14e4b.** `delete_portfolio` deleted
the holdings and the portfolio and not the ledger rows; SQLite does not
enforce ON DELETE CASCADE unless foreign keys are switched on, and it
reuses a deleted portfolio's id, so an orphaned ledger became the next
portfolio's holdings in `test_strict_nodes.py`. Pinned by
`test_delete_portfolio_removes_its_ledger`. Anything else that deletes a
portfolio row by hand has the same hole.

### Two run-by-hand scripts call the deleted `add_holding` - RESOLVED 10 September (eleventh session)

Recorded 10 September (tenth sitting), from the grep before be14e4b.
`tests/check_portfolio_manager.py` and `tests/system_diagnostic.py` are
not collected by pytest (no `test_` prefix) and call
`pm.add_holding(...)`, which became `record_transaction` with a date and an
amount. Both are broken as scripts. Either they record buys with dates, or
they go; each its own decision after the grep. Logged, not chased.

**Resolved 10 September (eleventh session), by deletion (20973e8,
ae1bbb8).** The 26-line round trip is `test_holdings_from_ledger.py`'s
delete and tickers tests; the six diagnostics are `test_strict_nodes.py`'s
six, one for one. Not rewritten: a hand-run copy of a check the suite runs
drifts again the next time the manager changes, which is how both broke.

### `ensure_asset_exists_helper` has no caller - RESOLVED 10 September (eleventh session)

Recorded 10 September (tenth sitting). Its callers were
`add_holding_with_auto_fetch` and `get_or_create_demo_portfolio`, both
deleted in be14e4b. Deletion is safe; own commit after the grep.

**Resolved 10 September (eleventh session), 282a25d.** Deleted after the
grep found the definition and nothing else. It was also broken as
written: it constructed `DataManager()` without the session and provider
the constructor takes. The module docstring's usage example still shows
that call; its own entry under Hygiene.

### A leaked asset row with no ticker - RESOLVED 10 September (eleventh session)

Recorded 10 September (tenth sitting), seen while listing the assets'
currencies. `assets` id 10 has no ticker, no name, no currency and no
type. Nothing holds it and no ledger row names it. Delete by hand, the
owner's, when convenient; the seed does not touch it.

**Resolved 10 September (eleventh session).** Nine child tables counted
zero rows against id 10; I deleted it by hand with one statement. The ids
run 1 to 14 without it.

### `Transaction.date` defaults to now, and `fees` to zero - RESOLVED 10 September (eleventh session)

Recorded 10 September (tenth sitting), seen with the migration. The model
gives `date` a DateTime with a `utcnow` default and `fees` a default of
0.0. Both are repair-shaped: a row written without a date gets today, a
row written without a fee gets a free trade, each with a plausible face.
`record_transaction` requires both, so the live writer cannot trip them;
the seed passes both. Dropping the defaults (and `date` becoming a Date)
is a model-and-migration change, own decision. The reader converts the
stored timestamp to a date.

**Resolved 10 September (eleventh session), two migrations, schema tests
first.** `date` is a Date with no default (76005d0, 552ab8900332):
`record_transaction` takes a date and refuses a datetime, the reader and
the seed test stop converting. `fees` is NOT NULL with no default
(6d04179, 88d7b7afdce7). The nine stored timestamps were rewritten to
their day by the migration, so no reseed; how that had to be done is
under "The migration and the reseed are run by hand".

### The workbook was written while Excel held it open

Recorded 10 September (tenth sitting), a process failure, not one of the
code. Before writing the `Ledger` sheet's section C, `lsof` reported Excel
still holding `expected_values.xlsx`, and the script wrote anyway. No harm
followed: Excel was closed without saving and the write survived. The
rule: check with `lsof` before any openpyxl write, and if the workbook is
open, close it first, every time. openpyxl writes formulas without cached
values, so a sheet written that way is recalculated by Excel on opening.

### The migration and the reseed are run by hand

Recorded 10 September (tenth sitting). `alembic upgrade head` and
`seed_portfolio.py --reset` are run from the shell by hand, never from a
script or a test: the first changes the schema of `data/portfolio.db`, the
second rewrites portfolio 3 and the nine assets' metadata. A migration is
therefore committed unexecuted, and the schema tests written before it
(`test_transactions_schema.py`, `test_no_holdings_table.py`) are what
show it did what it says once it has run.

**10 September (eleventh session): four migrations, one command, and two
lessons.** The four (fx_rates, fx_fetch_metadata, date, fees) were each
committed unexecuted with their schema test, and each was applied and
reverted on a scratch copy of the database first, through the alembic
API with the database URL set before any import; the real file stayed
untouched until I ran the upgrade. The one `alembic upgrade head` that
applied them ran hours after the first migration landed: two earlier
attempts of mine left no trace on the file, and the cause was never seen
because I reported "done" and not what the command printed. The output
is the record, not the word. The second lesson: alembic's
batch rebuild copies a column whose type changes through `CAST`, and
SQLite's `CAST(... AS DATE)` has numeric affinity, so `2024-01-15` came
out as the number 2024 on the scratch copy. A type change on a populated
SQLite column is add-fill-drop-rename, never `alter_column` with a
`type_`; migration 552ab8900332 says so and does it that way.

The suite copies the database, so while a migration is pending every
test that reads the affected table fails through the suite and passes on
the scratch copy. This session that was 55 tests at the peak, and the
scratch run was the only instrument that could see the code was right.

**10 September (twelfth session): one migration, one refetch, both by
hand, both pasted.** Migration 2ee0c9249a9f (`daily_prices.source`) was
committed unexecuted with its schema test, applied and reverted on a
scratch copy through the alembic API with the database URL set before any
import, and then run by the owner; the pasted output showed the one
`Running upgrade` line and the schema read back NOT NULL. The refetch was
a second by-hand step of the same class: a delete of the nine holdings'
price rows and their fetch records, then one CLI question. The first CLI
run happened before the delete and fetched nothing, which the output
showed at once (no provider line, 204 ms) - the cache doing its job, and
the reason the order matters. My predicted row count after the delete was
8,760; the file said 9,140, the four leftover tickers added up by hand.
Seven tests were red through the suite between the model commit and the
owner's upgrade; the migrated scratch copy ran the whole suite green
meanwhile, run with `--noconftest` and the database URL in the
environment.

### `Portfolio.currency` defaults to USD - RESOLVED 10 September (twelfth session)

Recorded 10 September (eleventh session), seen while the base currency
became the analysis node's input. `Portfolio.currency` is NOT NULL with a
default of `"USD"` on the model and `create_portfolio` defaults its
argument the same way, so a portfolio created without a currency is a
dollar portfolio with a plausible face: the fee default's shape, on the
column every figure is now reported in (D15). Nothing trips it today;
every caller names a currency or is portfolio 3. Dropping both defaults
is a model-and-migration change plus a signature change, own decision.
Logged, not chased.

**Resolved 10 September (twelfth session), ba73fa1 and ee9659d.** No
migration: the database column was NOT NULL with no server default all
along, and the dollars came from the model's Python-side default and the
manager's argument default. Both gone; `create_portfolio(name, *,
currency, description=None)`; the eight test call sites that omitted it
name USD. The test saw three of four red, not the two I predicted: a row
committed through the model without a currency also passed, because the
model filled the USD in before the database saw it.

### `price_fetch_interval_days` is not in config.toml - RESOLVED 10 September (twelfth session)

Recorded 10 September (eleventh session), seen while the rate fetch took
the price fetch's cache rules. `config.toml`'s `[data_fetch]` carries the
earnings, profile and shares intervals and not the price one;
`DataManager` reads it with a code default of 1, and so does
`update_fx_rates`. The value that runs is the default, which is policy in
code. Adding the key to the file and dropping the default is one change;
logged, not chased.

**Resolved 10 September (twelfth session), 4fe83cb and a12e4ed.** The
key is in `config.toml` beside the three intervals; both readers index it
and a missing key raises; the table of intervals that ran when the file
was missing is gone, and a missing file raises naming the path. Three
tests, three red first.

### Cost basis is recomputed in the allocation layer - RESOLVED 10 September (twelfth session)

Recorded 10 September (eleventh session), seen while the rate entered
`_market_values`. `allocation._cost_bases` computes quantity x
`average_price`, and `build_holdings_summary` drops the ledger's own
`cost_basis` and `realized` on the way to `shared_data`, so the figure
the allocation and P&L blocks carry is a recomputation of the ledger's
figure, not the figure. They agree to the cent on every reference,
including Part 8 C's 18,405.00, because the average is the basis divided
by the quantity; they would differ only by rounding. Still a second
arithmetic path for a figure the ledger already states, the shape this
file keeps removing. The fix is the summary carrying `cost_basis` and the
layer reading it; a formatter change follows, since the P&L prints the
average. Own decision; logged, not chased.

**Resolved 10 September (twelfth session), 7365f6a and 244645d.** The
summary carries `cost_basis`, the ledger's figure; `_cost_bases` reads it
and multiplies nothing; a holding without it raises on the key. The
falsifier is a contract test, not a reference one: a holding stating a
basis that is not quantity times average (10 at 5.00, basis 60.00) reaches
all three views and the P&L as 60.00. Part 8 B cannot tell (250 x 80.01 is
exactly 20,002.50). Thirty hand-built holdings in six test files gained
the key at the product of their own figures, so no reference moved; the
P&L formatter prints the same words. `realized` is still not carried
(pending item 18). One lesson from the edit itself: a regex pass over two
fixture files inserted the key twice and truncated the averages, and the
suite stayed green because Python accepted both; I read the lines and
repaired them in place. A check that passes on a mangled fixture is the
false-pass shape applied to my own edit.

### `test_shrinkage.py` is collected and calls a signature that no longer exists - RESOLVED 10 September (twelfth session)

Recorded 10 September (eleventh session), seen while looking for a stub
provider pattern. `tests/test_shrinkage.py` has a `test_` name and one
`test_` function, so pytest collects it; the function builds a live
provider and calls `update_prices_for_asset(ticker, days=756)`, a
signature that has not existed for weeks, inside a `try` that prints the
error and continues, then reads prices from the database and prints a
comparison. It passes on every run and checks nothing. The unguarded-file
shape from the ninth session, one file later: a script with a test's
name. Delete or rewrite as an assertion; own decision.

**Resolved 10 September (twelfth session), by deletion (5849c7d).**
Nothing referenced it; the covariance estimator has its asserting test in
`test_portfolio_volatility.py`. Not rewritten: the question it asked has
no reference to assert against.

### `portfolio_manager.py`'s usage example cannot run - RESOLVED 10 September (twelfth session)

Recorded 10 September (eleventh session), seen while deleting the helper
below it. The module docstring's usage shows `DataManager()` with no
arguments; the constructor takes a session and a provider, and
`get_data_manager()` is the way in. The docstring also carries the
check-mark and cross emoji I strip as I go. Both a docstring edit; logged.

**Resolved 10 September (twelfth session), 7a3c054.** The example goes
through `get_data_manager()`, imports what it uses, and the two lists are
plain dashes. Docstring only.

### Two more `source` columns default to `yfinance`

Recorded 10 September (twelfth session), seen while adding
`daily_prices.source`. `FinancialStatement.source` (NOT NULL, default
`yfinance`) and `MacroData.source` (nullable, default `yfinance`) in
`database_setup.py` carry the default the price and rate tables now
refuse: a row written without a source is stamped with the one provider
the system has ever had. Neither table is on the benchmark's path; both
are the repair shape. Dropping the defaults is a model change each, with a
migration only if the database carries a server default (it did not for
`portfolios.currency`; check before assuming). Logged, not chased.

### Four leftover tickers hold adjusted rows that nothing reads

Recorded 10 September (twelfth session). AMZN (6,549 rows), PLTR (1,328),
SAP (513) and VWO (750) are assets from the deleted portfolios 1 and 2;
no ledger row names them, and their price rows were fetched under the old
default, so most are dividend-adjusted and none carries a convention the
table now claims (`source` says `yfinance` on them too). They were left
out of the refetch on purpose: nothing reads them and a refetch is nine
provider calls per question already. Delete the four assets and their
rows by hand when convenient, the owner's, the way the leaked row 10 went;
the price fetch test creates and removes its own asset and does not touch
them.

### The answer text does not name the price source

Recorded 10 September (twelfth session). A close now carries its source
on the row, and the as-of line in every answer says the date and not the
provider. Part 3b asks for the data age and for the source of a policy
claim, not for the source of a price, so no case is failing; a "priced as
of 2026-09-02, yfinance" line is a rendering decision with the runner as
the loop that sees the text. Logged, not built.

### The CLI reads `exit` as a question

Recorded 10 September (twelfth session), from the owner's run. The quit
command is `:q`; `exit` went to the router, which refused it as an order
to sell, one model call. Harmless and easy to hit. A word in the banner or
a second alias is a CLI change; logged.

### pytest warning inventory

Recorded 7 September (third sitting), from a green run of 132. Twenty
warnings, four kinds: two Pydantic class-based `Config` declarations in
`schemas.py` (`AgentTask`, `RouterDecision`), deprecated for V3; sixteen
SQLAlchemy `Query.get()` legacy calls from `data_manager.py:57`; and two
`PytestReturnNotNoneWarning` from `test_portfolio_integration.py`, which is
the "does not assert" entry above showing up in pytest's own output. None
blocks anything; the Pydantic one has a removal date.

**9 September (ninth sitting).** Twenty-three: `AgentTask`'s Pydantic
warning went with the class; the SQLAlchemy `.get()` count was twenty on
this day's runs, not sixteen - it moves with what the price cache does
during the run, so the inventory's number is a floor.

**10 September (tenth sitting).** Twenty-one: the two
`PytestReturnNotNoneWarning` went with `test_portfolio_integration.py`.
And the suite runs in about three seconds, not fourteen: the fourteen were
uncached provider calls and the deleted file's two model calls, measured
by running the suite at HEAD with the reader change set aside.

**10 September (eleventh session).** Twenty-three at 572 tests, in about
four seconds: two more SQLAlchemy `.get()` warnings from the one live
`data_agent_node` run in `test_data_agent_currency.py`, the same floor
that moves with the price cache.

**10 September (twelfth session).** Twenty-six at 606 tests, in about
three seconds: three more SQLAlchemy `.get()` warnings from the price
fetch test's own fetches over the database copy, the same floor.

### `.gitignore` is corrupted

A PowerShell here-string was written into it literally. Line 1 is `@"`, there is a
`` *`$py.class `` line with a PowerShell escape, and mid-file sits
`"@ | Out-File -FilePath .gitignore -Encoding UTF8data/portfolio.db`. The DB is
still ignored by later standalone entries, so nothing is leaking.

**Not actionable in a session, 8 September (sixth sitting):** the standing rules
now say `.gitignore` is the owner's to edit. "Rewrite it" stands as a
description of what the file needs and is the owner's to do.

### `portfolio_tool/__init__.py` opens a database connection at import

Line 43 imports `database_setup`, which prints a German DEBUG line and constructs
an engine as an import side effect; line 52 imports `data_manager`, which needs
`tomli`. So no module under `portfolio_tool` can be imported without sqlalchemy,
pandas and tomli loading first, regardless of what that module itself needs.

Confirmed by execution 4 September: importing `quant/allocation.py`, which is
pure arithmetic over dicts and imports only `dataclasses` and `typing`, failed on
a missing `sqlalchemy`.

### `Allocation.total_value` means two different things - RESOLVED 8 September (eighth sitting)

In `allocation_by_asset_class` it is invested plus cash. In
`allocation_by_sector` it is sectored value, cash and unsectored excluded.
Nothing downstream is wrong today - `portfolio_analysis_agent_node` maps the
sector one to `sectored_value` in the published JSON - but the dataclass field
carries two meanings depending on which constructor produced it.

Same family as the fields that read as live and are not: the name says one thing
at one call site and another at the other, and only the mapping in the node
keeps it honest.

**Resolved 8 September (eighth sitting), 4b003be.** `total_value` is the D2 total in every view,
`cash_balance` is real in the sector view, and the sector view's own
denominator is `sectored_value`, None elsewhere. What the fix left is a
duplicate in the other direction: on the two views whose denominator is the
total, `pct_of_denominator` equals `pct_of_total`, two names for one figure
on each asset-class and position line. The checker reads `pct_of_total`
only. The rename to named denominators (`pct_of_sectored`, no
`pct_of_denominator`) is its own later decision; it touches the runner, two
fixtures and the formatter.

**Renamed 9 September (ninth sitting), 0c9f833.** `pct_of_denominator` is
gone; `pct_of_sectored` is the sector view's, None on the unsectored line
and in the other views; `pct_of_total` is the checker's field on every
line. The block's `denominator` label stays as the formatter's header;
dropping it is its own decision. Runner 12/12 after, 1.1's own check
having moved to the new name.

**The label dropped 10 September (tenth sitting), 3edf370.** No
`denominator` key in the block and no `denominator_label` on the
dataclass; the three headers name each denominator by the share field's
own word and give the amount from the block ("% of total portfolio value
410,200.50", "% of sectored value 208,197.50"). D2 and D3 left the answer
text; they are the reference's, not the reader's. Pending decision 14
closed.


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

### Does the router stay a classifier, or become a tool-caller? - ANSWERED by docs/DIRECTION.md, 8 September

**Answered, 8 September (seventh sitting, after the merge), by
`docs/DIRECTION.md` (df1bcef).** In the end state the router does not
exist: a strong model chooses tools by function calling, the tools validate
their own inputs, and each tool's internal graph is derived from a
dependency table. The router is scaffolding until then, and work on it
counts only when it moves toward the tool boundary: deterministic
extraction before any LLM, plans derived from intent and the extracted
parameters through a terminal-agent table closed by `REQUIRES`, and the
prompt shrunk to the one decision an LLM should make. What survives from
the reasoning below is the second point - the tool shape is being chosen
now, and a parameterised quant layer is what the tools will call. The
"nothing stable to diff" worry is answered by the invariants: every number
traces to a tool output, and the pipelines under the tools stay fixed and
pinned.

The entry as it stood before the answer:

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

**Built to the answer, 8 September (eighth sitting), Order 1 of DIRECTION.md.** The model now decides
intent, `measure`, `group_by`, confidence and a clarification question, and
nothing it emits beyond those is read: tickers, periods, percentages and the
compliance mode are extraction's (56caa2c, f099101, 55dd80c, 9c9be90), the
plan is the terminal table's closed by `REQUIRES` (0d60f18, bc2b555), the
vocabularies are registries (8c35dee, `TERMINAL`), and the prompt shrank
from 1574 to 1063 words (9364d24, 4d69e47). Memory is an extraction rule
(5fca3bd). What the tool boundary still lacks: `measure` and `group_by` are
the model's, and a defined window is not an input.

**9 September (ninth sitting).** The prompt is 1120 words with the
`status` rule line (b4aada5); `status` joins `measure` and `group_by` as
the model's.

### Decision 16: a stronger reader producing a typed request - LOGGED 9 September

Brought as a decision (handoff §5 item 16) and logged, not taken. The
shape: the model reads the sentence and emits every typed field -
tickers, period, the percentages, the compliance mode - and
`extraction.py` only validates them against the vocabularies, asking on
what fails; names, German and typos become the model's reading. What it
does to the golden set: seven of sixteen lines go from deterministic to
model-dependent - the two `1Y` lines, the "gain today" clarification, the
three compliance plans, the two clarifications - and validation catches
a wrong ticker but not a missed one, which is the bad-direction miss the
bridge entry above records, made nondeterministic. Cost per call,
measured with the token counter on the full prompt: Haiku 4.5 about
2,280 input tokens and $0.003; Sonnet 5 about 3,150 and $0.008; Opus 5
about 3,150 and $0.021; a golden run is 5, 13 or 34 cents. The prompt
would grow back, since the ticker, period and mode rules the shrink
removed would return. If taken it is Order 5's shape built early on the
router's schema, a dated change to DIRECTION.md's Order and its "a bigger
model is debt" sentence, and the reader built twice. Trigger: Order 5, or
earlier if a benchmark case needs a name, German or a typo read rather
than asked about. Rejected alongside: flipping `use_stronger_model` on
the current prompt (a no-op today, the Sonnet config carrying the Haiku
id); a hybrid with extraction first and the model on a miss (two readers,
two failure directions, the answer depending on phrasing).


### The personal IPS: bound to the portfolio, grown one clause at a time

**Built 10 September (thirteenth session), the binding; the personal
document and the real portfolio are mine and come later.** DIRECTION.md
Order 2, item 4. Decided before any code, in this order of questions.

**Where the file lives so that it never enters the repository and the
code still finds it: on the portfolio's row.** The policy belongs to the
portfolio, not to the process. My real portfolio will be a second row in
the same untracked database beside portfolio 3, and the benchmark is
scored against docs/IPS.md: case 3.4 passes because that policy has no
clause on currency, so a personal policy with one must never be the
policy portfolio 3 is checked against. `portfolios.ips_path`, required,
defaulted nowhere, like `currency` (adec72f, 76e3da6, migration
7b1c4e2d9a05, applied by me from the shell and the output pasted: one
upgrade line, the column NOT NULL, row 3 reading `ips.toml`). The
migration fills row 3 by id and no other row, so a portfolio it does not
know is refused by the NOT NULL step rather than handed the committed
policy. `create_portfolio` requires the path and the seed writes
`ips.toml` (f64cb30). A relative path is anchored to the project root
the way the database URL is (f3e7a2a), so the committed file is found
from any directory; a personal one is absolute and outside the tree.
The loader takes the path it is given and has no default (ba18e86): a
call naming none has forgotten which portfolio it is about.

Rejected: an environment variable in `.env` naming the file (a switch is
per process while a policy is per portfolio; with it set the runner
would check portfolio 3 against my policy and 3.4 would fail, and which
policy ran would be invisible in the data); a fixed path under my home
tried first with the committed file as fallback (a default with a
plausible face); an ignored file inside the working tree (a `.gitignore`
edit, or an exclude entry a clone does not have); a mapping in
`config.toml` (a committed file carrying a path on my machine).

**Who resolves the path: the compliance node, from the row, in every
mode (9ba662e).** My first shape had DataAgent publish it to
`shared_data` beside `base_currency` (c18054c), and that was wrong on
inspection of the plan table: the hypothetical and lookup modes plan
ComplianceAgent alone, so in 3.1 and 3.4 DataAgent never runs and the
path would have been absent exactly when a policy question is asked
without a check of the portfolio. Taken back out (352104c). The node
now reads `ips_path` from the portfolio the state names through
`load_portfolio_policy_path`, separate from `load_portfolio_context`
because a policy question needs no holdings and an empty portfolio still
has a policy. No portfolio is no policy: a refusal, never the committed
file. The node's "reads only shared_data" rule narrowed to what it was
protecting, no second arithmetic path; its tests name portfolio 3 on the
suite's copy and are no longer database-free. Rejected: DataAgent in
every compliance plan (prices fetched for a policy question, two golden
plan lines move); the row in the two thin modes and shared_data in the
full one (two sources, the second a fallback); the committed policy when
no portfolio is set; resolving the row at the graph entry into the state
(a new seam for one value, maybe right when the router goes).

**What the system says when a clause has a type the checker does not
know: the whole file refuses to load, as before, now saying what to do
(90fd67c).** The message names the clause, the type, the known types,
and the growth rule: a rule the checker cannot check yet is written as a
`statement` until its checker and its reference exist. A half-loaded
policy is the repair shape; a refusal is honest, and the cost, that my
file cannot load until every unknown type is downgraded to a statement,
is the point. Rejected: a loaded clause with status `unchecked` (a
clause nobody validates, a vocabulary value with no consumer).

**How the vocabulary grows: one clause, one decision, in this order.**
The personal document is written in docs/IPS.md's shape, numbered
clauses with ids, and its TOML derived. Every clause whose type exists
loads and is checked; every rule the checker cannot check yet is a
`statement`, cited by id and listed by every full check as a statement
outside the check, so the policy is visibly incomplete rather than
silently so. When a clause is to become checkable: a Part 7-style
reference for that one clause on my real portfolio, computed by hand in
the private directory; then the type in the loader's vocabulary with its
parameters; then the checker's arm with the test over that reference;
then the TOML entry's type flips from statement to the new type. The
loader's docstring carries the same order.

**Where the Part 8 reference for my real portfolio lives: the same
private directory, outside the repository.** The document, the derived
TOML, a hand-computed expected-values file for my rows and rates, and
the statements the figures come from. Nothing in the suite reads it, so
a fresh clone stays green. What the repository will hold is the check,
not the data: when the portfolio enters, a committed script that derives
holdings from a portfolio's ledger rows and compares them to a
hand-typed reference file at a path I give it, run by hand, the same
shape as pending item 24. Not built until the portfolio enters, last.

**Seen in the CLI on portfolio 3 after the binding.** The compliance
agent's line names the policy it loaded, the resolved absolute path of
the committed file; the lookup plans ComplianceAgent alone and answers
"contains nothing"; the full check plans all three agents and reports
seven breaches against Part 7's eight, the cents pair on the other side
of its limit at today's closes, as Part 7 says it will. Golden set and
runner not run: no routing, no prompt and no answer text changed.

**What remains of item 4, all mine, in order.** The private directory
and the personal document in it; its TOML, loaded once by hand to see
that every type is known or a statement; the real portfolio's ledger
rows from my statements and the Part 8 reference for them, hand-computed
first; then the row, with its absolute path, and the check script. My
real portfolio's data stays out of the repository and enters last.

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

### Volatility over as-traded closes or over a total-return series?

**Deferred, with the reference on the as-traded side. Recorded 10
September (twelfth session).** D19 fixed the stored close as the exchange's
print, and Part 4's 252 closes are prints, so the 10.2936% is a volatility
of as-traded closes: an ex-dividend drop counts as a negative daily return
(about 0.5% on JNJ each quarter, about 0.3% on TLT each month). Before
this session the live figure ran on the library's dividend-adjusted series
and the reference did not, which is one of the reasons the two never met
and nobody could say by how much. Now they run on the same series. Whether
the covariance *should* see dividends as returns is a D5-to-D8 question:
if it should not, the series is built from `close` and the dividends
table, deterministic and referenceable, never cached from a provider whose
adjusted figure changes with each later dividend. Decide with a recomputed
Part 4 beside the present one, not by flipping the provider flag back.

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
