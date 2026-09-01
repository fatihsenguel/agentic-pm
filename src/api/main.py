# api/main.py
import sys
import os
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime

# --- (1) Pfad-Fix (Genau wie in 'scripts') ---
# Fügt das Hauptverzeichnis (Finance_Phase_3) zum Suchpfad hinzu,
# damit wir 'portfolio_tool' importieren können.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)
# --- Ende Pfad-Fix ---

# (2) Importiere jetzt unsere Projekt-Module
try:
    from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import get_session, Asset, DailyPrice
except ImportError:
    print("FEHLER: Konnte 'portfolio_tool' nicht importieren.")
    print("Stelle sicher, dass 'api/main.py' im Root-Verzeichnis des Projekts liegt.")
    sys.exit(1)

# (3) Erstelle die FastAPI-App
app = FastAPI(
    title="Portfolio Tool API",
    description="Ein minimaler Endpunkt zur Überwachung der Datenfrische.",
    version="0.1.0"
)

# (4) Definition der Abhängigkeit (Dependency)
def get_db_session():
    """Stellt eine DB-Session bereit und schließt sie nach der Anfrage."""
    session = None
    try:
        session = get_session()
        yield session
    finally:
        if session:
            session.close()

# (5) Der "Freshness"-Endpunkt
@app.get("/freshness")
def get_data_freshness(session: Session = Depends(get_db_session)):
    """
    Überprüft das letzte verfügbare Datum (MAX(date)) für alle Assets
    in der 'daily_prices'-Tabelle.
    """
    print("API-Aufruf: /freshness")
    
    try:
        # Führe die Abfrage aus:
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
        
        # Formatiere die Ergebnisse in ein sauberes Dictionary
        result = {
            ticker: last_date.strftime("%Y-%m-%d") 
            for ticker, last_date in freshness_query
        }
        
        return result

    except Exception as e:
        print(f"Fehler bei der /freshness Abfrage: {e}")
        return {"error": str(e)}

@app.get("/")
def read_root():
    """Wurzel-Endpunkt, der zur Dokumentation weiterleitet."""
    return {"message": "Willkommen bei der Portfolio Tool API. Gehe zu /docs für die API-Dokumentation."}