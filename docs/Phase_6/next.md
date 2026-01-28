## 📋 Phase 6.6 Summary: What We Built and Why

---

### The Big Picture

We transformed an "AI Portfolio Optimizer" into a **PM Decision Support System** - a system that thinks like a portfolio manager, not just a calculator.

---

### What We Built

#### 1. **Dual-Intent System** (schemas.py, router_prompts.py)

**Why:** Users ask questions with different purposes. "Optimize my portfolio" implies action. "What's the VIX?" is just information. Treating them the same creates **action bias**.

**How:** 
- `QueryIntent`: What the user wants (information, decision, operational, analysis)
- `ExecutionIntent`: What agents to run (optimization, macro_analysis, portfolio_mgmt)
- Router classifies both independently

**Result:** Information queries never get trade recommendations. Decision queries get full PM analysis.

---

#### 2. **Decision Engine** (decision_engine.py, decision_schemas.py)

**Why:** Most AI systems assume action is always needed. Real PMs often decide "do nothing" is optimal. This is the **core differentiator**.

**How:**
- `RiskAssessment`: Evaluates CURRENT portfolio (concentration, diversification, breaches)
- `PMDecisionSummary`: HOLD/TILT/REBALANCE/HEDGE with confidence and rationale
- 7-tier decision priority logic (Crisis → HEDGE, High drift → REBALANCE, etc.)
- All thresholds from `config.py` (auditable, adjustable)

**Result:** System explicitly evaluates "should we act?" before "how should we act?"

---

#### 3. **Risk-First Workflow** (nodes.py, synthesizer)

**Why:** Institutional workflows assess risk BEFORE considering action. We mirror this.

**How:**
- `_extract_current_weights_from_state()`: Gets ACTUAL holdings from database
- Risk assessment runs on current weights, not proposed weights
- Decision summary shows Current vs Proposed allocation

**Result:** Output shows what you HAVE, what's RECOMMENDED, and WHY.

---

#### 4. **Decision Logging** (decision_logger.py, database_setup.py)

**Why:** Institutional decisions are auditable. Every recommendation should be traceable.

**How:**
- `DecisionLog` table stores every decision with full context
- Tracks: decision type, confidence, rationale, risk status, weights, macro regime
- Links to portfolio and original user query

**Result:** Can answer "what did the system recommend 3 months ago and why?"

---

#### 5. **Response Formatting** (synthesizer_node)

**Why:** Output should look like what a PM actually reads, not raw JSON.

**How:**
- Structured blocks: DECISION SUMMARY → RISK ASSESSMENT → ALLOCATION COMPARISON
- Clear visual hierarchy with separators
- Shows confidence levels, key risks, trade requirements

**Result:** Bank-ready output format.

---

### Files Created/Modified

| File | Purpose |
|------|---------|
| `src/agents/decision_schemas.py` | DecisionType, RiskStatus, PMDecisionSummary, RiskAssessment |
| `src/agents/decision_engine.py` | assess_portfolio_risk(), assess_decision_needed(), run_decision_assessment() |
| `src/agents/decision_logger.py` | log_decision(), get_decision_history(), get_decision_stats() |
| `src/agents/schemas.py` | QueryIntent, ExecutionIntent (updated) |
| `src/agents/router_prompts.py` | Dual-intent few-shot examples |
| `src/agents/nodes.py` | Updated synthesizer, _generate_decision_summary(), data_fetch fixes |
| `src/portfolio_tool/database_setup.py` | DecisionLog table |
| `tests/test_phase66_comprehensive.py` | 40 tests covering all components |
| `scripts/seed_database.py` | Realistic portfolio data seeder |

---

### Test Results

```
TOTAL: 40/40 passed ✅
- Schemas: 6/6
- State: 5/5
- Decision Engine: 5/5
- Config: 1/1
- Tools: 4/4
- Services: 4/4
- Router: 10/10
- E2E: 5/5
```

---

"""
🔬 RAG INTEGRATION PROTOCOL - Phase 6.7
========================================
The "Researcher" Brain for PM Decision Support System

PURPOSE: This document defines the complete RAG implementation plan.
         RAG synergizes with the Decision Engine - not standalone Q&A.

LAST UPDATED: January 25, 2026
VERSION: 1.0

=============================================================================
SECTION 1: VISION & GOALS
=============================================================================

WHAT WE'RE BUILDING:
    Documents feed INTO the Decision Engine to enhance decisions.
    
    BEFORE RAG:
        User: "Should I increase my NVDA position?"
        System: [Uses only price data + macro] → Generic recommendation
    
    AFTER RAG:
        User: "Should I increase my NVDA position?"
        System: [Reads NVDA's 10-K, earnings call, Fed minutes] 
              → "Based on Q3 earnings showing 279% data center growth, 
                 but noting China export risks cited on page 12..."

KEY PRINCIPLE:
    RAG insights are ONE INPUT to the Decision Engine, alongside:
    - Current portfolio weights
    - Optimization results
    - Macro regime
    - Risk assessment
    
    The Decision Engine synthesizes ALL inputs into HOLD/TILT/REBALANCE/HEDGE.

=============================================================================
SECTION 2: DOCUMENT TYPES
=============================================================================

┌─────────────────────┬────────────────────┬──────────────────────────────────┐
│ Document Type       │ Source             │ Use Case                         │
├─────────────────────┼────────────────────┼──────────────────────────────────┤
│ Earnings Reports    │ SEC EDGAR, IR      │ Extract revenue, EPS, guidance   │
│ 10-K/10-Q Filings   │ SEC EDGAR          │ Risk factors, business segments  │
│ Fed Minutes         │ fed_scraper.py ✅   │ Rate expectations, policy stance │
│ Research Notes      │ User uploads       │ Analyst recommendations          │
│ News Articles       │ News APIs/uploads  │ Breaking news impact             │
│ Internal Memos      │ User uploads       │ Investment theses, notes         │
└─────────────────────┴────────────────────┴──────────────────────────────────┘

METADATA FOR EACH DOCUMENT:
    - ticker: Related security (e.g., "NVDA", "SPY") or None
    - doc_type: "earnings", "10k", "fed_minutes", "research", "news"
    - date: Document date (for recency filtering)
    - source: "sec_edgar", "federal_reserve", "user_upload"
    - sections: Extracted section headers (for navigation)

=============================================================================
SECTION 3: TECHNOLOGY STACK
=============================================================================

┌─────────────────────┬────────────────────┬──────────────────────────────────┐
│ Component           │ Technology         │ Why                              │
├─────────────────────┼────────────────────┼──────────────────────────────────┤
│ Vector Store        │ ChromaDB           │ Local, free, great metadata      │
│ Embeddings          │ OpenAI small       │ Best quality, negligible cost    │
│ PDF Parsing         │ PyMuPDF (fitz)     │ Fast, handles tables well        │
│ Text Chunking       │ Custom recursive   │ Section-aware, not arbitrary     │
│ Fed Data            │ fed_scraper.py     │ Already built and tested         │
│ Orchestration       │ LangGraph          │ Existing infrastructure          │
└─────────────────────┴────────────────────┴──────────────────────────────────┘

EMBEDDING DETAILS:
    Model: text-embedding-3-small (OpenAI)
    Dimensions: 1536
    Cost: $0.02 per 1M tokens (~$0.001 for 50 documents)
    
    Fallback (if no API):
    Model: all-MiniLM-L6-v2 (sentence-transformers)
    Dimensions: 384
    Quality: ~90% of OpenAI

CHROMADB DETAILS:
    Storage: data/chroma/ (alongside portfolio.db)
    Collection: "portfolio_documents"
    Metadata filtering: ticker, doc_type, date range

=============================================================================
SECTION 4: ARCHITECTURE
=============================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOCUMENT INGESTION LAYER                            │
│                                                                              │
│   fed_scraper.py ──┬── document_loader.py ──── chunker.py                   │
│   PDF uploads ─────┤                              │                          │
│   Text files ──────┘                              ▼                          │
│                                           ┌──────────────┐                   │
│                                           │   Embeddings │                   │
│                                           │   (OpenAI)   │                   │
│                                           └──────┬───────┘                   │
│                                                  │                           │
│                                                  ▼                           │
│                                           ┌──────────────┐                   │
│                                           │   ChromaDB   │                   │
│                                           │   (vectors)  │                   │
│                                           └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              QUERY LAYER                                     │
│                                                                              │
│   User Query ───► Router ───► RAG Agent ───► search_documents()             │
│                                    │              │                          │
│                                    │              ▼                          │
│                                    │        ChromaDB query                   │
│                                    │        (with metadata filters)          │
│                                    │              │                          │
│                                    ▼              ▼                          │
│                              document_insights = {                           │
│                                  "sources": [...],                           │
│                                  "key_findings": [...],                      │
│                                  "risk_factors": [...],                      │
│                                  "citations": [...]                          │
│                              }                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DECISION ENGINE (Updated)                          │
│                                                                              │
│   run_decision_assessment(                                                   │
│       current_weights=...,                                                   │
│       target_weights=...,                                                    │
│       macro_regime=...,                                                      │
│       document_insights=...,  ◄── NEW: RAG findings                         │
│   ) → (RiskAssessment, PMDecisionSummary)                                   │
│                                                                              │
│   Decision rationale now includes:                                           │
│   • "According to Q3 earnings report..."                                     │
│   • "Fed minutes indicate higher-for-longer stance..."                       │
│   • "Risk factor from 10-K: China export restrictions"                       │
└─────────────────────────────────────────────────────────────────────────────┘

=============================================================================
SECTION 5: FILE STRUCTURE
=============================================================================

src/portfolio_tool/rag/
├── __init__.py              # RAG module exports
├── document_loader.py       # Load PDFs, text, Fed data
├── chunker.py               # Smart section-aware chunking
├── embeddings.py            # OpenAI + local fallback
├── vector_store.py          # ChromaDB wrapper
├── fed_scraper.py           # Your existing Fed scraper (move here)
└── schemas.py               # Document, Chunk, SearchResult dataclasses

src/portfolio_tool/tools/
└── rag_tools.py             # Tool wrappers for RAG agent

src/agents/
├── rag_agent.py             # NEW: The "Researcher" agent
├── nodes.py                 # Updated: Add rag_agent_node
├── graph.py                 # Updated: Add RAG to execution flow
└── decision_engine.py       # Updated: Accept document_insights

data/
├── portfolio.db             # Existing SQLite
├── chroma/                  # NEW: ChromaDB storage
│   └── portfolio_documents/ # Vector collection
└── documents/               # NEW: Uploaded PDFs cache
    ├── earnings/
    ├── filings/
    └── fed_minutes/

=============================================================================
SECTION 6: DATABASE TABLES
=============================================================================

Add to database_setup.py:

class Document(Base):
    '''Tracks all ingested documents for deduplication and metadata.'''
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    doc_type = Column(String(50), nullable=False)  # earnings, 10k, fed_minutes, etc.
    ticker = Column(String(20), nullable=True, index=True)
    source = Column(String(50), nullable=False)  # sec_edgar, federal_reserve, user_upload
    
    # Content tracking
    content_hash = Column(String(64), unique=True)  # SHA256 for dedup
    chunk_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Dates
    document_date = Column(Date, nullable=True)  # Date of the document content
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    # Status
    status = Column(String(20), default="pending")  # pending, processed, failed
    error_message = Column(String(500), nullable=True)
    
    # ChromaDB reference
    collection_name = Column(String(100), default="portfolio_documents")
    
    __table_args__ = (
        Index('ix_doc_ticker_type', 'ticker', 'doc_type'),
        Index('ix_doc_date', 'document_date'),
    )

=============================================================================
SECTION 7: IMPLEMENTATION PHASES
=============================================================================

PHASE 1: Document Ingestion (2 hours)
─────────────────────────────────────
Files:
    - src/portfolio_tool/rag/__init__.py
    - src/portfolio_tool/rag/schemas.py
    - src/portfolio_tool/rag/document_loader.py
    - src/portfolio_tool/rag/chunker.py

Capabilities:
    - Load PDFs (PyMuPDF)
    - Load text files
    - Load Fed minutes (integrate fed_scraper.py)
    - Smart chunking by section (not arbitrary 500-char splits)
    - Extract metadata (ticker, date, doc_type)

Key Classes:
    @dataclass
    class Document:
        content: str
        metadata: Dict[str, Any]
        chunks: List[Chunk] = field(default_factory=list)
    
    @dataclass
    class Chunk:
        content: str
        metadata: Dict[str, Any]
        index: int
        token_count: int

Test:
    loader = DocumentLoader()
    doc = loader.load_pdf("path/to/NVDA_10K.pdf", ticker="NVDA")
    chunks = Chunker().chunk_document(doc)
    assert len(chunks) > 0

─────────────────────────────────────
PHASE 2: Vector Store (1.5 hours)
─────────────────────────────────────
Files:
    - src/portfolio_tool/rag/embeddings.py
    - src/portfolio_tool/rag/vector_store.py

Capabilities:
    - Generate embeddings (OpenAI primary, local fallback)
    - Store in ChromaDB with metadata
    - Search with filters (ticker, doc_type, date range)
    - Relevance scoring

Key Classes:
    class EmbeddingService:
        def embed(self, texts: List[str]) -> List[List[float]]
        def embed_query(self, query: str) -> List[float]
    
    class VectorStore:
        def add_document(self, doc: Document) -> str  # Returns doc_id
        def search(self, query: str, filters: Dict, top_k: int) -> List[SearchResult]
        def delete_document(self, doc_id: str) -> bool

Test:
    store = VectorStore()
    store.add_document(doc)
    results = store.search("NVIDIA revenue growth", filters={"ticker": "NVDA"}, top_k=5)
    assert len(results) > 0

─────────────────────────────────────
PHASE 3: RAG Agent (2 hours)
─────────────────────────────────────
Files:
    - src/agents/rag_agent.py
    - src/portfolio_tool/tools/rag_tools.py

Tools:
    @tool
    def search_documents(query: str, ticker: str = None, doc_type: str = None, 
                         days_back: int = 90, top_k: int = 5) -> Dict:
        '''Semantic search across all documents.'''
    
    @tool
    def summarize_document(doc_id: str, focus: str = None) -> Dict:
        '''Summarize a specific document, optionally focusing on a topic.'''
    
    @tool
    def extract_risk_factors(ticker: str) -> Dict:
        '''Extract risk factors from 10-K/10-Q filings for a ticker.'''
    
    @tool
    def get_fed_sentiment(months_back: int = 3) -> Dict:
        '''Analyze Fed stance from recent minutes.'''
    
    @tool
    def find_ticker_mentions(ticker: str, days_back: int = 30) -> Dict:
        '''Find all mentions of a ticker across documents.'''

Agent:
    class RAGAgent:
        '''The "Researcher" - searches documents, extracts insights.'''
        
        def research(self, query: str, context: Dict) -> DocumentInsights:
            '''
            Main entry point. Returns structured insights for Decision Engine.
            
            Returns:
                DocumentInsights with:
                - sources: List of source documents used
                - key_findings: Extracted facts/metrics
                - risk_factors: Identified risks
                - sentiment: Overall document sentiment
                - citations: Quotable excerpts with page refs
            '''

Test:
    agent = RAGAgent()
    insights = agent.research("What did NVIDIA report?", {"ticker": "NVDA"})
    assert insights.key_findings is not None

─────────────────────────────────────
PHASE 4: Decision Engine Integration (1.5 hours)
─────────────────────────────────────
Files:
    - src/agents/decision_engine.py (update)
    - src/agents/decision_schemas.py (update)
    - src/agents/nodes.py (update)

Updates to decision_engine.py:
    def run_decision_assessment(
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        max_drift: float,
        macro_regime: str,
        vix_level: float,
        portfolio_volatility: float,
        trigger: str,
        document_insights: Optional[DocumentInsights] = None,  # ← NEW
    ) -> Tuple[RiskAssessment, PMDecisionSummary]:
        
        # Document insights can influence:
        # 1. Risk assessment (risks from filings)
        # 2. Decision confidence (earnings beat = higher confidence)
        # 3. Rationale text (include citations)

Updates to PMDecisionSummary:
    @dataclass
    class PMDecisionSummary:
        decision: DecisionType
        confidence: float
        rationale: str
        key_risks: List[str]
        trade_required: bool
        trigger: str
        document_citations: List[str] = field(default_factory=list)  # ← NEW

Updates to nodes.py:
    - Add rag_agent_node() function
    - Update router to include RAGAgent for decision queries
    - Update synthesizer to display document insights section

New Output Section:
    ════════════════════════════════════════════════════════════
    DOCUMENT INSIGHTS
    ════════════════════════════════════════════════════════════
    Sources: NVDA_Q3_2024_Earnings.pdf, Fed_Minutes_Dec2024.txt
    
    Key Findings:
      • NVDA revenue: $18.1B (+12% vs consensus)
      • Data center growth: +279% YoY
      • Fed stance: "Higher for longer" language maintained
    
    Risk Factors (from filings):
      • China export restrictions (NVDA 10-K, p.12)
      • Customer concentration risk (top 4 = 46% revenue)

Test:
    Full E2E test with uploaded document → decision with citations

=============================================================================
SECTION 8: ROUTER UPDATES
=============================================================================

Update router to trigger RAG Agent for relevant queries:

EXECUTION INTENT UPDATES:
    optimization → DataAgent → RAGAgent (if docs exist) → OptimizationAgent
    risk_analysis → DataAgent → RAGAgent → RiskAnalysisAgent
    
NEW INTENT:
    document_search → RAGAgent only (for pure document queries)

Router Few-Shot Examples:
    User: "What did NVIDIA report last quarter?"
    → query_intent: information, execution_intent: document_search
    
    User: "Given NVIDIA's earnings, should I increase my position?"
    → query_intent: decision, execution_intent: optimization
    → Agents: [DataAgent, RAGAgent, OptimizationAgent]

=============================================================================
SECTION 9: TARGET INTERVIEW PROMPTS
=============================================================================

These demonstrate RAG + Decision Engine synergy:

PROMPT 1: Document-Informed Decision
────────────────────────────────────
User: "I just uploaded NVIDIA's Q3 2024 earnings report. 
       Given this new information, should I increase my position 
       in the Growth Tech portfolio?"

Expected Output:
    DECISION: TILT (78% confidence)
    RATIONALE: Based on NVIDIA's Q3 earnings report analysis:
      • Revenue beat: $18.1B vs $16.2B expected
      • Data center: +279% YoY
      Risk factors from filing:
      • China export restrictions (page 12)
    DOCUMENT INSIGHTS: [citations from the PDF]
    ALLOCATION: Current NVDA 22% → Proposed 27%

PROMPT 2: Multi-Source Risk Assessment
────────────────────────────────────
User: "I'm worried about my Dividend Income portfolio given 
       recent Fed commentary. Search my documents for anything 
       about interest rate sensitivity and tell me if I should hedge."

Expected Output:
    DECISION: HEDGE (82% confidence)
    RATIONALE: Multiple risk signals detected:
      1. Macro: Fed funds 5.25-5.50%, inverted yield curve
      2. Documents: Fed minutes show "higher for longer" stance
      3. Portfolio: 25% in rate-sensitive bonds (BND, LQD)
    DOCUMENT INSIGHTS: [Fed minutes quotes, 10-K risk factors]

PROMPT 3: The "Do Nothing" with Evidence
────────────────────────────────────
User: "The market dropped 3% today. My All-Weather portfolio 
       is down 1.5%. Should I make any changes? 
       Check if any of my holdings have news."

Expected Output:
    DECISION: HOLD (91% confidence)
    RATIONALE: Portfolio performing AS DESIGNED
      • Market: -3.0%, Your portfolio: -1.5% (50% downside capture)
      • Document search: No material news for holdings
      • Defensive assets (GLD +0.8%, TLT +1.2%) working as intended
    DOCUMENT INSIGHTS: "No recent documents found for portfolio holdings"

=============================================================================
SECTION 10: TESTING STRATEGY
=============================================================================

Unit Tests:
    test_document_loader.py
        - test_load_pdf
        - test_load_text
        - test_load_fed_minutes
        - test_extract_metadata
    
    test_chunker.py
        - test_chunk_by_section
        - test_chunk_size_limits
        - test_overlap_handling
    
    test_vector_store.py
        - test_add_document
        - test_search_basic
        - test_search_with_filters
        - test_delete_document
    
    test_rag_agent.py
        - test_search_documents
        - test_extract_risk_factors
        - test_get_fed_sentiment

Integration Tests:
    test_rag_e2e.py
        - test_upload_and_search
        - test_decision_with_documents
        - test_no_documents_graceful

=============================================================================
SECTION 11: DEPENDENCIES
=============================================================================

Add to requirements.txt:
    chromadb>=0.4.0
    openai>=1.0.0  # For embeddings (you may already have this)
    pymupdf>=1.23.0  # PDF parsing (also called 'fitz')
    tiktoken>=0.5.0  # Token counting

Optional (local embeddings fallback):
    sentence-transformers>=2.2.0

Install:
    pip install chromadb pymupdf tiktoken

=============================================================================
SECTION 12: CONFIGURATION
=============================================================================

Add to src/config.py:

@dataclass
class RAGConfig:
    '''RAG pipeline configuration.'''
    # Embeddings
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    use_local_fallback: bool = True
    local_model: str = "all-MiniLM-L6-v2"
    
    # ChromaDB
    chroma_persist_dir: str = "data/chroma"
    collection_name: str = "portfolio_documents"
    
    # Chunking
    chunk_size: int = 1000  # tokens
    chunk_overlap: int = 100  # tokens
    
    # Search
    default_top_k: int = 5
    relevance_threshold: float = 0.7  # Minimum similarity score
    
    # Document storage
    documents_dir: str = "data/documents"

=============================================================================
END OF RAG INTEGRATION PROTOCOL
=============================================================================
"""