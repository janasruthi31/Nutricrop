# Phase 5 — NPK Nutrient Requirement Calculation Engine Validation

## 1. Overview
Phase 5 calculates exact Nitrogen (N), Phosphorus (\(\text{P}_2\text{O}_5\)), and Potassium (\(\text{K}_2\text{O}\)) nutrient requirements based on the verified Phase 4 agronomic rule and farmer soil-test profile.

## 2. Calculation Principles & Equations
1. **Linear STCR Targeted Yield Equations:**
   \[
   \text{Requirement N (kg/ha)} = K_N \times T - c_N \times \text{Soil N}
   \]
   \[
   \text{Requirement P}_2\text{O}_5 \text{ (kg/ha)} = K_P \times T - c_P \times \text{Soil P}
   \]
   \[
   \text{Requirement K}_2\text{O (kg/ha)} = K_K \times T - c_K \times \text{Soil K}
   \]
   Where \(T\) is target yield in tonnes/ha (or quintals/ha according to rule spec), and \(K_i, c_i\) are verified TNAU STCR coefficients.

2. **Universal Multiplier Guard:**
   Universal low (+25%) / high (-25%) rating multipliers are applied ONLY to standard `TNAU-SOIL-TEST` rules and are **NEVER** applied on top of STCR targeted yield linear formulas.

3. **Units & Area Conversions:**
   - Farm area in acres is converted to hectares using exact factor \(1 \text{ acre} = 0.404686 \text{ ha}\).
   - Elemental \(P \rightarrow \text{P}_2\text{O}_5 \times 2.291\).
   - Elemental \(K \rightarrow \text{K}_2\text{O} \times 1.205\).
   - Per-hectare nutrient requirements and total farm requirements are computed independently without double-multiplying.

## 3. API Contract & Implementation
- **Module:** `phase5_nutrient/`
- **Service:** `phase5_nutrient/service.py`
- **Endpoint:** `POST /api/nutrient-requirement/calculate`

## 4. Test Suite Results
- `test_01_valid_stcr_calculation`: PASSED
- `test_02_valid_soil_test_based_calculation`: PASSED
- `test_03_missing_target_yield`: PASSED
- `test_04_missing_required_soil_values`: PASSED
- `test_07_invalid_nutrient_units`: PASSED
- `test_10_acre_to_hectare_conversion`: PASSED
- `test_11_per_hectare_vs_total_farm`: PASSED
- Total Phase 5 Test Pass Rate: 100% (14/14 tests passing).
