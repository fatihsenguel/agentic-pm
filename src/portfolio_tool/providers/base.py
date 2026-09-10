# portfolio_tool/providers/base.py
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Optional
from portfolio_tool.provider_models import (
    ProviderAssetInfo, ProviderPriceData, ProviderDividendData,
    ProviderSplitData, ProviderSharesData,
    ProviderFundamentalData, ProviderEarningsData, ProviderFinancialStatement,
    ProviderMacroData, ProviderMacroSnapshot,  # NEU
    ProviderFxRate,
)

class DataProviderInterface(ABC):
    '''
    Das ist die abstrakte Schnittstelle (der "Vertrag").
    Jeder konkrete Provider MUSS diese Methoden implementieren.
    '''

    # The provider's name, written as `source` on every fx_rates row it
    # supplies. Set by each implementation; there is no default, because a
    # rate whose origin is unknown is not a price source.
    name: str

    # ==================== BESTEHENDE METHODEN ====================

    @abstractmethod
    def get_fx_rates(self, base: str, quote: str, start: date, end: date) -> List[ProviderFxRate]:
        '''Daily spot rates, units of `base` per one unit of `quote`, for
        [start, end]. The direction is this method's to get right
        (expected_values.md D17); nothing downstream inverts.'''
        pass
    
    @abstractmethod
    def get_asset_info(self, ticker: str) -> Optional[ProviderAssetInfo]:
        '''Holt Stammdaten für ein Asset (Snapshot, Typ 2).'''
        pass

    @abstractmethod
    def get_daily_prices(self, ticker: str, start: date, end: date) -> List[ProviderPriceData]:
        '''Holt tägliche Kursdaten (Zeitreihe, Typ 1).'''
        pass

    @abstractmethod
    def get_dividends(self, ticker: str, since: date | None = None) -> list[ProviderDividendData]:
        '''Holt die Dividenden-Historie (Zeitreihe, Typ 1).'''
        pass
        
    @abstractmethod
    def get_splits(self, ticker: str, since: date | None = None) -> List[ProviderSplitData]:
        '''Holt die Split-Historie (Zeitreihe, Typ 1).'''
        pass
        
    @abstractmethod
    def get_shares_history(self, ticker: str, since: date | None = None) -> List[ProviderSharesData]:
        '''Holt die Historie der Aktienanzahl (Zeitreihe, Typ 1).'''
        pass

    @abstractmethod
    def get_fundamental_data(self, ticker: str) -> Optional[ProviderFundamentalData]:
        '''Holt einen Snapshot der Fundamentaldaten (Snapshot, Typ 2).'''
        pass

    @abstractmethod
    def get_quarterly_earnings(self, ticker: str, since: date | None = None) -> List[ProviderEarningsData]:
        '''Holt die historische Zeitreihe der Quartalsberichte (Zeitreihe, Typ 1).'''
        pass

    @abstractmethod
    def get_financial_statements(self, ticker: str, report_type: str, period_type: str, since: date | None = None) -> List[ProviderFinancialStatement]:
        '''
        Holt Finanzberichte für einen Ticker, Typ (Income/Balance/Cashflow)
        und Frequenz (Annual/Quarterly).
        '''
        pass
    
    # ==================== NEUE MACRO METHODEN ====================
    
    @abstractmethod
    def get_vix_data(self, start: date, end: date) -> List[ProviderMacroData]:
        '''Holt VIX (Volatility Index) Zeitreihe.'''
        pass
    
    @abstractmethod
    def get_treasury_yields(self, start: date, end: date) -> Dict[str, List[ProviderMacroData]]:
        '''Holt Treasury Yields für mehrere Laufzeiten (10Y, 30Y, 3M).'''
        pass
    
    @abstractmethod
    def get_macro_snapshot(self) -> ProviderMacroSnapshot:
        '''Holt aktuellen Snapshot aller Macro-Indikatoren.'''
        pass
    
    @abstractmethod
    def get_macro_indicator(self, indicator: str, start: date, end: date) -> List[ProviderMacroData]:
        '''Holt einen spezifischen Macro-Indikator (VIX, TNX_10Y, GOLD, etc.).'''
        pass