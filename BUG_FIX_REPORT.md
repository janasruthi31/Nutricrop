# AgroWise AI — Unified Fertilizer Recommendation Bug Fix Report

**Date:** 2026-10-29  
**System:** AgroWise AI (Sustainable Fertilizer Usage Optimizer for Higher Crop Yield)  
**Author:** Senior Agricultural Software & AI Systems Engineer

---

## 1. Executive Summary

Farmers using AgroWise AI previously faced a fragmented and error-prone recommendation workflow:
1. They had to manually choose between three competing, confusing technical recommendation modes (*Soil Health Card Printed Dose*, *General Blanket TNAU*, and *Soil-Specific STCR*).
2. Selecting *STCR* or *Soil Health Card* frequently resulted in the **Zero-Value Bug**: 0 kg Nitrogen, 0 kg Phosphorus, 0 kg Potassium, 0 fertilizer bags, and ₹0 total cost, falsely indicating that 0 fertilizer was required when in reality calculation had failed or rule lookup had returned empty.
3. Multi-nutrient fertilizers such as DAP (18% N, 46% P₂O₅) lacked unified end-to-end accounting.
4. Missing dealer prices were converted to ₹0 instead of being explicitly flagged as `UNAVAILABLE`.

We have successfully engineered and verified **One Accurate, Unified Fertilizer Recommendation System** across the FastAPI backend and Flutter frontend without rebuilding the stack or breaking existing working features.

---

## 2. Five Confirmed High-Priority Issues & Root Cause Resolutions

| Bug ID | Component | Root Cause | Fix Implemented | Status |
|---|---|---|---|---|
| **BUG-001** | Frontend UI Fallbacks | In `npk_requirement_screen.dart` and `final_recommendation_screen.dart`, null or uncalculated nutrient fields defaulted to `?? 0.0`. When a rule was not verified (`NO_VERIFIED_RULE`), the UI fell through to render 0 kg N, 0 kg P, 0 kg K, and ₹0. | Rewrote UI logic with explicit `isSuccess` checks. When a calculation is unavailable or uncalibrated, an informative agricultural safety warning card is displayed. 0.0 kg nutrient cards and ₹0 costs are never displayed for failed calculations. | **RESOLVED & VERIFIED** |
| **BUG-002** | STCR Rule Status & Selector Conflict | All STCR rules (`TNAU_STCR_IPNS_RICE_001`, `COTTON_001`, `MAIZE_001`) in `agronomy/database.py` were disabled (`is_enabled: false`) due to discrepancy with TNAU bulletins. The UI manual selector forced STCR mode, yielding empty results and returning `NO_VERIFIED_RULE`. | Replaced the manual 3-mode selector with an automated, 3-tier cascade: Priority 1 (Validated STCR-IPNS) -> Priority 2 (Verified TNAU Soil-Test Rating Adjusted) -> Priority 3 (Verified TNAU Blanket). If no calibrated rule exists, it cascades safely or reports `NO_VALIDATED_RECOMMENDATION`. | **RESOLVED & VERIFIED** |
| **BUG-003** | Soil Health Card Mode Fallthrough | When `recommendation_mode == "SOIL_HEALTH_CARD"`, if a card had chemical test values (N, P, K) but no printed dosage table, `Phase5NutrientService` aborted with `MISSING_INPUTS`, leading to 0 values in UI. | In `phase5_nutrient/service.py`, added automatic fallthrough: if printed rates are absent on the card but laboratory test values are present, the engine automatically calculates requirements from measured soil values instead of aborting. | **RESOLVED & VERIFIED** |
| **BUG-004** | Groundnut & Blanket Rule Exclusion | `AgronomyService.select_rule()` previously skipped blanket rules like `TNAU_BLANKET_GROUNDNUT_001` if `recommendation_type` was unspecified or unified. | Removed the arbitrary blanket filter in `agronomy/service.py` so that verified blanket rules are available in the unified cascade when crop-response rules are not applicable. | **RESOLVED & VERIFIED** |
| **BUG-005** | Silent ₹0 Display for Missing Prices | Missing dealer prices or unpriced fertilizers displayed ₹0 instead of informing the farmer that costs were unavailable. | Implemented `total_cost_status: "AVAILABLE" | "UNAVAILABLE"` across backend and frontend. If any price is uncalibrated or missing, the UI clearly displays "Cost Unavailable" with an explanation, preserving accurate kg quantities. | **RESOLVED & VERIFIED** |

---

## 3. Architecture & Unified Cascade

The unified recommendation system operates under a strict, documented 3-tier agronomic priority cascade:

```
Farmer Input (Crop, Farm Area, Soil Test Values, District, Variety, Yield Target)
                                   │
                                   ▼
             UnifiedFertilizerRecommendationService (Phase 7)
                                   │
                ┌──────────────────┴──────────────────┐
                ▼                                     ▼
      AgronomyService (Rules)               Phase 3 Soil Extraction
                │                                     │
                ▼                                     ▼
        Cascade Evaluation                   Validated Soil Parameters
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
Priority 1  Priority 2  Priority 3
(STCR-IPNS) (TNAU Rating) (TNAU Blanket)
    │           │           │
    └───────────┼───────────┘
                │ If no verified rule matches:
                │ Return NO_VALIDATED_RECOMMENDATION
                ▼
        Phase 5 Nutrient Requirement Service
        • Deduct FYM / organic contributions
        • Calculate kg/ha & total farm kg (1 ha = 2.47105 ac)
        • Secondary & micronutrient advisory (Zn, S, B)
                │
                ▼
        Phase 6 Multi-Nutrient Fertilizer Optimizer
        • Solve linear/integer programming for least-cost commercial bags
        • DAP multi-nutrient accounting (18% N, 46% P₂O₅) without double-counting
        • Whole bag constraint (45kg Urea, 50kg DAP/MOP)
        • Mark total_cost_status as AVAILABLE or UNAVAILABLE
                │
                ▼
        Farmer-Facing Unified UI (Flutter)
        • Single recommendation display with Priority Tier badge
        • "Why this recommendation?" agronomic explanation
        • Full citation & rule source
        • Clear safety warning if inputs or rules are missing (No ₹0, No 0 kg)
```

---

## 4. Modified & Added Files

### Backend (`Python / FastAPI`)
1. [`agronomy/models.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/agronomy/models.py):
   - Added `priority_tier: Optional[int]`, `rule_priority: Optional[str]`, and `selection_reason: Optional[str]` to `RuleSelectionResponse`.
2. [`agronomy/service.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/agronomy/service.py):
   - Removed blanket rule suppression for unified recommendation mode.
   - Assigned priority tiers (Tier 1 for STCR, Tier 2 for TNAU Soil-Test, Tier 3 for TNAU Blanket), priorities, and selection reasons.
3. [`phase5_nutrient/service.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/service.py):
   - Added automatic calculation fallback when physical Soil Health Card recommendation columns are left blank by testing labs.
   - Propagated priority tier, selection reason, and rule metadata into `nutrient_requirements`.
4. [`phase7_integration/service.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase7_integration/service.py):
   - Implemented `UnifiedFertilizerRecommendationService` coordinating the unified cascade.
   - Attached `unified_recommendation` block and `total_cost_status: "AVAILABLE" | "UNAVAILABLE"` to response payloads.
5. [`tests/test_unified_fertilizer_recommendation.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/tests/test_unified_fertilizer_recommendation.py):
   - Comprehensive test suite covering Tests A through H (Rice TNAU soil-test, Groundnut blanket, STCR requirements, unsupported crops, missing soil data, unit conversions, DAP multi-nutrient accounting, missing price safety, regression).

### Frontend (`Flutter / Dart`)
1. [`flutter_app/lib/screens/npk_requirement_screen.dart`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/flutter_app/lib/screens/npk_requirement_screen.dart):
   - Removed manual 3-mode selector buttons.
   - Automated unified recommendation request to backend.
   - Replaced zero-default fallbacks with informative, safety-first status cards for missing inputs, unverified rules, or method incompatibilities.
   - Rendered Unified Recommendation Header with Priority Tier badge (Priority 1, 2, or 3), explanation ("Why this recommendation?"), rule ID, and source citation.
   - Displayed farm nutrient requirements (rates per acre & per ha, and farm totals).
2. [`flutter_app/lib/screens/final_recommendation_screen.dart`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/flutter_app/lib/screens/final_recommendation_screen.dart):
   - Consolidated UI into a single primary recommendation screen.
   - Implemented "Cost Unavailable" banner when dealer prices are missing (eliminated misleading ₹0 outputs).
   - Added Farm Nutrient Requirements summary card.
   - Responsive layout adjustments (wrapped text, `Flexible`, and `Expanded`) preventing RenderFlex overflow.
3. [`flutter_app/lib/widgets/common_widgets.dart`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/flutter_app/lib/widgets/common_widgets.dart):
   - `FertilizerProductCard`: Replaced ₹0 with "Price Unavailable" when price or total cost is zero/uncalibrated.
4. [`flutter_app/test/screens_flow_test.dart`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/flutter_app/test/screens_flow_test.dart):
   - Added widget tests verifying Unified Priority 2 badge, reason, farm nutrient requirements, and price unavailable handling.

---

## 5. Verification & Test Evidence

### Backend Test Results
Command executed:
```powershell
pytest tests/test_unified_fertilizer_recommendation.py tests/test_nutrient_equations_audit.py tests/test_final_equation_audit_safety.py tests/test_c_d_e_verification.py -q
```
Result:
```
47 passed in 12.95s (100% PASS)
```

Key verified test suites:
- **Test A:** Existing working soil-test recommendation (`TNAU_STD_RICE_001`) passes and calculates accurate fertilizer bags.
- **Test B:** Valid TNAU rule selection applies documented ratings and conversions.
- **Test C:** Valid STCR-IPNS rule requires full calibration inputs (Olsen-P, series, target yield).
- **Test D:** Unsupported crop (`DragonFruit`) returns explicit `NO_VERIFIED_RULE` / `UNSUPPORTED_CROP` status without fabricated doses.
- **Test E:** Missing soil data returns `MISSING_INPUTS` with exact missing parameter list.
- **Test F:** Unit conversion (1 acre = 0.404686 ha; rates vs farm totals) verified.
- **Test G:** Fertilizer optimizer accounts for DAP nitrogen (18%) and phosphate (46%) without double-counting.
- **Test H:** Missing prices report `total_cost_status == 'UNAVAILABLE'` rather than ₹0.

### Frontend Test Results
Command executed:
```powershell
flutter analyze
```
Result:
```
No issues found! (ran in 8.2s)
```

Command executed:
```powershell
flutter test
```
Result:
```
All 27 tests passed!
```

---

## 6. Honest Limitations & Agronomic Notes

1. **STCR Rules Calibration Status:**
   - The STCR equations in `agronomy/database.py` remain marked as `UNSUPPORTED` (`is_enabled: false`) until official TNAU bulletin coefficients are verified and signed off by an agronomy expert.
   - When a farmer requests a recommendation for Rice, Maize, or Cotton, the unified cascade safely and automatically uses the verified TNAU Soil-Test Based rating rule (`TNAU_STD_RICE_001` - Priority 2) instead of failing or returning 0.
2. **Dealer Prices:**
   - Fertilizer prices fluctuate across districts and private retailers. The local dealer price override tool in `FinalRecommendationScreen` allows farmers to enter their exact local bag prices to recalculate the optimal plan instantly.
