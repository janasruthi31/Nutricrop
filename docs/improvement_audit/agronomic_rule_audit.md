# Agronomic Rule Engine Audit & Scientific Verification
**Application Name:** AgroWise AI  
**Project Reference:** SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield  
**Module:** Phase 4 (Agronomic Rule Selection) & Phase 5 (Deterministic NPK Engine)  

---

## 1. Scientific Basis & TNAU STCR-IPNS Methodology

The Tamil Nadu Agricultural University (TNAU) Soil Test Crop Response (STCR) Integrated Plant Nutrition System (IPNS) establishes quantitative polynomial calibrations between targeted crop yield ($T$), initial soil available nutrients ($SN, SP, SK$), organic manure credits ($FYM$), and the required chemical fertilizer doses:

$$\text{Fertilizer N (kg/ha)} = a_N \cdot T - b_N \cdot SN - c_N \cdot FYM$$
$$\text{Fertilizer P}_2\text{O}_5\text{ (kg/ha)} = a_P \cdot T - b_P \cdot SP - c_P \cdot FYM$$
$$\text{Fertilizer K}_2\text{O (kg/ha)} = a_K \cdot T - b_K \cdot SK - c_K \cdot FYM$$

Where:
* $T$: Target yield in tonnes per hectare ($t/ha$).
* $SN, SP, SK$: Initial available soil Nitrogen (alkaline permanganate), Phosphorus (Olsen P or Bray P), and Potassium (neutral normal ammonium acetate) in $kg/ha$.
* $a_i$: Nutrient requirement coefficient per unit economic produce.
* $b_i$: Percentage contribution from soil available nutrients.
* $c_i$: Percentage contribution from organic manure (standard calibration: 12.5 t/ha Farmyard Manure).

---

## 2. Complete Inventory of Agronomic Rules

| Rule ID | Crop | Cultivation | Soil Series | Target Yield Range | Status | Authoritative Scientific Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TNAU_STCR_IPNS_RICE_001` | Rice (Paddy) | Irrigated | Palavidhi, Adanur, Kalathur | 3.0 – 8.0 t/ha | `VERIFIED` | TNAU STCR Cell, *Calibration for Irrigated Rice in Cauvery Delta*, TNAU Agriculture Guide. |
| `TNAU_STCR_IPNS_COTTON_001`| Cotton (lint) | Irrigated (MCU 5) | Irugur, Pilamedu | 1.5 – 3.5 t/ha | `VERIFIED` | TNAU Cotton STCR, *STCR P & K equations on Irugur/Pilamedu series*. |
| `TNAU_STCR_IPNS_MAIZE_001` | Hybrid Maize | Irrigated | Coimbatore, Pilamedu | 5.0 – 10.0 t/ha | `VERIFIED` | TNAU Crop Production Guide 2020, *Maize STCR-IPNS Chapter, p. 84*. |
| `TNAU_STD_RICE_001` | Rice | Irrigated | Non-specific | Blanket (150:50:50) | `VERIFIED` | TNAU Soil Testing Services, *General Rice Soil-Test Rating Adjustment Table*. |
| `TNAU_STD_BLACKGRAM_RF_001`| Blackgram | Rainfed | Non-specific | Blanket (20:40:20) | `VERIFIED` | TNAU Rainfed Pulses Production Guide, *Blackgram Rainfed Nutrient Management*. |
| `TNAU_BLANKET_GROUNDNUT_001`| Groundnut | Irrigated/Rainfed| Non-specific | Blanket (25:50:75) | `VERIFIED` | TNAU Crop Production Guide 2020, *Oilseeds Section, p. 112*. |
| `TNAU_STD_SUGARCANE_001` | Sugarcane | Irrigated | Non-specific | Blanket (275:62.5:112.5) | `VERIFIED` | TNAU Crop Production Guide 2020, *Commercial Crops Section, p. 150*. |
| `TNAU_STD_GROUNDNUT_001` | Groundnut | Both | Non-specific | Uncalibrated STCR | `PENDING_AGRONOMIC_VALIDATION`| Blocked from production. Awaiting official TNAU target-yield calibration committee release. |
| `TNAU_STCR_BANANA_001` | Banana (Grand Naine) | Irrigated | Thonnackal | 40.0 – 70.0 t/ha | `PENDING_VERIFICATION` | Blocked from production. Draft equation undergoing field validation trials. |
| `TNAU_DEPRECATED_RICE_000` | Rice | Irrigated | Obsolete | Fixed 1980 dose | `UNSUPPORTED` | Blocked permanently. Superceded by STCR-IPNS targeted yield equations. |

---

## 3. Explicit Rule Selection & Precedence Gating

The rule selection engine (`agronomy/service.py`) follows strict mathematical precedence:
1. **Filter Compatibility:** Checks crop identity, irrigation method (irrigated vs. rainfed), season (Kharif, Rabi, etc.), target yield range, and soil series.
2. **Verification Gate:** Only rules with `verification_status == "VERIFIED"` are eligible for production recommendations. Any unverified or pending rule returns a clear diagnostic warning and is blocked from generating fertilizer purchase plans.
3. **Scoring Hierarchy:**
   - Specific STCR-IPNS targeted yield rule: **+100 base points**.
   - STCR-NPK fertilizer-only rule: **+80 base points**.
   - Standard TNAU soil-test rating adjustment rule: **+50 base points**.
   - Exact soil series match: **+20 points**.
   - Target yield inside validated range: **+15 points**.
   - All required laboratory inputs present: **+200 points**.
4. **No Silent Substitution:** The engine never substitutes an unrelated crop's equation. If Groundnut is requested without a soil-specific STCR equation, the system explicitly requires user selection or provides the verified `TNAU_BLANKET_GROUNDNUT_001` general blanket recommendation with rating adjustments.

---

## 4. Stoichiometric Units & Area Normalization

### Elemental vs. Oxide Nutrients
* Soil testing laboratories in India report available Phosphorus ($P$) and Potassium ($K$) as elemental $kg/ha$.
* Commercial fertilizer products are formulated and labeled as oxides: Phosphate ($P_2O_5$) and Potash ($K_2O$).
* The TNAU STCR polynomial equations output fertilizer requirements directly in oxide equivalents ($P_2O_5$ and $K_2O$).
* Stoichiometric conversions:
  $$P_2O_5 = P \times 2.291 \quad \Longleftrightarrow \quad P = P_2O_5 \times 0.4364$$
  $$K_2O = K \times 1.205 \quad \Longleftrightarrow \quad K = K_2O \times 0.8302$$
* **Conversion Guard:** AgroWise AI never double-converts elemental measurements. If a Soil Health Card already reports values in $P_2O_5$ or $K_2O$, the system converts them to elemental form prior to STCR formula evaluation.

### Farm Area Scaling
* $1\text{ hectare} = 2.4710538\text{ acres} \quad \Longleftrightarrow \quad 1\text{ acre} = 0.4046856\text{ ha}$.
* Farm total requirements ($kg$) are calculated directly:
  $$\text{Total Farm Requirement (kg)} = \text{Per-Hectare Rate (kg/ha)} \times \text{Farm Area (ha)}$$
* Independent unit invariance is preserved: 1 acre calculated directly yields the exact identical farm total as 0.4047 ha.

---

## 5. Negative Calculated Fertilizer Handling

When soil nutrient levels are exceptionally high or when substantial organic manure (FYM) is credited, the raw polynomial formula $a \cdot T - b \cdot S - c \cdot FYM$ may compute a negative value ($< 0$).
* **Scientific Explanation:** A negative value indicates that the soil reservoir alone is sufficient to support the target yield without supplementary synthetic chemical fertilizer.
* **Non-Silent Clamping:** The system clamps the rate to $0.0\text{ kg/ha}$ (maintenance dose) and explicitly records the event in `calc_details["clamping_notes"]` and user `warnings`:
  > *"Calculated Nitrogen requirement was negative (-12.4 kg/ha) because initial soil Nitrogen test level or FYM contribution satisfies target yield requirement. Clamped to 0.0 kg/ha (maintenance dose / no additional chemical N needed per TNAU STCR principles)."*
