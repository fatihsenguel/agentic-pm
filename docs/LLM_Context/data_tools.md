# FILE: src/portfolio_tool/tools/data_tools.py
# PURPOSE: Interface between Agents and the Database.
# PRINCIPLE: "fetch_*" = API -> DB (Write). "get_*" = DB -> Agent (Read).

@tool
def fetch_stock_prices(ticker: str, start_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch and update daily stock prices (OHLCV) for a ticker.
    Writes to SQLite. Returns success/failure status.
    """

@tool
def fetch_financial_statements(ticker: str, report_type: str = "balance_sheet") -> Dict[str, Any]:
    """
    Fetch Balance Sheet, Income Statement, or Cash Flow.
    """

@tool
def fetch_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Fetch current metrics: Beta, Market Cap, PE Ratio, Sector, Industry.
    """

@tool
def query_financial_data(
    data_type: str,     # 'prices', 'earnings', 'statements', 'fundamentals'
    ticker: str,
    limit: int = 30,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    READ-ONLY: Flexible query tool for Agents to get raw data.
    Returns structured dictionary with list of records.
    """

@tool
def list_tracked_assets() -> Dict[str, Any]:
    """
    List all assets currently in the database + data coverage summary.
    """