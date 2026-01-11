import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, date

# --- WICHTIG: Der "moderne" Import ---
from langchain_core.tools import tool

# Deine internen Module
from portfolio_tool.database_setup import get_session, Asset
from portfolio_tool.data_manager import DataManager
from portfolio_tool.providers.yfinance_provider import YFinanceProvider
from portfolio_tool.services.quota_manager import DatabaseQuotaManager, MockQuotaManager

def _get_data_manager():
    """
    Erstellt den DataManager. 
    Nutzt MockQuotaManager, wenn Environment Variable 'USE_MOCK_QUOTA' gesetzt ist.
    """
    session = get_session()
    
    # CHECK: Sollen wir mocken?
    if os.environ.get("USE_MOCK_QUOTA") == "True":
        quota_mgr = MockQuotaManager(session)
    else:
        # Standard: Echter Manager (für Produktion)
        # Hier nutzen wir Standardwerte für den interaktiven Modus
        quota_mgr = DatabaseQuotaManager(
            session=session,
            pipeline_run_id=9999,  # Dummy ID für Agenten
            provider_name="yfinance",
            daily_limit=2000
        )
    
    provider = YFinanceProvider(quota_manager=quota_mgr)
    return DataManager(session, provider)

# --- TOOL 1: Preise holen ---
@tool
def fetch_stock_prices(ticker: str, start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch and update daily stock prices for a given ticker symbol.
    Use this to get historical price data (Open, High, Low, Close, Volume).
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT').
        start_date: Optional start date in 'YYYY-MM-DD' format. If not provided, updates from last known date.
    """
    dm = _get_data_manager()
    
    # Asset sicherstellen (Idempotent)
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    if not asset:
        return {"success": False, "error": f"Could not find or create asset for ticker {ticker}"}

    # Datum parsen
    parsed_date = None
    if start_date:
        try:
            parsed_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}

    # Update durchführen (Deine DataManager Logik)
    result = dm.update_prices_for_asset(asset, start_date=parsed_date)
    
    # Resultat als Dictionary zurückgeben
    return result.to_dict()

# --- TOOL 2: Financial Statements ---
@tool
def fetch_financial_statements(ticker: str, report_type: str = "balance_sheet") -> Dict[str, Any]:
    """
    Fetch financial statements (balance sheet, income statement, cash flow) for a company.
    
    Args:
        ticker: The stock ticker symbol.
        report_type: One of 'balance_sheet', 'income_statement', or 'cash_flow'.
    """
    valid_types = ["balance_sheet", "income_statement", "cash_flow"]
    if report_type not in valid_types:
        return {"success": False, "error": f"Invalid report_type. Choose from: {valid_types}"}

    dm = _get_data_manager()
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    
    # Ruft deine Methode update_financial_statements_for_asset auf
    result = dm.update_financial_statements_for_asset(asset, report_type=report_type, period_type="annual")
    
    return result.to_dict()

# --- TOOL 3: Fundamentals (Beta, Sektor etc.) ---
@tool
def fetch_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Fetch fundamental data (like Beta, Sector, Industry) and company profile info.
    Useful for getting an overview of what the company does.
    """
    dm = _get_data_manager()
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    
    # Kombiniert zwei Calls für mehr Kontext
    res_info = dm.force_update_asset_info(asset)
    res_fund = dm.update_fundamental_data(asset)
    
    return {
        "info_update": res_info.to_dict(),
        "fundamentals_update": res_fund.to_dict()
    }

# --- TOOL 4: Earnings History ---
@tool
def fetch_earnings_history(ticker: str) -> Dict[str, Any]:
    """
    Fetch historical quarterly earnings data (Revenue, EPS).
    Useful for analyzing growth trends.
    """
    dm = _get_data_manager()
    asset = dm._get_or_create_asset(ticker, ticker, "stock")
    
    result = dm.update_quarterly_earnings_for_asset(asset)
    return result.to_dict()