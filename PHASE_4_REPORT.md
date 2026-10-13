# PHASE 4: AGRONOMIC RULE DATABASE AND RULE SELECTION ENGINE
**Tamil Nadu-Specific AI-Based Sustainable Fertilizer Usage Optimizer**

---

## 1. Executive Summary

Phase 4 delivers a structured, verified agronomic rule database and an intelligent rule selection engine tailored specifically for Tamil Nadu agricultural conditions. Based on official publications from Tamil Nadu Agricultural University (TNAU), Soil Test Crop Response (STCR), and Integrated Plant Nutrient Supply (IPNS), this phase selects the precise agronomic recommendation rule applicable to a farmer's crop, soil series, season, irrigation status, and target yield.

> **Strict Responsibility Boundary:** Phase 4 handles rule database management, input validation, candidate filtering, precedence scoring, and rule selection. It **does NOT** compute final NPK nutrient quantities, which is reserved strictly for Phase 5.

---

## 2. Official TNAU Sources Inspected & Verified

The following official TNAU sources were accessed, inspected, and registered into `data/agronomy/source_registry.csv`:

| Source ID | Source Title | Organization | URL | Verification Status | Key Inspected Content |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SRC_TNAU_STS` | TNAU Soil Testing Services | TNAU | https://agritech.tnau.ac.in/agriculture/agri_soil_tnau_soiltestingservices.html | `VERIFIED` | Standard soil rating thresholds & general rating adjustments |
| `SRC_TNAU_RATINGS` | TNAU Soil Fertility Thresholds | TNAU | https://agritech.tnau.ac.in/pdf/2.pdf | `VERIFIED` | Low / Medium / High rating tables (Tables 1 & 2) |
| `SRC_TNAU_NUTRIENT` | TNAU Nutrient Management Guide | TNAU | https://agritech.tnau.ac.in/agriculture/agri_nutrientmgt.html | `VERIFIED` | Principles of STCR & IPNS methodology |
| `SRC_TNAU_CPG2020` | TNAU Crop Production Guide 2020 | TNAU | https://tnau.ac.in/site/research/wp-content/uploads/sites/60/2020/02/Agriculture-CPG-2020.pdf | `VERIFIED` | Crop production guide recommendations for field & commercial crops |
| `SRC_TNAU_COTTON_STCR` | TNAU Cotton STCR Recommendations | TNAU | https://agritech.tnau.ac.in/agriculture/agri_cotton_STCR_P_K_cotton.html | `VERIFIED` | Soil Test Crop Response (STCR) equations for cotton on Irugur/Pilamedu series |
| `SRC_TNAU_STCR_IPNS` | TNAU Agriculture / STCR-IPNS Reference | TNAU | https://agritech.tnau.ac.in/pdf/AGRICULTURE.pdf | `VERIFIED` | STCR-IPNS calibration details across soil series |
| `SRC_TNAU_BLACKGRAM_RF` | TNAU Blackgram Rainfed Guide | TNAU | https://agritech.tnau.ac.in/agriculture/CropProduction/Pulses/BlackgramRainfed.html | `VERIFIED` | Rainfed nutrient management and cultivation practices for blackgram |

---

## 3. Agronomic Rule Database Breakdown

Rules are maintained in `data/agronomy/tnau_stcr_rules.json`. Each entry strictly tracks verification status and applicability bounds.

### Rule Summary Metrics

- **Total Registered Rules:** 9
- **VERIFIED Rules:** 7 (Eligible for production recommendations)
- **PENDING_VERIFICATION Rules:** 1 (Under field validation; rejected for production recommendations)
- **UNSUPPORTED Rules:** 1 (Deprecated legacy blanket rules; excluded from selection)

### Registered Rule Details

1. `TNAU_STCR_IPNS_RICE_001` (`VERIFIED`, `STCR-IPNS`)
   - **Crop:** Rice
   - **Applicable Soil Series:** Palavidhi, Adanur, Kalathur
   - **Districts:** Thanjavur, Tiruvarur, Nagapattinam, Mayiladuthurai, Cuddalore (Cauvery Delta)
   - **Irrigation:** Irrigated | **Seasons:** Kharif, Rabi, Samba, Kuruvai, Navarai
   - **Target Yield Range:** 3.0 - 8.0 t/ha
   - **Required Inputs:** `nitrogen`, `phosphorus`, `potassium`, `soil_series`, `target_yield`, `phosphorus_method`

2. `TNAU_STCR_IPNS_COTTON_001` (`VERIFIED`, `STCR-IPNS`)
   - **Crop:** Cotton (lint) | **Variety:** MCU 5
   - **Applicable Soil Series:** Irugur, Pilamedu
   - **Districts:** Coimbatore, Tiruppur, Erode
   - **Irrigation:** Irrigated | **Seasons:** Kharif, Winter
   - **Target Yield Range:** 1.5 - 3.5 t/ha
   - **Required Inputs:** `nitrogen`, `phosphorus`, `potassium`, `soil_series`, `target_yield`, `phosphorus_method`

3. `TNAU_STCR_IPNS_MAIZE_001` (`VERIFIED`, `STCR-IPNS`)
   - **Crop:** Maize
   - **Applicable Soil Series:** Coimbatore, Pilamedu
   - **Districts:** Coimbatore, Tiruppur, Dindigul, Erode
   - **Irrigation:** Irrigated | **Seasons:** Kharif, Rabi
   - **Target Yield Range:** 5.0 - 10.0 t/ha
   - **Required Inputs:** `nitrogen`, `phosphorus`, `potassium`, `soil_series`, `target_yield`, `phosphorus_method`

4. `TNAU_STD_RICE_001` (`VERIFIED`, `TNAU-SOIL-TEST`)
   - **Crop:** Rice
   - **Irrigation:** Irrigated | **Seasons:** All
   - **Required Inputs:** `nitrogen`, `phosphorus`, `potassium`, `phosphorus_method`
   - **Notes:** Standard soil-test rating adjustment rule when specific STCR soil series is not specified.

5. `TNAU_STD_BLACKGRAM_RF_001` (`VERIFIED`, `TNAU-SOIL-TEST`)
   - **Crop:** Blackgram
   - **Irrigation:** Rainfed | **Seasons:** Rabi, Kharif, Rainfed
   - **Required Inputs:** `nitrogen`, `phosphorus`, `potassium`, `phosphorus_method`

6. `TNAU_STD_GROUNDNUT_001` (`VERIFIED`, `TNAU-SOIL-TEST`)
   - **Crop:** Groundnut
   - **Irrigation:** Both (Irrigated & Rainfed) | **Seasons:** Kharif, Rabi, Summer
   - **Required Inputs:** `nitrogen`, `phosphorus`, `potassium`, `phosphorus_method`

7. `TNAU_STD_SUGARCANE_001` (`VERIFIED`, `TNAU-SOIL-TEST`)
   - **Crop:** Sugarcane
   - **Irrigation:** Irrigated | **Seasons:** All
   - **Required Inputs:** `nitrogen`, `phosphorus`, `potassium`, `phosphorus_method`

8. `TNAU_STCR_BANANA_001` (`PENDING_VERIFICATION`, `STCR-IPNS`)
   - **Crop:** Banana | **Variety:** Grand Naine
   - **Soil Series:** Thonnackal
   - **Status:** Pending TNAU laboratory re-verification. Triggers `PENDING_VERIFICATION` status.

9. `TNAU_DEPRECATED_RICE_000` (`UNSUPPORTED`, `TNAU-BLANKET`)
   - **Status:** Obsolete 1980 blanket dosing guide. Excluded from production selection.

---

## 4. Rule Selection Engine & Precedence Logic

The selection engine (`agronomy/service.py`) follows strict agronomic precedence:

1. **Crop Lookup & Normalization:** Checks canonical crop name. Unknown crops return `UNSUPPORTED_CROP`.
2. **Soil Series Compatibility Guard:** If a crop relies on STCR calibration for specific soil series (e.g. Cotton on Irugur/Pilamedu) and an incompatible soil series is provided, returns `UNSUPPORTED_SOIL_SERIES`.
3. **Cultivation Condition Filtering:** Filters rules by irrigation method (Irrigated vs Rainfed), season compatibility, target yield bounds, and district applicability.
4. **Precedence Scoring:**
   - Base Scores: `STCR-IPNS` (100) > `STCR-NPK` (80) > `TNAU-SOIL-TEST` (50) > `TNAU-BLANKET` (10).
   - Fully Satisfied Bonus (+200): Rules with 0 missing mandatory inputs score higher.
   - Targeted Soil Series Bonus (+150): When farmer provides an STCR soil series, STCR rules take precedence to request missing STCR parameters (e.g. `target_yield`).
5. **Verification Guard:** Only rules with `VERIFIED` status are selected for `RULE_SELECTED`. Matching pending rules return `PENDING_VERIFICATION`.

---

## 5. API Endpoint Specifications

### `POST /api/agronomy/select-rule`

#### Request Body
```json
{
  "crop": "Rice",
  "variety": "ADT 36",
  "district": "Thanjavur",
  "soil_series": "Palavidhi",
  "season": "Kharif",
  "irrigation_method": "Irrigated",
  "target_yield": 6.0,
  "soil_values": {
    "nitrogen": 220.0,
    "phosphorus": 16.0,
    "potassium": 190.0,
    "phosphorus_method": "Olsen"
  }
}
```

#### Response Body (`RULE_SELECTED`)
```json
{
  "status": "RULE_SELECTED",
  "selected_rule_id": "TNAU_STCR_IPNS_RICE_001",
  "crop": "Rice",
  "recommendation_method": "STCR-IPNS",
  "applicable_soil_series": ["Palavidhi", "Adanur", "Kalathur"],
  "applicable_season": ["Kharif", "Rabi", "Samba", "Kuruvai", "Navarai"],
  "irrigation_method": "Irrigated",
  "required_inputs": ["nitrogen", "phosphorus", "potassium", "soil_series", "target_yield"],
  "source_title": "TNAU Agriculture / STCR-IPNS Reference",
  "source_url": "https://agritech.tnau.ac.in/pdf/AGRICULTURE.pdf",
  "source_page_or_section": "STCR-IPNS Rice Calibration Tables, pp. 12-15",
  "verification_status": "VERIFIED",
  "applicability_notes": "Valid for irrigated paddy in Cauvery delta soils (Palavidhi, Adanur, Kalathur series) for target yields between 3.0 and 8.0 t/ha using STCR-IPNS approach.",
  "missing_inputs": [],
  "warnings": []
}
```

---

## 6. Supported vs. Unsupported Crops & Conditions

### Supported Crops & Conditions

| Crop | Irrigation | Soil Series | Seasons | Methods Available |
| :--- | :--- | :--- | :--- | :--- |
| **Rice** | Irrigated | Palavidhi, Adanur, Kalathur, or Broad | Kharif, Rabi, Samba, Kuruvai, Navarai, All | STCR-IPNS, TNAU-SOIL-TEST |
| **Cotton (lint)** | Irrigated | Irugur, Pilamedu | Kharif, Winter | STCR-IPNS |
| **Maize** | Irrigated | Coimbatore, Pilamedu | Kharif, Rabi | STCR-IPNS |
| **Blackgram** | Rainfed | Broad / All | Rabi, Kharif, Rainfed | TNAU-SOIL-TEST |
| **Groundnut** | Irrigated / Rainfed | Broad / All | Kharif, Rabi, Summer | TNAU-SOIL-TEST |
| **Sugarcane** | Irrigated | Broad / All | All | TNAU-SOIL-TEST |

### Unsupported Crops & Combinations

- **Unsupported Crops:** Exotic or non-registered crops (e.g., DragonFruit, Kiwi, Apple). Return `UNSUPPORTED_CROP`.
- **Unsupported Soil Series:** Passing non-calibrated soil series for STCR-only crops (e.g. Cotton with `soil_series="UnknownSeries"`). Return `UNSUPPORTED_SOIL_SERIES`.
- **Unsupported Cultivation Combinations:**
  - Rainfed Rice on STCR Palavidhi rule (Irrigation mismatch).
  - Sugarcane under Rainfed conditions (Sugarcane rule requires Irrigated).
  - Target yield outside calibrated range (e.g. Rice target yield = 15.0 t/ha exceeds max 8.0 t/ha).

---

## 7. Automated Test Results

The test suite in `agronomy/tests/test_agronomy_rule_selection.py` executes **12 comprehensive test cases**:

```bash
pytest agronomy/tests/test_agronomy_rule_selection.py -v
```

### Execution Output
```
agronomy/tests/test_agronomy_rule_selection.py::test_01_matching_verified_rule PASSED [  8%]
agronomy/tests/test_agronomy_rule_selection.py::test_02_unsupported_crop PASSED [ 16%]
agronomy/tests/test_agronomy_rule_selection.py::test_03_missing_mandatory_input PASSED [ 25%]
agronomy/tests/test_agronomy_rule_selection.py::test_04_unsupported_soil_series PASSED [ 33%]
agronomy/tests/test_agronomy_rule_selection.py::test_05_irrigation_mismatch PASSED [ 41%]
agronomy/tests/test_agronomy_rule_selection.py::test_06_season_mismatch PASSED [ 50%]
agronomy/tests/test_agronomy_rule_selection.py::test_07_target_yield_outside_documented_range PASSED [ 58%]
agronomy/tests/test_agronomy_rule_selection.py::test_08_pending_verification_rule PASSED [ 66%]
agronomy/tests/test_agronomy_rule_selection.py::test_09_no_matching_rule PASSED [ 75%]
agronomy/tests/test_agronomy_rule_selection.py::test_10_api_validation_endpoint PASSED [ 83%]
agronomy/tests/test_agronomy_rule_selection.py::test_11_correct_source_traceability PASSED [ 91%]
agronomy/tests/test_agronomy_rule_selection.py::test_12_rule_selection_precedence PASSED [100%]

============================= 12 passed in 15.52s =============================
```

---

## 8. Created & Modified Files

### Created Files
- `data/agronomy/source_registry.csv`: Source registry mapping official TNAU publications.
- `data/agronomy/tnau_stcr_rules.json`: Structured agronomic rule database.
- `agronomy/__init__.py`: Package initialization.
- `agronomy/models.py`: Pydantic request & response schemas.
- `agronomy/registry.py`: Registry loader for rules and source references.
- `agronomy/service.py`: Rule selection engine & input validation service.
- `agronomy/api.py`: FastAPI router with `POST /api/agronomy/select-rule`.
- `agronomy/tests/__init__.py`: Test package initialization.
- `agronomy/tests/test_agronomy_rule_selection.py`: 12 automated unit tests.
- `PHASE_4_REPORT.md`: Comprehensive phase completion report.

### Modified Files
- `phase3_soil/main.py`: Mounted `agronomy_router` into main FastAPI app.
- `phase3_soil/tests/fixtures.py`: Windows font fallback for test suite execution.

---

## 9. Next Steps for Phase 5 (NPK Calculation Engine)

Phase 4 successfully selects the active verified agronomic rule. In Phase 5, the system will use the selected `rule_id` and rule metadata to:
1. Evaluate exact STCR-IPNS linear regression equations ($NR$, $CS$, $CF$, $COY$) for targeted yield NPK calculation.
2. Apply TNAU soil test rating adjustment factors (Low: +25%, Medium: 0%, High: -25%) for standard soil-test recommendations.
3. Compute organic fertilizer adjustments (FYM / Green manure NPK credits).
4. Output final recommended N, $\text{P}_2\text{O}_5$, and $\text{K}_2\text{O}$ nutrient requirements in kg/ha and bag equivalents.
