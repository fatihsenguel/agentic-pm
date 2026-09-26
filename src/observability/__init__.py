"""
Observability Module for Multi-Agent System.

Provides request, agent and tool tracing.

Components:
- Tracer: Full request/agent/tool tracing

Usage:
    from observability import Tracer, get_tracer, TraceLevel
    
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
    ConsoleFormatter,
    
    # Singleton
    get_tracer,
    set_tracer,
    
    # Decorators
    trace_agent,
    trace_tool,
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
    "ConsoleFormatter",
    "get_tracer",
    "set_tracer",
    "trace_agent",
    "trace_tool",
]