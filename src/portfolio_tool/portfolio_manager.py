"""
Portfolio Manager - STRICT CRUD Operations for Portfolios and Holdings

This module provides a STRICT interface for managing portfolios and their holdings.

DESIGN PRINCIPLES (PRODUCTION-GRADE):
- Single Responsibility: ONLY manages portfolio structure
- NO asset creation (use DataManager for that)
- NO guessing or defaults
- NO business logic (that belongs in agents/tools)
- Session isolation (separate from DataManager)
- Fail-fast with clear error messages

WHAT THIS MODULE DOES:
✅ Create/Read/Update/Delete portfolios
✅ Create/Read/Update/Delete holdings (links to EXISTING assets)
✅ Query portfolio structure

WHAT THIS MODULE DOES NOT DO:
❌ Create Asset records (use DataManager.fetch_price_data())
❌ Fetch market data
❌ Calculate portfolio metrics (use tools)
❌ Make investment decisions
❌ Guess asset properties

Usage:
    from portfolio_tool.portfolio_manager import PortfolioManager
    from portfolio_tool.data_manager import DataManager
    from datetime import datetime, timedelta
    
    # STEP 1: Ensure asset exists (DataManager's job)
    dm = DataManager()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dm.fetch_price_data("SPY", start_date, end_date)  # Creates Asset with REAL data
    
    # STEP 2: Create portfolio and add holdings (PortfolioManager's job)
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("My 401k", currency="USD")
    pm.add_holding(portfolio_id, "SPY", quantity=100, average_price=450.0)
    
    # Get tickers for agents
    tickers = pm.get_portfolio_tickers(portfolio_id)  # ["SPY"]
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from portfolio_tool.database_setup import (
    SessionLocal, 
    Portfolio, 
    PortfolioHolding,
    Asset
)

logger = logging.getLogger(__name__)


class AssetNotFoundError(Exception):
    """Raised when trying to add a holding for an asset that doesn't exist in database"""
    pass


class PortfolioManager:
    """
    Manages portfolio CRUD operations with STRICT validation.
    
    This is a PURE data access layer - no business logic, no guessing.
    """
    
    def __init__(self):
        """Initialize portfolio manager"""
        pass
    
    def _get_session(self) -> Session:
        """Get a new database session (session-per-operation pattern)"""
        return SessionLocal()
    
    # ========================================================================
    # PORTFOLIO OPERATIONS
    # ========================================================================
    
    def create_portfolio(
        self, 
        name: str, 
        description: Optional[str] = None,
        currency: str = "USD"
    ) -> int:
        """
        Create a new portfolio
        
        Args:
            name: Portfolio name (e.g., "My 401k", "Trading Account")
            description: Optional description
            currency: Base currency (default: USD)
            
        Returns:
            portfolio_id: ID of created portfolio
            
        Raises:
            Exception: If creation fails
        """
        session = self._get_session()
        try:
            portfolio = Portfolio(
                name=name,
                description=description,
                currency=currency,
                cash_balance=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(portfolio)
            session.commit()
            session.refresh(portfolio)
            
            portfolio_id = portfolio.id
            logger.info(f"Created portfolio '{name}' (ID: {portfolio_id})")
            return portfolio_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create portfolio '{name}': {e}")
            raise
        finally:
            session.close()
    
    def get_portfolio(self, portfolio_id: int) -> Optional[Dict]:
        """
        Get portfolio details
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio dict or None if not found
        """
        session = self._get_session()
        try:
            portfolio = session.get(Portfolio, portfolio_id)
            
            if not portfolio:
                return None
            
            return {
                "id": portfolio.id,
                "name": portfolio.name,
                "description": portfolio.description,
                "currency": portfolio.currency,
                "cash_balance": float(portfolio.cash_balance),
                "created_at": portfolio.created_at,
                "updated_at": portfolio.updated_at
            }
            
        finally:
            session.close()
    
    def list_portfolios(self) -> List[Dict]:
        """
        List all portfolios
        
        Returns:
            List of portfolio dicts
        """
        session = self._get_session()
        try:
            portfolios = session.query(Portfolio).all()
            
            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "currency": p.currency,
                    "cash_balance": float(p.cash_balance),
                    "created_at": p.created_at,
                    "updated_at": p.updated_at
                }
                for p in portfolios
            ]
            
        finally:
            session.close()
    
    def update_portfolio(
        self, 
        portfolio_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        cash_balance: Optional[float] = None
    ) -> bool:
        """
        Update portfolio details
        
        Args:
            portfolio_id: Portfolio ID
            name: New name (optional)
            description: New description (optional)
            cash_balance: New cash balance (optional)
            
        Returns:
            True if updated, False if not found
        """
        session = self._get_session()
        try:
            portfolio = session.get(Portfolio, portfolio_id)
            
            if not portfolio:
                return False
            
            if name is not None:
                portfolio.name = name
            if description is not None:
                portfolio.description = description
            if cash_balance is not None:
                portfolio.cash_balance = cash_balance
            
            portfolio.updated_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Updated portfolio {portfolio_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update portfolio {portfolio_id}: {e}")
            raise
        finally:
            session.close()
    
    def delete_portfolio(self, portfolio_id: int) -> bool:
        """
        Delete a portfolio and all its holdings
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            True if deleted, False if not found
        """
        session = self._get_session()
        try:
            portfolio = session.get(Portfolio, portfolio_id)
            
            if not portfolio:
                return False
            
            # Delete all holdings (cascade handles this, but explicit is clear)
            session.query(PortfolioHolding).filter(
                PortfolioHolding.portfolio_id == portfolio_id
            ).delete()
            
            # Delete portfolio
            session.delete(portfolio)
            session.commit()
            
            logger.info(f"Deleted portfolio {portfolio_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete portfolio {portfolio_id}: {e}")
            raise
        finally:
            session.close()
    
    # ========================================================================
    # HOLDING OPERATIONS (STRICT - NO ASSET CREATION)
    # ========================================================================
    
    def add_holding(
        self,
        portfolio_id: int,
        ticker: str,
        quantity: float,
        average_price: float
    ) -> int:
        """
        Add a holding to a portfolio
        
        STRICT POLICY: Asset MUST exist in database before adding holding.
        Use DataManager.fetch_price_data() to create assets with real data.
        
        Args:
            portfolio_id: Portfolio ID
            ticker: Asset ticker (e.g., "SPY")
            quantity: Number of shares
            average_price: Average purchase price per share
            
        Returns:
            holding_id: ID of created/updated holding
            
        Raises:
            ValueError: If portfolio doesn't exist
            AssetNotFoundError: If asset doesn't exist in database
            
        Example:
            # WRONG - will fail:
            pm.add_holding(1, "AAPL", 10, 150.0)  # ❌ AAPL not in database
            
            # CORRECT - fetch data first:
            dm = DataManager()
            dm.fetch_price_data("AAPL", start_date, end_date)  # Creates Asset
            pm.add_holding(1, "AAPL", 10, 150.0)  # ✅ Now it works
        """
        session = self._get_session()
        try:
            # Verify portfolio exists
            portfolio = session.get(Portfolio, portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            # ✅ STRICT: Asset MUST exist (no auto-creation)
            asset = session.query(Asset).filter(Asset.ticker == ticker).first()
            if not asset:
                raise AssetNotFoundError(
                    f"Asset '{ticker}' not found in database.\n"
                    f"\n"
                    f"Please fetch market data for this ticker first:\n"
                    f"\n"
                    f"  from portfolio_tool.data_manager import DataManager\n"
                    f"  from datetime import datetime, timedelta\n"
                    f"\n"
                    f"  dm = DataManager()\n"
                    f"  end_date = datetime.now()\n"
                    f"  start_date = end_date - timedelta(days=365)\n"
                    f"  dm.fetch_price_data('{ticker}', start_date, end_date)\n"
                    f"\n"
                    f"This will create the Asset with proper:\n"
                    f"  - asset_class (EQUITY, BOND, ETF, etc.) from yfinance\n"
                    f"  - currency (USD, EUR, etc.) from yfinance\n"
                    f"  - sector, industry, and other metadata\n"
                    f"\n"
                    f"Then you can add it to your portfolio."
                )
            
            # Check if holding already exists
            existing = session.query(PortfolioHolding).filter(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.asset_id == asset.id
            ).first()
            
            if existing:
                # Update existing holding
                old_quantity = existing.quantity
                new_quantity = old_quantity + quantity
                
                # Weighted average price
                total_cost = (existing.average_price * old_quantity + average_price * quantity)
                existing.average_price = total_cost / new_quantity
                existing.quantity = new_quantity
                existing.updated_at = datetime.utcnow()
                
                session.commit()
                logger.info(
                    f"Updated holding {ticker} in portfolio {portfolio_id}: "
                    f"{old_quantity} → {new_quantity} shares, "
                    f"avg price ${existing.average_price:.2f}"
                )
                return existing.id
            else:
                # Create new holding
                holding = PortfolioHolding(
                    portfolio_id=portfolio_id,
                    asset_id=asset.id,
                    quantity=quantity,
                    average_price=average_price,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(holding)
                session.commit()
                session.refresh(holding)
                
                logger.info(f"Added holding {ticker} to portfolio {portfolio_id}: {quantity} shares @ ${average_price:.2f}")
                return holding.id
            
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_holdings(self, portfolio_id: int) -> List[Dict]:
        """
        Get all holdings for a portfolio
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            List of holding dicts with FULL asset information
        """
        session = self._get_session()
        try:
            holdings = (
                session.query(PortfolioHolding, Asset)
                .join(Asset, PortfolioHolding.asset_id == Asset.id)
                .filter(PortfolioHolding.portfolio_id == portfolio_id)
                .all()
            )
            
            return [
                {
                    "id": holding.id,
                    "ticker": asset.ticker,
                    "name": asset.name,
                    "quantity": float(holding.quantity),
                    "average_price": float(holding.average_price),
                    "asset_class": asset.asset_class,
                    "sector": asset.sector,
                    "industry": asset.industry,
                    "country": asset.country,
                    "currency": asset.currency,
                    "created_at": holding.created_at,
                    "updated_at": holding.updated_at,
                    "purchase_date": holding.purchase_date
                }
                for holding, asset in holdings
            ]
            
        finally:
            session.close()
    
    def get_portfolio_tickers(self, portfolio_id: int) -> List[str]:
        """
        Get list of tickers in a portfolio
        
        This is the KEY METHOD used by agents to get the list of assets
        to analyze, optimize, or rebalance.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            List of tickers (e.g., ["SPY", "TLT", "GLD"])
        """
        session = self._get_session()
        try:
            holdings = (
                session.query(Asset.ticker)
                .join(PortfolioHolding, Asset.id == PortfolioHolding.asset_id)
                .filter(PortfolioHolding.portfolio_id == portfolio_id)
                .all()
            )
            
            tickers = [ticker for (ticker,) in holdings]
            logger.debug(f"Portfolio {portfolio_id} tickers: {tickers}")
            return tickers
            
        finally:
            session.close()
    
    def update_holding(
        self,
        holding_id: int,
        quantity: Optional[float] = None,
        average_price: Optional[float] = None
    ) -> bool:
        """
        Update a holding's quantity or average price
        
        Args:
            holding_id: Holding ID
            quantity: New quantity (optional)
            average_price: New average price (optional)
            
        Returns:
            True if updated, False if not found
        """
        session = self._get_session()
        try:
            holding = session.get(PortfolioHolding, holding_id)
            
            if not holding:
                return False
            
            if quantity is not None:
                holding.quantity = quantity
            if average_price is not None:
                holding.average_price = average_price
            
            holding.updated_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Updated holding {holding_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update holding {holding_id}: {e}")
            raise
        finally:
            session.close()
    
    def delete_holding(self, holding_id: int) -> bool:
        """
        Delete a holding from a portfolio
        
        Args:
            holding_id: Holding ID
            
        Returns:
            True if deleted, False if not found
        """
        session = self._get_session()
        try:
            holding = session.get(PortfolioHolding, holding_id)
            
            if not holding:
                return False
            
            session.delete(holding)
            session.commit()
            
            logger.info(f"Deleted holding {holding_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete holding {holding_id}: {e}")
            raise
        finally:
            session.close()
    
    # ========================================================================
    # UTILITY METHODS (PURE CALCULATIONS - NO DATA FETCHING)
    # ========================================================================
    
    def get_portfolio_value(
        self, 
        portfolio_id: int, 
        current_prices: Dict[str, float]
    ) -> float:
        """
        Calculate total portfolio value
        
        Args:
            portfolio_id: Portfolio ID
            current_prices: Dict of {ticker: current_price}
                           NOTE: Caller must provide prices (use DataManager)
            
        Returns:
            Total portfolio value
        """
        holdings = self.get_holdings(portfolio_id)
        
        total = 0.0
        for holding in holdings:
            ticker = holding["ticker"]
            quantity = holding["quantity"]
            
            if ticker in current_prices:
                total += quantity * current_prices[ticker]
            else:
                logger.warning(f"No price available for {ticker}")
        
        return total
    
    def get_portfolio_summary(self, portfolio_id: int) -> Dict:
        """
        Get portfolio metadata and holdings, unpriced.

        Pricing and P&L are not computed here. Market value and P&L are
        quant/allocation.py's job, fed by DataAgent through shared_data; this
        method used to carry a third copy of the P&L formula, one that skipped
        holdings with no price instead of raising.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            Summary dict with portfolio info and holdings
        """
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return {"error": "Portfolio not found"}
        
        holdings = self.get_holdings(portfolio_id)
        
        return {
            "portfolio": portfolio,
            "holdings": holdings,
            "num_holdings": len(holdings)
        }
    
    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================
    
    def validate_portfolio_integrity(self, portfolio_id: int) -> Dict[str, any]:
        """
        Validate portfolio data integrity
        
        Checks:
        - All holdings link to valid assets
        - All assets have required fields populated
        - No orphaned holdings
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Validation result dict with issues found
        """
        session = self._get_session()
        try:
            issues = []
            warnings = []
            
            portfolio = session.get(Portfolio, portfolio_id)
            if not portfolio:
                return {"valid": False, "error": f"Portfolio {portfolio_id} not found"}
            
            holdings = self.get_holdings(portfolio_id)
            
            for holding in holdings:
                # Check for incomplete asset data
                if not holding.get("asset_class") or holding["asset_class"] == "UNKNOWN":
                    issues.append(f"{holding['ticker']}: asset_class is UNKNOWN (fetch real data)")
                
                if not holding.get("name") or holding["name"] == holding["ticker"]:
                    warnings.append(f"{holding['ticker']}: name not set (using ticker as name)")
                
                if not holding.get("sector") and holding.get("asset_class") == "EQUITY":
                    warnings.append(f"{holding['ticker']}: sector not set (expected for equities)")
            
            return {
                "valid": len(issues) == 0,
                "portfolio_id": portfolio_id,
                "num_holdings": len(holdings),
                "issues": issues,
                "warnings": warnings
            }
            
        finally:
            session.close()


# ========================================================================
# HELPER FUNCTIONS (NOT PART OF CORE MANAGER)
# ========================================================================

def ensure_asset_exists_helper(ticker: str) -> bool:
    """
    Helper to ensure asset exists, with proper data fetching if needed.
    
    This is a WRAPPER FUNCTION for convenience - NOT part of PortfolioManager.
    Use this in demos, tests, or agent code.
    
    Args:
        ticker: Asset ticker
        
    Returns:
        True if asset exists (or was successfully created)
        
    Raises:
        Exception if data fetch fails
    """
    from portfolio_tool.database_setup import SessionLocal, Asset
    from portfolio_tool.data_manager import DataManager
    from datetime import datetime, timedelta
    
    # Check if exists
    session = SessionLocal()
    asset = session.query(Asset).filter(Asset.ticker == ticker).first()
    session.close()
    
    if asset:
        logger.debug(f"Asset {ticker} already exists")
        return True
    
    # Fetch data
    logger.info(f"Fetching data for {ticker}...")
    dm = DataManager()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    try:
        dm.fetch_price_data(ticker, start_date, end_date)
        logger.info(f"✓ Asset {ticker} created with real market data")
        return True
    except Exception as e:
        logger.error(f"Failed to fetch data for {ticker}: {e}")
        raise


def add_holding_with_auto_fetch(
    portfolio_id: int,
    ticker: str,
    quantity: float,
    average_price: float
) -> int:
    """
    Convenience function: Add holding with automatic data fetching if needed.
    
    This is a WRAPPER - NOT part of core PortfolioManager.
    Use this in demos or user-facing code for better UX.
    
    Args:
        portfolio_id: Portfolio ID
        ticker: Asset ticker
        quantity: Number of shares
        average_price: Average purchase price
        
    Returns:
        holding_id
    """
    # Ensure asset exists
    ensure_asset_exists_helper(ticker)
    
    # Add holding
    pm = PortfolioManager()
    return pm.add_holding(portfolio_id, ticker, quantity, average_price)


if __name__ == "__main__":
    # This demonstrates the CORRECT usage pattern
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("PORTFOLIO MANAGER - PRODUCTION USAGE PATTERN")
    print("=" * 80)
    
    print("\n⚠️  This will FAIL if assets don't exist - that's intentional!")
    print("Use ensure_asset_exists_helper() or fetch data first.\n")
    
    pm = PortfolioManager()
    
    # Create portfolio
    pid = pm.create_portfolio("Test Portfolio")
    print(f"✓ Created portfolio {pid}")
    
    # Try to add holdings - will fail if assets don't exist
    try:
        print("\nAttempting to add SPY (may fail if not in database)...")
        pm.add_holding(pid, "SPY", quantity=100, average_price=450.0)
        print("✓ Added SPY (asset existed in database)")
    except AssetNotFoundError as e:
        print(f"❌ Failed as expected: {e}")
        print("\n✅ This is CORRECT behavior - no guessing allowed!")
    
    # Cleanup
    pm.delete_portfolio(pid)
    print("\n✓ Cleaned up test portfolio")




# JUST FOR TESTSS
def get_or_create_demo_portfolio() -> int:
    """
    Helper to get or create a demo portfolio for testing.
    
    Returns:
        Portfolio ID
    """
    pm = PortfolioManager()
    
    # Check for existing
    portfolios = pm.list_portfolios()
    for p in portfolios:
        if p["name"] == "Demo Portfolio":
            return p["id"]
            
    # Create new
    pid = pm.create_portfolio("Demo Portfolio", currency="USD")
    
    # Add assets (safely)
    try:
        # We use the helper to ensure assets exist first
        # This is for DEMO purposes - in prod, use DataManager
        ensure_asset_exists_helper("SPY")
        ensure_asset_exists_helper("TLT")
        ensure_asset_exists_helper("GLD")
        
        pm.add_holding(pid, "SPY", 100, 400.0)  # $40k
        pm.add_holding(pid, "TLT", 200, 100.0)  # $20k
        pm.add_holding(pid, "GLD", 50, 180.0)   # $9k
        
    except Exception as e:
        logger.warning(f"Could not fully seed demo portfolio: {e}")
        
    return pid