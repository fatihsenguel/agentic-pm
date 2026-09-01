# src\portfolio_tool\providers\utils.py

import time
from collections import deque
import math
from typing import Optional, Any
from datetime import datetime, date

class SimpleRateLimiter:
    """
    Ein einfacher Rate-Limiter, der sicherstellt, dass nicht mehr als
    'per_minute'-Aufrufe in einem 60-Sekunden-Fenster erfolgen.
    (Basierend auf FIN_API_Runbook.md, Abschnitt 5.1)
    """
    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.window_seconds = 60
        # deque speichert die Zeitstempel der Aufrufe im Fenster
        self.timestamps = deque()

    def wait_for_slot(self):
        """
        Blockiert, bis ein Slot für einen Aufruf verfügbar ist.
        """
        now = time.time()

        # 1. Entferne alte Zeitstempel (älter als 'window_seconds')
        while self.timestamps and (now - self.timestamps[0] > self.window_seconds):
            self.timestamps.popleft()

        # 2. Prüfen, ob das Fenster voll ist
        if len(self.timestamps) < self.per_minute:
            # Slot ist frei
            self.timestamps.append(now)
            return

        # 3. Fenster ist voll. Wir müssen warten.
        # Warte, bis der älteste Aufruf aus dem Fenster fällt.
        oldest_call_time = self.timestamps[0]
        time_to_wait = (oldest_call_time + self.window_seconds) - now
        
        if time_to_wait > 0:
            # (+ 0.02s Puffer, um Rundungsfehler zu vermeiden)
            time.sleep(time_to_wait + 0.02)
        
        # Rekursiver Aufruf, um den Slot erneut zu prüfen (falls mehrere Threads warten)
        # In unserem Single-Thread-Skript könnten wir auch einfach 
        # self.timestamps.popleft() und self.timestamps.append(time.time()) machen.
        # Aber die rekursive Variante ist sicherer.
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