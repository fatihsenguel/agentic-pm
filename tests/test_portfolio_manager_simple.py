import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from portfolio_tool.portfolio_manager import PortfolioManager

print("Testing Portfolio Manager...")

# Create
pm = PortfolioManager()
pid = pm.create_portfolio("Test")
print(f"✓ Created portfolio {pid}")

# Add holdings
pm.add_holding(pid, "SPY", quantity=100, average_price=450.0)
print("✓ Added holding")

# Get tickers
tickers = pm.get_portfolio_tickers(pid)
print(f"✓ Tickers: {tickers}")
assert "SPY" in tickers

# Cleanup
pm.delete_portfolio(pid)
print("✓ Deleted portfolio")

print("\n✅ Portfolio Manager works!")