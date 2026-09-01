# src/portfolio_tool/esg_screener.py
"""
ESG Screener - Checks holdings against ESG exclusion lists.

Phase: 7.1 - ESG Screening Module

PURPOSE:
Screens portfolio holdings against the ESG exclusion database.
Identifies any holdings that violate ESG policies.

USAGE:
    from portfolio_tool.esg_screener import ESGScreener
    
    screener = ESGScreener()
    result = screener.check_security(ticker="BTI")
    if result["excluded"]:
        print(f"Cannot buy: {result['reason']}")
"""

from typing import List, Dict, Optional, Set
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import (
    get_session,
    ESGExclusion,
    ESGCategory,
    PortfolioHolding,
    Asset,
    DailyPrice
)
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.decision_schemas import (
    ComplianceCheck,
    ConstraintType,
    BreachSeverity
)


class ESGScreener:
    """
    Screens portfolio holdings against ESG exclusion list.
    
    The screener maintains an in-memory cache of exclusions for
    fast repeated lookups within a session.
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize ESGScreener.
        
        Args:
            session: Optional SQLAlchemy session
        """
        self._session = session
        self._owns_session = session is None
        self._exclusion_cache: Optional[Dict[str, Dict]] = None
    
    @property
    def session(self) -> Session:
        """Lazy session initialization."""
        if self._session is None:
            self._session = get_session()
        return self._session
    
    def close(self):
        """Close session if we own it."""
        if self._owns_session and self._session is not None:
            self._session.close()
            self._session = None
    
    def clear_cache(self):
        """Clear the exclusion cache (call if exclusions are updated)."""
        self._exclusion_cache = None
    
    # =========================================================================
    # EXCLUSION SET MANAGEMENT
    # =========================================================================
    
    def get_exclusion_set(
        self,
        categories: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> Dict[str, Dict]:
        """
        Get the current exclusion set as a lookup dictionary.
        
        Returns a dict keyed by both ISIN and ticker for fast O(1) lookups.
        
        Args:
            categories: Optional list of category strings to filter
            use_cache: Whether to use cached exclusions
            
        Returns:
            Dict mapping "isin:{ISIN}" and "ticker:{TICKER}" to exclusion info
        """
        if use_cache and self._exclusion_cache is not None and categories is None:
            return self._exclusion_cache
        
        query = self.session.query(ESGExclusion).filter(
            ESGExclusion.is_active == True
        )
        
        today = date.today()
        query = query.filter(ESGExclusion.effective_date <= today)
        query = query.filter(
            or_(
                ESGExclusion.expiry_date == None,
                ESGExclusion.expiry_date >= today
            )
        )
        
        if categories:
            category_enums = []
            for cat in categories:
                try:
                    category_enums.append(ESGCategory[cat.upper()])
                except KeyError:
                    try:
                        category_enums.append(ESGCategory(cat.lower()))
                    except ValueError:
                        pass
            
            if category_enums:
                query = query.filter(ESGExclusion.category.in_(category_enums))
        
        exclusions = {}
        for exc in query.all():
            exc_data = {
                "id": exc.id,
                "company_name": exc.company_name,
                "category": exc.category.value,
                "subcategory": exc.subcategory,
                "reason": exc.reason,
                "source": exc.source,
                "revenue_threshold": exc.revenue_threshold
            }
            
            if exc.isin:
                exclusions[f"isin:{exc.isin.upper()}"] = exc_data
            
            if exc.ticker:
                exclusions[f"ticker:{exc.ticker.upper()}"] = exc_data
        
        if categories is None:
            self._exclusion_cache = exclusions
        
        return exclusions
    
    def get_excluded_tickers(self, categories: Optional[List[str]] = None) -> Set[str]:
        """
        Get set of all excluded tickers.
        
        Args:
            categories: Optional category filter
            
        Returns:
            Set of ticker symbols
        """
        exclusions = self.get_exclusion_set(categories)
        tickers = set()
        for key in exclusions:
            if key.startswith("ticker:"):
                tickers.add(key.split(":")[1])
        return tickers
    
    # =========================================================================
    # SINGLE SECURITY CHECK
    # =========================================================================
    
    def check_security(
        self,
        ticker: Optional[str] = None,
        isin: Optional[str] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Check if a single security is on the exclusion list.
        
        Args:
            ticker: Ticker symbol
            isin: ISIN identifier
            categories: Optional category filter
            
        Returns:
            Dict with keys: excluded, category, reason, company_name
        """
        exclusions = self.get_exclusion_set(categories)
        
        if isin:
            key = f"isin:{isin.upper()}"
            if key in exclusions:
                exc = exclusions[key]
                return {
                    "excluded": True,
                    "category": exc["category"],
                    "reason": exc["reason"],
                    "company_name": exc["company_name"],
                    "source": exc["source"]
                }
        
        if ticker:
            key = f"ticker:{ticker.upper()}"
            if key in exclusions:
                exc = exclusions[key]
                return {
                    "excluded": True,
                    "category": exc["category"],
                    "reason": exc["reason"],
                    "company_name": exc["company_name"],
                    "source": exc["source"]
                }
        
        return {"excluded": False}
    
    def is_excluded(
        self,
        ticker: Optional[str] = None,
        isin: Optional[str] = None
    ) -> bool:
        """
        Quick check if a security is excluded.
        
        Args:
            ticker: Ticker symbol
            isin: ISIN identifier
            
        Returns:
            True if security is on exclusion list
        """
        return self.check_security(ticker=ticker, isin=isin)["excluded"]
    
    # =========================================================================
    # PORTFOLIO SCREENING
    # =========================================================================
    
    def check_portfolio(
        self,
        portfolio_id: int,
        categories: Optional[List[str]] = None
    ) -> List[ComplianceCheck]:
        """
        Check all holdings in a portfolio against ESG exclusions.
        
        Args:
            portfolio_id: Portfolio's database ID
            categories: Optional list of ESG categories to check
            
        Returns:
            List of ComplianceCheck objects for any breaches found
        """
        exclusions = self.get_exclusion_set(categories)
        
        if not exclusions:
            return []
        
        holdings = (
            self.session.query(PortfolioHolding, Asset)
            .join(Asset, PortfolioHolding.asset_id == Asset.id)
            .filter(PortfolioHolding.portfolio_id == portfolio_id)
            .all()
        )
        
        if not holdings:
            return []
        
        total_value = 0.0
        holding_values = []
        
        for holding, asset in holdings:
            current_price = self._get_current_price(asset.id)
            if current_price is None:
                current_price = holding.average_price or 0
            
            value = holding.quantity * current_price
            total_value += value
            holding_values.append((holding, asset, value, current_price))
        
        breaches = []
        
        for holding, asset, value, price in holding_values:
            weight = value / total_value if total_value > 0 else 0
            
            exclusion = None
            if asset.isin:
                key = f"isin:{asset.isin.upper()}"
                if key in exclusions:
                    exclusion = exclusions[key]
            
            if not exclusion and asset.ticker:
                key = f"ticker:{asset.ticker.upper()}"
                if key in exclusions:
                    exclusion = exclusions[key]
            
            if exclusion:
                category_display = exclusion["category"].replace("_", " ").title()
                
                breaches.append(ComplianceCheck(
                    constraint_name=f"ESG: No {category_display}",
                    constraint_type=ConstraintType.ESG,
                    status="breach",
                    severity=BreachSeverity.CRITICAL,
                    current_value=weight,
                    limit_value=0.0,
                    ticker=asset.ticker,
                    isin=asset.isin,
                    asset_class=asset.asset_class,
                    message=(
                        f"{asset.ticker} ({exclusion['company_name']}) "
                        f"violates ESG policy: {exclusion['reason']}"
                    ),
                    action=(
                        f"SELL IMMEDIATE: Liquidate entire {asset.ticker} position "
                        f"(~${value:,.0f})"
                    )
                ))
        
        return breaches
    
    def check_holdings_list(
        self,
        holdings: List[Dict[str, any]],
        categories: Optional[List[str]] = None
    ) -> List[ComplianceCheck]:
        """
        Check a list of holdings (dict format) against ESG exclusions.
        
        Args:
            holdings: List of dicts with keys: ticker, isin (optional),
                     quantity, price, value (optional)
            categories: Optional category filter
            
        Returns:
            List of ComplianceCheck objects for breaches
        """
        exclusions = self.get_exclusion_set(categories)
        
        if not exclusions:
            return []
        
        total_value = sum(
            h.get("value", h.get("quantity", 0) * h.get("price", 0))
            for h in holdings
        )
        
        breaches = []
        
        for h in holdings:
            ticker = h.get("ticker", "").upper()
            isin = h.get("isin", "").upper() if h.get("isin") else None
            value = h.get("value", h.get("quantity", 0) * h.get("price", 0))
            weight = value / total_value if total_value > 0 else 0
            
            exclusion = None
            if isin:
                key = f"isin:{isin}"
                if key in exclusions:
                    exclusion = exclusions[key]
            
            if not exclusion and ticker:
                key = f"ticker:{ticker}"
                if key in exclusions:
                    exclusion = exclusions[key]
            
            if exclusion:
                category_display = exclusion["category"].replace("_", " ").title()
                
                breaches.append(ComplianceCheck(
                    constraint_name=f"ESG: No {category_display}",
                    constraint_type=ConstraintType.ESG,
                    status="breach",
                    severity=BreachSeverity.CRITICAL,
                    current_value=weight,
                    limit_value=0.0,
                    ticker=ticker,
                    isin=isin,
                    message=(
                        f"{ticker} ({exclusion['company_name']}) "
                        f"violates ESG policy: {exclusion['reason']}"
                    ),
                    action=f"SELL IMMEDIATE: Liquidate {ticker} (~${value:,.0f})"
                ))
        
        return breaches
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_exclusion_stats(self) -> Dict[str, int]:
        """
        Get count of exclusions by category.
        
        Returns:
            Dict mapping category name to count
        """
        from sqlalchemy import func
        
        results = (
            self.session.query(
                ESGExclusion.category,
                func.count(ESGExclusion.id)
            )
            .filter(ESGExclusion.is_active == True)
            .group_by(ESGExclusion.category)
            .all()
        )
        
        return {cat.value: count for cat, count in results}
    
    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================
    
    def _get_current_price(self, asset_id: int) -> Optional[float]:
        """Get most recent price for an asset."""
        latest = (
            self.session.query(DailyPrice)
            .filter(DailyPrice.asset_id == asset_id)
            .order_by(DailyPrice.date.desc())
            .first()
        )
        return latest.close if latest else None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def check_security_esg(
    ticker: Optional[str] = None,
    isin: Optional[str] = None
) -> Dict[str, any]:
    """
    Convenience function to check a single security.
    """
    screener = ESGScreener()
    try:
        return screener.check_security(ticker=ticker, isin=isin)
    finally:
        screener.close()


def check_portfolio_esg(
    portfolio_id: int,
    categories: Optional[List[str]] = None
) -> List[ComplianceCheck]:
    """
    Convenience function to screen a portfolio.
    """
    screener = ESGScreener()
    try:
        return screener.check_portfolio(portfolio_id, categories)
    finally:
        screener.close()


def is_ticker_excluded(ticker: str) -> bool:
    """
    Quick check if a ticker is ESG-excluded.
    """
    screener = ESGScreener()
    try:
        return screener.is_excluded(ticker=ticker)
    finally:
        screener.close()