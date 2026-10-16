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
from typing import Optional
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

DISTRICT_RAINFALL_NORMALS = {
    "Ariyalur": {"rain_swm": 366.7, "rain_nem": 551.8, "rain_winter": 84.4, "rain_hot": 149.7, "rain_annual": 1152.6},
    "Chengalpattu": {"rain_swm": 465.8, "rain_nem": 871.1, "rain_winter": 48.4, "rain_hot": 81.8, "rain_annual": 1467.1},
    "Chennai": {"rain_swm": 561.3, "rain_nem": 1077.9, "rain_winter": 57.6, "rain_hot": 70.8, "rain_annual": 1767.6},
    "Coimbatore": {"rain_swm": 1012.3, "rain_nem": 494.1, "rain_winter": 38.3, "rain_hot": 370.0, "rain_annual": 1914.7},
    "Cuddalore": {"rain_swm": 407.1, "rain_nem": 823.6, "rain_winter": 121.9, "rain_hot": 179.4, "rain_annual": 1532.1},
    "Dharmapuri": {"rain_swm": 425.6, "rain_nem": 363.4, "rain_winter": 16.4, "rain_hot": 228.6, "rain_annual": 1033.9},
    "Dindigul": {"rain_swm": 393.2, "rain_nem": 509.7, "rain_winter": 78.7, "rain_hot": 238.8, "rain_annual": 1220.4},
    "Erode": {"rain_swm": 304.3, "rain_nem": 390.2, "rain_winter": 23.7, "rain_hot": 207.4, "rain_annual": 925.6},
    "Kallakurichi": {"rain_swm": 370.9, "rain_nem": 522.2, "rain_winter": 20.4, "rain_hot": 190.8, "rain_annual": 1104.3},
    "Kancheepuram": {"rain_swm": 586.2, "rain_nem": 795.1, "rain_winter": 43.2, "rain_hot": 122.7, "rain_annual": 1547.2},
    "Kanniyakumari": {"rain_swm": 419.4, "rain_nem": 715.6, "rain_winter": 37.1, "rain_hot": 409.6, "rain_annual": 1581.8},
    "Karur": {"rain_swm": 276.4, "rain_nem": 337.5, "rain_winter": 31.6, "rain_hot": 116.8, "rain_annual": 762.2},
    "Krishnagiri": {"rain_swm": 430.2, "rain_nem": 350.0, "rain_winter": 12.2, "rain_hot": 204.0, "rain_annual": 996.3},
    "Madurai": {"rain_swm": 376.3, "rain_nem": 478.7, "rain_winter": 38.6, "rain_hot": 166.8, "rain_annual": 1060.4},
    "Mayiladuthurai": {"rain_swm": 250.3, "rain_nem": 870.2, "rain_winter": 119.1, "rain_hot": 123.9, "rain_annual": 1363.4},
    "Nagapattinam": {"rain_swm": 225.2, "rain_nem": 1024.4, "rain_winter": 188.0, "rain_hot": 169.2, "rain_annual": 1606.7},
    "Namakkal": {"rain_swm": 355.4, "rain_nem": 352.4, "rain_winter": 20.3, "rain_hot": 174.0, "rain_annual": 902.2},
    "Perambalur": {"rain_swm": 398.4, "rain_nem": 494.5, "rain_winter": 54.8, "rain_hot": 151.2, "rain_annual": 1098.8},
    "Pudukkottai": {"rain_swm": 354.6, "rain_nem": 452.8, "rain_winter": 73.7, "rain_hot": 123.8, "rain_annual": 1004.9},
    "Ramanathapuram": {"rain_swm": 150.5, "rain_nem": 576.9, "rain_winter": 88.3, "rain_hot": 143.8, "rain_annual": 959.6},
    "Ranipet": {"rain_swm": 635.6, "rain_nem": 548.9, "rain_winter": 24.0, "rain_hot": 182.7, "rain_annual": 1391.2},
    "Salem": {"rain_swm": 478.1, "rain_nem": 382.2, "rain_winter": 19.0, "rain_hot": 209.2, "rain_annual": 1088.5},
    "Sivagangai": {"rain_swm": 412.2, "rain_nem": 537.8, "rain_winter": 53.4, "rain_hot": 170.3, "rain_annual": 1173.7},
    "Tenkasi": {"rain_swm": 192.8, "rain_nem": 631.6, "rain_winter": 42.8, "rain_hot": 261.3, "rain_annual": 1128.4},
    "Thanjavur": {"rain_swm": 341.9, "rain_nem": 605.2, "rain_winter": 115.4, "rain_hot": 159.3, "rain_annual": 1221.8},
    "The Nilgiris": {"rain_swm": 1299.6, "rain_nem": 486.6, "rain_winter": 61.3, "rain_hot": 372.8, "rain_annual": 2220.3},
    "Theni": {"rain_swm": 401.1, "rain_nem": 462.5, "rain_winter": 48.1, "rain_hot": 240.7, "rain_annual": 1152.3},
    "Thoothukudi": {"rain_swm": 81.1, "rain_nem": 480.4, "rain_winter": 54.6, "rain_hot": 122.0, "rain_annual": 738.1},
    "Tiruchirapalli": {"rain_swm": 339.8, "rain_nem": 398.3, "rain_winter": 45.9, "rain_hot": 132.6, "rain_annual": 916.6},
    "Tirunelveli": {"rain_swm": 202.6, "rain_nem": 860.3, "rain_winter": 131.7, "rain_hot": 243.1, "rain_annual": 1437.8},
    "Tirupathur": {"rain_swm": 537.0, "rain_nem": 408.1, "rain_winter": 7.5, "rain_hot": 190.7, "rain_annual": 1143.3},
    "Tiruppur": {"rain_swm": 200.0, "rain_nem": 396.3, "rain_winter": 38.1, "rain_hot": 152.0, "rain_annual": 786.4},
    "Tiruvallur": {"rain_swm": 573.4, "rain_nem": 820.7, "rain_winter": 56.8, "rain_hot": 108.5, "rain_annual": 1559.5},
    "Tiruvannamalai": {"rain_swm": 538.5, "rain_nem": 590.8, "rain_winter": 31.8, "rain_hot": 188.2, "rain_annual": 1349.3},
    "Tiruvarur": {"rain_swm": 339.4, "rain_nem": 771.8, "rain_winter": 170.3, "rain_hot": 170.7, "rain_annual": 1452.2},
    "Vellore": {"rain_swm": 546.6, "rain_nem": 442.9, "rain_winter": 24.9, "rain_hot": 196.9, "rain_annual": 1211.4},
    "Villupuram": {"rain_swm": 495.4, "rain_nem": 726.8, "rain_winter": 42.6, "rain_hot": 143.8, "rain_annual": 1408.6},
    "Virudhunagar": {"rain_swm": 246.6, "rain_nem": 513.5, "rain_winter": 55.0, "rain_hot": 204.0, "rain_annual": 1019.0}
}


def predict_district_yield(
    district: str,
    crop: str,
    season: str = "Kharif",
    year: int = 2024,
    rain_swm: Optional[float] = None,
    rain_nem: Optional[float] = None,
    rain_winter: Optional[float] = None,
    rain_hot: Optional[float] = None,
    rain_annual: Optional[float] = None
) -> float:
    """
    Predict district-average yield in kg/ha using the trained Phase 2 XGBoost model.
    Rejects unsupported categories or missing model artifacts with explicit exceptions.
    """
    if not os.path.exists(MODEL):
        raise FileNotFoundError(f"Trained yield model artifact not found at '{MODEL}'.")
    if not os.path.exists(META):
        raise FileNotFoundError(f"Yield model metadata not found at '{META}'.")

    meta = json.load(open(META, "r", encoding="utf-8"))
    model = joblib.load(MODEL)

    # Validate District
    d_match = None
    for d in meta["categories"]["District"]:
        if d.lower() == district.strip().lower():
            d_match = d
            break
    if not d_match:
        # Check alias (e.g., Trichy -> Tiruchirappalli)
        alias_map = {"trichy": "Tiruchirappalli", "nellai": "Tirunelveli", "tanjore": "Thanjavur"}
        d_alias = alias_map.get(district.strip().lower())
        if d_alias and d_alias in meta["categories"]["District"]:
            d_match = d_alias
        else:
            raise ValueError(f"District '{district}' is not supported by the district yield benchmark model. Valid districts: {', '.join(sorted(meta['categories']['District']))}")

    # Validate Crop
    c_match = None
    for c in meta["categories"]["Crop"]:
        if c.lower() == crop.strip().lower() or (crop.strip().lower() in c.lower()):
            c_match = c
            break
    if not c_match:
        crop_alias = {"paddy": "Rice", "cotton": "Cotton (lint)", "sugarcane": "Sugarcane", "corn": "Maize"}
        alias_c = crop_alias.get(crop.strip().lower())
        if alias_c and alias_c in meta["categories"]["Crop"]:
            c_match = alias_c
        else:
            raise ValueError(f"Crop '{crop}' is not supported by the district yield benchmark model. Valid crops: {', '.join(sorted(meta['categories']['Crop']))}")

    # Validate Season
    s_match = None
    for s in meta["categories"]["Season"]:
        if season.strip().lower() in s.lower() or s.lower() in season.strip().lower():
            s_match = s
            break
    if not s_match:
        s_match = meta["categories"]["Season"][0]  # Standard seasonal default fallback if close

    # Validate rainfall normals or supplied scenario inputs
    normals = DISTRICT_RAINFALL_NORMALS.get(d_match, {
        "rain_swm": 330.0, "rain_nem": 640.0, "rain_winter": 40.0, "rain_hot": 150.0, "rain_annual": 1160.0
    })
    r_swm = rain_swm if rain_swm is not None else normals["rain_swm"]
    r_nem = rain_nem if rain_nem is not None else normals["rain_nem"]
    r_winter = rain_winter if rain_winter is not None else normals["rain_winter"]
    r_hot = rain_hot if rain_hot is not None else normals["rain_hot"]
    r_annual = rain_annual if rain_annual is not None else normals["rain_annual"]

    for r_name, r_val in [("rain_swm", r_swm), ("rain_nem", r_nem), ("rain_winter", r_winter), ("rain_hot", r_hot), ("rain_annual", r_annual)]:
        if r_val < 0:
            raise ValueError(f"Rainfall parameter '{r_name}' cannot be negative ({r_val} mm).")

    row = pd.DataFrame([{
        "District": d_match, "Crop": c_match, "Season": s_match, "Year": int(year),
        "Rain_SWM_mm": float(r_swm), "Rain_NEM_mm": float(r_nem), "Rain_Winter_mm": float(r_winter),
        "Rain_HotWeather_mm": float(r_hot), "Rain_Annual_mm": float(r_annual)
    }])[meta["features"]]

    pred = float(model.predict(row)[0])
    return pred


if __name__ == "__main__":
    main()
