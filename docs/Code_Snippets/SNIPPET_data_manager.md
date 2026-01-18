"""
SNIPPET: data_manager.py
PURPOSE: Facade pattern for all data operations. Single entry point for Agent tools.
PATTERN: Facade + Idempotent Upserts + Session Isolation
"""

from sqlalchemy.orm import Session
from .providers.base import DataProviderInterface
from .models.responses import UpdateResult  # DTO for agent-ready responses

class DataManager:
    """
    FACADE: Single entry point for all data operations.
    - Coordinates: Provider (API) + Database (Persistence)
    - Returns: UpdateResult DTOs (success, affected_count, entities, metadata)
    - Pattern: All methods are idempotent (safe to retry)
    """
    
    def __init__(self, session: Session, provider: DataProviderInterface):
        self.session = session        # SQLAlchemy session
        self.provider = provider      # YFinanceProvider (or any DataProviderInterface impl)
        self.config = CONFIG          # Fetch intervals from config.toml
    
    # ==================== CORE UPDATE METHODS ====================
    # COMMON PATTERN FOR ALL UPDATE METHODS:
    """
    try:
        1. Determine if fetch needed (interval check or start_date logic)
        2. Call provider.get_X(ticker, ...) → returns List[DTO]
        3. Transform DTOs → list[dict] for upsert
        4. Call self._perform_upsert(model, values, index_elements)
        5. Update metadata timestamps
        6. self.session.commit()
        7. return UpdateResult(success=True, operation="...", affected_count=N, entities=[ticker])
    except Exception as e:
        self.session.rollback()
        return UpdateResult(success=False, ..., error_message=str(e))
    """
    
    def update_prices_for_asset(self, asset: Asset, start_date: date = None) -> UpdateResult:
        """Fetches daily OHLCV prices → upserts to daily_prices table."""
        # Determine start_date from last DB entry or default
        last_entry = session.query(func.max(DailyPrice.date)).filter(...).scalar()
        start_date = last_entry if last_entry else date(2000, 1, 1)
        
        # Fetch from provider
        provider_data = self.provider.get_daily_prices(ticker, start_date, date.today())
        
        # Transform to upsert format
        values = [{'asset_id': asset.id, 'date': dto.date, 'open': dto.open, ...} 
                  for dto in provider_data]
        
        # Batch upsert
        affected_count = self._perform_upsert(DailyPrice, values, index_elements=['asset_id', 'date'])
        
        return UpdateResult(
            success=True, 
            operation="update_prices", 
            affected_count=affected_count,
            entities=[asset.ticker],
            entity_type="asset"
        )
    
    def update_earnings_for_asset(self, asset: Asset, force_update: bool = False) -> UpdateResult:
        """Fetches quarterly earnings → upserts to quarterly_earnings table."""
        meta = self._get_or_create_metadata(asset.id)
        
        # Interval check (skip if fetched recently unless force_update)
        if not force_update and not self._should_fetch(meta.last_earnings_fetch_time, 7):
            return UpdateResult(True, "update_earnings", 0, [asset.ticker], "asset", 
                              metadata={"reason": "skipped_interval"})
        
        # Fetch from provider since last report date
        provider_data = self.provider.get_earnings_history(ticker, since=meta.last_earnings_report_date)
        
        # Transform & upsert
        values = [{'asset_id': asset.id, 'report_date': dto.report_date, 
                   'eps_actual': dto.eps_actual, 'eps_estimate': dto.eps_estimate, ...}
                  for dto in provider_data]
        
        affected_count = self._perform_upsert(QuarterlyEarnings, values, 
                                             index_elements=['asset_id', 'report_date'])
        
        # Update metadata timestamps
        meta.last_earnings_fetch_time = datetime.utcnow()
        self.session.commit()
        
        return UpdateResult(True, "update_earnings", affected_count, [asset.ticker], "asset")
    
    def update_financial_statements_for_asset(
        self, asset: Asset, report_type: str, period_type: str
    ) -> UpdateResult:
        """
        Fetches financial statements → upserts to financial_statements table.
        - report_type: "income_statement" | "balance_sheet" | "cash_flow"
        - period_type: "quarterly" | "annual"
        """
        # Fetch from provider
        provider_data = self.provider.get_financial_statements(
            ticker, report_type, period_type, since=last_date
        )
        
        # Transform (35+ columns: revenue, net_income, eps, total_assets, etc.)
        values = [{'asset_id': asset.id, 'date': dto.date, 'report_type': dto.report_type,
                   'revenue': dto.revenue, 'net_income': dto.net_income, ...}  # + 30 more cols
                  for dto in provider_data]
        
        affected_count = self._perform_upsert(
            FinancialStatement, values, 
            index_elements=['asset_id', 'date', 'report_type', 'period_type']
        )
        
        return UpdateResult(True, "update_financial_statements", affected_count, 
                          [asset.ticker], "asset", metadata={"report_type": report_type})
    
    # ==================== INTERNAL HELPERS ====================
    
    def _perform_upsert(self, model: DeclarativeMeta, values: list[dict], index_elements: list[str]) -> int:
        """
        CORE PATTERN: Idempotent batch upsert for SQLite.
        Returns: Total row count affected
        """
        BATCH_SIZE = 500
        for i in range(0, len(values), BATCH_SIZE):
            chunk = values[i:i + BATCH_SIZE]
            
            stmt = sqlite_insert(model).values(chunk)
            update_cols = [col for col in chunk[0].keys() if col not in index_elements]
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_={col: getattr(stmt.excluded, col) for col in update_cols}
            )
            self.session.execute(upsert_stmt)
        
        self.session.commit()
        return len(values)
    
    def _get_or_create_asset(self, ticker: str, name: str, asset_class: str) -> Asset:
        """Returns existing asset or creates new one with enriched data from provider."""
        asset = self.session.query(Asset).filter_by(ticker=ticker).first()
        if asset:
            return asset
        
        # Enrich with provider data
        info_dto = self.provider.get_asset_info(ticker)
        new_asset = Asset(
            ticker=ticker, 
            asset_class=asset_class,
            name=info_dto.long_name or name,
            sector=info_dto.sector,
            industry=info_dto.industry,
            # ... country, currency, etc.
        )
        self.session.add(new_asset)
        self.session.commit()
        return new_asset
    
    def _should_fetch(self, last_fetch_time: datetime, interval_days: int) -> bool:
        """Returns True if interval elapsed or no prior fetch."""
        if not last_fetch_time:
            return True
        return (datetime.utcnow() - last_fetch_time).days >= interval_days
    
    def _get_or_create_metadata(self, asset_id: int) -> AssetFetchMetadata:
        """Gets or creates fetch metadata tracking for an asset."""
        meta = self.session.query(AssetFetchMetadata).get(asset_id)
        if not meta:
            meta = AssetFetchMetadata(asset_id=asset_id)
            self.session.add(meta)
        return meta

# ==================== KEY DESIGN PATTERNS ====================
"""
1. FACADE PATTERN:
   - DataManager hides complexity of Provider + Database
   - Agent tools call DataManager, not Provider/DB directly

2. IDEMPOTENT UPSERTS:
   - All DB writes use ON CONFLICT UPDATE
   - Safe to retry failed operations
   - No duplicate data even if called multiple times

3. DTO RESPONSES (UpdateResult):
   - Every method returns structured UpdateResult
   - Agent-ready: success flag, affected_count, entities list
   - Metadata: Additional context (e.g., "up_to_date", "no_new_data")

4. SESSION ISOLATION:
   - Each DataManager has its own session
   - Prevents SQLite locking issues
   - Managed by QuotaManager (not shown here)

5. PROVIDER ABSTRACTION:
   - DataProviderInterface allows swapping YFinance → Bloomberg
   - DataManager doesn't care about provider implementation

6. BATCH PROCESSING:
   - Large datasets split into 500-row chunks
   - Prevents memory issues with 10K+ price points
"""

# ==================== EXAMPLE USAGE IN AGENT TOOLS ====================
"""
# In tools/data_tools.py:

@tool
def fetch_stock_prices(ticker: str, start_date: str = None) -> dict:
    '''Agent tool: Fetches stock prices and stores in DB.'''
    data_manager = get_data_manager()  # Singleton
    asset = data_manager._get_or_create_asset(ticker, ticker, "stock")
    
    result: UpdateResult = data_manager.update_prices_for_asset(asset, start_date)
    
    return {
        "success": result.success,
        "ticker": ticker,
        "rows_inserted": result.affected_count,
        "status": result.metadata.get("status", "updated")
    }
"""
