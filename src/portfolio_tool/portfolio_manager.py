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
✅ Record ledger rows (buys and sales) against EXISTING assets
✅ Read holdings, derived from the ledger (expected_values.md D13)
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
    
    # STEP 2: Create portfolio and record what was bought (PortfolioManager's job)
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("My 401k", currency="USD")
    pm.record_transaction(portfolio_id, "SPY", date(2024, 1, 15), "buy",
                          quantity=100, price=450.0, fees=0.0, amount=45_000.0)
    
    # Get tickers for agents
    tickers = pm.get_portfolio_tickers(portfolio_id)  # ["SPY"]
"""

import logging
from typing import List, Dict, Optional
from datetime import date as date_type, datetime, time
from sqlalchemy.orm import Session

from portfolio_tool.database_setup import (
    SessionLocal, 
    Portfolio, 
    PortfolioHolding,
    Asset,
    Transaction,
)
from portfolio_tool.quant.ledger import ROW_TYPES, derive_holdings

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
            
            # Delete the holdings and the ledger explicitly. SQLite does not
            # enforce ON DELETE CASCADE unless foreign keys are switched on,
            # and it reuses a deleted portfolio's id, so an orphaned ledger
            # row would become the next portfolio's holding.
            session.query(PortfolioHolding).filter(
                PortfolioHolding.portfolio_id == portfolio_id
            ).delete()
            session.query(Transaction).filter(
                Transaction.portfolio_id == portfolio_id
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
    
    def record_transaction(
        self,
        portfolio_id: int,
        ticker: str,
        date: date_type,
        kind: str,
        quantity: float,
        price: float,
        fees: float,
        amount: float,
    ) -> int:
        """
        Record one ledger row: a buy or a sale (expected_values.md Part 8).

        Every field is required. `amount` is the settled figure in the
        portfolio's currency - what was paid on a buy, what was received on
        a sale, fees inside (D11) - and is data (D14): it is not computed
        from price and fees here, because for a foreign-currency row the two
        differ by the day's rate. `fees` is required for the same reason a
        defaulted fee would be a fee of zero with a plausible face. No
        average is computed anywhere in this module: holdings derive from
        the rows (quant/ledger.py, D13).

        STRICT: the portfolio and the asset must already exist. Nothing is
        created here; DataManager.fetch_price_data creates assets.

        Args:
            portfolio_id: the portfolio the row belongs to
            ticker: an existing asset's ticker
            date: the trade date
            kind: 'buy' or 'sell'
            quantity: units traded
            price: price per unit in the instrument's currency
            fees: fees on the trade, in the portfolio's currency
            amount: the settled figure in the portfolio's currency

        Returns:
            the row's id

        Raises:
            ValueError: unknown kind, or portfolio not found
            AssetNotFoundError: the asset is not in the database
        """
        if kind not in ROW_TYPES:
            raise ValueError(
                f"Unknown transaction type {kind!r}; a ledger row is one of "
                f"{', '.join(ROW_TYPES)}."
            )

        session = self._get_session()
        try:
            portfolio = session.get(Portfolio, portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")

            asset = session.query(Asset).filter(Asset.ticker == ticker).first()
            if not asset:
                raise AssetNotFoundError(
                    f"Asset '{ticker}' not found in database.\n"
                    f"Fetch market data for it first "
                    f"(DataManager.fetch_price_data('{ticker}', start, end)), "
                    f"which creates the Asset with its metadata."
                )

            row = Transaction(
                portfolio_id=portfolio_id,
                asset_id=asset.id,
                date=datetime.combine(date, time()) if not isinstance(date, datetime) else date,
                type=kind,
                quantity=quantity,
                price_per_unit=price,
                fees=fees,
                amount=amount,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            logger.info(
                f"Recorded {kind} of {quantity} {ticker} @ {price} on {date} "
                f"in portfolio {portfolio_id} (amount {amount})"
            )
            return row.id

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_holdings(self, portfolio_id: int) -> List[Dict]:
        """
        Holdings of a portfolio, derived from its ledger rows (D13).

        The `transactions` table is the record of what was bought and sold;
        a holding is a view of it, computed by quant/ledger.py and never read
        from the holdings table. Unpriced: one dict per position still held,
        with the asset's metadata joined, plus the cost basis and realized
        gain the derivation carries. A portfolio with no rows has no
        holdings; the caller decides what an empty portfolio means.

        Raises LedgerError, from the derivation, on rows that cannot be
        turned into holdings - a sale over the position, an unknown type.
        That is a data error and is not repaired here.

        Returns:
            List of holding dicts: ticker, name, quantity, average_price,
            cost_basis, realized, asset_class, sector, instrument_type,
            industry, country, currency, purchase_date (a date).
        """
        session = self._get_session()
        try:
            found = (
                session.query(Transaction, Asset)
                .join(Asset, Transaction.asset_id == Asset.id)
                .filter(Transaction.portfolio_id == portfolio_id)
                .order_by(Transaction.date, Transaction.id)
                .all()
            )
            if not found:
                return []

            assets = {asset.ticker: asset for _, asset in found}
            rows = [
                {
                    "portfolio_id": t.portfolio_id,
                    "date": t.date.date() if isinstance(t.date, datetime) else t.date,
                    "type": t.type,
                    "ticker": asset.ticker,
                    "quantity": t.quantity,
                    "price": t.price_per_unit,
                    "fees": t.fees,
                    "amount": t.amount,
                }
                for t, asset in found
            ]
        finally:
            session.close()

        holdings = derive_holdings(rows)
        return [
            {
                "ticker": h.ticker,
                "name": assets[h.ticker].name,
                "quantity": float(h.quantity),
                "average_price": float(h.average_price),
                "cost_basis": float(h.cost_basis),
                "realized": float(h.realized),
                "asset_class": assets[h.ticker].asset_class,
                "sector": assets[h.ticker].sector,
                "instrument_type": assets[h.ticker].instrument_type,
                "industry": assets[h.ticker].industry,
                "country": assets[h.ticker].country,
                "currency": assets[h.ticker].currency,
                "purchase_date": date_type.fromisoformat(h.purchase_date),
            }
            for h in holdings.values()
        ]

    def get_portfolio_tickers(self, portfolio_id: int) -> List[str]:
        """
        Tickers of a portfolio's holdings, in get_holdings' order.

        The router builds its portfolio context from this list. It is a view
        of get_holdings so that the ledger has one reader, not two.
        """
        tickers = [h["ticker"] for h in self.get_holdings(portfolio_id)]
        logger.debug(f"Portfolio {portfolio_id} tickers: {tickers}")
        return tickers


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
