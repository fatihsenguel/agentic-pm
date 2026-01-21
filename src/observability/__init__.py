"""
Observability Module for Multi-Agent System.

Provides comprehensive tracing, token counting, and cost management.

Components:
- Tracer: Full request/agent/tool tracing
- TokenCounter: Token usage tracking
- CostCalculator: Cost estimation

Usage:
    from observability import (
        Tracer, 
        get_tracer, 
        TokenCounter, 
        get_token_counter,
        TraceLevel
    )
    
    # Configure tracer
    tracer = Tracer(level=TraceLevel.VERBOSE)
    
    # Trace a request
    with tracer.trace_request("req_123", "User message") as req:
        with req.trace_agent("DataAgent") as agent:
            agent.log_thinking("Processing...")
            
            with agent.trace_tool("fetch_prices") as tool:
                tool.set_input({"tickers": "SPY"})
                result = do_something()
                tool.set_output(result)
                
            agent.set_tokens(150, 80)
    
    # Get summary
    print(tracer.get_summary())
    
    # Token tracking
    counter = get_token_counter()
    counter.add_usage("DataAgent", 150, 80)
    print(counter.format_report())
"""

from .tracer import (
    # Main classes
    Tracer,
    TraceLevel,
    TraceEventType,
    
    # Context managers
    RequestTraceContext,
    AgentTrace,
    ToolTrace,
    
    # Data classes
    TraceEvent,
    RequestTrace,
    
    # Utilities
    CostCalculator,
    ConsoleFormatter,
    
    # Singleton
    get_tracer,
    set_tracer,
    
    # Decorators
    trace_agent,
    trace_tool,
)

from .token_counter import (
    TokenCounter,
    TokenUsage,
    UsageSummary,
    
    # Functions
    calculate_cost,
    get_token_counter,
    set_token_counter,
    
    # Constants
    MODEL_PRICING,
)


__all__ = [
    # Tracer
    "Tracer",
    "TraceLevel",
    "TraceEventType",
    "RequestTraceContext",
    "AgentTrace",
    "ToolTrace",
    "TraceEvent",
    "RequestTrace",
    "CostCalculator",
    "ConsoleFormatter",
    "get_tracer",
    "set_tracer",
    "trace_agent",
    "trace_tool",
    
    # Token Counter
    "TokenCounter",
    "TokenUsage",
    "UsageSummary",
    "calculate_cost",
    "get_token_counter",
    "set_token_counter",
    "MODEL_PRICING",
]