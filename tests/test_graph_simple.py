import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.graph import create_agent_graph
from agents.state import create_initial_state
from portfolio_tool.portfolio_manager import get_or_create_demo_portfolio

async def test():
    print("Testing full graph with portfolio...")
    
    # Setup
    portfolio_id = get_or_create_demo_portfolio()
    graph = create_agent_graph()
    
    # Create initial state
    initial_state = create_initial_state(
        "What's the current market regime?",
        portfolio_id=portfolio_id
    )
    
    print(f"✓ Running graph with portfolio {portfolio_id}...")
    
    # Run graph
    result = await graph.ainvoke(initial_state)
    
    print(f"✓ Graph completed")
    
    if result.get('final_response'):
        print(f"✓ Got response: {result['final_response'][:100]}...")
    
    print("\n✅ Full graph works with portfolio!")

asyncio.run(test())