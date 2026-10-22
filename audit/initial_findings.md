# Phase 1: Repository Audit and Baseline Findings

**Project:** AgroWise AI — AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Root Path:** `C:\Users\hp\OneDrive\Documents\TN_Yield_Model_Phase3_Combined`  
**Audit Date:** 2026-10-21  
**Environment Baseline:**
- **Python:** 3.11.0
- **Flutter:** 3.32.3 (Channel stable)
- **Dart:** 3.8.1
- **Pytest:** 9.1.1 (Backend tests: 143 passed, 1 warning in 61.55s)
- **Flutter Test:** 20 passed in 4.0s

---

## 1. Application Architecture and End-to-End Trace

```mermaid
flowchart TD
    subgraph Client [Flutter Mobile & Web App]
        A1[Soil Document Upload: PDF/Image] --> A2[VerifyScreen: Farmer Confirms Values]
        A2 --> A3[FarmDetailsScreen: Area, Series, FYM]
        A3 --> A4[CropSelectionScreen: Crop, Variety, Target Yield]
        A4 --> A5[FinalRecommendationScreen: Dynamic Plan]
    end

    subgraph Backend [FastAPI Microservices]
        B1["/api/soil/upload & /api/soil/documents/{id}/ocr (Phase 3)"]
        B2["/api/soil/documents/{id}/confirm (Phase 3)"]
        B3["/api/agronomy/select-rule (Phase 4)"]
        B4["/api/nutrient/calculate-npk (Phase 5)"]
        B5["/api/fertilizer/optimize (Phase 6 MILP)"]
        B6["Open-Meteo Weather Advisory (Phase 7)"]
        B7["Phase 2 XGBoost Yield Model"]
        B8["/api/full-recommendation (Phase 7 Orchestrator)"]
    end

    subgraph Persistence [SQLite DB & Storage]
        C1[(soil_documents & soil_ocr_results)]
        C2[(soil_profiles & soil_profile_fields)]
        C3[(saved_recommendations & farmer_farms)]
        C4[(users & fertilizer_prices)]
    end

    A1 -->|POST /api/soil/upload| B1
    B1 --> C1
    B1 --> A2
    A2 -->|POST /api/soil/documents/{id}/confirm| B2
    B2 --> C2
    A5 -->|POST /api/full-recommendation| B8
    B8 --> B3
    B8 --> B4
    B8 --> B5
    B8 --> B6
    B8 --> B7
    B8 --> C3
    C3 --> A5
```

### Trace of Pipeline:
1. **Upload & OCR (Phase 3):** Farmer uploads a PDF or camera scan to `/api/soil/upload`. If kind is PDF, `pdf2image` (Poppler) renders pages; `pytesseract` extracts text and OpenCV deskews/thresholds images.
2. **Farmer Confirmation Loop:** Extracted fields (N, P, K, pH, EC, OC, Micronutrients) are staged. `VerifyScreen` allows the farmer to review and edit values, then posts to `/api/soil/documents/{id}/confirm`, creating a verified `soil_profiles` entry.
3. **Agronomic Rule Matching (Phase 4):** `/api/agronomy/select-rule` queries `data/agronomy/tnau_stcr_rules.json` to match crop, soil series, and district.
4. **Targeted Nutrient Calculation (Phase 5):** `NutrientCalculationService` evaluates STCR-IPNS polynomial equations ($FN = aT - bSN - cFYM$) or rating-adjusted RDF, clamping negative values to zero.
5. **MILP Fertilizer Optimization (Phase 6):** `FertilizerOptimizerService` formulates integer commercial bag variables and calls `scipy.optimize.milp` with HiGHS solver to minimize purchase cost.
6. **Integration Orchestrator (Phase 7):** Chains Phases 4, 5, 6, queries Open-Meteo for live spray/top-dressing timing advisories, calls the XGBoost model for district benchmark yield, and returns a unified JSON plan.
7. **Farmer Presentation & Persistence:** Flutter renders NPK targets, bag counts, split schedules, and weather warnings; farmer saves recommendation to SQLite and can download a ReportLab PDF.

---

## 2. API Route Inventory

| Router | Method | Path | Auth Required | Description |
|---|---|---|---|---|
| `phase3_soil` | POST | `/api/soil/upload` | Bearer / Farmer ID | Uploads soil health card PDF or image |
| `phase3_soil` | POST | `/api/soil/documents/{id}/ocr` | Bearer / Farmer ID | Runs OCR on uploaded document |
| `phase3_soil` | POST | `/api/soil/documents/{id}/validate` | Bearer / Farmer ID | Runs range and method validation checks |
| `phase3_soil` | POST | `/api/soil/documents/{id}/confirm` | Bearer / Farmer ID | Farmer confirms values; saves profile |
| `phase3_soil` | GET | `/api/soil/profiles` | Bearer / Farmer ID | Lists confirmed soil profiles |
| `agronomy` | POST | `/api/agronomy/select-rule` | None / Public | Matches crop, soil series to STCR/Blanket rules |
| `nutrient` | POST | `/api/nutrient/calculate-npk` | None / Public | Calculates N, P2O5, K2O requirements |
| `fertilizer` | GET | `/api/fertilizer/catalog` | None / Public | Returns commercial fertilizer catalog |
| `fertilizer` | POST | `/api/fertilizer/optimize` | None / Public | MILP whole-bag fertilizer optimization |
| `integration` | GET | `/api/weather/current` | None / Public | Real-time Open-Meteo weather |
| `integration` | GET | `/api/weather/guidance` | None / Public | Agronomic application timing guidance |
| `integration` | GET | `/api/location/reverse-geocode`| None / Public | BigDataCloud / Nominatim GPS lookup |
| `integration` | POST | `/api/full-recommendation` | None / Public | End-to-end master pipeline orchestrator |
| `extra_api` | POST | `/api/auth/register` | None / Public | Registers farmer account |
| `extra_api` | POST | `/api/auth/login` | None / Public | Authenticates and returns JWT token |
| `extra_api` | GET | `/api/auth/profile` | Bearer / Farmer ID | Returns profile (had mock fallback) |
| `extra_api` | PUT | `/api/auth/profile` | Bearer / Farmer ID | Updates farmer profile |
| `extra_api` | GET/POST| `/api/farmer/farm` | Bearer / Farmer ID | Gets or updates farm land details |
| `extra_api` | GET/POST| `/api/farmer/history` | Bearer / Farmer ID | Fertilizer application log |
| `extra_api` | GET | `/api/farmer/notifications` | Bearer / Farmer ID | User notifications list |
| `extra_api` | POST | `/api/yield/predict` | None / Public | XGBoost district benchmark yield prediction |
| `extra_api` | GET/POST| `/api/recommendations` | Bearer / Farmer ID | Lists or saves fertilizer recommendations |
| `extra_api` | GET | `/api/recommendations/{id}/pdf`| Bearer / Farmer ID | Generates downloadable ReportLab PDF |
| `main` | GET | `/api/db/status` | **NONE (VULNERABLE)**| Dumps SQLite table record counts |
| `main` | GET | `/db` | **NONE (VULNERABLE)**| Dumps full SQLite table contents in HTML |

---

## 3. Confirmed Defects and Severity Register

### [DEFECT-SEC-01] CRITICAL: Authentication Bypass via Non-JWT Token String
- **File:** `phase7_integration/extra_api.py` (lines 116–128)
- **Root Cause:** When the `Authorization: Bearer <token>` or `X-Farmer-Id` header does not contain two dots (i.e. is not a 3-part JWT), the code executes: `else: user_id = token`.
- **Impact:** Any client can pass an arbitrary string as a Bearer token or header and impersonate any user without cryptographic verification or password.
- **Reproduction:** Sending `GET /api/recommendations` with `Authorization: Bearer test_victim_farmer` allows full access to `test_victim_farmer`'s recommendations.

### [DEFECT-SEC-02] CRITICAL: Public Unauthenticated Database Viewer Exposing Credentials
- **File:** `phase3_soil/main.py` (lines 71–139)
- **Root Cause:** Endpoints `/db` and `/api/db/status` have no authentication or role-based access control. In addition, `/db?table=users` interpolates the query parameter directly into SQL (`SELECT * FROM {table} LIMIT 250`).
- **Impact:** Anyone on the network can view all user emails, phone numbers, and PBKDF2 password hashes.

### [DEFECT-ML-01] HIGH: Artificial $R^2 \approx 0.95$ Due to Cross-Crop Scale Disparity
- **Files:** `train_yield_model.py`, `models/yield_prediction/supplementary_metrics.json`
- **Root Cause:** Pooling crops with 100x scale variance (Sugarcane at ~100 t/ha vs Pulses at ~0.5 t/ha) inflates $R^2$ because crop identity explains 88.8% of variance.
- **Evidence:** A dummy baseline predicting only `(Crop, Season)` mean yield achieves $R^2 = 0.9389$. For Pulses, XGBoost achieves a **negative $R^2$ of $-0.143$**.
- **Impact:** Misleading claims that the ML model has high predictive accuracy when it actually fails on pulses and provides negligible gain over a table lookup.

### [DEFECT-AGRI-01] HIGH: Narrow STCR Scope & Missing Major TN Crops
- **File:** `data/agronomy/tnau_stcr_rules.json`
- **Root Cause:** True verified STCR-IPNS equations are present for only 3 crops (Rice, Cotton, Maize) on limited soil series. Sugarcane, Blackgram, and Groundnut rely on blanket RDF. Banana is pending verification. 30+ major TN crops have zero rules.
- **Impact:** Applying the system to unsupported crops or soil series risks recommending uncalibrated rates.

### [DEFECT-OPT-01] MEDIUM: Unbounded Nutrient Surplus in MILP Solver (`ub = np.inf`)
- **File:** `phase6_fertilizer/service.py` (lines 202–206)
- **Root Cause:** The linear constraint defines `ub = [np.inf] * len(lhs_bounds)`, meaning there is no upper ceiling to prevent massive oversupply of a nutrient when purchasing multi-nutrient products like DAP.
- **Impact:** Over-fertilization risks toxicity and soil degradation.

### [DEFECT-DB-01] MEDIUM: SQLite WAL Mode and Connection Pooling Missing
- **File:** `phase3_soil/db.py` (lines 121–134)
- **Root Cause:** `PRAGMA journal_mode = WAL` is never executed; `db.connect()` opens and closes raw SQLite connections without pooling or timeout handling.
- **Impact:** Concurrent write requests cause `sqlite3.OperationalError: database is locked` on Windows.

### [DEFECT-ASYNC-01] MEDIUM: Synchronous Blocking HTTP I/O in Async Handlers
- **Files:** `phase7_integration/weather.py`, `phase7_integration/location.py`
- **Root Cause:** Uses blocking `urllib.request.urlopen()` with 5–8 second timeouts.
- **Impact:** Thread starvation in FastAPI under multiple concurrent requests.

### [DEFECT-FLUTTER-01] HIGH: Volatile In-Memory Auth Session (Lost on App Restart)
- **Files:** `flutter_app/lib/services/api_client.dart`, `pubspec.yaml`
- **Root Cause:** No persistent secure storage (`flutter_secure_storage` or `shared_preferences`). Auth tokens and farmer IDs are stored only in volatile static memory variables.
- **Impact:** Every app launch forces the user back to the login screen.

### [DEFECT-FLUTTER-02] MEDIUM: Mocked "Forgot Password" Action
- **File:** `flutter_app/lib/screens/login_screen.dart` (lines 91–99)
- **Root Cause:** Pressing submit on the dialog only shows a local SnackBar without any backend call.

### [DEFECT-PDF-01] MEDIUM: ReportLab Indic Script Font Failure
- **File:** `phase7_integration/extra_api.py` (lines 582–608)
- **Root Cause:** ReportLab uses built-in Helvetica font which lacks glyphs for Tamil / Indic Unicode characters.
- **Impact:** Rendering Tamil names, villages, or crop titles crashes or renders as black blocks.
