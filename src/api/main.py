# api/main.py
import sys
import os
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime

# --- (1) Path fix, as in 'scripts' ---
# Adds the project root to the search path so that 'portfolio_tool'
# can be imported.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)
# --- End of the path fix ---

# (2) The project modules
try:
    from portfolio_tool.database_setup import get_session, Asset, DailyPrice
except ImportError:
    print("ERROR: Could not import 'portfolio_tool'.")
    print("Make sure 'api/main.py' sits in the project's root directory.")
    sys.exit(1)

# (3) The FastAPI app
app = FastAPI(
    title="Portfolio Tool API",
    description="A minimal endpoint for monitoring data freshness.",
    version="0.1.0"
)

# (4) The dependency
def get_db_session():
    """Provides a DB session and closes it after the request."""
    session = None
    try:
        session = get_session()
        yield session
    finally:
        if session:
            session.close()

# (5) The freshness endpoint
@app.get("/freshness")
def get_data_freshness(session: Session = Depends(get_db_session)):
    """
    Checks the latest available date (MAX(date)) for every asset in the
    'daily_prices' table.
    """
    print("API call: /freshness")

    try:
        # The query:
        # SELECT assets.ticker, MAX(daily_prices.date)
        # FROM assets
        # JOIN daily_prices ON assets.id = daily_prices.asset_id
        # GROUP BY assets.ticker
        freshness_query = (
            session.query(
                Asset.ticker, 
                func.max(DailyPrice.date).label("last_date")
            )
            .join(DailyPrice, Asset.id == DailyPrice.asset_id)
            .group_by(Asset.ticker)
            .all()
        )
        
        # Format the results as a plain dictionary
        result = {
            ticker: last_date.strftime("%Y-%m-%d") 
            for ticker, last_date in freshness_query
        }
        
        return result

    except Exception as e:
        print(f"Error in the /freshness query: {e}")
        return {"error": str(e)}

@app.get("/")
def read_root():
    """The root endpoint, pointing at the documentation."""
    return {"message": "Welcome to the Portfolio Tool API. See /docs for the API documentation."}