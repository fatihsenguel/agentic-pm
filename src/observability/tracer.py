"""
Observability Module - Tracer for Multi-Agent System.

This module provides comprehensive tracing for:
- Agent invocations
- Tool calls
- LLM interactions
- Token usage
- Timing information

The tracer creates a complete audit trail that can be:
- Displayed in real-time (console/UI)
- Exported to JSON (for audit)
- Sent to LangSmith (optional)
- Analyzed for cost optimization

Usage:
    from observability import Tracer, trace_agent, trace_tool
    
    tracer = Tracer()
    
    with tracer.trace_request("user_request_123") as request_trace:
        with request_trace.trace_agent("RiskManager") as agent_trace:
            agent_trace.log_thinking("Analyzing request...")
            
            with agent_trace.trace_tool("fetch_prices") as tool_trace:
                tool_trace.set_input({"tickers": "SPY,TLT"})
                result = fetch_prices(...)
                tool_trace.set_output(result)
            
            agent_trace.log_decision("Delegating to MacroAgent")
    
    print(tracer.get_summary())
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from contextlib import contextmanager
from enum import Enum
import threading


# ==================== ENUMS ====================

class TraceLevel(Enum):
    """Trace verbosity levels."""
    MINIMAL = 1   # Only errors and final results
    NORMAL = 2    # Agent calls and results
    VERBOSE = 3   # Include tool calls
    DEBUG = 4     # Everything including thinking


class TraceEventType(Enum):
    """Types of trace events."""
    REQUEST_START = "request_start"
    REQUEST_END = "request_end"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_THINKING = "agent_thinking"
    AGENT_DECISION = "agent_decision"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    LLM_START = "llm_start"
    LLM_END = "llm_end"
    ERROR = "error"
    DELEGATION = "delegation"
    INTERRUPT = "interrupt"  # For Human-in-the-Loop


# ==================== DATA CLASSES ====================

@dataclass
class TraceEvent:
    """Single trace event."""
    event_id: str
    event_type: TraceEventType
    timestamp: datetime
    elapsed_ms: float
    
    # Context
    request_id: str
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    
    # Data
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Tokens (for LLM calls)
    input_tokens: int = 0
    output_tokens: int = 0
    
    # Error info
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "elapsed_ms": round(self.elapsed_ms, 2),
            "request_id": self.request_id,
            "agent_name": self.agent_name,
            "tool_name": self.tool_name,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "metadata": self.metadata,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "error": self.error,
        }


@dataclass
class RequestTrace:
    """Complete trace for a single user request."""
    request_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # User info
    user_input: str = ""
    final_response: str = ""
    
    # Events
    events: List[TraceEvent] = field(default_factory=list)
    
    # Aggregates
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    agents_used: List[str] = field(default_factory=list)
    tools_called: List[str] = field(default_factory=list)
    
    # Status
    success: bool = True
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        """Total duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "request_id": self.request_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": round(self.duration_ms, 2),
            "user_input": self.user_input,
            "final_response": self.final_response[:500] + "..." if len(self.final_response) > 500 else self.final_response,
            "events": [e.to_dict() for e in self.events],
            "summary": {
                "total_tokens": self.total_tokens,
                "total_cost_usd": round(self.total_cost_usd, 4),
                "agents_used": list(set(self.agents_used)),
                "tools_called": list(set(self.tools_called)),
                "num_events": len(self.events),
            },
            "success": self.success,
            "error": self.error,
        }


# ==================== TRACER CONTEXT MANAGERS ====================

class ToolTrace:
    """Context manager for tracing a tool call."""
    
    def __init__(self, tracer: 'Tracer', request_id: str, agent_name: str, tool_name: str):
        self.tracer = tracer
        self.request_id = request_id
        self.agent_name = agent_name
        self.tool_name = tool_name
        self.start_time = None
        self.input_data = None
        self.output_data = None
        self.error = None
    
    def set_input(self, data: Dict[str, Any]):
        """Set input parameters."""
        self.input_data = data
    
    def set_output(self, data: Any):
        """Set output result."""
        if isinstance(data, dict):
            self.output_data = data
        else:
            self.output_data = {"result": str(data)}
    
    def set_error(self, error: str):
        """Set error message."""
        self.error = error
    
    def __enter__(self):
        self.start_time = time.time()
        self.tracer._emit_event(
            event_type=TraceEventType.TOOL_START,
            request_id=self.request_id,
            agent_name=self.agent_name,
            tool_name=self.tool_name,
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.time() - self.start_time) * 1000
        
        if exc_type:
            self.error = str(exc_val)
        
        self.tracer._emit_event(
            event_type=TraceEventType.TOOL_END,
            request_id=self.request_id,
            agent_name=self.agent_name,
            tool_name=self.tool_name,
            elapsed_ms=elapsed_ms,
            input_data=self.input_data,
            output_data=self.output_data,
            error=self.error,
        )
        
        # Don't suppress exceptions
        return False


class AgentTrace:
    """Context manager for tracing an agent invocation."""
    
    def __init__(self, tracer: 'Tracer', request_id: str, agent_name: str):
        self.tracer = tracer
        self.request_id = request_id
        self.agent_name = agent_name
        self.start_time = None
        self.input_tokens = 0
        self.output_tokens = 0
        self.error = None
    
    def log_thinking(self, thought: str):
        """Log agent's reasoning."""
        self.tracer._emit_event(
            event_type=TraceEventType.AGENT_THINKING,
            request_id=self.request_id,
            agent_name=self.agent_name,
            metadata={"thought": thought},
        )
    
    def log_decision(self, decision: str):
        """Log agent's decision."""
        self.tracer._emit_event(
            event_type=TraceEventType.AGENT_DECISION,
            request_id=self.request_id,
            agent_name=self.agent_name,
            metadata={"decision": decision},
        )
    
    def log_delegation(self, to_agent: str, task: str):
        """Log delegation to another agent."""
        self.tracer._emit_event(
            event_type=TraceEventType.DELEGATION,
            request_id=self.request_id,
            agent_name=self.agent_name,
            metadata={"to_agent": to_agent, "task": task},
        )
    
    def set_tokens(self, input_tokens: int, output_tokens: int):
        """Set token usage for this agent."""
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
    
    def trace_tool(self, tool_name: str) -> ToolTrace:
        """Create a tool trace context."""
        return ToolTrace(self.tracer, self.request_id, self.agent_name, tool_name)
    
    def __enter__(self):
        self.start_time = time.time()
        self.tracer._emit_event(
            event_type=TraceEventType.AGENT_START,
            request_id=self.request_id,
            agent_name=self.agent_name,
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.time() - self.start_time) * 1000
        
        if exc_type:
            self.error = str(exc_val)
        
        self.tracer._emit_event(
            event_type=TraceEventType.AGENT_END,
            request_id=self.request_id,
            agent_name=self.agent_name,
            elapsed_ms=elapsed_ms,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            error=self.error,
        )
        
        return False


class RequestTraceContext:
    """Context manager for tracing an entire request."""
    
    def __init__(self, tracer: 'Tracer', request_id: str, user_input: str = ""):
        self.tracer = tracer
        self.request_id = request_id
        self.user_input = user_input
        self.start_time = None
        self.trace: Optional[RequestTrace] = None
    
    def trace_agent(self, agent_name: str) -> AgentTrace:
        """Create an agent trace context."""
        return AgentTrace(self.tracer, self.request_id, agent_name)
    
    def set_response(self, response: str):
        """Set the final response."""
        if self.trace:
            self.trace.final_response = response
    
    def set_error(self, error: str):
        """Set error for the request."""
        if self.trace:
            self.trace.success = False
            self.trace.error = error
    
    def __enter__(self):
        self.start_time = time.time()
        self.trace = RequestTrace(
            request_id=self.request_id,
            start_time=datetime.now(),
            user_input=self.user_input,
        )
        self.tracer._current_trace = self.trace
        
        self.tracer._emit_event(
            event_type=TraceEventType.REQUEST_START,
            request_id=self.request_id,
            metadata={"user_input": self.user_input},
        )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.trace.end_time = datetime.now()
        
        if exc_type:
            self.trace.success = False
            self.trace.error = str(exc_val)
        
        # Calculate aggregates
        self._calculate_aggregates()
        
        self.tracer._emit_event(
            event_type=TraceEventType.REQUEST_END,
            request_id=self.request_id,
            elapsed_ms=self.trace.duration_ms,
        )
        
        # Store completed trace
        self.tracer._store_trace(self.trace)
        self.tracer._current_trace = None
        
        return False
    
    def _calculate_aggregates(self):
        """Calculate aggregate statistics."""
        for event in self.trace.events:
            self.trace.total_tokens += event.input_tokens + event.output_tokens
            
            if event.agent_name and event.agent_name not in self.trace.agents_used:
                self.trace.agents_used.append(event.agent_name)
            
            if event.tool_name and event.tool_name not in self.trace.tools_called:
                self.trace.tools_called.append(event.tool_name)
        
        # Estimate cost (GPT-4 pricing as default)
        self.trace.total_cost_usd = self.tracer.cost_calculator.estimate_cost(
            self.trace.total_tokens
        )


# ==================== COST CALCULATOR ====================

class CostCalculator:
    """Calculate estimated costs for LLM usage."""
    
    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "claude-3-opus": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
    }
    
    def __init__(self, default_model: str = "gpt-4-turbo"):
        self.default_model = default_model
    
    def estimate_cost(
        self, 
        total_tokens: int, 
        model: Optional[str] = None,
        input_ratio: float = 0.7  # Assume 70% input, 30% output
    ) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            total_tokens: Total tokens used
            model: Model name (uses default if not specified)
            input_ratio: Ratio of input tokens (for estimation)
        
        Returns:
            Estimated cost in USD
        """
        model = model or self.default_model
        pricing = self.PRICING.get(model, self.PRICING["gpt-4-turbo"])
        
        input_tokens = int(total_tokens * input_ratio)
        output_tokens = total_tokens - input_tokens
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost


# ==================== CONSOLE FORMATTER ====================

class ConsoleFormatter:
    """Format trace events for console output."""
    
    # ANSI Colors
    COLORS = {
        "RiskManager": "\033[93m",    # Yellow
        "DataAgent": "\033[94m",       # Blue
        "MacroAgent": "\033[92m",      # Green
        "OptimizationAgent": "\033[95m", # Magenta
        "RebalanceAgent": "\033[96m",  # Cyan
        "BacktestAgent": "\033[91m",   # Red
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    EMOJIS = {
        TraceEventType.REQUEST_START: "🚀",
        TraceEventType.REQUEST_END: "✅",
        TraceEventType.AGENT_START: "🤖",
        TraceEventType.AGENT_END: "✓",
        TraceEventType.AGENT_THINKING: "💭",
        TraceEventType.AGENT_DECISION: "🎯",
        TraceEventType.TOOL_START: "🔧",
        TraceEventType.TOOL_END: "✓",
        TraceEventType.LLM_START: "🧠",
        TraceEventType.LLM_END: "✓",
        TraceEventType.ERROR: "❌",
        TraceEventType.DELEGATION: "📤",
        TraceEventType.INTERRUPT: "🛑",
    }
    
    def __init__(self, level: TraceLevel = TraceLevel.NORMAL):
        self.level = level
    
    def format_event(self, event: TraceEvent) -> Optional[str]:
        """Format a single event for console output."""
        
        # Filter by level
        if self.level == TraceLevel.MINIMAL:
            if event.event_type not in [TraceEventType.REQUEST_END, TraceEventType.ERROR]:
                return None
        elif self.level == TraceLevel.NORMAL:
            if event.event_type in [TraceEventType.AGENT_THINKING]:
                return None
        
        emoji = self.EMOJIS.get(event.event_type, "•")
        color = self.COLORS.get(event.agent_name, "")
        
        # Format based on event type
        if event.event_type == TraceEventType.REQUEST_START:
            return f"\n{emoji} Request started: {event.request_id[:8]}..."
        
        elif event.event_type == TraceEventType.REQUEST_END:
            return f"\n{emoji} Request complete ({event.elapsed_ms:.0f}ms)"
        
        elif event.event_type == TraceEventType.AGENT_START:
            return f"\n{color}┌─ {emoji} [{event.agent_name}] Starting...{self.RESET}"
        
        elif event.event_type == TraceEventType.AGENT_END:
            tokens = f" | {event.input_tokens + event.output_tokens} tokens" if event.input_tokens else ""
            return f"{color}└─ ✓ [{event.agent_name}] Done ({event.elapsed_ms:.0f}ms{tokens}){self.RESET}"
        
        elif event.event_type == TraceEventType.AGENT_THINKING:
            thought = event.metadata.get("thought", "")
            return f"{color}│  {emoji} {thought}{self.RESET}"
        
        elif event.event_type == TraceEventType.AGENT_DECISION:
            decision = event.metadata.get("decision", "")
            return f"{color}│  {emoji} Decision: {decision}{self.RESET}"
        
        elif event.event_type == TraceEventType.TOOL_START:
            params = ""
            if event.input_data:
                params = f" | params: {json.dumps(event.input_data)[:50]}..."
            return f"{color}│  {emoji} Calling: {event.tool_name}{params}{self.RESET}"
        
        elif event.event_type == TraceEventType.TOOL_END:
            status = "✓" if not event.error else "✗"
            return f"{color}│     {status} {event.tool_name} ({event.elapsed_ms:.0f}ms){self.RESET}"
        
        elif event.event_type == TraceEventType.DELEGATION:
            to_agent = event.metadata.get("to_agent", "")
            task = event.metadata.get("task", "")
            return f"{color}│  {emoji} Delegating to {to_agent}: {task}{self.RESET}"
        
        elif event.event_type == TraceEventType.ERROR:
            return f"\n{emoji} ERROR: {event.error}"
        
        elif event.event_type == TraceEventType.INTERRUPT:
            return f"\n{emoji} HUMAN APPROVAL REQUIRED"
        
        return None
    
    def format_summary(self, trace: RequestTrace) -> str:
        """Format request summary."""
        lines = [
            "",
            "═" * 60,
            "📊 REQUEST SUMMARY",
            "═" * 60,
            f"   Request ID:    {trace.request_id[:16]}...",
            f"   Duration:      {trace.duration_ms:.0f}ms",
            f"   Total Tokens:  {trace.total_tokens:,}",
            f"   Est. Cost:     ${trace.total_cost_usd:.4f}",
            f"   Agents Used:   {', '.join(trace.agents_used)}",
            f"   Tools Called:  {len(trace.tools_called)}",
            f"   Status:        {'✅ Success' if trace.success else '❌ Failed'}",
            "═" * 60,
        ]
        return "\n".join(lines)


# ==================== MAIN TRACER CLASS ====================

class Tracer:
    """
    Main tracer class for observability.
    
    Thread-safe implementation that can be used across the application.
    
    Usage:
        tracer = Tracer(level=TraceLevel.VERBOSE)
        
        with tracer.trace_request("req_123", "User message") as req:
            with req.trace_agent("DataAgent") as agent:
                agent.log_thinking("Fetching data...")
                
                with agent.trace_tool("fetch_prices") as tool:
                    tool.set_input({"tickers": "SPY"})
                    result = do_something()
                    tool.set_output(result)
        
        print(tracer.get_summary())
    """
    
    def __init__(
        self,
        level: TraceLevel = TraceLevel.NORMAL,
        console_output: bool = True,
        store_traces: bool = True,
        max_stored_traces: int = 100,
    ):
        """
        Initialize tracer.
        
        Args:
            level: Verbosity level
            console_output: Print events to console
            store_traces: Store completed traces
            max_stored_traces: Maximum traces to keep in memory
        """
        self.level = level
        self.console_output = console_output
        self.store_traces = store_traces
        self.max_stored_traces = max_stored_traces
        
        self._traces: List[RequestTrace] = []
        self._current_trace: Optional[RequestTrace] = None
        self._lock = threading.Lock()
        
        self.formatter = ConsoleFormatter(level)
        self.cost_calculator = CostCalculator()
        
        # Callbacks for custom handlers
        self._event_callbacks: List[Callable[[TraceEvent], None]] = []
    
    def trace_request(self, request_id: Optional[str] = None, user_input: str = "") -> RequestTraceContext:
        """
        Create a request trace context.
        
        Args:
            request_id: Unique request ID (generated if not provided)
            user_input: The user's input message
        
        Returns:
            RequestTraceContext for use in 'with' statement
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        return RequestTraceContext(self, request_id, user_input)
    
    def get_current_request(self):
        """
        Get the current request context helper.
        
        Returns an object that allows starting agent traces 
        linked to the current active request.
        """
        # If no request is running (e.g. during unit tests), return None
        if self._current_trace is None:
            return None
            
        # Helper class to allow calling trace_agent() on the current request
        # We define this locally to capture the tracer instance and request_id
        class CurrentRequestProxy:
            def __init__(self, tracer_instance, request_id):
                self.tracer = tracer_instance
                self.request_id = request_id
                
            def trace_agent(self, agent_name: str) -> 'AgentTrace':
                # Delegates to the existing AgentTrace context manager
                return AgentTrace(self.tracer, self.request_id, agent_name)
                
        return CurrentRequestProxy(self, self._current_trace.request_id)
    
    def _emit_event(
        self,
        event_type: TraceEventType,
        request_id: str,
        agent_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        elapsed_ms: float = 0,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error: Optional[str] = None,
    ):
        """Emit a trace event."""
        event = TraceEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            elapsed_ms=elapsed_ms,
            request_id=request_id,
            agent_name=agent_name,
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            metadata=metadata or {},
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            error=error,
        )
        
        # Store in current trace
        if self._current_trace:
            self._current_trace.events.append(event)
        
        # Console output
        if self.console_output:
            formatted = self.formatter.format_event(event)
            if formatted:
                print(formatted)
        
        # Custom callbacks
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Trace callback error: {e}")
    
    def _store_trace(self, trace: RequestTrace):
        """Store a completed trace."""
        if not self.store_traces:
            return
        
        with self._lock:
            self._traces.append(trace)
            
            # Limit stored traces
            if len(self._traces) > self.max_stored_traces:
                self._traces = self._traces[-self.max_stored_traces:]
    
    def add_callback(self, callback: Callable[[TraceEvent], None]):
        """Add a callback for trace events."""
        self._event_callbacks.append(callback)
    
    def get_traces(self) -> List[RequestTrace]:
        """Get all stored traces."""
        with self._lock:
            return list(self._traces)
    
    def get_last_trace(self) -> Optional[RequestTrace]:
        """Get the most recent trace."""
        with self._lock:
            return self._traces[-1] if self._traces else None
    
    def get_summary(self) -> str:
        """Get summary of the last trace."""
        trace = self.get_last_trace()
        if trace:
            return self.formatter.format_summary(trace)
        return "No traces available"
    
    def export_json(self, filepath: str):
        """Export all traces to JSON file."""
        traces = self.get_traces()
        with open(filepath, 'w') as f:
            json.dump([t.to_dict() for t in traces], f, indent=2)
    
    def clear(self):
        """Clear all stored traces."""
        with self._lock:
            self._traces.clear()


# ==================== SINGLETON INSTANCE ====================

# Global tracer instance
_global_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """Get the global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer()
    return _global_tracer


def set_tracer(tracer: Tracer):
    """Set the global tracer instance."""
    global _global_tracer
    _global_tracer = tracer


# ==================== DECORATORS ====================

def trace_agent(agent_name: str):
    """
    Decorator to trace an agent method.
    
    Usage:
        @trace_agent("DataAgent")
        def fetch_prices(self, tickers):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            # Get request_id from context or generate
            request_id = kwargs.pop('_request_id', str(uuid.uuid4()))
            
            with tracer.trace_request(request_id) as req:
                with req.trace_agent(agent_name) as agent_trace:
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        agent_trace.set_error(str(e))
                        raise
        return wrapper
    return decorator


def trace_tool(tool_name: str):
    """
    Decorator to trace a tool function.
    
    Usage:
        @trace_tool("fetch_prices")
        def fetch_prices(tickers):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            # If we're in a request context, use the current trace
            if tracer._current_trace:
                request_id = tracer._current_trace.request_id
                agent_name = "Unknown"  # Could be passed as param
                
                # Create minimal tool trace without full context
                start = time.time()
                try:
                    tracer._emit_event(
                        TraceEventType.TOOL_START,
                        request_id,
                        agent_name=agent_name,
                        tool_name=tool_name,
                        input_data={"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
                    )
                    
                    result = func(*args, **kwargs)
                    
                    tracer._emit_event(
                        TraceEventType.TOOL_END,
                        request_id,
                        agent_name=agent_name,
                        tool_name=tool_name,
                        elapsed_ms=(time.time() - start) * 1000,
                        output_data={"result": str(result)[:200]} if result else None
                    )
                    
                    return result
                except Exception as e:
                    tracer._emit_event(
                        TraceEventType.TOOL_END,
                        request_id,
                        agent_name=agent_name,
                        tool_name=tool_name,
                        elapsed_ms=(time.time() - start) * 1000,
                        error=str(e)
                    )
                    raise
            else:
                # No active trace, just run the function
                return func(*args, **kwargs)
        
        return wrapper
    return decorator
