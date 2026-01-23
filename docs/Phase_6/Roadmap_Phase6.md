# 🚀 ROADMAP: From Demo MVP to Production-Ready Multi-Agent System

## Executive Summary

Wir haben ein funktionierendes **Demo-MVP** gebaut. Jetzt geht es darum, die "Schummelstellen" zu eliminieren und ein **echtes, produktionsreifes Multi-Agent System** zu bauen.

**Aktueller Stand:** ~70% Complete (Demo-Ready)
**Ziel:** 100% Production-Ready

---

## 📊 Current State Analysis

### ✅ Was funktioniert (Production-Ready)

| Komponente | Status | Notes |
|------------|--------|-------|
| Database Schema | ✅ | Alembic Migrations, SQLite |
| DataManager | ✅ | CRUD für Prices, Macro Data |
| YFinance Provider | ✅ | Rate Limiting, Quota Management |
| Rebalance Tools | ✅ | Pure Math, Deterministic |
| MacroAgent Tools | ✅ | VIX, Yields, Regime Detection |
| DataAgent Tools | ✅ | Prices, Covariance, Returns |
| Demo Script | ✅ | Visual Agent Orchestration |

### ⚠️ Was "geschummelt" ist (Demo-Only)

| Komponente | Demo-Status | Production-Requirement |
|------------|-------------|------------------------|
| **Router/Supervisor** | If/Else Keywords | LLM-based Intent Detection |
| **Portfolio Data** | Hardcoded Weights | User Input / Database |
| **Agent Execution** | Direct Tool Calls | LangGraph State Machine |
| **RAG Pipeline** | Simulated | Real Embeddings + ChromaDB |
| **Tracing** | Print Statements | LangSmith / Custom Logger |
| **Token Tracking** | None | Per-Agent Token Counter |
| **Error Handling** | Basic Try/Catch | Structured Error Recovery |
| **UI** | CLI | Chainlit / Streamlit |

---

## 🎯 PHASE 6: Production-Ready Multi-Agent System

### Phase 6.1: Smart Router (LLM-Based Intent Detection)
**Priority:** 🔴 CRITICAL
**Effort:** 4-6 hours

Der "Supervisor" muss intelligent entscheiden, nicht mit If/Else.

```
Aktuell (Demo):
User: "Wie ist der Markt?" 
→ if "markt" in text: call MacroAgent  # Dumm!

Ziel (Production):
User: "Sollte ich bei diesem VIX-Level mehr in Bonds gehen?"
→ LLM analysiert: Braucht MacroAgent (VIX) + RebalanceAgent (Allocation)
→ Orchestriert beide intelligent
```

**Deliverables:**
- [ ] `src/agents/smart_router.py` - LLM-based intent detection
- [ ] `src/agents/router_prompts.py` - System prompts für Router
- [ ] Router kann Multi-Agent Chains erkennen
- [ ] Router kann Rückfragen stellen bei Ambiguität

---

### Phase 6.2: LangGraph State Machine
**Priority:** 🔴 CRITICAL  
**Effort:** 6-8 hours

Echte Agent-Orchestrierung statt direkter Tool-Calls.

```
Aktuell (Demo):
result = macro_agent.fetch_macro_data_tool(...)  # Direkt aufgerufen

Ziel (Production):
graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("data_agent", data_agent_node)
graph.add_node("macro_agent", macro_agent_node)
graph.add_conditional_edges(...)
app = graph.compile()
result = app.invoke({"messages": [user_message]})
```

**Deliverables:**
- [ ] `src/agents/graph.py` - LangGraph Definition
- [ ] `src/agents/nodes.py` - Node functions für jeden Agent
- [ ] `src/agents/state.py` - Erweiterte State Definition
- [ ] `src/agents/edges.py` - Conditional Edge Logic
- [ ] Async execution support
- [ ] Graceful error handling in graph

---

### Phase 6.3: Observability & Tracing
**Priority:** 🔴 CRITICAL
**Effort:** 4-5 hours

**Für Debugging UND für den Pitch essentiell!**

```
┌─────────────────────────────────────────────────────────────┐
│ TRACE: request_id=abc123                                    │
├─────────────────────────────────────────────────────────────┤
│ [00:00.000] USER: "Analysiere mein Portfolio"               │
│ [00:00.050] SUPERVISOR: Parsing intent...                   │
│ [00:00.200] SUPERVISOR: Detected tasks: [MACRO, REBALANCE]  │
│ [00:00.210] SUPERVISOR → MACRO_AGENT                        │
│ [00:00.500] MACRO_AGENT: Calling fetch_macro_data_tool      │
│             ├─ Input: {indicators: "VIX", days: 30}         │
│             ├─ Tokens: 150 in, 80 out                       │
│             └─ Duration: 1.2s                               │
│ [00:01.700] MACRO_AGENT → SUPERVISOR (result)               │
│ [00:01.750] SUPERVISOR → REBALANCE_AGENT                    │
│ ...                                                         │
├─────────────────────────────────────────────────────────────┤
│ SUMMARY:                                                    │
│   Total Duration: 3.5s                                      │
│   Total Tokens: 1,250 (≈ $0.02)                            │
│   Agents Used: [Supervisor, MacroAgent, RebalanceAgent]     │
│   Tools Called: 4                                           │
└─────────────────────────────────────────────────────────────┘
```

**Deliverables:**
- [ ] `src/observability/tracer.py` - Custom Tracer Class
- [ ] `src/observability/token_counter.py` - Token Usage Tracking
- [ ] `src/observability/cost_calculator.py` - Cost Estimation
- [ ] `src/observability/logger.py` - Structured JSON Logging
- [ ] Integration mit LangSmith (optional, aber empfohlen)
- [ ] Trace Export (JSON, für Audit)

---

### Phase 6.4: Token & Cost Management
**Priority:** 🟡 HIGH
**Effort:** 3-4 hours

Banker wollen wissen: "Was kostet das pro Request?"

**Deliverables:**
- [ ] Token counting per agent
- [ ] Token counting per tool call
- [ ] Cost estimation (GPT-4, Claude pricing)
- [ ] Budget limits (abort if > X tokens)
- [ ] Usage dashboard/report
- [ ] Database table für Usage History

```python
@dataclass
class UsageRecord:
    request_id: str
    timestamp: datetime
    agent_name: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
```

---

### Phase 6.5: Real Portfolio Management
**Priority:** 🟡 HIGH
**Effort:** 4-5 hours

Weg von Hardcoded Weights, hin zu echten User-Portfolios.

**Deliverables:**
- [ ] `portfolios` Table in Database
- [ ] `positions` Table (Ticker, Shares, Cost Basis)
- [ ] `transactions` Table (Buy/Sell History)
- [ ] DataManager methods: `get_portfolio()`, `update_position()`
- [ ] Portfolio Import (CSV, Manual Entry)
- [ ] Multi-Portfolio Support (für verschiedene User/Strategien)

```sql
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
    acquired_date DATE,
    updated_at TIMESTAMP
);
```

---

### Phase 6.6: RAG Pipeline (Fed Minutes)
**Priority:** 🟡 HIGH
**Effort:** 6-8 hours

Echte Dokumenten-Analyse statt simulierter Sentiment.

**Deliverables:**
- [ ] PDF Download & Text Extraction (fed_scraper.py erweitern)
- [ ] Text Chunking (500-1000 tokens per chunk)
- [ ] Embedding Generation (OpenAI oder Local)
- [ ] Vector Store (ChromaDB)
- [ ] Retrieval Function (`get_relevant_chunks()`)
- [ ] Fed Sentiment Extraction mit RAG
- [ ] Caching (nicht bei jedem Request neu embedden)

```python
class FedMinutesRAG:
    def __init__(self, chroma_client):
        self.collection = chroma_client.get_collection("fed_minutes")
    
    def query(self, question: str, n_results: int = 5) -> List[Chunk]:
        """Retrieve relevant chunks for a question."""
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )
        return results
    
    def analyze_sentiment(self, question: str) -> SentimentResult:
        """RAG-based sentiment analysis."""
        chunks = self.query(question)
        # LLM analyzes chunks...
```

---

### Phase 6.7: UI (Chainlit)
**Priority:** 🟢 MEDIUM
**Effort:** 4-6 hours

Browser-basierte UI mit echtem Agent Tracing.

**Deliverables:**
- [ ] `app.py` - Chainlit Application
- [ ] Agent Steps sichtbar (`cl.Step`)
- [ ] File Upload Support (Portfolio CSV)
- [ ] Chart Rendering (Plotly)
- [ ] Conversation History
- [ ] Export Function (PDF Report)

```python
import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    # Show thinking step
    async with cl.Step(name="RiskManager") as step:
        step.output = "Analyzing your request..."
        
        # Route to appropriate agent
        intent = await detect_intent(message.content)
        step.output = f"Detected intent: {intent}"
    
    # Execute agent
    async with cl.Step(name=intent.agent) as step:
        result = await execute_agent(intent)
        step.output = result.summary
    
    # Send response
    await cl.Message(content=result.response).send()
```

---

### Phase 6.8: Error Handling & Recovery
**Priority:** 🟢 MEDIUM
**Effort:** 3-4 hours

Graceful handling wenn etwas schiefgeht.

**Deliverables:**
- [ ] Custom Exception Classes
- [ ] Retry Logic (mit Exponential Backoff)
- [ ] Fallback Strategies (z.B. Cache nutzen wenn API down)
- [ ] User-friendly Error Messages
- [ ] Error Logging & Alerting
- [ ] Circuit Breaker Pattern

```python
class AgentError(Exception):
    """Base class for agent errors."""
    pass

class DataFetchError(AgentError):
    """Could not fetch data from provider."""
    pass

class RateLimitError(AgentError):
    """API rate limit exceeded."""
    retry_after: int

class OptimizationInfeasibleError(AgentError):
    """No feasible solution found."""
    constraints_violated: List[str]
```

---

### Phase 6.9: Data Maintenance & Scheduling
**Priority:** 🟢 MEDIUM
**Effort:** 3-4 hours

Automatische Datenaktualisierung.

**Deliverables:**
- [ ] Scheduled Jobs (APScheduler oder Celery)
- [ ] Daily Price Update Job
- [ ] Weekly Macro Data Update
- [ ] Monthly Fed Minutes Download
- [ ] Data Quality Checks
- [ ] Stale Data Alerts

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=18)  # 6 PM daily
def update_daily_prices():
    dm = get_data_manager()
    for ticker in get_active_tickers():
        dm.update_prices_for_asset(ticker, lookback_days=5)

@scheduler.scheduled_job('cron', day_of_week='mon', hour=7)
def update_macro_data():
    dm = get_data_manager()
    dm.update_vix(days=7)
    dm.update_treasury_yields(days=7)
```

---

### Phase 6.10: Testing & Documentation
**Priority:** 🟢 MEDIUM
**Effort:** 4-6 hours

**Deliverables:**
- [ ] Unit Tests für alle Tools
- [ ] Integration Tests für Agent Chains
- [ ] End-to-End Tests
- [ ] API Documentation (wenn REST API geplant)
- [ ] User Guide
- [ ] Developer Guide
- [ ] Architecture Diagram

---

### Phase 6.11: Human-in-the-Loop (Approval Workflow)
**Priority:** 🔴 CRITICAL (für Banken!)
**Effort:** 3-4 hours

**Keine Bank lässt eine KI Trades ausführen ohne menschliche Freigabe!**

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPROVAL WORKFLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User: "Rebalance mein Portfolio"                               │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ RebalanceAgent  │ Generiert Trade-Liste                      │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 🛑 INTERRUPT: Human Approval Required                   │    │
│  │                                                          │    │
│  │ Proposed Trades:                                         │    │
│  │   SELL 11 SPY @ €590 = €6,500                           │    │
│  │   BUY  52 TLT @ €88  = €4,600                           │    │
│  │                                                          │    │
│  │ Total Cost: €12.50 (0.012%)                             │    │
│  │                                                          │    │
│  │        [✓ APPROVE]    [✗ REJECT]    [✏️ MODIFY]         │    │
│  └─────────────────────────────────────────────────────────┘    │
│           │                                                      │
│           ▼ (nur wenn APPROVE)                                  │
│  ┌─────────────────┐                                            │
│  │ Execute Trades  │                                            │
│  └─────────────────┘                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Deliverables:**
- [ ] LangGraph `interrupt_before` für kritische Nodes
- [ ] Approval State in AgentState
- [ ] UI Components für Approval (Chainlit/Streamlit)
- [ ] Audit Log: Wer hat wann was approved
- [ ] Timeout Handling (Auto-Reject nach X Minuten)
- [ ] Modify Option (User kann Trade-Liste anpassen)

```python
# LangGraph mit Human-in-the-Loop
graph = StateGraph(AgentState)
graph.add_node("rebalance_proposal", generate_trades_node)
graph.add_node("rebalance_execution", execute_trades_node)

# CRITICAL: Interrupt before execution!
app = graph.compile(
    checkpointer=memory,
    interrupt_before=["rebalance_execution"]  # ← Killer-Feature!
)
```

---

### Phase 6.12: Output Parsers & Guardrails
**Priority:** 🔴 CRITICAL
**Effort:** 3-4 hours

**LLMs halluzinieren. Pydantic fängt es ab.**

```
Problem:
User: "Kaufe 100 Aktien von GPT-Coin"
LLM: {"ticker": "GPTCOIN", "shares": 100}  # ← Existiert nicht!

Lösung:
Pydantic Validator: "GPTCOIN is not a valid ticker" → Error
System: "Ich konnte diesen Ticker nicht finden. Meinten Sie..."
```

**Deliverables:**
- [ ] `src/agents/schemas.py` - Pydantic Models für alle Outputs
- [ ] `src/agents/validators.py` - Custom Validators
- [ ] Ticker Validation (gegen bekannte Liste oder API)
- [ ] Weight Validation (sum = 100%, keine negativen)
- [ ] Date Validation (nicht in der Zukunft)
- [ ] Graceful Error Messages für User

```python
from pydantic import BaseModel, validator, Field
from typing import List, Dict

class RouterDecision(BaseModel):
    """Validated output from the Smart Router."""
    intent: str = Field(..., description="Detected intent")
    agents_needed: List[str]
    confidence: float = Field(..., ge=0, le=1)
    
    @validator('agents_needed')
    def validate_agents(cls, v):
        valid_agents = {"DataAgent", "MacroAgent", "RebalanceAgent", "OptimizationAgent"}
        for agent in v:
            if agent not in valid_agents:
                raise ValueError(f"Unknown agent: {agent}")
        return v

class TradeProposal(BaseModel):
    """Validated trade proposal."""
    ticker: str
    action: str = Field(..., pattern="^(BUY|SELL)$")
    shares: float = Field(..., gt=0)
    
    @validator('ticker')
    def validate_ticker(cls, v):
        # Check against known tickers or API
        if not is_valid_ticker(v):
            raise ValueError(f"Invalid ticker: {v}")
        return v

class PortfolioWeights(BaseModel):
    """Validated portfolio weights."""
    weights: Dict[str, float]
    
    @validator('weights')
    def validate_weights(cls, v):
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        if any(w < 0 for w in v.values()):
            raise ValueError("Negative weights not allowed")
        return v
```

---

## 📅 Timeline Overview

```
Phase 6.1: Smart Router           ████░░░░░░  4-6h   Week 1
Phase 6.2: LangGraph             ██████░░░░  6-8h   Week 1-2
Phase 6.3: Observability         ████░░░░░░  4-5h   Week 1 ← START HERE
Phase 6.4: Token Management      ███░░░░░░░  3-4h   Week 2
Phase 6.5: Portfolio Management  ████░░░░░░  4-5h   Week 2-3
Phase 6.6: RAG Pipeline          ██████░░░░  6-8h   Week 3
Phase 6.7: Chainlit UI           ████░░░░░░  4-6h   Week 3-4
Phase 6.8: Error Handling        ███░░░░░░░  3-4h   Week 4
Phase 6.9: Data Scheduling       ███░░░░░░░  3-4h   Week 4
Phase 6.10: Testing & Docs       ████░░░░░░  4-6h   Week 4-5
Phase 6.11: Human-in-the-Loop    ███░░░░░░░  3-4h   Week 2 (mit 6.2)
Phase 6.12: Guardrails           ███░░░░░░░  3-4h   Week 1 (mit 6.1)

TOTAL: ~55-75 hours (5-6 weeks part-time)
```

---

## 🎯 Prioritized Implementation Order

### Sprint 1 (Must Have - Week 1-2)
1. **Phase 6.3: Observability** - Ohne Tracing kein Debugging!
2. **Phase 6.1: Smart Router** - Das Herzstück des Multi-Agent Systems
3. **Phase 6.2: LangGraph** - Echte Agent-Orchestrierung

### Sprint 2 (Should Have - Week 2-3)
4. **Phase 6.4: Token Management** - Kostencontrolle
5. **Phase 6.5: Portfolio Management** - Echte User-Daten
6. **Phase 6.6: RAG Pipeline** - Fed Minutes wirklich lesen

### Sprint 3 (Nice to Have - Week 3-5)
7. **Phase 6.7: Chainlit UI** - Schöne Oberfläche
8. **Phase 6.8: Error Handling** - Robustheit
9. **Phase 6.9: Data Scheduling** - Automatisierung
10. **Phase 6.10: Testing & Docs** - Professionalisierung

---

## 🏗️ Architecture After Phase 6

```
┌─────────────────────────────────────────────────────────────────┐
│                        CHAINLIT UI                               │
│                    (Browser Interface)                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY LAYER                          │
│         (Tracer, Token Counter, Cost Calculator, Logger)         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH ENGINE                            │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   START     │───►│  SUPERVISOR │───►│    END      │         │
│  └─────────────┘    │ (Router)    │    └─────────────┘         │
│                     └──────┬──────┘                             │
│                            │                                     │
│            ┌───────────────┼───────────────┐                    │
│            ▼               ▼               ▼                    │
│     ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│     │  DATA    │    │  MACRO   │    │ REBALANCE│               │
│     │  AGENT   │    │  AGENT   │    │  AGENT   │               │
│     └────┬─────┘    └────┬─────┘    └────┬─────┘               │
│          │               │               │                      │
└──────────┼───────────────┼───────────────┼──────────────────────┘
           │               │               │
           ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        TOOL LAYER                                │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ DataMgr  │  │ RAG      │  │ Rebalance│  │ Optimizer│        │
│  │ Tools    │  │ Pipeline │  │ Tools    │  │ Tools    │        │
│  └────┬─────┘  └────┬─────┘  └──────────┘  └──────────┘        │
│       │             │                                           │
└───────┼─────────────┼───────────────────────────────────────────┘
        │             │
        ▼             ▼
┌───────────────┐  ┌───────────────┐
│   SQLite DB   │  │   ChromaDB    │
│ (Prices,Macro │  │ (Embeddings)  │
│  Portfolios)  │  │               │
└───────────────┘  └───────────────┘
```

---

## ✅ Definition of Done

Das Projekt ist "Production-Ready" wenn:

- [ ] User kann natürliche Sprache verwenden (keine Keywords nötig)
- [ ] Agents werden intelligent geroutet (LLM-basiert)
- [ ] Jeder Request ist vollständig nachvollziehbar (Tracing)
- [ ] Token-Verbrauch wird pro Request geloggt
- [ ] Kosten werden geschätzt und angezeigt
- [ ] User kann eigenes Portfolio eingeben/laden
- [ ] Fed Minutes werden wirklich gelesen (RAG)
- [ ] System recovered gracefully von Fehlern
- [ ] Daten werden automatisch aktualisiert
- [ ] UI zeigt Agent-Kommunikation live

---

## 🚀 Nächster Schritt

**Empfehlung:** Starte mit **Phase 6.3 (Observability)**.

Warum? Ohne Tracing kannst du nicht debuggen. Wenn du dann den Smart Router (6.1) und LangGraph (6.2) baust, siehst du sofort was passiert.

```bash
# Beginne mit:
mkdir -p src/observability
touch src/observability/__init__.py
touch src/observability/tracer.py
touch src/observability/token_counter.py
```

Soll ich mit Phase 6.3 (Observability) anfangen?