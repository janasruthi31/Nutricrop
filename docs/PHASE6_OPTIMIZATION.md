# Phase 6 — Fertilizer Type, Quantity, and Cost Optimization Engine Validation

## 1. Overview
Phase 6 determines the optimal combination of commercial fertilizer products (Urea, DAP, MOP, SSP, Complex fertilizers) that satisfies the required N, \(\text{P}_2\text{O}_5\), and \(\text{K}_2\text{O}\) nutrient targets at the lowest total purchase cost.

## 2. Optimization Formulation
- **Solver:** `scipy.optimize.linprog` (Simplex / HiGHS algorithm).
- **Objective:**
  \[
  \min \sum_{j=1}^m c_j x_j
  \]
  where \(c_j\) is price per kg of fertilizer product \(j\), and \(x_j\) is kilograms of product \(j\).
- **Subject to Nutrient Sufficiency Constraints:**
  \[
  \sum_{j=1}^m \frac{N_j}{100} x_j \ge N_{\text{target}}
  \]
  \[
  \sum_{j=1}^m \frac{P_j}{100} x_j \ge P_{\text{target}}
  \]
  \[
  \sum_{j=1}^m \frac{K_j}{100} x_j \ge K_{\text{target}}
  \]
- **Commercial Bag Quantity & Sufficiency Verification:**
  - Continuous LP solution \(x_j\) is converted to commercial bags using ceiling function \(b_j = \lceil x_j / \text{bag\_size}_j \rceil\).
  - Delivered nutrients from bag quantities are re-calculated: \(\text{Delivered}_i = \sum b_j \cdot \text{bag\_size}_j \cdot (C_{i,j}/100)\).
  - Verifies \(\text{Delivered}_i \ge \text{Target}_i\) for all nutrients \(i \in \{N, P, K\}\).

## 3. API Contract & Service
- **Module:** `phase6_fertilizer/`
- **Endpoints:** 
  - `POST /api/fertilizer/optimize`
  - `POST /api/fertilizer-optimization/optimize`

## 4. Test Suite Results
- `test_01_valid_lp_optimization`: PASSED
- `test_02_consuming_phase5_output`: PASSED
- `test_03_zero_nutrient_requirement`: PASSED
- `test_04_restricted_allowed_fertilizers`: PASSED
- `test_05_invalid_input_requirements`: PASSED
- `test_06_api_validation_endpoint`: PASSED
- Total Phase 6 Test Pass Rate: 100% (6/6 tests passing).
