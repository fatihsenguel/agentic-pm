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

# SimpleRateLimiter bounds the call frequency; safe_int, safe_float and
# safe_decimal guard the conversions of what the library returns.
from .utils import SimpleRateLimiter, safe_float, safe_int, safe_decimal
# The database-backed manager bounds the daily volume and logs every call.
from portfolio_tool.services.quota_manager import DatabaseQuotaManager

import logging
logger = logging.getLogger(__name__)


# Raised when the daily quota is exhausted.
class QuotaExceededError(RuntimeError):
    """Raised when the daily quota has been exceeded."""
    pass


class YFinanceProvider(DataProviderInterface):
    """
    The DataProviderInterface implementation for Yahoo Finance.
    SimpleRateLimiter bounds the frequency and DatabaseQuotaManager the volume.
    """

    name = "yfinance"

    # The quota manager is injected, bound to its session and run.
    def __init__(self,
                 quota_manager: DatabaseQuotaManager, 
                 per_minute_limit: int = 60):
        """
        Args:
            quota_manager: an initialised manager bound to a DB session
                           and a pipeline_run_id.
            per_minute_limit: the frequency limit for the SimpleRateLimiter.
        """
        # Time-based limiter (frequency)
        self.limiter = SimpleRateLimiter(per_minute=per_minute_limit)

        # Database-backed limiter (volume and logging)
        self.quota_manager = quota_manager

        print(f"[Provider] YFinanceProvider initialised with a limit of {per_minute_limit} calls per minute.")

    # There is no global quota state and no daily check of the provider's
    # own: the volume limit is the manager's.

    # The one wrapper every API call goes through.
    @contextmanager
    def _execute_api_call(self, endpoint_name: str, asset_ticker: str):
        """
        The wrapper around every API call. It handles:
        1. frequency throttling (SimpleRateLimiter)
        2. the volume quota check (DatabaseQuotaManager.can_consume_credit)
        3. logging (DatabaseQuotaManager.log_api_call)
        """
        credit_consumed_in_db = False
        try:
            # 1. Frequency limit (blocks if necessary)
            self.limiter.wait_for_slot()

            # 2. Volume limit (an atomic check in the database)
            if not self.quota_manager.can_consume_credit():
                # The quota is exhausted: log it and raise.
                error_msg = "Daily quota limit reached"
                print(f"   [Provider error] {error_msg}. Call rejected: {endpoint_name} for {asset_ticker}")
                self.quota_manager.log_api_call(
                    endpoint_name=endpoint_name,
                    asset_ticker=asset_ticker,
                    success=False,
                    http_status_code=429, # HTTP 429: Too Many Requests
                    error_message=error_msg,
                    credits_consumed=0 # No credit was consumed
                )
                raise QuotaExceededError(error_msg)

            # The quota credit has been booked in the database
            credit_consumed_in_db = True

            # 3. 'yield': the actual API call runs in the calling method's 'try' block
            yield

            # 4. Log the success (reached only if 'yield' raised nothing)
            self.quota_manager.log_api_call(
                endpoint_name=endpoint_name,
                asset_ticker=asset_ticker,
                success=True,
                http_status_code=200,
                credits_consumed=1
            )
            
        except QuotaExceededError:
            # A quota error is passed on as it is
            raise

        except Exception as e:
            # Any other error (network, yfinance)
            print(f"   [Provider error] at {endpoint_name} for {asset_ticker}: {e}", file=sys.stderr)

            # Log the error. If the credit was already booked (step 2), the
            # call is logged as consumed even though it failed.
            self.quota_manager.log_api_call(
                endpoint_name=endpoint_name,
                asset_ticker=asset_ticker,
                success=False,
                http_status_code=500, # 500 assumed for server and network errors
                error_message=str(e),
                credits_consumed=1 if credit_consumed_in_db else 0
            )
            # Re-raise so the calling method can catch it
            raise

    # Every public method goes through the wrapper.

    def _get_stock_info(self, ticker: str) -> dict:
        """
        Fetches the 'info' dictionary. This is the actual API call.
        """
        print(f"   [Provider] Calling yf.Ticker({ticker}).info...")
        # The context manager handles throttling, quota and logging
        with self._execute_api_call(endpoint_name="info", asset_ticker=ticker):
            return yf.Ticker(ticker).info

    def get_asset_info(self, ticker: str) -> Optional[ProviderAssetInfo]:
        """Fetches master data for an asset (snapshot, type 2)."""
        try:
            # _get_stock_info already carries the wrapper
            info = self._get_stock_info(ticker)

            if not info or 'symbol' not in info:
                print(f"   [Provider warning] No 'info' data found for {ticker}.", file=sys.stderr)
                return None

            return ProviderAssetInfo(
                sector=info.get('sector'),
                industry=info.get('industry'),
                country=info.get('country'),
                currency=info.get('currency'),
                long_name=info.get('longName')
            )
        except (QuotaExceededError, Exception) as e:
            # The error was logged in the wrapper. Return None.
            return None

    def get_daily_prices(self, ticker: str, start: date, end: date) -> List[ProviderPriceData]:
        """Daily closes as traded (expected_values.md D19, Part 9).

        `auto_adjust=False`, because the library's default replaces the
        close with the dividend-adjusted close: a stored figure for a past
        date would then be lower than the exchange's print by every later
        dividend, and would change on each refetch after an ex-dividend
        date. Part 9 B has the rows where that had happened. `Close` with
        the flag off is the print, split-adjusted only; `Adj Close` is not
        read.
        """
        try:
            # The wrapper for this specific call
            with self._execute_api_call(endpoint_name="history", asset_ticker=ticker):
                print(f"   [Provider] Calling yf.Ticker({ticker}).history(start={start}, end={end}, auto_adjust=False)...")
                stock = yf.Ticker(ticker)
                df = stock.history(start=start, end=end, auto_adjust=False)
            
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
            # The error was logged in the wrapper.
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
                print(f"   [Provider] Calling yf.Ticker({symbol}).history(start={start}, end={end})...")
                df = yf.Ticker(symbol).history(start=start, end=end)

            if df.empty:
                return []

            return [
                ProviderFxRate(date=date_ts.date(), rate=safe_decimal(row['Close']))
                for date_ts, row in df.iterrows()
            ]
        except (QuotaExceededError, Exception) as e:
            # The error was logged in the wrapper.
            return []

    def get_dividends(self, ticker: str, since: date | None = None) -> List[ProviderDividendData]:
        """Fetches the dividend history (time series, type 1)."""
        try:
            with self._execute_api_call(endpoint_name="dividends", asset_ticker=ticker):
                print(f"   [Provider] Calling yf.Ticker({ticker}).dividends (since={since})...")
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
        """Fetches the split history (time series, type 1)."""
        try:
            with self._execute_api_call(endpoint_name="splits", asset_ticker=ticker):
                print(f"   [Provider] Calling yf.Ticker({ticker}).splits (since={since})...")
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
        """Fetches the history of shares outstanding (time series, type 1)."""
        try:
            with self._execute_api_call(endpoint_name="get_shares_full", asset_ticker=ticker):
                print(f"   [Provider] Calling yf.Ticker({ticker}).get_shares_full (since={since})...")
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
                        print(f"   [Provider warning] Shares value for {ticker} on {report_date} is NaN or None, skipping.", file=sys.stderr)
                        continue
                    results.append(
                        ProviderSharesData(
                            date=report_date,
                            shares=shares
                        )
                    )
                except (TypeError, ValueError) as e:
                    print(f"   [Provider warning] Could not parse the shares data for {ticker} on {report_date}: {e}", file=sys.stderr)
                    continue
            return sorted(results, key=lambda x: x.date)
        except (QuotaExceededError, Exception) as e:
            return []

    def get_fundamental_data(self, ticker: str) -> Optional[ProviderFundamentalData]:
        """Fetches a snapshot of the fundamentals (beta)."""
        try:
            # Uses _get_stock_info, which already carries the wrapper
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
        """Fetches the historical series of quarterly reports."""
        try:
            with self._execute_api_call(endpoint_name="quarterly_financials", asset_ticker=ticker):
                print(f"   [Provider] Calling yf.Ticker({ticker}).quarterly_financials (since={since})...")
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
                    print(f"   [Provider warning] Could not parse the earnings data for {ticker} on {report_date}: {e}", file=sys.stderr)
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
        Fetches financial statements via yfinance:
        - report_type: "income", "balance_sheet", "cash_flow"
        - period_type: "annual" or "quarterly"
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

            # yfinance: index = line items, columns = periods (timestamps)
            for col in df.columns:
                col_date = col.date() if hasattr(col, "date") else col
                if since and isinstance(col_date, date) and col_date <= since:
                    continue

                series = df[col]
                raw = series.to_dict()

                # Base fields (where present)
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
                    source=self.name,
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
        """Fetches the VIX (volatility index) time series."""
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
                        source=self.name
                    ))
            return results
        except Exception as e:
            logger.error(f"Error fetching VIX data: {e}")
            return []

    def get_treasury_yields(self, start: date, end: date) -> Dict[str, List[ProviderMacroData]]:
        """Fetches Treasury yields for several maturities."""
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
                            source=self.name
                        ))
                results[yield_name] = data_points
            except Exception as e:
                logger.error(f"Error fetching {yield_name}: {e}")
                results[yield_name] = []
        return results

    def get_macro_snapshot(self) -> Optional[ProviderMacroSnapshot]:
        """Fetches the current snapshot of every macro indicator."""
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
        """Fetches one macro indicator."""
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
                        source=self.name
                    ))
            return results
        except Exception as e:
            logger.error(f"Error fetching {indicator}: {e}")
            return []
        
    



