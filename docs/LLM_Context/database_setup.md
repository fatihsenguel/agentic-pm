# FILE: src/portfolio_tool/database_setup.py
# PURPOSE: SQLAlchemy Models. Defines the tables, relationships, and constraints.
# PRINCIPLE: Normalized schema with strong constraints for data integrity.

class Asset(Base):
    """The central entity. Represents a stock, ETF, etc."""
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True) # e.g. "AAPL"
    
    # Relationships
    daily_prices = relationship('DailyPrice', back_populates='asset')
    fundamentals = relationship('Fundamentals', uselist=False)
    financial_statements = relationship('FinancialStatement')

class DailyPrice(Base):
    """OHLCV Data. High volume."""
    __tablename__ = 'daily_prices'
    # Composite Unique Key ensures Idempotency (Asset + Date)
    __table_args__ = (UniqueConstraint('asset_id', 'date', name='_asset_date_uc'),)
    
    date = Column(Date, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer)

class FinancialStatement(Base):
    """Deep fundamental data (Income, Balance Sheet, Cash Flow)."""
    __tablename__ = "financial_statements"
    # Unique Key: Asset + Date + ReportType (income) + PeriodType (annual)
    __table_args__ = (UniqueConstraint("asset_id", "date", "report_type", "period_type"),)
    
    report_type = Column(String(32)) # "income_statement"
    revenue = Column(Float)
    net_income = Column(Float)
    free_cash_flow = Column(Float)

class MacroData(Base):
    """
    NEW: Stores VIX, Yields, etc. for MacroAgent.
    """
    __tablename__ = 'macro_data'
    # Unique Key: Date + Indicator
    __table_args__ = (UniqueConstraint('date', 'indicator', name='_macro_date_indicator_uc'),)
    
    date = Column(Date, nullable=False)
    indicator = Column(String(50), nullable=False) # "VIX", "TNX_10Y"
    value = Column(Float, nullable=False)

class ApiCallLog(Base):
    """Observability: Logs every API call for cost/quota tracking."""
    __tablename__ = 'api_call_logs'
    provider_name = Column(String(100))
    credits_consumed = Column(Integer, default=1)
    success = Column(Boolean)

def get_session() -> Session:
    """Returns a new database session."""
    pass