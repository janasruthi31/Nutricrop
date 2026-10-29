# AgroWise AI (Nutricrop) — Fertilizer Recommendation Module Audit

**Audit Date:** October 23, 2026  
**Auditor:** Antigravity AI (Pair Programming Assistant)  
**Scope:** Fertilizer Recommendation Engine, Agronomic Nutrient Calculations, Soil Test Interpretation, Historical Credits, Optimizer, and Integration Pipeline.

---

## 1. Existing Recommendation Workflow & File Paths

The fertilizer recommendation in AgroWise AI flows through a modular, staged pipeline:

```
[Confirmed Soil Report / Farmer Input]
                │
                ▼
  Phase 4: Rule Selection Service
  (`agronomy/service.py`, `agronomy/registry.py`)
  Matches: crop, district, soil series, season, target yield
                │
                ▼
  Phase 5: Nutrient Calculation Engine
  (`phase5_nutrient/service.py`, `phase5_nutrient/models.py`, `phase5_nutrient/units.py`)
  Calculates: Crop NPK requirements (kg/ha and field total)
  Applies: Soil test multipliers, FYM credits, previous crop credits, previous fertilizer residuals
                │
                ▼
  Phase 6: Fertilizer Optimizer Service
  (`phase6_fertilizer/service.py`, `phase6_fertilizer/models.py`, `phase6_fertilizer/catalog.py`)
  Solves: SciPy Mixed-Integer Linear Programming (MILP / HiGHS)
  Outputs: Commercial products (Urea, DAP, MOP, SSP, Complexes), whole bags, loose kg, cost, split schedule
                │
                ▼
  Phase 7: Full Integration Orchestrator
  (`phase7_integration/service.py`, `phase7_integration/extra_api.py`)
  Assembles: Soil test values, nutrient targets, fertilizer formulations, weather guidance, separate ML yield prediction
```

### Exact Files and Functions Responsible:

| Stage / Responsibility | File Path | Key Functions / Classes |
| :--- | :--- | :--- |
| **Rule Selection** | `agronomy/service.py` | `RuleSelectionService.select_rule()`, `RuleSelectionRequest` |
| **Rule Registry & Storage** | `agronomy/registry.py` | `AgronomicRuleRegistry.find_matching_rules()`, `data/agronomy/tnau_stcr_rules.json` |
| **Nutrient Calculation** | `phase5_nutrient/service.py` | `NutrientCalculationService.calculate()`, `_get_previous_crop_credit()`, `_calculate_previous_fertilizer_residual()`, `interpolate_soil_rating_multiplier()` |
| **Nutrient Schemas** | `phase5_nutrient/models.py` | `NutrientCalculationRequest`, `NutrientCalculationResponse`, `PreviousFertilizerItem` |
| **Unit Conversions** | `phase5_nutrient/units.py` | `convert_area_to_hectares()`, `normalize_soil_nutrient_value()`, `calculate_farm_total_nutrient()` |
| **Commercial Catalog** | `phase6_fertilizer/catalog.py` | `get_fertilizer_catalog()`, `data/agronomy/fertilizer_prices.json` |
| **Fertilizer Optimizer** | `phase6_fertilizer/service.py` | `FertilizerOptimizerService.optimize()`, `_generate_split_schedule()`, `_allocate_split()` |
| **Fertilizer Schemas** | `phase6_fertilizer/models.py` | `FertilizerOptimizationRequest`, `FertilizerOptimizationResponse`, `FertilizerProductRecommendation` |
| **Master Orchestration** | `phase7_integration/service.py` | `FullRecommendationService.generate_full_recommendation()` |
| **Farmer Data & History API** | `phase7_integration/extra_api.py` | `get_fertilizer_history()`, `add_fertilizer_history()`, `delete_fertilizer_history()`, `get_farm_details()` |
| **SQLite Persistence** | `phase3_soil/db.py` | `init_db()`, tables: `farmer_fertilizer_history`, `fertilizer_prices`, `soil_profiles` |

---

## 2. Defects and Gaps Identified

### Defect 1: Incomplete Previous Fertilizer History Representation
- In `phase5_nutrient/models.py` and `phase7_integration/extra_api.py`, `PreviousFertilizerItem` was missing critical agronomic fields:
  - `product_grade` (e.g., 18-46-0 for DAP, 46-0-0 for Urea, 20-20-0-13 for Ammonium Phosphate Sulphate).
  - `category` (chemical fertilizer, organic manure, compost, biofertilizer).
  - `bag_weight_kg` (Urea is 45 kg; DAP, MOP, SSP are 50 kg; compost bags are variable).
  - `field_area` & `field_area_unit` (quantity applied was divided by current farm area rather than the historical field area to which it was applied).
  - `application_method` (basal, top-dressing, foliar, fertigation).
  - `composition_n_pct`, `composition_p2o5_pct`, `composition_k2o_pct` for custom grades.
  - Grams (`g`, `grams`) were not supported as input units.

### Defect 2: Previous Fertilizer Residual Logic Deficiencies
- `_calculate_previous_fertilizer_residual()` used a static internal dictionary rather than the dynamic `phase6_fertilizer/catalog.py`.
- If a farmer entered bag units without bag weight, it defaulted to 50 kg even for Urea (which is statutory 45 kg in India).
- When historical applications were saved in `farmer_fertilizer_history`, the full recommendation endpoint did not automatically query and link the authenticated farmer's past applications when not explicitly passed in the request body.

### Defect 3: Missing Loose Quantity and Whole-Bag Distinction in Optimizer
- The optimizer output continuous fractional bags or rounded whole bags, but did not cleanly break down:
  - Whole commercial bags + exact loose kg (essential for smallholder farmers with 0.5–2 acre plots).
  - Post-packaging nutrient recalculation: After integer bag selection, exact nutrient supply must be recalculated from physical bags and loose amounts to report true surpluses and deficits.

### Defect 4: Product Selection Rationale and Cost Transparency
- Each recommended product lacked a clear agronomic rationale explaining *why* it was selected (e.g., "DAP provides primary phosphorus and basal starter nitrogen at lowest market cost").
- Custom farmer prices were supported, but price source and effective date were not clearly exposed per product in the UI response.

### Defect 5: Agronomic Credit Boundaries and Clamping Safeguards
- Crop residue / legume credits (e.g., 20 kg N/ha for Blackgram/Greengram) should apply only when the succeeding crop is a cereal/exhaustive crop (e.g., Rice, Maize, Cotton) and not when the succeeding crop is another legume.
- Synthetic N from previous fertilizers must remain 0.0 kg/ha carryover under tropical conditions (due to ammonia volatilization and leaching under high temperatures and monsoonal rainfall).
- Previous fertilizer residuals for P ($15\%$) and K ($10\%$) must be capped so they do not exceed reasonable carryover thresholds or produce negative nutrient recommendations without clear logging.

---

## 3. Authoritative Agronomic Sources Used

1. **Tamil Nadu Agricultural University (TNAU) Crop Production Guide (CPG) Agriculture 2020:**
   - Chapter 1: Cereals (Rice nutrient management, split application timing: 50% basal, 25% tillering, 25% panicle initiation).
   - Chapter 2: Pulses (Biological N fixation credits: 15–20 kg N/ha for grain legumes, 100% basal application).
   - Chapter 3: Millets & Maize (Balanced NPK nutrition and top-dressing).
   - Chapter 4: Oilseeds (Groundnut gypsum and nutrient management).
   - Chapter 5: Fiber Crops (Cotton split schedule: 50% basal, 25% squaring, 25% boll development).
   - Secondary & Micronutrient critical limits: DTPA-Zn ($1.2\text{ ppm}$), $\text{CaCl}_2\text{-S}$ ($10.0\text{ ppm}$), Hot-water B ($0.5\text{ ppm}$).

2. **ICAR All India Coordinated Research Project on Soil Test Crop Response (AICRP-STCR):**
   - Targeted Yield Equations for Tamil Nadu Soil Series (Palavidhi, Irugur, Noyyal, Kalathur).
   - Formula structure:
     $$FN = a \cdot T - b_{soil} \cdot SN - c_{fym} \cdot FYM - \text{credit}_{legume} - \text{residual}_{prev\_fert}$$
     $$FP_2O_5 = a \cdot T - b_{soil} \cdot SP - c_{fym} \cdot FYM - \text{residual}_{prev\_fert}$$
     $$FK_2O = a \cdot T - b_{soil} \cdot SK - c_{fym} \cdot FYM - \text{residual}_{prev\_fert}$$

3. **Fertilizer (Control) Order 1985 & Department of Fertilizers, Ministry of Chemicals & Fertilizers, GoI:**
   - Neem Coated Urea: $46\%\text{ N}$, $45\text{ kg}$ bag, Statutory MRP ₹$266.50$/bag ($₹5.92/\text{kg}$).
   - Di-Ammonium Phosphate (DAP): $18\%\text{ N}, 46\%\text{ P}_2\text{O}_5$, $50\text{ kg}$ bag, NBS Retail ₹$1350.00$/bag ($₹27.00/\text{kg}$).
   - Muriate of Potash (MOP): $60\%\text{ K}_2\text{O}$, $50\text{ kg}$ bag, NBS Retail ₹$1700.00$/bag ($₹34.00/\text{kg}$).
   - Single Super Phosphate (SSP): $16\%\text{ P}_2\text{O}_5, 11\%\text{ S}$, $50\text{ kg}$ bag, Retail ₹$600.00$/bag ($₹12.00/\text{kg}$).
   - Complex 20:20:0:13 (Ammonium Phosphate Sulphate): $20\%\text{ N}, 20\%\text{ P}_2\text{O}_5, 13\%\text{ S}$, $50\text{ kg}$ bag, ₹$1250.00$/bag ($₹25.00/\text{kg}$).
   - Complex 17:17:17: $17\%\text{ N}, 17\%\text{ P}_2\text{O}_5, 17\%\text{ K}_2\text{O}$, $50\text{ kg}$ bag, ₹$1450.00$/bag ($₹29.00/\text{kg}$).

---

## 4. Formulas and Unit Conversions Verified

### Soil Nutrients vs Fertilizer Nutrients
- **Soil Phosphorus:** Laboratory reports typically measure elemental $\text{P}$ via Olsen's method (alkaline/neutral soils) or Bray-1 method (acidic soils). Soil test ratings: Low ($<11\text{ kg/ha}$), Medium ($11\text{--}22\text{ kg/ha}$), High ($>22\text{ kg/ha}$).
- **Soil Potassium:** Laboratory reports measure elemental $\text{K}$ extracted by neutral normal ammonium acetate. Ratings: Low ($<118\text{ kg/ha}$), Medium ($118\text{--}280\text{ kg/ha}$), High ($>280\text{ kg/ha}$).
- **Fertilizer Phosphorus & Potassium:** Commercial fertilizers are expressed as oxides:
  $$P_2O_5 = P \times 2.29$$
  $$K_2O = K \times 1.20$$
  *Critical verification:* STCR equations calibrated by TNAU/ICAR already correlate elemental soil-test values ($SN, SP, SK$ in $\text{kg/ha}$) directly to oxide fertilizer requirements ($FP_2O_5, FK_2O$ in $\text{kg/ha}$). Therefore, elemental values are passed directly into STCR equations without double conversion.

### Area Conversions
- $1\text{ hectare} = 2.47105\text{ acres} = 10,000\text{ m}^2 = 247.105\text{ cents}$
- $1\text{ acre} = 0.404686\text{ hectares} = 100\text{ cents}$
- $1\text{ quintal} = 100\text{ kg} = 0.1\text{ metric tonne}$

### Historical Fertilizer Residual Carryover
- Nitrogen: $0.0\%$ carryover.
- Phosphorus ($P_2O_5$): $15\%$ carryover if applied $\le 6$ months ago; $0\%$ if $>6$ months ago.
- Potassium ($K_2O$): $10\%$ carryover if applied $\le 6$ months ago; $0\%$ if $>6$ months ago.
- Farm Area normalization:
  $$\text{Applied Rate (kg/ha)} = \frac{\text{Total Quantity (kg)}}{\text{Historical Field Area (ha)}}$$

---

## 5. Optimizer Constraints and Formulation

The fertilizer selection is formulated as a Mixed-Integer Linear Program (MILP):
$$\min_{x} \sum_{i=1}^M \left( c_i^{\text{bag}} \cdot x_i \right)$$
Subject to:
$$\sum_{i=1}^M \left( w_i \cdot \frac{N\%_i}{100} \right) x_i \ge N_{\text{target}}$$
$$\sum_{i=1}^M \left( w_i \cdot \frac{P_2O_5\%_i}{100} \right) x_i \ge P_2O_{5,\text{target}}$$
$$\sum_{i=1}^M \left( w_i \cdot \frac{K_2O\%_i}{100} \right) x_i \ge K_2O_{\text{target}}$$
$$x_i \ge 0, \quad x_i \in \mathbb{Z}_{\ge 0} \quad (\text{whole bags})$$

Where:
- $x_i$: Number of bags of fertilizer product $i$.
- $w_i$: Bag weight in kg ($45\text{ kg}$ for Urea, $50\text{ kg}$ for DAP/MOP/SSP).
- $c_i^{\text{bag}}$: Price per commercial bag in INR.

**Post-Optimization Packaging & Loose Quantity Calculation:**
- Whole bags: $\lfloor x_i \rfloor$ (integer bags).
- Loose quantity: $(x_i - \lfloor x_i \rfloor) \times w_i\text{ kg}$.
- Final supplied nutrients and surplus/deficit are recalculated directly from the final formulation.

---

## 6. Audit Summary of Existing Tests

- **Existing Phase 6 Tests:** 13/13 passed (`phase6_fertilizer/tests/test_fertilizer_optimization.py`).
- **Existing Phase 3 Tests:** 33/33 passed (`phase3_soil/tests/test_pipeline.py`).
- **Existing Flutter Tests:** 21/21 passed.

All existing capabilities remain functional. The upgrade will address the identified gaps while maintaining strict backward compatibility.
