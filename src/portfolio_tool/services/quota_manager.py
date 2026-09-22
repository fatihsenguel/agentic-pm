# =============================================================================
# FIX 2: quota_manager.py - Session Isolation
# =============================================================================
# Location: src/portfolio_tool/services/quota_manager.py
# 
# CHANGES:
# 1. QuotaManager creates its own sessions (not shared with DataManager)
# 2. Each operation uses a fresh session with proper cleanup
# 3. No more nested transactions that conflict with DataManager
#
# =============================================================================

import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from portfolio_tool.database_setup import (
    ApiQuota, 
    ApiCallLog, 
    PipelineRun,
    SessionLocal  # Use the session factory directly
)


class DatabaseQuotaManager:
    """
    Manages the API quotas centrally and logs every call in the database.

    This class uses sessions of its OWN for every database operation, to
    avoid conflicts with the DataManager (SQLite locking).
    """
    
    def __init__(self, 
                 provider_name: str, 
                 daily_limit: int,
                 pipeline_run_id: int = 9999):  # Default for agent usage
        """
        Initialize QuotaManager.
        
        NOTE: No session parameter! QuotaManager manages its own sessions.
        
        Args:
            provider_name: Name of the API provider (e.g., 'yfinance')
            daily_limit: Maximum API calls per day
            pipeline_run_id: ID of the current pipeline run for logging
        """
        self.provider_name = provider_name
        self.daily_limit = daily_limit
        self.pipeline_run_id = pipeline_run_id
        print(f"DEBUG [QuotaManager]: Initialised for '{provider_name}', run ID {pipeline_run_id}, limit {daily_limit}")

    def _get_session(self) -> Session:
        """Create a new independent session for this operation."""
        return SessionLocal()

    def _get_current_bucket_key(self) -> str:
        """Builds the unique key of today's daily quota window."""
        today = datetime.date.today()
        return f"daily_{self.provider_name}_{today.strftime('%Y-%m-%d')}"

    def _get_window_start(self) -> datetime.datetime:
        """Returns the UTC start of the current day."""
        return datetime.datetime.now(datetime.timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def can_consume_credit(self) -> bool:
        """
        Checks atomically whether a call may be made, and consumes a credit.
        
        Uses its own session to avoid conflicts with DataManager.
        
        Returns:
            True if credit was consumed, False if limit reached or error
        """
        bucket_key = self._get_current_bucket_key()
        session = self._get_session()
        
        try:
            # 1. Get or create quota entry
            quota = session.query(ApiQuota).filter(
                ApiQuota.bucket_key == bucket_key
            ).first()
            
            if not quota:
                print(f"DEBUG [QuotaManager]: Creating a new quota bucket: {bucket_key}")
                quota = ApiQuota(
                    provider_name=self.provider_name,
                    bucket_key=bucket_key,
                    calls_consumed=0,
                    window_start_time=self._get_window_start()
                )
                session.add(quota)
                session.flush()  # Get the ID without committing
            
            # 2. Check limit
            if quota.calls_consumed >= self.daily_limit:
                print(f"WARN [QuotaManager]: Daily limit reached for {bucket_key} ({self.daily_limit})")
                session.rollback()
                return False
            
            # 3. Consume credit
            quota.calls_consumed += 1
            print(f"DEBUG [QuotaManager]: Credit consumed. New count for {bucket_key}: {quota.calls_consumed}/{self.daily_limit}")
            
            session.commit()
            return True
            
        except Exception as e:
            print(f"ERROR [QuotaManager]: Error in the quota check: {e}")
            try:
                session.rollback()
            except:
                pass
            return False
        finally:
            session.close()

    def log_api_call(self, 
                     endpoint_name: str, 
                     asset_ticker: str = None, 
                     success: bool = True, 
                     http_status_code: int = None, 
                     error_message: str = None,
                     credits_consumed: int = 1):
        """
        Records the outcome of an API call in the ApiCallLog table.
        
        Uses its own session to avoid conflicts with DataManager.
        """
        session = self._get_session()
        
        try:
            # Truncate error message if too long
            if error_message and len(error_message) > 950:
                error_message = error_message[:950] + "..."

            log_entry = ApiCallLog(
                pipeline_run_id=self.pipeline_run_id,
                provider_name=self.provider_name,
                endpoint_name=endpoint_name,
                asset_ticker=asset_ticker,
                call_timestamp=datetime.datetime.utcnow(),
                http_status_code=http_status_code,
                success=success,
                credits_consumed=credits_consumed if success else 0,
                error_message=error_message
            )
            
            session.add(log_entry)
            session.commit()
            
        except Exception as e:
            print(f"WARN [QuotaManager]: Logging the API call failed: {e}")
            try:
                session.rollback()
            except:
                pass
            # Don't raise - logging failure shouldn't break the main process
        finally:
            session.close()


class MockQuotaManager:
    """
    A mock QuotaManager for tests.
    Allows every API call, with no real quota check and no database log.
    """
    
    def __init__(self, session=None):  # session param kept for backwards compatibility
        print("   ℹ️  Using MockQuotaManager (Testing Mode)")
    
    def can_consume_credit(self, cost: int = 1) -> bool:
        """Always allowed (for tests)."""
        return True
    
    def log_api_call(self, **kwargs):
        """Logs nothing (for tests)."""
        pass