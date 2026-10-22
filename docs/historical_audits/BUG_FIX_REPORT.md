# Master Bug Fix Report

**Project Title:** AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Date:** 2026-10-13  
**Status:** All Confirmed Bugs Resolved and Validated  

---

## 1. Summary of Confirmed Bugs & Resolution Status

| Bug ID | Component | Severity | Description | Status |
|---|---|---|---|---|
| **BUG-01** | Phase 5 / Phase 7 / Flutter UI | **High** | NPK Requirement JSON schema field mismatch (`n_req_kg_per_ha` vs `net_n_kg_per_ha`) causing zero values in UI and PDF reports | **FIXED** |
| **BUG-02** | Phase 6 / Phase 7 / Flutter UI | **High** | Fertilizer optimization product name key mismatch (`product_name` vs `name`) causing generic "Product" fallbacks | **FIXED** |
| **BUG-03** | Phase 6 Optimization | **Medium** | Whole-bag ceiling rounding without post-rounding nutrient satisfaction verification | **FIXED** |
| **BUG-04** | Phase 7 / Flutter Weather | **Medium** | Agro-weather API response key mismatch causing weather UI to fall back to hardcoded mock values | **FIXED** |
| **BUG-05** | Phase 3 Soil API Auth | **Medium** | Soil upload and confirmation endpoints rejected standard `Authorization: Bearer <token>` headers | **FIXED** |
| **BUG-06** | Flutter UI / Localization | **Medium** | Missing prompt-mandated failure messages in Tamil, English, and Hindi in `AppLocalizations` | **FIXED** |
| **BUG-07** | Flutter Login Screen | **Low** | Missing "Forgot Password" UI button and password recovery dialog | **FIXED** |
| **BUG-08** | PDF Generation Engine | **Medium** | ReportLab PDF generator failed when consuming live Phase 7 pipeline outputs due to schema keys | **FIXED** |

---

## 2. Detailed Bug Descriptions and Fixes

### BUG-01: Phase 5 NPK Schema Mismatch
- **Files Modified:**
  - `phase5_nutrient/models.py`
  - `phase5_nutrient/service.py`
  - `flutter_app/lib/screens/npk_requirement_screen.dart`
  - `flutter_app/lib/screens/recommendation_details_screen.dart`
  - `phase7_integration/extra_api.py`
- **Root Cause:**
  `phase5_nutrient` serialized its output with field names `n_req_kg_per_ha`, `p2o5_req_kg_per_ha`, `k2o_req_kg_per_ha`, `total_n_req_kg`, `total_p2o5_req_kg`, and `total_k2o_req_kg`. However, the Flutter frontend screens and the ReportLab PDF export function looked for `net_n_kg_per_ha`, `net_p2o5_kg_per_ha`, `net_k2o_kg_per_ha`, `total_farm_n_kg`, `total_farm_p2o5_kg`, and `total_farm_k2o_kg`. As a result, the farmer saw `0.0 kg/ha` on the screen and generated PDFs displayed `0 kg` nutrient requirements.
- **Fix Applied:**
  1. Added alias fields (`net_n_kg_per_ha`, `net_p2o5_kg_per_ha`, `net_k2o_kg_per_ha`, `total_farm_n_kg`, `total_farm_p2o5_kg`, `total_farm_k2o_kg`, and `calculation_method`) to `phase5_nutrient/models.py`.
  2. Populated these aliases directly in `phase5_nutrient/service.py` alongside the canonical fields, preserving 100% backward compatibility with existing tests.
  3. Updated Flutter screens to support both key formats via defensive fallback accessors (`data['net_n_kg_per_ha'] ?? data['n_req_kg_per_ha']`).
  4. Updated `extra_api.py` to extract nutrients regardless of which key naming was used.

---

### BUG-02: Phase 6 Fertilizer Product Name Key Mismatch
- **Files Modified:**
  - `phase6_fertilizer/models.py`
  - `phase6_fertilizer/service.py`
  - `flutter_app/lib/screens/final_recommendation_screen.dart`
  - `flutter_app/lib/screens/recommendation_details_screen.dart`
  - `phase7_integration/extra_api.py`
- **Root Cause:**
  `phase6_fertilizer` serialized each recommended fertilizer using `product_name`, but Flutter screens and PDF generation looked for `name`. When the map lookup failed, the UI defaulted to generic placeholders or empty labels.
- **Fix Applied:**
  1. Added optional `name: Optional[str] = None` property to `FertilizerRecommendationItem` in `phase6_fertilizer/models.py`.
  2. Populated `name = product.product_name` in `phase6_fertilizer/service.py`.
  3. Added dual-key fallback resolution `item['name'] ?? item['product_name'] ?? 'Fertilizer'` across Flutter widgets and PDF generation.

---

### BUG-03: Whole-Bag LP Optimizer Post-Rounding Validation
- **Files Modified:**
  - `phase6_fertilizer/service.py`
- **Root Cause:**
  `scipy.optimize.linprog` with the HiGHS solver solves continuous linear programming. When fractional kilograms were converted to whole 50 kg (or 45 kg Urea) bags via ceiling rounding (`ceil(kg / bag_weight)`), there was no explicit validation step verifying that the resulting bag combination satisfied all nutrient bounds ($A_{ub} x \ge b_{ub}$) without exceeding upper safety tolerances. Additionally, uninitialized variables could cause `UnboundLocalError` in edge infeasible cases.
- **Fix Applied:**
  1. Initialized `total_cost = 0.0`, `products_used = []`, and `supply = {'N': 0.0, 'P2O5': 0.0, 'K2O': 0.0}` at function scope.
  2. Implemented strict post-rounding validation recalculating actual nutrients supplied by whole bags:
     $$\text{supplied}_N = \sum \text{bags}_i \times \text{bag\_size}_i \times \%N_i$$
  3. Verified that $\text{supplied} \ge \text{target} - \epsilon$, guaranteeing that whole-bag solutions satisfy the farmer's agronomic needs before being presented as valid recommendations.

---

### BUG-04: Agro-Weather API Response Key Mismatch
- **Files Modified:**
  - `phase7_integration/weather.py`
  - `flutter_app/lib/screens/weather_screen.dart`
- **Root Cause:**
  `phase7_integration/weather.py` returned keys `condition`, `guidance_status`, and `advisory_en`. However, `weather_screen.dart` parsed `current_condition`, `risk_level`, and `actionable_advice`. This caused the Flutter weather screen to catch a null lookup and fall back to hardcoded mock weather values.
- **Fix Applied:**
  1. Enhanced `weather.py` to return both canonical and frontend-friendly alias fields: `current_condition`, `risk_level`, `actionable_advice`, `temperature_c`, and `rainfall_probability_pct`.
  2. Updated `weather_screen.dart` to handle dynamic language switching so Tamil and Hindi farmers receive advisory text in their preferred language.

---

### BUG-05: Phase 3 Soil Module Authentication Guard
- **Files Modified:**
  - `phase3_soil/api.py`
- **Root Cause:**
  The endpoint dependency `_guard()` in `phase3_soil/api.py` only checked for the custom header `X-Farmer-Id`. When requests came from the Flutter client sending JWT tokens via `Authorization: Bearer <token>`, the soil endpoints raised HTTP 401 Unauthorized.
- **Fix Applied:**
  Updated `_guard(x_farmer_id: Optional[str] = Header(None), authorization: Optional[str] = Header(None))` to inspect the `Authorization` header. If a valid `Bearer <token>` is present, it extracts the authenticated user ID and permits the operation.

---

### BUG-06: Missing Localized Failure Messages
- **Files Modified:**
  - `flutter_app/lib/l10n/app_localizations.dart`
- **Root Cause:**
  Seven required failure messages specified in the master prompt (Upload failure, OCR failure, Missing required values, Unsupported crop, Optimization failure, Weather failure, Yield prediction failure) were missing from the Flutter localization dictionary, leading to unhandled errors or raw backend stack traces in some failure states.
- **Fix Applied:**
  Added localized strings and getters in English (`en`), Tamil (`ta`), and Hindi (`hi`):
  - `uploadFailure`
  - `ocrFailure`
  - `missingSoilValues`
  - `unsupportedCrop`
  - `optimizationFailure`
  - `weatherFailure`
  - `yieldFailure`

---

### BUG-07: Missing "Forgot Password" Flow
- **Files Modified:**
  - `flutter_app/lib/screens/login_screen.dart`
- **Root Cause:**
  The login screen lacked an entry point for farmers who forgot their password, hindering multi-user usability.
- **Fix Applied:**
  Added a clean "Forgot Password?" text button on `login_screen.dart` with an accessible dialog prompting for phone/email and providing recovery guidance.

---

### BUG-08: ReportLab PDF Generation Schema Ingestion
- **Files Modified:**
  - `phase7_integration/extra_api.py`
- **Root Cause:**
  `extra_api.py` PDF generation logic assumed a single rigid schema naming. When combined full-recommendation JSON payloads were passed, missing keys caused the PDF generator to fail or omit nutrient and fertilizer sections.
- **Fix Applied:**
  Updated the PDF generation dictionary parsers to safely inspect both canonical and aliased keys for soil, NPK, fertilizer, and weather sections. Added end-to-end unit test `test_pdf_report_generation_from_full_pipeline_payload` to verify PDF generation directly from live orchestrator output.
