# MODEL TRAINING REPORT — yield_model_v1

**Scope:** Tamil Nadu district-average crop yield estimate (NOT farm-specific). Training date: 2026-10-29. Model version: v1.

## 1. Dataset used
Official Tamil Nadu *Season & Crop Reports* (PDFs in the uploaded ZIP, `01_Important_Data_Files/data/`), crop-years 2020-21 to 2024-25:
Table V-A (district-wise average yield rates) joined with Table I-A (district-wise seasonal rainfall) on **District (by serial number, spelling-normalised) + Crop-year**.
Extraction script: `extract_yield_dataset.py`. Cleaned file: `data/tn_district_yield_model_dataset.csv`.
Not used: the pack's CSV/XLS files (area-only, state-level, single weather point, soil, prices, rules) — see `DATASET_AUDIT.md`.
Reports 2014-15…2018-19 are in the ZIP but excluded: different column layouts and 32 pre-2019 districts (boundaries not comparable with the 37-38 post-2019 districts). 2019-20 is not in the ZIP.

## 2. Dataset dimensions
Raw extracted cells: 17230 · valid modelling rows: **8694** · districts: 38 · crops: 51 · crop-years: 2020-21, 2021-22, 2022-23, 2023-24, 2024-25.
Rows per crop-year: {'2020-21': 1375, '2021-22': 1870, '2022-23': 1828, '2023-24': 1786, '2024-25': 1835}.

## 3. Data cleaning (exact counts)
| Step | Rows removed |
|---|---|
| "Combined" season columns (derived aggregates of Kharif/Rabi; avoids near-duplicate rows) | 3601 |
| Coconut (reported in nuts/ha — not a mass unit) | 188 |
| Yield = 0 (crop not grown / no estimate in district; not a real zero yield) | 4238 |
| Rainfall blank or internally inconsistent in the source report | 509 |

Sugarcane is published in tonnes/ha; 190 rows were multiplied by 1000 (exact conversion to kg/ha). Everything else is already kg/ha.

## 4. Missing-value handling
No imputation was performed. Yield has no missing values. Rainfall is blank in the source for 463 rows (new/reorganised districts in 2020-21 and Mayiladuthurai in 2021-22) and
46 rows (Ranipet 2020-21: printed annual total contradicts its own monthly figures); these rows were excluded rather than invented. Temperature and humidity: **feature unavailable in uploaded dataset** (only one NASA POWER point for 2025 exists).

## 5. Duplicate handling
Duplicates on (District, Crop, Season, Crop-year): 0. No rows were duplicated or synthesised.

## 6. Tamil Nadu filtering
All data originate from Tamil Nadu reports; no other state is present. 38 districts (canonical 2024-25 spelling; 2020-22 spelling variants such as Thiruppur/Tiruppur mapped via serial number with a fuzzy-match assertion).

## 7. Feature selection
Categorical (one-hot): District, Crop, Season. Numeric: Year (start year of crop-year), Rain_SWM_mm, Rain_NEM_mm, Rain_Winter_mm, Rain_HotWeather_mm, Rain_Annual_mm (actual crop-year rainfall, June–May).
Unavailable: temperature, humidity, soil, fertilizer applied, irrigation (feature unavailable in uploaded dataset at district-year level).

## 8. Target definition
`yield` = published district-average yield (kg/ha). It is read directly from Table V-A; it was **not** derived from production/area.

## 9. Leakage checks
Production not used (and not even extracted). Area not used. Rainfall is observed for the same crop-year, so the model is a retrospective/scenario estimator — a real forecast would need forecast rainfall. Hyperparameters chosen only with leave-one-crop-year-out CV inside the training rows. The saved model was fitted on training rows only.

## 10-12. 80/20 split
Rows were sorted stably by crop-year (original report order kept within a year; no shuffle), then the first 80% = train, last 20% = test.
Total valid rows: 8694 · Training rows (80%): 6955 · Testing rows (20%): 1739.
Train rows by crop-year: {'2020-21': 1375, '2021-22': 1870, '2022-23': 1828, '2023-24': 1786, '2024-25': 96} · Test rows by crop-year: {'2024-25': 1739}.
Note: because years have unequal row counts the cut falls inside 2024-25, so the first 96 rows of 2024-25 (in report order) are in training. A strict year hold-out is reported in section 19 as a sensitivity check.

## 13-15. Model parameters (selected by CV on training rows only)
- XGBoost: `{'n_estimators': 300, 'max_depth': 6, 'learning_rate': 0.1}` + objective=reg:squarederror, subsample=0.8, colsample_bytree=0.8, tree_method=hist, random_state=42
- Random Forest: `{'n_estimators': 150, 'max_depth': None, 'min_samples_leaf': 1, 'max_features': 0.5}` + random_state=42
- Gradient Boosting: `{'n_estimators': 150, 'max_depth': 5, 'learning_rate': 0.1}` + subsample=0.8, random_state=42

## 16-19. Test results (unseen 20%, 1739 rows; units kg/ha)
| Model | MAE | RMSE | R² | MAPE % (null = invalid) |
|---|---|---|---|---|
| XGBoost Regressor (primary) | 1706.28 | 3945.54 | 0.95 | n/a (invalid) |
| Random Forest Regressor | 1583.62 | 3805.60 | 0.95 | n/a (invalid) |
| Gradient Boosting Regressor | 1893.05 | 3908.81 | 0.95 | n/a (invalid) |

**MAPE is not reported (null):** MAPE set to null: the test set contains actual yields near zero (min 10 kg/ha vs median 2645; 14 rows < 100 kg/ha), so percentage errors are dominated by a few tiny denominators. See supplementary_metrics.json (ape_diagnostics) for median APE.
Robust alternative (supplementary): median absolute % error — XGBoost 21.7%, RF 13.3%, GB 33.9%.

**Best model by test MAE/RMSE/R²:** random_forest. The primary model (as specified) remains XGBoost and is the one saved in `yield_model.joblib`.

**Honest interpretation:** the pooled R² (~0.95) is largely explained by crop identity: a trivial Crop+Season training-mean baseline reaches R² 0.939 (MAE 1748). The three ML models only modestly beat that baseline in MAE, rainfall features carry almost no importance, and within some groups (e.g. pulses) R² is close to zero. The model should be treated as a crop/season/district-average estimator, not as evidence that rainfall drives the predictions.

**Context (not tuned on):**
- Baseline "mean of Crop+Season in training" (not ML): MAE 1748.0, R² 0.939 on 1739 covered rows.
- Rows where the district figure is identical to the State figure (copied by the department): 55.7% of all valid rows. On the test set, district-specific rows only (702 rows): XGBoost MAE 2313.8, R² 0.944; state-copied rows (1037): XGBoost MAE 1295.0, R² 0.963.
- Strict year hold-out (train 2020-21…2023-24 = 6859 rows, test 2024-25 = 1835 rows): XGBoost MAE 1617.4 / R² 0.951; RF MAE 1520.3 / R² 0.954; GB MAE 1804.7 / R² 0.952.

Per crop group (test set): 
| Group | rows | XGB MAE | RF MAE | GB MAE | XGB R² (within group) |
|---|---|---|---|---|---|
| Cereals | 343 | 792.5 | 730.0 | 939.6 | 0.67 |
| Commercial (sugarcane/cotton/tobacco) | 105 | 3113.7 | 2648.0 | 2798.2 | 0.98 |
| Fruits | 283 | 4608.2 | 4468.7 | 4551.0 | 0.79 |
| Oilseeds | 197 | 275.2 | 214.8 | 511.6 | 0.90 |
| Pulses | 323 | 224.9 | 131.1 | 501.4 | -0.14 |
| Spices & plantation | 226 | 803.6 | 751.5 | 1307.5 | 0.94 |
| Vegetables & tubers | 262 | 2885.0 | 2696.1 | 3166.9 | 0.92 |

Overall R² is inflated by the huge between-crop scale differences (cereals ~ 10³ kg/ha vs vegetables/fruits/sugarcane ~ 10⁴–10⁵ kg/ha); judge the model by the per-group rows.

## 20. Feature importance (XGBoost, gain)
Top 15 encoded features are in `feature_importance.csv`. One-hot columns are named `<Variable>_<Category>` (e.g. `Crop_Banana`); `feature_importance_by_original_variable.csv` sums them back to the original variable:
Original_Variable
Crop                  0.8877
Season                0.0845
District              0.0246
Rain_Annual_mm        0.0006
Year                  0.0006
Rain_HotWeather_mm    0.0005
Rain_Winter_mm        0.0005
Rain_NEM_mm           0.0005
Rain_SWM_mm           0.0004

## 21. Limitations
- District figures are **district averages**, not farm-specific; the report copies the state value in a large share of cells (see above), so many "district" labels carry no district information.
- Only 5 crop-years (4-5 observations per district-crop-season); year-to-year dynamics cannot be learned reliably; the model cannot extrapolate trends.
- Rainfall is crop-year total/seasonal actuals (known only after the season) — not a forecast input.
- District boundaries changed in 2019; pre-2019 reports were excluded.
- Mixed crops and units dominate pooled RMSE; per-group results matter more.

## 22. Data gaps
District-year temperature and humidity; multi-year district weather; production/area-based derivation (not needed); soil and irrigation by district-year; 2019-20 report; any farm-level fertilizer application records.

## 23. Model version / date
yield_model_v1 · 2026-10-29 · xgboost 3.2.0 · scikit-learn 1.9.1

## Fertilizer-type ML
**Not trained.** The uploaded data does not contain sufficient validated Tamil Nadu farm-level fertilizer application labels (fertilizer type/quantity applied + crop + soil + location + season/year). Fertilizer recommendation stays in the TNAU/STCR/IPNS → N/P2O5/K2O → LP optimizer module; the yield model is never used for fertilizer type, dose or cost.
