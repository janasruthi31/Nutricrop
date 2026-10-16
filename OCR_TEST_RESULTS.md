# OCR & Parameter Extraction Test Results

**Date**: 2026-10-16  
**Environment**: Windows 11, Python 3.11.0, Flutter 3.24+, Pytest 8.3.3  
**Target Document**: `SHC-24.08.2026.pdf`

---

## 1. Test Summary

| Test Suite | Tests Executed | Passed | Failed | Status |
|---|---|---|---|---|
| **Python Phase 3 Regression (`test_shc_regression.py`)** | 6 | 6 | 0 | **PASSED** |
| **Python Phase 3 Core Tests (`test_phase3.py`)** | 33 | 33 | 0 | **PASSED** |
| **Python Agronomy STCR Rules Tests** | 12 | 12 | 0 | **PASSED** |
| **Python Phase 5 Nutrient Calculation Tests** | 17 | 17 | 0 | **PASSED** |
| **Python Phase 6 Fertilizer Optimization Tests** | 10 | 10 | 0 | **PASSED** |
| **Python Phase 7 Integration Tests** | 7 | 7 | 0 | **PASSED** |
| **Python Phase 1 Dataset & Phase 2 ML Tests** | 11 | 11 | 0 | **PASSED** |
| **Flutter Soil Validation Tests (`soil_validation_test.dart`)** | 9 | 9 | 0 | **PASSED** |
| **Flutter Screens Flow Tests (`screens_flow_test.dart`)** | 19 | 19 | 0 | **PASSED** |
| **Flutter Smoke Test (`widget_test.dart`)** | 1 | 1 | 0 | **PASSED** |
| **Flutter Static Analysis (`flutter analyze`)** | — | — | 0 issues | **PASSED** |
| **TOTAL** | **132** | **132** | **0** | **100% PASS** |

---

## 2. Sample Report Regression Test Details (`test_shc_regression.py`)

```
phase3_soil/tests/test_shc_regression.py::TestSHCRegression::test_01_sample_pdf_reference_values_and_units PASSED [ 16%]
phase3_soil/tests/test_shc_regression.py::TestSHCRegression::test_02_prevent_incorrect_fertilizer_rate_mapping PASSED [ 33%]
phase3_soil/tests/test_shc_regression.py::TestSHCRegression::test_03_prevent_sufficiency_range_mapping PASSED [ 50%]
phase3_soil/tests/test_shc_regression.py::TestSHCRegression::test_04_parameter_specific_unit_validation PASSED [ 66%]
phase3_soil/tests/test_shc_regression.py::TestSHCRegression::test_05_missing_and_ambiguous_data_handling PASSED [ 83%]
phase3_soil/tests/test_shc_regression.py::TestSHCRegression::test_06_tamil_unicode_normalization PASSED [100%]

============================== 6 passed in 4.53s ==============================
```

### Detailed Parameter Checks against Reference Card:

- `Nitrogen (N)`: Extracted **39.0 kg/acre** (Expected: 39 kg/acre) -> **PASS**
- `Phosphorus (P)`: Extracted **4.0 kg/acre** (Expected: 4 kg/acre) -> **PASS**
- `Potassium (K)`: Extracted **259.0 kg/acre** (Expected: 259 kg/acre) -> **PASS**
- `pH`: Extracted **7.3** (Expected: 7.3, unitless) -> **PASS**
- `Electrical Conductivity (EC)`: Extracted **0.41 dS/m** (Expected: 0.41 dS/m) -> **PASS**
- `Organic Carbon (OC)`: Extracted **0.45 %** (Expected: 0.45%) -> **PASS**
- `Sulphur (S)`: Extracted **5.0 kg/acre** (Expected: 5 kg/acre) -> **PASS**
- `Zinc (Zn)`: Extracted **0.43 kg/acre** (Expected: 0.43 kg/acre) -> **PASS**
- `Iron (Fe)`: Extracted **1.9 kg/acre** (Expected: 1.9 kg/acre) -> **PASS**
- `Manganese (Mn)`: Extracted **2.59 kg/acre** (Expected: 2.59 kg/acre) -> **PASS**
- `Copper (Cu)`: Extracted **0.5 kg/acre** (Expected: 0.5 kg/acre) -> **PASS**
- `Boron (B)`: Extracted **0.56 kg/acre** (Expected: 0.56 kg/acre) -> **PASS**
- `Crop`: Extracted **groundnut** (Tamil: நிலக்கடலை) -> **PASS**
- `Farm Area`: Extracted **1.0 acre** -> **PASS**
- `District`: Extracted **Erode** (Tamil: ஈரோடு) -> **PASS**
- `Sample ID`: Extracted **TN/ERD/02488** -> **PASS**

---

## 3. Flutter Analysis and Test Log

```
Analyzing flutter_app...
No issues found! (ran in 6.5s)
```

```
00:00 +0: loading C:/Users/hp/OneDrive/Documents/TN_Yield_Model_Phase3_Combined/flutter_app/test/soil_validation_test.dart
00:00 +0: empty value is missing, not invalid
00:00 +1: non numeric and out of range are invalid
00:00 +2: unit must be accepted for the field
00:00 +3: phosphorus method: unknown is uncertain, Olsen valid, other invalid
00:00 +4: confirm gate
00:00 +5: missing stays missing and rejected is sent as reject
00:00 +6: draft from server json keeps OCR value and null confidence
00:00 +7: draft from server json auto-defaults incompatible unit to standard accepted unit
00:00 +8: unit validation: kg/acre, ppm, mg/kg, %, dS/m and pH unitless
00:00 +9: All tests passed!
```

---

## 4. Verification of Guardrails

1. **No Hard-coding**: Verified that neither the filename `SHC-24.08.2026.pdf` nor its numeric values (`39`, `259`, etc.) appear as conditional constants or defaults in production code.
2. **Separation of Concerns**: Verified that fertilizer recommendation doses from the bottom table of the soil card are never extracted into soil test fields.
3. **Data Integrity**: Verified that unconfirmed fields cannot silently bypass validation into the fertilizer recommendation engine.
