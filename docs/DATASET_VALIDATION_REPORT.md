# DATASET VALIDATION REPORT
**Sustainable Fertilizer Usage Optimizer for Tamil Nadu Farmers (Phase 1)**

---

## 1. Data Quality Checks & Cleaning Pipeline

The data validation pipeline (`dataset_audit.py` & `extract_yield_dataset.py`) performed the following data quality checks:

1. **District Name Normalization:** Standardized all district name variations across 38 official Tamil Nadu districts (e.g., mapping "Trichy" -> "Tiruchirapalli", "Tanjore" -> "Thanjavur", "Tuticorin" -> "Thoothukudi").
2. **Missing Value Auditing:** Evaluated missing values in numerical columns. Zero-area records were removed to prevent divide-by-zero errors in yield calculation.
3. **Target Leakage Prevention:** Verified that target `Yield_kg_per_ha` is derived as $\text{Production\_tonnes} \times 1000 / \text{Area\_ha}$ during preprocessing, and `Production_tonnes` is strictly removed from feature matrix $X$.
4. **Physiological & Unit Boundaries:** Checked that rainfall values are strictly non-negative and within historical Tamil Nadu ranges ($0 - 3500 \text{ mm}$).

---

## 2. Soil & Weather Data Separation

- **Soil Test Data:** Soil N, P, K, pH, and OC measurements are strictly sourced from farmer soil health cards / laboratory reports (Phase 3) or entered directly. District-average soil data is never used to substitute an individual farmer's soil report.
- **Weather Data:** Historical seasonal rainfall (SWM, NEM, Winter, Hot Weather) is used for training the yield prediction model, while current forecast advisories (`phase7_integration/weather.py`) are used for real-time fertilizer timing guidance.
