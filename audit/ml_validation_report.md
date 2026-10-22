# Phase 3: Machine Learning Model Honest Evaluation Report

**Project:** AgroWise AI — AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Model Artifact:** `models/yield_prediction/yield_model.joblib`  
**Dataset:** `data/tn_district_yield_model_dataset.csv` (8,694 total rows; 6,955 train, 1,739 test — chronological 80/20 split)  
**Evaluation Date:** 2026-10-21  

---

## 1. Executive Summary of Findings

A rigorous baseline comparison and empirical audit was executed on the district yield regression model. The key findings are:

1. **R² Inflation Driven by Between-Crop Variance:**
   The pooled model's high $R^2 = 0.9508$ is primarily driven by the massive scale difference between crops (Sugarcane at $\sim 100,000\text{ kg/ha}$ vs Pulses at $\sim 500\text{ kg/ha}$).
   - A **zero-ML trivial baseline** predicting simply the training mean of `(Crop, Season)` achieves $R^2 = 0.9389$ and $\text{MAE} = 1,748.0\text{ kg/ha}$.
   - The complex XGBoost model improves $R^2$ by only **$+0.0119$** (from $0.9389$ to $0.9508$) and MAE by only $41.7\text{ kg/ha}$ ($2.4\%$).
2. **Failure on Pulses ($R^2 = -0.143$):**
   Within the Pulses cohort (323 test rows including Blackgram, Greengram, Cowpea), the XGBoost model has a **negative $R^2$ of $-0.143$**, performing significantly worse than a simple lookup table ($R^2 = +0.388$).
3. **Worse than Baseline on Fruits ($R^2 = 0.794$ vs $0.814$):**
   For fruits (283 test rows), the XGBoost model has higher error ($\text{MAE} = 4,608.2\text{ kg/ha}$) than the simple seasonal mean baseline ($\text{MAE} = 3,994.2\text{ kg/ha}$).
4. **Data Imputation in Official Government Reports:**
   In **59.6% of test records** (1,037 out of 1,739 rows), the district yield in the DES Season and Crop Reports was reported as exactly equal to the state average yield (`equals_state_value == True`), reflecting official administrative imputation rather than district-specific crop-cutting surveys.
5. **No Causal Link to Farm Fertilizer Application:**
   The ML model does not include farm soil NPK, pH, fertilizer dosage, seed variety, or pest pressure. It predicts macro district statistical averages and **cannot evaluate individual farm fertilizer response**.

---

## 2. Model Baseline Comparison Table

Evaluated on the exact 1,739 held-out test rows across identical metrics:

| Model / Baseline | MAE (kg/ha) | RMSE (kg/ha) | $R^2$ | Sample Count | Description |
|---|---|---|---|---|---|
| **1. Overall Mean Baseline** | 10,160.7 | 17,816.0 | -0.0038 | 1,739 | Unconditional training mean ($\bar{y} = 8,103.5$) |
| **2. Crop + Season Mean Baseline** | 1,748.0 | 4,395.2 | 0.9389 | 1,739 | Lookup table of training mean per `(Crop, Season)` |
| **3. Simple Ridge Regression** | 1,893.6 | 4,431.5 | 0.9379 | 1,739 | Linear Ridge on One-Hot `Crop + Season + District` |
| **4. Existing Trained XGBoost** | 1,706.3 | 3,945.5 | **0.9508** | 1,739 | XGBoost regressor on 9 features |

> [!IMPORTANT]
> The practical gain of the XGBoost model over the simple lookup table is an $R^2$ increment of only $0.0119$. Presenting $R^2 = 0.95$ as evidence of high predictive precision without citing the $0.9389$ baseline is misleading.

---

## 3. Disaggregated Performance by Crop Group

| Crop Group | Test Rows | Baseline MAE | XGBoost MAE | Baseline $R^2$ | XGBoost $R^2$ | Model Advantage / Assessment |
|---|---|---|---|---|---|---|
| **Cereals** (Rice, Maize, etc.) | 343 | 861.2 | 792.5 | 0.6229 | **0.6716** | Moderate improvement (+0.0487 $R^2$) |
| **Commercial** (Sugarcane, Cotton) | 105 | 3,691.5 | 3,113.7 | 0.9663 | **0.9794** | Modest improvement (+0.0131 $R^2$) |
| **Fruits** (Banana, Mango, etc.) | 283 | 3,994.2 | 4,608.2 | **0.8137** | 0.7939 | **Worse than baseline** (-0.0198 $R^2$) |
| **Oilseeds** (Groundnut, Gingelly) | 197 | 255.2 | 275.2 | 0.8799 | **0.9043** | Modest improvement (+0.0244 $R^2$) |
| **Pulses** (Blackgram, Redgram) | 323 | 136.0 | 224.9 | **0.3881** | **-0.1432** | **Severe failure** (Negative $R^2$; worse than mean) |
| **Spices & Plantation** | 226 | 1,552.1 | 803.6 | 0.7966 | **0.9401** | Significant improvement (+0.1435 $R^2$) |
| **Vegetables & Tubers** | 262 | 2,982.7 | 2,885.0 | 0.9154 | **0.9249** | Marginal improvement (+0.0095 $R^2$) |

---

## 4. Analysis of Official Imputation (`equals_state_value`)

| Cohort | Rows | Share | Baseline MAE | XGBoost MAE | Baseline $R^2$ | XGBoost $R^2$ |
|---|---|---|---|---|---|---|
| **Imputed (Equals State Average)** | 1,037 | **59.6%** | 1,107.0 | 1,295.0 | 0.9612 | 0.9628 |
| **District-Specific Survey Data** | 702 | **40.4%** | 2,694.9 | 2,313.8 | 0.9260 | 0.9436 |

- For nearly 60% of records in the official Season and Crop Reports (especially for minor crops and vegetables), the published district yield is identical to the state aggregate.
- On the 702 genuinely district-specific surveyed records, XGBoost achieves $R^2 = 0.9436$ vs Baseline $R^2 = 0.9260$, reducing MAE from $2,694.9$ to $2,313.8\text{ kg/ha}$.

---

## 5. Feature Importance Breakdown

From `models/yield_prediction/feature_importance_by_original_variable.csv`:

| Original Variable | Gain-Based Importance | Agronomic Context |
|---|---|---|
| **Crop** | **88.77%** | Dominates variance because crop biological yield scales differ by orders of magnitude. |
| **Season** | **8.45%** | Captures wet Kharif vs dry Rabi/Summer growing seasons. |
| **District** | **2.46%** | Regional soil-climatic zone differences. |
| **Annual Rainfall** | **0.063%** | Very weak gain contribution. |
| **Year** | **0.059%** | Multi-year technological trend. |
| **Seasonal Rainfalls (SWM, NEM, etc.)** | **< 0.15% combined** | Weak direct correlation with aggregate annual district yields. |

### Causal Caveat:
Rainfall importance is low because:
1. Irrigated crops (Paddy, Sugarcane) depend on canal/dam release (e.g. Mettur reservoir) rather than local rainfall.
2. District-wide seasonal rainfall totals aggregate over entire districts and cannot reflect micro-watershed rainfall distribution during critical flowering/grain-filling stages.

---

## 6. Recommendations for Operational Deployment

1. **Explicit UI Disclaimer:** The frontend must clearly label the ML prediction as a *"Historical District Average Benchmark (DES Season & Crop Reports)"*, and explicitly state: *"Does not evaluate individual field soil fertility or direct fertilizer response."*
2. **Crop-Specific Modeling:** For high-volume crops (Paddy, Sugarcane), future model iterations should train dedicated single-crop regressors with normalized targets ($z$-scores or relative yields) rather than cross-crop pooling.
3. **Pulse Fallback:** For Pulses (Blackgram, Greengram), the system should use the crop-season median/mean baseline rather than the negative $R^2$ XGBoost regression output.
