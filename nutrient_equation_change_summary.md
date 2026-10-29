# AgroWise AI (NutriCrop) — Nutrient Equation Change Summary

**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer for Higher Crop Yield  
**Release / Milestone:** Agronomic Equation Verification & Safety Fix  
**Date:** October 2026  
**Auditor:** Senior Agricultural Software Engineer & Agronomy-Data Validation Specialist  

---

## 1. Overview of Changes

This document details the modifications, corrections, and safeguards implemented during the agronomic equation verification and safety audit. All changes strictly adhere to the project constraints: preserving existing Flutter UI screens and navigation, authentication, database schemas, weather integrations, ML district yield models, and the SciPy HiGHS/PuLP MILP optimizer.

---

## 2. Summary of Modified and Created Files

| File Path | Nature of Change | Summary of Modifications | Agronomic / Technical Justification |
| :--- | :--- | :--- | :--- |
| [`data/agronomy/tnau_stcr_rules.json`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/data/agronomy/tnau_stcr_rules.json) | **Registry Modification** | 1. Purged unsupported universal `rating_adjustment_factors` from `TNAU_STD_BLACKGRAM_RF_001`, `TNAU_BLANKET_GROUNDNUT_001`, `TNAU_STD_GROUNDNUT_001`, and `TNAU_STD_SUGARCANE_001`.<br>2. Set `"supports_rating_adjustment": false` on all blanket rules.<br>3. Verified and preserved `"supports_rating_adjustment": true` on `TNAU_STD_RICE_001` with authoritative TNAU Soil Testing Services portal citation.<br>4. Labeled `TNAU_BLANKET_GROUNDNUT_001` and `TNAU_STD_BLACKGRAM_RF_001` as `GENERAL_BLANKET` to prevent conflation with STCR equations. | Prevents universal $\pm 25\%$ multiplier distortion; ensures blanket recommendations remain fixed official RDF doses unless explicitly authorized by crop-specific official publications. |
| [`phase5_nutrient/service.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/service.py) | **Code Modification** | 1. Added `current_fym_applied_t_per_ha` parameter to `_calculate_previous_fertilizer_residual` and skipped duplicate organic manure entries in previous history when basal FYM is already applied.<br>2. Gated `interpolate_soil_rating_multiplier()` behind `rule.get("supports_rating_adjustment") is True` AND non-blanket recommendation type.<br>3. Locked general blanket multipliers strictly to $1.00$ ($factor_N = 1.0, factor_P = 1.0, factor_K = 1.0$).<br>4. Separated diagnostic soil fertility interpretation (`soil_nutrient_status`) from fertilizer dose calculations.<br>5. Added user-facing transparency warnings. | Eliminates double-counting of organic manure; prevents blanket multipliers; maintains clear boundary between soil testing categories and fertilizer requirements. |
| [`phase5_nutrient/tests/test_golden_stcr.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/tests/test_golden_stcr.py) | **Test Suite Update** | Updated Golden Test Cases 1, 2, 3, 4, and 9 to expect the official fixed blanket RDF ($20.0\text{ N}, 40.0\text{ P}_2\text{O}_5, 20.0\text{ K}_2\text{O}\text{ kg/ha}$) for Blackgram without unsupported multipliers. | Aligns golden reference test suite with authoritative TNAU CPG 2020 p. 64. |
| [`phase5_nutrient/tests/test_npk_calculation.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/tests/test_npk_calculation.py) | **Test Suite Update** | Updated `test_02` and `test_11` to assert fixed $20:40:20\text{ kg/ha}$ Blackgram blanket RDF (and $50:100:50\text{ kg}$ total farm doses for 2.5 ha). | Eliminates stale assertions expecting continuous rating multipliers on blanket schedules. |
| [`tests/test_soil_report_agronomic_recommendation.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_soil_report_agronomic_recommendation.py) | **Test Suite Update** | Refactored `test_ref_03` to verify fixed Blackgram blanket RDF ($20.0, 40.0, 20.0\text{ kg/ha}$) without unsupported multipliers; added companion test `test_ref_03b` asserting authorized rating adjustments for Rice under `TNAU_STD_RICE_001`. | Validates that blanket schedules remain fixed while authorized Rice rating adjustments function correctly. |
| [`tests/test_nutrient_equations_audit.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_nutrient_equations_audit.py) | **Test Suite Update** | Aligned `test_01` and `test_10` with fixed $20.0\text{ kg N/ha}$ Blackgram blanket requirement and linear farm-total scaling. | Ensures the 11-point audit matrix test suite passes with verified agronomic values. |
| [`nutrient_equation_audit.md`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/nutrient_equation_audit.md) | **Deliverable** | Complete mathematical and literature audit defining variables, physical units, canonical STCR-IPNS equations, fixed blanket schedules, double-counting protections, and safety statuses. | Satisfies deliverable requirement 1. |
| [`agronomic_rule_verification.md`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/agronomic_rule_verification.md) | **Deliverable** | Registry of verified rules, source citations, equations, units, conditions, and pending/unsupported rules. | Satisfies deliverable requirement 2. |
| [`nutrient_equation_change_summary.md`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/nutrient_equation_change_summary.md) | **Deliverable** | This change summary document detailing modified files, rationale, and rule statuses. | Satisfies deliverable requirement 3. |
| [`nutrient_equation_test_report.md`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/nutrient_equation_test_report.md) | **Deliverable** | Test execution report covering all 209 Python tests and 21 Flutter tests with pass evidence. | Satisfies deliverable requirement 4. |

---

## 3. Detailed Explanation of Code & Logic Modifications

### 3.1 FYM & Organic Manure Double-Counting Protection
- **Vulnerability:** When a farmer entered both a basal FYM application rate (`fym_applied_t_per_ha = 12.5`) and entered an organic manure application in `previous_fertilizers` (e.g. "FYM, 12.5 tonnes applied 1 month ago"), the system deducted both:
  1. $c_{\text{FYM}}$ ($20.0\text{ kg N/ha}$) via the STCR-IPNS equation term.
  2. An additional $10\%\text{ N}, 20\%\text{ P}_2\text{O}_5, 15\%\text{ K}_2\text{O}$ residual via `_calculate_previous_fertilizer_residual`.
- **Implementation:**
  In [`phase5_nutrient/service.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/service.py#L457-L466), when `current_fym_applied_t_per_ha > 0`, any organic manure entry in `previous_fertilizers` for the recent application window ($\text{months\_ago} \le 3.0$) is ignored during residual calculations.

### 3.2 Removal of Universal Multipliers & Blanket Path Isolation
- **Vulnerability:** All blanket recommendations were automatically multiplied by $\pm 25\%$ or continuous interpolation factors based on soil nutrient ratings (Low $+25\%$, Medium $0\%$, High $-25\%$), despite lack of official TNAU source authorization.
- **Implementation:**
  In [`phase5_nutrient/service.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/service.py#L1065-L1110):
  ```python
  is_general_blanket = (
      req.recommendation_type == "GENERAL_BLANKET"
      or rec_method == "TNAU-BLANKET"
      or rule.get("recommendation_type") == "GENERAL_BLANKET"
  )
  rule_supports_adj = (
      bool(rule.get("supports_rating_adjustment", False))
      and rule.get("rating_adjustment_factors") is not None
  )

  if rule_supports_adj and not is_general_blanket and not is_no_soil_test:
      factor_n = self.interpolate_soil_rating_multiplier("nitrogen", sn, p_method)
      factor_p = self.interpolate_soil_rating_multiplier("phosphorus", sp, p_method)
      factor_k = self.interpolate_soil_rating_multiplier("potassium", sk, p_method)
      adjustment_mode = "RULE_AUTHORIZED_RATING_ADJUSTMENT"
  else:
      # Verified crop-specific blanket dose (1.00x multiplier)
      factor_n, factor_p, factor_k = 1.0, 1.0, 1.0
      adjustment_mode = "GENERAL_BLANKET_FIXED_RDF" if is_general_blanket else "FIXED_BLANKET_DOSE"
  ```

### 3.3 Separation of Blanket vs. STCR-IPNS Recommendations
- Verified standard blanket recommendations (Blackgram, Groundnut, Sugarcane) are categorized under `recommendation_method: "TNAU-BLANKET"` or `"TNAU-SOIL-TEST"` with `recommendation_type: "GENERAL_BLANKET"`.
- Calibrated STCR equations (Rice, Cotton, Maize) are categorized under `recommendation_method: "STCR-IPNS"` with `recommendation_type: "SOIL_SPECIFIC_STCR"`.
- Blanket recommendations are never labeled as STCR equations.

### 3.4 Decoupling of ML Yield Prediction and Weather
- Phase 2 Random Forest regression yield prediction is labeled as a historical district benchmark.
- Phase 7 weather guidance provides spray and field advisories.
- Neither Phase 2 nor Phase 7 has access to mutate the nutrient requirement variables ($a \cdot T - b \cdot SN - c \cdot FYM$).

### 3.5 Downstream Fertilizer Optimization
- Phase 6 PuLP LP/MILP optimizer executes only after Phase 5 produces a successful calculation response.
- Complex fertilizers (e.g. DAP) account for both N and $\text{P}_2\text{O}_5$.
- Surplus nutrients resulting from discrete packaging are explicitly reported in `nutrient_surplus_kg`.

---

## 4. Verification Status of All Agronomic Rules

| Rule Identifier | Crop | Recommendation Method | Recommendation Type | Verification Status | Official Publication Citation | Production Enabled? |
|---|---|---|---|---|---|---|
| `TNAU_STCR_IPNS_RICE_001` | Rice | `STCR-IPNS` | `SOIL_SPECIFIC_STCR` | **`VERIFIED`** | TNAU Agriculture / STCR-IPNS Reference pp. 12–15 | **Yes** |
| `TNAU_STCR_IPNS_COTTON_001` | Cotton (lint) | `STCR-IPNS` | `SOIL_SPECIFIC_STCR` | **`VERIFIED`** | TNAU Cotton STCR Portal (Irugur / Pilamedu Series) | **Yes** |
| `TNAU_STCR_IPNS_MAIZE_001` | Maize | `STCR-IPNS` | `SOIL_SPECIFIC_STCR` | **`VERIFIED`** | TNAU Crop Production Guide 2020, p. 84 | **Yes** |
| `TNAU_STD_RICE_001` | Rice | `TNAU-SOIL-TEST` | `GENERAL_BLANKET` | **`VERIFIED`** | TNAU Soil Testing Services Rice Table | **Yes** (Rating Adjusted) |
| `TNAU_STD_BLACKGRAM_RF_001` | Blackgram | `TNAU-SOIL-TEST` | `GENERAL_BLANKET` | **`VERIFIED`** | TNAU CPG 2020 p. 64 / Pulses Guide | **Yes** (Fixed RDF 20:40:20) |
| `TNAU_BLANKET_GROUNDNUT_001` | Groundnut | `TNAU-BLANKET` | `GENERAL_BLANKET` | **`VERIFIED`** | TNAU CPG 2020 Oilseeds Section, p. 112 | **Yes** (Fixed RDF 25:50:75) |
| `TNAU_STD_SUGARCANE_001` | Sugarcane | `TNAU-BLANKET` | `GENERAL_BLANKET` | **`VERIFIED`** | TNAU CPG 2020 Commercial Crops, p. 150 | **Yes** (Fixed RDF 275:62.5:112.5) |
| `TNAU_STD_GROUNDNUT_001` | Groundnut | `TNAU-SOIL-TEST` | `SOIL_SPECIFIC_STCR` | **`PENDING_AGRONOMIC_VALIDATION`** | TNAU CPG 2020 p. 112 (Targeted Yield uncalibrated) | **No** (Blocked) |
| `TNAU_STCR_BANANA_001` | Banana | `STCR-IPNS` | `SOIL_SPECIFIC_STCR` | **`PENDING_VERIFICATION`** | Draft STCR Banana Report (Theni / Trichy) | **No** (Blocked) |
| `TNAU_DEPRECATED_RICE_000` | Rice | `TNAU-BLANKET` | `GENERAL_BLANKET` | **`UNSUPPORTED`** | Obsolete 1980 Blanket Dosing Guide | **No** (Blocked) |
| *Unregistered Crops* | E.g. Turmeric | N/A | N/A | **`UNSUPPORTED_CROP`** | None | **No** (Blocked) |
