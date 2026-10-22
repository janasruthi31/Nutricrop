# AgroWise AI — AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers

**Project Reference: SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield**  
**Engineering & Security Audit Release: October 2026**  
**System Status:** Remediated, Hardened, Agronomically Governed & Fully Validated (148 Python Tests + 20 Flutter Tests Passed)  

---

## 1. Overview & System Architecture

AgroWise AI is an end-to-end, scientifically grounded decision-support system designed specifically for Tamil Nadu farmers. The application strictly adheres to official Tamil Nadu Agricultural University (TNAU) Soil Test Crop Response (STCR) and Integrated Plant Nutrition System (IPNS) guidelines, mathematical fertilizer cost optimization, district-level XGBoost crop yield prediction with honest baselines, live agro-weather spray advisories, and an interactive 28-screen Flutter mobile/web interface localized dynamically in **Tamil (தமிழ்)**, **English**, and **Hindi (हिन्दी)**.

```
       +-----------------------------------------------------------------+
       |         Mobile App (Flutter / Dart) - Android, iOS, Web         |
       |  - Dynamic Multilingual Localization (Tamil, English, Hindi)    |
       |  - Soil Health Card Review & Value Confirmation Screen          |
       |  - Offline Recommendation Caching & Secure Session Storage      |
       +-------------------------------+---------------------------------+
                                       | HTTPS / JWT Bearer
                                       v
       +-----------------------------------------------------------------+
       |                   FastAPI Backend Gateway                       |
       |  - Strict JWT HMAC-SHA256 Auth & Object-Level Authorization     |
       |  - Anti-Enumeration Rate-Limited Forgot-Password Flow           |
       |  - Gated Admin Diagnostics (Users/Tokens Never Exposed)         |
       +-------+--------------------+-------------------+----------------+
               |                    |                   |
               v                    v                   v
     +-------------------+ +------------------+ +-----------------------+
     |  Phase 3: Soil    | | Phase 4/5:       | | Phase 6: Optimizer    |
     |  - Tesseract OCR  | | Agronomy Engine  | | - SciPy HiGHS MILP    |
     |  - OpenCV Deskew  | | - TNAU STCR-IPNS | | - Discrete Whole Bags |
     |  - Plausibility   | | - Blanket RDF    | | - Fractional/Loose Kg |
     |  - Mandatory User | | - Manure Credits | | - Multi-Nutrient DAP  |
     |    Confirmation   | | - Unsupported    | | - Packaging Surplus   |
     |                   | |   Crop Refusal   | |   Warnings            |
     +---------+---------+ +--------+---------+ +-----------+-----------+
               |                    |                       |
               +--------------------+-----------------------+
                                    |
                                    v
     +------------------------------------------------------------------+
     |                    Persistence & Reporting                       |
     |  - SQLite (WAL Mode, 30s Busy Timeout, Scoped Connections)        |
     |  - PostgreSQL 16 Production Migration Architecture               |
     |  - Indic ReportLab PDF Generation (Nirmala.ttc / Noto Sans Tamil)|
     |  - Non-blocking Asynchronous Weather Retrieval (HTTPX Client)    |
     +------------------------------------------------------------------+
```

---

## 2. Prerequisites & Environment Configuration

### System Requirements
* **Operating System:** Windows 10/11, Ubuntu 20.04+, or macOS
* **Python:** 3.10 to 3.12 (Validated on Python 3.11.0)
* **Flutter / Dart:** Flutter SDK 3.19+ (Validated on Flutter 3.32.3 / Dart 3.8.1)
* **OCR Dependencies (Optional for live photo scans):** Tesseract OCR 5.x (`tesseract-ocr`) and Poppler (`pdf2image`)
* **Fonts (for Tamil/Hindi PDF generation):** `Nirmala.ttc` (pre-installed on Windows) or `Noto Sans Tamil`

### Environment Variables (`.env`)
Create `.env` in the project root:
```ini
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=sqlite:///./soil_phase3.sqlite3
JWT_SECRET_KEY=production_cryptographically_secure_256bit_key_here
ADMIN_API_KEY=your_secure_admin_diagnostic_key
ENABLE_ADMIN_DIAGNOSTICS=false
AGRI_ALLOW_TEST_BYPASS=false
ALLOWED_ORIGINS=https://agrowise.tn.gov.in
OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast
WEATHER_API_TIMEOUT_SECONDS=8.0
```

---

## 3. Backend Setup & Run Instructions

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start FastAPI Application
uvicorn phase3_soil.main:app --host 0.0.0.0 --port 8000 --reload
```
* **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Alternative Redoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 4. Mobile & Frontend Execution

### A. Run Flutter in Chrome (Web)
```powershell
cd flutter_app
flutter pub get
flutter run -d chrome
```

### B. Run on Physical Android Phone via LAN
For detailed steps on physical phone testing, Windows Firewall rules, and LAN IP binding, refer to [mobile_run_guide.md](mobile_run_guide.md):
```powershell
cd flutter_app
flutter run -d <DEVICE_ID> --dart-define=API_BASE=http://192.168.1.XX:8000
```

---

## 5. Automated Test Suite Execution

Both the backend and mobile test suites execute with a **100% pass rate**:

### A. Python Backend Suite (148 Tests)
```powershell
pytest -v
```
* **Result:** **148 passed, 0 failed, 136 warnings in 90.17s**.
* **Coverage:** OCR, OpenCV deskew, soil classification, HiGHS MILP, continuous fractional LP, brute-force optimality, JWT security, forgot password, cross-user isolation, admin DB lock, Indic PDF export, and TNAU agronomic rules.

### B. Flutter App Test Suite (20 Tests)
```powershell
cd flutter_app
flutter test
```
* **Result:** **20 passed, 0 failed in 4.0s**.
* **Coverage:** Dynamic multilingual switching (Tamil, Hindi, English), login and registration forms, forgot-password modal, session restoration, and smoke tests.

---

## 6. Authoritative Agronomic Rule Coverage

In accordance with **Non-Negotiable Rule 6**, AgroWise AI never fabricates fertilizer rates for crops lacking verified calibrations:

| Crop | Calibration Type | Applicable Conditions | Equation / Rate | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Rice** | STCR-IPNS | Palavidhi, Adanur, Kalathur series (Cauvery Delta) | $FN = 4.39 T - 0.52 SN - 0.84 ON$<br>$FP_2O_5 = 2.22 T - 1.63 SP - 0.98 OP$<br>$FK_2O = 2.44 T - 0.39 SK - 0.81 OK$ | **VERIFIED** (TNAU CPG 2020) |
| **Cotton** | STCR-IPNS | Irugur, Pilamedu series (Western Zone) | $FN = 10.9 T - 0.51 SN - 0.78 ON$<br>$FP_2O_5 = 4.80 T - 2.11 SP - 0.85 OP$<br>$FK_2O = 8.60 T - 0.28 SK - 0.72 OK$ | **VERIFIED** (TNAU Cotton STCR) |
| **Hybrid Maize** | STCR-IPNS | Coimbatore, Pilamedu series | $FN = 3.75 T - 0.54 SN - 0.74 ON$<br>$FP_2O_5 = 1.65 T - 1.58 SP - 0.82 OP$<br>$FK_2O = 2.10 T - 0.24 SK - 0.65 OK$ | **VERIFIED** (TNAU STCR-IPNS) |
| **Rice** | Blanket RDF | Irrigated (other soil series) | 120 - 40 - 40 kg/ha N:P₂O₅:K₂O | **VERIFIED** (TNAU CPG 2020) |
| **Blackgram** | Blanket RDF | Rainfed pulses | 25 - 50 - 25 kg/ha N:P₂O₅:K₂O | **VERIFIED** (TNAU CPG 2020) |
| **Groundnut** | Blanket RDF | Rainfed / Irrigated | 25 - 50 - 75 kg/ha N:P₂O₅:K₂O | **VERIFIED** (TNAU CPG 2020) |
| **Sugarcane** | Blanket RDF | Plant crop | 275 - 62.5 - 112.5 kg/ha N:P₂O₅:K₂O | **VERIFIED** (TNAU CPG 2020) |
| **Banana** | STCR | Thonnackal series | Experimental equation | **PENDING_VERIFICATION** (Blocked) |
| **30+ Other Crops** | None | Ragi, Sorghum, Redgram, Sesame, Tomato, Onion, etc. | Refuses calculation (`UNSUPPORTED_CROP`) | **UNSUPPORTED** (Zero Fabrication) |

---

## 7. Machine-Learning Evaluation & Limitations

An honest, empirical baseline evaluation was conducted across 8,694 historical records (1,739 held-out test rows):

* **Crop Identity Dominance:** Crop identity accounts for **88.8% of all yield variance**.
* **Marginal ML Gain:** A simple naive baseline using only `(Crop, Season)` mean yields achieves $R^2 = 0.9389$. The pooled XGBoost model ($R^2 = 0.9508$) provides only a **marginal improvement of +0.0119 $R^2$**.
* **Negative $R^2$ on Pulses:** XGBoost achieves **negative $R^2 = -0.1432$** on pulses, performing worse than the local historical mean.
* **Fruits Baseline Superiority:** Naive baseline ($R^2 = 0.8137$) outperforms XGBoost ($R^2 = 0.7939$) for fruit crops.
* **Government Imputation:** 59.6% of test records have district yields identical to state-average yields due to DES statistical imputation.
* **Rainfall Influence:** Rainfall features contribute $< 0.3\%$ of model importance due to annual aggregation masking critical dry spells.
* **Causal Caveat:** The yield model predicts historical agro-climatic benchmarks only. It does **not** predict fertilizer yield response or prove that a fertilizer recommendation will increase yield.

---

## 8. Security & Database Concurrency Hardening

1. **Authentication:** Replaced legacy arbitrary string fallbacks with HMAC-SHA256 JWT signature and expiry verification. Caller-controlled `X-Farmer-Id` headers are strictly rejected as proof of identity.
2. **Database Lockdown:** `/db` and `/api/db/status` require `ENABLE_ADMIN_DIAGNOSTICS="true"` and `X-Admin-Key`. The `users` and `password_resets` tables are strictly excluded from all diagnostic queries.
3. **Forgot Password Flow:** Anti-enumeration `POST /api/auth/forgot-password` generates 15-minute single-use OTPs stored as PBKDF2 hashes, rate-limited to 3 requests per 15 minutes.
4. **SQLite Concurrency:** Configured Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and 30-second busy timeout (`PRAGMA busy_timeout = 30000`) with thread-isolated connection context managers.
5. **PostgreSQL Ready:** Detailed schema DDL, indexes, and zero-downtime migration plan documented for high-concurrency production deployments.

---

## 9. Comprehensive Audit Deliverables

All technical audit documents are available in the repository:
* [audit/initial_findings.md](audit/initial_findings.md): Baseline audit, confirmed defects, and reproduction steps.
* [audit/security_fix_report.md](audit/security_fix_report.md): Authentication bypass, database lockdown, and regression test matrix.
* [audit/ml_validation_report.md](audit/ml_validation_report.md): Baseline comparisons, data leakage, and crop-specific evaluation.
* [audit/optimizer_validation_report.md](audit/optimizer_validation_report.md): MILP formulation, smallholder fractional mode, and brute-force optimality.
* [audit/agronomic_rule_coverage.md](audit/agronomic_rule_coverage.md): STCR-IPNS equations, blanket recommendations, and unsupported crop catalog.
* [audit/database_concurrency_report.md](audit/database_concurrency_report.md): WAL mode, connection safety, and PostgreSQL 16 migration plan.
* [audit/ocr_and_pdf_validation.md](audit/ocr_and_pdf_validation.md): Tesseract/Poppler requirements, OpenCV preprocessing, and Indic TrueType PDF generation.
* [audit/test_results.md](audit/test_results.md): Full test execution records and before-and-after tallies.
* [mobile_run_guide.md](mobile_run_guide.md): Physical Android device configuration and LAN setup.
* [final_change_summary.md](final_change_summary.md): Complete engineering change summary and defect resolution audit.
