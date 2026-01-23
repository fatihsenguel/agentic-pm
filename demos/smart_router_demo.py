# demos/smart_router_demo.py
"""
Smart Router Demo - Phase 6.1 + 6.12

This demo shows how the Smart Router replaces the old if/else routing
with LLM-based intent detection.

Usage:
    python demos/smart_router_demo.py
"""

import sys
import os
import asyncio
from typing import Dict, Any

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.dirname(current_dir)
sys.path.insert(0, os.path.join(src_path, 'src'))


class SmartRouterDemo:
    """Demonstrates the Smart Router capabilities."""
    
    def __init__(self):
        self._router = None
    
    @property
    def router(self):
        """Lazy load router."""
        if self._router is None:
            from agents.smart_router import create_router, RouterConfig
            config = RouterConfig(
                use_stronger_model=True,
                include_examples=True,
                validate_tickers=True,
            )
            self._router = create_router(config)
        return self._router
    
    async def demo_single_request(self, user_input: str) -> Dict[str, Any]:
        """Route a single request and show results."""
        print(f"\n{'='*60}")
        print(f"INPUT: {user_input}")
        print('='*60)
        
        decision, validation = await self.router.route(user_input)
        
        # Handle intent as string (use_enum_values=True in schema)
        intent_str = decision.intent if isinstance(decision.intent, str) else decision.intent.value
        
        print(f"\nINTENT: {intent_str.upper()}")
        print(f"CONFIDENCE: {decision.confidence:.0%}")
        print(f"MULTI-STEP: {decision.is_multi_step}")
        
        print(f"\nAGENTS NEEDED:")
        for task in decision.agents_needed:
            # Handle agent as string too
            agent_str = task.agent if isinstance(task.agent, str) else task.agent.value
            print(f"  - {agent_str}: {task.task_description}")
        
        # Handle execution_order as list of strings
        exec_order = [a if isinstance(a, str) else a.value for a in decision.execution_order]
        print(f"\nEXECUTION ORDER: {' -> '.join(exec_order)}")
        
        if decision.parameters.tickers:
            print(f"\nTICKERS: {', '.join(decision.parameters.tickers)}")
        
        if decision.parameters.max_volatility:
            print(f"MAX VOL: {decision.parameters.max_volatility:.0%}")
        
        print(f"\nREASONING: {decision.reasoning}")
        
        if validation.errors:
            print(f"\nVALIDATION ERRORS:")
            for err in validation.errors:
                print(f"  ! {err}")
        
        if validation.warnings:
            print(f"\nWARNINGS:")
            for warn in validation.warnings:
                print(f"  ? {warn}")
        
        if decision.clarification_question:
            print(f"\nCLARIFICATION NEEDED:")
            print(f"  {decision.clarification_question}")
        
        return {"decision": decision, "validation": validation}
    
    async def run_demos(self):
        """Run demo with several example requests."""
        examples = [
            "Optimiere mein Portfolio mit SPY, TLT, GLD bei maximal 12% Volatilitaet",
            "Wie ist die aktuelle Marktlage?",
            "Sollte ich bei diesem VIX-Level mehr in Bonds gehen?",
            "Mein Portfolio: SPY 45%, TLT 25%, GLD 20%. Soll 40/30/30 sein.",
            "Backteste die Strategie ueber 5 Jahre",
            "Portfolio",  # Ambiguous - should ask for clarification
        ]
        
        print("\n" + "="*60)
        print("SMART ROUTER DEMO - Phase 6.1")
        print("="*60)
        
        for example in examples:
            try:
                await self.demo_single_request(example)
            except Exception as e:
                print(f"\nERROR: {e}")
            
            print()
        
        # Show stats
        stats = self.router.get_stats()
        print("\n" + "="*60)
        print("ROUTING STATISTICS")
        print("="*60)
        print(f"Total Routes: {stats['total_routes']}")
        print(f"Success Rate: {stats['success_rate']:.0%}")
        print(f"Clarifications: {stats['clarifications_requested']}")
        print(f"Retries Needed: {stats['retries_needed']}")


async def main():
    """Main entry point."""
    demo = SmartRouterDemo()
    await demo.run_demos()


if __name__ == "__main__":
    asyncio.run(main())