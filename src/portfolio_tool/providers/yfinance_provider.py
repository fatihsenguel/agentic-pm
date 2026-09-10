# portfolio_tool/providers/yfinance_provider.py
import sys
import yfinance as yf
from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional, Dict, Optional, Any
from contextlib import contextmanager

from .base import DataProviderInterface
from ..provider_models import (
    ProviderAssetInfo, ProviderPriceData, ProviderDividendData,
    ProviderSplitData, ProviderSharesData,
    ProviderFundamentalData, ProviderEarningsData, ProviderFinancialStatement,
    ProviderMacroData,
    ProviderMacroSnapshot,
    ProviderFxRate,
)

# (1) WIR BEHALTEN SimpleRateLimiter für die FREQUENZ, safe_int und float für unsave int,float conversation fixes
from .utils import SimpleRateLimiter, safe_float, safe_int, safe_decimal
# (2) WIR IMPORTIEREN den NEUEN Manager für das VOLUMEN/LOGGIN
from portfolio_tool.services.quota_manager import DatabaseQuotaManager

import logging
logger = logging.getLogger(__name__)


# (3) Wir definieren eine eigene Fehlerklasse für Quota-Überschreitungen
class QuotaExceededError(RuntimeError):
    """Eigener Fehler, wenn das Quota überschritten wurde."""
    pass


class YFinanceProvider(DataProviderInterface):
    """
    Konkrete Implementierung des DataProviderInterface für Yahoo Finance.
    Nutzt SimpleRateLimiter für die Frequenz und DatabaseQuotaManager für das Volumen.
    """

    name = "yfinance"

    # (4) Der Konstruktor wird per Dependency Injection angepasst
    def __init__(self, 
                 quota_manager: DatabaseQuotaManager, 
                 per_minute_limit: int = 60):
        """
        Initialisiert den Provider.
        
        Args:
            quota_manager: Ein bereits initialisierter Manager, der an eine 
                           DB-Session und eine pipeline_run_id gebunden ist.
            per_minute_limit: Das Frequenz-Limit für den SimpleRateLimiter.
        """
        # Zeitbasierter Limiter (Frequenz)
        self.limiter = SimpleRateLimiter(per_minute=per_minute_limit)
        
        # Datenbank-basierter Limiter (Volumen & Logging)
        self.quota_manager = quota_manager
        
        print(f"[Provider] YFinanceProvider initialisiert mit {per_minute_limit} Aufrufen/Minute Limit.")

    # (5) --- ALTE GLOBALE QUOTA-LOGIK WURDE VOLLSTÄNDIG ENTFERNT ---
    # (kein _check_daily_quota(), keine globalen Variablen)

    # (6) NEUE ZENTRALE HELFERMETHODE (DRY-Prinzip)
    @contextmanager
    def _execute_api_call(self, endpoint_name: str, asset_ticker: str):
        """
        Ein zentraler Wrapper für JEDEN API-Aufruf.
        Handhabt:
        1. Frequenz-Throttling (SimpleRateLimiter)
        2. Volumen-Quota-Prüfung (DatabaseQuotaManager.can_consume_credit)
        3. Logging (DatabaseQuotaManager.log_api_call)
        """
        credit_consumed_in_db = False
        try:
            # 1. Frequenz-Limit (blockiert, falls nötig)
            self.limiter.wait_for_slot()
            
            # 2. Volumen-Limit (atomare DB-Prüfung)
            if not self.quota_manager.can_consume_credit():
                # Quota ist voll. Loggen und Fehler auslösen.
                error_msg = "Daily quota limit reached"
                print(f"   [Provider-FEHLER] {error_msg}. Call rejected: {endpoint_name} for {asset_ticker}")
                self.quota_manager.log_api_call(
                    endpoint_name=endpoint_name,
                    asset_ticker=asset_ticker,
                    success=False,
                    http_status_code=429, # HTTP 429: Too Many Requests
                    error_message=error_msg,
                    credits_consumed=0 # Es wurde kein Credit verbraucht
                )
                raise QuotaExceededError(error_msg)
            
            # Quota-Credit wurde erfolgreich in der DB gebucht
            credit_consumed_in_db = True
            
            # 3. 'yield' -> Führe den eigentlichen API-Aufruf aus (im 'try'-Block der aufrufenden Methode)
            yield
            
            # 4. Erfolg loggen (wird nur erreicht, wenn 'yield' keinen Fehler wirft)
            self.quota_manager.log_api_call(
                endpoint_name=endpoint_name,
                asset_ticker=asset_ticker,
                success=True,
                http_status_code=200,
                credits_consumed=1
            )
            
        except QuotaExceededError:
            # Quota-Fehler einfach weiterleiten
            raise
        
        except Exception as e:
            # Anderer Fehler (z.B. Netzwerk, yfinance-Fehler)
            print(f"   [Provider-FEHLER] bei {endpoint_name} für {asset_ticker}: {e}", file=sys.stderr)
            
            # Fehler loggen. WICHTIG: Wenn der Credit bereits gebucht wurde (Schritt 2),
            # loggen wir den Aufwand als "verbraucht", auch wenn er fehlschlug.
            self.quota_manager.log_api_call(
                endpoint_name=endpoint_name,
                asset_ticker=asset_ticker,
                success=False,
                http_status_code=500, # Annahme: 500 für Server/Netzwerkfehler
                error_message=str(e),
                credits_consumed=1 if credit_consumed_in_db else 0
            )
            # Fehler weiterleiten, damit die aufrufende Methode ihn fangen kann
            raise

    # (7) Alle öffentlichen Methoden werden an den neuen Wrapper angepasst
    
    def _get_stock_info(self, ticker: str) -> dict:
        """
        Hilfsmethode, um das 'info'-Wörterbuch zu holen.
        Dies ist der eigentliche API-Aufruf.
        """
        print(f"   [Provider] Rufe yf.Ticker({ticker}).info auf...")
        # Der Context Manager wickelt Throttling, Quota und Logging ab
        with self._execute_api_call(endpoint_name="info", asset_ticker=ticker):
            return yf.Ticker(ticker).info

    def get_asset_info(self, ticker: str) -> Optional[ProviderAssetInfo]:
        """Holt Stammdaten für ein Asset (Snapshot, Typ 2)."""
        try:
            # _get_stock_info enthält bereits den Wrapper
            info = self._get_stock_info(ticker)
            
            if not info or 'symbol' not in info:
                print(f"   [Provider-WARNUNG] Keine 'info'-Daten für {ticker} gefunden.", file=sys.stderr)
                return None

            return ProviderAssetInfo(
                sector=info.get('sector'),
                industry=info.get('industry'),
                country=info.get('country'),
                currency=info.get('currency'),
                long_name=info.get('longName')
            )
        except (QuotaExceededError, Exception) as e:
            # Fehler wurde bereits im Wrapper geloggt. Einfach None zurückgeben.
            return None

    def get_daily_prices(self, ticker: str, start: date, end: date) -> List[ProviderPriceData]:
        """Holt tägliche Kursdaten (Zeitreihe, Typ 1)."""
        try:
            # Wrapper für diesen spezifischen Aufruf
            with self._execute_api_call(endpoint_name="history", asset_ticker=ticker):
                print(f"   [Provider] Rufe yf.Ticker({ticker}).history(start={start}, end={end}) auf...")
                stock = yf.Ticker(ticker)
                df = stock.history(start=start, end=end)
            
            if df.empty:
                return []
            
            results = []
            for date_ts, row in df.iterrows():
                results.append(ProviderPriceData(
                    date=date_ts.date(),
                    open=safe_decimal(row['Open']),
                    high=safe_decimal(row['High']),
                    low=safe_decimal(row['Low']),
                    close=safe_decimal(row['Close']),
                    volume=safe_int(row['Volume'])
                ))
            return results
        except (QuotaExceededError, Exception) as e:
            # Fehler wurde bereits im Wrapper geloggt.
            return []

    def get_fx_rates(self, base: str, quote: str, start: date, end: date) -> List[ProviderFxRate]:
        """Daily spot rates, units of `base` per one unit of `quote`.

        Yahoo's symbol for that direction is `{quote}{base}=X`: USDEUR=X
        quotes euros per dollar (checked live 10 September 2026: 0.8624 on
        2026-09-02, against EURUSD=X at 1.15955). Each day's close is the
        rate; nothing is inverted here. Same throttle, quota and logging
        wrapper as prices.
        """
        symbol = f"{quote}{base}=X"
        try:
            with self._execute_api_call(endpoint_name="history", asset_ticker=symbol):
                print(f"   [Provider] Rufe yf.Ticker({symbol}).history(start={start}, end={end}) auf...")
                df = yf.Ticker(symbol).history(start=start, end=end)

            if df.empty:
                return []

            return [
                ProviderFxRate(date=date_ts.date(), rate=safe_decimal(row['Close']))
                for date_ts, row in df.iterrows()
            ]
        except (QuotaExceededError, Exception) as e:
            # Fehler wurde bereits im Wrapper geloggt.
            return []

    def get_dividends(self, ticker: str, since: date | None = None) -> List[ProviderDividendData]:
        """Holt die Dividenden-Historie (Zeitreihe, Typ 1)."""
        try:
            with self._execute_api_call(endpoint_name="dividends", asset_ticker=ticker):
                print(f"   [Provider] Rufe yf.Ticker({ticker}).dividends auf (since={since})...")
                tk = yf.Ticker(ticker)
                dividends_data = tk.dividends
            
            if dividends_data.empty:
                return []
            
            results = []
            for date_ts, amount in dividends_data.items():
                ex_date = date_ts.date()
                if since and ex_date <= since:
                    continue
                results.append(ProviderDividendData(
                    ex_date=ex_date,
                    amount=safe_decimal(str(amount))
                ))
            return sorted(results, key=lambda x: x.ex_date)
        except (QuotaExceededError, Exception) as e:
            return []

    def get_splits(self, ticker: str, since: date | None = None) -> List[ProviderSplitData]:
        """Holt die Split-Historie (Zeitreihe, Typ 1)."""
        try:
            with self._execute_api_call(endpoint_name="splits", asset_ticker=ticker):
                print(f"   [Provider] Rufe yf.Ticker({ticker}).splits auf (since={since})...")
                tk = yf.Ticker(ticker)
                splits_data = tk.splits
            
            if splits_data.empty:
                return []
            
            results = []
            for date_ts, ratio in splits_data.items():
                split_date = date_ts.date()
                if since and split_date <= since:
                    continue
                results.append(ProviderSplitData(
                    date=split_date,
                    ratio_str=f"{safe_float(ratio)}:1"
                ))
            return sorted(results, key=lambda x: x.date)
        except (QuotaExceededError, Exception) as e:
            return []

    def get_shares_history(self, ticker: str, since: date | None = None) -> List[ProviderSharesData]:
        """Holt die Historie der Aktienanzahl (Zeitreihe, Typ 1)."""
        try:
            with self._execute_api_call(endpoint_name="get_shares_full", asset_ticker=ticker):
                print(f"   [Provider] Rufe yf.Ticker({ticker}).get_shares_full auf (since={since})...")
                stock = yf.Ticker(ticker)
                shares_df = stock.get_shares_full(start="1900-01-01") 
            
            if shares_df is None or shares_df.empty:
                return []

            results = []
            for date_ts, shares_val in shares_df.items():
                report_date = date_ts.date()
                if since and report_date <= since:
                    continue
                try:
                    shares = safe_int(shares_val)
                    if shares is None:
                        print(f"   [Provider-WARNUNG] Shares-Wert für {ticker} am {report_date} ist NaN/None, überspringe.", file=sys.stderr)
                        continue
                    results.append(
                        ProviderSharesData(
                            date=report_date,
                            shares=shares
                        )
                    )
                except (TypeError, ValueError) as e:
                    print(f"   [Provider-WARNUNG] Konnte Shares-Daten für {ticker} am {report_date} nicht parsen: {e}", file=sys.stderr)
                    continue
            return sorted(results, key=lambda x: x.date)
        except (QuotaExceededError, Exception) as e:
            return []

    def get_fundamental_data(self, ticker: str) -> Optional[ProviderFundamentalData]:
        """Holt einen Snapshot der Fundamentaldaten (beta)."""
        try:
            # Nutzt _get_stock_info, das bereits den Wrapper enthält
            info = self._get_stock_info(ticker) 
            if not info:
                return None

            beta = info.get('beta')
            
            return ProviderFundamentalData(
                market_cap=None, 
                forward_pe=None,
                trailing_eps=None,
                beta=safe_decimal(str(beta)) if beta is not None else None
            )
        except (QuotaExceededError, Exception) as e:
            return None

    def get_quarterly_earnings(self, ticker: str, since: date | None = None) -> List[ProviderEarningsData]:
        """Holt die historische Zeitreihe der Quartalsberichte."""
        try:
            with self._execute_api_call(endpoint_name="quarterly_financials", asset_ticker=ticker):
                print(f"   [Provider] Rufe yf.Ticker({ticker}).quarterly_financials auf (since={since})...")
                stock = yf.Ticker(ticker)
                q_earnings_df = stock.quarterly_financials.T
            
            if q_earnings_df.empty:
                return []
                
            results = []
            for date_ts, row in q_earnings_df.iterrows():
                report_date = date_ts.date()
                if since and report_date <= since:
                    continue
                try:
                    revenue = safe_int(row.get('Total Revenue', 0))
                    basic_eps = safe_decimal(str(row.get('Basic EPS', 0.0)))
                    results.append(
                        ProviderEarningsData(
                            report_date=report_date,
                            revenue=revenue,
                            basic_eps=basic_eps
                        )
                    )
                except (TypeError, ValueError, KeyError) as e:
                    print(f"   [Provider-WARNUNG] Konnte Earnings-Daten für {ticker} am {report_date} nicht parsen: {e}", file=sys.stderr)
                    continue
            return sorted(results, key=lambda x: x.report_date)
        except (QuotaExceededError, Exception) as e:
            return []

    def get_financial_statements(
        self,
        ticker: str,
        report_type: str,
        period_type: str,
        since: date | None = None,
    ) -> List[ProviderFinancialStatement]:
        """
        Holt Financial Statements via yfinance:
        - report_type: "income", "balance_sheet", "cash_flow"
        - period_type: "annual" oder "quarterly"
        """
        try:
            endpoint_name = f"{period_type}_{report_type}_statements"
            with self._execute_api_call(endpoint_name=endpoint_name, asset_ticker=ticker):
                tk = yf.Ticker(ticker)

                if report_type == "income":
                    df = tk.financials if period_type == "annual" else tk.quarterly_financials
                elif report_type == "balance_sheet":
                    df = tk.balance_sheet if period_type == "annual" else tk.quarterly_balance_sheet
                elif report_type == "cash_flow":
                    df = tk.cashflow if period_type == "annual" else tk.quarterly_cashflow
                else:
                    return []

            if df is None or df.empty:
                return []

            results: List[ProviderFinancialStatement] = []

            # yfinance: Index = Line Items, Columns = Perioden (Timestamps)
            for col in df.columns:
                col_date = col.date() if hasattr(col, "date") else col
                if since and isinstance(col_date, date) and col_date <= since:
                    continue

                series = df[col]
                raw = series.to_dict()

                # Basisfelder (wenn vorhanden)
                revenue = (
                    raw.get("Total Revenue")
                    or raw.get("TotalRevenue")
                    or raw.get("Revenue")
                )
                net_income = raw.get("Net Income") or raw.get("NetIncome")
                eps = raw.get("Basic EPS") or raw.get("BasicEPS")
                total_assets = raw.get("Total Assets") or raw.get("TotalAssets")
                total_liabilities = (
                    raw.get("Total Liabilities Net Minority Interest")
                    or raw.get("Total Liabilities")
                    or raw.get("TotalLiab")
                )

                # Default kwargs
                kwargs: dict = {}

                if report_type == "income":
                    kwargs.update(
                        dict(
                            cost_of_revenue=raw.get("Cost Of Revenue") or raw.get("CostOfRevenue"),
                            research_and_development=raw.get("Research Development") or raw.get("ResearchAndDevelopment"),
                            selling_general_and_administrative=raw.get("Selling General Administrative") or raw.get("SellingGeneralAdministrative"),
                            interest_expense=raw.get("Interest Expense") or raw.get("InterestExpense"),
                            income_tax_expense=raw.get("Income Tax Expense") or raw.get("IncomeTaxExpense"),
                        )
                    )

                elif report_type == "balance_sheet":
                    kwargs.update(
                        dict(
                            cash_and_cash_equivalents=raw.get("Cash And Cash Equivalents") or raw.get("CashAndCashEquivalents"),
                            accounts_receivable=raw.get("Net Receivables") or raw.get("Accounts Receivable") or raw.get("NetReceivables"),
                            inventory=raw.get("Inventory"),
                            property_plant_equipment=raw.get("Property Plant Equipment") or raw.get("PropertyPlantEquipment"),
                            accounts_payable=raw.get("Accounts Payable") or raw.get("AccountsPayable"),
                            current_debt=raw.get("Short Long Term Debt") or raw.get("ShortTermDebt"),
                            long_term_debt=raw.get("Long Term Debt") or raw.get("LongTermDebt"),
                            common_stock=raw.get("Common Stock") or raw.get("CommonStock"),
                            retained_earnings=raw.get("Retained Earnings") or raw.get("RetainedEarnings"),
                            accumulated_other_comprehensive_income=(
                                raw.get("Accumulated Other Comprehensive Income Loss")
                                or raw.get("AccumulatedOtherComprehensiveIncomeLoss")
                            ),
                        )
                    )

                elif report_type == "cash_flow":
                    kwargs.update(
                        dict(
                            operating_cash_flow=(
                                raw.get("Total Cash From Operating Activities")
                                or raw.get("Net Cash Provided by Operating Activities")
                            ),
                            depreciation_and_amortization=raw.get("Depreciation") or raw.get("Depreciation Amortization"),
                            stock_based_compensation=raw.get("Stock Based Compensation") or raw.get("StockBasedCompensation"),
                            change_in_working_capital=raw.get("Change In Working Capital") or raw.get("ChangeInWorkingCapital"),
                            capital_expenditure=raw.get("Capital Expenditures") or raw.get("CapitalExpenditures"),
                            dividends_paid=raw.get("Dividends Paid") or raw.get("DividendsPaid"),
                            issuance_of_debt=raw.get("Issuance Of Debt") or raw.get("IssuanceOfDebt"),
                            repayment_of_debt=raw.get("Repayment Of Debt") or raw.get("RepaymentOfDebt"),
                            issuance_of_stock=raw.get("Issuance Of Stock") or raw.get("IssuanceOfStock"),
                            repurchase_of_stock=raw.get("Repurchase Of Stock") or raw.get("RepurchaseOfStock"),
                            free_cash_flow=raw.get("Free Cash Flow") or raw.get("FreeCashFlow"),
                        )
                    )

                dto = ProviderFinancialStatement(
                    date=col_date,
                    report_type=report_type,
                    period_type=period_type,
                    source="yfinance",
                    revenue=safe_float(revenue) if revenue is not None else None,
                    net_income=safe_float(net_income) if net_income is not None else None,
                    eps=safe_float(eps) if eps is not None else None,
                    free_cash_flow=safe_float(kwargs.pop("free_cash_flow")) if "free_cash_flow" in kwargs and kwargs["free_cash_flow"] is not None else None,
                    total_assets=safe_float(total_assets) if total_assets is not None else None,
                    total_liabilities=safe_float(total_liabilities) if total_liabilities is not None else None,
                    raw_json=raw,
                    **{
                        k: safe_float(v) if v is not None else None
                        for k, v in kwargs.items()
                    },
                )
                results.append(dto)

            return results

        except (QuotaExceededError, Exception):
            return []
    # =========================================================================
    # MACRO DATA IMPLEMENTATION (INTEGRATED)
    # =========================================================================

    def get_vix_data(self, start: date, end: date) -> List[ProviderMacroData]:
        """Holt VIX (Volatility Index) Zeitreihe."""
        try:
            with self._execute_api_call(endpoint_name="vix_history", asset_ticker="^VIX"):
                ticker = yf.Ticker("^VIX")
                df = ticker.history(start=start, end=end)
            
            if df.empty:
                logger.warning("No VIX data returned from yfinance")
                return []
            
            results = []
            for idx, row in df.iterrows():
                value = safe_float(row.get('Close'))
                if value is not None:
                    results.append(ProviderMacroData(
                        date=idx.date(),
                        indicator="VIX",
                        value=value,
                        source="yfinance"
                    ))
            return results
        except Exception as e:
            logger.error(f"Error fetching VIX data: {e}")
            return []

    def get_treasury_yields(self, start: date, end: date) -> Dict[str, List[ProviderMacroData]]:
        """Holt Treasury Yields für mehrere Laufzeiten."""
        yield_tickers = {
            "TNX_10Y": "^TNX",
            "TYX_30Y": "^TYX",
            "IRX_3M": "^IRX"
        }
        
        results = {}
        for yield_name, ticker_symbol in yield_tickers.items():
            try:
                with self._execute_api_call(endpoint_name=f"treasury_{yield_name.lower()}", asset_ticker=ticker_symbol):
                    ticker = yf.Ticker(ticker_symbol)
                    df = ticker.history(start=start, end=end)
                
                if df.empty:
                    results[yield_name] = []
                    continue
                
                data_points = []
                for idx, row in df.iterrows():
                    value = safe_float(row.get('Close'))
                    if value is not None:
                        data_points.append(ProviderMacroData(
                            date=idx.date(),
                            indicator=yield_name,
                            value=value,
                            source="yfinance"
                        ))
                results[yield_name] = data_points
            except Exception as e:
                logger.error(f"Error fetching {yield_name}: {e}")
                results[yield_name] = []
        return results

    def get_macro_snapshot(self) -> Optional[ProviderMacroSnapshot]:
        """Holt aktuellen Snapshot aller Macro-Indikatoren."""
        snapshot = ProviderMacroSnapshot(timestamp=datetime.utcnow())
        indicators = {
            "vix": "^VIX",
            "treasury_10y": "^TNX",
            "treasury_30y": "^TYX",
            "treasury_3m": "^IRX",
            "usd_index": "DX-Y.NYB",
            "gold_price": "GLD"
        }
        
        for attr_name, ticker_symbol in indicators.items():
            try:
                with self._execute_api_call(endpoint_name=f"macro_snapshot_{attr_name}", asset_ticker=ticker_symbol):
                    ticker = yf.Ticker(ticker_symbol)
                    hist = ticker.history(period="5d")
                
                if not hist.empty:
                    value = safe_float(hist['Close'].iloc[-1])
                    if value is not None:
                        setattr(snapshot, attr_name, value)
            except Exception as e:
                logger.warning(f"Could not fetch {attr_name}: {e}")
        
        return snapshot

    def get_macro_indicator(self, indicator: str, start: date, end: date) -> List[ProviderMacroData]:
        """Holt einen spezifischen Macro-Indikator."""
        ticker_map = {
            "VIX": "^VIX",
            "TNX_10Y": "^TNX",
            "TYX_30Y": "^TYX",
            "IRX_3M": "^IRX",
            "TNX_2Y": "2YY=F",
            "USD_INDEX": "DX-Y.NYB",
            "GOLD": "GLD",
        }
        
        ticker_symbol = ticker_map.get(indicator)
        if not ticker_symbol:
            logger.warning(f"Unknown macro indicator: {indicator}")
            return []
        
        try:
            with self._execute_api_call(endpoint_name=f"macro_{indicator.lower()}", asset_ticker=ticker_symbol):
                ticker = yf.Ticker(ticker_symbol)
                df = ticker.history(start=start, end=end)
            
            if df.empty:
                return []
            
            results = []
            for idx, row in df.iterrows():
                value = safe_float(row.get('Close'))
                if value is not None:
                    results.append(ProviderMacroData(
                        date=idx.date(),
                        indicator=indicator,
                        value=value,
                        source="yfinance"
                    ))
            return results
        except Exception as e:
            logger.error(f"Error fetching {indicator}: {e}")
            return []
        
    



