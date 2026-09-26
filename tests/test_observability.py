"""
Test Script for Observability Module.

Tests:
1. Tracer functionality
2. Token counter
3. Cost calculation
4. Export functionality

Run:
    python test_observability.py
"""

import sys
import os
import time

# Get the absolute path to the 'src' directory
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src')
sys.path.append(src_path)

def test_tracer_basic():
    """Test basic tracer functionality."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Tracer")
    print("=" * 60)
    
    from observability import Tracer, TraceLevel
    
    tracer = Tracer(level=TraceLevel.VERBOSE, console_output=True)
    
    with tracer.trace_request("test_req_001", "Test user message") as req:
        # Simulate RiskManager
        with req.trace_agent("RiskManager") as agent:
            agent.log_thinking("Analyzing user request...")
            agent.log_decision("Need to fetch market data")
            agent.log_delegation("DataAgent", "Fetch SPY prices")
            
            time.sleep(0.1)  # Simulate work
            agent.set_tokens(100, 50)
        
        # Simulate DataAgent
        with req.trace_agent("DataAgent") as agent:
            agent.log_thinking("Fetching price data...")
            
            with agent.trace_tool("fetch_prices_tool") as tool:
                tool.set_input({"tickers": "SPY,TLT", "period": "1Y"})
                time.sleep(0.05)
                tool.set_output({"success": True, "rows": 250})
            
            agent.set_tokens(50, 30)
        
        req.set_response("Here is your analysis...")
    
    # Check trace was stored
    last_trace = tracer.get_last_trace()
    assert last_trace is not None
    assert last_trace.request_id == "test_req_001"
    assert len(last_trace.events) > 0
    assert "RiskManager" in last_trace.agents_used
    assert "DataAgent" in last_trace.agents_used
    
    print(tracer.get_summary())
    
    print("\n✅ Basic tracer test PASSED")


def test_trace_export():
    """Test JSON export functionality."""
    print("\n" + "=" * 60)
    print("TEST 3: Trace Export")
    print("=" * 60)
    
    import json
    from observability import Tracer, TraceLevel
    
    tracer = Tracer(level=TraceLevel.MINIMAL, console_output=False)
    
    with tracer.trace_request("export_test", "Export test") as req:
        with req.trace_agent("TestAgent") as agent:
            agent.log_thinking("Testing export...")
            agent.set_tokens(100, 50)
    
    # Export
    tracer.export_json("test_traces.json")
    
    # Verify
    with open("test_traces.json") as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["request_id"] == "export_test"
    
    # Cleanup
    os.remove("test_traces.json")
    
    print("   ✓ Exported and verified JSON trace")
    print("\n✅ Export test PASSED")


def test_nested_tools():
    """Test nested tool tracing."""
    print("\n" + "=" * 60)
    print("TEST 4: Nested Tool Calls")
    print("=" * 60)
    
    from observability import Tracer, TraceLevel
    
    tracer = Tracer(level=TraceLevel.VERBOSE, console_output=True)
    
    with tracer.trace_request("nested_test", "Test nested tools") as req:
        with req.trace_agent("MacroAgent") as agent:
            agent.log_thinking("Need multiple data sources...")
            
            with agent.trace_tool("fetch_vix") as tool:
                tool.set_input({"days": 30})
                time.sleep(0.02)
                tool.set_output({"vix": 18.5})
            
            with agent.trace_tool("fetch_yields") as tool:
                tool.set_input({"maturities": ["2Y", "10Y"]})
                time.sleep(0.02)
                tool.set_output({"2Y": 4.5, "10Y": 4.2})
            
            with agent.trace_tool("assess_regime") as tool:
                tool.set_input({"vix": 18.5, "spread": -0.3})
                time.sleep(0.01)
                tool.set_output({"regime": "NEUTRAL"})
            
            agent.set_tokens(200, 100)
    
    last_trace = tracer.get_last_trace()
    assert len(last_trace.tools_called) == 3
    
    print("\n✅ Nested tools test PASSED")


def test_error_handling():
    """Test error tracing."""
    print("\n" + "=" * 60)
    print("TEST 5: Error Handling")
    print("=" * 60)
    
    from observability import Tracer, TraceLevel
    
    tracer = Tracer(level=TraceLevel.VERBOSE, console_output=True)
    
    try:
        with tracer.trace_request("error_test", "Test error handling") as req:
            with req.trace_agent("FailingAgent") as agent:
                agent.log_thinking("About to fail...")
                
                with agent.trace_tool("failing_tool") as tool:
                    tool.set_input({"will_fail": True})
                    raise ValueError("Simulated error!")
    except ValueError:
        pass  # Expected
    
    last_trace = tracer.get_last_trace()
    assert last_trace.success == False
    assert "Simulated error" in last_trace.error
    
    print("   ✓ Error was captured in trace")
    print("\n✅ Error handling test PASSED")


def test_no_token_counter_prices_a_model():
    """The token counter priced any model it did not know at a default
    rate and had no caller since the router went; the conversation layer
    records tokens and computes no price (decision 54)."""
    import importlib.util

    import observability

    assert importlib.util.find_spec("observability.token_counter") is None
    gone = {"TokenCounter", "TokenUsage", "UsageSummary", "calculate_cost",
            "get_token_counter", "set_token_counter", "MODEL_PRICING"}
    assert gone & set(observability.__all__) == set()
    assert [name for name in gone if hasattr(observability, name)] == []


def test_global_singleton():
    """Test global tracer singleton."""
    print("\n" + "=" * 60)
    print("TEST 7: Global Singleton")
    print("=" * 60)
    
    from observability import get_tracer, set_tracer, Tracer, TraceLevel
    
    # Create custom tracer
    custom_tracer = Tracer(level=TraceLevel.DEBUG, console_output=False)
    set_tracer(custom_tracer)
    
    # Get should return same instance
    retrieved = get_tracer()
    assert retrieved is custom_tracer
    
    print("   ✓ Singleton works correctly")
    print("\n✅ Singleton test PASSED")


def run_all_tests():
    """Run all observability tests."""
    print("\n" + "=" * 60)
    print("OBSERVABILITY MODULE TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_tracer_basic,
        test_trace_export,
        test_nested_tools,
        test_error_handling,
        test_global_singleton,
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
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
