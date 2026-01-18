"""
SNIPPET: tools/data_tools.py
PURPOSE: LangChain tool wrappers for DataManager (Layer 5 → Layer 3)
PATTERN: Singleton + Thin wrappers (logic in DataManager, not tools)
"""

from langchain_core.tools import tool
from portfolio_tool.data_manager import DataManager
from portfolio_tool.providers.yfinance_provider import YFinanceProvider
from portfolio_tool.services.quota_manager import DatabaseQuotaManager

# ========== SINGLETON PATTERN ==========
class DataManagerSingleton:
    """
    Thread-safe singleton to prevent SQLite locking.
    ONE DataManager instance for ALL tool calls.
    """
    _instance: Optional[DataManager] = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> DataManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    session = get_session()
                    quota_mgr = DatabaseQuotaManager(pipeline_run_id=9999, daily_limit=2000)
                    provider = YFinanceProvider(quota_manager=quota_mgr)
                    cls._instance = DataManager(session, provider)
        return cls._instance

def _get_data_manager() -> DataManager:
    return DataManagerSingleton.get_instance()

# ========== WRITE TOOLS (Fetch API → Store DB) ==========

@tool
def fetch_stock_prices(ticker: str, start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch OHLCV data from API → upsert to DB.
    Smart delta-update: If no start_date, fetches from last DB entry.
    
    Returns: UpdateResult.to_dict() → {"success": True, "affected_count": 252, ...}
    """
    dm = _get_data_manager()
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    result = dm.update_prices_for_asset(asset, start_date=parsed_date)
    return result.to_dict()

@tool
def fetch_financial_statements(ticker: str, report_type: str = "balance_sheet") -> Dict[str, Any]:
    """
    Fetch financials (income/balance/cashflow) from API → upsert to DB.
    report_type: "balance_sheet" | "income_statement" | "cash_flow"
    
    Returns: UpdateResult.to_dict()
    """
    dm = _get_data_manager()
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    result = dm.update_financial_statements_for_asset(asset, report_type, "quarterly")
    return result.to_dict()

@tool
def fetch_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Fetch beta, market_cap, sector from API → upsert to DB.
    Returns: UpdateResult.to_dict()
    """
    dm = _get_data_manager()
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    result = dm.update_fundamental_data(asset, force_update=True)
    return result.to_dict()

@tool
def fetch_earnings_history(ticker: str) -> Dict[str, Any]:
    """
    Fetch quarterly earnings (EPS actual/estimate) from API → upsert to DB.
    Returns: UpdateResult.to_dict()
    """
    dm = _get_data_manager()
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    result = dm.update_earnings_for_asset(asset, force_update=True)
    return result.to_dict()

# ========== READ TOOLS (Query DB only, no API calls) ==========

@tool
def get_asset_info(ticker: str) -> Dict[str, Any]:
    """
    Read asset metadata from DB: name, sector, industry, currency.
    No API call. Returns QueryResult.to_dict()
    """
    session = get_session()
    asset = session.query(Asset).filter_by(ticker=ticker.upper()).first()
    if not asset:
        return {"success": False, "error": f"Asset {ticker} not found in database"}
    
    return {
        "success": True,
        "ticker": asset.ticker,
        "name": asset.name,
        "sector": asset.sector,
        "industry": asset.industry,
        "currency": asset.currency
    }

@tool
def list_tracked_assets() -> Dict[str, Any]:
    """
    List all assets in DB with their metadata.
    Returns: {"success": True, "assets": [{ticker, name, sector}, ...], "count": N}
    """
    session = get_session()
    assets = session.query(Asset).all()
    return {
        "success": True,
        "assets": [{"ticker": a.ticker, "name": a.name, "sector": a.sector} for a in assets],
        "count": len(assets)
    }

@tool
def get_latest_price(ticker: str) -> Dict[str, Any]:
    """
    Get most recent closing price from DB.
    Returns: {"success": True, "ticker": "AAPL", "price": 207.39, "date": "2026-01-14"}
    """
    session = get_session()
    asset = session.query(Asset).filter_by(ticker=ticker.upper()).first()
    latest = session.query(DailyPrice).filter_by(asset_id=asset.id)\
                    .order_by(DailyPrice.date.desc()).first()
    return {
        "success": True,
        "ticker": ticker.upper(),
        "price": float(latest.close),
        "date": latest.date.strftime("%Y-%m-%d")
    }

@tool
def query_financial_data(data_type: str, ticker: str, limit: int = 10) -> Dict[str, Any]:
    """
    Flexible query for financial data.
    data_type: "prices" | "earnings" | "balance_sheet" | "income_statement" | "cash_flow"
    
    Returns: {"success": True, "data": [{...}, {...}], "count": N}
    """
    session = get_session()
    asset = session.query(Asset).filter_by(ticker=ticker.upper()).first()
    
    if data_type == "prices":
        records = session.query(DailyPrice).filter_by(asset_id=asset.id)\
                         .order_by(DailyPrice.date.desc()).limit(limit).all()
        data = [{"date": r.date, "close": float(r.close), "volume": r.volume} for r in records]
    elif data_type == "earnings":
        records = session.query(QuarterlyEarnings).filter_by(asset_id=asset.id)\
                         .order_by(QuarterlyEarnings.report_date.desc()).limit(limit).all()
        data = [{"date": r.report_date, "revenue": r.revenue, "eps": float(r.basic_eps)} 
                for r in records]
    # ... similar for other types
    
    return {"success": True, "data": data, "count": len(data)}

# ========== TOOL COLLECTIONS ==========
ALL_DATA_TOOLS = [
    fetch_stock_prices,           # WRITE
    fetch_financial_statements,   # WRITE
    fetch_fundamentals,           # WRITE
    fetch_earnings_history,       # WRITE
    get_asset_info,               # READ
    list_tracked_assets,          # READ
    get_latest_price,             # READ
    query_financial_data,         # READ
]

# ========== KEY PATTERNS ==========
"""
1. SINGLETON: One DataManager for all tools (prevents SQLite locking)
2. THIN WRAPPERS: Tools just call DataManager methods, no logic here
3. WRITE vs READ: 
   - WRITE tools → API calls → UpdateResult
   - READ tools → DB queries → QueryResult
4. IDEMPOTENT: fetch_* can be called multiple times safely (upserts)
5. SMART DEFAULTS: fetch_stock_prices() auto-detects last DB date
"""
