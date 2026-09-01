# src/portfolio_tool/tools/portfolio_tools.py
# Purpose: LangChain tools for portfolio management
# Layer: Agent Interface - Wraps PortfolioManager for agent access
#
# DESIGN PRINCIPLES:
# - Tools are thin wrappers around PortfolioManager
# - All tools return structured dicts with success/error
# - No business logic here - just interface

from typing import Dict, Any, Optional, List
from langchain_core.tools import tool

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.portfolio_manager import PortfolioManager


# =============================================================================
# SINGLETON PORTFOLIO MANAGER
# =============================================================================

_portfolio_manager: Optional[PortfolioManager] = None


def _get_portfolio_manager() -> PortfolioManager:
    """Get or create singleton PortfolioManager."""
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioManager()
    return _portfolio_manager


# =============================================================================
# READ TOOLS (Query portfolios)
# =============================================================================

@tool
def list_portfolios() -> Dict[str, Any]:
    """
    List all portfolios in the database.
    Use this to see what portfolios exist before performing operations.
    
    Returns:
        Dict with success status and list of portfolios (id, name, description).
    """
    try:
        pm = _get_portfolio_manager()
        portfolios = pm.list_portfolios()
        
        if not portfolios:
            return {
                "success": True,
                "message": "No portfolios found. Use create_portfolio to create one.",
                "portfolios": [],
                "count": 0
            }
        
        return {
            "success": True,
            "message": f"Found {len(portfolios)} portfolio(s).",
            "portfolios": portfolios,
            "count": len(portfolios)
        }
    except Exception as e:
        return {"success": False, "error": f"Error listing portfolios: {str(e)}"}


@tool
def get_portfolio_details(portfolio_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific portfolio.
    
    Args:
        portfolio_id: The ID of the portfolio to retrieve.
    
    Returns:
        Dict with portfolio details (name, description, created_at, etc.)
    """
    try:
        pm = _get_portfolio_manager()
        portfolio = pm.get_portfolio(portfolio_id)
        
        if not portfolio:
            return {
                "success": False,
                "error": f"Portfolio with ID {portfolio_id} not found."
            }
        
        return {
            "success": True,
            "portfolio": portfolio
        }
    except Exception as e:
        return {"success": False, "error": f"Error getting portfolio: {str(e)}"}


@tool
def get_portfolio_holdings(portfolio_id: int) -> Dict[str, Any]:
    """
    Get all holdings (positions) in a portfolio.
    Use this to see what assets are in a portfolio and their quantities.
    
    Args:
        portfolio_id: The ID of the portfolio.
    
    Returns:
        Dict with list of holdings (ticker, quantity, average_price, etc.)
    """
    try:
        pm = _get_portfolio_manager()
        
        # First check if portfolio exists
        portfolio = pm.get_portfolio(portfolio_id)
        if not portfolio:
            return {
                "success": False,
                "error": f"Portfolio with ID {portfolio_id} not found."
            }
        
        holdings = pm.get_holdings(portfolio_id)
        tickers = pm.get_portfolio_tickers(portfolio_id)
        
        return {
            "success": True,
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.get("name", "Unknown"),
            "holdings": holdings,
            "tickers": tickers,
            "count": len(holdings)
        }
    except Exception as e:
        return {"success": False, "error": f"Error getting holdings: {str(e)}"}


@tool
def get_portfolio_summary(portfolio_id: int) -> Dict[str, Any]:
    """
    Get a comprehensive summary of a portfolio including value and allocation.
    
    Args:
        portfolio_id: The ID of the portfolio.
    
    Returns:
        Dict with portfolio summary (total value, holdings, allocation percentages).
    """
    try:
        pm = _get_portfolio_manager()
        
        # Check if portfolio exists
        portfolio = pm.get_portfolio(portfolio_id)
        if not portfolio:
            return {
                "success": False,
                "error": f"Portfolio with ID {portfolio_id} not found."
            }
        
        summary = pm.get_portfolio_summary(portfolio_id)
        
        if not summary:
            return {
                "success": False,
                "error": f"Could not generate summary for portfolio {portfolio_id}."
            }
        
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        return {"success": False, "error": f"Error getting summary: {str(e)}"}


# =============================================================================
# WRITE TOOLS (Modify portfolios)
# =============================================================================

@tool
def create_portfolio(name: str, description: str = "") -> Dict[str, Any]:
    """
    Create a new portfolio.
    
    Args:
        name: Name of the portfolio (e.g., "Retirement Fund", "Tech Growth")
        description: Optional description of the portfolio's purpose.
    
    Returns:
        Dict with success status and new portfolio ID.
    """
    try:
        pm = _get_portfolio_manager()
        
        if not name or not name.strip():
            return {
                "success": False,
                "error": "Portfolio name cannot be empty."
            }
        
        portfolio_id = pm.create_portfolio(
            name=name.strip(),
            description=description.strip() if description else ""
        )
        
        return {
            "success": True,
            "message": f"Portfolio '{name}' created successfully.",
            "portfolio_id": portfolio_id
        }
    except Exception as e:
        return {"success": False, "error": f"Error creating portfolio: {str(e)}"}


@tool
def add_holding_to_portfolio(
    portfolio_id: int, 
    ticker: str, 
    quantity: float, 
    average_price: float
) -> Dict[str, Any]:
    """
    Add a new holding (position) to a portfolio.
    
    Args:
        portfolio_id: The ID of the portfolio.
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT').
        quantity: Number of shares.
        average_price: Average purchase price per share.
    
    Returns:
        Dict with success status and holding details.
    """
    try:
        pm = _get_portfolio_manager()
        
        # Validate inputs
        if quantity <= 0:
            return {"success": False, "error": "Quantity must be positive."}
        if average_price <= 0:
            return {"success": False, "error": "Average price must be positive."}
        
        # Check portfolio exists
        portfolio = pm.get_portfolio(portfolio_id)
        if not portfolio:
            return {
                "success": False,
                "error": f"Portfolio with ID {portfolio_id} not found."
            }
        
        # Add holding
        holding_id = pm.add_holding(
            portfolio_id=portfolio_id,
            ticker=ticker.upper().strip(),
            quantity=quantity,
            average_price=average_price
        )
        
        return {
            "success": True,
            "message": f"Added {quantity} shares of {ticker.upper()} to portfolio.",
            "holding_id": holding_id,
            "portfolio_id": portfolio_id
        }
    except Exception as e:
        return {"success": False, "error": f"Error adding holding: {str(e)}"}


@tool
def update_portfolio_holding(
    holding_id: int,
    quantity: Optional[float] = None,
    average_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    Update an existing holding's quantity or average price.
    
    Args:
        holding_id: The ID of the holding to update.
        quantity: New quantity (optional).
        average_price: New average price (optional).
    
    Returns:
        Dict with success status.
    """
    try:
        pm = _get_portfolio_manager()
        
        if quantity is not None and quantity <= 0:
            return {"success": False, "error": "Quantity must be positive."}
        if average_price is not None and average_price <= 0:
            return {"success": False, "error": "Average price must be positive."}
        
        success = pm.update_holding(
            holding_id=holding_id,
            quantity=quantity,
            average_price=average_price
        )
        
        if success:
            return {
                "success": True,
                "message": f"Holding {holding_id} updated successfully."
            }
        else:
            return {
                "success": False,
                "error": f"Could not update holding {holding_id}. It may not exist."
            }
    except Exception as e:
        return {"success": False, "error": f"Error updating holding: {str(e)}"}


@tool
def remove_holding_from_portfolio(holding_id: int) -> Dict[str, Any]:
    """
    Remove a holding from a portfolio.
    
    Args:
        holding_id: The ID of the holding to remove.
    
    Returns:
        Dict with success status.
    """
    try:
        pm = _get_portfolio_manager()
        
        success = pm.delete_holding(holding_id)
        
        if success:
            return {
                "success": True,
                "message": f"Holding {holding_id} removed successfully."
            }
        else:
            return {
                "success": False,
                "error": f"Could not remove holding {holding_id}. It may not exist."
            }
    except Exception as e:
        return {"success": False, "error": f"Error removing holding: {str(e)}"}


@tool
def delete_portfolio(portfolio_id: int) -> Dict[str, Any]:
    """
    Delete a portfolio and all its holdings.
    WARNING: This action cannot be undone!
    
    Args:
        portfolio_id: The ID of the portfolio to delete.
    
    Returns:
        Dict with success status.
    """
    try:
        pm = _get_portfolio_manager()
        
        # Check portfolio exists first
        portfolio = pm.get_portfolio(portfolio_id)
        if not portfolio:
            return {
                "success": False,
                "error": f"Portfolio with ID {portfolio_id} not found."
            }
        
        portfolio_name = portfolio.get("name", "Unknown")
        
        success = pm.delete_portfolio(portfolio_id)
        
        if success:
            return {
                "success": True,
                "message": f"Portfolio '{portfolio_name}' (ID: {portfolio_id}) deleted successfully."
            }
        else:
            return {
                "success": False,
                "error": f"Could not delete portfolio {portfolio_id}."
            }
    except Exception as e:
        return {"success": False, "error": f"Error deleting portfolio: {str(e)}"}


# =============================================================================
# HELPER TOOLS (For agent decision making)
# =============================================================================

@tool
def check_portfolio_exists(portfolio_id: int) -> Dict[str, Any]:
    """
    Quick check if a portfolio exists.
    
    Args:
        portfolio_id: The ID to check.
    
    Returns:
        Dict with exists boolean and basic info if found.
    """
    try:
        pm = _get_portfolio_manager()
        portfolio = pm.get_portfolio(portfolio_id)
        
        if portfolio:
            return {
                "success": True,
                "exists": True,
                "portfolio_id": portfolio_id,
                "name": portfolio.get("name")
            }
        else:
            return {
                "success": True,
                "exists": False,
                "portfolio_id": portfolio_id
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool  
def find_portfolio_by_name(name: str) -> Dict[str, Any]:
    """
    Find a portfolio by name (partial match).
    
    Args:
        name: Full or partial portfolio name to search for.
    
    Returns:
        Dict with matching portfolios.
    """
    try:
        pm = _get_portfolio_manager()
        all_portfolios = pm.list_portfolios()
        
        search_term = name.lower().strip()
        matches = [
            p for p in all_portfolios 
            if search_term in p.get("name", "").lower()
        ]
        
        if not matches:
            return {
                "success": True,
                "message": f"No portfolios found matching '{name}'.",
                "matches": [],
                "count": 0
            }
        
        return {
            "success": True,
            "message": f"Found {len(matches)} portfolio(s) matching '{name}'.",
            "matches": matches,
            "count": len(matches)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# TOOL COLLECTIONS
# =============================================================================

ALL_PORTFOLIO_TOOLS = [
    # Read
    list_portfolios,
    get_portfolio_details,
    get_portfolio_holdings,
    get_portfolio_summary,
    
    # Write
    create_portfolio,
    add_holding_to_portfolio,
    update_portfolio_holding,
    remove_holding_from_portfolio,
    delete_portfolio,
    
    # Helpers
    check_portfolio_exists,
    find_portfolio_by_name,
]

READ_PORTFOLIO_TOOLS = [
    list_portfolios,
    get_portfolio_details,
    get_portfolio_holdings,
    get_portfolio_summary,
    check_portfolio_exists,
    find_portfolio_by_name,
]

WRITE_PORTFOLIO_TOOLS = [
    create_portfolio,
    add_holding_to_portfolio,
    update_portfolio_holding,
    remove_holding_from_portfolio,
    delete_portfolio,
]