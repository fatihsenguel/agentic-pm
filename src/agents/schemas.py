# src/agents/schemas.py
# Purpose: Pydantic models for output validation (Guardrails)
# Principle: LLMs hallucinate. Pydantic catches it before it causes harm.
# Phase: 6.12 - Output Parsers & Guardrails

from typing import List, Dict, Optional, Any, Literal, Tuple, Mapping
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import re

from .tool_inputs import TOOLS


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
    'rebalancing': 'User wants drift analysis or trade generation',
    'data_fetch': 'User wants raw price data or metrics',
    'risk_analysis': 'User wants risk metrics (VaR, volatility, drawdown)',
    'research': 'User asks whether one named company clears their investment philosophy, or how it screens against the philosophy\'s criteria (return on capital, margins, balance sheet, price against value). The philosophy is not the Investment Policy Statement: a question naming the philosophy is research even when the company is held, and compliance is only for the IPS and the portfolio. The company is screened clause by clause on its filed figures; no recommendation is made. It also covers what one named company is worth: the answer is a valuation range the pipeline computes from the owner\'s stated assumptions, never a forecast of a price, so a question about a company\'s worth or value is research, not out_of_scope. It also covers what has to be true for the owner\'s thesis on a company on their watchlist to be right: the company\'s latest annual report is read and one dated prediction about the business is proposed for the owner to enter or not, never a price and never a recommendation, so a question about the owner\'s thesis is research, not out_of_scope. It also covers whether to buy one named company: the company is screened clause by clause, valued as a range, and checked against the Investment Policy Statement at the weight the owner wrote down, and the answer says what those checks found and whether they support an entry, with its uncertainty and its reasons. That is not a bare opinion and not a price target, so "should I buy X" is research, not out_of_scope. Whether to sell or hold something already owned is not: that is out_of_scope, below.',
    'ledger': 'User asks how their predictions have done, which predictions are due, scored or still open, or what the prediction ledger says: the ledger is read as of today and every prediction is listed with its due date and its status, a due one with what the company reported against it. No company is named in such a question and no judgement is made; a question about one named company is research, above.',
    'compliance': 'User asks about their Investment Policy Statement: whether the portfolio complies with it or breaks a rule, whether a position is too big, what would have to change to be within its limits, whether a proposed weight in one position is allowed, or what the policy says about a topic',
    'clarification_needed': 'Request is in scope but too vague to plan, need to ask user',
    'out_of_scope': 'Request is clear, and what it asks for is something this system does not do: whether to sell or hold a security already owned, whether something is a good investment as a bare opinion, what the owner should buy with no company named, screening or finding candidates, a price or return forecast, tax assessment, or placing an order. Two things that look like this and are not: what a company is worth is a valuation range from the owner\'s stated assumptions, and whether to buy one named company is answered through the philosophy screen, the range and the policy check at a stated weight - both are research, above. Whether the security is held makes no difference the other way: a question about a held position\'s own figures is in scope, below. Plan NO agents, leave clarification_question null. Questions about a portfolio the user already holds - its allocation, P&L, risk, drift, whether and how to rebalance it, whether it complies with their policy - are IN scope and keep their normal intent: "Should I rebalance my portfolio?" is rebalancing, not out_of_scope and not clarification_needed, because it asks about mechanics on holdings already chosen, not about whether to own a security. A question about how a ticker the active portfolio holds has performed, gained or lost, or how large it is, is a question about that position even without the word "my": data_fetch with PortfolioAnalysisAgent, measure "position_pnl" or "allocation", tickers [that symbol] - not out_of_scope. If a request could be either an in-scope question or an out-of-scope one (e.g. "analyze X" could mean price data), that is clarification_needed, not out_of_scope: ambiguity wins over refusal.',
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
# if the binding and this dict disagree.
AGENTS: Dict[str, str] = {
    "DataAgent": "Fetches market prices, calculates covariance matrices, returns, volatility",
    "RebalanceAgent": "Calculates drift, generates trade lists for rebalancing",
    "PortfolioAnalysisAgent": "Computes figures about an EXISTING portfolio's holdings: allocation by asset class and by sector, P&L per position since purchase, and the portfolio's own volatility from its weights and the covariance matrix. Needs DataAgent first (holdings, prices, cash, covariance).",
    "ComplianceAgent": "Checks an EXISTING portfolio against the owner's Investment Policy Statement: every clause with a numeric limit, breach or headroom per clause with the distance to the limit, citing clause ids. Needs DataAgent and PortfolioAnalysisAgent first.",
    "ScreeningAgent": "Screens ONE named company against the owner's investment philosophy on its filed figures from EDGAR: one finding per numeric clause, pass or fail with the distance, citing PHI ids; a bank or insurer is excluded on its SIC code before any figure is read. Needs no other agent.",
    "LedgerAgent": "Reads the owner's prediction ledger as of today: every prediction with its due date and its status, open, due or scored; a due figure prediction's verdict from the company's filing; the counts the ledger's. Names no company. Needs no other agent.",
    "ResearchAgent": "Reads the latest annual report of ONE company on the owner's watchlist, the business, the risks and management's discussion, into claims each with its quote, and proposes one dated prediction that tests the owner's thesis on it, every number in it the pipeline's, for the owner to enter or not. Needs ScreeningAgent first.",
}


def _enum_member_name(agent: str) -> str:
    """DataAgent -> DATA_AGENT, PortfolioAnalysisAgent -> PORTFOLIO_ANALYSIS_AGENT."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", agent).upper()


# Valid agent names in the system: the roster above as a str Enum, so that
# RouterDecision.execution_order rejects any name the graph
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
# holdings, prices, as-of dates and cash; RebalanceAgent on missing prices;
# ComplianceAgent on a missing allocation when it checks the portfolio.
# RebalanceAgent's missing target is not an entry: the target is the IPS's
# (KNOWN_GAPS, "Rebalance has no target allocation source"). ComplianceAgent's
# two portfolio-free tools skip its entry: TERMINAL marks those rows unclosed.
# ResearchAgent on a missing screening block (decision 66).
REQUIRES: Dict[str, Tuple[str, ...]] = {
    "PortfolioAnalysisAgent": ("DataAgent",),
    "RebalanceAgent": ("DataAgent",),
    "ComplianceAgent": ("PortfolioAnalysisAgent",),
    "ResearchAgent": ("ScreeningAgent",),
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

class ExtractedParameters(BaseModel):
    """Parameters extracted from user input."""
    tickers: List[str] = Field(default_factory=list)
    period: Optional[str] = Field(default=None, pattern=r"^\d+[YMD]$")  # e.g., "5Y", "3M", "30D"
    max_volatility: Optional[float] = Field(default=None, ge=0.01, le=1.0)
    portfolio_value: Optional[float] = Field(default=None, gt=0)

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
    # The compliance report's selection by finding status, the model's like
    # measure and group_by: "breach" when the user asks which positions,
    # clauses or limits are over - the breach list - and null for the full
    # check. The value is the finding's own `status` word. The other
    # selection value, a named position, is `tickers`. Rendering only: the
    # node checks every clause on every run and the plan does not change.
    status: Optional[Literal["breach"]] = Field(default=None)

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

    # What a research question asks (decision 66), set by extraction from a
    # closed pattern and never by the model: "thesis", what has to be true
    # for a candidate's thesis to be right, and "position", whether to own
    # the company at the weight its entry states. Read by nothing outside
    # research. The two take different plans - a position is checked by the
    # gate against the published allocation and a thesis implies none - so
    # the two values are two tools, `thesis` and `position`.
    asks: Optional[Literal["thesis", "position"]] = Field(default=None)

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


# The terminal-agent table: tool -> (terminal, closed), one row per tool of
# agents/tool_inputs.py (decision 45). The plan for a tool is the terminal's
# requirement chain, closed upward through REQUIRES in dependency order
# (docs/DIRECTION.md: each tool's internal graph); the model never sees a
# plan. The two portfolio-free compliance tools measure no portfolio and so
# are not closed: ComplianceAgent runs alone.
#
# A row's terminal may be a tuple, closed over each name in order with each
# name once. That is how a tool needs two things finished rather than one:
# `position` needs the portfolio computed and the company screened and read,
# and neither requires the other.
TERMINAL: Dict[str, Tuple[Any, bool]] = {
    "allocation": ("PortfolioAnalysisAgent", True),
    "position_pnl": ("PortfolioAnalysisAgent", True),
    "portfolio_volatility": ("PortfolioAnalysisAgent", True),
    "compliance_check": ("ComplianceAgent", True),
    "hypothetical_weight": ("ComplianceAgent", False),
    "policy_lookup": ("ComplianceAgent", False),
    "philosophy_screen": ("ScreeningAgent", True),
    "thesis": ("ResearchAgent", True),
    "position": (("PortfolioAnalysisAgent", "ResearchAgent"), True),
    "rebalance": ("RebalanceAgent", True),
    "ledger": ("LedgerAgent", True),
}


def _terminals(terminal) -> Tuple[str, ...]:
    """A row's terminal as a tuple, one name or several."""
    return terminal if isinstance(terminal, tuple) else (terminal,)


def validate_terminal(table: Mapping[str, Tuple[Any, bool]]) -> None:
    """Every row of a terminal table: its key is a tool and its terminal
    names agents the roster has. Called on TERMINAL at import, so a table
    that cannot route fails here rather than on the first live request, and
    taken as an argument so that the checks can be shown working against a
    table that breaks them."""
    for tool, (terminal, _closed) in table.items():
        if tool not in TOOLS:
            raise RuntimeError(f"TERMINAL has a row for {tool!r}, not a tool")
        for agent in _terminals(terminal):
            if agent not in AGENTS:
                raise RuntimeError(f"TERMINAL[{tool!r}] names {agent!r}, not in the roster")


validate_terminal(TERMINAL)
if set(TERMINAL) != set(TOOLS):
    raise RuntimeError(
        "tools and terminal table disagree: tool_inputs.TOOLS has "
        f"{sorted(TOOLS)}, TERMINAL has {sorted(TERMINAL)}. A tool is added to both or to neither."
    )


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


def derive_plan(tool: str) -> List[str]:
    """The plan for a tool, from TERMINAL and REQUIRES. KeyError on a name
    that is not a tool."""
    terminal, closed = TERMINAL[tool]
    names = _terminals(terminal)
    if not closed:
        return list(names)
    plan: List[str] = []
    for name in names:
        for step in _closure(name):
            if step not in plan:
                plan.append(step)
    return plan


# --- the router's intents, read through the tools; deleted with the router ---

def router_tool(intent: str, parameters: Mapping) -> Optional[str]:
    """The tool a router intent and its parameters stand for, or None where
    the intent runs none: raw prices and the per-holding volatilities, which
    decision 45 makes no tool, and the two intents that plan nothing.
    KeyError on an intent not in the registry."""
    if intent not in INTENTS:
        raise KeyError(intent)
    if intent == "compliance":
        if parameters.get("hypothetical_weight") is not None:
            return "hypothetical_weight"
        if parameters.get("policy_topic") is not None:
            return "policy_lookup"
        return "compliance_check"
    if intent == "research":
        asks = parameters.get("asks")
        return asks if asks in ("thesis", "position") else "philosophy_screen"
    if intent in ("data_fetch", "risk_analysis"):
        return parameters.get("measure")
    return {"rebalancing": "rebalance", "ledger": "ledger"}.get(intent)


def router_plan(intent: str, parameters) -> List[str]:
    """The plan for a router intent: its tool's, DataAgent alone for an
    analysis intent with no measure, and nothing for the two that plan
    nothing."""
    parameters = parameters if isinstance(parameters, Mapping) else parameters.model_dump()
    tool = router_tool(intent, parameters)
    if tool is not None:
        return derive_plan(tool)
    return ["DataAgent"] if intent in ("data_fetch", "risk_analysis") else []


def _plan_qualifier(intent: str, parameters: Mapping) -> str:
    if intent == "compliance":
        for key in ("hypothetical_weight", "policy_topic"):
            if parameters.get(key) is not None:
                return f" for {key}"
        return " over the portfolio"
    for name in ("measure", "asks"):
        if parameters.get(name) is not None:
            return f" with {name} {parameters[name]!r}"
    return ""


class RouterDecision(BaseModel):
    """
    Validated output from the Smart Router.
    """
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    # The plan: derived by the router from the tool the intent and parameters
    # stand for (router_plan), never asked of the model. Defaults empty so a
    # decision the model wrote without it validates on its own terms.
    execution_order: List[AgentName] = Field(default_factory=list)
    
    # Extracted information
    parameters: ExtractedParameters
    
    # Router's reasoning
    reasoning: str = Field(..., min_length=10, max_length=1000)
    
    # Clarification
    clarification_question: Optional[str] = Field(default=None)
    # The record of what extraction asked back - kind, token, candidate, the
    # message - for the next turn to resolve the reply against. Written by
    # the router from extraction, never by the model: the router drops any
    # value the model sends.
    pending: Optional[Dict[str, Any]] = Field(default=None)
    # What this turn's reply was resolved from, when it was a reply to the
    # previous turn's question: {"reply": ..., "message": ...}. Written by
    # the router, never by the model.
    resolved: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        use_enum_values = True
        extra = "ignore"  # Ignore unexpected fields from LLM
    
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
        if self.intent == IntentType.OUT_OF_SCOPE and self.execution_order:
            raise ValueError(
                "execution_order must be empty when intent is out_of_scope"
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
        status = self.parameters.status
        order = [a if isinstance(a, str) else a.value for a in self.execution_order]
        if self.intent == IntentType.COMPLIANCE:
            if len(modes) == 2:
                raise ValueError(
                    "hypothetical_weight and policy_topic are two different questions; "
                    "a compliance request sets at most one"
                )
            if modes and status is not None:
                raise ValueError(
                    f"status {status!r} with {modes[0]} set: a proposed weight or a "
                    "policy lookup has no breach list; status selects from the "
                    "portfolio check only"
                )
        elif modes or status is not None:
            fields = modes + (["status"] if status is not None else [])
            raise ValueError(
                f"{fields} set under intent {self.intent!r}; they belong to intent compliance"
            )
        elif "ComplianceAgent" in order:
            raise ValueError(
                f"ComplianceAgent is planned only under intent compliance, not "
                f"{self.intent!r}; the plan is {order}"
            )
        return self

    @model_validator(mode='after')
    def validate_plan(self) -> 'RouterDecision':
        """The plan is the one router_plan derives for the intent and
        parameters, exactly. The router writes that plan over the
        model's before validation, so a mismatch here is a hand-built
        decision or a table change; the error names both plans. Never
        reordered (the "too big" flip and its diagnostics, KNOWN_GAPS,
        8 September). Runs last, after the mode checks above."""
        intent = self.intent if isinstance(self.intent, str) else self.intent.value
        order = [a if isinstance(a, str) else a.value for a in self.execution_order]
        parameters = self.parameters.model_dump()
        derived = router_plan(intent, parameters)
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