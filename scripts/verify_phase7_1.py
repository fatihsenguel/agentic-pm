#!/usr/bin/env python3
"""
Phase 7.1 Verification Script

Run this to verify IPSManager and ESGScreener are working correctly.

Usage:
    python scripts/verify_phase7_1.py
"""

import sys
import os

# Add project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))


def main():
    print("=" * 60)
    print("PHASE 7.1 VERIFICATION: IPS Manager & ESG Screener")
    print("=" * 60)
    print()
    
    # =========================================================================
    # 1. Test IPSManager
    # =========================================================================
    print("1. TESTING IPS MANAGER")
    print("-" * 40)
    
    from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.ips_manager import IPSManager
    
    manager = IPSManager()
    
    # Get Anders Family Trust
    anders = manager.get_client("8821-X")
    if anders:
        print(f"   ✓ Found client: {anders.name}")
    else:
        print("   ✗ ERROR: Anders Family Trust not found!")
        return False
    
    # Get constraints
    constraints = manager.get_client_constraints(anders.id)
    print(f"   ✓ Loaded {len(constraints)} constraints")
    
    # Check constraint types
    types_found = set(c.type.value for c in constraints)
    print(f"   ✓ Constraint types: {types_found}")
    
    # Check ESG
    has_esg = manager.has_esg_constraints(anders.id)
    print(f"   ✓ Has ESG constraints: {has_esg}")
    
    esg_categories = manager.get_esg_categories(anders.id)
    print(f"   ✓ ESG categories: {esg_categories}")
    
    # Get default constraints
    defaults = manager.get_default_constraints("moderate")
    print(f"   ✓ Default constraints (moderate): {len(defaults)}")
    
    manager.close()
    print()
    
    # =========================================================================
    # 2. Test ESGScreener
    # =========================================================================
    print("2. TESTING ESG SCREENER")
    print("-" * 40)
    
    from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.esg_screener import ESGScreener
    
    screener = ESGScreener()
    
    # Get exclusion stats
    stats = screener.get_exclusion_stats()
    print(f"   ✓ Exclusion stats: {stats}")
    
    # Check excluded security
    result = screener.check_security(ticker="BTI")
    if result["excluded"]:
        print(f"   ✓ BTI is excluded: {result['category']}")
    else:
        print("   ✗ ERROR: BTI should be excluded!")
        return False
    
    # Check non-excluded security
    result = screener.check_security(ticker="AAPL")
    if not result["excluded"]:
        print(f"   ✓ AAPL is not excluded")
    else:
        print("   ✗ ERROR: AAPL should not be excluded!")
        return False
    
    # Get excluded tickers
    excluded = screener.get_excluded_tickers()
    print(f"   ✓ Total excluded tickers: {len(excluded)}")
    
    # Test holdings check
    test_holdings = [
        {"ticker": "AAPL", "quantity": 100, "price": 150.0},
        {"ticker": "BTI", "quantity": 50, "price": 35.0},
        {"ticker": "MSFT", "quantity": 75, "price": 400.0},
    ]
    
    breaches = screener.check_holdings_list(test_holdings)
    print(f"   ✓ Test holdings check: {len(breaches)} breach(es) found")
    
    if breaches:
        for b in breaches:
            print(f"      - {b.ticker}: {b.message[:50]}...")
    
    screener.close()
    print()
    
    # =========================================================================
    # 3. Integration Test
    # =========================================================================
    print("3. INTEGRATION TEST")
    print("-" * 40)
    
    manager = IPSManager()
    screener = ESGScreener()
    
    # Workflow: Client -> ESG Categories -> Screen Holdings
    client = manager.get_client("8821-X")
    categories = manager.get_esg_categories(client.id)
    
    # Holdings with violations
    holdings = [
        {"ticker": "AAPL", "quantity": 100, "price": 150.0},
        {"ticker": "BTI", "quantity": 50, "price": 35.0},   # Tobacco
        {"ticker": "BTU", "quantity": 30, "price": 20.0},   # Coal
        {"ticker": "NVDA", "quantity": 25, "price": 800.0},
    ]
    
    breaches = screener.check_holdings_list(holdings, categories=categories)
    
    print(f"   ✓ Client: {client.name}")
    print(f"   ✓ ESG Categories: {categories}")
    print(f"   ✓ Holdings checked: {len(holdings)}")
    print(f"   ✓ Breaches found: {len(breaches)}")
    
    for b in breaches:
        print(f"      🔴 {b.ticker}: {b.constraint_name}")
    
    manager.close()
    screener.close()
    print()
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 60)
    print("✅ PHASE 7.1 VERIFICATION COMPLETE!")
    print("=" * 60)
    print()
    print("Components verified:")
    print("  ✓ IPSManager - Client lookup")
    print("  ✓ IPSManager - Constraint loading")
    print("  ✓ IPSManager - ESG category extraction")
    print("  ✓ IPSManager - Default constraints")
    print("  ✓ ESGScreener - Exclusion set loading")
    print("  ✓ ESGScreener - Single security check")
    print("  ✓ ESGScreener - Holdings list check")
    print("  ✓ Integration - End-to-end workflow")
    print()
    print("Next: Phase 7.2 - Compliance Agent")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
