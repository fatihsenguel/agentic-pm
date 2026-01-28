"""
🧪 PHASE 6.5 COMPREHENSIVE TEST SUITE
=====================================

Tests all agent capabilities systematically:
1. Portfolio Management (list, get holdings, create, etc.)
2. Data Management (list assets, get info, etc.)
3. Multi-Agent Workflows (optimization, macro, rebalancing)

Usage:
    python tests/test_phase65_full.py
    python tests/test_phase65_full.py --verbose
    python tests/test_phase65_full.py --test portfolio
    python tests/test_phase65_full.py --test optimization

Author: Agentic Finance Team
Version: Phase 6.5
"""

import sys
import os
import asyncio
import argparse
import json
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    details: Optional[Dict] = None


class TestRunner:
    """Runs tests and collects results."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
        
    def log(self, msg: str, level: str = "info"):
        """Log a message."""
        if level == "info":
            print(f"  {msg}")
        elif level == "success":
            print(f"  {GREEN}✓{RESET} {msg}")
        elif level == "error":
            print(f"  {RED}✗{RESET} {msg}")
        elif level == "warning":
            print(f"  {YELLOW}⚠{RESET} {msg}")
        elif level == "debug" and self.verbose:
            print(f"  {DIM}{msg}{RESET}")
    
    def add_result(self, result: TestResult):
        """Add a test result."""
        self.results.append(result)
        
    def print_summary(self):
        """Print test summary."""
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        print(f"\n{'='*60}")
        print(f"{BOLD}TEST SUMMARY{RESET}")
        print(f"{'='*60}")
        
        for r in self.results:
            icon = f"{GREEN}✓{RESET}" if r.passed else f"{RED}✗{RESET}"
            duration = f"{r.duration_ms:.0f}ms"
            print(f"  {icon} {r.name} ({duration})")
            if not r.passed and r.error:
                print(f"      {RED}Error: {r.error[:80]}{RESET}")
        
        print(f"\n{BOLD}Results: {passed}/{total} passed, {failed} failed{RESET}")
        
        if failed == 0:
            print(f"\n{GREEN}🎉 All tests passed!{RESET}")
        else:
            print(f"\n{RED}❌ Some tests failed. See details above.{RESET}")
        
        return failed == 0


# =============================================================================
# TEST HELPERS
# =============================================================================

async def run_graph(user_input: str, portfolio_id: Optional[int] = None) -> Dict[str, Any]:
    """Run the agent graph and return final state."""
    from agents.graph import get_graph
    from agents.state import create_initial_state
    
    state = create_initial_state(user_input, portfolio_id=portfolio_id)
    graph = get_graph()
    
    final_state = None
    async for event in graph.astream(state):
        for node_name, state_update in event.items():
            final_state = state_update
    
    return final_state


def check_response_success(state: Dict) -> Tuple[bool, str]:
    """Check if the response indicates success."""
    if not state:
        return False, "No state returned"
    
    final_response = state.get("final_response")
    if not final_response:
        return False, "No final_response in state"
    
    if isinstance(final_response, dict):
        if final_response.get("success") == False:
            error = final_response.get("error") or final_response.get("data", {}).get("error", "Unknown error")
            return False, str(error)
        return True, ""
    
    return True, ""


def get_response_data(state: Dict) -> Dict:
    """Extract response data from state."""
    final_response = state.get("final_response", {})
    if isinstance(final_response, dict):
        return final_response.get("data", {})
    return {}


# =============================================================================
# PORTFOLIO MANAGEMENT TESTS
# =============================================================================

async def test_list_portfolios(runner: TestRunner) -> TestResult:
    """Test listing all portfolios."""
    start = datetime.now()
    
    try:
        state = await run_graph("List all my portfolios")
        success, error = check_response_success(state)
        
        if success:
            data = get_response_data(state)
            count = data.get("count", 0)
            runner.log(f"Found {count} portfolios", "success")
            
            # Verify we got portfolio data
            if "portfolios" not in data and count > 0:
                return TestResult("list_portfolios", False, 
                    (datetime.now() - start).total_seconds() * 1000,
                    "Response missing 'portfolios' key")
        
        return TestResult(
            name="list_portfolios",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None,
            details={"count": get_response_data(state).get("count", 0)}
        )
    except Exception as e:
        return TestResult("list_portfolios", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


async def test_get_holdings_by_id(runner: TestRunner) -> TestResult:
    """Test getting holdings by portfolio ID."""
    start = datetime.now()
    
    try:
        state = await run_graph("Show holdings in portfolio 1")
        success, error = check_response_success(state)
        
        if success:
            data = get_response_data(state)
            holdings = data.get("holdings", [])
            runner.log(f"Found {len(holdings)} holdings in portfolio 1", "success")
        
        return TestResult(
            name="get_holdings_by_id",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None
        )
    except Exception as e:
        return TestResult("get_holdings_by_id", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


async def test_get_holdings_by_name(runner: TestRunner) -> TestResult:
    """Test getting holdings by portfolio name."""
    start = datetime.now()
    
    try:
        state = await run_graph("Show me Demo Portfolio")
        success, error = check_response_success(state)
        
        if success:
            data = get_response_data(state)
            runner.log(f"Found holdings by name", "success")
        
        return TestResult(
            name="get_holdings_by_name",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None
        )
    except Exception as e:
        return TestResult("get_holdings_by_name", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


async def test_get_portfolio_summary(runner: TestRunner) -> TestResult:
    """Test getting portfolio summary."""
    start = datetime.now()
    
    try:
        state = await run_graph("Get summary of portfolio 1")
        success, error = check_response_success(state)
        
        if success:
            runner.log(f"Got portfolio summary", "success")
        
        return TestResult(
            name="get_portfolio_summary",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None
        )
    except Exception as e:
        return TestResult("get_portfolio_summary", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


# =============================================================================
# DATA MANAGEMENT TESTS
# =============================================================================

async def test_list_assets(runner: TestRunner) -> TestResult:
    """Test listing all tracked assets."""
    start = datetime.now()
    
    try:
        state = await run_graph("Show me all assets in the database")
        success, error = check_response_success(state)
        
        if success:
            data = get_response_data(state)
            count = data.get("count", 0)
            runner.log(f"Found {count} tracked assets", "success")
            
            if count == 0:
                return TestResult("list_assets", False,
                    (datetime.now() - start).total_seconds() * 1000,
                    "Expected assets but found 0")
        
        return TestResult(
            name="list_assets",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None,
            details={"count": get_response_data(state).get("count", 0)}
        )
    except Exception as e:
        return TestResult("list_assets", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


async def test_get_asset_info(runner: TestRunner) -> TestResult:
    """Test getting info for a specific asset."""
    start = datetime.now()
    
    try:
        state = await run_graph("Get info on AAPL")
        success, error = check_response_success(state)
        
        if success:
            runner.log(f"Got AAPL info", "success")
        
        return TestResult(
            name="get_asset_info",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None
        )
    except Exception as e:
        return TestResult("get_asset_info", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


async def test_get_latest_price(runner: TestRunner) -> TestResult:
    """Test getting latest price for an asset."""
    start = datetime.now()
    
    try:
        state = await run_graph("What is the latest price for AAPL?")
        success, error = check_response_success(state)
        
        if success:
            runner.log(f"Got AAPL latest price", "success")
        
        return TestResult(
            name="get_latest_price",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None
        )
    except Exception as e:
        return TestResult("get_latest_price", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


# =============================================================================
# MULTI-AGENT WORKFLOW TESTS
# =============================================================================

async def test_optimization_with_tickers(runner: TestRunner) -> TestResult:
    """Test optimization with explicit tickers."""
    start = datetime.now()
    
    try:
        state = await run_graph("Optimize a portfolio with AAPL, MSFT, AMZN")
        success, error = check_response_success(state)
        
        # Check that DataAgent ran
        sub_results = state.get("sub_results", {})
        data_agent_ran = "DataAgent" in sub_results
        opt_agent_ran = "OptimizationAgent" in sub_results
        
        runner.log(f"DataAgent ran: {data_agent_ran}", "debug")
        runner.log(f"OptimizationAgent ran: {opt_agent_ran}", "debug")
        
        if data_agent_ran and opt_agent_ran:
            opt_result = sub_results.get("OptimizationAgent", {})
            if opt_result.get("success"):
                weights = opt_result.get("optimal_weights", {})
                runner.log(f"Optimization complete, {len(weights)} weights", "success")
            else:
                error = opt_result.get("error", "Unknown optimization error")
                success = False
        
        return TestResult(
            name="optimization_with_tickers",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None,
            details={"agents_ran": list(sub_results.keys())}
        )
    except Exception as e:
        return TestResult("optimization_with_tickers", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


async def test_optimization_with_portfolio(runner: TestRunner) -> TestResult:
    """Test optimization using portfolio ID."""
    start = datetime.now()
    
    try:
        state = await run_graph("Optimize portfolio 2")
        success, error = check_response_success(state)
        
        sub_results = state.get("sub_results", {})
        
        # Check DataAgent loaded portfolio
        data_result = sub_results.get("DataAgent", {})
        if not data_result.get("success"):
            error = data_result.get("error", "DataAgent failed")
            success = False
        
        if success:
            runner.log(f"Portfolio 2 optimization complete", "success")
        
        return TestResult(
            name="optimization_with_portfolio",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None
        )
    except Exception as e:
        return TestResult("optimization_with_portfolio", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


async def test_optimization_with_constraints(runner: TestRunner) -> TestResult:
    """Test optimization with volatility constraint."""
    start = datetime.now()
    
    try:
        state = await run_graph("Optimize AAPL, MSFT, GOOGL with max 15% volatility")
        success, error = check_response_success(state)
        
        if success:
            sub_results = state.get("sub_results", {})
            opt_result = sub_results.get("OptimizationAgent", {})
            if opt_result.get("success"):
                vol = opt_result.get("expected_volatility", 0)
                runner.log(f"Optimization complete, vol={vol:.2%}", "success")
                
                # Check constraint was respected
                if vol > 0.16:  # Allow small tolerance
                    runner.log(f"Warning: volatility {vol:.2%} exceeds 15% constraint", "warning")
        
        return TestResult(
            name="optimization_with_constraints",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None
        )
    except Exception as e:
        return TestResult("optimization_with_constraints", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


async def test_macro_analysis(runner: TestRunner) -> TestResult:
    """Test macro environment analysis."""
    start = datetime.now()
    
    try:
        state = await run_graph("How is the market looking?")
        success, error = check_response_success(state)
        
        sub_results = state.get("sub_results", {})
        macro_ran = "MacroAgent" in sub_results
        
        if macro_ran:
            macro_result = sub_results.get("MacroAgent", {})
            if macro_result.get("success"):
                runner.log(f"Macro analysis complete", "success")
            else:
                error = macro_result.get("error", "MacroAgent failed")
                success = False
        
        return TestResult(
            name="macro_analysis",
            passed=success,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            error=error if not success else None
        )
    except Exception as e:
        return TestResult("macro_analysis", False,
            (datetime.now() - start).total_seconds() * 1000, str(e))


# =============================================================================
# TOOL DIRECT TESTS (Bypass Router)
# =============================================================================

def test_tools_direct(runner: TestRunner) -> List[TestResult]:
    """Test tools directly without going through the graph."""
    results = []
    
    print(f"\n{CYAN}Testing Tools Directly (No Router){RESET}")
    print("-" * 40)
    
    # Test list_portfolios tool
    try:
        from portfolio_tool.tools.portfolio_tools import list_portfolios
        start = datetime.now()
        result = list_portfolios.func()
        duration = (datetime.now() - start).total_seconds() * 1000
        
        success = result.get("success", False)
        count = result.get("count", 0)
        runner.log(f"list_portfolios: {count} portfolios", "success" if success else "error")
        
        results.append(TestResult("tool_list_portfolios", success, duration,
            None if success else result.get("error")))
    except Exception as e:
        results.append(TestResult("tool_list_portfolios", False, 0, str(e)))
    
    # Test list_tracked_assets tool
    try:
        from portfolio_tool.tools.data_tools import list_tracked_assets
        start = datetime.now()
        result = list_tracked_assets.func()
        duration = (datetime.now() - start).total_seconds() * 1000
        
        success = result.get("success", False)
        count = result.get("count", 0)
        runner.log(f"list_tracked_assets: {count} assets", "success" if success else "error")
        
        results.append(TestResult("tool_list_tracked_assets", success, duration,
            None if success else result.get("error")))
    except Exception as e:
        results.append(TestResult("tool_list_tracked_assets", False, 0, str(e)))
    
    # Test get_portfolio_holdings tool
    try:
        from portfolio_tool.tools.portfolio_tools import get_portfolio_holdings
        start = datetime.now()
        result = get_portfolio_holdings.func(1)  # Portfolio ID 1
        duration = (datetime.now() - start).total_seconds() * 1000
        
        success = result.get("success", False)
        count = result.get("count", 0)
        runner.log(f"get_portfolio_holdings(1): {count} holdings", "success" if success else "error")
        
        results.append(TestResult("tool_get_portfolio_holdings", success, duration,
            None if success else result.get("error")))
    except Exception as e:
        results.append(TestResult("tool_get_portfolio_holdings", False, 0, str(e)))
    
    return results


# =============================================================================
# ROUTER TESTS
# =============================================================================

async def test_router_intent_detection(runner: TestRunner) -> List[TestResult]:
    """Test that router correctly detects intents."""
    results = []
    
    print(f"\n{CYAN}Testing Router Intent Detection{RESET}")
    print("-" * 40)
    
    from agents.smart_router import get_router
    router = get_router()
    
    test_cases = [
        ("Show me all my portfolios", "portfolio_management", "list_portfolios"),
        ("Show holdings in portfolio 1", "portfolio_management", "get_holdings"),
        ("List all assets in the database", "data_management", "list_assets"),
        ("Get info on AAPL", "data_management", "get_info"),
        ("Optimize AAPL, MSFT, GOOGL", "optimization", None),
        ("How is the market?", "macro_analysis", None),
    ]
    
    for query, expected_intent, expected_command in test_cases:
        start = datetime.now()
        try:
            decision, validation = await router.route(query)
            duration = (datetime.now() - start).total_seconds() * 1000
            
            actual_intent = decision.intent.value if hasattr(decision.intent, 'value') else decision.intent
            actual_command = decision.parameters.command
            
            intent_match = actual_intent == expected_intent
            command_match = expected_command is None or actual_command == expected_command
            
            passed = intent_match and command_match
            
            status = "success" if passed else "error"
            runner.log(f"'{query[:30]}...' → {actual_intent}/{actual_command}", status)
            
            results.append(TestResult(
                f"router_{expected_intent}_{expected_command or 'none'}",
                passed, duration,
                None if passed else f"Expected {expected_intent}/{expected_command}, got {actual_intent}/{actual_command}"
            ))
        except Exception as e:
            results.append(TestResult(f"router_{expected_intent}", False, 0, str(e)))
    
    return results


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

async def run_all_tests(verbose: bool = False, test_filter: Optional[str] = None):
    """Run all tests."""
    runner = TestRunner(verbose=verbose)
    
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  🧪 PHASE 6.5 COMPREHENSIVE TEST SUITE{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{DIM}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    
    # Tool Direct Tests (always run first - fastest)
    if not test_filter or test_filter == "tools":
        tool_results = test_tools_direct(runner)
        for r in tool_results:
            runner.add_result(r)
    
    # Router Tests
    if not test_filter or test_filter == "router":
        router_results = await test_router_intent_detection(runner)
        for r in router_results:
            runner.add_result(r)
    
    # Portfolio Management Tests
    if not test_filter or test_filter == "portfolio":
        print(f"\n{CYAN}Testing Portfolio Management{RESET}")
        print("-" * 40)
        
        runner.add_result(await test_list_portfolios(runner))
        runner.add_result(await test_get_holdings_by_id(runner))
        runner.add_result(await test_get_holdings_by_name(runner))
        runner.add_result(await test_get_portfolio_summary(runner))
    
    # Data Management Tests
    if not test_filter or test_filter == "data":
        print(f"\n{CYAN}Testing Data Management{RESET}")
        print("-" * 40)
        
        runner.add_result(await test_list_assets(runner))
        runner.add_result(await test_get_asset_info(runner))
        runner.add_result(await test_get_latest_price(runner))
    
    # Multi-Agent Workflow Tests
    if not test_filter or test_filter == "optimization":
        print(f"\n{CYAN}Testing Multi-Agent Workflows{RESET}")
        print("-" * 40)
        
        runner.add_result(await test_optimization_with_tickers(runner))
        runner.add_result(await test_optimization_with_portfolio(runner))
        runner.add_result(await test_optimization_with_constraints(runner))
    
    # Macro Tests
    if not test_filter or test_filter == "macro":
        print(f"\n{CYAN}Testing Macro Analysis{RESET}")
        print("-" * 40)
        
        runner.add_result(await test_macro_analysis(runner))
    
    # Print summary
    return runner.print_summary()


def main():
    parser = argparse.ArgumentParser(description="Phase 6.5 Test Suite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--test", "-t", type=str, help="Run specific test group: tools, router, portfolio, data, optimization, macro")
    args = parser.parse_args()
    
    try:
        success = asyncio.run(run_all_tests(
            verbose=args.verbose,
            test_filter=args.test
        ))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Fatal error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
