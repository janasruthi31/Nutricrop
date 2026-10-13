"""
Build the district-level yield + rainfall dataset from the uploaded Tamil Nadu Season & Crop Reports.
Source: PDFs inside TN_Fertilizer_Combined_Pack.zip  (01_Important_Data_Files/data/)
Years used: 2020-21 ... 2024-25 (consistent 93-column Table V-A layout, 37-38 post-2019 districts).
Outputs  : data/tn_district_yield_rainfall_2020_25.csv  and  data/extraction_qa.json
Nothing is generated or filled: every value is a number printed in the reports.
"""
import sys, json, os, difflib
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scr_extract as se

PDF_DIR = sys.argv[1] if len(sys.argv) > 1 else "TN_pack/01_Important_Data_Files/data"
OUT_DIR = "data"
CANON = {}   # serial number -> canonical district spelling (taken from SCR 2024-25)
FILES = {"2024-25": "SCR2024-25.pdf", "2020-21": "SCR 2020-21.pdf", "2021-22": "SCR 2021-22.pdf",
         "2022-23": "SCR2022-23.pdf", "2023-24": "SRC2023-24.pdf"}

# Column number (printed in Table V-A) -> (crop, season, unit_in_report). Decoded from the rotated headers.
def _ksc(first, crop):  # Kharif, Rabi, Combined triple
    return {first: (crop, "Kharif"), first + 1: (crop, "Rabi"), first + 2: (crop, "Combined")}
COLMAP = {3: ("Rice", "Kuruvai/Kar/Sornavari"), 4: ("Rice", "Samba/Thaladi/Pishanam"),
          5: ("Rice", "Navarai/Kodai"), 6: ("Rice", "Combined")}
for first, crop in [(7, "Jowar"), (10, "Bajra"), (13, "Ragi"), (16, "Maize"), (20, "Varagu"), (23, "Samai"),
                    (28, "Red gram"), (31, "Green gram"), (34, "Black gram"), (37, "Horse gram"),
                    (40, "Cowpea"), (43, "Other pulses"), (59, "Potato"), (62, "Onion"),
                    (78, "Groundnut"), (81, "Gingelly"), (84, "Sunflower"), (89, "Cotton (lint)")]:
    COLMAP.update(_ksc(first, crop))
SINGLE = {19: "Korra", 26: "Other cereals", 27: "Bengal gram", 46: "Sugarcane", 47: "Arecanut", 48: "Chillies",
          49: "Cloves", 50: "Garlic", 51: "Pepper", 52: "Ginger", 53: "Turmeric", 54: "Coriander",
          55: "Cardamom", 56: "Tamarind", 57: "Tapioca", 58: "Sweet potato", 65: "Brinjal",
          66: "Lady's finger", 67: "Cabbage", 68: "Tomato", 69: "Banana", 70: "Mango", 71: "Lemon",
          72: "Orange", 73: "Cashew nut", 74: "Jack fruit", 75: "Pineapple", 76: "Guava", 77: "Grapes",
          87: "Rapeseed & mustard", 88: "Castor", 92: "Tobacco", 93: "Coconut"}
for c, crop in SINGLE.items():
    COLMAP[c] = (crop, "Annual")
UNIT_FACTOR = {"Sugarcane": 1000.0}          # report unit: tonnes/ha -> kg/ha (exact conversion)
EXCLUDED_CROPS = {"Coconut": "reported in nuts/ha (not a mass unit; not convertible to kg/ha)"}

# Rainfall pages (Table I-A): page order -> list of (label, offset-of-'actual' within the 9 numeric columns)
RAIN_LAYOUT = [("jun", "jul", "aug"), ("sep", "swm_total", "oct"), ("nov", "dec", "nem_total"),
               ("jan", "feb", "winter_total"), ("mar", "apr", "may"), ("hot_total", "annual")]

def build_rain(rv, qa, year):
    recs = {}
    for page_i, page in enumerate(rv):
        labels = RAIN_LAYOUT[page_i]
        first = page["col_nos"][0]
        for r in page["rows"]:
            if r["sl"] == 0:   # State row
                continue
            d = recs.setdefault(r["sl"], {"_name": r["district"]})
            for k, lab in enumerate(labels):
                # each group = actual, normal, %dev  -> 3 consecutive printed columns
                d[f"{lab}_actual"] = r["values"].get(first + 3 * k)
                d[f"{lab}_normal"] = r["values"].get(first + 3 * k + 1)
    bad = 0
    for sl, d in recs.items():
        dist = d["_name"]
        needed = [f"{m}_actual" for m in ("jun","jul","aug","sep","oct","nov","dec","swm_total","nem_total","winter_total","hot_total","annual")]
        if any(d.get(k) is None for k in needed):
            qa.setdefault(f"rain_{year}_districts_with_blank_rainfall_in_report", []).append(dist)
            d["_blank"] = True
            continue
        swm = sum(d[f"{m}_actual"] for m in ("jun", "jul", "aug", "sep"))
        nem = sum(d[f"{m}_actual"] for m in ("oct", "nov", "dec"))
        ann = d["swm_total_actual"] + d["nem_total_actual"] + d["winter_total_actual"] + d["hot_total_actual"]
        if abs(swm - d["swm_total_actual"]) > 1.0 or abs(nem - d["nem_total_actual"]) > 1.0 or abs(ann - d["annual_actual"]) > 2.0:
            bad += 1
            d["_inconsistent"] = True
            qa.setdefault(f"rain_{year}_districts_with_internally_inconsistent_rainfall", []).append(dist)
    qa[f"rain_{year}_arithmetic_mismatch_districts"] = bad
    return recs

def main():
    qa = {"fixed_missing_printed_column_numbers": []}
    rows = []
    for year, fn in FILES.items():
        path = os.path.join(PDF_DIR, fn)
        yv = se.extract_report(path, se.YIELD_RE)
        rv = se.extract_report(path, se.RAIN_RE)
        rain = build_rain(rv, qa, year)
        state = {}
        if year == "2024-25":
            CANON.update({r["sl"]: r["district"] for r in yv[0]["rows"] if r["sl"] > 0})
        for page in yv:
            for r in page["rows"]:
                if r["district"].lower().startswith("state"):
                    state.update(r["values"])
        for page in yv:
            for r in page["rows"]:
                if r["district"].lower().startswith("state"): continue
                rr = rain.get(r["sl"], {})
                canon = CANON[r["sl"]]
                assert difflib.SequenceMatcher(None, r["district"].lower(), canon.lower()).ratio() > 0.75, (year, r["district"], canon)
                assert difflib.SequenceMatcher(None, rr.get("_name", canon).lower(), canon.lower()).ratio() > 0.75, (year, rr.get("_name"), canon)
                for col, val in r["values"].items():
                    crop, season = COLMAP[col]
                    rows.append({"District": canon, "District_as_printed": r["district"], "Rain_flag": "blank_in_report" if rr.get("_blank") else ("inconsistent_in_report" if rr.get("_inconsistent") else "ok"), "Crop": crop, "Season": season,
                                 "Crop_Year": year, "Year": int(year[:4]), "column_no": col,
                                 "reported_value": val, "state_value": state.get(col),
                                 **{k: rr.get(k) for k in
                                    ("swm_total_actual", "nem_total_actual", "winter_total_actual",
                                     "hot_total_actual", "annual_actual")},
                                 "source_pdf": fn, "source_pdf_page": page["pdf_page"]})
        qa[f"{year}_districts"] = len({r["District"] for r in rows if r["Crop_Year"] == year})
    rows.sort(key=lambda r: (r["Year"],))  # chronological, stable (keeps report order within a year)
    qa["fixed_missing_printed_column_numbers"] = se.FIXED_MISSING_COLS
    df = pd.DataFrame(rows)
    df.rename(columns={"swm_total_actual": "Rain_SWM_mm", "nem_total_actual": "Rain_NEM_mm",
                       "winter_total_actual": "Rain_Winter_mm", "hot_total_actual": "Rain_HotWeather_mm",
                       "annual_actual": "Rain_Annual_mm"}, inplace=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    df.to_csv(os.path.join(OUT_DIR, "tn_district_yield_rainfall_raw_long.csv"), index=False)
    json.dump(qa, open(os.path.join(OUT_DIR, "extraction_qa.json"), "w"), indent=2, default=str)
    print(df.shape, qa)

if __name__ == "__main__":
    main()
