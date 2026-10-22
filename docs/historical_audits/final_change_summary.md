# Final Change Summary & System Repair Audit: AgroWise AI

**Project:** AgroWise AI — AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Date:** 2026-10-21  
**Git Branch:** `fix/system-security-agronomy-ml-overhaul` (Baseline Commit: `8db703d`)  
**Status:** All 14 Master Prompt Phases Audited, Repaired, Verified, and Documented.  

---

## 1. Confirmed Defects and Root Causes

| Defect ID | Severity | Component | Confirmed Defect | Root Cause |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | **Critical** | `phase7_integration/extra_api.py`, `phase3_soil/api.py` | Authentication bypass via arbitrary token strings or caller-controlled `X-Farmer-Id` headers. | Legacy fallback `user_id = token` when tokens were not JWTs, and unconditional acceptance of `X-Farmer-Id`. |
| **SEC-02** | **Critical** | `phase3_soil/main.py` | Production database schema and row scraping exposed via public `/db` and `/api/db/status`. | Database diagnostics routes lacked authentication, authorization, or table allowlisting. |
| **SEC-03** | **High** | `flutter_app/lib/screens/login_screen.dart` | Mocked forgot-password dialog falsely claiming recovery instructions were sent. | UI displayed static message; no backend recovery endpoints or token models existed. |
| **SEC-04** | **Medium** | `phase3_soil/main.py` | CORS wildcard misconfiguration (`allow_origins=["*"]` with `allow_credentials=True`). | Incompatible CORS specification rejected by standard browsers. |
| **ML-01** | **High** | `train_yield_model.py`, `supplementary_metrics.json` | Overstated XGBoost performance ($R^2 = 0.9508$) failing to disclose that a naive `(Crop, Season)` mean yields $R^2 = 0.9389$ (+0.0119 marginal gain). | Crop identity explains 88.8% of variance; Pulses exhibited negative $R^2 = -0.1432$; 59.6% of test records were government state-average imputations. |
| **OPT-01** | **High** | `phase6_fertilizer/service.py` | Documented 1.5× surplus cap was absent in code (`ub=np.inf`), and whole-bag MILP forced excessive over-purchases on smallholder plots (< 0.5 ha). | Optimization lacked continuous LP mode for fractional bags/loose kilograms and lacked surplus packaging alerts. |
| **AGR-01** | **High** | `agronomy/`, `tnau_stcr_rules.json` | Risk of fabrications for non-calibrated crops and unverified rules. | Registry lacked strict classification separating verified STCR-IPNS from blanket RDF and blocking unsupported crops. |
| **CONC-01**| **Medium** | `phase3_soil/db.py` | SQLite concurrency lock contention under parallel multi-user writes. | Default rollback journal mode locked whole database during writes, with short default timeout. |
| **NET-01** | **Medium** | `weather.py`, `location.py` | Blocking `urllib.request.urlopen` calls inside FastAPI async handlers. | Synchronous network I/O blocked the Python asyncio event loop during weather queries. |
| **MOB-01** | **Medium** | `api_client.dart`, `splash_screen.dart` | Mobile session loss on app restart and lack of offline recommendation access. | Auth tokens and saved recommendations were held in volatile memory without persistent storage. |
| **PDF-01** | **Medium** | `phase7_integration/extra_api.py` | PDF export crashed with `UnicodeEncodeError` when rendering Tamil or Hindi text. | ReportLab default font styles (`Helvetica`) only support Latin-1 characters. |

---

## 2. Files Changed and Why

1. **`phase7_integration/extra_api.py`**:
   - Replaced unverified string fallback with strict HMAC-SHA256 JWT validation, signature verification, and expiration enforcement.
   - Removed arbitrary caller `X-Farmer-Id` acceptance; isolated test bypass to `AGRI_ALLOW_TEST_BYPASS="true"`.
   - Replaced mock farmer fallbacks with HTTP 404 responses.
   - Added `POST /api/auth/forgot-password` (anti-enumeration, rate-limited, 15m PBKDF2 hashed OTP) and `POST /api/auth/reset-password`.
   - Integrated Indic TrueType fonts for multilingual Tamil/Hindi/English PDF generation.
2. **`phase3_soil/api.py`**:
   - Updated `_guard` to verify JWT Bearer tokens and claims rather than passing unverified strings.
3. **`phase3_soil/main.py`**:
   - Gated `/db` and `/api/db/status` behind `ENABLE_ADMIN_DIAGNOSTICS="true"` and `X-Admin-Key` verification.
   - Enforced strict table allowlist (`ALLOWED_DIAGNOSTIC_TABLES`), completely blocking `users` and `password_resets`.
   - Fixed CORS configuration (`allow_credentials=False` for wildcard origins).
4. **`phase3_soil/db.py`**:
   - Enabled `PRAGMA journal_mode = WAL` and `PRAGMA busy_timeout = 30000` to prevent database lock contention.
   - Created `password_resets` table with indexes for time-limited OTPs.
5. **`phase6_fertilizer/models.py` & `service.py`**:
   - Added `allow_fractional_bags` and `max_surplus_factor` to `FertilizerOptimizationRequest`.
   - Enabled continuous LP fractional bag solving for smallholders.
   - Added automated agronomic surplus warnings when whole-bag packaging results in $> 1.5\times$ target nutrient application.
6. **`phase7_integration/weather.py` & `location.py`**:
   - Replaced blocking `urllib.request.urlopen` with non-blocking `httpx.Client(timeout=8.0)`.
7. **`flutter_app/pubspec.yaml` & `pubspec.lock`**:
   - Added `shared_preferences: ^2.2.3` for secure local session persistence.
8. **`flutter_app/lib/services/api_client.dart`**:
   - Added persistent session initialization (`init()`), token storage, clear on logout, offline recommendation caching, and real forgot/reset password API methods.
9. **`flutter_app/lib/screens/login_screen.dart` & `splash_screen.dart`**:
   - Hooked up real forgot password API submission and splash screen session restoration.
10. **`phase7_integration/pdf_fonts.py` (New)**:
    - Registered Windows `Nirmala.ttc` and `Noto Sans Tamil` TrueType fonts with ReportLab.
11. **`conftest.py` (New)**:
    - Isolated test bypass configuration strictly to pytest harness execution.
12. **`mobile_run_guide.md` (New)**:
    - Comprehensive guide for running on physical Android devices over LAN.
13. **`audit/` Documentation Suite (9 files)**:
    - Detailed reports for all 14 phases.

---

## 3. Actual Test Commands and Results

### 3.1 Python Backend Test Suite (`pytest -v`)
* **Command:** `pytest -v`
* **Test Count:** 148 items collected
* **Result:** **148 passed, 0 failed, 136 warnings in 90.17s (100% pass rate)**.
* **Coverage:** OCR preprocessing, extraction regex, soil classifications, MILP optimization, fractional bags, brute-force optimality, JWT security, forgot password, cross-user isolation, admin DB lock, Indic PDF export, and TNAU agronomic rules.

### 3.2 Flutter Application Test Suite (`flutter test`)
* **Command:** `flutter test`
* **Test Count:** 20 tests collected
* **Result:** **20 passed, 0 failed in 4.0s (100% pass rate)**.
* **Coverage:** Dynamic language switching (Tamil, Hindi, English), login and registration forms, forgot-password modal, session restoration, and smoke tests.

---

## 4. Machine-Learning Evaluation Protocol & Baselines

Empirical evaluation executed across all 8,694 historical records (1,739 held-out test rows) using identical records:

| Model / Baseline | Overall $R^2$ | MAE (kg/ha) | RMSE (kg/ha) | Practical Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Overall Mean Baseline** | 0.0000 | 1,480.2 | 2,410.5 | Uninformative baseline. |
| **District Mean Baseline** | 0.0912 | 1,390.1 | 2,298.4 | District alone explains <10% of yield variance. |
| **Crop Mean Baseline** | 0.8878 | 462.1 | 808.2 | **Crop identity explains 88.8% of all variance.** |
| **Crop + Season Mean Baseline** | **0.9389** | **341.2** | **596.1** | **Standard statistical benchmark.** |
| **Existing XGBoost Model** | **0.9508** | **318.5** | **534.8** | **Marginal improvement of only +0.0119 $R^2$.** |

### Critical Crop-Specific Findings:
* **Pulses Group:** XGBoost achieves **negative $R^2 = -0.1432$** (predicts worse than local crop mean).
* **Fruits Group:** Naive `(Crop, Season)` baseline ($R^2 = 0.8137$) outperforms XGBoost ($R^2 = 0.7939$).
* **Data Imputation:** 59.6% of test records possess district yields identical to state averages due to government statistical imputation, artificially compressing model variance.
* **Rainfall Impact:** Rainfall contributes $< 0.3\%$ of feature importance due to annual aggregation masking critical dry spells.

---

## 5. Agronomic Rule Coverage & Unsupported Crops

### 5.1 Supported & Verified Rules
* **Rice STCR-IPNS (`TNAU_STCR_IPNS_RICE_001`):** Palavidhi, Adanur, Kalathur series (Cauvery Delta). Formally calibrated equations accounting for available soil NPK and FYM manure credits.
* **Cotton STCR-IPNS (`TNAU_STCR_IPNS_COTTON_001`):** Irugur and Pilamedu series.
* **Hybrid Maize STCR-IPNS (`TNAU_STCR_IPNS_MAIZE_001`):** Coimbatore and Pilamedu series.
* **Blanket RDF Recommendations (CPG 2020):** Standard published rates for Rice (120:40:40), Blackgram (25:50:25), Groundnut (25:50:75), and Sugarcane (275:62.5:112.5).

### 5.2 Provisional Rules Gated Behind Validation
* **Banana (`TNAU_STCR_BANANA_001`):** Thonnackal series equation marked `PENDING_VERIFICATION`. Blocked from production output unless explicit provisional consent is requested.
* **Groundnut STCR (`TNAU_STD_GROUNDNUT_001`):** Marked `PENDING_AGRONOMIC_VALIDATION`.

### 5.3 Unsupported Crops (Refusal to Fabricate Doses)
Over 30 crops (ragi, sorghum, redgram, sesame, tapioca, turmeric, tomato, brinjal, onion, mango, coconut, coffee, tea) are classified as `UNSUPPORTED_CROP`. The system halts with an honest limitation advisory and refuses to fabricate unverified fertilizer doses.

---

## 6. Fertilizer Optimizer Validation

* **Multi-Nutrient Modeling:** Matrix $\mathbf{A}$ correctly models dual nutrients in complex fertilizers (e.g. DAP: 18% N, 46% P₂O₅) without double-counting.
* **Smallholder Support:** Implemented `allow_fractional_bags=True` using continuous LP, allowing farmers with small plots (< 0.5 ha) to receive exact loose-kilogram guidance instead of forced 50kg bag purchases.
* **Surplus Packaging Diagnostics:** Whole-bag purchases that cause $>1.5\times$ oversupply trigger clear warnings explaining packaging constraints and providing exact loose requirements.
* **Optimality Benchmark:** Verified against exhaustive brute-force search across 125 candidate permutations, achieving 100% exact cost optimality.

---

## 7. Security Regression Test Results

* Anonymous access to `/api/recommendations` -> **HTTP 401 Unauthorized (PASSED)**
* Request with caller `X-Farmer-Id` only -> **HTTP 401 Unauthorized (PASSED)**
* Request with arbitrary non-JWT string -> **HTTP 401 Unauthorized (PASSED)**
* Cross-user data retrieval attempt (Farmer B accessing Farmer A's report) -> **HTTP 403 Forbidden (PASSED)**
* Tampered token signature -> **HTTP 401 Unauthorized (PASSED)**
* Expired token -> **HTTP 401 Unauthorized (PASSED)**
* Anti-enumeration forgot-password request -> **HTTP 200 generic message (PASSED)**
* Reset password with wrong OTP -> **HTTP 400 Bad Request (PASSED)**
* Reset password with valid OTP -> **HTTP 200, old password rejected with 401 (PASSED)**
* Anonymous access to `/db` and `/api/db/status` -> **HTTP 403 Forbidden (PASSED)**
* Admin diagnostic query targeting `users` table -> **HTTP 403 Forbidden (PASSED)**

---

## 8. Physical Device & Offline Verification

* **Physical Device Connectivity:** Created `mobile_run_guide.md` specifying `--dart-define=API_BASE=http://<LAN_IP>:8000`, Windows Firewall port 8000 rules, and Android cleartext traffic configurations.
* **Offline Persistence:** `ApiClient` caches successful recommendations in local storage (`shared_preferences`). When offline, cached recommendations remain viewable with explicit `saved_offline_at` timestamps.

---

## 9. External Credentials and Hardware Requirements

1. **SMS / Email Gateway:** The password reset flow generates cryptographically secure OTPs in SQLite; integration with a production SMS gateway (e.g. CDAC SMS Seva / Twilio) requires production API keys injected into `_send_reset_notification()`.
2. **Production JWT Secret:** Set `JWT_SECRET_KEY` in production environment variables (`openssl rand -hex 32`).
3. **Official Field Calibration:** Calibration of STCR equations for Banana and additional soil series requires joint field trial datasets from TNAU.

---

## 10. Residual Defect Classification

| Rank | Defect Description | Classification | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| 1 | Low ML predictive power on Pulses ($R^2 = -0.1432$) | **Medium** | System transparently presents local historical mean for pulses rather than misleading model output. |
| 2 | High proportion of government imputed yield records (59.6%) | **Low** | Documented in ML validation report; model interpretation caveats highlighted. |
| 3 | Tesseract OCR requires host system binary installation | **Low** | Server auto-detects binary paths and returns clean HTTP 503 rather than crashing when uninstalled. |
