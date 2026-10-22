# Agronomic Rule Coverage & STCR-IPNS Validation Report (Phase 4)

**Date:** 2026-10-21  
**Project:** AgroWise AI (Agronomic Recommendation Engine)  
**Status:** Audited, Formally Governed & Source-Referenced  
**Authoritative References:** TNAU Crop Production Guide (CPG 2020), TNAU Department of Soil Science & Agricultural Chemistry, All India Coordinated Research Project on STCR (ICAR-IISS).

---

## 1. Executive Summary

A critical flaw in agricultural AI decision-support tools is the fabrication of generic fertilizer rates presented as "AI-calibrated" or "soil-specific" recommendations. 

In AgroWise AI, **Non-Negotiable Rule 6** governs all agronomic decisions:  
> *"Never use generic fertilizer rates as though they were verified soil-specific STCR-IPNS recommendations. If an agronomic rule is not verified, halt with a transparent limitation and request agronomic verification."*

The agronomic engine strictly distinguishes between:
1. **Soil-Specific STCR-IPNS Equations:** Soil-series calibrated, target-yield driven mathematical response equations accounting for available soil nutrients and organic manure credits.
2. **Authoritative Blanket Recommendations:** Published state-level Recommended Dose of Fertilizers (RDF) from TNAU CPG 2020 used only when soil series calibration is unavailable.
3. **Provisional / Unverified Rules:** Explicitly gated behind confirmation flags, accompanied by prominent warnings.
4. **Unsupported Crops:** Strictly blocked with `UNSUPPORTED_CROP` status. The system refuses to fabricate nutrient doses for crops without verified agronomic backing.
5. **Soil Health Card Mode:** Direct preservation and scaling of printed laboratory recommendations from uploaded cards.

---

## 2. Rule Registry & Calibration Equations

### 2.1 Verified STCR-IPNS Equations

| Rule ID | Crop | Soil Series & Districts | Yield Target ($T$) | Calibration Equation (kg/ha) | Manure Credit (FYM 12.5 t/ha) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TNAU_STCR_IPNS_RICE_001` | Rice (*Oryza sativa*) | Palavidhi, Adanur, Kalathur (Cauvery Delta) | 5.0 – 7.0 t/ha | $FN = 4.39 T - 0.52 SN - 0.84 ON$<br>$FP_2O_5 = 2.22 T - 1.63 SP - 0.98 OP$<br>$FK_2O = 2.44 T - 0.39 SK - 0.81 OK$ | $ON = 35.0$<br>$OP = 17.5$<br>$OK = 35.0$ | **VERIFIED** (TNAU CPG 2020) |
| `TNAU_STCR_IPNS_COTTON_001` | Cotton (*Gossypium hirsutum*) | Irugur, Pilamedu (Western Zone) | 2.0 – 3.5 t/ha | $FN = 10.9 T - 0.51 SN - 0.78 ON$<br>$FP_2O_5 = 4.80 T - 2.11 SP - 0.85 OP$<br>$FK_2O = 8.60 T - 0.28 SK - 0.72 OK$ | $ON = 35.0$<br>$OP = 17.5$<br>$OK = 35.0$ | **VERIFIED** (TNAU Cotton STCR) |
| `TNAU_STCR_IPNS_MAIZE_001` | Hybrid Maize (*Zea mays*) | Coimbatore, Pilamedu (Western Zone) | 7.0 – 10.0 t/ha | $FN = 3.75 T - 0.54 SN - 0.74 ON$<br>$FP_2O_5 = 1.65 T - 1.58 SP - 0.82 OP$<br>$FK_2O = 2.10 T - 0.24 SK - 0.65 OK$ | $ON = 35.0$<br>$OP = 17.5$<br>$OK = 35.0$ | **VERIFIED** (TNAU STCR-IPNS) |

*Notation:*
* $FN, FP_2O_5, FK_2O$: Fertilizer nutrient requirement to be applied (kg/ha).
* $T$: Target yield in tonnes/hectare.
* $SN, SP, SK$: Alkaline permanganate N, Olsen P, and Neutral normal ammonium acetate K (kg/ha).
* $ON, OP, OK$: Nutrient contribution from organic manure (kg/ha).

---

### 2.2 Verified Authoritative Blanket Recommendations (TNAU CPG 2020)

Used strictly when soil series STCR equations are not available for the farmer's location:

| Rule ID | Crop | Target Condition | Blanket RDF (N - P₂O₅ - K₂O kg/ha) | Application Method | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TNAU_STD_RICE_001` | Rice | Medium duration, irrigated | 120 - 40 - 40 | 3 Splits: 50% Basal, 25% Tillering, 25% PI | **VERIFIED** |
| `TNAU_STD_BLACKGRAM_RF_001` | Blackgram | Rainfed pulses | 25 - 50 - 25 | 100% Basal at sowing | **VERIFIED** |
| `TNAU_BLANKET_GROUNDNUT_001` | Groundnut | Rainfed/Irrigated | 25 - 50 - 75 | Basal + Gypsum at 40-45 DAS | **VERIFIED** |
| `TNAU_STD_SUGARCANE_001` | Sugarcane | Plant crop | 275 - 62.5 - 112.5 | 3 Splits: 30, 60, 90 DAP | **VERIFIED** |

---

### 2.3 Provisional & Pending Validation Rules

| Rule ID | Crop | Soil Series | Limitation & Pending Requirement | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TNAU_STCR_BANANA_001` | Banana (Grand Naine) | Thonnackal | Equation derived from limited trial plots; pending multi-district verification by TNAU. Blocked from production use unless `allow_unverified=True` is explicitly passed. | **PENDING_VERIFICATION** |
| `TNAU_STD_GROUNDNUT_001` | Groundnut | Red Sandy Loam | Unverified coefficient set. Superseded by `TNAU_BLANKET_GROUNDNUT_001`. | **PENDING_AGRONOMIC_VALIDATION** |
| `TNAU_DEPRECATED_RICE_000` | Rice | Generic | Legacy unreferenced rule. Permanently blocked. | **UNSUPPORTED** |

---

### 2.4 Unsupported Crop Catalog (Refusal to Fabricate Doses)

The following crops are registered in the Tamil Nadu agricultural yield dataset or commonly grown across the state, but currently lack verified STCR-IPNS equations in the system registry:

```
Ragi, Sorghum (Jowar), Bajra (Cumbu), Redgram (Pigeon Pea), Greengram,
Sesame (Gingelly), Sunflower, Soybean, Tapioca (Cassava), Turmeric,
Tomato, Brinjal (Eggplant), Bhendi (Okra), Onion, Potato, Cabbage,
Cauliflower, Mango, Guava, Coconut, Coffee, Tea, Cardamom, Cashewnut,
Chilli, Jasmine, Rose, Crossandra, Chrysanthemum, Fodder Sorghum.
```

**Policy when an unsupported crop is selected:**
1. The engine returns HTTP 200 with `status: "UNSUPPORTED_CROP"`.
2. No fertilizer quantities are computed or returned (`recommended_products: []`).
3. The farmer is informed with an actionable advisory:
   > *"Agronomic rule coverage for '{crop}' is not currently calibrated in the verified TNAU registry. AgroWise AI does not fabricate fertilizer recommendations without authoritative calibration. Please consult your local Krishi Vigyan Kendra (KVK) or Assistant Director of Agriculture (ADA) office for local package of practices."*

---

## 3. Soil Health Card Report Interpretation & Safety Checks

### 3.1 Parameter Extraction & Range Validation
Extracted parameters are validated against physiological bounds established by TNAU Soil Testing Laboratories:

| Parameter | Canonical Unit | Plausible Range | Deficiency Threshold | Toxic / High Threshold |
| :--- | :--- | :--- | :--- | :--- |
| Soil Reaction ($pH$) | pH scale | 3.5 – 10.5 | Acidic: $< 6.5$ | Alkaline: $> 8.5$ |
| Electrical Conductivity ($EC$) | dS/m | 0.0 – 16.0 | Normal: $< 1.0$ | Saline: $> 2.0$ |
| Available Nitrogen ($N$) | kg/ha | 50 – 700 | Low: $< 280$ | High: $> 450$ |
| Available Phosphorus ($P$) | kg/ha | 2 – 150 | Low: $< 11.0$ | High: $> 22.0$ |
| Available Potassium ($K$) | kg/ha | 20 – 1200 | Low: $< 118$ | High: $> 280$ |
| Organic Carbon ($OC$) | % | 0.05 – 3.0 | Low: $< 0.5$ | High: $> 0.75$ |
| Zinc ($Zn$) | ppm | 0.1 – 20.0 | Deficient: $< 1.2$ | Sufficient: $\ge 1.2$ |
| Iron ($Fe$) | ppm | 0.5 – 100.0 | Deficient: $< 3.7$ | Sufficient: $\ge 3.7$ |

### 3.2 Farmer Confirmation & Review Workflow
- Ambiguous OCR readings (confidence $< 80\%$) are marked `status: "UNCERTAIN"` requiring farmer manual confirmation before calculation.
- Soil test measurements are explicitly labeled as soil fertility ratings and never confused with fertilizer product purchase quantities.
