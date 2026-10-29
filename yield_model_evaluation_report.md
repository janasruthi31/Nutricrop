# Machine Learning District Yield Model Evaluation Report

**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer  
**Module:** Phase 2 — District Yield Benchmark Machine Learning Model  
**Model Artifacts:** `models/yield_prediction/yield_model.joblib`, `metadata.json`, `metrics.json`  
**Evaluation Date:** 2026-10-28  

---

## 1. Model Overview & Evaluation Strategy

The district yield estimation module provides a statistical benchmark of expected district-average historical crop yield ($\text{kg/ha}$) based on historical Tamil Nadu Season & Crop Reports and India Meteorological Department (IMD) seasonal rainfall.

### 1.1 Strict Temporal Validation Split
To prevent temporal data leakage caused by adjacent-year autocorrelation across districts, observations were strictly divided in chronological order without shuffling:
- **Total Valid Observations:** $8,694$ district-crop-season observations.
- **Training Set (80.0%):** $6,955$ samples (earlier historical years).
- **Held-Out Test Set (20.0%):** $1,739$ samples (most recent historical years).

---

## 2. Quantitative Evaluation Results (Held-Out Test Data)

Evaluation metrics were computed exclusively on the $1,739$ held-out test observations.

| Model / Algorithm | MAE ($\text{kg/ha}$) | RMSE ($\text{kg/ha}$) | $R^2$ Score | MAPE Status |
|---|---|---|---|---|
| **XGBoost Regressor (Production Model)** | **$1,706.28$** | **$3,945.54$** | **$0.9508$ ($95.1\%$)** | Set to `null` (see §2.1) |
| Random Forest Regressor | $1,583.62$ | $3,805.60$ | $0.9542$ ($95.4\%$) | Set to `null` (see §2.1) |
| Gradient Boosting Regressor | $1,912.02$ | $3,970.83$ | $0.9501$ ($95.0\%$) | Set to `null` (see §2.1) |

*Hyperparameters for Production XGBoost:* `n_estimators=300`, `max_depth=6`, `learning_rate=0.1`, `random_state=42`.

### 2.1 Technical Explanation for Null Mean Absolute Percentage Error (MAPE)
In `metrics.json`, MAPE is explicitly designated as `null`. This is a deliberate, mathematically justified agronomic decision:
- **Near-Zero Denominator Distortion:** In the held-out test set, actual district yields range from a minimum of $10.0\text{ kg/ha}$ (severe crop failure due to extreme drought/flood events) to over $100,000\text{ kg/ha}$ (high-tonnage sugarcane). Fourteen observations have actual yields $< 100\text{ kg/ha}$.
- When the actual yield $y_i \to 0$, the relative percentage error term $\frac{|y_i - \hat{y}_i|}{y_i}$ explodes toward infinity. A modest absolute error of $400\text{ kg/ha}$ on a $20\text{ kg/ha}$ crop failure record yields a $2000\%$ relative error, completely dominating and distorting the arithmetic mean.
- **Reporting Standard:** Mean Absolute Error ($\text{MAE} = 1706.3\text{ kg/ha}$) and Root Mean Squared Error ($\text{RMSE} = 3945.5\text{ kg/ha}$) along with the coefficient of determination ($R^2 = 0.951$) provide the only honest, unskewed evaluation of residual spread.

---

## 3. Explicit Model Limitations & Non-Guarantees

1. **District-Level Aggregate Average, Not Farm-Specific:**
   The training data records average crop performance across an entire revenue district ($100,000\text{ to }500,000\text{ hectares}$). Actual field yields on a specific farmer's plot deviate significantly due to microclimate, local topography, soil profile depth, irrigation water quality, sowing date, seed purity, and pest infestations.
2. **Benchmark Comparison Only:**
   The estimate serves exclusively as an informative baseline for regional yield potential. It does **not** constitute a promised, guaranteed, or insurable field yield.
3. **Strict Decoupling from Agronomic Fertilizer Requirements:**
   The ML yield prediction is strictly decoupled from the fertilizer optimization engine. ML yield predictions **never** dynamically alter, scale, or increase recommended chemical fertilizer doses. Nutrient recommendations remain strictly bound to verified TNAU STCR-IPNS equations and standard recommended doses.
4. **Historical Data Quality & Scope:**
   Predictions are restricted to the 38 recognized districts of Tamil Nadu and the 25 calibrated crop categories. Any query outside this domain returns `status: "NOT_VALIDATED"`.

---

## 4. Test Verification Summary

Regression suite `tests/test_c_d_e_verification.py` verifies all Section E contracts:
- `test_e01`: Verifies endpoint returns `target_variable="yield"` in `kg/ha`, and derived production in tonnes. (**PASS**)
- `test_e02`: Verifies unsupported district or crop raises error / returns unvalidated status. (**PASS**)
- `test_e03`: Verifies that altering rainfall and yield predictions does not alter agronomic NPK nutrient requirements or fertilizer doses. (**PASS**)
- `test_e04`: Verifies that full recommendation metadata includes all required limitations, Table V-A ground truth citations, and held-out evaluation metrics ($R^2 > 0.90$). (**PASS**)
