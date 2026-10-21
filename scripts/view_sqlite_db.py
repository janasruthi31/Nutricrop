"""
SQLite Database Viewer Utility for TN Fertilizer Optimizer.
Inspect all tables and confirmed soil reports, farms, and fertilizer recommendations.
Usage:
    python scripts/view_sqlite_db.py
"""

import os
import sys
import sqlite3
import json

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "phase3_soil", "soil_phase3.sqlite3")

def view_database():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at: {DB_PATH}")
        return

    print("=" * 70)
    print("TN FERTILIZER OPTIMIZER - SQLITE DATABASE SUMMARY")
    print(f"Database File: {DB_PATH}")
    print("=" * 70)

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # 1. Table Statistics
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r["name"] for r in cur.fetchall()]
    print("\n[1] ALL SQLITE TABLES:")
    for tbl in tables:
        cur.execute(f"SELECT COUNT(*) as cnt FROM {tbl}")
        count = cur.fetchone()["cnt"]
        print(f"   * {tbl:<28} : {count} records")

    # 2. Latest Confirmed Soil Profiles
    print("\n[2] CONFIRMED SOIL REPORTS IN SQLITE (`soil_profiles`):")
    cur.execute("SELECT soil_profile_id, district, sample_id, verification_status, updated_at, profile_json FROM soil_profiles ORDER BY updated_at DESC LIMIT 5")
    profiles = cur.fetchall()
    if not profiles:
        print("   (No soil profiles confirmed yet)")
    else:
        for idx, p in enumerate(profiles, 1):
            p_data = json.loads(p["profile_json"])
            print(f"   Report #{idx}:")
            print(f"     - Profile ID : {p['soil_profile_id']}")
            print(f"     - District   : {p['district']}")
            print(f"     - Sample ID  : {p['sample_id']}")
            print(f"     - Status     : {p['verification_status']}")
            print(f"     - Updated At : {p['updated_at']}")
            print(f"     - Soil N     : {p_data.get('nitrogen', {}).get('value')} {p_data.get('nitrogen', {}).get('unit')}")
            print(f"     - Soil P     : {p_data.get('phosphorus', {}).get('value')} {p_data.get('phosphorus', {}).get('unit')} ({p_data.get('phosphorus', {}).get('method')})")
            print(f"     - Soil K     : {p_data.get('potassium', {}).get('value')} {p_data.get('potassium', {}).get('unit')}")
            print(f"     - Soil pH    : {p_data.get('ph')}")

    # 3. Saved Farms
    print("\n[3] SAVED FARMS IN SQLITE (`farmer_farms`):")
    cur.execute("SELECT farm_id, district, village, area, area_unit, irrigation, soil_series FROM farmer_farms ORDER BY created_at DESC LIMIT 3")
    farms = cur.fetchall()
    for f in farms:
        print(f"   * Farm {f['farm_id'][:8]}... | {f['district']} | Area: {f['area']} {f['area_unit']} | Irrigation: {f['irrigation']}")

    # 4. Saved Fertilizer Recommendations
    print("\n[4] SAVED FERTILIZER RECOMMENDATIONS IN SQLITE (`saved_recommendations`):")
    cur.execute("SELECT recommendation_id, crop, district, farm_area, farm_area_unit, total_cost_inr, created_at FROM saved_recommendations ORDER BY created_at DESC LIMIT 3")
    recs = cur.fetchall()
    if not recs:
        print("   (No recommendations saved yet)")
    else:
        for r in recs:
            print(f"   * Rec {r['recommendation_id'][:8]}... | Crop: {r['crop']} | Area: {r['farm_area']} {r['farm_area_unit']} | Cost: Rs. {r['total_cost_inr']}")

    print("\n" + "=" * 70)
    con.close()

if __name__ == "__main__":
    view_database()
