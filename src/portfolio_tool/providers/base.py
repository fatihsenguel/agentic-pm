# portfolio_tool/providers/base.py
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
    Das ist die abstrakte Schnittstelle (der "Vertrag").
    Jeder konkrete Provider MUSS diese Methoden implementieren.
    """
    
    @abstractmethod
    def get_asset_info(self, ticker: str) -> Optional[ProviderAssetInfo]:
        """Holt Stammdaten für ein Asset (Snapshot, Typ 2)."""
        pass

    @abstractmethod
    def get_daily_prices(self, ticker: str, start: date, end: date) -> List[ProviderPriceData]:
        """Holt tägliche Kursdaten (Zeitreihe, Typ 1)."""
        pass

    @abstractmethod
    def get_dividends(self, ticker: str, since: date | None = None) -> list[ProviderDividendData]:
        """Holt die Dividenden-Historie (Zeitreihe, Typ 1)."""
        pass
        
    @abstractmethod
    def get_splits(self, ticker: str, since: date | None = None) -> List[ProviderSplitData]:
        """Holt die Split-Historie (Zeitreihe, Typ 1)."""
        pass
        
    @abstractmethod
    def get_shares_history(self, ticker: str, since: date | None = None) -> List[ProviderSharesData]:
        """Holt die Historie der Aktienanzahl (Zeitreihe, Typ 1)."""
        pass

    @abstractmethod
    def get_fundamental_data(self, ticker: str) -> Optional[ProviderFundamentalData]:
        """Holt einen Snapshot der Fundamentaldaten (Snapshot, Typ 2)."""
        pass

    @abstractmethod
    def get_quarterly_earnings(self, ticker: str, since: date | None = None) -> List[ProviderEarningsData]:
        """Holt die historische Zeitreihe der Quartalsberichte (Zeitreihe, Typ 1)."""
        pass

    @abstractmethod
    def get_financial_statements(self, ticker: str, report_type: str, period_type: str, since: date | None = None) -> List[ProviderFinancialStatement]:
        """
        Holt Finanzberichte für einen Ticker, Typ (Income/Balance/Cashflow)
        und Frequenz (Annual/Quarterly).

        Wenn `since` gesetzt ist, nur Perioden mit date > since zurückgeben.
        """
        pass