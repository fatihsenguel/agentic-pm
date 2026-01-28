# src/portfolio_tool/database_setup.py
import sys
import os

import enum

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, BigInteger, Enum, Boolean, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
import datetime

# Database (portfolio.db) unabh vom pfad machen
base_dir = os.path.dirname(os.path.abspath(__file__))  # src/portfolio_tool/
src_dir = os.path.dirname(base_dir)                      # src/
project_root = os.path.dirname(src_dir)                  # E:\Programming\AGENTIC_FINANCE\
db_path = os.path.join(project_root, "data", "portfolio.db")

DATABASE_URL = f"sqlite:///{db_path}"

print(f"DEBUG: Verbinde mit DB unter {DATABASE_URL}")

engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()


# --- 2. Tabellen-Definitionen (Models) ---
# (Ihr Code von hier...
class Asset(Base):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    asset_class = Column(String(50))
    sector = Column(String(50), nullable=True)
    industry = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True)
    daily_prices = relationship('DailyPrice', back_populates='asset', cascade='all, delete-orphan')
    transactions = relationship('Transaction', back_populates='asset', cascade='all, delete-orphan')
    dividends = relationship('Dividend', back_populates='asset', cascade='all, delete-orphan')
    corporate_actions = relationship('CorporateAction', back_populates='asset', cascade='all, delete-orphan')
    shares_history = relationship('SharesHistory', back_populates='asset', cascade='all, delete-orphan')
    fundamentals = relationship('Fundamentals', uselist=False, back_populates='asset', cascade='all, delete-orphan')
    quarterly_earnings = relationship('QuarterlyEarnings', back_populates='asset', cascade='all, delete-orphan')
    financial_statements = relationship('FinancialStatement', back_populates='asset', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Asset(id={self.id}, ticker='{self.ticker}', name='{self.name}')>"
    
class AssetFetchMetadata(Base):
    """
    Tracks the last fetch timestamps for various data types per asset
    to avoid redundant API calls.
    """
    __tablename__ = "asset_fetch_metadata"
    
    asset_id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    
    # When_t was the last time we successfully fetched earnings from the provider?
    last_earnings_fetch_time = Column(DateTime, nullable=True) 
    
    # What is the date of the most recent earnings report we have stored?
    last_earnings_report_date = Column(Date, nullable=True)
    
    # When was the last time we fetched the company profile/info (beta, sector)?
    last_profile_fetch_time = Column(DateTime, nullable=True)
    
    # When was the last time we fetched the shares history?
    last_shares_fetch_time = Column(DateTime, nullable=True)

    # (Wir können hier bei Bedarf leicht weitere Zeitstempel hinzufügen, 
    #  z.B. last_dividends_fetch_time)

class DailyPrice(Base):
    __tablename__ = 'daily_prices'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    volume = Column(Integer)
    
    market_cap = Column(BigInteger, nullable=True)
    
    
    asset = relationship('Asset', back_populates='daily_prices')
    __table_args__ = (UniqueConstraint('asset_id', 'date', name='_asset_date_uc'),)
    def __repr__(self):
        return f"<DailyPrice(asset_ticker='{self.asset.ticker}', date={self.date}, close={self.close})>"

class Transaction(Base):
    # ... (Ihr Code) ...
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    type = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    fees = Column(Float, default=0.0)
    asset = relationship('Asset', back_populates='transactions')

class Dividend(Base):
    # ... (Ihr Code) ...
    __tablename__ = 'dividends'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    ex_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=True)
    declaration_date = Column(Date, nullable=True)
    asset = relationship('Asset', back_populates='dividends')
    __table_args__ = (UniqueConstraint('asset_id', 'ex_date', name='_asset_ex_date_uc'),)
    
class CorporateAction(Base):
    # ... (Ihr Code) ...
    __tablename__ = 'corporate_actions'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False)
    action_type = Column(String(20), nullable=False)
    value = Column(String(50), nullable=False)
    asset = relationship('Asset', back_populates='corporate_actions')
    __table_args__ = (UniqueConstraint('asset_id', 'date', 'action_type', name='_asset_action_date_uc'),)

class SharesHistory(Base):
    # ... (Ihr Code) ...
    __tablename__ = 'shares_history'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False)
    shares = Column(BigInteger, nullable=False)
    asset = relationship('Asset', back_populates='shares_history')
    __table_args__ = (UniqueConstraint('asset_id', 'date', name='_asset_shares_date_uc'),)

class Fundamentals(Base):
    """
    Speichert einen Schnappschuss der Fundamentaldaten.
    Dies ist eine 1:1-Beziehung zu Asset.
    """
    __tablename__ = 'fundamentals'
    
    id = Column(Integer, primary_key=True)
    # Wichtig: unique=True erzwingt die 1:1-Beziehung
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, unique=True)
    
    market_cap = Column(BigInteger, nullable=True)
    forward_pe = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    trailing_eps = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Beziehung zurück zu Asset
    asset = relationship('Asset', back_populates='fundamentals')

    def __repr__(self):
        return f"<Fundamentals(asset='{self.asset.ticker}', market_cap={self.market_cap})>"

class QuarterlyEarnings(Base):
    """
    Speichert die historische Zeitreihe der Quartalsberichte.
    Dies ist eine 1:N-Beziehung zu Asset.
    """
    __tablename__ = 'quarterly_earnings'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    
    report_date = Column(Date, nullable=False)
    revenue = Column(BigInteger, nullable=True)
    basic_eps = Column(Float, nullable=True)
    
    # Beziehung zurück zu Asset
    asset = relationship('Asset', back_populates='quarterly_earnings')
    
    # Einzigartigkeit: Ein Asset pro Berichtsdatum
    __table_args__ = (
        UniqueConstraint('asset_id', 'report_date', name='_asset_earnings_date_uc'),
    )

    def __repr__(self):
        return f"<QuarterlyEarnings(asset='{self.asset.ticker}', date={self.report_date})>"

class PipelineRunStatus(enum.Enum):
    """Definiert den Status einer Pipeline-Ausführung."""
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class PipelineRun(Base):
    """
    Erfasst eine einzelne Ausführung eines Orchestrierungs-Skripts (z.B. update_all_assets.py).
    Dies ist der "Eltern-Eintrag" für alle Logs, die während dieses Laufs entstehen.
    """
    __tablename__ = 'pipeline_runs'
    
    id = Column(Integer, primary_key=True)
    script_name = Column(String(255), nullable=False, index=True)
    
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    status = Column(Enum(PipelineRunStatus), nullable=False, default=PipelineRunStatus.RUNNING)
    
    # Metadaten (aus "Kurzfristig" in der Bibel)
    git_commit_hash = Column(String(40), nullable=True)
    config_hash = Column(String(64), nullable=True) # z.B. SHA-256 der config.toml
    
    error_message = Column(String, nullable=True)
    
    # Beziehung: Ein PipelineRun hat viele ApiCallLogs
    api_calls = relationship('ApiCallLog', back_populates='pipeline_run', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<PipelineRun(id={self.id}, script='{self.script_name}', status='{self.status.value}')>"

class ApiQuota(Base):
    """
    Speichert den *aktuellen* verbrauchten Stand für ein bestimmtes Quota-Fenster.
    Dies ist die Tabelle, die der 'CentralRateLimitManager' (Nächster Schritt) 
    atomar (SELECT ... FOR UPDATE) aktualisieren wird.
    """
    __tablename__ = 'api_quotas'
    
    id = Column(Integer, primary_key=True)
    
    # z.B. 'yfinance' oder 'alphavantage'
    provider_name = Column(String(100), nullable=False)
    
    # Eindeutiger Schlüssel für das Zeitfenster, z.B. "daily_2025-11-10"
    bucket_key = Column(String(255), nullable=False, unique=True, index=True)
    
    calls_consumed = Column(Integer, nullable=False, default=0)
    
    # Wann begann dieses Fenster (nützlich für die Logik)
    window_start_time = Column(DateTime(timezone=True), nullable=False)
    
    # Wann wurde dieser Zähler zuletzt erhöht?
    last_updated = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<ApiQuota(bucket='{self.bucket_key}', consumed={self.calls_consumed})>"

class ApiCallLog(Base):
    """
    Ein unveränderliches "Ledger" (Protokoll) *jeder* einzelnen API-Anfrage.
    Ermöglicht detailliertes Debugging, Auditing und Performance-Analyse.
    """
    __tablename__ = 'api_call_logs'
    
    id = Column(Integer, primary_key=True)
    
    # Fremdschlüssel: Zu welchem Lauf gehört dieser API-Aufruf?
    pipeline_run_id = Column(Integer, ForeignKey('pipeline_runs.id'), nullable=False, index=True)
    
    provider_name = Column(String(100), nullable=False, index=True)
    
    # z.B. '.info', '.history', '/v1/getData'
    endpoint_name = Column(String(255), nullable=True)
    
    # Für welches Asset? (Optional, aber sehr nützlich für Debugging)
    asset_ticker = Column(String(20), nullable=True, index=True)
    
    # Zeitstempel des Aufrufs
    call_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Erfolg oder Misserfolg (z.B. HTTP 200, 429, 500)
    http_status_code = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    
    # Wie viele "Credits" hat dieser Aufruf verbraucht (meistens 1)
    credits_consumed = Column(Integer, nullable=False, default=1)
    
    # Falls ein Fehler aufgetreten ist
    error_message = Column(String, nullable=True)
    
    # Beziehung zurück zum "Eltern-Lauf"
    pipeline_run = relationship('PipelineRun', back_populates='api_calls')

    def __repr__(self):
        return f"<ApiCallLog(provider='{self.provider_name}', endpoint='{self.endpoint_name}', success={self.success})>"

class FinancialStatement(Base):
    """
    Speichert einen vollständigen Finanzbericht (z.B. Income Statement annual).
    Eine Zeile pro (Asset, Date, report_type, period_type).
    """
    __tablename__ = "financial_statements"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)

    # "Header" – identifizieren den Report
    date = Column(Date, nullable=False, index=True)      # Periodenende (z.B. 2024-12-31)
    report_type = Column(String(32), nullable=False)     # "income", "balance_sheet", "cash_flow"
    period_type = Column(String(16), nullable=False)     # "annual", "quarterly"
    source = Column(String(32), nullable=False, default="yfinance")

    # Golden Columns – Standardmetriken
    revenue = Column(Float, nullable=True)
    net_income = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)
    free_cash_flow = Column(Float, nullable=True)

    total_assets = Column(Float, nullable=True)
    total_liabilities = Column(Float, nullable=True)

    # --- Income Statement Raw Data ---
    cost_of_revenue = Column(Float, nullable=True)
    research_and_development = Column(Float, nullable=True)
    selling_general_and_administrative = Column(Float, nullable=True)
    interest_expense = Column(Float, nullable=True)
    income_tax_expense = Column(Float, nullable=True)

    # --- Balance Sheet Raw Data ---
    cash_and_cash_equivalents = Column(Float, nullable=True)
    accounts_receivable = Column(Float, nullable=True)
    inventory = Column(Float, nullable=True)
    property_plant_equipment = Column(Float, nullable=True)
    accounts_payable = Column(Float, nullable=True)
    current_debt = Column(Float, nullable=True)
    long_term_debt = Column(Float, nullable=True)
    common_stock = Column(Float, nullable=True)
    retained_earnings = Column(Float, nullable=True)
    accumulated_other_comprehensive_income = Column(Float, nullable=True)

    # --- Cash Flow Statement Raw Data ---
    depreciation_and_amortization = Column(Float, nullable=True)
    stock_based_compensation = Column(Float, nullable=True)
    change_in_working_capital = Column(Float, nullable=True)
    capital_expenditure = Column(Float, nullable=True)
    dividends_paid = Column(Float, nullable=True)
    issuance_of_debt = Column(Float, nullable=True)
    repayment_of_debt = Column(Float, nullable=True)
    issuance_of_stock = Column(Float, nullable=True)
    repurchase_of_stock = Column(Float, nullable=True)
    operating_cash_flow = Column(Float, nullable=True)

    # Rohdump des Providers (alle Zeilen als Dict)
    raw_json = Column(JSON, nullable=True)

    # Beziehung zurück zu Asset
    asset = relationship("Asset", back_populates="financial_statements")

    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "date",
            "report_type",
            "period_type",
            name="_asset_financial_statement_uc",
        ),
    )

    def __repr__(self):
        return (
            f"<FinancialStatement(asset_id={self.asset_id}, "
            f"date={self.date}, report_type='{self.report_type}', "
            f"period_type='{self.period_type}')>"
        )

# ==================== NEUE TABELLE ====================

class MacroData(Base):
    """
    Time-series: Macro-economic indicator data.
    
    Speichert tägliche Werte für:
    - VIX (Volatility Index)
    - Treasury Yields (10Y, 2Y, 30Y, 3M)
    - USD Index
    - Gold price
    
    PATTERN:
    - Analog zu DailyPrice (asset_id, date) → (indicator, date)
    - UniqueConstraint für ON CONFLICT UPDATE
    - Indexed für schnelle Queries
    """
    __tablename__ = 'macro_data'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    indicator = Column(String(50), nullable=False)  # "VIX", "TNX_10Y", etc.
    value = Column(Float, nullable=False)
    source = Column(String(50), default="yfinance")
    created_at = Column(DateTime, default=None)
    
    __table_args__ = (
        # Unique constraint für idempotente Upserts
        # PATTERN: Gleich wie DailyPrice._asset_date_uc
        UniqueConstraint('date', 'indicator', name='_macro_date_indicator_uc'),
        
        # Indexes für häufige Queries
        Index('ix_macro_indicator', 'indicator'),
        Index('ix_macro_date', 'date'),
        Index('ix_macro_indicator_date', 'indicator', 'date'),
    )

class Portfolio(Base):
    """
    User portfolio - contains multiple asset holdings.
    
    Example:
        Portfolio(name="Retirement 401k", currency="USD")
    """
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    cash_balance = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationship to holdings
    holdings = relationship('PortfolioHolding', back_populates='portfolio', cascade='all, delete-orphan')
    decision_logs = relationship('DecisionLog', back_populates='portfolio', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}', holdings={len(self.holdings)})>"


class PortfolioHolding(Base):
    """
    Individual holding within a portfolio.
    
    Example:
        PortfolioHolding(portfolio_id=1, asset_id=5, quantity=100, average_price=450.0)
        # Means: 100 shares of asset #5, bought at avg price $450
    """
    __tablename__ = 'portfolio_holdings'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey('assets.id', ondelete='CASCADE'), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    portfolio = relationship('Portfolio', back_populates='holdings')
    asset = relationship('Asset')
    
    # Unique constraint: one holding per asset per portfolio
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'asset_id', name='_portfolio_asset_uc'),
    )
    
    def __repr__(self):
        return f"<PortfolioHolding(portfolio_id={self.portfolio_id}, asset_id={self.asset_id}, qty={self.quantity})>"


class DecisionLog(Base):
    """
    Audit trail of all PM decisions.
    
    Every portfolio decision (HOLD, TILT, REBALANCE, HEDGE) is logged here
    for auditability and analysis.
    
    Example:
        DecisionLog(
            portfolio_id=1,
            decision_type="HOLD",
            confidence=0.85,
            rationale="Portfolio drift within tolerance",
            trigger="user_request"
        )
    """
    __tablename__ = 'decision_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Decision details
    decision_type = Column(String(20), nullable=False)  # HOLD, TILT, REBALANCE, HEDGE
    confidence = Column(Float, nullable=False)
    rationale = Column(String(1000), nullable=True)
    trigger = Column(String(50), nullable=False)  # "user_request", "drift_threshold", "macro_change", "scheduled"
    
    # Risk context at time of decision
    risk_status = Column(String(20), nullable=True)  # ACCEPTABLE, ELEVATED, CRITICAL
    key_risks = Column(JSON, nullable=True)  # List of risk factors
    
    # Portfolio state at time of decision
    current_weights = Column(JSON, nullable=True)  # {"SPY": 0.4, "TLT": 0.3, ...}
    proposed_weights = Column(JSON, nullable=True)  # Target weights if action recommended
    max_drift = Column(Float, nullable=True)
    
    # Macro context
    macro_regime = Column(String(20), nullable=True)  # "neutral", "risk_off", "crisis"
    vix_level = Column(Float, nullable=True)
    
    # Execution tracking
    trade_required = Column(Boolean, nullable=False, default=False)
    executed = Column(Boolean, nullable=False, default=False)
    execution_timestamp = Column(DateTime, nullable=True)
    
    # User/session tracking
    request_id = Column(String(50), nullable=True)  # Links to the original request
    user_query = Column(String(500), nullable=True)  # What the user asked
    
    # Relationship to portfolio
    portfolio = relationship('Portfolio')
    
    __table_args__ = (
        Index('ix_decision_portfolio', 'portfolio_id'),
        Index('ix_decision_timestamp', 'timestamp'),
        Index('ix_decision_type', 'decision_type'),
    )
    
    def __repr__(self):
        return f"<DecisionLog(id={self.id}, portfolio={self.portfolio_id}, decision='{self.decision_type}', confidence={self.confidence})>"


class Document(Base):
    """
    Tracks all documents ingested into the RAG system.
    
    Phase: 6.7 - RAG Integration
    
    Purpose:
    - Deduplication via content_hash (don't re-index same document)
    - Metadata storage for filtering (ticker, doc_type, date)
    - Status tracking for processing pipeline
    - Links to ChromaDB collection
    
    Example:
        Document(
            filename="NVDA_Q3_2024_Earnings.pdf",
            doc_type="earnings",
            ticker="NVDA",
            source="user_upload",
            content_hash="abc123...",
            status="processed",
            chunk_count=42
        )
    """
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    
    # -------------------------------------------------------------------------
    # IDENTIFICATION
    # -------------------------------------------------------------------------
    filename = Column(String(255), nullable=False)
    doc_type = Column(String(50), nullable=False)  # earnings, 10k, 10q, fed_minutes, research, news, memo, other
    ticker = Column(String(20), nullable=True, index=True)  # Related security (NULL for macro docs)
    source = Column(String(50), nullable=False)  # sec_edgar, federal_reserve, user_upload, news_api, manual
    
    # -------------------------------------------------------------------------
    # CONTENT TRACKING
    # -------------------------------------------------------------------------
    content_hash = Column(String(64), unique=True, nullable=False)  # SHA256 for deduplication
    chunk_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    
    # -------------------------------------------------------------------------
    # DATES
    # -------------------------------------------------------------------------
    document_date = Column(Date, nullable=True)  # Date OF the document content
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)  # When we received it
    processed_date = Column(DateTime, nullable=True)  # When processing completed
    
    # -------------------------------------------------------------------------
    # STATUS
    # -------------------------------------------------------------------------
    status = Column(String(20), default="pending")  # pending, processing, processed, failed
    error_message = Column(String(500), nullable=True)
    
    # -------------------------------------------------------------------------
    # VECTOR STORE REFERENCE
    # -------------------------------------------------------------------------
    collection_name = Column(String(100), default="portfolio_documents")
    
    # -------------------------------------------------------------------------
    # EXTRACTED METADATA
    # -------------------------------------------------------------------------
    sections = Column(JSON, nullable=True)  # List of section headers found
    
    __table_args__ = (
        # Indexes for common query patterns
        Index('ix_doc_ticker', 'ticker'),
        Index('ix_doc_type', 'doc_type'),
        Index('ix_doc_ticker_type', 'ticker', 'doc_type'),
        Index('ix_doc_date', 'document_date'),
        Index('ix_doc_status', 'status'),
        Index('ix_doc_upload', 'upload_date'),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', ticker='{self.ticker}', status='{self.status}')>"



# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --- 3. Session Management ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session() -> Session:
    """Stellt eine neue DB-Session zur Verfügung."""
    return SessionLocal()

def get_engine():
    """
    Accessor for the SQLAlchemy engine.
    
    Used by Pandas 'read_sql' and other direct connection needs.
    This provides a consistent interface rather than importing the global 'engine' variable.
    """
    return engine