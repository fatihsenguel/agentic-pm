"""
Comprehensive test for refactored DataManager.
Tests all update methods to verify they return UpdateResult.
"""

import sys
sys.path.insert(0, r'E:\Programming\AGENTIC_FINANCE\src')

from portfolio_tool.data_manager import DataManager
from portfolio_tool.database_setup import Asset, get_session
from portfolio_tool.providers.yfinance_provider import YFinanceProvider
from portfolio_tool.models.responses import UpdateResult


# === MOCK QUOTA MANAGER FÜR TESTS ===
class MockQuotaManager:
    """
    Mock QuotaManager für Tests.
    Erlaubt alle API-Calls ohne echte Quota-Prüfung.
    """
    
    def __init__(self, session):
        self.session = session
        print("   ℹ️  Using MockQuotaManager (no real quota checks)")
    
    def can_consume_credit(self) -> bool:
        """Immer erlauben (für Tests)."""
        return True
    
    def log_api_call(self, **kwargs):
        """Nichts loggen (für Tests)."""
        pass


def test_all_update_methods():
    """Test that all update methods return UpdateResult."""
    
    print("\n" + "="*70)
    print("🧪 COMPREHENSIVE DATAMANAGER REFACTORING TEST")
    print("="*70 + "\n")
    
    # Setup
    print("📦 Initializing DataManager...")
    session = get_session()
    
    # Mock QuotaManager (kein echtes Quota-Management für Tests)
    quota_manager = MockQuotaManager(session)
    
    # Provider mit Mock QuotaManager
    provider = YFinanceProvider(quota_manager)
    
    # DataManager
    dm = DataManager(session, provider)
    print("   ✅ DataManager initialized\n")
    
    # Get/Create test asset
    print("🔍 Getting/Creating test asset (AAPL)...")
    asset = dm._get_or_create_asset("AAPL", "Apple Inc.", "stock")
    
    if not asset:
        print("   ❌ FAILED: Could not create/find AAPL")
        return False
    
    print(f"   ✅ Asset ready: {asset.ticker}\n")
    
    # Track results
    all_passed = True
    results = {}
    
    # === TEST 1: update_prices_for_asset ===
    print("="*70)
    print("TEST 1/8: update_prices_for_asset()")
    print("="*70)
    try:
        result = dm.update_prices_for_asset(asset, start_date=None)
        
        assert isinstance(result, UpdateResult), f"Wrong type: {type(result)}"
        assert hasattr(result, 'success'), "Missing 'success' attribute"
        assert hasattr(result, 'operation'), "Missing 'operation' attribute"
        assert hasattr(result, 'affected_count'), "Missing 'affected_count' attribute"
        
        print(f"✅ Returns UpdateResult")
        print(f"   Success: {result.success}")
        print(f"   Operation: {result.operation}")
        print(f"   Affected: {result.affected_count}")
        print(f"   Entities: {result.entities}")
        
        if result.error_message:
            print(f"   ⚠️  Error: {result.error_message}")
        
        results['update_prices'] = "✅ PASS"
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results['update_prices'] = f"❌ FAIL: {e}"
        all_passed = False
    
    print()
    
    # === TEST 2: update_dividends_for_asset ===
    print("="*70)
    print("TEST 2/8: update_dividends_for_asset()")
    print("="*70)
    try:
        result = dm.update_dividends_for_asset(asset)
        
        assert isinstance(result, UpdateResult), f"Wrong type: {type(result)}"
        
        print(f"✅ Returns UpdateResult")
        print(f"   Success: {result.success}")
        print(f"   Affected: {result.affected_count}")
        
        results['update_dividends'] = "✅ PASS"
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results['update_dividends'] = f"❌ FAIL: {e}"
        all_passed = False
    
    print()
    
    # === TEST 3: update_splits_for_asset ===
    print("="*70)
    print("TEST 3/8: update_splits_for_asset()")
    print("="*70)
    try:
        result = dm.update_splits_for_asset(asset)
        
        assert isinstance(result, UpdateResult), f"Wrong type: {type(result)}"
        
        print(f"✅ Returns UpdateResult")
        print(f"   Success: {result.success}")
        print(f"   Affected: {result.affected_count}")
        
        results['update_splits'] = "✅ PASS"
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results['update_splits'] = f"❌ FAIL: {e}"
        all_passed = False
    
    print()
    
    # === TEST 4: update_shares_history_for_asset ===
    print("="*70)
    print("TEST 4/8: update_shares_history_for_asset()")
    print("="*70)
    try:
        result = dm.update_shares_history_for_asset(asset, force_update=True)
        
        assert isinstance(result, UpdateResult), f"Wrong type: {type(result)}"
        
        print(f"✅ Returns UpdateResult")
        print(f"   Success: {result.success}")
        print(f"   Affected: {result.affected_count}")
        
        results['update_shares'] = "✅ PASS"
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results['update_shares'] = f"❌ FAIL: {e}"
        all_passed = False
    
    print()
    
    # === TEST 5: update_quarterly_earnings_for_asset ===
    print("="*70)
    print("TEST 5/8: update_quarterly_earnings_for_asset()")
    print("="*70)
    try:
        result = dm.update_quarterly_earnings_for_asset(asset, force_update=True)
        
        assert isinstance(result, UpdateResult), f"Wrong type: {type(result)}"
        
        print(f"✅ Returns UpdateResult")
        print(f"   Success: {result.success}")
        print(f"   Affected: {result.affected_count}")
        
        results['update_earnings'] = "✅ PASS"
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results['update_earnings'] = f"❌ FAIL: {e}"
        all_passed = False
    
    print()
    
    # === TEST 6: force_update_asset_info ===
    print("="*70)
    print("TEST 6/8: force_update_asset_info()")
    print("="*70)
    try:
        result = dm.force_update_asset_info(asset)
        
        assert isinstance(result, UpdateResult), f"Wrong type: {type(result)}"
        
        print(f"✅ Returns UpdateResult")
        print(f"   Success: {result.success}")
        print(f"   Affected: {result.affected_count}")
        
        results['update_asset_info'] = "✅ PASS"
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results['update_asset_info'] = f"❌ FAIL: {e}"
        all_passed = False
    
    print()
    
    # === TEST 7: update_fundamental_data ===
    print("="*70)
    print("TEST 7/8: update_fundamental_data()")
    print("="*70)
    try:
        result = dm.update_fundamental_data(asset, force_update=True)
        
        assert isinstance(result, UpdateResult), f"Wrong type: {type(result)}"
        
        print(f"✅ Returns UpdateResult")
        print(f"   Success: {result.success}")
        print(f"   Affected: {result.affected_count}")
        
        results['update_fundamentals'] = "✅ PASS"
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results['update_fundamentals'] = f"❌ FAIL: {e}"
        all_passed = False
    
    print()
    
    # === TEST 8: update_financial_statements_for_asset ===
    print("="*70)
    print("TEST 8/8: update_financial_statements_for_asset()")
    print("="*70)
    try:
        result = dm.update_financial_statements_for_asset(
            asset,
            report_type="balance_sheet",
            period_type="annual"
        )
        
        assert isinstance(result, UpdateResult), f"Wrong type: {type(result)}"
        
        print(f"✅ Returns UpdateResult")
        print(f"   Success: {result.success}")
        print(f"   Affected: {result.affected_count}")
        
        results['update_statements'] = "✅ PASS"
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results['update_statements'] = f"❌ FAIL: {e}"
        all_passed = False
    
    print()
    
    # === SUMMARY ===
    print("="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    for method, status in results.items():
        print(f"   {method:30} {status}")
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ DataManager is fully refactored and agent-ready!")
        print("="*70)
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  DO NOT COMMIT until all tests pass!")
        print("="*70)
        return False



if __name__ == "__main__":
    success = test_all_update_methods()
    
    if success:
        print("\n✅ You can now commit your changes:")
        print('   git add .')
        print('   git commit -m "Phase 1B complete: All DataManager methods return UpdateResult"')
    else:
        print("\n❌ Fix the errors above before committing!")
    
    exit(0 if success else 1)


    pipeline_run.status = PipelineRunStatus.SUCCESS
    pipeline_run.end_time = func.now()
    session.commit()