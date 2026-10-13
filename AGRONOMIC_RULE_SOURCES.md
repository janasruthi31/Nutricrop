# Agronomic Rule Sources and Mathematical Formulation

**Project Title:** AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Authority:** Tamil Nadu Agricultural University (TNAU) & ICAR All India Coordinated Research Project on Soil Test Crop Response (AICRP-STCR)  

---

## 1. Agronomic Authority & Literature Sources

The fertilizer requirement engine is strictly grounded in calibrated Soil Test Crop Response (STCR) and Integrated Plant Nutrition System (IPNS) field trials conducted across agro-climatic zones of Tamil Nadu.

### Primary References from Source Registry (`data/agronomy/source_registry.csv`):
1. **TNAU Crop Production Guide (CPG) – Agriculture (2020):** Directorate of Agriculture, Government of Tamil Nadu & Tamil Nadu Agricultural University, Coimbatore.
2. **STCR Calibration Bulletin for Tamil Nadu Soils (2018):** Department of Soil Science & Agricultural Chemistry, TNAU Coimbatore.
3. **ICAR-AICRP on STCR Annual Progress Reports (2015–2022):** Indian Council of Agricultural Research, New Delhi.
4. **Soil Series of Tamil Nadu & Fertilizer Recommendations:** Soil Survey and Land Use Organization, Department of Agriculture, Government of Tamil Nadu.

---

## 2. Mathematical Formulation of STCR-IPNS Equations

The STCR approach calculates targeted yield fertilizer doses based on three physiological parameters:
1. **Nutrient Requirement (NR):** Amount of nutrient (kg) required to produce one quintal (100 kg) of economic yield.
2. **Percentage Contribution from Soil (CS%):** Efficiency of indigenous soil available nutrients.
3. **Percentage Contribution from Fertilizer (CF%):** Efficiency of added chemical fertilizer nutrients.
4. **Percentage Contribution from Organic Manure (CO%):** Efficiency of Farm Yard Manure (FYM) nutrients.

### Canonical Mathematical Equations:
$$\text{Fertilizer } N \ (\text{kg/ha}) = a \cdot T - b \cdot \text{SN} - c \cdot \text{ON}$$
$$\text{Fertilizer } P_2O_5 \ (\text{kg/ha}) = d \cdot T - e \cdot \text{SP} - f \cdot \text{OP}$$
$$\text{Fertilizer } K_2O \ (\text{kg/ha}) = g \cdot T - h \cdot \text{SK} - i \cdot \text{OK}$$

Where:
- $T$ = Targeted crop yield in quintals per hectare ($q/\text{ha}$).
- $\text{SN}$ = Alkaline permanganate oxidizable available Nitrogen in soil ($\text{kg/ha}$).
- $\text{SP}$ = Available Phosphorus by Olsen's method (neutral/alkaline soils) or Bray-1 method (acid soils) ($\text{kg/ha}$).
- $\text{SK}$ = Neutral normal ammonium acetate exchangeable Potassium ($\text{kg/ha}$).
- $\text{ON}, \text{OP}, \text{OK}$ = Quantity of nutrients contributed by Farm Yard Manure ($\text{kg/ha}$), calculated as $\text{FYM tonnes} \times \text{nutrient content} \times \text{efficiency factor}$.

---

## 3. Verified Crop Rule Inventory (`data/agronomy/tnau_stcr_rules.json`)

| Rule Identifier | Crop | Soil Series / Tract | Target Range (q/ha) | Status | Verification Note |
|---|---|---|---|---|---|
| `TNAU_RICE_STCR_001` | **Rice (Paddy)** | Adanur Series (Clay loam) | 50 – 80 | **VERIFIED** | TNAU CPG 2020 verified for Kuruvai/Thaladi |
| `TNAU_RICE_STCR_002` | **Rice (Paddy)** | Kalathur Series (Heavy clay) | 50 – 85 | **VERIFIED** | Cauvery Delta Cauvery alluvium calibrated |
| `TNAU_COTTON_STCR_001`| **Cotton** | Perianaickenpalayam (Black) | 20 – 35 | **VERIFIED** | Winter irrigated Cambodia cotton |
| `TNAU_MAIZE_STCR_001` | **Hybrid Maize**| Irugur Series (Red sandy loam) | 60 – 100 | **VERIFIED** | High-yielding kharif/rabi grain hybrids |
| `TNAU_GROUNDNUT_001` | **Groundnut** | Pilamedu Series (Sandy clay) | 20 – 35 | **VERIFIED** | Semi-spreading groundnut with gypsum |
| `TNAU_SUGARCANE_001` | **Sugarcane** | Cumbu-Coimbatore tract | 1000 – 1500 | **VERIFIED** | Plant crop in Western Agro-climatic zone |
| `TNAU_BLACKGRAM_001` | **Blackgram** | Vamban / Cauvery Alluvium | 8 – 15 | **VERIFIED** | Pulse crop STCR with rhizobium inoculation |
| `TNAU_BANANA_PENDING` | **Banana (Grand Naine)**| Alluvial soils | 400 – 600 | **PENDING** | Equation under empirical re-verification; blocked in production |
| `TNAU_RICE_BLANKET_OLD`| **Rice (1980 Blanket)**| Universal | Fixed | **UNSUPPORTED** | Deprecated 1980 blanket dose; rejected by policy |

---

## 4. Methodological Distinctions & Nutrient Conversion Integrity

### 4.1 Elemental vs. Oxide Forms
Soil test laboratories and fertilizer commercial products express Phosphorus and Potassium in different chemical conventions:
- **Phosphorus:**
  $$\text{Elemental P} \times 2.29 = P_2O_5$$
  $$\text{Olsen P (kg/ha)} \times 2.29 = P_2O_5 \text{ equivalent}$$
- **Potassium:**
  $$\text{Elemental K} \times 1.20 = K_2O$$
  $$\text{Ammonium Acetate K (kg/ha)} \times 1.20 = K_2O \text{ equivalent}$$

The calculation engine in `phase5_nutrient/service.py` preserves this exact stoichiometric conversion to ensure that fertilizer bags (which are sold in terms of $\% P_2O_5$ and $\% K_2O$) match the crop's physiological demand.

### 4.2 Olsen vs. Bray Phosphorus Methods
- Neutral to alkaline soils ($\text{pH} > 6.5$) prevalent across the Cauvery Delta, Coimbatore, and Southern Tamil Nadu use **Olsen's $0.5\text{ M } \text{NaHCO}_3$ extraction**.
- Acid soils ($\text{pH} < 6.5$) in the Western Ghats (Nilgiris, parts of Dindigul) utilize **Bray-1 extraction**.
- The validation service inspects soil pH and measurement method; Bray-1 values are never converted to Olsen values without the specific soil buffering multiplier.
