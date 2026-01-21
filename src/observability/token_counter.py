"""
Token Counter for Multi-Agent System.

Tracks token usage per:
- Request
- Agent
- Tool
- Model

Provides cost estimation and budget management.

Usage:
    from observability import TokenCounter
    
    counter = TokenCounter()
    
    # Track usage
    counter.add_usage(
        agent="DataAgent",
        model="gpt-4-turbo",
        input_tokens=150,
        output_tokens=80
    )
    
    # Get statistics
    print(counter.get_summary())
    print(counter.get_cost_report())
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional
import json
import threading


# ==================== DATA CLASSES ====================

@dataclass
class TokenUsage:
    """Single token usage record."""
    timestamp: datetime
    request_id: str
    agent_name: str
    model: str
    input_tokens: int
    output_tokens: int
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id,
            "agent_name": self.agent_name,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class UsageSummary:
    """Aggregated usage summary."""
    period: str  # "day", "week", "month", "all"
    start_date: datetime
    end_date: datetime
    
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    
    by_agent: Dict[str, int] = field(default_factory=dict)
    by_model: Dict[str, int] = field(default_factory=dict)
    
    estimated_cost_usd: float = 0.0
    
    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens
    
    def to_dict(self) -> Dict:
        return {
            "period": self.period,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "by_agent": self.by_agent,
            "by_model": self.by_model,
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
        }


# ==================== PRICING ====================

# Pricing per 1M tokens (as of 2024)
MODEL_PRICING = {
    # OpenAI
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    
    # Anthropic
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
    
    # Default fallback
    "default": {"input": 10.0, "output": 30.0},
}


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4-turbo"
) -> float:
    """Calculate cost for token usage."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    
    return input_cost + output_cost


# ==================== TOKEN COUNTER ====================

class TokenCounter:
    """
    Track and manage token usage across the system.
    
    Thread-safe implementation.
    """
    
    def __init__(
        self,
        budget_limit_usd: Optional[float] = None,
        default_model: str = "gpt-4-turbo",
    ):
        """
        Initialize token counter.
        
        Args:
            budget_limit_usd: Optional budget limit (raises warning when exceeded)
            default_model: Default model for cost estimation
        """
        self.budget_limit_usd = budget_limit_usd
        self.default_model = default_model
        
        self._usage_records: List[TokenUsage] = []
        self._lock = threading.Lock()
        
        # Running totals for quick access
        self._total_input = 0
        self._total_output = 0
        self._total_cost = 0.0
    
    def add_usage(
        self,
        agent_name: str,
        input_tokens: int,
        output_tokens: int,
        request_id: str = "",
        model: Optional[str] = None,
    ) -> float:
        """
        Record token usage.
        
        Args:
            agent_name: Name of the agent
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            request_id: Associated request ID
            model: Model used (uses default if not specified)
        
        Returns:
            Cost of this usage in USD
        """
        model = model or self.default_model
        
        record = TokenUsage(
            timestamp=datetime.now(),
            request_id=request_id,
            agent_name=agent_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        
        cost = calculate_cost(input_tokens, output_tokens, model)
        
        with self._lock:
            self._usage_records.append(record)
            self._total_input += input_tokens
            self._total_output += output_tokens
            self._total_cost += cost
        
        # Check budget
        if self.budget_limit_usd and self._total_cost > self.budget_limit_usd:
            print(f"⚠️ WARNING: Budget exceeded! ${self._total_cost:.2f} > ${self.budget_limit_usd:.2f}")
        
        return cost
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self._total_input + self._total_output
    
    @property
    def total_cost(self) -> float:
        """Get total estimated cost."""
        return self._total_cost
    
    def get_summary(
        self,
        period: str = "all",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> UsageSummary:
        """
        Get usage summary for a period.
        
        Args:
            period: "day", "week", "month", or "all"
            start_date: Custom start date
            end_date: Custom end date
        
        Returns:
            UsageSummary with aggregated statistics
        """
        now = datetime.now()
        
        # Determine date range
        if period == "day":
            start = datetime.combine(now.date(), datetime.min.time())
            end = now
        elif period == "week":
            start = now - timedelta(days=7)
            end = now
        elif period == "month":
            start = now - timedelta(days=30)
            end = now
        else:
            start = datetime.min
            end = now
        
        if start_date:
            start = start_date
        if end_date:
            end = end_date
        
        # Filter and aggregate
        summary = UsageSummary(
            period=period,
            start_date=start,
            end_date=end,
        )
        
        seen_requests = set()
        
        with self._lock:
            for record in self._usage_records:
                if start <= record.timestamp <= end:
                    summary.total_input_tokens += record.input_tokens
                    summary.total_output_tokens += record.output_tokens
                    
                    # Count by agent
                    if record.agent_name not in summary.by_agent:
                        summary.by_agent[record.agent_name] = 0
                    summary.by_agent[record.agent_name] += record.total_tokens
                    
                    # Count by model
                    if record.model not in summary.by_model:
                        summary.by_model[record.model] = 0
                    summary.by_model[record.model] += record.total_tokens
                    
                    # Count unique requests
                    if record.request_id:
                        seen_requests.add(record.request_id)
                    
                    # Add cost
                    summary.estimated_cost_usd += calculate_cost(
                        record.input_tokens,
                        record.output_tokens,
                        record.model
                    )
        
        summary.total_requests = len(seen_requests)
        
        return summary
    
    def get_agent_breakdown(self) -> Dict[str, Dict[str, int]]:
        """Get token usage breakdown by agent."""
        breakdown = {}
        
        with self._lock:
            for record in self._usage_records:
                if record.agent_name not in breakdown:
                    breakdown[record.agent_name] = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "calls": 0,
                    }
                breakdown[record.agent_name]["input_tokens"] += record.input_tokens
                breakdown[record.agent_name]["output_tokens"] += record.output_tokens
                breakdown[record.agent_name]["calls"] += 1
        
        return breakdown
    
    def format_report(self) -> str:
        """Generate formatted usage report."""
        summary = self.get_summary()
        breakdown = self.get_agent_breakdown()
        
        lines = [
            "",
            "╔" + "═" * 58 + "╗",
            "║" + " " * 18 + "TOKEN USAGE REPORT" + " " * 22 + "║",
            "╠" + "═" * 58 + "╣",
            f"║  Total Tokens:     {summary.total_tokens:>15,}" + " " * 21 + "║",
            f"║  Input Tokens:     {summary.total_input_tokens:>15,}" + " " * 21 + "║",
            f"║  Output Tokens:    {summary.total_output_tokens:>15,}" + " " * 21 + "║",
            f"║  Total Requests:   {summary.total_requests:>15,}" + " " * 21 + "║",
            f"║  Estimated Cost:   ${summary.estimated_cost_usd:>14.4f}" + " " * 21 + "║",
            "╠" + "═" * 58 + "╣",
            "║  BY AGENT:" + " " * 47 + "║",
        ]
        
        for agent, data in sorted(breakdown.items()):
            total = data["input_tokens"] + data["output_tokens"]
            lines.append(f"║    {agent:<20} {total:>10,} tokens ({data['calls']} calls)" + " " * 5 + "║")
        
        lines.extend([
            "╠" + "═" * 58 + "╣",
            "║  BY MODEL:" + " " * 47 + "║",
        ])
        
        for model, tokens in sorted(summary.by_model.items()):
            lines.append(f"║    {model:<20} {tokens:>10,} tokens" + " " * 17 + "║")
        
        if self.budget_limit_usd:
            remaining = self.budget_limit_usd - self._total_cost
            status = "✓" if remaining > 0 else "⚠️"
            lines.extend([
                "╠" + "═" * 58 + "╣",
                f"║  Budget: ${self.budget_limit_usd:.2f}  |  Remaining: ${remaining:.2f} {status}" + " " * 10 + "║",
            ])
        
        lines.append("╚" + "═" * 58 + "╝")
        
        return "\n".join(lines)
    
    def export_json(self, filepath: str):
        """Export usage records to JSON."""
        with self._lock:
            data = {
                "exported_at": datetime.now().isoformat(),
                "summary": self.get_summary().to_dict(),
                "records": [r.to_dict() for r in self._usage_records],
            }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def reset(self):
        """Reset all counters."""
        with self._lock:
            self._usage_records.clear()
            self._total_input = 0
            self._total_output = 0
            self._total_cost = 0.0


# ==================== SINGLETON ====================

_global_counter: Optional[TokenCounter] = None


def get_token_counter() -> TokenCounter:
    """Get the global token counter."""
    global _global_counter
    if _global_counter is None:
        _global_counter = TokenCounter()
    return _global_counter


def set_token_counter(counter: TokenCounter):
    """Set the global token counter."""
    global _global_counter
    _global_counter = counter


# Missing import
from datetime import timedelta
