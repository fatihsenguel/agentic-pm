# src/portfolio_tool/tools/data_tools.py
# Layer 5: Agent Interface - Exposes Layer 3 (DataManager) as LangChain Tools
# 
# DESIGN PRINCIPLE:
# - WRITE Tools: Fetch raw data from APIs and store in DB
# - READ Tools: Query existing raw data from DB (no calculations!)
# - Calculated metrics (PE ratio, returns, etc.) belong in analytics_tools.py



# THIS DOES NOT HAVE SINGLETON FUNCTIONALITY. THE NEW DATA_TOOLS.PY USES SINGLETON FUNCTIONALITY FOR THE MVP, SINCE SQLITE CANT USE PARALLEL DATABASE ACCESS (HAD A PROBLEM WITH THE PROMPT "FETCH DATA FOR PALANTIR", AND THE AGENT TRIED TO FETCH FUNDAMENTALS, PRICES ETC AT ONCE)

import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, date

from langchain_core.tools import tool

# Internal modules
from ..database_setup import (
    get_session, 
    Asset, 
    DailyPrice, 
    Fundamentals,
    QuarterlyEarnings,
    FinancialStatement,
    Dividend
)
from ..data_manager import DataManager
from ..providers.yfinance_provider import YFinanceProvider
from ..services.quota_manager import DatabaseQuotaManager, MockQuotaManager

from sqlalchemy import func


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def _get_data_manager():
    """
    Factory: Creates DataManager with session and quota manager.
    Uses MockQuotaManager when USE_MOCK_QUOTA env var is set.
    """
    session = get_session()
    
    if os.environ.get("USE_MOCK_QUOTA") == "True":
        quota_mgr = MockQuotaManager(session)
    else:
        quota_mgr = DatabaseQuotaManager(
            session=session,
            pipeline_run_id=9999,  # Dummy ID for agent interactions
            provider_name="yfinance",
            daily_limit=2000
        )
    
    provider = YFinanceProvider(quota_manager=quota_mgr)
    return DataManager(session, provider)


def _get_session():
    """Helper: Get session for READ-only operations (no provider needed)."""
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
    dm = _get_data_manager()
    
    # Ensure asset exists (idempotent)
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    if not asset:
        return {"success": False, "error": f"Could not find or create asset for ticker {ticker}"}

    # Parse date if provided
    parsed_date = None
    if start_date:
        try:
            parsed_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}

    result = dm.update_prices_for_asset(asset, start_date=parsed_date)
    return result.to_dict()


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

    dm = _get_data_manager()
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    
    result = dm.update_financial_statements_for_asset(
        asset, 
        report_type=report_type, 
        period_type="annual"
    )
    return result.to_dict()


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
    dm = _get_data_manager()
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    
    # Combine two updates for complete fundamental picture
    res_info = dm.force_update_asset_info(asset)
    res_fund = dm.update_fundamental_data(asset)
    
    return {
        "info_update": res_info.to_dict(),
        "fundamentals_update": res_fund.to_dict()
    }


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
    dm = _get_data_manager()
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    
    result = dm.update_quarterly_earnings_for_asset(asset)
    return result.to_dict()


# =============================================================================
# READ TOOLS (Query existing data - NO API calls, NO calculations)
# =============================================================================

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
                # Asset master data
                "ticker": asset.ticker,
                "name": asset.name,
                "asset_class": asset.asset_class,
                "sector": asset.sector,
                "industry": asset.industry,
                "country": asset.country,
                "currency": asset.currency,
                
                # Raw fundamentals (no calculated metrics!)
                "fundamentals": {
                    "market_cap": fundamentals.market_cap if fundamentals else None,
                    "beta": fundamentals.beta if fundamentals else None,
                    "forward_pe": fundamentals.forward_pe if fundamentals else None,
                    "trailing_eps": fundamentals.trailing_eps if fundamentals else None,
                    "last_updated": str(fundamentals.last_updated) if fundamentals else None
                } if fundamentals else None,
                
                # Data coverage summary
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
            # Get price stats per asset
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
        
        # Sort by ticker
        asset_list.sort(key=lambda x: x["ticker"])
        
        # Build summary
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
# TOOL COLLECTIONS (for easy import in agents)
# =============================================================================

# All available tools
ALL_DATA_TOOLS = [
    # Write/Fetch Tools (make API calls)
    fetch_stock_prices,
    fetch_financial_statements,
    fetch_fundamentals,
    fetch_earnings_history,
    # Read Tools (DB only, no API calls)
    get_asset_info,
    list_tracked_assets,
    get_latest_price,
]

# Grouped exports for selective import
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
]