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
"""


@contextmanager
def connect(path=None):
    con = sqlite3.connect(path or config.DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
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
        con.executescript(SCHEMA)
