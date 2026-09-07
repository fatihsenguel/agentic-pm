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
    OUT_OF_SCOPE = "out_of_scope"  # Clear request for something the system does not do


class AgentName(str, Enum):
    """Valid agent names in the system."""
    DATA_AGENT = "DataAgent"
    MACRO_AGENT = "MacroAgent"
    OPTIMIZATION_AGENT = "OptimizationAgent"
    REBALANCE_AGENT = "RebalanceAgent"
    BACKTEST_AGENT = "BacktestAgent"
    PORTFOLIO_ANALYSIS_AGENT = "PortfolioAnalysisAgent"
    # Fallback for router logic
    ROUTER = "Router"


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
    portfolio_id: Optional[int] = Field(default=None, description="Portfolio ID if analyzing a saved portfolio")

    # Which figure a portfolio-analysis question asks for. Each value is the
    # key PortfolioAnalysisAgent publishes it under in shared_data, so the
    # router's vocabulary, the synthesizer's dispatch and the benchmark
    # runner's probes share one word. A value with no computation behind it
    # does not belong here - the schema must not be wider than the code.
    measure: Optional[Literal["allocation", "position_pnl", "portfolio_volatility"]] = Field(default=None)
    # How to break an allocation down. Only dimensions that are computed;
    # industry and country exist on Asset but nothing groups by them yet.
    group_by: Optional[Literal["asset_class", "sector"]] = Field(default=None)

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
    """
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    # Agent execution plan
    agents_needed: List[AgentTask]
    execution_order: List[AgentName] = Field(default_factory=list)
    
    # Extracted information
    parameters: ExtractedParameters
    
    # For multi-step workflows
    is_multi_step: bool = Field(default=False)
    requires_confirmation: bool = Field(default=False)
    
    # Router's reasoning
    reasoning: str = Field(..., min_length=10, max_length=1000)
    
    # Clarification
    clarification_question: Optional[str] = Field(default=None)
    
    class Config:
        use_enum_values = True
        extra = "ignore"  # Ignore unexpected fields from LLM
    
    # ✅ FIX: ALIAS PROPERTY
    # This allows nodes.py to call decision.execution_plan safely
    @property
    def execution_plan(self) -> List[str]:
        return [str(agent) for agent in self.execution_order]

    @model_validator(mode='before')
    @classmethod
    def handle_aliased_fields(cls, data: Any) -> Any:
        """Allow LLM to send 'execution_plan' OR 'execution_order'."""
        if isinstance(data, dict):
            # If LLM sent 'execution_plan', map it to 'execution_order'
            if 'execution_plan' in data and 'execution_order' not in data:
                data['execution_order'] = data['execution_plan']
        return data

    @model_validator(mode='after')
    def validate_execution_order(self) -> 'RouterDecision':
        """Ensure execution_order matches agents_needed."""
        # Extract agent names from tasks
        task_agents = {task.agent for task in self.agents_needed}
        
        # If execution_order is empty but agents exist, autofill it
        if not self.execution_order and self.agents_needed:
            self.execution_order = [task.agent for task in self.agents_needed]
            
        # Verify consistency
        order_names = set(self.execution_order)
        if task_agents != order_names:
            # Auto-correct if possible (LLM often gets this wrong)
            if len(task_agents) == len(self.agents_needed):
                self.execution_order = [task.agent for task in self.agents_needed]
        
        return self
    
    @model_validator(mode='after')
    def validate_clarification(self) -> 'RouterDecision':
        """If clarification needed, must have question."""
        if self.intent == IntentType.CLARIFICATION_NEEDED and not self.clarification_question:
            raise ValueError(
                "clarification_question is required when intent is clarification_needed"
            )
        return self

    @model_validator(mode='after')
    def validate_out_of_scope(self) -> 'RouterDecision':
        """An out-of-scope request plans nothing. A plan alongside the
        refusal would be trimmed by nothing downstream and run as planned,
        so it is rejected here rather than repaired."""
        if self.intent == IntentType.OUT_OF_SCOPE and (
            self.agents_needed or self.execution_order
        ):
            raise ValueError(
                "agents_needed and execution_order must be empty when intent is out_of_scope"
            )
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
        if not v:
            return v

        negative = {k: w for k, w in v.items() if w < 0}
        if negative:
            raise ValueError(f"Negative weights not allowed: {negative}")

        total = sum(v.values())
        if abs(total - 1.0) > 0.05:  # 5% tolerance
            raise ValueError(f"Weights must sum to 1.0 (+/-0.05), got {total:.4f}")

        return v


class RebalanceProposal(BaseModel):
    """Complete rebalance proposal with validation."""
    should_rebalance: bool
    recommendation: Literal["full_rebalance", "partial_rebalance", "no_action"]
    max_drift: float = Field(..., ge=0, le=1)
    trades: List[TradeProposal] = Field(default_factory=list)
    total_transaction_cost: float = Field(default=0, ge=0)
    estimated_tax: float = Field(default=0, ge=0)


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
        if not self.success and not self.error:
            self.error = "Unknown error occurred"
        return self


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def safe_parse_router_response(raw_response: Dict[str, Any]) -> tuple[Optional[RouterDecision], Optional[str]]:
    """
    Safely parse router response, returning (decision, error).
    """
    try:
        decision = RouterDecision.model_validate(raw_response)
        return decision, None
    except Exception as e:
        return None, str(e)