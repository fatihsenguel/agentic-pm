# demos/langgraph_demo.py
"""
LangGraph Demo - Phase 6.2

This demo shows the full multi-agent orchestration using LangGraph.
The Smart Router determines which agents to call, and LangGraph
executes them in the correct order.

Usage:
    python demos/langgraph_demo.py

Example flow:
    User: "Optimiere mein Portfolio mit SPY, TLT, GLD"
    
    1. Router detects: OPTIMIZATION
    2. Router plans: DataAgent -> OptimizationAgent
    3. LangGraph executes:
       - DataAgent fetches prices, calculates covariance
       - OptimizationAgent runs mean-variance optimization
    4. Synthesizer creates final response
"""

import sys
import os
import asyncio
from datetime import datetime

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.dirname(current_dir)
sys.path.insert(0, os.path.join(src_path, 'src'))


class LangGraphDemo:
    """Demonstrates the LangGraph multi-agent system."""
    
    def __init__(self):
        self._graph = None
    
    @property
    def graph(self):
        """Lazy load graph."""
        if self._graph is None:
            from agents.graph import get_graph
            self._graph = get_graph()
        return self._graph
    
    def print_header(self):
        """Print demo header."""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║           🏦 LANGGRAPH MULTI-AGENT DEMO - Phase 6.2              ║
║                  Full Agent Orchestration                         ║
╠══════════════════════════════════════════════════════════════════╣
║  Graph Flow:                                                      ║
║    Router → Dispatcher → [Agents...] → Synthesizer → Response    ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    async def run_with_streaming(self, user_message: str):
        """Run the graph with streaming to show progress."""
        from agents.graph import stream_agent_graph
        from agents.state import create_initial_state
        
        print(f"\n{'='*60}")
        print(f"INPUT: {user_message}")
        print('='*60)
        
        print("\n📊 EXECUTION TRACE:")
        print("-" * 40)
        
        start_time = datetime.now()
        final_state = None
        
        async for node_name, state in stream_agent_graph(user_message):
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Format node output
            if node_name == "router":
                decision = state.get("router_decision", {})
                intent = decision.get("intent", "unknown")
                agents = decision.get("execution_order", [])
                print(f"  [{elapsed:.1f}s] 🎯 Router: {intent.upper()}")
                if agents:
                    print(f"           Plan: {' → '.join(agents)}")
            
            elif node_name == "dispatcher":
                current = state.get("current_agent", "none")
                print(f"  [{elapsed:.1f}s] 📋 Dispatcher → {current}")
            
            elif node_name.endswith("_agent"):
                agent_name = node_name.replace("_agent", "").title() + "Agent"
                result = state.get("sub_results", {}).get(agent_name, {})
                success = "✓" if result.get("success") else "✗"
                mock = " (mock)" if result.get("mock") else ""
                print(f"  [{elapsed:.1f}s] 🤖 {agent_name}: {success}{mock}")
            
            elif node_name == "synthesizer":
                print(f"  [{elapsed:.1f}s] 📝 Synthesizer: Creating response...")
            
            final_state = state
        
        total_time = (datetime.now() - start_time).total_seconds()
        print("-" * 40)
        print(f"  Total time: {total_time:.1f}s")
        
        # Print final response
        if final_state:
            response = final_state.get("final_response", "No response generated")
            print(f"\n{'='*60}")
            print("RESPONSE:")
            print('='*60)
            print(response)
        
        return final_state
    
    async def run_demos(self):
        """Run demo with several example requests."""
        self.print_header()
        
        examples = [
            "Wie ist die aktuelle Marktlage?",
            "Optimiere mein Portfolio mit SPY, TLT, GLD bei maximal 15% Volatilitaet",
            "Sollte ich bei diesem VIX-Level mehr in Bonds gehen?",
            "Backteste die Strategie ueber 3 Jahre",
        ]
        
        for example in examples:
            try:
                await self.run_with_streaming(example)
            except Exception as e:
                print(f"\n❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n")
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        print("\n" + "="*60)
        print("Demo complete!")
        print("="*60)


async def interactive_mode():
    """Run in interactive mode."""
    demo = LangGraphDemo()
    demo.print_header()
    
    print("Interactive mode. Type 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            await demo.run_with_streaming(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LangGraph Multi-Agent Demo")
    parser.add_argument("--interactive", "-i", action="store_true", 
                        help="Run in interactive mode")
    parser.add_argument("--message", "-m", type=str, 
                        help="Run with a single message")
    args = parser.parse_args()
    
    demo = LangGraphDemo()
    
    if args.message:
        demo.print_header()
        await demo.run_with_streaming(args.message)
    elif args.interactive:
        await interactive_mode()
    else:
        await demo.run_demos()


if __name__ == "__main__":
    asyncio.run(main())
