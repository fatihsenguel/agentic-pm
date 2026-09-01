"""
Portfolio Manager - CRUD Operations for Portfolios and Holdings

This module provides a clean interface for managing portfolios and their holdings.
Follows the project's design principles:
- Single responsibility (only portfolio CRUD)
- Session isolation (separate from DataManager)
- Structured responses
- Error handling

Usage:
    from portfolio_tool.portfolio_manager import PortfolioManager
    
    pm = PortfolioManager()
    
    # Create portfolio
    portfolio_id = pm.create_portfolio("My 401k", currency="USD")
    
    # Add holdings
    pm.add_holding(portfolio_id, "SPY", quantity=100, avg_price=450.0)
    pm.add_holding(portfolio_id, "TLT", quantity=50, avg_price=88.0)
    
    # Get tickers (KEY METHOD!)
    tickers = pm.get_portfolio_tickers(portfolio_id)  # ["SPY", "TLT"]
    
    # Get full holdings
    holdings = pm.get_holdings(portfolio_id)
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import (
    SessionLocal, 
    Portfolio, 
    PortfolioHolding,
    Asset
)

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Manages portfolio CRUD operations with clean interface"""
    
    def __init__(self):
        """Initialize portfolio manager"""
        # Note: We create sessions per-operation (session isolation principle)
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
                cash_balance=0.0,  # Start with zero cash
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
            
            # Delete all holdings first (cascade should handle this, but explicit is better)
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
    # HOLDING OPERATIONS
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
        
        Args:
            portfolio_id: Portfolio ID
            ticker: Asset ticker (e.g., "SPY")
            quantity: Number of shares
            average_price: Average purchase price per share
            
        Returns:
            holding_id: ID of created holding
            
        Raises:
            Exception: If portfolio doesn't exist or ticker is invalid
        """
        session = self._get_session()
        try:
            # Verify portfolio exists
            portfolio = session.get(Portfolio, portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            # Get or create asset
            asset = session.query(Asset).filter(Asset.ticker == ticker).first()
            if not asset:
                # Create asset if doesn't exist
                asset = Asset(
                    ticker=ticker,
                    name=ticker,
                    asset_class="UNKNOWN",  # can be modified later
                    sector=None,
                    industry=None,
                    country=None,
                    currency="USD"
                )
                session.add(asset)
                session.flush()  # Get asset.id
            
            # Check if holding already exists
            existing = session.query(PortfolioHolding).filter(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.asset_id == asset.id
            ).first()
            
            if existing:
                # Update existing holding
                existing.quantity += quantity
                # Update average price (weighted average)
                total_cost = (existing.average_price * (existing.quantity - quantity) + 
                             average_price * quantity)
                existing.average_price = total_cost / existing.quantity
                existing.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"Updated holding {ticker} in portfolio {portfolio_id}")
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
                logger.info(f"Added holding {ticker} to portfolio {portfolio_id}")
                return holding.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add holding {ticker}: {e}")
            raise
        finally:
            session.close()
    
    def get_holdings(self, portfolio_id: int) -> List[Dict]:
        """
        Get all holdings for a portfolio
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            List of holding dicts with format:
            [
                {
                    "id": 1,
                    "ticker": "SPY",
                    "quantity": 100.0,
                    "average_price": 450.0,
                    "asset_class": "EQUITY",
                    "created_at": datetime,
                    "updated_at": datetime
                },
                ...
            ]
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
                    "quantity": float(holding.quantity),
                    "average_price": float(holding.average_price),
                    "asset_class": asset.asset_class,
                    "created_at": holding.created_at,
                    "updated_at": holding.updated_at,
                    "name": asset.name,
                    "sector": asset.sector
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
    # UTILITY METHODS
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
    
    def get_portfolio_summary(
        self, 
        portfolio_id: int,
        current_prices: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Get comprehensive portfolio summary
        
        Args:
            portfolio_id: Portfolio ID
            current_prices: Optional dict of current prices
            
        Returns:
            Summary dict with portfolio info, holdings, and optionally values
        """
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return {"error": "Portfolio not found"}
        
        holdings = self.get_holdings(portfolio_id)
        
        summary = {
            "portfolio": portfolio,
            "holdings": holdings,
            "num_holdings": len(holdings)
        }
        
        if current_prices:
            # Add current values and returns
            for holding in holdings:
                ticker = holding["ticker"]
                if ticker in current_prices:
                    current_price = current_prices[ticker]
                    cost_basis = holding["quantity"] * holding["average_price"]
                    current_value = holding["quantity"] * current_price
                    
                    holding["current_price"] = current_price
                    holding["cost_basis"] = cost_basis
                    holding["current_value"] = current_value
                    holding["unrealized_gain"] = current_value - cost_basis
                    holding["return_pct"] = ((current_price / holding["average_price"]) - 1) * 100
            
            summary["total_value"] = self.get_portfolio_value(portfolio_id, current_prices)
        
        return summary


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

def create_demo_portfolio() -> int:
    """
    Create a demo portfolio with sample holdings
    Useful for testing and demos
    
    Returns:
        portfolio_id: ID of created demo portfolio
    """
    pm = PortfolioManager()
    
    # Create portfolio
    portfolio_id = pm.create_portfolio(
        name="Demo Portfolio",
        description="Sample portfolio for testing Phase 6.5",
        currency="USD"
    )
    
    # Add default holdings
    pm.add_holding(portfolio_id, "SPY", quantity=100, average_price=450.0)
    pm.add_holding(portfolio_id, "TLT", quantity=50, average_price=88.0)
    pm.add_holding(portfolio_id, "GLD", quantity=20, average_price=185.0)
    
    logger.info(f"Created demo portfolio {portfolio_id} with SPY/TLT/GLD")
    return portfolio_id


def get_or_create_demo_portfolio() -> int:
    """
    Get existing demo portfolio or create if doesn't exist
    
    Returns:
        portfolio_id: ID of demo portfolio
    """
    pm = PortfolioManager()
    portfolios = pm.list_portfolios()
    
    # Check if demo portfolio exists
    demo = next((p for p in portfolios if p["name"] == "Demo Portfolio"), None)
    
    if demo:
        return demo["id"]
    else:
        return create_demo_portfolio()


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Portfolio Manager...")
    
    pm = PortfolioManager()
    
    # Create portfolio
    pid = pm.create_portfolio("Test Portfolio")
    print(f"✓ Created portfolio {pid}")
    
    # Add holdings
    pm.add_holding(pid, "SPY", quantity=100, average_price=450.0)
    pm.add_holding(pid, "AAPL", quantity=50, average_price=180.0)
    print("✓ Added holdings")
    
    # Get tickers (KEY!)
    tickers = pm.get_portfolio_tickers(pid)
    print(f"✓ Tickers: {tickers}")
    
    # Get holdings
    holdings = pm.get_holdings(pid)
    print(f"✓ Holdings: {len(holdings)} positions")
    
    # Cleanup
    pm.delete_portfolio(pid)
    print("✓ Cleaned up test portfolio")
    
    print("\n✅ All tests passed!")