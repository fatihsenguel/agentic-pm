import sqlite3
import os

# Pfad zur Datenbank (so wie er im Code genutzt wird)
db_path = os.path.join("data", "portfolio.db")

print(f"🕵️  Prüfe Datenbank unter: {db_path}")

if not os.path.exists(db_path):
    print("❌ FEHLER: Die Datenbank-Datei existiert an diesem Pfad nicht!")
    print("   Prüfe, ob der Ordner 'data' existiert.")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Alle Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print("\n📋 Gefundene Tabellen:")
        for t in tables:
            print(f"   - {t}")
            
        # 2. Gezielte Suche nach macro_data
        if "macro_data" in tables:
            print("\n✅ 'macro_data' Tabelle existiert!")
            
            # 3. Prüfen, was Alembic denkt (alembic_version tabelle)
            if "alembic_version" in tables:
                cursor.execute("SELECT * FROM alembic_version")
                version = cursor.fetchone()
                print(f"\n🏷️  Aktuelle Alembic Revision in DB: {version[0]}")
            else:
                print("\n⚠️  Keine 'alembic_version' Tabelle gefunden (Alembic wurde nie initialisiert?)")
        else:
            print("\n❌ 'macro_data' Tabelle FEHLT!")
            
    except Exception as e:
        print(f"Fehler beim Lesen der DB: {e}")
    finally:
        if 'conn' in locals():
            conn.close()