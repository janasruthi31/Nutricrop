#!/usr/bin/env python3
"""
Predict a DISTRICT-AVERAGE crop yield estimate with models/yield_prediction/yield_model.joblib.
This is NOT a farm-specific prediction and NOT a guaranteed yield. It is unrelated to fertilizer
type / dose / cost (those come from the separate TNAU/STCR/IPNS + LP optimizer module).

Example:
  python predict_yield.py --district Thanjavur --crop Rice --season "Samba/Thaladi/Pishanam" --year 2024 \
      --rain-swm 330 --rain-nem 640 --rain-winter 40 --rain-hot 150 --rain-annual 1160
"""
import argparse, json, sys, os
import joblib, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "models/yield_prediction/yield_model.joblib")
META = os.path.join(HERE, "models/yield_prediction/metadata.json")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--district", required=True); ap.add_argument("--crop", required=True)
    ap.add_argument("--season", required=True, help="e.g. Kharif, Rabi, Annual, 'Samba/Thaladi/Pishanam' (see metadata.json)")
    ap.add_argument("--year", type=int, required=True, help="start year of crop-year, e.g. 2024 for 2024-25")
    ap.add_argument("--rain-swm", type=float, required=True, help="South-West monsoon rainfall, mm (Jun-Sep)")
    ap.add_argument("--rain-nem", type=float, required=True, help="North-East monsoon rainfall, mm (Oct-Dec)")
    ap.add_argument("--rain-winter", type=float, required=True, help="Winter rainfall, mm (Jan-Feb)")
    ap.add_argument("--rain-hot", type=float, required=True, help="Hot-weather rainfall, mm (Mar-May)")
    ap.add_argument("--rain-annual", type=float, required=True, help="Whole crop-year rainfall, mm")
    a = ap.parse_args()
    meta = json.load(open(META)); model = joblib.load(MODEL)
    for key, val in (("District", a.district), ("Crop", a.crop), ("Season", a.season)):
        if val not in meta["categories"][key]:
            sys.exit(f"Unknown {key} '{val}'. Valid values: {meta['categories'][key]}")
    row = pd.DataFrame([{"District": a.district, "Crop": a.crop, "Season": a.season, "Year": a.year,
                         "Rain_SWM_mm": a.rain_swm, "Rain_NEM_mm": a.rain_nem, "Rain_Winter_mm": a.rain_winter,
                         "Rain_HotWeather_mm": a.rain_hot, "Rain_Annual_mm": a.rain_annual}])[meta["features"]]
    warn = [f"{c}={row[c].iloc[0]} is outside the training range {lo:.0f}-{hi:.0f}" for c, (lo, hi) in meta["numeric_training_ranges"].items()
            if not lo <= row[c].iloc[0] <= hi]
    pred = float(model.predict(row)[0])
    print("=" * 66)
    print("District-average yield estimate — NOT FARM-SPECIFIC")
    print("=" * 66)
    print(f"District: {a.district} | Crop: {a.crop} | Season: {a.season} | Crop-year start: {a.year}")
    print(f"Estimated district-average yield: {pred:,.0f} kg/ha")
    print("This is a statistical estimate from official district averages, not a guaranteed yield.")
    print("It does not determine fertilizer type, dose or cost.")
    for w in warn: print("WARNING:", w)

def predict_district_yield(
    district: str,
    crop: str,
    season: str = "Kharif",
    year: int = 2024,
    rain_swm: float = 330.0,
    rain_nem: float = 640.0,
    rain_winter: float = 40.0,
    rain_hot: float = 150.0,
    rain_annual: float = 1160.0
) -> float:
    """Predict district average yield in kg/ha."""
    if not os.path.exists(MODEL) or not os.path.exists(META):
        return 3500.0  # Fallback estimate if model file missing

    meta = json.load(open(META))
    model = joblib.load(MODEL)

    # Normalize category strings if available
    d_match = district
    for d in meta["categories"]["District"]:
        if d.lower() == district.lower():
            d_match = d
            break

    c_match = crop
    for c in meta["categories"]["Crop"]:
        if c.lower() == crop.lower():
            c_match = c
            break

    s_match = season
    for s in meta["categories"]["Season"]:
        if season.lower() in s.lower():
            s_match = s
            break

    row = pd.DataFrame([{
        "District": d_match, "Crop": c_match, "Season": s_match, "Year": year,
        "Rain_SWM_mm": rain_swm, "Rain_NEM_mm": rain_nem, "Rain_Winter_mm": rain_winter,
        "Rain_HotWeather_mm": rain_hot, "Rain_Annual_mm": rain_annual
    }])[meta["features"]]

    pred = float(model.predict(row)[0])
    return pred


if __name__ == "__main__":
    main()
