# AgroWise AI (NutriCrop) — Bug Register & Architectural Audit

**Date:** October 29, 2026  
**Scope:** Unified Fertilizer Recommendation System Audit (Root Causes of Zero-Value Output, 3-Method Disconnect, and Rule Selection Failures)  
**Standard:** Tamil Nadu Agricultural University (TNAU) Agronomic Guidelines & ICAR-AICRP (STCR)

---

## 1. Executive Audit Summary

The existing prototype separated recommendation generation into three distinct paths:
1. **Soil Health Card (Printed Dose)**
2. **General Blanket (TNAU Verified Fixed RDF)**
3. **Soil-Specific STCR (Targeted Yield Equation / Calculated Agronomic)**

The farmer was forced to manually select among these methods via a 3-way toggle. When the farmer selected **TNAU Blanket** or **STCR-IPNS**, the system frequently displayed:
- Nitrogen: `0.0 kg`
- Phosphorus: `0.0 kg`
- Potassium: `0.0 kg`
- Recommended Products: `None`
- Estimated Fertilizer Cost: `₹0`

### Primary Confirmed Root Cause
Zero-value results did **not** represent a genuine agronomic recommendation of zero fertilizer. Instead, they arose because:
1. All STCR-IPNS rules (`TNAU_STCR_IPNS_RICE_001`, `TNAU_STCR_IPNS_COTTON_001`, `TNAU_STCR_IPNS_MAIZE_001`) are disabled (`is_enabled: false`, `verification_status: "UNSUPPORTED"`) due to scientific discrepancies identified in the official equation audit.
2. When the farmer selected "Soil-Specific STCR", the backend filtered exclusively for STCR rules (`if is_stcr_req and not rule_is_stcr: continue`), found no verified rules, and returned status `NO_VERIFIED_RULE` with `null` nutrient values and `0.0` cost.
3. In `SOIL_HEALTH_CARD` mode, if the uploaded soil card did not contain a printed recommendation table, `NutrientCalculationService` failed with `MISSING_INPUTS` (`missing_inputs: ["printed_recommendation"]`).
4. The Flutter UI (`npk_requirement_screen.dart` and `final_recommendation_screen.dart`) fell back to `?? 0.0` on all numeric fields without checking whether `status == "SUCCESS"`, masking the failure as a valid recommendation of 0 kg at ₹0 cost.
5. In addition, when valid soil test values were available, the system did not automatically fall back to the highest available verified recommendation tier (Priority 1: Validated STCR -> Priority 2: Verified TNAU Soil Test -> Priority 3: Verified TNAU Blanket).

---

## 2. Five Highest-Priority Confirmed Issues

### Issue 1: Farmer-Facing 3-Method Toggle Forced Farmer to Guess and Defaulted to Unsupported Rules
- **Severity:** Critical
- **Affected Files:**
  - `flutter_app/lib/screens/npk_requirement_screen.dart` (lines 27, 232–234, 744–830)
  - `agronomy/service.py` (lines 58–61, 121–125)
  - `phase7_integration/service.py` (lines 53–54, 98–105)
- **Reproduction Steps:**
  1. Complete soil test verification for Rice (e.g. N=220, P=16, K=190 kg/ha).
  2. Navigate to `NpkRequirementScreen`.
  3. The default or selected mode is `CALCULATED_AGRONOMIC` (`SOIL_SPECIFIC_STCR`).
  4. The request sends `recommendation_type: 'SOIL_SPECIFIC_STCR'`.
  5. The rule selection engine filters out all non-STCR rules. Since STCR Rice rule is disabled, no rule matches.
- **Root Cause:**
  `RuleSelectionService` enforces a strict mode filter:
  ```python
  if is_stcr_req and not rule_is_stcr:
      continue
  ```
  Because `TNAU_STCR_IPNS_RICE_001` has `is_enabled: false` and `verification_status: UNSUPPORTED`, zero rules match. The engine returns `NO_VERIFIED_RULE`, preventing the system from using the verified, active `TNAU_STD_RICE_001` (TNAU Soil-Test schedule).
- **Proposed Architectural Fix:**
  - Deprecate farmer-facing method selection. The farmer always enters field data; the backend determines the optimal rule via a unified selection cascade:
    1. **Priority 1:** Applicable validated STCR-IPNS rule.
    2. **Priority 2:** Applicable verified TNAU Soil-Test-Based rule (e.g., `TNAU_STD_RICE_001`).
    3. **Priority 3:** Applicable verified TNAU Blanket rule (e.g., `TNAU_BLANKET_GROUNDNUT_001`, `TNAU_STD_SUGARCANE_001`).
    4. **No Rule:** Return explicit `NO_VALIDATED_RECOMMENDATION` with clear actionable reasons.
  - Remove the 3-mode tab toggle in `npk_requirement_screen.dart`.
- **Test:** `test_unified_rule_selection_rice_fallback_to_soil_test`

---

### Issue 2: Zero-Value Display and Failure Concealment in the Flutter UI
- **Severity:** Critical
- **Affected Files:**
  - `flutter_app/lib/screens/npk_requirement_screen.dart` (lines 692–703)
  - `flutter_app/lib/screens/final_recommendation_screen.dart` (lines 100–120)
  - `phase7_integration/service.py` (lines 329–341)
- **Reproduction Steps:**
  1. Submit a recommendation request with an unsupported crop (e.g. `DragonFruit`) or missing required input.
  2. The backend responds with status `UNSUPPORTED_CROP` or `MISSING_INPUTS` and `total_cost_inr: 0.0`.
  3. The UI extracts `netNHa = (p5['n_req_kg_per_ha'] as num?)?.toDouble() ?? 0.0` and renders nutrient cards showing `0.0 kg N`, `0.0 kg P`, `0.0 kg K`, and `Farm Total: 0.0 kg`.
  4. The cost displays `₹0`.
- **Root Cause:**
  The Flutter UI treats `null` or missing response properties as `0.0` using null-coalescing operators without checking `response['status']` or `is_verified`. It renders valid-looking fertilizer cards with zero quantities, deceiving the farmer into believing their soil requires zero fertilizer.
- **Proposed Architectural Fix:**
  - Refactor UI to inspect `_recommendationResponse['status']` and `_recommendationResponse['is_verified']`.
  - When status is not `SUCCESS` / `VALIDATED_RECOMMENDATION`:
    - Do NOT render 0.0 kg nutrient cards or ₹0 cost.
    - Render a prominent, actionable status banner explaining exactly why a recommendation could not be calculated (e.g., missing soil phosphorus method, unsupported crop, or pending calibration).
    - Distinguish a true calculated agronomic zero (e.g., soil already has excessive nutrient supply clamped at 0) from an uncalculated/failed state using the backend's explicit `status` and `clamping_notes`.
- **Test:** `test_ui_displays_error_state_on_unsupported_crop_without_zeroes`

---

### Issue 3: Soil Health Card Mode Fails Completely When Card Has No Printed Recommendation Table
- **Severity:** High
- **Affected Files:**
  - `phase5_nutrient/service.py` (lines 556–573)
  - `phase7_integration/service.py` (lines 98–105)
- **Reproduction Steps:**
  1. Upload a soil report PDF that contains laboratory chemical test values (N, P, K, pH, EC) but has an empty or unprinted fertilizer recommendation section.
  2. Select `SOIL_HEALTH_CARD` mode.
  3. Backend returns `status: "MISSING_INPUTS"` with `missing_inputs: ["printed_recommendation"]`.
  4. Result is 0 kg at ₹0.
- **Root Cause:**
  `NutrientCalculationService` treated `SOIL_HEALTH_CARD` as an isolated mode that strictly copies printed values. If printed values were absent, it aborted with `MISSING_INPUTS` even though accurate laboratory soil values were present.
- **Proposed Architectural Fix:**
  - In the unified workflow:
    - If printed recommendations are present, parse them for comparison and verification.
    - If printed recommendations are absent, smoothly and automatically calculate the nutrient requirement from the measured soil test values using Priority 2 (TNAU Soil-Test-Based) without failing or requiring farmer intervention.
- **Test:** `test_soil_report_without_printed_rec_calculates_from_soil_values`

---

### Issue 4: Incompatible Phosphorus Test Method or Missing Soil Input Halts Calculation Without Fallback or Guidance
- **Severity:** High
- **Affected Files:**
  - `agronomy/service.py` (lines 157–163)
  - `phase5_nutrient/service.py` (lines 845–889)
  - `flutter_app/lib/screens/verify_screen.dart` (lines 80–120)
- **Reproduction Steps:**
  1. Upload a soil report with Bray-1 phosphorus for a crop whose STCR rule only supports Olsen-P.
  2. The calculation aborts with `INCOMPATIBLE_SOIL_TEST_METHOD`.
  3. No recommendation or actionable guidance is provided; UI displays zeroes.
- **Root Cause:**
  Bray-to-Olsen conversion is agronomically prohibited by TNAU/ICAR without site-specific calibration. However, when an STCR rule rejects Bray-P, the system did not automatically fall back to the TNAU Standard Recommendation (which supports both Olsen and Bray rating bands via `classify('phosphorus', val, 'kg/ha', 'Bray')`).
- **Proposed Architectural Fix:**
  - When Bray-P is supplied:
    - If STCR rule is incompatible, log a warning and fall back to Priority 2 (TNAU Soil-Test-Based recommendation with Bray rating classification).
    - In `verify_screen.dart`, allow the farmer to explicitly confirm whether their test method is Olsen or Bray, defaulting to Olsen for alkaline/neutral soils and Bray for acidic soils per TNAU standards.
- **Test:** `test_bray_phosphorus_falls_back_to_verified_tnau_soil_test`

---

### Issue 5: Missing Traceability Metadata & Explanation on Recommendation Screens
- **Severity:** Medium
- **Affected Files:**
  - `flutter_app/lib/screens/npk_requirement_screen.dart`
  - `flutter_app/lib/screens/final_recommendation_screen.dart`
  - `phase7_integration/service.py`
- **Reproduction Steps:**
  1. Observe the result on `final_recommendation_screen.dart`.
  2. The explanation text is generic and does not state whether a Soil-Test equation, an STCR equation, or a Blanket schedule was used, nor does it cite the source publication or explain the basis of calculation.
- **Root Cause:**
  The API response explanation field (`derivation_explanation`, `source_title`, `rule_id`, `calculation_method`) was partially populated but not consistently surfaced in the final recommendation screen.
- **Proposed Architectural Fix:**
  - Return consistent unified recommendation metadata:
    - `rule_id`: Identifier of the selected rule.
    - `rule_priority`: Priority tier applied (STCR-IPNS, TNAU Soil-Test, or TNAU Blanket).
    - `source_title`: Official publication reference (e.g. *TNAU Crop Production Guide 2020*).
    - `selection_reason`: Transparent explanation of why this specific rule was selected.
    - `application_schedule`: Stage-by-stage split application advice.
  - Surface this clearly in `NpkRequirementScreen` and `FinalRecommendationScreen`.
- **Test:** `test_recommendation_response_traceability_metadata`

---

## 3. Implementation Plan Summary

1. **Backend Orchestration:** Build `UnifiedFertilizerRecommendationService` (or refactor `FullRecommendationService`) with the strict 3-tier selection priority and zero-value prevention.
2. **Registry & Rule Refinement:** Ensure all verified rules (`TNAU_STD_RICE_001`, `TNAU_STD_BLACKGRAM_RF_001`, `TNAU_BLANKET_GROUNDNUT_001`, `TNAU_STD_SUGARCANE_001`) have clean priority tags and full metadata.
3. **Frontend Unified Screen:** Refactor `npk_requirement_screen.dart` and `final_recommendation_screen.dart`:
   - Remove the 3-mode selector toggle.
   - Display the single unified recommendation with source traceability, formula breakdown, product quantities, and split application timing.
   - Replace any `?? 0.0` fallbacks with genuine status-driven error/warning states.
4. **Testing Suite:**
   - Execute Test A (Existing working Soil Test-Based).
   - Execute Test B (Valid TNAU rule).
   - Execute Test C (STCR-IPNS validation / safety check).
   - Execute Test D (No matching rule -> `NO_VALIDATED_RECOMMENDATION`).
   - Execute Test E (Missing soil data -> `NEEDS_INPUT`).
   - Execute Test F (Unit conversions & farm totals).
   - Execute Test G (Fertilizer optimizer integrity).
   - Execute Test H (Frontend flutter test regression).
