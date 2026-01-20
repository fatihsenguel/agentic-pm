# portfolio_tool/provider_models.py
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any

"""
Definiert die standardisierten "Data Transfer Objects" (DTOs).
JEDER Provider (yfinance, alphavantage, etc.) MUSS seine Rohdaten
in DIESE Formate umwandeln, bevor er sie an den DataManager übergibt.

NOTE: Felder die von externen APIs kommen können NaN/None sein,
daher sind numerische Felder als Optional definiert.
"""

@dataclass
class ProviderAssetInfo:
    """Standardisiertes Format für Asset-Stammdaten."""
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    long_name: Optional[str] = None

@dataclass
class ProviderPriceData:
    """Standardisiertes Format für tägliche Kurse."""
    date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Decimal = None  # close ist required für viele Berechnungen
    volume: Optional[int] = None  # Volume kann NaN sein bei manchen APIs

@dataclass
class ProviderDividendData:
    """Standardisiertes Format für Dividenden."""
    ex_date: date
    amount: Decimal

@dataclass
class ProviderSplitData:
    """Standardisiertes Format für Splits."""
    date: date
    ratio_str: str  # z.B. "2:1"

@dataclass
class ProviderSharesData:
    """Standardisiertes Format für Aktienanzahl-Historie."""
    date: date
    shares: Optional[int] = None  # Kann NaN sein

@dataclass
class ProviderFundamentalData:
    """Standardisiertes Format für Snapshot-Fundamentaldaten."""
    market_cap: Optional[int] = None
    forward_pe: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    trailing_eps: Optional[Decimal] = None

@dataclass
class ProviderEarningsData:
    """Standardisiertes Format für historische Quartalsberichte."""
    report_date: date
    revenue: Optional[int] = None  # Kann NaN sein
    basic_eps: Optional[Decimal] = None  # Kann NaN sein

@dataclass
class ProviderFinancialStatement:
    """
    Standardisiertes Format für einen Finanzbericht (eine Periode).
    Alle Felder sind optional, weil je nach Firma / Provider nicht alles da ist.
    """
    date: date                 # Periodenende
    report_type: str           # "income", "balance_sheet", "cash_flow"
    period_type: str           # "annual", "quarterly"
    source: str                # z.B. "yfinance"

    # Generische Kernfelder
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    free_cash_flow: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None

    # Income Statement
    cost_of_revenue: Optional[float] = None
    research_and_development: Optional[float] = None
    selling_general_and_administrative: Optional[float] = None
    interest_expense: Optional[float] = None
    income_tax_expense: Optional[float] = None

    # Balance Sheet
    cash_and_cash_equivalents: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    property_plant_equipment: Optional[float] = None
    accounts_payable: Optional[float] = None
    current_debt: Optional[float] = None
    long_term_debt: Optional[float] = None
    common_stock: Optional[float] = None
    retained_earnings: Optional[float] = None
    accumulated_other_comprehensive_income: Optional[float] = None

    # Cash Flow Statement
    operating_cash_flow: Optional[float] = None
    depreciation_and_amortization: Optional[float] = None
    stock_based_compensation: Optional[float] = None
    change_in_working_capital: Optional[float] = None
    capital_expenditure: Optional[float] = None
    dividends_paid: Optional[float] = None
    issuance_of_debt: Optional[float] = None
    repayment_of_debt: Optional[float] = None
    issuance_of_stock: Optional[float] = None
    repurchase_of_stock: Optional[float] = None

    # kompletter Roh-Dump aus yfinance (eine Spalte der DataFrame)
    raw_json: Optional[Dict[str, Any]] = None


# ==================== NEUE MACRO DTOs ====================

@dataclass
class ProviderMacroData:
    """
    Standardisiertes Format für Macro-Indikatoren.
    
    Wird verwendet für: VIX, Treasury Yields, USD Index, Gold
    Analog zu ProviderPriceData, aber für Macro-Zeitreihen.
    """
    date: date
    indicator: str  # "VIX", "TNX_10Y", "TYX_30Y", "IRX_3M", "USD_INDEX", "GOLD"
    value: float
    source: str = "yfinance"


@dataclass
class ProviderMacroSnapshot:
    """
    Standardisiertes Format für einen Macro-Snapshot (alle Indikatoren auf einmal).
    
    Analog zu ProviderFundamentalData - ein Snapshot, keine Zeitreihe.
    """
    timestamp: datetime
    vix: Optional[float] = None
    treasury_10y: Optional[float] = None  # ^TNX - Wert in % (z.B. 4.35 = 4.35%)
    treasury_2y: Optional[float] = None   # 2YY=F
    treasury_30y: Optional[float] = None  # ^TYX
    treasury_3m: Optional[float] = None   # ^IRX
    usd_index: Optional[float] = None     # DX-Y.NYB
    gold_price: Optional[float] = None    # GLD oder GC=F


# ==================== INDICATOR CONSTANTS ====================

class MacroIndicators:
    """
    Standard Macro-Indikator Namen.
    Verwende diese Konstanten für Konsistenz im gesamten Codebase.
    """
    # Volatility
    VIX = "VIX"
    
    # Treasury Yields (Werte als Prozent gespeichert, z.B. 4.5 = 4.5%)
    TREASURY_10Y = "TNX_10Y"
    TREASURY_2Y = "TNX_2Y"
    TREASURY_30Y = "TYX_30Y"
    TREASURY_3M = "IRX_3M"
    
    # Yield Curve (abgeleitet: 10Y - 2Y oder 10Y - 3M)
    YIELD_CURVE_SLOPE = "YIELD_CURVE_SLOPE"
    
    # Currency
    USD_INDEX = "USD_INDEX"
    
    # Commodities
    GOLD = "GOLD"
    
    @classmethod
    def all(cls) -> list:
        """Alle Indikator-Namen."""
        return [
            cls.VIX,
            cls.TREASURY_10Y,
            cls.TREASURY_2Y,
            cls.TREASURY_30Y,
            cls.TREASURY_3M,
            cls.USD_INDEX,
            cls.GOLD
        ]
    
    @classmethod
    def yields(cls) -> list:
        """Yield-bezogene Indikatoren."""
        return [
            cls.TREASURY_10Y,
            cls.TREASURY_2Y,
            cls.TREASURY_30Y,
            cls.TREASURY_3M
        ]


# ==================== YAHOO TICKER MAPPINGS ====================

MACRO_TICKER_MAP = {
    "VIX": "^VIX",
    "TNX_10Y": "^TNX",
    "TYX_30Y": "^TYX",
    "IRX_3M": "^IRX",
    "TNX_2Y": "2YY=F",  # 2Y Futures
    "USD_INDEX": "DX-Y.NYB",
    "GOLD": "GLD",      # ETF (zuverlässiger als Futures)
    "GOLD_FUTURES": "GC=F",
}
