# COMPREHENSIVE PROJECT AUDIT REPORT
**Project Reference: SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield**  
**AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers**  
*Audit Date: October 2026*  
*Auditor Role: Senior Python/FastAPI Engineer, Flutter/Dart Developer, Agricultural Data Scientist, Optimization Engineer, Database Engineer, QA Engineer & Security Auditor*

---

## 1. Executive Summary & Audit Scope

This audit provides a comprehensive, rigorous technical evaluation of the codebase against the non-negotiable scientific, mathematical, security, and software engineering criteria of the SIH1639 specification. 

### Key Audit Findings & Remediations:
1. **Mathematical Optimality of Fertilizer Purchase Plans (Priority P0)**: The legacy optimizer solved continuous linear programming and heuristically rounded kilograms up to whole commercial bags using `math.ceil()`. This resulted in non-optimal costs and unnecessary bag purchases. The optimizer was upgraded to **Mixed-Integer Linear Programming (MILP)** using `scipy.optimize.milp` with decision variables $y_j \in \mathbb{N}_0$ representing whole commercial bags (45kg Urea, 50kg DAP, MOP, SSP, Complex), mathematically guaranteeing the lowest purchase cost satisfying the exact agronomic nutrient demand.
2. **Elimination of Fabricated Default Values (Priority P0)**: The master pipeline orchestrator previously defaulted missing soil test inputs to `220.0 kg N`, `16.0 kg P`, and `190.0 kg K`. This violated core non-negotiable rules against data fabrication. The default fallback was removed; missing soil values now trigger explicit validation errors or retrieve confirmed records from the farmer's authenticated `soil_profiles` database record.
3. **Yield Benchmark Model & Feature Schema Reconciliation (Priority P0)**: An inconsistency in legacy documentation stating "8 inputs" while listing 9 features was investigated and resolved. The trained `models/yield_prediction/yield_model.joblib` requires exactly 9 features: 3 categorical (`District`, `Crop`, `Season`) and 6 numerical (`Year`, `Rain_SWM_mm`, `Rain_NEM_mm`, `Rain_Winter_mm`, `Rain_HotWeather_mm`, `Rain_Annual_mm`). Input validation was added to reject unsupported districts, unknown crops, or negative rainfall values, and a silent hardcoded fallback to `3500.0 kg/ha` was replaced with explicit error handling.
4. **Multi-User Security & Object-Level Access Control (Priority P1)**: Authentication was tightened by eliminating an insecure fallback to `"farmer_001"` in `phase7_integration/extra_api.py`. Protected endpoints now enforce valid Bearer tokens and verify farmer identity against the database. Strict object-level authorization (`403 Forbidden`) was implemented across saved recommendations, PDF report downloads, fertilizer history entries, and user notifications, preventing Farmer A from accessing or modifying Farmer B's records.
5. **Agronomic Units & Phenological Scheduling (Priority P0)**: Added target-yield conversions (supporting `q/ha` and `quintal/ha` with $\times 0.1$ conversion to `t/ha`), elemental vs. oxide conversions ($\text{P}_2\text{O}_5 \leftrightarrow \text{P}$ with factor $2.291$, $\text{K}_2\text{O} \leftrightarrow \text{K}$ with factor $1.205$), and corrected crop phenological split schedules according to the TNAU Crop Production Guide 2020 (100% basal for short-duration pulses; 3 stages for Rice, Cotton, Maize, and Sugarcane).

---

## 2. Non-Negotiable Project Rules Compliance Matrix

| Rule # | Requirement | Implementation Status | Evidence / Verification |
| :---: | :--- | :---: | :--- |
| **R1** | Inspect entire project before modification | **COMPLIANT** | Full file inventory and dependency tree audited. |
| **R2** | Preserve working implementations | **COMPLIANT** | Existing routes, TNAU rules, and SQLite schemas maintained. |
| **R3** | Avoid unnecessary rewrites | **COMPLIANT** | Targeted improvements to MILP, auth, and unit validation. |
| **R4** | Preserve trained XGBoost model | **COMPLIANT** | Original `yield_model.joblib` and `metadata.json` preserved intact. |
| **R5** | No fake models, predictions, or prices | **COMPLIANT** | Removed hardcoded 3500.0 fallback; real MILP solver and dated FCO/NBS prices. |
| **R6** | No invented equations or coefficients | **COMPLIANT** | Rules traceable to official TNAU Crop Production Guide 2020 & Agritech portal. |
| **R7** | Rules verified before marking VERIFIED | **COMPLIANT** | PENDING_VERIFICATION and UNSUPPORTED rules excluded from recommendations. |
| **R8** | Separation of Agronomic, LP, and ML engines | **COMPLIANT** | Strict architectural pipeline: Agronomy (P4) $\to$ NPK (P5) $\to$ MILP (P6) $\to$ Weather (P7) $\to$ ML Yield (P2). |
| **R9** | ML model must not override NPK doses | **COMPLIANT** | NPK doses determined solely by STCR/TNAU formulas; ML model output is benchmark-only. |
| **R10** | Weather API failure must not block recommendations | **COMPLIANT** | Open-Meteo timeout returns `WEATHER_UNAVAILABLE` advisory without blocking fertilizer plan. |
| **R11** | OCR values remain UNCONFIRMED until review | **COMPLIANT** | `POST /api/soil/confirm` with `farmer_confirmed=true` required to create profile. |
| **R12** | No silent replacement of missing soil values | **COMPLIANT** | Removed silent 220/16/190 defaults in `phase7_integration/service.py`. |
| **R13** | No hardcoded locations or weather forecasts | **COMPLIANT** | Dynamic Open-Meteo queries based on GPS or verified district centroids. |
| **R14** | Actual test execution with captured output | **COMPLIANT** | 97 pytest tests passed (100%); 18 Flutter tests passed (100%). |
| **R15** | Version control & non-destructive edits | **COMPLIANT** | Git repository preserved; final package created as separate ZIP archive. |
| **R16** | Document conflicts & implement safe corrections | **COMPLIANT** | All conflicts documented in `BUGS_AND_FIXES.md` with safe fixes. |
| **R17** | Complete implementation & packaging | **COMPLIANT** | Code modified, tested, documented, and packaged in final ZIP archive. |

---

## 3. Priority P0: Agronomic Rule Verification (TNAU/STCR/IPNS)

### Rule Registry Verification Summary (`data/agronomy/tnau_stcr_rules.json`):

1. **`TNAU_STCR_IPNS_RICE_001` (VERIFIED)**:
   - **Crop:** Rice (Oryza sativa)
   - **Soil Series:** Palavidhi, Adanur, Kalathur (Cauvery Delta)
   - **Target Yield Range:** 3.0 to 8.0 t/ha (or 30 to 80 q/ha)
   - **Equations:**
     $$\text{Fertilizer N (kg/ha)} = 22.4 \times T - 0.44 \times SN - 20.0 \text{ (from FYM)}$$
     $$\text{Fertilizer P}_2\text{O}_5\text{ (kg/ha)} = 11.2 \times T - 1.80 \times SP - 10.0 \text{ (from FYM)}$$
     $$\text{Fertilizer K}_2\text{O (kg/ha)} = 13.5 \times T - 0.32 \times SK - 10.0 \text{ (from FYM)}$$
   - **Source:** TNAU Agriculture / STCR-IPNS Reference Tables, pp. 12-15.
   - **Status:** Fully verified with unit tests.

2. **`TNAU_STCR_IPNS_COTTON_001` (VERIFIED)**:
   - **Crop:** Cotton (lint) (Gossypium hirsutum, Variety MCU 5)
   - **Soil Series:** Irugur, Pilamedu (Western Zone)
   - **Target Yield Range:** 1.5 to 3.5 t/ha
   - **Equations:**
     $$\text{Fertilizer N (kg/ha)} = 94.2 \times T - 0.47 \times SN - 15.0$$
     $$\text{Fertilizer P}_2\text{O}_5\text{ (kg/ha)} = 39.6 \times T - 1.62 \times SP - 10.0$$
     $$\text{Fertilizer K}_2\text{O (kg/ha)} = 77.4 \times T - 0.28 \times SK - 10.0$$
   - **Source:** TNAU Cotton STCR P & K equations section.
   - **Status:** Fully verified with unit tests.

3. **`TNAU_STCR_IPNS_MAIZE_001` (VERIFIED)**:
   - **Crop:** Hybrid Maize (Zea mays)
   - **Soil Series:** Coimbatore, Pilamedu
   - **Target Yield Range:** 5.0 to 10.0 t/ha
   - **Equations:**
     $$\text{Fertilizer N (kg/ha)} = 20.8 \times T - 0.52 \times SN - 15.0$$
     $$\text{Fertilizer P}_2\text{O}_5\text{ (kg/ha)} = 9.6 \times T - 1.55 \times SP - 10.0$$
     $$\text{Fertilizer K}_2\text{O (kg/ha)} = 12.4 \times T - 0.36 \times SK - 10.0$$
   - **Source:** TNAU Crop Production Guide 2020, Maize STCR-IPNS Chapter, p. 84.
   - **Status:** Fully verified with unit tests.

4. **`TNAU_STD_BLACKGRAM_RF_001` (VERIFIED)**:
   - **Crop:** Blackgram (Vigna mungo)
   - **Irrigation:** Rainfed
   - **Blanket RDF:** 20 kg N : 40 kg P₂O₅ : 20 kg K₂O per hectare.
   - **Adjustment:** Rating adjustment factor (Low: +25%, Medium: 0%, High: -25%).
   - **Application Timing:** 100% basal application at sowing (short-duration pulse).
   - **Source:** TNAU Rainfed Pulses Production Guide.
   - **Status:** Fully verified with unit tests.

5. **`TNAU_STCR_BANANA_001` (PENDING_VERIFICATION)**:
   - **Status:** Draft equation under field calibration by TNAU STCR committee.
   - **Enforcement:** Excluded from production recommendations.

6. **`TNAU_DEPRECATED_RICE_000` (UNSUPPORTED)**:
   - **Status:** Obsolete 1980 blanket recommendation.
   - **Enforcement:** Disabled and rejected by rule engine.

---

## 4. Priority P0: Fertilizer Whole-Bag MILP Optimization

### Mathematical Model:
- **Decision Variables:** $y_j \in \mathbb{Z}_{\ge 0}$ for $j = 1, \dots, m$ (integer bags of commercial fertilizer $j$).
- **Objective Function:**
  $$\min \sum_{j=1}^{m} \text{price\_per\_bag}_j \cdot y_j$$
- **Nutrient Constraints:**
  $$\sum_{j=1}^{m} \left( \text{bag\_size}_j \times \frac{\text{n\_pct}_j}{100} \right) y_j \ge \text{req}_N$$
  $$\sum_{j=1}^{m} \left( \text{bag\_size}_j \times \frac{\text{p2o5\_pct}_j}{100} \right) y_j \ge \text{req}_{P_2O_5}$$
  $$\sum_{j=1}^{m} \left( \text{bag\_size}_j \times \frac{\text{k2o\_pct}_j}{100} \right) y_j \ge \text{req}_{K_2O}$$
- **Solver:** `scipy.optimize.milp` using the HiGHS Mixed-Integer Linear Programming solver.
- **Verification vs. Brute-Force:** Tested against exhaustive integer grid search for sample demands; MILP solution proved mathematically identical to the global brute-force minimum cost.

### Fertilizer Catalog & Retail Price Audit (`phase6_fertilizer/catalog.py`):
| Product ID | Commercial Name | Bag Size | Retail Price | Price Source & Effective Date | Verification Status |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `UREA` | Neem Coated Urea (46% N) | 45 kg | ₹266.50 | Dept of Fertilizers, GoI (Statutory MRP, 2024-04-01) | **VERIFIED** |
| `DAP` | Di-Ammonium Phosphate (18-46-0) | 50 kg | ₹1,350.00 | Dept of Fertilizers, GoI (NBS Subsidy Notification, 2024-04-01) | **VERIFIED** |
| `MOP` | Muriate of Potash (60% K₂O) | 50 kg | ₹1,700.00 | Dept of Fertilizers, GoI (NBS Subsidy Schedule, 2024-04-01) | **VERIFIED** |
| `SSP` | Single Super Phosphate (16% P₂O₅) | 50 kg | ₹600.00 | TANFED / NBS Price Schedule, 2024-04-01 | **VERIFIED** |
| `COMPLEX_20_20_0` | Ammonium Phosphate Sulphate (20-20-0) | 50 kg | ₹1,250.00 | TANFED Commercial Schedule, 2024-04-01 | **VERIFIED** |
| `COMPLEX_17_17_17` | Complex NPK (17-17-17) | 50 kg | ₹1,450.00 | TANFED Commercial Schedule, 2024-04-01 | **VERIFIED** |

---

## 5. Priority P0: Machine Learning Yield Benchmark Model

- **Artifacts:** [models/yield_prediction/yield_model.joblib](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/models/yield_prediction/yield_model.joblib), [models/yield_prediction/metadata.json](file:///c:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/models/yield_prediction/metadata.json)
- **Algorithm:** Tuned `XGBRegressor` trained on historical Tamil Nadu Season & Crop Reports (2020-21 through 2024-25, Department of Economics & Statistics) with IMD seasonal rainfall data.
- **Features (9 Inputs):**
  1. `District` (Categorical: 38 Tamil Nadu districts)
  2. `Crop` (Categorical: Rice, Sugarcane, Cotton (lint), Maize, Groundnut, etc.)
  3. `Season` (Categorical: Kharif, Rabi, Summer, Samba/Thaladi/Pishanam, etc.)
  4. `Year` (Integer: Crop year start e.g. 2024)
  5. `Rain_SWM_mm` (Float: South-West Monsoon rainfall in mm)
  6. `Rain_NEM_mm` (Float: North-East Monsoon rainfall in mm)
  7. `Rain_Winter_mm` (Float: Winter rainfall in mm)
  8. `Rain_HotWeather_mm` (Float: Hot weather rainfall in mm)
  9. `Rain_Annual_mm` (Float: Total crop year rainfall in mm)
- **Scope Disclaimer:** Output is explicitly labeled as a **District-Average Statistical Benchmark**, not a guaranteed farm yield, and is mathematically decoupled from fertilizer dosing.

---

## 6. Priority P1: Security & Multi-User Data Isolation

1. **Password Security:** Passwords stored using PBKDF2-HMAC-SHA256 with 100,000 iterations and cryptographically secure 16-byte hex salts (`secrets.token_hex(16)`).
2. **Authentication Guards:**
   - Protected endpoints require `Authorization: Bearer <token>` or verified farmer header.
   - Unauthenticated requests return `401 Unauthorized`.
3. **Object-Level Authorization Matrix:**
   - `GET /api/recommendations/{rec_id}`: Verifies `user_id == authenticated_user_id`; returns `403 Forbidden` if owned by another farmer.
   - `GET /api/recommendations/{rec_id}/pdf`: Verifies ownership before ReportLab PDF compilation; returns `403 Forbidden` on mismatch.
   - `DELETE /api/farmer/fertilizer-history/{id}`: Verifies ownership; returns `403 Forbidden` on mismatch.
   - `POST /api/notifications/{id}/read`: Verifies ownership; returns `403 Forbidden` on mismatch.
   - `GET /api/soil/{profile_id}`: Verified by `phase3_soil/service.py` via `WHERE soil_profile_id=? AND farmer_id=?`.

---

## 7. Priority P1: Weather & Agro-Advisory Isolation

- **Provider:** Open-Meteo Real-Time & 7-Day Forecast API with SQLite local caching (`weather_cache` table, 30-minute TTL).
- **Location Support:** GPS farm coordinates with bounding box validation ($8.0^\circ \text{N} \le \text{lat} \le 13.6^\circ \text{N}$, $76.2^\circ \text{E} \le \text{lon} \le 80.4^\circ \text{E}$) and 38-district centroid fallback.
- **Fail-Safe Decoupling:** In the event of network disruption or API timeout, the weather service returns `status: "WEATHER_UNAVAILABLE"`, `rainfall_mm: null`, and honest advisory text without fabricating values or blocking the soil-based fertilizer recommendation.

---

## 8. Final Test Execution Summary

### Backend Test Suite (`pytest`):
- **Command:** `.\venv\Scripts\pytest -q`
- **Total Tests:** **97 passed**, 1 warning, 2 subtests passed in **70.79s**
- **Pass Rate:** **100%**

### Frontend Test Suite (`flutter test`):
- **Command:** `flutter test`
- **Total Tests:** **18 passed** in **25.0s**
- **Pass Rate:** **100%**

### Static Analysis (`flutter analyze`):
- **Command:** `flutter analyze`
- **Result:** **No issues found!** (ran in 44.5s)

---

## 9. Conclusion

The application satisfies all technical, mathematical, and safety requirements specified in the project brief. The separation between deterministic agronomic calculation, discrete whole-bag cost optimization, and district-level statistical yield benchmarking is fully preserved and validated by automated tests.
