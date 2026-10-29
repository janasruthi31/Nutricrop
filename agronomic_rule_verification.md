# AgroWise AI (NutriCrop) — Agronomic Rule Verification Registry

**Date:** October 2026  
**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer for Higher Crop Yield  
**Target Region:** Tamil Nadu, India  
**Auditor:** Senior Agricultural Software Engineer & Agronomy-Data Validation Specialist  

---

## 1. Registry Architecture & Governance Standards

In compliance with the **Antigravity Master Prompt: Correct Universal Low/Medium/High Fertilizer Multipliers**, every agronomic recommendation rule in AgroWise AI must strictly adhere to the following governance rules:

1. **Explicit Source Verification:** A rule may only be marked with `verification_status: "VERIFIED"` if an authoritative, peer-reviewed, or government-published agronomic reference (TNAU Crop Production Guide, TNAU Agritech Portal, ICAR STCR Annual Reports) is cited with exact publication title, year, page or section number, and verified URL.
2. **Prohibition of Fabricated Multipliers:** Universal $\pm 25\%$ multipliers (Low $+25\%$, Medium $0\%$, High $-25\%$) are strictly prohibited across general blanket schedules. A rating-based adjustment is permitted **only** if the official source explicitly documents that adjustment for the specific crop and calibration conditions.
3. **Safe Rejection of Unsupported Rules:** Any rule lacking localized calibration or official verification must remain flagged as `PENDING_AGRONOMIC_VALIDATION` or `UNSUPPORTED`. If a farmer requests a recommendation for an unsupported crop or soil series, the production engine must return `UNSUPPORTED_CROP` or `NO_VERIFIED_RULE` instead of guessing or applying generic adjustments.
4. **Soil Interpretation vs Requirement Separation:** Diagnostic classification of soil fertility (Low, Medium, High via Alkaline $\text{KMnO}_4$, Olsen-P, and Ammonium Acetate-K) does not modify nutrient doses unless authorized by a verified crop-specific schedule.

---

## 2. Verified Crop-Specific Rules

### 2.1 Rule `TNAU_STCR_IPNS_RICE_001` — Irrigated Rice (Cauvery Delta)
- **Crop:** Rice (*Oryza sativa*)
- **Target Region / District:** Thanjavur, Tiruvarur, Nagapattinam, Mayiladuthurai, Cuddalore
- **Soil Series:** Palavidhi, Adanur, Kalathur
- **Season / Irrigation:** Kharif, Rabi, Samba, Kuruvai, Navarai | Irrigated
- **Recommendation Method:** STCR-IPNS (Soil Test Crop Response — Integrated Plant Nutrient System)
- **Target Yield Range:** $3.0 - 8.0\text{ t/ha}$
- **Required Inputs & Units:**
  - Soil Nitrogen: $\text{kg/ha}$ (Alkaline $\text{KMnO}_4$)
  - Soil Phosphorus: $\text{kg/ha}$ (Olsen-P)
  - Soil Potassium: $\text{kg/ha}$ ($\text{NH}_4\text{OAc}$-K)
  - Target Yield ($T$): $\text{t/ha}$
  - Organic Manure ($FYM$): $\text{t/ha}$
- **STCR Calibration Equations:**
  $$\text{Target N (kg/ha)} = \max(0, 22.4 \times T - 0.44 \times SN - 20.0 \times \text{FYM})$$
  $$\text{Target P}_2\text{O}_5\text{ (kg/ha)} = \max(0, 11.2 \times T - 1.80 \times SP - 10.0 \times \text{FYM})$$
  $$\text{Target K}_2\text{O (kg/ha)} = \max(0, 13.5 \times T - 0.32 \times SK - 10.0 \times \text{FYM})$$
- **Supports Rating Adjustment Multipliers:** **NO** (`supports_rating_adjustment: false`). Target yield equation accounts continuously for soil nutrient supply.
- **Authoritative Publication:**
  - *Title:* TNAU Agriculture / STCR-IPNS Reference
  - *Section:* STCR-IPNS Rice Calibration Tables, pp. 12–15
  - *URL:* [https://agritech.tnau.ac.in/pdf/AGRICULTURE.pdf](https://agritech.tnau.ac.in/pdf/AGRICULTURE.pdf)
- **Verification Status:** **VERIFIED**

---

### 2.2 Rule `TNAU_STCR_IPNS_COTTON_001` — Irrigated Cotton (Western Zone)
- **Crop:** Cotton (lint) (*Gossypium hirsutum*)
- **Variety:** MCU 5
- **Target Region / District:** Coimbatore, Tiruppur, Erode
- **Soil Series:** Irugur, Pilamedu
- **Season / Irrigation:** Kharif, Winter | Irrigated
- **Recommendation Method:** STCR-IPNS
- **Target Yield Range:** $1.5 - 3.5\text{ t/ha}$
- **Required Inputs & Units:**
  - Soil Nitrogen: $\text{kg/ha}$
  - Soil Phosphorus: $\text{kg/ha}$ (Olsen-P)
  - Soil Potassium: $\text{kg/ha}$ ($\text{NH}_4\text{OAc}$-K)
  - Target Yield ($T$): $\text{t/ha}$
- **STCR Calibration Equations:**
  $$\text{Target N (kg/ha)} = \max(0, 94.2 \times T - 0.47 \times SN - 15.0 \times \text{FYM})$$
  $$\text{Target P}_2\text{O}_5\text{ (kg/ha)} = \max(0, 39.6 \times T - 1.62 \times SP - 10.0 \times \text{FYM})$$
  $$\text{Target K}_2\text{O (kg/ha)} = \max(0, 77.4 \times T - 0.28 \times SK - 10.0 \times \text{FYM})$$
- **Supports Rating Adjustment Multipliers:** **NO** (`supports_rating_adjustment: false`).
- **Authoritative Publication:**
  - *Title:* TNAU Agritech Portal — Cotton STCR P & K Equations
  - *Section:* Irrigated Cotton on Irugur and Pilamedu Series
  - *URL:* [https://agritech.tnau.ac.in/agriculture/agri_cotton_STCR_P_K_cotton.html](https://agritech.tnau.ac.in/agriculture/agri_cotton_STCR_P_K_cotton.html)
- **Verification Status:** **VERIFIED**

---

### 2.3 Rule `TNAU_STCR_IPNS_MAIZE_001` — Hybrid Maize (Western/Southern Zone)
- **Crop:** Maize (*Zea mays*)
- **Target Region / District:** Coimbatore, Tiruppur, Dindigul, Erode
- **Soil Series:** Coimbatore, Pilamedu
- **Season / Irrigation:** Kharif, Rabi | Irrigated
- **Recommendation Method:** STCR-IPNS
- **Target Yield Range:** $5.0 - 10.0\text{ t/ha}$
- **STCR Calibration Equations:**
  $$\text{Target N (kg/ha)} = \max(0, 20.8 \times T - 0.52 \times SN - 15.0 \times \text{FYM})$$
  $$\text{Target P}_2\text{O}_5\text{ (kg/ha)} = \max(0, 9.6 \times T - 1.55 \times SP - 10.0 \times \text{FYM})$$
  $$\text{Target K}_2\text{O (kg/ha)} = \max(0, 12.4 \times T - 0.36 \times SK - 10.0 \times \text{FYM})$$
- **Supports Rating Adjustment Multipliers:** **NO** (`supports_rating_adjustment: false`).
- **Authoritative Publication:**
  - *Title:* TNAU Crop Production Guide 2020
  - *Section:* Maize STCR-IPNS Chapter, p. 84
  - *URL:* [https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf](https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf)
- **Verification Status:** **VERIFIED**

---

### 2.4 Rule `TNAU_STD_RICE_001` — Soil-Test-Based Irrigated Rice (Authorized Rating Adjustment Exception)
- **Crop:** Rice (*Oryza sativa*)
- **Target Region / District:** State-wide (Tamil Nadu)
- **Soil Series:** General (when specific Cauvery delta STCR soil series is unmapped)
- **Season / Irrigation:** All seasons | Irrigated
- **Recommendation Method:** TNAU-SOIL-TEST
- **Recommendation Type:** GENERAL_BLANKET / SOIL_TEST_RATING
- **Base Blanket RDF:**
  $$\text{Base RDF} = 150.0\text{ kg N} : 50.0\text{ kg P}_2\text{O}_5 : 50.0\text{ kg K}_2\text{O / ha}$$
- **Supports Rating Adjustment Multipliers:** **YES** (`supports_rating_adjustment: true`).
- **Authorized Adjustment Factors:**
  - **Low Soil Fertility:** Increase dose by 25% ($\times 1.25$) $\to 187.5 : 62.5 : 62.5\text{ kg/ha}$
  - **Medium Soil Fertility:** Standard dose ($\times 1.00$) $\to 150.0 : 50.0 : 50.0\text{ kg/ha}$
  - **High Soil Fertility:** Decrease dose by 25% ($\times 0.75$) $\to 112.5 : 37.5 : 37.5\text{ kg/ha}$
- **Authoritative Publication:**
  - *Title:* TNAU Soil Testing Services Portal — General Rice Recommendation Table
  - *Section:* Irrigated Rice Soil Test Rating Matrix
  - *URL:* [https://agritech.tnau.ac.in/agriculture/agri_soil_tnau_soiltestingservices.html](https://agritech.tnau.ac.in/agriculture/agri_soil_tnau_soiltestingservices.html)
- **Verification Status:** **VERIFIED**

---

### 2.5 Rule `TNAU_STD_BLACKGRAM_RF_001` — Rainfed Pulses (Blackgram)
- **Crop:** Blackgram (*Vigna mungo*)
- **Target Region / District:** State-wide (Tamil Nadu)
- **Season / Irrigation:** Kharif, Rabi, Rainfed | Rainfed
- **Recommendation Method:** TNAU-SOIL-TEST
- **Recommendation Type:** GENERAL_BLANKET
- **Verified Blanket RDF:**
  $$\text{Fixed RDF} = 20.0\text{ kg N} : 40.0\text{ kg P}_2\text{O}_5 : 20.0\text{ kg K}_2\text{O / ha} + 20\text{ kg S/ha (gypsum)}$$
- **Supports Rating Adjustment Multipliers:** **NO** (`supports_rating_adjustment: false`).
- **Agronomic Audit Decision:** Soil ratings (Low, Medium, High) provide diagnostic interpretation only. Blanket recommendation is fixed ($20:40:20\text{ kg/ha}$) with multiplier strictly set to $1.00$.
- **Authoritative Publication:**
  - *Title:* TNAU Rainfed Pulses Production Guide & CPG 2020
  - *Section:* Rainfed Blackgram Nutrient Management, p. 64
  - *URL:* [https://agritech.tnau.ac.in/agriculture/CropProduction/Pulses/BlackgramRainfed.html](https://agritech.tnau.ac.in/agriculture/CropProduction/Pulses/BlackgramRainfed.html)
- **Verification Status:** **VERIFIED**

---

### 2.6 Rule `TNAU_BLANKET_GROUNDNUT_001` — General Blanket Groundnut
- **Crop:** Groundnut (*Arachis hypogaea*)
- **Target Region / District:** State-wide (Tamil Nadu)
- **Season / Irrigation:** Kharif, Rabi, Summer | Both (Irrigated & Rainfed)
- **Recommendation Method:** TNAU-BLANKET
- **Recommendation Type:** GENERAL_BLANKET
- **Verified Blanket RDF:**
  $$\text{Fixed RDF} = 25.0\text{ kg N} : 50.0\text{ kg P}_2\text{O}_5 : 75.0\text{ kg K}_2\text{O / ha}$$
- **Supports Rating Adjustment Multipliers:** **NO** (`supports_rating_adjustment: false`). Multipliers strictly $1.00$.
- **Authoritative Publication:**
  - *Title:* TNAU Crop Production Guide 2020 Oilseeds Section
  - *Section:* Groundnut General Blanket Schedule, p. 112
  - *URL:* [https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf](https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf)
- **Verification Status:** **VERIFIED**

---

### 2.7 Rule `TNAU_STD_SUGARCANE_001` — Sugarcane Plant Crop
- **Crop:** Sugarcane (*Saccharum officinarum*)
- **Target Region / District:** State-wide (Tamil Nadu)
- **Season / Irrigation:** All seasons | Irrigated
- **Recommendation Method:** TNAU-BLANKET
- **Recommendation Type:** GENERAL_BLANKET
- **Verified Blanket RDF:**
  $$\text{Fixed RDF} = 275.0\text{ kg N} : 62.5\text{ kg P}_2\text{O}_5 : 112.5\text{ kg K}_2\text{O / ha}$$
- **Supports Rating Adjustment Multipliers:** **NO** (`supports_rating_adjustment: false`).
- **Authoritative Publication:**
  - *Title:* TNAU Crop Production Guide 2020 Commercial Crops Section
  - *Section:* Sugarcane Recommendation, p. 150
  - *URL:* [https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf](https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf)
- **Verification Status:** **VERIFIED**

---

## 3. Rules Pending Agronomic Validation or Unsupported

The following rules have been safely blocked from production execution. If selected without explicit test flags, the pipeline returns `UNVERIFIED_RULE`, `PENDING_AGRONOMIC_VALIDATION`, or `UNSUPPORTED_CROP`:

| Rule ID | Crop | Target Condition | Reason Pending / Unsupported | Current System Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `TNAU_STD_GROUNDNUT_001` | Groundnut | Targeted Yield (Uncalibrated) | Equation coefficients lack official TNAU STCR cell validation for specific soil series. Standard blanket `TNAU_BLANKET_GROUNDNUT_001` is used instead. | **PENDING_AGRONOMIC_VALIDATION**. Blocked from unvalidated target yield calculations. |
| `TNAU_STCR_BANANA_001` | Banana (*Grand Naine*) | Theni / Tiruchirapalli (Thonnackal series) | Draft calibration coefficients pending field validation by TNAU STCR committee. | **PENDING_VERIFICATION**. Blocked from production. Yields `UNVERIFIED_RULE` warning. |
| `TNAU_DEPRECATED_RICE_000` | Rice | Local Varieties | Obsolete 1980 blanket dosing guide superseded by STCR-IPNS equations. | **UNSUPPORTED**. Production calculation path strictly rejects this rule. |
| *Crops lacking rules* (e.g. Turmeric, Jasmine, Tapioca, Coconut) | Various | Any | No verified TNAU STCR calibration or official digital rule entry exists in registry. | **UNSUPPORTED_CROP**. Returns safe error payload without inventing fertilizer doses. |

---

## 4. Verification Compliance Summary

- **Total Registered Rules in Registry:** 9
- **Verified Production Rules:** 7 (Rice STCR, Cotton STCR, Maize STCR, Rice Soil-Test Table, Blackgram Blanket, Groundnut Blanket, Sugarcane Blanket)
- **Rules Authorizing Soil-Rating Multipliers:** 1 (`TNAU_STD_RICE_001`)
- **Rules Enforcing Fixed Blanket RDF (Multiplier 1.00):** 3 (`TNAU_STD_BLACKGRAM_RF_001`, `TNAU_BLANKET_GROUNDNUT_001`, `TNAU_STD_SUGARCANE_001`)
- **Rules Pending Validation:** 2 (`TNAU_STD_GROUNDNUT_001`, `TNAU_STCR_BANANA_001`)
- **Deprecated / Unsupported Rules:** 1 (`TNAU_DEPRECATED_RICE_000`)
