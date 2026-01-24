import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.nodes import load_portfolio_context, get_current_positions
from agents.state import create_initial_state
from portfolio_tool.portfolio_manager import get_or_create_demo_portfolio

async def test():
    print("Testing Node helper functions...")
    
    # Create state with portfolio
    portfolio_id = get_or_create_demo_portfolio()
    state = create_initial_state("test", portfolio_id=portfolio_id)
    
    # Test load_portfolio_context
    print("\n1. Testing load_portfolio_context...")
    tickers, holdings = load_portfolio_context(state)
    print(f"✓ Loaded tickers: {tickers}")
    print(f"✓ Loaded {len(holdings) if holdings else 0} holdings")
    
    assert len(tickers) > 0
    
    # Test get_current_positions
    if holdings:
        print("\n2. Testing get_current_positions...")
        positions = get_current_positions(holdings)
        print(f"✓ Positions: {positions}")
        assert len(positions) > 0
    
    print("\n✅ Node helpers work!")

asyncio.run(test())