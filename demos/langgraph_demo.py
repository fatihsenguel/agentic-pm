"""
🚀 AGENTIC FINANCE DEMO - "Bank-Ready" Version
Run this to talk to your Quant Agent.

This connects:
1. The Smart Router (Brain)
2. The Strict Nodes (Body)
3. The Portfolio Database (Context)
"""

import sys
import os
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Configure Logging (Less verbose for demo, but show errors)
logging.basicConfig(
    level=logging.ERROR,
    format='%(name)s: %(message)s'
)

# Imports
from agents.graph import create_agent_graph, stream_agent_graph
from agents.state import create_initial_state
from portfolio_tool.portfolio_manager import get_or_create_demo_portfolio, PortfolioManager
from config import config

# Colors for nice output
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

async def run_demo_interactive():
    print(f"\n{BOLD}{CYAN}🏦 AGENTIC FINANCE - PORTFOLIO MANAGER AI{RESET}")
    print("=" * 60)
    
    # 1. Setup Portfolio Context
    print(f"{YELLOW}[System] Loading Portfolio Context...{RESET}")
    pm = PortfolioManager()
    
    pid = None
    try:
        # Create/Get a demo portfolio so we have something to analyze
        pid = get_or_create_demo_portfolio()
        tickers = pm.get_portfolio_tickers(pid)
        print(f"{GREEN}✓ Loaded Active Portfolio ID {pid}{RESET}")
        print(f"  • Holdings: {', '.join(tickers)}")
    except Exception as e:
        print(f"{RED}❌ Could not load portfolio context: {e}{RESET}")
        print("  (Agents will still work if you explicitly mention tickers like 'SPY')")

    print("=" * 60)
    print("Type 'exit' to quit.\n")

    # 2. Interactive Loop
    while True:
        try:
            user_input = input(f"\n{BOLD}You:{RESET} ")
            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n{YELLOW}Goodbye!{RESET}")
                break
            
            if not user_input.strip():
                continue

            print(f"\n{CYAN}🤖 Agent is thinking...{RESET}")
            print("-" * 60)
            
            # 3. Stream the Graph Execution
            # We pass 'pid' so the Router knows about your holdings
            start_time = asyncio.get_event_loop().time()
            final_state = None
            
            async for node_name, state in stream_agent_graph(user_input, portfolio_id=pid):
                elapsed = asyncio.get_event_loop().time() - start_time
                final_state = state
                
                # Visual Feedback based on Node
                if node_name == "Router":
                    decision = state.get("router_decision", {})
                    intent = decision.get("intent", "UNKNOWN")
                    print(f"[{elapsed:.1f}s] 🧠 {BOLD}Router:{RESET} Detected intent '{intent}'")
                    if decision.get("reasoning"):
                        print(f"           📝 {decision['reasoning']}")
                
                elif node_name == "DataAgent":
                    print(f"[{elapsed:.1f}s] 📊 {BOLD}DataAgent:{RESET} Market data fetched successfully")
                
                elif node_name == "OptimizationAgent":
                    print(f"[{elapsed:.1f}s] 🧮 {BOLD}OptimizationAgent:{RESET} Solver converged")
                
                elif node_name == "RebalanceAgent":
                    print(f"[{elapsed:.1f}s] ⚖️ {BOLD}RebalanceAgent:{RESET} Trade list generated")
                
                elif node_name == "synthesizer":
                    print(f"[{elapsed:.1f}s] ✍️ {BOLD}Synthesizer:{RESET} Formatting response...")

            # 4. Display Final Result
            print("-" * 60)
            
            if final_state:
                # Check for direct answer (Router clarification)
                if final_state.get("final_response"):
                    print(f"{GREEN}{BOLD}AI:{RESET} {final_state['final_response']}")
                
                # Check for Router Error/Clarification
                elif final_state.get("router_decision", {}).get("intent") == "clarification_needed":
                    q = final_state["router_decision"].get("clarification_question")
                    print(f"{YELLOW}AI: {q}{RESET}")

                # Check for Success Shared Data
                else:
                    shared = final_state.get("shared_data", {})
                    
                    # Show Optimization Results
                    if "optimal_weights" in shared:
                        print(f"\n{BOLD}📊 Recommended Allocation:{RESET}")
                        weights = shared["optimal_weights"]
                        # Sort by weight
                        for t, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
                            if w > 0.001: # Hide tiny dust
                                print(f"  • {t:<5}: {w*100:5.1f}%")
                    
                    # Show Rebalance Trades
                    if "rebalance_result" in shared:
                        res = shared["rebalance_result"]
                        trades = res.get("trades", [])
                        if trades:
                            print(f"\n{BOLD}🔄 Recommended Trades:{RESET}")
                            for t in trades:
                                action = t.get('action', 'TRADE').upper()
                                color = GREEN if action == 'BUY' else RED
                                print(f"  • {color}{action:<4}{RESET} {t['ticker']:<5} {t['shares']:>4} shares  (${t['trade_value']:,.2f})")
                        else:
                            print(f"\n{GREEN}✅ Portfolio is balanced. No trades needed.{RESET}")

                    # Fallback
                    if not final_state.get("final_response") and not "optimal_weights" in shared and not "rebalance_result" in shared:
                        print(f"{GREEN}Done. Check logs for details.{RESET}")

        except Exception as e:
            print(f"\n{RED}❌ System Error: {e}{RESET}")
            # Uncomment for debugging:
            # import traceback
            # traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(run_demo_interactive())
    except KeyboardInterrupt:
        print("\nGoodbye!")