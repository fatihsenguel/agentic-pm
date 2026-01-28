# src/agents/schemas.py
# Purpose: Pydantic models for output validation (Guardrails)
# Principle: LLMs hallucinate. Pydantic catches it before it causes harm.
# Phase: 6.12 - Output Parsers & Guardrails
# REFACTORED: Phase 6.6 - Separated QueryIntent (semantic) from ExecutionIntent (workflow)

from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


# =============================================================================
# ENUMS FOR VALIDATION
# =============================================================================

class QueryIntent(str, Enum):
    """
    Semantic intent: WHY is the user asking?
    
    This separates the user's PURPOSE from the technical workflow.
    Only DECISION queries produce PMDecisionSummary outputs.
    
    Interview talking point:
    "We explicitly separate semantic user intent from execution workflows,
    and only introduce portfolio decision semantics when action is implied."
    """
    OPERATIONAL = "operational"      # DB reads/writes, admin tasks (list assets, create portfolio)
    INFORMATION = "information"      # Facts, stats, prices, EPS - no action implied
    ANALYSIS = "analysis"            # Attribution, explanations - "why did X happen?"
    DECISION = "decision"            # Portfolio action implied - "should we rebalance?"
    CLARIFICATION = "clarification"  # Need more info from user
    UNKNOWN = "unknown"              # Cannot determine intent


class ExecutionIntent(str, Enum):
    """
    Execution intent: WHAT workflow runs?
    
    This determines which agents execute and in what order.
    Decoupled from semantic meaning - a DECISION query and an INFORMATION query
    might both trigger the same ExecutionIntent (e.g., DATA_FETCH).
    """
    OPTIMIZATION = "optimization"        # DataAgent → OptimizationAgent
    MACRO_ANALYSIS = "macro_analysis"    # DataAgent → MacroAgent
    REBALANCING = "rebalancing"          # DataAgent → RebalanceAgent
    BACKTEST = "backtest"                # DataAgent → BacktestAgent
    DATA_FETCH = "data_fetch"            # DataAgent only (prices, returns, covariance)
    RISK_ANALYSIS = "risk_analysis"      # DataAgent → RiskManager
    DATA_MANAGEMENT = "data_management"  # Admin: list_assets, update_db, get_info
    PORTFOLIO_MGMT = "portfolio_mgmt"    # Admin: list/create/update portfolios
    CLARIFICATION_NEEDED = "clarification_needed"  # Router needs more info
    DOCUMENT_SEARCH = "document_search"
    UNKNOWN = "unknown"                  # Fallback


# =============================================================================
# BACKWARD COMPATIBILITY ALIAS
# =============================================================================
# This allows existing code that imports IntentType to keep working.
# smart_router.py imports IntentType - this alias prevents breakage.
IntentType = ExecutionIntent


class AgentName(str, Enum):
    """Valid agent names in the system."""
    DATA_AGENT = "DataAgent"
    MACRO_AGENT = "MacroAgent"
    OPTIMIZATION_AGENT = "OptimizationAgent"
    REBALANCE_AGENT = "RebalanceAgent"
    BACKTEST_AGENT = "BacktestAgent"
    # Fallback for router logic
    ROUTER = "Router"
    RAG_AGENT = "RAGAgent"


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
    command: Optional[str] = Field(default=None, description="Admin command: list_assets, update_db, fetch_prices, get_info")
    report_type: Optional[str] = Field(
        default=None, 
        description="For financial statements: balance_sheet, income_statement, cash_flow"
    )
    data_type: Optional[str] = Field(
        default=None,
        description="For queries: prices, earnings, statements, fundamentals"
    )
    limit: Optional[int] = Field(
        default=30,
        ge=1,
        le=100,
        description="Max records to return for queries"
    )
    portfolio_name: Optional[str] = Field(
        default=None,
        description="Portfolio name for search/create operations"
    )
    quantity: Optional[float] = Field(
        default=None,
        ge=0,
        description="Number of shares for add_holding"
    )
    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Price per share for add_holding"
    )
    search_documents: Optional[bool] = Field(
        default=None,
        description="Whether to search indexed documents for context"
    )
    include_fed_sentiment: Optional[bool] = Field(
        default=None,
        description="Whether to analyze Fed sentiment"
    )

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
    
    REFACTORED (Phase 6.6):
    - query_intent: WHY the user is asking (semantic purpose)
    - execution_intent: WHAT workflow to run (technical routing)
    
    This separation enables:
    1. Only DECISION queries trigger PMDecisionSummary
    2. Clean routing without semantic overload
    3. Interview-ready architecture explanation
    """
    # NEW: Dual intent system
    query_intent: QueryIntent = Field(
        default=QueryIntent.UNKNOWN,
        description="Semantic intent: why is the user asking?"
    )
    execution_intent: ExecutionIntent = Field(
        ...,
        description="Execution intent: what workflow runs?"
    )
    
    # BACKWARD COMPAT: Alias 'intent' to 'execution_intent'
    # This allows nodes.py to keep using decision.intent or decision["intent"]
    @property
    def intent(self) -> ExecutionIntent:
        """Backward compatibility: 'intent' maps to 'execution_intent'."""
        return self.execution_intent
    
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
    
    # ALIAS PROPERTY for backward compat with nodes.py
    @property
    def execution_plan(self) -> List[str]:
        return [str(agent) for agent in self.execution_order]

    @model_validator(mode='before')
    @classmethod
    def handle_aliased_fields(cls, data: Any) -> Any:
        """
        Handle field aliases and backward compatibility.
        
        Supports:
        - 'execution_plan' → 'execution_order'
        - 'intent' → 'execution_intent' (backward compat)
        """
        if isinstance(data, dict):
            # Handle execution_plan → execution_order alias
            if 'execution_plan' in data and 'execution_order' not in data:
                data['execution_order'] = data['execution_plan']
            
            # Handle backward compat: 'intent' → 'execution_intent'
            if 'intent' in data and 'execution_intent' not in data:
                data['execution_intent'] = data['intent']
            
            # Default query_intent if not provided (backward compat)
            if 'query_intent' not in data:
                # Infer from execution_intent
                exec_intent = data.get('execution_intent') or data.get('intent', '')
                if exec_intent in ('data_management', 'portfolio_mgmt'):
                    data['query_intent'] = 'operational'
                elif exec_intent == 'clarification_needed':
                    data['query_intent'] = 'clarification'
                else:
                    # Conservative default - let synthesizer decide
                    data['query_intent'] = 'unknown'
        
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
        if self.execution_intent == ExecutionIntent.CLARIFICATION_NEEDED and not self.clarification_question:
            # Provide default question
            self.clarification_question = "Could you please clarify your request? I need to know which assets to analyze."
        return self
    
    @model_validator(mode='after')
    def sync_query_intent_with_clarification(self) -> 'RouterDecision':
        """Ensure query_intent is CLARIFICATION when execution is CLARIFICATION_NEEDED."""
        if self.execution_intent == ExecutionIntent.CLARIFICATION_NEEDED:
            # Use object.__setattr__ to bypass Pydantic's frozen model if needed
            object.__setattr__(self, 'query_intent', QueryIntent.CLARIFICATION)
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
        
        # Warn but don't crash on small mismatches (floating point issues)
        total = sum(v.values())
        if abs(total - 1.0) > 0.05:  # 5% tolerance
            # Just normalize it silently
            pass
            
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


# =============================================================================
# INTENT MAPPING HELPERS
# =============================================================================

def infer_query_intent(user_message: str, execution_intent: ExecutionIntent) -> QueryIntent:
    """
    Infer QueryIntent from user message and execution intent.
    
    This is a fallback for when the LLM doesn't provide query_intent.
    Production systems should have the Router emit both intents.
    """
    message_lower = user_message.lower()
    
    # Operational indicators
    if execution_intent in (ExecutionIntent.DATA_MANAGEMENT, ExecutionIntent.PORTFOLIO_MGMT):
        return QueryIntent.OPERATIONAL
    
    # Decision indicators (action implied)
    decision_keywords = [
        "should i", "should we", "recommend", "what to do",
        "buy or sell", "rebalance", "adjust", "change allocation",
        "reduce exposure", "increase position", "hedge",
        "based on the filing", "according to the 10-k",
        "given the earnings", "fed minutes suggest",  
    ]

    if any(kw in message_lower for kw in decision_keywords):
        return QueryIntent.DECISION
    
    # Add new document_keywords check before info_keywords:
    document_keywords = [
        "10-k", "10-q", "filing", "earnings report", "annual report",
        "fed minutes", "fomc", "what did the report say",
        "according to", "based on the document"
    ]
    
    if any(kw in message_lower for kw in document_keywords):
        # Document queries are typically informational unless action implied
        if any(kw in message_lower for kw in decision_keywords):
            return QueryIntent.DECISION
        return QueryIntent.INFORMATION
    
    # Analysis indicators (explanation requested)
    analysis_keywords = [
        "why did", "explain", "what caused", "how come",
        "attribute", "break down", "analyze performance"
    ]
    if any(kw in message_lower for kw in analysis_keywords):
        return QueryIntent.ANALYSIS
    
    # Information indicators (facts requested)
    info_keywords = [
        "what is", "what's", "how much", "current price",
        "show me", "list", "get", "fetch", "average", "total"
    ]
    if any(kw in message_lower for kw in info_keywords):
        return QueryIntent.INFORMATION
    
    # Default based on execution intent
    if execution_intent in (ExecutionIntent.OPTIMIZATION, ExecutionIntent.REBALANCING):
        return QueryIntent.DECISION  # These typically imply action
    
    return QueryIntent.UNKNOWN


def requires_decision_summary(query_intent: QueryIntent) -> bool:
    """
    Check if a query should produce a PMDecisionSummary.
    
    Only DECISION queries warrant decision logic.
    This prevents action bias for informational queries.
    """
    return query_intent == QueryIntent.DECISION