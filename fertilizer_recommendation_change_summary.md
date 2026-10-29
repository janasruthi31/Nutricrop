# AgroWise AI (Nutricrop) — Fertilizer Recommendation Module Change Summary

**Date:** October 23, 2026  
**Auditor / Implementer:** Antigravity AI  
**Scope:** Upgrade ONLY the Fertilizer Recommendation Module (Soil Test Interpretation, Previous Crop Biological Credits, Historical Fertilizer Carryover, Product Optimization, Whole Bag & Loose Packaging, and Master Integration).

---

## 1. Summary of Changes by File

| Module / Component | File Path | Key Changes Made |
| :--- | :--- | :--- |
| **Database Migration** | `phase3_soil/db.py` | • Added backward-compatible SQLite migration in `init_db()` for table `farmer_fertilizer_history` adding columns: `farm_id`, `fertilizer_grade`, `category`, `bag_weight_kg`, `field_area`, `field_area_unit`, `application_method`, `n_pct`, `p2o5_pct`, `k2o_pct`. Existing rows preserved with zero regression. |
| **Nutrient Schemas** | `phase5_nutrient/models.py` | • Expanded `PreviousFertilizerItem` to model all required agronomic inputs: `product_grade`, `category`, `bag_weight_kg`, `application_date`, `crop_season`, `field_area`, `field_area_unit`, `application_method`, `n_pct`, `p2o5_pct`, `k2o_pct`, and `notes`. |
| **Nutrient Calculation Engine** | `phase5_nutrient/service.py` | • **Dynamic Fertilizer Residual Carryover:** Dynamically queries commercial catalog, handles custom NPKS grades (e.g., 18-46-0, 20-20-0, 10-26-26), performs full unit conversion (`g`, `kg`, `tonne`, `bags`, `kg/acre`, `kg/ha`), normalizes by previous application field area, enforces 0% tropical synthetic N carryover, 15% P₂O₅ residual (≤6 months), 10% K₂O residual (≤6 months), and gradual organic manure mineralization.<br>• **Previous Crop Biological Credits:** Legume N credits (15–20 kg N/ha) apply to succeeding cereal/exhaustive crops per TNAU CPG 2020 / ICAR-STCR.<br>• Maintained standard lowercase response key contracts (`{"n": ..., "p2o5": ..., "k2o": ...}`) across all nutrient credit dictionaries. |
| **Fertilizer Optimizer Models** | `phase6_fertilizer/models.py` | • Added `whole_bags` (integer bags) and `loose_kg` (fractional quantities in kg) to `FertilizerProductRecommendation`.<br>• Added `nutrient_contributions` per product, `selection_rationale`, `nutrient_deficit_kg`, `has_deficit`, `agronomic_rule_source`, and `optimizer_rationale` to `FertilizerOptimizationResponse`. |
| **Fertilizer Optimizer Service** | `phase6_fertilizer/service.py` | • Enhanced optimizer to calculate exact integer bag counts and loose kg per product based on configurable bag weights (e.g., Urea 45 kg, DAP/MOP 50 kg).<br>• Recalculated exact supplied nutrients, deficits, and surpluses directly from the physical packaging formulation.<br>• Emitted clear explanations for why each commercial product was selected and warned when non-zero deficits or surpluses occur. |
| **Master Orchestrator** | `phase7_integration/service.py` | • Added auto-query of authenticated farmer's stored fertilizer history from SQLite when not explicitly passed in payload.<br>• Added structured `soil_test_summary` and `previous_history_considered` sections to final API response.<br>• Calibrated crop-specific target yield fallbacks (Cotton: 2.5 t/ha, Pulses: 1.0 t/ha, Sugarcane: 120 t/ha, Rice/Maize: 6.0 t/ha).<br>• Ensured `district_yield_prediction` always contains `scope` and `disclaimer` benchmark flags.<br>• Guaranteed ML yield prediction remains strictly decoupled and advisory. |
| **Farmer History API** | `phase7_integration/extra_api.py` | • Upgraded `add_fertilizer_history()` endpoint to accept and persist all new fields (`fertilizer_grade`, `category`, `bag_weight_kg`, `field_area`, `field_area_unit`, `application_method`, `n_pct`, `p2o5_pct`, `k2o_pct`) to the database. |
| **Agronomic Rules Data** | `data/agronomy/tnau_stcr_rules.json` | • Aligned verification status of calibrated TNAU rules (`TNAU_STCR_IPNS_RICE_001`, `TNAU_STCR_IPNS_COTTON_001`, `TNAU_STCR_IPNS_MAIZE_001`, `TNAU_STD_RICE_001`, `TNAU_STD_BLACKGRAM_RF_001`, `TNAU_BLANKET_GROUNDNUT_001`, `TNAU_STD_SUGARCANE_001`) to `"VERIFIED"` per `AGRONOMIC_RULE_SOURCES.md`. Unverified equations remain `"PENDING_AGRONOMIC_VALIDATION"`. |
| **Automated Test Suite** | `tests/test_fertilizer_recommendation_upgrade.py` | • Implemented 19 comprehensive test cases covering every requirement of the master prompt. |

---

## 2. Strict Scope Adherence

The following components were **strictly preserved** without redesign or modification:
- **Flutter UI Architecture:** No Flutter screens, widgets, or navigation files were changed.
- **Soil Report OCR:** Extraction pipelines, prompt templates, and confirmed report workflows remain intact.
- **Authentication & Farmer Isolation:** JWT verification and farmer data segregation remain strictly enforced.
- **Weather Integration:** Weather APIs and advisory timing remain unchanged.
- **ML Crop Yield Prediction:** Model training scripts, pickled estimators, and prediction logic remain unchanged; yield prediction remains strictly decoupled from the fertilizer dose.

---

## 3. Compatibility Considerations

1. **Database Schema:**
   - The SQLite migration dynamically adds new columns via `ALTER TABLE farmer_fertilizer_history ADD COLUMN ...` only when missing. Existing rows without new columns remain completely valid.
2. **API Payload Backward Compatibility:**
   - All newly added request fields in `NutrientCalculationRequest` and `PreviousFertilizerItem` are optional with sensible defaults.
   - Older clients sending legacy payloads with only `product`, `quantity`, `unit`, and `months_ago` continue to function seamlessly.
3. **Response Key Stability:**
   - Both lowercase dictionary formats (`{"n": ..., "p2o5": ..., "k2o": ...}`) and uppercase breakdown dictionaries (`{"N": ..., "P2O5": ..., "K2O": ...}`) are supported across Phase 5 and Phase 7 responses, ensuring complete compatibility with existing frontend decoders and backend tests.

---

## 4. Tests Executed and Actual Outcomes

All tests were executed against the live Python 3.11 virtual environment using `pytest`:

### Command 1: Full Upgrade Test Suite (19 Master Cases)
```powershell
.\venv\Scripts\pytest -q tests/test_fertilizer_recommendation_upgrade.py
```
**Outcome:**
`19 passed in 4.39s` (100% pass rate)

| Case # | Description | Result |
| :---: | :--- | :---: |
| **Case 1** | Valid confirmed soil report and supported crop (Rice STCR IPNS) | **PASS** |
| **Case 2** | Soil-test value variations producing consistent STCR nutrient changes | **PASS** |
| **Case 3** | Different current crops (Rice, Cotton, Maize) selecting verified rules | **PASS** |
| **Case 4** | Farm area scaling total fertilizer quantities and cost proportionally | **PASS** |
| **Case 5** | Previous crop history affecting results only where supported (legume biological N credit) | **PASS** |
| **Case 6** | Previous fertilizer history with multiple products, custom bag weights, and elapsed dates | **PASS** |
| **Case 7** | Missing previous crop or fertilizer history handled without fabricated values | **PASS** |
| **Case 8** | Missing, unreadable, or invalid soil values triggering validation errors | **PASS** |
| **Case 9** | Incorrect units and bag-size conversions (e.g. 45 kg Urea vs 50 kg DAP) | **PASS** |
| **Case 10** | Multi-nutrient fertilizer contributions (DAP supplying N and P₂O₅) | **PASS** |
| **Case 11** | Organic manure (FYM) credits under STCR IPNS method | **PASS** |
| **Case 12** | Nutrient surplus and deficit reporting | **PASS** |
| **Case 13** | Whole-bag rounding and loose quantities calculation | **PASS** |
| **Case 14** | Infeasible optimizer output detection | **PASS** |
| **Case 15** | Unsupported crop or soil combinations reporting reliable advisory | **PASS** |
| **Case 16** | Fertilizer price updates changing cost without altering agronomic nutrient requirements | **PASS** |
| **Case 17** | Repeated identical inputs producing reproducible deterministic results | **PASS** |
| **Case 18** | Farmer-level data isolation and multi-tenant security | **PASS** |
| **Case 19** | Final recommendation consistency between backend API and display data | **PASS** |

### Command 2: Combined Regression Test Suite
```powershell
.\venv\Scripts\pytest -q tests/test_fertilizer_recommendation_upgrade.py agronomy/tests/ phase5_nutrient/tests/ phase6_fertilizer/tests/ phase3_soil/tests/test_phase3.py
```
**Outcome:**
`110 passed, 0 failed in 8.72s` (100% pass rate)
- `tests/test_fertilizer_recommendation_upgrade.py`: 19 passed
- `agronomy/tests/test_agronomy_rule_selection.py`: 12 passed
- `phase5_nutrient/tests/test_golden_stcr.py`: 9 passed
- `phase5_nutrient/tests/test_npk_calculation.py`: 24 passed
- `phase6_fertilizer/tests/test_fertilizer_optimization.py`: 13 passed
- `phase3_soil/tests/test_phase3.py`: 33 passed

---

## 5. Proposed Rather Than Implemented (Future Work)

The following items are identified for future phases once additional field-level data become available:
1. **Soil Series Micro-Mapping Integration:** Expanding STCR coefficient calibration from district-level soil associations to all 120+ granular Tamil Nadu soil series identified by the Soil Survey and Land Use Organization (Coimbatore).
2. **Real-time Retail Fertilizer Inventory Sync:** Connecting fertilizer recommendation output to local PACCS (Primary Agricultural Cooperative Credit Societies) and private dealer POS inventories via IFMS (Integrated Fertilizer Management System).
3. **Foliar and Micronutrient Split Optimization:** Adding separate linear optimization constraints for micronutrients (ZnSO₄, Borax, FeSO₄) and foliar sprays (TNAU Pulse Wonder, Cotton Plus) alongside basal NPK.
