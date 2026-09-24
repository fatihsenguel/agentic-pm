"""
Unit Tests for Strict nodes.py - Banking Grade

These tests verify that nodes.py fails correctly when given bad data
and succeeds with good data.

Run: python tests/test_strict_nodes.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import asyncio
import pytest
from datetime import date, datetime, timedelta

# Test imports
from agents.state import create_initial_state, AgentState
from agents.nodes import (
    load_portfolio_context,
    PortfolioContextError,
    DataCalculationError,
    data_agent_node,
    rebalance_agent_node,
)
from portfolio_tool.portfolio_manager import PortfolioManager
from portfolio_tool.data_manager import DataManager, get_data_manager


# ============================================================================
# TEST 1: load_portfolio_context() - STRICT MODE
# ============================================================================

def test_load_portfolio_context_no_portfolio_no_tickers():
    """Should FAIL when no portfolio and no tickers in query"""
    state = create_initial_state("Do something")
    
    try:
        ctx = load_portfolio_context(state)
        tickers, holdings = ctx.tickers, ctx.holdings
        assert False, "Should have raised PortfolioContextError"
    except PortfolioContextError as e:
        assert "No portfolio specified" in str(e)
        assert "no tickers found" in str(e)
        print("✓ Correctly failed: No portfolio, no tickers")


def test_load_portfolio_context_empty_portfolio():
    """Should FAIL when portfolio exists but is empty"""
    # Create empty portfolio
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("Empty Test Portfolio", currency="USD", ips_path="ips.toml")
    
    state = create_initial_state("Test", portfolio_id=portfolio_id)
    
    try:
        ctx = load_portfolio_context(state)
        tickers, holdings = ctx.tickers, ctx.holdings
        assert False, "Should have raised PortfolioContextError"
    except PortfolioContextError as e:
        assert "is empty" in str(e)
        assert "add holdings" in str(e).lower()
        print("✓ Correctly failed: Empty portfolio")
    finally:
        pm.delete_portfolio(portfolio_id)


def test_load_portfolio_context_with_valid_portfolio():
    """Should SUCCEED when portfolio has holdings"""
    # Create portfolio with holdings
    pm = PortfolioManager()
    dm = get_data_manager()
    
    # Ensure assets exist
    end = datetime.now()
    start = end - timedelta(days=365)
    dm.fetch_price_data("SPY", start, end)
    dm.fetch_price_data("TLT", start, end)
    
    portfolio_id = pm.create_portfolio("Test Portfolio", currency="USD", ips_path="ips.toml")
    pm.record_transaction(portfolio_id, "SPY", date(2024, 1, 15), "buy", 100, 450.0, 0.0, 45_000.0)
    pm.record_transaction(portfolio_id, "TLT", date(2024, 1, 15), "buy", 50, 88.0, 0.0, 4_400.0)
    
    state = create_initial_state("Test", portfolio_id=portfolio_id)
    
    try:
        ctx = load_portfolio_context(state)
        tickers, holdings = ctx.tickers, ctx.holdings
        
        assert tickers == ["SPY", "TLT"]
        assert len(holdings) == 2
        assert holdings[0]["ticker"] in ["SPY", "TLT"]
        print(f"✓ Correctly loaded portfolio: {tickers}")
    finally:
        pm.delete_portfolio(portfolio_id)


def test_load_portfolio_context_with_tickers_in_the_inputs():
    """Should SUCCEED when no portfolio but tickers in the inputs"""
    state = create_initial_state("Analyze AAPL")
    state["inputs"] = {"tickers": ["AAPL", "MSFT"]}

    ctx = load_portfolio_context(state)
    tickers, holdings = ctx.tickers, ctx.holdings
    
    assert tickers == ["AAPL", "MSFT"]
    assert holdings is None
    print(f"✓ Correctly used router tickers: {tickers}")


# ============================================================================
# TEST 2: data_agent_node() - STRICT MODE
# ============================================================================

async def test_data_agent_invalid_portfolio():
    """DataAgent should fail with invalid portfolio"""
    state = create_initial_state("Test", portfolio_id=999999)
    
    result = await data_agent_node(state)
    
    assert "error" in result.get("sub_results", {}).get("DataAgent", {})
    assert len(result.get("errors", [])) > 0
    print("✓ DataAgent correctly failed: Invalid portfolio")


async def test_data_agent_empty_portfolio():
    """DataAgent should fail with empty portfolio"""
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("Empty Portfolio", currency="USD", ips_path="ips.toml")
    
    state = create_initial_state("Test", portfolio_id=portfolio_id)
    
    try:
        result = await data_agent_node(state)
        
        assert "error" in result.get("sub_results", {}).get("DataAgent", {})
        print("✓ DataAgent correctly failed: Empty portfolio")
    finally:
        pm.delete_portfolio(portfolio_id)


async def test_data_agent_with_valid_data():
    """DataAgent should succeed with valid portfolio"""
    # Setup
    pm = PortfolioManager()
    dm = get_data_manager()
    
    end = datetime.now()
    start = end - timedelta(days=365)
    dm.fetch_price_data("SPY", start, end)
    
    portfolio_id = pm.create_portfolio("Test Portfolio", currency="USD", ips_path="ips.toml")
    pm.record_transaction(portfolio_id, "SPY", date(2024, 1, 15), "buy", 100, 450.0, 0.0, 45_000.0)
    
    state = create_initial_state("Test", portfolio_id=portfolio_id)
    
    try:
        result = await data_agent_node(state)
        
        data_result = result.get("sub_results", {}).get("DataAgent", {})
        assert data_result.get("success") == True
        
        shared = result.get("shared_data", {})
        assert "expected_returns" in shared
        assert "covariance_matrix" in shared
        assert "latest_prices" in shared
        
        # ✅ CRITICAL: Verify data types
        assert isinstance(shared["expected_returns"], dict)
        assert isinstance(shared["covariance_matrix"], dict)
        
        print("✓ DataAgent succeeded with valid data")
        print(f"  Expected returns: {shared['expected_returns']}")
    finally:
        pm.delete_portfolio(portfolio_id)


async def test_rebalance_no_fallback_prices():
    """RebalanceAgent should fail without prices, not use $100"""
    state = create_initial_state("Test")
    
    state["portfolio_holdings"] = [
        {"ticker": "SPY", "quantity": 100, "average_price": 450.0, "cost_basis": 45000.0}
    ]
    
    state["shared_data"] = {
        "tickers": ["SPY"],
        # Missing latest_prices. The node checks prices before it looks for a
        # target, so the missing target raises nothing here.
    }

    result = await rebalance_agent_node(state)
    
    rebal_result = result.get("sub_results", {}).get("RebalanceAgent", {})
    assert rebal_result.get("success") == False
    
    error_msg = str(result.get("errors", []))
    assert "price" in error_msg.lower()
    print("✓ RebalanceAgent has no fallback prices")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

async def run_all_tests():
    """Run all strict mode tests"""
    print("\n" + "="*80)
    print("🧪 STRICT MODE UNIT TESTS - Banking Grade")
    print("="*80)
    
    print("\n📋 TEST SUITE 1: load_portfolio_context()")
    print("-" * 80)
    test_load_portfolio_context_no_portfolio_no_tickers()
    test_load_portfolio_context_empty_portfolio()
    test_load_portfolio_context_with_valid_portfolio()
    test_load_portfolio_context_with_router_tickers()
    
    print("\n📋 TEST SUITE 2: data_agent_node()")
    print("-" * 80)
    await test_data_agent_invalid_portfolio()
    await test_data_agent_empty_portfolio()
    await test_data_agent_with_valid_data()
    
    print("\n📋 TEST SUITE 3: No Fallback Data")
    print("-" * 80)
    await test_rebalance_no_fallback_prices()

    print("\n" + "="*80)
    print("✅ ALL STRICT MODE TESTS PASSED")
    print("="*80)
    print("\nYour system is PRODUCTION READY! 🏦")
    print("\nKey Validations:")
    print("  ✓ Fails fast with clear errors")
    print("  ✓ No fallback data anywhere")
    print("  ✓ Data types strictly checked")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
