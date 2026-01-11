import sys
import os

# --- NEU: MOCK AKTIVIEREN ---
os.environ["USE_MOCK_QUOTA"] = "True" 
# ----------------------------

# Pfad zu 'src' hinzufügen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from portfolio_tool.tools.data_tools import fetch_stock_prices, fetch_fundamentals

def test_manual_tool_execution():
    print("\n--- 1. TEST: fetch_stock_prices (SAP) ---")
    # Simulation: Agent ruft Tool mit Argumenten auf
    args = {"ticker": "SAP", "start_date": "2024-01-01"}
    result = fetch_stock_prices.invoke(args)
    print(f"Ergebnis: {result}")

    print("\n--- 2. TEST: fetch_fundamentals (SAP) ---")
    args_fund = {"ticker": "SAP"}
    result_fund = fetch_fundamentals.invoke(args_fund)
    print(f"Ergebnis: {result_fund}")

if __name__ == "__main__":
    test_manual_tool_execution()