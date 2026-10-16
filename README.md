# AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers

**Project Reference: SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield**  
**Audit & Engineering Release: October 2026**  
**Author & Lead Engineer:** Senior Python/FastAPI Engineer, Flutter/Dart Developer, Agricultural Data Scientist, Optimization Engineer, Database Engineer, QA Engineer & Security Auditor  

---

## 1. Overview & System Architecture

An end-to-end, scientifically grounded decision support system designed specifically for Tamil Nadu farmers. The application strictly adheres to official Tamil Nadu Agricultural University (TNAU) Soil Test Crop Response (STCR) and Integrated Plant Nutrition System (IPNS) guidelines, mathematical whole-bag fertilizer cost optimization, district-level XGBoost crop yield prediction, live agro-weather spray advisories, and an interactive 27-screen mobile/web interface localized dynamically in **Tamil (தமிழ்)**, **English**, and **Hindi (हिन्दी)**.

### Architectural Separation of Concerns:
1. **Soil Health Card Ingestion & Validation (Phase 3)**: Multi-format OCR extraction (PDF/JPEG/PNG) requiring explicit farmer review and confirmation (`POST /api/soil/confirm`).
2. **Agronomic Rule Selection & NPK Calculation (Phase 4 & 5)**: Deterministic, verified TNAU STCR-IPNS polynomial equations calculating exact $\text{N}$, $\text{P}_2\text{O}_5$, and $\text{K}_2\text{O}$ requirements with unit normalization (`t/ha`, `q/ha`, `kg/ha`, acres, hectares).
3. **Whole-Bag Mixed-Integer Optimizer (Phase 6)**: Exact Mixed-Integer Linear Programming (MILP) via `scipy.optimize.milp` using integer commercial bag decision variables (45 kg Urea, 50 kg DAP, MOP, SSP, Complex) to mathematically guarantee the lowest purchase cost without heuristic rounding.
4. **District-Level Crop Yield Benchmark (Phase 2)**: 9-feature XGBoost regressor (`yield_model.joblib`) providing historical agro-climatic benchmarks without altering or overriding deterministic NPK recommendations.
5. **Agro-Weather Timing Guidance (Phase 7)**: Live Open-Meteo rainfall and temperature forecast with resilient error isolation (weather outages never block valid fertilizer recommendations).
6. **Multi-User Security & Persistence (Phase 7 Extra API)**: JWT authentication with strict object-level authorization preventing cross-farmer data access, persisting recommendations and generating audit-ready PDF reports via ReportLab.

---

## 2. Prerequisites & System Requirements

- **Operating System:** Windows 10/11, Ubuntu 20.04+, or macOS
- **Python:** Version 3.10 to 3.12 (Python 3.12 recommended)
- **Flutter / Dart:** Flutter SDK 3.19.0+ / Dart 3.3.0+
- **OCR Engine (Optional for live scanned images):** Tesseract OCR 5.x (`tesseract-ocr`)
- **Web Browser:** Google Chrome / Edge (for Flutter Web)

---

## 3. Environment & Configuration Setup

1. Copy the example environment configuration:
   ```powershell
   copy .env.example .env
   ```
2. Verify environment settings in `.env`:
   ```ini
   ENVIRONMENT=production
   DEBUG=False
   DATABASE_URL=sqlite:///./soil_phase3.sqlite3
   JWT_SECRET=production_super_secret_jwt_key_sih1639_tnau
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   WEATHER_API_TIMEOUT_SECONDS=10
   OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast
   ```

---

## 4. Python Backend Installation & Database Initialization

1. Activate virtual environment (or create one):
   ```powershell
   # If creating new venv:
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Database Setup:
   The SQLite database `soil_phase3.sqlite3` is automatically initialized on application startup with all 10 verified tables:
   - `users`: Authenticated farmer accounts with password hashes
   - `farmer_farms`: Land holdings, district centroids, soil series
   - `farmer_fertilizer_history`: Historical applications & organic manure tracking
   - `saved_recommendations`: Full recommendation audit trail
   - `user_notifications`: User-specific agro-alerts & advisories
   - `soil_documents`, `soil_ocr_results`, `soil_profiles`, `soil_profile_fields`: OCR records

4. Trained Machine Learning Artifacts:
   - Model Path: `models/yield_prediction/yield_model.joblib`
   - Metadata & Schema: `models/yield_prediction/metadata.json`

---

## 5. How to Run the Applications

### A. Run Backend API Server (FastAPI)
```powershell
uvicorn phase3_soil.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### B. Run Mobile / Web Frontend (Flutter)
```powershell
cd flutter_app
flutter pub get
flutter run -d chrome
```

---

## 6. How to Run Automated Test Suites

### A. Python Backend & ML Test Suite (97 Tests)
```powershell
.\venv\Scripts\pytest.exe -v
```
*Current Result: 97 passed, 1 warning, 2 subtests passed in 56.27s (100% pass rate).*

### B. Flutter Widget & Integration Test Suite (18 Tests)
```powershell
cd flutter_app
flutter test
```
*Current Result: 18 passed in 39.0s (100% pass rate).*

### C. Flutter Static Code Analysis
```powershell
cd flutter_app
flutter analyze
```
*Current Result: No issues found! (ran in 19.8s).*

---

## 7. Supported Features

- **27 Responsive Screens:** Localized dynamically in Tamil (தமிழ்), English, and Hindi (हिन्दी).
- **TNAU STCR-IPNS Agronomic Rules:** Verified formulas for Rice, Cotton, Hybrid Maize, and Rainfed Pulses (Blackgram).
- **Commercial Package Whole-Bag MILP Solver:** Solves for integer bags (45kg Urea, 50kg DAP, MOP, SSP, Complex) using statutory subsidized MRPs (effective 2024-04-01).
- **Crop-Specific Phenological Split Schedules:** Basal, Tillering, Panicle (Rice); Basal, Squaring, Boll (Cotton); Basal, Knee-high, Tasseling (Maize); 100% basal at sowing (Pulses).
- **Soil Health Card OCR Workflow:** Strict distinction between extracted values and confirmed values (`farmer_confirmed=true`).
- **Security & Multi-User Isolation:** Protected endpoints reject unauthenticated access with 401; cross-farmer resource queries return 403 Forbidden.
- **Server-Side PDF Export:** Audit-grade ReportLab PDF report generation matching saved recommendation data.

---

## 8. What Has and Has Not Been Independently Verified

### Independently Verified:
- **TNAU STCR Equations:** Rice (`TNAU_STCR_IPNS_RICE_001`), Cotton (`TNAU_STCR_IPNS_COTTON_001`), Hybrid Maize (`TNAU_STCR_IPNS_MAIZE_001`), and Blackgram (`TNAU_STD_BLACKGRAM_RF_001`) verified against the official TNAU Crop Production Guide 2020.
- **Optimizer Mathematical Optimality:** Exact match between `scipy.optimize.milp` results and exhaustive brute-force integer search.
- **Unit Conversions:** $1\text{ quintal} = 0.1\text{ tonne}$, $1\text{ acre} = 0.404686\text{ ha}$, $\text{P} \times 2.291 = \text{P}_2\text{O}_5$, $\text{K} \times 1.205 = \text{K}_2\text{O}$.
- **XGBoost 9-Feature Pipeline:** Validated against `metadata.json` and `yield_model.joblib` without retraining or fabricating predictions.
- **Security Isolation:** Verified through automated tests that Farmer A cannot access Farmer B's records.

### Documented Limitations & Not Independently Verified:
- **Banana STCR Rule (`TNAU_STCR_BANANA_001`):** Marked as `PENDING_VERIFICATION` and excluded from production recommendations pending official TNAU committee release.
- **Micro-plot Soil Heterogeneity:** STCR formulas assume composite field sampling per Soil Health Card guidelines.
- **Retail Pricing Variations:** Statutory MRPs reflect Government of India NBS notification rates; local primary agricultural cooperative societies (PACCS) may assess nominal local handling charges.
- **Physical Device Deployment:** Physical Android/iOS hardware execution was not performed due to headless container execution; web build was validated and compiled successfully (`flutter build web`).
