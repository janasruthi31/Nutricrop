# AgroWise AI: Production Scaling & PostgreSQL Architecture Guide

This document specifies the horizontal scaling architecture, PostgreSQL database integration, and multi-worker deployment guidelines for AgroWise AI (SIH1639: "Sustainable Fertilizer Usage Optimizer for Higher Yield").

---

## 1. Switching to PostgreSQL via `DATABASE_URL`

### 1.1 Architecture & Dual-Driver Support
AgroWise AI supports seamless zero-downtime switching between lightweight local SQLite development and production PostgreSQL using the standard `DATABASE_URL` environment variable.

- **Development/Edge default**: Self-contained SQLite file at `phase3_soil/soil_data.db` with WAL (Write-Ahead Logging) mode and 30-second busy timeout.
- **Production PostgreSQL**: Activated automatically whenever `DATABASE_URL` starts with `postgresql://` or `postgres://`.

### 1.2 Configuration
Set `DATABASE_URL` in your production environment (e.g., Docker, Kubernetes, AWS ECS, or `.env`):

```bash
# PostgreSQL Connection String Format:
# postgresql://<username>:<password>@<host>:<port>/<database_name>?sslmode=require
export DATABASE_URL="postgresql://agrowise_user:SecureFarmPass2026@pg-cluster.internal:5432/agrowise_prod?sslmode=prefer"
```

### 1.3 Automatic Initialization & Table Migrations
When `DATABASE_URL` is detected:
1. `phase3_soil.db.connect()` automatically initializes connection pooling using `psycopg2` and `DictCursor`.
2. `init_db()` creates the relational tables (`users`, `soil_documents`, `soil_ocr_results`, `soil_profiles`, `soil_profile_fields`, `farmer_farms`, `farmer_fertilizer_history`, `saved_recommendations`, `weather_cache`, `fertilizer_prices`, and `password_resets`).
3. Seeds standard statutory fertilizer prices from `data/agronomy/fertilizer_prices.json`.

---

## 2. Multi-Worker Server Deployment

### 2.1 Concurrency Model
The FastAPI backend serves CPU-bound tasks (SciPy Mixed-Integer Linear Programming via HiGHS, Tesseract OCR preprocessing, XGBoost yield inference) alongside I/O-bound tasks (Open-Meteo weather lookups, reverse geocoding, database queries).

To maximize multi-core throughput on cloud VM instances:

```bash
# Recommended production command (4 worker processes on a 4-vCPU instance):
uvicorn phase3_soil.main:app \
  --workers 4 \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info \
  --proxy-headers \
  --forwarded-allow-ips='*'
```

### 2.2 Worker Count Rule of Thumb
$$\text{Workers} = (2 \times \text{Number of CPU Cores}) + 1$$

| Instance Type | vCPUs | RAM | Recommended Uvicorn Workers | Expected Concurrency |
| :--- | :--- | :--- | :--- | :--- |
| **Edge / RasPi 4** | 4 | 4 GB | 2 | 50 concurrent farmers |
| **Cloud Standard (c6i.xlarge)** | 4 | 8 GB | 4 | 250 concurrent farmers |
| **State Server (c6i.4xlarge)** | 16 | 32 GB | 16 | 1,200 concurrent farmers |

---

## 3. High-Load Caching Strategies

1. **Weather Caching**: Weather observations and 7-day forecasts for all 38 Tamil Nadu districts are cached with a **3-hour TTL** (`CACHE_TTL_SECONDS = 10800`). Repeat requests hit SQLite/PostgreSQL in `< 2 ms`.
2. **Recommendation Caching**: Identical soil test requests are cached by SHA-256 payload hash for **3 hours**, preventing redundant MILP solver executions.
3. **Seasonal Climatological Fallback**: If Open-Meteo or external network connectivity drops, the system falls back to TNAU seasonal agro-climatology without dropping farmer requests.

---

## 4. Load Testing

A dedicated load-testing utility is provided in `scripts/load_test.py`. It benchmarks concurrent asynchronous requests against `/api/full-recommendation` and `/api/weather/guidance`.

### Running the Load Test:
```bash
python scripts/load_test.py --concurrency 20 --requests 100
```
