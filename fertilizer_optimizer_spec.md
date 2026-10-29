# Fertilizer Cost Optimizer Specification & Agronomic Constraints

**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer  
**Module:** Phase 6 — Fertilizer Type, Quantity, and Cost Optimization Engine  
**Version:** 2.0 (Authoritative Verification & Multi-Nutrient Accounting)  
**Date:** 2026-10-28  

---

## 1. Problem Overview & Scope

The fertilizer optimization module formulates and solves a mathematical programming problem to determine the most cost-effective combination of commercial fertilizer products required to fulfill crop-specific agronomic nutrient targets for Tamil Nadu smallholders.

**Core Safety Mandate:** Cost minimization is executed **only after** the agronomic nutrient requirements ($R_N$, $R_P$, $R_K$) have been strictly determined by an applicable, verified agronomic rule (TNAU STCR-IPNS equation or Standard Recommended Dose of Fertilizer). The optimizer is never permitted to reduce fertilizer costs by violating verified agronomic nutrient requirements or applying incompatible product mixtures.

---

## 2. Mathematical Formulation

### 2.1 Sets and Indices
- $J$: Set of eligible candidate commercial fertilizer products, indexed by $j \in \{1, 2, \dots, n\}$.
- $I$: Set of primary macronutrients, $I = \{\text{N}, \text{P}_2\text{O}_5, \text{K}_2\text{O}\}$.

### 2.2 Parameters
- $c_j$: Retail price per commercial bag of fertilizer product $j$ (INR per bag).
- $w_j$: Commercial package weight of product $j$ (kg per bag; e.g., $45\text{ kg}$ for Neem-Coated Urea, $50\text{ kg}$ for DAP, MOP, SSP).
- $p_{ij}$: Percentage nutrient concentration of nutrient $i$ in product $j$ ($\%$ by weight).
- $a_{ij}$: Nutrient delivery coefficient of nutrient $i$ delivered by one bag of product $j$:
  $$a_{ij} = w_j \times \frac{p_{ij}}{100} \quad (\text{kg of nutrient } i \text{ per bag})$$
- $R_i$: Total farm nutrient requirement for nutrient $i$ (kg for total farm area $A$ hectares):
  $$R_i = r_i \times A$$
  where $r_i$ is the per-hectare net requirement determined by Phase 5.
- $S_{\max}$: Upper allowable surplus factor (default $1.5$ to $2.5$, configurable), preventing toxic or uneconomic nutrient overdosing.

### 2.3 Decision Variables
- $x_j$: Quantity of fertilizer product $j$ recommended.
  - **Discrete Formulation (Default):** $x_j \in \mathbb{Z}_{\ge 0}$ (whole commercial bags).
  - **Fractional Formulation (Smallholders):** $x_j \in \mathbb{R}_{\ge 0}$ (continuous bag fractions, where fractional parts are converted to loose kilograms).

### 2.4 Objective Function
Minimize total commercial fertilizer expenditure:
$$\min_{x} \quad Z = \sum_{j \in J} c_j x_j$$

### 2.5 Constraints

1. **Agronomic Nutrient Lower Bounds (Zero Deficit Mandate):**
   Every verified nutrient target must be fully met or exceeded:
   $$\sum_{j \in J} a_{ij} x_j \ge R_i, \quad \forall i \in I \text{ where } R_i > 0$$
   *Deficits are strictly prohibited.* The optimizer cannot sacrifice nutrient sufficiency for cost savings.

2. **Agronomic Nutrient Upper Bounds (Surplus Factor Cap):**
   To prevent nutrient imbalance, groundwater leaching, and fertilizer toxicity:
   $$\sum_{j \in J} a_{ij} x_j \le S_{\max} \times R_i, \quad \forall i \in I \text{ where } R_i > 0$$
   If discrete bag packaging forces an oversupply exceeding $S_{\max}$, the problem is declared infeasible, prompting the smallholder to utilize loose/fractional quantities.

3. **Multi-Nutrient Accounting:**
   Every nutrient contributed by multi-nutrient products is simultaneously credited toward all nutrient bounds:
   - **DAP ($18\text{-}46\text{-}0$):** Contributes $w_{\text{DAP}} \times 0.18\text{ kg N}$ and $w_{\text{DAP}} \times 0.46\text{ kg P}_2\text{O}_5$.
   - **Complex $20\text{-}20\text{-}0$:** Contributes $w_{\text{NP}} \times 0.20\text{ kg N}$ and $w_{\text{NP}} \times 0.20\text{ kg P}_2\text{O}_5$.
   - **Complex $17\text{-}17\text{-}17$:** Contributes $w_{\text{NPK}} \times 0.17$ across all three nutrients (N, $\text{P}_2\text{O}_5$, $\text{K}_2\text{O}$).
   - **Single Superphosphate (SSP):** Contributes $16\% \text{ P}_2\text{O}_5$ plus $11\text{-}12\%$ essential Sulphur.
   - **Muriate of Potash (MOP):** Contributes $60\% \text{ K}_2\text{O}$.

4. **Product Incompatibility & Prohibited Combinations:**
   Authoritative guidance from the **TNAU Crop Production Guide (Agriculture) 2020** (Fertilizer Management Section) identifies chemical combinations that must never be mixed or co-applied:
   $$\{x_u > 0 \land x_v > 0\} \implies \text{PROHIBITED}, \quad \forall (u, v) \in \text{ProhibitedPairs}$$
   
   | Prohibited Combination | Agronomic & Chemical Failure Mechanism | Authoritative Source |
   |---|---|---|
   | **CAN + Basic Slag** | Alkaline slag reacts with ammonium ions, liberating gaseous ammonia ($\text{NH}_3 \uparrow$), resulting in severe nitrogen volatilization loss. | TNAU CPG 2020, p. 302 |
   | **Urea + CAN** | Urea mixed with Calcium Ammonium Nitrate produces a critical relative humidity depression, forming an extremely hygroscopic, unspreadable deliquescent slurry. | TNAU CPG 2020 / ICAR Handbook |
   | **DAP + Lime / Basic Slag** | Water-soluble monocalcium/diammonium phosphate reacts with free calcium, reverting into water-insoluble tricalcium phosphate ($\text{Ca}_3(\text{PO}_4)_2$), locking phosphorus away from root uptake. | TNAU CPG 2020, Soil Fertility |

5. **Product Availability and Pricing Integrity:**
   - Candidate products with `is_available = false` are strictly excluded from set $J$.
   - Products with missing, null, or non-positive retail prices ($\le 0$) are excluded from set $J$.
   - Subsidized statutory MRPs and market prices reflect the Department of Fertilizers, Government of India (NBS Subsidy Schedule) and local dealer records. Price timestamp (`price_data_timestamp = "2026-10-22"`) is permanently attached to every response.

---

## 3. Packaging Rounding & Smallholder Economics

### 3.1 Discrete vs. Fractional Mode
- **Discrete Mode (`allow_fractional_bags = False`):**
  Solves via Mixed-Integer Linear Programming using the **HiGHS MILP solver** (`scipy.optimize.milp`). All $x_j$ are integers.
- **Fractional Mode (`allow_fractional_bags = True`):**
  Solves via continuous Linear Programming. Ideal for smallholders ($< 1\text{ hectare}$ or $< 2.5\text{ acres}$) where whole-bag purchases would force extreme over-expenditure and severe nutrient surplus.
  - Whole commercial bags: $\lfloor x_j \rfloor$
  - Loose fertilizer: $(x_j - \lfloor x_j \rfloor) \times w_j \text{ kg}$

### 3.2 Packaging Rounding Breakdown
Every response reports:
- `whole_bags_total`: Total commercial bags.
- `loose_kg_total`: Total loose quantity in kg.
- `surplus_from_rounding_kg`: Surplus of each nutrient caused solely by packaging increments.
- `packaging_effect_description`: Plain-language explanation of discrete packaging effects.

---

## 4. Infeasibility Handling & Limiting Constraints

When no feasible solution exists (e.g., candidate products cannot supply a required nutrient, or discrete packaging exceeds the surplus factor cap, or an incompatible pair was requested), the optimizer executes the following safety protocol:
1. Returns status: `NO_FEASIBLE_SOLUTION` (equivalent to `INFEASIBLE`).
2. Explains the exact constraint that prevented optimization in `limiting_constraint`:
   - *"No available candidate fertilizer product supplies required Phosphorus (P2O5)."*
   - *"Prohibited fertilizer combination requested: CAN, UREA. Urea mixed with Calcium Ammonium Nitrate forms a highly hygroscopic mixture that rapidly deliquesces into an unspreadable slurry."*
   - *"Commercial whole-bag packaging constraint causes surplus over allowable factor limit."*
3. Total cost is reported as `0.0`.
4. Recommended products list is empty (`[]`).
5. **Never presents an invalid, partial, or violating combination to the farmer.**

---

## 5. Phenological Split Application Schedules

Optimized product quantities are dynamically distributed across crop phenological stages in accordance with TNAU Crop Production Guide 2020:
- **Rice (3 Splits):** $50\%$ N, $100\%$ $\text{P}_2\text{O}_5$, $50\%$ $\text{K}_2\text{O}$ at Basal; $25\%$ N, $25\%$ $\text{K}_2\text{O}$ at Active Tillering ($21\text{-}25\text{ DAT}$); $25\%$ N, $25\%$ $\text{K}_2\text{O}$ at Panicle Initiation ($40\text{-}45\text{ DAT}$).
- **Groundnut (Basal):** $100\%$ Basal application at sowing with gypsum top-dressing at $40\text{-}45\text{ DAS}$.
- **Sugarcane (3 Splits):** $25\%$ at Planting, $50\%$ at Tillering ($45\text{-}60\text{ DAP}$), $25\%$ at Grand Growth ($90\text{-}120\text{ DAP}$).
- **Blackgram (Basal):** $100\%$ Basal application at sowing for rainfed pulses.
