# AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers
**Project Reference: SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield**

---

## 1. Overview & System Architecture

An end-to-end decision support application for Tamil Nadu farmers integrating verified soil-test data, official TNAU/STCR/IPNS agronomic rules, deterministic NPK requirement calculation, Linear Programming (LP) fertilizer cost optimization, real-time agro-weather timing guidance, district-level XGBoost crop yield estimation, and a 27-screen mobile application localized in **Tamil (தமிழ்)**, **English**, and **Hindi (हिन्दी)**.

---

## 2. Implemented Application Screens (27 Screens)

| # | Screen Name | Description & Backend Integration |
| :--- | :--- | :--- |
| **1** | **Splash Screen** | Agricultural branding, auth session verification, auto-routing. |
| **2** | **Language Selection** | Tamil (தமிழ்), English, and Hindi (हिन्दी) reactive switching. |
| **3** | **Farmer Login** | `POST /api/auth/login` with password hash verification & token storage. |
| **4** | **Farmer Registration** | `POST /api/auth/register` with TN district & language preferences. |
| **5** | **Farmer Dashboard** | Vanakkam greeting, profile header, 6 action cards, live weather & latest activity. |
| **6** | **Soil Report Upload** | PDF, image, and camera upload via `POST /api/soil/upload`. |
| **7** | **Soil Report Extraction** | Automated Tesseract OCR extraction via `POST /api/soil/ocr`. |
| **8** | **Soil Report Verification**| Farmer value review, range validation & confirmation via `POST /api/soil/confirm`. |
| **9** | **Farm Details** | District, village, area (acres/ha), irrigation & TNAU soil series (`/api/farmer/farm`). |
| **10** | **Crop Selection** | Verified TNAU crops (Rice, Sugarcane, Cotton, Maize, Groundnut), seasons & target yield. |
| **11** | **Previous Fertilizer** | History tracking for organic manure (FYM) & previous fertilizers (`/api/farmer/fertilizer-history`). |
| **12** | **NPK Requirement** | Deterministic N, P2O5, K2O calculation (kg/ha and farm total) via TNAU STCR rules. |
| **13** | **Fertilizer Optimization** | Linear Programming (`scipy.optimize.linprog`) commercial bag solver (45kg/50kg MRPs). |
| **14** | **Final Recommendation** | Commercial purchase plan, bag counts, estimated cost (INR), actions & disclaimers. |
| **15** | **Application Schedule** | Basal, tillering, and panicle initiation split application schedules & timing advice. |
| **16** | **Yield Prediction Input**| Feature inputs (district, crop, season, SWM, NEM, winter rainfall mm) for Phase 2 ML model. |
| **17** | **Yield Prediction Results**| District-average statistical benchmark (kg/ha) with honest scope disclaimers. |
| **18** | **Weather Information** | Agro-weather advisories, rainfall risks, and fertilizer spray timing guidance (`/api/weather/guidance`). |
| **19** | **Sustainability Insights**| Soil nutrient balance, IPNS organic manure benefits, and environmental protection. |
| **20** | **Recommendation History** | Saved recommendation list with filter & search (`GET /api/recommendations`). |
| **21** | **Recommendation Details** | Full audit record view of saved recommendations with soil inputs & product bags. |
| **22** | **Report Generation** | Downloadable PDF report generated server-side using ReportLab (`/api/recommendations/{id}/pdf`). |
| **23** | **Farmer Profile** | Farmer identity, mobile number, district, and contact updates (`/api/auth/profile`). |
| **24** | **Notifications** | Real application alerts: welcome messages, saved recommendations, weather advisories. |
| **25** | **Help & Guidance** | Farmer-friendly FAQs explaining Soil Health Cards, STCR equations, and LP optimization. |
| **26** | **Settings** | Language switch, backend API endpoint, logout, and version details. |
| **27** | **About the Application** | SIH1639 project reference, TNAU Agritech citations, and scientific disclaimers. |

---

## 3. API Endpoints Reference

| Method | Endpoint Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Server health status |
| `POST` | `/api/auth/register` | Register new farmer account |
| `POST` | `/api/auth/login` | Authenticate farmer with credentials |
| `GET` | `/api/auth/profile` | Get farmer profile |
| `PUT` | `/api/auth/profile` | Update farmer profile |
| `POST` | `/api/soil/upload` | Upload PDF or JPEG soil health card |
| `POST` | `/api/soil/ocr` | Run OCR extraction on uploaded soil document |
| `POST` | `/api/soil/validate` | Plausibility & range checks on soil values |
| `POST` | `/api/soil/confirm` | Confirm soil profile with farmer edits |
| `GET` | `/api/soil/{soil_profile_id}` | Retrieve confirmed soil profile |
| `GET` | `/api/farmer/farm` | Retrieve saved farm details |
| `POST` | `/api/farmer/farm` | Save farm details |
| `GET` | `/api/farmer/fertilizer-history` | List previous fertilizer applications |
| `POST` | `/api/farmer/fertilizer-history` | Add previous fertilizer application |
| `POST` | `/api/agronomy/select-rule` | Select verified TNAU/STCR/IPNS agronomic rule |
| `POST` | `/api/nutrient-requirement/calculate` | Calculate per-ha & total N, P2O5, K2O requirements |
| `POST` | `/api/fertilizer/optimize` | Minimize fertilizer purchase cost via LP optimization |
| `POST` | `/api/yield/predict` | Predict district-average yield benchmark using XGBoost model |
| `GET` | `/api/yield/meta` | Get ML model feature categories (districts, crops, seasons) |
| `GET` | `/api/weather/guidance` | District agro-weather alerts & fertilizer timing advice |
| `POST` | `/api/full-recommendation` | End-to-end master recommendation pipeline |
| `POST` | `/api/recommendations` | Save recommendation to user history |
| `GET` | `/api/recommendations` | List user's saved recommendations |
| `GET` | `/api/recommendations/{id}` | Get saved recommendation audit record |
| `GET` | `/api/recommendations/{id}/pdf`| Download official ReportLab PDF report |
| `GET` | `/api/notifications` | Get farmer notifications |

---

## 4. Multi-User Database Schema (`soil_phase3.sqlite3`)

1. `users`: `(user_id, email, password_hash, full_name, phone, preferred_language, district, created_at, updated_at)`
2. `farmer_farms`: `(farm_id, user_id, district, village, area, area_unit, irrigation, soil_series, created_at)`
3. `farmer_fertilizer_history`: `(id, user_id, crop, season, year, fertilizer_product, quantity, unit, application_date, notes, created_at)`
4. `saved_recommendations`: `(recommendation_id, user_id, crop, district, farm_area, farm_area_unit, target_yield, total_cost_inr, response_json, created_at)`
5. `user_notifications`: `(id, user_id, title, message, category, is_read, created_at)`
6. `soil_documents`, `soil_ocr_results`, `soil_profiles`, `soil_profile_fields` (Core Soil OCR tables)

---

## 5. Quick Start & Execution

### 1. Launch Backend Server (FastAPI)
```powershell
uvicorn phase3_soil.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Launch Mobile / Web Application (Flutter)
```powershell
cd flutter_app
flutter pub get
flutter run -d chrome
```

### 3. Run Automated Test Suites

**Backend Suite (79 Tests Passing):**
```powershell
pytest agronomy/tests phase3_soil/tests phase5_nutrient/tests phase6_fertilizer/tests phase7_integration/tests tests -v
```

**Flutter Suite (15 Tests Passing):**
```powershell
cd flutter_app
flutter test
```

**Static Code Analysis:**
```powershell
cd flutter_app
flutter analyze
```
*(Result: 0 issues found)*
