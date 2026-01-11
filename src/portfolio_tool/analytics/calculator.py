# in portfolio_tool/analytics/calculator.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
# Importiere die DB-Modelle aus Schicht 2
from ..database_setup import Asset, DailyPrice, SharesHistory

class MetricsCalculator:
    
    def __init__(self, session: Session):
        self.session = session

    def update_historical_market_cap(self, asset: Asset):
        """
        Berechnet Market Cap für alle DailyPrice-Einträge, 
        bei denen sie 'NULL' ist. (Backfill & Delta-Update in einem).
        """
        print(f"  > Prüfe historische Market Cap für {asset.ticker}...")

        # 1. HOLE ROHDATEN (EXTRAHIEREN)
        # Finde alle Preise, für die wir noch keine Market Cap haben.
        prices_to_calculate = self.session.query(DailyPrice).filter(
            DailyPrice.asset_id == asset.id,
            DailyPrice.market_cap == None # <-- Unsere "To-Do-Liste"
        ).order_by(DailyPrice.date).all()

        if not prices_to_calculate:
            print("  > Market Cap ist auf dem neuesten Stand.")
            return

        # Hole die *gesamte* Aktienanzahl-Historie für dieses Asset,
        # sortiert nach Datum.
        shares_history = self.session.query(SharesHistory).filter(
            SharesHistory.asset_id == asset.id
        ).order_by(SharesHistory.date).all()

        if not shares_history:
            print(f"  > FEHLER: Keine Aktienanzahl-Historie für {asset.ticker} gefunden. Überspringe.")
            return

        # 2. BERECHNE METRIK (TRANSFORMIEREN)
        # Dies ist eine effiziente "Zwei-Listen"-Iteration, um 
        # Tausende von DB-Abfragen zu vermeiden.
        
        shares_idx = 0 # Unser "Zeiger" für die Aktienanzahl-Liste
        updated_count = 0
        
        for price in prices_to_calculate:
            # Finde die korrekte Aktienanzahl für das Datum des Kurses
            # Wir spulen den 'shares_idx'-Zeiger vor, bis das 
            # shares_date das price.date "einholt" oder überholt.
            while (shares_idx + 1 < len(shares_history) and 
                   shares_history[shares_idx + 1].date <= price.date):
                shares_idx += 1
            
            # Jetzt ist shares_history[shares_idx] der korrekte
            # (letzte bekannte) Wert für 'shares' an diesem Tag.
            correct_shares = shares_history[shares_idx].shares
            
            # 3. LADEN (ZURÜCKSCHREIBEN INS MODELL)
            price.market_cap = price.close * correct_shares
            updated_count += 1
            
        print(f"  > {updated_count} neue Market Cap-Datenpunkte berechnet.")
        # Der Commit passiert im Hauptskript (Schritt 4)