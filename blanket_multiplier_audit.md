# AgroWise AI (NutriCrop) — Blanket Fertilizer Multiplier Audit Report

**Date:** October 2026  
**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer for Higher Crop Yield  
**Target Region:** Tamil Nadu, India  
**Auditor:** Senior Agricultural Software Engineer & Agronomy-Data Validation Specialist  

---

## 1. Executive Summary & Objective

In agricultural extension systems and software, a dangerous oversimplification frequently occurs when **soil-test interpretation categories** (Low, Medium, High) are conflated with **fertilizer requirement adjustment percentages**. Specifically, the existing AgroWise AI codebase and historical design documents implemented blanket fertilizer adjustment factors:
- **Low soil nutrient level:** Increase fertilizer dose by 25% (multiplier `1.25`)
- **Medium soil nutrient level:** No adjustment (multiplier `1.00`)
- **High soil nutrient level:** Decrease fertilizer dose by 25% (multiplier `0.75`)

This audit was conducted pursuant to the **Antigravity Master Prompt: Correct Universal Low/Medium/High Fertilizer Multipliers** to:
1. Locate every occurrence of universal multipliers (`+25%`, `0%`, `-25%`, `1.25`, `0.75`, and continuous interpolation analogues) across code, registries, APIs, and tests.
2. Cross-reference every multiplier against authoritative agronomic sources from Tamil Nadu Agricultural University (TNAU) and the Indian Council of Agricultural Research (ICAR).
3. Safely eliminate unsupported universal multipliers from production calculations without inventing replacement percentages.
4. Separate diagnostic soil classification from agronomic fertilizer dose calculation.
5. Retain rule-specific adjustments only where explicitly documented and verified by official agronomic literature (specifically the TNAU Soil Testing Services Rice recommendation schedule).

---

## 2. Discovered Multipliers & Usage Inventory

A comprehensive grep and semantic audit across all subdirectories (`agronomy/`, `data/agronomy/`, `phase5_nutrient/`, `phase6_fertilizer/`, `phase7_integration/`, `tests/`) revealed the following implementations:

| Location / File | Entity / Parameter | Nature of Usage | Authoritative Source? | Status & Action Taken |
| :--- | :--- | :--- | :--- | :--- |
| `data/agronomy/tnau_stcr_rules.json` | `TNAU_STD_BLACKGRAM_RF_001` (`rating_adjustment_factors`) | Hardcoded `{ "low": 1.25, "medium": 1.0, "high": 0.75 }` applied to Rainfed Blackgram blanket RDF (20:40:20 kg/ha). | **NO**. TNAU CPG 2020 p. 64 and TNAU Agritech Pulses portal provide a fixed blanket dose of 20:40:20 kg/ha + 20 kg/ha S. | **REMOVED**. Deleted `rating_adjustment_factors`, set `"supports_rating_adjustment": false`. |
| `data/agronomy/tnau_stcr_rules.json` | `TNAU_BLANKET_GROUNDNUT_001` (`rating_adjustment_factors`) | Hardcoded `{ "low": 1.25, "medium": 1.0, "high": 0.75 }` applied to Groundnut blanket RDF (25:50:75 kg/ha). | **NO**. TNAU CPG 2020 p. 112 specifies a fixed general blanket recommendation without universal rating multipliers. | **REMOVED**. Deleted `rating_adjustment_factors`, set `"supports_rating_adjustment": false`. |
| `data/agronomy/tnau_stcr_rules.json` | `TNAU_STD_GROUNDNUT_001` (`rating_adjustment_factors`) | Blanket multiplier block under a provisional STCR placeholder. | **NO**. Uncalibrated placeholder rule. | **REMOVED**. Set `"supports_rating_adjustment": false`. |
| `data/agronomy/tnau_stcr_rules.json` | `TNAU_STD_SUGARCANE_001` (`rating_adjustment_factors`) | Hardcoded `{ "low": 1.25, "medium": 1.0, "high": 0.75 }` applied to Sugarcane blanket RDF (275:62.5:112.5 kg/ha). | **NO**. TNAU CPG 2020 p. 150 defines fixed blanket schedule. No universal $\pm 25\%$ scaling exists in official guide. | **REMOVED**. Deleted `rating_adjustment_factors`, set `"supports_rating_adjustment": false`. |
| `data/agronomy/tnau_stcr_rules.json` | `TNAU_STD_RICE_001` (`rating_adjustment_factors`) | Rating adjustment factors `{ "low": 1.25, "medium": 1.0, "high": 0.75 }` applied to standard rice dose (150:50:50 kg/ha). | **YES**. TNAU Soil Testing Services portal explicitly publishes the Rice Soil Rating Adjustment Table (+25% Low, 0% Medium, -25% High). | **RETAINED AS VERIFIED EXCEPTION**. Set `"supports_rating_adjustment": true`. |
| `phase5_nutrient/service.py` (`interpolate_soil_rating_multiplier`) | Function mapping soil ratings: Low $[1.05, 1.30]$, Med $[0.95, 1.05]$, High $[0.70, 0.95]$ | Continuous piecewise interpolation function designed to smooth the discrete $1.25 / 1.00 / 0.75$ step-function. | **NO (for blanket schedules)**. While mathematically continuous, applying it universally to blanket crops had no agronomic basis. | **ISOLATED TO AUTHORIZED RULES**. Gated behind `if rule_supports_adj and not is_general_blanket and not is_no_soil_test:`. For all other rules, factors are strictly `1.0, 1.0, 1.0`. |
| `phase5_nutrient/service.py` (Blanket Execution Path, lines 1070-1110) | Blanket dose calculation: `req_n = blanket_rdf['N'] * factor_n` | Multiplied blanket doses by rating factors for any blanket recommendation. | **NO**. Conflated soil rating interpretation with fertilizer dose requirement. | **CORRECTED**. Soil rating classification is preserved in `soil_nutrient_status` as diagnostic data, but blanket dose uses factor `1.00`. |
| `phase6_fertilizer/service.py` | LP/MILP Optimization Engine | Consumes `n_req_kg_per_ha`, `p2o5_req_kg_per_ha`, `k2o_req_kg_per_ha` from Phase 5. | **N/A (Downstream)**. | **VERIFIED CLEAN**. Phase 6 does not apply, re-introduce, or scale by soil rating multipliers. |
| `tests/test_soil_report_agronomic_recommendation.py` | `test_ref_03_tnau_rating_adjusted_blanket_blackgram` | Asserted $N=22.78$, $P_2O_5=40.56$, $K_2O=17.76$ for Blackgram based on continuous rating multipliers. | **NO**. Outdated test assertion. | **UPDATED & SPLIT**. Refactored to `test_ref_03_tnau_blanket_blackgram_fixed_without_unsupported_multipliers` ($20:40:20$) and added `test_ref_03b_tnau_authorized_rating_adjustment_rice`. |
| `phase5_nutrient/tests/test_golden_stcr.py` | `test_golden_01`, `02`, `03`, `04`, `09` | Asserted $22.6\text{ kg N/ha}$ for Blackgram blanket based on $1.13\times$ rating factor. | **NO**. Outdated test assertions. | **CORRECTED**. Updated to official fixed blanket dose of $20.0\text{ kg N/ha}$. |
| `phase5_nutrient/tests/test_npk_calculation.py` | `test_02`, `test_11` | Asserted $22.42\text{ kg N/ha}$ for Blackgram based on $1.121\times$ rating factor. | **NO**. Outdated test assertions. | **CORRECTED**. Updated to official fixed blanket dose of $20.0\text{ kg N/ha}$ (and farm total $50.0\text{ kg}$ for 2.5 ha). |
| `tests/test_nutrient_equations_audit.py` | `test_01`, `test_10` | Asserted $22.60\text{ kg N/ha}$ for Blackgram based on $1.13\times$ rating factor. | **NO**. Outdated test assertions. | **CORRECTED**. Updated to official fixed blanket dose of $20.0\text{ kg N/ha}$ (and farm total $50.0\text{ kg}$ for 2.5 ha). |

---

## 3. Authoritative Agronomic Literature Evaluation

### 3.1 TNAU Crop Production Guide (Agriculture) 2020
- **Reference:** TNAU & Directorate of Agriculture, Government of Tamil Nadu (2020), *Crop Production Guide (Agriculture)*. [PDF Link](https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf)
- **Findings:**
  1. **Rainfed Pulses (Blackgram, Greengram) — Page 64:**  
     *Official Recommendation:* $20 : 40 : 20\text{ kg N:P}_2\text{O}_5:\text{K}_2\text{O}/\text{ha}$ along with $20\text{ kg S/ha}$ applied as gypsum.  
     *Multiplier Rule:* There is **no provision** to scale this blanket recommendation by $+25\%$ or $-25\%$ based on soil ratings.
  2. **Groundnut — Page 112:**  
     *Official Recommendation:* $25 : 50 : 75\text{ kg N:P}_2\text{O}_5:\text{K}_2\text{O}/\text{ha}$ for irrigated/rainfed groundnut.  
     *Multiplier Rule:* Fixed blanket dose. No universal percentage adjustments permitted.
  3. **Sugarcane — Page 150:**  
     *Official Recommendation:* $275 : 62.5 : 112.5\text{ kg N:P}_2\text{O}_5:\text{K}_2\text{O}/\text{ha}$ for coastal and interior tracts.  
     *Multiplier Rule:* Fixed blanket dose. No universal percentage adjustments permitted.

### 3.2 TNAU Soil Rating Chart
- **Reference:** TNAU Agritech Portal — Agricultural Soil Rating Chart. [Portal Link](https://agritech.tnau.ac.in/agriculture/agri_soil_soilratingchart.html)
- **Findings:**
  - Defines fertility rating limits for Tamil Nadu soils:
    - **Available Nitrogen (Alkaline $\text{KMnO}_4$):** Low $< 280\text{ kg/ha}$, Medium $280 - 450\text{ kg/ha}$, High $> 450\text{ kg/ha}$.
    - **Available Phosphorus (Olsen-P for alkaline/neutral soils):** Low $< 11.0\text{ kg/ha}$, Medium $11.0 - 22.0\text{ kg/ha}$, High $> 22.0\text{ kg/ha}$.
    - **Available Potassium ($\text{NH}_4\text{OAc}$-K):** Low $< 118\text{ kg/ha}$, Medium $118 - 280\text{ kg/ha}$, High $> 280\text{ kg/ha}$.
  - **Crucial Distinction:** The rating chart is strictly an **analytical interpretation guide** for soil testing laboratories. It classifies whether a soil nutrient pool is deficient, medium, or high. It does **not** specify that fertilizer applications must be multiplied by $\pm 25\%$.

### 3.3 TNAU Soil Testing Services Portal — Rice Recommendation Table (Verified Exception)
- **Reference:** TNAU Soil Testing Services (STS) Portal — General Fertilizer Recommendations. [Portal Link](https://agritech.tnau.ac.in/agriculture/agri_soil_tnau_soiltestingservices.html)
- **Findings:**
  - TNAU publishes a specific Soil-Test-Based Fertilizer Recommendation Table for **Irrigated Rice**:
    - Medium soil fertility status receives the standard recommended dose: $150 : 50 : 50\text{ kg N:P}_2\text{O}_5:\text{K}_2\text{O}/\text{ha}$.
    - Low soil fertility status receives $+25\%$ ($187.5 : 62.5 : 62.5\text{ kg/ha}$).
    - High soil fertility status receives $-25\%$ ($112.5 : 37.5 : 37.5\text{ kg/ha}$).
  - **Verdict:** This is the **only** verified agronomic rule in Tamil Nadu agricultural literature authorizing this discrete percentage rating adjustment. It is retained strictly under rule `TNAU_STD_RICE_001` with explicit metadata flags.

---

## 4. Separation of Architectural Responsibilities

The audit established a clean architectural boundary separating three distinct agronomic phases:

```
+-------------------------------------------------------------------------------+
| Responsibility 1: Soil Diagnostic Classification                             |
| Source: TNAU Soil Rating Chart                                                |
| Interprets measured soil-test values (e.g. SN=190 kg/ha -> 'Low')             |
| Emits diagnostic status only; NEVER modifies fertilizer dose.                 |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
| Responsibility 2: Agronomic Nutrient Requirement Determination                |
| Source: Verified TNAU STCR-IPNS Equation OR Official Blanket Schedule        |
| - If STCR-IPNS calibrated: Target N = a*T - b*SN - c*FYM                     |
| - If Official Blanket: Fixed RDF (Multiplier = 1.00)                          |
| - Exception: Rice TNAU_STD_RICE_001 applies rule-authorized rating adjustment |
| Clamps at 0.0, deducts organic FYM and verified legume credits.               |
+-------------------------------------------------------------------------------+
                                       |
                                       v
+-------------------------------------------------------------------------------+
| Responsibility 3: Linear Programming Fertilizer Product Optimization         |
| Source: PuLP MILP Optimizer (Phase 6)                                         |
| Converts validated nutrient requirements into actual commercial fertilizer   |
| bags (Urea, DAP, MOP, SSP) using market prices and packing constraints.       |
| Strictly decoupled from soil test interpretation multipliers.                 |
+-------------------------------------------------------------------------------+
```

---

## 5. Summary of Code Changes

1. **`data/agronomy/tnau_stcr_rules.json`:**
   - Modified `TNAU_STD_BLACKGRAM_RF_001`: Removed `rating_adjustment_factors`, set `"supports_rating_adjustment": false`, `"recommendation_type": "GENERAL_BLANKET"`.
   - Modified `TNAU_BLANKET_GROUNDNUT_001`: Removed `rating_adjustment_factors`, set `"supports_rating_adjustment": false`, `"recommendation_type": "GENERAL_BLANKET"`.
   - Modified `TNAU_STD_GROUNDNUT_001`: Removed `rating_adjustment_factors`, set `"supports_rating_adjustment": false`.
   - Modified `TNAU_STD_SUGARCANE_001`: Removed `rating_adjustment_factors`, set `"supports_rating_adjustment": false`, `"recommendation_type": "GENERAL_BLANKET"`.
   - Modified `TNAU_STD_RICE_001`: Preserved authorized rating factors, verified source link to TNAU STS portal, set `"supports_rating_adjustment": true`.

2. **`phase5_nutrient/service.py`:**
   - Isolated `interpolate_soil_rating_multiplier()` so it is called strictly when `rule.get("supports_rating_adjustment") is True` AND the mode is not `GENERAL_BLANKET`.
   - For all general blanket recommendations, forced `factor_n, factor_p, factor_k = 1.0, 1.0, 1.0`.
   - Added user-facing transparency warnings detailing that blanket recommendations are fixed and that soil ratings provide diagnostic interpretation only.

3. **Automated Test Suites:**
   - Updated `tests/test_soil_report_agronomic_recommendation.py`, `phase5_nutrient/tests/test_golden_stcr.py`, `phase5_nutrient/tests/test_npk_calculation.py`, and `tests/test_nutrient_equations_audit.py` to assert fixed blanket doses (multiplier $= 1.00$) for Blackgram and Groundnut, while verifying rating adjustments on Rice (`TNAU_STD_RICE_001`).

---

## 6. Conclusion

Unsupported universal $\pm 25\%$ multipliers have been permanently purged from production calculation paths. Soil rating classification is preserved exclusively as diagnostic information for farmers, while fertilizer nutrient recommendations are calculated strictly according to verified TNAU STCR equations or fixed official blanket schedules.
