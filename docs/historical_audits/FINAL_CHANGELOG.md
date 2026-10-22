# Final Engineering Changelog

**Project Title:** AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Project Reference:** SIH1639 — Sustainable Fertilizer Usage Optimizer  
**Release Date:** October 2026  
**Auditor & Lead Engineer:** Senior Python/FastAPI Engineer, Flutter/Dart Developer, Agricultural Data Scientist, Optimization Engineer, Database Engineer, QA Engineer & Security Auditor  

---

## 1. Summary of Changes

This changelog records all modifications implemented across the backend microservices, optimization algorithms, ML inference pipelines, security layer, Flutter client, test suites, and documentation.

---

## 2. Component-by-Component Modifications

### A. Fertilizer Optimizer & Packaging (`phase6_fertilizer/`)
- **`phase6_fertilizer/service.py`**:
  - Replaced continuous LP relaxation (`scipy.optimize.linprog`) and heuristic ceiling rounding (`math.ceil`) with exact **Mixed-Integer Linear Programming (MILP)** using `scipy.optimize.milp` with HiGHS branch-and-cut solver.
  - Defined integer decision variables $y_j \in \mathbb{N}_0$ representing whole commercial bags (45 kg Urea, 50 kg DAP, 50 kg MOP, 50 kg SSP, 50 kg Complex).
  - Constructed constraint matrix $\mathbf{A} \cdot \mathbf{y} \ge \mathbf{b}$ for Nitrogen, Phosphorus ($\text{P}_2\text{O}_5$), and Potassium ($\text{K}_2\text{O}$).
  - Implemented upper bound constraints ($1.5 \times$ upper bound) to prevent toxic nutrient surplus.
  - Recalculated exact supplied nutrient kilograms directly from the optimal integer bag counts.
  - Added deterministic integer grid search fallback for constrained instances.
  - Updated `generate_fertilizer_schedule` to look up crop-specific phenological split schedules per TNAU Crop Production Guide 2020 (100% basal for pulses; 3 stages for Rice, Maize, Cotton, and Sugarcane).
- **`phase6_fertilizer/catalog.py`**:
  - Enriched catalog with statutory MRP prices (effective 2024-04-01), Department of Fertilizers (GoI) NBS subsidy citations, commercial bag sizes, and phenological split templates.
- **`phase6_fertilizer/optimizer.py`**:
  - Created module interface exposing `optimize_fertilizer_selection` and catalog components to preserve clean architectural references.

### B. Agronomic Engine & Unit Normalization (`phase5_nutrient/`)
- **`phase5_nutrient/units.py`**:
  - Implemented `normalize_target_yield(value, unit)` supporting `t/ha`, `q/ha` / `quintal/ha` ($\times 0.1$), and `kg/ha` ($\times 0.001$).
  - Implemented `convert_elemental_to_oxide(n, p, k, p_unit, k_unit)` converting elemental $\text{P} \to \text{P}_2\text{O}_5$ ($\times 2.291$) and $\text{K} \to \text{K}_2\text{O}$ ($\times 1.205$).
  - Implemented `convert_area(value, unit)` supporting hectares, acres ($\times 0.404686$), and square meters ($\times 0.0001$).
- **`phase5_nutrient/models.py`**:
  - Added `target_yield_unit`, `p_unit`, `k_unit`, and `irrigation_method` fields to `NutrientCalculationRequest`.
  - Added frontend compatibility aliases (`net_n_kg_per_ha`, `total_farm_n_kg`, etc.) to `NutrientCalculationResponse`.
- **`phase5_nutrient/service.py`**:
  - Integrated unit conversions into the STCR calculation pipeline before formula evaluation.
  - Populated canonical and alias fields simultaneously.

### C. Pipeline Orchestration & Data Validation (`phase7_integration/`)
- **`phase7_integration/service.py`**:
  - Eliminated silent default soil values (`220.0 N, 16.0 P, 190.0 K`).
  - Added database lookup to retrieve confirmed soil test records from the farmer's authenticated `soil_profiles` table when `soil_profile_id` is supplied.
  - Enforced explicit validation errors when soil nutrient measurements are missing.
- **`phase7_integration/extra_api.py`**:
  - Removed insecure fallback to `"farmer_001"` in `get_current_user`; enforced HTTP 401 Unauthorized for unauthenticated requests.
  - Enforced object-level authorization across saved recommendations, PDF downloads, farm records, fertilizer history, and notifications, returning HTTP 403 Forbidden for cross-farmer unauthorized access attempts.

### D. Machine Learning Inference Pipeline (`predict_yield.py`)
- **`predict_yield.py`**:
  - Removed silent fallback returning `3500.0 kg/ha`.
  - Added strict input validation against `models/yield_prediction/metadata.json` valid categories (districts, crops, seasons).
  - Added non-negative rainfall input validation ($Rain \ge 0$).
  - Reconciled feature schema to strictly require the 9 trained features in order:
    1. `District`
    2. `Crop`
    3. `Season`
    4. `Year`
    5. `Rain_SWM_mm`
    6. `Rain_NEM_mm`
    7. `Rain_Winter_mm`
    8. `Rain_HotWeather_mm`
    9. `Rain_Annual_mm`
  - Preserved original trained XGBoost pipeline in `models/yield_prediction/yield_model.joblib` without retraining.

### E. Flutter Mobile/Web Application (`flutter_app/`)
- **`flutter_app/lib/screens/login_screen.dart`**:
  - Added "Forgot Password?" action with localized modal dialog in English, Tamil, and Hindi.
- **`flutter_app/lib/screens/npk_requirement_screen.dart` & `final_recommendation_screen.dart`**:
  - Added defensive multi-key accessors (`data['net_n_kg_per_ha'] ?? data['n_req_kg_per_ha']` and `data['name'] ?? data['product_name']`).
- **`flutter_app/test/screens_flow_test.dart`**:
  - Built comprehensive widget and integration test suite (18 tests) covering multilingual switching (Tamil, Hindi, English), authentication screens, farm details, crop selection, rainfall inputs, and error states.

### F. Automated Test Suites (`tests/`, microservice tests)
- **`phase6_fertilizer/tests/test_fertilizer_optimization.py`**:
  - Added `test_08_milp_optimality_compared_to_brute_force` proving mathematical optimality against brute-force search.
  - Added `test_09_crop_specific_schedules` verifying crop-specific split timing.
  - Added `test_10_whole_bag_integer_units` verifying integer bag counts.
- **`tests/test_phase2_yield.py`**:
  - Added 8 tests verifying 9-feature schema consistency, model loading, case-insensitivity, negative rainfall rejection, and isolation from NPK logic.
- **`phase5_nutrient/tests/test_npk_calculation.py`**:
  - Added tests for `q/ha` to `t/ha` conversion, elemental to oxide conversion, and farm area conversions.
- **`phase7_integration/tests/test_extra_api.py`**:
  - Added tests for authentication enforcement, cross-user 403 Forbidden isolation, and recommendation persistence.

### G. Documentation Deliverables
- **`AUDIT_REPORT.md`**: Comprehensive architectural, agronomic, optimizer, ML, and security evaluation.
- **`BUGS_AND_FIXES.md`**: Master defect register with 9 detailed bug reports and verifying tests.
- **`TEST_RESULTS.md`**: Automated test run results (97 backend pytest, 18 Flutter tests, 0 analyzer issues, Flutter web build).
- **`FINAL_CHANGELOG.md`**: This engineering changelog.
- **`README.md`**: Updated production setup, prerequisites, execution, and verification guide.
