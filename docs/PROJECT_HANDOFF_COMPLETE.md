# AGENTIC QUANT PORTFOLIO MANAGER
## Complete Project Handoff Document for LLM Continuation

**Version:** 1.0
**Date:** January 2026
**Status:** Phase 3 Complete, Phase 5 (Quant PM) Ready to Start

---

# 📋 QUICK CONTEXT FOR NEW LLM

## What is this project?

An **AI-powered financial analysis platform** that uses a multi-agent architecture to perform portfolio management tasks. The user interacts via natural language, and specialized AI agents collaborate to fetch data, optimize portfolios, analyze documents, and backtest strategies.

## Current State

| Aspect | Status |
|--------|--------|
| **Data Infrastructure** | ✅ Complete (Phase 1-2) |
| **Analytics Engine** | ✅ Complete (Phase 3) |
| **Single Agent** | ✅ Working (14 tools) |
| **Multi-Agent System** | ⏳ Not started (Phase 5) |
| **SAA/TAA/Backtesting** | ⏳ Not started (Phase 5) |

## Target Audience

The developer is applying for **Portfolio Manager / Quant PM roles** at:
- Investment Banks (Goldman Sachs, JPMorgan, Deutsche Bank)
- Asset Managers (BlackRock, Allianz, DWS, Amundi)

The project must demonstrate both **AI engineering skills** AND **quantitative finance understanding**.

---

# 🎯 PROJECT GOALS (Phase 5)

## The 4 Target Prompts

| # | Prompt | What it demonstrates |
|---|--------|---------------------|
| **#1** | Strategic Asset Allocation (SAA) | Markowitz optimization, Risk Parity, constraints |
| **#2** | Tactical Asset Allocation (TAA) | RAG on Fed Minutes, regime detection, signals |
| **#3** | Strategy Backtesting | Deterministic simulation, NO LLM in loop |
| **#4** | Rebalancing Recommendation | Drift analysis, tax-aware decisions |

## Critical Design Principle: No Look-Ahead Bias

```
⚠️ CRITICAL FOR BACKTESTING:

The LLM must NEVER make trade decisions during backtests.

✅ LLM ALLOWED:
   • Translate user strategy → deterministic rules
   • Interpret completed backtest results
   • Generate reports

❌ LLM FORBIDDEN:
   • Decide "should I buy in 2020?"
   • Any decision inside the simulation loop
   • Access to "future" data during simulation

WHY: LLM was trained on data that includes 2020-2024.
     It "knows" what happened. Using it for decisions = bias.
```

---

# 🏗️ CURRENT ARCHITECTURE (Phase 3)

## Project Structure

```
agentic-finance/
├── src/
│   ├── agents/                      # AI Layer
│   │   ├── cli.py                   # REPL with debug modes (OFF/ON/VERBOSE)
│   │   ├── config.py                # LLM configuration
│   │   ├── finance_agent.py         # LangGraph single agent (ReAct pattern)
│   │   ├── prompts.py               # System prompts with scope guards
│   │   └── state.py                 # AgentState, message trimming
│   │
│   ├── portfolio_tool/              # Data Layer
│   │   ├── analytics/
│   │   │   └── metrics.py           # MetricsCalculator (returns, vol, Sharpe, drawdown)
│   │   ├── models/
│   │   │   └── responses.py         # UpdateResult, QueryResult DTOs
│   │   ├── providers/
│   │   │   ├── base.py              # DataProviderInterface (abstract)
│   │   │   ├── yfinance_provider.py # YFinance implementation
│   │   │   └── utils.py             # safe_int, safe_float, safe_decimal
│   │   ├── services/
│   │   │   └── quota_manager.py     # Rate limiting with session isolation
│   │   ├── tools/
│   │   │   ├── data_tools.py        # 8 data tools (@tool decorated)
│   │   │   └── analytics_tools.py   # 6 analytics tools
│   │   ├── database_setup.py        # SQLAlchemy ORM models
│   │   └── data_manager.py          # Facade pattern (single entry point)
│   │
│   └── api/
│       └── main.py                  # (Future FastAPI, not implemented)
│
├── tests/
│   ├── conftest.py                  # Pytest config, adds src/ to path
│   ├── test_phase3_analytics.py     # Analytics tests
│   └── ...
│
├── alembic/                         # Database migrations
│   └── versions/                    # 6 migration files
│
├── data/
│   └── portfolio.db                 # SQLite database
│
├── config.toml                      # App configuration
└── pyproject.toml                   # Dependencies
```

## Technology Stack

| Category | Technologies |
|----------|--------------|
| **Language** | Python 3.10+ |
| **LLM Framework** | LangChain, LangGraph |
| **Database** | SQLAlchemy 2.0, SQLite, Alembic |
| **Data Source** | yfinance |
| **Analytics** | Pandas |
| **Testing** | pytest |
| **LLM** | OpenAI GPT-4o-mini (configurable) |

## Dependencies (pyproject.toml)

```toml
dependencies = [
    "sqlalchemy>=2.0.0",
    "pandas>=2.0.0",
    "yfinance>=0.2.0",
]

[project.optional-dependencies]
agents = [
    "langchain>=0.2.0",
    "langgraph>=0.2.0",
]
```

---

# 📊 DATA LAYER DETAILS

## Database Schema (SQLAlchemy Models)

```
┌─────────────────────────────────────────────────────────────────┐
│  CORE TABLES                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  assets                    # Tracked stocks                     │
│  ├── id, ticker (unique), name, asset_class                    │
│  ├── sector, industry, country, currency                       │
│  └── Relationships: 1:N with prices, earnings, financials      │
│                                                                 │
│  daily_prices              # OHLCV time series                  │
│  ├── asset_id, date, open, high, low, close, volume            │
│  └── UniqueConstraint: (asset_id, date) → idempotent upserts   │
│                                                                 │
│  quarterly_earnings        # EPS data                           │
│  ├── asset_id, report_date, revenue, basic_eps                 │
│  └── UniqueConstraint: (asset_id, report_date)                 │
│                                                                 │
│  financial_statements      # Income/Balance/CashFlow            │
│  ├── asset_id, date, report_type, period_type                  │
│  ├── 35+ columns: revenue, net_income, total_assets, etc.      │
│  ├── raw_json: Full provider response for extensibility        │
│  └── UniqueConstraint: (asset_id, date, report_type, period)   │
│                                                                 │
│  fundamentals              # Snapshot data (1:1 with Asset)     │
│  └── market_cap, forward_pe, beta, trailing_eps                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  OPERATIONAL TABLES                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  asset_fetch_metadata      # Tracks last fetch times            │
│  pipeline_runs             # ETL job audit log                  │
│  api_quotas                # Rate limit tracking                │
│  api_call_logs             # Immutable API call ledger          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## DataManager (Facade Pattern)

The `DataManager` is the **single entry point** for all data operations:

```python
class DataManager:
    """
    Facade: Coordinates Provider (API) + Database (Persistence)
    All methods return UpdateResult or QueryResult DTOs
    """
    
    def __init__(self, session: Session, provider: DataProviderInterface):
        self.session = session
        self.provider = provider  # YFinanceProvider
    
    # UPDATE METHODS (fetch from API → upsert to DB)
    def update_prices_for_asset(asset, start_date) -> UpdateResult
    def update_earnings_for_asset(asset, force_update) -> UpdateResult
    def update_financial_statements_for_asset(asset, report_type, period_type) -> UpdateResult
    
    # Internal helpers
    def _perform_upsert(model, values, index_elements) -> int  # Batch upsert
    def _get_or_create_asset(ticker, name, asset_class) -> Asset
    def _should_fetch(last_fetch_time, interval_days) -> bool
```

## Response DTOs

```python
@dataclass
class UpdateResult:
    """Response from data update operations."""
    success: bool
    operation: str              # "update_prices", "update_earnings"
    affected_count: int         # Rows inserted/updated
    entities: List[str]         # ["AAPL", "MSFT"]
    entity_type: str = "asset"
    metadata: Dict = {}         # {"status": "up_to_date"}
    error_message: Optional[str] = None

@dataclass
class QueryResult:
    """Response from data retrieval operations."""
    success: bool
    data: List[Dict]            # Query results
    count: int
    query_type: str
    metadata: Dict = {}
    error_message: Optional[str] = None
```

## Current Database Status

| Asset | Ticker | Data Status |
|-------|--------|-------------|
| Apple | AAPL | Prices, some financials |
| Microsoft | MSFT | Prices, some financials |
| SAP | SAP | Partial |
| Amazon | AMZN | Partial |
| Palantir | PLTR | Partial |

*Note: Data is from testing, not fully up-to-date*

---

# 🤖 AI LAYER DETAILS

## Current Agent (Single Agent, Phase 3)

```python
# LangGraph ReAct Pattern

def create_finance_agent():
    """
    Graph:
    ┌─────────┐  tool_calls  ┌─────────┐
    │  agent  │ ────────────►│  tools  │
    └────┬────┘              └────┬────┘
         │ no tool_calls          │
         ▼                        │
      [END]  ◄────────────────────┘
    """
    tool_node = ToolNode(ALL_TOOLS)  # 14 tools
    
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
```

**Key Configuration:**
```python
llm_with_tools = llm.bind_tools(ALL_TOOLS, parallel_tool_calls=False)  # Sequential!
```

## Current Tools (14 Total)

### Data Tools (8)
```python
# FETCH (trigger API calls)
fetch_stock_prices(ticker, start_date?)      → UpdateResult
fetch_financial_statements(ticker, type)     → UpdateResult
fetch_fundamentals(ticker)                   → UpdateResult
fetch_earnings_history(ticker)               → UpdateResult

# QUERY (database only)
get_asset_info(ticker)                       → QueryResult
list_tracked_assets()                        → QueryResult
get_latest_price(ticker)                     → QueryResult
query_financial_data(type, ticker, limit?)   → QueryResult
```

### Analytics Tools (6)
```python
calculate_returns(ticker, days=365)          → Dict (return%, CAGR)
calculate_volatility(ticker, days=365)       → Dict (annualized vol)
calculate_sharpe_ratio(ticker, days=365)     → Dict (risk-adjusted)
calculate_max_drawdown(ticker, days=365)     → Dict (worst decline)
get_price_statistics(ticker, days=30)        → Dict (min/max/avg)
compare_stocks(tickers, days=365)            → Dict (side-by-side)
```

## MetricsCalculator

```python
class MetricsCalculator:
    """All calculations include audit trail."""
    
    def calculate_returns(self, ticker, days=365) -> Dict:
        # Returns include:
        return {
            "success": True,
            "ticker": "AAPL",
            "period_days": 364,
            "data_points": 251,           # Transparency
            "first_date": "2025-01-15",   # Audit trail
            "last_date": "2026-01-14",    # Audit trail
            "first_price": 182.50,        # Verifiable
            "last_price": 207.39,         # Verifiable
            "total_return": 0.1363,
            "total_return_pct": "13.63%",
            "cagr": 0.1368,
            "interpretation": "..."       # Human-readable
        }
```

## CLI Features

```
Commands:
  /debug    → Toggle: OFF → ON (brief) → VERBOSE (full JSON) → OFF
  /stats    → Token usage & cost estimate
  /clear    → Clear conversation history
  /quit     → Exit with session summary

Debug Modes:
  OFF:      No debug output
  ON:       Tool calls + key metrics summary
  VERBOSE:  Full JSON responses (for auditing calculations)
```

---

# 🧭 DESIGN PRINCIPLES

## 1. Separation of Concerns (SoC)
```
Each component has ONE responsibility:
├── DataManager      → Data operations only
├── MetricsCalculator → Calculations only
├── YFinanceProvider → API communication only
└── Tools            → Agent interface only
```

## 2. Hot Potato Principle
```
LLMs NEVER receive raw data. Each layer aggregates.

Example:
├── 10,000 price points in DB
├── MetricsCalculator: Calculates return
└── Agent receives: {return: "13.63%", period: "364 days"}
```

## 3. Idempotent Operations
```
All DB writes use ON CONFLICT UPDATE:
├── Safe to retry failed operations
├── No duplicate data
└── _perform_upsert() handles batching
```

## 4. Provider Abstraction
```python
class DataProviderInterface(ABC):
    """YFinanceProvider implements this. Bloomberg could too."""
    
    @abstractmethod
    def get_daily_prices(ticker, start, end) -> List[PriceDTO]
    
    @abstractmethod
    def get_financial_statements(ticker, type) -> List[FinancialDTO]
```

## 5. Agent-Ready Responses
```
All tools return structured DTOs:
├── success: bool
├── affected_count / data
├── metadata: Dict (audit trail)
└── error_message: Optional
```

## 6. Session Isolation
```
QuotaManager uses separate sessions to prevent SQLite locking:
├── DataManager: Main session for data ops
└── QuotaManager: Own session factory for quota tracking
```

---

# 🗺️ PHASE 5 ROADMAP SUMMARY

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RISK MANAGER AGENT (Supervisor)              │
│         Parses mandate, validates constraints, coordinates      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  DATA AGENT   │   │ OPTIMIZATION  │   │  MACRO/RAG    │
│               │   │    AGENT      │   │    AGENT      │
│ • Prices      │   │ • Markowitz   │   │ • Fed Minutes │
│ • Covariance  │   │ • Risk Parity │   │ • Sentiment   │
│ • VIX data    │   │ • Constraints │   │ • Regime      │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ DataManager   │   │ PyPortfolioOpt│   │ ChromaDB      │
│ (existing)    │   │ scipy.optimize│   │ (new)         │
└───────────────┘   └───────────────┘   └───────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      BACKTEST AGENT                             │
│  ⚠️ CRITICAL: Uses DETERMINISTIC engine, NO LLM in simulation  │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | Foundation + Data Agent | Multi-agent structure, covariance calculation |
| 2 | Optimization Agent | Markowitz, Risk Parity, Prompt #1 (SAA) |
| 3 | Backtest Agent | Deterministic engine, Prompt #3 |
| 4 | Macro/RAG Agent | Fed Minutes analysis, Prompt #2 (TAA) |
| 5-6 | Integration + Polish | Prompt #4, demos, documentation |

## New Components to Build

```
src/
├── agents/
│   ├── base_agent.py           # BaseAgent abstract class
│   ├── risk_manager_agent.py   # Supervisor
│   ├── data_agent.py           # Quant data focus
│   ├── optimization_agent.py   # SAA/TAA
│   ├── macro_agent.py          # RAG for Fed Minutes
│   ├── backtest_agent.py       # Orchestrates backtest
│   └── protocols.py            # PortfolioTask, PortfolioResult
│
├── portfolio_tool/
│   ├── quant/                  # NEW MODULE
│   │   ├── covariance.py       # Cov matrix estimation
│   │   ├── returns.py          # Return calculations
│   │   └── risk_metrics.py     # VaR, etc.
│   │
│   ├── optimization/           # NEW MODULE
│   │   ├── base.py             # OptimizerInterface
│   │   ├── mean_variance.py    # Markowitz
│   │   ├── risk_parity.py      # Equal risk contribution
│   │   └── constraints.py      # Portfolio constraints
│   │
│   ├── backtest/               # NEW MODULE
│   │   ├── engine.py           # BacktestEngine (NO LLM!)
│   │   ├── strategies.py       # Strategy definitions
│   │   └── metrics.py          # Performance attribution
│   │
│   └── rag/                    # NEW MODULE
│       ├── document_loader.py  # PDF processing
│       ├── chunker.py          # Semantic chunking
│       ├── embeddings.py       # Embedding provider
│       └── vector_store.py     # ChromaDB wrapper
```

---

# ⚠️ CRITICAL INFORMATION FOR CONTINUATION

## 1. SQLite Locking Issue (SOLVED)

```python
# PROBLEM: Parallel tool calls caused "database is locked"
# SOLUTION: 
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)

# QuotaManager also has session isolation
class QuotaManager:
    def _get_session(self):  # Creates fresh session per operation
        return SessionLocal()
```

## 2. NaN Handling (SOLVED)

```python
# PROBLEM: yfinance returns NaN/inf values that crash DB inserts
# SOLUTION: Safe conversion utilities

def safe_int(value, default=None) -> Optional[int]:
    """Handles NaN, inf, None, invalid types."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
```

## 3. Hot Potato Principle

```
NEVER send raw data to LLM:
❌ BAD:  Return 10,000 price rows to agent
✅ GOOD: Return {return: "13.63%", volatility: "22%"}

This applies to ALL layers, including agent-to-agent communication.
```

## 4. Backtest Engine Design

```python
class BacktestEngine:
    """
    ⚠️ THIS CLASS MUST NOT USE ANY LLM.
    
    All decisions are based on pre-defined rules.
    Same inputs = Same outputs. Always.
    """
    
    def run(self, strategy: Strategy, data: DataFrame) -> BacktestResult:
        for date in trading_days:
            # DETERMINISTIC rule evaluation only
            if strategy.should_rebalance(date):  # Pure boolean logic
                self._rebalance(...)
        return results
```

## 5. Testing Strategy

```
Level 1 (Unit):        ✅ Pure functions - deterministic, fast
Level 2 (Integration): ✅ Tools with DB - testable, important  
Level 3 (Agent E2E):   ⚠️ Minimal - LLM non-deterministic, expensive

Run tests from project root:
$ cd E:\Programming\AGENTIC_FINANCE
$ pytest tests/ -v
```

## 6. Config Settings

```toml
# config.toml
[data_fetch]
earnings_fetch_interval_days = 7
profile_fetch_interval_days  = 30
shares_fetch_interval_days   = 30
```

---

# 📁 KEY FILES REFERENCE

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `data_manager.py` | Facade for data ops | `DataManager`, `_perform_upsert()` |
| `database_setup.py` | ORM models | `Asset`, `DailyPrice`, `FinancialStatement` |
| `finance_agent.py` | LangGraph agent | `create_finance_agent()`, `agent_node()` |
| `responses.py` | DTOs | `UpdateResult`, `QueryResult` |
| `metrics.py` | Calculations | `MetricsCalculator` |
| `data_tools.py` | Agent tools | `fetch_stock_prices()`, etc. |
| `analytics_tools.py` | Agent tools | `calculate_returns()`, etc. |
| `prompts.py` | System prompts | `FINANCE_AGENT_SYSTEM_PROMPT` |
| `cli.py` | REPL interface | Debug modes, token tracking |
| `quota_manager.py` | Rate limiting | Session isolation pattern |
| `yfinance_provider.py` | API wrapper | Implements `DataProviderInterface` |
| `utils.py` | Helpers | `safe_int()`, `safe_float()` |

---

# 🚀 IMMEDIATE NEXT STEPS

1. **Create `src/agents/base_agent.py`** - Abstract base class for all agents
2. **Create `src/agents/protocols.py`** - `PortfolioTask`, `PortfolioResult` DTOs
3. **Create `src/portfolio_tool/quant/covariance.py`** - Covariance matrix estimation
4. **Refactor existing code into `DataAgent`** - Extract from current single agent
5. **Build `OptimizationAgent`** with PyPortfolioOpt integration

---

# 📚 RELATED DOCUMENTS

| Document | Location | Purpose |
|----------|----------|---------|
| Roadmap v5 | `ROADMAP_v5_Quant_PM.md` | Detailed implementation plan |
| CV Entry | `CV_Projects_MultiAgent_Final.md` | Interview talking points |
| Project Status | `PROJECT_STATUS_Phase3_Complete.md` | Phase 3 summary |

---

# ✅ CHECKLIST FOR NEW LLM

Before starting implementation, verify:

- [ ] Understand the 4 target prompts (SAA, TAA, Backtest, Rebalance)
- [ ] Understand "No Look-Ahead Bias" principle for backtesting
- [ ] Understand Hot Potato Principle (no raw data to LLMs)
- [ ] Understand existing patterns (Facade, DTOs, Idempotent Upserts)
- [ ] Review ROADMAP_v5_Quant_PM.md for detailed week-by-week plan
- [ ] Ask clarifying questions before writing code

**Ready to continue Phase 5 implementation!**

