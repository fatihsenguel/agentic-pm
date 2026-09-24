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

# The agent roster, stated once. Name -> the one-line description of what the
# agent does. Every other statement of the roster derives from this:
# AgentName below, and the nodes and edges of the tool graph, which graph.py
# binds to their node functions and checks against this dict at import.
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


# Valid agent names in the system: the roster above as a str Enum. Members are
# not written by hand; add an agent to AGENTS.
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
