# src/agents/decision_logger.py
"""
Decision Log Persistence

Logs every PM decision to the database for auditability.
Integrates with the decision engine to automatically log decisions.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def log_decision(
    decision_type: str,
    confidence: float,
    rationale: str,
    trigger: str,
    risk_status: Optional[str] = None,
    key_risks: Optional[List[str]] = None,
    current_weights: Optional[Dict[str, float]] = None,
    proposed_weights: Optional[Dict[str, float]] = None,
    max_drift: Optional[float] = None,
    macro_regime: Optional[str] = None,
    vix_level: Optional[float] = None,
    trade_required: bool = False,
    portfolio_id: Optional[int] = None,
    request_id: Optional[str] = None,
    user_query: Optional[str] = None,
) -> Optional[int]:
    """
    Log a PM decision to the database.
    
    Args:
        decision_type: HOLD, TILT, REBALANCE, or HEDGE
        confidence: 0.0 - 1.0
        rationale: Human-readable explanation
        trigger: What prompted this decision
        risk_status: ACCEPTABLE, ELEVATED, or CRITICAL
        key_risks: List of risk factors
        current_weights: Portfolio weights at decision time
        proposed_weights: Recommended weights (if action needed)
        max_drift: Maximum drift from target
        macro_regime: Current macro environment
        vix_level: VIX at decision time
        trade_required: Whether trades are recommended
        portfolio_id: Which portfolio this applies to
        request_id: Original request ID for tracing
        user_query: What the user asked
        
    Returns:
        decision_log_id if successful, None if failed
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import get_session, DecisionLog
        
        session = get_session()
        
        log_entry = DecisionLog(
            timestamp=datetime.utcnow(),
            portfolio_id=portfolio_id,
            decision_type=decision_type.upper(),
            confidence=confidence,
            rationale=rationale[:1000] if rationale else None,  # Truncate if too long
            trigger=trigger,
            risk_status=risk_status,
            key_risks=key_risks,
            current_weights=current_weights,
            proposed_weights=proposed_weights,
            max_drift=max_drift,
            macro_regime=macro_regime,
            vix_level=vix_level,
            trade_required=trade_required,
            executed=False,  # Not executed yet
            request_id=request_id,
            user_query=user_query[:500] if user_query else None,  # Truncate
        )
        
        session.add(log_entry)
        session.commit()
        
        log_id = log_entry.id
        session.close()
        
        logger.info(f"Logged decision: {decision_type} (id={log_id})")
        return log_id
        
    except ImportError as e:
        logger.warning(f"DecisionLog table not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to log decision: {e}")
        return None


def log_decision_from_summary(
    decision,  # PMDecisionSummary
    risk,  # RiskAssessment
    current_weights: Optional[Dict[str, float]] = None,
    proposed_weights: Optional[Dict[str, float]] = None,
    max_drift: Optional[float] = None,
    macro_regime: Optional[str] = None,
    vix_level: Optional[float] = None,
    portfolio_id: Optional[int] = None,
    request_id: Optional[str] = None,
    user_query: Optional[str] = None,
) -> Optional[int]:
    """
    Log a decision using PMDecisionSummary and RiskAssessment objects.
    
    This is the preferred method - call it from the synthesizer after
    generating a decision summary.
    
    Args:
        decision: PMDecisionSummary from decision engine
        risk: RiskAssessment from decision engine
        current_weights: Current portfolio allocation
        proposed_weights: Recommended allocation
        max_drift: Maximum weight drift
        macro_regime: Current macro regime
        vix_level: Current VIX level
        portfolio_id: Portfolio this applies to
        request_id: Request ID for tracing
        user_query: Original user query
        
    Returns:
        decision_log_id if successful, None if failed
    """
    return log_decision(
        decision_type=decision.decision.value if hasattr(decision.decision, 'value') else str(decision.decision),
        confidence=decision.confidence,
        rationale=decision.rationale,
        trigger=decision.trigger,
        risk_status=risk.status.value if hasattr(risk.status, 'value') else str(risk.status),
        key_risks=risk.drivers,
        current_weights=current_weights,
        proposed_weights=proposed_weights,
        max_drift=max_drift,
        macro_regime=macro_regime,
        vix_level=vix_level,
        trade_required=decision.trade_required,
        portfolio_id=portfolio_id,
        request_id=request_id,
        user_query=user_query,
    )


def get_decision_history(
    portfolio_id: Optional[int] = None,
    limit: int = 20,
    decision_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve decision history from the database.
    
    Args:
        portfolio_id: Filter by portfolio (None = all)
        limit: Maximum number of records to return
        decision_type: Filter by decision type (HOLD, TILT, etc.)
        
    Returns:
        List of decision log dicts, most recent first
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import get_session, DecisionLog
        
        session = get_session()
        
        query = session.query(DecisionLog)
        
        if portfolio_id:
            query = query.filter(DecisionLog.portfolio_id == portfolio_id)
        if decision_type:
            query = query.filter(DecisionLog.decision_type == decision_type.upper())
        
        query = query.order_by(DecisionLog.timestamp.desc()).limit(limit)
        
        results = []
        for log in query.all():
            results.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "portfolio_id": log.portfolio_id,
                "decision_type": log.decision_type,
                "confidence": log.confidence,
                "rationale": log.rationale,
                "trigger": log.trigger,
                "risk_status": log.risk_status,
                "key_risks": log.key_risks,
                "trade_required": log.trade_required,
                "executed": log.executed,
                "max_drift": log.max_drift,
                "macro_regime": log.macro_regime,
                "vix_level": log.vix_level,
            })
        
        session.close()
        return results
        
    except ImportError as e:
        logger.warning(f"DecisionLog table not available: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to get decision history: {e}")
        return []


def mark_decision_executed(decision_log_id: int) -> bool:
    """
    Mark a decision as executed.
    
    Call this after trades have been placed.
    
    Args:
        decision_log_id: ID of the decision log entry
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import get_session, DecisionLog
        
        session = get_session()
        
        log_entry = session.query(DecisionLog).filter(DecisionLog.id == decision_log_id).first()
        
        if log_entry:
            log_entry.executed = True
            log_entry.execution_timestamp = datetime.utcnow()
            session.commit()
            session.close()
            return True
        
        session.close()
        return False
        
    except Exception as e:
        logger.error(f"Failed to mark decision executed: {e}")
        return False


def get_decision_stats(portfolio_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
    """
    Get decision statistics for a portfolio.
    
    Args:
        portfolio_id: Portfolio to analyze (None = all)
        days: Number of days to look back
        
    Returns:
        Dict with decision counts, execution rates, etc.
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import get_session, DecisionLog
        from datetime import timedelta
        
        session = get_session()
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = session.query(DecisionLog).filter(DecisionLog.timestamp >= cutoff)
        
        if portfolio_id:
            query = query.filter(DecisionLog.portfolio_id == portfolio_id)
        
        logs = query.all()
        
        stats = {
            "total_decisions": len(logs),
            "by_type": {},
            "trades_required": 0,
            "trades_executed": 0,
            "avg_confidence": 0.0,
        }
        
        if logs:
            confidence_sum = 0
            for log in logs:
                # Count by type
                dtype = log.decision_type
                stats["by_type"][dtype] = stats["by_type"].get(dtype, 0) + 1
                
                # Count trades
                if log.trade_required:
                    stats["trades_required"] += 1
                if log.executed:
                    stats["trades_executed"] += 1
                
                # Sum confidence
                confidence_sum += log.confidence
            
            stats["avg_confidence"] = confidence_sum / len(logs)
            stats["execution_rate"] = (
                stats["trades_executed"] / stats["trades_required"] 
                if stats["trades_required"] > 0 else 0
            )
        
        session.close()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get decision stats: {e}")
        return {"error": str(e)}
