# portfolio_tool/providers/base.py
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Optional
from portfolio_tool.provider_models import (
    ProviderAssetInfo, ProviderPriceData, ProviderDividendData,
    ProviderSplitData, ProviderSharesData,
    ProviderFundamentalData, ProviderEarningsData, ProviderFinancialStatement,
    ProviderMacroData, ProviderMacroSnapshot,
    ProviderFxRate,
)

class DataProviderInterface(ABC):
    '''
    The abstract interface, the contract: every concrete provider MUST
    implement these methods.
    '''

    # The provider's name, written as `source` on every fx_rates row it
    # supplies. Set by each implementation; there is no default, because a
    # rate whose origin is unknown is not a price source.
    name: str

    # ==================== ASSET METHODS ====================

    @abstractmethod
    def get_fx_rates(self, base: str, quote: str, start: date, end: date) -> List[ProviderFxRate]:
        '''Daily spot rates, units of `base` per one unit of `quote`, for
        [start, end]. The direction is this method's to get right
        (expected_values.md D17); nothing downstream inverts.'''
        pass
    
    @abstractmethod
    def get_asset_info(self, ticker: str) -> Optional[ProviderAssetInfo]:
        '''Fetches master data for an asset (snapshot, type 2).'''
        pass

    @abstractmethod
    def get_daily_prices(self, ticker: str, start: date, end: date) -> List[ProviderPriceData]:
        '''Fetches daily prices (time series, type 1).'''
        pass

    @abstractmethod
    def get_dividends(self, ticker: str, since: date | None = None) -> list[ProviderDividendData]:
        '''Fetches the dividend history (time series, type 1).'''
        pass
        
    @abstractmethod
    def get_splits(self, ticker: str, since: date | None = None) -> List[ProviderSplitData]:
        '''Fetches the split history (time series, type 1).'''
        pass
        
    @abstractmethod
    def get_shares_history(self, ticker: str, since: date | None = None) -> List[ProviderSharesData]:
        '''Fetches the history of shares outstanding (time series, type 1).'''
        pass

    @abstractmethod
    def get_fundamental_data(self, ticker: str) -> Optional[ProviderFundamentalData]:
        '''Fetches a snapshot of the fundamentals (snapshot, type 2).'''
        pass

    @abstractmethod
    def get_quarterly_earnings(self, ticker: str, since: date | None = None) -> List[ProviderEarningsData]:
        '''Fetches the historical series of quarterly reports (time series, type 1).'''
        pass

    @abstractmethod
    def get_financial_statements(self, ticker: str, report_type: str, period_type: str, since: date | None = None) -> List[ProviderFinancialStatement]:
        '''
        Fetches financial statements for a ticker, by type (income, balance
        sheet, cash flow) and frequency (annual, quarterly).
        '''
        pass
    
    # ==================== MACRO METHODS ====================
    
    @abstractmethod
    def get_vix_data(self, start: date, end: date) -> List[ProviderMacroData]:
        '''Fetches the VIX (volatility index) time series.'''
        pass
    
    @abstractmethod
    def get_treasury_yields(self, start: date, end: date) -> Dict[str, List[ProviderMacroData]]:
        '''Fetches Treasury yields for several maturities (10Y, 30Y, 3M).'''
        pass
    
    @abstractmethod
    def get_macro_snapshot(self) -> ProviderMacroSnapshot:
        '''Fetches the current snapshot of every macro indicator.'''
        pass
    
    @abstractmethod
    def get_macro_indicator(self, indicator: str, start: date, end: date) -> List[ProviderMacroData]:
        '''Fetches one macro indicator (VIX, TNX_10Y, GOLD, etc.).'''
        pass