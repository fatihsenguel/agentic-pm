"""
🚀 PROJECT CONTEXT: QUANT PORTFOLIO MANAGER
============================================
Multi-Agent System for Institutional Portfolio Management

PURPOSE: This file contains everything an LLM needs to understand the project.
         Upload this + ROADMAP + tree when starting a new chat.

LAST UPDATED: Phase 6.2 Complete (LangGraph + Config Refactoring)
VERSION: 0.6.2
DATE: January 23, 2026

=============================================================================
SECTION 1: ARCHITECTURE OVERVIEW
=============================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                    │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         🎯 SMART ROUTER (LLM-based)                          │
│           Intent Detection → Parameter Extraction → Agent Selection          │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    📊 LANGGRAPH STATE MACHINE (Phase 6.2)                    │
│        Flow: Router → Dispatcher → [Agents] → Synthesizer → Response        │
└───────────┬─────────────────┬─────────────────┬─────────────────┬───────────┘
            │                 │                 │                 │
            ▼                 ▼                 ▼                 ▼
     ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
     │ 📊 DATA  │      │ 🌍 MACRO │      │ 🔧 OPTIM │      │ ⚖️ REBAL │
     │  AGENT   │      │  AGENT   │      │  AGENT   │      │  AGENT   │
     └────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOL LAYER                                      │
│         (data_tools, macro_tools, optimization_tools, rebalance_tools)       │
│                   ⚠️ DETERMINISTIC - NO LLM MATH! ⚠️                         │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SERVICE LAYER                                      │
│                  (DataManager, QuotaManager, MetricsCalculator)              │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROVIDER LAYER                                     │
│                         (YFinanceProvider)                                   │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SQLite DB                                       │
│      (daily_prices, macro_data, assets, portfolios, portfolio_holdings)     │
└─────────────────────────────────────────────────────────────────────────────┘

=============================================================================
SECTION 2: DESIGN PRINCIPLES (CRITICAL - MUST FOLLOW!)
=============================================================================

1. SEPARATION OF CONCERNS (SoC):
   ├── Config           → ONLY configuration values (single source of truth)
   ├── DataManager      → ONLY CRUD/DB operations
   ├── MetricsCalc      → ONLY math computations  
   ├── Provider         → ONLY external API calls
   ├── Tools            → ONLY agent interface (thin wrapper)
   └── Agent            → ONLY orchestration & decisions

2. HOT POTATO PRINCIPLE (🥔):
   ├── LLMs NEVER receive raw data (no DataFrames, no 1000-row CSVs!)
   ├── Each layer AGGREGATES before passing up
   └── Agent receives: {"return": "13.6%", "vol": "12%"} NOT [list of 1000 prices]

3. DRY (DON'T REPEAT YOURSELF):
   ├── Configuration in ONE place: src/config.py
   ├── Business logic in tools, NOT in agent configs
   └── ❌ NO duplicate XxxAgentConfig classes - use centralized config!

4. IDEMPOTENT OPERATIONS:
   └── All DB writes: INSERT ... ON CONFLICT (ticker, date) DO UPDATE
       Safe to retry. No duplicates.

5. DETERMINISTIC MATH:
   ├── Rebalancing = Pure scipy/numpy (NO LLM!)
   ├── Optimization = Pure scipy/numpy (NO LLM!)
   ├── Covariance = Pure numpy/pandas (NO LLM!)
   └── Same inputs ALWAYS produce same outputs (auditable)

6. AGENT-READY RESPONSES:
   └── All tools return: {"success": bool, "data": {...}, "error": Optional[str]}

7. SESSION ISOLATION:
   └── DataManager and QuotaManager use SEPARATE DB sessions (no SQLite locks)

8. CONFIGURATION HIERARCHY:
   ├── AgentConfig = Agent IDENTITY (name, role, temperature, verbose)
   └── config.xxx = Business LOGIC (thresholds, rates, constraints)
   
   Example:
       AgentConfig(name="DataAgent", role=AgentRole.DATA)  # Identity
       config.data.default_period = "3Y"                   # Business logic

=============================================================================
SECTION 3: CONFIGURATION SYSTEM (Phase 6.2 - CRITICAL!)
=============================================================================

⚠️ NEVER create XxxAgentConfig classes! Use centralized config instead.

File: src/config.py (SINGLE SOURCE OF TRUTH)

Structure:
    @dataclass
    class AppConfig:
        data: DataConfig                    # Data fetching & covariance
        macro: MacroConfig                  # VIX thresholds, yield curve
        optimization: OptimizationConfig    # Risk-free rate, max weights
        rebalance: RebalanceConfig          # Drift threshold, transaction costs
        backtest: BacktestConfig            # Initial capital, slippage
        risk: RiskManagerConfig             # VaR, concentration limits
        api: APIConfig                      # Rate limits, timeouts
        features: FeatureFlags              # Observability, tracing
    
    config = AppConfig()  # Singleton

Usage Examples:

    # In any agent:
    from config import config
    
    # Data settings:
    period = config.data.default_period                    # "3Y"
    method = config.data.default_covariance_method         # "sample"
    trading_days = config.data.trading_days_per_year       # 252
    
    # Macro settings:
    if vix > config.macro.vix_elevated:                    # 25.0
        regime = "elevated"
    
    # Optimization settings:
    max_weight = config.optimization.default_max_weight    # 0.40
    risk_free = config.optimization.risk_free_rate         # 0.05
    
    # Rebalance settings:
    threshold = config.rebalance.default_drift_threshold   # 5.0%
    tax_rate = config.rebalance.capital_gains_rate         # 0.25
    
    # Feature flags:
    if config.features.tracing_enabled:
        tracer = get_tracer()

Key Settings by Config Section:

DataConfig:
    - default_period: "3Y"
    - default_covariance_method: "sample"  # Changed from "shrinkage" (Phase 6.2)
    - trading_days_per_year: 252
    - min_observations: 60
    - default_risk_free_rate: 0.05

MacroConfig:
    - vix_low: 15.0
    - vix_elevated: 25.0
    - vix_high: 35.0
    - vix_crisis: 40.0
    - yield_curve_flat: 10.0 (bps)
    - hawkish_threshold: 0.25
    - dovish_threshold: -0.25

OptimizationConfig:
    - default_method: "max_sharpe"
    - risk_free_rate: 0.05
    - default_max_weight: 0.40
    - default_min_weight: 0.0
    - tolerance: 1e-10

RebalanceConfig:
    - default_drift_threshold: 5.0%
    - default_transaction_cost_bps: 10.0
    - capital_gains_rate: 0.25

BacktestConfig:
    - default_initial_capital: 100000
    - default_period: "5Y"
    - transaction_cost_bps: 10.0
    - risk_free_rate: 0.05

RiskManagerConfig:
    - var_confidence_level: 0.95
    - max_concentration: 0.30
    - min_diversification_assets: 5

FeatureFlags:
    - tracing_enabled: bool (from env: ENABLE_TRACING)
    - observability_enabled: bool (from env: ENABLE_OBSERVABILITY)

=============================================================================
SECTION 4: COVARIANCE ESTIMATION (Phase 6.2 - FIXED!)
=============================================================================

ISSUE DISCOVERED: Ledoit-Wolf shrinkage was hitting 100% intensity, forcing all
correlations to zero. This broke portfolio optimization.

ROOT CAUSE: 
    - Only 3 assets (SPY, TLT, GLD)
    - 1254 observations available
    - 418:1 observation-to-asset ratio (excellent!)
    - Shrinkage algorithm too conservative for this scenario

SOLUTION:
    Changed default method from "shrinkage" to "sample" covariance.
    
    Why this works:
    - With 400+ observations per asset, sample covariance is reliable
    - Rule of thumb: Need 50:1 ratio, we have 418:1
    - Sample covariance gives REAL correlations:
        SPY-TLT: 10.4% (slightly positive)
        SPY-GLD: 6.9% (slightly positive)  
        TLT-GLD: 20.2% (moderately positive)

Available Methods:
    1. "sample" - Standard covariance (good for 3-10 assets, 200+ obs)
    2. "shrinkage" - Ledoit-Wolf (good for 20+ assets, limited data)
    3. "exponential" - EWMA (good for dynamic/recent emphasis)

Configuration:
    File: src/config.py
    Setting: config.data.default_covariance_method = "sample"
    
    Changed in 3 locations:
    - src/config.py (default value)
    - src/agents/data_agent.py (tool defaults)
    - src/agents/nodes.py (function calls)

=============================================================================
SECTION 5: PROTOCOLS & DATA STRUCTURES
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
    OPTIMIZATION = "optimization"       # Create optimal portfolio
    BACKTEST = "backtest"               # Historical simulation
    MACRO_ANALYSIS = "macro_analysis"   # Macro environment check
    REBALANCE = "rebalance"             # Drift analysis & trades

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
    universe: List[str]              # ["SPY", "TLT", "GLD"]
    constraints: PortfolioConstraints
    current_weights: Optional[Dict[str, float]] = None  # For rebalancing
    target_weights: Optional[Dict[str, float]] = None
    historical_period: str = "3Y"    # Changed from "5Y" in Phase 6.2
    optimization_method: Optional[OptimizationMethod] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass  
class PortfolioResult:
    """Response object from agents. MUST be summary, not raw data!"""
    success: bool
    agent_name: str
    task_id: str
    
    # Result type and data
    result_type: str                 # "optimization", "backtest", etc.
    data: Dict[str, Any]             # Structured result data
    
    # Metrics (already calculated, not raw data!)
    message: str = ""                # Summary message
    reasoning: str = ""              # Why this result
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

"""
=============================================================================
SECTION 6: DATABASE SCHEMA
=============================================================================
SQLite with SQLAlchemy ORM. All tables use UPSERT for idempotency.

NEW IN PHASE 6.2: Portfolio Management Tables
"""

# Core tables
class Asset:
    """Stock/ETF master data."""
    # Columns: id, ticker (unique), name, asset_type, sector, currency

class DailyPrice:
    """Historical OHLCV data."""
    # Columns: id, asset_id (FK), date, open, high, low, close, volume
    # Unique: (asset_id, date)

class MacroData:
    """Macro indicators (VIX, yields, etc.)."""
    # Columns: id, indicator, date, value
    # Unique: (indicator, date)

# NEW: Portfolio Management (Phase 6.2)
class Portfolio:
    """User portfolio definition."""
    # Columns: id, name, description, currency, cash_balance, created_at, updated_at
    # Example: Portfolio(name="Retirement 401k", currency="USD")

class PortfolioHolding:
    """Individual positions in a portfolio."""
    # Columns: id, portfolio_id (FK), asset_id (FK), quantity, average_price
    # Unique: (portfolio_id, asset_id)
    # Example: PortfolioHolding(portfolio_id=1, asset_id=5, quantity=100, avg_price=450.0)

"""
Usage Example:

    from portfolio_tool.portfolio_manager import PortfolioManager
    
    pm = PortfolioManager()
    
    # Create portfolio
    portfolio_id = pm.create_portfolio("My 401k", currency="USD")
    
    # Add holdings
    pm.add_holding(portfolio_id, "SPY", quantity=100, avg_price=450.0)
    pm.add_holding(portfolio_id, "TLT", quantity=50, avg_price=88.0)
    pm.add_holding(portfolio_id, "GLD", quantity=20, avg_price=185.0)
    
    # Get holdings
    holdings = pm.get_holdings(portfolio_id)
    tickers = pm.get_portfolio_tickers(portfolio_id)  # ["SPY", "TLT", "GLD"]
    
    # Update/Delete
    pm.update_holding(holding_id, quantity=150)
    pm.delete_holding(holding_id)

⚠️ STATUS: Tables created, not yet integrated into agents (Phase 6.5)
"""

"""
=============================================================================
SECTION 7: LANGGRAPH STATE MACHINE (Phase 6.2)
=============================================================================

Architecture:
    User Input
        ↓
    Router (LLM-based intent detection)
        ↓
    Dispatcher (Routes to appropriate agents)
        ↓
    Agent(s) Execute (Data → Macro → Optimization → etc.)
        ↓
    Synthesizer (Combines results into natural language)
        ↓
    Response to User

Key Features:
    ✅ Smart routing based on natural language intent
    ✅ Multi-agent chains (e.g., Data → Optimization)
    ✅ Parallel execution where possible
    ✅ Automatic result synthesis
    ✅ Error handling and recovery

State Structure:
    @dataclass
    class AgentState:
        messages: List[dict]              # Conversation history
        router_decision: Optional[dict]   # Router output
        agent_results: Dict[str, Any]     # Results from each agent
        shared_data: Dict[str, Any]       # Data passed between agents
        current_agent: Optional[str]      # Active agent
        error: Optional[str]              # Error message if any

Example Flow:

    User: "Optimiere mein Portfolio mit SPY, TLT, GLD bei maximal 15% Volatilität"
    
    Router → Detects: OPTIMIZATION intent
          → Extracts: tickers=["SPY","TLT","GLD"], max_volatility=0.15
          → Plans: DataAgent → OptimizationAgent
    
    DataAgent → Fetches prices (3 years)
             → Calculates covariance matrix (sample method)
             → Calculates expected returns
             → Stores in shared_data
    
    OptimizationAgent → Reads shared_data (returns, covariance)
                     → Runs scipy optimization
                     → Returns: {"SPY": 0.40, "TLT": 0.20, "GLD": 0.40}
    
    Synthesizer → Formats: "📊 Optimal Allocation: SPY 40%, TLT 20%, GLD 40%
                           Expected Return: 20.83%, Volatility: 10.34%"

Performance:
    - Router: 2-7 seconds (LLM-based)
    - Data fetching: ~1.5s per ticker
    - Optimization: ~0.1s (fast!)
    - Total: 3-8 seconds end-to-end

Demo Results (Phase 6.2):
    ✅ Macro Analysis: VIX 15.64 (normal), Yield Curve normal
    ✅ Portfolio Optimization: SPY 40%, GLD 40%, TLT 20% (Sharpe 1.531)
    ✅ Combined Analysis: Macro + Rebalancing advice
    ✅ Backtest: 38.93% return, 11.65% CAGR, Sharpe 0.59
"""

"""
=============================================================================
SECTION 8: FILE STRUCTURE
=============================================================================

src/
├── config.py                    # ⭐ NEW: Centralized configuration
│
├── agents/
│   ├── __init__.py              # Exports (cleaned up - no XxxAgentConfig!)
│   ├── base_agent.py            # BaseAgent, SupervisorAgent, AgentConfig
│   ├── config.py                # LLM configuration (OpenAI, Anthropic)
│   ├── protocols.py             # DTOs and Enums
│   ├── state.py                 # LangGraph state definition
│   ├── prompts.py               # System prompts
│   │
│   ├── smart_router.py          # ⭐ Phase 6.1: LLM-based intent detection
│   ├── router_prompts.py        # Router system prompts
│   │
│   ├── nodes.py                 # ⭐ Phase 6.2: LangGraph node functions
│   ├── graph.py                 # ⭐ Phase 6.2: LangGraph workflow definition
│   │
│   ├── data_agent.py            # DataAgent (refactored - uses config.data)
│   ├── macro_agent.py           # MacroAgent (refactored - uses config.macro)
│   ├── optimization_agent.py    # OptimizationAgent (refactored)
│   ├── rebalance_agent.py       # RebalanceAgent (refactored)
│   ├── backtest_agent.py        # BacktestAgent (refactored)
│   └── risk_manager_agent.py    # Supervisor (refactored)
│
├── observability/               # Phase 6.3 (partially implemented)
│   ├── __init__.py
│   ├── tracer.py                # Request/agent/tool tracing
│   └── token_counter.py         # Token usage tracking
│
└── portfolio_tool/
    ├── data_manager.py          # Database CRUD operations
    ├── database_setup.py        # SQLAlchemy models
    ├── portfolio_manager.py     # ⭐ NEW: Portfolio CRUD (not integrated yet)
    │
    ├── tools/
    │   ├── data_tools.py        # Price, covariance tools
    │   ├── macro_tools.py       # VIX, regime tools
    │   ├── optimization_tools.py # Mean-variance, risk parity
    │   └── rebalance_tools.py   # PURE MATH rebalancing
    │
    ├── providers/
    │   └── yfinance_provider.py  # Yahoo Finance API
    │
    ├── quant/
    │   ├── covariance.py        # Covariance estimators (sample, shrinkage, EWMA)
    │   ├── risk_metrics.py      # VaR, Sharpe, etc.
    │   └── returns.py           # Return calculations
    │
    └── optimization/
        ├── mean_variance.py     # Markowitz optimization
        └── risk_parity.py       # Equal risk contribution

demos/
├── langgraph_demo.py            # ⭐ Phase 6.2 demo (4/4 tests passing!)
└── multi_agent_cli.py           # Old CLI (deprecated)

tests/
├── test_shrinkage.py            # ⭐ Covariance diagnostic tool
├── test_all_configs.py          # ⭐ Config validation tests
└── violation_detector.py        # ⭐ DRY/SoC violation scanner

=============================================================================
SECTION 9: CURRENT STATUS & ROADMAP
=============================================================================

COMPLETED:
✅ Phase 5.1-5.4: All core agents (Data, Macro, Optimization, Backtest)
✅ Phase 5.5: Rebalancing (pure math, deterministic)
✅ Phase 6.1: Smart Router (LLM-based intent detection)
✅ Phase 6.2: LangGraph State Machine + Config Refactoring
    - LangGraph workflow (Router → Dispatcher → Agents → Synthesizer)
    - Centralized config.py (single source of truth)
    - Removed all XxxAgentConfig classes (DRY principle)
    - Fixed covariance shrinkage (changed to sample method)
    - Added Portfolio/PortfolioHolding tables
    - All demos working (4/4 tests passing!)

IN PROGRESS:
⏳ Phase 6.5: Portfolio Management (4-5h)
    - Integrate portfolio_manager.py
    - Remove hardcoded ["SPY", "TLT", "GLD"]
    - Add portfolio selection to router
    - Update agents to use real portfolio data

TODO:
⬜ Phase 6.3: Observability (4-5h)
⬜ Phase 6.4: Token Management (3-4h)
⬜ Phase 6.6: RAG Pipeline (6-8h)
⬜ Phase 6.7: Chainlit UI (4-6h)
⬜ Phase 6.8: Error Handling (3-4h)
⬜ Phase 6.9: Data Scheduling (3-4h)
⬜ Phase 6.10: Testing & Docs (4-6h)
⬜ Phase 6.11: Human-in-the-Loop (3-4h)
⬜ Phase 6.12: Guardrails (3-4h)

CURRENT WORKING DIRECTORY: E:\Programming\AGENTIC_FINANCE

=============================================================================
SECTION 10: HOW TO HELP
=============================================================================

When implementing new features:

1. ALWAYS check which layer you're working in (Agent? Tool? DataManager?)

2. CONFIGURATION:
   - NEVER create XxxAgentConfig classes
   - ALWAYS use config.xxx for business logic
   - AgentConfig is ONLY for agent identity (name, role, temperature)

3. DATA HANDLING:
   - NEVER pass raw DataFrames to agents - aggregate first!
   - ALWAYS return structured responses: {"success": bool, "data": {...}}

4. MATH/CALCULATIONS:
   - Use scipy/numpy, NOT LLM
   - Keep deterministic (same inputs = same outputs)

5. DATABASE:
   - Use UPSERT pattern (ON CONFLICT DO UPDATE)
   - Session isolation (separate sessions for concurrent operations)

6. COVARIANCE:
   - Default method: "sample" (good for <10 assets, 200+ observations)
   - Use "shrinkage" only for 20+ assets or limited data
   - Use "exponential" for dynamic/recent emphasis

7. TICKER VALIDATION:
   - Always validate before fetching
   - Do NOT invent tickers (e.g., "GPTCOIN", "MSFT2")
   - If unsure, ask the user

8. ERROR HANDLING:
   - Always use try/except
   - Return {"success": False, "error": str(e)}
   - Never let exceptions bubble up to LLM

Example - Adding a Config Value:

    # 1. Add to config.py:
    @dataclass
    class DataConfig:
        new_setting: float = 0.10
    
    # 2. Use in agent:
    from config import config
    
    value = config.data.new_setting

Example - Using Portfolio Manager:

    from portfolio_tool.portfolio_manager import PortfolioManager
    
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("My Portfolio")
    pm.add_holding(portfolio_id, "SPY", quantity=100, avg_price=450.0)
    tickers = pm.get_portfolio_tickers(portfolio_id)

=============================================================================
SECTION 11: KNOWN ISSUES & LIMITATIONS
=============================================================================

CURRENT LIMITATIONS:
1. Hardcoded tickers ["SPY", "TLT", "GLD"] in demos (Phase 6.5 will fix)
2. Mock data in RebalanceAgent output (trades are simulated)
3. No user authentication (single-user system for now)
4. Observability partially implemented (tracers exist but not integrated)
5. No UI yet (CLI only, Chainlit coming in Phase 6.7)

FIXED IN PHASE 6.2:
✅ Covariance shrinkage at 100% → Changed to sample method
✅ Duplicate config classes → Centralized in config.py
✅ Hardcoded business logic → Moved to config.py
✅ No agent orchestration → Added LangGraph state machine

=============================================================================
END OF PROJECT CONTEXT
=============================================================================

For questions or clarifications, refer to:
- ROADMAP.md (high-level plan)
- Individual agent files (detailed implementation)
- demos/langgraph_demo.py (working examples)
"""