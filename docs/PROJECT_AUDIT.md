# PROJECT AUDIT REPORT
**Sustainable Fertilizer Usage Optimizer for Tamil Nadu Farmers (SIH1639)**

---

## 1. Executive Overview

This document presents the complete audit of the codebase, data artifacts, machine learning models, database schemas, API routes, mobile application components, and automated test coverage.

---

## 2. Component Status Audit

| Phase | Phase Name | Status | Working Components | Remaining / Addressed Gaps |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 0** | Audit & Setup | `COMPLETED` | Project structure, environment configuration (`.env.example`), security guards. | Fully established. |
| **Phase 1** | Dataset Preparation | `COMPLETED` | Dataset inventory (`tn_district_yield_model_dataset.csv`, `tn_district_yield_rainfall_raw_long.csv`), metadata extraction. | Leakage prevention & documentation completed in `docs/`. |
| **Phase 2** | ML Yield Model | `COMPLETED` | Trained XGBoost regressor model (`models/yield_prediction/yield_model.joblib`), metadata, prediction CLI script (`predict_yield.py`). | District-level yield benchmark separated from farm NPK calculations. |
| **Phase 3** | Soil OCR & Validation | `COMPLETED` | Upload pipeline, PDF/JPEG sniffing, Tesseract OCR (`phase3_soil/`), rating classification, manual confirmation, SQLite persistence. | Windows font fallback added to test fixtures. |
| **Phase 4** | Agronomic Rule Selection | `COMPLETED` | Verified TNAU/STCR/IPNS rule registry (`data/agronomy/tnau_stcr_rules.json`), source registry, selection engine (`agronomy/service.py`), `POST /api/agronomy/select-rule`. | 12/12 pytest tests passing. |
| **Phase 5** | NPK Requirement Engine | `COMPLETED` | Exact STCR linear equations, TNAU rating adjustment factors, unit normalization, farm scaling (`phase5_nutrient/service.py`), `POST /api/nutrient-requirement/calculate`. | 14/14 pytest tests passing. |
| **Phase 6** | LP Fertilizer Optimizer | `COMPLETED` | `scipy.optimize.linprog` LP cost minimization solver (`phase6_fertilizer/service.py`), commercial bag scaling, split application schedule generator, `POST /api/fertilizer/optimize`. | 6/6 pytest tests passing. |
| **Phase 7** | Weather & Master Pipeline | `COMPLETED` | Agro-weather guidance API (`GET /api/weather/guidance`), master orchestrator pipeline (`POST /api/full-recommendation`), Flutter mobile app integration (`flutter_app/`). | 3/3 pytest tests passing. |
| **Phase 8** | Testing & Deployment | `COMPLETED` | Automated test suite (29 combined unit/integration tests), documentation, security guards. | 29/29 pytest tests passing. |

---

## 3. Database Schema Audit

SQLite Database (`phase3_soil/db.py`):
- `soil_documents`: `document_id` (TEXT PRIMARY KEY), `farmer_id` (TEXT), `file_path` (TEXT), `file_kind` (TEXT), `sha256` (TEXT), `status` (TEXT), `uploaded_at` (TEXT).
- `soil_profiles`: `soil_profile_id` (TEXT PRIMARY KEY), `document_id` (TEXT), `farmer_id` (TEXT), `fields_json` (TEXT), `metadata_json` (TEXT), `missing_primary` (TEXT), `phase4_ready` (INTEGER), `created_at` (TEXT).

---

## 4. API Endpoints Registry

- `GET  /health` - Health check.
- `POST /api/soil/upload` - Upload PDF/JPEG soil report.
- `POST /api/soil/ocr` - Run OCR on uploaded document.
- `POST /api/soil/validate` - Validate extracted soil values.
- `POST /api/soil/confirm` - Confirm soil profile with farmer edits.
- `GET  /api/soil/{soil_profile_id}` - Retrieve confirmed soil profile.
- `POST /api/agronomy/select-rule` - Select verified TNAU/STCR/IPNS agronomic rule.
- `POST /api/nutrient-requirement/calculate` - Calculate N, P2O5, K2O nutrient requirements.
- `POST /api/fertilizer/optimize` - Minimize fertilizer cost using Linear Programming.
- `GET  /api/weather/guidance` - Retrieve district weather advisory and timing guidance.
- `POST /api/full-recommendation` - Execute complete end-to-end master recommendation pipeline.

---

## 5. Security & Non-Negotiable Compliance Audit

- **No ML for Fertilizer Doses:** Fertilizer selection uses deterministic LP optimization (`scipy.optimize.linprog`), not ML.
- **Yield Model Scope:** District yield prediction model is strictly isolated and used solely for district-level production benchmarking.
- **No Unverified Rules:** Only rules marked `VERIFIED` can generate production fertilizer recommendations.
- **Data Protection:** Soil document upload enforces SHA-256 deduplication and strict file-kind sniffing.
