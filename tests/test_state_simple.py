import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.state import create_initial_state

print("Testing State with portfolio_id...")

# Create state with portfolio
state = create_initial_state("test message", portfolio_id=123)

print(f"✓ portfolio_id in state: {state.get('portfolio_id')}")
assert state.get('portfolio_id') == 123

print(f"✓ portfolio_holdings in state: {state.get('portfolio_holdings')}")
assert 'portfolio_holdings' in state

print("\n✅ State works with portfolio!")