# Machine Learning Yield Prediction Model Validation
**Application Name:** AgroWise AI  
**Project Reference:** SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield  
**Module:** Phase 2 (District-Level Crop Yield Benchmark Regressor)  

---

## 1. Dataset Provenance & Target Definition

The machine learning yield model is trained on official Tamil Nadu agricultural statistics:
* **Primary Source:** Tamil Nadu Department of Economics and Statistics — *Season and Crop Reports (SCR)* spanning five agricultural years (2020-21, 2021-22, 2022-23, 2023-24, and 2024-25).
* **Data Extraction Tables:** Table V-A (District-wise Area, Production, and Average Yield of Crops) merged with Table I-A (District-wise Seasonal Rainfall Normal and Actuals).
* **Row Count:** 8,694 total verified records across 38 administrative districts and 32 principal crops.
* **Target Variable:** District average crop yield in **kilograms per hectare ($kg/ha$)**. Sugarcane records, historically reported in tonnes of cane per hectare ($t/ha$), were converted via $1\text{ t} = 1000\text{ kg}$ to ensure unified numerical scale across all crop types.

---

## 2. Target Leakage & Feature Provenance Audit

### Leakage Audit Findings
In many amateur agricultural ML projects, crop production (tonnes) is inadvertently included as an input feature alongside area (hectares). Because $\text{Yield} = \text{Production} / \text{Area}$, including production causes severe target leakage ($R^2 \approx 0.999$), making the model useless at inference time when future harvest tonnage is unknown.

**Audit Verification in AgroWise AI:**
* `production_used_as_feature = false` (enforced in `train_yield_model.py` and documented in `models/yield_prediction/metadata.json`).
* Total production is completely excluded from the training matrix.
* Predictions rely exclusively on pre-season or in-season agro-climatic inputs available before harvest.

### 9-Feature Verified Schema
The inference engine and model artifact strictly enforce the following 9 features:
1. `District` (Categorical: 38 Tamil Nadu administrative districts)
2. `Crop` (Categorical: 32 recognized crops)
3. `Season` (Categorical: Kharif, Rabi, Summer, Whole Year)
4. `Year` (Integer numeric: Reference agricultural year)
5. `Rain_SWM_mm` (Numeric: South-West Monsoon rainfall in mm, June–September)
6. `Rain_NEM_mm` (Numeric: North-East Monsoon rainfall in mm, October–December)
7. `Rain_Winter_mm` (Numeric: Winter rainfall in mm, January–February)
8. `Rain_HotWeather_mm` (Numeric: Summer/Hot-weather rainfall in mm, March–May)
9. `Rain_Annual_mm` (Numeric: Total annual precipitation in mm)

---

## 3. Evaluation Strategy & Benchmark Metrics

### Chronological Train-Test Split
Rather than random shuffling (which leaks temporal autocorrelation across neighboring seasons), the dataset was evaluated using a strict **80/20 chronological split**:
* **Training Set:** 6,955 records (80%).
* **Held-Out Test Set:** 1,739 records (20%).

### Comparative Model Benchmarks on Held-Out Test Data

| Model Architecture | Mean Absolute Error (MAE) | Root Mean Squared Error (RMSE) | Coefficient of Determination ($R^2$) |
| :--- | :--- | :--- | :--- |
| **XGBoost Regressor (Selected)** | **1,706.28 kg/ha** | **3,945.54 kg/ha** | **0.9508** |
| Random Forest Regressor | 1,583.62 kg/ha | 3,805.60 kg/ha | 0.9542 |
| Gradient Boosting Regressor | 1,893.05 kg/ha | 3,908.81 kg/ha | 0.9517 |

*Note on MAPE:* Mean Absolute Percentage Error (MAPE) is set to `null` because the dataset includes crops with near-zero yields (minimum 10 kg/ha vs. median 2,645 kg/ha), causing division by near-zero denominators to distort overall percentage errors. Median Absolute Percentage Error (MedAPE) is evaluated in `supplementary_metrics.json`.

---

## 4. User Communication & Ethical Scope Boundaries

AgroWise AI enforces strict communication guardrails across all user touchpoints:
1. **Statistical Estimate Only:** The yield prediction is presented as a district-average agro-climatic benchmark, not a guaranteed harvest for an individual field plot.
2. **Scientific Honesty Regarding $R^2$:** The coefficient of determination ($R^2 = 0.95$) is **never** described as the "percentage probability that a prediction is correct". It reflects the proportion of total yield variance explained by the features across the state of Tamil Nadu.
3. **Decoupled Architecture:** Machine learning predictions operate strictly as an advisory baseline and are **never** permitted to modify or distort the deterministic, soil-chemical TNAU STCR NPK calculations.
