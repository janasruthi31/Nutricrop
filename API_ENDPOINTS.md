# FastAPI Backend API Endpoints Documentation

**Project Title:** AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**Base URL:** `http://localhost:8000` (configurable via `APP_API_BASE_URL`)  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)  

---

## 1. Authentication & Farmer Profile

### 1.1 Farmer Registration
- **Method:** `POST`
- **Path:** `/api/auth/register`
- **Request Body (JSON):**
  ```json
  {
    "email": "farmer@example.com",
    "password": "Password123!",
    "full_name": "Murugan Shanmugam",
    "phone": "+91 94441 23456",
    "district": "Thanjavur",
    "preferred_language": "ta"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "user_id": "usr_789abc",
    "email": "farmer@example.com",
    "full_name": "Murugan Shanmugam",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

### 1.2 Farmer Login
- **Method:** `POST`
- **Path:** `/api/auth/login`
- **Request Body (JSON):**
  ```json
  {
    "email": "farmer@example.com",
    "password": "Password123!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "user_id": "usr_789abc",
      "full_name": "Murugan Shanmugam",
      "district": "Thanjavur",
      "preferred_language": "ta"
    }
  }
  ```

### 1.3 Get Current Farmer Profile
- **Method:** `GET`
- **Path:** `/api/auth/me`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** Current farmer profile data.

---

## 2. Soil Health Card OCR and Validation (Phase 3)

### 2.1 Upload Soil Health Card Document
- **Method:** `POST`
- **Path:** `/api/soil/upload`
- **Headers:** `Authorization: Bearer <token>` or `X-Farmer-Id: <user_id>`
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `file`: PDF or image file (PNG, JPG) up to 10 MB.
- **Response (201 Created):**
  ```json
  {
    "document_id": "doc_12345",
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "mime_type": "application/pdf",
    "upload_status": "UPLOADED"
  }
  ```

### 2.2 Run Soil Document OCR Extraction
- **Method:** `POST`
- **Path:** `/api/soil/documents/{document_id}/ocr`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "document_id": "doc_12345",
    "ocr_status": "EXTRACTED",
    "extracted_parameters": {
      "ph": 7.2,
      "ec": 0.45,
      "organic_carbon_pct": 0.52,
      "available_n_kg_per_ha": 180.0,
      "available_p_kg_per_ha": 18.5,
      "available_k_kg_per_ha": 210.0
    },
    "confidence_scores": {
      "ph": 0.98,
      "available_n_kg_per_ha": 0.95
    }
  }
  ```

### 2.3 Validate Extracted Soil Parameters
- **Method:** `POST`
- **Path:** `/api/soil/documents/{document_id}/validate`
- **Request Body (JSON):** Optional farmer overrides or corrections.
- **Response (200 OK):**
  ```json
  {
    "validation_status": "VALID",
    "blockers": [],
    "warnings": [],
    "tnau_ratings": {
      "n_rating": "LOW",
      "p_rating": "MEDIUM",
      "k_rating": "MEDIUM"
    }
  }
  ```

### 2.4 Confirm Soil Profile
- **Method:** `POST`
- **Path:** `/api/soil/documents/{document_id}/confirm`
- **Request Body (JSON):** Confirmed parameter values.
- **Response (200 OK):** Confirmed profile record ID and verification timestamp.

---

## 3. Agronomic Rule Selection (Phase 4)

### 3.1 Match Agronomic STCR-IPNS Rule
- **Method:** `POST`
- **Path:** `/api/agronomy/select-rule`
- **Request Body (JSON):**
  ```json
  {
    "crop": "Rice",
    "soil_series": "Adanur",
    "season": "Kuruvai",
    "yield_target_q_per_ha": 60.0
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "rule_id": "TNAU_RICE_STCR_001",
    "crop": "Rice",
    "status": "VERIFIED",
    "source_reference": "TNAU Crop Production Guide 2020",
    "equation_coefficients": {
      "fn_equation": "4.25 * T - 0.54 * SN - 0.72 * ON",
      "fp_equation": "1.85 * T - 0.42 * SP - 0.65 * OP",
      "fk_equation": "2.40 * T - 0.38 * SK - 0.55 * OK"
    }
  }
  ```

---

## 4. NPK Requirement Calculation (Phase 5)

### 4.1 Compute Net NPK Requirement
- **Method:** `POST`
- **Path:** `/api/nutrient/calculate-npk`
- **Request Body (JSON):**
  ```json
  {
    "crop": "Rice",
    "farm_area": 2.0,
    "farm_area_unit": "acre",
    "yield_target_q_per_ha": 60.0,
    "soil_test_values": {
      "available_n_kg_per_ha": 180.0,
      "available_p_kg_per_ha": 18.5,
      "available_k_kg_per_ha": 210.0
    },
    "fym_applied_tonnes_per_ha": 12.5
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "n_req_kg_per_ha": 124.8,
    "p2o5_req_kg_per_ha": 48.2,
    "k2o_req_kg_per_ha": 52.6,
    "net_n_kg_per_ha": 124.8,
    "net_p2o5_kg_per_ha": 48.2,
    "net_k2o_kg_per_ha": 52.6,
    "total_farm_n_kg": 101.0,
    "total_farm_p2o5_kg": 39.0,
    "total_farm_k2o_kg": 42.6,
    "calculation_method": "TNAU_STCR_IPNS"
  }
  ```

---

## 5. Fertilizer Cost Optimization (Phase 6)

### 5.1 Commercial Fertilizer Catalog
- **Method:** `GET`
- **Path:** `/api/fertilizer/catalog`
- **Response (200 OK):** List of subsidized commercial fertilizers in Tamil Nadu, nutrient grades (N-P-K-S), bag sizes, and maximum retail prices.

### 5.2 Optimize Fertilizer Combination & Bag Quantities
- **Method:** `POST`
- **Path:** `/api/fertilizer/optimize`
- **Request Body (JSON):**
  ```json
  {
    "net_n_kg": 101.0,
    "net_p2o5_kg": 39.0,
    "net_k2o_kg": 42.6,
    "available_products": ["Urea", "DAP", "MOP"],
    "allow_bag_rounding": true
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "OPTIMAL",
    "total_cost_inr": 2345.50,
    "recommended_products": [
      {
        "product_name": "Urea",
        "name": "Urea",
        "bags": 3,
        "bag_size_kg": 45.0,
        "cost_inr": 801.0
      },
      {
        "product_name": "DAP",
        "name": "DAP",
        "bags": 2,
        "bag_size_kg": 50.0,
        "cost_inr": 1350.0
      },
      {
        "product_name": "Muriate of Potash (MOP)",
        "name": "Muriate of Potash (MOP)",
        "bags": 1,
        "bag_size_kg": 50.0,
        "cost_inr": 194.50
      }
    ],
    "application_schedule": {
      "basal": [...],
      "tillering": [...],
      "panicle_initiation": [...]
    }
  }
  ```

---

## 6. Crop Yield Prediction & Weather Guidance (Phases 2 & 7)

### 6.1 District-Level Benchmark Crop Yield Prediction (ML)
- **Method:** `POST`
- **Path:** `/api/yield/predict`
- **Request Body (JSON):**
  ```json
  {
    "district": "Thanjavur",
    "crop": "Rice",
    "season": "Kharif",
    "rainfall_mm": 950.0,
    "area_ha": 1.5
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "predicted_yield_kg_per_ha": 3840.5,
    "predicted_yield_tonnes_per_ha": 3.84,
    "confidence_range": {
      "lower_kg_per_ha": 3450.0,
      "upper_kg_per_ha": 4230.0
    },
    "canonical_unit": "kg/ha",
    "benchmark_note": "District benchmark average based on Season & Crop Reports (2020-2025). Does not replace soil-specific field diagnostics."
  }
  ```

### 6.2 Agro-Meteorological Weather Guidance
- **Method:** `GET`
- **Path:** `/api/weather/guidance?district=Thanjavur&language=ta`
- **Response (200 OK):**
  ```json
  {
    "district": "Thanjavur",
    "current_condition": "Light Rain / Clear Intervals",
    "temperature_c": 28.5,
    "rainfall_probability_pct": 20,
    "risk_level": "FAVORABLE",
    "actionable_advice": "மழை வாய்ப்பு குறைவு. மேலுரமிடுதலைத் தொடரலாம்.",
    "spray_condition": "FAVORABLE"
  }
  ```

---

## 7. Master Orchestration, Storage, & Reports (Phase 7)

### 7.1 Full End-to-End Recommendation
- **Method:** `POST`
- **Path:** `/api/full-recommendation`
- **Request Body (JSON):** Combined payload containing farm area, soil measurements, selected crop, and yield targets.
- **Response (200 OK):** Comprehensive composite object containing NPK needs, optimized bags, application splits, weather advice, and regional yield benchmark.

### 7.2 Save Recommendation to Farmer History
- **Method:** `POST`
- **Path:** `/api/recommendations/save`
- **Headers:** `Authorization: Bearer <token>`
- **Request Body (JSON):** Full recommendation payload.
- **Response (201 Created):** `{ "recommendation_id": "rec_98231", "saved_at": "2026-10-13T..." }`

### 7.3 Farmer Recommendation History
- **Method:** `GET`
- **Path:** `/api/recommendations/history`
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** List of past recommendations for the authenticated farmer.

### 7.4 Download Bilingual PDF Soil & Fertilizer Report
- **Method:** `POST`
- **Path:** `/api/recommendations/download-pdf`
- **Headers:** `Authorization: Bearer <token>`
- **Content-Type:** `application/json`
- **Response (200 OK):** Binary PDF stream (`Content-Type: application/pdf`, `Content-Disposition: attachment; filename="Soil_Fertilizer_Recommendation.pdf"`).
