# src/agents/validators.py
# Purpose: Custom validators for ticker symbols, weights, and other inputs
# Principle: Catch hallucinations BEFORE they hit the database or APIs
# Phase: 6.12 - Output Parsers & Guardrails

import re
from typing import List, Dict, Set, Optional, Tuple
from functools import lru_cache


# =============================================================================
# KNOWN TICKER DATABASE
# =============================================================================

# Common ETFs that are frequently used in portfolio management
KNOWN_ETFS: Set[str] = {
    # US Equity ETFs
    "SPY", "IVV", "VOO", "QQQ", "DIA", "IWM", "IWF", "IWD", "VTI", "VTV",
    "VUG", "SCHD", "SPLG", "MGK", "VIG", "NOBL", "SDY", "DVY", "HDV",
    # International ETFs
    "VWO", "EEM", "IEMG", "VEA", "EFA", "IEFA", "VGK", "EWJ", "FXI", "MCHI",
    "EWZ", "EWG", "EWU", "INDA", "VPL", "AAXJ",
    # Bond ETFs
    "TLT", "IEF", "SHY", "BND", "AGG", "LQD", "HYG", "JNK", "TIP", "GOVT",
    "VCIT", "VCSH", "BNDX", "EMB", "MUB", "VTEB", "SCHZ", "SPTL",
    # Commodity ETFs
    "GLD", "IAU", "SLV", "GDX", "GDXJ", "USO", "UNG", "DBA", "DBC", "PDBC",
    # Sector ETFs
    "XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE",
    "VNQ", "IYR", "KRE", "XBI", "IBB", "ARKK", "ARKG", "SOXX", "SMH",
    # Factor ETFs
    "MTUM", "QUAL", "VLUE", "SIZE", "USMV", "EFAV", "EEMV",
    # Leveraged/Inverse (careful!)
    "TQQQ", "SQQQ", "UPRO", "SPXU", "TNA", "TZA",
}

# Major US Stocks (most commonly discussed)
KNOWN_STOCKS: Set[str] = {
    # Tech Giants
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC",
    "CRM", "ORCL", "ADBE", "NFLX", "PYPL", "SQ", "SHOP", "SNOW", "PLTR", "UBER",
    # Finance
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "V", "MA", "AXP",
    # Healthcare
    "JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "TMO", "ABT", "BMY", "AMGN",
    # Consumer
    "WMT", "COST", "HD", "LOW", "TGT", "MCD", "SBUX", "NKE", "DIS", "CMCSA",
    "PG", "KO", "PEP", "PM", "MO",
    # Industrial
    "CAT", "DE", "BA", "RTX", "LMT", "GE", "HON", "UPS", "FDX", "MMM",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "VLO", "PSX",
    # Other
    "BRK.A", "BRK.B", "T", "VZ", "NEE", "DUK", "SO",
}

# Macro/Index tickers (special handling)
MACRO_TICKERS: Set[str] = {
    "^VIX", "VIX", "^GSPC", "^DJI", "^IXIC", "^TNX", "^IRX", "^TYX",
    "TNX_10Y", "IRX_3M", "TYX_30Y",  # Our internal naming
    "DX-Y.NYB",  # Dollar index
}

# Combine all known tickers
ALL_KNOWN_TICKERS: Set[str] = KNOWN_ETFS | KNOWN_STOCKS | MACRO_TICKERS


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def is_valid_ticker_format(ticker: str) -> bool:
    """
    Check if ticker has valid format (not if it exists).
    
    Valid formats:
    - 1-5 uppercase letters: AAPL, SPY, VWO
    - Letters with numbers: BRK.B, 3M (rare)
    - Special chars: ^VIX, DX-Y.NYB
    """
    if not ticker or len(ticker) > 10:
        return False
    
    # Remove common prefixes/suffixes for validation
    clean = ticker.upper().strip()
    
    # Special index tickers
    if clean.startswith("^"):
        return len(clean) >= 2 and clean[1:].replace(".", "").isalnum()
    
    # Standard tickers: letters, numbers, dots, hyphens
    pattern = r'^[A-Z]{1,5}(\.[A-Z])?$|^[A-Z0-9\.\-]{1,10}$'
    return bool(re.match(pattern, clean))


def is_known_ticker(ticker: str) -> bool:
    """Check if ticker is in our known database."""
    return ticker.upper() in ALL_KNOWN_TICKERS


@lru_cache(maxsize=1000)
def validate_ticker(ticker: str) -> Tuple[bool, str]:
    """
    Validate a single ticker.
    
    Returns:
        (is_valid, message)
    """
    ticker = ticker.upper().strip()
    
    if not ticker:
        return False, "Empty ticker"
    
    if not is_valid_ticker_format(ticker):
        return False, f"Invalid ticker format: {ticker}"
    
    if is_known_ticker(ticker):
        return True, f"Valid known ticker: {ticker}"
    
    # Unknown but valid format - allow with warning
    return True, f"Unknown ticker (not in database): {ticker}"


def validate_tickers(tickers: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Validate a list of tickers.
    
    Returns:
        (valid_tickers, unknown_tickers, invalid_tickers)
    """
    valid = []
    unknown = []
    invalid = []
    
    for ticker in tickers:
        ticker = ticker.upper().strip()
        
        if not is_valid_ticker_format(ticker):
            invalid.append(ticker)
        elif is_known_ticker(ticker):
            valid.append(ticker)
        else:
            unknown.append(ticker)
    
    return valid, unknown, invalid


def suggest_ticker(invalid_ticker: str) -> Optional[str]:
    """
    Suggest a valid ticker for a potentially misspelled one.
    
    Simple Levenshtein-like matching for common mistakes.
    """
    invalid_upper = invalid_ticker.upper()
    
    # Common mistakes mapping
    common_mistakes = {
        "GOLD": "GLD",
        "BONDS": "BND",
        "STOCK": "SPY",
        "BITCOIN": None,  # Not a valid stock ticker
        "BTC": None,
        "ETH": None,
        "CRYPTO": None,
        "SP500": "SPY",
        "S&P": "SPY",
        "S&P500": "SPY",
        "NASDAQ": "QQQ",
        "DOW": "DIA",
        "TREASURY": "TLT",
        "TBILL": "SHY",
    }
    
    if invalid_upper in common_mistakes:
        return common_mistakes[invalid_upper]
    
    # Check for close matches (1 character difference)
    for known in ALL_KNOWN_TICKERS:
        if len(known) == len(invalid_upper):
            diff = sum(a != b for a, b in zip(known, invalid_upper))
            if diff == 1:
                return known
    
    return None


# =============================================================================
# WEIGHT VALIDATION
# =============================================================================

def validate_weights(weights: Dict[str, float]) -> Tuple[bool, List[str]]:
    """
    Validate portfolio weights.
    
    Rules:
    - Must sum to 1.0 (±2% tolerance)
    - No negative weights (unless short selling allowed)
    - No weight > 100%
    - All tickers must be valid format
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    if not weights:
        return False, ["Weights dictionary is empty"]
    
    # Check total
    total = sum(weights.values())
    if abs(total - 1.0) > 0.02:
        errors.append(f"Weights sum to {total:.4f}, should be 1.0 (±2%)")
    
    # Check individual weights
    for ticker, weight in weights.items():
        # Validate ticker format
        if not is_valid_ticker_format(ticker):
            errors.append(f"Invalid ticker format: {ticker}")
        
        # Validate weight value
        if weight < 0:
            errors.append(f"Negative weight for {ticker}: {weight:.4f}")
        elif weight > 1.0:
            errors.append(f"Weight > 100% for {ticker}: {weight:.4f}")
        elif weight > 0 and weight < 0.001:
            errors.append(f"Weight too small for {ticker}: {weight:.6f} (< 0.1%)")
    
    return len(errors) == 0, errors


# =============================================================================
# CONSTRAINT VALIDATION
# =============================================================================

def validate_volatility_constraint(max_vol: float) -> Tuple[bool, str]:
    """Validate max volatility constraint."""
    if max_vol <= 0:
        return False, "Max volatility must be positive"
    if max_vol > 1.0:
        return False, f"Max volatility {max_vol:.0%} seems too high (>100%)"
    if max_vol < 0.01:
        return False, f"Max volatility {max_vol:.2%} seems too low (<1%)"
    return True, f"Valid volatility constraint: {max_vol:.2%}"


def validate_return_target(target_return: float) -> Tuple[bool, str]:
    """Validate target return."""
    if target_return < -0.5:
        return False, f"Target return {target_return:.0%} is unrealistically negative"
    if target_return > 1.0:
        return False, f"Target return {target_return:.0%} is unrealistically high (>100%)"
    return True, f"Valid return target: {target_return:.2%}"


def validate_period(period: str) -> Tuple[bool, str]:
    """
    Validate time period string.
    
    Valid formats: 1Y, 3Y, 5Y, 10Y, 6M, 30D, etc.
    """
    pattern = r'^(\d+)([YMD])$'
    match = re.match(pattern, period.upper())
    
    if not match:
        return False, f"Invalid period format: {period}. Use formats like 5Y, 6M, 30D"
    
    value, unit = int(match.group(1)), match.group(2)
    
    if unit == 'Y' and value > 30:
        return False, f"Period {period} too long (max 30 years)"
    if unit == 'M' and value > 360:
        return False, f"Period {period} too long (max 360 months)"
    if unit == 'D' and value > 10000:
        return False, f"Period {period} too long (max 10000 days)"
    
    return True, f"Valid period: {period}"


# =============================================================================
# COMPREHENSIVE INPUT VALIDATION
# =============================================================================

class ValidationResult:
    """Result of comprehensive validation."""
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: Dict[str, str] = {}  # invalid -> suggested
    
    def add_error(self, msg: str):
        self.is_valid = False
        self.errors.append(msg)
    
    def add_warning(self, msg: str):
        self.warnings.append(msg)
    
    def add_suggestion(self, invalid: str, suggested: Optional[str]):
        if suggested:
            self.suggestions[invalid] = suggested


def validate_optimization_request(
    tickers: List[str],
    max_volatility: Optional[float] = None,
    target_return: Optional[float] = None,
    period: str = "5Y"
) -> ValidationResult:
    """
    Comprehensive validation for optimization requests.
    """
    result = ValidationResult()
    
    # Validate tickers
    if not tickers:
        result.add_error("No tickers provided")
    else:
        valid, unknown, invalid = validate_tickers(tickers)
        
        if invalid:
            for t in invalid:
                result.add_error(f"Invalid ticker: {t}")
                suggestion = suggest_ticker(t)
                result.add_suggestion(t, suggestion)
        
        if unknown:
            for t in unknown:
                result.add_warning(f"Unknown ticker (not in database): {t}")
        
        if len(valid) + len(unknown) < 2:
            result.add_error("Need at least 2 valid tickers for optimization")
    
    # Validate volatility constraint
    if max_volatility is not None:
        valid, msg = validate_volatility_constraint(max_volatility)
        if not valid:
            result.add_error(msg)
    
    # Validate return target
    if target_return is not None:
        valid, msg = validate_return_target(target_return)
        if not valid:
            result.add_error(msg)
    
    # Validate period
    valid, msg = validate_period(period)
    if not valid:
        result.add_error(msg)
    
    return result


def validate_rebalance_request(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
    portfolio_value: float
) -> ValidationResult:
    """
    Comprehensive validation for rebalancing requests.
    """
    result = ValidationResult()
    
    # Validate portfolio value
    if portfolio_value <= 0:
        result.add_error("Portfolio value must be positive")
    elif portfolio_value < 100:
        result.add_warning("Portfolio value seems very small")
    
    # Validate current weights
    valid, errors = validate_weights(current_weights)
    for err in errors:
        result.add_error(f"Current weights: {err}")
    
    # Validate target weights
    valid, errors = validate_weights(target_weights)
    for err in errors:
        result.add_error(f"Target weights: {err}")
    
    # Check ticker consistency
    current_tickers = set(current_weights.keys())
    target_tickers = set(target_weights.keys())
    
    if current_tickers != target_tickers:
        only_current = current_tickers - target_tickers
        only_target = target_tickers - current_tickers
        
        if only_current:
            result.add_warning(f"Tickers only in current: {only_current} (will be sold)")
        if only_target:
            result.add_warning(f"Tickers only in target: {only_target} (will be bought)")
    
    return result
