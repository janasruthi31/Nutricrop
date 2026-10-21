# Mixed-Integer Linear Programming (MILP) Fertilizer Optimizer Validation
**Application Name:** AgroWise AI  
**Project Reference:** SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield  
**Module:** Phase 6 (Fertilizer Product Selection & Whole-Bag Cost Minimization)  

---

## 1. Mathematical Formulation

Agricultural supply chains sell fertilizers in discrete, commercial whole bags (e.g., 45 kg Urea, 50 kg DAP), not continuous fractional kilograms. Continuous Linear Programming (LP) followed by heuristic rounding can violate nutrient requirements or cause arbitrary over-expenditure. 

AgroWise AI formulates the procurement problem as an exact **Mixed-Integer Linear Program (MILP)** solved to global optimality using the HiGHS solver via `scipy.optimize.milp`:

### Decision Variables
$$x_j \in \mathbb{Z}_{\ge 0} \quad \text{for } j = 1, \dots, m$$
Where $x_j$ represents the integer count of commercial bags purchased for approved fertilizer product $j$.

### Objective Function
Minimize total purchase expenditure in Indian Rupees ($\text{INR}$):
$$\min_{x} \sum_{j=1}^{m} c_j \cdot x_j$$
Where $c_j$ is the verified retail price per commercial bag of product $j$.

### Nutrient Delivery Constraints
Every commercial bag of product $j$ with mass $M_j$ (kg) and nutrient grade $(g_{N,j}, g_{P,j}, g_{K,j})$ delivers:
$$a_{N,j} = M_j \cdot \frac{g_{N,j}}{100}, \quad a_{P,j} = M_j \cdot \frac{g_{P,j}}{100}, \quad a_{K,j} = M_j \cdot \frac{g_{K,j}}{100}$$

The optimization must satisfy the farm's total stoichiometric requirements ($R_N, R_{P_2O_5}, R_{K_2O}$ in kg):
$$\sum_{j=1}^{m} a_{N,j} \cdot x_j \ge R_N$$
$$\sum_{j=1}^{m} a_{P,j} \cdot x_j \ge R_{P_2O_5}$$
$$\sum_{j=1}^{m} a_{K,j} \cdot x_j \ge R_{K_2O}$$

---

## 2. Commercial Fertilizer Catalog & Pricing Registry

Prices reflect Government of India (GoI) statutory Maximum Retail Prices (MRP) under the Nutrient Based Subsidy (NBS) scheme effective from 2024-04-01:

| Product Code | Commercial Name | Category | Grade ($N : P_2O_5 : K_2O$) | Bag Mass ($M_j$) | MRP per Bag | Effective Date | Regulatory Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `UREA` | Neem Coated Urea | Straight Nitrogenous | $46\% : 0\% : 0\%$ | 45.0 kg | ₹266.50 | 2024-04-01 | Dept of Fertilizers, GoI (Statutory MRP) |
| `DAP` | Di-Ammonium Phosphate | Complex / Phosphatic | $18\% : 46\% : 0\%$ | 50.0 kg | ₹1,350.00 | 2024-04-01 | Dept of Fertilizers, NBS Schedule |
| `MOP` | Muriate of Potash | Straight Potassic | $0\% : 0\% : 60\%$ | 50.0 kg | ₹1,700.00 | 2024-04-01 | Dept of Fertilizers, NBS Schedule |
| `SSP` | Single Super Phosphate | Straight Phosphatic | $0\% : 16\% : 0\%$ | 50.0 kg | ₹600.00 | 2024-04-01 | TANFED / NBS Notification |
| `COMPLEX_20_20_0` | Ammonium Phosphate Sulphate | Complex | $20\% : 20\% : 0\%$ | 50.0 kg | ₹1,250.00 | 2024-04-01 | TANFED Commercial Schedule |
| `COMPLEX_17_17_17`| Complex 17:17:17 | Complex NPK | $17\% : 17\% : 17\%$ | 50.0 kg | ₹1,450.00 | 2024-04-01 | TANFED Commercial Schedule |

### Coupled Nutrient Accounting
* **DAP Indivisibility:** 1 bag (50 kg) of DAP provides $9.0\text{ kg N}$ alongside $23.0\text{ kg } P_2O_5$. The solver automatically accounts for this Nitrogen contribution, preventing excessive Urea purchases.
* **Complex Fertilizers:** Multi-grade products deliver simultaneous inputs across all non-zero components, evaluated in the linear constraint matrix $\mathbf{A}$.

---

## 3. Mathematical Optimality & Brute-Force Verification

To guarantee that `scipy.optimize.milp` reliably identifies the global optimum:
1. **Automated Optimality Test (`test_08_milp_optimality_compared_to_brute_force`):** Executes an exhaustive integer grid search across all feasible combinations ($0 \le x_j \le 15$ bags) for test requirements ($N=85\text{ kg}, P_2O_5=40\text{ kg}, K_2O=50\text{ kg}$).
2. **Result:** The MILP solver output matches the brute-force minimum cost with zero error ($\Delta \text{Cost} = 0.00\text{ INR}$).
3. **Whole-Bag Verification Guard:** A post-solve validation step explicitly verifies that $\sum a_{ij} x_j \ge b_i$. If a solver returns an unbounded, time-limited, or infeasible status, the recommendation is rejected with an explicit diagnostic error.

---

## 4. Nutrient Balance & Surplus Reporting

Whole-bag discrete optimization inherently produces small surpluses because fertilizers cannot be bought in fractional quantities. AgroWise AI transparently reports:
* **Required (kg):** Farm total nutrient need computed from STCR.
* **Supplied (kg):** Total nutrient delivered by the purchased bags.
* **Surplus (kg):** $\max(0.0, \text{Supplied} - \text{Required})$.

---

## 5. Crop-Specific Phenological Split Application Schedules

Purchased fertilizer bags must be applied according to physiological growth stages to maximize Fertilizer Use Efficiency (FUE) and prevent volatilization/leaching:

* **Rice (Paddy):**
  - *Basal Application (Sowing/Transplanting):* $50\% \text{ N} + 100\% P_2O_5 + 50\% K_2O$.
  - *Active Tillering (21–25 DAT):* $25\% \text{ N} + 0\% P_2O_5 + 25\% K_2O$.
  - *Panicle Initiation (40–45 DAT):* $25\% \text{ N} + 0\% P_2O_5 + 25\% K_2O$.
* **Cotton (MCU 5):**
  - *Basal (Sowing):* $50\% \text{ N} + 100\% P_2O_5 + 50\% K_2O$.
  - *Square Formation (40–45 DAS):* $25\% \text{ N} + 0\% P_2O_5 + 25\% K_2O$.
  - *Boll Formation (70–75 DAS):* $25\% \text{ N} + 0\% P_2O_5 + 25\% K_2O$.
* **Hybrid Maize:**
  - *Basal (Sowing):* $50\% \text{ N} + 100\% P_2O_5 + 50\% K_2O$.
  - *Knee-High Stage (25–30 DAS):* $25\% \text{ N} + 0\% P_2O_5 + 25\% K_2O$.
  - *Tasseling / Silking (45–50 DAS):* $25\% \text{ N} + 0\% P_2O_5 + 25\% K_2O$.
* **Pulses (Blackgram / Greengram):**
  - *Basal (100% at Sowing):* $100\% \text{ N} + 100\% P_2O_5 + 100\% K_2O$. Short duration pulses do not receive split top-dressing per TNAU CPG 2020.
