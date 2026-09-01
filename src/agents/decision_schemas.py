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
from typing import List, Dict, Optional, Literal, Any

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

# =============================================================================
# PHASE 7.0: COMPLIANCE ENUMS
# =============================================================================

class ConstraintType(str, Enum):
    """Types of IPS constraints."""
    ALLOCATION = "allocation"
    CONCENTRATION = "concentration"
    LIQUIDITY = "liquidity"
    SECTOR = "sector"
    DURATION = "duration"
    CREDIT = "credit"
    ESG = "esg"
    GEOGRAPHY = "geography"
    CURRENCY = "currency"


class BreachSeverity(str, Enum):
    """Severity classification for compliance breaches."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplianceStatus(str, Enum):
    """Overall compliance status for a portfolio."""
    COMPLIANT = "compliant"
    WARNING = "warning"
    NON_COMPLIANT = "non_compliant"


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
    compliance_breaches: List['ComplianceCheck'] = field(default_factory=list)

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
            "suggested_action": self.suggested_action.value,
            "compliance_breaches": [b.to_dict() for b in self.compliance_breaches] if self.compliance_breaches else []

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


# =============================================================================
# PHASE 7.0: COMPLIANCE DATACLASSES
# =============================================================================

@dataclass
class IPSConstraint:
    """A single IPS constraint loaded from database."""
    type: ConstraintType
    name: str
    
    asset_class: Optional[str] = None
    sector: Optional[str] = None
    ticker: Optional[str] = None
    
    min_weight: Optional[float] = None
    max_weight: Optional[float] = None
    target_weight: Optional[float] = None
    tolerance: float = 0.05
    
    exemptions: List[str] = field(default_factory=list)
    breach_severity: BreachSeverity = BreachSeverity.HIGH
    rule: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "name": self.name,
            "asset_class": self.asset_class,
            "sector": self.sector,
            "ticker": self.ticker,
            "min_weight": self.min_weight,
            "max_weight": self.max_weight,
            "target_weight": self.target_weight,
            "tolerance": self.tolerance,
            "exemptions": self.exemptions,
            "breach_severity": self.breach_severity.value,
            "rule": self.rule
        }


@dataclass
class ComplianceCheck:
    """Result of checking ONE constraint against a portfolio."""
    constraint_name: str
    constraint_type: ConstraintType
    status: Literal["pass", "warning", "breach"]
    
    severity: Optional[BreachSeverity] = None
    current_value: float = 0.0
    limit_value: float = 0.0
    
    ticker: Optional[str] = None
    isin: Optional[str] = None
    asset_class: Optional[str] = None
    sector: Optional[str] = None
    
    message: str = ""
    action: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "constraint_name": self.constraint_name,
            "constraint_type": self.constraint_type.value,
            "status": self.status,
            "severity": self.severity.value if self.severity else None,
            "current_value": self.current_value,
            "limit_value": self.limit_value,
            "ticker": self.ticker,
            "isin": self.isin,
            "asset_class": self.asset_class,
            "sector": self.sector,
            "message": self.message,
            "action": self.action
        }
    
    def format_row(self) -> str:
        """Format as a single row for display."""
        severity_emoji = {
            BreachSeverity.CRITICAL: "🔴",
            BreachSeverity.HIGH: "🟠",
            BreachSeverity.MEDIUM: "🟡",
            BreachSeverity.LOW: "ℹ️"
        }
        emoji = severity_emoji.get(self.severity, "✓") if self.status != "pass" else "✓"
        target = self.ticker or self.asset_class or self.sector or "Portfolio"
        return f"{emoji} {self.constraint_name}: {target} at {self.current_value:.1%} (limit: {self.limit_value:.1%})"


@dataclass
class RemediationTrade:
    """
    A specific trade to fix a compliance breach.
    Added based on Gemini feedback - connects breaches to actionable trades.
    """
    action: Literal["BUY", "SELL", "TRIM", "ADD"]
    ticker: str
    
    shares: Optional[float] = None
    target_weight: Optional[float] = None
    estimated_value: float = 0.0
    
    reason: str = ""
    priority: int = 1
    breach_type: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "ticker": self.ticker,
            "shares": self.shares,
            "target_weight": self.target_weight,
            "estimated_value": self.estimated_value,
            "reason": self.reason,
            "priority": self.priority,
            "breach_type": self.breach_type
        }
    
    def format_instruction(self) -> str:
        """Format as human-readable instruction."""
        if self.shares:
            return f"{self.action} {self.shares:.0f} shares of {self.ticker} (~${self.estimated_value:,.0f})"
        elif self.target_weight:
            return f"{self.action} {self.ticker} to {self.target_weight:.1%} weight (~${self.estimated_value:,.0f})"
        else:
            return f"{self.action} {self.ticker} (~${self.estimated_value:,.0f})"


@dataclass
class ComplianceReport:
    """Full compliance report for a portfolio."""
    
    portfolio_id: int
    portfolio_name: str
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    
    as_of_date: datetime = field(default_factory=datetime.utcnow)
    compliance_run_id: str = ""
    status: ComplianceStatus = ComplianceStatus.COMPLIANT
    
    total_aum: float = 0.0
    num_positions: int = 0
    
    checks: List[ComplianceCheck] = field(default_factory=list)
    allocation: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    remediation_trades: List[RemediationTrade] = field(default_factory=list)
    
    @property
    def breaches(self) -> List[ComplianceCheck]:
        return [c for c in self.checks if c.status == "breach"]
    
    @property
    def warnings(self) -> List[ComplianceCheck]:
        return [c for c in self.checks if c.status == "warning"]
    
    @property
    def passes(self) -> List[ComplianceCheck]:
        return [c for c in self.checks if c.status == "pass"]
    
    @property
    def critical_breaches(self) -> List[ComplianceCheck]:
        return [c for c in self.breaches if c.severity == BreachSeverity.CRITICAL]
    
    @property
    def high_breaches(self) -> List[ComplianceCheck]:
        """Breaches requiring action within 24-48h."""
        return [c for c in self.breaches if c.severity == BreachSeverity.HIGH]
    
    @property
    def num_breaches(self) -> int:
        return len(self.breaches)
    
    @property 
    def num_critical(self) -> int:
        return len(self.critical_breaches)
    
    def to_dict(self) -> Dict:
        return {
            "portfolio_id": self.portfolio_id,
            "portfolio_name": self.portfolio_name,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "as_of_date": self.as_of_date.isoformat(),
            "compliance_run_id": self.compliance_run_id,
            "status": self.status.value,
            "total_aum": self.total_aum,
            "num_positions": self.num_positions,
            "checks": [c.to_dict() for c in self.checks],
            "allocation": self.allocation,
            "recommendations": self.recommendations,
            "remediation_trades": [t.to_dict() for t in self.remediation_trades],
            "summary": {
                "num_breaches": self.num_breaches,
                "num_critical": self.num_critical,
                "num_warnings": len(self.warnings),
                "num_passes": len(self.passes)
            }
        }
    
    def format_summary(self) -> str:
        """Format executive summary."""
        status_emoji = {
            ComplianceStatus.COMPLIANT: "✅ COMPLIANT",
            ComplianceStatus.WARNING: "⚠️ WARNING",
            ComplianceStatus.NON_COMPLIANT: "🔴 NON-COMPLIANT"
        }
        
        lines = [
            "═" * 65,
            "                     COMPLIANCE REPORT",
            "═" * 65,
            f"Portfolio: {self.portfolio_name} (ID: {self.portfolio_id})",
            f"Client:    {self.client_name or 'N/A'} ({self.client_id or 'N/A'})",
            f"Date:      {self.as_of_date.strftime('%Y-%m-%d %H:%M')}",
            f"Status:    {status_emoji.get(self.status, self.status.value)}",
            "",
            f"Total AUM:    ${self.total_aum:,.2f}",
            f"Positions:    {self.num_positions}",
            f"Breaches:     {self.num_breaches} ({self.num_critical} critical)",
            f"Warnings:     {len(self.warnings)}",
            "",
            f"Run ID: {self.compliance_run_id}",
            "═" * 65,
        ]
        return "\n".join(lines)
    
    def format_breaches_table(self) -> str:
        """Format breach table for display."""
        if not self.breaches:
            return "✓ No breaches detected."
        
        lines = ["─" * 65, "DETAILED BREACHES", "─" * 65]
        
        severity_emoji = {
            BreachSeverity.CRITICAL: "🔴 CRIT",
            BreachSeverity.HIGH: "🟠 HIGH",
            BreachSeverity.MEDIUM: "🟡 MED ",
            BreachSeverity.LOW: "ℹ️  LOW "
        }
        
        sorted_breaches = sorted(
            self.breaches, 
            key=lambda x: ["critical", "high", "medium", "low"].index(
                x.severity.value if x.severity else "low"
            )
        )
        
        for b in sorted_breaches:
            sev = severity_emoji.get(b.severity, "    ")
            target = b.ticker or b.asset_class or "N/A"
            lines.append(
                f"{sev} │ {b.constraint_name[:25]:<25} │ {target:<8} │ "
                f"{b.current_value:>6.1%} vs {b.limit_value:>6.1%}"
            )
        
        lines.append("─" * 65)
        return "\n".join(lines)
    
    def format_allocation_drift(self) -> str:
        """Format allocation drift analysis with visual bars."""
        if not self.allocation:
            return ""
        
        lines = ["─" * 65, "ASSET ALLOCATION", "─" * 65]
        
        for asset_class, weight in sorted(self.allocation.items(), key=lambda x: -x[1]):
            bar_length = int(weight * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            lines.append(f"{asset_class.title():<15} {weight:>6.1%}  {bar}")
        
        lines.append("─" * 65)
        return "\n".join(lines)


    def format_remediation(self) -> str:
        """Format remediation trades."""
        if not self.remediation_trades:
            return "No remediation trades required."
        
        lines = ["─" * 65, "REMEDIATION TRADES", "─" * 65]
        
        for i, trade in enumerate(self.remediation_trades, 1):
            lines.append(f"  {i}. {trade.format_instruction()}")
            if trade.reason:
                lines.append(f"     Reason: {trade.reason}")
        
        lines.append("─" * 65)
        return "\n".join(lines)
    
    def format_full_report(self) -> str:
        """Format complete compliance report."""
        sections = [self.format_summary(), "", self.format_breaches_table()]
        
        if self.allocation:
            sections.extend(["", self.format_allocation_drift()])
        
        sections.extend(["", self.format_remediation(), "", "═" * 65])
        return "\n".join(sections)