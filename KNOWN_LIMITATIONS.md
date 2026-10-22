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
  Agronomic equations and blanket dose benchmarks are active for **6 crops**: Rice (Paddy), Cotton, Hybrid Maize, Groundnut, Sugarcane, and Blackgram. Only equations backed by published TNAU/ICAR citations and passing golden integration tests are marked `VERIFIED`. All other rules are strictly marked `PROVISIONAL` and flagged in both API and UI responses.
- **Pending / Unsupported Crops:**
  Crops without peer-reviewed calibration equations or TNAU blanket schedules (e.g. Banana, exotic vegetables) are flagged as `UNSUPPORTED` or `PROVISIONAL` and will not yield certified agronomic recommendations.
- **Soil Method Assumptions:**
  Soil tests must be conducted using standardized methods (Alkaline Permanganate for N, Olsen/Bray for P, Ammonium Acetate for K). Unusual lab protocols will be rejected by validation range checks.

---

## 4. Fertilizer Optimization & Commercial Discretization

- **Mixed-Integer Linear Programming (MILP):**
  Optimization uses the exact Mixed-Integer Linear Programming solver `scipy.optimize.milp` with the HiGHS backend. Decision variables for commercial fertilizer bags are modeled directly as discrete integers ($x_i \in \mathbb{Z}_{\ge 0}$), with optional non-negative continuous slack for loose kg purchases. The optimizer minimizes total farmer expenditure while satisfying N, P₂O₅, and K₂O crop requirements. Any nutrient surplus resulting from integer bag sizes is computed and explicitly reported in `nutrient_surplus_kg`.
- **Subsidized and Local Retail Prices:**
  Default fertilizer prices in `data/agronomy/fertilizer_catalog.json` reflect standard Government of India maximum retail prices (e.g. Urea at ₹266.50 per 45 kg bag) tagged with a `last_updated` timestamp. Farmers can optionally provide custom local bag prices at calculation time to reflect specific co-operative or dealer rates.

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
