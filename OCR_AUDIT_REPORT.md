# Soil Health Card (SHC) OCR & Parameter Extraction Audit Report

**Project Title**: AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  
**SIH Reference**: SIH1639 — Sustainable Fertilizer Usage Optimizer  
**Audit Scope**: Tamil Nadu Soil Health Card OCR, PDF parsing, parameter mapping, unit validation, and Flutter Review Extracted Soil Information workflow.  
**Test Fixture Document**: `SHC-24.08.2026.pdf` (Tamil Nadu Soil Health Card, Erode District, Groundnut, 1 Acre).

---

## 1. Executive Summary

A comprehensive investigation into the soil test card extraction and review pipeline was conducted. The investigation identified critical root causes in document section separation, Unicode encoding of Tamil vowels, multi-line table cell lookaheads, and client-side unit whitelisting.

All identified defects have been rectified dynamically without hard-coding document names or test fixture values. The updated pipeline was validated against the reference Soil Health Card fixture (`SHC-24.08.2026.pdf`), achieving **100% extraction accuracy** across all 12 target parameters and metadata, with **0 static analysis errors** and **100% test pass rates** across Python pytest (103/103 passed) and Flutter test suites (29/29 passed).

---

## 2. Root Cause Analysis

### Issue A: Association of Fertilizer Recommendation Dosages with Soil Test Results
* **Symptom**: Nitrogen mapped to `14` or `50`, Potassium mapped to `15` or `25`, Zinc mapped to `10.00` or `50`.
* **Root Cause**: Tamil Nadu Soil Health Cards contain two distinct functional sections:
  1. `மண் ஆய்வு முடிவுகள்` (Soil Analysis / Test Results)
  2. `உரப்பரிந்துரைகள்` (Fertilizer Recommendations — containing crop-specific doses of Urea, DAP, Potash, Micronutrient mixture, and Bio-fertilizers).
  In the internal stream of the PDF, the `உரப்பரிந்துரைகள்` text happened to precede the soil test tables. The previous parser performed top-down sequential matching across the document, encountering fertilizer recommendation lines (e.g., `தழை (N) 14 யூரியா 11...`, `சாம்பல் (K2O) 15 பொட்டாஷ் 25...`, `துத்தநாகம் கரைக்கக்கூடிய பாக்டீரியா ... 50 மி.லி`) and erroneously assigning fertilizer rates to soil test nutrient concentrations.

### Issue B: Visual-Order Tamil Unicode Vowel Encoding Discrepancy
* **Symptom**: Tamil section headings such as `வேதியியல் பண்புகள்` (Chemical Properties) and nutrient labels like `போரான்` (Boron) failed regex matching, causing section boundary detection to fail.
* **Root Cause**: In visual Tamil font rendering (common in Indian government PDFs), pre-base vowel signs (`\u0bc6` ெ, `\u0bc7` ே, `\u0bc8` ை) and two-part vowel signs (`\u0bca` ொ, `\u0bcb` ோ, `\u0bcc` ௌ) are positioned visually before or around the consonant. Standard canonical Unicode expects `<consonant> + <vowel_sign>`. Standard NFC normalization does not reorder pre-base vowel signs if placed in visual order, preventing exact keyword detection.

### Issue C: Discarding True Values in Favor of Sufficiency Benchmark Ranges
* **Symptom**: pH was extracted as `7.5` instead of `7.3`; Organic Carbon was extracted as `0.75` instead of `0.45`.
* **Root Cause**: In the chemical properties table, benchmark sufficiency ranges are printed next to test values (e.g. `(pH) 7.3 6.0 - \n 7.5 நடுநிலை`, `(OC %) 0.45 0.51 - \n 0.75 குறைவு`). Because line 1 of the cell had `6.0 -`, the previous parser rejected the entire line due to the hyphen `-` and grabbed `7.5` from line 2, which was the upper bound of the reference range rather than the measured value.

### Issue D: Incorrect Unit Extraction and Assignment of `%` to All Nutrients
* **Symptom**: Nitrogen, Potassium, Zinc, and Boron displayed `Unit "%" is not accepted for <Field>` in red banners on the review screen.
* **Root Cause**:
  1. `_find_header_unit` searched backwards up to 45 lines without checking field compatibility, grabbing `%` from `Organic Carbon (OC %)` or `70% சதவீதம் கீழ்` and assigning `%` to subsequent nutrients.
  2. The table header unit for Major Nutrients and Micronutrients in Tamil cards is `(கிலோ / ஏக்கர்)` (`kg/acre`). Neither `FIELDS` in `tnau_reference.py` nor `fieldSpecs` in `soil_field.dart` included `kg/acre` in their allowed unit whitelists.
  3. When an incompatible unit entered the Flutter DTO, `SoilValidator.check` marked the draft as `invalid` (`blocksConfirm = true`), preventing confirmation.

---

## 3. Architecture & Corrections Applied

```
Document Upload (PDF / Image)
      │
      ├── [ocr.py] Document Detection: Digital PDF vs Scanned Document
      │     └── If Digital PDF: Extract native Unicode text (pypdf/fitz)
      │     └── If Scanned/Image: Preprocess (OpenCV) -> Tesseract OCR
      │
      ├── [extraction.py] Tamil Unicode Normalization:
      │     └── Reorder visual pre-base & two-part vowel signs to canonical Unicode
      │
      ├── [extraction.py] Document Layout & Section Partitioning:
      │     ├── Section A: Metadata (Farmer, District, Village, Survey No, Crop, Area)
      │     ├── Section B: Soil Test Results (மண் ஆய்வு முடிவுகள்) -> EXTRACTED
      │     └── Section C: Fertilizer Recommendations (உரப்பரிந்துரைகள்) -> EXCLUDED
      │
      ├── [extraction.py] Table Parsing & Range Disambiguation:
      │     ├── Header Unit Propagation: (கிலோ / ஏக்கர்) -> "kg/acre"
      │     ├── Inline Units: EC (dS/m), (OC %)
      │     └── Range Disambiguation: Measured Value separated from Benchmark
      │
      ├── [units.py & tnau_reference.py] Parameter Validation & Normalization:
      │     ├── Explicit support for kg/acre, kg/ha, mg/kg, dS/m, %, and unitless pH
      │     └── Area-based conversion traceability (1 acre = 0.404686 ha; 1 ha = 2.47105 acres)
      │
      └── [verify_screen.dart & soil_field.dart] Farmer Verification & Confirmation:
            ├── Clear visual states: Green (Valid), Orange (Uncertain), Red (Invalid)
            ├── Parameter-specific unit selector in Edit modal
            └── Mandatory farmer acknowledgement before profile confirmation
```

---

## 4. Test Fixture Reference Validation

Comparison of reference values from `SHC-24.08.2026.pdf` against actual extraction output:

| Parameter | Reference Value | Extracted Value | Extracted Unit | Status | Accuracy |
|---|---|---|---|---|---|
| **Nitrogen (N)** | 39 kg/acre | 39.0 | kg/acre | Valid | 100% Match |
| **Phosphorus (P)** | 4 kg/acre | 4.0 | kg/acre | Uncertain (Needs Olsen/Bray check) | 100% Match |
| **Potassium (K)** | 259 kg/acre | 259.0 | kg/acre | Valid | 100% Match |
| **Soil pH** | 7.3 | 7.3 | None (Unitless) | Valid | 100% Match |
| **Electrical Conductivity (EC)** | 0.41 dS/m | 0.41 | dS/m | Valid | 100% Match |
| **Organic Carbon (OC)** | 0.45% | 0.45 | % | Valid | 100% Match |
| **Sulphur (S)** | 5 kg/acre | 5.0 | kg/acre | Valid | 100% Match |
| **Zinc (Zn)** | 0.43 kg/acre | 0.43 | kg/acre | Valid | 100% Match |
| **Iron (Fe)** | 1.9 kg/acre | 1.9 | kg/acre | Valid | 100% Match |
| **Manganese (Mn)** | 2.59 kg/acre | 2.59 | kg/acre | Valid | 100% Match |
| **Copper (Cu)** | 0.5 kg/acre | 0.5 | kg/acre | Valid | 100% Match |
| **Boron (B)** | 0.56 kg/acre | 0.56 | kg/acre | Valid | 100% Match |
| **Crop** | groundnut (நிலக்கடலை) | groundnut | — | Valid | 100% Match |
| **Farm Area** | 1 acre | 1.0 | acre | Valid | 100% Match |
| **Farmer Name** | K.SELVAN | K.SELVAN | — | Valid | 100% Match |
| **Sample ID** | TN/ERD/02488 | TN/ERD/02488 | — | Valid | 100% Match |
| **District** | ஈரோடு (Erode) | Erode | — | Valid | 100% Match |
| **Village** | வரதநல்லூர் | வரதநல்லூர் | — | Valid | 100% Match |
| **Survey Number** | 41 / 9 | 41 / 9 | — | Valid | 100% Match |

---

## 5. Verification & Test Outcomes

- **Python Tests**: **103 passed / 0 failed** (including 6 new dedicated regression tests in `test_shc_regression.py`).
- **Flutter Tests**: **29 passed / 0 failed** (20 UI flow & localization tests + 9 soil validation tests).
- **Static Analysis**: `flutter analyze` completed with **0 issues found**.
- **Hardcoding Check**: Verified that no report filenames (`SHC-24.08.2026.pdf`) or static numeric defaults were introduced into production application logic.
