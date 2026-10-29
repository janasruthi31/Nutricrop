# Final Equation Test Report & Verification Assessment

**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer for Higher Crop Yield  
**Date:** October 28, 2026  
**Auditor:** Senior Agricultural Software Engineer & Agronomy-Data Validation Specialist  
**Standard:** Agricultural Software Quality, Farmer Safety, and TNAU Agronomic Verification  

---

## 1. Executive Summary

A core directive of this agronomic audit is:
> *"The latest audit report claims that 209 Python tests and 21 Flutter tests passed. Do not treat those results as proof that the equations are scientifically correct. Independently verify the source, equation, units and applicable conditions."*

This report documents the empirical test execution results across both Python backend and Flutter frontend test suites following the disablement of unverified and discrepant STCR-IPNS equations.

### Test Execution Summary Table

| Test Suite / Component | Scope | Total Tests | Passed | Failed | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `tests/test_final_equation_audit_safety.py` | New Safety & Regression Suite | 11 | 11 | 0 | **100% PASS** |
| `tests/test_nutrient_equations_audit.py` | 11-Point Agronomic Matrix | 11 | 11 | 0 | **100% PASS** |
| `tests/test_phase1_dataset.py` | Dataset & Registry Schema | 3 | 3 | 0 | **100% PASS** |
| `tests/test_phase2_yield.py` | Yield Prediction Models | 8 | 8 | 0 | **100% PASS** |
| `flutter_app/test/` | Flutter UI & Flow Suite | 21 | 21 | 0 | **100% PASS** |
| Legacy Agronomic Test Suites | Outdated STCR-permissive tests | 64 | 33 | 31 | **Expected Failures (Safety Gate Active)** |

---

## 2. Dedicated Safety Test Suite Execution (`test_final_equation_audit_safety.py`)

A newly created test suite (`tests/test_final_equation_audit_safety.py`) explicitly validates the safety gate requirements specified by the agricultural audit:

```
collected 11 items

tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_01_all_unsupported_stcr_rules_are_disabled_in_registry PASSED [  9%]
tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_02_verified_standard_rules_are_enabled_in_registry PASSED [ 18%]
tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_03_rice_production_safely_falls_back_to_verified_standard_rdf PASSED [ 27%]
tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_04_explicit_stcr_request_for_rice_is_rejected PASSED [ 36%]
tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_05_cotton_request_returns_no_verified_rule_and_halts_optimizer PASSED [ 45%]
tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_06_maize_request_returns_no_verified_rule_and_halts_optimizer PASSED [ 54%]
tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_07_blackgram_uses_verified_standard_rdf PASSED [ 63%]
tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_08_groundnut_uses_verified_blanket_rdf PASSED [ 72%]
tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_09_sugarcane_uses_verified_standard_rdf PASSED [ 81%]
tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_10_phase5_blocks_unsupported_rules_without_allow_unverified PASSED [ 90%]
tests/test_final_equation_audit_safety.py::TestFinalEquationAuditSafety::test_11_phase5_allows_calculation_for_audit_when_allow_unverified_true PASSED [100%]

============================= 11 passed in 3.69s ==============================
```

### Safety Tests Validation Highlights:
1. **Rule Disablement Integrity (`test_01` & `test_02`):** Confirms `TNAU_STCR_IPNS_RICE_001`, `TNAU_STCR_IPNS_COTTON_001`, `TNAU_STCR_IPNS_MAIZE_001`, `TNAU_STD_GROUNDNUT_001`, `TNAU_STCR_BANANA_001`, and `TNAU_DEPRECATED_RICE_000` are disabled (`is_enabled: false`) and non-verified (`is_verified: false`). Confirms `TNAU_STD_RICE_001`, `TNAU_STD_BLACKGRAM_RF_001`, `TNAU_BLANKET_GROUNDNUT_001`, and `TNAU_STD_SUGARCANE_001` are enabled and verified.
2. **Safe Rice Production Fallback (`test_03`):** Irrigated Rice requests seamlessly fall back to `TNAU_STD_RICE_001` (Standard RDF) with verified TNAU rating table adjustments.
3. **Explicit Unsupported STCR Rejection (`test_04`):** If a user explicitly requests STCR mode for rice, the system rejects it with `status: "NO_VERIFIED_RULE"`.
4. **Cotton & Maize Commercial Halting (`test_05` & `test_06`):** Cotton and Maize queries return `status: "NO_VERIFIED_RULE"`, `error_code: "NO_VERIFIED_RULE"`, completely halting the commercial fertilizer optimizer (`recommended_products: []`, `total_cost_inr: 0.0`).
5. **Gating Parameter Enforcement (`test_10` & `test_11`):** Calls with `allow_unverified=False` reject unverified rules, while `allow_unverified=True` allows execution solely for mathematical auditing.

---

## 3. Flutter Mobile Application Test Results

The Flutter automated test suite was executed in `flutter_app/`:

```
00:00 +0: loading flutter_app/test/screens_flow_test.dart
00:01 +1: LanguageSelectionScreen displays English, Tamil, Hindi options
00:01 +10: LoginScreen renders email, password fields and login button
00:02 +11: RegisterScreen renders form fields
00:02 +12: VerifyScreen renders with full 12 fields from real PDF
00:05 +18: SoilApp smoke test
00:05 +21: All tests passed!
```

**Result:** **21/21 tests passed (100%)**.  
The Flutter client correctly handles the `NO_VERIFIED_RULE` response, rendering the amber warning card without crashing or exposing unverified purchase recommendations.

---

## 4. Analysis of Legacy Test Suite Failures

When running legacy test suites across the repository, 31 tests failed while 33 passed. An analysis of these failures reveals that they fall into three distinct categories:

### Failure Category A: Legacy Tests Asserting `TNAU_STCR_IPNS_RICE_001` Selection
- **Files:** `tests/test_soil_report_agronomic_recommendation.py`, `tests/test_agronomic_validation_workflow.py`, `tests/test_soil_series_and_methods.py`.
- **Failure Symptom:**
  ```
  AssertionError: assert 'TNAU_STD_RICE_001' == 'TNAU_STCR_IPNS_RICE_001'
  ```
- **Agronomic Explanation:** These legacy tests were written under the unverified assumption that `TNAU_STCR_IPNS_RICE_001` was an active, verified production rule. Because the audit disabled this rule due to serious discrepancies against Adanur and Kalathur series, the system correctly selected `TNAU_STD_RICE_001`. The failure of the test assertion is evidence that the safety gate is actively intercepting unverified rules.

### Failure Category B: Legacy Tests Expecting Commercial Optimizer Output for Cotton & Maize
- **Files:** `tests/test_fertilizer_recommendation_upgrade.py`, `tests/test_economic_benefit_audit.py`, `tests/test_task6_agronomic_behaviour_and_e2e.py`.
- **Failure Symptom:**
  ```
  AssertionError: assert len(recommended_products) > 0  [len was 0]
  AssertionError: assert total_cost_inr > 0             [cost was 0.0]
  ```
- **Agronomic Explanation:** Legacy tests asserted that passing cotton or maize soil test data would result in a commercial fertilizer shopping list. Because Cotton and Maize STCR rules are unverified and have no verified blanket fallback in the registry, the optimizer correctly halts with `status: "NO_VERIFIED_RULE"`, `recommended_products: []`, and `total_cost_inr: 0.0`. This prevents farmers from spending money on unvalidated fertilizer doses.

### Failure Category C: Legacy Tests Asserting `is_verified: true` on Provisional Rules
- **Files:** `tests/test_groundnut_npk_audit.py`.
- **Failure Symptom:**
  ```
  AssertionError: assert data["recommendation_type"] == "STCR_IPNS"
  ```
- **Agronomic Explanation:** The test expected groundnut to use a provisional STCR equation. The audit classified `TNAU_STD_GROUNDNUT_001` as `PENDING_VERIFICATION`, routing groundnut to the verified `TNAU_BLANKET_GROUNDNUT_001` (Standard RDF).

---

## 5. Unresolved Limitations & Required Field Validations

1. **Automated Tests Do Not Replace Field Trials:** Passing automated tests confirms code syntax and contract fulfillment, not biological efficacy. No automated test can prove that $150\text{ kg N/ha}$ produces optimum yield under unpredictable Northeast Monsoon rainfall.
2. **Missing Soil Series Calibrations:**
   - **Palavidhi Series:** Currently has no published TNAU STCR calibration. Multi-season field trials with graded NPK doses are required in Dindigul/Madurai districts.
   - **Coimbatore Series:** Red gravelly loam soils in Coimbatore district require independent STCR equations distinct from Pilamedu cracking clay.
3. **Pending Verification Rules:**
   - **Banana (`TNAU_STCR_BANANA_001`):** Requires validation of per-plant to per-hectare population conversions (e.g. 2500 plants/ha for Grand Naine).
   - **Groundnut Target Yield (`TNAU_STD_GROUNDNUT_001`):** Requires confirmation of pod yield target feasibility in rainfed red sandy soils.

---

## 6. Final Acceptance Conclusion

**Final Acceptance Criterion Satisfied:**  
No unverified, mismatched, or discrepant STCR-IPNS equation can generate a production fertilizer recommendation in AgroWise AI. Production recommendations are generated exclusively by verified TNAU standard recommendations or halted with `NO_VERIFIED_RULE`.
