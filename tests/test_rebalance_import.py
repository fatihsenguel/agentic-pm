# Create a test file: tests/test_rebalance.py
import sys
sys.path.insert(0, 'src')

from config import config

# Test config is working
print(f"Rebalance threshold: {config.rebalance.default_drift_threshold}")
print(f"Transaction cost: {config.rebalance.default_transaction_cost_bps}")
print("✅ Config works!")