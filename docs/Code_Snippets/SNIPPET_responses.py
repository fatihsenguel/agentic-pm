"""
SNIPPET: models/responses.py
PURPOSE: DTOs for agent-tool communication (standardized response format)
"""

@dataclass
class UpdateResult:
    """Response from data update operations (fetches/upserts)."""
    success: bool
    operation: str                    # "update_prices", "update_earnings", etc.
    affected_count: int               # Rows inserted/updated
    entities: List[str]               # ["AAPL", "MSFT"]
    entity_type: str = "asset"
    metadata: Dict[str, Any] = {}     # {"status": "up_to_date", "provider": "yfinance"}
    error_message: Optional[str] = None

@dataclass
class QueryResult:
    """Response from data retrieval operations (queries)."""
    success: bool
    data: List[Dict[str, Any]]        # Actual query results
    count: int                        # len(data)
    query_type: str                   # "get_balance_sheets", "list_assets"
    metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None

# USAGE PATTERN:
# Tools return these DTOs → Agent sees structured, typed responses
# Example: fetch_stock_prices() → UpdateResult(success=True, affected_count=252, entities=["AAPL"])
