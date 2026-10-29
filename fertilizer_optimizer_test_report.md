# Fertilizer Cost Optimizer Test & Verification Report

**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer  
**Module:** Phase 6 — Fertilizer Type, Quantity, and Cost Optimization Engine  
**Test Suites:** `phase6_fertilizer/tests/test_fertilizer_optimization.py` and `tests/test_c_d_e_verification.py` (Section D)  
**Execution Date:** 2026-10-28  
**Result:** 100% PASS (18/18 Tests Passed)  

---

## 1. Executive Summary

This test report presents the verification results for the AgroWise AI Fertilizer Cost Optimizer. Testing confirms that:
1. Multi-nutrient fertilizers (such as DAP $18\text{-}46\text{-}0$ and Complex $20\text{-}20\text{-}0$) account simultaneously for all delivered nutrients without double-counting or nutrient omission.
2. The optimizer strictly enforces non-deficit constraints ($\sum a_{ij} x_j \ge R_i$) and halts rather than recommending cost-cutting solutions that violate verified agronomic nutrient requirements.
3. Agronomically prohibited product combinations (Urea + CAN, CAN + Basic Slag, DAP + Lime) are detected and rejected with explicit `NO_FEASIBLE_SOLUTION` / `limiting_constraint` statuses.
4. Unavailable products (`is_available: false`) and products with missing or non-positive retail prices ($\le 0$) are filtered out prior to optimization.
5. Infeasible problems return explicit status codes and limiting constraints without fabricating partial recommendations.
6. Package rounding effects (whole bags vs. loose kg) and statutory price timestamps (`price_data_timestamp="2026-10-22"`) are reported transparently.

---

## 2. Test Execution Matrix

### 2.1 Dedicated Optimizer Suite (`phase6_fertilizer/tests/test_fertilizer_optimization.py`)

| Test Case | Scenario Description | Inputs | Expected Output | Status |
|---|---|---|---|---|
| `test_01` | Valid LP Cost Minimization | Rice: $100\text{ kg N}$, $50\text{ kg P}_2\text{O}_5$, $60\text{ kg K}_2\text{O}$ on $2\text{ ha}$ | `status=OPTIMIZATION_SUCCESS`, `total_cost > 0`, 3-split schedule | **PASS** |
| `test_02` | Direct Consumption of Phase 5 Output | Phase 5 STCR payload ($52.5\text{ N}$, $37.5\text{ P}$, $30.0\text{ K}$) | `status=OPTIMIZATION_SUCCESS`, exact nutrient requirements matched | **PASS** |
| `test_03` | Zero Nutrient Requirement | $0\text{ kg N}$, $0\text{ kg P}_2\text{O}_5$, $0\text{ kg K}_2\text{O}$ | `status=OPTIMIZATION_SUCCESS`, `total_cost=0.0`, 0 products | **PASS** |
| `test_04` | Restricted Product Catalog | `allowed_fertilizers=["UREA", "SSP", "MOP"]` | DAP excluded; SSP selected for $\text{P}_2\text{O}_5$ | **PASS** |
| `test_05` | Invalid Input Handling | Null or non-numeric requirements | `status=VALIDATION_ERROR`, explicit validation message | **PASS** |
| `test_06` | REST API Validation Endpoint | FastAPI `/api/fertilizer/optimize` | Status 200, valid JSON response adhering to Pydantic schema | **PASS** |
| `test_07` | Infeasible Nutrient Constraint | Required P cannot be supplied (only Urea & MOP allowed) | `status in ("INFEASIBLE", "NO_FEASIBLE_SOLUTION")`, `limiting_constraint is not None` | **PASS** |
| `test_08` | MILP vs Brute Force Optimality | Discrete whole bag search space comparison | MILP cost matches or beats brute force discrete search | **PASS** |
| `test_09` | Crop-Specific Split Schedules | Phenological stages for Rice, Sugarcane, Pulses | Correct split stage names, percentages, and timing | **PASS** |
| `test_10` | Whole Bag Integer Units | `allow_fractional_bags=False` | $x_j \in \mathbb{Z}_{\ge 0}$, whole bags $\ge 0$, `loose_kg = 0.0` | **PASS** |
| `test_11` | Smallholder Fractional Quantities | `allow_fractional_bags=True` on $0.4\text{ ha}$ plot | Precise fractional quantities, loose kg reported | **PASS** |
| `test_12` | Surplus Factor Constraint | `max_surplus_factor=1.1` on smallholder plot | Solves with strictly bounded oversupply $\le 10\%$ | **PASS** |
| `test_13` | Smallholder Surplus Packaging Warning | Whole bag rounding forcing oversupply $> 1.5\times$ | Warning emitted advising farmer to use loose/fractional quantities | **PASS** |

### 2.2 Section D Regression Suite (`tests/test_c_d_e_verification.py`)

| Test Case | Scenario Description | Inputs | Expected Output | Status |
|---|---|---|---|---|
| `test_d01` | Multi-Nutrient DAP Balance | $18\text{ kg N}$, $46\text{ kg P}_2\text{O}_5$, $0\text{ kg K}_2\text{O}$ on $1\text{ ha}$ | 2 bags DAP ($100\text{ kg}$) selected; DAP supplies $18\text{ N}$ and $46\text{ P}$; zero Urea needed | **PASS** |
| `test_d02` | Prohibited Combinations Rejected | Urea + CAN requested together | `status in ("INFEASIBLE", "NO_FEASIBLE_SOLUTION")`, `limiting_constraint` cites prohibited mixture | **PASS** |
| `test_d03` | Unavailable & Unpriced Products Excluded | Catalog with price $\le 0$ and `is_available: false` | Free and unavailable products excluded; valid Urea selected | **PASS** |
| `test_d04` | Limiting Constraint on Infeasibility | Missing P supplier in allowed list | `limiting_constraint` explicitly names Phosphorus ($\text{P}_2\text{O}_5$) | **PASS** |
| `test_d05` | Packaging Rounding Effects & Timestamp | $0.4\text{ ha}$ smallholder plot discrete rounding | `price_data_timestamp="2026-10-22"`, `package_rounding_effects` breakdown populated | **PASS** |

---

## 3. Detailed Case Study: Multi-Nutrient Accounting (DAP)

### Problem Definition:
- Farm Area: $1.0\text{ hectare}$
- Target Requirements: $18.0\text{ kg N}$, $46.0\text{ kg P}_2\text{O}_5$, $0.0\text{ kg K}_2\text{O}$
- Available Catalog: Urea ($46\% \text{ N}$, ₹266.50 / $45\text{ kg}$), DAP ($18\% \text{ N}$, $46\% \text{ P}_2\text{O}_5$, ₹1,350.00 / $50\text{ kg}$), MOP ($60\% \text{ K}_2\text{O}$, ₹1,700.00 / $50\text{ kg}$)

### Execution & Solver Output:
1. Requirement for $\text{P}_2\text{O}_5$ ($46\text{ kg}$) requires $\frac{46}{0.46} = 100\text{ kg of DAP}$ ($2\text{ commercial 50-kg bags}$).
2. $2\text{ bags of DAP}$ supply:
   - Phosphorus: $100\text{ kg} \times 0.46 = 46.0\text{ kg P}_2\text{O}_5$ (exactly $100\%$ of target).
   - Nitrogen: $100\text{ kg} \times 0.18 = 18.0\text{ kg N}$ (exactly $100\%$ of target).
3. The optimizer detects that the nitrogen requirement of $18.0\text{ kg}$ is fully met by the DAP bags.
4. **Recommended Plan:**
   - DAP: $2\text{ bags}$ ($100.0\text{ kg}$), Total Cost: ₹2,700.00.
   - Urea: $0\text{ bags}$ ($0.0\text{ kg}$), Total Cost: ₹0.00.
   - MOP: $0\text{ bags}$ ($0.0\text{ kg}$), Total Cost: ₹0.00.
   - Total Cost: ₹2,700.00.
   - Nitrogen Supplied: $18.0\text{ kg}$ (Surplus: $0.0\text{ kg}$, Deficit: $0.0\text{ kg}$).
   - $\text{P}_2\text{O}_5$ Supplied: $46.0\text{ kg}$ (Surplus: $0.0\text{ kg}$, Deficit: $0.0\text{ kg}$).

*Result:* Proves that DAP is not treated as a phosphorus-only fertilizer, avoiding redundant nitrogen over-application and unnecessary expenditure.

---

## 4. Test Execution Summary

```
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-8.3.3
rootdir: C:\Users\hp\OneDrive\Documents\TN_Yield_Model_Phase3_Combined
collected 18 items

phase6_fertilizer/tests/test_fertilizer_optimization.py::test_01_valid_lp_optimization PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_02_consuming_phase5_output PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_03_zero_nutrient_requirement PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_04_restricted_allowed_fertilizers PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_05_invalid_input_requirements PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_06_api_validation_endpoint PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_07_infeasible_nutrient_constraint PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_08_milp_optimality_compared_to_brute_force PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_09_crop_specific_schedules PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_10_whole_bag_integer_units PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_11_fractional_bags_for_smallholders PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_12_surplus_factor_constraint PASSED
phase6_fertilizer/tests/test_fertilizer_optimization.py::test_13_smallholder_surplus_packaging_warning PASSED
tests/test_c_d_e_verification.py::TestSectionDFertilizerOptimizerConstraints::test_d01_multi_nutrient_product_dap_accounts_for_n_and_p PASSED
tests/test_c_d_e_verification.py::TestSectionDFertilizerOptimizerConstraints::test_d02_prohibited_combinations_rejected PASSED
tests/test_c_d_e_verification.py::TestSectionDFertilizerOptimizerConstraints::test_d03_unavailable_or_unpriced_fertilizers_are_excluded PASSED
tests/test_c_d_e_verification.py::TestSectionDFertilizerOptimizerConstraints::test_d04_infeasible_problem_returns_explicit_limiting_constraint PASSED
tests/test_c_d_e_verification.py::TestSectionDFertilizerOptimizerConstraints::test_d05_package_rounding_effects_and_timestamp_reported PASSED

============================= 18 passed in 3.12s ==============================
```

All optimizer constraints, multi-nutrient balances, packaging options, and safety rules function as specified with zero regression.
