import sys
import os
from sqlalchemy.orm import Session

# --- sys.path fix: two levels up, the project root ---
script_dir = os.path.dirname(os.path.abspath(__file__))          # .../portfolio_tool/scripts
project_root = os.path.dirname(os.path.dirname(script_dir))      # .../Finance_Phase_3
sys.path.insert(0, project_root)
# --- End of the fix ---

import datetime

from portfolio_tool.database_setup import (
    get_session,
    Asset,
    PipelineRun,
    PipelineRunStatus,
    func,
)
from portfolio_tool.data_manager import DataManager
from portfolio_tool.providers.yfinance_provider import YFinanceProvider
from portfolio_tool.services.quota_manager import DatabaseQuotaManager

# Configuration of the backfill run
PROVIDER_NAME = "yfinance"
YFINANCE_DAILY_LIMIT = 2000      # a safety net
PER_MINUTE_LIMIT = 60


def main_backfill():
    """
    A ONE-OFF backfill script.

    Goal:
      - fill the shares history completely
      - fill the quarterly earnings completely
      - fill the financial statements (income, balance sheet, cash flow;
        annual and quarterly) completely.
    """
    print("--- STARTING THE ONE-OFF BACKFILL ---")

    session: Session = get_session()
    run: PipelineRun | None = None
    run_id_for_logging: int | None = None

    try:
        # 1) Create the PipelineRun for this backfill
        run = PipelineRun(
            script_name="portfolio_tool/scripts/run_backfill.py",
            status=PipelineRunStatus.RUNNING,
        )
        session.add(run)
        session.commit()
        run_id_for_logging = run.id
        print(f"\n=== Starting backfill PipelineRun ID: {run_id_for_logging} ===")

        # 2) Initialise the QuotaManager, the provider and the DataManager
        quota_manager = DatabaseQuotaManager(
            session=session,
            pipeline_run_id=run.id,
            provider_name=PROVIDER_NAME,
            daily_limit=YFINANCE_DAILY_LIMIT,
        )

        provider = YFinanceProvider(
            quota_manager=quota_manager,
            per_minute_limit=PER_MINUTE_LIMIT,
        )
        manager = DataManager(session, provider)

        # 3) Load every asset from the database
        assets = session.query(Asset).all()
        print(f"Filling in missing data for {len(assets)} assets...")

        # 4) Per asset: backfill shares, earnings and financial statements
        for asset in assets:
            print(f"\n--- Backfill for: {asset.ticker} ---")

            # 4.1 Shares history (force_update=True ignores the interval guard)
            print("  > Backfill shares history...")
            manager.update_shares_history_for_asset(asset, force_update=True)

            # 4.2 Quarterly Earnings
            print("  > Backfill Quarterly Earnings...")
            manager.update_quarterly_earnings_for_asset(asset, force_update=True)

            # 4.3 Financial Statements (Income, Balance Sheet, Cash Flow)
            print("  > Backfill Financial Statements (income / balance / cashflow)...")
            for report_type in ("income", "balance_sheet", "cash_flow"):
                for period_type in ("annual", "quarterly"):
                    print(f"    - {report_type} ({period_type})")
                    manager.update_financial_statements_for_asset(
                        asset=asset,
                        report_type=report_type,
                        period_type=period_type,
                    )

        # 5) All well: set the run to SUCCESS
        print(f"\n=== Backfill PipelineRun ID: {run_id_for_logging} completed. ===")
        run.status = PipelineRunStatus.SUCCESS
        run.end_time = func.now()
        session.commit()

    except Exception as e:
        import traceback
        print("!!!!!!!!!!!!!! SEVERE ERROR IN THE BACKFILL !!!!!!!!!!!!!!", file=sys.stderr)
        traceback.print_exc()
        session.rollback()

        if run is not None:
            try:
                run.status = PipelineRunStatus.FAILED
                run.end_time = func.now()
                run.error_message = str(e)[:950]
                session.add(run)
                session.commit()
            except Exception as log_e:
                print(f"Further error while logging the FAILED status: {log_e}", file=sys.stderr)
                session.rollback()

    finally:
        session.close()
        print(
            f"--- Backfill process (Run ID: {run_id_for_logging if run_id_for_logging else '??'}) "
            f"finished. Session closed. ---"
        )


if __name__ == "__main__":
    main_backfill()
