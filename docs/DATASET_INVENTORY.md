# DATASET INVENTORY REPORT
**Sustainable Fertilizer Usage Optimizer for Tamil Nadu Farmers (Phase 1)**

---

## 1. Inventory Summary

This report documents all raw, processed, and reference datasets utilized by the project.

| Filename | Location | Source / Origin | Row Count | Columns | Date Coverage | Geographic Coverage | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `tn_district_yield_model_dataset.csv` | `data/` | Directorate of Economics and Statistics (DES) & IMD | 4,284 | 14 | 1998 - 2020 | 38 Districts in Tamil Nadu | Training & evaluating XGBoost crop yield prediction model |
| `tn_district_yield_rainfall_raw_long.csv` | `data/` | IMD Rainfall & DES Crop Production records | 18,450 | 12 | 1998 - 2020 | Tamil Nadu Districts | Raw long-format district crop production data |
| `source_registry.csv` | `data/agronomy/` | TNAU Official Agronomic Publications | 7 | 7 | 2018 - 2020 | Tamil Nadu Statewide | Agronomic source traceability & verification registry |
| `tnau_stcr_rules.json` | `data/agronomy/` | TNAU STCR Cell & Crop Production Guides | 9 | 16 | 2020 | Tamil Nadu Agro-climatic zones | Agronomic rule database for rule selection & NPK calculation |

---

## 2. Dataset Column Schemas

### `tn_district_yield_model_dataset.csv`
- `State`: State name ("Tamil Nadu").
- `District`: District name (38 standardized Tamil Nadu districts).
- `Crop`: Crop name (Rice, Maize, Groundnut, Sugarcane, Cotton (lint), Ragi, Banana, Tomato, Onion, Turmeric).
- `Season`: Season classification (Kharif, Rabi, Summer, Whole Year, Samba/Thaladi/Pishanam).
- `Year`: Crop-year start year.
- `Area_ha`: Cultivated area in hectares.
- `Production_tonnes`: Total crop production in tonnes.
- `Yield_kg_per_ha`: Calculated target variable ($\text{Production\_tonnes} \times 1000 / \text{Area\_ha}$).
- `Rain_SWM_mm`: South-West Monsoon rainfall (mm).
- `Rain_NEM_mm`: North-East Monsoon rainfall (mm).
- `Rain_Winter_mm`: Winter season rainfall (mm).
- `Rain_HotWeather_mm`: Hot weather season rainfall (mm).
- `Rain_Annual_mm`: Total annual rainfall (mm).

---

## 3. Dataset Leakage & Use Guards

1. **Target Leakage Prevention:** `Production_tonnes` is strictly excluded from input feature vectors during ML model training and inference.
2. **Geographic Isolation:** District-level yield estimates are explicitly labeled as **District Benchmarks** and are never presented as farm-specific yield guarantees.
