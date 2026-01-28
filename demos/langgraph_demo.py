"""
🚀 AGENTIC FINANCE DEMO - "Bank-Ready" Version
Run this to talk to your Quant Agent.
"""

import sys
import os
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Configure Logging
logging.basicConfig(level=logging.ERROR)

# Imports
from agents.state import create_initial_state
from portfolio_tool.portfolio_manager import get_or_create_demo_portfolio, PortfolioManager
from langchain_core.messages import HumanMessage, AIMessage # <--- Import this

# Colors
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
        pid = get_or_create_demo_portfolio()
        tickers = pm.get_portfolio_tickers(pid)
        print(f"{GREEN}✓ Loaded Active Portfolio ID {pid}{RESET}")
        print(f"  • Holdings: {', '.join(tickers)}")
    except Exception as e:
        print(f"{RED}❌ Could not load portfolio context: {e}{RESET}")

    print("=" * 60)
    print("Type 'exit' to quit.\n")

    # Initialize Chat Memory
    chat_memory = []

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
            
            # 3. Create State with History
            state_input = create_initial_state(user_input, portfolio_id=pid)
            
            # Inject memory (Old messages + Newest message)
            if chat_memory:
                # create_initial_state adds the user input as the last message
                # We need to prepend the history
                current_msg = state_input["messages"][-1] 
                state_input["messages"] = chat_memory + [current_msg]

            # 4. Stream Execution (SINGLE RUN)
            from agents.graph import get_graph
            graph = get_graph()
            
            final_state = None
            start_time = asyncio.get_event_loop().time()
            
            # ⚡️ FIXED: Replaced double loop with single robust loop
            async for event in graph.astream(state_input):
                 for node_name, state in event.items():
                    elapsed = asyncio.get_event_loop().time() - start_time
                    final_state = state
                    
                    if node_name == "Router":
                        decision = state.get("router_decision", {})
                        intent = decision.get("intent", "UNKNOWN")
                        print(f"[{elapsed:.1f}s] 🧠 {BOLD}Router:{RESET} Detected intent '{intent}'")
                    
                    elif node_name == "DataAgent":
                        print(f"[{elapsed:.1f}s] 📊 {BOLD}DataAgent:{RESET} Market data fetched")
                    
                    elif node_name == "OptimizationAgent":
                        print(f"[{elapsed:.1f}s] 🧮 {BOLD}OptimizationAgent:{RESET} Optimization complete")

                    elif node_name == "RebalanceAgent":
                        print(f"[{elapsed:.1f}s] ⚖️ {BOLD}RebalanceAgent:{RESET} Trades generated")
                        
                    elif node_name == "BacktestAgent":
                        print(f"[{elapsed:.1f}s] 📈 {BOLD}BacktestAgent:{RESET} Simulation complete")

                    elif node_name == "synthesizer":
                        print(f"[{elapsed:.1f}s] ✍️ {BOLD}Synthesizer:{RESET} Writing response...")

            # 5. Display Result & Update Memory
            print("-" * 60)
            
            ai_response = ""
            if final_state:
                # NEW: The synthesizer returns a dict (AgentResponse)
                raw_response = final_state.get("final_response")
                
                if raw_response and isinstance(raw_response, dict):
                    # Extract the human-readable summary from the nested 'data' field
                    ai_response = raw_response.get("data", {}).get("summary", "")
                    
                    # Print the primary AI response
                    print(f"{GREEN}{BOLD}AI:{RESET}\n{ai_response}")
                    
                    # DEBUG: Print structured metrics if they exist (Hot Potato Principle)
                    details = raw_response.get("data", {}).get("details", {})
                    if details:
                        print(f"\n{YELLOW}[Metrics]:{RESET} {details}")
                
                # Fallback for clarification logic
                elif final_state.get("router_decision", {}).get("intent") == "clarification_needed":
                    ai_response = final_state["router_decision"].get("clarification_question")
                    print(f"{YELLOW}AI: {ai_response}{RESET}")

                # Save to memory
                chat_memory.append(HumanMessage(content=user_input))
                if ai_response:
                    chat_memory.append(AIMessage(content=ai_response))

                # Success Data Display
                shared = final_state.get("shared_data", {})
                if "optimal_weights" in shared:
                    print(f"\n{BOLD}📊 Allocation:{RESET}")
                    for t, w in shared["optimal_weights"].items():
                        if w > 0.01: print(f"  • {t:<5}: {w*100:5.1f}%")

        except Exception as e:
            print(f"\n{RED}❌ System Error: {e}{RESET}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(run_demo_interactive())
    except KeyboardInterrupt:
        print("\nGoodbye!")