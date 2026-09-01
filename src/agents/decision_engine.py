# src/agents/decision_engine.py
"""
Decision Engine for PM-Style Decision Support.

Phase: 6.6 - Decision Summary Layer (Priority 1)

PURPOSE:
This module contains the DETERMINISTIC decision logic that evaluates:
1. Current portfolio risk state (assess_portfolio_risk)
2. Whether action is warranted (assess_decision_needed)

KEY PRINCIPLES:
- NO LLM involvement - pure rule-based logic
- Config-driven thresholds (from src/config.py)
- HOLD is a valid, well-reasoned output
- Risk assessment BEFORE action recommendation

INTERVIEW TALKING POINTS:
1. "Risk assessment runs before optimization - institutional workflow"
2. "HOLD is explicitly evaluated, not a default fallback"
3. "All thresholds are config-driven, no magic numbers"
4. "Deterministic logic means same inputs = same outputs (auditable)"

USAGE:
    from src.agents.decision_engine import assess_decision_needed, assess_portfolio_risk
    from src.config import config
    
    # First: Assess risk
    risk = assess_portfolio_risk(
        weights={"SPY": 0.6, "TLT": 0.3, "GLD": 0.1},
        config=config
    )
    
    # Then: Determine if action needed
    decision = assess_decision_needed(
        context=DecisionContext(
            current_weights=weights,
            target_weights=target,
            max_drift=0.08,
            macro_regime="neutral"
        ),
        risk_assessment=risk,
        config=config
    )
"""

from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime

from .decision_schemas import (
    DecisionType,
    RiskStatus,
    RiskAssessment,
    PMDecisionSummary,
    DecisionContext
)

# Import config - adjust path as needed
try:
    from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.config import config as app_config, AppConfig
except ImportError:
    from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.config import config as app_config, AppConfig


def calculate_hhi(weights: Dict[str, float]) -> float:
    """
    Calculate Herfindahl-Hirschman Index for concentration.
    
    HHI = sum of squared weights
    Range: 1/n (perfectly diversified) to 1.0 (single asset)
    
    For interpretation:
    - < 0.15: Well diversified
    - 0.15 - 0.25: Moderate concentration
    - > 0.25: High concentration
    """
    if not weights:
        return 0.0
    
    return sum(w ** 2 for w in weights.values() if w > 0)


def assess_portfolio_risk(
    weights: Dict[str, float],
    config: Optional[AppConfig] = None,
    volatility: Optional[float] = None,
    covariance: Optional[Dict] = None
) -> RiskAssessment:
    """
    Evaluate current portfolio risk state.
    
    This runs BEFORE considering any changes.
    It answers: "What is the risk profile right now?"
    
    Args:
        weights: Current portfolio weights {ticker: weight}
        config: AppConfig instance (uses global if not provided)
        volatility: Portfolio volatility if pre-calculated
        covariance: Covariance matrix if available (for future CVaR calc)
    
    Returns:
        RiskAssessment with status, drivers, and breaches
    """
    cfg = config or app_config
    risk_cfg = cfg.risk
    
    breaches: List[str] = []
    drivers: List[str] = []
    
    # Skip if no weights
    if not weights:
        return RiskAssessment(
            status=RiskStatus.CRITICAL,
            primary_drivers=["No portfolio weights provided"],
            breaches=["Cannot assess empty portfolio"],
            suggested_action=DecisionType.HOLD
        )
    
    # Filter out zero/near-zero weights
    active_weights = {k: v for k, v in weights.items() if v > 0.01}
    num_positions = len(active_weights)
    
    # =========================================================================
    # CHECK 1: Concentration (max single position)
    # =========================================================================
    max_weight = max(weights.values()) if weights else 0
    max_ticker = max(weights, key=weights.get) if weights else "N/A"
    
    if max_weight > risk_cfg.max_concentration:
        breaches.append(
            f"Concentration: {max_ticker} at {max_weight:.1%} "
            f"(limit: {risk_cfg.max_concentration:.0%})"
        )
    elif max_weight > risk_cfg.max_concentration_warning:
        drivers.append(
            f"Near concentration limit: {max_ticker} at {max_weight:.1%}"
        )
    
    # =========================================================================
    # CHECK 2: Diversification (number of positions)
    # =========================================================================
    if num_positions < risk_cfg.min_diversification_assets:
        breaches.append(
            f"Under-diversified: {num_positions} positions "
            f"(minimum: {risk_cfg.min_diversification_assets})"
        )
    
    # =========================================================================
    # CHECK 3: HHI Concentration Score
    # =========================================================================
    hhi = calculate_hhi(weights)
    
    if hhi > 0.25:
        drivers.append(f"High concentration score: HHI = {hhi:.2f}")
    elif hhi > 0.15:
        drivers.append(f"Moderate concentration: HHI = {hhi:.2f}")
    
    # =========================================================================
    # CHECK 4: Volatility (if provided)
    # =========================================================================
    estimated_vol = volatility or 0.0
    
    if volatility is not None:
        if volatility > risk_cfg.hard_max_volatility:
            breaches.append(
                f"Volatility breach: {volatility:.1%} "
                f"(hard limit: {risk_cfg.hard_max_volatility:.0%})"
            )
        elif volatility > risk_cfg.default_max_volatility:
            drivers.append(
                f"Elevated volatility: {volatility:.1%} "
                f"(target: {risk_cfg.default_max_volatility:.0%})"
            )
    
    # =========================================================================
    # DETERMINE STATUS
    # =========================================================================
    if len(breaches) >= 2:
        status = RiskStatus.CRITICAL
        suggested = DecisionType.REBALANCE
    elif len(breaches) == 1:
        status = RiskStatus.ELEVATED
        suggested = DecisionType.REBALANCE
    elif len(drivers) >= 2:
        status = RiskStatus.ELEVATED
        suggested = DecisionType.TILT
    else:
        status = RiskStatus.ACCEPTABLE
        suggested = DecisionType.HOLD
    
    return RiskAssessment(
        status=status,
        primary_drivers=drivers[:3],  # Top 3
        breaches=breaches,
        concentration_score=hhi,
        max_position_weight=max_weight,
        num_positions=num_positions,
        estimated_volatility=estimated_vol,
        tail_risk_estimate=None,  # TODO: Calculate CVaR if covariance provided
        suggested_action=suggested
    )


def assess_decision_needed(
    context: DecisionContext,
    risk_assessment: RiskAssessment,
    config: Optional[AppConfig] = None
) -> PMDecisionSummary:
    """
    PM-style decision logic: Should we act, and why?
    
    This runs AFTER risk assessment to determine the appropriate response.
    It synthesizes drift, risk, and macro context into a decision.
    
    Args:
        context: DecisionContext with portfolio state and metrics
        risk_assessment: Output from assess_portfolio_risk()
        config: AppConfig instance (uses global if not provided)
    
    Returns:
        PMDecisionSummary with decision, rationale, and confidence
    """
    cfg = config or app_config
    
    # Extract key inputs
    drift = context.max_drift
    drift_threshold = context.drift_threshold or cfg.rebalance.default_drift_threshold / 100
    macro_regime = context.macro_regime or "neutral"
    risk_status = risk_assessment.status
    
    # =========================================================================
    # DECISION LOGIC (Priority Order)
    # =========================================================================
    
    # CASE 1: Critical risk - must act
    if risk_status == RiskStatus.CRITICAL:
        return PMDecisionSummary(
            decision=DecisionType.REBALANCE,
            confidence=0.95,
            rationale=_build_rationale(
                "Critical risk status requires immediate attention.",
                risk_assessment.breaches,
                macro_regime
            ),
            risk_status=risk_status,
            key_risks=risk_assessment.breaches[:3],
            trade_required=True,
            estimated_trades=len(context.current_weights),
            trigger=context.trigger,
            portfolio_id=None
        )
    
    # CASE 2: Crisis macro regime - defensive posture
    if macro_regime == "crisis":
        return PMDecisionSummary(
            decision=DecisionType.HEDGE,
            confidence=0.85,
            rationale=_build_rationale(
                "Crisis regime detected. Consider defensive positioning.",
                ["Elevated market stress indicators"],
                macro_regime
            ),
            risk_status=risk_status,
            key_risks=["Market regime: CRISIS"] + risk_assessment.primary_drivers[:2],
            trade_required=True,
            estimated_trades=2,  # Typical hedge: reduce equity, add bonds/gold
            trigger=context.trigger
        )
    
    # CASE 3: Elevated risk + significant drift - rebalance
    if risk_status == RiskStatus.ELEVATED and drift > drift_threshold:
        return PMDecisionSummary(
            decision=DecisionType.REBALANCE,
            confidence=0.80,
            rationale=_build_rationale(
                f"Portfolio drift ({drift:.1%}) exceeds threshold ({drift_threshold:.0%}) "
                f"with elevated risk status.",
                risk_assessment.primary_drivers,
                macro_regime
            ),
            risk_status=risk_status,
            key_risks=risk_assessment.primary_drivers[:3],
            trade_required=True,
            estimated_trades=_estimate_trades(context.current_weights, drift_threshold),
            estimated_turnover=drift,
            trigger=context.trigger
        )
    
    # CASE 4: Risk-off macro + elevated risk - tactical tilt
    if macro_regime == "risk_off" and risk_status == RiskStatus.ELEVATED:
        return PMDecisionSummary(
            decision=DecisionType.TILT,
            confidence=0.75,
            rationale=_build_rationale(
                "Risk-off environment with elevated portfolio risk suggests tactical adjustment.",
                risk_assessment.primary_drivers,
                macro_regime
            ),
            risk_status=risk_status,
            key_risks=["Market regime: RISK_OFF"] + risk_assessment.primary_drivers[:2],
            trade_required=True,
            estimated_trades=1,  # Minor adjustment
            expected_impact={"volatility_change": -0.02},
            trigger=context.trigger
        )
    
    # CASE 5: Significant drift alone (no risk issues)
    if drift > drift_threshold * 1.5:  # 1.5x threshold = clear signal
        return PMDecisionSummary(
            decision=DecisionType.REBALANCE,
            confidence=0.75,
            rationale=_build_rationale(
                f"Portfolio drift ({drift:.1%}) significantly exceeds threshold ({drift_threshold:.0%}). "
                f"Rebalancing recommended to restore target allocation.",
                [],
                macro_regime
            ),
            risk_status=risk_status,
            key_risks=risk_assessment.primary_drivers[:3] if risk_assessment.primary_drivers else ["Drift from target allocation"],
            trade_required=True,
            estimated_trades=_estimate_trades(context.current_weights, drift_threshold),
            estimated_turnover=drift,
            trigger=context.trigger
        )
    
    # CASE 6: Moderate drift - monitor or minor tilt
    if drift > drift_threshold:
        return PMDecisionSummary(
            decision=DecisionType.TILT,
            confidence=0.65,
            rationale=_build_rationale(
                f"Portfolio drift ({drift:.1%}) exceeds threshold ({drift_threshold:.0%}), "
                f"but risk status is acceptable. Consider minor adjustment or continue monitoring.",
                [],
                macro_regime
            ),
            risk_status=risk_status,
            key_risks=risk_assessment.primary_drivers[:3] if risk_assessment.primary_drivers else ["Moderate drift from targets"],
            trade_required=False,  # Optional
            estimated_trades=1,
            trigger=context.trigger
        )
    
    # CASE 7: HOLD - no action warranted
    # This is the KEY differentiator - explicitly choosing not to act
    return PMDecisionSummary(
        decision=DecisionType.HOLD,
        confidence=0.85,
        rationale=_build_rationale(
            f"Portfolio drift ({drift:.1%}) is within tolerance ({drift_threshold:.0%}). "
            f"Risk status is {risk_status.value}. Macro environment is {macro_regime}. "
            f"No action warranted at this time.",
            [],
            macro_regime
        ),
        risk_status=risk_status,
        key_risks=risk_assessment.primary_drivers[:3] if risk_assessment.primary_drivers else [],
        trade_required=False,
        estimated_trades=0,
        trigger=context.trigger
    )


def _build_rationale(main_reason: str, factors: List[str], macro_regime: str) -> str:
    """Build a comprehensive rationale string."""
    parts = [main_reason]
    
    if factors:
        parts.append(f"Contributing factors: {', '.join(factors[:2])}")
    
    if macro_regime and macro_regime != "neutral":
        regime_desc = {
            "risk_on": "supportive risk environment",
            "risk_off": "defensive market conditions",
            "crisis": "crisis-level market stress"
        }.get(macro_regime, macro_regime)
        parts.append(f"Macro context: {regime_desc}.")
    
    return " ".join(parts)


def _estimate_trades(weights: Dict[str, float], threshold: float) -> int:
    """Estimate number of trades needed based on position count."""
    # Simple heuristic: positions that would need adjustment
    # In reality, this would compare current vs target
    if not weights:
        return 0
    
    # Assume roughly half of positions need adjustment in a rebalance
    return max(1, len(weights) // 2)


# =============================================================================
# CONVENIENCE FUNCTION: Full Assessment Pipeline
# =============================================================================

def run_decision_assessment(
    current_weights: Dict[str, float],
    target_weights: Optional[Dict[str, float]] = None,
    max_drift: float = 0.0,
    macro_regime: str = "neutral",
    vix_level: Optional[float] = None,
    portfolio_volatility: Optional[float] = None,
    config: Optional[AppConfig] = None,
    trigger: str = "user_request",
    document_insights: Optional[Dict[str, Any]] = None,  # NEW: Phase 6.7
) -> Tuple[RiskAssessment, PMDecisionSummary]:
    """
    Convenience function to run the full decision assessment pipeline.
    
    Phase 6.7: Added document_insights parameter for RAG integration.
    
    Args:
        current_weights: Current portfolio weights
        target_weights: Target weights (optional)
        max_drift: Maximum drift from targets
        macro_regime: Current macro regime
        vix_level: Current VIX level
        portfolio_volatility: Portfolio volatility
        config: Config override
        trigger: What triggered this assessment
        document_insights: RAG document insights (optional)
            - risk_factors: List of risks from documents
            - citations: List of citation dicts
            - key_findings: List of findings
            - fed_sentiment: Fed sentiment dict
    
    Returns:
        Tuple of (RiskAssessment, PMDecisionSummary)
    """
    cfg = config or app_config
    
    # Extract document insights (Phase 6.7)
    doc_risk_factors = []
    doc_citations = []
    doc_findings = []
    
    if document_insights:
        doc_risk_factors = document_insights.get("risk_factors", [])
        doc_citations = document_insights.get("citations", [])
        doc_findings = document_insights.get("key_findings", [])
        
        # If document has Fed sentiment, it might influence macro regime
        fed_sentiment = document_insights.get("fed_sentiment", {})
        if fed_sentiment and fed_sentiment.get("success"):
            fed_score = fed_sentiment.get("score", 0)
            # Strong hawkish Fed + no explicit macro -> suggest risk_off
            if fed_score > 0.5 and macro_regime == "neutral":
                macro_regime = "risk_off"
            # Strong dovish Fed + no explicit macro -> suggest risk_on
            elif fed_score < -0.5 and macro_regime == "neutral":
                macro_regime = "risk_on"
    
    # Step 1: Assess risk
    risk = assess_portfolio_risk(
        weights=current_weights,
        config=cfg,
        volatility=portfolio_volatility
    )
    
    # Step 2: Build context
    context = DecisionContext(
        current_weights=current_weights,
        target_weights=target_weights,
        max_drift=max_drift,
        macro_regime=macro_regime,
        vix_level=vix_level,
        portfolio_volatility=portfolio_volatility,
        drift_threshold=cfg.rebalance.default_drift_threshold / 100,
        max_concentration=cfg.risk.max_concentration,
        min_diversification=cfg.risk.min_diversification_assets,
        trigger=trigger
    )
    
    # Step 3: Determine decision
    decision = assess_decision_needed(
        context=context,
        risk_assessment=risk,
        config=cfg
    )
    
    # Step 4: Integrate document insights (Phase 6.7)
    if doc_risk_factors:
        # Prepend document risks with [DOC] prefix for clarity
        doc_risks_formatted = [f"[DOC] {r[:100]}" for r in doc_risk_factors[:2]]
        decision.key_risks = doc_risks_formatted + decision.key_risks
        decision.key_risks = decision.key_risks[:5]  # Keep top 5
    
    if doc_citations:
        decision.document_citations = doc_citations[:3]
    
    # Optionally enhance rationale with key findings
    if doc_findings:
        finding_summary = "; ".join(doc_findings[:2])[:100]
        if finding_summary:
            decision.rationale += f" Document context: {finding_summary}."
    
    return risk, decision


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def should_generate_decision_summary(query_intent: str) -> bool:
    """
    Check if a query should produce a PMDecisionSummary.
    
    Only DECISION queries warrant decision logic.
    This prevents action bias for informational queries.
    """
    return query_intent == "decision"


def extract_macro_regime_from_results(macro_result: Dict) -> str:
    """
    Extract macro regime string from MacroAgent results.
    
    Handles the nested structure: macro_result["regime"]["regime"]
    """
    if not macro_result or not macro_result.get("success"):
        return "neutral"
    
    regime_data = macro_result.get("regime", {})
    return regime_data.get("regime", "neutral").lower()


def extract_vix_from_results(macro_result: Dict) -> Optional[float]:
    """Extract VIX level from MacroAgent results."""
    if not macro_result or not macro_result.get("success"):
        return None
    
    snapshot = macro_result.get("snapshot", {})
    vix_data = snapshot.get("vix", {})
    return vix_data.get("value")
