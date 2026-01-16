# portfolio_tool/provider_models.py
from dataclasses import dataclass, field
from datetime import date
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