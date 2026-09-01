import sys
import os
# Pfad-Fix (wie in den anderen Skripten)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Importiere unsere neuen Komponenten
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import get_session, Asset
from portfolio_tool.analytics.calculator import MetricsCalculator

def main_metrics_update():
    print("Starte Berechnung der abgeleiteten Metriken (Schicht 4)...")
    session = get_session()
    
    calculator = MetricsCalculator(session)
    assets = session.query(Asset).all()
    print(f"Berechne Metriken für {len(assets)} Assets...")

    try:
        for asset in assets:
            print(f"--- Verarbeitung {asset.ticker} ---")
            
            # Rufe die neue, historische Methode auf
            calculator.update_historical_market_cap(asset)
            # -------------------------

        session.commit() # Ein Commit am Ende speichert alle Änderungen
        print("Metriken-Update erfolgreich abgeschlossen.")
    except Exception as e:
        print(f"FEHLER beim Metriken-Update: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main_metrics_update()