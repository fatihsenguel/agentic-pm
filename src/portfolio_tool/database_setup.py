# src/portfolio_tool/database_setup.py
import sys
import os

import enum

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, BigInteger, Enum, Boolean, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
import datetime

# Where the database lives is policy, so it comes from config rather than being
# computed here. config.resolve_database_url anchors a relative SQLite path to
# the project root, which is what the hardcoded path did.
from config import config

DATABASE_URL = config.database.url

print(f"DEBUG: Verbinde mit DB unter {DATABASE_URL}")

engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()


# --- 2. Tabellen-Definitionen (Models) ---
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
    # The provider's name, written by the fetch from its DTO. Required and
    # defaulted nowhere, as on daily_prices and fx_rates: a statement whose
    # origin is unknown is a claim nobody made.
    source = Column(String(32), nullable=False)

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
    # The provider's name, written by the fetch from its DTO, required and
    # defaulted nowhere, like daily_prices.source and fx_rates.source.
    source = Column(String(50), nullable=False)
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
    """Stellt eine neue DB-Session zur Verfügung."""
    return SessionLocal()

def get_engine():
    """
    Accessor for the SQLAlchemy engine.
    
    Used by Pandas 'read_sql' and other direct connection needs.
    This provides a consistent interface rather than importing the global 'engine' variable.
    """
    return engine