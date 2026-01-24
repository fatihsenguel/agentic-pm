import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.smart_router import SmartRouter
from portfolio_tool.portfolio_manager import get_or_create_demo_portfolio

async def test():
    print("Testing Router with portfolio_id...")
    
    # Get demo portfolio
    portfolio_id = get_or_create_demo_portfolio()
    print(f"✓ Demo portfolio: {portfolio_id}")
    
    # Test router
    router = SmartRouter()
    decision, validation = await router.route(
        "Analyze my portfolio",
        portfolio_id=portfolio_id
    )
    
    print(f"✓ Router accepted portfolio_id")
    print(f"✓ Decision tickers: {decision.parameters.tickers}")
    print(f"✓ Decision portfolio_id: {decision.parameters.portfolio_id}")
    
    assert decision.parameters.portfolio_id == portfolio_id
    
    print("\n✅ Router works with portfolio!")

asyncio.run(test())