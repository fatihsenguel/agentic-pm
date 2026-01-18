"""
SNIPPET: providers/yfinance_provider.py
PURPOSE: Yahoo Finance API implementation with rate limiting and quota management
PATTERN: Context Manager for API calls + DTO transformation + Error handling
"""

import yfinance as yf
from contextlib import contextmanager
from .base import DataProviderInterface
from ..provider_models import (
    ProviderAssetInfo, ProviderPriceData, ProviderFundamentalData,
    ProviderEarningsData, ProviderFinancialStatement
)
from .utils import SimpleRateLimiter, safe_float, safe_int, safe_decimal
from portfolio_tool.services.quota_manager import DatabaseQuotaManager

class QuotaExceededError(RuntimeError):
    """Raised when daily API quota is exceeded."""
    pass

class YFinanceProvider(DataProviderInterface):
    """
    IMPLEMENTATION: Yahoo Finance provider with dual rate limiting.
    
    Rate Limiting Strategy:
    1. FREQUENCY: SimpleRateLimiter (60 calls/minute) - in-memory, time-based
    2. VOLUME: DatabaseQuotaManager (daily quota) - DB-backed, persistent
    
    Error Handling:
    - Logs ALL API calls to database (success + failures)
    - Returns empty lists/None on errors (never crashes)
    - Raises QuotaExceededError when quota exhausted
    """
    
    def __init__(self, quota_manager: DatabaseQuotaManager, per_minute_limit: int = 60):
        """
        Dependency Injection:
        - quota_manager: DB-backed quota tracker (bound to pipeline_run_id)
        - per_minute_limit: Time-based throttling
        """
        self.limiter = SimpleRateLimiter(per_minute=per_minute_limit)
        self.quota_manager = quota_manager
    
    # ==================== CORE PATTERN: API CALL WRAPPER ====================
    
    @contextmanager
    def _execute_api_call(self, endpoint_name: str, asset_ticker: str):
        """
        CONTEXT MANAGER: Wraps EVERY API call with rate limiting + logging.
        
        Flow:
        1. Frequency check: limiter.wait_for_slot() → blocks if too fast
        2. Quota check: quota_manager.can_consume_credit() → False if quota exhausted
        3. Credit booking: Atomically reserves 1 credit in DB
        4. Yield: Execute actual API call
        5. Success logging: quota_manager.log_api_call(success=True, credits=1)
        
        Error Handling:
        - QuotaExceededError: Logged with status 429, credits=0
        - Other errors: Logged with status 500, credits=1 (already consumed)
        """
        credit_consumed_in_db = False
        try:
            # Step 1: Frequency throttling
            self.limiter.wait_for_slot()
            
            # Step 2: Quota check (atomic DB operation)
            if not self.quota_manager.can_consume_credit():
                error_msg = "Daily quota limit reached"
                self.quota_manager.log_api_call(
                    endpoint_name=endpoint_name,
                    asset_ticker=asset_ticker,
                    success=False,
                    http_status_code=429,  # Too Many Requests
                    error_message=error_msg,
                    credits_consumed=0
                )
                raise QuotaExceededError(error_msg)
            
            credit_consumed_in_db = True
            
            # Step 3: Execute API call (caller's code runs here)
            yield
            
            # Step 4: Log success
            self.quota_manager.log_api_call(
                endpoint_name=endpoint_name,
                asset_ticker=asset_ticker,
                success=True,
                http_status_code=200,
                credits_consumed=1
            )
            
        except QuotaExceededError:
            raise  # Re-raise quota errors
        
        except Exception as e:
            # Log failure (credit already consumed if quota check passed)
            self.quota_manager.log_api_call(
                endpoint_name=endpoint_name,
                asset_ticker=asset_ticker,
                success=False,
                http_status_code=500,
                error_message=str(e),
                credits_consumed=1 if credit_consumed_in_db else 0
            )
            raise
    
    # ==================== PROVIDER IMPLEMENTATIONS ====================
    
    def get_asset_info(self, ticker: str) -> Optional[ProviderAssetInfo]:
        """
        Fetches company metadata from yfinance.
        Returns: ProviderAssetInfo or None on error
        """
        try:
            with self._execute_api_call(endpoint_name="info", asset_ticker=ticker):
                info = yf.Ticker(ticker).info
            
            if not info or 'symbol' not in info:
                return None
            
            return ProviderAssetInfo(
                sector=info.get('sector'),
                industry=info.get('industry'),
                country=info.get('country'),
                currency=info.get('currency'),
                long_name=info.get('longName')
            )
        except (QuotaExceededError, Exception):
            return None
    
    def get_daily_prices(self, ticker: str, start: date, end: date) -> List[ProviderPriceData]:
        """
        Fetches OHLCV bars from yfinance.
        Returns: List[ProviderPriceData] or [] on error
        
        Transformation:
        yfinance DataFrame → List[ProviderPriceData(date, open, high, low, close, volume)]
        """
        try:
            with self._execute_api_call(endpoint_name="history", asset_ticker=ticker):
                stock = yf.Ticker(ticker)
                df = stock.history(start=start, end=end)
            
            if df.empty:
                return []
            
            results = []
            for idx, row in df.iterrows():
                results.append(ProviderPriceData(
                    date=idx.date(),
                    open=Decimal(str(row['Open'])),
                    high=Decimal(str(row['High'])),
                    low=Decimal(str(row['Low'])),
                    close=Decimal(str(row['Close'])),
                    volume=int(row['Volume'])
                ))
            return results
            
        except (QuotaExceededError, Exception):
            return []
    
    def get_fundamental_data(self, ticker: str) -> Optional[ProviderFundamentalData]:
        """
        Fetches snapshot metrics (beta, market cap, P/E).
        Returns: ProviderFundamentalData or None on error
        """
        try:
            with self._execute_api_call(endpoint_name="info", asset_ticker=ticker):
                info = yf.Ticker(ticker).info
            
            return ProviderFundamentalData(
                beta=safe_float(info.get('beta')),
                market_cap=safe_int(info.get('marketCap')),
                pe_ratio=safe_float(info.get('trailingPE')),
                # ... other metrics
            )
        except (QuotaExceededError, Exception):
            return None
    
    def get_quarterly_earnings(self, ticker: str, since: date | None = None) -> List[ProviderEarningsData]:
        """
        Fetches quarterly earnings history.
        Returns: List[ProviderEarningsData(report_date, revenue, basic_eps)]
        
        Transformation:
        yfinance DataFrame (transposed) → List[ProviderEarningsData]
        """
        try:
            with self._execute_api_call(endpoint_name="quarterly_financials", asset_ticker=ticker):
                stock = yf.Ticker(ticker)
                q_earnings_df = stock.quarterly_financials.T  # Transpose: columns → rows
            
            if q_earnings_df.empty:
                return []
            
            results = []
            for date_ts, row in q_earnings_df.iterrows():
                report_date = date_ts.date()
                if since and report_date <= since:
                    continue
                
                results.append(ProviderEarningsData(
                    report_date=report_date,
                    revenue=safe_int(row.get('Total Revenue', 0)),
                    basic_eps=safe_decimal(str(row.get('Basic EPS', 0.0)))
                ))
            
            return sorted(results, key=lambda x: x.report_date)
            
        except (QuotaExceededError, Exception):
            return []
    
    def get_financial_statements(
        self, ticker: str, report_type: str, period_type: str, since: date | None = None
    ) -> List[ProviderFinancialStatement]:
        """
        Fetches income/balance/cashflow statements.
        
        Complexity:
        - 3 report types × 2 frequencies = 6 different yfinance properties
        - 35+ financial metrics per statement
        - Handles multiple field name variations (e.g., "Total Revenue" vs "TotalRevenue")
        
        Returns: List[ProviderFinancialStatement] with all metrics, or [] on error
        """
        try:
            endpoint_name = f"{period_type}_{report_type}_statements"
            with self._execute_api_call(endpoint_name=endpoint_name, asset_ticker=ticker):
                tk = yf.Ticker(ticker)
                
                # Select correct yfinance property
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
            
            # yfinance structure: Index=Line Items, Columns=Periods (timestamps)
            for col in df.columns:
                col_date = col.date() if hasattr(col, "date") else col
                if since and isinstance(col_date, date) and col_date <= since:
                    continue
                
                series = df[col]
                raw = series.to_dict()
                
                # Extract metrics (handles field name variations)
                revenue = raw.get("Total Revenue") or raw.get("TotalRevenue") or raw.get("Revenue")
                net_income = raw.get("Net Income") or raw.get("NetIncome")
                # ... (35+ metrics with fallback field names)
                
                dto = ProviderFinancialStatement(
                    date=col_date,
                    report_type=report_type,
                    period_type=period_type,
                    source="yfinance",
                    revenue=safe_float(revenue) if revenue is not None else None,
                    net_income=safe_float(net_income) if net_income is not None else None,
                    # ... 33 more fields
                    raw_json=raw  # Store full dict for future extensibility
                )
                results.append(dto)
            
            return results
            
        except (QuotaExceededError, Exception):
            return []

# ==================== KEY DESIGN PATTERNS ====================
"""
1. CONTEXT MANAGER PATTERN:
   - _execute_api_call() wraps ALL API calls
   - DRY: Rate limiting + logging logic in ONE place
   - Automatic cleanup (logging) even on exceptions

2. DUAL RATE LIMITING:
   - SimpleRateLimiter: In-memory, fast, per-minute
   - DatabaseQuotaManager: Persistent, daily, multi-process safe

3. SAFE TRANSFORMATION:
   - safe_float(), safe_int(), safe_decimal() prevent crashes on bad data
   - Returns empty lists/None on errors (never crashes agent)
   - All errors logged to DB (audit trail)

4. DTO TRANSFORMATION:
   - yfinance returns: DataFrames, dicts, timestamps
   - Provider returns: Clean DTOs (ProviderPriceData, etc.)
   - DataManager never sees raw yfinance data

5. ERROR HANDLING:
   - QuotaExceededError: Specific error for quota limits
   - Generic Exception: Catches all other errors (network, parsing, etc.)
   - All errors logged with context (endpoint, ticker, status code)

6. IDEMPOTENCY:
   - Multiple calls with same params → same result
   - No state stored in provider (stateless)
   - DB logging handles deduplication via timestamps
"""

# ==================== USAGE IN DATA MANAGER ====================
"""
# In data_manager.py:

from .providers.yfinance_provider import YFinanceProvider
from .services.quota_manager import DatabaseQuotaManager

# Initialize (dependency injection)
quota_manager = DatabaseQuotaManager(session, pipeline_run_id, daily_limit=500)
provider = YFinanceProvider(quota_manager, per_minute_limit=60)

# Use in DataManager
data_manager = DataManager(session, provider)
result = data_manager.update_prices_for_asset(asset, start_date)
# → Provider handles: throttling + quota + logging + DTO transformation
# → DataManager sees: List[ProviderPriceData] ready for DB upsert
"""
