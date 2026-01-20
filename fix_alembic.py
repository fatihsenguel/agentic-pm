import sqlite3
import os

# Pfad zur DB
db_path = os.path.join("data", "portfolio.db")

print(f"🔧 Repariere Alembic Version in {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Wir setzen die Version auf die ID der letzten existierenden Datei zurück.
# Basierend auf deinem Tree ist das 'd4db413ede26'
previous_revision = 'd4db413ede26' 

try:
    cursor.execute(f"UPDATE alembic_version SET version_num = '{previous_revision}'")
    conn.commit()
    print(f"✅ Datenbank erfolgreich auf Version '{previous_revision}' zurückgesetzt.")
except Exception as e:
    print(f"❌ Fehler: {e}")
finally:
    conn.close()