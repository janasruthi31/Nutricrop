import sqlite3
import os

db_path = os.path.join("phase3_soil", "soil_phase3.sqlite3")
print("DB Path:", db_path, "Exists:", os.path.exists(db_path))
if os.path.exists(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print("Tables in SQLite DB:", tables)
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cur.fetchone()[0]
        print(f"  - {t}: {cnt} rows")
    con.close()
