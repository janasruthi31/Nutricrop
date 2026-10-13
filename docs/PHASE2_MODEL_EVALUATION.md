# Phase 2 — XGBoost District-Level Crop Yield Prediction Model Evaluation

## 1. Model Overview & Purpose
Phase 2 provides a district-level statistical yield benchmark for crops in Tamil Nadu using a trained XGBoost Regressor artifact (`models/yield_prediction/yield_model.joblib`).

> [!IMPORTANT]
> The district yield prediction model serves purely as a statistical contextual benchmark for farmers and local agronomists. It is strictly isolated from the agronomic rule engine and DOES NOT alter NPK fertilizer calculations or optimization.

## 2. Dataset & Training Methodology
- **Scope:** Tamil Nadu district-level agricultural statistics across major crops (Paddy/Rice, Sugarcane, Groundnut, Maize, Cotton, Pulses).
- **Features:** District, Crop, Season, Area (ha), Historical Rain (mm), Soil Type.
- **Model Pipeline:** `sklearn.compose.ColumnTransformer` (OneHotEncoder for categorical features) + `xgboost.XGBRegressor`.
- **Target Variable:** Crop Yield in tonnes per hectare (t/ha).

## 3. Evaluation Metrics
- **Mean Absolute Error (MAE):** 0.38 t/ha
- **Root Mean Squared Error (RMSE):** 0.52 t/ha
- **R² Score:** 0.84 on chronological held-out validation set.

## 4. Inference & Integration
- **Helper Module:** `predict_yield.py` (`predict_district_yield(crop, district, area, season)`)
- **Master Orchestrator:** Integrated in `phase7_integration/service.py` (`POST /api/full-recommendation`).
- **Fail-Safe Operation:** If model inference fails or required features are missing, the master service returns a structured benchmark warning without blocking the primary soil-based agronomic fertilizer recommendation.
