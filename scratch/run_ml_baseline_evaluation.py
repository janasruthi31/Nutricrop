import json
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA = "data/tn_district_yield_model_dataset.csv"
MODEL_PATH = "models/yield_prediction/yield_model.joblib"

df = pd.read_csv(DATA)
n = len(df)
n_train = int(round(0.8 * n))
train, test = df.iloc[:n_train].copy(), df.iloc[n_train:].copy()

yte = test["yield"].values
ytr = train["yield"].values

# 1. Overall mean baseline
mean_val = np.mean(ytr)
p_overall_mean = np.full_like(yte, fill_value=mean_val)

# 2. Crop + Season mean baseline
crop_season_mean = train.groupby(["Crop", "Season"])["yield"].mean()
p_crop_season_mean = np.array(test.set_index(["Crop", "Season"]).index.map(crop_season_mean).values, copy=True)
# Fallback to Crop mean if (Crop, Season) not in train
crop_mean = train.groupby("Crop")["yield"].mean()
nan_mask = np.isnan(p_crop_season_mean)
p_crop_season_mean[nan_mask] = test.set_index("Crop").index.map(crop_mean).values[nan_mask]
# Fallback to overall mean if still nan
nan_mask2 = np.isnan(p_crop_season_mean)
p_crop_season_mean[nan_mask2] = mean_val

# 3. Simple Linear Regression (Ridge) on Crop + Season + District
cat_cols = ["Crop", "Season", "District"]
pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)])
pipe_ridge = Pipeline([("pre", pre), ("reg", Ridge(alpha=1.0))])
pipe_ridge.fit(train[cat_cols], ytr)
p_ridge = pipe_ridge.predict(test[cat_cols])

# 4. Existing trained XGBoost pipeline
xgb_model = joblib.load(MODEL_PATH)
features = ["District", "Crop", "Season", "Year", "Rain_SWM_mm", "Rain_NEM_mm", "Rain_Winter_mm", "Rain_HotWeather_mm", "Rain_Annual_mm"]
p_xgb = xgb_model.predict(test[features])

def compute_metrics(y, p):
    return {
        "MAE": float(mean_absolute_error(y, p)),
        "RMSE": float(np.sqrt(mean_squared_error(y, p))),
        "R2": float(r2_score(y, p)),
        "Sample_Count": len(y)
    }

models = {
    "Overall_Mean_Baseline": p_overall_mean,
    "Crop_Season_Mean_Baseline": p_crop_season_mean,
    "Simple_Ridge_Regression": p_ridge,
    "Trained_XGBoost_Model": p_xgb
}

overall_results = {}
for name, p in models.items():
    overall_results[name] = compute_metrics(yte, p)

# Crop Group breakdown
test["pred_xgb"] = p_xgb
test["pred_cs_mean"] = p_crop_season_mean
group_results = {}
for g, sub in test.groupby("Crop_Group"):
    y_sub = sub["yield"].values
    group_results[g] = {
        "Rows": len(sub),
        "Crop_Season_Mean": compute_metrics(y_sub, sub["pred_cs_mean"].values),
        "XGBoost": compute_metrics(y_sub, sub["pred_xgb"].values)
    }

# Equals State breakdown
eq_results = {}
for is_eq in [True, False]:
    sub = test[test["equals_state_value"] == is_eq]
    label = "Equals_State_Imputed" if is_eq else "District_Specific_Survey"
    eq_results[label] = {
        "Rows": len(sub),
        "Crop_Season_Mean": compute_metrics(sub["yield"].values, sub["pred_cs_mean"].values),
        "XGBoost": compute_metrics(sub["yield"].values, sub["pred_xgb"].values)
    }

output = {
    "Overall": overall_results,
    "By_Crop_Group": group_results,
    "By_Imputation_Status": eq_results
}

print(json.dumps(output, indent=2))
with open("audit/ml_eval_results.json", "w") as f:
    json.dump(output, f, indent=2)
