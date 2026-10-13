"""Step-1 audit of every file in TN_Fertilizer_Combined_Pack.zip (extracted dir passed as argv[1])."""
import os, sys, glob, json, io, re
import pandas as pd

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/data"
OUT = sys.argv[2] if len(sys.argv) > 2 else "DATASET_AUDIT.md"
KEYS = {"yield": r"yield", "production": r"production", "rainfall": r"rain|prectot", "temperature": r"temp|t2m",
        "humidity": r"humid|rh2m", "fertilizer": r"fertili|urea|dap|mop|npk|n_percent|p2o5|k2o"}

def flags(cols):
    low = " ".join(c.lower() for c in cols)
    return {k: bool(re.search(p, low)) for k, p in KEYS.items()}

def col_find(df, pat):
    for c in df.columns:
        if re.search(pat, str(c).lower()): return c
    return None

def audit_df(name, df, note):
    r = {"file": name, "rows": len(df), "cols": df.shape[1], "columns": [str(c) for c in df.columns],
         "missing_cells": int(df.isna().sum().sum()),
         "missing_by_col": {str(k): int(v) for k, v in df.isna().sum().items() if v},
         "duplicate_rows": int(df.duplicated().sum())}
    sc = col_find(df, r"^state$|state_name"); dc = col_find(df, r"district"); cc = col_find(df, r"^crop"); yc = col_find(df, r"^year|^yr")
    sec = col_find(df, r"season|domain")
    r["state_coverage"] = sorted(set(map(str, df[sc].dropna().unique())))[:10] if sc else "no state column"
    r["tamil_nadu_coverage"] = ("all rows Tamil Nadu (state column)" if sc and set(map(str, df[sc].dropna().unique())) == {"Tamil Nadu"} else
                                "Tamil Nadu-specific by source (no state column)" if not sc else "mixed")
    r["district_coverage"] = f"{df[dc].nunique()} districts" if dc else "no district column"
    r["crop_coverage"] = f"{df[cc].nunique()} crops" if cc else ("crops as columns" if "Rice (Paddy)" in df.columns else "no crop column")
    r["year_range"] = f"{df[yc].min()}–{df[yc].max()}" if yc else "no year column"
    r["season_coverage"] = sorted(set(map(str, df[sec].dropna().unique())))[:8] if sec else "no season column"
    r.update({f"{k}_available": v for k, v in flags(df.columns).items()})
    r["suitable_for_yield_ml"] = note
    return r

res = []
# --- CSV
for f in sorted(glob.glob(f"{ROOT}/**/*.csv", recursive=True)):
    df = pd.read_csv(f)
    rel = os.path.relpath(f, ROOT)
    note = "NO"
    if "tn_district_crop_area_reports_long" in f: note = "NO – area only (no yield/production); 3 seasons of 2024-25 only"
    elif "state_crop_yield_reference" in f: note = "NO – state-level, 12 rows; used only as an independent validation of extracted State rows"
    elif "weather_power" in f: note = "NO – single grid point (11N,77E), year 2025 only; not district-level, no yield year overlap"
    elif "soil" in f: note = "NO – soil snapshot, no yield/year dimension"
    elif "fertilizer" in f or "rules" in f: note = "NO – reference/price/rule table (belongs to the separate fertilizer module)"
    res.append(audit_df(rel, df, note))
# --- HTML-as-.xls
for f in sorted(glob.glob(f"{ROOT}/**/*.xls", recursive=True)):
    try:
        df = pd.read_html(io.StringIO(open(f, encoding="utf-8", errors="ignore").read()))[0]
    except Exception as e:
        res.append({"file": os.path.relpath(f, ROOT), "error": str(e)}); continue
    r = audit_df(os.path.relpath(f, ROOT), df, "NO – crop AREA by district for one season (no yield, no production, single season-year)")
    r["note"] = "file is an HTML table saved with .xls extension; crops are columns, values are area"
    res.append(r)

others = {"PDF": sorted(glob.glob(f"{ROOT}/**/*.pdf", recursive=True)), "HTM": sorted(glob.glob(f"{ROOT}/**/*.htm", recursive=True)),
          "MD": sorted(glob.glob(f"{ROOT}/**/*.md", recursive=True)), "TXT": sorted(glob.glob(f"{ROOT}/**/*.txt", recursive=True)),
          "PY": sorted(glob.glob(f"{ROOT}/**/*.py", recursive=True)), "JSON": sorted(glob.glob(f"{ROOT}/**/*.json", recursive=True))}

with open(OUT, "w") as w:
    w.write("# STEP 1 — DATASET AUDIT (TN_Fertilizer_Combined_Pack.zip)\n\n## Tabular files (CSV and HTML-based .xls)\n\n")
    for r in res:
        w.write(f"### {r['file']}\n")
        for k, v in r.items():
            if k != "file": w.write(f"- **{k}**: {v}\n")
        w.write("\n")
    w.write("## Non-tabular files (not auto-parsed; PDFs inspected selectively)\n\n")
    for k, v in others.items():
        w.write(f"**{k}** ({len(v)} files)\n")
        for p in v: w.write(f"- {os.path.relpath(p, ROOT)}\n")
        w.write("\n")
json.dump(res, open(OUT.replace(".md", ".json"), "w"), indent=2, default=str)
print(len(res), "tabular files audited; others:", {k: len(v) for k, v in others.items()})
