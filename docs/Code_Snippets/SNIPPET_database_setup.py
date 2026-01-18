"""
SNIPPET: database_setup.py
PURPOSE: SQLAlchemy ORM models (database schema)
PATTERN: Relational schema with unique constraints for idempotent upserts
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, BigInteger, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

# ========== CORE DATA TABLES ==========

class Asset(Base):
    """
    Core entity: A tracked stock/asset.
    Relationships: 1:N with prices, earnings, financials, etc.
    """
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False)  # AAPL, MSFT
    name = Column(String(100), nullable=False)                # Apple Inc.
    asset_class = Column(String(50))                          # stock, ETF, crypto
    sector = Column(String(50))                               # Technology
    industry = Column(String(50))                             # Consumer Electronics
    country = Column(String(50))                              # USA
    currency = Column(String(10))                             # USD
    
    # Relationships (1:N)
    daily_prices = relationship('DailyPrice', back_populates='asset')
    quarterly_earnings = relationship('QuarterlyEarnings', back_populates='asset')
    financial_statements = relationship('FinancialStatement', back_populates='asset')
    fundamentals = relationship('Fundamentals', uselist=False, back_populates='asset')  # 1:1

class DailyPrice(Base):
    """
    Time-series: Daily OHLCV data.
    Unique constraint: (asset_id, date) → Idempotent upserts
    """
    __tablename__ = 'daily_prices'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    volume = Column(Integer)
    
    asset = relationship('Asset', back_populates='daily_prices')
    __table_args__ = (UniqueConstraint('asset_id', 'date', name='_asset_date_uc'),)

class QuarterlyEarnings(Base):
    """
    Time-series: Quarterly earnings reports.
    Unique constraint: (asset_id, report_date)
    """
    __tablename__ = 'quarterly_earnings'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    report_date = Column(Date, nullable=False)
    revenue = Column(BigInteger)
    basic_eps = Column(Float)
    
    asset = relationship('Asset', back_populates='quarterly_earnings')
    __table_args__ = (UniqueConstraint('asset_id', 'report_date', name='_asset_earnings_date_uc'),)

class FinancialStatement(Base):
    """
    Time-series: Financial statements (income/balance/cashflow).
    Unique constraint: (asset_id, date, report_type, period_type)
    Contains 35+ metrics (revenue, net_income, total_assets, etc.)
    """
    __tablename__ = 'financial_statements'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False)                    # Period end date
    report_type = Column(String(32), nullable=False)       # "income", "balance_sheet", "cash_flow"
    period_type = Column(String(16), nullable=False)       # "annual", "quarterly"
    source = Column(String(32), default="yfinance")
    
    # Golden columns (most important)
    revenue = Column(Float)
    net_income = Column(Float)
    eps = Column(Float)
    free_cash_flow = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    
    # 30+ additional columns for detailed financials:
    # Income: cost_of_revenue, r_and_d, sga, interest_expense, income_tax_expense
    # Balance: cash, accounts_receivable, inventory, ppe, debt, equity
    # Cashflow: operating_cf, capex, dividends_paid, stock_repurchases
    # ... (see full file for all 35+ columns)
    
    raw_json = Column(JSON)  # Store full provider response for extensibility
    
    asset = relationship('Asset', back_populates='financial_statements')
    __table_args__ = (UniqueConstraint('asset_id', 'date', 'report_type', 'period_type'),)

class Fundamentals(Base):
    """
    Snapshot: Current fundamental metrics (1:1 with Asset).
    Updated periodically (not time-series).
    """
    __tablename__ = 'fundamentals'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), unique=True)  # 1:1
    market_cap = Column(BigInteger)
    forward_pe = Column(Float)
    beta = Column(Float)
    trailing_eps = Column(Float)
    last_updated = Column(DateTime)
    
    asset = relationship('Asset', back_populates='fundamentals')

# ========== OPERATIONAL TABLES ==========

class AssetFetchMetadata(Base):
    """
    Tracks last fetch timestamps to avoid redundant API calls.
    One row per asset.
    """
    __tablename__ = 'asset_fetch_metadata'
    asset_id = Column(Integer, ForeignKey('assets.id'), primary_key=True)
    last_earnings_fetch_time = Column(DateTime)      # When did we last fetch earnings?
    last_earnings_report_date = Column(Date)         # Most recent earnings date in DB
    last_profile_fetch_time = Column(DateTime)       # When did we last fetch beta/sector?
    last_shares_fetch_time = Column(DateTime)

class PipelineRun(Base):
    """
    Audit log: Tracks execution of ETL jobs.
    Parent record for ApiCallLog entries.
    """
    __tablename__ = 'pipeline_runs'
    id = Column(Integer, primary_key=True)
    script_name = Column(String(255), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(20))  # RUNNING, SUCCESS, FAILED
    error_message = Column(String)
    
    api_calls = relationship('ApiCallLog', back_populates='pipeline_run')

class ApiQuota(Base):
    """
    Current API quota consumption (for rate limiting).
    Atomically updated via SELECT ... FOR UPDATE.
    """
    __tablename__ = 'api_quotas'
    id = Column(Integer, primary_key=True)
    provider_name = Column(String(100))              # "yfinance"
    bucket_key = Column(String(255), unique=True)    # "daily_2025-01-17"
    calls_consumed = Column(Integer, default=0)
    window_start_time = Column(DateTime)

class ApiCallLog(Base):
    """
    Immutable ledger: Every API call logged for audit/debugging.
    Linked to PipelineRun for traceability.
    """
    __tablename__ = 'api_call_logs'
    id = Column(Integer, primary_key=True)
    pipeline_run_id = Column(Integer, ForeignKey('pipeline_runs.id'))
    provider_name = Column(String(100))              # "yfinance"
    endpoint_name = Column(String(255))              # "history", "info"
    asset_ticker = Column(String(20))                # "AAPL"
    call_timestamp = Column(DateTime)
    http_status_code = Column(Integer)               # 200, 429, 500
    success = Column(Boolean, default=True)
    credits_consumed = Column(Integer, default=1)
    error_message = Column(String)
    
    pipeline_run = relationship('PipelineRun', back_populates='api_calls')

# ========== SESSION MANAGEMENT ==========
SessionLocal = sessionmaker(bind=engine)

def get_session():
    """Factory: Creates a new DB session."""
    return SessionLocal()

# ========== KEY DESIGN PATTERNS ==========
"""
1. UNIQUE CONSTRAINTS for idempotent upserts:
   - (asset_id, date) for DailyPrice
   - (asset_id, report_date) for QuarterlyEarnings
   - (asset_id, date, report_type, period_type) for FinancialStatement
   → ON CONFLICT UPDATE works automatically

2. RELATIONSHIPS:
   - Asset (1:N): daily_prices, earnings, financials
   - Asset (1:1): fundamentals (snapshot, not time-series)
   - PipelineRun (1:N): api_calls (audit trail)

3. METADATA TRACKING:
   - AssetFetchMetadata: Prevents redundant API calls
   - ApiCallLog: Immutable audit log
   - PipelineRun: ETL job execution tracking

4. EXTENSIBILITY:
   - FinancialStatement.raw_json: Store full provider response
   - Can add new columns without breaking existing code
   - Foreign keys cascade delete (clean orphaned data)

5. INDEXING (not shown but important):
   - Indexed: ticker, date, asset_id for fast queries
   - Unique constraints auto-create indexes
"""
