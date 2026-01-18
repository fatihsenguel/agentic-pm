# AGENTIC FINANCE PLATFORM
## Multi-Agent System Roadmap v4.0

---

# 📋 EXECUTIVE SUMMARY

**Ziel:** Erweiterung der bestehenden Agentic Finance Platform zu einem Multi-Agent System, das komplexe Finanzanalysen durch spezialisierte, kollaborierende Agents löst.

**Timeline:** 4-5 Wochen

**Ziel-Prompts:**
1. **Prompt #4: Peer Comparison** - Automatische Konkurrenzanalyse mit Bewertung
2. **Prompt #2: Earnings Call Analyse** - RAG-basierte Dokumentenanalyse mit Price Correlation

**Outcome:** Interview-ready MVP für Großbanken und Asset Manager

---

# 🧭 PROJEKTPHILOSOPHIE

## Unsere Architektur-Prinzipien

Diese Prinzipien haben uns durch Phase 1-3 geführt und bleiben für Phase 4 gültig:

### 1. Separation of Concerns (SoC)
```
PRINZIP: Jede Komponente hat EINE klare Verantwortung.

PHASE 1-3 BEISPIEL:
├── DataManager → Daten-Operationen
├── MetricsCalculator → Berechnungen
├── YFinanceProvider → API-Kommunikation
└── Tools → Agent-Interface

PHASE 4 ANWENDUNG:
├── Supervisor Agent → Planung & Delegation
├── Data Agent → Datenbeschaffung
├── Analyst Agent → Interpretation & Empfehlung
└── RAG Agent → Dokumentenanalyse
```

### 2. Hot Potato Principle
```
PRINZIP: LLMs bekommen NIEMALS Rohdaten. Jede Schicht aggregiert.

PHASE 1-3 BEISPIEL:
├── 10.000 Preispunkte → MetricsCalculator → {return: 13.6%, vol: 22%}
└── Agent sieht nur Summary, nie die 10.000 Rows

PHASE 4 ANWENDUNG:
├── RAG Agent extrahiert 3 Key Points, nicht 60 Seiten Transkript
├── Data Agent liefert Metriken, nicht Rohdaten
└── Supervisor bekommt strukturierte Agent-Responses
```

### 3. DRY (Don't Repeat Yourself)
```
PRINZIP: Logik existiert genau EINMAL.

PHASE 1-3 BEISPIEL:
├── UpdateResult DTO → einheitliches Response-Format für ALLE Tools
└── DataManagerSingleton → eine Instanz, überall genutzt

PHASE 4 ANWENDUNG:
├── BaseAgent Klasse → gemeinsame Logik für alle Agents
├── AgentResponse DTO → einheitliches Format für Agent-Kommunikation
└── Shared Tools → Agents nutzen gleiche Tool-Bibliothek
```

### 4. Interface Abstraction (Provider Pattern)
```
PRINZIP: Externe Abhängigkeiten hinter Interfaces verstecken.

PHASE 1-3 BEISPIEL:
├── DataProviderInterface → YFinanceProvider implementiert
└── Morgen: BloombergProvider implementiert gleiche Interface

PHASE 4 ANWENDUNG:
├── BaseAgent Interface → alle Agents implementieren gleiche Methoden
├── EmbeddingProvider Interface → OpenAI, Cohere, lokale Modelle austauschbar
└── VectorStoreInterface → ChromaDB, Pinecone, Weaviate austauschbar
```

### 5. Idempotenz & Robustheit
```
PRINZIP: Jede Operation ist sicher wiederholbar.

PHASE 1-3 BEISPIEL:
├── Upserts statt Inserts → kein Duplicate Data
├── safe_int/safe_float → kein Crash bei NaN
└── Session Isolation → kein Locking

PHASE 4 ANWENDUNG:
├── Agent Retry Logic → Fehler führen zu Retry, nicht Crash
├── Idempotente Embeddings → gleiches Dokument = gleicher Vector
└── Supervisor Recovery → wenn ein Agent scheitert, alternatives Vorgehen
```

### 6. Agent-Ready Responses
```
PRINZIP: Responses sind selbstbeschreibend und maschinenlesbar.

PHASE 1-3 BEISPIEL:
UpdateResult(
    success=True,
    operation="update_prices",
    affected_count=252,
    entities=["AAPL"],
    metadata={"provider": "yfinance"}
)

PHASE 4 ANWENDUNG:
AgentResponse(
    agent_name="data_agent",
    task="fetch_peer_data",
    success=True,
    result={...},
    confidence=0.95,
    reasoning="Found 5 peers in same sector..."
)
```

### 7. Testability First
```
PRINZIP: Jede Komponente ist isoliert testbar.

PHASE 1-3 BEISPIEL:
├── MockQuotaManager für Tests ohne DB
├── Unit Tests für safe_int/safe_float
└── Integration Tests für Tools

PHASE 4 ANWENDUNG:
├── Mock Agents für Supervisor Tests
├── Isolated Agent Tests ohne andere Agents
└── End-to-End Tests mit vollständigem System
```

---

# 🎯 ZIEL-PROMPTS

## Prompt #4: Intelligent Peer Comparison

### User Input:
```
"Vergleiche SAP mit seinen direkten Konkurrenten:
1. Identifiziere die 4 relevantesten Peers (nicht ich - DU entscheidest)
2. Vergleiche: Revenue Growth, Margin, P/E, EV/EBITDA
3. Wo ist SAP über-/unterbewertet relativ zu Peers?
4. Was sind potenzielle Gründe für die Bewertungsunterschiede?"
```

### Erwarteter Output:
```
📊 PEER COMPARISON: SAP SE

🔍 Identifizierte Peers (nach Sektor: Enterprise Software, Market Cap >$50B):
   • Oracle (ORCL) - $320B
   • Salesforce (CRM) - $250B
   • ServiceNow (NOW) - $150B
   • Workday (WDAY) - $60B

📈 Vergleichstabelle:
┌──────────┬───────────┬─────────┬────────┬────────────┐
│ Ticker   │ Rev Growth│ Margin  │ P/E    │ EV/Revenue │
├──────────┼───────────┼─────────┼────────┼────────────┤
│ SAP      │ 8.2%      │ 22.1%   │ 25.3   │ 5.2x       │
│ ORCL     │ 6.1%      │ 28.5%   │ 22.1   │ 6.8x       │
│ CRM      │ 11.3%     │ 18.2%   │ 42.5   │ 7.1x       │
│ NOW      │ 24.1%     │ 21.5%   │ 85.2   │ 15.2x      │
│ WDAY     │ 17.8%     │ 15.3%   │ 55.3   │ 9.8x       │
└──────────┴───────────┴─────────┴────────┴────────────┘

💡 Bewertungsanalyse:
SAP erscheint UNTERBEWERTET relativ zu Peers:
- Niedrigstes EV/Revenue (5.2x vs. Durchschnitt 8.8x)
- Zweitniedrigstes P/E trotz stabilen Wachstums
- Höchste Margin unter den "klassischen" Anbietern

🤔 Mögliche Gründe für Discount:
1. Langsameres Wachstum (8.2% vs. 14.8% Peer-Durchschnitt)
2. Europäische Aktie → geringere US-Investorenbasis
3. Komplexe Cloud-Transition noch nicht abgeschlossen

📅 Datenstand: 2026-01-17 | Berechnet aus 251 Handelstagen
```

### Warum wertvoll:
- Agent trifft EIGENE Entscheidungen (Peer-Auswahl)
- Kombiniert Daten + Interpretation
- Audit Trail (Datenstand, Berechnungsbasis)

---

## Prompt #2: Earnings Call Analysis with Price Correlation

### User Input:
```
"Analysiere den letzten Earnings Call von NVIDIA:
1. Was waren die 3 wichtigsten Aussagen des CEO zu AI-Umsätzen?
2. Wie hat sich der Guidance-Ton vs. letztes Quartal verändert?
3. Welche Fragen der Analysten wurden ausweichend beantwortet?
4. Vergleiche die Aussagen mit der tatsächlichen Aktienperformance der letzten 5 Tage"
```

### Erwarteter Output:
```
📄 EARNINGS CALL ANALYSE: NVIDIA Q4 2024

📊 Dokument: nvidia_q4_2024_transcript.pdf (47 Seiten, hochgeladen)

🎯 Top 3 CEO-Aussagen zu AI-Umsätzen:

1. "Data center revenue reached $22.6 billion, up 93% year-over-year, 
    driven entirely by AI infrastructure demand."
   → Seite 4, CEO Jensen Huang

2. "We're seeing demand that far exceeds our supply capabilities. 
    Every major cloud provider has expanded their orders."
   → Seite 7, CEO Jensen Huang

3. "Sovereign AI initiatives from governments represent a new $10B+ 
    addressable market we didn't have 18 months ago."
   → Seite 12, CEO Jensen Huang

📈 Guidance-Ton Vergleich:

| Aspekt          | Q3 2024           | Q4 2024           | Veränderung    |
|-----------------|-------------------|-------------------|----------------|
| Revenue Outlook | "Strong demand"   | "Unprecedented"   | ↑ Bullisher    |
| Supply          | "Constrained"     | "Severely limited"| ↑ Mehr Urgency |
| Competition     | Nicht erwähnt     | "No credible alt" | ↑ Konfidenter  |

⚠️ Ausweichende Antworten:

1. Frage (Morgan Stanley): "Can you quantify the Blackwell ramp timeline?"
   → Antwort war vage: "Ramping nicely" ohne konkrete Zahlen
   → INTERPRETATION: Mögliche Produktionsprobleme?

2. Frage (Goldman): "What's the China revenue exposure post-restrictions?"
   → CEO pivotierte zu "global demand" ohne China-Zahlen
   → INTERPRETATION: China-Rückgang wird nicht quantifiziert

📉 Price Correlation:

┌─────────────┬──────────┬──────────┐
│ Datum       │ Close    │ Change   │
├─────────────┼──────────┼──────────┤
│ 2026-01-13  │ $142.50  │ —        │  ← Earnings After-Hours
│ 2026-01-14  │ $156.80  │ +10.0%   │  ← Post-Earnings Rally
│ 2026-01-15  │ $154.20  │ -1.7%    │
│ 2026-01-16  │ $158.90  │ +3.0%    │
│ 2026-01-17  │ $161.20  │ +1.4%    │
└─────────────┴──────────┴──────────┘

5-Tage Performance: +13.1%

💡 Synthese:
Der stark positive Earnings Call (bullishe Guidance, AI-Dominanz-Narrativ) 
korreliert mit der +13% Rallye. Die ausweichenden Antworten zu China und 
Blackwell wurden vom Markt offenbar ignoriert - Fokus lag auf der 
Headline-Nachfrage. 

⚠️ Risiko: Die nicht-quantifizierten China-Auswirkungen könnten in 
zukünftigen Quartalen überraschen.

📅 Analyse erstellt: 2026-01-17 | Dokument-Chunks: 127 | Embedding-Model: text-embedding-3-small
```

### Warum wertvoll:
- Ersetzt 2-3 Stunden Analyst-Arbeit
- Verbindet unstrukturierte Daten (PDF) mit strukturierten (Preise)
- Identifiziert Risiken die im Mainstream übersehen werden

---

# 🏗️ SYSTEM-ARCHITEKTUR

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AGENTIC FINANCE PLATFORM v4                           │
│                              Multi-Agent System                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│                         ┌─────────────────────────┐                             │
│                         │      USER INTERFACE     │                             │
│                         │    (CLI / Future: API)  │                             │
│                         └───────────┬─────────────┘                             │
│                                     │                                           │
│                                     ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                        SUPERVISOR AGENT                                   │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Responsibilities:                                                   │  │  │
│  │  │ • Parse user intent                                                 │  │  │
│  │  │ • Create execution plan                                             │  │  │
│  │  │ • Delegate to specialized agents                                    │  │  │
│  │  │ • Handle parallel vs. sequential execution                          │  │  │
│  │  │ • Aggregate results                                                 │  │  │
│  │  │ • Synthesize final response                                         │  │  │
│  │  │ • Error recovery & retry logic                                      │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────┬───────────────────────────────────────┘  │
│                                     │                                           │
│              ┌──────────────────────┼──────────────────────┐                   │
│              │                      │                      │                   │
│              ▼                      ▼                      ▼                   │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐          │
│  │    DATA AGENT     │  │  ANALYST AGENT    │  │    RAG AGENT      │          │
│  │                   │  │                   │  │                   │          │
│  │ Skills:           │  │ Skills:           │  │ Skills:           │          │
│  │ • Fetch prices    │  │ • Calculate       │  │ • Load documents  │          │
│  │ • Fetch fundament.│  │   metrics         │  │ • Chunk & embed   │          │
│  │ • Find peers      │  │ • Compare stocks  │  │ • Semantic search │          │
│  │ • Validate data   │  │ • Interpret       │  │ • Extract answers │          │
│  │ • Check freshness │  │   results         │  │ • Summarize       │          │
│  │                   │  │ • Identify risks  │  │                   │          │
│  │ Tools:            │  │ • Recommend       │  │ Tools:            │          │
│  │ • fetch_*         │  │                   │  │ • load_document   │          │
│  │ • get_*           │  │ Tools:            │  │ • query_documents │          │
│  │ • query_*         │  │ • calculate_*     │  │ • summarize_doc   │          │
│  │ • find_peers      │  │ • compare_*       │  │                   │          │
│  └─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘          │
│            │                      │                      │                     │
│            ▼                      ▼                      ▼                     │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐          │
│  │   DATA LAYER      │  │  ANALYTICS LAYER  │  │    RAG LAYER      │          │
│  │                   │  │                   │  │                   │          │
│  │ • DataManager     │  │ • MetricsCalc     │  │ • DocumentLoader  │          │
│  │ • YFinanceProvider│  │ • PeerFinder      │  │ • EmbeddingService│          │
│  │ • Database (SQL)  │  │ • ValuationCalc   │  │ • VectorStore     │          │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘          │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  CROSS-CUTTING CONCERNS                                                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐  │
│  │ AgentResponse   │ │ QuotaManager    │ │ AuditLogger     │ │ ErrorHandler │  │
│  │ DTO             │ │ (API Limits)    │ │ (Traceability)  │ │ (Recovery)   │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Agent Communication Protocol

```
┌─────────────────────────────────────────────────────────────────┐
│                  AGENT RESPONSE SCHEMA                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  @dataclass                                                     │
│  class AgentResponse:                                           │
│      agent_name: str          # "data_agent"                    │
│      task_id: str             # UUID for tracing                │
│      task_description: str    # "Fetch peer data for SAP"       │
│      success: bool                                              │
│      result: Dict[str, Any]   # The actual payload              │
│      confidence: float        # 0.0 - 1.0                       │
│      reasoning: str           # Why this result                 │
│      execution_time_ms: int                                     │
│      tokens_used: int                                           │
│      error_message: Optional[str]                               │
│      retry_possible: bool                                       │
│      metadata: Dict[str, Any] # Audit trail info                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Execution Flow: Prompt #4 (Peer Comparison)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER: "Vergleiche SAP mit Konkurrenten"                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SUPERVISOR: Analysiert Intent                                              │
│  → Task Type: PEER_COMPARISON                                               │
│  → Primary Entity: SAP                                                      │
│  → Required Agents: [DATA_AGENT, ANALYST_AGENT]                             │
│  → Execution: SEQUENTIAL (Data first, then Analysis)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               │
┌───────────────────────────────────┐               │
│  STEP 1: DATA AGENT               │               │
│                                   │               │
│  Task 1.1: get_asset_info("SAP")  │               │
│  → Sector: Technology             │               │
│  → Industry: Enterprise Software  │               │
│  → Market Cap: $250B              │               │
│                                   │               │
│  Task 1.2: find_peers("SAP")      │               │
│  → Criteria: Same sector,         │               │
│    Market Cap >$50B               │               │
│  → Result: [ORCL, CRM, NOW, WDAY] │               │
│                                   │               │
│  Task 1.3: fetch_fundamentals     │               │
│    for each peer                  │               │
│  → Revenue, Margins, P/E, etc.    │               │
│                                   │               │
│  Returns: AgentResponse with      │               │
│  structured peer data             │               │
└───────────────────┬───────────────┘               │
                    │                               │
                    ▼                               │
┌───────────────────────────────────┐               │
│  STEP 2: ANALYST AGENT            │◄──────────────┘
│                                   │
│  Input: Peer data from Step 1     │
│                                   │
│  Task 2.1: Calculate metrics      │
│  → Revenue Growth, Margins        │
│  → Valuation multiples            │
│                                   │
│  Task 2.2: Compare & Rank         │
│  → Relative valuation             │
│  → Identify outliers              │
│                                   │
│  Task 2.3: Interpret              │
│  → Why is SAP valued lower?       │
│  → What are the risks?            │
│                                   │
│  Returns: AgentResponse with      │
│  analysis and recommendations     │
└───────────────────┬───────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SUPERVISOR: Synthesizes Final Response                                     │
│  → Combines Data Agent facts + Analyst Agent interpretation                 │
│  → Formats for user                                                         │
│  → Adds audit trail (data dates, calculation basis)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER receives structured analysis                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Execution Flow: Prompt #2 (Earnings Call)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER: "Analysiere NVIDIA Earnings Call und vergleiche mit Aktienperformance"│
│  + Uploaded: nvidia_q4_2024.pdf                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SUPERVISOR: Analysiert Intent                                              │
│  → Task Type: DOCUMENT_ANALYSIS + PRICE_CORRELATION                         │
│  → Primary Entity: NVDA                                                     │
│  → Required Agents: [RAG_AGENT, DATA_AGENT, ANALYST_AGENT]                  │
│  → Execution: PARALLEL (RAG + Data), then SEQUENTIAL (Analyst)              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
         ┌──────────┴──────────┐         ┌─────────┴─────────┐
         ▼                     │         ▼                   │
┌─────────────────────┐        │  ┌─────────────────────┐    │
│  RAG AGENT          │        │  │  DATA AGENT         │    │
│  (PARALLEL)         │        │  │  (PARALLEL)         │    │
│                     │        │  │                     │    │
│  Task: Load & embed │        │  │  Task: Get NVDA     │    │
│  nvidia_q4_2024.pdf │        │  │  prices last 5 days │    │
│                     │        │  │                     │    │
│  Queries:           │        │  │  Returns:           │    │
│  • "CEO AI revenue" │        │  │  Price series with  │    │
│  • "Guidance tone"  │        │  │  daily changes      │    │
│  • "Evasive answers"│        │  │                     │    │
│                     │        │  │                     │    │
│  Returns:           │        │  │                     │    │
│  Extracted points   │        │  │                     │    │
│  with citations     │        │  │                     │    │
└──────────┬──────────┘        │  └──────────┬──────────┘    │
           │                   │             │               │
           └───────────────────┴──────┬──────┴───────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │  ANALYST AGENT                  │
                    │  (SEQUENTIAL - needs both)      │
                    │                                 │
                    │  Input:                         │
                    │  • RAG extracted points         │
                    │  • Price data                   │
                    │                                 │
                    │  Tasks:                         │
                    │  • Correlate tone with prices   │
                    │  • Identify risks from evasions │
                    │  • Generate synthesis           │
                    │                                 │
                    │  Returns:                       │
                    │  Integrated analysis            │
                    └───────────────┬─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SUPERVISOR: Synthesizes Final Response                                     │
│  → Structures: Key Points → Tone Comparison → Price Impact → Risks          │
│  → Adds audit trail (doc chunks used, embedding model, data dates)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 📅 IMPLEMENTATION ROADMAP

## Phase 4.1: Multi-Agent Foundation (Woche 1)

### Ziele:
- [ ] Multi-Agent Grundstruktur mit LangGraph
- [ ] Supervisor Agent mit Routing-Logik
- [ ] Agent Communication Protocol (AgentResponse DTO)
- [ ] Refactor bestehenden Code zu Data Agent

### Deliverables:

```
src/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # BaseAgent Klasse
│   ├── supervisor_agent.py     # Supervisor mit Routing
│   ├── data_agent.py           # Refactored aus bestehendem Code
│   └── protocols.py            # AgentResponse, AgentTask DTOs
├── orchestration/
│   ├── __init__.py
│   ├── graph.py                # LangGraph State Machine
│   ├── router.py               # Intent Detection & Routing
│   └── executor.py             # Parallel/Sequential Execution
```

### Technische Details:

**BaseAgent (Abstract Class):**
```python
class BaseAgent(ABC):
    """Base class for all specialized agents."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique agent identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """What this agent does (for Supervisor)."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """List of task types this agent can handle."""
        pass
    
    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute a task and return structured response."""
        pass
    
    def _create_response(self, ...) -> AgentResponse:
        """Helper to create standardized responses."""
        pass
```

**Supervisor Routing Logic:**
```python
TASK_ROUTING = {
    "fetch_data": ["data_agent"],
    "calculate_metrics": ["analyst_agent"],
    "compare_stocks": ["data_agent", "analyst_agent"],  # Sequential
    "analyze_document": ["rag_agent"],
    "earnings_analysis": ["rag_agent", "data_agent", "analyst_agent"],  # Parallel + Sequential
}
```

### Tests:
- [ ] BaseAgent interface compliance tests
- [ ] Supervisor routing logic tests
- [ ] AgentResponse serialization tests
- [ ] Mock agent communication tests

---

## Phase 4.2: Analyst Agent + Prompt #4 (Woche 2)

### Ziele:
- [ ] Analyst Agent implementieren
- [ ] Peer Finder Logik
- [ ] Valuation Comparison
- [ ] End-to-End: Prompt #4 funktioniert

### Deliverables:

```
src/
├── agents/
│   └── analyst_agent.py        # NEU
├── portfolio_tool/
│   ├── analytics/
│   │   ├── metrics.py          # Existing
│   │   ├── peer_finder.py      # NEU
│   │   └── valuation.py        # NEU
│   └── tools/
│       └── analyst_tools.py    # NEU: compare_with_peers, analyze_valuation
```

### Peer Finder Logic:

```python
class PeerFinder:
    """Identifies comparable companies based on multiple criteria."""
    
    def find_peers(
        self,
        ticker: str,
        criteria: PeerCriteria = None
    ) -> List[PeerMatch]:
        """
        Find peers for a given stock.
        
        Default criteria:
        - Same sector
        - Market cap within 0.2x - 5x range
        - Same primary geography (optional)
        
        Returns ranked list of peers with match scores.
        """
        pass
    
    def _get_sector_peers(self, sector: str) -> List[str]:
        """Get all stocks in a sector from our database."""
        pass
    
    def _filter_by_market_cap(
        self, 
        candidates: List[str], 
        target_mcap: int,
        min_ratio: float = 0.2,
        max_ratio: float = 5.0
    ) -> List[str]:
        """Filter candidates by market cap similarity."""
        pass
    
    def _calculate_match_score(
        self,
        target: AssetInfo,
        candidate: AssetInfo
    ) -> float:
        """Calculate similarity score (0-1) between two companies."""
        pass
```

### Valuation Calculator:

```python
class ValuationCalculator:
    """Calculates and compares valuation metrics."""
    
    def calculate_multiples(self, ticker: str) -> ValuationMetrics:
        """
        Calculate key valuation multiples:
        - P/E Ratio
        - EV/Revenue
        - EV/EBITDA
        - Price/Book
        - Price/Sales
        """
        pass
    
    def compare_valuations(
        self,
        target: str,
        peers: List[str]
    ) -> ValuationComparison:
        """
        Compare target valuation vs peers.
        
        Returns:
        - Relative rankings
        - Premium/discount calculations
        - Statistical analysis (mean, median, std)
        """
        pass
    
    def interpret_valuation(
        self,
        comparison: ValuationComparison
    ) -> ValuationInsight:
        """
        Generate insights about valuation.
        
        - Is target over/undervalued?
        - What might explain the difference?
        - Confidence level of assessment
        """
        pass
```

### Tests:
- [ ] PeerFinder unit tests (sector matching, market cap filtering)
- [ ] ValuationCalculator unit tests
- [ ] Analyst Agent integration tests
- [ ] End-to-End: Prompt #4 with mocked data
- [ ] End-to-End: Prompt #4 with real data

---

## Phase 4.3: RAG Agent + Prompt #2 (Woche 3)

### Ziele:
- [ ] RAG Pipeline (Document Loading, Chunking, Embedding)
- [ ] Vector Store Integration (ChromaDB)
- [ ] RAG Agent implementieren
- [ ] End-to-End: Prompt #2 funktioniert

### Deliverables:

```
src/
├── agents/
│   └── rag_agent.py            # NEU
├── portfolio_tool/
│   └── rag/                    # NEU - Komplettes Modul
│       ├── __init__.py
│       ├── document_loader.py  # PDF, TXT, DOCX support
│       ├── chunker.py          # Intelligent text splitting
│       ├── embeddings.py       # Embedding provider interface
│       ├── vector_store.py     # ChromaDB wrapper
│       └── retriever.py        # Semantic search + reranking
```

### Document Loader:

```python
class DocumentLoader:
    """Load and preprocess documents for RAG."""
    
    SUPPORTED_FORMATS = [".pdf", ".txt", ".docx", ".md"]
    
    def load(self, file_path: Path) -> Document:
        """Load document and extract text."""
        pass
    
    def _load_pdf(self, file_path: Path) -> str:
        """Extract text from PDF using pypdf or pdfplumber."""
        pass
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        pass
```

### Chunking Strategy:

```python
class SemanticChunker:
    """Chunk documents intelligently for financial content."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        respect_sections: bool = True  # Don't split mid-section
    ):
        pass
    
    def chunk(self, document: Document) -> List[Chunk]:
        """
        Split document into chunks.
        
        Special handling for:
        - Financial tables (keep together)
        - Q&A sections (question + answer together)
        - Headers/sections (don't orphan headers)
        """
        pass
```

### Vector Store Interface:

```python
class VectorStoreInterface(ABC):
    """Abstract interface for vector stores."""
    
    @abstractmethod
    def add_documents(self, chunks: List[Chunk], metadata: Dict) -> None:
        pass
    
    @abstractmethod
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter: Dict = None
    ) -> List[SearchResult]:
        pass
    
    @abstractmethod
    def delete(self, document_id: str) -> None:
        pass


class ChromaDBStore(VectorStoreInterface):
    """ChromaDB implementation of vector store."""
    
    def __init__(self, persist_directory: str = "./data/chroma"):
        pass
```

### RAG Agent Tools:

```python
@tool
def load_document(file_path: str) -> Dict:
    """Load and index a document for analysis."""
    pass

@tool  
def query_document(
    question: str,
    document_id: str = None,  # None = search all documents
    top_k: int = 5
) -> Dict:
    """Ask a question about loaded documents."""
    pass

@tool
def summarize_document(
    document_id: str,
    focus_area: str = None  # e.g., "AI revenue", "guidance"
) -> Dict:
    """Generate a summary of a document, optionally focused on a topic."""
    pass
```

### Tests:
- [ ] DocumentLoader tests (PDF, TXT)
- [ ] Chunker tests (edge cases, financial content)
- [ ] VectorStore tests (add, search, delete)
- [ ] RAG Agent integration tests
- [ ] End-to-End: Prompt #2 with sample earnings call

---

## Phase 4.4: Integration & Polish (Woche 4)

### Ziele:
- [ ] Beide Prompts End-to-End funktionierend
- [ ] Error Handling & Recovery
- [ ] Performance Optimization
- [ ] Documentation & Demo

### Deliverables:

```
├── README.md                   # Vollständige Dokumentation
├── docs/
│   ├── ARCHITECTURE.md         # Detaillierte Architektur-Erklärung
│   ├── AGENTS.md               # Agent-spezifische Dokumentation
│   └── SETUP.md                # Installation & Konfiguration
├── examples/
│   ├── peer_comparison_demo.py # Standalone Demo für Prompt #4
│   ├── earnings_analysis_demo.py # Standalone Demo für Prompt #2
│   └── sample_data/
│       └── nvidia_q4_2024.pdf  # Sample Earnings Transcript
├── demo/
│   └── demo_recording.gif      # Animated Demo
```

### Performance Optimizations:
- [ ] Parallel Agent Execution wo möglich
- [ ] Caching für wiederkehrende Queries (optional)
- [ ] Lazy Loading für RAG (nur laden wenn gebraucht)

### Error Handling:
- [ ] Agent Timeout Handling
- [ ] Retry Logic für fehlgeschlagene Agent Calls
- [ ] Graceful Degradation (wenn ein Agent scheitert, partial results)
- [ ] User-friendly Error Messages

---

# ⚠️ RISIKEN & TESTING-FOKUS

## Kritische Problembereiche

### 1. Agent Coordination Failures

**Problem:** Supervisor wartet auf Agent der nie antwortet
```
Supervisor → Data Agent: "Fetch peer data"
Data Agent: *hängt bei API Call*
Supervisor: *wartet ewig*
```

**Lösung:**
```python
async def execute_with_timeout(
    agent: BaseAgent, 
    task: AgentTask,
    timeout_seconds: int = 30
) -> AgentResponse:
    try:
        return await asyncio.wait_for(
            agent.execute(task),
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        return AgentResponse(
            success=False,
            error_message=f"Agent {agent.name} timed out after {timeout_seconds}s",
            retry_possible=True
        )
```

**Tests:**
- [ ] Agent timeout handling
- [ ] Supervisor retry logic
- [ ] Partial results wenn ein Agent scheitert

---

### 2. Context Window Explosion

**Problem:** Zu viele Agent-Responses füllen Context Window
```
Supervisor Context:
- System Prompt: 1000 tokens
- Data Agent Response: 2000 tokens
- Analyst Agent Response: 1500 tokens
- RAG Agent Response: 3000 tokens
- Previous conversation: 2000 tokens
= 9500 tokens input BEVOR Supervisor antwortet
```

**Lösung:**
```python
class ResponseCompressor:
    """Compress agent responses to essential information."""
    
    MAX_TOKENS_PER_RESPONSE = 500
    
    def compress(self, response: AgentResponse) -> AgentResponse:
        """Keep only essential fields, summarize large results."""
        if self._estimate_tokens(response.result) > self.MAX_TOKENS_PER_RESPONSE:
            response.result = self._summarize(response.result)
            response.metadata["compressed"] = True
        return response
```

**Tests:**
- [ ] Token counting accuracy
- [ ] Compression doesn't lose critical info
- [ ] End-to-end with large responses

---

### 3. RAG Quality Issues

**Problem:** Falsche oder irrelevante Chunks werden retrieved
```
Query: "What did the CEO say about AI revenue?"
Retrieved: Chunk about "AI" in legal disclaimers section
Result: Useless answer
```

**Lösung:**
```python
class HybridRetriever:
    """Combine semantic + keyword search with reranking."""
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Chunk]:
        # 1. Semantic search
        semantic_results = self.vector_store.search(query, top_k=top_k*2)
        
        # 2. Keyword search
        keyword_results = self._keyword_search(query, top_k=top_k*2)
        
        # 3. Combine and dedupe
        combined = self._merge_results(semantic_results, keyword_results)
        
        # 4. Rerank with cross-encoder
        reranked = self.reranker.rerank(query, combined, top_k=top_k)
        
        return reranked
```

**Tests:**
- [ ] Retrieval relevance tests (golden dataset)
- [ ] Edge cases: Short queries, ambiguous queries
- [ ] Financial jargon handling

---

### 4. Peer Finding Accuracy

**Problem:** Falsche Peers werden identifiziert
```
Query: "Find peers for SAP"
Bad Result: [AAPL, MSFT, GOOGL]  # Wrong - these are not direct competitors
Good Result: [ORCL, CRM, NOW, WDAY]  # Correct - enterprise software
```

**Lösung:**
```python
class PeerFinder:
    # Multi-criteria matching
    PEER_CRITERIA = {
        "sector_match": 0.4,       # Must be same sector
        "industry_match": 0.3,     # Same industry = bonus
        "market_cap_ratio": 0.2,   # Similar size
        "geography": 0.1           # Same region = bonus
    }
    
    # Hardcoded overrides for known peer groups
    PEER_OVERRIDES = {
        "SAP": ["ORCL", "CRM", "NOW", "WDAY", "INTU"],
        "AAPL": ["MSFT", "GOOGL", "SAMSUNG"],  # Different logic for hardware
    }
```

**Tests:**
- [ ] Golden dataset of known peer groups
- [ ] Edge cases: Conglomerates, unique businesses
- [ ] Market cap boundary tests

---

### 5. Parallel Execution Race Conditions

**Problem:** Agents accessing shared resources simultaneously
```
Data Agent: *fetches NVDA prices*
RAG Agent: *loads document, needs NVDA ticker for metadata*
Race condition: RAG Agent might not find NVDA if Data Agent hasn't inserted yet
```

**Lösung:**
```python
class ExecutionCoordinator:
    """Manage dependencies between parallel agent tasks."""
    
    def plan_execution(self, tasks: List[AgentTask]) -> ExecutionPlan:
        """
        Analyze task dependencies and create execution plan.
        
        Returns:
        - Which tasks can run in parallel
        - Which must be sequential
        - Dependency graph
        """
        pass
```

**Tests:**
- [ ] Parallel execution with no dependencies
- [ ] Sequential execution with dependencies
- [ ] Mixed parallel/sequential

---

### 6. LLM Inconsistency

**Problem:** Gleicher Prompt, verschiedene Agent-Entscheidungen
```
Run 1: Supervisor → [Data Agent, Analyst Agent]
Run 2: Supervisor → [Data Agent, RAG Agent, Analyst Agent]  # Different plan!
```

**Lösung:**
```python
# More deterministic prompts with explicit criteria
SUPERVISOR_PROMPT = """
You are a Supervisor agent. Given a user query, create an execution plan.

ROUTING RULES (follow exactly):
1. If query mentions "document", "earnings call", "transcript" → include RAG_AGENT
2. If query mentions "compare", "peers", "competitors" → include DATA_AGENT + ANALYST_AGENT
3. If query asks for "price", "return", "volatility" → include DATA_AGENT
...

DO NOT deviate from these rules.
"""

# Temperature = 0 for deterministic routing
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

**Tests:**
- [ ] Same prompt → same routing (10 runs)
- [ ] Edge case prompts
- [ ] Ambiguous prompts → reasonable default

---

## Test Matrix

| Test Type | Scope | Priority | Automated |
|-----------|-------|----------|-----------|
| Unit: PeerFinder | L4 | HIGH | ✅ |
| Unit: ValuationCalc | L4 | HIGH | ✅ |
| Unit: DocumentLoader | L4 | HIGH | ✅ |
| Unit: Chunker | L4 | HIGH | ✅ |
| Integration: Data Agent | L5 | HIGH | ✅ |
| Integration: Analyst Agent | L5 | HIGH | ✅ |
| Integration: RAG Agent | L5 | HIGH | ✅ |
| Integration: Supervisor Routing | L7 | HIGH | ✅ |
| E2E: Prompt #4 | All | CRITICAL | ✅ |
| E2E: Prompt #2 | All | CRITICAL | ✅ |
| Performance: Token Usage | Cross | MEDIUM | ✅ |
| Performance: Latency | Cross | MEDIUM | ✅ |
| Chaos: Agent Timeout | L7 | MEDIUM | ✅ |
| Chaos: Partial Failure | L7 | MEDIUM | ✅ |

---

# 📊 SUCCESS CRITERIA

## Minimum Viable Product (MVP)

| Criteria | Target | Measurement |
|----------|--------|-------------|
| Prompt #4 Success Rate | >90% | 10 test runs with different tickers |
| Prompt #2 Success Rate | >85% | 10 test runs with different documents |
| End-to-End Latency | <30s | Time from query to response |
| Token Efficiency | <10k/query | Average tokens per complex query |
| Error Recovery | >80% | Retry success rate on failures |

## Demo Requirements

| Requirement | Status |
|-------------|--------|
| README with architecture diagram | ⬜ |
| Working demo of Prompt #4 | ⬜ |
| Working demo of Prompt #2 | ⬜ |
| Sample earnings call PDF included | ⬜ |
| 2-minute demo video/GIF | ⬜ |
| Clean, documented code | ⬜ |
| Passing test suite | ⬜ |

---

# 🚀 NEXT STEPS

**Immediate Action:** Start Phase 4.1 - Multi-Agent Foundation

Week 1, Day 1:
1. Create `src/agents/base_agent.py`
2. Create `src/agents/protocols.py` (AgentResponse, AgentTask)
3. Create basic `src/agents/supervisor_agent.py`
4. Write first integration test

Soll ich mit der Implementierung beginnen?

