import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
conn.close()

print(f"Base de donnees : {DB_PATH}")
print("Tables dans la base :")
for t in sorted(tables):
    print(f"  - {t}")

if "avances_personnel" in tables:
    print("\n[OK] La table avances_personnel existe !")
else:
    print("\n[MANQUANT] La table avances_personnel n'existe PAS.")