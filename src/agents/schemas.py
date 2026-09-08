# src/agents/schemas.py
# Purpose: Pydantic models for output validation (Guardrails)
# Principle: LLMs hallucinate. Pydantic catches it before it causes harm.
# Phase: 6.12 - Output Parsers & Guardrails

from typing import List, Dict, Optional, Any, Literal, Tuple, Mapping
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import re


# =============================================================================
# ENUMS FOR VALIDATION
# =============================================================================

# The intent vocabulary, stated once. Value -> the one-line description the
# router prompt renders, in the order the prompt lists them. Every other
# statement derives from or is checked against this: IntentType below, the
# INTENT TYPES block and the schema's "intent" line in both prompts
# (router_prompts.py), and the synthesizer's dispatch chain, which nodes.py
# holds to this set at import. The descriptions are the prompt's text, moved
# and not edited; the prompt shrink is its own change with its own golden runs.
INTENTS: Dict[str, str] = {
    'optimization': 'User wants to create or optimize a portfolio',
    'macro_analysis': 'User asks about market conditions, VIX, yields',
    'rebalancing': 'User wants drift analysis or trade generation',
    'backtest': 'User wants historical simulation',
    'data_fetch': 'User wants raw price data or metrics',
    'risk_analysis': 'User wants risk metrics (VaR, volatility, drawdown)',
    'compliance': 'User asks about their Investment Policy Statement: whether the portfolio complies with it or breaks a rule, whether a position is too big, what would have to change to be within its limits, whether a proposed weight in one position is allowed, or what the policy says about a topic',
    'combined': 'Multi-step workflow requiring multiple agents in sequence',
    'clarification_needed': 'Request is in scope but too vague to plan, need to ask user',
    'out_of_scope': 'Request is clear, and what it asks for is something this system does not do: a judgement about whether to own a security (should I buy/sell/hold X, is X a good investment, what should I buy, screening or finding candidates), a price or return forecast, tax assessment, or placing an order. Whether the security is held makes no difference to refusing that judgement - and no difference the other way: a question about a held position\'s own figures is in scope, below. Plan NO agents, leave clarification_question null. Questions about a portfolio the user already holds - its allocation, P&L, risk, drift, whether and how to rebalance it, whether it complies with their policy - are IN scope and keep their normal intent: "Should I rebalance my portfolio?" is rebalancing, not out_of_scope and not clarification_needed, because it asks about mechanics on holdings already chosen, not about whether to own a security. A question about how a ticker the active portfolio holds has performed, gained or lost, or how large it is, is a question about that position even without the word "my": data_fetch with PortfolioAnalysisAgent, measure "position_pnl" or "allocation", tickers [that symbol] - not out_of_scope. If a request could be either an in-scope question or an out-of-scope one (e.g. "analyze X" could mean price data), that is clarification_needed, not out_of_scope: ambiguity wins over refusal.',
}


# Valid intents: the registry above as a str Enum, so that RouterDecision.intent
# rejects any value the graph cannot route. Members are not written by hand;
# add an intent to INTENTS.
IntentType = Enum(
    "IntentType",
    {value.upper(): value for value in INTENTS},
    type=str,
)


# The agent roster, stated once. Name -> the one-line description the router
# prompt renders, in the order the prompt lists them. Every other statement of
# the roster derives from this: AgentName below, the AVAILABLE AGENTS block and
# its count in router_prompts.py, and the nodes, routing map and loop edges in
# graph.py, which binds each name to its node function and raises at import
# if the binding and this dict disagree. RiskManagerAgent is absent on
# purpose: it is an unwired supervisor, not an agent the graph runs.
AGENTS: Dict[str, str] = {
    "DataAgent": "Fetches market prices, calculates covariance matrices, returns, volatility",
    "MacroAgent": "Analyzes VIX, yield curve, market regime (risk-on/risk-off)",
    "OptimizationAgent": "Runs portfolio optimization (Mean-Variance, Risk Parity, etc.)",
    "RebalanceAgent": "Calculates drift, generates trade lists for rebalancing",
    "BacktestAgent": "Runs historical simulations of portfolio strategies",
    "PortfolioAnalysisAgent": "Computes figures about an EXISTING portfolio's holdings: allocation by asset class and by sector, P&L per position since purchase, and the portfolio's own volatility from its weights and the covariance matrix. Needs DataAgent first (holdings, prices, cash, covariance).",
    "ComplianceAgent": "Checks an EXISTING portfolio against the owner's Investment Policy Statement: every clause with a numeric limit, breach or headroom per clause with the distance to the limit, citing clause ids. Needs DataAgent and PortfolioAnalysisAgent first.",
}


def _enum_member_name(agent: str) -> str:
    """DataAgent -> DATA_AGENT, PortfolioAnalysisAgent -> PORTFOLIO_ANALYSIS_AGENT."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", agent).upper()


# Valid agent names in the system: the roster above as a str Enum, so that
# AgentTask.agent and RouterDecision.execution_order reject any name the graph
# cannot run. Members are not written by hand; add an agent to AGENTS.
AgentName = Enum(
    "AgentName",
    {_enum_member_name(name): name for name in AGENTS},
    type=str,
)


# What an agent needs to have run before it, stated once beside the roster.
# Every node raises on input an earlier agent did not publish, but only the
# validator sees the plan before anything runs: an entry here turns a raise
# discovered mid-run into a rejection the router is asked to repair. Each
# entry is a raise verified at the node: PortfolioAnalysisAgent on missing
# holdings, prices, as-of dates and cash; OptimizationAgent on missing
# tickers, expected returns and covariance; BacktestAgent on missing
# optimal_weights; RebalanceAgent on missing prices; ComplianceAgent on a
# missing allocation when it checks the portfolio. RebalanceAgent's missing
# target is not an entry on the optimiser: the target is the IPS's to state
# (KNOWN_GAPS, "Rebalance has no target allocation source"). ComplianceAgent's
# two portfolio-free modes skip its entry: TERMINAL marks those rows unclosed.
REQUIRES: Dict[str, Tuple[str, ...]] = {
    "PortfolioAnalysisAgent": ("DataAgent",),
    "OptimizationAgent": ("DataAgent",),
    "BacktestAgent": ("DataAgent", "OptimizationAgent"),
    "RebalanceAgent": ("DataAgent",),
    "ComplianceAgent": ("PortfolioAnalysisAgent",),
}

_named_in_requires = set(REQUIRES) | {n for needs in REQUIRES.values() for n in needs}
if _named_in_requires - set(AGENTS):
    raise RuntimeError(
        "REQUIRES names agents not in the roster: "
        f"{sorted(_named_in_requires - set(AGENTS))}; schemas.AGENTS has {sorted(AGENTS)}"
    )


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
    # How to break an allocation down. Each value is a view the agent
    # publishes under allocation.by_<value>; position is Part 7's IPS-4.1
    # table, largest first. Only dimensions that are computed: industry and
    # country exist on Asset but nothing groups by them yet.
    group_by: Optional[Literal["asset_class", "sector", "position"]] = Field(default=None)

    # The compliance modes (intent "compliance"), decided by which of these is
    # set. Neither: check the existing portfolio against the policy.
    # hypothetical_weight: the share of total the user proposes to put into one
    # position, as a fraction; refused or permitted against the concentration
    # limits with no portfolio measured (benchmark 3.1). policy_topic: what the
    # user asks the policy about - one of the topics ips.toml carries, or the
    # user's own words when none fits, in which case the policy contains
    # nothing on it (3.4). Both set is a contradiction and is rejected.
    hypothetical_weight: Optional[float] = Field(default=None, gt=0, le=1.0)
    policy_topic: Optional[str] = Field(default=None)

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


# The terminal-agent table: intent -> discriminator -> (terminal, closed).
# The plan for a request is the terminal's requirement chain, closed upward
# through REQUIRES in dependency order; the model's plan is never read for
# these intents (docs/DIRECTION.md: plans derived from intent through a
# dependency table, which becomes each tool's internal graph). The
# discriminator is a parameter that decides the terminal: "" is the row with
# none set; "measure" is the row for either analysis intent when the model
# set a measure; the two compliance modes are the rows for a hypothetical
# weight or a policy topic, which measure no portfolio and so are not closed
# - ComplianceAgent runs alone. "combined" has no terminal: the two taught
# macro sequences are the model's plan, held to REQUIRES like any other.
TERMINAL: Dict[str, Optional[Dict[str, Tuple[Optional[str], bool]]]] = {
    "optimization": {"": ("OptimizationAgent", True)},
    "macro_analysis": {"": ("MacroAgent", True)},
    "rebalancing": {"": ("RebalanceAgent", True)},
    "backtest": {"": ("BacktestAgent", True)},
    "data_fetch": {"": ("DataAgent", True), "measure": ("PortfolioAnalysisAgent", True)},
    "risk_analysis": {"": ("DataAgent", True), "measure": ("PortfolioAnalysisAgent", True)},
    "compliance": {
        "": ("ComplianceAgent", True),
        "hypothetical_weight": ("ComplianceAgent", False),
        "policy_topic": ("ComplianceAgent", False),
    },
    "combined": None,
    "clarification_needed": {"": (None, True)},
    "out_of_scope": {"": (None, True)},
}

if set(TERMINAL) != set(INTENTS):
    raise RuntimeError(
        "intent registry and terminal table disagree: schemas.INTENTS has "
        f"{sorted(INTENTS)}, TERMINAL has {sorted(TERMINAL)}. An intent is added to both or to neither."
    )
for _intent, _rows in TERMINAL.items():
    for _key, (_terminal, _) in (_rows or {}).items():
        if _key and _key not in ExtractedParameters.model_fields:
            raise RuntimeError(f"TERMINAL[{_intent!r}] discriminates on {_key!r}, not a parameter")
        if _terminal is not None and _terminal not in AGENTS:
            raise RuntimeError(f"TERMINAL[{_intent!r}] names {_terminal!r}, not in the roster")


def _closure(agent: str) -> List[str]:
    """The agent after everything REQUIRES says it needs, transitively,
    each name once, in dependency order."""
    out: List[str] = []
    for need in REQUIRES.get(agent, ()):
        for name in _closure(need):
            if name not in out:
                out.append(name)
    out.append(agent)
    return out


def _discriminator(intent: str, parameters: Mapping) -> str:
    rows = TERMINAL[intent]
    for key in rows:
        if key and parameters.get(key) is not None:
            return key
    return ""


def derive_plan(intent: str, parameters) -> Optional[List[str]]:
    """The plan for an intent and its parameters, from TERMINAL and REQUIRES.

    None for an intent with no terminal (combined), where the model's plan
    stands. An empty list for an intent that runs nothing. KeyError on an
    intent not in the registry.
    """
    parameters = parameters if isinstance(parameters, Mapping) else parameters.model_dump()
    rows = TERMINAL[intent]
    if rows is None:
        return None
    terminal, closed = rows[_discriminator(intent, parameters)]
    if terminal is None:
        return []
    return _closure(terminal) if closed else [terminal]


def _plan_qualifier(intent: str, parameters: Mapping) -> str:
    key = _discriminator(intent, parameters)
    if intent == "compliance":
        return f" for {key}" if key else " over the portfolio"
    return f" with {key} {parameters.get(key)!r}" if key else ""


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

    @model_validator(mode='after')
    def validate_compliance(self) -> 'RouterDecision':
        """The compliance modes belong to intent compliance and at most one
        is set; ComplianceAgent is planned under no other intent - no
        formatter reads it there. The shape of a compliance plan itself is
        validate_plan's, from the table."""
        modes = [k for k in ("hypothetical_weight", "policy_topic")
                 if getattr(self.parameters, k) is not None]
        order = [a if isinstance(a, str) else a.value for a in self.execution_order]
        if self.intent == IntentType.COMPLIANCE:
            if len(modes) == 2:
                raise ValueError(
                    "hypothetical_weight and policy_topic are two different questions; "
                    "a compliance request sets at most one"
                )
        elif modes:
            raise ValueError(
                f"{modes} set under intent {self.intent!r}; they belong to intent compliance"
            )
        elif "ComplianceAgent" in order:
            raise ValueError(
                f"ComplianceAgent is planned only under intent compliance, not "
                f"{self.intent!r}; the plan is {order}"
            )
        return self

    @model_validator(mode='after')
    def validate_plan(self) -> 'RouterDecision':
        """The plan is the one TERMINAL and REQUIRES derive for the intent
        and parameters, exactly. The router writes that plan over the
        model's before validation, so a mismatch here is a hand-built
        decision or a table change; the error names both plans. Under
        combined, where the model's plan stands, every agent must follow
        what REQUIRES says it needs - never reordered, the error going back
        as the repair prompt (the "too big" flip and its diagnostics,
        KNOWN_GAPS, 8 September). Runs last, after validate_execution_order's
        autofill and the mode checks above."""
        intent = self.intent if isinstance(self.intent, str) else self.intent.value
        order = [a if isinstance(a, str) else a.value for a in self.execution_order]
        parameters = self.parameters.model_dump()
        derived = derive_plan(intent, parameters)
        if derived is None:
            for i, agent in enumerate(order):
                missing = [need for need in REQUIRES.get(agent, ()) if need not in order[:i]]
                if missing:
                    raise ValueError(
                        f"{agent} requires {', '.join(missing)} before it in "
                        f"execution_order; the plan is {order}"
                    )
            return self
        if order != derived:
            raise ValueError(
                f"a {intent} plan{_plan_qualifier(intent, parameters)} is {derived}, not {order}"
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