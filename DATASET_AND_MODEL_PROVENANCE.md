# Dataset and Machine Learning Model Provenance

**Project Title:** AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Document Type:** Provenance, Integrity, and Agronomic Alignment Record  

---

## 1. Dataset Provenance and Integrity

### 1.1 Source and Authority
- **Primary Source:** Season and Crop Reports of Tamil Nadu (Annual Statistical Reports, 2020–2025).
- **Issuing Authority:** Directorate of Economics and Statistics (DES), Government of Tamil Nadu, Chennai.
- **Meteorological Data:** Agro-climatic district monthly and seasonal rainfall records compiled from the India Meteorological Department (IMD) Regional Meteorological Centre, Chennai.

### 1.2 File Integrity and Storage
- **Raw Dataset:** `data/tn_district_yield_rainfall_raw_long.csv`
  - Unmodified long-format tabular records of district-crop-season observations.
- **Cleaned Dataset:** `data/tn_district_yield_model_dataset.csv`
  - Rows: **8,694 cleaned records**
  - Geographic Coverage: **38 revenue districts of Tamil Nadu**
  - Temporal Window: Agricultural years 2020 to 2025.

### 1.3 Schema and Target Units
| Column Name | Data Type | Units / Range | Description |
|---|---|---|---|
| `district` | Categorical (String) | 38 TN Districts | Revenue district of Tamil Nadu |
| `crop` | Categorical (String) | Major TN Crops | Rice (Paddy), Cotton, Maize, Groundnut, Sugarcane, Pulses |
| `season` | Categorical (String) | Kharif, Rabi, Summer | Agro-climatic cropping season |
| `year` | Integer | 2020 – 2025 | Agricultural year |
| `area_ha` | Float | Hectares (ha) | Cultivated cropped area |
| `rainfall_mm` | Float | Millimeters (mm) | Cumulative seasonal precipitation |
| **`yield_kg_per_ha`** | Float | **Kilograms per Hectare (kg/ha)** | **Canonical Model Target** |

### 1.4 Data Cleaning and Quality Assurance
1. **Target Unit Uniformity:** All historical production (tonnes) and area (hectares) figures were converted to the single canonical agronomic unit:
   $$\text{Yield (kg/ha)} = \frac{\text{Production (tonnes)} \times 1000}{\text{Area (hectares)}}$$
2. **Missing Value Policy:** No imputation or synthetic fabrication was applied to target crop yields. Outlier entries with biologically impossible yields (e.g. negative or >30,000 kg/ha for cereals) were cross-verified against official gazettes or removed.
3. **Data Leakage Prevention:** Train/test splits were partitioned temporally and across distinct district cohorts to prevent historical cross-contamination.

---

## 2. Machine Learning Model Provenance

### 2.1 Model Architecture
- **Model Type:** Extreme Gradient Boosting (`XGBRegressor`) embedded within a Scikit-Learn `Pipeline`.
- **Feature Preprocessing:**
  - One-Hot Encoding for categorical features (`district`, `crop`, `season`) with `handle_unknown='ignore'`.
  - Robust scaling for continuous numerical features (`rainfall_mm`, `area_ha`).
- **Target Variable:** `yield_kg_per_ha` (continuous regression).

### 2.2 Serialized Artifacts
- **Primary Serialized Model:** `models/yield_prediction/yield_model.joblib`
- **Model Metadata File:** `models/yield_prediction/metadata.json`
- **Official Evaluation Metrics:** `models/yield_prediction/metrics.json`
- **Supplementary Validation:** `models/yield_prediction/supplementary_metrics.json`

### 2.3 Verified Model Performance Metrics
The evaluation metrics recorded during the frozen model release validation:
- **Coefficient of Determination ($R^2$):** **0.9508** (95.08% of regional yield variance explained across Tamil Nadu crops and districts).
- **Mean Absolute Error (MAE):** **1,706.2 kg/ha**
- **Root Mean Square Error (RMSE):** **3,945.8 kg/ha**

### 2.4 Model Scope and Ethical Agronomic Boundaries
> [!IMPORTANT]
> **Macro Benchmark vs. Micro Diagnostic:**
> The ML model produces a **district-level historical benchmark expectation**. It is explicitly **NOT** a micro-level sensor for an individual farmer's field and does **NOT** dictate chemical fertilizer dosage. 
> Fertilizer N-P-K dosages are strictly and exclusively calculated by deterministic, field-specific soil test equations (TNAU STCR-IPNS, Phase 5) based on the farmer's laboratory Soil Health Card. The ML yield benchmark provides contextual guidance and regional planning comparison only.
