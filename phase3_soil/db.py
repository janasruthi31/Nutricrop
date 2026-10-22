"""SQLite persistence (the project had no pre-existing DB/schema, so a self-contained SQLite file is used)."""
import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS soil_documents (
  document_id TEXT PRIMARY KEY, farmer_id TEXT NOT NULL, file_path TEXT NOT NULL, file_kind TEXT NOT NULL,
  size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL, status TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  UNIQUE (farmer_id, sha256));
CREATE TABLE IF NOT EXISTS soil_ocr_results (
  ocr_id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES soil_documents(document_id),
  engine TEXT NOT NULL, engine_version TEXT, psm INTEGER, mean_confidence REAL,
  raw_text_redacted TEXT, fields_json TEXT NOT NULL, metadata_json TEXT, quality_json TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS soil_profiles (
  soil_profile_id TEXT PRIMARY KEY, farmer_id TEXT NOT NULL, document_id TEXT REFERENCES soil_documents(document_id),
  source TEXT NOT NULL, fingerprint TEXT NOT NULL, district TEXT, village TEXT, sample_id TEXT, test_date TEXT,
  laboratory TEXT, crop TEXT, verification_status TEXT NOT NULL, profile_json TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  UNIQUE (farmer_id, fingerprint));
CREATE TABLE IF NOT EXISTS soil_profile_fields (
  soil_profile_id TEXT NOT NULL REFERENCES soil_profiles(soil_profile_id), field TEXT NOT NULL,
  ocr_value TEXT, confirmed_value REAL, unit TEXT, test_method TEXT, status TEXT NOT NULL, classification TEXT,
  ocr_confidence REAL, modified_by_user INTEGER NOT NULL, action TEXT,
  PRIMARY KEY (soil_profile_id, field));
CREATE INDEX IF NOT EXISTS idx_profiles_farmer ON soil_profiles(farmer_id);

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT NOT NULL,
  phone TEXT,
  preferred_language TEXT DEFAULT 'en',
  district TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS farmer_farms (
  farm_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  district TEXT NOT NULL,
  village TEXT,
  area REAL NOT NULL,
  area_unit TEXT NOT NULL,
  irrigation TEXT,
  soil_series TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS farmer_fertilizer_history (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  crop TEXT NOT NULL,
  season TEXT,
  year INTEGER,
  fertilizer_product TEXT NOT NULL,
  quantity REAL NOT NULL,
  unit TEXT NOT NULL,
  application_date TEXT,
  notes TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS saved_recommendations (
  recommendation_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  crop TEXT NOT NULL,
  district TEXT NOT NULL,
  farm_area REAL NOT NULL,
  farm_area_unit TEXT NOT NULL,
  target_yield REAL,
  total_cost_inr REAL,
  response_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_notifications (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  category TEXT NOT NULL,
  is_read INTEGER DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weather_cache (
  cache_key TEXT PRIMARY KEY,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  district TEXT,
  current_json TEXT NOT NULL,
  forecast_json TEXT NOT NULL,
  observation_time TEXT NOT NULL,
  source TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fertilizer_prices (
  product_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  n_pct REAL NOT NULL,
  p2o5_pct REAL NOT NULL,
  k2o_pct REAL NOT NULL,
  bag_size_kg REAL NOT NULL,
  price_per_bag_inr REAL NOT NULL,
  price_per_kg_inr REAL NOT NULL,
  source TEXT NOT NULL,
  effective_date TEXT NOT NULL,
  last_updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS password_resets (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  user_id TEXT NOT NULL,
  token_hash TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  used INTEGER DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_password_resets_email ON password_resets(email);
"""


@contextmanager
def connect(path=None):
    con = sqlite3.connect(path or config.DB_PATH, timeout=30.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 30000")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db(path=None):
    with connect(path) as con:
        try:
            con.execute("PRAGMA journal_mode = WAL")
            con.execute("PRAGMA synchronous = NORMAL")
        except Exception:
            pass
        con.executescript(SCHEMA)

        # Migrations for existing databases: ensure farmer_farms has latitude, longitude, taluk, state
        cursor = con.execute("PRAGMA table_info(farmer_farms)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        if "latitude" not in existing_cols:
            con.execute("ALTER TABLE farmer_farms ADD COLUMN latitude REAL")
        if "longitude" not in existing_cols:
            con.execute("ALTER TABLE farmer_farms ADD COLUMN longitude REAL")
        if "taluk" not in existing_cols:
            con.execute("ALTER TABLE farmer_farms ADD COLUMN taluk TEXT")
        if "state" not in existing_cols:
            con.execute("ALTER TABLE farmer_farms ADD COLUMN state TEXT DEFAULT 'Tamil Nadu'")

        # Seed fertilizer_prices from catalog if table is empty
        row = con.execute("SELECT COUNT(*) as cnt FROM fertilizer_prices").fetchone()
        if row and row["cnt"] == 0:
            from phase6_fertilizer.catalog import FERTILIZER_CATALOG
            for item in FERTILIZER_CATALOG:
                con.execute(
                    """INSERT OR IGNORE INTO fertilizer_prices 
                       (product_id, name, category, n_pct, p2o5_pct, k2o_pct, bag_size_kg, price_per_bag_inr, price_per_kg_inr, source, effective_date, last_updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item["id"],
                        item["name"],
                        item["category"],
                        item["n_pct"],
                        item["p2o5_pct"],
                        item["k2o_pct"],
                        item["bag_size_kg"],
                        item["price_per_bag_inr"],
                        item["price_per_kg_inr"],
                        item.get("source", "Department of Fertilizers, GoI (NBS Subsidy Schedule 2024-25)"),
                        item.get("effective_date", "2024-04-01"),
                        "2026-10-14T00:00:00Z"
                    )
                )

