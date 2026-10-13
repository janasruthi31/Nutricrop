# Comprehensive Master Project Audit Report

**Project Title:** AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Audit Date:** 2026-10-13  
**Auditor:** Senior Full-Stack Agronomic Software Engineer & Release Lead  

---

## 1. Executive Summary

A comprehensive architectural and source code audit was conducted on the entire codebase spanning Flutter mobile frontend, FastAPI backend, machine learning models, agronomic calculation engines, SQLite persistence, and test suites.

### Key Audit Findings:
1. **Core Architecture Exists and Runs:** The repository contains complete functional implementations for all eight phases, including the Flutter frontend (28 screen components), FastAPI backend with SQLite persistence, XGBoost district yield prediction, TNAU STCR-IPNS rule registry, and linear programming fertilizer optimizer.
2. **Current Test Status:**
   - **Backend pytest:** 79 tests collected, 79 passed, 5 warnings (ran in 63.5s).
   - **Flutter analyze:** 0 issues found (ran in 54.5s).
   - **Flutter test:** 15 tests collected, 15 passed (ran in 3.4s).
3. **Confirmed Bugs Identified:**
   - **NPK Schema Field Disconnect:** `phase5_nutrient` outputs `n_req_kg_per_ha` and `total_n_req_kg`, while the Flutter frontend screens (`npk_requirement_screen.dart`, `recommendation_details_screen.dart`) and PDF generation (`extra_api.py`) searched for `net_n_kg_per_ha` and `total_farm_n_kg`, causing 0.0 values in UI and PDFs.
   - **Fertilizer Product Name Key Disconnect:** `phase6_fertilizer` outputs `product_name`, but the frontend and PDF generation searched for `name`, causing fertilizer product titles to fall back to generic "Fertilizer" or "Product".
   - **Agro-Weather API Key Disconnect:** `phase7_integration/weather.py` returned `condition`, `guidance_status`, and `advisory_en`, while `weather_screen.dart` looked for `current_condition`, `risk_level`, and `actionable_advice`, falling back to hardcoded demo defaults.
   - **Authentication Token Extraction in Soil Module:** `phase3_soil/api.py` required `X-Farmer-Id` header and did not extract user credentials from standard `Authorization: Bearer <token>` headers used elsewhere in the application.
   - **Missing Prompt-Specified Localized Error Messages:** Translations for the 7 mandatory domain-specific failure messages (upload failure, OCR failure, missing values, unsupported crop, optimization failure, weather failure, yield failure) were missing in `app_localizations.dart`.
   - **Missing Forgot Password Feature:** Forgot Password recovery was not exposed on `login_screen.dart`.
   - **Optimization Integer Bag Re-Validation:** Linear programming optimizer in `phase6_fertilizer/service.py` performed ceiling-rounding on continuous quantities without explicitly validating and documenting nutrient satisfaction post-rounding.

---

## 2. Existing Project Structure

```
TN_Yield_Model_Phase3_Combined/
├── agronomy/                    # Phase 4 Agronomic Rule Registry & Service
│   ├── api.py                   # Rule selection router (/api/agronomy/select-rule)
│   ├── models.py                # Pydantic schemas for rule requests & responses
│   ├── registry.py              # Loads TNAU STCR rules and CSV sources
│   ├── service.py               # Deterministic crop, soil series, season matching
│   └── tests/                   # 12 Pytest tests for rule selection
├── data/
│   ├── agronomy/
│   │   ├── source_registry.csv  # 15 Official TNAU agronomic references
│   │   └── tnau_stcr_rules.json # 9 TNAU rules (7 verified, 1 pending, 1 deprecated)
│   ├── extraction_qa.json       # OCR golden validation QA fixtures
│   ├── tn_district_yield_model_dataset.csv     # 8,694 cleaned crop-yield records
│   └── tn_district_yield_rainfall_raw_long.csv # Raw Season & Crop Reports (2020-25)
├── docs/                        # Architectural documentation and phase reports
├── flutter_app/                 # Complete Flutter Mobile Application
│   ├── lib/
│   │   ├── config.dart          # Environment configuration (API host, timeouts)
│   │   ├── main.dart            # Flutter entry point with dynamic locale notifier
│   │   ├── l10n/
│   │   │   └── app_localizations.dart # 3-language localized strings (en, ta, hi)
│   │   ├── models/
│   │   │   └── soil_field.dart  # Soil parameter metadata, bounds, and ranges
│   │   ├── screens/             # 28 Mobile UI screens
│   │   ├── services/
│   │   │   ├── api_client.dart  # Master HTTP client (auth, yield, farmer, recs)
│   │   │   └── soil_api.dart    # Soil report upload & validation client
│   │   ├── theme/
│   │   │   └── app_theme.dart   # Farmer-friendly green agricultural light theme
│   │   └── widgets/
│   │       └── common_widgets.dart # Reusable UI components
│   └── test/                    # 15 Flutter widget & unit tests
├── models/
│   └── yield_prediction/        # Phase 2 ML Model Artifacts
│       ├── metadata.json        # Features, categories, ranges, target units (kg/ha)
│       ├── metrics.json         # R² (0.9508), MAE (1,706 kg/ha), RMSE (3,945 kg/ha)
│       ├── supplementary_metrics.json
│       ├── test_predictions.csv
│       ├── training_log.json
│       └── yield_model.joblib   # Serialized XGBoost regression pipeline
├── phase3_soil/                 # Phase 3 Soil Health Card OCR & Validation
│   ├── api.py                   # /api/soil (upload, ocr, validate, confirm, profile)
│   ├── classification.py        # TNAU Low/Medium/High soil ratings
│   ├── config.py                # Storage paths, size limits (10 MB), API keys
│   ├── crops.py                 # Crop aliases and normalization
│   ├── db.py                    # SQLite schema and thread-safe connection pooling
│   ├── extraction.py            # Regex & positional OCR extraction & redaction
│   ├── main.py                  # Master FastAPI Application factory
│   ├── ocr.py                   # Tesseract & PyPDF text extraction
│   ├── service.py               # Document hashing, upload, verification workflow
│   ├── tnau_reference.py        # Valid range limits and measurement methods
│   ├── units.py                 # Conversion (kg/ha, ppm, %, dS/m)
│   ├── validation.py            # Primary nutrient validation & blocker rules
│   └── tests/                   # 33 Pytest tests for soil processing
├── phase5_nutrient/             # Phase 5 NPK Requirement Calculation Engine
│   ├── api.py                   # /api/nutrient/calculate-npk
│   ├── models.py                # Nutrient calculation schemas
│   ├── service.py               # STCR-IPNS linear equations & blanket adjustments
│   ├── units.py                 # Area conversions (hectare, acre, cent, sq.m)
│   └── tests/                   # 14 Pytest tests for NPK calculations
├── phase6_fertilizer/           # Phase 6 Fertilizer Cost & Bag LP Optimizer
│   ├── api.py                   # /api/fertilizer/optimize & /catalog
│   ├── catalog.py               # Commercial fertilizers (Urea, DAP, MOP, SSP, NPK)
│   ├── models.py                # Fertilizer optimization schemas & schedules
│   ├── service.py               # scipy.optimize.linprog HiGHS solver
│   └── tests/                   # 6 Pytest tests for fertilizer optimization
├── phase7_integration/          # Phase 7 Weather Guidance & Master Orchestrator
│   ├── api.py                   # /api/full-recommendation & /api/weather/guidance
│   ├── extra_api.py             # Auth, profile, farm, history, PDF generation
│   ├── service.py               # Master end-to-end pipeline orchestrator
│   ├── weather.py               # Agro-weather advisory rules by TN district
│   └── tests/                   # 7 Pytest integration tests
├── predict_yield.py             # CLI & python import for yield predictions
├── train_yield_model.py         # XGBoost training & cross-validation script
└── tests/                       # Root tests for datasets and model integrity
```

---

## 3. Implemented Features by Phase

| Phase | Description | Implementation Status | Verified Evidence |
|---|---|---|---|
| **Phase 1: Dataset Preparation** | TN Season & Crop Reports (2020-25) Table V-A & I-A | **Implemented** | 8,694 valid rows, zero duplicates, verified chronological train/test split. |
| **Phase 2: District Yield Prediction** | XGBoost regression predicting district benchmark in kg/ha | **Implemented** | R² = 0.9508, RMSE = 3,945 kg/ha, metadata ranges verified, independent of fertilizer NPK. |
| **Phase 3: Soil OCR & Validation** | PDF/Image upload, OCR extraction, farmer review & confirm | **Implemented** | SHA-256 document deduplication, PII redaction, field status tracking, Olsen vs Bray method separation. |
| **Phase 4: Agronomic Rule Selection** | TNAU STCR-IPNS rule registry and soil series matching | **Implemented** | 7 verified rules, 1 pending (Banana), 1 deprecated; crops: Rice, Cotton, Maize, Blackgram, Groundnut, Sugarcane. |
| **Phase 5: NPK Calculation** | Deterministic targeted yield equations & blanket adjustments | **Implemented** | STCR equations ($FN = aT - bSN - cFYM$), unit conversions, farm-area scaling. |
| **Phase 6: Fertilizer Optimization** | Linear programming cost minimization (SciPy HiGHS) | **Implemented** | Non-negative bounds, whole-bag ceiling rounding, split application schedule generation. |
| **Phase 7: Backend & Integration** | Master pipeline orchestration, agro-weather advisories | **Implemented** | End-to-end chaining of Phases 4→5→6→2→7, weather failure non-blocking fallback. |
| **Phase 8: Testing & Deployment** | Automated testing, ReportLab PDF generation, SQLite DB | **Implemented** | 79 pytest tests passed, 15 flutter tests passed, downloadable PDF report with tables. |

---

## 4. Confirmed Bugs (Must Fix)

### Bug 1: NPK Requirement Schema Key Mismatch
- **Location:** `flutter_app/lib/screens/npk_requirement_screen.dart` (lines 138-143), `flutter_app/lib/screens/recommendation_details_screen.dart` (lines 102, 110, 118), and `phase7_integration/extra_api.py` (lines 481-483).
- **Description:** Phase 5 returns `n_req_kg_per_ha`, `p2o5_req_kg_per_ha`, `k2o_req_kg_per_ha`, `total_n_req_kg`, `total_p2o5_req_kg`, and `total_k2o_req_kg`. The frontend screens and PDF generator queried `net_n_kg_per_ha`, `net_p2o5_kg_per_ha`, `net_k2o_kg_per_ha`, `total_farm_n_kg`, `total_farm_p2o5_kg`, and `total_farm_k2o_kg`.
- **Symptom:** UI displays 0.0 kg/ha and 0.0 kg farm totals; PDF prints 0.0 kg for all nutrients.
- **Severity:** High (Functional bug).

### Bug 2: Fertilizer Product Name Key Mismatch
- **Location:** `flutter_app/lib/screens/final_recommendation_screen.dart` (line 130), `flutter_app/lib/screens/recommendation_details_screen.dart` (line 129), and `phase7_integration/extra_api.py` (line 504).
- **Description:** `phase6_fertilizer/models.py` defines `product_name`. The Flutter screens and PDF generator evaluated `prod['name']`.
- **Symptom:** Recommended products rendered as fallback "Fertilizer" in UI and "Product" in PDF.
- **Severity:** Medium (Display bug).

### Bug 3: Weather Guidance Field Disconnect
- **Location:** `phase7_integration/weather.py` vs `flutter_app/lib/screens/weather_screen.dart` (lines 54-59).
- **Description:** `weather.py` provides `condition`, `guidance_status`, `advisory_en`, `temp_max_c`, while `weather_screen.dart` looked for `current_condition`, `risk_level`, `actionable_advice`, `temperature_c`.
- **Symptom:** Weather advisory on screen fell back to hardcoded default values.
- **Severity:** Medium (Integration bug).

### Bug 4: Soil Endpoint Authorization Header Handling
- **Location:** `phase3_soil/api.py` (`_guard`).
- **Description:** Only looked for `X-Farmer-Id` header, rejecting standard `Authorization: Bearer <token>` requests if `X-Farmer-Id` was absent.
- **Severity:** Low (Compatibility limitation).

### Bug 5: Missing Localized Domain Failure Messages
- **Location:** `flutter_app/lib/l10n/app_localizations.dart`.
- **Description:** Phase 6 of user specification requires 7 standardized failure messages translated in English, Tamil, and Hindi. These keys were missing from the localization bundle.
- **Severity:** Low (Compliance issue).

### Bug 6: Optimization Whole-Bag Nutrient Satisfaction Revalidation
- **Location:** `phase6_fertilizer/service.py` (lines 155-180).
- **Description:** Nutrient supply was reported based solely on the continuous solution $x^*$, without explicit assertion that the ceiling-rounded whole-bag quantities satisfy $A_{ub} x_{rounded} \ge b_{ub}$.
- **Severity:** Medium (Agronomic rigor).

---

## 5. Potential Risks & Observations

1. **SQLite Concurrency in Multi-User Environments:** SQLite file database is ideal for local development, demonstration, and edge deployments. For multi-tenant production deployments with high concurrent writes, PostgreSQL is recommended.
2. **PyPDF / Tesseract Native Dependencies:** When executing OCR on scanned images, system Tesseract OCR binaries must be installed in PATH. The service gracefully handles unreadable documents by routing farmers to the manual entry screen.
3. **ReportLab Dependency:** PDF generation relies on ReportLab, which is confirmed installed in the environment.

---

## 6. Current Test Execution Results

- **Backend Pytest Suite:**
  - Command: `pytest`
  - Total Tests: 79
  - Passed: 79
  - Failed: 0
  - Warnings: 5 (Deprecation warnings for asyncio loop scope and swig bindings)
- **Flutter Analyzer:**
  - Command: `flutter analyze`
  - Result: No issues found! (0 errors, 0 warnings, 0 hints)
- **Flutter Widget/Unit Tests:**
  - Command: `flutter test`
  - Total Tests: 15
  - Passed: 15
  - Failed: 0

---

## 7. Action Plan & Recommended Fixes

1. **Fix Schema Disconnects:**
   - Update `phase5_nutrient/models.py` and `phase5_nutrient/service.py` to ensure both `n_req_kg_per_ha` and `net_n_kg_per_ha`, `total_n_req_kg` and `total_farm_n_kg`, `selected_method` and `calculation_method` are populated in responses.
   - Update `phase6_fertilizer/models.py` and `service.py` to include `name` alongside `product_name`.
   - Update Dart screens (`npk_requirement_screen.dart`, `final_recommendation_screen.dart`, `recommendation_details_screen.dart`) to robustly look up both key variants.
2. **Align Weather Schema:**
   - Update `phase7_integration/weather.py` to supply both schema sets (`guidance_status` + `risk_level`, `condition` + `current_condition`, `advisory_en` + `actionable_advice`).
   - Update `weather_screen.dart` to support both and display localized Tamil/Hindi advisories.
3. **Enhance Auth Compatibility:**
   - Update `phase3_soil/api.py` `_guard` to accept `Authorization: Bearer <token>` in addition to `X-Farmer-Id`.
4. **Complete Localization & Forgot Password:**
   - Add the 7 prompt-specified failure messages in English, Tamil, and Hindi in `app_localizations.dart`.
   - Add Forgot Password feature / dialog on `login_screen.dart`.
5. **Revalidate Optimization Bag Discretization:**
   - Calculate both continuous and bag-rounded nutrient supply in `phase6_fertilizer/service.py`, verifying constraints $A_{ub} x \ge b_{ub}$.
6. **Retest and Validate:**
   - Run pytest and flutter test suites to ensure 100% pass rate.
   - Run comprehensive end-to-end integration verification.
7. **Package Delivery ZIP:**
   - Create clean distribution ZIP `AI_Soil_Specific_Fertilizer_Optimizer_Final.zip` excluding build artifacts and secrets.
