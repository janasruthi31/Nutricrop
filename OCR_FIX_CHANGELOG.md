# OCR & Parameter Extraction Fix Changelog

**Release Branch**: `release/final-verified-delivery`  
**Reference Document**: `SHC-24.08.2026.pdf`

---

## 1. Summary of Changes

### A. Backend (`phase3_soil`)

1. **`phase3_soil/extraction.py`**:
   - Added `normalize_tamil_text()` to convert visual-order Tamil pre-base vowel signs (`\u0bc6`, `\u0bc7`, `\u0bc8`) and two-part vowel signs (`\u0bca`, `\u0bcb`, `\u0bcc`) into canonical Unicode representation.
   - Implemented document section partitioning: identified and segregated `உரப்பரிந்துரைகள்` (Fertilizer Recommendations) from `மண் ஆய்வு முடிவுகள்` (Soil Test Results) to prevent recommendation doses (e.g. Urea 11, DAP 50, Potash 25, biofertilizers) from being mapped to soil nutrient test results.
   - Implemented token-level range disambiguation `_extract_number_from_tokens()`: prevents benchmark/sufficiency ranges (e.g., `113-180`, `48 - 113`, `6.0 - 7.5`, `0.51 - 0.75`) from overriding true measured values.
   - Updated table header unit lookup `_find_header_unit`: accurately extracts and validates `(கிலோ / ஏக்கர்)` (`kg/acre`), `kg/ha`, and `mg/kg`.
   - Enhanced `extract_metadata()`: extracts crop name (`நிலக்கடலை` -> `groundnut`), farm area (`1.0` acre), farmer name, sample ID (`TN/ERD/02488`), district, village, and survey number.

2. **`phase3_soil/tnau_reference.py`**:
   - Added `kg/acre` to allowed unit lists in `FIELDS` for `nitrogen`, `phosphorus`, `potassium`, `sulphur`, `zinc`, `iron`, `manganese`, `copper`, and `boron`.
   - Added `uS/cm` and `mS/cm` for electrical conductivity, and `g/kg` for organic carbon.
   - Added physical plausibility ranges for all nutrients in `kg/acre` (scaled to 1 ha = 2.471 acres).

3. **`phase3_soil/units.py`**:
   - Expanded `_UNIT_ALIASES` with Tamil and parenthetical variations: `(கிலோ/ஏக்கர்)`, `கிலோ / ஏக்கர்`, `(oc%)`, `(%)`, `(ds/m)`.
   - Updated `normalize_value_unit()`: preserves `kg/acre` as the valid measurement unit while maintaining area-based traceability to `kg/ha` ($kg/ha = kg/acre \times 2.47105$).
   - Prevented unwarranted conversion of micronutrient `kg/acre` measurements to `mg/kg` without bulk density models.

4. **`phase3_soil/ocr.py`**:
   - Stage 1 / Stage 2 Optimization: For digitally generated PDFs, native digital text is extracted directly using `pypdf`. If clean text is present ($\ge 5$ words), it is parsed directly, bypassing lossy OCR rasterization and language pack mismatches on Tamil script.

5. **`phase3_soil/tests/test_shc_regression.py`**:
   - Created automated test suite with 6 test cases verifying exact reference extraction from `SHC-24.08.2026.pdf`, prevention of fertilizer rate confusion, prevention of benchmark range confusion, parameter-specific unit validation, missing data handling, and Tamil Unicode normalization.

---

### B. Frontend (`flutter_app`)

1. **`flutter_app/lib/models/soil_field.dart`**:
   - Updated `fieldSpecs` to include `kg/acre` in accepted unit lists for major nutrients ($N, P, K$), secondary nutrient ($S$), and micronutrients ($Zn, Fe, Mn, Cu, B$).
   - Added `uS/cm` and `mS/cm` for electrical conductivity; `g/kg` for organic carbon.
   - Hardened `FieldDraft.fromJson`: safe default fallback when OCR provides an unknown or incompatible unit (defaults to standard accepted agronomic unit while allowing farmer modification).

2. **`flutter_app/lib/screens/verify_screen.dart`**:
   - Preserved clear visual indicator states: Green (Valid), Orange/Yellow (Uncertain/Review), Red (Invalid), Grey (Missing).
   - Constrained Edit dialog unit dropdown to only display units valid for the selected parameter.
   - Retained farmer confirmation gate: requires checking the verification acknowledgement before enabling the **Confirm & Validate** button.

3. **`flutter_app/test/soil_validation_test.dart`**:
   - Added automated tests verifying acceptance of `kg/acre`, rejection of `%` for $N, P, K$, unitless validation for $pH$, and client-side confirmation gating.

---

## 2. Directory Locks & Build Resolution

- Resolved Windows file lock on `flutter_app/build` caused by concurrent process execution by removing the stale build directory and verifying clean directory recreation during Flutter build.
