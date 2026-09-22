# src/portfolio_tool/database_setup.py
import sys
import os

import enum

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, BigInteger, Enum, Boolean, JSON, Index, Text, text
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
import datetime

# Where the database lives is policy, so it comes from config rather than being
# computed here. config.resolve_database_url anchors a relative SQLite path to
# the project root, which is what the hardcoded path did.
from config import config

DATABASE_URL = config.database.url

print(f"DEBUG: Connecting to the database at {DATABASE_URL}")

engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()


# --- 2. Table definitions (models) ---
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
    # 'share' or 'fund'. IPS-4.2 and 4.3 count directly held shares only, so
    # the checker needs to know and raises when this is NULL rather than guess
    # (migration 05034c6316c8). Written by seed_portfolio.py.
    instrument_type = Column(String(10), nullable=True)
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

    # When was the last time we fetched daily prices?
    last_price_fetch_time = Column(DateTime, nullable=True)

    # How far back have we actually asked the provider for prices?
    earliest_price_start = Column(Date, nullable=True)

    # Further fetch timestamps go here as they are needed, e.g.
    # last_dividends_fetch_time.

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

    # Where the close came from: the provider's name, written by the fetch
    # (expected_values.md D17, D19, Part 9). Required and defaulted nowhere,
    # as on fx_rates: a close whose origin is unknown is a claim nobody made.
    source = Column(String(50), nullable=False)

    asset = relationship('Asset', back_populates='daily_prices')
    __table_args__ = (UniqueConstraint('asset_id', 'date', name='_asset_date_uc'),)
    def __repr__(self):
        return f"<DailyPrice(asset_ticker='{self.asset.ticker}', date={self.date}, close={self.close})>"

class FxRate(Base):
    """
    One spot rate for one day: a price source like a close (expected_values.md D17).

    `rate` is units of `base` per one unit of `quote`: with base EUR and
    quote USD, 0.85 is 0.85 euros per dollar, and a foreign holding's value
    in the base currency is quantity x price x rate on the price's as-of
    date (D16). Every column is required and none is defaulted: a rate with
    no date is not a price source, and a rate with no source is a claim
    nobody made. One row per (base, quote, date). Nothing here or in the
    lookup (quant/fx.py) falls back to yesterday's row or to 1; a missing
    rate raises.
    """
    __tablename__ = 'fx_rates'
    id = Column(Integer, primary_key=True)
    base = Column(String(3), nullable=False)
    quote = Column(String(3), nullable=False)
    date = Column(Date, nullable=False)
    rate = Column(Float, nullable=False)
    source = Column(String(50), nullable=False)
    __table_args__ = (UniqueConstraint('base', 'quote', 'date', name='_fx_base_quote_date_uc'),)

    def __repr__(self):
        return f"<FxRate({self.base}/{self.quote} {self.date}: {self.rate})>"

class FiledFact(Base):
    """
    One figure as a filer filed it, in one filing (expected_values.md Parts 12
    and 13): the EDGAR provider's record as stored.

    `value` is text holding exactly the digits EDGAR sent; SQLite has no exact
    decimal type and a float returns 0.241 as 0.24099999... The reader turns
    it into a Decimal. `start` is empty for an instant; `fy`, `fp` and `frame`
    are the filing's labels, provenance and never a key (D26, D31), and empty
    where EDGAR leaves them empty. Everything else is required and nothing is
    defaulted: a figure with no filing, no date or no source is a claim nobody
    made.

    The company is its EDGAR number, not an assets row: a watchlist company
    is not held. The key is D26's (tag, start, end, accn) per company, as two
    partial unique indexes, because SQLite never counts two empty `start`
    values as equal inside a unique constraint and a plain one would store an
    instant twice. A restatement is a second row under a new accession;
    nothing is overwritten.
    """
    __tablename__ = 'filed_facts'
    id = Column(Integer, primary_key=True)
    cik = Column(Integer, nullable=False)
    tag = Column(String(200), nullable=False)
    unit = Column(String(20), nullable=False)
    start = Column(Date, nullable=True)
    end = Column(Date, nullable=False)
    value = Column(Text, nullable=False)
    accn = Column(String(20), nullable=False)
    fy = Column(Integer, nullable=True)
    fp = Column(String(2), nullable=True)
    form = Column(String(10), nullable=False)
    filed = Column(Date, nullable=False)
    frame = Column(String(20), nullable=True)
    source = Column(String(50), nullable=False)
    __table_args__ = (
        Index('_filed_fact_instant_uc', 'cik', 'tag', 'end', 'accn',
              unique=True, sqlite_where=text('start IS NULL')),
        Index('_filed_fact_duration_uc', 'cik', 'tag', 'start', 'end', 'accn',
              unique=True, sqlite_where=text('start IS NOT NULL')),
    )

    def __repr__(self):
        return f"<FiledFact(cik={self.cik}, tag='{self.tag}', end={self.end}, accn='{self.accn}')>"

class FiledFetchMetadata(Base):
    """
    The filings fetch's cache record, one row per company.

    A company-facts document is the company's whole history, so the only fact
    to keep is when it was last fetched: for the interval rule
    (filings_fetch_interval_days in config.toml), and as the pull date an
    answer states. Written only after a fetch has returned, so the time is
    required, where fx_fetch_metadata's is filled after the row exists; a
    fetch that fails leaves no record and is retried.
    """
    __tablename__ = 'filed_fetch_metadata'
    cik = Column(Integer, primary_key=True, autoincrement=False)
    last_fetch_time = Column(DateTime, nullable=False)

class Filer(Base):
    """
    One filer as EDGAR's submissions document states it (expected_values.md
    Part 13 C): its name, its SIC code and the code's description, with the
    date they were pulled.

    The document carries the current code only, no date and no history, so
    the row is the code as of `pulled_at`; a later pull that finds another
    code overwrites the row and moves the date (decision 49). `sic` and
    `sic_description` are empty where EDGAR leaves them empty; the screen
    stops on a block whose code is empty (D35). `name` and `pulled_at` are
    required and defaulted nowhere: the row is written only after a fetch
    has returned. `entityType`, `ownerOrg` and `fiscalYearEnd` are not
    stored; nothing consumes them.
    """
    __tablename__ = 'filers'
    cik = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(200), nullable=False)
    sic = Column(String(4), nullable=True)
    sic_description = Column(String(200), nullable=True)
    pulled_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<Filer(cik={self.cik}, sic='{self.sic}', pulled_at={self.pulled_at})>"

class TickerCik(Base):
    """
    One (ticker, CIK) pair as the SEC's published ticker file states it,
    with the date it was pulled (decision 29, question 50): the forward map
    from a ticker to the filer it names, which neither EDGAR document
    carries in that direction.

    The file is one document for every listed filer, so a refresh rewrites
    the whole table as the file now states it and moves every row's date; a
    ticker the file no longer carries leaves the table with the refresh.
    Keyed by ticker, since the provider refuses a file in which one ticker
    names two filers. Every column is required and defaulted nowhere: a row
    is written only after a fetch has returned. The file's company title is
    not stored; the filers row holds EDGAR's name.
    """
    __tablename__ = 'ticker_ciks'
    ticker = Column(String(10), primary_key=True)
    cik = Column(Integer, nullable=False)
    pulled_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<TickerCik(ticker='{self.ticker}', cik={self.cik}, pulled_at={self.pulled_at})>"

class FiledDocument(Base):
    """
    One filing's primary document as text (expected_values.md Part 16, D51),
    one row per accession, written once: an accession never changes, so
    there is no interval and no pull date.

    `text` is the whole document under D51, not its sections: the sectioner
    runs over it at read time, so a change to the sectioner needs no fetch.
    It is read by the sectioner and never published. `source` is the
    provider's name, the source a reading record states (Part 15 D47).

    The filer, the form and the filed date are not stored: the filing is
    named by the accession on filed_facts, and a second copy could disagree
    with the first. The file's name has no consumer once the text is here.
    Every column is required and defaulted nowhere: a row is written only
    after a fetch has returned and the text has been extracted.
    """
    __tablename__ = 'filed_documents'
    accn = Column(String(20), primary_key=True)
    text = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)

    def __repr__(self):
        return f"<FiledDocument(accn='{self.accn}', {len(self.text or '')} characters)>"

class DocumentReading(Base):
    """
    One reading of one section of a stored document, as the model supplied
    it (expected_values.md Part 15, D47): the cache, one row per accession,
    section, model and prompt version.

    `claims` is JSON text, the one to twelve entries of claim, quote and
    uncertainty that passed `reading.record`. They are read and written
    whole, and on a hit they go through `reading.record` again against the
    stored section, so a cached reading is held to the rule a fresh one is.
    `model` is the id the record keeps (decision 67). A reading that was
    refused leaves no row. When it was made and what it cost are not
    stored; nothing consumes them.
    """
    __tablename__ = 'document_readings'
    accn = Column(String(20), ForeignKey('filed_documents.accn'), primary_key=True)
    section = Column(String(10), primary_key=True)
    model = Column(String(100), primary_key=True)
    prompt_version = Column(String(64), primary_key=True)
    claims = Column(Text, nullable=False)

    def __repr__(self):
        return (f"<DocumentReading(accn='{self.accn}', section='{self.section}', "
                f"model='{self.model}')>")

class FxFetchMetadata(Base):
    """
    The rate fetch's cache record, one row per (base, quote).

    The same two facts asset_fetch_metadata keeps for prices, kept apart
    because a pair has no asset. Coverage is "how far back have we asked
    the provider" (`earliest_start`), never "do we hold a row on that
    date", which fails on every weekend and holiday; `last_fetch_time` is
    for the interval rule. Both nullable: the row is created before the
    first fetch and filled by it.
    """
    __tablename__ = 'fx_fetch_metadata'
    base = Column(String(3), primary_key=True)
    quote = Column(String(3), primary_key=True)
    last_fetch_time = Column(DateTime, nullable=True)
    earliest_start = Column(Date, nullable=True)

class Transaction(Base):
    """
    One ledger row: a buy or a sale of an asset in a portfolio.

    A row belongs to a portfolio (expected_values.md D14); holdings derive
    from rows (D13). `amount` is the settled figure in the portfolio's
    currency - what was paid on a buy, what was received on a sale, fees
    included (D11) - and is data, never computed from the other columns.
    `date` is the trade day, a Date with no default: a row without one is
    unstorable rather than stamped with today (migration 552ab8900332).
    `fees` is required with no default: a row without one is a free trade
    with a plausible face (migration 88d7b7afdce7).
    """
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False)
    type = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    fees = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    asset = relationship('Asset', back_populates='transactions')

class Dividend(Base):
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
    __tablename__ = 'corporate_actions'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False)
    action_type = Column(String(20), nullable=False)
    value = Column(String(50), nullable=False)
    asset = relationship('Asset', back_populates='corporate_actions')
    __table_args__ = (UniqueConstraint('asset_id', 'date', 'action_type', name='_asset_action_date_uc'),)

class SharesHistory(Base):
    __tablename__ = 'shares_history'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    date = Column(Date, nullable=False)
    shares = Column(BigInteger, nullable=False)
    asset = relationship('Asset', back_populates='shares_history')
    __table_args__ = (UniqueConstraint('asset_id', 'date', name='_asset_shares_date_uc'),)

class Fundamentals(Base):
    """
    A snapshot of the fundamentals.
    One row per asset (1:1).
    """
    __tablename__ = 'fundamentals'

    id = Column(Integer, primary_key=True)
    # unique=True enforces the 1:1 relationship
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, unique=True)
    
    market_cap = Column(BigInteger, nullable=True)
    forward_pe = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    trailing_eps = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # The relationship back to Asset
    asset = relationship('Asset', back_populates='fundamentals')

    def __repr__(self):
        return f"<Fundamentals(asset='{self.asset.ticker}', market_cap={self.market_cap})>"

class QuarterlyEarnings(Base):
    """
    The historical series of quarterly reports.
    Many rows per asset (1:N).
    """
    __tablename__ = 'quarterly_earnings'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    
    report_date = Column(Date, nullable=False)
    revenue = Column(BigInteger, nullable=True)
    basic_eps = Column(Float, nullable=True)
    
    # The relationship back to Asset
    asset = relationship('Asset', back_populates='quarterly_earnings')
    
    # Uniqueness: one row per asset and report date
    __table_args__ = (
        UniqueConstraint('asset_id', 'report_date', name='_asset_earnings_date_uc'),
    )

    def __repr__(self):
        return f"<QuarterlyEarnings(asset='{self.asset.ticker}', date={self.report_date})>"

class PipelineRunStatus(enum.Enum):
    """The status of a pipeline run."""
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class PipelineRun(Base):
    """
    One run of an orchestration script: the parent row of every log
    written during that run.
    """
    __tablename__ = 'pipeline_runs'
    
    id = Column(Integer, primary_key=True)
    script_name = Column(String(255), nullable=False, index=True)
    
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    status = Column(Enum(PipelineRunStatus), nullable=False, default=PipelineRunStatus.RUNNING)
    
    # Run metadata
    git_commit_hash = Column(String(40), nullable=True)
    config_hash = Column(String(64), nullable=True) # e.g. the SHA-256 of config.toml
    
    error_message = Column(String, nullable=True)
    
    # One PipelineRun has many ApiCallLogs
    api_calls = relationship('ApiCallLog', back_populates='pipeline_run', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<PipelineRun(id={self.id}, script='{self.script_name}', status='{self.status.value}')>"

class ApiQuota(Base):
    """
    The *current* consumption in one quota window: the table the quota
    manager updates atomically.
    """
    __tablename__ = 'api_quotas'

    id = Column(Integer, primary_key=True)

    # e.g. 'yfinance' or 'alphavantage'
    provider_name = Column(String(100), nullable=False)
    
    # The unique key of the time window, e.g. "daily_2025-11-10"
    bucket_key = Column(String(255), nullable=False, unique=True, index=True)
    
    calls_consumed = Column(Integer, nullable=False, default=0)
    
    # When this window began
    window_start_time = Column(DateTime(timezone=True), nullable=False)
    
    # When this counter was last raised
    last_updated = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<ApiQuota(bucket='{self.bucket_key}', consumed={self.calls_consumed})>"

class ApiCallLog(Base):
    """
    An immutable ledger of *every* API request, for debugging, auditing
    and performance analysis.
    """
    __tablename__ = 'api_call_logs'

    id = Column(Integer, primary_key=True)

    # Foreign key: the run this API call belongs to
    pipeline_run_id = Column(Integer, ForeignKey('pipeline_runs.id'), nullable=False, index=True)
    
    provider_name = Column(String(100), nullable=False, index=True)
    
    # e.g. '.info', '.history', '/v1/getData'
    endpoint_name = Column(String(255), nullable=True)
    
    # For which asset (optional, useful when debugging)
    asset_ticker = Column(String(20), nullable=True, index=True)
    
    # The time of the call
    call_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Success or failure (e.g. HTTP 200, 429, 500)
    http_status_code = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    
    # How many credits this call consumed (usually 1)
    credits_consumed = Column(Integer, nullable=False, default=1)
    
    # If an error occurred
    error_message = Column(String, nullable=True)
    
    # The relationship back to the parent run
    pipeline_run = relationship('PipelineRun', back_populates='api_calls')

    def __repr__(self):
        return f"<ApiCallLog(provider='{self.provider_name}', endpoint='{self.endpoint_name}', success={self.success})>"

class FinancialStatement(Base):
    """
    One complete financial statement (e.g. an annual income statement).
    One row per (asset, date, report_type, period_type).
    """
    __tablename__ = "financial_statements"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)

    # The header: identifies the report
    date = Column(Date, nullable=False, index=True)      # period end (e.g. 2024-12-31)
    report_type = Column(String(32), nullable=False)     # "income", "balance_sheet", "cash_flow"
    period_type = Column(String(16), nullable=False)     # "annual", "quarterly"
    # The provider's name, written by the fetch from its DTO. Required and
    # defaulted nowhere, as on daily_prices and fx_rates: a statement whose
    # origin is unknown is a claim nobody made.
    source = Column(String(32), nullable=False)

    # The golden columns: the standard metrics
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

    # The provider's raw dump (every line item as a dict)
    raw_json = Column(JSON, nullable=True)

    # The relationship back to Asset
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

# ==================== MACRO DATA ====================

class MacroData(Base):
    """
    Time series: macro-economic indicator data.

    Daily values for:
    - VIX (volatility index)
    - Treasury yields (10Y, 2Y, 30Y, 3M)
    - USD index
    - Gold price

    The same shape as DailyPrice, (asset_id, date) becoming
    (indicator, date): a UniqueConstraint for ON CONFLICT UPDATE and
    indexes for fast queries.
    """
    __tablename__ = 'macro_data'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    indicator = Column(String(50), nullable=False)  # "VIX", "TNX_10Y", etc.
    value = Column(Float, nullable=False)
    # The provider's name, written by the fetch from its DTO, required and
    # defaulted nowhere, like daily_prices.source and fx_rates.source.
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=None)
    
    __table_args__ = (
        # The unique constraint for idempotent upserts, the same shape
        # as DailyPrice._asset_date_uc
        UniqueConstraint('date', 'indicator', name='_macro_date_indicator_uc'),
        
        # Indexes for frequent queries
        Index('ix_macro_indicator', 'indicator'),
        Index('ix_macro_date', 'date'),
        Index('ix_macro_indicator_date', 'indicator', 'date'),
    )

class Portfolio(Base):
    """
    User portfolio: a name, a currency, a cash balance. Its holdings are a
    view of its ledger rows.

    Example:
        Portfolio(name="Retirement 401k", currency="USD", ips_path="ips.toml")
    """
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    # No default (expected_values.md D15): every figure the system reports
    # is in this currency, so a portfolio that names none is an error,
    # not a dollar portfolio with a plausible face.
    currency = Column(String(10), nullable=False)
    # The policy this portfolio is checked against (DIRECTION.md Order 2,
    # item 4): the path of its ips.toml, relative to the project root or
    # absolute. Required and defaulted nowhere, like currency: the benchmark
    # portfolio names the committed file, a personal one names a file the
    # repository never sees, and a portfolio naming none is not checked
    # against the committed policy with a plausible face.
    ips_path = Column(String(500), nullable=False)
    cash_balance = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # What a portfolio holds is derived from its `transactions` rows
    # (expected_values.md D13); there is no holdings table.

    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}')>"





# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --- 3. Session Management ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session() -> Session:
    """Provides a new database session."""
    return SessionLocal()

def get_engine():
    """
    Accessor for the SQLAlchemy engine.
    
    Used by Pandas 'read_sql' and other direct connection needs.
    This provides a consistent interface rather than importing the global 'engine' variable.
    """
    return engine