# src/agents/cli.py
# Purpose: Interactive REPL for the finance agent
# Features: Token tracking, debug mode, cost estimation, full audit trail

import os
import sys
import json
from typing import Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from .finance_agent import create_finance_agent, chat
from .config import ACTIVE_LLM_CONFIG, AGENT_SETTINGS
from .prompts import FINANCE_AGENT_SYSTEM_PROMPT


# =============================================================================
# TOKEN TRACKING & COST ESTIMATION
# =============================================================================

class TokenTracker:
    """
    Tracks token usage and estimates costs.
    
    Note: This is an ESTIMATE. Actual billing may vary slightly.
    For precise tracking, use OpenAI's usage API or LangSmith.
    """
    
    # Pricing per 1M tokens (as of Jan 2025)
    PRICING = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    }
    
    def __init__(self, model: str):
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.session_start = datetime.now()
        self.query_count = 0
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate: ~4 chars per token for English."""
        return len(text) // 4
    
    def track_query(self, messages: list, response_content: str):
        """Track tokens for a single query."""
        # Estimate input tokens (all messages)
        input_text = ""
        for msg in messages:
            if hasattr(msg, 'content') and msg.content:
                input_text += str(msg.content)
        
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(response_content)
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.query_count += 1
        
        return input_tokens, output_tokens
    
    def get_cost_estimate(self) -> float:
        """Calculate estimated cost in USD."""
        pricing = self.PRICING.get(self.model, {"input": 1.0, "output": 2.0})
        
        input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def get_summary(self) -> str:
        """Get formatted summary of token usage."""
        cost = self.get_cost_estimate()
        duration = datetime.now() - self.session_start
        
        return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Session Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model:          {self.model}
Queries:        {self.query_count}
Input Tokens:   {self.total_input_tokens:,} (estimated)
Output Tokens:  {self.total_output_tokens:,} (estimated)
Total Tokens:   {self.total_input_tokens + self.total_output_tokens:,}
Est. Cost:      ${cost:.4f}
Duration:       {duration.seconds // 60}m {duration.seconds % 60}s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


# =============================================================================
# DEBUG / OBSERVABILITY
# =============================================================================

class AgentObserver:
    """
    Observes agent execution for debugging.
    Shows what the agent "thinks" and which tools it calls.
    
    Modes:
    - OFF: No debug output
    - ON (brief): Shows tool calls and truncated results
    - VERBOSE: Shows full tool results with formatted JSON
    """
    
    def __init__(self, enabled: bool = False, verbose: bool = False):
        self.enabled = enabled
        self.verbose = verbose  # If True, show full tool results
    
    def toggle(self) -> str:
        """Toggle through debug modes: OFF -> ON -> VERBOSE -> OFF"""
        if not self.enabled:
            self.enabled = True
            self.verbose = False
            return "ON (brief)"
        elif not self.verbose:
            self.verbose = True
            return "ON (verbose - full tool results)"
        else:
            self.enabled = False
            self.verbose = False
            return "OFF"
    
    def log(self, message: str):
        if self.enabled:
            print(f"  🔍 {message}")
    
    def _format_tool_result(self, content: str) -> str:
        """Format tool result for display."""
        try:
            # Try to parse as JSON and pretty-print
            data = json.loads(content)
            
            if self.verbose:
                # Full formatted output
                return json.dumps(data, indent=2, default=str)
            else:
                # Brief: Show key metrics only
                return self._extract_key_info(data)
        except json.JSONDecodeError:
            # Not JSON, return as-is (truncated if not verbose)
            if self.verbose:
                return content
            else:
                return content[:100] + "..." if len(content) > 100 else content
    
    def _extract_key_info(self, data: dict) -> str:
        """Extract and format key information from tool result."""
        if not isinstance(data, dict):
            return str(data)[:100]
        
        # Build a brief summary based on what fields exist
        parts = []
        
        # Success/Error status
        if "success" in data:
            status = "✓" if data["success"] else "✗"
            parts.append(status)
        
        # Ticker
        if "ticker" in data:
            parts.append(data["ticker"])
        
        # Key metrics (prioritized list)
        key_fields = [
            ("total_return_pct", "Return"),
            ("cagr_pct", "CAGR"),
            ("volatility_pct", "Vol"),
            ("sharpe_ratio", "Sharpe"),
            ("max_drawdown_pct", "MaxDD"),
            ("affected_count", "Records"),
            ("count", "Count"),
            ("current_price", "Price"),
            ("first_date", "From"),
            ("last_date", "To"),
        ]
        
        for field, label in key_fields:
            if field in data and data[field] is not None:
                parts.append(f"{label}: {data[field]}")
        
        # Error message if present
        if "error" in data and data["error"]:
            parts.append(f"Error: {data['error'][:50]}")
        
        return " | ".join(parts) if parts else str(data)[:100]
    
    def observe_messages(self, messages: list):
        """Log the message flow for debugging."""
        if not self.enabled:
            return
        
        print("\n  ┌─ Agent Thought Process ─────────────────")
        
        for i, msg in enumerate(messages):
            if isinstance(msg, SystemMessage):
                self.log(f"[{i}] SYSTEM: (prompt loaded)")
            
            elif isinstance(msg, HumanMessage):
                content = str(msg.content)[:60] + "..." if len(str(msg.content)) > 60 else msg.content
                self.log(f"[{i}] USER: {content}")
            
            elif isinstance(msg, AIMessage):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        args_str = json.dumps(tc['args']) if isinstance(tc['args'], dict) else str(tc['args'])
                        self.log(f"[{i}] 🔧 TOOL CALL: {tc['name']}({args_str})")
                else:
                    content = str(msg.content)[:60] + "..." if len(str(msg.content)) > 60 else msg.content
                    self.log(f"[{i}] ASSISTANT: {content}")
            
            elif isinstance(msg, ToolMessage):
                formatted = self._format_tool_result(str(msg.content))
                
                if self.verbose and "\n" in formatted:
                    # Multi-line output for verbose mode
                    self.log(f"[{i}] 📦 TOOL RESULT:")
                    for line in formatted.split("\n"):
                        print(f"      {line}")
                else:
                    self.log(f"[{i}] 📦 TOOL RESULT: {formatted}")
        
        print("  └──────────────────────────────────────────\n")


# =============================================================================
# MAIN CLI
# =============================================================================

def print_banner():
    """Print welcome banner."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    🤖 FinBro Agent CLI                        ║
║                    ─────────────────────                      ║
║  Commands:                                                    ║
║    /help     - Show available commands                        ║
║    /debug    - Toggle debug mode (OFF → ON → VERBOSE)         ║
║    /stats    - Show token usage & costs                       ║
║    /clear    - Clear conversation history                     ║
║    /quit     - Exit                                           ║
╚═══════════════════════════════════════════════════════════════╝
""")


def print_help():
    """Print help information."""
    print("""
Available Commands:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  /help          Show this help message
  /debug         Toggle debug mode (OFF → ON → VERBOSE)
                   - OFF: No debug output
                   - ON: Brief tool calls and key metrics
                   - VERBOSE: Full JSON tool results (for auditing)
  /stats         Show token usage and cost estimate
  /clear         Clear conversation history
  /history       Show conversation history
  /quit, /exit   Exit the CLI

Example Queries:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  "What assets are being tracked?"
  "Fetch stock prices for AAPL"
  "What is the return of AAPL over the last year?"
  "Calculate volatility for TSLA"
  "Compare AAPL, MSFT, and GOOGL"

Debug Mode Tips:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Use VERBOSE mode to verify calculations:
  - See exact date ranges used
  - See start/end prices for return calculations
  - Audit all input data the agent used
""")


def main():
    """Main CLI loop."""
    print_banner()
    
    # Initialize
    print(f"📡 Loading agent with {ACTIVE_LLM_CONFIG.model}...")
    agent = create_finance_agent()
    print("✅ Agent ready!\n")
    
    # State
    conversation_history = []
    token_tracker = TokenTracker(ACTIVE_LLM_CONFIG.model)
    observer = AgentObserver(enabled=False, verbose=False)
    
    # Main loop
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower()
                
                if cmd in ["/quit", "/exit", "/q"]:
                    print(token_tracker.get_summary())
                    print("\n👋 Goodbye!")
                    break
                
                elif cmd == "/help":
                    print_help()
                    continue
                
                elif cmd == "/debug":
                    status = observer.toggle()
                    print(f"Debug mode: {status}")
                    continue
                
                elif cmd == "/stats":
                    print(token_tracker.get_summary())
                    continue
                
                elif cmd == "/clear":
                    conversation_history = []
                    print("🗑️  Conversation history cleared.")
                    continue
                
                elif cmd == "/history":
                    if not conversation_history:
                        print("No conversation history yet.")
                    else:
                        print(f"\n📜 History ({len(conversation_history)} messages):")
                        for i, msg in enumerate(conversation_history):
                            role = "You" if isinstance(msg, HumanMessage) else "Agent"
                            content = str(msg.content)[:100]
                            print(f"  [{i}] {role}: {content}...")
                    continue
                
                else:
                    print(f"Unknown command: {user_input}. Type /help for available commands.")
                    continue
            
            # Regular query - send to agent
            conversation_history.append(HumanMessage(content=user_input))
            
            # Invoke agent
            result = agent.invoke({"messages": conversation_history})
            
            # Observe if debug mode
            observer.observe_messages(result["messages"])
            
            # Extract response
            final_message = result["messages"][-1]
            response_content = final_message.content
            
            # Update conversation history with full result
            conversation_history = list(result["messages"])
            
            # Track tokens
            input_tokens, output_tokens = token_tracker.track_query(
                result["messages"][:-1],  # All except response
                response_content
            )
            
            # Print response
            print(f"\n🤖 Agent: {response_content}")
            
            # Show token usage in debug mode
            if observer.enabled:
                print(f"\n  📈 Tokens: ~{input_tokens} in, ~{output_tokens} out")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted. Type /quit to exit properly.")
            continue
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if observer.enabled:
                import traceback
                traceback.print_exc()
            continue


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()