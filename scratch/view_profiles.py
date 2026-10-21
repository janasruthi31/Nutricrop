import sqlite3
import os
import json

db_path = os.path.join("phase3_soil", "soil_phase3.sqlite3")
con = sqlite3.connect(db_path)
cur = con.cursor()
cur.execute("SELECT soil_profile_id, farmer_id, district, village, sample_id, crop, verification_status, updated_at FROM soil_profiles")
rows = cur.fetchall()
print(f"Total confirmed soil profiles in SQLite: {len(rows)}")
for r in rows:
    print(r)
con.close()
