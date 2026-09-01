"""
🚀 PROJECT CONTEXT: PM DECISION SUPPORT SYSTEM
==============================================
Multi-Agent System for Institutional Portfolio Management

PURPOSE: This file contains everything an LLM needs to understand the project.
         Upload this when starting a new chat. The LLM should be able to continue
         development without additional context.

LAST UPDATED: Phase 6.7 Complete (RAG Integration with Decision Engine)
VERSION: 0.8.0
DATE: January 26, 2026

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
    6. Document-Backed Decisions - RAG provides citations from filings/reports (NEW!)
    7. Fed Sentiment Analysis - Hybrid rule-based + LLM analysis of FOMC minutes (NEW!)

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
│   └── ExecutionIntent: WHAT to run (optimization, document_search, etc.)    │
│                                                                              │
│   This prevents action bias: "What's VIX?" → info only, no trade recs       │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    📊 LANGGRAPH STATE MACHINE                                │
│        Flow: Router → Dispatcher → [Agents] → Decision Engine → Synthesizer │
└───────────┬─────────────┬─────────────┬─────────────┬───────────┬───────────┘
            │             │             │             │           │
            ▼             ▼             ▼             ▼           ▼
     ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ ┌──────────┐
     │ 📊 DATA   │  │ 📄 RAG   │  │ 🌍 MACRO │  │ 🔧 OPTIM │ │ ⚖️ REBAL │
     │  AGENT   │  │  AGENT   │  │  AGENT   │  │  AGENT   │ │  AGENT   │
     └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ └────┬─────┘
          │             │             │             │             │
          ▼             ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         🧠 DECISION ENGINE (Phase 6.6 + 6.7)                 │
│                                                                              │
│   1. RiskAssessment: Evaluate CURRENT portfolio (before any action)         │
│   2. DocumentInsights: Citations from RAG (10-Ks, earnings, Fed) ← NEW!     │
│   3. PMDecisionSummary: HOLD / TILT / REBALANCE / HEDGE with [DOC] refs     │
│   4. DecisionLog: Persist to database for audit trail                       │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TOOL LAYER                                      │
│       (data_tools, macro_tools, rag_tools, optimization_tools, etc.)         │
│                   ⚠️ DETERMINISTIC - NO LLM MATH! ⚠️                         │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                   ┌──────────────────────┼──────────────────────┐
                   ▼                      ▼                      ▼
┌─────────────────────────┐  ┌─────────────────────────┐  ┌──────────────────┐
│       SQLite DB         │  │      ChromaDB           │  │    YFinance      │
│  portfolios, prices,    │  │   (Vector Store)        │  │   Market Data    │
│  holdings, decisions    │  │  10-Ks, earnings, Fed   │  │                  │
└─────────────────────────┘  └─────────────────────────┘  └──────────────────┘

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
   ├── Fed Sentiment (rule-based) = Pure Python keyword matching
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
│ document_search    │ RAGAgent (NEW - Phase 6.7)                          │
│ combined           │ DataAgent + RAGAgent + others (multi-agent)         │
└────────────────────┴─────────────────────────────────────────────────────┘

CRITICAL RULE:
- Decision Summaries (HOLD/TILT/REBALANCE/HEDGE) are ONLY generated 
  when query_intent == "decision"
- Information/operational queries get data only, no trade recommendations
- This prevents action bias

=============================================================================
SECTION 5: DECISION ENGINE (Phase 6.6 + 6.7)
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
- run_decision_assessment(..., document_insights) → (RiskAssessment, PMDecisionSummary)
- should_generate_decision_summary(query_intent) → bool

DOCUMENT INTEGRATION (Phase 6.7):
- run_decision_assessment() now accepts optional document_insights parameter
- Document risk factors get [DOC] prefix in key_risks
- Fed sentiment influences macro_regime (hawkish → risk_off if neutral)
- Citations added to PMDecisionSummary.document_citations

=============================================================================
SECTION 6: RAG PIPELINE (Phase 6.7) - NEW!
=============================================================================

ARCHITECTURE:
┌──────────────────────────────────────────────────────────────────────────┐
│                         RAG PIPELINE                                      │
└──────────────────────────────────────────────────────────────────────────┘
                              │
    Documents (PDF/TXT)       │
    ├── 10-K Filings          │
    ├── Earnings Reports      │
    └── Fed Minutes           │
              │               │
              ▼               │
    ┌─────────────────┐       │
    │ DocumentLoader  │───────┼───▶  Extracts text, detects ticker/type
    └─────────────────┘       │
              │               │
              ▼               │
    ┌─────────────────┐       │
    │    Chunker      │───────┼───▶  Section-aware chunking (1000 tokens)
    └─────────────────┘       │
              │               │
              ▼               │
    ┌─────────────────┐       │
    │ EmbeddingService│───────┼───▶  OpenAI text-embedding-3-small
    └─────────────────┘       │
              │               │
              ▼               │
    ┌─────────────────┐       │
    │  VectorStore    │───────┼───▶  ChromaDB with metadata filtering
    │  (ChromaDB)     │       │
    └─────────────────┘       │
              │               │
              ▼               │
    ┌─────────────────┐       │
    │   RAGAgent      │───────┼───▶  Orchestrates search + extraction
    └─────────────────┘       │
              │               │
              ▼               │
    ┌─────────────────┐       │
    │ DecisionEngine  │───────┼───▶  Document insights in rationale
    └─────────────────┘       │

FILES:
├── src/portfolio_tool/rag/
│   ├── __init__.py              # Clean exports
│   ├── schemas.py               # Document, Chunk, SearchResult, DocumentInsights
│   ├── document_loader.py       # PDF/TXT loading with auto-detection
│   ├── chunker.py               # Section-aware text chunking
│   ├── embeddings.py            # OpenAI + local fallback embeddings
│   ├── vector_store.py          # ChromaDB wrapper with metadata filtering
│   ├── sentiment.py             # Hybrid Fed sentiment (rule-based + GPT)
│   ├── fed_scraper.py           # Auto-fetch FOMC minutes
│   ├── document_manager.py      # Easy ingestion API
│   └── rag_agent.py             # Document research orchestrator

DOCUMENT TYPES SUPPORTED:
┌──────────────────┬─────────────────────────────────────────────────────────┐
│ Type             │ Auto-Detection                                          │
├──────────────────┼─────────────────────────────────────────────────────────┤
│ 10-K / 10-Q      │ Filename contains "10K", "10-K", "10Q", "10-Q"          │
│ Earnings         │ Filename contains "earnings", "Q1", "Q2", etc.          │
│ Fed Minutes      │ Filename contains "fed", "fomc", "minutes"              │
│ Other            │ Default fallback                                        │
└──────────────────┴─────────────────────────────────────────────────────────┘

FED SENTIMENT ANALYSIS (Hybrid):
┌─────────────────────────────────────────────────────────────────────────────┐
│                     HYBRID SENTIMENT ANALYZER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Step 1: Rule-based scoring (ALWAYS runs - free, fast)                      │
│          HAWKISH keywords: inflation, tightening, restrictive, elevated     │
│          DOVISH keywords: accommodate, support, patient, gradual            │
│                                                                             │
│  Step 2: Confidence check                                                   │
│          If confidence < 0.6 OR score near neutral → use LLM                │
│                                                                             │
│  Step 3: LLM refinement (only if needed)                                    │
│          GPT analyzes summarized text (~500 tokens)                         │
│          Weighted blend of rule + LLM scores                                │
│                                                                             │
│  Output: {score: -1 to +1, confidence: 0-1, method: "hybrid"}               │
└─────────────────────────────────────────────────────────────────────────────┘

DOCUMENT MANAGER USAGE:
    from portfolio_tool.rag import DocumentManager
    
    dm = DocumentManager()
    
    # Ingest single document
    dm.ingest("data/documents/NVDA_10K.pdf", ticker="NVDA")
    
    # Ingest all documents in folder
    dm.ingest_folder()
    
    # Fetch and ingest Fed minutes
    dm.ingest_fed_minutes()
    
    # List indexed documents
    dm.list_documents()
    
    # Search
    dm.search("China export restrictions", ticker="NVDA")

=============================================================================
SECTION 7: DATABASE SCHEMA
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

VECTOR STORE (ChromaDB - separate from SQLite):
├── Collection: "documents"
├── Metadata: doc_id, ticker, doc_type, section, filename, content_hash
└── Embeddings: OpenAI text-embedding-3-small (1536 dimensions)

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
    document_citations (JSON array) ← NEW Phase 6.7

=============================================================================
SECTION 8: FILE STRUCTURE
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
│   ├── backtest_agent.py        # Historical simulation
│   └── rag_agent.py             # ⭐ Phase 6.7: Document research
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
    │   ├── portfolio_tools.py   # Portfolio management tools
    │   └── rag_tools.py         # ⭐ Phase 6.7: RAG tool wrappers
    │
    ├── providers/
    │   └── yfinance_provider.py # YFinance API wrapper
    │
    └── rag/                     # ⭐ Phase 6.7: RAG Module
        ├── __init__.py          # Clean exports
        ├── schemas.py           # Document, Chunk, SearchResult
        ├── document_loader.py   # PDF/TXT loading
        ├── chunker.py           # Section-aware chunking
        ├── embeddings.py        # OpenAI + local embeddings
        ├── vector_store.py      # ChromaDB wrapper
        ├── sentiment.py         # Hybrid Fed sentiment
        ├── fed_scraper.py       # FOMC minutes fetcher
        ├── document_manager.py  # Easy ingestion API
        └── rag_agent.py         # Document research orchestrator

scripts/
├── seed_database.py             # Realistic data seeder

demos/
├── langgraph_demo_v3.py         # ⭐ Interactive CLI with RAG commands
├── interview_demo.py            # ⭐ Simulated WOW demo for interviews

tests/
├── test_phase66_comprehensive.py # 40-test comprehensive suite
├── test_rag_phase1.py           # ⭐ Document ingestion (26 tests)
├── test_rag_phase2.py           # ⭐ Vector store (18 tests)
├── test_rag_phase3.py           # ⭐ RAG agent + sentiment (22 tests)
├── test_rag_phase4.py           # ⭐ Decision integration (9 tests)
├── test_rag_integration.py      # ⭐ End-to-end (14 tests)
└── conftest.py                  # Pytest configuration

data/
├── portfolio.db                 # SQLite database
├── chroma/                      # ChromaDB vector store
└── documents/                   # Document folder for ingestion
    ├── NVDA_Q3_2024_Earnings.txt
    ├── AAPL_10K_2024.txt
    └── (Fed minutes via /fed command)

=============================================================================
SECTION 9: CONFIGURATION (src/config.py)
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

@dataclass
class RAGConfig:                         # ⭐ NEW Phase 6.7
    chroma_persist_dir: str = "data/chroma"
    documents_dir: str = "data/documents"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 100
    min_chunk_size: int = 50
    default_top_k: int = 5
    relevance_threshold: float = 0.7
    supported_extensions: tuple = (".pdf", ".txt", ".md")
    max_document_size_mb: int = 50

@dataclass
class SentimentConfig:                   # ⭐ NEW Phase 6.7
    llm_confidence_threshold: float = 0.6   # Below this → use LLM
    ambiguous_score_range: float = 0.2      # Near-neutral → use LLM
    max_text_tokens: int = 500              # Truncate before LLM
    llm_provider: str = "openai"            # openai or anthropic
    llm_model: str = "gpt-4o-mini"

=============================================================================
SECTION 10: CURRENT STATUS
=============================================================================

✅ COMPLETED:
├── Phase 5.x: Core Agents (Data, Macro, Optimization, Rebalance, Backtest)
├── Phase 6.1: Smart Router (LLM-based intent detection)
├── Phase 6.2: LangGraph State Machine (dynamic routing, streaming)
├── Phase 6.12: Guardrails & Schemas (strict typing)
├── Phase 6.3: Basic Observability (tracing)
├── Phase 6.5: Portfolio Management (admin tools wired to router)
├── Phase 6.6: Decision Engine
│   ├── Dual-Intent System (QueryIntent + ExecutionIntent)
│   ├── Risk Assessment (runs BEFORE optimization)
│   ├── PM Decision Summary (HOLD/TILT/REBALANCE/HEDGE)
│   ├── Decision Logging (full audit trail)
│   ├── Response Formatting (PM-style output)
│   └── 40/40 Tests Passing
│
└── Phase 6.7: RAG Integration ⭐ NEW - COMPLETE
    ├── Document Ingestion (PDF, TXT, MD support)
    ├── Section-Aware Chunking (preserves structure)
    ├── Vector Store (ChromaDB with metadata filtering)
    ├── Hybrid Fed Sentiment (rule-based + LLM)
    ├── RAG Agent (orchestrates search + extraction)
    ├── Decision Engine Integration (document citations)
    ├── DocumentManager (easy ingestion API)
    ├── Demo v3 with RAG commands
    └── 89/89 Tests Passing (26+18+22+9+14)

⏳ FUTURE CONSIDERATIONS:
├── News API integration (for "check holdings for news")
├── Trade execution (broker integration)
├── Multi-user authentication
├── Scheduled alerts

=============================================================================
SECTION 11: KNOWN LIMITATIONS
=============================================================================

1. NO TRADE EXECUTION: Recommendations only, no broker integration
2. NO AUTHENTICATION: Single user, no multi-tenancy
3. NO ALERTS: Cannot schedule "alert me when drift > 5%"
4. NO NEWS API: Cannot fetch real-time news (only indexed documents)
5. FED SCRAPER: May break if federalreserve.gov changes structure

=============================================================================
SECTION 12: TARGET INTERVIEW PROMPTS (WOW Demos)
=============================================================================

These prompts demonstrate the SYNERGY between RAG and Decision Engine:

PROMPT 1 - The "Smart HOLD" (Anti-Action-Bias):
"Markets dropped 4% today. My portfolio is down 2.1%. 
Should I sell everything and go to cash?"

Expected: HOLD decision with evidence that diversification is working
Shows: System is NOT action-biased - knows when to do nothing

PROMPT 2 - Document-Informed Decision:
"Based on NVIDIA's Q3 earnings showing 279% growth but China export 
restrictions, should I increase my position?"

Expected: Decision with [DOC] citations from actual filing
Shows: RAG feeds into decision rationale with audit trail

PROMPT 3 - Fed Policy Impact:
"The Fed just released hawkish minutes. How does this affect my 
dividend portfolio? Should I rotate into shorter duration?"

Expected: Fed sentiment analysis + macro context + rotation recommendation
Shows: Hybrid sentiment analysis + institutional thinking

PROMPT 4 - Full Quarterly Review:
"Run a full quarterly review of my portfolio:
Check drift, analyze macro, review relevant filings, recommend actions."

Expected: Multi-agent collaboration with comprehensive output
Shows: Full orchestration capabilities

=============================================================================
SECTION 13: WORKING WITH THIS PROJECT
=============================================================================

RUNNING THE DEMO:
    python demos/langgraph_demo_v3.py
    
    RAG Commands:
    • /ingest <file>  - Ingest document into RAG
    • /ingestall      - Ingest all from data/documents/
    • /fed            - Fetch & analyze Fed minutes
    • /docs           - List indexed documents
    • /search <query> - Search documents
    • /stats          - RAG statistics
    
    Other Commands:
    • /assets         - List tracked assets
    • /macro          - Macro environment
    • /portfolios     - List portfolios
    • /debug          - Toggle debug mode
    • exit            - Quit

RUNNING INTERVIEW DEMO (Simulated):
    python demos/interview_demo.py
    
    Pre-configured WOW prompts with perfect responses.
    Use for interviews when real system might have issues.

RUNNING TESTS:
    # Full RAG test suite (89 tests)
    pytest tests/test_rag*.py -v
    
    # Specific phase
    pytest tests/test_rag_phase1.py -v  # Document ingestion
    pytest tests/test_rag_phase2.py -v  # Vector store
    pytest tests/test_rag_phase3.py -v  # RAG agent
    pytest tests/test_rag_phase4.py -v  # Decision integration
    
    # Decision engine tests
    pytest tests/test_phase66_comprehensive.py -v

INGESTING DOCUMENTS:
    from portfolio_tool.rag import DocumentManager
    dm = DocumentManager()
    dm.ingest("data/documents/NVDA_10K.pdf", ticker="NVDA")
    dm.ingest_folder()  # All documents

KEY ENVIRONMENT VARIABLES:
    OPENAI_API_KEY     - Required for embeddings and sentiment LLM
    ANTHROPIC_API_KEY  - Required for Claude router (if used)
    USE_MOCK_QUOTA=True - Skip API quota tracking in tests

COMMON ISSUES:
    "No portfolio specified" → Use /use 1 or specify portfolio in query
    "No covariance matrix" → DataAgent must run before OptimizationAgent
    "No documents indexed" → Run /ingestall or dm.ingest_folder()
    "Fed scraper failed" → Website structure may have changed
    "Router timeout" → Complex prompts may need simpler phrasing

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
    """What agents to run? (Phase 6.6 + 6.7)"""
    OPTIMIZATION = "optimization"
    MACRO_ANALYSIS = "macro_analysis"
    REBALANCING = "rebalancing"
    BACKTEST = "backtest"
    DATA_FETCH = "data_fetch"
    RISK_ANALYSIS = "risk_analysis"
    DATA_MANAGEMENT = "data_management"
    PORTFOLIO_MGMT = "portfolio_mgmt"
    DOCUMENT_SEARCH = "document_search"  # NEW Phase 6.7
    COMBINED = "combined"                 # NEW Phase 6.7 (multi-agent)
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

class DocumentType(str, Enum):
    """Document types for RAG (Phase 6.7)"""
    SEC_10K = "10k"
    SEC_10Q = "10q"
    EARNINGS = "earnings"
    FED_MINUTES = "fed_minutes"
    RESEARCH = "research"
    OTHER = "other"

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
    key_risks: List[str]                 # Top risk factors (may include [DOC] prefix)
    trade_required: bool                 # Explicit yes/no
    trigger: str                         # What prompted this assessment
    document_citations: List[Dict]       # NEW Phase 6.7: [{"text": "...", "source": "..."}]

@dataclass
class RiskAssessment:
    """Structured risk evaluation - runs BEFORE optimization."""
    status: RiskStatus
    hhi_score: float                     # Concentration (0-1)
    drivers: List[str]                   # Risk drivers
    breaches: List[str]                  # Limit breaches

@dataclass
class DocumentInsights:
    """Insights extracted from documents via RAG (Phase 6.7)"""
    sources: List[str]                   # Document filenames
    key_findings: List[str]              # Main points extracted
    risk_factors: List[str]              # Risks mentioned in docs
    fed_sentiment: Optional[Dict]        # {score, confidence, method}
    citations: List[Dict]                # [{text, source}]
    has_relevant_content: bool           # Whether search found anything

@dataclass
class PortfolioConstraints:
    """Investment constraints for optimization."""
    min_weight: float = 0.0
    max_weight: float = 0.40
    max_volatility: Optional[float] = None
    long_only: bool = True
