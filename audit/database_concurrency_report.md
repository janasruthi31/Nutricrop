# Database Concurrency, Integrity & Reliability Report (Phase 6)

**Date:** 2026-10-21  
**Project:** AgroWise AI (Database Concurrency & Persistence Engine)  
**Status:** Hardened, Concurrency-Tested, Migration-Ready  
**Scope:** SQLite Concurrency Hardening (WAL Mode, Busy Timeouts, Connection Lifecycle) and PostgreSQL Production Migration Architecture.

---

## 1. Executive Summary

AgroWise AI utilizes SQLite for local persistence of soil health cards, farmer profiles, farm boundaries, and recommendation histories. Under default settings, SQLite uses standard rollback journaling, which acquires an exclusive database lock during writes and blocks all concurrent read requests. Furthermore, unmanaged connection sharing across threads can cause "database is locked" exceptions or corrupted transactions.

In Phase 6, SQLite was hardened with Write-Ahead Logging (WAL), connection timeout scaling, robust transaction boundaries, and thread-isolated context managers. Additionally, a comprehensive production PostgreSQL migration plan was designed for high-concurrency multi-user workloads.

---

## 2. SQLite Hardening & Concurrency Controls

### 2.1 Write-Ahead Logging (WAL) Mode
In `phase3_soil/db.py`, database initialization now executes:
```sql
PRAGMA journal_mode = WAL;
```
* **Benefit:** WAL mode completely decouples readers from writers. Readers read from the database file while writers append changes to the separate `-wal` file. Readers never block writers, and writers never block readers.
* **Checkpointing:** Passive checkpointing runs automatically when the WAL file reaches 1,000 pages (approx. 4MB), ensuring minimal memory overhead.

---

### 2.2 Busy Timeout & Lock Contention Handling
```python
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
```
* **30-Second Timeout (`busy_timeout = 30000`):** When two transactions attempt to write simultaneously, SQLite waits up to 30,000 milliseconds for the lock to become available before raising an operational error.
* **Connection Lifecycle:** Connections are created on-demand within a scoped context manager and strictly closed in `finally:`. Connections are never shared across FastAPI async request workers or threads.
* **Deterministic Rollback:** Unhandled exceptions trigger an explicit `con.rollback()`, preventing partially written records or transaction leaks.
* **Foreign Key Integrity:** `PRAGMA foreign_keys = ON` guarantees relational consistency between `soil_documents` and `soil_profiles`.

---

## 3. Production PostgreSQL Migration Readiness

For state-wide deployments serving thousands of simultaneous Tamil Nadu farmers during peak sowing seasons (Kharif/Rabi), migrating from SQLite to PostgreSQL is recommended.

### 3.1 Architecture Comparison

| Metric / Feature | Current SQLite Deployment | Target PostgreSQL 16 Deployment |
| :--- | :--- | :--- |
| **Concurrency Model** | Single-writer lock (WAL allows concurrent reads) | Multi-Version Concurrency Control (MVCC) with concurrent reads and writes |
| **Connection Pooling** | Per-thread connection lifecycle | Connection pool via `asyncpg` / `SQLAlchemy` (e.g., 20 pooled, 10 overflow) |
| **Crash Safety** | Process-level write ahead log | Full Write-Ahead Log with Point-In-Time Recovery (PITR) and streaming replication |
| **Geospatial Queries** | Flat latitude/longitude columns | PostGIS extension (`GEOGRAPHY(Point, 4326)`) with spatial indexing |
| **Target Scale** | Up to 50 concurrent requests | 5,000+ concurrent requests |

---

### 3.2 Schema DDL Migration Mapping

```sql
-- PostgreSQL 16 Production Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Table
CREATE TABLE users (
    user_id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(32),
    preferred_language VARCHAR(8) DEFAULT 'ta',
    district VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_district ON users(district);

-- Password Resets (Time-limited OTPs)
CREATE TABLE password_resets (
    id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at BIGINT NOT NULL,
    used SMALLINT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_password_resets_email ON password_resets(email);

-- Recommendations History
CREATE TABLE recommendations (
    recommendation_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    crop VARCHAR(64) NOT NULL,
    district VARCHAR(64) NOT NULL,
    farm_area NUMERIC(10, 4) NOT NULL,
    farm_area_unit VARCHAR(16) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_recs_user ON recommendations(user_id, created_at DESC);
CREATE INDEX idx_recs_crop ON recommendations(crop);
```

---

### 3.3 Zero-Downtime Migration Execution Plan

1. **Step 1 (Schema & DB Provisioning):** Provision AWS RDS PostgreSQL / Cloud SQL instance with automated daily snapshots and cross-AZ replication.
2. **Step 2 (Data Extraction & Loading):** Use `pgloader` with an automated configuration script to migrate SQLite records into PostgreSQL tables without datatype corruption:
   ```bash
   pgloader sqlite:///data/soil_reports.db postgresql://user:pwd@host/agrowise_prod
   ```
3. **Step 3 (Dual-Write Validation):** Deploy application release with dual-writing to SQLite and PostgreSQL for 48 hours to confirm transaction consistency.
4. **Step 4 (Cutover & Validation):** Point application environment variables (`DATABASE_URL`) to PostgreSQL. Validate authentication, soil uploads, and recommendation downloads.
5. **Step 5 (Rollback Strategy):** In the event of an unpredicted database connection failure, the application configuration can revert to SQLite by swapping `DATABASE_URL` back to the SQLite connection string within 60 seconds.
