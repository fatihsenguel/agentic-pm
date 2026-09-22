"""
Test Script for Phase 5.4 - the macro tables and DataAgent.

This script tests:
1. Database connection and MacroData table
2. DataManager macro methods
3. DataAgent tools (DB-backed)

Decision 51 deleted MacroAgent on 21 September. The macro tables stay: the
risk-free rate DataAgent publishes is the 10Y Treasury yield read from
macro_data, so the rows and the DataManager methods over them have a live
reader. What went with the agent is this file's MacroAgent tool tests, its
shared_data interaction test, and its integration script.

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


