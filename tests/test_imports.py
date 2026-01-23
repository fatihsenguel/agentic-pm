# tests/test_imports.py
"""
Quick test to verify all agents import successfully after config refactor.
"""

import sys
sys.path.insert(0, 'src')

print("Testing imports after config refactor...")
print("=" * 60)

tests = []

# Test 1: Config imports
print("\n1. Testing config.py...")
try:
    from config import config
    assert hasattr(config, 'data')
    assert hasattr(config, 'macro')
    assert hasattr(config, 'optimization')
    assert hasattr(config, 'rebalance')
    assert hasattr(config, 'backtest')
    assert hasattr(config, 'risk')
    assert hasattr(config, 'features')
    print("   ✅ config.py loads successfully")
    print(f"   ✅ All config sections present: {list(vars(config).keys())}")
    tests.append(("Config", True))
except Exception as e:
    print(f"   ❌ config.py FAILED: {e}")
    tests.append(("Config", False))

# Test 2: Agent imports
agents_to_test = [
    "data_agent",
    "macro_agent",
    "optimization_agent",
    "rebalance_agent",
    "backtest_agent",
    "risk_manager_agent",
    "smart_router"
]

for agent_name in agents_to_test:
    print(f"\n2. Testing agents.{agent_name}...")
    try:
        module = __import__(f'agents.{agent_name}', fromlist=[''])
        
        # Check for obsolete XxxAgentConfig classes
        obsolete_configs = [name for name in dir(module) if 'AgentConfig' in name and name != 'AgentConfig']
        if obsolete_configs and agent_name != 'base_agent':
            print(f"   ⚠️  WARNING: Found obsolete config classes: {obsolete_configs}")
            tests.append((agent_name, False))
        else:
            print(f"   ✅ {agent_name} imports successfully")
            tests.append((agent_name, True))
    except ImportError as e:
        print(f"   ❌ {agent_name} FAILED: {e}")
        tests.append((agent_name, False))
    except Exception as e:
        print(f"   ❌ {agent_name} ERROR: {e}")
        tests.append((agent_name, False))

# Test 3: Config values
print("\n3. Testing config values...")
try:
    from config import config
    
    # Test a few key values
    assert config.data.default_period == "3Y"
    assert config.data.trading_days_per_year == 252
    assert config.macro.vix_elevated == 25.0
    assert config.optimization.risk_free_rate == 0.05
    assert config.rebalance.default_drift_threshold == 5.0
    
    print("   ✅ Config values are correct")
    tests.append(("Config Values", True))
except AssertionError as e:
    print(f"   ❌ Config value mismatch: {e}")
    tests.append(("Config Values", False))
except Exception as e:
    print(f"   ❌ Config value test FAILED: {e}")
    tests.append(("Config Values", False))

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

passed = sum(1 for _, success in tests if success)
total = len(tests)

for name, success in tests:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {name}")

print(f"\nTotal: {passed}/{total} tests passed")

if passed == total:
    print("\n🎉 ALL TESTS PASSED! Ready to run the demo.")
else:
    print(f"\n⚠️  {total - passed} tests failed. Fix these before running the demo.")

sys.exit(0 if passed == total else 1)
