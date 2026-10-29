# Soil-Series Coverage and Soil-Test Method Test Execution Report
**Project:** AgroWise AI (NutriCrop)  
**Execution Environment:** Windows (x64), Python 3.11.0, Flutter 3.29.0 / Dart 3.7.0  
**Date:** October 28, 2026  
**Overall Result:** 219/219 Backend Tests PASSED (100%), 21/21 Flutter Tests PASSED (100%)  

---

## 1. Executive Summary

A comprehensive automated test suite was developed and executed to rigorously validate:
1. Soil-series calibration conditions for Rice, Cotton, and Maize STCR-IPNS targeted yield equations.
2. Clean rejection of uncalibrated or invented soil series (`UNSUPPORTED_SOIL_SERIES`).
3. Safe and transparent fallback to standard fertilizer recommendations (`STANDARD_RDF`) when supported by published TNAU guidelines.
4. Chemical extractant compatibility enforcement for soil phosphorus (Olsen vs. Bray-1).
5. Clean rejection of Bray-1 phosphorus for Olsen-calibrated equations (`INCOMPATIBLE_SOIL_TEST_METHOD`) with zero generic conversion factors.
6. Proper reporting of missing phosphorus method (`MISSING_INPUTS` with `error_code="MISSING_PHOSPHORUS_METHOD"`).
7. Consistency between Python backend calculation models, FastAPI endpoints, and Flutter mobile UI data contracts.

---

## 2. Dedicated Soil-Series & Method Test Matrix (`tests/test_soil_series_and_methods.py`)

The newly implemented test suite `tests/test_soil_series_and_methods.py` executes 10 comprehensive test scenarios covering the full decision matrix:

| Test ID | Test Scenario | Inputs / Conditions | Expected Behavior | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | Supported Soil Series: Rice | Crop: Rice, Series: `Palavidhi`, Target: $6.0\text{ t/ha}$, NPK: 220, 16 (Olsen), 190 | `status == "SUCCESS"`, `is_stcr_ipns == True`, `selected_rule_id == "TNAU_STCR_IPNS_RICE_001"` | Status: `SUCCESS`, Rule: `TNAU_STCR_IPNS_RICE_001`, Precision label displayed | **PASSED** |
| **02** | Supported Soil Series: Cotton | Crop: Cotton, Series: `Irugur`, Target: $2.5\text{ t/ha}$, NPK: 200, 14 (Olsen), 180 | `status == "SUCCESS"`, `is_stcr_ipns == True`, `selected_rule_id == "TNAU_STCR_IPNS_COTTON_001"` | Status: `SUCCESS`, Rule: `TNAU_STCR_IPNS_COTTON_001` | **PASSED** |
| **03** | Supported Soil Series: Maize | Crop: Maize, Series: `Coimbatore`, Target: $6.0\text{ t/ha}$, NPK: 220, 16 (Olsen), 190 | `status == "SUCCESS"`, `is_stcr_ipns == True`, `selected_rule_id == "TNAU_STCR_IPNS_MAIZE_001"` | Status: `SUCCESS`, Rule: `TNAU_STCR_IPNS_MAIZE_001` | **PASSED** |
| **04** | Unsupported Series with STCR Request | Crop: Rice, Series: `Somayanur` (uncalibrated), `recommendation_type: STCR_IPNS` | `status == "UNSUPPORTED_SOIL_SERIES"`, `error_code == "UNSUPPORTED_SOIL_SERIES"`, Cost: 0, Bags: 0 | Status: `UNSUPPORTED_SOIL_SERIES`, Optimizer halted | **PASSED** |
| **05** | Fallback to Standard RDF | Crop: Rice, Series: `Somayanur` (uncalibrated), general recommendation request | `status == "SUCCESS"`, `is_standard_rdf == True`, Fallback to `TNAU_STD_RICE_001`, `confidence == "lower"` | Status: `SUCCESS`, Rule: `TNAU_STD_RICE_001`, Lower confidence banner displayed | **PASSED** |
| **06** | Unsupported Series: No Fallback | Crop: Cotton, Series: `Somayanur` (uncalibrated), general recommendation request | `status == "UNSUPPORTED_SOIL_SERIES"`, Cost: 0, Bags: 0 (No blanket fallback registered) | Status: `UNSUPPORTED_SOIL_SERIES`, Optimizer halted cleanly | **PASSED** |
| **07** | Bray-1 P Incompatible with STCR Rice | Crop: Rice, Series: `Palavidhi`, Soil P: $16\text{ kg/ha}$, `soil_phosphorus_method: "Bray"` | `status == "INCOMPATIBLE_SOIL_TEST_METHOD"`, Actionable warning on Olsen requirement, Cost: 0 | Status: `INCOMPATIBLE_SOIL_TEST_METHOD`, Optimizer halted, generic conversion prohibited | **PASSED** |
| **08** | Missing Soil Phosphorus Method | Crop: Rice, Series: `Palavidhi`, Soil P: $16\text{ kg/ha}$, `soil_phosphorus_method: None` | `status == "MISSING_INPUTS"`, `error_code == "MISSING_PHOSPHORUS_METHOD"`, Missing inputs list | Status: `MISSING_INPUTS`, Error code: `MISSING_PHOSPHORUS_METHOD` | **PASSED** |
| **09** | Bray-1 Compatible with Standard RDF | Crop: Blackgram, `soil_phosphorus_method: "Bray"`, `recommendation_type: GENERAL_BLANKET` | `status == "SUCCESS"`, Diagnostic rating interpretation, fixed $20:40:20\text{ kg/ha}$ dose | Status: `SUCCESS`, Standard dose applied, diagnostic Bray rating documented | **PASSED** |
| **10** | API Contract Consistency | Full pipeline execution verification across all response fields | Verification of `is_stcr_ipns`, `is_standard_rdf`, `applicable_limitations`, `supported_phosphorus_methods`, `source_information` | All metadata fields populated and verified | **PASSED** |

---

## 3. Comprehensive Backend Test Suite Results

Command executed:
```bash
pytest -v
```

Summary of results:
```text
============================ 219 passed in 18.93s =============================
```

### Breakdown by Test Suite:
1. `tests/test_soil_series_and_methods.py`: **10/10 PASSED** (Soil-series validation and phosphorus extraction compatibility).
2. `tests/test_soil_report_agronomic_recommendation.py`: **16/16 PASSED** (Authoritative reference cases: Palavidhi rice, Irugur cotton, Blackgram RDF, high-K clamping, FYM scaling, DB export, PDF generation).
3. `tests/test_agronomic_validation_workflow.py`: **10/10 PASSED** (Provisional vs. verified rules, unverified bypass security, unit conversions, whole bag rounding).
4. `tests/test_nutrient_equations_audit.py`: **11/11 PASSED** (Monotonic yield response, soil sensitivity, oxide/elemental stoichiometry, FYM double-counting prevention).
5. `tests/test_task6_agronomic_behaviour_and_e2e.py`: **9/9 PASSED** (Preceding legume credit, residual fertilizer deduction, clamping, end-to-end PDF report generation).
6. `tests/test_groundnut_npk_audit.py`: **9/9 PASSED** (Groundnut hectare/acre conversions, farm totals, blanket RDF).
7. `tests/test_fertilizer_recommendation_upgrade.py`: **19/19 PASSED** (Price change decoupling, commercial package whole bags, reproducibility, user isolation).
8. `phase5_nutrient/tests/test_npk_calculation.py`: **24/24 PASSED** (NPK engine core units, micronutrient advisories, test date expiration, blanket comparison).
9. `phase5_nutrient/tests/test_golden_stcr.py`: **9/9 PASSED** (Golden STCR reference cases, biological N fixation credits, printed card comparison).
10. `phase7_integration/tests/test_integration.py`: **14/14 PASSED** (Master pipeline, Open-Meteo weather guidance, reverse geocode, Tamil voice synthesis, privacy).
11. `phase7_integration/tests/test_extra_api.py`: **12/12 PASSED** (Auth, JWT lockdown, yield predict, PDF download, SQL injection resistance).
12. `phase6_fertilizer/tests/test_fertilizer_optimization.py`: **13/13 PASSED** (Linear programming optimization, surplus bounds, custom prices).
13. `phase1_dataset` & `phase2_yield`: **11/11 PASSED** (Dataset schemas, ML yield benchmark predictions).
14. Miscellaneous suites: **52/52 PASSED**.

---

## 4. Flutter Mobile Test Suite Results

Command executed:
```bash
flutter test
```

Summary of results:
```text
00:05 +21: All tests passed!
```

### Verified Flutter Scenarios:
1. `screens_flow_test.dart`: Language selection (English, Tamil, Hindi), login form rendering, registration form validation.
2. `verify_screen_render_test.dart`: 12-field Soil Health Card confirmation, Phosphorus method dropdown with guidance caption (*"Confirm method from Soil Health Card (Olsen for neutral/alkaline, Bray for acidic). Do not guess."*).
3. `widget_test.dart`: Application smoke test and navigation flow.
4. Error handling banners in `NpkRequirementScreen` and `FinalRecommendationScreen` for `INCOMPATIBLE_SOIL_TEST_METHOD` and `UNSUPPORTED_SOIL_SERIES`.
5. Recommendation badge rendering: Emerald green badge for `STCR_IPNS` vs. soft blue badge for `STANDARD_RDF`.
6. Display of `applicable_limitations` bullet list and authoritative references.

---

## 5. Verification Conclusion

All software engineering criteria specified in Tasks A, B, and C are satisfied with 100% test pass rates across both backend and frontend environments. No regression was introduced into existing authentication, OCR, SQLite persistence, weather forecasting, or ML district yield benchmarks.
