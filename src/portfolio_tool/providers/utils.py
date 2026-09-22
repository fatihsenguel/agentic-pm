# src\portfolio_tool\providers\utils.py

import time
from collections import deque
import math
from typing import Optional, Any
from datetime import datetime, date

class SimpleRateLimiter:
    """
    A simple rate limiter that allows no more than 'per_minute' calls
    within a 60-second window.
    (After FIN_API_Runbook.md, section 5.1)
    """
    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.window_seconds = 60
        # The deque holds the timestamps of the calls within the window
        self.timestamps = deque()

    def wait_for_slot(self):
        """
        Blocks until a slot for a call is available.
        """
        now = time.time()

        # 1. Drop the old timestamps (older than 'window_seconds')
        while self.timestamps and (now - self.timestamps[0] > self.window_seconds):
            self.timestamps.popleft()

        # 2. Is the window full?
        if len(self.timestamps) < self.per_minute:
            # A slot is free
            self.timestamps.append(now)
            return

        # 3. The window is full: wait until the oldest call falls out of it.
        oldest_call_time = self.timestamps[0]
        time_to_wait = (oldest_call_time + self.window_seconds) - now

        if time_to_wait > 0:
            # (plus a 0.02 s buffer against rounding errors)
            time.sleep(time_to_wait + 0.02)

        # A recursive call checks the slot again, in case several threads
        # are waiting. A single-threaded script could simply do
        # self.timestamps.popleft() and self.timestamps.append(time.time());
        # the recursive form is the safer one.
        self.wait_for_slot()


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """
    Safely convert a value to int, handling NaN, None, and invalid types.
    
    Args:
        value: The value to convert (can be float, str, None, NaN, etc.)
        default: Value to return if conversion fails (default: None)
    
    Returns:
        int or default value
    
    Examples:
        >>> safe_int(42.7)           # 42
        >>> safe_int(float('nan'))   # None
        >>> safe_int(None)           # None
        >>> safe_int("invalid", 0)   # 0
    """
    if value is None:
        return default
    
    try:
        # Handle numpy/pandas NaN
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return default
        
        return int(value)
    
    except (ValueError, TypeError, OverflowError):
        return default


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Safely convert a value to float, handling NaN, None, and invalid types.
    
    Args:
        value: The value to convert
        default: Value to return if conversion fails (default: None)
    
    Returns:
        float or default value
    
    Examples:
        >>> safe_float("3.14")       # 3.14
        >>> safe_float(float('nan')) # None
        >>> safe_float(None)         # None
    """
    if value is None:
        return default
    
    try:
        result = float(value)
        
        # Handle NaN and infinity
        if math.isnan(result) or math.isinf(result):
            return default
            
        return result
    
    except (ValueError, TypeError):
        return default


def safe_date(value: Any, default: Optional[date] = None) -> Optional[date]:
    """
    Safely convert a value to date, handling various input formats.
    
    Args:
        value: The value to convert (datetime, date, str, timestamp)
        default: Value to return if conversion fails (default: None)
    
    Returns:
        date or default value
    """
    if value is None:
        return default
    
    try:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, str):
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        
        # Handle pandas Timestamp
        if hasattr(value, 'date') and callable(value.date):
            return value.date()
        
        return default
        
    except (ValueError, TypeError, OverflowError, OSError):
        return default
    

from decimal import Decimal, InvalidOperation

def safe_decimal(value: Any, default: Optional[Decimal] = None) -> Optional[Decimal]:
    """
    Safely convert a value to Decimal, handling NaN, None, and invalid types.
    
    Args:
        value: The value to convert
        default: Value to return if conversion fails (default: None)
    
    Returns:
        Decimal or default value
    
    Examples:
        >>> safe_decimal("3.14")       # Decimal('3.14')
        >>> safe_decimal(float('nan')) # None
        >>> safe_decimal(None)         # None
    """
    if value is None:
        return default
    
    try:
        # Handle NaN and infinity for floats
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return default
        
        return Decimal(str(value))
    
    except (ValueError, TypeError, InvalidOperation):
        return default