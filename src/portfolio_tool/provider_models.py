# src/portfolio_tool/provider_models.py
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List

"""
DTO Definitions (Data Transfer Objects).
Contains both Provider DTOs (Raw) and Domain DTOs (Internal).
"""

# =============================================================================
# 1. PROVIDER DTOS (Raw data from External APIs)
#    These match the structure returned by yfinance/APIs.
# =============================================================================

@dataclass
class ProviderAssetInfo:
    """Standardized format for Asset Metadata."""
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    long_name: Optional[str] = None

@dataclass
class ProviderPriceData:
    """Standardized format for daily prices (Raw)."""
    date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Decimal = None  
    volume: Optional[int] = None

@dataclass
class ProviderFxRate:
    """One spot rate for one day, as the provider quotes it: units of the
    portfolio's base currency per one unit of the asset's currency (the
    fx_rates convention, expected_values.md D17). Direction is the
    provider adapter's to get right; nothing downstream inverts."""
    date: date
    rate: Decimal

@dataclass
class ProviderDividendData:
    ex_date: date
    amount: Decimal

@dataclass
class ProviderSplitData:
    date: date
    ratio_str: str 

@dataclass
class ProviderSharesData:
    date: date
    shares: Optional[int] = None

@dataclass
class ProviderFundamentalData:
    market_cap: Optional[int] = None
    forward_pe: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    trailing_eps: Optional[Decimal] = None

@dataclass
class ProviderEarningsData:
    report_date: date
    revenue: Optional[int] = None
    basic_eps: Optional[Decimal] = None

@dataclass
class ProviderFinancialStatement:
    date: date
    report_type: str       
    period_type: str       
    source: str
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    free_cash_flow: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    raw_json: Optional[Dict[str, Any]] = None

@dataclass
class ProviderMacroData:
    date: date
    indicator: str
    value: float
    # The provider's name, as on every other DTO: required, so a row whose
    # origin nobody stated cannot be built.
    source: str

@dataclass
class ProviderMacroSnapshot:
    timestamp: datetime
    vix: Optional[float] = None
    treasury_10y: Optional[float] = None
    treasury_2y: Optional[float] = None
    treasury_30y: Optional[float] = None
    treasury_3m: Optional[float] = None
    usd_index: Optional[float] = None
    gold_price: Optional[float] = None

# =============================================================================
# 2. DOMAIN DTOS (Internal Contract)
#    These are what DataAgent and Database expect.
# =============================================================================

@dataclass
class PriceData:
    """
    REQUIRED by DataAgent / Database.
    This is the internal representation of a price record.
    It INCLUDES the ticker, which ProviderPriceData often lacks.
    """
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: Optional[float] = None

@dataclass
class FinancialStatementData:
    """REQUIRED by DataAgent."""
    ticker: str
    date: date
    period: str
    report_type: str
    currency: str
    data: Dict[str, Any]

@dataclass
class FundamentalData:
    """REQUIRED by DataAgent."""
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    currency: str = "USD"
    beta: Optional[float] = None
    pe_ratio: Optional[float] = None

# =============================================================================
# 3. COMPATIBILITY ALIASES (Fixes ImportError)
# =============================================================================

# This fixes "cannot import name 'FinancialData'"
FinancialData = FinancialStatementData

# =============================================================================
# 4. CONSTANTS
# =============================================================================

class MacroIndicators:
    VIX = "VIX"
    TREASURY_10Y = "TNX_10Y"
    TREASURY_2Y = "TNX_2Y"
    TREASURY_30Y = "TYX_30Y"
    TREASURY_3M = "IRX_3M"
    YIELD_CURVE_SLOPE = "YIELD_CURVE_SLOPE"
    USD_INDEX = "USD_INDEX"
    GOLD = "GOLD"
    
    @classmethod
    def all(cls) -> list:
        return [cls.VIX, cls.TREASURY_10Y, cls.TREASURY_2Y, cls.TREASURY_30Y, 
                cls.TREASURY_3M, cls.USD_INDEX, cls.GOLD]

MACRO_TICKER_MAP = {
    "VIX": "^VIX",
    "TNX_10Y": "^TNX",
    "TYX_30Y": "^TYX",
    "IRX_3M": "^IRX",
    "TNX_2Y": "2YY=F",
    "USD_INDEX": "DX-Y.NYB",
    "GOLD": "GLD",
    "GOLD_FUTURES": "GC=F",
}