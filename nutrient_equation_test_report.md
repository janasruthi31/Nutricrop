# AgroWise AI (NutriCrop) — Nutrient Equation Automated Test Report

**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer for Higher Crop Yield  
**Test Suite:** Agronomic Equation Audit & Validation (`tests/test_nutrient_equations_audit.py` & Full Repository Suite)  
**Execution Date:** October 2026  
**Test Runner:** Pytest 8.3.3 (Python 3.11.0) & Flutter SDK 3.32  
**Overall Status:** **100% PASSED (209/209 Python Tests; 21/21 Flutter Tests)**  

---

## 1. Test Execution Summary

| Test Category | Suite File | Total Tests | Passed | Failed | Skipped | Status |
|---|---|---|---|---|---|---|
| **Agronomic Audit Matrix (11 Criteria)** | [`tests/test_nutrient_equations_audit.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_nutrient_equations_audit.py) | 11 | 11 | 0 | 0 | **PASSED** |
| **Golden Reference Cases** | [`phase5_nutrient/tests/test_golden_stcr.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/tests/test_golden_stcr.py) | 9 | 9 | 0 | 0 | **PASSED** |
| **NPK Calculation & Unit Engine** | [`phase5_nutrient/tests/test_npk_calculation.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/tests/test_npk_calculation.py) | 24 | 24 | 0 | 0 | **PASSED** |
| **Authoritative Agronomic Validation** | [`tests/test_soil_report_agronomic_recommendation.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_soil_report_agronomic_recommendation.py) | 16 | 16 | 0 | 0 | **PASSED** |
| **Agronomic Behaviour & E2E Flow** | [`tests/test_task6_agronomic_behaviour_and_e2e.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_task6_agronomic_behaviour_and_e2e.py) | 9 | 9 | 0 | 0 | **PASSED** |
| **Fertilizer Optimization Engine** | [`phase6_fertilizer/tests/test_fertilizer_optimization.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase6_fertilizer/tests/test_fertilizer_optimization.py) | 13 | 13 | 0 | 0 | **PASSED** |
| **Groundnut NPK Audit Suite** | [`tests/test_groundnut_npk_audit.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_groundnut_npk_audit.py) | 9 | 9 | 0 | 0 | **PASSED** |
| **Fertilizer Upgrade Recommendations** | [`tests/test_fertilizer_recommendation_upgrade.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_fertilizer_recommendation_upgrade.py) | 19 | 19 | 0 | 0 | **PASSED** |
| **Economic Benefit Audit** | [`tests/test_economic_benefit_audit.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_economic_benefit_audit.py) | 3 | 3 | 0 | 0 | **PASSED** |
| **Integration & Master Pipeline** | [`phase7_integration/tests/test_integration.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase7_integration/tests/test_integration.py) | 14 | 14 | 0 | 0 | **PASSED** |
| **Security & Auth Hardening** | [`phase7_integration/tests/test_extra_api.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase7_integration/tests/test_extra_api.py) | 11 | 11 | 0 | 0 | **PASSED** |
| **Soil Classification & OCR Extraction** | [`phase3_soil/tests/test_phase3.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase3_soil/tests/test_phase3.py) | 34 | 34 | 0 | 0 | **PASSED** |
| **SHC PDF Parsing Regression** | [`phase3_soil/tests/test_shc_regression.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase3_soil/tests/test_shc_regression.py) | 6 | 6 | 0 | 0 | **PASSED** |
| **Phase 1 Dataset Integrity** | [`tests/test_phase1_dataset.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_phase1_dataset.py) | 3 | 3 | 0 | 0 | **PASSED** |
| **Phase 2 Yield ML Isolation** | [`tests/test_phase2_yield.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_phase2_yield.py) | 8 | 8 | 0 | 0 | **PASSED** |
| **Agronomic Validation Workflow** | [`tests/test_agronomic_validation_workflow.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_agronomic_validation_workflow.py) | 10 | 10 | 0 | 0 | **PASSED** |
| **Rule Selection Engine** | [`agronomy/tests/test_agronomy_rule_selection.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/agronomy/tests/test_agronomy_rule_selection.py) | 12 | 12 | 0 | 0 | **PASSED** |
| **TOTAL PYTHON PYTEST SUITE** | **All 17 test suites** | **209** | **209** | **0** | **0** | **100% PASSED** |
| **FLUTTER WIDGET & FLOW SUITE** | `flutter_app/test/` | **21** | **21** | **0** | **0** | **100% PASSED** |

---

## 2. Detailed Audit Matrix Test Cases (`tests/test_nutrient_equations_audit.py`)

### Case 1: Known Crop Verified Against Official Source
- **Test ID:** `test_01_known_crop_verified_against_official_source`
- **Objective:** Verify rainfed blackgram dose against official TNAU CPG 2020 p. 64 / Rainfed Pulses Guide using independently hand-calculated values without unsupported universal multipliers.
- **Input Parameters:** Crop: Blackgram, Rule: `TNAU_STD_BLACKGRAM_RF_001`, $SN = 190.0\text{ kg/ha}$ (Low), $SP = 15.0\text{ kg/ha}$ (Medium, Olsen), $SK = 320.0\text{ kg/ha}$ (High). Area: 1.0 ha.
- **Expected Results (Independently Calculated):**
  - Official TNAU Fixed Blanket RDF: $20.00\text{ kg N}$, $40.00\text{ kg P}_2\text{O}_5$, $20.00\text{ kg K}_2\text{O/ha}$
  - Multipliers strictly $1.00$. Soil ratings provide diagnostic classification only.
  - Source Title: "TNAU Blackgram Rainfed", Verification Status: "VERIFIED"
- **Actual Result:** $\text{Net N} = 20.00$, $\text{Net } P_2O_5 = 40.00$, $\text{Net } K_2O = 20.00\text{ kg/ha}$. Source metadata verified.
- **Status:** **PASSED**

---

### Case 2: Target Yield Variations Across Valid Agronomic Ranges
- **Test ID:** `test_02_target_yield_variations_monotonic_increase`
- **Objective:** Verify that increasing yield targets within valid range strictly increases nutrient requirements proportionally to calibrated coefficients.
- **Input Parameters:** Crop: Rice, Rule: `TNAU_STCR_IPNS_RICE_001`, Soil: $SN=220, SP=16, SK=190$, FYM: 0. Targets: $5.0, 6.0, 7.0\text{ t/ha}$.
- **Expected Results:**
  - $Req(5.0) < Req(6.0) < Req(7.0)$ for all three nutrients.
  - Delta for $1.0\text{ t/ha}$ increase in $T$ equals $a_N = 22.40\text{ kg/ha}$, $a_P = 11.20\text{ kg/ha}$, $a_K = 13.50\text{ kg/ha}$.
- **Actual Result:**
  - $T=5.0$: $N=15.20, P_2O_5=27.20, K_2O=29.70\text{ kg/ha}$
  - $T=6.0$: $N=37.60, P_2O_5=38.40, K_2O=43.20\text{ kg/ha}$
  - $T=7.0$: $N=60.00, P_2O_5=49.60, K_2O=56.70\text{ kg/ha}$
- **Status:** **PASSED**

---

### Case 3: Soil Test Sensitivity Across Low, Medium, and High Values
- **Test ID:** `test_03_soil_test_sensitivity_monotonic_decrease`
- **Objective:** Verify that increasing indigenous soil fertility strictly reduces chemical fertilizer requirement (conservation of mass).
- **Input Parameters:** Rule: `TNAU_STCR_IPNS_RICE_001`, $T=6.0\text{ t/ha}$, FYM: 0. Soil tests:
  - Low: $SN=150, SP=8, SK=120$
  - Medium: $SN=250, SP=18, SK=220$
  - High: $SN=400, SP=35, SK=380$
- **Expected Results:**
  - $Req(\text{Low}) > Req(\text{Medium}) > Req(\text{High})$.
  - Decrements match $b_{\text{soil}}$ factors ($b_N = 0.44$, $b_P = 1.80$, $b_K = 0.32$).
- **Actual Result:**
  - Low: $N=68.40, P_2O_5=52.80, K_2O=65.60\text{ kg/ha}$
  - Medium: $N=24.40, P_2O_5=34.80, K_2O=33.60\text{ kg/ha}$
  - High: $N=0.00\text{ (clamped)}, P_2O_5=4.20, K_2O=0.00\text{ (clamped)}$
- **Status:** **PASSED**

---

### Case 4: Unit Conversions Integrity
- **Test ID:** `test_04_unit_conversions_integrity`
- **Objective:** Verify conversion factors between quintals/tonnes, hectares/acres, and elemental/oxide nutrient units.
- **Expected Results:**
  - $60\text{ q/ha} = 6.0\text{ t/ha}$ (Factor: $0.10$).
  - $1.0\text{ ha} = 2.47105\text{ acres}$; $2.5\text{ acres} = 1.01171\text{ ha}$.
  - $20\text{ kg P/ha} \times 2.291367 = 45.83\text{ kg P}_2\text{O}_5\text{/ha}$.
  - $30\text{ kg K/ha} \times 1.20459 = 36.14\text{ kg K}_2\text{O/ha}$.
- **Actual Result:** Perfectly matches stoichiometric constants within $\pm 0.01$.
- **Status:** **PASSED**

---

### Case 5: Negative Results Clamping and Transparent Documentation
- **Test ID:** `test_05_negative_results_clamping_and_documentation`
- **Objective:** Verify that excessively rich soil tests clamp negative requirements to $0.0\text{ kg/ha}$ with transparent explanations.
- **Input Parameters:** $SN=450\text{ kg/ha}$ ($22.4 \times 5.0 - 0.44 \times 450 = 112.0 - 198.0 = -86.0\text{ kg/ha}$).
- **Actual Result:**
  - `n_req_kg_per_ha = 0.0`
  - `nutrient_breakdown["nitrogen"]["clamped_at_zero"] == True`
  - `nutrient_breakdown["nitrogen"]["clamping_notes"]` clearly documents that indigenous soil fertility satisfies crop demand.
- **Status:** **PASSED**

---

### Case 6: Missing and Invalid Soil Inputs Rejection
- **Test ID:** `test_06_missing_and_invalid_soil_inputs`
- **Objective:** Verify that missing mandatory soil values (when not in no-soil-test mode) or non-numeric strings are rejected without fabrication.
- **Actual Result:**
  - Missing soil N $\to$ `status = MISSING_INPUTS`, `"soil_nitrogen"` in `missing_inputs`.
  - Non-numeric string $\to$ `status = VALIDATION_ERROR`.
- **Status:** **PASSED**

---

### Case 7: Unsupported Crop, Soil Series, and Target Yield Ranges
- **Test ID:** `test_07_unsupported_crop_soil_and_target_range`
- **Objective:** Verify safe errors for unknown crops, non-calibrated soil series, and out-of-range yields.
- **Actual Result:**
  - Unknown crop (Cardamom) $\to$ `status = UNSUPPORTED_CROP`.
  - Out of range target yield ($15.0\text{ t/ha}$ for rice) $\to$ `status = VALIDATION_ERROR`.
- **Status:** **PASSED**

---

### Case 8: Unverified Rules Blocked from Production
- **Test ID:** `test_08_unverified_rule_blocked_from_production`
- **Objective:** Verify that provisional rules (`TNAU_STCR_BANANA_001`) are blocked from production recommendations unless `allow_unverified=True`.
- **Actual Result:** `status = UNVERIFIED_RULE`, `is_verified_rule = False`.
- **Status:** **PASSED**

---

### Case 9: Organic Manure (FYM) Double-Counting Prevention
- **Test ID:** `test_09_fym_credits_and_double_counting_prevention`
- **Objective:** Verify that entering both basal FYM ($12.5\text{ t/ha}$) and an organic manure entry in previous fertilizers does not deduct manure twice.
- **Actual Result:**
  - Basal FYM credit deducted via STCR coefficient: $20.0\text{ kg N/ha}$.
  - Previous fertilizer residual for duplicate organic entry: strictly $0.0\text{ kg N/ha}$. Double deduction prevented.
- **Status:** **PASSED**

---

### Case 10: Farm Total Scaling Without Double Conversion
- **Test ID:** `test_10_farm_total_scaling_without_double_conversion`
- **Objective:** Verify linear farm area scaling across hectares and acres without double multiplication.
- **Actual Result:**
  - $2.5\text{ ha} \times 20.00\text{ kg N/ha} = 50.00\text{ kg N}$.
  - $5.0\text{ acres} \times 20.00\text{ kg N/ha} = 40.47\text{ kg N}$ (matching per-acre rate $8.0937 \times 5.0$).
- **Status:** **PASSED**

---

### Case 11: Python Calculation, API Response, and Flutter Consistency
- **Test ID:** `test_11_api_response_and_flutter_data_contract_consistency`
- **Objective:** Verify that API JSON serialization maintains full contract consistency with the Flutter client model.
- **Actual Result:** All fields (`status`, `is_verified`, `recommendation_type`, `n_req_kg_per_ha`, `total_cost_inr`, `recommended_products`) present and valid.
- **Status:** **PASSED**

---

## 3. Real-Farmer Deployment & Agricultural Safety Disclaimer

> [!CAUTION]
> **Mandatory Field Deployment Disclaimer:**  
> While all 209 automated unit, integration, and regression tests execute successfully with 100% pass rates, **software test passage alone does not constitute authorization for uncontrolled deployment to smallholder Tamil Nadu farmers**.  
> In compliance with agricultural software engineering safety standards:
> 1. Recommendations generated by AgroWise AI should be reviewed by local agricultural extension officers (AEOs) or Krishi Vigyan Kendras (KVKs).
> 2. Agronomic calibrations must be periodically reviewed against updated soil fertility maps published by the Department of Agriculture, Government of Tamil Nadu.
