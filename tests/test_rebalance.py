"""
Test Script for Rebalancing Tools and Agent.

Tests:
1. Pure math functions (rebalance_tools.py)
2. RebalanceAgent integration
3. Edge cases and error handling

Run:
    python test_rebalance.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_drift_calculation():
    """Test basic drift calculation."""
    print("\n" + "=" * 60)
    print("TEST 1: Drift Calculation")
    print("=" * 60)
    
    from portfolio_tool.tools.rebalance_tools import (
        calculate_drift,
        calculate_max_drift,
        should_rebalance
    )
    
    # Test case: Portfolio has drifted
    current = {"SPY": 0.65, "TLT": 0.25, "GLD": 0.10}
    target = {"SPY": 0.60, "TLT": 0.30, "GLD": 0.10}
    
    drift = calculate_drift(current, target)
    max_drift = calculate_max_drift(drift)
    should_reb, recommendation = should_rebalance(drift, threshold_percent=5.0)
    
    print(f"\nCurrent Weights: {current}")
    print(f"Target Weights:  {target}")
    print(f"\nDrift by Asset:")
    for ticker, d in drift.items():
        status = "OVER" if d > 0 else "UNDER" if d < 0 else "OK"
        print(f"   {ticker}: {d:+.2%} ({status})")
    
    print(f"\nMax Drift: {max_drift:.2%}")
    print(f"Should Rebalance: {should_reb}")
    print(f"Recommendation: {recommendation}")
    
    # Assertions
    assert abs(drift["SPY"] - 0.05) < 0.001, "SPY drift should be +5%"
    assert abs(drift["TLT"] - (-0.05)) < 0.001, "TLT drift should be -5%"
    assert abs(drift["GLD"]) < 0.001, "GLD drift should be 0%"
    assert should_reb == True, "Should rebalance at 5% drift"
    
    print("\n✅ Drift calculation test PASSED")


def test_trade_generation():
    """Test trade list generation."""
    print("\n" + "=" * 60)
    print("TEST 2: Trade Generation")
    print("=" * 60)
    
    from portfolio_tool.tools.rebalance_tools import generate_trades, RebalanceConfig
    
    current = {"SPY": 0.65, "TLT": 0.25, "GLD": 0.10}
    target = {"SPY": 0.60, "TLT": 0.30, "GLD": 0.10}
    portfolio_value = 100000
    prices = {"SPY": 450.0, "TLT": 95.0, "GLD": 180.0}
    
    config = RebalanceConfig(
        min_drift_for_partial=2.0,
        transaction_cost_bps=10.0,
    )
    
    trades = generate_trades(
        current_weights=current,
        target_weights=target,
        portfolio_value=portfolio_value,
        prices=prices,
        config=config,
    )
    
    print(f"\nPortfolio Value: €{portfolio_value:,}")
    print(f"Prices: {prices}")
    print(f"\nGenerated Trades:")
    
    total_value = 0
    for trade in trades:
        print(f"   {trade.action} {trade.shares:.2f} {trade.ticker} "
              f"@ €{trade.estimated_price:.2f} = €{abs(trade.trade_value):,.2f}")
        print(f"      Transaction Cost: €{trade.transaction_cost:.2f}")
        total_value += abs(trade.trade_value)
    
    print(f"\nTotal Trade Value: €{total_value:,.2f}")
    
    # Assertions
    assert len(trades) >= 1, "Should generate at least 1 trade"
    
    # Check SPY is sold (overweight)
    spy_trade = next((t for t in trades if t.ticker == "SPY"), None)
    if spy_trade:
        assert spy_trade.action == "SELL", "SPY should be sold (overweight)"
    
    # Check TLT is bought (underweight)
    tlt_trade = next((t for t in trades if t.ticker == "TLT"), None)
    if tlt_trade:
        assert tlt_trade.action == "BUY", "TLT should be bought (underweight)"
    
    print("\n✅ Trade generation test PASSED")


def test_full_analysis():
    """Test complete rebalancing analysis."""
    print("\n" + "=" * 60)
    print("TEST 3: Full Rebalancing Analysis")
    print("=" * 60)
    
    from portfolio_tool.tools.rebalance_tools import analyze_rebalance, RebalanceConfig
    
    current = {"SPY": 0.65, "TLT": 0.25, "GLD": 0.10}
    target = {"SPY": 0.60, "TLT": 0.30, "GLD": 0.10}
    portfolio_value = 100000
    prices = {"SPY": 450.0, "TLT": 95.0, "GLD": 180.0}
    
    result = analyze_rebalance(
        current_weights=current,
        target_weights=target,
        portfolio_value=portfolio_value,
        prices=prices,
    )
    
    print(result.to_summary())
    
    # Assertions
    assert result.should_rebalance == True, "Should recommend rebalancing"
    assert result.max_drift >= 0.05, "Max drift should be >= 5%"
    assert len(result.trades) >= 1, "Should have trades"
    assert result.total_transaction_cost > 0, "Should have transaction costs"
    
    print("\n✅ Full analysis test PASSED")


def test_no_rebalance_needed():
    """Test case where no rebalancing is needed."""
    print("\n" + "=" * 60)
    print("TEST 4: No Rebalance Needed")
    print("=" * 60)
    
    from portfolio_tool.tools.rebalance_tools import analyze_rebalance
    
    # Minimal drift - within threshold
    current = {"SPY": 0.61, "TLT": 0.29, "GLD": 0.10}
    target = {"SPY": 0.60, "TLT": 0.30, "GLD": 0.10}
    portfolio_value = 100000
    prices = {"SPY": 450.0, "TLT": 95.0, "GLD": 180.0}
    
    result = analyze_rebalance(
        current_weights=current,
        target_weights=target,
        portfolio_value=portfolio_value,
        prices=prices,
    )
    
    print(f"\nMax Drift: {result.max_drift:.2%}")
    print(f"Should Rebalance: {result.should_rebalance}")
    print(f"Recommendation: {result.recommendation}")
    
    assert result.should_rebalance == False, "Should NOT recommend rebalancing"
    assert result.recommendation in ["no_action", "monitor_closely", "below_break_even"]
    
    print("\n✅ No rebalance test PASSED")


def test_cost_benefit():
    """Test cost-benefit analysis."""
    print("\n" + "=" * 60)
    print("TEST 5: Cost-Benefit Analysis")
    print("=" * 60)
    
    from portfolio_tool.tools.rebalance_tools import (
        analyze_rebalance,
        RebalanceConfig,
        calculate_break_even_drift
    )
    
    # High transaction costs scenario
    config = RebalanceConfig(
        transaction_cost_bps=50.0,  # 0.5% - very high
        drift_threshold_percent=5.0,
    )
    
    current = {"SPY": 0.65, "TLT": 0.25, "GLD": 0.10}
    target = {"SPY": 0.60, "TLT": 0.30, "GLD": 0.10}
    portfolio_value = 100000
    prices = {"SPY": 450.0, "TLT": 95.0, "GLD": 180.0}
    
    result = analyze_rebalance(
        current_weights=current,
        target_weights=target,
        portfolio_value=portfolio_value,
        prices=prices,
        config=config,
    )
    
    print(f"\nTransaction Cost Rate: {config.transaction_cost_bps} bps")
    print(f"Total Transaction Costs: €{result.total_transaction_cost:,.2f}")
    print(f"Cost as % of Portfolio: {result.cost_as_percent:.3%}")
    print(f"Break-Even Drift: {result.break_even_drift:.2%}")
    
    # With high costs, break-even should be higher
    break_even = calculate_break_even_drift(portfolio_value, config.transaction_cost_bps)
    print(f"Calculated Break-Even: {break_even:.2%}")
    
    assert result.total_transaction_cost > 0
    assert result.break_even_drift > 0
    
    print("\n✅ Cost-benefit test PASSED")


def test_rebalance_agent():
    """Test RebalanceAgent integration."""
    print("\n" + "=" * 60)
    print("TEST 6: RebalanceAgent Integration")
    print("=" * 60)
    
    try:
        from agents.rebalance_agent import create_rebalance_agent
        
        agent = create_rebalance_agent(verbose=True)
        
        print(f"\nAgent: {agent.name}")
        print(f"Tools: {[t.__name__ for t in agent.get_tools()]}")
        
        # Test drift check
        result = agent.calculate_drift_tool(
            current_weights={"SPY": 0.65, "TLT": 0.25, "GLD": 0.10},
            target_weights={"SPY": 0.60, "TLT": 0.30, "GLD": 0.10}
        )
        
        print(f"\nDrift Check Result:")
        print(f"   Success: {result['success']}")
        print(f"   Max Drift: {result['max_drift_formatted']}")
        print(f"   Should Rebalance: {result['should_rebalance']}")
        
        assert result["success"] == True
        
        # Test full analysis
        full_result = agent.analyze_rebalance_tool(
            current_weights={"SPY": 0.65, "TLT": 0.25, "GLD": 0.10},
            target_weights={"SPY": 0.60, "TLT": 0.30, "GLD": 0.10},
            portfolio_value=100000,
            prices={"SPY": 450, "TLT": 95, "GLD": 180}
        )
        
        print(f"\nFull Analysis:")
        print(f"   Success: {full_result['success']}")
        print(f"   Recommendation: {full_result['decision']['recommendation']}")
        print(f"   Num Trades: {full_result['trade_summary']['num_trades']}")
        
        assert full_result["success"] == True
        
        print("\n✅ RebalanceAgent test PASSED")
        
    except ImportError as e:
        print(f"\n⚠️ RebalanceAgent not installed yet: {e}")
        print("   (This is expected if you haven't copied the files)")


def test_determinism():
    """Test that calculations are deterministic (same input = same output)."""
    print("\n" + "=" * 60)
    print("TEST 7: Determinism Check")
    print("=" * 60)
    
    from portfolio_tool.tools.rebalance_tools import analyze_rebalance
    
    current = {"SPY": 0.65, "TLT": 0.25, "GLD": 0.10}
    target = {"SPY": 0.60, "TLT": 0.30, "GLD": 0.10}
    portfolio_value = 100000
    prices = {"SPY": 450.0, "TLT": 95.0, "GLD": 180.0}
    
    # Run same calculation 5 times
    results = []
    for i in range(5):
        result = analyze_rebalance(
            current_weights=current,
            target_weights=target,
            portfolio_value=portfolio_value,
            prices=prices,
        )
        results.append(result)
    
    # All results should be identical
    first = results[0]
    for i, result in enumerate(results[1:], 2):
        assert result.max_drift == first.max_drift, f"Run {i} max_drift differs"
        assert result.should_rebalance == first.should_rebalance, f"Run {i} decision differs"
        assert len(result.trades) == len(first.trades), f"Run {i} trade count differs"
        assert result.total_transaction_cost == first.total_transaction_cost, f"Run {i} cost differs"
    
    print(f"\n✓ Ran calculation 5 times")
    print(f"✓ All results identical")
    print(f"✓ Max Drift: {first.max_drift:.4f}")
    print(f"✓ Transaction Cost: €{first.total_transaction_cost:.2f}")
    
    print("\n✅ Determinism test PASSED - Calculations are reproducible!")


def run_all_tests():
    """Run all rebalancing tests."""
    print("\n" + "=" * 60)
    print("REBALANCING MODULE TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_drift_calculation,
        test_trade_generation,
        test_full_analysis,
        test_no_rebalance_needed,
        test_cost_benefit,
        test_rebalance_agent,
        test_determinism,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
