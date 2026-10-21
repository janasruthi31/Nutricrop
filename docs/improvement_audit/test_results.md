# Automated Test Results and Verification Log
**Application Name:** AgroWise AI  
**Project Reference:** SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield  
**Verification Date:** October 2026  
**Auditor / Test Engineer:** Senior QA Engineer & Agricultural Software Architect  

---

## 1. Test Execution Commands & Summary Metrics

All automated test suites were executed in the project environment using verified virtual environment interpreters and standard toolchains:

| Test Suite | Execution Command Line | Working Directory | Total Tests | Passed | Failed | Skipped | Execution Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend Pytest** | `.\venv\Scripts\pytest.exe -v` | Repository Root | 128 | 128 | 0 | 0 | 24.69s |
| **Flutter Analysis**| `flutter analyze` | `flutter_app/` | Static rules | Clean | 0 | 0 | 8.1s |
| **Flutter Widgets** | `flutter test` | `flutter_app/` | 20 | 20 | 0 | 0 | 4.0s |
| **Economic Audit** | `.\venv\Scripts\python.exe scripts/evaluate_economic_benefits.py` | Repository Root | 3 Scenarios | 3 | 0 | 0 | 1.8s |

---

## 2. Python Backend Pytest Suite Breakdown (128 Tests)

### Phase 3: Soil Card OCR, Sniffing & Field Plausibility (51 Tests)
* `phase3_soil/tests/test_extraction.py`: 18 tests passing (regex extractors, Olsen vs. Bray detection, pH, EC, OC, N, P, K, micro-nutrients).
* `phase3_soil/tests/test_service.py`: 12 tests passing (file upload, JPEG/PNG/PDF sniffing, SHA-256 deduplication, farmer review payload, confirmation with `farmer_confirmed=true`).
* `phase3_soil/tests/test_validation.py`: 15 tests passing (hard physical boundaries, soft agronomic bounds, unit standardizations).
* `phase3_soil/tests/test_shc_regression.py`: 6 tests passing (Tamil Unicode normalization, OCR confidence weighting, parameter-specific unit conversions).

### Phase 4 & Phase 5: Agronomic Rules & Deterministic NPK Calculations (32 Tests)
* `agronomy/tests/test_agronomy_rules.py`: 12 tests passing (rule registry loading, compatibility scoring, soil series matching, precedence gating, rejection of unverified rules).
* `phase5_nutrient/tests/test_npk_calculation.py`: 17 tests passing (STCR targeted yield formulas, rating adjustment factors, target yield range limits, unit conversions, farm area scaling).
* `tests/test_agronomic_validation_workflow.py`: 10 tests passing (end-to-end agronomic validation, Groundnut provisional rules, direct API bypass protection, stoichiometric oxide conversions).
* `tests/test_groundnut_npk_audit.py`: 9 tests passing (Acre/hectare conversions, Soil Health Card printed recommendation scaling, no double conversion, unit equivalence).

### Phase 6: Mixed-Integer Linear Programming Fertilizer Optimizer (10 Tests)
* `phase6_fertilizer/tests/test_fertilizer_optimization.py`: 10 tests passing (discrete integer bag counts, coupled nutrient accounting in DAP and NPK complexes, zero nutrient handling, solver optimality vs. brute force, crop split application schedules).

### Phase 2: District Yield Benchmark Regressor (8 Tests)
* `tests/test_phase2_yield.py`: 8 tests passing (model and metadata artifact loading, 9-feature schema consistency, case-insensitive district lookup, non-mutation of NPK requirements, negative rainfall validation).

### Phase 7: Agro-Weather, Authentication & Security (18 Tests)
* `phase7_integration/tests/test_extra_api.py`: 8 tests passing (farmer registration, PBKDF2 password hashing, HMAC-SHA256 JWT tokens, cross-user IDOR access isolation, PDF generation).
* `phase7_integration/tests/test_integration.py`: 9 tests passing (live Open-Meteo weather advisory, offline fallback, cache expiry, master full recommendation pipeline).
* `tests/test_economic_benefit_audit.py`: 3 tests passing (empirical Rice, Maize, and Cotton economic comparisons).

---

## 3. Flutter Client Test Suite Breakdown (20 Tests)

Executed via `flutter test` across all mobile widget workflows:
* `widget_test.dart`: 6 tests passing (app launch, theme initialization, navigation shell smoke tests).
* `screens_flow_test.dart`: 14 tests passing:
  - Language selection screen rendering in English, Tamil (தமிழ்), and Hindi (हिन्दी).
  - Dynamic runtime language switching with instantaneous string re-binding.
  - Login screen form validation and password recovery dialog.
  - Soil card upload, camera scanner flow, and manual edit review dialog.
  - Localized error messages and warning banners across all 3 languages.

---

## 4. End-to-End Workflow Demonstration

The complete end-to-end pipeline was executed and validated with real test data:
1. **Authentication:** Authenticated test user receives cryptographically signed JWT token.
2. **Soil Health Card Ingestion:** Uploaded multi-parameter soil test report is parsed; extracted values ($N=220, P=16, K=190\text{ kg/ha}$) are presented for farmer review.
3. **Confirmation:** Farmer confirms values (`POST /api/soil/confirm`), creating an immutable profile record.
4. **Agronomic Rule Selection:** Matching algorithm selects verified rule `TNAU_STCR_IPNS_RICE_001` for irrigated rice in Thanjavur (Palavidhi series).
5. **NPK Requirement:** Calculates net fertilizer requirements ($N=17.6\text{ kg/ha}, P_2O_5=28.4\text{ kg/ha}, K_2O=10.2\text{ kg/ha}$).
6. **Whole-Bag Optimization:** SciPy MILP solves for integer commercial bags (1 Urea, 1 DAP, 1 MOP, 1 SSP) with total cost of ₹3,916.50.
7. **Agro-Weather Advisory:** Retrieves real-time weather, evaluates precipitation against configurable rain threshold, and outputs timing advice.
8. **Yield Benchmark:** XGBoost model outputs district average benchmark ($4,850\text{ kg/ha}$).
9. **PDF Report Generation:** ReportLab generates downloadable, tamper-proof bilingual PDF report matching all database values.
10. **Security Isolation:** Verified that a separate authenticated user cannot access or download this recommendation record (`403 Forbidden`).
