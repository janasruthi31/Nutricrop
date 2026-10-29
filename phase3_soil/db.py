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


import logging
import os
import sqlite3
from contextlib import contextmanager

from . import config

logger = logging.getLogger(__name__)


class _PostgresConnectionAdapter:
    """Wraps a psycopg2 connection to provide SQLite-compatible execution semantics."""
    def __init__(self, raw_conn):
        self.raw_conn = raw_conn

    def execute(self, sql: str, params=()):
        if sql.strip().upper().startswith("PRAGMA"):
            class _DummyCursor:
                def fetchall(self):
                    return []
                def fetchone(self):
                    return None
            return _DummyCursor()
        pg_sql = sql.replace("?", "%s")
        if "INSERT OR IGNORE INTO" in pg_sql:
            pg_sql = pg_sql.replace("INSERT OR IGNORE INTO", "INSERT INTO") + " ON CONFLICT DO NOTHING"
        elif "INSERT OR REPLACE INTO" in pg_sql:
            pg_sql = pg_sql.replace("INSERT OR REPLACE INTO", "INSERT INTO")
        cur = self.raw_conn.cursor()
        cur.execute(pg_sql, params)
        return cur

    def executescript(self, script: str):
        cur = self.raw_conn.cursor()
        for statement in script.split(";"):
            stmt = statement.strip()
            if stmt and not stmt.upper().startswith("PRAGMA"):
                try:
                    cur.execute(stmt)
                except Exception as e:
                    logger.debug(f"Statement in executescript skipped: {e}")
        return cur

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        self.raw_conn.close()


@contextmanager
def connect(path=None):
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if db_url and (db_url.startswith("postgres://") or db_url.startswith("postgresql://")):
        try:
            import psycopg2
            import psycopg2.extras
            raw_conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.DictCursor)
            adapter = _PostgresConnectionAdapter(raw_conn)
            try:
                yield adapter
                adapter.commit()
            except Exception:
                adapter.rollback()
                raise
            finally:
                adapter.close()
            return
        except Exception as e:
            logger.warning(f"DATABASE_URL PostgreSQL connection failed ({e}), falling back to SQLite.")

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
        existing_cols = {row["name"] for row in (cursor.fetchall() or [])}
        if "latitude" not in existing_cols:
            try:
                con.execute("ALTER TABLE farmer_farms ADD COLUMN latitude REAL")
            except Exception:
                pass
        if "longitude" not in existing_cols:
            try:
                con.execute("ALTER TABLE farmer_farms ADD COLUMN longitude REAL")
            except Exception:
                pass
        if "taluk" not in existing_cols:
            try:
                con.execute("ALTER TABLE farmer_farms ADD COLUMN taluk TEXT")
            except Exception:
                pass
        if "state" not in existing_cols:
            try:
                con.execute("ALTER TABLE farmer_farms ADD COLUMN state TEXT DEFAULT 'Tamil Nadu'")
            except Exception:
                pass

        # Migrations for farmer_fertilizer_history: ensure backward-compatible support for all prompt attributes
        cursor_fh = con.execute("PRAGMA table_info(farmer_fertilizer_history)")
        fh_cols = {row["name"] for row in (cursor_fh.fetchall() or [])}
        for col_name, col_type in [
            ("farm_id", "TEXT"),
            ("fertilizer_grade", "TEXT"),
            ("category", "TEXT"),
            ("bag_weight_kg", "REAL"),
            ("field_area", "REAL"),
            ("field_area_unit", "TEXT"),
            ("application_method", "TEXT"),
            ("n_pct", "REAL"),
            ("p2o5_pct", "REAL"),
            ("k2o_pct", "REAL"),
        ]:
            if col_name not in fh_cols:
                try:
                    con.execute(f"ALTER TABLE farmer_fertilizer_history ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

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

