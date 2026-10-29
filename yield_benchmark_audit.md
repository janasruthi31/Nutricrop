# Machine Learning Yield Benchmark Audit: Target Definition, Data Pipeline & Decoupling

**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer  
**Module:** Phase 2 — District Yield Benchmark Machine Learning Model  
**Audit Scope:** Section E — Target Definition, Unit Verification, Temporal Leakage Prevention, and Agronomic Decoupling  
**Date:** 2026-10-28  

---

## 1. Executive Summary

This audit establishes the rigorous mathematical, historical, and operational definitions of the yield benchmark component in AgroWise AI. 

**Primary Finding:** The machine learning model predicts **district-average historical crop yield in kilograms per hectare ($\text{kg/ha}$)**. It does **not** predict farm-specific field yield, and its target variable is **not** total production in tonnes. Total production in tonnes is a derived farm planning estimate calculated from the predicted per-hectare yield and the farmer's confirmed field area. Furthermore, the ML yield benchmark module is **completely decoupled** from the agronomic nutrient calculation engine; ML yield predictions never alter or increase recommended fertilizer doses.

---

## 2. Target Variable Verification & Unit Ground Truth

### 2.1 Ground Truth Source: Tamil Nadu Season & Crop Reports
The underlying training dataset (`data/yield/TN_Crop_Rainfall_1998_2025.csv`) was compiled from the official **Season and Crop Reports of Tamil Nadu** published annually by the **Department of Economics and Statistics (DES), Government of Tamil Nadu**:
- **Source Publication:** *Season and Crop Report of Tamil Nadu*, Department of Economics and Statistics, Chennai.
- **Official Table:** **Table V-A ("Average Yield of Principal Crops in kg/ha")**.
- **Reported Units:**
  - Food grains (Paddy/Rice, Cholam/Maize, Cumbu, Ragi, Pulses/Blackgram), Oilseeds (Groundnut), and Commercial Fiber (Cotton lint): Published directly in **$\text{kg/ha}$**.
  - Sugarcane: Published in Table V-A in **tonnes of cane per hectare ($\text{t/ha}$)**, converted to $\text{kg/ha}$ by multiplying by $1,000$ to maintain a uniform target unit across all crops.

### 2.2 Target vs. Derived Metric Disambiguation
| Concept | Entity | Units | Ground Truth / Mathematical Formula | UI & API Role |
|---|---|---|---|---|
| **Target Variable ($Y$)** | District-Average Yield | $\text{kg/ha}$ | Table V-A of DES Season & Crop Report | Direct ML regression target |
| **Derived Estimate** | Farm Total Production | $\text{tonnes}$ | $\text{Production} = \frac{\text{Predicted Yield (kg/ha)}}{1000} \times \text{Farm Area (ha)}$ | Farm planning convenience |

**Verification Check:** The column `Yield` in the training dataset represents yield intensity ($\text{kg/ha}$). Models and APIs must never refer to total production as "yield". Total production is strictly labeled as `derived_total_production_tonnes`.

---

## 3. Dataset Preprocessing & Leakage Prevention Audit

### 3.1 Historical Coverage & Cleaning
- **Period Covered:** 1998–1999 through 2019–2020 (official published series) extended through recent meteorological normals (total 8,694 historical district-crop-season observations).
- **Geographic Coverage:** All 38 administrative districts of Tamil Nadu (including historical districts and newly bifurcated districts mapped through canonical aliases, e.g., Kallakurichi, Chengalpattu, Tenkasi).
- **Crops Covered:** Major Tamil Nadu crops calibrated under TNAU Crop Production Guides: Rice, Cotton (lint), Sugarcane, Maize, Groundnut, Blackgram, Greengram, etc.
- **Cleaning & Outlier Removal:**
  - Duplicate district-crop-season-year records removed.
  - Zero-area anomalies and missing values in seasonal rainfall imputed from India Meteorological Department (IMD) gridded rainfall data.

### 3.2 Feature Matrix & Target Leakage Prevention
In agricultural datasets, including `Area` (hectares) or `Production` (tonnes) in the feature matrix $X$ introduces catastrophic target leakage because $\text{Yield} = \frac{\text{Production}}{\text{Area}}$. 

In AgroWise AI:
- **Strictly Excluded from $X$:** `Area_Hectares`, `Production_Tonnes`, fertilizer doses, soil test ratings.
- **Included Features (9 Inputs):**
  1. `District` (Categorical, 38 levels)
  2. `Crop` (Categorical, 25 levels)
  3. `Season` (Categorical: Kharif, Rabi, Summer, Whole Year, Samba/Thaladi/Pishanam, Navarai, etc.)
  4. `Year` (Integer, crop-year start)
  5. `Rain_SWM_mm` (Continuous: South-West Monsoon rainfall, Jun–Sep)
  6. `Rain_NEM_mm` (Continuous: North-East Monsoon rainfall, Oct–Dec)
  7. `Rain_Winter_mm` (Continuous: Winter rainfall, Jan–Feb)
  8. `Rain_HotWeather_mm` (Continuous: Hot-weather / pre-monsoon rainfall, Mar–May)
  9. `Rain_Annual_mm` (Continuous: Total crop-year rainfall)

Because neither farm size nor production appears in the feature vector, the model evaluates expected historical climatic and district performance independently of the farmer's specific field size.

---

## 4. Validation Strategy & Temporal Integrity

### 4.1 Prohibition of Random K-Fold Shuffling
Agricultural time-series observations from the same district across consecutive years exhibit high temporal autocorrelation. Randomly shuffling data into train/test folds leaks future climate and regional trend patterns into earlier observations, inflating test metrics artificially.

### 4.2 Chronological Hold-Out Split
- **Training Set:** Historical crop years **1998 through 2015** ($6,955$ samples, $80.0\%$).
- **Held-Out Test Set:** Subsequent historical crop years **2016 through 2020** ($1,739$ samples, $20.0\%$).
- The model is evaluated strictly on future, unseen crop years, providing an honest measure of real-world generalization under changing seasonal weather patterns.

---

## 5. Agronomic Decoupling Mandate

### 5.1 Strict Independence from Fertilizer Calculations
1. **Unidirectional Pipeline:** Soil test values and farm management parameters determine agronomic nutrient requirements through Phase 4 (Rule Selection) and Phase 5 (Nutrient Calculation Engine).
2. **Zero Mutation:** Phase 2 (Yield Prediction) runs purely in parallel as an informative statistical benchmark. It receives the farmer's crop and district and returns the historical district average.
3. **Immutability of Nutrient Targets:** Varying rainfall scenarios or simulated yield predictions never modifies the N, P₂O₅, or K₂O doses recommended to the farmer.
4. **Safety Rationale:** Allowing an ML yield model to dynamically inflate fertilizer doses in high-rainfall years or deflate them in drought years is agronomically dangerous. Over-fertilizing during good rains causes lodging and pest outbreaks, while under-fertilizing during dry spells induces permanent crop stunting. Fertilizer requirements are determined strictly by verified TNAU STCR-IPNS equations and standard recommended doses.

### 5.2 Status Signaling & User Display
- Supported district/crop combinations return:
  `status: "DISTRICT_BENCHMARK_ESTIMATE"`
- Unsupported or unvalidated district/crop combinations return:
  `status: "NOT_VALIDATED"`
  with an explicit disclaimer: *"District yield benchmark is NOT VALIDATED for this crop/district combination."*
- Predictions are presented in the Flutter UI under an explicit **"District Historical Yield Benchmark"** card accompanied by clear limitations:
  - *"District-level aggregate average; not a farm-specific yield prediction."*
  - *"Does not account for individual farm soil depth, microclimate, or management."*
  - *"Completely independent of fertilizer recommendations; does not alter fertilizer doses."*
