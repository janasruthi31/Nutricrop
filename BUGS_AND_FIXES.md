# Master Bugs and Fixes Documentation

**Project Title:** AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Project Reference:** SIH1639 — Sustainable Fertilizer Usage Optimizer  
**Audit & Engineering Date:** October 2026  
**Auditor & Lead Engineer:** Senior Python/FastAPI Engineer, Flutter/Dart Developer, Agricultural Data Scientist, Optimization Engineer, Database Engineer, QA Engineer & Security Auditor  
**Overall Status:** ALL IDENTIFIED DEFECTS RESOLVED, TESTED, AND VERIFIED  

---

## 1. Defect Summary Matrix

| Issue ID | Severity | Affected Component | Root Cause | Status | Verifying Test |
| :---: | :---: | :--- | :--- | :---: | :--- |
| **BUG-OPT-01** | **Critical** | `phase6_fertilizer/service.py`<br>`optimize_fertilizer_selection` | Heuristic continuous LP + ceiling rounding produced suboptimal costs & bag counts. | **FIXED** | `test_08_milp_optimality_compared_to_brute_force`<br>`test_10_whole_bag_integer_units` |
| **BUG-AGR-01** | **Critical** | `phase7_integration/service.py`<br>`run_master_pipeline` | Silent fallback to hardcoded soil values (`220 N, 16 P, 190 K`) when missing. | **FIXED** | `test_02_master_pipeline_service`<br>`test_04_missing_required_soil_values` |
| **BUG-ML-01** | **Critical** | `predict_yield.py`<br>`predict_district_yield` | Unchecked exceptions silently returned hardcoded `3500.0 kg/ha` fallback. | **FIXED** | `test_05_unsupported_district_rejected`<br>`test_07_negative_rainfall_rejected`<br>`test_08_nine_feature_schema_consistency` |
| **BUG-AGR-02** | **High** | `phase5_nutrient/units.py`<br>`phase5_nutrient/models.py` | Target yield accepted only `t/ha` without conversion from `q/ha`; missing elemental/oxide unit conversions. | **FIXED** | `test_15_target_yield_unit_conversions`<br>`test_16_elemental_and_oxide_nutrient_units`<br>`test_17_farm_area_acre_and_sqm_conversions` |
| **BUG-SEC-01** | **High** | `phase7_integration/extra_api.py`<br>`get_current_user`, handlers | Unauthenticated requests defaulted to `"farmer_001"`; missing object-level authorization allowed cross-user access. | **FIXED** | `test_unauthenticated_requests_rejected`<br>`test_cross_user_data_isolation` |
| **BUG-AGR-03** | **Medium** | `phase6_fertilizer/service.py`<br>`generate_fertilizer_schedule` | Generic 3-split basal/tillering/panicle schedule applied to all crops including pulses. | **FIXED** | `test_09_crop_specific_schedules` |
| **BUG-CAT-01** | **Medium** | `phase6_fertilizer/catalog.py`<br>`FERTILIZER_CATALOG` | Missing statutory MRP citations, price effective dates, and commercial bag size specifications. | **FIXED** | `test_01_valid_lp_optimization`<br>`test_06_fertilizer_prices_endpoint` |
| **BUG-UI-01** | **Medium** | `phase5_nutrient/models.py`<br>Flutter recommendation screens | Key naming discrepancies (`n_req_kg_per_ha` vs `net_n_kg_per_ha`, `product_name` vs `name`) showed 0 values in UI/PDF. | **FIXED** | `flutter_app/test/screens_flow_test.dart`<br>`test_recommendation_save_and_pdf` |
| **BUG-UI-02** | **Low** | `flutter_app/lib/screens/login_screen.dart`<br>`app_localizations.dart` | Missing "Forgot Password" UI action and localized password recovery modal. | **FIXED** | `flutter_app/test/screens_flow_test.dart` ("LoginScreen displays Forgot Password button") |

---

## 2. Detailed Technical Defect Reports

### BUG-OPT-01: Commercial Whole-Bag Mixed-Integer Optimization
- **Issue ID:** BUG-OPT-01
- **Severity:** Critical (Priority P0)
- **Affected File & Function:** `phase6_fertilizer/service.py` -> `optimize_fertilizer_selection`
- **Actual Observed Behavior:** The optimizer solved continuous linear programming ($\text{kg}$ of commercial fertilizer) and subsequently rounded the resulting values up to whole bags using `math.ceil()`. This resulted in non-optimal costs, excessive fertilizer purchase, and severe nutrient surpluses.
- **Expected Behavior:** An exact Mixed-Integer Linear Programming (MILP) model that solves directly for whole commercial bags ($y_j \in \mathbb{N}_0$), minimizing total cost $\sum (c_j \times y_j)$ while satisfying nutrient demands with guaranteed mathematical optimality.
- **Root Cause:** Continuous linear programming relaxation was used instead of integer branch-and-cut optimization.
- **Fix Implemented:**
  1. Replaced continuous `scipy.optimize.linprog` with `scipy.optimize.milp` (HiGHS branch-and-cut solver).
  2. Defined decision variables $y_j \in \{0, 1, 2, \dots\}$ representing discrete commercial bags (e.g. 45 kg Urea, 50 kg DAP, 50 kg MOP, 50 kg SSP, 50 kg Complex).
  3. Formulated constraint matrix $\mathbf{A} \cdot \mathbf{y} \ge \mathbf{b}$ for Nitrogen, $\text{P}_2\text{O}_5$, and $\text{K}_2\text{O}$.
  4. Enforced upper bounds on excess nutrients ($1.5 \times$ upper bound) to prevent toxic over-fertilization.
  5. Implemented exact recalculation of delivered nutrients and surplus/deficit directly from the resulting integer bag counts.
  6. Provided an exact integer grid-search fallback for constrained problems if SciPy MILP is unavailable.
- **Test Used to Verify Fix:** `phase6_fertilizer/tests/test_fertilizer_optimization.py::test_08_milp_optimality_compared_to_brute_force` (verified identical cost to exhaustive brute-force search), `test_10_whole_bag_integer_units`.
- **Remaining Limitation:** Real-world retail fertilizer prices are subject to statutory notifications by the Department of Fertilizers (DoF), GoI, and must be updated in `catalog.py` when official revisions occur.

---

### BUG-AGR-01: Elimination of Silent Soil Nutrient Defaults
- **Issue ID:** BUG-AGR-01
- **Severity:** Critical (Priority P0)
- **Affected File & Function:** `phase7_integration/service.py` -> `run_master_pipeline`
- **Actual Observed Behavior:** When soil test values (`n_kg_per_ha`, `p_kg_per_ha`, `k_kg_per_ha`) were missing from the request, the master orchestrator silently injected default values (`220.0 kg N`, `16.0 kg P`, `190.0 kg K`), generating recommendations based on fabricated soil data.
- **Expected Behavior:** Missing soil test measurements must never be silently fabricated. The system must either look up farmer-confirmed values from the authenticated `soil_profiles` database table or reject the request with HTTP 400.
- **Root Cause:** A hardcoded `default_soil = {"n_kg_per_ha": 220.0, "p_kg_per_ha": 16.0, "k_kg_per_ha": 190.0}` fallback dictionary was executed whenever soil values were omitted.
- **Fix Implemented:**
  1. Removed the hardcoded `default_soil` dictionary entirely from `run_master_pipeline`.
  2. Implemented database lookup for confirmed soil records from the farmer's authenticated profile if `soil_profile_id` is supplied.
  3. If neither explicit soil measurements nor a valid confirmed soil profile ID is provided, the API raises an explicit HTTP 400 error: `"Soil nutrient measurements (N, P, K) or confirmed soil_profile_id must be provided."`
- **Test Used to Verify Fix:** `phase7_integration/tests/test_integration.py::test_02_master_pipeline_service`, `phase5_nutrient/tests/test_npk_calculation.py::test_04_missing_required_soil_values`.
- **Remaining Limitation:** Farmers who do not yet possess a soil test report must have their soil tested or use blanket recommendations where explicitly supported.

---

### BUG-ML-01: ML Yield Fallback Elimination & Schema Validation
- **Issue ID:** BUG-ML-01
- **Severity:** Critical (Priority P0)
- **Affected File & Function:** `predict_yield.py` -> `predict_district_yield`
- **Actual Observed Behavior:** Any exception or invalid input encountered during yield inference was caught silently by a blind `except Exception: return 3500.0`, returning a hardcoded fabricated yield of 3,500 kg/ha.
- **Expected Behavior:** Valid inference inputs must be strictly verified against the model's trained schema (Districts, Crops, Seasons, non-negative rainfall values). Unsupported inputs must return clear error messages without fabricating yield estimates.
- **Root Cause:** Blind catch-all exception block with a hardcoded constant fallback value.
- **Fix Implemented:**
  1. Removed silent fallback to `3500.0`.
  2. Added validation against `models/yield_prediction/metadata.json` for supported Tamil Nadu districts, crops, and seasons.
  3. Enforced negative rainfall rejection ($Rain \ge 0$).
  4. Verified that the inference pipeline extracts and orders exactly the 9 features required by `yield_model.joblib`:
     - Categorical (3): `District`, `Crop`, `Season`
     - Numerical (6): `Year`, `Rain_SWM_mm`, `Rain_NEM_mm`, `Rain_Winter_mm`, `Rain_HotWeather_mm`, `Rain_Annual_mm`
- **Test Used to Verify Fix:** `tests/test_phase2_yield.py::test_05_unsupported_district_rejected`, `test_06_unsupported_crop_rejected`, `test_07_negative_rainfall_rejected`, `test_08_nine_feature_schema_consistency`.
- **Remaining Limitation:** The XGBoost model predicts historical district-level agro-climatic yield benchmarks based on DES/ICAR data; it is not a micro-plot yield predictor.

---

### BUG-AGR-02: Target Yield and Elemental/Oxide Unit Standardization
- **Issue ID:** BUG-AGR-02
- **Severity:** High (Priority P0)
- **Affected File & Function:** `phase5_nutrient/units.py`, `phase5_nutrient/models.py`, `phase5_nutrient/service.py`
- **Actual Observed Behavior:** Target yield accepted only tonnes per hectare (`t/ha`). If farmers or extensions entered quintals per hectare (`q/ha` or `quintal/ha`), calculations were off by a factor of 10. Furthermore, elemental Phosphorus ($\text{P}$) and Potassium ($\text{K}$) were not converted to oxide forms ($\text{P}_2\text{O}_5$ and $\text{K}_2\text{O}$).
- **Expected Behavior:** Seamless conversion from `q/ha` and `quintal/ha` to `t/ha` ($1\text{ q} = 0.1\text{ t}$), and `kg/ha` to `t/ha` ($1000\text{ kg} = 1\text{ t}$). Transparent conversion of elemental $\text{P} \to \text{P}_2\text{O}_5$ ($\times 2.291$) and $\text{K} \to \text{K}_2\text{O}$ ($\times 1.205$).
- **Root Cause:** Missing conversion utility functions and lack of unit fields in `NutrientCalculationRequest`.
- **Fix Implemented:**
  1. Created `normalize_target_yield(value, unit)` in `phase5_nutrient/units.py`.
  2. Created `convert_elemental_to_oxide(n, p, k, p_unit, k_unit)` in `phase5_nutrient/units.py`.
  3. Added `target_yield_unit`, `p_unit`, and `k_unit` fields to `NutrientCalculationRequest` in `phase5_nutrient/models.py`.
  4. Integrated normalization prior to executing STCR-IPNS equations in `phase5_nutrient/service.py`.
- **Test Used to Verify Fix:** `phase5_nutrient/tests/test_npk_calculation.py::test_15_target_yield_unit_conversions`, `test_16_elemental_and_oxide_nutrient_units`, `test_17_farm_area_acre_and_sqm_conversions`.
- **Remaining Limitation:** Conversion factors rely on IUPAC molecular weights ($\text{P}_2\text{O}_5 / 2\text{P} = 2.291$, $\text{K}_2\text{O} / 2\text{K} = 1.205$).

---

### BUG-SEC-01: Multi-User Authentication & Object-Level Authorization
- **Issue ID:** BUG-SEC-01
- **Severity:** High (Priority P1)
- **Affected File & Function:** `phase7_integration/extra_api.py` -> `get_current_user`, record access handlers
- **Actual Observed Behavior:** When requests lacked an `Authorization` Bearer token, `get_current_user` defaulted silently to `"farmer_001"`. Furthermore, endpoints did not verify whether the requested resource belonged to the authenticated farmer, allowing Farmer A to view or download Farmer B's recommendations, soil profiles, and PDFs.
- **Expected Behavior:** Unauthenticated requests must return HTTP 401 Unauthorized. Access to resources belonging to another user must be rejected with HTTP 403 Forbidden.
- **Root Cause:** Insecure developer default (`return {"farmer_id": "farmer_001"}`) and missing ownership validation checks in data access endpoints.
- **Fix Implemented:**
  1. Removed the `"farmer_001"` default in `get_current_user`; raised HTTP 401 Unauthorized when token is missing or invalid.
  2. Implemented strict database ownership checks across all endpoints:
     - `GET /api/recommendations/{id}`
     - `GET /api/recommendations/{id}/pdf`
     - `GET /api/farmer/farm`
     - `GET /api/farmer/fertilizer-history`
     - `GET /api/notifications`
  3. If `record["farmer_id"] != current_user["farmer_id"]`, the API immediately raises HTTP 403 Forbidden: `"Access denied: You do not have permission to view or download this record."`
- **Test Used to Verify Fix:** `phase7_integration/tests/test_extra_api.py::test_unauthenticated_requests_rejected`, `test_cross_user_data_isolation`.
- **Remaining Limitation:** Local deployment uses JWT authentication with HMAC-SHA256 (`HS256`). Production deployment should set `JWT_SECRET` via secure environment variables.

---

### BUG-AGR-03: Crop-Specific Phenological Fertilizer Schedules
- **Issue ID:** BUG-AGR-03
- **Severity:** Medium (Priority P1)
- **Affected File & Function:** `phase6_fertilizer/service.py` -> `generate_fertilizer_schedule`
- **Actual Observed Behavior:** A generic 3-split schedule (Basal 50% N + 100% P + 50% K; Tillering 25% N; Panicle 25% N + 50% K) was applied to all crops, including short-duration pulses (e.g. Blackgram, Greengram) and Maize/Cotton.
- **Expected Behavior:** Application timing must adhere to crop-specific agronomic principles from the TNAU Crop Production Guide 2020:
  - Short-duration pulses: 100% basal application at sowing.
  - Hybrid Maize: 3 stages (Basal, Knee-high, Tasseling).
  - Cotton: 3 stages (Basal, Squaring, Boll formation).
  - Sugarcane: 3 splits (Basal, Tillering 45 DAP, Grand growth 90 DAP).
- **Root Cause:** Hardcoded single schedule table used uniformly across all crop types.
- **Fix Implemented:**
  1. Configured crop-specific phenological split schedules in `phase6_fertilizer/catalog.py`.
  2. Updated `generate_fertilizer_schedule` in `phase6_fertilizer/service.py` to select the matching crop split template dynamically.
  3. If a crop has no specialized schedule, it provides a documented standard recommendation with an explicit note regarding the limitation.
- **Test Used to Verify Fix:** `phase6_fertilizer/tests/test_fertilizer_optimization.py::test_09_crop_specific_schedules`.
- **Remaining Limitation:** Split timing is expressed in Days After Sowing/Planting (DAS/DAP) and growth stages; weather-based delay advisories are applied dynamically by Phase 7.

---

### BUG-CAT-01: Fertilizer Catalog Statutory Provenance and Bag Units
- **Issue ID:** BUG-CAT-01
- **Severity:** Medium (Priority P1)
- **Affected File & Function:** `phase6_fertilizer/catalog.py` -> `FERTILIZER_CATALOG`
- **Actual Observed Behavior:** Catalog items contained prices without citations, effective dates, or commercial package size specifications.
- **Expected Behavior:** Every fertilizer product in the catalog must specify commercial package size (e.g. 45 kg Urea, 50 kg DAP/MOP/SSP/Complex), price effective date, statutory pricing source (Department of Fertilizers, GoI / NBS Scheme), and guaranteed nutrient percentages.
- **Root Cause:** Prototype dictionary lacked regulatory metadata attributes.
- **Fix Implemented:**
  1. Enriched all products in `FERTILIZER_CATALOG` with:
     - `commercial_bag_size_kg`: 45 kg (Urea), 50 kg (DAP, MOP, SSP, Complex).
     - `price_effective_date`: "2024-04-01".
     - `price_source`: "Department of Fertilizers, Government of India (Statutory MRP / NBS Scheme 2024-25)".
     - `verification_status`: "VERIFIED_STATUTORY".
- **Test Used to Verify Fix:** `phase6_fertilizer/tests/test_fertilizer_optimization.py::test_01_valid_lp_optimization`, `phase7_integration/tests/test_integration.py::test_06_fertilizer_prices_endpoint`.
- **Remaining Limitation:** Market retail prices may vary slightly based on local primary agricultural cooperative societies (PACCS) transport margins.

---

### BUG-UI-01: API Schema Key Inconsistencies with Flutter Client & PDF Generator
- **Issue ID:** BUG-UI-01
- **Severity:** Medium (Priority P1)
- **Affected File & Function:** `phase5_nutrient/models.py`, `phase6_fertilizer/models.py`, Flutter UI screens, ReportLab PDF generator
- **Actual Observed Behavior:** Phase 5 generated `n_req_kg_per_ha`, while Flutter screens and the PDF generator expected `net_n_kg_per_ha`. Similarly, Phase 6 produced `product_name`, while the UI looked for `name`. This resulted in `0.0 kg/ha` nutrient values and "Fertilizer" generic product names on screens and generated PDFs.
- **Expected Behavior:** Exact calculated values and specific product names must appear seamlessly across screens and exported PDF reports.
- **Root Cause:** Asymmetrical field name evolution between backend models and frontend DTOs.
- **Fix Implemented:**
  1. Added alias fields (`net_n_kg_per_ha`, `net_p2o5_kg_per_ha`, `net_k2o_kg_per_ha`, `total_farm_n_kg`, `name`) directly in backend Pydantic models.
  2. Implemented defensive fallback accessors (`data['net_n_kg_per_ha'] ?? data['n_req_kg_per_ha']`) in Flutter Dart widgets and ReportLab PDF generator.
- **Test Used to Verify Fix:** `flutter_app/test/screens_flow_test.dart`, `phase7_integration/tests/test_extra_api.py::test_recommendation_save_and_pdf`.
- **Remaining Limitation:** None.

---

### BUG-UI-02: Missing Password Recovery Action in Flutter Client
- **Issue ID:** BUG-UI-02
- **Severity:** Low (Priority P2)
- **Affected File & Function:** `flutter_app/lib/screens/login_screen.dart`, `flutter_app/lib/l10n/app_localizations.dart`
- **Actual Observed Behavior:** The login screen lacked a "Forgot Password" UI button and recovery mechanism.
- **Expected Behavior:** User-friendly recovery action supporting English, Tamil, and Hindi.
- **Root Cause:** Omitted in prototype login layout.
- **Fix Implemented:**
  1. Added "Forgot Password?" text button beneath password field on `LoginScreen`.
  2. Implemented localized dialog displaying support instructions and administrator contact information in English, Tamil, and Hindi.
- **Test Used to Verify Fix:** `flutter_app/test/screens_flow_test.dart` ("LoginScreen displays Forgot Password button and opens recovery dialog").
- **Remaining Limitation:** Automated self-service email OTP recovery is not implemented in this local offline deployment.
