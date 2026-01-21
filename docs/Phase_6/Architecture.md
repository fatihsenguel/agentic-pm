# 🏗️ Architecture Documentation

## Overview

The Quant Portfolio Manager follows a **layered multi-agent architecture** designed for institutional-grade reliability, auditability, and maintainability.

---

## 🎯 Design Principles

### 1. Separation of Concerns (SoC)

Each component has **ONE responsibility**:

| Component | Responsibility | Does NOT do |
|-----------|---------------|-------------|
| `DataManager` | CRUD / DB Operations | Math, API calls |
| `MetricsCalculator` | Mathematical computations | DB access, API calls |
| `Provider` | External API communication | DB access, math |
| `Tools` | Agent interface layer | Business logic |
| `Agent` | Decision making, orchestration | Direct data access |

```
❌ WRONG: Agent calls Yahoo Finance directly
✅ RIGHT: Agent → Tool → DataManager → Provider → Yahoo Finance
```

### 2. Hot Potato Principle 🥔

**LLMs NEVER receive raw data.**

The principle: Pass data through layers, each layer **aggregates and summarizes**.

```
Raw Data (1000 prices)
    │
    ▼ DataManager: Store in DB
Stored Data
    │
    ▼ MetricsCalculator: Calculate returns, volatility
Metrics (return: 0.136, vol: 0.12)
    │
    ▼ Tool: Format for agent
Response {success: true, return: "13.6%", vol: "12%"}
    │
    ▼ Agent: Interpret and explain
"The portfolio returned 13.6% with 12% volatility"
```

**Why?**
- Token efficiency (don't waste tokens on raw data)
- Prevents hallucination (agent can't misinterpret raw numbers)
- Faster responses
- Lower cost

### 3. Idempotent Operations

All database writes are **safe to retry**:

```python
# ✅ CORRECT: Idempotent insert
INSERT INTO daily_prices (ticker, date, close_price)
VALUES ('SPY', '2024-01-15', 450.00)
ON CONFLICT (ticker, date) DO UPDATE SET close_price = 450.00;

# ❌ WRONG: Non-idempotent
INSERT INTO daily_prices (ticker, date, close_price)
VALUES ('SPY', '2024-01-15', 450.00);
# Fails on retry with duplicate key error!
```

### 4. Provider Abstraction

Data sources are **interchangeable**:

```python
class DataProviderInterface(Protocol):
    def fetch_prices(self, ticker: str, period: str) -> pd.DataFrame: ...
    def fetch_info(self, ticker: str) -> Dict: ...

class YFinanceProvider(DataProviderInterface):
    """Free data from Yahoo Finance."""
    ...

class BloombergProvider(DataProviderInterface):
    """Premium data from Bloomberg Terminal."""
    ...

# Usage - provider can be swapped without changing business logic
provider = get_provider()  # Returns YFinance or Bloomberg based on config
data = provider.fetch_prices("SPY", "1Y")
```

### 5. Agent-Ready Responses

All tools return **structured responses**:

```python
@dataclass
class ToolResponse:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str] = None

# Example
{
    "success": True,
    "data": {
        "vix_level": 18.5,
        "regime": "NEUTRAL",
        "recommendation": "Maintain current allocation"
    },
    "metadata": {
        "timestamp": "2024-01-15T10:30:00",
        "data_source": "yahoo_finance",
        "freshness": "real-time"
    },
    "error": None
}
```

### 6. Session Isolation

Prevent SQLite locking with **separate sessions**:

```python
# ❌ WRONG: Shared session causes locks
class App:
    def __init__(self):
        self.session = create_session()
        self.data_manager = DataManager(self.session)
        self.quota_manager = QuotaManager(self.session)  # LOCK!

# ✅ RIGHT: Isolated sessions
class App:
    def __init__(self):
        self.data_manager = DataManager()   # Creates own session
        self.quota_manager = QuotaManager() # Creates own session
```

---

## 📐 System Architecture

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                            │
│                                                                      │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│   │  Chainlit   │    │    CLI      │    │   REST API  │            │
│   │     UI      │    │             │    │             │            │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘            │
└──────────┼──────────────────┼──────────────────┼────────────────────┘
           │                  │                  │
           └──────────────────┼──────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────┐
│                        OBSERVABILITY LAYER                           │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  Tracer  │  TokenCounter  │  CostCalculator  │  Logger      │   │
│   └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────┐
│                        AGENT LAYER                                   │
│                                                                      │
│                    ┌─────────────────┐                              │
│                    │  RiskManager    │                              │
│                    │  (Supervisor)   │                              │
│                    └────────┬────────┘                              │
│                             │                                        │
│         ┌───────────────────┼───────────────────┐                   │
│         ▼                   ▼                   ▼                   │
│   ┌───────────┐      ┌───────────┐      ┌───────────┐              │
│   │   Data    │      │   Macro   │      │ Rebalance │              │
│   │   Agent   │      │   Agent   │      │   Agent   │              │
│   └─────┬─────┘      └─────┬─────┘      └─────┬─────┘              │
│         │                  │                  │                     │
│   ┌─────┴─────┐      ┌─────┴─────┐      ┌─────┴─────┐              │
│   │Optimization│     │ Backtest  │      │           │              │
│   │   Agent   │      │   Agent   │      │           │              │
│   └───────────┘      └───────────┘      └───────────┘              │
│                                                                      │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────┐
│                        TOOL LAYER                                    │
│                                                                      │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│   │ data_tools │  │macro_tools │  │rebalance_  │  │ analytics_ │   │
│   │            │  │            │  │   tools    │  │   tools    │   │
│   └─────┬──────┘  └─────┬──────┘  └────────────┘  └─────┬──────┘   │
│         │               │                               │           │
└─────────┼───────────────┼───────────────────────────────┼───────────┘
          │               │                               │
┌─────────┼───────────────┼───────────────────────────────┼───────────┐
│         │          SERVICE LAYER                        │           │
│         │                                               │           │
│   ┌─────┴──────┐  ┌─────────────┐  ┌─────────────┐     │           │
│   │   Data     │  │   Quota     │  │  Metrics    │     │           │
│   │  Manager   │  │  Manager    │  │ Calculator  │◄────┘           │
│   └─────┬──────┘  └─────────────┘  └─────────────┘                 │
│         │                                                           │
└─────────┼───────────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────────────┐
│         │           PROVIDER LAYER                                   │
│         │                                                            │
│   ┌─────┴──────┐                                                    │
│   │  YFinance  │  (Future: Bloomberg, Refinitiv, etc.)              │
│   │  Provider  │                                                    │
│   └─────┬──────┘                                                    │
│         │                                                            │
└─────────┼───────────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────────────┐
│         │           DATA LAYER                                       │
│         ▼                                                            │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    SQLite Database                           │   │
│   │                                                              │   │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │   │
│   │  │daily_prices│  │ macro_data │  │ portfolios │            │   │
│   │  └────────────┘  └────────────┘  └────────────┘            │   │
│   │                                                              │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent Architecture

### Agent Types

| Agent | Role | Tools | LLM Required |
|-------|------|-------|--------------|
| **RiskManagerAgent** | Supervisor, routing | All (via delegation) | Yes |
| **DataAgent** | Market data | fetch_prices, calculate_covariance | Yes |
| **MacroAgent** | Macro analysis | fetch_macro, assess_regime, taa_signal | Yes |
| **RebalanceAgent** | Rebalancing | analyze_rebalance, calculate_drift | No* |
| **OptimizationAgent** | Portfolio opt | optimize_portfolio | No* |
| **BacktestAgent** | Backtesting | run_backtest | No* |

*These agents use deterministic tools. LLM is only for interpretation.

### Agent Communication Flow

```
User: "Optimiere mein Portfolio mit max 12% Volatilität"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ RiskManagerAgent                                             │
│                                                              │
│ 1. Parse intent: OPTIMIZATION                                │
│ 2. Extract params: {max_vol: 0.12}                          │
│ 3. Delegate to: DataAgent, OptimizationAgent                │
└─────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│  DataAgent    │       │ Optimization  │
│               │       │    Agent      │
│ fetch_prices()│──────►│               │
│ calc_cov()    │ data  │ optimize()    │
└───────────────┘       └───────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Optimal Weights:  │
                    │ SPY: 40%          │
                    │ TLT: 30%          │
                    │ GLD: 15%          │
                    │ VWO: 15%          │
                    │ Sharpe: 0.73      │
                    └───────────────────┘
```

---

## 🔧 Tool Architecture

### Tool Design Pattern

```python
def tool_function(
    param1: str,
    param2: int,
    # ... parameters the agent can provide
) -> Dict[str, Any]:
    """
    Tool docstring (shown to LLM).
    
    Args:
        param1: Description for LLM
        param2: Description for LLM
    
    Returns:
        Structured response dict
    """
    try:
        # 1. Validate inputs
        validated = validate_inputs(param1, param2)
        
        # 2. Call service layer
        result = service.do_something(validated)
        
        # 3. Return structured response
        return {
            "success": True,
            "data": result,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": "service_name"
            }
        }
    except ValidationError as e:
        return {
            "success": False,
            "data": None,
            "error": f"Validation error: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Unexpected error: {e}"
        }
```

### Tool Categories

```
tools/
├── data_tools.py       # Price fetching, covariance, returns
├── macro_tools.py      # VIX, yields, regime assessment
├── rebalance_tools.py  # Drift calculation, trade generation
└── analytics_tools.py  # Performance metrics, risk metrics
```

---

## 💾 Data Architecture

### Database Schema

```sql
-- Core price data
CREATE TABLE daily_prices (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(15,4),
    high_price DECIMAL(15,4),
    low_price DECIMAL(15,4),
    close_price DECIMAL(15,4),
    adj_close DECIMAL(15,4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);

-- Macro indicators
CREATE TABLE macro_data (
    id INTEGER PRIMARY KEY,
    indicator VARCHAR(50) NOT NULL,  -- 'VIX', 'TNX_10Y', 'IRX_3M'
    date DATE NOT NULL,
    value DECIMAL(15,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(indicator, date)
);

-- Portfolio tracking (Phase 6.5)
CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP,
    base_currency VARCHAR(3) DEFAULT 'EUR'
);

CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(id),
    ticker VARCHAR(10),
    shares DECIMAL(15,4),
    cost_basis DECIMAL(15,4),
    acquired_date DATE
);
```

### Data Flow

```
External API (Yahoo Finance)
         │
         ▼
┌─────────────────┐
│ YFinanceProvider│ ──► Rate limiting, error handling
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   DataManager   │ ──► CRUD operations, caching
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLite (WAL)   │ ──► Persistent storage
└─────────────────┘
```

---

## 🔍 Observability Architecture

### Tracing Flow

```
Request arrives
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│ Tracer.trace_request("req_123", "User message")             │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ AgentTrace("RiskManager")                           │   │
│   │                                                      │   │
│   │   ├─ log_thinking("Analyzing...")                   │   │
│   │   ├─ log_decision("Delegate to DataAgent")          │   │
│   │   │                                                  │   │
│   │   └─ ToolTrace("fetch_prices")                      │   │
│   │       ├─ set_input({tickers: "SPY"})                │   │
│   │       └─ set_output({success: true})                │   │
│   │                                                      │   │
│   │   set_tokens(150, 80)                               │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
│ Output: RequestTrace with all events                        │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────┐
│ Console Output  │ (formatted, colored)
│ JSON Export     │ (for audit)
│ LangSmith       │ (optional)
└─────────────────┘
```

### Token Tracking

```
┌─────────────────────────────────────────────────────────────┐
│ TokenCounter                                                 │
│                                                              │
│   add_usage("DataAgent", input=150, output=80, model="gpt4")│
│   add_usage("MacroAgent", input=200, output=100)            │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ Usage Report:                                        │   │
│   │   Total: 530 tokens                                  │   │
│   │   Cost: $0.0089                                      │   │
│   │   By Agent:                                          │   │
│   │     DataAgent: 230 tokens                            │   │
│   │     MacroAgent: 300 tokens                           │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 Security Considerations

### API Keys
- Stored in `.env` (never committed)
- Loaded via `python-dotenv`

### Database
- SQLite with WAL mode for concurrent reads
- No sensitive data in plain text

### LLM Safety
- Output validation with Pydantic (Phase 6.12)
- No raw data to LLM (Hot Potato Principle)

---

## 📈 Future Architecture (Phase 6+)

### LangGraph Integration (Phase 6.2)

```python
from langgraph.graph import StateGraph

graph = StateGraph(AgentState)

# Nodes
graph.add_node("supervisor", supervisor_node)
graph.add_node("data_agent", data_agent_node)
graph.add_node("macro_agent", macro_agent_node)
graph.add_node("rebalance_agent", rebalance_agent_node)

# Edges
graph.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "data": "data_agent",
        "macro": "macro_agent",
        "rebalance": "rebalance_agent",
        "end": END
    }
)

# Human-in-the-loop (Phase 6.11)
app = graph.compile(
    checkpointer=memory,
    interrupt_before=["execute_trades"]  # Requires human approval
)
```

### RAG Pipeline (Phase 6.6)

```
Fed Minutes PDF
      │
      ▼
┌─────────────────┐
│ Document Loader │ ──► Extract text
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Chunker      │ ──► Split into 500-token chunks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Embeddings    │ ──► OpenAI text-embedding-3-small
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    ChromaDB     │ ──► Vector storage
└────────┬────────┘
         │
         ▼
Query: "What did the Fed say about inflation?"
         │
         ▼
┌─────────────────┐
│   Retriever     │ ──► Find relevant chunks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      LLM        │ ──► Synthesize answer
└─────────────────┘
```

---

## 📚 References

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)