# Application Page and Integration Audit (Gap Analysis)
**Project Reference: SIH1639 — AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers**
*Audit Date: October 2026*

---

## 1. Executive Summary

This audit assesses the current state of the application across the frontend (Flutter), backend (FastAPI), database (SQLite), agronomic engine, machine learning model, and testing suite. The analysis identifies what exists, what is missing or incomplete, and defines a phased implementation plan to deliver the complete 27-screen mobile application localized in Tamil, English, and Hindi.

---

## 2. Screen-by-Screen Gap Analysis

| # | Screen Name | Current Status | Existing Code | Missing / Needed Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Splash Screen** | ❌ Missing | None | App logo, agricultural branding, auth token verification, auto-route to Language/Login/Dashboard. |
| **2** | **Language Selection** | ❌ Missing | None | Language selector (Tamil, English, Hindi), persistence in preferences/user profile. |
| **3** | **Login Page** | ❌ Missing | None | Farmer ID / Email & password form, secure token storage, backend auth endpoint integration. |
| **4** | **Registration Page** | ❌ Missing | None | Farmer registration (name, email/phone, district, password, preferred language), duplicate validation. |
| **5** | **Farmer Dashboard** | ❌ Missing | None | Farmer greeting, profile icon, language toggle, feature cards (Soil, Fertilizer, Yield, Weather, History, Reports), quick action buttons. |
| **6** | **Soil Report Upload** | 🟡 Partial | `lib/screens/upload_screen.dart` | Exists for PDF/Image/Camera; needs localization (ta/en/hi), auth header injection, and responsive UI polish. |
| **7** | **Soil Report Extraction** | 🟡 Partial | `lib/screens/processing_screen.dart` | Exists for OCR polling; needs localization, failure handling, and retry UI. |
| **8** | **Soil Report Verification** | 🟡 Partial | `lib/screens/verify_screen.dart` | Exists for value review/edit; needs localization, missing input alerts, and handoff to Farm Details. |
| **9** | **Farm Details** | ❌ Missing | None | District, village, farm area (acres/ha with tested conversions), irrigation method, soil type. |
| **10** | **Crop Selection** | ❌ Missing | None | Supported TNAU crop picker, variety, season, target yield input, validation against rule registry. |
| **11** | **Previous Fertilizer Details**| ❌ Missing | None | Historical fertilizer usage tracking (product, qty, application date), user vs verified data badge. |
| **12** | **NPK Requirement** | ❌ Missing | None | Visual breakdown of N, P2O5, K2O (kg/ha & total farm), TNAU/STCR rule attribution, method explanation. |
| **13** | **Fertilizer Optimization** | ❌ Missing | None | Commercial catalog products, nutrient composition, live prices, LP solver status, bag counts. |
| **14** | **Final Recommendation** | ❌ Missing | None | Farmer-friendly recommendation cards, bag counts (45kg/50kg), total estimated cost (INR), actions. |
| **15** | **Application Schedule** | ❌ Missing | None | Basal, tillering, panicle initiation split stages, product timing & safety advice. |
| **16** | **Crop Yield Prediction Input**| ❌ Missing | None | Form for district-level XGBoost model (District, Crop, Season, Year, Monsoon & seasonal rainfall mm). |
| **17** | **Crop Yield Prediction Results**| ❌ Missing| None | District-average benchmark display (kg/ha), honest scope disclaimer (statistical estimate, not farm guarantee). |
| **18** | **Weather Information** | ❌ Missing | None | Agro-weather advisory from `/api/weather/guidance`, rainfall status, spray/fertilizer timing guidance. |
| **19** | **Sustainability Insights** | ❌ Missing | None | Balanced nutrient check (surplus/deficit analysis), IPNS organic manure contribution, cost savings. |
| **20** | **Recommendation History** | ❌ Missing | None | User's past saved recommendations list, search/filter by crop/date. |
| **21** | **Recommendation Details** | ❌ Missing | None | Full audit record view of saved recommendations (soil inputs, rule ID, bag count, prices). |
| **22** | **Report Generation** | ❌ Missing | None | Real PDF generation via backend ReportLab, preview and download capability. |
| **23** | **Farmer Profile** | ❌ Missing | None | Farmer account details, contact info, preferred language, default farm district. |
| **24** | **Notifications** | ❌ Missing | None | Event-driven notifications (recommendation ready, report generated, weather advisory). |
| **25** | **Help and Guidance** | ❌ Missing | None | Farmer guides: How to read Soil Card, STCR method explained, LP cost optimizer FAQs. |
| **26** | **Settings** | ❌ Missing | None | Language switch, dark/light theme, API endpoint configuration, logout, app version. |
| **27** | **About the Application** | ❌ Missing | None | SIH1639 info, TNAU/STCR references, model architecture summary, disclaimers. |

---

## 3. Backend & API Endpoint Gap Analysis

### Existing Working Endpoints
- `GET /health`: Health status.
- `POST /api/soil/upload`: Upload soil test PDF/image.
- `POST /api/soil/ocr`: Run Tesseract OCR and extract structured soil fields.
- `POST /api/soil/validate`: Plausibility and range checks.
- `POST /api/soil/confirm`: Confirms verified soil profile.
- `GET /api/soil/{soil_profile_id}`: Retrieves confirmed soil profile.
- `POST /api/agronomy/select-rule`: Selects verified TNAU/STCR/IPNS agronomic rule.
- `POST /api/nutrient-requirement/calculate`: Calculates N, P2O5, K2O requirements.
- `POST /api/fertilizer/optimize`: Linear programming fertilizer cost minimization.
- `GET /api/weather/guidance`: District agro-weather advisories and fertilizer timing.
- `POST /api/full-recommendation`: Master end-to-end orchestration pipeline.

### Missing Backend Endpoints Needed
1. **Authentication & Multi-User (`/api/auth/`)**:
   - `POST /api/auth/register`: Create user account with hashed password and preferred language.
   - `POST /api/auth/login`: Authenticate and return JWT/bearer token and user info.
   - `GET /api/auth/profile`: Retrieve user profile.
   - `PUT /api/auth/profile`: Update user profile and language preference.
2. **Standalone ML Prediction (`/api/yield/`)**:
   - `POST /api/yield/predict`: Endpoint exposing `predict_district_yield` with input validation.
   - `GET /api/yield/meta`: District, crop, and rainfall category metadata.
3. **Recommendation History & PDF Generation (`/api/recommendations/`)**:
   - `GET /api/recommendations`: Retrieve authenticated farmer's saved recommendations.
   - `POST /api/recommendations`: Save full recommendation record.
   - `GET /api/recommendations/{id}`: Retrieve detailed recommendation.
   - `GET /api/recommendations/{id}/pdf`: Generate and download downloadable PDF report via ReportLab.
4. **Previous Fertilizer History (`/api/farmer/fertilizer-history`)**:
   - `GET /api/farmer/fertilizer-history`: List recorded fertilizer usages.
   - `POST /api/farmer/fertilizer-history`: Add previous fertilizer entry.
5. **Notifications (`/api/notifications`)**:
   - `GET /api/notifications`: Retrieve user-specific alerts and system events.

---

## 4. Database Schema Audit & Migrations

### Current Database (`soil_phase3.sqlite3`)
The database contains tables:
- `soil_documents`
- `soil_ocr_results`
- `soil_profiles`
- `soil_profile_fields`

### Required Tables to Add
To support multi-user authentication, history, and user-specific farm data:
1. `users`: `(user_id, email, password_hash, full_name, phone, preferred_language, district, created_at, updated_at)`
2. `farmer_farms`: `(farm_id, user_id, district, village, area, area_unit, irrigation, soil_series, created_at)`
3. `farmer_fertilizer_history`: `(id, user_id, crop, season, year, fertilizer_product, quantity, unit, application_date, notes, created_at)`
4. `saved_recommendations`: `(recommendation_id, user_id, crop, district, farm_area, target_yield, full_response_json, created_at)`
5. `user_notifications`: `(id, user_id, title, message, category, is_read, created_at)`

---

## 5. Localization Audit

- **Current State**: Hardcoded English across all existing Dart widgets.
- **Requirement**: Full support for Tamil (`ta`), English (`en`), and Hindi (`hi`).
- **Solution**:
  - Implement a centralized localization system with English, Tamil, and Hindi translation dictionaries covering all 27 screens, labels, errors, buttons, dialogs, and agricultural terminology.
  - Reactive `LocaleNotifier` allowing instantaneous on-the-fly language switching from Language Selection or Settings screen.
  - Localized units (kg, ha, acre, bags) and formatted currency (₹ / INR).

---

## 6. Machine Learning & Agronomic Separation Compliance

- **Integrity Check**:
  - Phase 2 ML Model (`models/yield_prediction/yield_model.joblib`) predicts **district-average yield** in kg/ha based on district rainfall and year. It is **NOT** used to determine NPK doses or fertilizer bags.
  - Phase 4 Agronomic Engine (`data/agronomy/tnau_stcr_rules.json`) applies verified TNAU & STCR linear regression equations.
  - Phase 6 LP Optimizer (`phase6_fertilizer/`) uses `scipy.optimize.linprog` to select lowest-cost commercial bags.
  - Phase 7 Weather Guidance provides spray/timing advisories without modifying agronomic NPK baselines.
  - This strict separation is completely preserved.

---

## 7. Phased Implementation Roadmap

- **Phase A**: Multi-User Database Schema & FastAPI Auth, Yield & Report Endpoints.
- **Phase B**: Complete Localization System (Tamil, English, Hindi) & Navigation Shell (Bottom Navigation Bar).
- **Phase C**: Authentication Screens (Splash, Language Selection, Login, Register, Profile, Settings).
- **Phase D**: Core Soil & Agronomic Flow Integration (Upload, OCR, Verify, Farm Details, Crop Selection, Previous Fertilizer).
- **Phase E**: NPK Calculation, LP Fertilizer Optimization, Recommendation & Schedule Screens.
- **Phase F**: Machine Learning Yield Prediction & Agro-Weather Advisory Screens.
- **Phase G**: Recommendation History, Details, PDF Report Generation & Notifications.
- **Phase H**: Help, FAQs, About Screen, Automated Test Suite Execution & Documentation.
