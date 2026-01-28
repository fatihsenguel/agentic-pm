"""
🚀 AGENTIC FINANCE DEMO v3.0 - Full RAG + Decision Engine
==========================================================

Complete demo showcasing:
- RAG document search
- Fed sentiment analysis
- PM-style decision summaries
- All existing capabilities

Usage:
    python demos/langgraph_demo_v3.py

NEW Commands:
    /ingest X    - Ingest document X into RAG
    /ingestall   - Ingest all docs in data/documents/
    /fed         - Fetch & analyze latest Fed minutes
    /docs        - List indexed documents
    /search X    - Search documents for X
    /stats       - Show RAG statistics

Author: Agentic Finance Team
Version: 3.0 (Phase 6.7 - RAG Integration)
"""

import sys
import os
import asyncio
import logging

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Configure Logging
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
ACTIVE_PORTFOLIO_ID = 1  # Default portfolio


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Print the welcome banner."""
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════╗
║      🦊 AGENTIC FINANCE - PORTFOLIO MANAGER AI v3.0              ║
║           RAG + Decision Engine + Full Capabilities               ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
""")


def print_help():
    """Print help information."""
    print(f"""
{BOLD}{YELLOW}📚 AVAILABLE COMMANDS{RESET}
{DIM}{'─' * 60}{RESET}

{BOLD}{MAGENTA}📄 RAG / Document Commands (NEW!):{RESET}
  {GREEN}/ingest X{RESET}    - Ingest document X into RAG system
  {GREEN}/ingestall{RESET}   - Ingest all docs from data/documents/
  {GREEN}/fed{RESET}         - Fetch & analyze latest Fed minutes
  {GREEN}/docs{RESET}        - List all indexed documents
  {GREEN}/search X{RESET}    - Search documents for query X
  {GREEN}/stats{RESET}       - Show RAG statistics
  {GREEN}/sentiment X{RESET} - Analyze sentiment of text X

{BOLD}📊 Data Commands:{RESET}
  {GREEN}/assets{RESET}      - List all tracked assets
  {GREEN}/info X{RESET}      - Get detailed info for ticker X
  {GREEN}/price X{RESET}     - Get latest price for ticker X
  {GREEN}/macro{RESET}       - Run macro environment analysis

{BOLD}💼 Portfolio Commands:{RESET}
  {GREEN}/portfolios{RESET}  - List all portfolios
  {GREEN}/holdings X{RESET}  - Show holdings in portfolio X
  {GREEN}/use X{RESET}       - Set active portfolio to X (for decisions)
  {GREEN}/opt{RESET}         - Optimize active portfolio
  {GREEN}/rebalance{RESET}   - Check if rebalancing needed

{BOLD}🔧 System Commands:{RESET}
  {BLUE}/debug{RESET}       - Toggle debug mode
  {BLUE}/clear{RESET}       - Clear screen
  {BLUE}/help{RESET}        - Show this help
  {BLUE}exit{RESET}         - Quit

{BOLD}{CYAN}🎯 INTERVIEW-READY PROMPTS:{RESET}
{DIM}  "Based on NVIDIA's 10-K, what are the main risk factors?"
  "Given the Fed's hawkish stance, should I reduce equity exposure?"
  "Should I rebalance my portfolio? Show me the analysis."
  "Markets dropped 4% today. Should I sell or hold?"{RESET}
""")


def print_db_status():
    """Print database connection status."""
    try:
        from portfolio_tool.database_setup import get_session, Asset
        session = get_session()
        count = session.query(Asset).count()
        session.close()
        print(f"{GREEN}✓ Database:{RESET} {count} assets tracked")
    except Exception as e:
        print(f"{RED}✗ Database error: {e}{RESET}")


def print_rag_status():
    """Print RAG system status."""
    try:
        from portfolio_tool.rag import get_document_manager
        dm = get_document_manager()
        stats = dm.get_stats()
        doc_count = len(dm.list_documents())
        chunk_count = stats.get("total_chunks", 0)
        print(f"{GREEN}✓ RAG System:{RESET} {doc_count} documents, {chunk_count} chunks indexed")
    except Exception as e:
        print(f"{YELLOW}⚠ RAG System: Not initialized ({e}){RESET}")


# =============================================================================
# RAG COMMANDS
# =============================================================================

def cmd_ingest(filepath: str):
    """Ingest a document into RAG."""
    try:
        from portfolio_tool.rag import get_document_manager
        dm = get_document_manager()
        
        # Handle relative paths
        if not os.path.isabs(filepath):
            filepath = os.path.join("data/documents", filepath)
        
        print(f"{CYAN}Ingesting: {filepath}{RESET}")
        result = dm.ingest(filepath)
        
        if result.success:
            if result.skipped:
                print(f"{YELLOW}⚠ Already indexed (skipped){RESET}")
            else:
                print(f"{GREEN}✓ Ingested: {result.chunk_count} chunks{RESET}")
                print(f"  Ticker: {result.ticker or 'Auto-detected'}")
                print(f"  Doc ID: {result.doc_id[:16]}...")
        else:
            print(f"{RED}✗ Failed: {result.error}{RESET}")
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")


def cmd_ingest_all():
    """Ingest all documents from folder."""
    try:
        from portfolio_tool.rag import get_document_manager
        dm = get_document_manager()
        
        print(f"{CYAN}Ingesting all documents from data/documents/...{RESET}")
        results = dm.ingest_folder()
        
        success = sum(1 for r in results if r.success and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)
        failed = sum(1 for r in results if not r.success)
        
        print(f"{GREEN}✓ Added: {success}{RESET}")
        print(f"{YELLOW}⚠ Skipped: {skipped}{RESET}")
        if failed:
            print(f"{RED}✗ Failed: {failed}{RESET}")
            for r in results:
                if not r.success:
                    print(f"  - {r.filepath}: {r.error}")
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")


def cmd_fed():
    """Fetch and analyze Fed minutes."""
    try:
        from portfolio_tool.rag import get_document_manager
        dm = get_document_manager()
        
        print(f"{CYAN}Fetching latest Fed minutes...{RESET}")
        result = dm.ingest_fed_minutes()
        
        if result.success:
            print(f"{GREEN}✓ Fed minutes indexed{RESET}")
            
            # Run sentiment analysis
            from portfolio_tool.rag import FedSentimentAnalyzer
            
            # Read the file we just created
            docs = dm.list_documents()
            fed_docs = [d for d in docs if "fed" in d.get("filename", "").lower()]
            
            if fed_docs:
                print(f"\n{CYAN}Analyzing sentiment...{RESET}")
                # Search for Fed content
                results = dm.search("monetary policy inflation", top_k=3)
                if results:
                    text = " ".join([r["content"] for r in results])
                    analyzer = FedSentimentAnalyzer()
                    sentiment = analyzer.analyze(text)
                    
                    score = sentiment.get("score", 0)
                    conf = sentiment.get("confidence", 0)
                    method = sentiment.get("method", "unknown")
                    
                    stance = "🦅 HAWKISH" if score > 0.3 else "🕊️ DOVISH" if score < -0.3 else "➡️ NEUTRAL"
                    
                    print(f"\n{BOLD}Fed Sentiment:{RESET}")
                    print(f"  Stance: {stance}")
                    print(f"  Score: {score:+.2f} (-1 dovish to +1 hawkish)")
                    print(f"  Confidence: {conf:.0%}")
                    print(f"  Method: {method}")
        else:
            print(f"{RED}✗ Failed: {result.error}{RESET}")
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")


def cmd_docs():
    """List indexed documents."""
    try:
        from portfolio_tool.rag import get_document_manager
        dm = get_document_manager()
        
        docs = dm.list_documents()
        
        if not docs:
            print(f"{YELLOW}No documents indexed yet.{RESET}")
            print(f"{DIM}Use /ingest <file> or /ingestall to add documents.{RESET}")
            return
        
        print(f"\n{BOLD}📄 Indexed Documents ({len(docs)}):{RESET}")
        print(f"{'─' * 50}")
        
        for doc in docs:
            filename = doc.get("filename", "Unknown")
            ticker = doc.get("ticker", "-")
            chunks = doc.get("chunk_count", "?")
            print(f"  • {filename}")
            print(f"    Ticker: {ticker} | Chunks: {chunks}")
        
        print()
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")


def cmd_search(query: str):
    """Search documents."""
    try:
        from portfolio_tool.rag import get_document_manager
        dm = get_document_manager()
        
        print(f"{CYAN}Searching for: '{query}'{RESET}\n")
        results = dm.search(query, top_k=5)
        
        if not results:
            print(f"{YELLOW}No results found.{RESET}")
            return
        
        print(f"{BOLD}🔍 Search Results ({len(results)}):{RESET}")
        print(f"{'─' * 50}")
        
        for i, r in enumerate(results, 1):
            score = r.get("score", 0)
            content = r.get("content", "")[:150]
            source = r.get("citation", r.get("filename", "Unknown"))
            
            print(f"\n{BOLD}[{i}] Score: {score:.2f}{RESET}")
            print(f"    {DIM}{content}...{RESET}")
            print(f"    📎 {source}")
        
        print()
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")


def cmd_stats():
    """Show RAG statistics."""
    try:
        from portfolio_tool.rag import get_document_manager
        dm = get_document_manager()
        
        stats = dm.get_stats()
        
        print(f"\n{BOLD}📊 RAG Statistics:{RESET}")
        print(f"{'─' * 40}")
        print(f"  Documents indexed: {len(dm.list_documents())}")
        print(f"  Total chunks: {stats.get('total_chunks', 0)}")
        print(f"  Unique tickers: {len(stats.get('tickers', []))}")
        print(f"  Document types: {stats.get('doc_types', [])}")
        print(f"  Documents folder: {stats.get('documents_dir', 'N/A')}")
        print()
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")


def cmd_sentiment(text: str):
    """Analyze text sentiment."""
    try:
        from portfolio_tool.rag import FedSentimentAnalyzer
        
        analyzer = FedSentimentAnalyzer()
        result = analyzer.analyze(text)
        
        score = result.get("score", 0)
        conf = result.get("confidence", 0)
        method = result.get("method", "unknown")
        signals = result.get("signals", [])
        
        stance = "🦅 HAWKISH" if score > 0.3 else "🕊️ DOVISH" if score < -0.3 else "➡️ NEUTRAL"
        
        print(f"\n{BOLD}Sentiment Analysis:{RESET}")
        print(f"  Stance: {stance}")
        print(f"  Score: {score:+.2f}")
        print(f"  Confidence: {conf:.0%}")
        print(f"  Method: {method}")
        if signals:
            print(f"  Signals: {', '.join(signals[:5])}")
        print()
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")


# =============================================================================
# SHORTCUT HANDLER
# =============================================================================

def handle_shortcut(command: str) -> str:
    """Convert shortcut commands to natural language or execute directly."""
    global ACTIVE_PORTFOLIO_ID
    
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""
    
    # RAG commands (execute directly, return None)
    if cmd == "/ingest":
        if arg:
            cmd_ingest(arg)
        else:
            print(f"{YELLOW}Usage: /ingest <filename>{RESET}")
        return None
    
    if cmd == "/ingestall":
        cmd_ingest_all()
        return None
    
    if cmd == "/fed":
        cmd_fed()
        return None
    
    if cmd == "/docs":
        cmd_docs()
        return None
    
    if cmd == "/search":
        if arg:
            cmd_search(arg)
        else:
            print(f"{YELLOW}Usage: /search <query>{RESET}")
        return None
    
    if cmd == "/stats":
        cmd_stats()
        return None
    
    if cmd == "/sentiment":
        if arg:
            cmd_sentiment(arg)
        else:
            print(f"{YELLOW}Usage: /sentiment <text>{RESET}")
        return None
    
    if cmd == "/use":
        if arg:
            try:
                ACTIVE_PORTFOLIO_ID = int(arg)
                print(f"{GREEN}✓ Active portfolio set to {ACTIVE_PORTFOLIO_ID}{RESET}")
            except:
                print(f"{YELLOW}Usage: /use <portfolio_id>{RESET}")
        else:
            print(f"Current active portfolio: {ACTIVE_PORTFOLIO_ID}")
        return None
    
    # Convert to natural language
    shortcuts = {
        "/assets": "Show me all assets in the database",
        "/info": f"Get detailed info on {arg}" if arg else None,
        "/price": f"What is the latest price for {arg}?" if arg else None,
        "/update": f"Update prices for {arg}" if arg else None,
        "/macro": "How is the market looking? Analyze VIX and yield curve.",
        "/opt": f"Optimize my portfolio" if not arg else f"Optimize a portfolio with {arg}",
        "/rebalance": "Should I rebalance my portfolio? Check drift and recommend.",
        "/portfolios": "Show me all my portfolios",
        "/holdings": f"Show holdings in portfolio {arg}" if arg else None,
        "/summary": f"Get summary of portfolio {arg}" if arg else None,
    }
    
    result = shortcuts.get(cmd)
    if result is None and cmd in shortcuts:
        print(f"{YELLOW}Please specify an argument. Example: {cmd} AAPL{RESET}")
        return None
    
    return result if result else command


# =============================================================================
# AGENT RUNNER
# =============================================================================

async def run_agent(user_input: str, portfolio_id: int = None) -> tuple:
    """Run the agent graph and return the response."""
    global DEBUG_MODE
    
    # Create state with portfolio context
    state_input = create_initial_state(user_input, portfolio_id=portfolio_id)
    
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
                query_intent = decision.get("query_intent", "?")
                exec_intent = decision.get("execution_intent", decision.get("intent", "?"))
                agents = decision.get("execution_order", [])
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 🧠 {BOLD}Router:{RESET} {query_intent}/{exec_intent} → {agents}")
            
            elif node_name == "DataAgent":
                sub = state.get("sub_results", {}).get("DataAgent", {})
                icon = "✓" if sub.get("success") else "✗"
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 📊 {BOLD}DataAgent:{RESET} {icon}")
            
            elif node_name == "RAGAgent":
                sub = state.get("sub_results", {}).get("RAGAgent", {})
                icon = "✓" if sub.get("success") else "✗"
                sources = len(sub.get("sources", []))
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 📄 {BOLD}RAGAgent:{RESET} {icon} ({sources} sources)")
            
            elif node_name == "MacroAgent":
                sub = state.get("sub_results", {}).get("MacroAgent", {})
                icon = "✓" if sub.get("success") else "✗"
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 🌍 {BOLD}MacroAgent:{RESET} {icon}")
            
            elif node_name == "OptimizationAgent":
                sub = state.get("sub_results", {}).get("OptimizationAgent", {})
                icon = "✓" if sub.get("success") else "✗"
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 🧮 {BOLD}OptimizationAgent:{RESET} {icon}")
            
            elif node_name == "RebalanceAgent":
                sub = state.get("sub_results", {}).get("RebalanceAgent", {})
                icon = "✓" if sub.get("success") else "✗"
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} ⚖️ {BOLD}RebalanceAgent:{RESET} {icon}")
            
            elif node_name == "BacktestAgent":
                sub = state.get("sub_results", {}).get("BacktestAgent", {})
                icon = "✓" if sub.get("success") else "✗"
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} 📈 {BOLD}BacktestAgent:{RESET} {icon}")
            
            elif node_name == "synthesizer":
                print(f"  {DIM}[{elapsed:.1f}s]{RESET} ✍️ {BOLD}Synthesizer:{RESET} formatting...")
    
    # Extract response
    ai_response = ""
    if final_state:
        raw_response = final_state.get("final_response")
        
        if raw_response and isinstance(raw_response, dict):
            ai_response = raw_response.get("data", {}).get("summary", "")
            
            if DEBUG_MODE:
                details = raw_response.get("data", {}).get("details", {})
                if details:
                    print(f"\n  {DIM}[Debug] Details: {list(details.keys())}{RESET}")
        
        elif raw_response and isinstance(raw_response, str):
            ai_response = raw_response
        
        elif final_state.get("router_decision", {}).get("intent") == "clarification_needed":
            ai_response = final_state["router_decision"].get("clarification_question", "Could you clarify?")
    
    return ai_response, final_state


# =============================================================================
# MAIN LOOP
# =============================================================================

async def run_demo():
    """Main demo loop."""
    global DEBUG_MODE, ACTIVE_PORTFOLIO_ID
    
    clear_screen()
    print_banner()
    
    # Check systems
    print(f"{YELLOW}[System]{RESET} Checking connections...")
    print_db_status()
    print_rag_status()
    print(f"{GREEN}✓ Active Portfolio:{RESET} {ACTIVE_PORTFOLIO_ID}")
    print()
    
    print(f"{DIM}Type /help for commands, 'exit' to quit.{RESET}")
    print(f"{'─' * 60}\n")
    
    # Main loop
    while True:
        try:
            user_input = input(f"{BOLD}You:{RESET} ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n{YELLOW}Goodbye! 👋{RESET}")
                break
            
            if user_input.lower() == "/help":
                print_help()
                continue
            
            if user_input.lower() == "/clear":
                clear_screen()
                print_banner()
                continue
            
            if user_input.lower() == "/debug":
                DEBUG_MODE = not DEBUG_MODE
                print(f"{YELLOW}Debug mode: {'ON' if DEBUG_MODE else 'OFF'}{RESET}\n")
                continue
            
            # Handle shortcuts
            if user_input.startswith("/"):
                converted = handle_shortcut(user_input)
                if converted is None:
                    # Command was executed directly
                    continue
                print(f"{DIM}→ {converted}{RESET}")
                user_input = converted
            
            # Run agent
            print(f"\n{CYAN}🤖 Processing...{RESET}")
            print(f"{'─' * 40}")
            
            ai_response, final_state = await run_agent(user_input, ACTIVE_PORTFOLIO_ID)
            
            print(f"{'─' * 40}")
            
            if ai_response:
                print(f"\n{GREEN}{BOLD}AI:{RESET}")
                print(ai_response)
            else:
                print(f"\n{RED}No response generated.{RESET}")
                if final_state:
                    errors = final_state.get("errors", [])
                    if errors:
                        print(f"{RED}Errors: {errors}{RESET}")
            
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
