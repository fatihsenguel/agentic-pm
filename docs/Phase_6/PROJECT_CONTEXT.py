"""
🚀 PROJECT CONTEXT: QUANT PORTFOLIO MANAGER
============================================
Multi-Agent System for Institutional Portfolio Management

PURPOSE: This file contains everything an LLM needs to understand the project.
         Upload this + ROADMAP + tree when starting a new chat.

LAST UPDATED: Phase 6.3 Complete (Observability)
VERSION: 0.6.0

=============================================================================
SECTION 1: ARCHITECTURE OVERVIEW
=============================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                    │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OBSERVABILITY LAYER                                  │
│                    (Tracer, TokenCounter, CostCalculator)                    │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      🎯 RISK MANAGER AGENT (Supervisor)                      │
│                   Parses intent, validates, routes to workers                │
└───────────┬─────────────────┬─────────────────┬─────────────────┬───────────┘
            │                 │                 │                 │
            ▼                 ▼                 ▼                 ▼
     ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
     │ 📊 DATA  │      │ 🌍 MACRO │      │ ⚖️ REBAL │      │ 📈 BACK  │
     │  AGENT   │      │  AGENT   │      │  AGENT   │      │  TEST    │
     └────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOL LAYER                                      │
│         (data_tools, macro_tools, rebalance_tools, analytics_tools)          │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SERVICE LAYER                                      │
│                  (DataManager, QuotaManager, MetricsCalculator)              │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROVIDER LAYER                                     │
│                         (YFinanceProvider)                                   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SQLite DB                                       │
│              (daily_prices, macro_data, assets, portfolios)                  │
└─────────────────────────────────────────────────────────────────────────────┘

=============================================================================
SECTION 2: DESIGN PRINCIPLES (CRITICAL - MUST FOLLOW!)
=============================================================================

1. SEPARATION OF CONCERNS (SoC):
   ├── DataManager    → ONLY CRUD/DB operations
   ├── MetricsCalc    → ONLY math computations  
   ├── Provider       → ONLY external API calls
   ├── Tools          → ONLY agent interface (thin wrapper)
   └── Agent          → ONLY orchestration & decisions

2. HOT POTATO PRINCIPLE (🥔):
   ├── LLMs NEVER receive raw data (no DataFrames, no 1000-row CSVs!)
   ├── Each layer AGGREGATES before passing up
   └── Agent receives: {"return": "13.6%", "vol": "12%"} NOT [list of 1000 prices]

3. IDEMPOTENT OPERATIONS:
   └── All DB writes: INSERT ... ON CONFLICT (ticker, date) DO UPDATE
       Safe to retry. No duplicates.

4. DETERMINISTIC MATH:
   ├── Rebalancing = Pure scipy/numpy (NO LLM!)
   ├── Optimization = Pure scipy/numpy (NO LLM!)
   └── Same inputs ALWAYS produce same outputs (auditable)

5. AGENT-READY RESPONSES:
   └── All tools return: {"success": bool, "data": {...}, "error": Optional[str]}

6. SESSION ISOLATION:
   └── DataManager and QuotaManager use SEPARATE DB sessions (no SQLite locks)

=============================================================================
SECTION 3: PROTOCOLS & DATA STRUCTURES
=============================================================================
"""

from typing import List, Dict, Optional, Any, Callable, Protocol
from enum import Enum
from dataclasses import dataclass, field
from datetime import date, datetime

# ─────────────────────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────────────────────

class TaskType(Enum):
    """What the user wants to do."""
    OPTIMIZE = "optimize"           # Create optimal portfolio
    BACKTEST = "backtest"           # Historical simulation
    ANALYZE_REGIME = "analyze_regime"  # Macro environment check
    REBALANCE = "rebalance"         # Drift analysis & trades

class OptimizationMethod(Enum):
    """Portfolio optimization algorithms."""
    MEAN_VARIANCE = "mean_variance"     # Markowitz
    MIN_VARIANCE = "min_variance"       # Minimum volatility
    MAX_SHARPE = "max_sharpe"           # Maximum Sharpe ratio
    RISK_PARITY = "risk_parity"         # Equal risk contribution

class RegimeType(Enum):
    """Market regime classification."""
    RISK_ON = "risk_on"         # VIX < 15, positive slope
    RISK_OFF = "risk_off"       # VIX > 25
    NEUTRAL = "neutral"         # Normal conditions
    CRISIS = "crisis"           # VIX > 35, inverted yield curve

class RebalanceFrequency(Enum):
    """How often to rebalance."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

# ─────────────────────────────────────────────────────────────────────────────
# CORE DTOs (Data Transfer Objects)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PortfolioConstraints:
    """Investment constraints for optimization."""
    min_weight: float = 0.0          # Minimum per asset (e.g., 0.05 = 5%)
    max_weight: float = 1.0          # Maximum per asset (e.g., 0.40 = 40%)
    max_volatility: Optional[float] = None  # Portfolio vol cap (e.g., 0.15)
    max_drawdown: Optional[float] = None    # Max acceptable drawdown
    long_only: bool = True           # No short selling

@dataclass
class PortfolioTask:
    """Request object passed between agents."""
    task_id: str
    task_type: TaskType
    universe: List[str]              # ["SPY", "TLT", "GLD", "VWO"]
    constraints: PortfolioConstraints
    current_weights: Optional[Dict[str, float]] = None  # For rebalancing
    target_weights: Optional[Dict[str, float]] = None
    historical_period: str = "5Y"
    optimization_method: Optional[OptimizationMethod] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass  
class PortfolioResult:
    """Response object from agents. MUST be summary, not raw data!"""
    success: bool
    agent_name: str
    
    # Portfolio weights
    weights: Dict[str, float]        # {"SPY": 0.40, "TLT": 0.30, ...}
    
    # Metrics (already calculated, not raw data!)
    expected_return: Optional[float] = None   # e.g., 0.082 = 8.2%
    expected_volatility: Optional[float] = None  # e.g., 0.115 = 11.5%
    sharpe_ratio: Optional[float] = None      # e.g., 0.73
    
    # Audit trail
    optimization_method: Optional[str] = None
    reasoning: str = ""
    warnings: List[str] = field(default_factory=list)
    
    # Timestamp for compliance
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class RegimeSignal:
    """Output from MacroAgent regime analysis."""
    regime: RegimeType
    vix_level: float
    vix_regime: str                  # "low", "normal", "elevated", "high"
    yield_curve_slope: float         # 10Y - 3M spread
    yield_curve_status: str          # "normal", "flat", "inverted"
    
    # Tactical adjustment
    equity_adjustment: float         # e.g., -0.10 = reduce equity 10%
    confidence: float                # 0.0 to 1.0
    rationale: List[str]             # Human-readable reasons

@dataclass
class RebalanceResult:
    """Output from RebalanceAgent. DETERMINISTIC - same inputs = same outputs!"""
    should_rebalance: bool
    recommendation: str              # "full_rebalance", "partial", "no_action"
    max_drift: float                 # Maximum drift from target
    
    # Trades (if rebalancing)
    trades: List[Dict[str, Any]]     # [{"ticker": "SPY", "action": "SELL", "shares": 10, ...}]
    
    # Costs
    total_transaction_cost: float
    estimated_tax: float
    net_cost: float
    cost_as_percent: float           # Cost as % of portfolio
    
    # Break-even analysis
    break_even_drift: float          # Drift level where rebalancing pays off

# ─────────────────────────────────────────────────────────────────────────────
# AGENT STATE (LangGraph)
# ─────────────────────────────────────────────────────────────────────────────

from typing import TypedDict, Annotated
# from langgraph.graph.message import add_messages  # Uncomment when using LangGraph

class AgentState(TypedDict):
    """
    Global state passed through LangGraph.
    TypedDict ensures compatibility with LangGraph reducers.
    All agents can read/write to this.
    """
    messages: Annotated[List[Any], "add_messages"]  # Chat history (use add_messages reducer)
    current_task: Optional[PortfolioTask]
    
    # Results from sub-agents
    sub_results: Dict[str, PortfolioResult]
    
    # Shared computed data (Hot Potato - pass summaries, not raw data!)
    # Example keys: "covariance_matrix", "macro_regime", "latest_prices"
    shared_data: Dict[str, Any]
    
    # Audit
    trace_id: Optional[str]

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM EXCEPTIONS (Phase 6.8 - Error Handling)
# ─────────────────────────────────────────────────────────────────────────────

class AgentError(Exception):
    """Base class for all agent errors."""
    pass

class DataFetchError(AgentError):
    """Provider API failed or rate limit hit."""
    pass

class OptimizationError(AgentError):
    """Solver failed to converge or no feasible solution."""
    constraints_violated: List[str] = []

class ValidationError(AgentError):
    """Input parameters violated constraints."""
    pass

class RateLimitError(AgentError):
    """API rate limit exceeded."""
    retry_after: int = 60  # seconds

class TickerNotFoundError(AgentError):
    """Ticker symbol does not exist or is invalid."""
    pass
    
"""
=============================================================================
SECTION 4: AGENT INTERFACES
=============================================================================
"""

class BaseAgent(Protocol):
    """All agents implement this interface."""
    
    name: str
    tools: List[Callable]
    
    def get_tools(self) -> List[Callable]:
        """Return tools this agent can use."""
        ...
    
    async def process(self, state: AgentState) -> AgentState:
        """Process the current state and return updated state."""
        ...

class RiskManagerAgent:
    """
    🎯 SUPERVISOR AGENT (Entry Point)
    
    Responsibilities:
    1. Parse user message into PortfolioTask
    2. Validate constraints (reject if unreasonable)
    3. Route to appropriate sub-agent(s)
    4. Validate final result
    5. Generate compliance-ready response
    
    DOES NOT: Make investment decisions, do math, fetch data
    """
    
    def parse_user_mandate(self, message: str) -> PortfolioTask:
        """
        Extract structured task from natural language.
        
        Example:
            Input: "Optimiere Portfolio mit SPY, TLT, max 12% Volatilität"
            Output: PortfolioTask(
                task_type=OPTIMIZE,
                universe=["SPY", "TLT"],
                constraints=PortfolioConstraints(max_volatility=0.12)
            )
        """
        ...
    
    def validate_constraints(self, constraints: PortfolioConstraints) -> List[str]:
        """Return list of warnings/errors if constraints are unreasonable."""
        ...
    
    def validate_result(self, result: PortfolioResult) -> List[str]:
        """Check result meets all constraints. Return warnings."""
        ...
    
    def route_to_agent(self, task: PortfolioTask) -> str:
        """Decide which sub-agent handles this task."""
        ...

class DataAgent:
    """
    📊 DATA WORKER AGENT
    
    Responsibilities:
    1. Fetch price data (via tools -> DataManager -> YFinance)
    2. Calculate covariance matrix
    3. Calculate returns
    4. Provide risk-free rate
    
    Tools:
    - fetch_prices_tool(tickers, period) -> {success, data, metadata}
    - calculate_covariance_tool(tickers, method) -> {success, matrix, vols}
    - calculate_returns_tool(tickers) -> {success, returns}
    - get_risk_free_rate_tool() -> {success, rate}
    """
    pass

class MacroAgent:
    """
    🌍 MACRO WORKER AGENT
    
    Responsibilities:
    1. Fetch macro indicators (VIX, Treasury yields)
    2. Assess market regime
    3. Generate TAA (Tactical Asset Allocation) signals
    4. (Future) Analyze Fed Minutes via RAG
    
    Tools:
    - fetch_macro_data_tool(indicators, days) -> {success, rows_updated}
    - get_macro_snapshot_tool() -> {success, vix, yield_curve}
    - assess_regime_tool(vix_level, yield_curve_slope) -> RegimeSignal
    - generate_taa_signal_tool(current_equity_weight) -> {action, adjustment}
    """
    pass

class RebalanceAgent:
    """
    ⚖️ REBALANCE WORKER AGENT
    
    CRITICAL: All calculations are DETERMINISTIC (no LLM!)
    Uses rebalance_tools.py which is PURE MATH.
    
    Responsibilities:
    1. Calculate portfolio drift
    2. Determine if rebalancing needed (threshold-based)
    3. Generate trade list with cost estimates
    4. Provide break-even analysis
    
    Tools:
    - analyze_rebalance_tool(current, target, value, prices) -> RebalanceResult
    - calculate_drift_tool(current, target) -> {max_drift, by_asset}
    - generate_trade_list_tool(current, target, value, prices) -> {trades}
    """
    pass

"""
=============================================================================
SECTION 5: TOOL SIGNATURES
=============================================================================
Tools are the interface between Agents and Business Logic.
All tools return: {"success": bool, "data": {...}, "metadata": {...}, "error": Optional[str]}
"""

# ─────────────────────────────────────────────────────────────────────────────
# DATA TOOLS (src/portfolio_tool/tools/data_tools.py)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_prices_tool(tickers: str, period: str = "5Y") -> Dict[str, Any]:
    """
    Fetch historical prices and store in database.
    
    Args:
        tickers: Comma-separated ticker symbols ("SPY,TLT,GLD")
        period: Lookback period ("1Y", "3Y", "5Y", "10Y")
    
    Returns:
        {
            "success": True,
            "data": {
                "tickers": ["SPY", "TLT", "GLD"],
                "num_observations": 750,
                "period": "2021-01-15 to 2024-01-15",
                "latest_prices": {"SPY": 590.0, "TLT": 88.0, "GLD": 420.0}
            }
        }
    """
    ...

def calculate_covariance_tool(
    tickers: str, 
    period: str = "3Y",
    method: str = "shrinkage"  # or "sample"
) -> Dict[str, Any]:
    """
    Calculate covariance matrix for optimization.
    
    Returns:
        {
            "success": True,
            "data": {
                "covariance_matrix": {...},  # Nested dict
                "correlation_matrix": {...},
                "annualized_volatilities": {"SPY": 0.18, "TLT": 0.12}
            }
        }
    """
    ...

def get_risk_free_rate_tool() -> Dict[str, Any]:
    """
    Get current risk-free rate (3-month Treasury).
    
    Returns:
        {"success": True, "data": {"rate": 0.05, "rate_formatted": "5.00%"}}
    """
    ...

# ─────────────────────────────────────────────────────────────────────────────
# MACRO TOOLS (src/portfolio_tool/tools/macro_tools.py)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_macro_data_tool(indicators: str = "VIX,TNX_10Y,IRX_3M", days: int = 30) -> Dict:
    """
    Fetch macro indicators from Yahoo Finance and store in DB.
    
    Returns:
        {"success": True, "data": {"rows_updated": 73, "indicators": ["VIX", ...]}}
    """
    ...

def get_macro_snapshot_tool() -> Dict[str, Any]:
    """
    Get current macro environment summary.
    
    Returns:
        {
            "success": True,
            "data": {
                "vix": {"value": 18.5, "regime": "normal", "high_30d": 22.0, "low_30d": 15.0},
                "yield_curve": {"slope": "+0.45%", "status": "normal", "10y": 4.50, "3m": 4.05}
            }
        }
    """
    ...

def assess_regime_tool(vix_level: float, yield_curve_slope: float) -> Dict[str, Any]:
    """
    Assess current market regime.
    
    Returns:
        {
            "success": True,
            "data": {
                "regime": "NEUTRAL",
                "risk_stance": "neutral",
                "equity_adjustment": 0.0,
                "confidence": 0.75,
                "rationale": ["VIX at normal levels", "Yield curve positive"]
            }
        }
    """
    ...

def generate_taa_signal_tool(current_equity_weight: float) -> Dict[str, Any]:
    """
    Generate tactical asset allocation signal.
    
    Returns:
        {
            "success": True,
            "data": {
                "action": "HOLD",  # or "REDUCE_EQUITY", "INCREASE_EQUITY"
                "current_equity": 0.55,
                "recommended_equity": 0.55,
                "adjustment": 0.0,
                "rationale": ["Market regime neutral", "No adjustment needed"]
            }
        }
    """
    ...

# ─────────────────────────────────────────────────────────────────────────────
# REBALANCE TOOLS (src/portfolio_tool/tools/rebalance_tools.py)
# CRITICAL: These are PURE MATH - NO LLM INVOLVED!
# ─────────────────────────────────────────────────────────────────────────────

def analyze_rebalance(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
    portfolio_value: float,
    prices: Dict[str, float],
    config: "RebalanceConfig" = None
) -> "RebalanceResult":
    """
    Complete rebalancing analysis. DETERMINISTIC.
    
    Args:
        current_weights: {"SPY": 0.45, "TLT": 0.25, ...}
        target_weights: {"SPY": 0.40, "TLT": 0.30, ...}
        portfolio_value: Total portfolio value in EUR
        prices: Current prices {"SPY": 590.0, ...}
        config: RebalanceConfig with thresholds and costs
    
    Returns:
        RebalanceResult with:
        - should_rebalance: bool
        - recommendation: str
        - trades: List[Trade]
        - costs: transaction + tax estimates
        - break_even_drift: float
    """
    ...

@dataclass
class RebalanceConfig:
    """Configuration for rebalancing calculations."""
    drift_threshold_percent: float = 5.0    # Trigger rebalance if drift > 5%
    transaction_cost_bps: float = 10.0      # 10 basis points = 0.10%
    capital_gains_tax_rate: float = 0.25    # 25% tax on gains
    min_trade_value: float = 100.0          # Don't trade below €100

"""
=============================================================================
SECTION 6: DATABASE SCHEMA
=============================================================================
SQLite with SQLAlchemy ORM. All tables use UPSERT for idempotency.
"""

# from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint

class Asset:
    """Stock/ETF master data."""
    # Columns: id, ticker (unique), name, asset_type, sector, currency
    pass

class DailyPrice:
    """Historical OHLCV data."""
    # Columns: id, asset_id (FK), date, open, high, low, close, adj_close, volume
    # Unique: (asset_id, date)
    pass

class MacroData:
    """Macro indicators (VIX, yields, etc.)."""
    # Columns: id, indicator, date, value
    # Unique: (indicator, date)
    pass

class FinancialStatement:
    """Company financials (optional, for fundamental analysis)."""
    # Columns: id, asset_id, date, report_type, revenue, net_income, ...
    # Unique: (asset_id, date, report_type)
    pass

"""
=============================================================================
SECTION 7: OBSERVABILITY (Phase 6.3)
=============================================================================
Full tracing for debugging and compliance.
"""

class Tracer:
    """
    Trace all agent/tool invocations.
    
    Usage:
        tracer = get_tracer()
        with tracer.trace_request("req_123", "User message") as req:
            with req.trace_agent("DataAgent") as agent:
                agent.log_thinking("Fetching prices...")
                with agent.trace_tool("fetch_prices") as tool:
                    tool.set_input({"tickers": "SPY"})
                    result = do_something()
                    tool.set_output(result)
                agent.set_tokens(150, 80)
        print(tracer.get_summary())
    
    Output:
        ┌─ 🤖 [DataAgent] Starting...
        │  💭 Fetching prices...
        │  🔧 Calling: fetch_prices
        │     ✓ fetch_prices (50ms)
        └─ ✓ [DataAgent] Done (50ms | 230 tokens)
        
        📊 REQUEST SUMMARY
           Duration: 50ms
           Tokens: 230
           Cost: $0.0037
    """
    pass

class TokenCounter:
    """
    Track token usage per agent/model.
    
    Usage:
        counter = get_token_counter()
        counter.add_usage("DataAgent", input_tokens=150, output_tokens=80)
        print(counter.format_report())
    """
    pass

"""
=============================================================================
SECTION 8: FILE STRUCTURE
=============================================================================

src/
├── agents/
│   ├── __init__.py          # Exports all agents
│   ├── base_agent.py        # BaseAgent, SupervisorAgent classes
│   ├── config.py            # LLM configuration (OpenAI, Anthropic)
│   ├── data_agent.py        # DataAgent implementation
│   ├── macro_agent.py       # MacroAgent implementation
│   ├── rebalance_agent.py   # RebalanceAgent implementation
│   ├── risk_manager_agent.py # Supervisor agent
│   ├── protocols.py         # All DTOs and Enums
│   ├── prompts.py           # System prompts for agents
│   └── state.py             # LangGraph state definition
│
├── observability/
│   ├── __init__.py
│   ├── tracer.py            # Request/agent/tool tracing
│   └── token_counter.py     # Token usage tracking
│
└── portfolio_tool/
    ├── data_manager.py      # Database CRUD operations
    ├── database_setup.py    # SQLAlchemy models
    │
    ├── tools/
    │   ├── data_tools.py    # Price, covariance tools
    │   ├── macro_tools.py   # VIX, regime tools
    │   └── rebalance_tools.py # PURE MATH rebalancing
    │
    ├── providers/
    │   └── yfinance_provider.py  # Yahoo Finance API
    │
    ├── quant/
    │   ├── covariance.py    # Shrinkage estimator
    │   └── risk_metrics.py  # VaR, Sharpe, etc.
    │
    └── optimization/
        ├── mean_variance.py # Markowitz optimization
        └── risk_parity.py   # Equal risk contribution

=============================================================================
SECTION 9: CURRENT STATUS & ROADMAP
=============================================================================

COMPLETED:
✅ Phase 5.1-5.4: All core agents (Data, Macro, Optimization, Backtest)
✅ Phase 5.5: Rebalancing (pure math, deterministic)
✅ Phase 6.3: Observability (Tracer, TokenCounter)

IN PROGRESS / TODO:
⬜ Phase 6.1: Smart Router (LLM-based intent detection, replace if/else)
⬜ Phase 6.2: LangGraph State Machine (real agent orchestration)
⬜ Phase 6.6: RAG Pipeline (Fed Minutes analysis)
⬜ Phase 6.7: Chainlit UI
⬜ Phase 6.11: Human-in-the-Loop (approval before trades)
⬜ Phase 6.12: Guardrails (Pydantic validation, no hallucinated tickers)

=============================================================================
SECTION 10: HOW TO HELP
=============================================================================

When implementing new features:

1. ALWAYS check which layer you're working in (Agent? Tool? DataManager?)
2. NEVER pass raw DataFrames to agents - aggregate first!
3. ALWAYS return structured responses: {"success": bool, "data": {...}}
4. For math/calculations: Use scipy/numpy, NOT LLM
5. For DB writes: Use UPSERT pattern (ON CONFLICT DO UPDATE)
6. Add tracing: Use the Tracer for debugging

Example - Adding a new tool:

    def my_new_tool(param1: str, param2: int) -> Dict[str, Any]:
        '''
        One-line description.
        
        Args:
            param1: Description
            param2: Description
        
        Returns:
            {"success": bool, "data": {...}, "error": Optional[str]}
        '''
        try:
            # 1. Validate inputs
            # 2. Call DataManager or do calculation
            # 3. Return structured response
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

7. TICKER VALIDATION: Before calling `fetch_prices`, ALWAYS validate tickers.
   Do NOT invent tickers (e.g., "GPTCOIN", "MSFT2"). If unsure, ask the user.
   Valid tickers: Real stock symbols from major exchanges (NYSE, NASDAQ, etc.)

Example - Error Handling:

    from agents.protocols import DataFetchError, TickerNotFoundError
    
    def fetch_data(ticker: str):
        if not is_valid_ticker(ticker):
            raise TickerNotFoundError(f"Invalid ticker: {ticker}")
        try:
            data = provider.fetch(ticker)
        except RateLimitError:
            raise DataFetchError("Rate limit hit, retry in 60s")
        return data
"""
