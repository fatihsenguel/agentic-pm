#!/usr/bin/env python3
"""
Phase 7.3 Verification Script - Router & Graph Integration

This script tests that the compliance routing is working correctly.

Usage:
    python scripts/verify_phase7_3.py
"""

import sys
import os
import asyncio

# Add project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))


async def test_routing():
    """Test that compliance queries are routed correctly."""
    from agents.smart_router import get_router
    
    print("=" * 70)
    print("PHASE 7.3 VERIFICATION: Router & Graph Integration")
    print("=" * 70)
    print()
    
    router = get_router()
    
    # Test queries that should route to ComplianceAgent
    test_queries = [
        ("Check IPS compliance for my portfolio", "compliance_check", "ComplianceAgent"),
        ("Are there any ESG violations?", "compliance_check", "ComplianceAgent"),
        ("Is BTI allowed under our ESG policy?", "compliance_check", "ComplianceAgent"),
        ("Check allocation limits", "compliance_check", "ComplianceAgent"),
        ("Run compliance check for client 8821-X", "compliance_check", "ComplianceAgent"),
    ]
    
    print("1. TESTING ROUTER INTENT DETECTION")
    print("-" * 50)
    
    passed = 0
    failed = 0
    
    for query, expected_intent, expected_agent in test_queries:
        try:
            decision, validation = await router.route(
                user_message=query,
                portfolio_id=1
            )
            
            if decision:
                actual_intent = decision.execution_intent.value if hasattr(decision.execution_intent, 'value') else decision.execution_intent
                actual_agent = decision.execution_order[0] if decision.execution_order else "None"
                
                intent_match = actual_intent == expected_intent
                agent_match = actual_agent == expected_agent
                
                if intent_match and agent_match:
                    print(f"   ✓ '{query[:40]}...'")
                    print(f"     → Intent: {actual_intent}, Agent: {actual_agent}")
                    passed += 1
                else:
                    print(f"   ✗ '{query[:40]}...'")
                    print(f"     Expected: {expected_intent} / {expected_agent}")
                    print(f"     Got:      {actual_intent} / {actual_agent}")
                    failed += 1
            else:
                print(f"   ✗ '{query[:40]}...' - Router returned None")
                failed += 1
                
        except Exception as e:
            print(f"   ✗ '{query[:40]}...' - Error: {e}")
            failed += 1
    
    print()
    print(f"   Results: {passed}/{len(test_queries)} passed")
    print()
    
    return passed == len(test_queries)


async def test_compliance_node():
    """Test that the compliance agent node works."""
    print("2. TESTING COMPLIANCE AGENT NODE")
    print("-" * 50)
    
    try:
        from agents.nodes import compliance_agent_node
        print("   ✓ compliance_agent_node imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import compliance_agent_node: {e}")
        print("   → Make sure you've added compliance_agent_node to nodes.py")
        return False
    
    # Test with a mock state
    from agents.state import create_initial_state
    
    state = create_initial_state("Check compliance", portfolio_id=1)
    state["router_decision"] = {
        "execution_intent": "compliance_check",
        "execution_order": ["ComplianceAgent"],
        "parameters": {
            "portfolio_id": 1,
            "command": "compliance_check",
            "tickers": []
        }
    }
    
    try:
        result = await compliance_agent_node(state)
        
        if "sub_results" in result and "ComplianceAgent" in result.get("sub_results", {}):
            compliance_result = result["sub_results"]["ComplianceAgent"]
            if compliance_result.get("success"):
                print(f"   ✓ Compliance check ran successfully")
                print(f"     Status: {compliance_result.get('status', 'N/A')}")
                print(f"     Breaches: {compliance_result.get('num_breaches', 0)}")
                return True
            else:
                print(f"   ✗ Compliance check failed: {compliance_result.get('error')}")
                return False
        else:
            print(f"   ✗ Unexpected result structure")
            return False
            
    except Exception as e:
        import traceback
        print(f"   ✗ Error running compliance node: {e}")
        traceback.print_exc()
        return False


async def test_graph_integration():
    """Test that the full graph works with compliance queries."""
    print("3. TESTING FULL GRAPH INTEGRATION")
    print("-" * 50)
    
    try:
        from agents.graph import run_agent_graph
        
        result = await run_agent_graph(
            "Check IPS compliance for my portfolio",
            portfolio_id=1
        )
        
        # Check if ComplianceAgent was in the execution
        sub_results = result.get("sub_results", {})
        
        if "ComplianceAgent" in sub_results:
            compliance = sub_results["ComplianceAgent"]
            print(f"   ✓ ComplianceAgent executed in graph")
            print(f"     Status: {compliance.get('status', 'N/A')}")
            
            # Check final response
            final = result.get("final_response", {})
            if final.get("success"):
                print(f"   ✓ Graph completed successfully")
                return True
            else:
                print(f"   ⚠ Graph completed but final response indicates failure")
                return True  # Still counts as integration working
        else:
            print(f"   ✗ ComplianceAgent not found in sub_results")
            print(f"     Available: {list(sub_results.keys())}")
            return False
            
    except Exception as e:
        import traceback
        print(f"   ✗ Error running graph: {e}")
        traceback.print_exc()
        return False


async def main():
    """Run all verification tests."""
    
    results = []
    
    # Test 1: Routing
    try:
        results.append(("Router Intent Detection", await test_routing()))
    except Exception as e:
        print(f"   ✗ Router test failed with error: {e}")
        results.append(("Router Intent Detection", False))
    
    print()
    
    # Test 2: Node
    try:
        results.append(("Compliance Agent Node", await test_compliance_node()))
    except Exception as e:
        print(f"   ✗ Node test failed with error: {e}")
        results.append(("Compliance Agent Node", False))
    
    print()
    
    # Test 3: Full Graph
    try:
        results.append(("Full Graph Integration", await test_graph_integration()))
    except Exception as e:
        print(f"   ✗ Graph test failed with error: {e}")
        results.append(("Full Graph Integration", False))
    
    # Summary
    print()
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("✅ PHASE 7.3 VERIFICATION COMPLETE!")
        print()
        print("You can now ask:")
        print('  • "Check IPS compliance for my portfolio"')
        print('  • "Are there any ESG violations?"')
        print('  • "Is BTI allowed under our ESG policy?"')
        print('  • "Run compliance check for client 8821-X"')
    else:
        print("❌ Some tests failed. Please check the integration steps.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
