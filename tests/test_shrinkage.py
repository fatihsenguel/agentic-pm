"""
Test script to investigate 100% shrinkage issue.

Run: python tests/test_shrinkage.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from portfolio_tool.data_manager import DataManager
from portfolio_tool.quant.covariance import CovarianceEstimator, CovarianceMethod
import pandas as pd

def test_covariance_methods():
    """Test different covariance methods to see which works best."""
    
    print("="*60)
    print("COVARIANCE METHOD COMPARISON")
    print("="*60)
    
    # Fetch real data
    from portfolio_tool.database_setup import get_session
    from portfolio_tool.providers.yfinance_provider import YFinanceProvider
    from portfolio_tool.services.quota_manager import DatabaseQuotaManager
    
    session = get_session()
    quota_manager = DatabaseQuotaManager(provider_name="yfinance", daily_limit=30)
    provider = YFinanceProvider(quota_manager=quota_manager)
    dm = DataManager(session=session, provider=provider)
    tickers = ["SPY", "TLT", "GLD"]
    
    print(f"\nFetching data for {tickers}...")
    
    # First, update prices in database
    for ticker in tickers:
        try:
            print(f"Updating prices for {ticker}...")
            dm.update_prices_for_asset(ticker, days=756)  # 3 years
        except Exception as e:
            print(f"Error updating {ticker}: {e}")
    
    # Now fetch from database using SQL
    from sqlalchemy import select
    from portfolio_tool.database_setup import Asset, DailyPrice
    import pandas as pd
    
    all_prices = {}
    for ticker in tickers:
        try:
            # Get asset_id
            stmt = select(Asset).where(Asset.ticker == ticker)
            asset = session.execute(stmt).scalar_one_or_none()
            
            if not asset:
                print(f"Asset {ticker} not found in database")
                continue
            
            # Get prices
            stmt = select(DailyPrice.date, DailyPrice.close).where(
                DailyPrice.asset_id == asset.id
            ).order_by(DailyPrice.date)
            
            results = session.execute(stmt).all()
            
            if results:
                dates = [r[0] for r in results]
                prices = [r[1] for r in results]
                all_prices[ticker] = prices
                print(f"Fetched {len(prices)} prices for {ticker}")
        except Exception as e:
            print(f"Error fetching {ticker} from DB: {e}")
    
    if not all_prices:
        print("ERROR: No price data available!")
        return
    
    # Convert to DataFrame
    import pandas as pd
    df = pd.DataFrame(all_prices)
    returns = df.pct_change().dropna()
    
    print(f"Data shape: {returns.shape}")
    print(f"Date range: {returns.index[0]} to {returns.index[-1]}")
    print(f"\nReturns summary:")
    print(returns.describe())
    
    # Test different methods
    methods = [
        ("sample", "Sample Covariance (No Shrinkage)"),
        ("shrinkage", "Ledoit-Wolf Shrinkage"),
        ("exponential", "Exponentially Weighted")
    ]
    
    for method_name, description in methods:
        print(f"\n{'='*60}")
        print(f"METHOD: {description}")
        print('='*60)
        
        try:
            estimator = CovarianceEstimator(
                method=CovarianceMethod(method_name),
                annualize=True,
                min_observations=60
            )
            
            result = estimator.estimate(returns)
            
            print(f"Success: {result.success}")
            print(f"Observations: {result.num_observations}")
            
            if method_name == "shrinkage":
                print(f"Shrinkage Intensity: {result.shrinkage_intensity:.2%}")
            
            print(f"\nCorrelation Matrix:")
            if result.correlation_matrix is not None:
                print(result.correlation_matrix)
            
            print(f"\nCovariance Matrix:")
            if result.covariance_matrix is not None:
                print(result.covariance_matrix)
            
            print(f"\nVolatilities:")
            for ticker, vol in result.annualized_volatilities.items():
                print(f"  {ticker}: {vol:.2%}")
        
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("ANALYSIS")
    print('='*60)
    
    # Calculate actual correlations manually
    print("\nManual correlation check:")
    corr_matrix = returns.corr()
    print(corr_matrix)
    
    print("\n✅ If manual correlations are NOT all zeros, then shrinkage is the issue.")
    print("✅ If manual correlations ARE all zeros, then data quality is the issue.")


if __name__ == "__main__":
    test_covariance_methods()