"""
SNIPPET: providers/base.py
PURPOSE: Abstract interface for data providers (Provider Pattern)
PATTERN: Interface abstraction - allows swapping YFinance → Bloomberg → etc.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from portfolio_tool.provider_models import (
    ProviderAssetInfo, ProviderPriceData, ProviderDividendData,
    ProviderSplitData, ProviderSharesData,
    ProviderFundamentalData, ProviderEarningsData, ProviderFinancialStatement
)

class DataProviderInterface(ABC):
    """
    INTERFACE: All data providers must implement these methods.
    - Vendor-agnostic: DataManager doesn't know if it's YFinance, Bloomberg, or Alpha Vantage
    - Returns: Provider-specific DTOs (ProviderAssetInfo, ProviderPriceData, etc.)
    - Thread-safe: Each method is stateless
    """
    
    @abstractmethod
    def get_asset_info(self, ticker: str) -> Optional[ProviderAssetInfo]:
        """
        Returns: ProviderAssetInfo(sector, industry, country, currency, long_name)
        Example: get_asset_info("AAPL") → {sector: "Technology", industry: "Consumer Electronics", ...}
        """
        pass

    @abstractmethod
    def get_daily_prices(self, ticker: str, start: date, end: date) -> List[ProviderPriceData]:
        """
        Returns: List[ProviderPriceData(date, open, high, low, close, volume)]
        Example: get_daily_prices("AAPL", "2024-01-01", "2024-12-31") → 252 daily bars
        """
        pass

    @abstractmethod
    def get_dividends(self, ticker: str, since: date | None = None) -> list[ProviderDividendData]:
        """Returns: List[ProviderDividendData(date, amount)]"""
        pass
        
    @abstractmethod
    def get_splits(self, ticker: str, since: date | None = None) -> List[ProviderSplitData]:
        """Returns: List[ProviderSplitData(date, ratio)]"""
        pass
        
    @abstractmethod
    def get_shares_history(self, ticker: str, since: date | None = None) -> List[ProviderSharesData]:
        """Returns: List[ProviderSharesData(date, shares_outstanding)]"""
        pass

    @abstractmethod
    def get_fundamental_data(self, ticker: str) -> Optional[ProviderFundamentalData]:
        """
        Returns: ProviderFundamentalData(beta, market_cap, pe_ratio, etc.)
        Example: get_fundamental_data("AAPL") → {beta: 1.2, market_cap: 3000000000000, ...}
        """
        pass

    @abstractmethod
    def get_quarterly_earnings(self, ticker: str, since: date | None = None) -> List[ProviderEarningsData]:
        """
        Returns: List[ProviderEarningsData(report_date, revenue, basic_eps)]
        Example: Quarterly earnings history for valuation analysis
        """
        pass

    @abstractmethod
    def get_financial_statements(
        self, ticker: str, report_type: str, period_type: str, since: date | None = None
    ) -> List[ProviderFinancialStatement]:
        """
        Returns: List[ProviderFinancialStatement(date, report_type, period_type, revenue, net_income, ...35+ fields)]
        
        Parameters:
        - report_type: "income_statement" | "balance_sheet" | "cash_flow"
        - period_type: "quarterly" | "annual"
        - since: Only return statements after this date
        
        Example: get_financial_statements("AAPL", "income_statement", "quarterly") 
                 → Last 4 quarters of P&L data
        """
        pass

# ==================== KEY DESIGN PATTERN ====================
"""
PROVIDER PATTERN BENEFITS:

1. VENDOR INDEPENDENCE:
   DataManager → DataProviderInterface ← YFinanceProvider
                                       ← BloombergProvider (future)
                                       ← AlphaVantageProvider (future)

2. TESTABILITY:
   - Can inject MockProvider for tests
   - No need to hit real APIs in unit tests

3. EXTENSIBILITY:
   - Add new provider without changing DataManager
   - Each provider handles its own API quirks (rate limits, auth, etc.)

4. SEPARATION OF CONCERNS:
   - Provider: API communication only
   - DataManager: Business logic + persistence
   - No mixing of concerns
"""
