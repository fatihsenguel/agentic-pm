# src/portfolio_tool/tools/data_tools.py
# Layer 5: Agent Interface - Exposes Layer 3 (DataManager) as LangChain Tools
# 
# DESIGN PRINCIPLE:
# - WRITE Tools: Fetch raw data from APIs and store in DB
# - READ Tools: Query existing raw data from DB (no calculations!)
# - Calculated metrics (PE ratio, returns, etc.) belong in analytics_tools.py
#
# IMPORTANT: Uses singleton pattern for DataManager to avoid SQLite locking issues

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import threading

from langchain_core.tools import tool

# Internal modules
from portfolio_tool.database_setup import (
    get_session, 
    Asset, 
    DailyPrice, 
    Fundamentals,
    QuarterlyEarnings,
    FinancialStatement,
)
from portfolio_tool.data_manager import DataManager
from portfolio_tool.providers.yfinance_provider import YFinanceProvider
from portfolio_tool.services.quota_manager import DatabaseQuotaManager, MockQuotaManager

from sqlalchemy import func, desc


# =============================================================================
# SINGLETON DATA MANAGER (prevents SQLite locking issues)
# =============================================================================

class DataManagerSingleton:
    """
    Thread-safe singleton for DataManager.
    Ensures only ONE DataManager instance exists across all tool calls.
    This prevents SQLite "database is locked" errors.
    """
    _instance: Optional[DataManager] = None
    _lock = threading.Lock()
    _session = None
    
    @classmethod
    def get_instance(cls) -> DataManager:
        """Get or create the singleton DataManager instance."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._session = get_session()
                    
                    if os.environ.get("USE_MOCK_QUOTA") == "True":
                        quota_mgr = MockQuotaManager()
                    else:
                        quota_mgr = DatabaseQuotaManager(
                            pipeline_run_id=9999,
                            provider_name="yfinance",
                            daily_limit=2000
                        )
                    
                    provider = YFinanceProvider(quota_manager=quota_mgr)
                    cls._instance = DataManager(cls._session, provider)
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset the singleton (useful for testing)."""
        with cls._lock:
            if cls._session:
                cls._session.close()
            cls._instance = None
            cls._session = None


def _get_data_manager() -> DataManager:
    """Get the singleton DataManager instance."""
    return DataManagerSingleton.get_instance()


def _get_session():
    """Get session for READ-only operations."""
    # For read operations, we can use the singleton's session
    # or create a new one (reads don't cause locking issues)
    return get_session()


# =============================================================================
# WRITE TOOLS (Fetch from API & Store in DB)
# =============================================================================

@tool
def fetch_stock_prices(ticker: str, start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch and update daily stock prices for a given ticker symbol.
    Use this to get historical price data (Open, High, Low, Close, Volume).
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT').
        start_date: Optional start date in 'YYYY-MM-DD' format. 
                   If not provided, performs smart delta-update from last known date.
    
    Returns:
        Status dict with success, affected_count, and date range info.
    """
    try:
        dm = _get_data_manager()
        
        # Ensure asset exists (idempotent)
        asset = dm._get_or_create_asset(ticker, ticker, "stock")
        if not asset:
            return {
                "success": False, 
                "error": f"Could not find or create asset for ticker {ticker}"
            }

        # Parse date if provided
        parsed_date = None
        if start_date:
            try:
                parsed_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}

        result = dm.update_prices_for_asset(asset, start_date=parsed_date)
        return result.to_dict()
    
    except Exception as e:
        return {"success": False, "error": f"Error fetching prices: {str(e)}"}


@tool
def fetch_financial_statements(ticker: str, report_type: str = "balance_sheet") -> Dict[str, Any]:
    """
    Fetch financial statements (balance sheet, income statement, cash flow) for a company.
    
    Args:
        ticker: The stock ticker symbol.
        report_type: One of 'balance_sheet', 'income_statement', or 'cash_flow'.
    
    Returns:
        Status dict with success and number of statements fetched.
    """
    valid_types = ["balance_sheet", "income_statement", "cash_flow"]
    if report_type not in valid_types:
        return {"success": False, "error": f"Invalid report_type. Choose from: {valid_types}"}

    try:
        dm = _get_data_manager()
        asset = dm._get_or_create_asset(ticker, ticker, "stock")
        
        if not asset:
            return {"success": False, "error": f"Could not find or create asset for {ticker}"}
        
        result = dm.update_financial_statements_for_asset(
            asset, 
            report_type=report_type, 
            period_type="annual"
        )
        return result.to_dict()
    
    except Exception as e:
        return {"success": False, "error": f"Error fetching statements: {str(e)}"}


@tool
def fetch_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Fetch fundamental data (Beta, Market Cap, EPS) and company profile info (Sector, Industry).
    Use this to get an overview of what the company does and its key metrics.
    
    Args:
        ticker: The stock ticker symbol.
    
    Returns:
        Combined status of profile and fundamentals updates.
    """
    try:
        dm = _get_data_manager()
        asset = dm._get_or_create_asset(ticker, ticker, "stock")
        
        if not asset:
            return {
                "success": False, 
                "error": f"Could not find or create asset for {ticker}"
            }
        
        # Update asset info
        res_info = dm.force_update_asset_info(asset)
        
        # Update fundamentals
        res_fund = dm.update_fundamental_data(asset)
        
        return {
            "success": res_info.success and res_fund.success,
            "info_update": res_info.to_dict(),
            "fundamentals_update": res_fund.to_dict()
        }
    
    except Exception as e:
        return {"success": False, "error": f"Error fetching fundamentals: {str(e)}"}


@tool
def fetch_earnings_history(ticker: str) -> Dict[str, Any]:
    """
    Fetch historical quarterly earnings data (Revenue, EPS).
    Useful for analyzing growth trends over time.
    
    Args:
        ticker: The stock ticker symbol.
    
    Returns:
        Status dict with number of quarters fetched.
    """
    try:
        dm = _get_data_manager()
        asset = dm._get_or_create_asset(ticker, ticker, "stock")
        
        if not asset:
            return {"success": False, "error": f"Could not find or create asset for {ticker}"}
        
        result = dm.update_quarterly_earnings_for_asset(asset)
        return result.to_dict()
    
    except Exception as e:
        return {"success": False, "error": f"Error fetching earnings: {str(e)}"}


# =============================================================================
# READ TOOLS (Query existing data - NO API calls, NO calculations)
# =============================================================================

# Maximum records to prevent "Hot Potato" violations
MAX_QUERY_LIMIT = 100


@tool
def query_financial_data(
    data_type: str,
    ticker: str,
    limit: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    order: str = "desc"
) -> Dict[str, Any]:
    """
    Flexible database query for financial data. Returns raw data from the database.
    Use this to retrieve historical data for analysis.
    
    IMPORTANT: This does NOT fetch new data from APIs. Use fetch_* tools first if needed.
    
    Args:
        data_type: Type of data to query. One of:
            - 'prices': Daily OHLCV price data
            - 'earnings': Quarterly earnings (Revenue, EPS)
            - 'statements': Financial statements (Balance Sheet, Income, Cash Flow)
            - 'fundamentals': Current fundamental metrics (Beta, Market Cap)
        ticker: Stock ticker symbol (e.g., 'AAPL')
        limit: Maximum records to return (default 30, max 100). Use smaller limits for LLM context.
        start_date: Optional filter - only data from this date onwards (YYYY-MM-DD)
        end_date: Optional filter - only data up to this date (YYYY-MM-DD)
        order: Sort order - 'desc' (newest first, default) or 'asc' (oldest first)
    
    Returns:
        Dict with 'success', 'data' (list of records), 'count', and metadata.
    
    Examples:
        - Get last 30 days of AAPL prices: query_financial_data('prices', 'AAPL', limit=30)
        - Get 2024 earnings: query_financial_data('earnings', 'MSFT', start_date='2024-01-01', end_date='2024-12-31')
        - Get all financial statements: query_financial_data('statements', 'GOOGL', limit=50)
    """
    # Validate data_type
    valid_types = ['prices', 'earnings', 'statements', 'fundamentals']
    if data_type not in valid_types:
        return {
            "success": False,
            "error": f"Invalid data_type '{data_type}'. Must be one of: {valid_types}"
        }
    
    # Enforce limit cap (Hot Potato principle)
    if limit > MAX_QUERY_LIMIT:
        limit = MAX_QUERY_LIMIT
    if limit < 1:
        limit = 1
    
    # Parse dates
    parsed_start = None
    parsed_end = None
    try:
        if start_date:
            parsed_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}
    
    session = _get_session()
    
    try:
        # Find asset
        asset = session.query(Asset).filter(
            func.upper(Asset.ticker) == ticker.upper()
        ).first()
        
        if not asset:
            return {
                "success": False,
                "error": f"Asset '{ticker}' not found in database. Use fetch_stock_prices or fetch_fundamentals first."
            }
        
        # Route to appropriate query handler
        if data_type == 'prices':
            return _query_prices(session, asset, limit, parsed_start, parsed_end, order)
        elif data_type == 'earnings':
            return _query_earnings(session, asset, limit, parsed_start, parsed_end, order)
        elif data_type == 'statements':
            return _query_statements(session, asset, limit, parsed_start, parsed_end, order)
        elif data_type == 'fundamentals':
            return _query_fundamentals(session, asset)
        
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}
    finally:
        session.close()


def _query_prices(session, asset, limit: int, start_date, end_date, order: str) -> Dict[str, Any]:
    """Query daily price data."""
    query = session.query(DailyPrice).filter(DailyPrice.asset_id == asset.id)
    
    if start_date:
        query = query.filter(DailyPrice.date >= start_date)
    if end_date:
        query = query.filter(DailyPrice.date <= end_date)
    
    # Order
    if order == 'asc':
        query = query.order_by(DailyPrice.date.asc())
    else:
        query = query.order_by(DailyPrice.date.desc())
    
    # Get total count before limit
    total_count = query.count()
    
    # Apply limit
    records = query.limit(limit).all()
    
    data = []
    for r in records:
        data.append({
            "date": str(r.date),
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
            "market_cap": r.market_cap
        })
    
    return {
        "success": True,
        "ticker": asset.ticker,
        "data_type": "prices",
        "data": data,
        "count": len(data),
        "total_available": total_count,
        "truncated": total_count > limit,
        "order": order
    }


def _query_earnings(session, asset, limit: int, start_date, end_date, order: str) -> Dict[str, Any]:
    """Query quarterly earnings data."""
    query = session.query(QuarterlyEarnings).filter(QuarterlyEarnings.asset_id == asset.id)
    
    if start_date:
        query = query.filter(QuarterlyEarnings.report_date >= start_date)
    if end_date:
        query = query.filter(QuarterlyEarnings.report_date <= end_date)
    
    if order == 'asc':
        query = query.order_by(QuarterlyEarnings.report_date.asc())
    else:
        query = query.order_by(QuarterlyEarnings.report_date.desc())
    
    total_count = query.count()
    records = query.limit(limit).all()
    
    data = []
    for r in records:
        data.append({
            "report_date": str(r.report_date),
            "revenue": r.revenue,
            "basic_eps": r.basic_eps
        })
    
    return {
        "success": True,
        "ticker": asset.ticker,
        "data_type": "earnings",
        "data": data,
        "count": len(data),
        "total_available": total_count,
        "truncated": total_count > limit,
        "order": order
    }


def _query_statements(session, asset, limit: int, start_date, end_date, order: str) -> Dict[str, Any]:
    """Query financial statements."""
    query = session.query(FinancialStatement).filter(FinancialStatement.asset_id == asset.id)
    
    if start_date:
        query = query.filter(FinancialStatement.date >= start_date)
    if end_date:
        query = query.filter(FinancialStatement.date <= end_date)
    
    if order == 'asc':
        query = query.order_by(FinancialStatement.date.asc())
    else:
        query = query.order_by(FinancialStatement.date.desc())
    
    total_count = query.count()
    records = query.limit(limit).all()
    
    data = []
    for r in records:
        data.append({
            "date": str(r.date),
            "report_type": r.report_type,
            "period_type": r.period_type,
            # Key metrics (not all fields - keep response lean)
            "revenue": r.revenue,
            "net_income": r.net_income,
            "eps": r.eps,
            "total_assets": r.total_assets,
            "total_liabilities": r.total_liabilities,
            "free_cash_flow": r.free_cash_flow,
            "operating_cash_flow": r.operating_cash_flow
        })
    
    return {
        "success": True,
        "ticker": asset.ticker,
        "data_type": "statements",
        "data": data,
        "count": len(data),
        "total_available": total_count,
        "truncated": total_count > limit,
        "order": order
    }


def _query_fundamentals(session, asset) -> Dict[str, Any]:
    """Query current fundamentals (single record, no time series)."""
    fund = session.query(Fundamentals).filter(Fundamentals.asset_id == asset.id).first()
    
    if not fund:
        return {
            "success": True,
            "ticker": asset.ticker,
            "data_type": "fundamentals",
            "data": None,
            "message": "No fundamental data available. Use fetch_fundamentals first."
        }
    
    # Safe attribute access - only include fields that exist
    data = {}
    
    # Check each attribute safely using getattr with default None
    for field in ['market_cap', 'beta', 'forward_pe', 'trailing_pe', 'trailing_eps', 
                  'forward_eps', 'dividend_yield', 'profit_margin', 'book_value',
                  'price_to_book', 'last_updated']:
        value = getattr(fund, field, None)
        if value is not None:
            # Convert datetime to string if needed
            if field == 'last_updated' and value:
                data[field] = str(value)
            else:
                data[field] = value
    
    # If no fields were populated, show what we tried
    if not data:
        return {
            "success": True,
            "ticker": asset.ticker,
            "data_type": "fundamentals",
            "data": None,
            "message": "Fundamentals record exists but no data fields are populated."
        }
    
    return {
        "success": True,
        "ticker": asset.ticker,
        "data_type": "fundamentals",
        "data": data
    }


@tool
def get_asset_info(ticker: str) -> Dict[str, Any]:
    """
    Get information about an asset from the local database.
    This does NOT fetch new data - it only reads what's already stored.
    Use fetch_fundamentals first if you need fresh data.
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT').
    
    Returns:
        Asset details: name, sector, industry, raw fundamentals, and data coverage.
    """
    session = _get_session()
    
    try:
        # Find asset (case-insensitive)
        asset = session.query(Asset).filter(
            func.upper(Asset.ticker) == ticker.upper()
        ).first()
        
        if not asset:
            return {
                "success": False,
                "error": f"Asset '{ticker}' not found in database. Use fetch_stock_prices or fetch_fundamentals first."
            }
        
        # Get price data range
        price_stats = session.query(
            func.min(DailyPrice.date).label("first_date"),
            func.max(DailyPrice.date).label("last_date"),
            func.count(DailyPrice.id).label("count")
        ).filter(DailyPrice.asset_id == asset.id).first()
        
        # Get fundamentals snapshot (raw data only!)
        fundamentals = session.query(Fundamentals).filter(
            Fundamentals.asset_id == asset.id
        ).first()
        
        # Get earnings count
        earnings_count = session.query(func.count(QuarterlyEarnings.id)).filter(
            QuarterlyEarnings.asset_id == asset.id
        ).scalar()
        
        # Get financial statements count
        statements_count = session.query(func.count(FinancialStatement.id)).filter(
            FinancialStatement.asset_id == asset.id
        ).scalar()
        
        return {
            "success": True,
            "data": {
                "ticker": asset.ticker,
                "name": asset.name,
                "asset_class": asset.asset_class,
                "sector": asset.sector,
                "industry": asset.industry,
                "country": asset.country,
                "currency": asset.currency,
                "fundamentals": {
                    "market_cap": fundamentals.market_cap if fundamentals else None,
                    "beta": fundamentals.beta if fundamentals else None,
                    "forward_pe": fundamentals.forward_pe if fundamentals else None,
                    "trailing_eps": fundamentals.trailing_eps if fundamentals else None,
                    "last_updated": str(fundamentals.last_updated) if fundamentals else None
                } if fundamentals else None,
                "data_coverage": {
                    "price_data": {
                        "first_date": str(price_stats.first_date) if price_stats.first_date else None,
                        "last_date": str(price_stats.last_date) if price_stats.last_date else None,
                        "total_records": price_stats.count or 0
                    },
                    "quarterly_earnings_count": earnings_count or 0,
                    "financial_statements_count": statements_count or 0
                }
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}
    finally:
        session.close()


@tool
def list_tracked_assets() -> Dict[str, Any]:
    """
    List all assets currently tracked in the database.
    Returns a summary of each asset including ticker, name, sector, and data availability.
    Use this to see what data is already available before fetching new data.
    
    Returns:
        List of all tracked assets with their data coverage.
    """
    session = _get_session()
    
    try:
        assets = session.query(Asset).all()
        
        if not assets:
            return {
                "success": True,
                "message": "No assets tracked yet. Use fetch_stock_prices to add assets.",
                "data": [],
                "count": 0
            }
        
        asset_list = []
        for asset in assets:
            price_info = session.query(
                func.max(DailyPrice.date).label("last_date"),
                func.count(DailyPrice.id).label("count")
            ).filter(DailyPrice.asset_id == asset.id).first()
            
            asset_list.append({
                "ticker": asset.ticker,
                "name": asset.name,
                "sector": asset.sector,
                "industry": asset.industry,
                "asset_class": asset.asset_class,
                "last_price_date": str(price_info.last_date) if price_info.last_date else None,
                "price_records": price_info.count or 0
            })
        
        asset_list.sort(key=lambda x: x["ticker"])
        sectors = list(set(a["sector"] for a in asset_list if a["sector"]))
        
        return {
            "success": True,
            "data": asset_list,
            "count": len(asset_list),
            "summary": {
                "total_assets": len(asset_list),
                "sectors": sectors,
                "assets_with_price_data": sum(1 for a in asset_list if a["price_records"] > 0)
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}
    finally:
        session.close()


@tool
def get_latest_price(ticker: str) -> Dict[str, Any]:
    """
    Get the most recent price data for an asset from the database.
    This does NOT fetch new data - use fetch_stock_prices first if data is stale.
    
    Args:
        ticker: The stock ticker symbol.
    
    Returns:
        Latest price record (date, open, high, low, close, volume).
    """
    session = _get_session()
    
    try:
        asset = session.query(Asset).filter(
            func.upper(Asset.ticker) == ticker.upper()
        ).first()
        
        if not asset:
            return {
                "success": False,
                "error": f"Asset '{ticker}' not found. Use fetch_stock_prices first."
            }
        
        latest = session.query(DailyPrice).filter(
            DailyPrice.asset_id == asset.id
        ).order_by(DailyPrice.date.desc()).first()
        
        if not latest:
            return {
                "success": False,
                "error": f"No price data for '{ticker}'. Use fetch_stock_prices first."
            }
        
        return {
            "success": True,
            "data": {
                "ticker": asset.ticker,
                "date": str(latest.date),
                "open": latest.open,
                "high": latest.high,
                "low": latest.low,
                "close": latest.close,
                "volume": latest.volume,
                "market_cap": latest.market_cap
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}
    finally:
        session.close()




# =============================================================================
# TOOL COLLECTIONS
# =============================================================================

ALL_DATA_TOOLS = [
    fetch_stock_prices,
    fetch_financial_statements,
    fetch_fundamentals,
    fetch_earnings_history,
    get_asset_info,
    list_tracked_assets,
    get_latest_price,
    query_financial_data
]

FETCH_TOOLS = [
    fetch_stock_prices,
    fetch_financial_statements,
    fetch_fundamentals,
    fetch_earnings_history,
]

READ_TOOLS = [
    get_asset_info,
    list_tracked_assets,
    get_latest_price,
    query_financial_data
]