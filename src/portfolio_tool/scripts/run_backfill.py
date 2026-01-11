import sys
import os
from sqlalchemy.orm import Session

# --- Sys.path-Fix: zwei Ebenen hoch -> Projektwurzel (Finance_Phase_3) ---
script_dir = os.path.dirname(os.path.abspath(__file__))          # .../portfolio_tool/scripts
project_root = os.path.dirname(os.path.dirname(script_dir))      # .../Finance_Phase_3
sys.path.insert(0, project_root)
# --- Ende Fix ---

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

# Konfiguration für den Backfill-Run
PROVIDER_NAME = "yfinance"
YFINANCE_DAILY_LIMIT = 2000      # Sicherheitsnetz
PER_MINUTE_LIMIT = 60            # wie im update_all_assets-Skript


def main_backfill():
    """
    EINMALIGES Backfill-Skript.

    Ziel:
      - Shares-Historie vollständig befüllen
      - Quarterly Earnings vollständig befüllen
      - Financial Statements (Income, Balance Sheet, Cash Flow;
        annual + quarterly) vollständig befüllen.
    """
    print("--- STARTE EINMALIGEN BACKFILL ---")

    session: Session = get_session()
    run: PipelineRun | None = None
    run_id_for_logging: int | None = None

    try:
        # 1) PipelineRun für diesen Backfill anlegen
        run = PipelineRun(
            script_name="portfolio_tool/scripts/run_backfill.py",
            status=PipelineRunStatus.RUNNING,
        )
        session.add(run)
        session.commit()
        run_id_for_logging = run.id
        print(f"\n=== Starte Backfill-PipelineRun ID: {run_id_for_logging} ===")

        # 2) QuotaManager + Provider + DataManager initialisieren
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

        # 3) Alle Assets aus der DB laden
        assets = session.query(Asset).all()
        print(f"Fülle fehlende Daten für {len(assets)} Assets auf...")

        # 4) Pro Asset: Shares, Earnings und Financial Statements backfillen
        for asset in assets:
            print(f"\n--- Backfill für: {asset.ticker} ---")

            # 4.1 Shares History (force_update=True -> Intervall-GUARD ignorieren)
            print("  > Backfill Shares-Historie...")
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

        # 5) Wenn alles gut: Run auf SUCCESS setzen
        print(f"\n=== Backfill-PipelineRun ID: {run_id_for_logging} erfolgreich abgeschlossen. ===")
        run.status = PipelineRunStatus.SUCCESS
        run.end_time = func.now()
        session.commit()

    except Exception as e:
        import traceback
        print("!!!!!!!!!!!!!! SCHWERER FEHLER IM BACKFILL !!!!!!!!!!!!!!", file=sys.stderr)
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
                print(f"Zusätzlicher Fehler beim Loggen des FAILED-Status: {log_e}", file=sys.stderr)
                session.rollback()

    finally:
        session.close()
        print(
            f"--- Backfill-Prozess (Run ID: {run_id_for_logging if run_id_for_logging else '??'}) "
            f"abgeschlossen. Session geschlossen. ---"
        )


if __name__ == "__main__":
    main_backfill()
