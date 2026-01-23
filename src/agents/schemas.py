# src/agents/schemas.py
# Purpose: Pydantic models for output validation (Guardrails)
# Principle: LLMs hallucinate. Pydantic catches it before it causes harm.
# Phase: 6.12 - Output Parsers & Guardrails

from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


# =============================================================================
# ENUMS FOR VALIDATION
# =============================================================================

class IntentType(str, Enum):
    """Valid intent types the router can detect."""
    OPTIMIZATION = "optimization"
    MACRO_ANALYSIS = "macro_analysis"
    REBALANCING = "rebalancing"
    BACKTEST = "backtest"
    DATA_FETCH = "data_fetch"
    RISK_ANALYSIS = "risk_analysis"
    COMBINED = "combined"  # Multi-step workflows
    UNKNOWN = "unknown"
    CLARIFICATION_NEEDED = "clarification_needed"


class AgentName(str, Enum):
    """Valid agent names in the system."""
    DATA_AGENT = "DataAgent"
    MACRO_AGENT = "MacroAgent"
    OPTIMIZATION_AGENT = "OptimizationAgent"
    REBALANCE_AGENT = "RebalanceAgent"
    BACKTEST_AGENT = "BacktestAgent"


class TradeAction(str, Enum):
    """Valid trade actions."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# =============================================================================
# ROUTER OUTPUT SCHEMAS
# =============================================================================

class AgentTask(BaseModel):
    """A single task to be executed by an agent."""
    agent: AgentName
    task_description: str = Field(..., min_length=5, max_length=500)
    depends_on: Optional[List[AgentName]] = Field(default=None)
    priority: int = Field(default=1, ge=1, le=10)
    
    class Config:
        use_enum_values = True


class ExtractedParameters(BaseModel):
    """Parameters extracted from user input."""
    tickers: List[str] = Field(default_factory=list)
    period: Optional[str] = Field(default=None, pattern=r"^\d+[YMD]$")  # e.g., "5Y", "3M", "30D"
    max_volatility: Optional[float] = Field(default=None, ge=0.01, le=1.0)
    target_return: Optional[float] = Field(default=None, ge=-1.0, le=5.0)
    portfolio_value: Optional[float] = Field(default=None, gt=0)
    rebalance_threshold: Optional[float] = Field(default=None, ge=0.01, le=0.5)
    
    @field_validator('tickers')
    @classmethod
    def validate_tickers(cls, v: List[str]) -> List[str]:
        """Validate ticker format (basic validation)."""
        validated = []
        for ticker in v:
            ticker = ticker.upper().strip()
            # Basic format: 1-5 uppercase letters, optionally with numbers
            if ticker and 1 <= len(ticker) <= 6 and ticker.replace('.', '').replace('-', '').isalnum():
                validated.append(ticker)
        return validated


class RouterDecision(BaseModel):
    """
    Validated output from the Smart Router.
    
    This is what the LLM returns after analyzing user intent.
    Pydantic ensures no hallucinated agents or invalid parameters.
    """
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    # Agent execution plan
    agents_needed: List[AgentTask]
    execution_order: List[AgentName]  # Sequential execution order
    
    # Extracted information
    parameters: ExtractedParameters
    
    # For multi-step workflows
    is_multi_step: bool = Field(default=False)
    requires_confirmation: bool = Field(default=False)
    
    # Router's reasoning (for debugging/tracing)
    reasoning: str = Field(..., min_length=10, max_length=1000)
    
    # If clarification needed
    clarification_question: Optional[str] = Field(default=None)
    
    class Config:
        use_enum_values = True
    
    @model_validator(mode='after')
    def validate_execution_order(self) -> 'RouterDecision':
        """Ensure execution_order matches agents_needed."""
        agent_names = {task.agent for task in self.agents_needed}
        order_names = set(self.execution_order)
        
        if agent_names != order_names:
            raise ValueError(
                f"execution_order {order_names} doesn't match agents_needed {agent_names}"
            )
        return self
    
    @model_validator(mode='after')
    def validate_clarification(self) -> 'RouterDecision':
        """If clarification needed, must have question."""
        if self.intent == IntentType.CLARIFICATION_NEEDED and not self.clarification_question:
            raise ValueError("clarification_question required when intent is CLARIFICATION_NEEDED")
        return self


# =============================================================================
# TRADE & PORTFOLIO SCHEMAS
# =============================================================================

class TradeProposal(BaseModel):
    """A single validated trade proposal."""
    ticker: str = Field(..., min_length=1, max_length=10)
    action: TradeAction
    shares: float = Field(..., gt=0)
    estimated_price: Optional[float] = Field(default=None, gt=0)
    estimated_value: Optional[float] = Field(default=None)
    reason: Optional[str] = Field(default=None)
    
    @field_validator('ticker')
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        """Basic ticker format validation."""
        v = v.upper().strip()
        if not v or len(v) > 10:
            raise ValueError(f"Invalid ticker format: {v}")
        return v


class PortfolioWeights(BaseModel):
    """Validated portfolio weights."""
    weights: Dict[str, float]
    
    @field_validator('weights')
    @classmethod
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Ensure weights sum to ~1.0 and are non-negative."""
        if not v:
            raise ValueError("Weights cannot be empty")
        
        total = sum(v.values())
        if abs(total - 1.0) > 0.02:  # 2% tolerance
            raise ValueError(f"Weights must sum to 1.0 (±2%), got {total:.4f}")
        
        for ticker, weight in v.items():
            if weight < 0:
                raise ValueError(f"Negative weight for {ticker}: {weight}")
            if weight > 1:
                raise ValueError(f"Weight > 100% for {ticker}: {weight}")
        
        return v


class RebalanceProposal(BaseModel):
    """Complete rebalance proposal with validation."""
    should_rebalance: bool
    recommendation: Literal["full_rebalance", "partial_rebalance", "no_action"]
    max_drift: float = Field(..., ge=0, le=1)
    trades: List[TradeProposal] = Field(default_factory=list)
    total_transaction_cost: float = Field(default=0, ge=0)
    estimated_tax: float = Field(default=0, ge=0)
    
    @model_validator(mode='after')
    def validate_rebalance_consistency(self) -> 'RebalanceProposal':
        """Ensure recommendation matches should_rebalance."""
        if self.should_rebalance and self.recommendation == "no_action":
            raise ValueError("should_rebalance=True but recommendation is no_action")
        if not self.should_rebalance and self.recommendation != "no_action":
            raise ValueError("should_rebalance=False but recommendation is not no_action")
        return self


# =============================================================================
# MACRO & REGIME SCHEMAS
# =============================================================================

class RegimeType(str, Enum):
    """Market regime classification."""
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"
    CRISIS = "crisis"


class MacroSnapshot(BaseModel):
    """Validated macro environment snapshot."""
    vix_level: float = Field(..., ge=0, le=100)
    vix_regime: Literal["low", "normal", "elevated", "high", "extreme"]
    yield_curve_slope: float = Field(..., ge=-5, le=5)  # In percentage points
    yield_curve_status: Literal["normal", "flat", "inverted"]
    regime: RegimeType
    equity_adjustment: float = Field(..., ge=-0.5, le=0.5)  # -50% to +50%
    confidence: float = Field(..., ge=0, le=1)
    rationale: List[str] = Field(default_factory=list)


# =============================================================================
# AGENT RESPONSE SCHEMAS
# =============================================================================

class AgentResponse(BaseModel):
    """Standard response format from any agent."""
    success: bool
    agent_name: str
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = Field(default=None)
    warnings: List[str] = Field(default_factory=list)
    tokens_used: Optional[int] = Field(default=None, ge=0)
    duration_ms: Optional[int] = Field(default=None, ge=0)
    
    @model_validator(mode='after')
    def validate_error_on_failure(self) -> 'AgentResponse':
        """If not successful, should have error message."""
        if not self.success and not self.error:
            self.error = "Unknown error occurred"
        return self


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def parse_router_response(raw_response: Dict[str, Any]) -> RouterDecision:
    """
    Parse and validate raw LLM response into RouterDecision.
    
    Raises ValidationError if response is invalid.
    """
    return RouterDecision.model_validate(raw_response)


def parse_weights(raw_weights: Dict[str, Any]) -> PortfolioWeights:
    """Parse and validate portfolio weights."""
    return PortfolioWeights(weights=raw_weights)


def safe_parse_router_response(raw_response: Dict[str, Any]) -> tuple[Optional[RouterDecision], Optional[str]]:
    """
    Safely parse router response, returning (decision, error).
    
    Returns:
        (RouterDecision, None) on success
        (None, error_message) on failure
    """
    try:
        decision = RouterDecision.model_validate(raw_response)
        return decision, None
    except Exception as e:
        return None, str(e)
