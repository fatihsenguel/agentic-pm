# src/agents/decision_schemas.py
"""
Decision Layer Schemas for PM-Style Decision Support.

Phase: 6.6 - Decision Summary Layer (Priority 1)

PURPOSE:
These schemas represent the OUTPUT of PM-style decision logic.
They are generated ONLY for DECISION queries (query_intent == "decision").

KEY INSIGHT:
"The system never assumes trading is required. It explicitly evaluates 
whether no action is the optimal decision."

INTERVIEW TALKING POINTS:
1. "We separate semantic intent from execution - only DECISION queries trigger this"
2. "HOLD is a valid, well-reasoned output - not a cop-out"
3. "Risk assessment runs BEFORE optimization, not after"
4. "Every decision includes structured rationale and confidence levels"
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Literal


class DecisionType(str, Enum):
    """
    PM-style decision types.
    
    These represent the OUTCOME of decision logic, not the user's request.
    A user might ask to "optimize" but the system concludes "HOLD" is optimal.
    """
    HOLD = "hold"           # No action warranted - current state is acceptable
    TILT = "tilt"           # Minor tactical adjustment (e.g., reduce equity 5%)
    REBALANCE = "rebalance" # Structural portfolio change to restore targets
    HEDGE = "hedge"         # Temporary risk mitigation (add protection)


class RiskStatus(str, Enum):
    """Portfolio risk status levels."""
    ACCEPTABLE = "acceptable"   # Within all constraints
    ELEVATED = "elevated"       # One or more warnings
    CRITICAL = "critical"       # Multiple breaches, action required


@dataclass
class RiskAssessment:
    """
    Structured risk evaluation - runs BEFORE optimization.
    
    This answers: "What is the current risk state of the portfolio?"
    It does NOT recommend actions - that's PMDecisionSummary's job.
    
    Interview talking point:
    "Risk assessment runs before optimization. The system mirrors 
    institutional workflows: risk first, action second."
    """
    status: RiskStatus
    
    # What's driving the risk
    primary_drivers: List[str] = field(default_factory=list)
    # e.g., ["Tech concentration (42%)", "High correlation to SPY (0.87)"]
    
    # Explicit constraint breaches
    breaches: List[str] = field(default_factory=list)
    # e.g., ["Max position exceeded: AAPL at 45%", "Below min diversification (3 assets)"]
    
    # Quantitative metrics
    concentration_score: float = 0.0      # HHI or similar, 0-1, higher = more concentrated
    max_position_weight: float = 0.0      # Largest single position
    num_positions: int = 0                # Number of holdings
    estimated_volatility: float = 0.0     # Portfolio volatility if available
    tail_risk_estimate: Optional[float] = None  # CVaR or VaR if calculated
    
    # What this risk level suggests (informational, not prescriptive)
    suggested_action: DecisionType = DecisionType.HOLD
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "primary_drivers": self.primary_drivers,
            "breaches": self.breaches,
            "concentration_score": self.concentration_score,
            "max_position_weight": self.max_position_weight,
            "num_positions": self.num_positions,
            "estimated_volatility": self.estimated_volatility,
            "tail_risk_estimate": self.tail_risk_estimate,
            "suggested_action": self.suggested_action.value
        }
    
    def format_summary(self) -> str:
        """Format for human-readable output."""
        lines = [
            f"Status: {self.status.value.upper()}",
            ""
        ]
        
        if self.primary_drivers:
            lines.append("Primary Drivers:")
            for driver in self.primary_drivers[:3]:
                lines.append(f"  • {driver}")
            lines.append("")
        
        if self.breaches:
            lines.append("⚠️ Constraint Breaches:")
            for breach in self.breaches:
                lines.append(f"  • {breach}")
            lines.append("")
        
        if not self.breaches:
            lines.append("✓ No constraint breaches")
        
        return "\n".join(lines)


@dataclass
class PMDecisionSummary:
    """
    Executive summary for every portfolio decision.
    This is what a PM actually sees and acts on.
    
    Generated ONLY when query_intent == "decision".
    
    Interview talking point:
    "The system explicitly evaluates whether no action is optimal.
    Most AI projects assume action bias - mine doesn't."
    """
    # Core decision
    decision: DecisionType
    confidence: float                     # 0.0 - 1.0
    
    # Human-readable explanation
    rationale: str
    
    # Risk context (from RiskAssessment)
    risk_status: RiskStatus
    key_risks: List[str] = field(default_factory=list)  # Top 3 risk factors
    
    # NEW: Document citations (Phase 6.7)
    document_citations: List[Dict[str, str]] = field(default_factory=list)
    # e.g., [{"text": "Revenue up 279%", "source": "NVDA_Q3_2024.pdf, p.2"}]

    # Action details
    trade_required: bool = False
    estimated_trades: int = 0             # Number of trades if action taken
    estimated_turnover: float = 0.0       # Portfolio turnover percentage
    
    # Expected impact (if action is taken)
    expected_impact: Dict[str, float] = field(default_factory=dict)
    # e.g., {"volatility_change": -0.02, "expected_return_change": 0.01}
    
    # What triggered this assessment
    trigger: str = "user_request"
    # Options: "user_request", "drift_threshold", "macro_change", "risk_breach", "scheduled_review"
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    portfolio_id: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return {
            "decision": self.decision.value,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "risk_status": self.risk_status.value,
            "key_risks": self.key_risks,
            "trade_required": self.trade_required,
            "estimated_trades": self.estimated_trades,
            "estimated_turnover": self.estimated_turnover,
            "expected_impact": self.expected_impact,
            "trigger": self.trigger,
            "timestamp": self.timestamp.isoformat(),
            "portfolio_id": self.portfolio_id,
            "document_citations": self.document_citations
        }
    
    def format_summary(self) -> str:
        """
        Format for human-readable output.
        This is the "executive summary" format from the roadmap.
        """
        lines = [
            "═" * 60,
            "DECISION SUMMARY",
            "═" * 60,
            f"Decision:        {self.decision.value.upper()}",
            f"Confidence:      {self.confidence:.0%}",
            f"Trade Required:  {'Yes' if self.trade_required else 'No'}",
            "",
            "Rationale:",
            f"  {self.rationale}",
            "",
            "═" * 60,
            "RISK ASSESSMENT",
            "═" * 60,
            f"Status: {self.risk_status.value.upper()}",
            ""
        ]
        
        if self.key_risks:
            lines.append("Key Risks:")
            for risk in self.key_risks[:3]:
                lines.append(f"  • {risk}")
        else:
            lines.append("Key Risks: None identified")


        if self.document_citations:
            lines.append("")
            lines.append("═" * 60)
            lines.append("DOCUMENT EVIDENCE")
            lines.append("═" * 60)
            for citation in self.document_citations[:3]:
                text = citation.get('text', '')[:80]
                source = citation.get('source', 'Unknown')
                lines.append(f"  • \"{text}...\"")
                lines.append(f"    Source: {source}")
        
        lines.append("")
        
        # Expected impact if action taken
        if self.expected_impact and self.trade_required:
            lines.append("═" * 60)
            lines.append("EXPECTED IMPACT (if action taken)")
            lines.append("═" * 60)
            for metric, change in self.expected_impact.items():
                direction = "↑" if change > 0 else "↓" if change < 0 else "→"
                lines.append(f"  {metric}: {direction} {abs(change):.1%}")
        
        return "\n".join(lines)


@dataclass
class DecisionContext:
    """
    Input context for decision assessment.
    Aggregates all relevant data for the decision engine.
    """
    # Portfolio state
    current_weights: Dict[str, float] = field(default_factory=dict)
    target_weights: Optional[Dict[str, float]] = None
    portfolio_value: float = 0.0
    
    # Drift metrics
    max_drift: float = 0.0
    total_drift: float = 0.0
    
    # Risk metrics (if available)
    portfolio_volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    
    # Macro context (if available)
    macro_regime: Optional[str] = None  # "risk_on", "risk_off", "neutral", "crisis"
    vix_level: Optional[float] = None
    yield_curve_status: Optional[str] = None  # "normal", "flat", "inverted"
    
    # Configuration reference
    drift_threshold: float = 0.05
    max_concentration: float = 0.30
    min_diversification: int = 5
    
    # Trigger
    trigger: str = "user_request"
