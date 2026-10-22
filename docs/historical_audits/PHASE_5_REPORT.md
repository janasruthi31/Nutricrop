# PHASE 5: NPK NUTRIENT REQUIREMENT CALCULATION ENGINE
**Tamil Nadu-Specific AI-Based Sustainable Fertilizer Usage Optimizer**

---

## 1. Executive Summary

Phase 5 delivers a deterministic, scientifically verified NPK Nutrient Requirement Calculation Engine for Tamil Nadu farmers. Consuming the verified rule selection output from Phase 4, Phase 5 evaluates exact TNAU/STCR/IPNS equations and soil-test rating adjustments to compute elemental and oxide nutrient requirements ($N$, $\text{P}_2\text{O}_5$, $\text{K}_2\text{O}$) in kg/ha and for the total farm area.

> **Strict Responsibility Boundary:** Phase 5 outputs pure nutrient requirements ($N, \text{P}_2\text{O}_5, \text{K}_2\text{O}$ in kg/ha and total kg). It **does NOT** compute fertilizer product types (Urea, DAP, MOP, SSP, etc.) or bag counts, which is reserved strictly for Phase 6 (Fertilizer Product Optimization).

---

## 2. Calculation Methodologies & Formulas

Phase 5 supports two distinct, verified agronomic calculation methodologies based on the selected Phase 4 rule:

### A. Soil Test Crop Response (STCR-IPNS) Targeted Yield Calculations
For STCR rules (e.g. `TNAU_STCR_IPNS_RICE_001`, `TNAU_STCR_IPNS_COTTON_001`, `TNAU_STCR_IPNS_MAIZE_001`), nutrient requirements are computed using calibrated linear regression equations incorporating target yield ($T$ in t/ha), soil available nutrients ($SN, SP, SK$ in kg/ha), and organic manure credits ($c_{\text{fym}}$):

$$\text{N Requirement (kg/ha)} = \max\left(0, a_N \cdot T - b_N \cdot SN - c_{\text{fym}, N}\right)$$
$$\text{P}_2\text{O}_5\text{ Requirement (kg/ha)} = \max\left(0, a_P \cdot T - b_P \cdot SP - c_{\text{fym}, P}\right)$$
$$\text{K}_2\text{O Requirement (kg/ha)} = \max\left(0, a_K \cdot T - b_K \cdot SK - c_{\text{fym}, K}\right)$$

#### Calibrated Coefficients Matrix

| Crop Rule ID | Target Yield Unit | $a_N$ | $b_{N, \text{soil}}$ | $c_{\text{fym}, N}$ | $a_P$ | $b_{P, \text{soil}}$ | $c_{\text{fym}, P}$ | $a_K$ | $b_{K, \text{soil}}$ | $c_{\text{fym}, K}$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TNAU_STCR_IPNS_RICE_001` | t/ha | 22.4 | 0.44 | 20.0 | 11.2 | 1.80 | 10.0 | 13.5 | 0.32 | 10.0 |
| `TNAU_STCR_IPNS_COTTON_001` | t/ha | 94.2 | 0.47 | 15.0 | 39.6 | 1.62 | 10.0 | 77.4 | 0.28 | 10.0 |
| `TNAU_STCR_IPNS_MAIZE_001` | t/ha | 20.8 | 0.52 | 15.0 | 9.6 | 1.55 | 10.0 | 12.4 | 0.36 | 10.0 |

---

### B. TNAU Soil-Test Rating Adjustment Calculations (TNAU-SOIL-TEST)
For general crops without a specific STCR soil-series calibration (e.g. `TNAU_STD_RICE_001`, `TNAU_STD_BLACKGRAM_RF_001`, `TNAU_STD_GROUNDNUT_001`, `TNAU_STD_SUGARCANE_001`), Phase 5 classifies soil test values into TNAU fertility rating classes (Low, Medium, High) and applies rating adjustment factors to the Recommended Dose of Fertilizer (RDF):

- **Low Soil Fertility:** Add **25%** to RDF ($\text{Requirement} = 1.25 \times \text{RDF}$)
- **Medium Soil Fertility:** **100%** of RDF (No adjustment: $1.00 \times \text{RDF}$)
- **High Soil Fertility:** Subtract **25%** from RDF ($\text{Requirement} = 0.75 \times \text{RDF}$)

#### Base RDF & Soil Rating Thresholds

| Crop Rule ID | Base RDF $N : \text{P}_2\text{O}_5 : \text{K}_2\text{O}$ (kg/ha) | Low N Threshold | Low P Threshold (Olsen) | Low K Threshold |
| :--- | :--- | :--- | :--- | :--- |
| `TNAU_STD_RICE_001` | 150 : 50 : 50 | $< 280$ kg/ha | $< 11.0$ kg/ha | $< 118$ kg/ha |
| `TNAU_STD_BLACKGRAM_RF_001` | 20 : 40 : 20 | $< 280$ kg/ha | $< 11.0$ kg/ha | $< 118$ kg/ha |
| `TNAU_STD_GROUNDNUT_001` | 25 : 50 : 75 | $< 280$ kg/ha | $< 11.0$ kg/ha | $< 118$ kg/ha |
| `TNAU_STD_SUGARCANE_001` | 275 : 62.5 : 112.5 | $< 280$ kg/ha | $< 11.0$ kg/ha | $< 118$ kg/ha |

---

## 3. Unit Normalization & Farm Area Scaling

### Unit Conversions

- **Soil Nutrient Units:**
  - `kg/ha`: Multiplier = $1.0$
  - `mg/kg` (or `ppm`): Multiplier = $2.24$ (Standard depth conversion for 15 cm soil layer)
  - Unsupported units (e.g. `lbs/acre`) raise explicit `VALIDATION_ERROR`.

- **Farm Area Conversions:**
  - `hectare` (`ha`): Multiplier = $1.0$
  - `acre`: Multiplier = $0.404686$ ha/acre
  - `cent` (100 cents = 1 acre): Multiplier = $0.00404686$ ha/cent
  - `sq_meter` ($m^2$): Multiplier = $0.0001$ ha/$m^2$

### Farm-Total Requirements

$$\text{Total N (kg)} = \text{N (kg/ha)} \times \text{Farm Area (ha)}$$
$$\text{Total P}_2\text{O}_5\text{ (kg)} = \text{P}_2\text{O}_5\text{ (kg/ha)} \times \text{Farm Area (ha)}$$
$$\text{Total K}_2\text{O (kg)} = \text{K}_2\text{O (kg/ha)} \times \text{Farm Area (ha)}$$

*Note: Per-hectare requirements are preserved as primary output, and farm-total quantities are calculated without double multiplication.*

---

## 4. API Endpoint Specifications

### `POST /api/nutrient-requirement/calculate`

#### Example Request 1: STCR Irrigated Rice (5 Acres Farm Area)
```json
{
  "crop": "Rice",
  "selected_rule_id": "TNAU_STCR_IPNS_RICE_001",
  "target_yield": 6.0,
  "soil_nitrogen": 220.0,
  "soil_nitrogen_unit": "kg/ha",
  "soil_phosphorus": 16.0,
  "soil_phosphorus_unit": "kg/ha",
  "soil_phosphorus_method": "Olsen",
  "soil_potassium": 190.0,
  "soil_potassium_unit": "kg/ha",
  "farm_area": 5.0,
  "farm_area_unit": "acre"
}
```

#### Example Response 1 (`CALCULATION_SUCCESS`)
```json
{
  "status": "CALCULATION_SUCCESS",
  "crop": "Rice",
  "selected_rule_id": "TNAU_STCR_IPNS_RICE_001",
  "selected_method": "STCR-IPNS",
  "n_req_kg_per_ha": 17.6,
  "p2o5_req_kg_per_ha": 28.4,
  "k2o_req_kg_per_ha": 10.2,
  "farm_area_hectares": 2.0234,
  "total_n_req_kg": 35.61,
  "total_p2o5_req_kg": 57.46,
  "total_k2o_req_kg": 20.64,
  "calculation_details": {
    "method": "STCR-IPNS",
    "formula_N": "22.4 * T - 0.44 * SN - 20.0",
    "formula_P2O5": "11.2 * T - 1.8 * SP - 10.0",
    "formula_K2O": "13.5 * T - 0.32 * SK - 10.0",
    "inputs_used": {
      "target_yield": 6.0,
      "soil_N_kg_per_ha": 220.0,
      "soil_P_kg_per_ha": 16.0,
      "soil_K_kg_per_ha": 190.0,
      "phosphorus_method": "Olsen"
    }
  },
  "units": {
    "per_ha": "kg/ha",
    "total": "kg",
    "area": "hectare"
  },
  "source_title": "TNAU Agriculture / STCR-IPNS Reference",
  "source_url": "https://agritech.tnau.ac.in/pdf/AGRICULTURE.pdf",
  "source_page_or_section": "STCR-IPNS Rice Calibration Tables, pp. 12-15",
  "warnings": [],
  "missing_inputs": [],
  "validation_errors": []
}
```

---

## 5. Supported vs. Unsupported Scenarios

### Supported Scenarios

- STCR-IPNS targeted yield calculations for Rice, Cotton, and Maize.
- TNAU Soil-Test rating-based adjustments for Blackgram, Groundnut, Sugarcane, and Rice.
- Farm area conversion from acres, cents, square meters, or hectares.
- Automatic integration with Phase 4 rule selection engine when `phase4_result` or direct parameters are supplied.

### Unsupported Scenarios & Handled Validation Errors

- **Unverified Rules:** Rule with `verification_status="PENDING_VERIFICATION"` returns `UNVERIFIED_RULE`.
- **Missing Required Inputs:** Missing target yield for STCR or missing soil test values returns `MISSING_INPUTS`.
- **Target Yield Out of Range:** Target yield exceeding calibrated bounds (e.g. 15.0 t/ha for Rice) returns `VALIDATION_ERROR`.
- **Invalid Units:** Unsupported nutrient unit (e.g. `lbs/acre`) or invalid P method returns `VALIDATION_ERROR`.
- **Invalid Farm Area:** Zero or negative farm area returns `VALIDATION_ERROR`.

---

## 6. Automated Test Suite Execution Results

The test suite in `phase5_nutrient/tests/test_npk_calculation.py` executes **14 comprehensive test cases**:

```bash
pytest phase5_nutrient/tests/test_npk_calculation.py -v
```

### Execution Output
```
phase5_nutrient/tests/test_npk_calculation.py::test_01_valid_stcr_calculation PASSED [  7%]
phase5_nutrient/tests/test_npk_calculation.py::test_02_valid_soil_test_based_calculation PASSED [ 14%]
phase5_nutrient/tests/test_npk_calculation.py::test_03_missing_target_yield PASSED [ 21%]
phase5_nutrient/tests/test_npk_calculation.py::test_04_missing_required_soil_values PASSED [ 28%]
phase5_nutrient/tests/test_npk_calculation.py::test_05_unsupported_crop PASSED [ 35%]
phase5_nutrient/tests/test_npk_calculation.py::test_06_unverified_rule PASSED [ 42%]
phase5_nutrient/tests/test_npk_calculation.py::test_07_invalid_nutrient_units PASSED [ 50%]
phase5_nutrient/tests/test_npk_calculation.py::test_08_olsen_bray_method_mismatch PASSED [ 57%]
phase5_nutrient/tests/test_npk_calculation.py::test_09_invalid_farm_area PASSED [ 64%]
phase5_nutrient/tests/test_npk_calculation.py::test_10_acre_to_hectare_conversion PASSED [ 71%]
phase5_nutrient/tests/test_npk_calculation.py::test_11_per_hectare_vs_total_farm PASSED [ 78%]
phase5_nutrient/tests/test_npk_calculation.py::test_12_invalid_numeric_values PASSED [ 85%]
phase5_nutrient/tests/test_npk_calculation.py::test_13_target_yield_outside_documented_range PASSED [ 92%]
phase5_nutrient/tests/test_npk_calculation.py::test_14_api_validation_endpoint PASSED [100%]

============================= 14 passed in 2.51s ==============================
```

### Combined Phase 4 & Phase 5 Test Output
```bash
pytest agronomy/tests phase5_nutrient/tests -v
```
```
============================= 26 passed in 2.66s ==============================
```

---

## 7. Created & Modified Files

### Created Files
- `phase5_nutrient/__init__.py`: Package initialization.
- `phase5_nutrient/units.py`: Area & nutrient unit conversions.
- `phase5_nutrient/models.py`: Pydantic request & response schemas.
- `phase5_nutrient/service.py`: NPK Nutrient Calculation Engine.
- `phase5_nutrient/api.py`: FastAPI router with `POST /api/nutrient-requirement/calculate`.
- `phase5_nutrient/tests/__init__.py`: Test package initialization.
- `phase5_nutrient/tests/test_npk_calculation.py`: 14 automated unit tests.
- `PHASE_5_REPORT.md`: Comprehensive phase completion report.

### Modified Files
- `data/agronomy/tnau_stcr_rules.json`: Added STCR equation coefficients and TNAU soil test blanket RDF metadata.
- `phase3_soil/main.py`: Mounted `nutrient_router` into main FastAPI app.

---

## 8. Execution Commands

### Running Backend Server
```bash
uvicorn phase3_soil.main:app --reload
```

### Running Test Suite
```bash
# Run Phase 5 tests only
pytest phase5_nutrient/tests/test_npk_calculation.py -v

# Run combined Phase 4 and Phase 5 test suite
pytest agronomy/tests phase5_nutrient/tests -v
```

---

## 9. Next Steps for Phase 6 (Fertilizer Product Optimization)

With Phase 5 outputting precise nutrient requirements ($N, \text{P}_2\text{O}_5, \text{K}_2\text{O}$), Phase 6 will consume these values to:
1. Formulate linear programming (LP) cost-minimization models selecting straight & complex fertilizers (Urea, DAP, MOP, SSP, 20:20:0, 16:20:0).
2. Compute commercial fertilizer bag counts ($50\text{ kg}$ or $45\text{ kg}$ bags).
3. Compute split application schedules (Basal, Tillering, Panicle Initiation).
4. Provide estimated fertilizer cost calculations for Tamil Nadu farmers.
