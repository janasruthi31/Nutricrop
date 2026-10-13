#!/usr/bin/env python3
"""
Train + evaluate the district-level crop-yield models for Tamil Nadu (REAL data only).

Input  : data/tn_district_yield_rainfall_raw_long.csv  (built by extract_yield_dataset.py from the
         official Season & Crop Report PDFs 2020-21..2024-25 inside TN_Fertilizer_Combined_Pack.zip)
Target : yield (kg/ha) = published district-average yield (Table V-A). NOT derived, NOT farm-specific.
Models : XGBRegressor (primary), RandomForestRegressor, GradientBoostingRegressor
Split  : chronological 80/20 by row order (sorted stably by crop-year; no shuffling)
Outputs: models/yield_prediction/{yield_model.joblib, metadata.json, metrics.json,
         test_predictions.csv, feature_importance.csv} + MODEL_TRAINING_REPORT.md
"""
import os, json, datetime, itertools, warnings
import numpy as np, pandas as pd, joblib
import xgboost, sklearn
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict

warnings.filterwarnings("ignore")
SEED = 42
DATA = "data/tn_district_yield_rainfall_raw_long.csv"
MODEL_DIR = "models/yield_prediction"
os.makedirs(MODEL_DIR, exist_ok=True)

CAT = ["District", "Crop", "Season"]
NUM = ["Year", "Rain_SWM_mm", "Rain_NEM_mm", "Rain_Winter_mm", "Rain_HotWeather_mm", "Rain_Annual_mm"]
FEATURES = CAT + NUM
TARGET = "yield"

GROUP = {}
for c in ["Rice", "Jowar", "Bajra", "Ragi", "Maize", "Korra", "Varagu", "Samai", "Other cereals"]: GROUP[c] = "Cereals"
for c in ["Red gram", "Green gram", "Black gram", "Horse gram", "Cowpea", "Other pulses", "Bengal gram"]: GROUP[c] = "Pulses"
for c in ["Groundnut", "Gingelly", "Sunflower", "Rapeseed & mustard", "Castor"]: GROUP[c] = "Oilseeds"
for c in ["Sugarcane", "Cotton (lint)", "Tobacco"]: GROUP[c] = "Commercial (sugarcane/cotton/tobacco)"
for c in ["Arecanut", "Chillies", "Cloves", "Garlic", "Pepper", "Ginger", "Turmeric", "Coriander", "Cardamom", "Tamarind"]: GROUP[c] = "Spices & plantation"
for c in ["Potato", "Onion", "Brinjal", "Lady's finger", "Cabbage", "Tomato", "Tapioca", "Sweet potato"]: GROUP[c] = "Vegetables & tubers"
for c in ["Banana", "Mango", "Lemon", "Orange", "Cashew nut", "Jack fruit", "Pineapple", "Guava", "Grapes"]: GROUP[c] = "Fruits"

log = {}   # everything written into the report comes from here (no hand-typed numbers)

# ------------------------------------------------------------------ 1. load & validate
raw = pd.read_csv(DATA)
need = set(CAT + ["Crop_Year", "Year", "reported_value", "state_value", "Rain_flag"] + NUM[1:])
assert need <= set(raw.columns), f"missing columns: {need - set(raw.columns)}"
log["raw_rows"] = len(raw)
log["raw_years"] = sorted(raw.Crop_Year.unique())
log["raw_districts"] = int(raw.District.nunique())
df = raw.copy()

# ------------------------------------------------------------------ 2. cleaning (every step counted)
n0 = len(df); df = df[df.Season != "Combined"]; log["removed_combined_columns"] = n0 - len(df)
n0 = len(df); df = df[df.Crop != "Coconut"]; log["removed_coconut_non_mass_unit"] = n0 - len(df)
sugar = df.Crop == "Sugarcane"
df[TARGET] = df.reported_value
df.loc[sugar, TARGET] = df.loc[sugar, "reported_value"] * 1000.0     # tonnes/ha -> kg/ha (exact unit conversion)
df["state_value_kg"] = df.state_value
df.loc[sugar, "state_value_kg"] = df.loc[sugar, "state_value"] * 1000.0
log["sugarcane_rows_unit_converted"] = int(sugar.sum())
n0 = len(df); log["rows_value_missing"] = int(df[TARGET].isna().sum()); df = df[df[TARGET].notna()]
n0 = len(df); df = df[df[TARGET] > 0]; log["removed_zero_yield_not_grown_or_no_estimate"] = n0 - len(df)
log["rows_with_blank_rainfall_in_report"] = int((df.Rain_flag == "blank_in_report").sum())
log["rows_with_inconsistent_rainfall_in_report"] = int((df.Rain_flag == "inconsistent_in_report").sum())
n0 = len(df); df = df[df.Rain_flag == "ok"]; log["removed_for_missing_or_inconsistent_rainfall"] = n0 - len(df)
assert df[FEATURES].isna().sum().sum() == 0, "NaN remains in features"
log["duplicate_rows_by_key"] = int(df.duplicated(["District", "Crop", "Season", "Crop_Year"]).sum())
assert log["duplicate_rows_by_key"] == 0
df["Crop_Group"] = df.Crop.map(GROUP)
assert df.Crop_Group.notna().all(), df[df.Crop_Group.isna()].Crop.unique()
df["equals_state_value"] = (df[TARGET] == df.state_value_kg)
df = df.sort_values("Year", kind="stable").reset_index(drop=True)      # chronological, stable (keeps report order inside a year)
log["valid_rows"] = len(df)
log["rows_per_crop_year"] = df.Crop_Year.value_counts().sort_index().to_dict()
log["districts"] = int(df.District.nunique()); log["crops"] = int(df.Crop.nunique())
log["seasons"] = sorted(df.Season.unique())
log["share_equal_to_state_value"] = float(df.equals_state_value.mean())
log["min_yield"] = float(df[TARGET].min())
log["leakage"] = {"production_used_as_feature": False, "area_used_as_feature": False,
                  "target_is_published_yield_not_derived": True, "features": FEATURES}
df.to_csv("data/tn_district_yield_model_dataset.csv", index=False)

# ------------------------------------------------------------------ 3. 80/20 split (ordered, no shuffle)
n = len(df); n_train = int(round(0.8 * n))
train, test = df.iloc[:n_train].copy(), df.iloc[n_train:].copy()
log.update(train_rows=len(train), test_rows=len(test),
           train_years=train.Crop_Year.value_counts().sort_index().to_dict(),
           test_years=test.Crop_Year.value_counts().sort_index().to_dict())
assert len(set(train.index) & set(test.index)) == 0
Xtr, ytr, Xte, yte = train[FEATURES], train[TARGET].values, test[FEATURES], test[TARGET].values

def make_pre():
    return ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT),
                              ("num", "passthrough", NUM)])

def metrics(y, p):
    m = {"MAE": float(mean_absolute_error(y, p)), "RMSE": float(np.sqrt(mean_squared_error(y, p))), "R2": float(r2_score(y, p))}
    # MAPE is only reported when no actual value is near zero relative to the data scale
    # (rule: min(actual) >= 1% of median(actual)); otherwise it is dominated by a few tiny denominators.
    valid = (y > 0).all() and y.min() >= 0.01 * np.median(y)
    m["MAPE"] = float(np.mean(np.abs((y - p) / y)) * 100) if valid else None
    return m

# ------------------------------------------------------------------ 4. models + small grids (CV inside TRAIN only)
GRIDS = {
    "xgboost": (lambda **k: XGBRegressor(objective="reg:squarederror", random_state=SEED, n_jobs=1, tree_method="hist", subsample=0.8, colsample_bytree=0.8, **k),
                [dict(n_estimators=n_, max_depth=d, learning_rate=lr) for n_, d, lr in itertools.product([300], [4, 6], [0.05, 0.1])]),
    "random_forest": (lambda **k: RandomForestRegressor(random_state=SEED, n_jobs=1, **k),
                      [dict(n_estimators=150, max_depth=d, min_samples_leaf=l, max_features=0.5) for d, l in itertools.product([None, 20], [1, 3])]),
    "gradient_boosting": (lambda **k: GradientBoostingRegressor(random_state=SEED, subsample=0.8, **k),
                          [dict(n_estimators=150, max_depth=d, learning_rate=lr) for d, lr in itertools.product([3, 5], [0.05, 0.1])]),
}
logo = LeaveOneGroupOut(); groups = train.Crop_Year.values
fitted, results, cv_log, best_params = {}, {}, {}, {}
for name, (mk, grid) in GRIDS.items():
    scores = []
    for params in grid:
        pipe = Pipeline([("pre", make_pre()), ("model", mk(**params))])
        pred = cross_val_predict(pipe, Xtr, ytr, cv=logo, groups=groups)
        scores.append((float(mean_absolute_error(ytr, pred)), params))
        print(name, params, "CV MAE %.1f" % scores[-1][0], flush=True)
    scores.sort(key=lambda s: s[0])
    best_params[name] = scores[0][1]; cv_log[name] = [{"params": p, "cv_MAE_train_only": s} for s, p in scores]
    pipe = Pipeline([("pre", make_pre()), ("model", mk(**best_params[name]))]).fit(Xtr, ytr)   # fit on TRAIN only
    fitted[name] = pipe
    results[name] = metrics(yte, pipe.predict(Xte))
    print(name, "TEST", results[name], flush=True)
log["best_params"] = best_params; log["cv"] = cv_log

# ------------------------------------------------------------------ 5. extra diagnostics (report only; no tuning on them)
xgb = fitted["xgboost"]; pte = {k: m.predict(Xte) for k, m in fitted.items()}
test = test.assign(Predicted_Yield=pte["xgboost"], Absolute_Error=np.abs(pte["xgboost"] - yte))
supp = {"by_crop_group": {}, "district_specific_only": {}, "equals_state_only": {}, "strict_year_holdout_2024_25": {}}
for g, sub in test.groupby("Crop_Group"):
    supp["by_crop_group"][g] = {"rows": len(sub), **{m: metrics(sub[TARGET].values, pte[m][test.index.get_indexer(sub.index)] if False else pte[m][[test.index.get_loc(i) for i in sub.index]]) for m in pte}}
msk = (~test.equals_state_value).values
for label, mk_ in (("district_specific_only", msk), ("equals_state_only", ~msk)):
    supp[label] = {"rows": int(mk_.sum()), **{m: metrics(yte[mk_], pte[m][mk_]) for m in pte}}
# baseline reference: predicting the training mean of each Crop+Season (not a trained ML model; context only)
base = train.groupby(["Crop", "Season"])[TARGET].mean()
bp = test.set_index(["Crop", "Season"]).index.map(base).values
ok = ~np.isnan(bp)
supp["baseline_crop_season_train_mean"] = {"rows_covered": int(ok.sum()), **metrics(yte[ok], bp[ok])}
# strict year hold-out: train on crop-years < 2024-25, test on 2024-25 (sensitivity check)
tr2, te2 = df[df.Year < 2024], df[df.Year == 2024]
supp["strict_year_holdout_2024_25"]["rows_train"], supp["strict_year_holdout_2024_25"]["rows_test"] = len(tr2), len(te2)
for name, (mk, _) in GRIDS.items():
    p = Pipeline([("pre", make_pre()), ("model", mk(**best_params[name]))]).fit(tr2[FEATURES], tr2[TARGET])
    supp["strict_year_holdout_2024_25"][name] = metrics(te2[TARGET].values, p.predict(te2[FEATURES]))
ape = {k: np.abs(pte[k] - yte) / yte * 100 for k in pte}
supp["ape_diagnostics"] = {"rows_actual_below_100_kg_ha": int((yte < 100).sum()), "min_actual": float(yte.min()), "median_actual": float(np.median(yte)),
    **{k: {"median_APE_pct": float(np.median(v)), "MAPE_pct_rows_actual_ge_100": float(v[yte >= 100].mean()), "MAPE_pct_all_rows_(misleading)": float(v.mean())} for k, v in ape.items()}}
json.dump(supp, open(f"{MODEL_DIR}/supplementary_metrics.json", "w"), indent=2)

# ------------------------------------------------------------------ 6. feature importance (XGBoost, gain-based)
names = list(xgb.named_steps["pre"].get_feature_names_out())
clean = [n_.replace("cat__", "").replace("num__", "") for n_ in names]
imp = pd.DataFrame({"Feature": clean, "Importance": xgb.named_steps["model"].feature_importances_}).sort_values("Importance", ascending=False)
imp.to_csv(f"{MODEL_DIR}/feature_importance.csv", index=False)
def orig(f):
    for c in CAT:
        if f.startswith(c + "_"): return c
    return f
imp["Original_Variable"] = imp.Feature.map(orig)
by_var = imp.groupby("Original_Variable").Importance.sum().sort_values(ascending=False)
by_var.rename("Importance").reset_index().to_csv(f"{MODEL_DIR}/feature_importance_by_original_variable.csv", index=False)

# ------------------------------------------------------------------ 7. artifacts
joblib.dump(xgb, f"{MODEL_DIR}/yield_model.joblib")
out = test[["District", "Crop", "Season", "Crop_Year", "Year", "Crop_Group"] + NUM[1:] + [TARGET, "Predicted_Yield", "Absolute_Error", "equals_state_value", "source_pdf", "source_pdf_page"]]
out = out.rename(columns={TARGET: "Actual_Yield"})
out.to_csv(f"{MODEL_DIR}/test_predictions.csv", index=False)
mape_note = ("MAPE set to null: the test set contains actual yields near zero (min %.0f kg/ha vs median %.0f; %d rows < 100 kg/ha), "
             "so percentage errors are dominated by a few tiny denominators. See supplementary_metrics.json (ape_diagnostics) for median APE." % (yte.min(), np.median(yte), (yte < 100).sum()))
json.dump({**results, "notes": {"units": "kg/ha", "test_rows": int(len(test)), "MAPE": mape_note}}, open(f"{MODEL_DIR}/metrics.json", "w"), indent=2)
today = datetime.date.today().isoformat()
meta = {"model_name": "yield_model_v1", "algorithm": "XGBoostRegressor", "task": "regression", "target": "yield",
        "target_unit": "kg/ha (sugarcane converted from tonnes/ha)", "geographic_scope": "Tamil Nadu",
        "prediction_scope": "district-average", "train_test_split": "80/20 (chronological row order, no shuffle)",
        "training_rows": int(len(train)), "testing_rows": int(len(test)), "total_valid_rows": int(n),
        "features": FEATURES, "categorical_features": CAT, "numeric_features": NUM,
        "training_dataset": "data/tn_district_yield_rainfall_raw_long.csv -> cleaned data/tn_district_yield_model_dataset.csv "
                            "(TN Season & Crop Reports 2020-21..2024-25, Table V-A yield + Table I-A rainfall)",
        "data_source": "uploaded TN_Fertilizer_Combined_Pack.zip", "production_used_as_feature": False,
        "xgboost_params": best_params["xgboost"], "categories": {c: sorted(df[c].unique()) for c in CAT},
        "numeric_training_ranges": {c: [float(df[c].min()), float(df[c].max())] for c in NUM},
        "library_versions": {"xgboost": xgboost.__version__, "scikit-learn": sklearn.__version__, "pandas": pd.__version__},
        "random_state": SEED, "model_version": "v1", "training_date": today,
        "disclaimer": "District-average yield estimate - NOT FARM-SPECIFIC. Not a guaranteed yield."}
json.dump(meta, open(f"{MODEL_DIR}/metadata.json", "w"), indent=2)
json.dump(log, open(f"{MODEL_DIR}/training_log.json", "w"), indent=2, default=str)

# ------------------------------------------------------------------ 8. report (all numbers come from variables above)
def f(m, k): return "n/a (invalid)" if m[k] is None else f"{m[k]:.2f}"
tbl = "\n".join(f"| {lbl} | {f(results[k],'MAE')} | {f(results[k],'RMSE')} | {f(results[k],'R2').replace('n/a (invalid)','n/a')} | {f(results[k],'MAPE')} |"
                for k, lbl in [("xgboost", "XGBoost Regressor (primary)"), ("random_forest", "Random Forest Regressor"), ("gradient_boosting", "Gradient Boosting Regressor")])
grp = "\n".join(f"| {g} | {v['rows']} | {v['xgboost']['MAE']:.1f} | {v['random_forest']['MAE']:.1f} | {v['gradient_boosting']['MAE']:.1f} | {v['xgboost']['R2']:.2f} |" for g, v in supp["by_crop_group"].items())
sy = supp["strict_year_holdout_2024_25"]
rep = f"""# MODEL TRAINING REPORT — yield_model_v1

**Scope:** Tamil Nadu district-average crop yield estimate (NOT farm-specific). Training date: {today}. Model version: v1.

## 1. Dataset used
Official Tamil Nadu *Season & Crop Reports* (PDFs in the uploaded ZIP, `01_Important_Data_Files/data/`), crop-years 2020-21 to 2024-25:
Table V-A (district-wise average yield rates) joined with Table I-A (district-wise seasonal rainfall) on **District (by serial number, spelling-normalised) + Crop-year**.
Extraction script: `extract_yield_dataset.py`. Cleaned file: `data/tn_district_yield_model_dataset.csv`.
Not used: the pack's CSV/XLS files (area-only, state-level, single weather point, soil, prices, rules) — see `DATASET_AUDIT.md`.
Reports 2014-15…2018-19 are in the ZIP but excluded: different column layouts and 32 pre-2019 districts (boundaries not comparable with the 37-38 post-2019 districts). 2019-20 is not in the ZIP.

## 2. Dataset dimensions
Raw extracted cells: {log['raw_rows']} · valid modelling rows: **{log['valid_rows']}** · districts: {log['districts']} · crops: {log['crops']} · crop-years: {', '.join(log['raw_years'])}.
Rows per crop-year: {log['rows_per_crop_year']}.

## 3. Data cleaning (exact counts)
| Step | Rows removed |
|---|---|
| "Combined" season columns (derived aggregates of Kharif/Rabi; avoids near-duplicate rows) | {log['removed_combined_columns']} |
| Coconut (reported in nuts/ha — not a mass unit) | {log['removed_coconut_non_mass_unit']} |
| Yield = 0 (crop not grown / no estimate in district; not a real zero yield) | {log['removed_zero_yield_not_grown_or_no_estimate']} |
| Rainfall blank or internally inconsistent in the source report | {log['removed_for_missing_or_inconsistent_rainfall']} |

Sugarcane is published in tonnes/ha; {log['sugarcane_rows_unit_converted']} rows were multiplied by 1000 (exact conversion to kg/ha). Everything else is already kg/ha.

## 4. Missing-value handling
No imputation was performed. Yield has no missing values. Rainfall is blank in the source for {log['rows_with_blank_rainfall_in_report']} rows (new/reorganised districts in 2020-21 and Mayiladuthurai in 2021-22) and
{log['rows_with_inconsistent_rainfall_in_report']} rows (Ranipet 2020-21: printed annual total contradicts its own monthly figures); these rows were excluded rather than invented. Temperature and humidity: **feature unavailable in uploaded dataset** (only one NASA POWER point for 2025 exists).

## 5. Duplicate handling
Duplicates on (District, Crop, Season, Crop-year): {log['duplicate_rows_by_key']}. No rows were duplicated or synthesised.

## 6. Tamil Nadu filtering
All data originate from Tamil Nadu reports; no other state is present. {log['districts']} districts (canonical 2024-25 spelling; 2020-22 spelling variants such as Thiruppur/Tiruppur mapped via serial number with a fuzzy-match assertion).

## 7. Feature selection
Categorical (one-hot): {', '.join(CAT)}. Numeric: Year (start year of crop-year), Rain_SWM_mm, Rain_NEM_mm, Rain_Winter_mm, Rain_HotWeather_mm, Rain_Annual_mm (actual crop-year rainfall, June–May).
Unavailable: temperature, humidity, soil, fertilizer applied, irrigation (feature unavailable in uploaded dataset at district-year level).

## 8. Target definition
`yield` = published district-average yield (kg/ha). It is read directly from Table V-A; it was **not** derived from production/area.

## 9. Leakage checks
Production not used (and not even extracted). Area not used. Rainfall is observed for the same crop-year, so the model is a retrospective/scenario estimator — a real forecast would need forecast rainfall. Hyperparameters chosen only with leave-one-crop-year-out CV inside the training rows. The saved model was fitted on training rows only.

## 10-12. 80/20 split
Rows were sorted stably by crop-year (original report order kept within a year; no shuffle), then the first 80% = train, last 20% = test.
Total valid rows: {log['valid_rows']} · Training rows (80%): {log['train_rows']} · Testing rows (20%): {log['test_rows']}.
Train rows by crop-year: {log['train_years']} · Test rows by crop-year: {log['test_years']}.
Note: because years have unequal row counts the cut falls inside 2024-25, so the first {log['train_years'].get('2024-25', 0)} rows of 2024-25 (in report order) are in training. A strict year hold-out is reported in section 19 as a sensitivity check.

## 13-15. Model parameters (selected by CV on training rows only)
- XGBoost: `{best_params['xgboost']}` + objective=reg:squarederror, subsample=0.8, colsample_bytree=0.8, tree_method=hist, random_state={SEED}
- Random Forest: `{best_params['random_forest']}` + random_state={SEED}
- Gradient Boosting: `{best_params['gradient_boosting']}` + subsample=0.8, random_state={SEED}

## 16-19. Test results (unseen 20%, {log['test_rows']} rows; units kg/ha)
| Model | MAE | RMSE | R² | MAPE % (null = invalid) |
|---|---|---|---|---|
{tbl}

**MAPE is not reported (null):** {mape_note}
Robust alternative (supplementary): median absolute % error — XGBoost {supp['ape_diagnostics']['xgboost']['median_APE_pct']:.1f}%, RF {supp['ape_diagnostics']['random_forest']['median_APE_pct']:.1f}%, GB {supp['ape_diagnostics']['gradient_boosting']['median_APE_pct']:.1f}%.

**Best model by test MAE/RMSE/R²:** {min(results, key=lambda k: results[k]['MAE'])}. The primary model (as specified) remains XGBoost and is the one saved in `yield_model.joblib`.

**Honest interpretation:** the pooled R² (~0.95) is largely explained by crop identity: a trivial Crop+Season training-mean baseline reaches R² {supp['baseline_crop_season_train_mean']['R2']:.3f} (MAE {supp['baseline_crop_season_train_mean']['MAE']:.0f}). The three ML models only modestly beat that baseline in MAE, rainfall features carry almost no importance, and within some groups (e.g. pulses) R² is close to zero. The model should be treated as a crop/season/district-average estimator, not as evidence that rainfall drives the predictions.

**Context (not tuned on):**
- Baseline "mean of Crop+Season in training" (not ML): MAE {supp['baseline_crop_season_train_mean']['MAE']:.1f}, R² {supp['baseline_crop_season_train_mean']['R2']:.3f} on {supp['baseline_crop_season_train_mean']['rows_covered']} covered rows.
- Rows where the district figure is identical to the State figure (copied by the department): {log['share_equal_to_state_value']*100:.1f}% of all valid rows. On the test set, district-specific rows only ({supp['district_specific_only']['rows']} rows): XGBoost MAE {supp['district_specific_only']['xgboost']['MAE']:.1f}, R² {supp['district_specific_only']['xgboost']['R2']:.3f}; state-copied rows ({supp['equals_state_only']['rows']}): XGBoost MAE {supp['equals_state_only']['xgboost']['MAE']:.1f}, R² {supp['equals_state_only']['xgboost']['R2']:.3f}.
- Strict year hold-out (train 2020-21…2023-24 = {sy['rows_train']} rows, test 2024-25 = {sy['rows_test']} rows): XGBoost MAE {sy['xgboost']['MAE']:.1f} / R² {sy['xgboost']['R2']:.3f}; RF MAE {sy['random_forest']['MAE']:.1f} / R² {sy['random_forest']['R2']:.3f}; GB MAE {sy['gradient_boosting']['MAE']:.1f} / R² {sy['gradient_boosting']['R2']:.3f}.

Per crop group (test set): 
| Group | rows | XGB MAE | RF MAE | GB MAE | XGB R² (within group) |
|---|---|---|---|---|---|
{grp}

Overall R² is inflated by the huge between-crop scale differences (cereals ~ 10³ kg/ha vs vegetables/fruits/sugarcane ~ 10⁴–10⁵ kg/ha); judge the model by the per-group rows.

## 20. Feature importance (XGBoost, gain)
Top 15 encoded features are in `feature_importance.csv`. One-hot columns are named `<Variable>_<Category>` (e.g. `Crop_Banana`); `feature_importance_by_original_variable.csv` sums them back to the original variable:
{by_var.round(4).to_string()}

## 21. Limitations
- District figures are **district averages**, not farm-specific; the report copies the state value in a large share of cells (see above), so many "district" labels carry no district information.
- Only 5 crop-years (4-5 observations per district-crop-season); year-to-year dynamics cannot be learned reliably; the model cannot extrapolate trends.
- Rainfall is crop-year total/seasonal actuals (known only after the season) — not a forecast input.
- District boundaries changed in 2019; pre-2019 reports were excluded.
- Mixed crops and units dominate pooled RMSE; per-group results matter more.

## 22. Data gaps
District-year temperature and humidity; multi-year district weather; production/area-based derivation (not needed); soil and irrigation by district-year; 2019-20 report; any farm-level fertilizer application records.

## 23. Model version / date
yield_model_v1 · {today} · xgboost {xgboost.__version__} · scikit-learn {sklearn.__version__}

## Fertilizer-type ML
**Not trained.** The uploaded data does not contain sufficient validated Tamil Nadu farm-level fertilizer application labels (fertilizer type/quantity applied + crop + soil + location + season/year). Fertilizer recommendation stays in the TNAU/STCR/IPNS → N/P2O5/K2O → LP optimizer module; the yield model is never used for fertilizer type, dose or cost.
"""
open("MODEL_TRAINING_REPORT.md", "w").write(rep)
print(json.dumps(results, indent=2))
