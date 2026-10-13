# ARCHITECTURE AUDIT REPORT
**Sustainable Fertilizer Usage Optimizer for Tamil Nadu Farmers (SIH1639)**

---

## 1. Baseline System Inspection

A complete audit of the repository, data assets, microservices, databases, ML models, and API endpoints was conducted.

### Summary of Audit Findings

| Component | Architecture & Code Inspection Result | Required Correction / Enhancement |
| :--- | :--- | :--- |
| **Phase 3: Soil OCR** | Working PDF/JPEG upload & Tesseract OCR engine in `phase3_soil/`. SQLite tables present (`soil_documents`, `soil_profiles`). | Standardize explicit document status vocabulary (`EXTRACTED_PENDING_CONFIRMATION`, `CONFIRMED`, `OCR_FAILED`, `INVALID_INPUT`). |
| **Phase 4: Rule Selection** | Rule database (`data/agronomy/tnau_stcr_rules.json`) and source registry (`data/agronomy/source_registry.csv`). Selection engine in `agronomy/service.py`. | Add explicit rule `version` field. Ensure rule selection strictly enforces hard eligibility conditions before applying precedence, and returns explicit ambiguity/missing input states without arbitrary score overrides. |
| **Phase 5: NPK Calculation** | Evaluates STCR linear regression formulas and TNAU soil test rating multipliers in `phase5_nutrient/service.py`. | Ensure generic rating multipliers are NEVER applied on top of STCR targeted yield equations unless explicitly prescribed by authoritative source. Ensure strict elemental ($P, K$) vs oxide ($\text{P}_2\text{O}_5, \text{K}_2\text{O}$) distinction. |
| **Phase 6: LP Optimizer** | LP solver using `scipy.optimize.linprog` in `phase6_fertilizer/service.py`. Fertilizer product catalog in `phase6_fertilizer/catalog.py`. | Add MILP / post-rounding nutrient sufficiency check after ceiling/rounding bag quantities to guarantee that bag-rounded solutions NEVER under-apply required nutrients. Ensure endpoint compatibility with `/api/fertilizer-optimization/optimize`. |
| **Phase 7: Weather & Pipeline** | Weather advisory service in `phase7_integration/weather.py` and master recommendation pipeline in `phase7_integration/service.py`. | Ensure weather API failures or ML model timeouts fail open gracefully without replacing valid agronomic recommendations with dummy values. Update Flutter app models & screens. |
| **Phase 2: Yield Model** | XGBoost Regressor model artifact `models/yield_prediction/yield_model.joblib` and prediction script `predict_yield.py`. | Generate reproducible model evaluation metrics report (`docs/PHASE2_MODEL_EVALUATION.md`) confirming district-level scope and preventing target leakage. |

---

## 2. Identified Integration Risks & Non-Negotiable Compliance Rules

1. **No ML Dosing:** Fertilizer products and quantities are determined exclusively by Linear Programming (`scipy.optimize.linprog`), never by machine learning classifiers or regressors.
2. **Rule Verification Guard:** Only rules with `verification_status="VERIFIED"` are eligible for production recommendations.
3. **Bag Rounding Sufficiency:** Commercial bag rounding must be checked post-optimization. If integer rounding reduces delivered nutrients below target, a discrete solution is selected to ensure 100% nutrient sufficiency.
4. **Data Isolation:** District-level yield prediction is an independent benchmark and does NOT alter NPK calculation or fertilizer LP optimization.

---

## 3. Prioritized Action Plan

1. Update Phase 4 Rule Registry with versioning (`version: "1.0"`) and refine selection logic.
2. Enhance Phase 5 NPK Calculation Engine to ensure pure STCR linear equations are evaluated without generic multiplier interference.
3. Enhance Phase 6 Fertilizer LP Optimizer with post-rounding discrete bag nutrient sufficiency validation and endpoint alias `/api/fertilizer-optimization/optimize`.
4. Update Phase 3 status vocabulary to include `EXTRACTED_PENDING_CONFIRMATION`, `CONFIRMED`, `OCR_FAILED`, `INVALID_INPUT`.
5. Update Phase 7 Master Pipeline and Weather Guidance with resilient fail-open error handling.
6. Create all 7 required Phase Validation Markdown reports under `docs/` and update `SYSTEM_ARCHITECTURE.md`.
7. Execute automated pytest test suite and report 100% pass results.
