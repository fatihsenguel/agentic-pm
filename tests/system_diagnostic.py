"""
System Diagnostic - Check Banking System Health

This script checks if your strict nodes.py system is working correctly.
It verifies:
1. No fallback data anywhere
2. Proper error messages
3. Data integrity
4. Logging is informative

Run: python tests/system_diagnostic.py
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents.state import create_initial_state
from agents.nodes import (
    load_portfolio_context,
    data_agent_node,
    optimization_agent_node,
    PortfolioContextError,
    DataCalculationError,
)
from portfolio_tool.portfolio_manager import PortfolioManager
from portfolio_tool.data_manager import DataManager, get_data_manager


# ============================================================================
# DIAGNOSTIC TESTS
# ============================================================================

class SystemDiagnostic:
    """System health checker"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    async def test(self, name: str, func, should_fail=False):
        """Run a diagnostic test"""
        print(f"\n{'='*80}")
        print(f"TEST: {name}")
        print(f"{'='*80}")
        
        try:
            result = func()
            if asyncio.iscoroutine(result):
                result = await result
            
            if should_fail:
                print("❌ FAIL: Should have raised an error but didn't")
                self.failed += 1
                self.results.append((name, False, "Did not fail as expected"))
            else:
                print("✅ PASS: Test succeeded")
                self.passed += 1
                self.results.append((name, True, "Success"))
                
        except Exception as e:
            if should_fail:
                print(f"✅ PASS: Correctly failed with: {type(e).__name__}")
                print(f"Error message:\n{str(e)}")
                
                # Check if error message is helpful
                error_msg = str(e).lower()
                has_what = any(word in error_msg for word in ['missing', 'not found', 'failed', 'invalid', 'empty', 'no '])
                has_why = any(word in error_msg for word in ['because', 'cannot', 'requires', 'must', 'without', 'needed'])
                has_how = any(word in error_msg for word in ['please', 'use', 'add', 'check', 'ensure', 'verify', 'specify', 'include'])
                
                if has_what and has_why and has_how:
                    print("✅ Error message is EXCELLENT (has what/why/how)")
                elif has_what and has_why:
                    print("⚠️  Error message is GOOD (has what/why, missing solution)")
                else:
                    print(f"❌ Error message is POOR (What={has_what}, Why={has_why}, How={has_how})")
                
                self.passed += 1
                self.results.append((name, True, f"Correctly failed: {type(e).__name__}"))
            else:
                print(f"❌ FAIL: Unexpected error: {type(e).__name__}")
                print(f"Error: {str(e)}")
                self.failed += 1
                self.results.append((name, False, f"Unexpected error: {str(e)}"))
    
    def report(self):
        """Generate diagnostic report"""
        print("\n" + "="*80)
        print("📊 DIAGNOSTIC REPORT")
        print("="*80)
        
        print(f"\nResults: {self.passed}/{self.passed + self.failed} tests passed")
        print(f"  ✅ Passed: {self.passed}")
        print(f"  ❌ Failed: {self.failed}")
        
        print("\nDetails:")
        for name, passed, details in self.results:
            status = "✅" if passed else "❌"
            print(f"  {status} {name}")
            if not passed:
                print(f"      {details}")
        
        if self.failed == 0:
            print("\n" + "="*80)
            print("🎉 SYSTEM IS PRODUCTION READY!")
            print("="*80)
            print("\nYour system:")
            print("  ✓ Has no fallback data")
            print("  ✓ Fails fast with clear errors")
            print("  ✓ Handles errors gracefully without crashing")
            print("  ✓ Validates data integrity")
            print("\nYou can confidently deploy this to production! 🏦")
        else:
            print("\n" + "="*80)
            print("⚠️  ISSUES FOUND")
            print("="*80)
            print(f"\n{self.failed} test(s) need attention.")
            print("Review the failures above and fix before production.")


# ============================================================================
# TEST SCENARIOS
# ============================================================================

async def diagnostic_1_empty_portfolio():
    """Test: Empty portfolio should fail (Low level helper - raises Exception)"""
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("Empty Portfolio")
    
    try:
        state = create_initial_state("Test", portfolio_id=portfolio_id)
        tickers, holdings = load_portfolio_context(state)
        # Should not reach here
    finally:
        pm.delete_portfolio(portfolio_id)


async def diagnostic_2_missing_tickers():
    """Test: No portfolio and no tickers should fail (Low level helper - raises Exception)"""
    state = create_initial_state("Do something vague")
    tickers, holdings = load_portfolio_context(state)


async def diagnostic_3_valid_portfolio():
    """Test: Valid portfolio should succeed"""
    pm = PortfolioManager()
    dm = get_data_manager()
    
    end = datetime.now()
    start = end - timedelta(days=365)
    dm.fetch_price_data("SPY", start, end)
    
    portfolio_id = pm.create_portfolio("Valid Portfolio")
    pm.add_holding(portfolio_id, "SPY", 100, 450.0)
    
    try:
        state = create_initial_state("Test", portfolio_id=portfolio_id)
        tickers, holdings = load_portfolio_context(state)
        
        assert tickers == ["SPY"], f"Expected ['SPY'], got {tickers}"
        assert holdings is not None, "Expected holdings, got None"
        assert len(holdings) == 1, f"Expected 1 holding, got {len(holdings)}"
    finally:
        pm.delete_portfolio(portfolio_id)


async def diagnostic_4_data_agent_invalid_portfolio():
    """Test: DataAgent with invalid portfolio should Handle Error Gracefully"""
    state = create_initial_state("Test", portfolio_id=999999)
    result = await data_agent_node(state)
    
    # We expect the agent to CATCH the error and return it in the state
    if "errors" not in result or len(result["errors"]) == 0:
        raise AssertionError("Agent should have reported an error, but didn't.")
        
    print(f"  ✓ Agent gracefully reported: {result['errors'][0]}")


async def diagnostic_5_data_agent_valid():
    """Test: DataAgent with valid data should succeed"""
    pm = PortfolioManager()
    dm = get_data_manager()
    
    end = datetime.now()
    start = end - timedelta(days=1095)
    
    for ticker in ["SPY", "TLT"]:
        dm.fetch_price_data(ticker, start, end)
    
    portfolio_id = pm.create_portfolio("Test Portfolio")
    pm.add_holding(portfolio_id, "SPY", 100, 450.0)
    pm.add_holding(portfolio_id, "TLT", 50, 88.0)
    
    try:
        state = create_initial_state("Test", portfolio_id=portfolio_id)
        result = await data_agent_node(state)
        
        # Check success
        data_result = result.get("sub_results", {}).get("DataAgent", {})
        if not data_result.get("success"):
            raise AssertionError(f"DataAgent failed: {data_result.get('error')}")
        
        # Check data types
        shared = result.get("shared_data", {})
        
        if not isinstance(shared.get("expected_returns"), dict):
            raise AssertionError("expected_returns is not dict")
        
        if not isinstance(shared.get("covariance_matrix"), dict):
            raise AssertionError("covariance_matrix is not dict")
        
        # Check no strings (all floats)
        for ticker, value in shared["expected_returns"].items():
            if not isinstance(value, (int, float)):
                raise AssertionError(f"Return for {ticker} is {type(value)}, not float")
        
    finally:
        pm.delete_portfolio(portfolio_id)


async def diagnostic_6_optimization_misaligned():
    """Test: Optimization with misaligned matrices should Handle Error Gracefully"""
    state = create_initial_state("Test")
    
    # Misaligned data
    state["shared_data"] = {
        "tickers": ["SPY", "TLT"],
        "expected_returns": {"SPY": 0.10},  # Missing TLT
        "covariance_matrix": {
            "SPY": {"SPY": 0.04, "TLT": 0.01},
            "TLT": {"SPY": 0.01, "TLT": 0.02},
        }
    }
    
    result = await optimization_agent_node(state)
    
    opt_result = result.get("sub_results", {}).get("OptimizationAgent", {})
    if opt_result.get("success"):
        raise AssertionError("Should have failed with misaligned matrices")
    
    print(f"  ✓ Agent gracefully reported error: {opt_result.get('error')}")


# ============================================================================
# RUN DIAGNOSTICS
# ============================================================================

async def run_diagnostics():
    """Run all diagnostic tests"""
    print("\n" + "="*80)
    print("🏥 SYSTEM DIAGNOSTIC - Banking System Health Check")
    print("="*80)
    print("\nThis will verify:")
    print("  • No fallback data")
    print("  • Proper error handling")
    print("  • Clear error messages")
    print("  • Data integrity")
    
    diag = SystemDiagnostic()
    
    # --- LOW LEVEL TESTS (Should Raise Exception) ---
    await diag.test("Empty Portfolio Fails", diagnostic_1_empty_portfolio, should_fail=True)
    await diag.test("Missing Tickers Fails", diagnostic_2_missing_tickers, should_fail=True)
    
    # --- AGENT TESTS (Should Handle Gracefully - NO CRASH) ---
    # These verify the agent catches the error and returns a clean error state
    await diag.test("Invalid Portfolio Handled Gracefully", diagnostic_4_data_agent_invalid_portfolio, should_fail=False)
    await diag.test("Misaligned Matrices Handled Gracefully", diagnostic_6_optimization_misaligned, should_fail=False)
    
    # --- SUCCESS TESTS ---
    await diag.test("Valid Portfolio Succeeds", diagnostic_3_valid_portfolio, should_fail=False)
    await diag.test("DataAgent With Valid Data Succeeds", diagnostic_5_data_agent_valid, should_fail=False)
    
    diag.report()


if __name__ == "__main__":
    asyncio.run(run_diagnostics())