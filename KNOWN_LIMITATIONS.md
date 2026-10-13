# Known Limitations and Operational Scope

**Project Title:** AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Date:** 2026-10-13  

---

## 1. Machine Learning Yield Model Scope

- **District Benchmark vs. Individual Field Prediction:**
  The XGBoost regression model is trained on aggregate Season and Crop Reports (2020–2025) published by the Department of Economics and Statistics, Tamil Nadu. It predicts **district-level historical benchmark yields** (in `kg/ha`).
- **No Direct Diagnostic Role:**
  The ML model does **not** evaluate specific field topography, irrigation pump discharge, micro-nutrient deficiencies (Zinc, Boron), or insect-pest pressures.
- **Independence from Fertilizer Dosing:**
  The ML yield benchmark does **not** determine chemical fertilizer dosages. Fertilizer dosages are strictly computed by deterministic TNAU STCR-IPNS equations.

---

## 2. Soil Report OCR and Automated Extraction

- **Scan Quality Dependence:**
  Automated OCR relies on high-contrast digital scans or PDFs of standardized Soil Health Cards issued by the Government of India / Government of Tamil Nadu.
- **Handwritten or Low-Contrast Reports:**
  Skewed, stained, or handwritten test cards may produce partial OCR field extractions or low confidence scores.
- **Mandatory Farmer Verification:**
  The system enforces a mandatory human-in-the-loop verification step (`/api/soil/documents/{id}/validate` and `/confirm`). The farmer must review and confirm extracted values before NPK calculations proceed.

---

## 3. Agronomic Crop Rule Registry Boundaries

- **Supported Crops:**
  Verified STCR-IPNS equations are active for **7 crops**: Rice (Paddy), Cotton, Hybrid Maize, Groundnut, Sugarcane, and Blackgram.
- **Pending / Unsupported Crops:**
  Crops without peer-reviewed calibration equations (e.g. Banana, exotic vegetables) are flagged as `PENDING_VERIFICATION` or `UNSUPPORTED` and cannot be processed for certified recommendations until verified field trial coefficients are added to `tnau_stcr_rules.json`.
- **Soil Method Assumptions:**
  Soil tests must be conducted using standardized methods (Alkaline Permanganate for N, Olsen/Bray for P, Ammonium Acetate for K). Unusual lab protocols will be rejected by validation range checks.

---

## 4. Fertilizer Optimization & Commercial Discretization

- **Continuous Solver with Discrete Ceiling Rounding:**
  Optimization uses the `scipy.optimize.linprog` continuous HiGHS solver followed by integer whole-bag ceiling conversion ($x_{\text{bags}} = \lceil x / \text{bag\_size} \rceil$). While post-rounding validation guarantees that nutrient minimums are satisfied, integer-bag quantization may result in modest nutrient surpluses (within safe agronomic thresholds).
- **Subsidized Price Volatility:**
  Fertilizer prices stored in `catalog.py` represent standard Government of India maximum subsidized retail prices (e.g. Urea at ₹267 per 45 kg bag). Local retail premiums or dealer handling fees are not modeled.

---

## 5. Agro-Meteorological Weather Service

- **Offline Rule-Based Fallback:**
  When external weather APIs are unreachable or when API keys are not supplied in `.env`, the system provides pre-calibrated seasonal agro-met guidance for each of Tamil Nadu's 38 districts.
- **Non-Blocking Architecture:**
  Weather service failures never block the calculation, display, or PDF generation of soil-based fertilizer recommendations.

---

## 6. Multi-User Database Architecture

- **SQLite for Local / Edge Deployment:**
  The default database configuration uses SQLite with Write-Ahead Logging (WAL) and thread-safe connection pooling in `phase3_soil/db.py`.
- **Production Scalability:**
  For multi-tenant cloud deployments exceeding thousands of simultaneous active farmers, migration to PostgreSQL via SQLAlchemy is recommended.
