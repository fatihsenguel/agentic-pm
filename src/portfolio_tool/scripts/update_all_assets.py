import sys
import os
import datetime
from sqlalchemy.orm import Session  # Für Type Hinting

# --- Pfad-Fix (unverändert) ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)
# ---

# (1) NEUE IMPORTE für Logging, Quota und Status
# Diese funktionieren, weil 'project_root' (der Ordner über 'portfolio_tool') im Pfad ist
from portfolio_tool.database_setup import ( 
    get_session, Asset, PipelineRun, 
    PipelineRunStatus, func
)
from portfolio_tool.data_manager import DataManager
from portfolio_tool.providers.base import DataProviderInterface
from portfolio_tool.providers.yfinance_provider import YFinanceProvider

# (WICHTIG) Der neue Service, den wir injizieren - KORRIGIERT
from portfolio_tool.services.quota_manager import DatabaseQuotaManager

# --- (2) KONFIGURATION (angepasst) ---
STOCKS_TO_TRACK = [
    {'ticker': 'AAPL', 'name': 'Apple Inc.', 'class': 'Stock'},
    {'ticker': 'MSFT', 'name': 'Microsoft Corporation', 'class': 'Stock'},
    {'ticker': 'AMZN', 'name': 'Amazon.com, Inc.', 'class': 'Stock'},
    #{'ticker': 'GOOGL', 'name': 'Alphabet Inc. (Class A)', 'class': 'Stock'},
    # (Fügen Sie hier die restlichen MAG7 hinzu, z.B. NVDA, META, TSLA)
]
NUM_ASSETS = len(STOCKS_TO_TRACK) 

# Konfiguration für den Provider
PROVIDER_NAME = "yfinance"
# (Dieser Wert ist ein Sicherheitsnetz. Für AlphaVantage wäre er z.B. 25)
YFINANCE_DAILY_LIMIT = 2000 


# --- (3) PROVIDER "FABRIK" (ANGEPASST) ---
def get_provider(quota_manager: DatabaseQuotaManager) -> DataProviderInterface:
    """
    Erstellt und gibt den konfigurierten Datenprovider zurück.
    Akzeptiert den QuotaManager per Dependency Injection.
    """
    if PROVIDER_NAME == "yfinance":
        # Wir übergeben den Manager an den Konstruktor von YFinanceProvider
        return YFinanceProvider(
            quota_manager=quota_manager,
            per_minute_limit=60 # Das Frequenz-Limit bleibt
        )
    else:
        raise ValueError(f"Unbekannter Provider: {PROVIDER_NAME}")

# --- (4) HAUPTFUNKTION (STARK ANGEPASST FÜR LOGGING & STATUS) ---

def main_update():
    print("Starte intelligenten Update-Prozess (Phase 2)...")
    
    session: Session = get_session()
    run: PipelineRun = None # Wichtig: 'run' initialisieren
    run_id_for_logging: int = 0

    try:
        # --- 1. PipelineRun erstellen ---
        # Wir erstellen den "Eltern-Eintrag" für diesen Lauf.
        # Wir committen sofort, um die 'run.id' für den QuotaManager zu erhalten.
        run = PipelineRun(
            script_name="scripts/update_all_assets.py",
            status=PipelineRunStatus.RUNNING
        )
        session.add(run)
        session.commit()
        run_id_for_logging = run.id
        print(f"\n=== Starte PipelineRun ID: {run_id_for_logging} ===")

        # --- 2. Services, Provider und Manager initialisieren ---
        
        # Erstelle den zentralen QuotaManager, gebunden an diesen einen Run
        quota_manager = DatabaseQuotaManager(
            session=session,
            pipeline_run_id=run.id,
            provider_name=PROVIDER_NAME,
            daily_limit=YFINANCE_DAILY_LIMIT
        )
        
        # Erstelle den Provider und injiziere den QuotaManager
        provider_instance = get_provider(quota_manager)
        
        # Erstelle den DataManager (Konstruktor unverändert)
        manager = DataManager(session, provider_instance)

        # --- 3. Asset-Setup (unverändert) ---
        print("Lade Assets aus der DB...")
        db_assets = session.query(Asset).all()
        asset_map = {asset.ticker: asset for asset in db_assets}
        
        for stock_info in STOCKS_TO_TRACK:
            if stock_info['ticker'] not in asset_map:
                print(f"Erstelle fehlendes Asset: {stock_info['ticker']}")
                asset = manager.get_or_create_asset(
                    ticker=stock_info['ticker'],
                    name=stock_info['name'],
                    asset_class=stock_info['class']
                )
                if asset:
                    asset_map[asset.ticker] = asset
        
        # --- 4. Scheduling-Logik (unverändert) ---
        
        today = datetime.date.today()
        weekday = today.weekday()
        day_of_month = today.day

        print(f"\n=== 1. TÄGLICHE AUFGABEN (Preise, Divs, Splits) ===")
        for asset in asset_map.values():
            print(f"\n--- Tägliche Verarbeitung {asset.ticker} ---")
            manager.update_prices_for_asset(asset)
            manager.update_dividends_for_asset(asset)
            manager.update_splits_for_asset(asset)
        
        print(f"\n=== 2. WÖCHENTLICH ROTIERENDE AUFGABEN (Tag {weekday}) ===")
        if weekday < NUM_ASSETS:
            # ... (unveränderte Logik) ...
            ticker_to_update = STOCKS_TO_TRACK[weekday]['ticker']
            asset = asset_map.get(ticker_to_update)
            if asset:
                print(f"--- Wöchentliches Profil-Update für {asset.ticker} ---")
                manager.update_fundamental_data(asset)
                manager.force_update_asset_info(asset)
        else:
            print("... (Kein Asset für Wochentag > 4 geplant)")

        print(f"\n=== 3. MONATLICHE AUFGABEN (Tag {day_of_month}) ===")
        if 1 <= day_of_month <= NUM_ASSETS:
            # ... (unveränderte Logik) ...
            ticker_to_update = STOCKS_TO_TRACK[day_of_month - 1]['ticker']
            asset = asset_map.get(ticker_to_update)
            if asset:
                print(f"--- Monatliches Earnings/Shares-Update für {asset.ticker} ---")
                manager.update_quarterly_earnings_for_asset(asset)
                manager.update_shares_history_for_asset(asset)
        else:
            print(f"... (Kein Asset für Monatstag {day_of_month} geplant)")
        
        # --- 5. Erfolgreichen Run markieren ---
        print(f"\n=== PipelineRun ID: {run_id_for_logging} erfolgreich abgeschlossen. ===")
        run.status = PipelineRunStatus.SUCCESS
        run.end_time = func.now()
        session.commit() # Finaler Commit für den SUCCESS-Status

    except Exception as e:
        print(f"!!!!!!!!!!!!!! SCHWERWIEGENDER FEHLER !!!!!!!!!!!!!!", file=sys.stderr)
        print(f"Ein Fehler ist aufgetreten: {e}", file=sys.stderr)
        session.rollback() # Alle Daten-Änderungen (außer dem Run) zurückrollen
        
        if run:
            # 'run' ist jetzt "detached" durch den Rollback.
            # Wir müssen es in der (jetzt zurückgerollten) Session
            # aktualisieren, um den Fehler zu loggen.
            try:
                run.status = PipelineRunStatus.FAILED
                run.end_time = func.now()
                run.error_message = str(e)[:950] # Gekürzt für DB
                session.add(run) # Das 'detached' Objekt wieder hinzufügen
                session.commit() # Den FAILED-Status committen
            except Exception as log_e:
                print(f"ZUSÄTZLICHER FEHLER beim Loggen des FAILED-Status: {log_e}", file=sys.stderr)
                session.rollback()
            
    finally:
        session.close()
        print(f"--- Update-Prozess (Run ID: {run_id_for_logging if run_id_for_logging else '??'}) abgeschlossen. Session geschlossen. ---")


if __name__ == "__main__":
    main_update()