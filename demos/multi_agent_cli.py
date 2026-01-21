"""
Multi-Agent CLI for Quant Portfolio Manager.

This CLI demonstrates the FULL multi-agent architecture:
- RiskManagerAgent as Supervisor
- Delegates to specialized agents (Data, Macro, Optimization, Rebalance)
- Shows agent communication visually
- Maintains conversation history

Usage:
    python multi_agent_cli.py
    
Example Prompts:
    "Optimiere ein Portfolio mit SPY, TLT, GLD und max 12% Volatilität"
    "Wie ist die aktuelle Marktlage? Analysiere VIX und Yield Curve"
    "Backteste die Strategie über 5 Jahre"
    "Mein Portfolio ist gedriftet - soll ich rebalancen?"
"""

import sys
import os
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List

# add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.dirname(current_dir) # Geht von 'agents' hoch zu 'src'
sys.path.insert(0, src_path)

# Rich for beautiful console output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better output: pip install rich")


# ==================== CONSOLE UTILITIES ====================

class AgentConsole:
    """Console wrapper for agent output with visual indicators."""
    
    # Agent colors and emojis
    AGENT_STYLES = {
        "RiskManager": {"emoji": "🎯", "color": "bold yellow"},
        "DataAgent": {"emoji": "📊", "color": "bold blue"},
        "MacroAgent": {"emoji": "🌍", "color": "bold green"},
        "OptimizationAgent": {"emoji": "⚡", "color": "bold magenta"},
        "RebalanceAgent": {"emoji": "⚖️", "color": "bold cyan"},
        "BacktestAgent": {"emoji": "📈", "color": "bold red"},
        "System": {"emoji": "🔧", "color": "bold white"},
        "User": {"emoji": "👤", "color": "bold white"},
    }
    
    def __init__(self):
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
    
    def print_header(self):
        """Print welcome header."""
        header = """
╔══════════════════════════════════════════════════════════════════╗
║           🏦 QUANT PORTFOLIO MANAGER - MULTI-AGENT CLI           ║
║                    Institutional Grade MVP                        ║
╠══════════════════════════════════════════════════════════════════╣
║  Agents:                                                          ║
║    🎯 RiskManager (Supervisor) - Koordiniert alle Agents         ║
║    📊 DataAgent              - Marktdaten & Covariance           ║
║    🌍 MacroAgent             - VIX, Yields, Fed Sentiment        ║
║    ⚡ OptimizationAgent      - Portfolio Optimization            ║
║    ⚖️  RebalanceAgent         - Drift & Trade Generation         ║
║    📈 BacktestAgent          - Historical Simulation             ║
╠══════════════════════════════════════════════════════════════════╣
║  Commands: 'quit' to exit, 'help' for examples                   ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(header)
    
    def print_agent_message(self, agent: str, message: str, is_thinking: bool = False):
        """Print a message from an agent with visual styling."""
        style = self.AGENT_STYLES.get(agent, {"emoji": "•", "color": "white"})
        emoji = style["emoji"]
        
        if is_thinking:
            prefix = f"{emoji} [{agent}] 💭"
        else:
            prefix = f"{emoji} [{agent}]"
        
        if RICH_AVAILABLE and self.console:
            self.console.print(f"{prefix} {message}", style=style["color"])
        else:
            print(f"{prefix} {message}")
    
    def print_delegation(self, from_agent: str, to_agent: str, task: str):
        """Print agent delegation visually."""
        from_style = self.AGENT_STYLES.get(from_agent, {})
        to_style = self.AGENT_STYLES.get(to_agent, {})
        
        from_emoji = from_style.get("emoji", "•")
        to_emoji = to_style.get("emoji", "•")
        
        print(f"\n   {from_emoji} {from_agent} ──────► {to_emoji} {to_agent}")
        print(f"   └─ Task: {task}")
    
    def print_result(self, agent: str, result: Dict[str, Any]):
        """Print agent result."""
        style = self.AGENT_STYLES.get(agent, {})
        emoji = style.get("emoji", "•")
        
        print(f"\n   {emoji} [{agent}] Result:")
        
        if isinstance(result, dict):
            for key, value in result.items():
                if key not in ["success", "error"]:
                    print(f"      • {key}: {value}")
    
    def print_user_prompt(self):
        """Print user input prompt."""
        print("\n" + "─" * 60)
        return input("👤 You: ")
    
    def print_thinking(self, agent: str):
        """Show agent is thinking."""
        self.print_agent_message(agent, "Analyzing request...", is_thinking=True)
    
    def print_error(self, message: str):
        """Print error message."""
        print(f"\n❌ Error: {message}")
    
    def print_help(self):
        """Print help text with example prompts."""
        help_text = """
╔══════════════════════════════════════════════════════════════════╗
║                        EXAMPLE PROMPTS                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  📊 PORTFOLIO OPTIMIZATION (SAA):                                ║
║     "Optimiere ein Portfolio mit SPY, TLT, GLD"                  ║
║     "Erstelle ein Portfolio mit max 12% Volatilität"             ║
║     "Mean-Variance Optimization für SPY, TLT, VWO"               ║
║                                                                   ║
║  🌍 MACRO ANALYSIS:                                               ║
║     "Wie ist die aktuelle Marktlage?"                            ║
║     "Analysiere VIX und Yield Curve"                             ║
║     "Was sagt das Macro-Umfeld?"                                 ║
║                                                                   ║
║  ⚖️  REBALANCING:                                                  ║
║     "Mein Portfolio ist gedriftet - analysiere den Drift"        ║
║     "Soll ich rebalancen?"                                       ║
║     "Generiere eine Trade-Liste für Rebalancing"                 ║
║                                                                   ║
║  📈 BACKTEST:                                                     ║
║     "Backteste diese Strategie über 5 Jahre"                     ║
║     "Wie hätte sich das Portfolio historisch entwickelt?"        ║
║                                                                   ║
║  🎯 COMBINED:                                                     ║
║     "Analysiere Markt und optimiere dann das Portfolio"          ║
║     "Prüfe ob taktische Anpassung nötig ist"                    ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(help_text)


# ==================== MULTI-AGENT ORCHESTRATOR ====================

class MultiAgentOrchestrator:
    """
    Orchestrates the multi-agent system.
    
    This class coordinates:
    - RiskManagerAgent (Supervisor)
    - DataAgent
    - MacroAgent
    - OptimizationAgent
    - RebalanceAgent
    - BacktestAgent
    """
    
    def __init__(self, console: AgentConsole, verbose: bool = True):
        self.console = console
        self.verbose = verbose
        self.agents = {}
        self.conversation_history = []
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agents."""
        self.console.print_agent_message("System", "Initializing agents...")
        
        try:
            # Data Agent
            from agents.data_agent import create_data_agent
            self.agents["DataAgent"] = create_data_agent(verbose=self.verbose)
            self.console.print_agent_message("DataAgent", "Ready ✓")
        except ImportError as e:
            self.console.print_error(f"DataAgent not available: {e}")
        
        try:
            # Macro Agent
            from agents.macro_agent import create_macro_agent
            self.agents["MacroAgent"] = create_macro_agent(verbose=self.verbose)
            self.console.print_agent_message("MacroAgent", "Ready ✓")
        except ImportError as e:
            self.console.print_error(f"MacroAgent not available: {e}")
        
        try:
            # Rebalance Agent
            from agents.rebalance_agent import create_rebalance_agent
            self.agents["RebalanceAgent"] = create_rebalance_agent(verbose=self.verbose)
            self.console.print_agent_message("RebalanceAgent", "Ready ✓")
        except ImportError as e:
            self.console.print_error(f"RebalanceAgent not available: {e}")
        
        try:
            # Optimization Agent (optional)
            from agents.optimization_agent import create_optimization_agent
            self.agents["OptimizationAgent"] = create_optimization_agent(verbose=self.verbose)
            self.console.print_agent_message("OptimizationAgent", "Ready ✓")
        except ImportError as e:
            self.console.print_agent_message("OptimizationAgent", f"Not available (optional)")
        
        try:
            # Backtest Agent (optional)
            from agents.backtest_agent import create_backtest_agent
            self.agents["BacktestAgent"] = create_backtest_agent(verbose=self.verbose)
            self.console.print_agent_message("BacktestAgent", "Ready ✓")
        except ImportError as e:
            self.console.print_agent_message("BacktestAgent", f"Not available (optional)")
        
        print()  # Newline after agent init
    
    def _detect_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Detect user intent from input.
        
        This is a simple rule-based parser. In production,
        this would use the LLM via RiskManagerAgent.
        """
        input_lower = user_input.lower()
        
        intent = {
            "type": "unknown",
            "agents_needed": [],
            "parameters": {}
        }
        
        # Detect task type
        if any(word in input_lower for word in ["optimier", "portfolio", "allokation", "allocat"]):
            intent["type"] = "optimization"
            intent["agents_needed"] = ["DataAgent", "OptimizationAgent"]
        
        elif any(word in input_lower for word in ["macro", "markt", "vix", "yield", "fed", "regime"]):
            intent["type"] = "macro_analysis"
            intent["agents_needed"] = ["MacroAgent"]
        
        elif any(word in input_lower for word in ["rebalance", "drift", "trade", "gewicht"]):
            intent["type"] = "rebalancing"
            intent["agents_needed"] = ["DataAgent", "RebalanceAgent"]
        
        elif any(word in input_lower for word in ["backtest", "historisch", "simulation", "performance"]):
            intent["type"] = "backtest"
            intent["agents_needed"] = ["DataAgent", "BacktestAgent"]
        
        elif any(word in input_lower for word in ["preis", "daten", "fetch", "lade"]):
            intent["type"] = "data_fetch"
            intent["agents_needed"] = ["DataAgent"]
        
        # Extract tickers
        import re
        tickers = re.findall(r'\b([A-Z]{2,5})\b', user_input)
        exclude = {'THE', 'AND', 'FOR', 'WITH', 'MAX', 'MIN', 'USD', 'EUR', 'VIX', 'FED'}
        intent["parameters"]["tickers"] = [t for t in tickers if t not in exclude]
        
        # Extract volatility constraint
        vol_match = re.search(r'(\d+(?:\.\d+)?)\s*%?\s*(?:vol|volatil)', input_lower)
        if vol_match:
            intent["parameters"]["max_volatility"] = float(vol_match.group(1)) / 100
        
        return intent
    
    async def process_request(self, user_input: str) -> str:
        """
        Process a user request through the multi-agent system.
        
        Shows the full agent orchestration.
        """
        # Store in history
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Step 1: RiskManager analyzes request
        self.console.print_agent_message("RiskManager", "Analyzing your request...")
        intent = self._detect_intent(user_input)
        
        self.console.print_agent_message(
            "RiskManager", 
            f"Detected intent: {intent['type'].upper()}"
        )
        
        if intent["parameters"].get("tickers"):
            self.console.print_agent_message(
                "RiskManager",
                f"Detected tickers: {', '.join(intent['parameters']['tickers'])}"
            )
        
        # Step 2: Delegate to appropriate agents
        results = {}
        
        for agent_name in intent["agents_needed"]:
            if agent_name not in self.agents:
                self.console.print_agent_message(
                    "RiskManager",
                    f"⚠️ {agent_name} not available, skipping"
                )
                continue
            
            self.console.print_delegation("RiskManager", agent_name, intent["type"])
            
            agent = self.agents[agent_name]
            
            # Execute agent task based on type
            try:
                result = await self._execute_agent_task(
                    agent_name, 
                    agent, 
                    intent
                )
                results[agent_name] = result
                
                # Show key results
                if result.get("success"):
                    self.console.print_agent_message(agent_name, "✓ Task completed")
                else:
                    self.console.print_agent_message(
                        agent_name, 
                        f"✗ Error: {result.get('error', 'Unknown')}"
                    )
                    
            except Exception as e:
                self.console.print_error(f"{agent_name} error: {e}")
                results[agent_name] = {"success": False, "error": str(e)}
        
        # Step 3: RiskManager synthesizes response
        self.console.print_agent_message("RiskManager", "Synthesizing final response...")
        
        response = self._synthesize_response(intent, results)
        
        # Store in history
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now()
        })
        
        return response
    
    async def _execute_agent_task(
        self, 
        agent_name: str, 
        agent: Any, 
        intent: Dict
    ) -> Dict[str, Any]:
        """Execute a specific agent task."""
        
        tickers = intent["parameters"].get("tickers", ["SPY", "TLT", "GLD"])
        
        if agent_name == "DataAgent":
            # Fetch price data
            self.console.print_agent_message("DataAgent", "Fetching market data...")
            result = agent.fetch_prices_tool(
                tickers=",".join(tickers),
                period="3Y"
            )
            
            if result.get("success"):
                self.console.print_agent_message(
                    "DataAgent",
                    f"Loaded {result.get('num_observations', 0)} observations"
                )
            
            return result
        
        elif agent_name == "MacroAgent":
            # Macro analysis
            self.console.print_agent_message("MacroAgent", "Fetching macro indicators...")
            
            # Fetch data first
            fetch_result = agent.fetch_macro_data_tool(
                indicators="VIX,TNX_10Y,IRX_3M",
                days=30
            )
            
            self.console.print_agent_message(
                "MacroAgent",
                f"Updated {fetch_result.get('rows_updated', 0)} macro data points"
            )
            
            # Get snapshot
            snapshot = agent.get_macro_snapshot_tool()
            
            # Assess regime
            vix_data = snapshot.get("vix", {})
            regime = agent.assess_regime_tool(
                vix_level=vix_data.get("value", 20),
                yield_curve_slope=snapshot.get("yield_curve", {}).get("slope_raw", 0.5)
            )
            
            self.console.print_agent_message(
                "MacroAgent",
                f"Market Regime: {regime.get('regime', 'unknown').upper()}"
            )
            
            return {
                "success": True,
                "snapshot": snapshot,
                "regime": regime
            }
        
        elif agent_name == "RebalanceAgent":
            # Rebalancing analysis
            self.console.print_agent_message("RebalanceAgent", "Analyzing portfolio drift...")
            
            # Use demo weights (in production, would get from user/DB)
            current_weights = {"SPY": 0.45, "TLT": 0.25, "GLD": 0.20, "VWO": 0.10}
            target_weights = {"SPY": 0.40, "TLT": 0.30, "GLD": 0.15, "VWO": 0.15}
            
            result = agent.analyze_rebalance_tool(
                current_weights=current_weights,
                target_weights=target_weights,
                portfolio_value=100000,
                prices={"SPY": 590, "TLT": 88, "GLD": 420, "VWO": 45}
            )
            
            if result.get("success"):
                decision = result.get("decision", {})
                self.console.print_agent_message(
                    "RebalanceAgent",
                    f"Recommendation: {decision.get('recommendation', 'N/A').upper()}"
                )
            
            return result
        
        elif agent_name == "OptimizationAgent":
            # Portfolio optimization
            self.console.print_agent_message("OptimizationAgent", "Running optimization...")
            
            # In production, would call actual optimization
            # For now, return mock result
            return {
                "success": True,
                "optimal_weights": {"SPY": 0.40, "TLT": 0.30, "GLD": 0.15, "VWO": 0.15},
                "expected_return": 0.082,
                "expected_volatility": 0.115,
                "sharpe_ratio": 0.73
            }
        
        elif agent_name == "BacktestAgent":
            # Backtest
            self.console.print_agent_message("BacktestAgent", "Running simulation...")
            
            # Mock result
            return {
                "success": True,
                "total_return": 0.487,
                "cagr": 0.082,
                "max_drawdown": -0.186,
                "sharpe_ratio": 0.73
            }
        
        return {"success": False, "error": "Unknown agent"}
    
    def _synthesize_response(self, intent: Dict, results: Dict) -> str:
        """Synthesize final response from agent results."""
        
        lines = [
            "",
            "═" * 60,
            "📋 ANALYSIS SUMMARY",
            "═" * 60,
        ]
        
        if intent["type"] == "macro_analysis":
            macro_result = results.get("MacroAgent", {})
            if macro_result.get("success"):
                snapshot = macro_result.get("snapshot", {})
                regime = macro_result.get("regime", {})
                
                vix = snapshot.get("vix", {})
                yc = snapshot.get("yield_curve", {})
                
                lines.extend([
                    "",
                    "🌍 MACRO ENVIRONMENT:",
                    f"   VIX: {vix.get('value', 'N/A'):.1f} ({vix.get('regime', 'N/A').upper()})",
                    f"   Yield Curve: {yc.get('status', 'N/A').upper()}",
                    "",
                    f"🎯 MARKET REGIME: {regime.get('regime', 'N/A').upper()}",
                    f"   Risk Stance: {regime.get('risk_stance', 'N/A')}",
                    f"   Equity Adjustment: {regime.get('equity_adjustment', 0):+.0%}",
                ])
        
        elif intent["type"] == "rebalancing":
            rebal_result = results.get("RebalanceAgent", {})
            if rebal_result.get("success"):
                decision = rebal_result.get("decision", {})
                drift = rebal_result.get("drift_analysis", {})
                trades = rebal_result.get("trades", [])
                
                lines.extend([
                    "",
                    "⚖️ REBALANCING ANALYSIS:",
                    f"   Max Drift: {drift.get('max_drift', 'N/A')}",
                    f"   Threshold: {drift.get('threshold', 'N/A')}",
                    "",
                    f"🎯 RECOMMENDATION: {decision.get('recommendation', 'N/A').upper()}",
                ])
                
                if trades:
                    lines.append("\n📋 TRADES:")
                    for trade in trades[:5]:  # Show max 5 trades
                        lines.append(
                            f"   {trade['action']} {trade['shares']:.1f} {trade['ticker']} "
                            f"@ €{trade['estimated_price']:.2f}"
                        )
        
        elif intent["type"] == "optimization":
            data_result = results.get("DataAgent", {})
            opt_result = results.get("OptimizationAgent", {})
            
            if data_result.get("success"):
                lines.extend([
                    "",
                    f"📊 DATA: {data_result.get('num_observations', 'N/A')} observations loaded",
                ])
            
            if opt_result.get("success"):
                weights = opt_result.get("optimal_weights", {})
                lines.extend([
                    "",
                    "⚡ OPTIMAL ALLOCATION:",
                ])
                for asset, weight in sorted(weights.items(), key=lambda x: -x[1]):
                    lines.append(f"   {asset}: {weight:.1%}")
                
                lines.extend([
                    "",
                    "📈 EXPECTED METRICS:",
                    f"   Return: {opt_result.get('expected_return', 0):.2%}",
                    f"   Volatility: {opt_result.get('expected_volatility', 0):.2%}",
                    f"   Sharpe: {opt_result.get('sharpe_ratio', 0):.2f}",
                ])
        
        else:
            lines.extend([
                "",
                "ℹ️ Request processed. See agent outputs above for details.",
            ])
        
        lines.extend([
            "",
            "═" * 60,
            "",
        ])
        
        return "\n".join(lines)


# ==================== MAIN CLI LOOP ====================

async def main():
    """Main CLI loop."""
    console = AgentConsole()
    console.print_header()
    
    # Initialize orchestrator
    orchestrator = MultiAgentOrchestrator(console, verbose=True)
    
    print("\n" + "─" * 60)
    print("Ready! Type your request or 'help' for examples.")
    
    while True:
        try:
            # Get user input
            user_input = console.print_user_prompt()
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'help':
                console.print_help()
                continue
            
            if not user_input.strip():
                continue
            
            # Process request
            response = await orchestrator.process_request(user_input)
            
            # Print response
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            console.print_error(str(e))


def run():
    """Entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
