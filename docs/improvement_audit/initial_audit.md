# Initial Codebase and Architecture Audit
**Application Name:** AgroWise AI  
**Project Reference:** SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield  
**Audit Date:** October 2026  
**Auditor:** Senior Agricultural Software Architect & Lead Security/Systems Engineer  

---

## 1. Executive Summary & Repository Structure

AgroWise AI is a complete, full-stack agricultural decision support platform designed specifically for Tamil Nadu farmers. The codebase combines a Python 3.12 / FastAPI asynchronous backend with a Flutter 3.x trilingual mobile/web client, integrating official Tamil Nadu Agricultural University (TNAU) Soil Test Crop Response (STCR) models, Mixed-Integer Linear Programming (MILP) fertilizer optimization, regional XGBoost yield prediction, and Open-Meteo agro-weather advisories.

### Discovered Repository Layout
```
TN_Yield_Model_Phase3_Combined/
├── agronomy/                    # Phase 4: Agronomic rule selection & registry service
├── data/
│   ├── agronomy/                # tnau_stcr_rules.json, source_registry.csv
│   └── tn_district_yield_...csv # Cleaned historical crop yield and rainfall datasets
├── docs/                        # Architecture, dataset, and phase audit reports
│   └── improvement_audit/       # Deep improvement audit deliverables
├── flutter_app/                 # Cross-platform Flutter frontend (28 screens, en/ta/hi)
│   ├── lib/
│   │   ├── l10n/                # Localization JSON dictionaries (English, Tamil, Hindi)
│   │   ├── screens/             # 28 dedicated mobile screens
│   │   ├── services/            # API client and networking
│   │   └── widgets/             # Specialized UI widgets and cards
│   └── test/                    # Widget and screen flow automated tests
├── models/
│   └── yield_prediction/        # yield_model.joblib, metadata.json, metrics.json
├── phase3_soil/                 # Phase 3: Soil card OCR, extraction, validation & SQLite DB
├── phase5_nutrient/             # Phase 5: Stoichiometric NPK requirement calculation
├── phase6_fertilizer/           # Phase 6: SciPy MILP whole-bag fertilizer optimizer & catalog
├── phase7_integration/          # Phase 7: Weather guidance, JWT auth, and master pipeline
├── scripts/                     # Packaging and economic evaluation scripts
└── tests/                       # Pytest automated test suites
```

---

## 2. Component-by-Component Baseline Audit

| Component | Technology | Entry Point / File | Discovered Baseline Status | Audit Findings & Gaps Identified |
| :--- | :--- | :--- | :--- | :--- |
| **Backend Gateway** | FastAPI / Uvicorn | `phase3_soil/main.py:app` | Fully operational (100% test pass) | Endpoints cleanly separated into modular APIRouters. CORS enabled for development. |
| **Agronomic Rules** | Python / Pydantic | `agronomy/service.py` | Operational with strict precedence | 7 verified rules, 1 pending validation (Groundnut), 1 pending verification (Banana), 1 deprecated (Old Rice). Unverified rules blocked by default. |
| **NPK Calculations** | Python / NumPy | `phase5_nutrient/service.py` | Deterministic STCR calculations | Handled elemental vs oxide stoichiometric conversions ($P \rightarrow P_2O_5 \times 2.291$, $K \rightarrow K_2O \times 1.205$). Needed explicit logging of clamping when calculated nutrients are negative. |
| **Fertilizer Optimizer**| SciPy MILP / HiGHS | `phase6_fertilizer/service.py`| Discrete commercial bag solver | Solves integer bag counts (45kg Urea, 50kg DAP, MOP, SSP, Complexes). Revalidates $A \cdot x \ge b$. Coupled nutrients (DAP, NPK complex) correctly accounted for. |
| **Yield Regressor** | XGBoost / Scikit-learn| `predict_yield.py` | 9-feature model artifact | Trained on 8,694 historical TN district records (SCR 2020-21 to 2024-25). Production excluded from features, zero target leakage. |
| **Agro-Weather** | Open-Meteo REST API | `phase7_integration/weather.py`| Live observation & 7-day forecast | SQLite cache with 30-min TTL. Fallback to stale cache or offline state. Needed configurable rain threshold and explicit forecast uncertainty disclaimer. |
| **Database & Security**| SQLite / PBKDF2 / JWT | `phase3_soil/db.py`, `extra_api.py`| 10 relational tables | Object-level authorization enforced (`WHERE user_id = ?`). SHA-256 deduplication for uploaded documents. PBKDF2 password hashing. |
| **PDF Reporting** | ReportLab | `extra_api.py:download_pdf` | Server-side PDF generation | Tamper-proof, bilingual layout reflecting actual database recommendation records. |
| **Mobile Frontend** | Flutter 3.32 / Dart | `flutter_app/lib/main.dart` | 28 dynamic screens | Trilingual (Tamil, English, Hindi). Dynamic API URL configuration in Settings. Zero hardcoded results in production flows. |

---

## 3. Discovered Defects and Remediations

1. **Negative STCR Dosing Transparency:**
   - *Defect:* When soil test nutrient status or FYM contribution exceeded the uptake requirement for a modest target yield, STCR formulas yielded negative numbers. While mathematical `max(0.0, raw)` prevented negative doses, the clamping was not explicitly documented in the returned calculation payload.
   - *Fix:* Enhanced `phase5_nutrient/service.py` to record `raw_calculated_rates_kg_per_ha` and append explicit scientific explanations to `clamping_notes` and `warnings`.
2. **Rainfall Advisory Configurable Threshold:**
   - *Defect:* Weather guidance previously hard-coded a 10.0 mm rainfall caution threshold without allowing project-level configuration or stating meteorological uncertainty.
   - *Fix:* Added `DEFAULT_RAIN_THRESHOLD_MM = float(os.environ.get("FERTILIZER_RAIN_THRESHOLD_MM", "5.0"))`, exposed `rain_threshold_mm` in API endpoints, and included an explicit forecast uncertainty disclaimer.
3. **Empirical Economic Validation:**
   - *Defect:* Previous documentation referenced standard literature savings (15–30%) without a reproducible test suite comparing real farmer baselines.
   - *Fix:* Created `scripts/evaluate_economic_benefits.py` and `tests/test_economic_benefit_audit.py`, measuring exact baseline costs, optimized whole-bag costs, and rupee/percentage savings across Rice, Maize, and Cotton.

---

## 4. Baseline Test Results Summary

Prior to making modifications, the existing test suites were executed to verify regression integrity:
* **Python Backend Pytest Suite:** 125 tests passed in 35.36s (100% pass rate).
* **Flutter Static Analysis:** `flutter analyze` completed with 0 errors, 0 warnings, 0 lints.
* **Flutter Widget & Screen Tests:** 20 tests passed in 4.0s (100% pass rate).
