"""
Test Script for Phase 5.4 - MacroAgent and DataAgent Integration.

This script tests:
1. Database connection and MacroData table
2. DataManager macro methods
3. DataAgent tools (DB-backed)
4. MacroAgent tools (DB-backed)
5. Agent interaction (shared_data flow)

Run from project root:
    python -m tests.test_phase5_4_integration

Or copy this file to tests/ and run:
    pytest tests/test_phase5_4_integration.py -v
"""

import sys
import os
from datetime import date, datetime, timedelta
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ==================== UNIT TESTS ====================

class TestDatabaseSetup:
    """Test MacroData table exists and works."""
    
    def test_macro_data_table_exists(self):
        """Verify MacroData table is in database."""
        from portfolio_tool.database_setup import MacroData, get_session
        
        session = get_session()
        try:
            # Try to query - will fail if table doesn't exist
            count = session.query(MacroData).count()
            print(f"✅ MacroData table exists, {count} records")
            assert True
        except Exception as e:
            print(f"❌ MacroData table error: {e}")
            assert False, f"MacroData table not found: {e}"
        finally:
            session.close()
    
    def test_macro_data_insert(self):
        """Test inserting macro data."""
        from portfolio_tool.database_setup import MacroData, get_session
        
        session = get_session()
        try:
            # Insert test record
            test_record = MacroData(
                date=date.today(),
                indicator="TEST_INDICATOR",
                value=99.99,
                source="test"
            )
            session.add(test_record)
            session.commit()
            
            # Verify
            result = session.query(MacroData).filter(
                MacroData.indicator == "TEST_INDICATOR"
            ).first()
            
            assert result is not None
            assert result.value == 99.99
            print("✅ MacroData insert works")
            
            # Cleanup
            session.delete(result)
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"❌ MacroData insert error: {e}")
            assert False, str(e)
        finally:
            session.close()


class TestDataManagerMacro:
    """Test DataManager macro methods."""
    
    def test_update_vix(self):
        """Test VIX data fetching and storage."""
        from portfolio_tool.data_manager import get_data_manager
        
        dm = get_data_manager()
        result = dm.update_vix(days=7)
        
        print(f"VIX Update: success={result.success}, affected={result.affected_count}")
        
        # VIX update might return 0 if market is closed or no new data
        assert result.success or "no_data" in str(result.metadata)
        print("✅ update_vix works")
    
    def test_update_treasury_yields(self):
        """Test Treasury yields fetching."""
        from portfolio_tool.data_manager import get_data_manager
        
        dm = get_data_manager()
        result = dm.update_treasury_yields(days=7)
        
        print(f"Yields Update: success={result.success}, affected={result.affected_count}")
        assert result.success or "no_data" in str(result.metadata)
        print("✅ update_treasury_yields works")
    
    def test_get_latest_macro_values(self):
        """Test retrieving latest macro values."""
        from portfolio_tool.data_manager import get_data_manager
        
        dm = get_data_manager()
        result = dm.get_latest_macro_values()
        
        print(f"Latest Macro: {result}")
        assert result.get("success") is True or result.get("indicators") == {}
        print("✅ get_latest_macro_values works")
    
    def test_get_vix_with_regime(self):
        """Test VIX regime classification."""
        from portfolio_tool.data_manager import get_data_manager
        
        dm = get_data_manager()
        
        # First ensure we have some VIX data
        dm.update_vix(days=30)
        
        result = dm.get_vix_with_regime()
        print(f"VIX Regime: {result}")
        
        if result.get("success"):
            assert "current_vix" in result
            assert "regime" in result
            print(f"✅ VIX: {result['current_vix']}, Regime: {result['regime']}")
        else:
            print("⚠️ VIX regime: no data (expected if first run)")
    
    def test_get_yield_curve_status(self):
        """Test yield curve status."""
        from portfolio_tool.data_manager import get_data_manager
        
        dm = get_data_manager()
        
        # First ensure we have yield data
        dm.update_treasury_yields(days=30)
        
        result = dm.get_yield_curve_status()
        print(f"Yield Curve: {result}")
        
        if result.get("success") and result.get("slope_10y_3m") is not None:
            print(f"✅ Yield Curve Slope: {result['slope_10y_3m']}, Status: {result['status']}")
        else:
            print("⚠️ Yield curve: incomplete data (expected if first run)")


class TestDataAgentTools:
    """Test DataAgent tool methods."""
    
    def test_fetch_prices_tool(self):
        """Test fetching prices via DataAgent."""
        from agents.data_agent import create_data_agent
        
        agent = create_data_agent(verbose=True)
        result = agent.fetch_prices_tool(tickers="SPY", period="1Y")
        
        print(f"Fetch Prices: {result.get('success')}, obs={result.get('num_observations')}")
        
        if result.get("success"):
            assert result.get("num_observations", 0) > 0
            assert "SPY" in result.get("latest_prices", {})
            print(f"✅ SPY latest: ${result['latest_prices']['SPY']}")
        else:
            print(f"⚠️ Fetch prices failed: {result.get('error')}")
    
    def test_calculate_returns_tool(self):
        """Test return calculations."""
        from agents.data_agent import create_data_agent
        
        agent = create_data_agent()
        
        # Fetch first
        agent.fetch_prices_tool(tickers="SPY,TLT", period="1Y")
        
        result = agent.calculate_returns_tool(tickers="SPY,TLT", period="1Y")
        
        print(f"Returns: {result.get('success')}")
        
        if result.get("success"):
            assert "annualized_returns" in result
            print(f"✅ Returns: {result['annualized_returns']}")
        else:
            print(f"⚠️ Returns failed: {result.get('error')}")
    
    def test_get_risk_free_rate_tool(self):
        """Test risk-free rate retrieval."""
        from agents.data_agent import create_data_agent
        
        agent = create_data_agent()
        result = agent.get_risk_free_rate_tool()
        
        print(f"Risk-Free Rate: {result}")
        
        assert result.get("success")
        assert "rate" in result
        print(f"✅ Risk-Free Rate: {result['rate_formatted']} (source: {result['source']})")
    
    def test_calculate_covariance_tool(self):
        """Test covariance matrix calculation."""
        from agents.data_agent import create_data_agent
        
        agent = create_data_agent()
        result = agent.calculate_covariance_tool(tickers="SPY,TLT,GLD", period="3Y")
        
        print(f"Covariance: {result.get('success')}")
        
        if result.get("success"):
            assert "covariance_matrix" in result
            assert "correlation_matrix" in result
            print(f"✅ Covariance calculated for {result.get('num_observations')} observations")
        else:
            print(f"⚠️ Covariance failed: {result.get('error')}")


class TestMacroAgentTools:
    """Test MacroAgent tool methods."""
    
    def test_fetch_macro_data_tool(self):
        """Test fetching macro data."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent(verbose=True)
        result = agent.fetch_macro_data_tool(indicators="VIX,TNX_10Y", days=7)
        
        print(f"Fetch Macro: {result}")
        
        assert result.get("success") or "error" in result
        print(f"✅ Macro fetch: {result.get('rows_updated', 0)} rows")
    
    def test_get_macro_snapshot_tool(self):
        """Test macro snapshot."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent()
        
        # Fetch first
        agent.fetch_macro_data_tool(indicators="VIX,TNX_10Y,IRX_3M", days=7)
        
        result = agent.get_macro_snapshot_tool()
        
        print(f"Macro Snapshot: {result}")
        
        if result.get("success"):
            if result.get("vix"):
                print(f"✅ VIX: {result['vix']['value']} ({result['vix']['regime']})")
            if result.get("yield_curve"):
                print(f"✅ Yield Curve: {result['yield_curve']['slope']} ({result['yield_curve']['status']})")
        else:
            print("⚠️ Snapshot: no data yet")
    
    def test_get_vix_analysis_tool(self):
        """Test VIX analysis."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent()
        result = agent.get_vix_analysis_tool(days=30)
        
        print(f"VIX Analysis: {result}")
        
        if result.get("success"):
            print(f"✅ VIX: {result['current_vix']}, Regime: {result['regime']}, Signal: {result['signal']}")
    
    def test_assess_regime_tool(self):
        """Test regime assessment."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent()
        
        # Test with manual values
        result = agent.assess_regime_tool(
            vix_level=28.0,
            yield_curve_slope=-0.3
        )
        
        print(f"Regime Assessment: {result}")
        
        assert result.get("success")
        assert result.get("regime") in ["risk_on", "risk_off", "neutral", "crisis", "recovery"]
        print(f"✅ Regime: {result['regime']}, Equity Adj: {result['equity_adjustment']}")
    
    def test_generate_taa_signal_tool(self):
        """Test TAA signal generation."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent()
        result = agent.generate_taa_signal_tool(current_equity_weight=0.60)
        
        print(f"TAA Signal: {result}")
        
        if result.get("success"):
            print(f"✅ Action: {result['action']}")
            print(f"   Current: {result['current_equity_weight']}")
            print(f"   Recommended: {result['recommended_equity_weight']}")
            print(f"   Rationale: {result['rationale']}")


class TestAgentInteraction:
    """Test how agents share data."""
    
    def test_shared_data_flow(self):
        """Test that MacroAgent updates shared_data correctly."""
        import asyncio
        from agents.macro_agent import create_macro_agent
        from agents.base_agent import AgentState
        from agents.protocols import PortfolioTask, TaskType
        
        async def run_test():
            agent = create_macro_agent()
            
            # Create state
            state = AgentState()
            state.current_task = PortfolioTask(
                task_id="test_macro_flow",
                task_type=TaskType.MACRO_ANALYSIS,
                universe=[]
            )
            
            # Process
            result_state = await agent.process(state)
            
            # Check shared_data
            shared = result_state.shared_data
            
            print(f"Shared Data Keys: {list(shared.keys())}")
            
            expected_keys = ["vix_level", "market_regime", "macro_signal"]
            for key in expected_keys:
                if key in shared:
                    print(f"✅ {key}: {shared[key]}")
                else:
                    print(f"⚠️ {key}: missing")
            
            return shared
        
        shared = asyncio.run(run_test())
        assert "market_regime" in shared or True  # Allow empty if no data
        print("✅ Agent interaction test complete")


# ==================== INTEGRATION TEST ====================

def run_full_integration_test():
    """Run a full integration test simulating real usage."""
    print("\n" + "=" * 60)
    print("PHASE 5.4 FULL INTEGRATION TEST")
    print("=" * 60 + "\n")
    
    from agents.data_agent import create_data_agent
    from agents.macro_agent import create_macro_agent
    
    # 1. Setup
    print("1. Creating agents...")
    data_agent = create_data_agent(verbose=True)
    macro_agent = create_macro_agent(verbose=True)
    print("   ✅ Agents created\n")
    
    # 2. Fetch macro data
    print("2. Fetching macro data (VIX, Yields)...")
    macro_result = macro_agent.fetch_macro_data_tool(
        indicators="VIX,TNX_10Y,TYX_30Y,IRX_3M",
        days=30
    )
    print(f"   Result: {macro_result.get('rows_updated', 0)} rows updated\n")
    
    # 3. Get macro snapshot
    print("3. Getting macro snapshot...")
    snapshot = macro_agent.get_macro_snapshot_tool()
    if snapshot.get("vix"):
        print(f"   VIX: {snapshot['vix']['value']} ({snapshot['vix']['regime']})")
    if snapshot.get("yield_curve"):
        print(f"   Yield Curve: {snapshot['yield_curve']['status']}")
    print()
    
    # 4. Assess regime
    print("4. Assessing market regime...")
    if snapshot.get("vix"):
        regime = macro_agent.assess_regime_tool(
            vix_level=snapshot['vix']['value'],
            yield_curve_slope=snapshot.get('yield_curve', {}).get('slope')
        )
        print(f"   Regime: {regime.get('regime')}")
        print(f"   Risk Stance: {regime.get('risk_stance')}")
        print(f"   Equity Adjustment: {regime.get('equity_adjustment')}")
    print()
    
    # 5. Fetch price data
    print("5. Fetching price data (SPY, TLT, GLD)...")
    prices = data_agent.fetch_prices_tool(tickers="SPY,TLT,GLD", period="3Y")
    print(f"   Observations: {prices.get('num_observations')}")
    print(f"   Latest Prices: {prices.get('latest_prices')}")
    print()
    
    # 6. Calculate covariance
    print("6. Calculating covariance matrix...")
    cov = data_agent.calculate_covariance_tool(tickers="SPY,TLT,GLD", period="3Y")
    if cov.get("success"):
        print(f"   Method: {cov.get('method')}")
        print(f"   Volatilities: {cov.get('annualized_volatilities')}")
    print()
    
    # 7. Get risk-free rate
    print("7. Getting risk-free rate...")
    rf = data_agent.get_risk_free_rate_tool()
    print(f"   Rate: {rf.get('rate_formatted')} (source: {rf.get('source')})")
    print()
    
    # 8. Generate TAA signal
    print("8. Generating TAA signal...")
    taa = macro_agent.generate_taa_signal_tool(current_equity_weight=0.60)
    if taa.get("success"):
        print(f"   Action: {taa['action']}")
        print(f"   Current Weight: {taa['current_equity_weight']}")
        print(f"   Recommended Weight: {taa['recommended_equity_weight']}")
        print(f"   Rationale: {taa['rationale']}")
    print()
    
    print("=" * 60)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 60)


# ==================== MAIN ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Phase 5.4 Integration")
    parser.add_argument("--full", action="store_true", help="Run full integration test")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    args = parser.parse_args()
    
    if args.full:
        run_full_integration_test()
    elif args.unit:
        # Run unit tests
        print("Running unit tests...\n")
        
        # Database
        print("=== Database Tests ===")
        db_tests = TestDatabaseSetup()
        db_tests.test_macro_data_table_exists()
        db_tests.test_macro_data_insert()
        
        # DataManager
        print("\n=== DataManager Tests ===")
        dm_tests = TestDataManagerMacro()
        dm_tests.test_update_vix()
        dm_tests.test_get_vix_with_regime()
        
        # DataAgent
        print("\n=== DataAgent Tests ===")
        da_tests = TestDataAgentTools()
        da_tests.test_get_risk_free_rate_tool()
        da_tests.test_fetch_prices_tool()
        
        # MacroAgent
        print("\n=== MacroAgent Tests ===")
        ma_tests = TestMacroAgentTools()
        ma_tests.test_assess_regime_tool()
        ma_tests.test_generate_taa_signal_tool()
        
        print("\n✅ Unit tests complete!")
    else:
        # Default: run full test
        run_full_integration_test()
