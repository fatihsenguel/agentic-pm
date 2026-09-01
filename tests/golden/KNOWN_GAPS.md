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
