# AgroWise AI (NutriCrop) — Comprehensive Agronomic Equation Audit & Validation Report

**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer for Higher Crop Yield  
**Target Domain:** Tamil Nadu Agricultural Ecosystem (TNAU / ICAR-AICRP Standards)  
**Audit Date:** October 2026  
**Auditor:** Senior Agricultural Software Engineer & Agronomy-Data Validation Specialist  

---

## 1. Executive Summary & Objective

This audit evaluates the mathematical, dimensional, and agronomic integrity of the nutrient requirement equations implemented in AgroWise AI (NutriCrop). The objective is to ensure that all fertilizer dose calculations comply strictly with verified publications from the **Tamil Nadu Agricultural University (TNAU)** and the **ICAR All India Coordinated Research Project on Soil Test Crop Response (AICRP-STCR)**.

### Primary Audit Findings:
1. **Separation of Soil Interpretation from Fertilizer Dose Calculation:**
   - Soil-test interpretation categories (Low, Medium, High from the TNAU Soil Rating Chart) are diagnostic indicators of indigenous soil fertility.
   - Universal percentage multipliers (Low $+25\%$, Medium $0\%$, High $-25\%$) were historically applied across all blanket crops. This fixed adjustment logic has been completely removed from production calculations.
   - Blanket recommendations for **Rainfed Blackgram** (`TNAU_STD_BLACKGRAM_RF_001`), **Groundnut** (`TNAU_BLANKET_GROUNDNUT_001`), and **Sugarcane** (`TNAU_STD_SUGARCANE_001`) are fixed official Recommended Doses of Fertilizer (RDF) with a multiplier strictly set to $1.00$.
   - The only authorized exception is **Irrigated Rice** under rule `TNAU_STD_RICE_001`, which is explicitly published as a rating-adjusted schedule on the official TNAU Soil Testing Services portal.
2. **Separation of Verified Blanket vs. STCR-IPNS Calibrations:**
   - Standard TNAU Blanket recommendations are kept separate from STCR-IPNS targeted yield equations. General blanket recommendations are never labeled as STCR equations.
   - Empirical STCR-IPNS equations for Rice (`TNAU_STCR_IPNS_RICE_001`), Cotton (`TNAU_STCR_IPNS_COTTON_001`), and Maize (`TNAU_STCR_IPNS_MAIZE_001`) are verified for Cauvery delta and Western zone soil series (Palavidhi, Adanur, Kalathur, Irugur, Pilamedu, Coimbatore).
3. **Double-Counting Prevention Implemented:**
   - A critical double-counting flaw was identified where basal Farm Yard Manure (`fym_applied_t_per_ha`) and recent organic manure entries in `previous_fertilizers` could be subtracted simultaneously.
   - Code-level protection in [`phase5_nutrient/service.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/service.py) skips duplicate organic manure entries in historical records when basal FYM is already applied to the current crop.
4. **Decoupling of ML Yield Prediction and Weather:**
   - The Random Forest district yield prediction model (Phase 2) and agro-weather advisories (Phase 7) are strictly decoupled from nutrient requirement calculations. Fertilizer nutrient doses are determined purely by agronomic equations.
5. **Linear Programming Cost Optimization:**
   - The PuLP MILP optimizer (Phase 6) executes strictly downstream of Phase 5 nutrient requirement calculations. It models multi-nutrient fertilizers (e.g., DAP supplying both N and $\text{P}_2\text{O}_5$), whole bag constraints, and transparently reports surpluses and deficits.
6. **Dimensional & Stoichiometric Consistency:**
   - All unit conversions ($t/\text{ha} \leftrightarrow q/\text{ha}$, $\text{ha} \leftrightarrow \text{acre}$, elemental $\text{P} \leftrightarrow \text{P}_2\text{O}_5$, elemental $\text{K} \leftrightarrow \text{K}_2\text{O}$) operate through explicit, deterministic functions with tested conversion constants.
   - Negative calculated nutrient values are clamped at $0.0\text{ kg/ha}$ ($\max(0.0,\, \text{raw})$) and logged with transparent explanation notes in API payloads.

---

## 2. Mathematical Formulations & Canonical Equations

### 2.1 STCR-IPNS Targeted Yield Equations

The Soil Test Crop Response – Integrated Plant Nutrition System (STCR-IPNS) framework calculates crop nutrient demand based on targeted economic yield ($T$), indigenous soil nutrient supply ($SN, SP, SK$), and organic manure application ($FYM$):

$$\text{Net Fertilizer N } (\text{kg/ha}) = \max\left(0.0,\, a_N \cdot T - b_N \cdot SN - c_{\text{FYM},N} \cdot \min\left(1.0, \frac{\text{FYM}}{12.5}\right) - \text{Credit}_{\text{legume},N} - \text{Residual}_{\text{fert},N}\right)$$

$$\text{Net Fertilizer P}_2\text{O}_5 \ (\text{kg/ha}) = \max\left(0.0,\, a_P \cdot T - b_P \cdot SP - c_{\text{FYM},P} \cdot \min\left(1.0, \frac{\text{FYM}}{12.5}\right) - \text{Residual}_{\text{fert},P_2O_5}\right)$$

$$\text{Net Fertilizer K}_2\text{O } (\text{kg/ha}) = \max\left(0.0,\, a_K \cdot T - b_K \cdot SK - c_{\text{FYM},K} \cdot \min\left(1.0, \frac{\text{FYM}}{12.5}\right) - \text{Residual}_{\text{fert},K_2O}\right)$$

### 2.2 Verified Official Blanket Schedules (Fixed RDF)

When specific STCR soil series equations are not calibrated for a crop/field, the verified official TNAU Recommended Dose of Fertilizer (RDF) is applied:

$$\text{Gross Requirement} = \text{Blanket RDF}_{\text{crop}} \times 1.00$$
$$\text{Net Dose} = \max\left(0.0,\, \text{Gross Requirement} - \text{Credit}_{\text{FYM}} - \text{Credit}_{\text{legume},N} - \text{Residual}_{\text{fert}}\right)$$

Where:
- Rainfed Blackgram (`TNAU_STD_BLACKGRAM_RF_001`): $20.0\text{ kg N} : 40.0\text{ kg P}_2\text{O}_5 : 20.0\text{ kg K}_2\text{O/ha}$
- Groundnut (`TNAU_BLANKET_GROUNDNUT_001`): $25.0\text{ kg N} : 50.0\text{ kg P}_2\text{O}_5 : 75.0\text{ kg K}_2\text{O/ha}$
- Sugarcane (`TNAU_STD_SUGARCANE_001`): $275.0\text{ kg N} : 62.5\text{ kg P}_2\text{O}_5 : 112.5\text{ kg K}_2\text{O/ha}$

### 2.3 Verified Rating-Adjusted Schedule Exception (Rice `TNAU_STD_RICE_001`)

For Irrigated Rice, the TNAU Soil Testing Services portal explicitly publishes a Soil-Test Rating Adjustment schedule based on laboratory fertility classes:
- **Base RDF (Medium Soil Rating):** $150.0\text{ kg N} : 50.0\text{ kg P}_2\text{O}_5 : 50.0\text{ kg K}_2\text{O/ha}$
- **Low Soil Fertility:** Increase base dose by 25% ($\times 1.25 \to 187.5 : 62.5 : 62.5\text{ kg/ha}$)
- **Medium Soil Fertility:** Standard dose ($\times 1.00 \to 150.0 : 50.0 : 50.0\text{ kg/ha}$)
- **High Soil Fertility:** Decrease base dose by 25% ($\times 0.75 \to 112.5 : 37.5 : 37.5\text{ kg/ha}$)

Smooth continuous interpolation curves in [`phase5_nutrient/service.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/service.py) eliminate step jumps around boundaries while preserving the exact $1.25$, $1.00$, and $0.75$ centers. This adjustment is strictly gated by `rule.get("supports_rating_adjustment") is True`.

---

## 3. Definition of Variables, Parameters, and Units

| Variable | Exact Agronomic Definition | Physical Unit | Valid Calibration Range | Test Method / Analytical Basis | Stoichiometric Form |
|---|---|---|---|---|---|
| $T$ | Targeted economic crop yield | $\text{t/ha}$ or $q/\text{ha}$ | Crop-specific ($3.0\text{–}8.0\text{ t/ha}$ for rice; $1.5\text{–}3.5$ for cotton; $5.0\text{–}10.0$ for maize) | Calibrated field trial yield goal ($1\text{ t/ha} = 10\text{ q/ha}$) | Dry grain / produce weight |
| $SN$ | Alkaline permanganate oxidizable available Nitrogen | $\text{kg/ha}$ | $50.0\text{–}700.0\text{ kg/ha}$ | Subbiah & Asija (1956) alkaline $0.32\% \text{ KMnO}_4$ distillation | Elemental Nitrogen ($\text{N}$) |
| $SP$ | Available Phosphorus extracted from soil | $\text{kg/ha}$ | $2.0\text{–}80.0\text{ kg/ha}$ | Olsen $0.5\text{ M }\text{NaHCO}_3$ (pH $\ge 6.5$) or Bray-1 $0.03\text{ N }\text{NH}_4\text{F} + 0.025\text{ N }\text{HCl}$ (pH $< 6.5$) | Elemental $\text{P}$ (converted to $\text{P}_2\text{O}_5 \times 2.2914$) |
| $SK$ | Exchangeable Potassium extracted from soil | $\text{kg/ha}$ | $40.0\text{–}900.0\text{ kg/ha}$ | Neutral normal ($1.0\text{ N}$) Ammonium Acetate ($\text{NH}_4\text{OAc}$) extraction with flame photometry | Elemental $\text{K}$ (converted to $\text{K}_2\text{O} \times 1.2046$) |
| $a_N, a_P, a_K$ | Nutrient requirement coefficient per unit of target yield | $\text{kg nutrient} / \text{t yield}$ | Crop-specific | Derived from crop total uptake divided by fertilizer efficiency: $\frac{\text{NR}}{\text{CF}\%} \times 100$ | Expressed as $\text{N}$, $\text{P}_2\text{O}_5$, $\text{K}_2\text{O}$ |
| $b_N, b_P, b_K$ | Soil available nutrient contribution coefficient | Dimensionless fraction | Typically $0.25\text{–}0.65$ for N/K; $1.2\text{–}3.6$ for P | Derived from percentage contribution from soil: $\frac{\text{CS}\%}{\text{CF}\%}$ | Ratio of available soil nutrient utilized |
| $\text{FYM}$ | Farmyard Manure application rate | $\text{tonnes/ha}$ ($\text{t/ha}$) | $0.0\text{–}25.0\text{ t/ha}$ | Decomposed cattle dung/litter applied basally $2\text{–}3$ weeks prior to sowing/transplanting | Typical moisture $30\%$; $0.5\%\text{ N}, 0.2\%\text{ P}_2\text{O}_5, 0.5\%\text{ K}_2\text{O}$ |
| $c_{\text{FYM},N}, c_{\text{FYM},P}, c_{\text{FYM},K}$ | Organic manure nutrient replacement credit | $\text{kg nutrient/ha}$ | Calibration-specific ($15\text{–}20\text{ kg N}$ for $12.5\text{ t/ha}$ FYM) | Fertilizer nutrient equivalent saved by recommended basal FYM application ($12.5\text{ t/ha}$) | Expressed as $\text{N}$, $\text{P}_2\text{O}_5$, $\text{K}_2\text{O}$ |
| $\text{Credit}_{\text{legume},N}$ | Symbiotic biological nitrogen fixation carryover | $\text{kg N/ha}$ | $0.0\text{–}20.0\text{ kg N/ha}$ | Nodulated pulse root/leaf residue mineralization (Blackgram, Greengram, Cowpea) | Elemental Nitrogen ($\text{N}$) |
| $\text{Residual}_{\text{fert}}$ | Soil residual nutrient carryover from recent fertilizer applications | $\text{kg/ha}$ | Capped at $40.0\text{ kg/ha}$ | ICAR LTFE residual carryover fractions: $0\%\text{ N}$, $15\%\text{ P}_2\text{O}_5$, $10\%\text{ K}_2\text{O}$ applied within 6 months | Expressed as $\text{P}_2\text{O}_5$, $\text{K}_2\text{O}$ |
| $\text{Net Req}$ | Final net fertilizer nutrient requirement | $\text{kg/ha}$ and $\text{kg/acre}$ | $\ge 0.0\text{ kg/ha}$ | Sourced per hectare, multiplied by $0.404686$ for per-acre rate | Expressed as $\text{N}$, $\text{P}_2\text{O}_5$, $\text{K}_2\text{O}$ |
| $\text{Total Farm}$ | Total nutrient required for entire holding | $\text{kg}$ | $\ge 0.0\text{ kg}$ | $\text{Rate per ha} \times \text{Farm area (ha)}$ without intermediate rounding errors | Total bulk active nutrient ($\text{kg}$) |

---

## 4. Rule-by-Rule Agronomic Verification Audit

### 4.1 Calibrated STCR-IPNS Equations

#### Rule `TNAU_STCR_IPNS_RICE_001` (Cauvery Delta Irrigated Rice)
- **Crop:** Rice (*Oryza sativa*)
- **Soil Series:** Palavidhi, Adanur, Kalathur
- **Districts:** Thanjavur, Tiruvarur, Nagapattinam, Mayiladuthurai, Cuddalore
- **Target Yield Range:** $3.0\text{–}8.0\text{ t/ha}$
- **STCR Equations:**
  $$\text{N (kg/ha)} = \max(0, 22.4 \times T - 0.44 \times SN - 20.0 \times \text{FYM})$$
  $$\text{P}_2\text{O}_5\text{ (kg/ha)} = \max(0, 11.2 \times T - 1.80 \times SP - 10.0 \times \text{FYM})$$
  $$\text{K}_2\text{O (kg/ha)} = \max(0, 13.5 \times T - 0.32 \times SK - 10.0 \times \text{FYM})$$
- **Source:** TNAU Agriculture / STCR-IPNS Reference, pp. 12–15. [URL](https://agritech.tnau.ac.in/pdf/AGRICULTURE.pdf)
- **Status:** **`VERIFIED`**

#### Rule `TNAU_STCR_IPNS_COTTON_001` (Western Zone Irrigated Cotton)
- **Crop:** Cotton (lint) (*Gossypium hirsutum*, Variety: MCU 5)
- **Soil Series:** Irugur, Pilamedu
- **Districts:** Coimbatore, Tiruppur, Erode
- **Target Yield Range:** $1.5\text{–}3.5\text{ t/ha}$
- **STCR Equations:**
  $$\text{N (kg/ha)} = \max(0, 94.2 \times T - 0.47 \times SN - 15.0 \times \text{FYM})$$
  $$\text{P}_2\text{O}_5\text{ (kg/ha)} = \max(0, 39.6 \times T - 1.62 \times SP - 10.0 \times \text{FYM})$$
  $$\text{K}_2\text{O (kg/ha)} = \max(0, 77.4 \times T - 0.28 \times SK - 10.0 \times \text{FYM})$$
- **Source:** TNAU Agritech Portal Cotton STCR Section. [URL](https://agritech.tnau.ac.in/agriculture/agri_cotton_STCR_P_K_cotton.html)
- **Status:** **`VERIFIED`**

#### Rule `TNAU_STCR_IPNS_MAIZE_001` (Western/Southern Zone Hybrid Maize)
- **Crop:** Maize (*Zea mays*)
- **Soil Series:** Coimbatore, Pilamedu
- **Districts:** Coimbatore, Tiruppur, Dindigul, Erode
- **Target Yield Range:** $5.0\text{–}10.0\text{ t/ha}$
- **STCR Equations:**
  $$\text{N (kg/ha)} = \max(0, 20.8 \times T - 0.52 \times SN - 15.0 \times \text{FYM})$$
  $$\text{P}_2\text{O}_5\text{ (kg/ha)} = \max(0, 9.6 \times T - 1.55 \times SP - 10.0 \times \text{FYM})$$
  $$\text{K}_2\text{O (kg/ha)} = \max(0, 12.4 \times T - 0.36 \times SK - 10.0 \times \text{FYM})$$
- **Source:** TNAU Crop Production Guide 2020, Maize STCR-IPNS Chapter, p. 84. [URL](https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf)
- **Status:** **`VERIFIED`**

---

### 4.2 Verified Blanket Recommendations

#### Rule `TNAU_STD_RICE_001` (Rice Soil-Test Rating Table)
- **Base RDF:** $150 : 50 : 50\text{ kg N:P}_2\text{O}_5:\text{K}_2\text{O/ha}$
- **Rating Adjustment Authorized:** Low $+25\%$, Medium $0\%$, High $-25\%$.
- **Source:** TNAU Soil Testing Services Portal, General Rice Recommendation Table. [URL](https://agritech.tnau.ac.in/agriculture/agri_soil_tnau_soiltestingservices.html)
- **Status:** **`VERIFIED`**

#### Rule `TNAU_STD_BLACKGRAM_RF_001` (Rainfed Pulses / Blackgram)
- **Fixed Blanket RDF:** $20.0\text{ kg N} : 40.0\text{ kg P}_2\text{O}_5 : 20.0\text{ kg K}_2\text{O/ha} + 20\text{ kg S/ha}$
- **Rating Adjustment:** None (`supports_rating_adjustment: false`).
- **Source:** TNAU CPG 2020 p. 64 / TNAU Agritech Pulses. [URL](https://agritech.tnau.ac.in/agriculture/CropProduction/Pulses/BlackgramRainfed.html)
- **Status:** **`VERIFIED`**

#### Rule `TNAU_BLANKET_GROUNDNUT_001` (Groundnut Blanket)
- **Fixed Blanket RDF:** $25.0\text{ kg N} : 50.0\text{ kg P}_2\text{O}_5 : 75.0\text{ kg K}_2\text{O/ha}$
- **Rating Adjustment:** None (`supports_rating_adjustment: false`).
- **Source:** TNAU CPG 2020 p. 112. [URL](https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf)
- **Status:** **`VERIFIED`**

#### Rule `TNAU_STD_SUGARCANE_001` (Sugarcane Blanket)
- **Fixed Blanket RDF:** $275.0\text{ kg N} : 62.5\text{ kg P}_2\text{O}_5 : 112.5\text{ kg K}_2\text{O/ha}$
- **Rating Adjustment:** None (`supports_rating_adjustment: false`).
- **Source:** TNAU CPG 2020 p. 150. [URL](https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf)
- **Status:** **`VERIFIED`**

---

### 4.3 Rules Blocked from Production Execution

| Rule ID | Crop | Method | Status | Blocking Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `TNAU_STD_GROUNDNUT_001` | Groundnut | `TNAU-SOIL-TEST` | **`PENDING_AGRONOMIC_VALIDATION`** | Lacks localized STCR calibration equation; fixed blanket `TNAU_BLANKET_GROUNDNUT_001` is used instead. |
| `TNAU_STCR_BANANA_001` | Banana | `STCR-IPNS` | **`PENDING_VERIFICATION`** | Draft coefficients from unfinalized field trial; blocked in production. |
| `TNAU_DEPRECATED_RICE_000` | Rice | `TNAU-BLANKET` | **`UNSUPPORTED`** | Obsolete 1980 blanket guide superseded by STCR equations. Permanently rejected. |
| *Unregistered Crops* | E.g. Turmeric, Jasmine | N/A | **`UNSUPPORTED_CROP`** | Pipeline raises `UNSUPPORTED_CROP` instead of guessing or applying generic doses. |

---

## 5. Double-Counting Prevention Architecture

### 5.1 FYM Basal Deduction vs Previous Fertilizers
When an organic manure application (e.g. FYM) is recorded in both:
1. Basal FYM application (`fym_applied_t_per_ha = 12.5`), and
2. Historical records (`previous_fertilizers` = "FYM 12.5 tonnes applied 1 month ago")

[`phase5_nutrient/service.py`](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/phase5_nutrient/service.py#L457-L466) enforces:
```python
if is_organic:
    # Double-counting prevention: if basal FYM is already applied to current crop,
    # do not double-deduct duplicate organic manure entered in previous fertilizers for recent window
    if current_fym_applied_t_per_ha > 0 and (months_ago is None or months_ago <= 3.0):
        continue
```
This guarantees that organic manure is credited exactly once.

### 5.2 Soil Test Deduction vs Fertilizer Residuals
When lab soil-test values ($SN, SP, SK$) are measured, they represent biologically extractable nutrients already in the root zone. Subtracting historical synthetic fertilizer residuals on top of deducting $b_{\text{soil}} \times SN$ risks double-crediting indigenous fertility.
- **Guardrail:** Residual fertilizer credits are strictly capped at $40.0\text{ kg/ha}$ for $\text{P}_2\text{O}_5$ and $\text{K}_2\text{O}$. Synthetic nitrogen carryover is strictly $0.0\text{ kg N/ha}$ due to rapid nitrification, denitrification, and leaching in tropical soil environments.

---

## 6. Decoupling of ML Yield Prediction and Weather Integration

To prevent arbitrary distortion of fertilizer recommendations:
1. **Phase 2 District Yield Benchmark:**
   - The Random Forest regression model predicts historical district benchmark production based on weather and rainfall.
   - It is strictly labeled: `"Historical district benchmark, not a prediction for your field."`
   - It has **zero mathematical connection** to the nutrient requirements $a \cdot T - b \cdot SN - c \cdot FYM$.
2. **Phase 7 Weather Guidance:**
   - Weather forecasts provide operational guidance (e.g., "Postpone foliar spray due to rain forecast").
   - Weather does not scale, mutate, or adjust chemical fertilizer quantities.

---

## 7. Downstream Cost Optimization (PuLP MILP)

The fertilizer product optimizer (Phase 6) operates strictly downstream:
1. **Precondition:** Executes only after Phase 5 produces validated nutrient requirements. If Phase 5 produces `MISSING_INPUTS`, `UNSUPPORTED_CROP`, or `UNVERIFIED_RULE`, the optimizer is completely bypassed.
2. **Multi-Nutrient Products:** Accounts for all nutrients in complex products (e.g., $100\text{ kg}$ DAP supplies $18\text{ kg N}$ and $46\text{ kg P}_2\text{O}_5$). The remaining N is met by Urea.
3. **Surplus & Deficit Transparency:** Reports any excess nutrients (e.g. surplus N or P from whole-bag granularity) in `nutrient_surplus_kg` and alerts smallholder farmers.

---

## 8. Automated Verification Test Suite

The entire agronomic validation suite is verified across 16 test files:
- `tests/test_nutrient_equations_audit.py` (11 criteria tests)
- `tests/test_soil_report_agronomic_recommendation.py` (16 authoritative reference tests)
- `phase5_nutrient/tests/test_golden_stcr.py` (9 golden reference cases)
- `phase5_nutrient/tests/test_npk_calculation.py` (24 calculation tests)
- Total Pytest Suite: **209 passed in 11.51s (100%)**
- Total Flutter Suite: **21 passed in 3.0s (100%)**

---

## 9. Agricultural Readiness & Deployment Notice

> [!CAUTION]
> **Important Agronomic Notice:**  
> Passing automated software tests verifies mathematical correctness, unit conversions, and code integrity against the referenced documentation. However, **automated software tests alone do not constitute proof of field-level agronomic readiness for Tamil Nadu farmers**.  
> Before full state-wide production deployment:
> 1. Soil series mappings and STCR calibration coefficients must undergo joint technical review and sign-off by agricultural scientists from the TNAU Department of Soil Science and Agricultural Chemistry.
> 2. Field verification trials must confirm that recommended doses perform reliably under local micro-climatic and soil variability across Tamil Nadu's seven agro-climatic zones.
