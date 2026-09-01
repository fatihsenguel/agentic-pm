# 🏦 Quant Portfolio Manager - Multi-Agent System

An institutional-grade portfolio management system powered by AI agents.

## 🎯 Overview

This system uses a **multi-agent architecture** to handle portfolio optimization, macro analysis, backtesting, and rebalancing. Each agent is specialized for a specific task, coordinated by a supervisor agent (RiskManager).

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                             │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🎯 RISK MANAGER AGENT                         │
│                       (Supervisor)                               │
│         Analyzes requests, delegates to specialists              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ 📊 DATA      │   │ 🌍 MACRO     │   │ ⚖️ REBALANCE │
   │    AGENT     │   │    AGENT     │   │    AGENT     │
   └──────────────┘   └──────────────┘   └──────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
   ┌──────────────────────────────────────────────────────────────┐
   │                      TOOL LAYER                               │
   │   (data_tools, macro_tools, rebalance_tools, analytics)       │
   └──────────────────────────────────────────────────────────────┘
          │
          ▼
   ┌──────────────────────────────────────────────────────────────┐
   │                    DATA LAYER                                 │
   │              (DataManager, Providers)                         │
   └──────────────────────────────────────────────────────────────┘
          │
          ▼
   ┌──────────────────────────────────────────────────────────────┐
   │                    SQLite DATABASE                            │
   │        (daily_prices, macro_data, portfolios)                 │
   └──────────────────────────────────────────────────────────────┘
```

## ✨ Features

### Agents
- **RiskManagerAgent** - Supervisor that coordinates all other agents
- **DataAgent** - Market data fetching, covariance calculation, returns
- **MacroAgent** - VIX analysis, yield curve, market regime detection
- **RebalanceAgent** - Portfolio drift analysis, trade generation
- **OptimizationAgent** - Mean-variance, risk parity optimization
- **BacktestAgent** - Historical strategy simulation

### Capabilities
- 📊 **SAA (Strategic Asset Allocation)** - Optimal portfolio weights
- 🌍 **Macro Analysis** - VIX, yield curve, Fed sentiment
- 📈 **TAA (Tactical Asset Allocation)** - Regime-based adjustments
- ⚖️ **Rebalancing** - Drift detection, trade generation with costs
- 📉 **Backtesting** - Historical performance simulation
- 🔍 **Observability** - Full tracing, token tracking, cost estimation

## 🏗️ Architecture

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design documentation.

### Design Principles

1. **Separation of Concerns (SoC)**
   - `DataManager`: Only CRUD/DB operations
   - `MetricsCalculator`: Only math
   - `Provider`: Only API communication
   - `Tools`: Only agent interface

2. **Hot Potato Principle**
   - LLMs **NEVER** receive raw data (no CSV dumps)
   - Layers aggregate data: DB → Calculator → Tool → Agent
   - Example: Agent receives `{return: "13.6%", vol: "12%"}`, not 1000 prices

3. **Idempotent Operations**
   - All DB writes use `ON CONFLICT UPDATE`
   - Safe to retry, no duplicates

4. **Provider Abstraction**
   - Interfaces decouple logic from source (YFinance vs Bloomberg)

5. **Agent-Ready Responses**
   - Tools return structured dicts: `{success, data, metadata, error}`

6. **Session Isolation**
   - `DataManager` and `QuotaManager` use separate DB sessions

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd AGENTIC_FINANCE

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .

# Setup environment
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, etc.)

# Initialize database
alembic upgrade head
```

### Run Demo

```bash
# Full workflow demo (choreographed, safe for presentations)
python demos/demo_full_workflow.py

# Interactive multi-agent CLI
python demos/multi_agent_cli.py
```

### Example Prompts

```
"Optimiere ein Portfolio mit SPY, TLT, GLD und max 12% Volatilität"
"Wie ist die aktuelle Marktlage? Analysiere VIX und Yield Curve"
"Mein Portfolio ist gedriftet - soll ich rebalancen?"
"Backteste diese Strategie über 5 Jahre"
```

## 📁 Project Structure

```
AGENTIC_FINANCE/
├── alembic/              # Database migrations
├── data/                 # SQLite database
├── demos/                # Demo scripts
│   ├── demo_full_workflow.py
│   └── multi_agent_cli.py
├── docs/                 # Documentation
├── src/
│   ├── agents/           # AI Agents
│   │   ├── data_agent.py
│   │   ├── macro_agent.py
│   │   ├── rebalance_agent.py
│   │   └── risk_manager_agent.py
│   ├── observability/    # Tracing & Monitoring
│   │   ├── tracer.py
│   │   └── token_counter.py
│   └── portfolio_tool/   # Core Business Logic
│       ├── analytics/    # Metrics calculation
│       ├── backtest/     # Backtesting engine
│       ├── models/       # Data models
│       ├── optimization/ # Portfolio optimization
│       ├── providers/    # Data providers (YFinance)
│       ├── quant/        # Quantitative functions
│       ├── rag/          # Fed Minutes analysis
│       ├── services/     # Quota management
│       └── tools/        # Agent tools
├── tests/                # Test suite
└── outputs/              # Generated files
```

## 🔧 Configuration

### Environment Variables (.env)

```env
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///data/portfolio.db
LOG_LEVEL=INFO
```

### Config File (config.toml)

```toml
[database]
path = "data/portfolio.db"

[providers]
default = "yfinance"

[agents]
default_model = "gpt-4-turbo"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_rebalance.py -v

# Run with coverage
pytest --cov=src
```

## 📊 Observability

The system includes comprehensive tracing:

```python
from observability import get_tracer

tracer = get_tracer()

with tracer.trace_request("req_123", "User message") as req:
    with req.trace_agent("DataAgent") as agent:
        agent.log_thinking("Fetching data...")
        with agent.trace_tool("fetch_prices") as tool:
            result = fetch_prices(...)
            tool.set_output(result)

print(tracer.get_summary())
```

Output:
```
┌─ 🤖 [DataAgent] Starting...
│  💭 Fetching data...
│  🔧 Calling: fetch_prices
│     ✓ fetch_prices (50ms)
└─ ✓ [DataAgent] Done (50ms | 80 tokens)

📊 REQUEST SUMMARY
   Duration:      50ms
   Total Tokens:  80
   Est. Cost:     $0.0012
```

## 📈 Roadmap

- [x] Phase 5: Core Agents (Data, Macro, Rebalance)
- [x] Phase 6.3: Observability & Tracing
- [ ] Phase 6.1: Smart Router (LLM-based)
- [ ] Phase 6.2: LangGraph State Machine
- [ ] Phase 6.6: RAG Pipeline (Fed Minutes)
- [ ] Phase 6.7: Chainlit UI
- [ ] Phase 6.11: Human-in-the-Loop Approval

See [ROADMAP_PHASE_6.md](docs/ROADMAP_PHASE_6.md) for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) and [LangGraph](https://github.com/langchain-ai/langgraph)
- Market data from [Yahoo Finance](https://finance.yahoo.com/)
- Optimization powered by [scipy](https://scipy.org/)