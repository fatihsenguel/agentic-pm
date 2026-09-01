# Known gaps (not bugs — unbuilt features)

## Rebalance has no target allocation source
"Should I rebalance my portfolio?" fails with:
  "No target weights from OptimizationAgent."

RebalanceAgent needs a target to measure drift against. The router currently
plans [DataAgent, RebalanceAgent] and there is no target.

DO NOT fix by inserting OptimizationAgent into the chain. Re-optimising on every
drift check means the target moves with the covariance matrix, which is not how
strategic asset allocation works. Drift must be measured against a fixed target.

Correct fix: targets belong to the portfolio / IPS. See ips_manager.py on
wip/phase7-snapshot. Resolve when Phase 7 is pulled forward.

## RiskManagerAgent is not wired
src/agents/risk_manager_agent.py exists but has no graph node, no routing entry,
and no mention in router_prompts.py. Risk queries route to DataAgent and stop.

## No position-level performance
"How has SPY performed since I bought it?" fetches prices and stops. Nothing
compares current price against average_price to produce P&L.

## No holdings-metadata queries
"Allocation by asset class" and "positions in sector X" have data (Asset carries
asset_class, sector, industry, country) but no agent reads holdings as positions
rather than as a ticker list.

## tests/test_portfolio_integration.py does not actually assert
Written as a standalone script: every test function returns True/False and a
main() tallies them. pytest ignores return values, so all its tests pass
unconditionally regardless of outcome. 18 return statements, several marked
"Skip, not fail" / "Don't fail on expected exceptions".

Fixing means rewriting the file with real assertions, not a mechanical
return -> assert swap. Expect genuine failures to surface once it does.

Same pattern was fixed in test_all_configs.py::test_no_self_config_references
(now asserts, and anchors paths to the repo root so it works from any cwd).

## RAG parked on wip/rag-early
The early RAG attempt (chunker, document_loader, embeddings, fed_scraper,
sentiment) was removed from baseline-v1 and parked on branch wip/rag-early.
It could not run: the [rag] extra is uninstalled and this commit has no
vector_store.py. A fuller version exists on master (b327e80) — prefer that one.

RAG is NOT needed for the IPS work. A self-authored IPS is structured data
(targets, limits, allowed instruments) checked deterministically. RAG becomes
relevant for equity research: 10-K filings, earnings transcripts, CEO commentary.

## CORRECTION: rag/ was restored, parking was wrong
The parking note above was based on a wrong assumption. None of the five modules
in src/portfolio_tool/rag/ need heavy dependencies:
  fed_scraper.py    -> requests, bs4        (installed)
  document_loader.py-> stdlib only
  chunker.py        -> stdlib + document_loader
  sentiment.py      -> stdlib + document_loader, chunker
  embeddings.py     -> numpy                (installed)
Nothing imports sentence_transformers, torch or chromadb. Those belong to the
LATER RAG work on master (b327e80), not to this code.

MacroAgent and macro_tools have six LAZY imports of these modules (inside
functions, so removing them broke nothing at import time and tests stayed green):
  macro_agent.py:171,179,771,821
  macro_tools.py:456,515
Deleting rag/ silently killed fetch_fed_minutes and list_available_fed_minutes.
Caught only because VS Code flagged unresolved imports.

OPEN DECISION (do not act without deciding):
- Is the Fed-minutes capability wanted at all? It is a macro signal; the stated
  priority is IPS-driven portfolio management first, equity research second.
- Is this hand-rolled stack (own chunker + own cosine similarity) the right
  foundation, or should it be replaced by a real vector store? master's later
  RAG version has vector_store.py + chromadb.
- Is sentiment.py reusable for 10-K / earnings-call work, or would that be
  built differently?
- NONE OF IT IS VERIFIED. fetch_fed_minutes has not been run since January and
  scrapes live Fed HTML with January-era selectors. Test before judging.

The golden set has NO macro-document coverage, which is why this was invisible.
Add a Fed-minutes query once the decision is made.
