"""
🚀 PROJECT CONTEXT: QUANT PORTFOLIO MANAGER
============================================
Multi-Agent System for Institutional Portfolio Management

PURPOSE: This file contains everything an LLM needs to understand the project.
         Upload this + ROADMAP + tree when starting a new chat.

LAST UPDATED: Phase 6.1, 6.2, 6.12 Complete (Router, Graph, Guardrails)
VERSION: 0.6.3
DATE: January 24, 2026

=============================================================================
SECTION 1: ARCHITECTURE OVERVIEW
=============================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                    │
│                 (includes Conversation History/Memory)                       │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         🎯 SMART ROUTER (LLM-based)                          │
│           Intent Detection → Parameter Extraction → Agent Selection          │
│                (Uses Pydantic Schemas for Strict Validation)                 │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    📊 LANGGRAPH STATE MACHINE (Phase 6.2)                    │
│        Flow: Router → Dispatcher → [Agents] → Synthesizer → Response        │
│                (Supports Dynamic Routing & Streaming)                       │
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
   ├── Schemas          → ONLY data contracts & validation (Pydantic)
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

6. STRICT TYPING (Phase 6.12):
   ├── All Router outputs must pass `RouterDecision` schema
   ├── All Agent outputs must pass `AgentResponse` schema
   └── No "magic strings" or hallucinations allowed.

7. CONFIGURATION HIERARCHY:
   ├── AgentConfig = Agent IDENTITY (name, role, temperature, verbose)
   └── config.xxx = Business LOGIC (thresholds, rates, constraints)

8. STATELESS BACKEND:

├── The Graph is stateless.

└── Session history is managed by the client (Demo/UI) and injected per request.

=============================================================================
SECTION 3: CONFIGURATION SYSTEM
=============================================================================

File: src/config.py (SINGLE SOURCE OF TRUTH)

[Content remains unchanged - Config system is stable]

=============================================================================
SECTION 4: COVARIANCE ESTIMATION
=============================================================================

Default Method: "sample" (since Phase 6.2)
Rationale: Robustness for >50 observations.
Fallback: "shrinkage" if N < P.

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
"""

"""
=============================================================================
SECTION 7: LANGGRAPH STATE MACHINE (Phase 6.2)
=============================================================================

Architecture:
    User Input (with History)
        ↓
    Router (LLM + Pydantic Validation)
        ↓
    Dispatcher (Dynamic Routing via `graph.py`)
        ↓
    Agent(s) Execute
        ↓
    Synthesizer
        ↓
    Response

Key Features:
    ✅ Memory: Router sees conversation history (No "State Amnesia")
    ✅ Streaming: Real-time feedback in Demo
    ✅ Dynamic: Router builds custom execution plans (e.g., Data -> Optimization)

State Structure:
    @dataclass
    class AgentState:
        messages: List[dict]              # Conversation history (Role/Content)
        router_decision: Optional[dict]   # Validated Router output
        agent_results: Dict[str, Any]     # Results from each agent
        shared_data: Dict[str, Any]       # Data passed between agents
        portfolio_id: Optional[int]       # Context for current portfolio
        error: Optional[str]              # Error message if any

=============================================================================
SECTION 8: FILE STRUCTURE
=============================================================================

src/
├── config.py                    # Centralized configuration
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py            # BaseAgent
│   ├── config.py                # LLM configuration
│   ├── state.py                 # LangGraph state definition
│   ├── schemas.py               # ⭐ Phase 6.12: Pydantic Data Contracts
│   ├── validators.py            # ⭐ Phase 6.12: Input Validation Logic
│   │
│   ├── smart_router.py          # ⭐ Phase 6.1: Intent Detection
│   ├── router_prompts.py        # System prompts (with Few-Shot)
│   │
│   ├── nodes.py                 # Phase 6.2: Agent Node Functions
│   ├── graph.py                 # Phase 6.2: Dynamic Graph Definition
│   │
│   ├── data_agent.py
│   ├── macro_agent.py
│   ├── optimization_agent.py
│   ├── rebalance_agent.py
│   ├── backtest_agent.py
│   └── risk_manager_agent.py
│
├── observability/               # Phase 6.3
│   ├── tracer.py                # Robust Tracing (Crash-Proof)
│   └── token_counter.py
│
└── portfolio_tool/
    ├── data_manager.py          # Database CRUD
    ├── database_setup.py        # Models
    ├── portfolio_manager.py     # Portfolio CRUD
    │
    ├── tools/
    │   ├── data_tools.py        # Admin/Data Tools (Needs wiring)
    │   ├── macro_tools.py
    │   ├── optimization_tools.py
    │   ├── rebalance_tools.py
    │   └── rag_tools.py         # ⭐ Phase 6.6 (Upcoming)
    │
    └── providers/
        └── yfinance_provider.py

demos/
├── langgraph_demo.py            # ⭐ Bank-Ready Demo (Memory + Streaming)

tests/
├── system_diagnostic.py         # ⭐ Strict System Health Check
├── test_strict_nodes.py         # Unit tests for nodes
└── test_design_violations.py    # Architecture linter

=============================================================================
SECTION 9: CURRENT STATUS & ROADMAP
=============================================================================

COMPLETED:
✅ Phase 5.x: All Core Agents & Math
✅ Phase 6.1: Smart Router (LLM-based Intent Detection)
✅ Phase 6.2: LangGraph State Machine (Dynamic Routing)
✅ Phase 6.12: Guardrails & Schemas (Strict Typing)
✅ Phase 6.3: Basic Observability (Tracer)
✅ Resilience: System Diagnostics & "Crash-Proof" Nodes
✅ UX: Streaming Demo with Conversation Memory

IN PROGRESS:
⏳ Phase 6.5: Portfolio Management (Admin Tools Integration)
    - Wiring `data_tools.py` to Router for "List Assets" capabilities

TODO:
⬜ Phase 6.6: RAG Pipeline (The "Researcher" Brain)
⬜ Phase 6.4: Token Management (Cost tracking)
⬜ Phase 6.7: Chainlit UI

=============================================================================
SECTION 11: KNOWN ISSUES & LIMITATIONS
=============================================================================

CURRENT LIMITATIONS:
1. Admin Tools Disconnected: `data_tools.py` exists but Router doesn't know "List Assets" yet.
2. Mock data in RebalanceAgent output (trades are simulated, not executed).
3. No user authentication.
4. RAG not implemented (cannot read news/PDFs yet).

FIXED RECENTLY:
✅ "State Amnesia":
   - Issue: Router treated every message as a new session.
   - Fix: Injected `conversation_history` into `router_node` and added a client-side `chat_memory` list in `langgraph_demo.py`.

✅ Hardcoded Tickers:
   - Issue: System only analyzed ["SPY", "TLT"] by default.
   - Fix: Updated `smart_router.py` to accept `portfolio_id`, fetch holdings via `PortfolioManager`, and merge them with user input.

✅ Crash on Missing Data:
   - Issue: Agents raised unchecked exceptions when DB was empty.
   - Fix: Implemented "Fail-Fast" logic in `nodes.py`. Agents now verify `shared_data` existence first and return clean `{"success": False, "error": "..."}` dicts.

✅ AttributeErrors (Router):
   - Issue: Nodes expected `execution_plan` but LLM sent `execution_order`.
   - Fix: Implemented Pydantic Schemas (`schemas.py`) with strict field aliasing and validation validators.

=============================================================================
END OF PROJECT CONTEXT
=============================================================================
"""