"""
🚀 PROJECT CONTEXT: PM DECISION SUPPORT SYSTEM
==============================================
Multi-Agent System for Institutional Portfolio Management

PURPOSE: This file contains everything an LLM needs to understand the project.
         Upload this when starting a new chat. The LLM should be able to continue
         development without additional context.

LAST UPDATED: Phase 6.6 Complete (Decision Engine, Dual-Intent, Decision Logging)
VERSION: 0.7.0
DATE: January 25, 2026

=============================================================================
SECTION 1: PROJECT IDENTITY
=============================================================================

WHAT THIS IS:
    A PM Decision Support System that thinks like an institutional portfolio manager.
    NOT just an optimizer - a system that evaluates "should we act?" before "how?"

KEY DIFFERENTIATORS:
    1. HOLD is a valid decision - System explicitly evaluates "do nothing" as optimal
    2. Risk-First Assessment - Evaluates risk BEFORE recommending action
    3. No Action Bias - Information queries never get trade recommendations
    4. Auditable Decisions - Every decision logged with rationale and confidence
    5. PM-style Output - Looks like what a real PM reads, not raw JSON

TARGET USERS:
    - Portfolio Managers at banks/asset managers
    - Quant analysts needing decision support
    - Interview demonstration for finance + AI roles

=============================================================================
SECTION 2: ARCHITECTURE OVERVIEW
=============================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                    │
│                 (includes Conversation History/Memory)                       │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    🎯 SMART ROUTER (LLM + Pydantic)                          │
│                                                                              │
│   DUAL-INTENT SYSTEM (Phase 6.6):                                           │
│   ├── QueryIntent: WHY user asks (information, decision, operational)       │
│   └── ExecutionIntent: WHAT to run (optimization, macro_analysis, etc.)     │
│                                                                              │
│   This prevents action bias: "What's VIX?" → info only, no trade recs       │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    📊 LANGGRAPH STATE MACHINE                                │
│        Flow: Router → Dispatcher → [Agents] → Decision Engine → Synthesizer │
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
│                         🧠 DECISION ENGINE (Phase 6.6)                       │
│                                                                              │
│   1. RiskAssessment: Evaluate CURRENT portfolio (before any action)         │
│   2. PMDecisionSummary: HOLD / TILT / REBALANCE / HEDGE                     │
│   3. DecisionLog: Persist to database for audit trail                       │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOL LAYER                                      │
│         (data_tools, macro_tools, optimization_tools, rebalance_tools)       │
│                   ⚠️ DETERMINISTIC - NO LLM MATH! ⚠️                         │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SQLite DB                                       │
│   daily_prices, macro_data, assets, portfolios, holdings, decision_logs     │
└─────────────────────────────────────────────────────────────────────────────┘

=============================================================================
SECTION 3: DESIGN PRINCIPLES (CRITICAL - MUST FOLLOW!)
=============================================================================

1. SEPARATION OF CONCERNS (SoC):
   ├── Config           → ONLY configuration values (single source of truth)
   ├── DataManager      → ONLY CRUD/DB operations
   ├── Provider         → ONLY external API calls
   ├── Tools            → ONLY agent interface (thin wrapper)
   ├── Schemas          → ONLY data contracts & validation (Pydantic)
   ├── DecisionEngine   → ONLY PM decision logic (risk assessment, decision)
   └── Agent            → ONLY orchestration & LLM interaction

2. HOT POTATO PRINCIPLE (🥔):
   ├── LLMs NEVER receive raw data (no DataFrames, no 1000-row CSVs!)
   ├── Each layer AGGREGATES before passing up
   └── Agent receives: {"return": "13.6%", "vol": "12%"} NOT [list of 1000 prices]

3. DRY (DON'T REPEAT YOURSELF):
   ├── Configuration in ONE place: src/config.py
   ├── Business logic in tools, NOT in agent configs
   └── ❌ NO duplicate XxxAgentConfig classes - use centralized config!

4. IDEMPOTENT OPERATIONS:
   └── All DB writes: INSERT ... ON CONFLICT DO UPDATE (safe to retry)

5. DETERMINISTIC MATH:
   ├── Rebalancing = Pure scipy/numpy (NO LLM!)
   ├── Optimization = Pure scipy/numpy (NO LLM!)
   ├── Decision Engine = Pure Python logic (NO LLM!)
   └── Same inputs ALWAYS produce same outputs (auditable)

6. STRICT TYPING:
   ├── All Router outputs must pass `RouterDecision` schema
   ├── All Agent outputs must pass `AgentResponse` schema
   ├── All Decisions must pass `PMDecisionSummary` schema
   └── No "magic strings" or hallucinations allowed

7. RISK-FIRST WORKFLOW:
   ├── Assess CURRENT portfolio risk before considering changes
   ├── HOLD is a valid, well-reasoned decision
   └── Never assume action is required

8. STATELESS BACKEND:
   ├── The Graph is stateless
   └── Session history managed by client and injected per request

=============================================================================
SECTION 4: DUAL-INTENT SYSTEM (Phase 6.6)
=============================================================================

The Router classifies TWO independent intents:

QUERY INTENT (Why is the user asking?):
┌────────────────┬─────────────────────────────────────────────────────────┐
│ Intent         │ Description                                             │
├────────────────┼─────────────────────────────────────────────────────────┤
│ operational    │ Admin tasks: list portfolios, show holdings, CRUD       │
│ information    │ Factual queries: "What's VIX?", "Show me SPY price"     │
│ analysis       │ Explanatory: "Why did my portfolio underperform?"       │
│ decision       │ Action-oriented: "Should I rebalance?", "Optimize..."   │
│ clarification  │ Ambiguous query needing more info                       │
│ unknown        │ Cannot determine intent                                 │
└────────────────┴─────────────────────────────────────────────────────────┘

EXECUTION INTENT (What agents to run?):
┌────────────────────┬─────────────────────────────────────────────────────┐
│ Intent             │ Agents Triggered                                    │
├────────────────────┼─────────────────────────────────────────────────────┤
│ optimization       │ DataAgent → OptimizationAgent                       │
│ macro_analysis     │ MacroAgent                                          │
│ rebalancing        │ DataAgent → RebalanceAgent                          │
│ backtest           │ DataAgent → BacktestAgent                           │
│ data_fetch         │ DataAgent                                           │
│ risk_analysis      │ DataAgent → RiskAnalysisAgent                       │
│ data_management    │ DataAgent (admin commands)                          │
│ portfolio_mgmt     │ DataAgent (portfolio CRUD)                          │
└────────────────────┴─────────────────────────────────────────────────────┘

CRITICAL RULE:
- Decision Summaries (HOLD/TILT/REBALANCE/HEDGE) are ONLY generated 
  when query_intent == "decision"
- Information/operational queries get data only, no trade recommendations
- This prevents action bias

=============================================================================
SECTION 5: DECISION ENGINE (Phase 6.6)
=============================================================================

File: src/agents/decision_engine.py
Schemas: src/agents/decision_schemas.py

DECISION TYPES:
┌────────────┬──────────────────────────────────────────────────────────────┐
│ Type       │ When Used                                                    │
├────────────┼──────────────────────────────────────────────────────────────┤
│ HOLD       │ Risk acceptable, drift low, no action needed (85% conf)      │
│ TILT       │ Minor tactical adjustment, moderate drift (65-75% conf)      │
│ REBALANCE  │ Structural change needed, high drift/risk (75-95% conf)      │
│ HEDGE      │ Crisis regime, defensive action needed (85% conf)            │
└────────────┴──────────────────────────────────────────────────────────────┘

RISK STATUS:
┌────────────┬──────────────────────────────────────────────────────────────┐
│ Status     │ Triggers                                                     │
├────────────┼──────────────────────────────────────────────────────────────┤
│ ACCEPTABLE │ All checks pass, no breaches                                 │
│ ELEVATED   │ 1-2 breaches (concentration, under-diversification)          │
│ CRITICAL   │ 3+ breaches, requires immediate attention                    │
└────────────┴──────────────────────────────────────────────────────────────┘

DECISION PRIORITY (7-tier):
1. CRITICAL risk → REBALANCE (95% confidence)
2. Crisis macro regime → HEDGE (85%)
3. ELEVATED risk + drift → REBALANCE (80%)
4. Risk-off + elevated → TILT (75%)
5. High drift (>1.5x threshold) → REBALANCE (75%)
6. Moderate drift → TILT (65%)
7. All else → HOLD (85%)

KEY FUNCTIONS:
- assess_portfolio_risk(weights, config) → RiskAssessment
- assess_decision_needed(drift, regime, risk, config) → PMDecisionSummary
- run_decision_assessment(...) → (RiskAssessment, PMDecisionSummary)
- should_generate_decision_summary(query_intent) → bool

=============================================================================
SECTION 6: DATABASE SCHEMA
=============================================================================

TABLES:
┌─────────────────────┬────────────────────────────────────────────────────┐
│ Table               │ Purpose                                            │
├─────────────────────┼────────────────────────────────────────────────────┤
│ assets              │ Tracked securities (ticker, name, asset_class)     │
│ daily_prices        │ OHLCV history (asset_id, date, close, volume)      │
│ macro_data          │ VIX, yields, etc. (indicator, date, value)         │
│ portfolios          │ User portfolios (name, description, cash_balance)  │
│ portfolio_holdings  │ Positions (portfolio_id, asset_id, quantity, price)│
│ decision_logs       │ Audit trail (decision_type, confidence, rationale) │
│ financial_statements│ Income, balance sheet, cash flow data              │
│ quarterly_earnings  │ EPS, revenue by quarter                            │
└─────────────────────┴────────────────────────────────────────────────────┘

DECISION_LOGS TABLE (Phase 6.6):
    id, timestamp, portfolio_id
    decision_type (HOLD/TILT/REBALANCE/HEDGE)
    confidence (0.0-1.0)
    rationale (text)
    trigger (user_request, drift_threshold, macro_change)
    risk_status (ACCEPTABLE/ELEVATED/CRITICAL)
    key_risks (JSON array)
    current_weights, proposed_weights (JSON)
    max_drift, macro_regime, vix_level
    trade_required, executed, execution_timestamp
    request_id, user_query

=============================================================================
SECTION 7: FILE STRUCTURE
=============================================================================

src/
├── config.py                    # Centralized configuration (thresholds, etc.)
│
├── agents/
│   ├── __init__.py
│   ├── state.py                 # AgentState TypedDict for LangGraph
│   ├── schemas.py               # Pydantic schemas (RouterDecision, etc.)
│   ├── validators.py            # Input validation logic
│   │
│   ├── smart_router.py          # LLM-based intent detection
│   ├── router_prompts.py        # System prompts with few-shot examples
│   │
│   ├── nodes.py                 # All agent node functions + synthesizer
│   ├── graph.py                 # LangGraph definition
│   │
│   ├── decision_engine.py       # ⭐ Phase 6.6: PM decision logic
│   ├── decision_schemas.py      # ⭐ Phase 6.6: Decision data structures
│   ├── decision_logger.py       # ⭐ Phase 6.6: Decision persistence
│   │
│   ├── data_agent.py            # Data fetching and calculation
│   ├── macro_agent.py           # Macro environment analysis
│   ├── optimization_agent.py    # Portfolio optimization
│   ├── rebalance_agent.py       # Drift analysis and trade calculation
│   └── backtest_agent.py        # Historical simulation
│
├── observability/
│   ├── tracer.py                # Request tracing
│   └── token_counter.py         # LLM token tracking
│
└── portfolio_tool/
    ├── database_setup.py        # SQLAlchemy models
    ├── data_manager.py          # Database CRUD operations
    ├── portfolio_manager.py     # Portfolio CRUD operations
    │
    ├── tools/
    │   ├── data_tools.py        # Data/admin tool wrappers
    │   ├── macro_tools.py       # Macro data tools
    │   ├── optimization_tools.py# Optimization tools
    │   ├── rebalance_tools.py   # Rebalancing tools
    │   └── portfolio_tools.py   # Portfolio management tools
    │
    └── providers/
        └── yfinance_provider.py # YFinance API wrapper

scripts/
├── seed_database.py             # ⭐ Realistic data seeder

demos/
├── langgraph_demo.py            # Interactive CLI demo

tests/
├── test_phase66_comprehensive.py # ⭐ 40-test comprehensive suite
├── test_decision_engine.py      # Decision engine unit tests
├── conftest.py                  # Pytest configuration
└── ...

=============================================================================
SECTION 8: CONFIGURATION (src/config.py)
=============================================================================

Key configuration sections:

@dataclass
class DataConfig:
    default_period: str = "3Y"           # Historical data lookback
    min_observations: int = 252          # Minimum for calculations

@dataclass  
class MacroConfig:
    vix_elevated: float = 25.0           # Risk-off threshold
    vix_crisis: float = 35.0             # Crisis threshold
    yield_curve_inverted: float = 0.0    # Inversion threshold

@dataclass
class OptimizationConfig:
    default_method: str = "max_sharpe"   # Optimization method
    default_min_weight: float = 0.0      # Min weight per asset
    default_max_weight: float = 0.40     # Max weight per asset (40%)
    risk_free_rate: float = 0.05         # For Sharpe calculation

@dataclass
class RebalanceConfig:
    default_drift_threshold: float = 5.0 # % drift before rebalance

@dataclass
class RiskConfig:
    max_concentration: float = 0.30      # Max 30% in single asset
    min_diversification_assets: int = 5  # Minimum 5 positions

=============================================================================
SECTION 9: CURRENT STATUS
=============================================================================

✅ COMPLETED:
├── Phase 5.x: Core Agents (Data, Macro, Optimization, Rebalance, Backtest)
├── Phase 6.1: Smart Router (LLM-based intent detection)
├── Phase 6.2: LangGraph State Machine (dynamic routing, streaming)
├── Phase 6.12: Guardrails & Schemas (strict typing)
├── Phase 6.3: Basic Observability (tracing)
├── Phase 6.5: Portfolio Management (admin tools wired to router)
└── Phase 6.6: Decision Engine
    ├── Dual-Intent System (QueryIntent + ExecutionIntent)
    ├── Risk Assessment (runs BEFORE optimization)
    ├── PM Decision Summary (HOLD/TILT/REBALANCE/HEDGE)
    ├── Decision Logging (full audit trail)
    ├── Response Formatting (PM-style output)
    └── 40/40 Tests Passing

⏳ NEXT: Phase 6.7 - RAG Integration (see Section 11)

=============================================================================
SECTION 10: KNOWN LIMITATIONS
=============================================================================

1. NO RAG: Cannot read PDFs, earnings reports, or news articles
2. NO TRADE EXECUTION: Recommendations only, no broker integration
3. NO AUTHENTICATION: Single user, no multi-tenancy
4. NO ALERTS: Cannot schedule "alert me when drift > 5%"
5. LIMITED MACRO: Only VIX + yields, no Fed speeches or news

=============================================================================
SECTION 11: RAG INTEGRATION ROADMAP (Phase 6.7)
=============================================================================

GOAL: RAG should SYNERGIZE with Decision Engine, not be standalone.
      Documents feed into risk assessment and decision rationale.

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER QUERY                                      │
│   "Given NVDA's earnings report, should I increase my position?"            │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          ▼                               ▼                               ▼
    ┌──────────┐                   ┌──────────┐                    ┌──────────┐
    │   RAG    │                   │   Data   │                    │  Macro   │
    │  Agent   │                   │  Agent   │                    │  Agent   │
    │          │                   │          │                    │          │
    │ • Search │                   │ • Prices │                    │ • VIX    │
    │ • Extract│                   │ • Cov    │                    │ • Yields │
    │ • Cite   │                   │ • Returns│                    │ • Regime │
    └────┬─────┘                   └────┬─────┘                    └────┬─────┘
         │                              │                               │
         └──────────────────────────────┼───────────────────────────────┘
                                        │
                                        ▼
              ┌─────────────────────────────────────────────┐
              │           🧠 DECISION ENGINE                │
              │                                             │
              │  Inputs:                                    │
              │  • Current weights (from holdings)          │
              │  • Target weights (from optimization)       │
              │  • Macro regime (from MacroAgent)           │
              │  • Document insights (from RAG Agent) ← NEW │
              │                                             │
              │  Output:                                    │
              │  • PMDecisionSummary with citations         │
              └─────────────────────────────────────────────┘

IMPLEMENTATION PHASES:

Phase 1: Document Ingestion (2 hours)
├── src/portfolio_tool/rag/document_loader.py
├── src/portfolio_tool/rag/chunker.py
└── Capabilities: Load PDFs, smart chunking by section

Phase 2: Vector Store (1.5 hours)
├── src/portfolio_tool/rag/vector_store.py
├── src/portfolio_tool/rag/embeddings.py
└── Capabilities: ChromaDB storage, metadata filtering

Phase 3: RAG Agent (2 hours)
├── src/agents/rag_agent.py
├── src/portfolio_tool/tools/rag_tools.py
└── Capabilities: search_documents(), summarize_earnings(), extract_risk_factors()

Phase 4: Decision Engine Integration (1.5 hours)
├── Update decision_engine.py to accept document_insights
├── Update synthesizer to show citations
└── Capabilities: Document-backed rationale in decisions

NEW DATABASE TABLES:
├── documents (id, filename, doc_type, ticker, upload_date, content_hash)
└── document_chunks (id, document_id, chunk_index, content, embedding_id)

=============================================================================
SECTION 12: TARGET INTERVIEW PROMPTS
=============================================================================

These prompts demonstrate the SYNERGY between RAG and Decision Engine:

PROMPT 1 - Document-Informed Decision:
"I just uploaded NVIDIA's Q3 2024 earnings report. 
Given this new information, should I increase my position in the Growth Tech portfolio?"

Expected: Decision with earnings metrics, risk factors FROM THE FILING, citations

PROMPT 2 - Multi-Source Risk Assessment:
"I'm worried about my Dividend Income portfolio given recent Fed commentary. 
Search my documents for anything about interest rate sensitivity 
and tell me if I should hedge."

Expected: Combines macro data + document search + portfolio analysis

PROMPT 3 - The "Do Nothing" with Evidence:
"The market dropped 3% today. My All-Weather portfolio is down 1.5%. 
Should I make any changes? Check if any of my holdings have news."

Expected: HOLD decision with evidence that portfolio is working as designed

=============================================================================
SECTION 13: WORKING WITH THIS PROJECT
=============================================================================

RUNNING THE DEMO:
    python demos/langgraph_demo.py
    
    Commands:
    • /debug - Toggle debug mode
    • /portfolio <id> - Switch portfolio context
    • exit - Quit

RUNNING TESTS:
    python tests/test_phase66_comprehensive.py
    python tests/test_phase66_comprehensive.py --test decision  # Specific category

SEEDING DATABASE:
    python scripts/seed_database.py              # Full seed with prices
    python scripts/seed_database.py --skip-prices # Quick seed

KEY ENVIRONMENT VARIABLES:
    ANTHROPIC_API_KEY - Required for Claude LLM
    USE_MOCK_QUOTA=True - Skip API quota tracking in tests

COMMON ISSUES:
    "No portfolio specified" → Use /portfolio 1 or specify portfolio in query
    "No covariance matrix" → DataAgent must run before OptimizationAgent
    "DecisionLog not found" → Run: python -c "from portfolio_tool.database_setup import Base, engine; Base.metadata.create_all(engine)"

=============================================================================
END OF PROJECT CONTEXT
=============================================================================
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import date, datetime

# ─────────────────────────────────────────────────────────────────────────────
# ENUMS (Keep in sync with actual implementation)
# ─────────────────────────────────────────────────────────────────────────────

class QueryIntent(str, Enum):
    """Why is the user asking? (Phase 6.6)"""
    OPERATIONAL = "operational"       # Admin: list, show, create
    INFORMATION = "information"       # Factual: What's VIX?
    ANALYSIS = "analysis"             # Explanatory: Why did X happen?
    DECISION = "decision"             # Action: Should I rebalance?
    CLARIFICATION = "clarification"   # Ambiguous query
    UNKNOWN = "unknown"

class ExecutionIntent(str, Enum):
    """What agents to run? (Phase 6.6)"""
    OPTIMIZATION = "optimization"
    MACRO_ANALYSIS = "macro_analysis"
    REBALANCING = "rebalancing"
    BACKTEST = "backtest"
    DATA_FETCH = "data_fetch"
    RISK_ANALYSIS = "risk_analysis"
    DATA_MANAGEMENT = "data_management"
    PORTFOLIO_MGMT = "portfolio_mgmt"
    CLARIFICATION_NEEDED = "clarification_needed"
    UNKNOWN = "unknown"

class DecisionType(str, Enum):
    """PM-style decision types (Phase 6.6)"""
    HOLD = "hold"           # No action warranted
    TILT = "tilt"           # Minor tactical adjustment
    REBALANCE = "rebalance" # Structural portfolio change
    HEDGE = "hedge"         # Defensive action for crisis

class RiskStatus(str, Enum):
    """Portfolio risk status (Phase 6.6)"""
    ACCEPTABLE = "acceptable"   # All checks pass
    ELEVATED = "elevated"       # 1-2 breaches
    CRITICAL = "critical"       # 3+ breaches

class OptimizationMethod(str, Enum):
    """Portfolio optimization algorithms."""
    MEAN_VARIANCE = "mean_variance"
    MIN_VARIANCE = "min_variance"
    MAX_SHARPE = "max_sharpe"
    RISK_PARITY = "risk_parity"

class RegimeType(str, Enum):
    """Market regime classification."""
    RISK_ON = "risk_on"     # VIX < 15
    RISK_OFF = "risk_off"   # VIX > 25
    NEUTRAL = "neutral"     # Normal
    CRISIS = "crisis"       # VIX > 35

# ─────────────────────────────────────────────────────────────────────────────
# KEY DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PMDecisionSummary:
    """
    Executive summary for every portfolio decision.
    This is what a PM actually sees and acts on.
    """
    decision: DecisionType
    confidence: float                    # 0.0 - 1.0
    rationale: str                       # Human-readable explanation
    key_risks: List[str]                 # Top risk factors
    trade_required: bool                 # Explicit yes/no
    trigger: str                         # What prompted this assessment

@dataclass
class RiskAssessment:
    """Structured risk evaluation - runs BEFORE optimization."""
    status: RiskStatus
    hhi_score: float                     # Concentration (0-1)
    drivers: List[str]                   # Risk drivers
    breaches: List[str]                  # Limit breaches

@dataclass
class PortfolioConstraints:
    """Investment constraints for optimization."""
    min_weight: float = 0.0
    max_weight: float = 0.40
    max_volatility: Optional[float] = None
    long_only: bool = True
