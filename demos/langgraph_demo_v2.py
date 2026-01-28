"""
🚀 AGENTIC FINANCE DEMO v2.0 - Full Capabilities Test
======================================================

A sophisticated demo for testing all agent capabilities with the real database.

Features:
- Real database connection (no mock portfolio)
- All admin commands (list, update, get_info, etc.)
- Optimization workflows
- Macro analysis
- Clear debug output
- Command shortcuts for quick testing

Usage:
    python demos/langgraph_demo_v2.py

Commands:
    /help     - Show available commands
    /assets   - Quick: List all assets
    /info X   - Quick: Get info on ticker X
    /price X  - Quick: Get latest price for X
    /update X - Quick: Update prices for X
    /macro    - Quick: Market analysis
    /opt      - Quick: Optimize portfolio
    /debug    - Toggle debug mode
    /clear    - Clear screen
    exit      - Quit

Author: Agentic Finance Team
Version: 2.0 (Phase 6.5)
"""

import sys
import os
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Configure Logging (set to WARNING to reduce noise, DEBUG for troubleshooting)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Imports
from agents.graph import get_graph
from agents.state import create_initial_state
from langchain_core.messages import HumanMessage, AIMessage

# Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Global settings
DEBUG_MODE = False


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Print the welcome banner."""
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════╗
║           🏦 AGENTIC FINANCE - PORTFOLIO MANAGER AI v2.0          ║
║                     Full Capabilities Demo                         ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
""")


def print_help():
    """Print help information."""
    print(f"""
{BOLD}{YELLOW}📚 AVAILABLE COMMANDS{RESET}
{DIM}{'─' * 60}{RESET}

{BOLD}Quick Commands (shortcuts):{RESET}
  {GREEN}/assets{RESET}      - List all tracked assets in database
  {GREEN}/info X{RESET}      - Get detailed info for ticker X (e.g., /info AAPL)
  {GREEN}/price X{RESET}     - Get latest price for ticker X
  {GREEN}/update X{RESET}    - Update/fetch prices for ticker X
  {GREEN}/earnings X{RESET}  - Get earnings history for ticker X
  {GREEN}/balance X{RESET}   - Get balance sheet for ticker X
  {GREEN}/macro{RESET}       - Run macro environment analysis
  {GREEN}/opt X,Y,Z{RESET}   - Optimize portfolio with tickers X,Y,Z

  {BOLD}Portfolio Commands:{RESET}
  {GREEN}/portfolios{RESET}   - List all portfolios
  {GREEN}/holdings X{RESET}   - Show holdings in portfolio X (ID or name)
  {GREEN}/summary X{RESET}    - Get summary of portfolio X
  {GREEN}/newportfolio X{RESET} - Create new portfolio named X
  
{BOLD}System Commands:{RESET}
  {BLUE}/debug{RESET}       - Toggle debug mode (verbose output)
  {BLUE}/clear{RESET}       - Clear the screen
  {BLUE}/help{RESET}        - Show this help message
  {BLUE}exit{RESET}         - Quit the application

{BOLD}Natural Language Examples:{RESET}
  {DIM}"Show me all assets in the database"
  "Get info on AAPL"
  "What's the current price of MSFT?"
  "Update prices for SPY and TLT"
  "Show quarterly earnings for NVDA"
  "Get the balance sheet for AAPL"
  "How is the market looking?"
  "Optimize a portfolio with AAPL, MSFT, GOOGL"{RESET}
""")


def print_db_status():
    """Print database connection status and asset count."""
    try:
        from portfolio_tool.database_setup import get_session, Asset
        session = get_session()
        count = session.query(Asset).count()
        session.close()
        print(f"{GREEN}✓ Database connected{RESET} - {count} assets tracked")
    except Exception as e:
        print(f"{RED}✗ Database error: {e}{RESET}")


def handle_shortcut(command: str) -> str:
    """Convert shortcut commands to natural language."""
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""
    
    shortcuts = {
        "/assets": "Show me all assets in the database",
        "/info": f"Get detailed info on {arg}" if arg else "Get info on what ticker?",
        "/price": f"What is the latest price for {arg}?" if arg else "Get price for what ticker?",
        "/update": f"Update prices for {arg}" if arg else "Update prices for what ticker?",
        "/earnings": f"Show quarterly earnings for {arg}" if arg else "Get earnings for what ticker?",
        "/balance": f"Get the balance sheet for {arg}" if arg else "Get balance sheet for what ticker?",
        "/income": f"Get the income statement for {arg}" if arg else "Get income statement for what ticker?",
        "/cashflow": f"Get the cash flow statement for {arg}" if arg else "Get cash flow for what ticker?",
        "/macro": "How is the market looking? Analyze VIX and yield curve.",
        "/opt": f"Optimize a portfolio with {arg}" if arg else "Optimize a portfolio with AAPL, MSFT, GOOGL",
        "/portfolios": "Show me all my portfolios",
        "/holdings": f"Show holdings in portfolio {arg}" if arg else "Show holdings in which portfolio?",
        "/summary": f"Get summary of portfolio {arg}" if arg else "Get summary of which portfolio?",
        "/newportfolio": f"Create a new portfolio called {arg}" if arg else "Create portfolio with what name?",
    }
    
    return shortcuts.get(cmd, shortcuts.get(parts[0].lower().split()[0], command))


async def run_agent(user_input: str, chat_memory: list = None) -> tuple:
    """
    Run the agent graph and return the response.
    
    Args:
        user_input: User's message
        chat_memory: Optional conversation history
        
    Returns:
        Tuple of (ai_response_text, final_state)
    """
    global DEBUG_MODE
    
    # Create state WITHOUT portfolio_id (use real DB, no mock)
    state_input = create_initial_state(user_input, portfolio_id=None)
    
    # Inject memory if provided (for multi-turn conversations)
    if chat_memory:
        current_msg = state_input["messages"][-1]
        state_input["messages"] = chat_memory + [current_msg]
    
    # Get graph
    graph = get_graph()
    
    # Track execution
    final_state = None
    start_time = asyncio.get_event_loop().time()
    
    # Stream execution
    async for event in graph.astream(state_input):
        for node_name, state in event.items():
            elapsed = asyncio.get_event_loop().time() - start_time
            final_state = state
            
            # Print progress
            if node_name == "Router":
                decision = state.get("router_decision", {})
                intent = decision.get("intent", "UNKNOWN")
                agents = decision.get("execution_order", [])
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 🧠 {BOLD}Router:{RESET} intent='{intent}' → {agents}")
                
                if DEBUG_MODE:
                    params = decision.get("parameters", {})
                    print(f"         {DIM}Parameters: {params}{RESET}")
            
            elif node_name == "DataAgent":
                sub = state.get("sub_results", {}).get("DataAgent", {})
                success = sub.get("success", False)
                icon = "✓" if success else "✗"
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 📊 {BOLD}DataAgent:{RESET} {icon}")
            
            elif node_name == "MacroAgent":
                sub = state.get("sub_results", {}).get("MacroAgent", {})
                success = sub.get("success", False)
                icon = "✓" if success else "✗"
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 🌍 {BOLD}MacroAgent:{RESET} {icon}")
            
            elif node_name == "OptimizationAgent":
                sub = state.get("sub_results", {}).get("OptimizationAgent", {})
                success = sub.get("success", False)
                icon = "✓" if success else "✗"
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 🧮 {BOLD}OptimizationAgent:{RESET} {icon}")
            
            elif node_name == "RebalanceAgent":
                sub = state.get("sub_results", {}).get("RebalanceAgent", {})
                success = sub.get("success", False)
                icon = "✓" if success else "✗"
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} ⚖️ {BOLD}RebalanceAgent:{RESET} {icon}")
            
            elif node_name == "BacktestAgent":
                sub = state.get("sub_results", {}).get("BacktestAgent", {})
                success = sub.get("success", False)
                icon = "✓" if success else "✗"
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 📈 {BOLD}BacktestAgent:{RESET} {icon}")
            
            elif node_name == "synthesizer":
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} ✍️ {BOLD}Synthesizer:{RESET} formatting response...")
    
    # Extract response
    ai_response = ""
    if final_state:
        raw_response = final_state.get("final_response")
        
        if raw_response and isinstance(raw_response, dict):
            ai_response = raw_response.get("data", {}).get("summary", "")
            
            if DEBUG_MODE:
                details = raw_response.get("data", {}).get("details", {})
                if details:
                    print(f"\n  {DIM}[Debug] Details: {details}{RESET}")
        
        elif raw_response and isinstance(raw_response, str):
            ai_response = raw_response
        
        elif final_state.get("router_decision", {}).get("intent") == "clarification_needed":
            ai_response = final_state["router_decision"].get("clarification_question", "Could you clarify?")
    
    return ai_response, final_state


async def run_demo():
    """Main demo loop."""
    global DEBUG_MODE
    
    clear_screen()
    print_banner()
    
    # Check database
    print(f"{YELLOW}[System]{RESET} Checking database connection...")
    print_db_status()
    print()
    
    print(f"{DIM}Type /help for commands, 'exit' to quit.{RESET}")
    print(f"{'─' * 60}\n")
    
    # Initialize memory
    chat_memory = []
    
    # Main loop
    while True:
        try:
            # Get input
            user_input = input(f"{BOLD}You:{RESET} ").strip()
            
            # Handle empty input
            if not user_input:
                continue
            
            # Handle exit
            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n{YELLOW}Goodbye! 👋{RESET}")
                break
            
            # Handle system commands
            if user_input.lower() == "/help":
                print_help()
                continue
            
            if user_input.lower() == "/clear":
                clear_screen()
                print_banner()
                continue
            
            if user_input.lower() == "/debug":
                DEBUG_MODE = not DEBUG_MODE
                status = "ON" if DEBUG_MODE else "OFF"
                print(f"{YELLOW}Debug mode: {status}{RESET}\n")
                continue
            
            # Handle shortcuts
            if user_input.startswith("/"):
                converted = handle_shortcut(user_input)
                if "what ticker?" in converted.lower():
                    print(f"{YELLOW}⚠️ Please specify a ticker. Example: {user_input} AAPL{RESET}\n")
                    continue
                print(f"{DIM}→ {converted}{RESET}")
                user_input = converted
            
            # Run agent
            print(f"\n{CYAN}🤖 Processing...{RESET}")
            print(f"{'─' * 40}")
            
            # WITH MEMORY
            # ai_response, final_state = await run_agent(user_input, chat_memory if chat_memory else None)
            # WITHOUT MEMORY
            ai_response, final_state = await run_agent(user_input, None)

            print(f"{'─' * 40}")
            
            # Display response
            if ai_response:
                print(f"\n{GREEN}{BOLD}AI:{RESET}")
                print(ai_response)
            else:
                print(f"\n{RED}No response generated.{RESET}")
                if final_state:
                    errors = final_state.get("errors", [])
                    if errors:
                        print(f"{RED}Errors: {errors}{RESET}")
            
            # Update memory
            chat_memory.append(HumanMessage(content=user_input))
            if ai_response:
                chat_memory.append(AIMessage(content=ai_response))
            
            # Keep memory manageable (last 10 exchanges)
            if len(chat_memory) > 20:
                chat_memory = chat_memory[-20:]
            
            print()
            
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Interrupted. Type 'exit' to quit.{RESET}")
        except Exception as e:
            print(f"\n{RED}❌ Error: {e}{RESET}")
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()
            print()


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nGoodbye!")
